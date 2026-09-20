"""Fixed, bounded child-process execution for runtime validation."""

import hashlib
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .exit_codes import EXIT_LOCK
from .evidence import module_sha256, shard_resume_eligible


CHILD_TIMEOUT_SECONDS = 30 * 60
ORDINARY_LOCAL_DEADLINE_SECONDS = 45 * 60
PROCESS_TERMINATION_GRACE_SECONDS = 5
OUTCOME_PLUGIN = "core.managed_postgresql_runtime.outcome_plugin"
STAGE_COMMANDS = {
    "migrate": ("python", "manage.py", "migrate", "--noinput"),
    "drift": ("python", "manage.py", "makemigrations", "--check", "--dry-run"),
    "ordinary": ("python", "-m", "pytest", "-m", "not pg_only"),
    "ordinary_local": (
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "core.managed_postgresql_runtime.outcome_plugin",
        "-m",
        "not pg_only",
    ),
    "pg_only": ("python", "-m", "pytest", "-m", "pg_only"),
    "pending_migrations": ("python", "manage.py", "migrate", "--check"),
    "deploy_check": ("python", "manage.py", "check", "--deploy", "--fail-level", "ERROR"),
}
POSTGRES_URL_PATTERN = re.compile(r"\bpostgres(?:ql)?://[^\s'\";]+", re.IGNORECASE)
PASSWORD_PATTERN = re.compile(r"(?i)(password=)[^\s;]+")


class ChildProcessError(RuntimeError):
    """A requested child stage does not meet the fixed-command contract."""


class ChildTimeoutError(ChildProcessError):
    """A child exceeded its bounded execution time."""

    def __init__(self, message, *, shard_index=None, shard_module=None):
        super().__init__(message)
        self.shard_index = shard_index
        self.shard_module = shard_module

    code = EXIT_LOCK


class ChildCancelledError(ChildProcessError):
    """A local validation child was cancelled after bounded cleanup."""

    def __init__(self, *, shard_index=None, shard_module=None):
        super().__init__("managed PostgreSQL child was cancelled")
        self.shard_index = shard_index
        self.shard_module = shard_module

    code = 130


@dataclass(frozen=True)
class ChildResult:
    """The redacted outcome of a fixed child command."""

    argv: tuple[str, ...]
    returncode: int
    output: str


@dataclass(frozen=True)
class Shard:
    """A deterministic module-level ordinary-suite shard."""

    module: str
    node_ids: tuple[str, ...]


@dataclass(frozen=True)
class ShardRun:
    """One completed shard child and its temporary outcome."""

    shard: Shard
    child: ChildResult
    outcome: dict


def redact_output(value, database_url=None):
    """Remove database credentials and URL-like values from child-facing text."""
    output = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)
    if database_url:
        output = output.replace(database_url, "[REDACTED]")
    output = POSTGRES_URL_PATTERN.sub("[REDACTED]", output)
    return PASSWORD_PATTERN.sub(r"\1[REDACTED]", output)


def node_ids_ref(node_ids):
    """Hash sorted node IDs without exposing them in durable evidence."""
    return hashlib.sha256("\n".join(sorted(node_ids)).encode("utf-8")).hexdigest()


def _module_from_node_id(node_id, backend_root):
    module, separator, _test_name = node_id.partition("::")
    relative = PurePosixPath(module)
    allowed = relative.suffix == ".py" and (
        relative.parts[:2] == ("core", "tests")
        or len(relative.parts) >= 4 and relative.parts[:3] == ("apps", relative.parts[1], "tests")
    )
    if not separator or relative.is_absolute() or ".." in relative.parts or not allowed:
        raise ChildProcessError("ordinary shard selector is invalid")
    root = Path(backend_root).resolve()
    candidate = root / relative
    if candidate.is_symlink() or not candidate.resolve().is_relative_to(root):
        raise ChildProcessError("ordinary shard selector is invalid")
    return relative.as_posix()


def build_shard_plan(node_ids, *, backend_root):
    """Group the collected ordinary nodes by normalized test module."""
    if not node_ids or len(set(node_ids)) != len(node_ids):
        raise ChildProcessError("ordinary shard collection is incomplete")
    groups = {}
    for node_id in node_ids:
        groups.setdefault(_module_from_node_id(node_id, backend_root), []).append(node_id)
    return tuple(Shard(module, tuple(sorted(groups[module]))) for module in sorted(groups))


def _without_neon(environment):
    return {key: value for key, value in dict(environment or {}).items() if "NEON" not in key.upper()}


def ordinary_local_deadline(*, monotonic=time.monotonic):
    """Return the one monotonic 45-minute deadline for local validation."""
    return monotonic() + ORDINARY_LOCAL_DEADLINE_SECONDS


def _reap_process_group(process, *, kill_process_group):
    """Terminate, wait briefly, force-kill only if needed, then reap."""
    kill_process_group(process.pid, signal.SIGTERM)
    try:
        output, _ = process.communicate(timeout=PROCESS_TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        kill_process_group(process.pid, signal.SIGKILL)
        output, _ = process.communicate()
    return output


def _run_child(
    argv,
    *,
    backend_root,
    database_url=None,
    environment=None,
    timeout_seconds=CHILD_TIMEOUT_SECONDS,
    popen=subprocess.Popen,
    kill_process_group=os.killpg,
    shard_index=None,
    shard_module=None,
):
    try:
        process = popen(
            list(argv),
            cwd=backend_root,
            env=dict(environment or {}),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
            shell=False,
        )
        output, _ = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as error:
        output = _reap_process_group(process, kill_process_group=kill_process_group)
        raise ChildTimeoutError(
            redact_output(output or error.output or "", database_url), shard_index=shard_index, shard_module=shard_module
        ) from error
    except KeyboardInterrupt as error:
        _reap_process_group(process, kill_process_group=kill_process_group)
        raise ChildCancelledError(shard_index=shard_index, shard_module=shard_module) from error
    except OSError as error:
        raise ChildProcessError("managed PostgreSQL child could not start") from error
    return ChildResult(tuple(argv), process.returncode, redact_output(output, database_url))


def run_stage(
    stage,
    *,
    backend_root,
    database_url=None,
    environment=None,
    timeout_seconds=CHILD_TIMEOUT_SECONDS,
    popen=subprocess.Popen,
    kill_process_group=os.killpg,
):
    """Run only a declared stage with a closed input and isolated process group."""
    try:
        argv = STAGE_COMMANDS[stage]
    except KeyError as error:
        raise ChildProcessError("managed PostgreSQL child stage is invalid") from error

    return _run_child(
        argv,
        backend_root=backend_root,
        database_url=database_url,
        environment=environment,
        timeout_seconds=timeout_seconds,
        popen=popen,
        kill_process_group=kill_process_group,
    )


def collect_ordinary_node_ids(*, backend_root, database_url=None, environment=None, **kwargs):
    """Collect ordinary node IDs through a bounded, fixed child process."""
    child = _run_child(
        (sys.executable, "-m", "pytest", "--collect-only", "-q", "-m", "not pg_only", "--override-ini", "addopts="),
        backend_root=backend_root,
        database_url=database_url,
        environment=_without_neon(environment),
        **kwargs,
    )
    if child.returncode:
        raise ChildProcessError("ordinary shard collection failed")
    node_ids = tuple(sorted(line.strip() for line in child.output.splitlines() if "::" in line))
    build_shard_plan(node_ids, backend_root=backend_root)
    return node_ids


def resume_pending_shards(plan, *, evidence_by_module, run_id, backend_root, collection_ref=None):
    """Return only shards without valid, passed evidence for this collection."""
    collection_ref = collection_ref or node_ids_ref(node_id for shard in plan for node_id in shard.node_ids)
    pending = []
    for shard in plan:
        record = evidence_by_module.get(shard.module) if isinstance(evidence_by_module, dict) else None
        if not shard_resume_eligible(
            record,
            run_id=run_id,
            module=shard.module,
            module_sha256=module_sha256(shard.module, backend_root=backend_root),
            collection_ref=collection_ref,
            expected_collected=len(shard.node_ids),
        ):
            pending.append(shard)
    return tuple(pending)


def run_ordinary_shards(
    plan,
    *,
    backend_root,
    outcome_directory,
    database_url=None,
    environment=None,
    deadline=None,
    monotonic=time.monotonic,
    on_interrupted=None,
    **kwargs,
):
    """Execute one deterministic pytest module shard at a time."""
    runs = []
    for index, shard in enumerate(plan, start=1):
        child_kwargs = dict(kwargs)
        if deadline is not None:
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise ChildTimeoutError(
                    "ordinary local validation deadline expired",
                    shard_index=index,
                    shard_module=shard.module,
                )
            child_kwargs["timeout_seconds"] = min(child_kwargs.get("timeout_seconds", CHILD_TIMEOUT_SECONDS), remaining)
        outcome_path = Path(outcome_directory) / f"ordinary-shard-{index:04}.json"
        try:
            child = _run_child(
                (sys.executable, "-m", "pytest", "-p", OUTCOME_PLUGIN, shard.module, "-m", "not pg_only", "--override-ini", "addopts=", "--reuse-db"),
                backend_root=backend_root,
                database_url=database_url,
                environment={**_without_neon(environment), "MANAGED_POSTGRESQL_PYTEST_RESULT": str(outcome_path)},
                shard_index=index,
                shard_module=shard.module,
                **child_kwargs,
            )
        except (ChildTimeoutError, ChildCancelledError):
            if on_interrupted is not None:
                on_interrupted(shard)
            raise
        runs.append(ShardRun(shard, child, {"outcome_path": str(outcome_path)}))
    return tuple(runs)


def aggregate_ordinary_shards(expected_node_ids, runs):
    """Return bounded aggregate evidence only for exact clean shard coverage."""
    expected = tuple(sorted(expected_node_ids))
    planned = tuple(node_id for run in runs for node_id in run.shard.node_ids)
    if not expected or len(set(expected)) != len(expected) or tuple(sorted(planned)) != expected:
        return None
    outcomes = [run.outcome for run in runs]
    if any(
        run.child.returncode
        or not isinstance(outcome, dict)
        or set(outcome) != {"collected", "passed", "skipped", "failed", "errors", "node_ref"}
        for run, outcome in zip(runs, outcomes)
    ):
        return None
    if any(outcome["node_ref"] != node_ids_ref(run.shard.node_ids) for run, outcome in zip(runs, outcomes)):
        return None
    counts = {key: sum(outcome[key] for outcome in outcomes) for key in ("collected", "passed", "skipped", "failed", "errors")}
    if any(not isinstance(value, int) for outcome in outcomes for value in outcome.values() if value is not outcome.get("node_ref")):
        return None
    if counts["collected"] != len(expected) or counts["passed"] != len(expected) or any(counts[key] for key in ("skipped", "failed", "errors")):
        return None
    summaries = [f"{run.shard.module}\0{outcome['node_ref']}" for run, outcome in zip(runs, outcomes)]
    return {
        **counts,
        "shard_count": len(runs),
        "expected_collected": len(expected),
        "completed_collected": counts["collected"],
        "collection_ref": node_ids_ref(expected),
        "shards_ref": hashlib.sha256("\n".join(summaries).encode("utf-8")).hexdigest(),
    }
