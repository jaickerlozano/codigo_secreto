"""Local ordinary-validation command contracts."""

import json
from hashlib import sha256

import pytest

from core.managed_postgresql_runtime import cli
from core.managed_postgresql_runtime.evidence import canonicalize_evidence, validate_local_evidence
from core.managed_postgresql_runtime.runner import (
    ChildCancelledError,
    ChildProcessError,
    ChildResult,
    ChildTimeoutError,
    Shard,
    ShardRun,
    node_ids_ref,
)


def test_local_path_validation_rejects_non_modules_and_accepts_test_module(tmp_path):
    module = tmp_path / "core" / "tests" / "test_allowed.py"
    module.parent.mkdir(parents=True)
    module.write_text("def test_allowed(): pass\n", encoding="utf-8")
    plan = (Shard("core/tests/test_allowed.py", ("core/tests/test_allowed.py::test_allowed",)),)

    assert cli.validate_ordinary_local_plan(plan, backend_root=tmp_path) == plan

    for filename in ("requirements.txt", "CMakeLists.txt", "README.md", "README.mdx", "README.sh"):
        invalid_plan = (Shard(f"core/tests/{filename}", (f"core/tests/{filename}::ignored",)),)
        with pytest.raises(ChildProcessError):
            cli.validate_ordinary_local_plan(invalid_plan, backend_root=tmp_path)


def test_ordinary_local_fresh_run_replaces_current_and_does_not_resume(monkeypatch, tmp_path):
    module = tmp_path / "core" / "tests" / "test_allowed.py"
    module.parent.mkdir(parents=True)
    module.write_text("def test_allowed(): pass\n", encoding="utf-8")
    node_id = "core/tests/test_allowed.py::test_allowed"
    shard = Shard("core/tests/test_allowed.py", (node_id,))
    evidence_root = tmp_path / ".ordinary-validation-evidence"
    evidence_root.mkdir(mode=0o700)
    (evidence_root / "current.json").write_text(
        json.dumps({"schema": "ordinary-local-validation/v1", "kind": "current", "run_id": "prior-run", "timestamp": "2026-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )
    invoked_plans = []

    monkeypatch.setattr(cli, "LOCAL_EVIDENCE_ROOT", evidence_root)
    monkeypatch.setattr(cli, "local_database_url_from_environment", lambda _environment: "postgresql://localhost/local")
    monkeypatch.setattr(cli, "open_local_readiness_target", lambda **_kwargs: type("Connection", (), {"close": lambda self: None})())
    monkeypatch.setattr(cli, "collect_ordinary_node_ids", lambda **_kwargs: (node_id,))
    monkeypatch.setattr(cli, "build_shard_plan", lambda *_args, **_kwargs: (shard,))

    def run_shards(plan, **_kwargs):
        invoked_plans.append(plan)
        return (ShardRun(shard, ChildResult(("pytest",), 0, ""), {"outcome_path": "unused"}),)

    monkeypatch.setattr(cli, "run_ordinary_shards", run_shards)
    monkeypatch.setattr(cli, "read_outcome", lambda _path: {"collected": 1, "passed": 1, "skipped": 0, "failed": 0, "errors": 0})

    assert cli.ordinary_local(resume=False, backend_root=tmp_path) == cli.EXIT_SUCCESS
    current = json.loads((evidence_root / "current.json").read_text(encoding="utf-8"))

    assert current["run_id"] != "prior-run"
    assert invoked_plans == [(shard,)]


def test_release_command_arguments_remain_unchanged():
    parser = cli.build_parser()

    ordinary = parser.parse_args(["ordinary-validate", "--release-id", "release-1", "--result", "ordinary.json"])
    migration = parser.parse_args(["release-migrate", "--release-id", "release-1", "--result", "migration.json"])
    startup = parser.parse_args(["startup-check", "--release-id", "release-1", "--migration-result", "migration.json", "--result", "startup.json"])

    assert vars(ordinary) == {"command": "ordinary-validate", "release_id": "release-1", "result": "ordinary.json"}
    assert vars(migration) == {"command": "release-migrate", "release_id": "release-1", "result": "migration.json"}
    assert vars(startup) == {
        "command": "startup-check",
        "release_id": "release-1",
        "migration_result": "migration.json",
        "result": "startup.json",
    }
    assert vars(parser.parse_args(["ordinary-local", "--resume"])) == {"command": "ordinary-local", "resume": True}


def _configure_local_run(monkeypatch, tmp_path):
    module = tmp_path / "core" / "tests" / "test_allowed.py"
    module.parent.mkdir(parents=True)
    module.write_text("def test_allowed(): pass\n", encoding="utf-8")
    node_id = "core/tests/test_allowed.py::test_allowed"
    shard = Shard("core/tests/test_allowed.py", (node_id,))
    evidence_root = tmp_path / ".ordinary-validation-evidence"

    monkeypatch.setattr(cli, "LOCAL_EVIDENCE_ROOT", evidence_root)
    monkeypatch.setattr(cli, "local_database_url_from_environment", lambda _environment: "postgresql://localhost/local")
    monkeypatch.setattr(cli, "open_local_readiness_target", lambda **_kwargs: type("Connection", (), {"close": lambda self: None})())
    monkeypatch.setattr(cli, "collect_ordinary_node_ids", lambda **_kwargs: (node_id,))
    monkeypatch.setattr(cli, "build_shard_plan", lambda *_args, **_kwargs: (shard,))

    return evidence_root, node_id, shard


def _write_current_and_shard(evidence_root, *, run_id, shard, node_id, module_sha256):
    shard_path = evidence_root / "runs" / run_id / "shards"
    shard_path.mkdir(parents=True)
    (evidence_root / "current.json").write_bytes(
        canonicalize_evidence(
            {"schema": "ordinary-local-validation/v1", "kind": "current", "run_id": run_id, "timestamp": "2026-01-01T00:00:00+00:00"}
        )
    )
    (shard_path / f"{sha256(shard.module.encode()).hexdigest()}.json").write_bytes(
        canonicalize_evidence(
            {
                "schema": "ordinary-local-validation/v1",
                "kind": "shard",
                "run_id": run_id,
                "timestamp": "2026-01-01T00:00:00+00:00",
                "module": shard.module,
                "module_sha256": module_sha256,
                "collection_ref": node_ids_ref((node_id,)),
                "status": "passed",
                "collected": 1,
                "passed": 1,
                "skipped": 0,
                "failed": 0,
                "errors": 0,
            }
        )
    )


def test_ordinary_local_resume_skips_only_identity_valid_evidence(monkeypatch, tmp_path):
    evidence_root, node_id, shard = _configure_local_run(monkeypatch, tmp_path)
    run_id = "valid-run"
    _write_current_and_shard(
        evidence_root,
        run_id=run_id,
        shard=shard,
        node_id=node_id,
        module_sha256=sha256((tmp_path / shard.module).read_bytes()).hexdigest(),
    )
    invoked_plans = []
    monkeypatch.setattr(cli, "run_ordinary_shards", lambda plan, **_kwargs: invoked_plans.append(plan) or ())

    assert cli.ordinary_local(resume=True, backend_root=tmp_path) == cli.EXIT_SUCCESS
    assert invoked_plans == [()]
    assert json.loads((evidence_root / "current.json").read_text(encoding="utf-8"))["run_id"] == run_id


def test_ordinary_local_resume_reruns_stale_evidence(monkeypatch, tmp_path):
    evidence_root, node_id, shard = _configure_local_run(monkeypatch, tmp_path)
    _write_current_and_shard(
        evidence_root,
        run_id="stale-run",
        shard=shard,
        node_id=node_id,
        module_sha256="0" * 64,
    )
    invoked_plans = []
    monkeypatch.setattr(
        cli,
        "run_ordinary_shards",
        lambda plan, **_kwargs: invoked_plans.append(plan)
        or (ShardRun(shard, ChildResult(("pytest",), 0, ""), {"outcome_path": "unused"}),),
    )
    monkeypatch.setattr(cli, "read_outcome", lambda _path: {"collected": 1, "passed": 1, "skipped": 0, "failed": 0, "errors": 0})

    assert cli.ordinary_local(resume=True, backend_root=tmp_path) == cli.EXIT_SUCCESS
    assert invoked_plans == [(shard,)]


def test_ordinary_local_reports_missing_child_interpreter(monkeypatch, tmp_path):
    _evidence_root, _node_id, _shard = _configure_local_run(monkeypatch, tmp_path)
    monkeypatch.setattr(cli, "run_ordinary_shards", lambda *_args, **_kwargs: (_ for _ in ()).throw(ChildProcessError("managed PostgreSQL child could not start")))

    assert cli.ordinary_local(backend_root=tmp_path) == cli.EXIT_TESTS


@pytest.mark.parametrize(
    ("error", "expected_code"),
    [
        (ChildTimeoutError("ordinary local validation deadline expired"), ChildTimeoutError.code),
        (ChildCancelledError(), ChildCancelledError.code),
    ],
)
def test_ordinary_local_persists_interrupted_shard_on_deadline_or_cancellation(monkeypatch, tmp_path, error, expected_code):
    evidence_root, _node_id, shard = _configure_local_run(monkeypatch, tmp_path)

    def interrupt_run(plan, **kwargs):
        kwargs["on_interrupted"](plan[0])
        raise error

    monkeypatch.setattr(cli, "run_ordinary_shards", interrupt_run)

    assert cli.ordinary_local(backend_root=tmp_path) == expected_code
    current = json.loads((evidence_root / "current.json").read_text(encoding="utf-8"))
    shard_path = evidence_root / "runs" / current["run_id"] / "shards" / f"{sha256(shard.module.encode()).hexdigest()}.json"
    assert json.loads(shard_path.read_text(encoding="utf-8"))["status"] == "interrupted"


def test_ordinary_local_persists_readiness_before_collection(monkeypatch, tmp_path):
    evidence_root, _node_id, shard = _configure_local_run(monkeypatch, tmp_path)
    collected_after_ready = []

    def ready(**kwargs):
        kwargs["record"]({"status": "sample_error", "observed_at": 0})
        kwargs["record"]({"status": "ready", "observed_at": 1})
        return type("Connection", (), {"close": lambda self: None})()

    def collect(**_kwargs):
        observations = sorted((evidence_root / "runs").glob("*/observations/*.json"))
        collected_after_ready.extend(json.loads(path.read_text(encoding="utf-8"))["status"] for path in observations)
        return (shard.node_ids[0],)

    monkeypatch.setattr(cli, "open_local_readiness_target", ready)
    monkeypatch.setattr(cli, "collect_ordinary_node_ids", collect)
    monkeypatch.setattr(cli, "run_ordinary_shards", lambda *_args, **_kwargs: ())

    assert cli.ordinary_local(backend_root=tmp_path) == cli.EXIT_SUCCESS
    assert collected_after_ready == ["sample_error", "ready"]
    current = json.loads((evidence_root / "current.json").read_text(encoding="utf-8"))
    observations = [
        validate_local_evidence(json.loads(path.read_text(encoding="utf-8")))
        for path in sorted((evidence_root / "runs" / current["run_id"] / "observations").glob("*.json"))
    ]
    assert all(record["run_id"] == current["run_id"] for record in observations)


@pytest.mark.parametrize(
    ("error", "expected_code"),
    [
        (cli.DatabaseTargetError(cli.EXIT_POSTGRESQL), cli.EXIT_POSTGRESQL),
        (KeyboardInterrupt(), 130),
    ],
)
def test_ordinary_local_does_not_start_shards_when_readiness_fails(monkeypatch, tmp_path, error, expected_code):
    evidence_root, _node_id, _shard = _configure_local_run(monkeypatch, tmp_path)
    monkeypatch.setattr(cli, "open_local_readiness_target", lambda **_kwargs: (_ for _ in ()).throw(error))
    monkeypatch.setattr(cli, "collect_ordinary_node_ids", lambda **_kwargs: pytest.fail("collection must not start"))

    assert cli.ordinary_local(backend_root=tmp_path) == expected_code
    current = json.loads((evidence_root / "current.json").read_text(encoding="utf-8"))
    run_root = evidence_root / "runs" / current["run_id"]
    assert not (run_root / "shards").exists()
