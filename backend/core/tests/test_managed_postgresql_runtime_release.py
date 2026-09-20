"""Release migration and startup approval contracts."""

from contextlib import contextmanager
from pathlib import Path

from core.managed_postgresql_runtime import cli
from core.managed_postgresql_runtime.runner import ChildResult


PROJECT_ROOT = Path(__file__).resolve().parents[3]


@contextmanager
def held_lock(_connection):
    yield


def successful_stage(stage, **_kwargs):
    return ChildResult((stage,), 0, "completed")


def configure_release(monkeypatch):
    connection = type("Connection", (), {"closed": False, "close": lambda self: setattr(self, "closed", True)})()
    monkeypatch.setattr(cli, "open_release_target", lambda: connection, raising=False)
    monkeypatch.setattr(cli, "advisory_lock", held_lock)
    monkeypatch.setattr(cli, "run_stage", successful_stage)
    monkeypatch.setattr(
        cli,
        "database_url_from_environment",
        lambda _environment: "postgresql://operator:secret@db.invalid/release",
    )
    return connection


def test_startup_denied_without_migration_result(monkeypatch, tmp_path):
    result_path = tmp_path / "startup.json"

    assert cli.startup_check(
        release_id="release-1",
        migration_result_path=tmp_path / "missing.json",
        result_path=result_path,
    ) == cli.EXIT_STARTUP
    assert '"status":"failed"' in result_path.read_text(encoding="utf-8")


def test_startup_denied_on_release_id_mismatch(monkeypatch, tmp_path):
    migration_path = tmp_path / "migration.json"
    result_path = tmp_path / "startup.json"
    configure_release(monkeypatch)

    assert cli.release_migrate(release_id="release-1", result_path=migration_path) == cli.EXIT_SUCCESS
    assert cli.startup_check(
        release_id="release-2",
        migration_result_path=migration_path,
        result_path=result_path,
    ) == cli.EXIT_STARTUP


def test_startup_denied_on_non_object_migration_evidence(tmp_path):
    migration_path = tmp_path / "migration.json"
    result_path = tmp_path / "startup.json"
    cli.write_evidence(migration_path, ["not", "a", "result"])

    assert cli.startup_check(
        release_id="release-1",
        migration_result_path=migration_path,
        result_path=result_path,
    ) == cli.EXIT_STARTUP


def test_startup_denied_on_stale_graph(monkeypatch, tmp_path):
    migration_path = tmp_path / "migration.json"
    result_path = tmp_path / "startup.json"
    configure_release(monkeypatch)

    assert cli.release_migrate(release_id="release-1", result_path=migration_path) == cli.EXIT_SUCCESS
    payload = cli.read_migration_evidence(migration_path)
    payload["graph_ref"] = "0" * 64
    cli.write_evidence(migration_path, payload)

    assert cli.startup_check(
        release_id="release-1",
        migration_result_path=migration_path,
        result_path=result_path,
    ) == cli.EXIT_STARTUP


def test_startup_approved_after_valid_migration(monkeypatch, tmp_path):
    migration_path = tmp_path / "migration.json"
    result_path = tmp_path / "startup.json"
    connection = configure_release(monkeypatch)

    assert cli.release_migrate(release_id="release-1", result_path=migration_path) == cli.EXIT_SUCCESS
    assert cli.startup_check(
        release_id="release-1",
        migration_result_path=migration_path,
        result_path=result_path,
    ) == cli.EXIT_SUCCESS
    assert '"migration_result_id"' in result_path.read_text(encoding="utf-8")
    assert connection.closed is True


def test_operator_runbook_requires_the_serialized_release_contract():
    runbook = (PROJECT_ROOT / "docs" / "production-security.md").read_text(encoding="utf-8")

    assert "validate → release-migrate → startup-check → server start" in runbook
    assert "--ack-disposable" in runbook
    assert "credential-redacted" in runbook
    assert "must not start" in runbook
