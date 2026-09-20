"""Bounded canonical evidence output for runtime validation."""

import json
import os
import re
import stat
import tempfile
import hashlib
from pathlib import Path, PurePosixPath


EVIDENCE_SCHEMA = "managed-postgresql-result/v1"
LOCAL_EVIDENCE_SCHEMA = "ordinary-local-validation/v1"
MAX_EVIDENCE_BYTES = 64 * 1024
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
LOCAL_RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
LOCAL_EVIDENCE_KINDS = frozenset({"current", "run", "shard", "observation"})
LOCAL_SHARD_FIELDS = frozenset(
    {
        "schema",
        "kind",
        "run_id",
        "timestamp",
        "module",
        "module_sha256",
        "collection_ref",
        "status",
        "collected",
        "passed",
        "skipped",
        "failed",
        "errors",
    }
)


class EvidenceWriteError(ValueError):
    """Raised when evidence cannot meet the bounded output contract."""


class LocalEvidenceError(EvidenceWriteError):
    """Raised when local validation evidence cannot meet its safety contract."""


def canonicalize_evidence(payload):
    """Return the contract's canonical UTF-8 JSON representation."""
    try:
        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8") + b"\n"
    except (TypeError, ValueError) as error:
        raise EvidenceWriteError("evidence must be JSON serializable") from error
    if len(serialized) > MAX_EVIDENCE_BYTES:
        raise EvidenceWriteError("evidence exceeds the 64 KiB contract limit")
    return serialized


def write_evidence(path, payload):
    """Atomically publish canonical evidence with owner-only permissions."""
    destination = Path(path)
    evidence = canonicalize_evidence(payload)
    temporary_path = None
    try:
        descriptor, temporary_path = tempfile.mkstemp(
            dir=destination.parent,
            prefix=f".{destination.name}.",
        )
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as temporary_file:
            temporary_file.write(evidence)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, destination)
        directory_descriptor = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except OSError as error:
        raise EvidenceWriteError("unable to write validation evidence") from error
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)
    return evidence


def validate_local_evidence(payload):
    """Validate the common, privacy-safe local evidence envelope."""
    if not isinstance(payload, dict):
        raise LocalEvidenceError("local evidence must be an object")
    if payload.get("schema") != LOCAL_EVIDENCE_SCHEMA:
        raise LocalEvidenceError("local evidence schema is invalid")
    if payload.get("kind") not in LOCAL_EVIDENCE_KINDS:
        raise LocalEvidenceError("local evidence kind is invalid")
    if not isinstance(payload.get("run_id"), str) or not LOCAL_RUN_ID_PATTERN.fullmatch(payload["run_id"]):
        raise LocalEvidenceError("local evidence run ID is invalid")
    if not isinstance(payload.get("timestamp"), str) or not payload["timestamp"].strip():
        raise LocalEvidenceError("local evidence timestamp is invalid")
    return payload


def module_sha256(module, *, backend_root):
    """Return the SHA-256 identity for a real module below the backend root."""
    relative = PurePosixPath(module)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts or relative.suffix != ".py":
        raise LocalEvidenceError("ordinary shard module is invalid")
    root = Path(backend_root).resolve()
    candidate = root / relative
    try:
        if candidate.is_symlink() or not candidate.resolve().is_relative_to(root):
            raise LocalEvidenceError("ordinary shard module is invalid")
        return hashlib.sha256(candidate.read_bytes()).hexdigest()
    except OSError as error:
        raise LocalEvidenceError("ordinary shard module is unavailable") from error


def shard_resume_eligible(
    payload,
    *,
    run_id,
    module,
    module_sha256,
    collection_ref,
    expected_collected,
):
    """Return whether canonical passed shard evidence can safely be reused."""
    if not isinstance(payload, dict) or set(payload) != LOCAL_SHARD_FIELDS:
        return False
    try:
        validate_local_evidence(payload)
    except LocalEvidenceError:
        return False
    counts = ("collected", "passed", "skipped", "failed", "errors")
    return (
        payload["kind"] == "shard"
        and payload["run_id"] == run_id
        and payload["module"] == module
        and payload["module_sha256"] == module_sha256
        and payload["collection_ref"] == collection_ref
        and all(
            isinstance(payload[field], str) and SHA256_PATTERN.fullmatch(payload[field])
            for field in ("module_sha256", "collection_ref")
        )
        and payload["status"] == "passed"
        and all(isinstance(payload[field], int) for field in counts)
        and payload["collected"] == payload["passed"] == expected_collected > 0
        and all(payload[field] == 0 for field in ("skipped", "failed", "errors"))
    )


class LocalEvidenceStore:
    """Publish local-only evidence below a private, current-user-owned root."""

    def __init__(self, root):
        self.root = Path(root)
        self._ensure_private_directory(self.root)

    @staticmethod
    def _ensure_private_directory(directory):
        try:
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            metadata = directory.lstat()
        except OSError as error:
            raise LocalEvidenceError("local evidence directory is unavailable") from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid():
            raise LocalEvidenceError("local evidence directory is unsafe")
        try:
            os.chmod(directory, 0o700)
        except OSError as error:
            raise LocalEvidenceError("local evidence directory is unavailable") from error

    def _destination(self, relative_path):
        relative = PurePosixPath(relative_path)
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            raise LocalEvidenceError("local evidence path is invalid")
        directory = self.root
        for part in relative.parts[:-1]:
            directory /= part
            self._ensure_private_directory(directory)
        destination = directory / relative.name
        try:
            if destination.is_symlink():
                raise LocalEvidenceError("local evidence path is unsafe")
        except OSError as error:
            raise LocalEvidenceError("local evidence path is unavailable") from error
        return destination

    def write(self, relative_path, payload):
        """Validate and atomically publish one local evidence record."""
        validate_local_evidence(payload)
        destination = self._destination(relative_path)
        try:
            write_evidence(destination, payload)
        except EvidenceWriteError as error:
            raise LocalEvidenceError("local evidence could not be published") from error
        return destination


def _valid_ordinary_aggregate(stage):
    fields = ("collected", "passed", "skipped", "failed", "errors", "shard_count", "expected_collected", "completed_collected")
    allowed = {"name", "status", "code", *fields, "collection_ref", "shards_ref"}
    if set(stage) != allowed or not all(isinstance(stage.get(field), int) for field in fields):
        return False
    if not all(SHA256_PATTERN.fullmatch(stage.get(field, "")) for field in ("collection_ref", "shards_ref")):
        return False
    return (
        stage["shard_count"] > 0
        and stage["expected_collected"] == stage["completed_collected"] == stage["passed"] > 0
        and stage["collected"] == stage["completed_collected"]
        and all(stage[key] == 0 for key in ("skipped", "failed", "errors"))
    )


def read_profile_evidence(path, *, command, stage_names):
    """Return canonical successful evidence only when its stage profile matches."""
    try:
        content = Path(path).read_bytes()
        payload = json.loads(content)
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    try:
        canonical = canonicalize_evidence(payload)
    except EvidenceWriteError:
        return None
    stages = payload.get("stages")
    if canonical != content or not isinstance(stages, list):
        return None
    if (
        payload.get("schema") != EVIDENCE_SCHEMA
        or payload.get("command") != command
        or payload.get("status") != "passed"
        or payload.get("code") != 0
        or not all(isinstance(payload.get(field), str) for field in ("result_id", "release_id", "target_ref", "graph_ref"))
    ):
        return None
    if tuple(stage.get("name") for stage in stages if isinstance(stage, dict)) != tuple(stage_names):
        return None
    if any(stage.get("status") != "passed" or stage.get("code") != 0 for stage in stages):
        return None
    if command == "ordinary-validate" and not _valid_ordinary_aggregate(stages[0]):
        return None
    return payload
