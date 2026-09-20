"""Foundation contracts for managed PostgreSQL runtime validation."""

import stat
from pathlib import Path

import pytest

from core.managed_postgresql_runtime.cli import (
    EXIT_EVIDENCE,
    EXIT_INPUT,
    EXIT_LOCK,
    EXIT_MIGRATION,
    EXIT_POSTGRESQL,
    EXIT_STARTUP,
    EXIT_SUCCESS,
    EXIT_TESTS,
    EXIT_UNSAFE,
    RELEASE_ID_PATTERN,
)
from core.managed_postgresql_runtime.evidence import (
    EVIDENCE_SCHEMA,
    EvidenceWriteError,
    LOCAL_EVIDENCE_SCHEMA,
    LocalEvidenceError,
    LocalEvidenceStore,
    module_sha256,
    shard_resume_eligible,
    validate_local_evidence,
    write_evidence,
)
from core.settings import _should_read_dotenv


BACKEND_ROOT = Path(__file__).resolve().parents[2]


def test_requirements_declares_the_locked_psycopg_v3_adapter():
    requirements = (BACKEND_ROOT / "requirements.txt").read_text(encoding="utf-8")

    assert "psycopg[binary]==3.2.10" in requirements


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, True), ("1", True), ("0", False)],
)
def test_dotenv_guard_respects_explicit_disable(value, expected):
    assert _should_read_dotenv(value) is expected


def test_exit_codes_defined():
    assert (
        EXIT_SUCCESS,
        EXIT_INPUT,
        EXIT_UNSAFE,
        EXIT_POSTGRESQL,
        EXIT_MIGRATION,
        EXIT_TESTS,
        EXIT_EVIDENCE,
        EXIT_LOCK,
        EXIT_STARTUP,
    ) == (0, 2, 3, 4, 5, 6, 7, 8, 9)


@pytest.mark.parametrize("release_id", ("release-1", "2026.09_06", "A" * 128))
def test_release_id_regex_accepts_contract_values(release_id):
    assert RELEASE_ID_PATTERN.fullmatch(release_id)


@pytest.mark.parametrize("release_id", ("", "has space", "slash/value", "A" * 129))
def test_release_id_regex_rejects_invalid(release_id):
    assert RELEASE_ID_PATTERN.fullmatch(release_id) is None


def test_evidence_schema_version():
    assert EVIDENCE_SCHEMA == "managed-postgresql-result/v1"


def test_evidence_atomic_write(tmp_path):
    result_path = tmp_path / "result.json"
    payload = {"schema": EVIDENCE_SCHEMA, "status": "passed"}

    written = write_evidence(result_path, payload)

    assert written == b'{"schema":"managed-postgresql-result/v1","status":"passed"}\n'
    assert result_path.read_bytes() == written
    assert stat.S_IMODE(result_path.stat().st_mode) == 0o600


def test_evidence_rejects_payloads_larger_than_the_contract(tmp_path):
    with pytest.raises(EvidenceWriteError):
        write_evidence(tmp_path / "oversized.json", {"detail": "x" * 65536})


def test_local_evidence_schema_rejects_missing_or_malformed_common_fields():
    valid = {
        "schema": LOCAL_EVIDENCE_SCHEMA,
        "kind": "run",
        "run_id": "run-1",
        "timestamp": "2026-09-16T09:00:00Z",
    }

    assert validate_local_evidence(valid) == valid
    for invalid in (
        {key: value for key, value in valid.items() if key != "timestamp"},
        {**valid, "schema": EVIDENCE_SCHEMA},
        {**valid, "kind": "unknown"},
        {**valid, "run_id": ""},
        {**valid, "timestamp": 0},
    ):
        with pytest.raises(LocalEvidenceError):
            validate_local_evidence(invalid)


def test_local_evidence_store_enforces_private_modes_and_canonical_records(tmp_path):
    store = LocalEvidenceStore(tmp_path / "evidence")
    payload = {
        "schema": LOCAL_EVIDENCE_SCHEMA,
        "kind": "run",
        "run_id": "run-1",
        "timestamp": "2026-09-16T09:00:00Z",
    }

    record_path = store.write("runs/run-1/run.json", payload)

    assert stat.S_IMODE(store.root.stat().st_mode) == 0o700
    assert stat.S_IMODE(record_path.stat().st_mode) == 0o600
    assert record_path.read_bytes() == (
        b'{"kind":"run","run_id":"run-1","schema":"ordinary-local-validation/v1",'
        b'"timestamp":"2026-09-16T09:00:00Z"}\n'
    )


def test_local_evidence_store_rejects_symlink_and_non_owned_roots(tmp_path, monkeypatch):
    target = tmp_path / "target"
    target.mkdir()
    symlink_root = tmp_path / "evidence-link"
    symlink_root.symlink_to(target, target_is_directory=True)

    with pytest.raises(LocalEvidenceError):
        LocalEvidenceStore(symlink_root)

    root = tmp_path / "evidence"
    root.mkdir()
    monkeypatch.setattr("core.managed_postgresql_runtime.evidence.os.getuid", lambda: -1)

    with pytest.raises(LocalEvidenceError):
        LocalEvidenceStore(root)


def test_resume_evidence_requires_matching_module_and_collection_identity(tmp_path):
    module = tmp_path / "core" / "tests" / "test_runtime.py"
    module.parent.mkdir(parents=True)
    module.write_text("def test_runtime(): pass\n", encoding="utf-8")
    module_hash = module_sha256("core/tests/test_runtime.py", backend_root=tmp_path)
    evidence = {
        "schema": LOCAL_EVIDENCE_SCHEMA,
        "kind": "shard",
        "run_id": "run-1",
        "timestamp": "2026-09-16T09:00:00Z",
        "module": "core/tests/test_runtime.py",
        "module_sha256": module_hash,
        "collection_ref": "a" * 64,
        "status": "passed",
        "collected": 1,
        "passed": 1,
        "skipped": 0,
        "failed": 0,
        "errors": 0,
    }

    assert shard_resume_eligible(
        evidence,
        run_id="run-1",
        module="core/tests/test_runtime.py",
        module_sha256=module_hash,
        collection_ref="a" * 64,
        expected_collected=1,
    ) is True
    assert shard_resume_eligible(
        {**evidence, "module_sha256": "b" * 64},
        run_id="run-1",
        module="core/tests/test_runtime.py",
        module_sha256=module_hash,
        collection_ref="a" * 64,
        expected_collected=1,
    ) is False
    assert shard_resume_eligible(
        {**evidence, "collection_ref": "b" * 64},
        run_id="run-1",
        module="core/tests/test_runtime.py",
        module_sha256=module_hash,
        collection_ref="a" * 64,
        expected_collected=1,
    ) is False
