"""Process-boundary contracts for managed PostgreSQL validation."""

import signal
import subprocess
import sys

import pytest

from core.managed_postgresql_runtime import runner
from core.managed_postgresql_runtime.cli import EXIT_LOCK


class FakeProcess:
    def __init__(self, output, *, returncode=0, timeout=False):
        self.output = output
        self.returncode = returncode
        self.timeout = timeout
        self.pid = 4321
        self.timeouts = []

    def communicate(self, timeout=None):
        self.timeouts.append(timeout)
        if self.timeout and len(self.timeouts) == 1:
            raise subprocess.TimeoutExpired("managed-postgresql-runtime", timeout)
        return self.output, None


def test_fixed_argv_no_shell(tmp_path):
    captured = {}
    process = FakeProcess("migration completed")

    def popen(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return process

    result = runner.run_stage("migrate", backend_root=tmp_path, popen=popen)

    assert result.argv == ("python", "manage.py", "migrate", "--noinput")
    assert captured == {
        "argv": ["python", "manage.py", "migrate", "--noinput"],
        "kwargs": {
            "cwd": tmp_path,
            "env": {},
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "start_new_session": True,
            "shell": False,
        },
    }


def test_fixed_argv_rejects_unknown_stage(tmp_path):
    with pytest.raises(runner.ChildProcessError):
        runner.run_stage("operator-input", backend_root=tmp_path)


def test_ordinary_local_stage_uses_current_python_and_excludes_pg_only(tmp_path):
    captured = {}

    result = runner.run_stage(
        "ordinary_local",
        backend_root=tmp_path,
        popen=lambda argv, **kwargs: captured.update(argv=argv, kwargs=kwargs) or FakeProcess("completed"),
    )

    assert result.argv == (
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "core.managed_postgresql_runtime.outcome_plugin",
        "-m",
        "not pg_only",
    )
    assert captured["argv"] == list(result.argv)


def test_timeout_kills_process_group(tmp_path):
    process = FakeProcess("child timed out", timeout=True)
    killed = []

    with pytest.raises(runner.ChildTimeoutError) as error:
        runner.run_stage(
            "drift",
            backend_root=tmp_path,
            timeout_seconds=1,
            popen=lambda *_args, **_kwargs: process,
            kill_process_group=lambda process_id, signal_number: killed.append(
                (process_id, signal_number)
            ),
        )

    assert error.value.code == EXIT_LOCK
    assert killed == [(4321, signal.SIGTERM)]
    assert process.timeouts == [1, 5]


def test_child_output_redacted(tmp_path):
    database_url = "postgresql://" + "operator:" + "sensitive" + "@db.invalid/validation"
    output = f"failed for {database_url}; password=sensitive"

    result = runner.run_stage(
        "ordinary",
        backend_root=tmp_path,
        database_url=database_url,
        popen=lambda *_args, **_kwargs: FakeProcess(output, returncode=1),
    )

    assert result.returncode == 1
    assert result.output == "failed for [REDACTED]; password=[REDACTED]"
    assert database_url not in result.output
    assert "sensitive" not in result.output


def test_redaction_replaces_url_like_substrings_without_a_known_target():
    output = "connection to postgres://operator:secret@db.invalid/runtime failed"

    assert runner.redact_output(output) == "connection to [REDACTED] failed"


def test_shard_selector_rejects_non_test_and_executable_like_paths(tmp_path):
    safe_module = tmp_path / "apps" / "orders" / "tests" / "test_checkout.py"
    safe_module.parent.mkdir(parents=True)
    safe_module.touch()
    linked_module = tmp_path / "apps" / "orders" / "tests" / "test_link.py"
    linked_module.symlink_to(safe_module)

    plan = runner.build_shard_plan(
        ["apps/orders/tests/test_checkout.py::test_checkout"],
        backend_root=tmp_path,
    )

    assert [shard.module for shard in plan] == ["apps/orders/tests/test_checkout.py"]
    for node_id in (
        "../apps/orders/tests/test_checkout.py::test_checkout",
        "apps/orders/tests/test_link.py::test_checkout",
        "apps/orders/requirements.txt::test_checkout",
        "apps/orders/tests/CMakeLists.txt::test_checkout",
        "apps/orders/tests/README.mdx::test_checkout",
        "apps/orders/tests/README.sh::test_checkout",
    ):
        with pytest.raises(runner.ChildProcessError):
            runner.build_shard_plan([node_id], backend_root=tmp_path)


def test_shards_run_sequentially_with_fixed_argv(tmp_path):
    for module in ("apps/orders/tests/test_checkout.py", "core/tests/test_runtime.py"):
        path = tmp_path / module
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    plan = runner.build_shard_plan(
        [
            "apps/orders/tests/test_checkout.py::test_checkout",
            "core/tests/test_runtime.py::test_runtime",
        ],
        backend_root=tmp_path,
    )
    captured = []
    previous = []

    def popen(argv, **kwargs):
        assert all(process.timeouts for process in previous)
        process = FakeProcess("completed")
        previous.append(process)
        captured.append((argv, kwargs))
        return process

    runs = runner.run_ordinary_shards(
        plan,
        backend_root=tmp_path,
        database_url="postgresql://operator:secret@db.invalid/ordinary",
        environment={"NEON_DATABASE_URL": "must-not-reach-child", "SAFE": "1"},
        outcome_directory=tmp_path,
        popen=popen,
    )

    assert [run.shard.module for run in runs] == ["apps/orders/tests/test_checkout.py", "core/tests/test_runtime.py"]
    assert [argv for argv, _kwargs in captured] == [
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "core.managed_postgresql_runtime.outcome_plugin",
            "apps/orders/tests/test_checkout.py",
            "-m",
            "not pg_only",
            "--override-ini",
            "addopts=",
            "--reuse-db",
        ],
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "core.managed_postgresql_runtime.outcome_plugin",
            "core/tests/test_runtime.py",
            "-m",
            "not pg_only",
            "--override-ini",
            "addopts=",
            "--reuse-db",
        ],
    ]
    assert all(kwargs["cwd"] == tmp_path and kwargs["shell"] is False for _argv, kwargs in captured)
    assert all(kwargs["stdin"] is subprocess.DEVNULL and kwargs["start_new_session"] is True for _argv, kwargs in captured)
    assert all("NEON_DATABASE_URL" not in kwargs["env"] for _argv, kwargs in captured)
    assert all("MANAGED_POSTGRESQL_RUNTIME" not in kwargs["env"] for _argv, kwargs in captured)


def test_shard_timeout_kills_group_and_fails_incomplete(tmp_path):
    for module in ("apps/orders/tests/test_checkout.py", "core/tests/test_runtime.py"):
        path = tmp_path / module
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    plan = runner.build_shard_plan(
        ["apps/orders/tests/test_checkout.py::test_checkout", "core/tests/test_runtime.py::test_runtime"],
        backend_root=tmp_path,
    )
    spawned = []
    killed = []

    with pytest.raises(runner.ChildTimeoutError):
        runner.run_ordinary_shards(
            plan,
            backend_root=tmp_path,
            outcome_directory=tmp_path,
            popen=lambda *_args, **_kwargs: spawned.append(FakeProcess("timeout", timeout=True)) or spawned[-1],
            kill_process_group=lambda process_id, signal_number: killed.append((process_id, signal_number)),
        )

    assert len(spawned) == 1
    assert killed == [(4321, signal.SIGTERM)]


def test_shard_output_and_neon_environment_are_excluded(tmp_path):
    path = tmp_path / "core" / "tests" / "test_runtime.py"
    path.parent.mkdir(parents=True)
    path.touch()
    plan = runner.build_shard_plan(["core/tests/test_runtime.py::test_runtime"], backend_root=tmp_path)
    outcome = {
        "collected": 1,
        "passed": 1,
        "skipped": 0,
        "failed": 0,
        "errors": 0,
        "node_ref": runner.node_ids_ref(plan[0].node_ids),
    }

    aggregate = runner.aggregate_ordinary_shards(
        ["core/tests/test_runtime.py::test_runtime"],
        [runner.ShardRun(plan[0], runner.ChildResult(("pytest",), 0, "postgresql://operator:secret@db.invalid"), outcome)],
    )

    assert aggregate == {
        "collected": 1,
        "passed": 1,
        "skipped": 0,
        "failed": 0,
        "errors": 0,
        "shard_count": 1,
        "expected_collected": 1,
        "completed_collected": 1,
        "collection_ref": runner.node_ids_ref(["core/tests/test_runtime.py::test_runtime"]),
        "shards_ref": aggregate["shards_ref"],
    }
    assert "secret" not in str(aggregate)
    assert "postgresql://" not in str(aggregate)


def test_resume_plan_skips_only_valid_passed_shards(tmp_path):
    first_module = tmp_path / "core" / "tests" / "test_first.py"
    second_module = tmp_path / "core" / "tests" / "test_second.py"
    first_module.parent.mkdir(parents=True)
    first_module.write_text("def test_first(): pass\n", encoding="utf-8")
    second_module.write_text("def test_second(): pass\n", encoding="utf-8")
    plan = runner.build_shard_plan(
        [
            "core/tests/test_first.py::test_first",
            "core/tests/test_second.py::test_second",
        ],
        backend_root=tmp_path,
    )
    collection_ref = runner.node_ids_ref(node_id for shard in plan for node_id in shard.node_ids)
    valid = {
        "schema": "ordinary-local-validation/v1",
        "kind": "shard",
        "run_id": "run-1",
        "timestamp": "2026-09-16T09:00:00Z",
        "module": plan[0].module,
        "module_sha256": runner.module_sha256(plan[0].module, backend_root=tmp_path),
        "collection_ref": collection_ref,
        "status": "passed",
        "collected": 1,
        "passed": 1,
        "skipped": 0,
        "failed": 0,
        "errors": 0,
    }

    pending = runner.resume_pending_shards(
        plan,
        evidence_by_module={plan[0].module: valid, plan[1].module: {**valid, "module": plan[1].module, "status": "failed"}},
        run_id="run-1",
        backend_root=tmp_path,
        collection_ref=collection_ref,
    )

    assert pending == (plan[1],)

    valid_second = {
        **valid,
        "module": plan[1].module,
        "module_sha256": runner.module_sha256(plan[1].module, backend_root=tmp_path),
    }
    for invalid in (
        {**valid_second, "status": "failed"},
        {**valid_second, "status": "interrupted"},
        {**valid_second, "collection_ref": "b" * 64},
        {"status": "passed"},
    ):
        assert runner.resume_pending_shards(
            plan,
            evidence_by_module={plan[0].module: valid, plan[1].module: invalid},
            run_id="run-1",
            backend_root=tmp_path,
            collection_ref=collection_ref,
        ) == (plan[1],)


def test_deadline_prevents_later_shard_launch_and_propagates_remaining_time(tmp_path):
    path = tmp_path / "core" / "tests" / "test_runtime.py"
    path.parent.mkdir(parents=True)
    path.touch()
    plan = runner.build_shard_plan(["core/tests/test_runtime.py::test_runtime"], backend_root=tmp_path)
    started = []

    assert runner.ordinary_local_deadline(monotonic=lambda: 100.0) == 2800.0

    with pytest.raises(runner.ChildTimeoutError):
        runner.run_ordinary_shards(
            plan,
            backend_root=tmp_path,
            outcome_directory=tmp_path,
            deadline=100.0,
            monotonic=lambda: 100.0,
            popen=lambda *_args, **_kwargs: started.append(True),
        )

    assert started == []


def test_cancellation_terminates_waits_kills_reaps_and_reports_interrupted(tmp_path):
    path = tmp_path / "core" / "tests" / "test_runtime.py"
    path.parent.mkdir(parents=True)
    path.touch()
    plan = runner.build_shard_plan(["core/tests/test_runtime.py::test_runtime"], backend_root=tmp_path)
    process = FakeProcess("", timeout=False)
    calls = []

    def communicate(timeout=None):
        calls.append(timeout)
        if len(calls) == 1:
            raise KeyboardInterrupt()
        if timeout == 5:
            raise subprocess.TimeoutExpired("pytest", timeout)
        return "", None

    process.communicate = communicate
    killed = []
    interrupted = []

    with pytest.raises(runner.ChildCancelledError) as error:
        runner.run_ordinary_shards(
            plan,
            backend_root=tmp_path,
            outcome_directory=tmp_path,
            popen=lambda *_args, **_kwargs: process,
            kill_process_group=lambda process_id, signal_number: killed.append((process_id, signal_number)),
            on_interrupted=lambda shard: interrupted.append(shard.module),
        )

    assert error.value.shard_module == "core/tests/test_runtime.py"
    assert killed == [(4321, signal.SIGTERM), (4321, signal.SIGKILL)]
    assert interrupted == ["core/tests/test_runtime.py"]
