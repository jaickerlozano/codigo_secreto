"""Command-line contract for managed PostgreSQL runtime validation."""

import argparse
import hashlib
import json
import os
import re
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

EXIT_SUCCESS = 0
EXIT_INPUT = 2
EXIT_MIGRATION = 5
EXIT_TESTS = 6
EXIT_EVIDENCE = 7
EXIT_STARTUP = 9

from .exit_codes import EXIT_LOCK, EXIT_POSTGRESQL, EXIT_UNSAFE
from .database import DatabaseTargetError, advisory_lock, database_url_from_environment, local_database_url_from_environment, open_disposable_target, open_local_readiness_target, open_release_target
from .evidence import EvidenceWriteError, EVIDENCE_SCHEMA, LocalEvidenceError, LocalEvidenceStore, canonicalize_evidence, validate_local_evidence, write_evidence
from .pytest_plugin import PYTEST_RESULT_PATH_ENV, RUNTIME_ENV, pg_only_coverage_complete, read_outcome
from .runner import (
    ChildProcessError,
    ChildCancelledError,
    ChildTimeoutError,
    ShardRun,
    aggregate_ordinary_shards,
    build_shard_plan,
    collect_ordinary_node_ids,
    node_ids_ref,
    ordinary_local_deadline,
    resume_pending_shards,
    run_ordinary_shards,
    run_stage,
)

RELEASE_ID_PATTERN = re.compile(r"[A-Za-z0-9._-]{1,128}")
LOCAL_EVIDENCE_ROOT = Path(".ordinary-validation-evidence")


def release_id(value):
    if RELEASE_ID_PATTERN.fullmatch(value) is None:
        raise argparse.ArgumentTypeError("release ID must contain 1-128 safe characters")
    return value


def build_parser():
    parser = argparse.ArgumentParser(prog="managed-postgresql-runtime")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate")
    validate.add_argument("--ack-disposable", action="store_true")
    validate.add_argument("--result", required=True)

    ordinary_validate = commands.add_parser("ordinary-validate")
    ordinary_validate.add_argument("--release-id", required=True, type=release_id)
    ordinary_validate.add_argument("--result", required=True)

    ordinary_local = commands.add_parser("ordinary-local")
    ordinary_local.add_argument("--resume", action="store_true")

    release_migrate = commands.add_parser("release-migrate")
    release_migrate.add_argument("--release-id", required=True, type=release_id)
    release_migrate.add_argument("--result", required=True)

    startup_check = commands.add_parser("startup-check")
    startup_check.add_argument("--release-id", required=True, type=release_id)
    startup_check.add_argument("--migration-result", required=True)
    startup_check.add_argument("--result", required=True)
    return parser


def _stage(name, status, code, outcome=None):
    stage = {"name": name, "status": status, "code": code}
    if outcome is not None:
        stage.update(outcome)
    return stage


def _target_ref(database_url):
    parsed = urlparse(database_url)
    target = f"{parsed.scheme}://{parsed.hostname or ''}:{parsed.port or ''}{parsed.path}"
    return hashlib.sha256(target.encode()).hexdigest()


def migration_graph_ref(backend_root=None):
    """Return a stable reference for the migration files that define the graph."""
    root = Path(backend_root or os.getcwd())
    digest = hashlib.sha256()
    for path in sorted((root / "apps").glob("*/migrations/*.py")):
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def read_migration_evidence(path):
    """Read only canonical migration evidence, returning None for malformed input."""
    try:
        content = Path(path).read_bytes()
        payload = json.loads(content)
        return payload if isinstance(payload, dict) and canonicalize_evidence(payload) == content else None
    except (OSError, ValueError, EvidenceWriteError):
        return None


def _result_payload(
    *,
    status,
    code,
    stages,
    database_url,
    command="validate",
    release_id=None,
    graph_ref=None,
    migration_result_id=None,
):
    return {
        "schema": EVIDENCE_SCHEMA,
        "result_id": hashlib.sha256(os.urandom(32)).hexdigest(),
        "command": command,
        "status": status,
        "code": code,
        "release_id": release_id,
        "target_ref": _target_ref(database_url) if database_url else None,
        "graph_ref": graph_ref,
        "migration_result_id": migration_result_id,
        "stages": stages,
        "started_at": datetime.now(UTC).isoformat(),
        "finished_at": datetime.now(UTC).isoformat(),
    }


def validate(*, acknowledged, result_path):
    """Run every fixed validation stage and fail closed on incomplete evidence."""
    connection = None
    database_url = None
    stages = []
    code = EXIT_SUCCESS
    try:
        connection = open_disposable_target(acknowledged=acknowledged)
        database_url = database_url_from_environment(os.environ)
        with advisory_lock(connection), tempfile.TemporaryDirectory() as temporary_directory:
            for name in ("migrate", "drift", "ordinary", "pg_only"):
                outcome_path = os.path.join(temporary_directory, f"{name}.json")
                child = run_stage(
                    name,
                    backend_root=os.getcwd(),
                    database_url=database_url,
                    environment={**os.environ, RUNTIME_ENV: "1", PYTEST_RESULT_PATH_ENV: outcome_path},
                )
                if child.returncode:
                    code = EXIT_MIGRATION if name in {"migrate", "drift"} else EXIT_TESTS
                    stages.append(_stage(name, "failed", code))
                    break
                outcome = read_outcome(outcome_path) if name in {"ordinary", "pg_only"} else None
                if name in {"ordinary", "pg_only"} and outcome is None:
                    code = EXIT_TESTS
                    stages.append(_stage(name, "failed", code))
                    break
                if name == "pg_only" and not pg_only_coverage_complete(outcome):
                    code = EXIT_TESTS
                    stages.append(_stage(name, "failed", code, outcome))
                    break
                stages.append(_stage(name, "passed", EXIT_SUCCESS, outcome))
    except DatabaseTargetError as error:
        code = error.code
    except ChildTimeoutError as error:
        code = error.code
    except ChildProcessError:
        code = EXIT_TESTS
    finally:
        if connection is not None:
            connection.close()
    try:
        write_evidence(
            result_path,
            _result_payload(
                status="passed" if code == EXIT_SUCCESS else "failed",
                code=code,
                stages=stages,
                database_url=database_url,
            ),
        )
    except EvidenceWriteError:
        return EXIT_EVIDENCE
    return code


def _local_timestamp():
    return datetime.now(UTC).isoformat()


def _local_record(kind, run_id, **fields):
    return {
        "schema": "ordinary-local-validation/v1",
        "kind": kind,
        "run_id": run_id,
        "timestamp": _local_timestamp(),
        **fields,
    }


def _read_local_record(path):
    try:
        candidate = Path(path)
        if candidate.is_symlink():
            return None
        contents = candidate.read_bytes()
        payload = json.loads(contents)
        if canonicalize_evidence(payload) != contents:
            return None
        return validate_local_evidence(payload)
    except (OSError, ValueError, LocalEvidenceError, EvidenceWriteError):
        return None


def _resume_evidence(store):
    current = _read_local_record(store.root / "current.json")
    if current is None or current["kind"] != "current":
        return None, {}
    run_id = current["run_id"]
    records = {}
    for path in (store.root / "runs" / run_id / "shards").glob("*.json"):
        record = _read_local_record(path)
        if record is not None and record.get("kind") == "shard" and isinstance(record.get("module"), str):
            records[record["module"]] = record
    return run_id, records


def _next_observation_sequence(store, run_id):
    observations = store.root / "runs" / run_id / "observations"
    sequences = (int(path.stem) for path in observations.glob("*.json") if path.stem.isdigit())
    return max(sequences, default=-1) + 1


def validate_ordinary_local_plan(plan, *, backend_root):
    """Allow local execution only for real ordinary Python test modules."""
    root = Path(backend_root).resolve()
    for shard in plan:
        relative = Path(shard.module)
        allowed = relative.suffix == ".py" and (
            relative.parts[:2] == ("core", "tests")
            or len(relative.parts) >= 4 and relative.parts[0] == "apps" and relative.parts[2] == "tests"
        )
        candidate = root / relative
        if relative.is_absolute() or ".." in relative.parts or not allowed or candidate.is_symlink() or not candidate.is_file():
            raise ChildProcessError("ordinary local shard module is invalid")
    return plan


def ordinary_local(*, resume=False, backend_root=None):
    """Run ordinary validation locally with durable, opt-in resumable evidence."""
    root = Path(backend_root or os.getcwd()).resolve()
    store = LocalEvidenceStore(root / LOCAL_EVIDENCE_ROOT)
    run_id, evidence_by_module = _resume_evidence(store) if resume else (None, {})
    run_id = run_id or uuid.uuid4().hex
    store.write("current.json", _local_record("current", run_id))
    store.write(f"runs/{run_id}/run.json", _local_record("run", run_id))

    connection = None
    try:
        deadline = ordinary_local_deadline()
        environment = dict(os.environ)
        database_url = local_database_url_from_environment(environment)
        observation_sequence = _next_observation_sequence(store, run_id)

        def record_readiness(observation):
            nonlocal observation_sequence
            store.write(
                f"runs/{run_id}/observations/{observation_sequence:04d}.json",
                _local_record("observation", run_id, **observation),
            )
            observation_sequence += 1

        try:
            connection = open_local_readiness_target(
                environment=environment,
                deadline=deadline,
                record=record_readiness,
            )
        except KeyboardInterrupt:
            return 130
        node_ids = collect_ordinary_node_ids(
            backend_root=root,
            database_url=database_url,
            environment=environment,
        )
        plan = validate_ordinary_local_plan(build_shard_plan(node_ids, backend_root=root), backend_root=root)
        collection_ref = node_ids_ref(node_ids)
        pending = resume_pending_shards(
            plan,
            evidence_by_module=evidence_by_module,
            run_id=run_id,
            backend_root=root,
            collection_ref=collection_ref,
        ) if resume else plan
        outcome_directory = store.root / "runs" / run_id / "outcomes"
        outcome_directory.mkdir(mode=0o700, exist_ok=True)

        def record_interrupted(shard):
            store.write(
                f"runs/{run_id}/shards/{hashlib.sha256(shard.module.encode()).hexdigest()}.json",
                _local_record(
                    "shard",
                    run_id,
                    module=shard.module,
                    module_sha256=hashlib.sha256((root / shard.module).read_bytes()).hexdigest(),
                    collection_ref=collection_ref,
                    status="interrupted",
                    collected=0,
                    passed=0,
                    skipped=0,
                    failed=0,
                    errors=0,
                ),
            )

        runs = run_ordinary_shards(
            pending,
            backend_root=root,
            database_url=database_url,
            environment=environment,
            outcome_directory=outcome_directory,
            deadline=deadline,
            on_interrupted=record_interrupted,
        )
        for run in runs:
            outcome = read_outcome(run.outcome["outcome_path"]) or {}
            counts = {field: outcome.get(field, 0) for field in ("collected", "passed", "skipped", "failed", "errors")}
            status = "passed" if run.child.returncode == 0 and counts["collected"] == counts["passed"] > 0 and not any(counts[field] for field in ("skipped", "failed", "errors")) else "failed"
            store.write(
                f"runs/{run_id}/shards/{hashlib.sha256(run.shard.module.encode()).hexdigest()}.json",
                _local_record(
                    "shard",
                    run_id,
                    module=run.shard.module,
                    module_sha256=hashlib.sha256((root / run.shard.module).read_bytes()).hexdigest(),
                    collection_ref=collection_ref,
                    status=status,
                    **counts,
                ),
            )
        return EXIT_SUCCESS if all(run.child.returncode == 0 for run in runs) else EXIT_TESTS
    except DatabaseTargetError as error:
        return error.code
    except (ChildTimeoutError, ChildCancelledError) as error:
        return error.code
    except (ChildProcessError, LocalEvidenceError, OSError):
        return EXIT_TESTS
    finally:
        if connection is not None:
            connection.close()


def ordinary_validate(*, release_id, result_path):
    """Run the complete non-``pg_only`` suite on a local or CI PostgreSQL target."""
    connection = None
    database_url = None
    stages = []
    graph_ref = None
    code = EXIT_SUCCESS
    try:
        database_url = database_url_from_environment(os.environ)
        connection = open_release_target()
        with tempfile.TemporaryDirectory() as temporary_directory:
            environment = dict(os.environ)
            environment.pop(RUNTIME_ENV, None)
            node_ids = collect_ordinary_node_ids(
                backend_root=os.getcwd(),
                database_url=database_url,
                environment=environment,
            )
            plan = build_shard_plan(node_ids, backend_root=os.getcwd())
            completed_runs = run_ordinary_shards(
                plan,
                backend_root=os.getcwd(),
                database_url=database_url,
                environment=environment,
                outcome_directory=temporary_directory,
            )
            runs = tuple(
                ShardRun(run.shard, run.child, read_outcome(run.outcome["outcome_path"]))
                for run in completed_runs
            )
            outcome = aggregate_ordinary_shards(node_ids, runs)
            if outcome is None:
                code = EXIT_TESTS
                failed_shard = next(
                    (
                        (index, run)
                        for index, run in enumerate(runs, start=1)
                        if run.child.returncode
                    ),
                    None,
                )
                failure = None if failed_shard is None else {
                    "shard_index": failed_shard[0],
                    "shard_module": failed_shard[1].shard.module,
                }
                stages.append(_stage("ordinary", "failed", code, failure))
            else:
                stages.append(_stage("ordinary", "passed", EXIT_SUCCESS, outcome))
                graph_ref = migration_graph_ref()
    except DatabaseTargetError as error:
        code = error.code
    except ChildTimeoutError as error:
        code = error.code
        if error.shard_index is not None:
            stages.append(_stage("ordinary", "failed", code, {
                "shard_index": error.shard_index,
                "shard_module": error.shard_module,
            }))
    except ChildProcessError:
        code = EXIT_TESTS
    finally:
        if connection is not None:
            connection.close()
    return _publish_release_result(
        command="ordinary-validate",
        release_id=release_id,
        result_path=result_path,
        code=code,
        stages=stages,
        database_url=database_url,
        graph_ref=graph_ref,
    )


def _publish_release_result(*, command, release_id, result_path, code, stages, database_url, graph_ref, migration_result_id=None):
    try:
        write_evidence(
            result_path,
            _result_payload(
                status="passed" if code == EXIT_SUCCESS else "failed",
                code=code,
                stages=stages,
                database_url=database_url,
                command=command,
                release_id=release_id,
                graph_ref=graph_ref,
                migration_result_id=migration_result_id,
            ),
        )
    except EvidenceWriteError:
        return EXIT_EVIDENCE
    return code


def release_migrate(*, release_id, result_path):
    """Serialize migration and prove that no migration remains pending."""
    connection = None
    database_url = None
    graph_ref = None
    stages = []
    code = EXIT_SUCCESS
    try:
        database_url = database_url_from_environment(os.environ)
        connection = open_release_target()
        with advisory_lock(connection):
            for stage in ("migrate", "pending_migrations"):
                child = run_stage(stage, backend_root=os.getcwd(), database_url=database_url, environment=os.environ)
                if child.returncode:
                    code = EXIT_MIGRATION
                    stages.append(_stage(stage, "failed", code))
                    break
                stages.append(_stage(stage, "passed", EXIT_SUCCESS))
            if code == EXIT_SUCCESS:
                graph_ref = migration_graph_ref()
    except DatabaseTargetError as error:
        code = error.code
    except ChildTimeoutError as error:
        code = error.code
    except ChildProcessError:
        code = EXIT_MIGRATION
    finally:
        if connection is not None:
            connection.close()
    return _publish_release_result(
        command="release-migrate",
        release_id=release_id,
        result_path=result_path,
        code=code,
        stages=stages,
        database_url=database_url,
        graph_ref=graph_ref,
    )


def _valid_migration_evidence(payload, *, release_id, database_url, graph_ref):
    return bool(payload) and all(
        (
            payload.get("schema") == EVIDENCE_SCHEMA,
            payload.get("command") == "release-migrate",
            payload.get("status") == "passed",
            payload.get("code") == EXIT_SUCCESS,
            payload.get("release_id") == release_id,
            payload.get("target_ref") == _target_ref(database_url),
            payload.get("graph_ref") == graph_ref,
        )
    )


def startup_check(*, release_id, migration_result_path, result_path):
    """Approve startup only after matching successful migration evidence."""
    migration = read_migration_evidence(migration_result_path)
    database_url = None
    graph_ref = None
    connection = None
    stages = []
    code = EXIT_STARTUP
    try:
        database_url = database_url_from_environment(os.environ)
        graph_ref = migration_graph_ref()
        if not _valid_migration_evidence(migration, release_id=release_id, database_url=database_url, graph_ref=graph_ref):
            stages.append(_stage("migration_evidence", "failed", EXIT_STARTUP))
        else:
            connection = open_release_target()
            with advisory_lock(connection):
                for stage in ("pending_migrations", "deploy_check"):
                    child = run_stage(stage, backend_root=os.getcwd(), database_url=database_url, environment=os.environ)
                    if child.returncode:
                        stages.append(_stage(stage, "failed", EXIT_STARTUP))
                        break
                    stages.append(_stage(stage, "passed", EXIT_SUCCESS))
                else:
                    code = EXIT_SUCCESS
    except (DatabaseTargetError, ChildProcessError):
        stages.append(_stage("startup", "failed", EXIT_STARTUP))
    finally:
        if connection is not None:
            connection.close()
    return _publish_release_result(
        command="startup-check",
        release_id=release_id,
        result_path=result_path,
        code=code,
        stages=stages,
        database_url=database_url,
        graph_ref=graph_ref,
        migration_result_id=migration.get("result_id") if migration else None,
    )


def main(argv=None):
    arguments = build_parser().parse_args(argv)
    if arguments.command == "validate":
        return validate(acknowledged=arguments.ack_disposable, result_path=arguments.result)
    if arguments.command == "ordinary-validate":
        return ordinary_validate(release_id=arguments.release_id, result_path=arguments.result)
    if arguments.command == "ordinary-local":
        return ordinary_local(resume=arguments.resume)
    if arguments.command == "release-migrate":
        return release_migrate(release_id=arguments.release_id, result_path=arguments.result)
    if arguments.command == "startup-check":
        return startup_check(
            release_id=arguments.release_id,
            migration_result_path=arguments.migration_result,
            result_path=arguments.result,
        )
    return EXIT_INPUT
