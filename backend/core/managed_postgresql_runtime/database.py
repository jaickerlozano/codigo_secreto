"""Fail-closed PostgreSQL target checks and serialization lock."""

import os
import time
from contextlib import contextmanager
from ipaddress import ip_address
from urllib.parse import urlparse

import psycopg

from .exit_codes import EXIT_LOCK, EXIT_POSTGRESQL, EXIT_UNSAFE


LOCK_SEED = 20260906
LOCK_TIMEOUT_SECONDS = 60
CONNECT_TIMEOUT_SECONDS = 10
NON_SYSTEM_RELATIONS_QUERY = """
    SELECT count(*)
    FROM pg_catalog.pg_class AS relation
    JOIN pg_catalog.pg_namespace AS namespace ON namespace.oid = relation.relnamespace
    WHERE namespace.nspname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
      AND namespace.nspname NOT LIKE 'pg_temp_%'
      AND relation.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
"""
TRY_LOCK_QUERY = "SELECT pg_try_advisory_lock(hashtextextended(current_database(), %s))"
UNLOCK_QUERY = "SELECT pg_advisory_unlock(hashtextextended(current_database(), %s))"


class DatabaseTargetError(RuntimeError):
    """A target cannot safely satisfy the validation contract."""

    def __init__(self, code):
        super().__init__("managed PostgreSQL target validation failed")
        self.code = code


def database_url_from_environment(environment=None):
    """Return a complete PostgreSQL URL without including it in errors."""
    values = os.environ if environment is None else environment
    database_url = values.get("DATABASE_URL")
    parsed = urlparse(database_url or "")
    if (
        parsed.scheme not in {"postgres", "postgresql"}
        or not parsed.hostname
        or not parsed.path.strip("/")
    ):
        raise DatabaseTargetError(EXIT_POSTGRESQL)
    return database_url


def local_database_url_from_environment(environment=None):
    """Return a local-only PostgreSQL URL after strict loopback validation."""
    database_url = database_url_from_environment(environment)
    hostname = urlparse(database_url).hostname
    if hostname != "localhost":
        try:
            if not ip_address(hostname).is_loopback:
                raise ValueError
        except ValueError as error:
            raise DatabaseTargetError(EXIT_UNSAFE) from error
    return database_url


class ReadinessObserver:
    """Record non-fatal readiness samples no more than once per interval."""

    def __init__(self, record, *, interval_seconds=30, clock=time.monotonic, sample_immediately=False):
        self.record = record
        self.interval_seconds = interval_seconds
        self.clock = clock
        self.next_sample_at = clock() if sample_immediately else clock() + interval_seconds

    def observe(self, status, *, force=False):
        """Record a known readiness status when it is due or explicitly forced."""
        observed_at = self.clock()
        if not force and observed_at < self.next_sample_at:
            return False
        self.next_sample_at = observed_at + self.interval_seconds
        self.record({"status": status, "observed_at": observed_at})
        return True

    def sample_if_due(self, probe):
        """Record a sanitized diagnostic sample and never propagate probe errors."""
        observed_at = self.clock()
        if observed_at < self.next_sample_at:
            return False
        self.next_sample_at = observed_at + self.interval_seconds
        try:
            probe()
        except (OSError, psycopg.Error):
            self.record({"status": "sample_error", "observed_at": observed_at})
        else:
            self.record({"status": "ready", "observed_at": observed_at})
        return True


def open_local_readiness_target(
    *,
    environment=None,
    deadline,
    record,
    clock=time.monotonic,
    sleep=time.sleep,
    retry_interval_seconds=1,
):
    """Wait for the already loopback-validated local target before execution."""
    observer = ReadinessObserver(record, clock=clock, sample_immediately=True)
    while clock() < deadline:
        try:
            connection = open_release_target(environment=environment)
        except DatabaseTargetError as error:
            if error.code != EXIT_POSTGRESQL:
                raise
            observer.observe("sample_error")
            remaining = deadline - clock()
            if remaining <= 0:
                raise
            sleep(min(retry_interval_seconds, remaining))
            continue
        if clock() >= deadline:
            connection.close()
            raise DatabaseTargetError(EXIT_POSTGRESQL)
        try:
            observer.observe("ready", force=True)
        except BaseException:
            connection.close()
            raise
        return connection
    raise DatabaseTargetError(EXIT_POSTGRESQL)


def open_disposable_target(*, acknowledged, environment=None):
    """Connect only after explicit disposal acknowledgement and empty-db proof."""
    if not acknowledged:
        raise DatabaseTargetError(EXIT_UNSAFE)
    database_url = database_url_from_environment(environment)
    try:
        connection = psycopg.connect(
            database_url,
            autocommit=True,
            connect_timeout=CONNECT_TIMEOUT_SECONDS,
        )
    except (OSError, psycopg.Error) as error:
        raise DatabaseTargetError(EXIT_POSTGRESQL) from error
    try:
        relation_count = connection.execute(NON_SYSTEM_RELATIONS_QUERY).fetchone()[0]
    except psycopg.Error as error:
        connection.close()
        raise DatabaseTargetError(EXIT_POSTGRESQL) from error
    if relation_count:
        connection.close()
        raise DatabaseTargetError(EXIT_UNSAFE)
    return connection


def open_release_target(*, environment=None):
    """Connect to the supplied PostgreSQL release target without mutating it."""
    database_url = database_url_from_environment(environment)
    try:
        return psycopg.connect(
            database_url,
            autocommit=True,
            connect_timeout=CONNECT_TIMEOUT_SECONDS,
        )
    except (OSError, psycopg.Error) as error:
        raise DatabaseTargetError(EXIT_POSTGRESQL) from error


@contextmanager
def advisory_lock(
    connection,
    *,
    timeout_seconds=LOCK_TIMEOUT_SECONDS,
    clock=time.monotonic,
    sleep=time.sleep,
):
    """Hold the target-derived PostgreSQL advisory lock for one operation."""
    started_at = clock()
    while True:
        acquired = connection.execute(TRY_LOCK_QUERY, (LOCK_SEED,)).fetchone()[0]
        if acquired:
            break
        if clock() - started_at >= timeout_seconds:
            raise DatabaseTargetError(EXIT_LOCK)
        sleep(1)
    try:
        yield
    finally:
        connection.execute(UNLOCK_QUERY, (LOCK_SEED,))
