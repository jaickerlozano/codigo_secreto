"""Fail-closed pytest evidence and validation orchestration contracts."""

from contextlib import contextmanager
from types import SimpleNamespace

from core.managed_postgresql_runtime import cli, evidence, pytest_plugin
from core.managed_postgresql_runtime import runner
from core.managed_postgresql_runtime.runner import ChildResult


@contextmanager
def held_lock(_connection):
    yield


def successful_stage(stage, **_kwargs):
    return ChildResult((stage,), 0, "completed")


def configure_validate(monkeypatch, tmp_path, run_stage=successful_stage):
    connection = type("Connection", (), {"closed": False, "close": lambda self: setattr(self, "closed", True)})()
    evidence = []
    monkeypatch.setattr(cli, "open_disposable_target", lambda **_kwargs: connection)
    monkeypatch.setattr(cli, "advisory_lock", held_lock)
    monkeypatch.setattr(cli, "run_stage", run_stage)
    monkeypatch.setattr(cli, "write_evidence", lambda _path, payload: evidence.append(payload))
    monkeypatch.setattr(cli, "database_url_from_environment", lambda _env: "postgresql://operator:secret@db.invalid/validation")
    return connection, evidence, tmp_path / "result.json"


def configure_ordinary(monkeypatch, tmp_path, run_stage=successful_stage):
    connection = type("Connection", (), {"closed": False, "close": lambda self: setattr(self, "closed", True)})()
    published = []
    node_ids = tuple(f"core/tests/test_runtime.py::test_runtime_{index}" for index in range(1, 4))
    shard = runner.Shard("core/tests/test_runtime.py", node_ids)

    def run_shards(_plan, *, outcome_directory, **kwargs):
        outcome_path = tmp_path / "ordinary-shard.json"
        child = run_stage("ordinary", environment={**kwargs["environment"], pytest_plugin.PYTEST_RESULT_PATH_ENV: str(outcome_path)})
        outcome = pytest_plugin.read_outcome(outcome_path)
        if outcome is not None:
            pytest_plugin.write_outcome(outcome_path, **outcome, node_ref=runner.node_ids_ref(node_ids))
        return (runner.ShardRun(shard, child, {"outcome_path": str(outcome_path)}),)

    monkeypatch.setattr(cli, "open_release_target", lambda: connection)
    monkeypatch.setattr(cli, "collect_ordinary_node_ids", lambda **_kwargs: node_ids)
    monkeypatch.setattr(cli, "build_shard_plan", lambda *_args, **_kwargs: (shard,))
    monkeypatch.setattr(cli, "run_ordinary_shards", run_shards)
    monkeypatch.setattr(cli, "write_evidence", lambda _path, payload: published.append(payload))
    monkeypatch.setattr(cli, "migration_graph_ref", lambda: "graph-ref")
    monkeypatch.setattr(cli, "database_url_from_environment", lambda _env: "postgresql://operator:secret@db.invalid/ordinary")
    return connection, published, tmp_path / "ordinary.json"


def write_pytest_result(kwargs, *, collected=1, passed=1, skipped=0, failed=0, errors=0):
    path = kwargs["environment"][pytest_plugin.PYTEST_RESULT_PATH_ENV]
    pytest_plugin.write_outcome(
        path,
        collected=collected,
        passed=passed,
        skipped=skipped,
        failed=failed,
        errors=errors,
    )


def test_validate_full_success(monkeypatch, tmp_path):
    connection, evidence, result_path = configure_validate(
        monkeypatch,
        tmp_path,
        run_stage=lambda stage, **kwargs: (write_pytest_result(kwargs) if stage in {"ordinary", "pg_only"} else None) or successful_stage(stage),
    )

    assert cli.validate(acknowledged=True, result_path=result_path) == cli.EXIT_SUCCESS
    assert [stage["name"] for stage in evidence[0]["stages"]] == ["migrate", "drift", "ordinary", "pg_only"]
    assert evidence[0]["status"] == "passed"
    assert connection.closed is True


def test_validate_migration_failure_exits_5(monkeypatch, tmp_path):
    _connection, evidence, result_path = configure_validate(
        monkeypatch,
        tmp_path,
        run_stage=lambda stage, **_kwargs: ChildResult((stage,), 1 if stage == "migrate" else 0, "failed"),
    )

    assert cli.validate(acknowledged=True, result_path=result_path) == cli.EXIT_MIGRATION
    assert evidence[0]["stages"][-1] == {"code": cli.EXIT_MIGRATION, "name": "migrate", "status": "failed"}


def test_validate_drift_failure_exits_5(monkeypatch, tmp_path):
    _connection, evidence, result_path = configure_validate(
        monkeypatch,
        tmp_path,
        run_stage=lambda stage, **_kwargs: ChildResult((stage,), 1 if stage == "drift" else 0, "failed"),
    )

    assert cli.validate(acknowledged=True, result_path=result_path) == cli.EXIT_MIGRATION
    assert evidence[0]["stages"][-1]["name"] == "drift"


def test_validate_pg_only_zero_collected_exits_6(monkeypatch, tmp_path):
    _connection, _evidence, result_path = configure_validate(
        monkeypatch,
        tmp_path,
        run_stage=lambda stage, **kwargs: (write_pytest_result(kwargs, collected=0, passed=0) if stage == "pg_only" else write_pytest_result(kwargs) if stage == "ordinary" else None) or successful_stage(stage),
    )

    assert cli.validate(acknowledged=True, result_path=result_path) == cli.EXIT_TESTS


def test_validate_pg_only_skip_exits_6(monkeypatch, tmp_path):
    _connection, _evidence, result_path = configure_validate(
        monkeypatch,
        tmp_path,
        run_stage=lambda stage, **kwargs: (write_pytest_result(kwargs, skipped=1, passed=0) if stage == "pg_only" else write_pytest_result(kwargs) if stage == "ordinary" else None) or successful_stage(stage),
    )

    assert cli.validate(acknowledged=True, result_path=result_path) == cli.EXIT_TESTS


def test_validate_missing_pytest_evidence_exits_6(monkeypatch, tmp_path):
    _connection, _evidence, result_path = configure_validate(
        monkeypatch,
        tmp_path,
        run_stage=lambda stage, **kwargs: (write_pytest_result(kwargs) if stage == "pg_only" else None) or successful_stage(stage),
    )

    assert cli.validate(acknowledged=True, result_path=result_path) == cli.EXIT_TESTS


def test_validate_credential_redacted_in_result(monkeypatch, tmp_path):
    _connection, evidence, result_path = configure_validate(
        monkeypatch,
        tmp_path,
        run_stage=lambda stage, **kwargs: (write_pytest_result(kwargs) if stage in {"ordinary", "pg_only"} else None) or successful_stage(stage),
    )

    cli.validate(acknowledged=True, result_path=result_path)
    assert "secret" not in str(evidence[0])
    assert "postgresql://" not in str(evidence[0])


def test_pg_only_coverage_requires_collected_and_clean_outcomes():
    assert pytest_plugin.pg_only_coverage_complete({"collected": 2, "passed": 2, "skipped": 0, "failed": 0, "errors": 0}) is True
    assert pytest_plugin.pg_only_coverage_complete({"collected": 2, "passed": 1, "skipped": 1, "failed": 0, "errors": 0}) is False


def test_ordinary_validate_runs_only_ordinary_suite_with_correlation_inputs(monkeypatch, tmp_path):
    captured = {}

    def run_ordinary(stage, **kwargs):
        captured.update(kwargs)
        write_pytest_result(kwargs, collected=3, passed=3)
        return successful_stage(stage)

    connection, published, result_path = configure_ordinary(monkeypatch, tmp_path, run_stage=run_ordinary)

    assert cli.ordinary_validate(release_id="release-1", result_path=result_path) == cli.EXIT_SUCCESS
    assert pytest_plugin.RUNTIME_ENV not in captured["environment"]
    assert published[0]["command"] == "ordinary-validate"
    assert published[0]["release_id"] == "release-1"
    assert published[0]["graph_ref"] == "graph-ref"
    stage = published[0]["stages"][-1]
    assert {key: stage[key] for key in ("name", "status", "code", "collected", "passed", "skipped", "failed", "errors", "shard_count", "expected_collected", "completed_collected")} == {
        "name": "ordinary", "status": "passed", "code": 0, "collected": 3, "passed": 3, "skipped": 0, "failed": 0, "errors": 0,
        "shard_count": 1, "expected_collected": 3, "completed_collected": 3,
    }
    assert len(stage["collection_ref"]) == len(stage["shards_ref"]) == 64
    assert connection.closed is True


def test_ordinary_validate_fails_closed_on_skipped_suite(monkeypatch, tmp_path):
    _connection, published, result_path = configure_ordinary(
        monkeypatch,
        tmp_path,
        run_stage=lambda stage, **kwargs: (write_pytest_result(kwargs, collected=3, passed=2, skipped=1) or successful_stage(stage)),
    )

    assert cli.ordinary_validate(release_id="release-1", result_path=result_path) == cli.EXIT_TESTS
    assert published[0]["status"] == "failed"
    assert published[0]["stages"][-1]["name"] == "ordinary"


def test_ordinary_timeout_publishes_redacted_shard_identity(monkeypatch, tmp_path):
    _connection, published, result_path = configure_ordinary(monkeypatch, tmp_path)
    process = SimpleNamespace(pid=4321)

    def communicate(timeout=None):
        if timeout is not None:
            raise runner.subprocess.TimeoutExpired("pytest", timeout, output="postgresql://operator:secret@db.invalid/ordinary")
        return "", None

    process.communicate = communicate
    monkeypatch.setattr(
        cli,
        "run_ordinary_shards",
        lambda plan, **kwargs: runner.run_ordinary_shards(
            plan, popen=lambda *_args, **_kwargs: process, kill_process_group=lambda *_args: None, **kwargs
        ),
    )

    assert cli.ordinary_validate(release_id="release-1", result_path=result_path) == cli.EXIT_LOCK
    assert published[0]["stages"] == [{
        "name": "ordinary", "status": "failed", "code": cli.EXIT_LOCK,
        "shard_index": 1, "shard_module": "core/tests/test_runtime.py",
    }]
    assert "secret" not in str(published[0])


def test_ordinary_failure_publishes_redacted_shard_identity(monkeypatch, tmp_path):
    def failed_ordinary(_stage, **kwargs):
        write_pytest_result(kwargs, collected=3, passed=2, failed=1)
        return runner.ChildResult(("pytest",), 1, "postgresql://operator:secret@db.invalid/ordinary")

    connection, published, result_path = configure_ordinary(monkeypatch, tmp_path, run_stage=failed_ordinary)

    assert cli.ordinary_validate(release_id="release-1", result_path=result_path) == cli.EXIT_TESTS
    assert published[0]["stages"] == [{
        "name": "ordinary", "status": "failed", "code": cli.EXIT_TESTS,
        "shard_index": 1, "shard_module": "core/tests/test_runtime.py",
    }]
    assert "secret" not in str(published[0])
    assert connection.closed is True


def test_ordinary_profile_reader_rejects_managed_stages(tmp_path):
    ordinary_path = tmp_path / "ordinary.json"
    managed_path = tmp_path / "managed.json"
    ordinary_payload = cli._result_payload(
        status="passed",
        code=cli.EXIT_SUCCESS,
        command="ordinary-validate",
        release_id="release-1",
        graph_ref="a" * 64,
        database_url="postgresql://operator:secret@db.invalid/ordinary",
        stages=[cli._stage("ordinary", "passed", cli.EXIT_SUCCESS, {
            "collected": 1, "passed": 1, "skipped": 0, "failed": 0, "errors": 0,
            "shard_count": 1, "expected_collected": 1, "completed_collected": 1,
            "collection_ref": "a" * 64, "shards_ref": "b" * 64,
        })],
    )
    managed_payload = {**ordinary_payload, "stages": [cli._stage("migrate", "passed", cli.EXIT_SUCCESS)]}
    evidence.write_evidence(ordinary_path, ordinary_payload)
    evidence.write_evidence(managed_path, managed_payload)

    assert evidence.read_profile_evidence(ordinary_path, command="ordinary-validate", stage_names=("ordinary",)) == ordinary_payload
    assert evidence.read_profile_evidence(managed_path, command="ordinary-validate", stage_names=("ordinary",)) is None


def test_node_id_digest_coverage_proof_rejects_overlaps_and_gaps():
    expected = [
        "apps/orders/tests/test_checkout.py::test_checkout",
        "core/tests/test_runtime.py::test_runtime",
    ]
    plan = (
        runner.Shard("apps/orders/tests/test_checkout.py", (expected[0],)),
        runner.Shard("core/tests/test_runtime.py", (expected[0],)),
    )
    outcome = {
        "collected": 1,
        "passed": 1,
        "skipped": 0,
        "failed": 0,
        "errors": 0,
        "node_ref": runner.node_ids_ref((expected[0],)),
    }

    assert runner.aggregate_ordinary_shards(
        expected,
        [runner.ShardRun(shard, successful_stage("ordinary"), outcome) for shard in plan],
    ) is None


def test_aggregate_evidence_passes_only_on_exact_set_equality():
    shard = runner.Shard("core/tests/test_runtime.py", ("core/tests/test_runtime.py::test_runtime",))
    clean = {
        "collected": 1,
        "passed": 1,
        "skipped": 0,
        "failed": 0,
        "errors": 0,
        "node_ref": runner.node_ids_ref(shard.node_ids),
    }

    assert runner.aggregate_ordinary_shards(
        list(shard.node_ids),
        [runner.ShardRun(shard, successful_stage("ordinary"), clean)],
    )["completed_collected"] == 1
    for invalid in ({**clean, "passed": 0}, {**clean, "skipped": 1, "passed": 0}, {**clean, "collected": 0, "passed": 0}):
        assert runner.aggregate_ordinary_shards(
            list(shard.node_ids),
            [runner.ShardRun(shard, successful_stage("ordinary"), invalid)],
        ) is None


def test_ordinary_validate_publishes_only_bounded_shard_aggregate(monkeypatch, tmp_path):
    node_id = "core/tests/test_runtime.py::test_runtime"
    shard = runner.Shard("core/tests/test_runtime.py", (node_id,))
    aggregate = {
        "collected": 1,
        "passed": 1,
        "skipped": 0,
        "failed": 0,
        "errors": 0,
        "shard_count": 1,
        "expected_collected": 1,
        "completed_collected": 1,
        "collection_ref": runner.node_ids_ref((node_id,)),
        "shards_ref": "a" * 64,
    }
    connection, published, result_path = configure_ordinary(monkeypatch, tmp_path)
    monkeypatch.setattr(cli, "collect_ordinary_node_ids", lambda **_kwargs: (node_id,))
    monkeypatch.setattr(cli, "build_shard_plan", lambda *_args, **_kwargs: (shard,))
    monkeypatch.setattr(
        cli,
        "run_ordinary_shards",
        lambda *_args, **_kwargs: (runner.ShardRun(shard, successful_stage("ordinary"), {"outcome_path": "temporary"}),),
    )
    monkeypatch.setattr(cli, "read_outcome", lambda _path: {"node_ref": runner.node_ids_ref((node_id,)), "collected": 1, "passed": 1, "skipped": 0, "failed": 0, "errors": 0})
    monkeypatch.setattr(cli, "aggregate_ordinary_shards", lambda *_args: aggregate)

    assert cli.ordinary_validate(release_id="release-1", result_path=result_path) == cli.EXIT_SUCCESS
    assert published[0]["stages"] == [{"name": "ordinary", "status": "passed", "code": 0, **aggregate}]
    assert connection.closed is True
    assert "temporary" not in str(published[0])


def test_ordinary_evidence_rejects_invalid_aggregate(tmp_path):
    payload = cli._result_payload(
        status="passed",
        code=0,
        command="ordinary-validate",
        release_id="release-1",
        graph_ref="a" * 64,
        database_url="postgresql://operator:secret@db.invalid/ordinary",
        stages=[
            {
                "name": "ordinary",
                "status": "passed",
                "code": 0,
                "collected": 1,
                "passed": 1,
                "skipped": 0,
                "failed": 0,
                "errors": 0,
                "shard_count": 1,
                "expected_collected": 1,
                "completed_collected": 1,
                "collection_ref": "not-a-digest",
                "shards_ref": "a" * 64,
            }
        ],
    )
    path = tmp_path / "ordinary.json"
    evidence.write_evidence(path, payload)

    assert evidence.read_profile_evidence(path, command="ordinary-validate", stage_names=("ordinary",)) is None


def test_ordinary_evidence_rejects_raw_child_output(tmp_path):
    payload = cli._result_payload(
        status="passed",
        code=0,
        command="ordinary-validate",
        release_id="release-1",
        graph_ref="a" * 64,
        database_url="postgresql://operator:secret@db.invalid/ordinary",
        stages=[{
            "name": "ordinary", "status": "passed", "code": 0,
            "collected": 1, "passed": 1, "skipped": 0, "failed": 0, "errors": 0,
            "shard_count": 1, "expected_collected": 1, "completed_collected": 1,
            "collection_ref": "a" * 64, "shards_ref": "b" * 64,
            "output": "postgresql://operator:secret@db.invalid/ordinary",
        }],
    )
    path = tmp_path / "ordinary.json"
    evidence.write_evidence(path, payload)

    assert evidence.read_profile_evidence(path, command="ordinary-validate", stage_names=("ordinary",)) is None


def test_pytest_plugin_records_the_sorted_node_id_digest(monkeypatch, tmp_path):
    result_path = tmp_path / "outcome.json"
    session = SimpleNamespace(config=SimpleNamespace(), items=[SimpleNamespace(nodeid="core/tests/test_b.py::test_b"), SimpleNamespace(nodeid="core/tests/test_a.py::test_a")])
    monkeypatch.setenv(pytest_plugin.PYTEST_RESULT_PATH_ENV, str(result_path))

    pytest_plugin.pytest_collection_finish(session)
    pytest_plugin.pytest_sessionfinish(session, 0)

    assert pytest_plugin.read_outcome(result_path)["node_ref"] == runner.node_ids_ref(
        ["core/tests/test_a.py::test_a", "core/tests/test_b.py::test_b"]
    )
