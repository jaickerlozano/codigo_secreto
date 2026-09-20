"""Database safety contracts for managed PostgreSQL validation."""

import pytest

from core.managed_postgresql_runtime import database
from core.managed_postgresql_runtime.cli import EXIT_LOCK, EXIT_POSTGRESQL, EXIT_UNSAFE


class FakeCursor:
    def __init__(self, result):
        self.result = result

    def fetchone(self):
        return self.result


class FakeConnection:
    def __init__(self, results):
        self.results = iter(results)
        self.calls = []
        self.closed = False

    def execute(self, statement, parameters=None):
        self.calls.append((statement, parameters))
        return FakeCursor(next(self.results))

    def close(self):
        self.closed = True


def test_missing_database_url_exits_4(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(database.DatabaseTargetError) as error:
        database.database_url_from_environment()

    assert error.value.code == EXIT_POSTGRESQL


def test_reachable_disposable_target_is_checked_before_use(monkeypatch):
    connection = FakeConnection([(0,)])
    captured = {}

    def connect(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return connection

    monkeypatch.setenv("DATABASE_URL", "postgresql://operator@db.example/validation")
    monkeypatch.setattr(database.psycopg, "connect", connect)

    assert database.open_disposable_target(acknowledged=True) is connection
    assert captured == {
        "url": "postgresql://operator@db.example/validation",
        "kwargs": {"autocommit": True, "connect_timeout": 10},
    }
    assert "pg_catalog.pg_class" in connection.calls[0][0]


def test_unreachable_host_exits_4(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://operator@db.example/validation")
    monkeypatch.setattr(database.psycopg, "connect", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError()))

    with pytest.raises(database.DatabaseTargetError) as error:
        database.open_disposable_target(acknowledged=True)

    assert error.value.code == EXIT_POSTGRESQL


def test_non_disposable_target_exits_3(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://operator@db.example/validation")

    with pytest.raises(database.DatabaseTargetError) as error:
        database.open_disposable_target(acknowledged=False)

    assert error.value.code == EXIT_UNSAFE


def test_nonempty_database_exits_3(monkeypatch):
    connection = FakeConnection([(1,)])
    monkeypatch.setenv("DATABASE_URL", "postgresql://operator@db.example/validation")
    monkeypatch.setattr(database.psycopg, "connect", lambda *_args, **_kwargs: connection)

    with pytest.raises(database.DatabaseTargetError) as error:
        database.open_disposable_target(acknowledged=True)

    assert error.value.code == EXIT_UNSAFE
    assert connection.closed is True


def test_advisory_lock_is_held_then_released():
    connection = FakeConnection([(True,), (True,)])

    with database.advisory_lock(connection):
        assert len(connection.calls) == 1

    assert "pg_try_advisory_lock" in connection.calls[0][0]
    assert "pg_advisory_unlock" in connection.calls[1][0]


def test_lock_contention_exits_8():
    connection = FakeConnection([(False,), (False,)])
    clock = iter([0, 60])

    with pytest.raises(database.DatabaseTargetError) as error:
        with database.advisory_lock(
            connection,
            timeout_seconds=60,
            clock=lambda: next(clock),
            sleep=lambda _seconds: None,
        ):
            pytest.fail("a contended lock must not enter its protected block")

    assert error.value.code == EXIT_LOCK


@pytest.mark.parametrize(
    "database_url",
    (
        "postgresql://operator@db.example/validation",
        "postgresql://operator@192.168.1.10/validation",
        "postgresql://operator@[2001:db8::1]/validation",
    ),
)
def test_local_database_url_rejects_every_non_loopback_host(database_url):
    with pytest.raises(database.DatabaseTargetError) as error:
        database.local_database_url_from_environment({"DATABASE_URL": database_url})

    assert error.value.code == EXIT_UNSAFE


@pytest.mark.parametrize(
    "database_url",
    (
        "postgresql://operator@localhost/validation",
        "postgresql://operator@127.0.0.1/validation",
        "postgresql://operator@[::1]/validation",
    ),
)
def test_local_database_url_accepts_only_loopback_hosts(database_url):
    assert database.local_database_url_from_environment({"DATABASE_URL": database_url}) == database_url


def test_readiness_observer_samples_every_30_seconds_and_never_stops_waiting():
    observations = []
    clock = iter((0, 29, 30, 59, 60))
    observer = database.ReadinessObserver(observations.append, clock=lambda: next(clock))

    assert observer.sample_if_due(lambda: None) is False
    assert observer.sample_if_due(lambda: None) is True
    assert observer.sample_if_due(lambda: None) is False
    assert observer.sample_if_due(lambda: (_ for _ in ()).throw(OSError("unavailable"))) is True
    assert observations == [
        {"status": "ready", "observed_at": 30},
        {"status": "sample_error", "observed_at": 60},
    ]


def test_readiness_observer_records_forced_ready_and_initial_error():
    observations = []
    clock = iter((0, 0, 0))
    observer = database.ReadinessObserver(
        observations.append,
        clock=lambda: next(clock),
        sample_immediately=True,
    )

    assert observer.observe("sample_error") is True
    assert observer.observe("ready", force=True) is True
    assert observations == [
        {"status": "sample_error", "observed_at": 0},
        {"status": "ready", "observed_at": 0},
    ]


def test_open_local_readiness_target_returns_immediately_when_ready(monkeypatch):
    connection = FakeConnection(())
    sleeps = []
    observations = []
    monkeypatch.setattr(database, "open_release_target", lambda **_kwargs: connection)

    assert database.open_local_readiness_target(
        environment={"DATABASE_URL": "postgresql://localhost/local"},
        deadline=10,
        record=observations.append,
        clock=lambda: 0,
        sleep=sleeps.append,
    ) is connection
    assert sleeps == []
    assert observations == [{"status": "ready", "observed_at": 0}]


def test_open_local_readiness_target_retries_with_diagnostics_until_ready(monkeypatch):
    connection = FakeConnection(())
    attempts = iter(
        (
            database.DatabaseTargetError(EXIT_POSTGRESQL),
            database.DatabaseTargetError(EXIT_POSTGRESQL),
            connection,
        )
    )
    observed = []
    sleeps = []
    now = [0]

    def open_target(**_kwargs):
        result = next(attempts)
        if isinstance(result, Exception):
            raise result
        return result

    def sleep(seconds):
        sleeps.append(seconds)
        now[0] += 30

    monkeypatch.setattr(database, "open_release_target", open_target)

    assert database.open_local_readiness_target(
        environment={"DATABASE_URL": "postgresql://localhost/local"},
        deadline=90,
        record=observed.append,
        clock=lambda: now[0],
        sleep=sleep,
        retry_interval_seconds=30,
    ) is connection
    assert sleeps == [30, 30]
    assert observed == [
        {"status": "sample_error", "observed_at": 0},
        {"status": "sample_error", "observed_at": 30},
        {"status": "ready", "observed_at": 60},
    ]


def test_open_local_readiness_target_stops_at_deadline_and_closes_late_success(monkeypatch):
    connection = FakeConnection(())
    attempts = []
    now = [0]

    def unavailable(**_kwargs):
        attempts.append("connect")
        raise database.DatabaseTargetError(EXIT_POSTGRESQL)

    def sleep(seconds):
        now[0] += seconds

    monkeypatch.setattr(database, "open_release_target", unavailable)
    with pytest.raises(database.DatabaseTargetError) as error:
        database.open_local_readiness_target(
            environment={"DATABASE_URL": "postgresql://localhost/local"},
            deadline=1,
            record=lambda _record: None,
            clock=lambda: now[0],
            sleep=sleep,
        )
    assert error.value.code == EXIT_POSTGRESQL
    assert attempts == ["connect"]

    now[0] = 0

    def late_connection(**_kwargs):
        now[0] = 1
        return connection

    monkeypatch.setattr(database, "open_release_target", late_connection)
    with pytest.raises(database.DatabaseTargetError) as error:
        database.open_local_readiness_target(
            environment={"DATABASE_URL": "postgresql://localhost/local"},
            deadline=1,
            record=lambda _record: None,
            clock=lambda: now[0],
        )
    assert error.value.code == EXIT_POSTGRESQL
    assert connection.closed is True
