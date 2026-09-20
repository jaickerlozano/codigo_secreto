"""Child-only pytest safeguards and outcome recording for real PostgreSQL runs."""

import json
import os
import hashlib
from pathlib import Path

import pytest


RUNTIME_ENV = "MANAGED_POSTGRESQL_RUNTIME"
PYTEST_RESULT_PATH_ENV = "MANAGED_POSTGRESQL_PYTEST_RESULT"


def runtime_mode(environment=None):
    return (os.environ if environment is None else environment).get(RUNTIME_ENV) == "1"


def write_outcome(path, **counts):
    Path(path).write_text(json.dumps(counts, sort_keys=True), encoding="utf-8")


def read_outcome(path):
    try:
        outcome = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    required = {"collected", "passed", "skipped", "failed", "errors"}
    allowed = required | {"node_ref"}
    if set(outcome) not in (required, allowed) or any(not isinstance(outcome[key], int) for key in required):
        return None
    if "node_ref" in outcome and (not isinstance(outcome["node_ref"], str) or len(outcome["node_ref"]) != 64):
        return None
    return outcome


def pg_only_coverage_complete(outcome):
    return outcome is not None and outcome["collected"] > 0 and all(
        outcome[key] == 0 for key in ("skipped", "failed", "errors")
    )


@pytest.fixture(scope="session")
def django_db_setup():
    """Use the already-migrated disposable target without create/drop operations."""
    yield


def pytest_collection_finish(session):
    session.config._managed_postgresql_collected = len(session.items)
    session.config._managed_postgresql_node_ref = hashlib.sha256(
        "\n".join(sorted(item.nodeid for item in session.items)).encode("utf-8")
    ).hexdigest()
    session.config._managed_postgresql_outcomes = {
        "passed": 0,
        "skipped": 0,
        "failed": 0,
        "errors": 0,
    }


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" and not (report.skipped or report.failed):
        return
    outcomes = item.config._managed_postgresql_outcomes
    if report.skipped:
        outcomes["skipped"] += 1
    elif report.failed:
        outcomes["failed" if report.when == "call" else "errors"] += 1
    elif report.when == "call":
        outcomes["passed"] += 1


def pytest_sessionfinish(session, exitstatus):
    path = os.environ.get(PYTEST_RESULT_PATH_ENV)
    if path:
        write_outcome(
            path,
            collected=getattr(session.config, "_managed_postgresql_collected", 0),
            node_ref=getattr(session.config, "_managed_postgresql_node_ref", None),
            **getattr(session.config, "_managed_postgresql_outcomes", {}),
        )
