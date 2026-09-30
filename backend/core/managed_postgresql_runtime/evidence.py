"""Bounded canonical evidence output for runtime validation."""

import ctypes
import hashlib
import json
import os
import re
import stat
import tempfile
from ctypes import wintypes
from functools import lru_cache
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


_OWNER_SECURITY_INFORMATION = 0x00000001
_DACL_SECURITY_INFORMATION = 0x00000004
_PROTECTED_DACL_SECURITY_INFORMATION = 0x80000000
_SE_DACL_PROTECTED = 0x1000
_TOKEN_QUERY = 0x0008
_TOKEN_USER = 1
_ACCESS_ALLOWED_ACE_TYPE = 0
_FILE_ALL_ACCESS = 0x001F01FF
_MOVEFILE_REPLACE_EXISTING = 0x00000001
_MOVEFILE_WRITE_THROUGH = 0x00000008


class _Acl(ctypes.Structure):
    _fields_ = (
        ("revision", wintypes.BYTE),
        ("reserved", wintypes.BYTE),
        ("size", wintypes.WORD),
        ("ace_count", wintypes.WORD),
        ("reserved2", wintypes.WORD),
    )


class _AceHeader(ctypes.Structure):
    _fields_ = (
        ("ace_type", wintypes.BYTE),
        ("ace_flags", wintypes.BYTE),
        ("ace_size", wintypes.WORD),
    )


class _AccessAllowedAce(ctypes.Structure):
    _fields_ = (
        ("header", _AceHeader),
        ("mask", wintypes.DWORD),
        ("sid_start", wintypes.DWORD),
    )


class _SidAndAttributes(ctypes.Structure):
    _fields_ = (("sid", wintypes.LPVOID), ("attributes", wintypes.DWORD))


class _TokenUser(ctypes.Structure):
    _fields_ = (("user", _SidAndAttributes),)


@lru_cache(maxsize=1)
def _windows_api():
    """Return the narrowly configured Windows security and file APIs."""
    if os.name != "nt" or not hasattr(ctypes, "WinDLL"):
        raise OSError("Windows security APIs are unavailable")
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    advapi32.OpenProcessToken.argtypes = (wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE))
    advapi32.OpenProcessToken.restype = wintypes.BOOL
    advapi32.GetTokenInformation.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    )
    advapi32.GetTokenInformation.restype = wintypes.BOOL
    advapi32.ConvertSidToStringSidW.argtypes = (wintypes.LPVOID, ctypes.POINTER(wintypes.LPWSTR))
    advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL
    advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.DWORD),
    )
    advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = wintypes.BOOL
    advapi32.SetFileSecurityW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.LPVOID)
    advapi32.SetFileSecurityW.restype = wintypes.BOOL
    advapi32.GetFileSecurityW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    )
    advapi32.GetFileSecurityW.restype = wintypes.BOOL
    advapi32.GetSecurityDescriptorOwner.argtypes = (
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.BOOL),
    )
    advapi32.GetSecurityDescriptorOwner.restype = wintypes.BOOL
    advapi32.GetSecurityDescriptorDacl.argtypes = (
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.BOOL),
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.BOOL),
    )
    advapi32.GetSecurityDescriptorDacl.restype = wintypes.BOOL
    advapi32.GetSecurityDescriptorControl.argtypes = (
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.WORD),
        ctypes.POINTER(wintypes.DWORD),
    )
    advapi32.GetSecurityDescriptorControl.restype = wintypes.BOOL
    advapi32.GetAce.argtypes = (wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.LPVOID))
    advapi32.GetAce.restype = wintypes.BOOL

    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = (wintypes.HLOCAL,)
    kernel32.LocalFree.restype = wintypes.HLOCAL
    kernel32.MoveFileExW.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD)
    kernel32.MoveFileExW.restype = wintypes.BOOL
    return advapi32, kernel32


def _raise_windows_error():
    raise ctypes.WinError(ctypes.get_last_error())


def _sid_string(advapi32, kernel32, sid):
    value = wintypes.LPWSTR()
    if not advapi32.ConvertSidToStringSidW(sid, ctypes.byref(value)):
        _raise_windows_error()
    try:
        return value.value
    finally:
        kernel32.LocalFree(value)


def _current_windows_sid(advapi32, kernel32):
    token = wintypes.HANDLE()
    if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), _TOKEN_QUERY, ctypes.byref(token)):
        _raise_windows_error()
    try:
        required = wintypes.DWORD()
        advapi32.GetTokenInformation(token, _TOKEN_USER, None, 0, ctypes.byref(required))
        if not required.value:
            _raise_windows_error()
        buffer = ctypes.create_string_buffer(required.value)
        if not advapi32.GetTokenInformation(
            token,
            _TOKEN_USER,
            buffer,
            required.value,
            ctypes.byref(required),
        ):
            _raise_windows_error()
        return _sid_string(advapi32, kernel32, ctypes.cast(buffer, ctypes.POINTER(_TokenUser)).contents.user.sid)
    finally:
        kernel32.CloseHandle(token)


def _read_windows_security_descriptor(path, advapi32):
    security_information = _OWNER_SECURITY_INFORMATION | _DACL_SECURITY_INFORMATION
    required = wintypes.DWORD()
    advapi32.GetFileSecurityW(str(path), security_information, None, 0, ctypes.byref(required))
    if not required.value:
        _raise_windows_error()
    descriptor = ctypes.create_string_buffer(required.value)
    if not advapi32.GetFileSecurityW(
        str(path),
        security_information,
        descriptor,
        required.value,
        ctypes.byref(required),
    ):
        _raise_windows_error()
    return descriptor


def _verify_windows_private_path(path, expected_sid, advapi32, kernel32):
    descriptor = _read_windows_security_descriptor(path, advapi32)
    owner = wintypes.LPVOID()
    owner_defaulted = wintypes.BOOL()
    if not advapi32.GetSecurityDescriptorOwner(descriptor, ctypes.byref(owner), ctypes.byref(owner_defaulted)):
        _raise_windows_error()
    if _sid_string(advapi32, kernel32, owner) != expected_sid:
        raise OSError("Windows evidence owner is not the current user")

    dacl_present = wintypes.BOOL()
    dacl = wintypes.LPVOID()
    dacl_defaulted = wintypes.BOOL()
    if not advapi32.GetSecurityDescriptorDacl(
        descriptor,
        ctypes.byref(dacl_present),
        ctypes.byref(dacl),
        ctypes.byref(dacl_defaulted),
    ):
        _raise_windows_error()
    control = wintypes.WORD()
    revision = wintypes.DWORD()
    if not advapi32.GetSecurityDescriptorControl(descriptor, ctypes.byref(control), ctypes.byref(revision)):
        _raise_windows_error()
    if not dacl_present.value or not dacl.value or dacl_defaulted.value or not control.value & _SE_DACL_PROTECTED:
        raise OSError("Windows evidence DACL is not private")

    acl = ctypes.cast(dacl, ctypes.POINTER(_Acl)).contents
    if acl.ace_count != 1:
        raise OSError("Windows evidence DACL grants additional access")
    ace_pointer = wintypes.LPVOID()
    if not advapi32.GetAce(dacl, 0, ctypes.byref(ace_pointer)):
        _raise_windows_error()
    ace = ctypes.cast(ace_pointer, ctypes.POINTER(_AccessAllowedAce)).contents
    ace_sid = wintypes.LPVOID(ace_pointer.value + _AccessAllowedAce.sid_start.offset)
    if (
        ace.header.ace_type != _ACCESS_ALLOWED_ACE_TYPE
        or ace.header.ace_flags != 0
        or ace.mask != _FILE_ALL_ACCESS
        or _sid_string(advapi32, kernel32, ace_sid) != expected_sid
    ):
        raise OSError("Windows evidence DACL is not private")


def _assert_windows_private_path(path):
    """Prove that a Windows path is owned and accessible only by the current user."""
    advapi32, kernel32 = _windows_api()
    resolved = Path(path).resolve(strict=True)
    current_sid = _current_windows_sid(advapi32, kernel32)
    _verify_windows_private_path(resolved, current_sid, advapi32, kernel32)


def _secure_windows_path(path):
    """Apply and prove a protected current-user-only Windows DACL."""
    advapi32, kernel32 = _windows_api()
    resolved = Path(path).resolve(strict=True)
    current_sid = _current_windows_sid(advapi32, kernel32)
    descriptor = wintypes.LPVOID()
    sddl = f"D:P(A;;FA;;;{current_sid})"
    if not advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW(
        sddl,
        1,
        ctypes.byref(descriptor),
        None,
    ):
        _raise_windows_error()
    try:
        information = _DACL_SECURITY_INFORMATION | _PROTECTED_DACL_SECURITY_INFORMATION
        if not advapi32.SetFileSecurityW(str(resolved), information, descriptor):
            _raise_windows_error()
    finally:
        kernel32.LocalFree(descriptor)
    _verify_windows_private_path(resolved, current_sid, advapi32, kernel32)


def _is_windows():
    return os.name == "nt"


def _is_link_or_reparse(metadata):
    return stat.S_ISLNK(metadata.st_mode) or bool(
        _is_windows()
        and getattr(metadata, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _verify_private_path(path, *, directory):
    metadata = Path(path).lstat()
    expected_type = stat.S_ISDIR if directory else stat.S_ISREG
    if _is_link_or_reparse(metadata) or not expected_type(metadata.st_mode):
        raise OSError("evidence path type is unsafe")
    if _is_windows():
        _assert_windows_private_path(path)
        return
    getuid = getattr(os, "getuid", None)
    expected_mode = 0o700 if directory else 0o600
    if getuid is None or metadata.st_uid != getuid() or stat.S_IMODE(metadata.st_mode) != expected_mode:
        raise OSError("POSIX evidence ownership or mode is unsafe")


def _replace_evidence(source, destination):
    if _is_windows():
        _advapi32, kernel32 = _windows_api()
        flags = _MOVEFILE_REPLACE_EXISTING | _MOVEFILE_WRITE_THROUGH
        if not kernel32.MoveFileExW(str(source), str(destination), flags):
            _raise_windows_error()
        return
    os.replace(source, destination)
    directory_descriptor = os.open(Path(destination).parent, os.O_RDONLY)
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)


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
    """Atomically publish canonical evidence with private platform permissions."""
    destination = Path(path)
    evidence = canonicalize_evidence(payload)
    temporary_path = None
    try:
        descriptor, temporary_path = tempfile.mkstemp(
            dir=destination.parent,
            prefix=f".{destination.name}.",
        )
        if _is_windows():
            _secure_windows_path(temporary_path)
        else:
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as temporary_file:
            temporary_file.write(evidence)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        _replace_evidence(temporary_path, destination)
        temporary_path = None
        _verify_private_path(destination, directory=False)
    except OSError as error:
        raise EvidenceWriteError("unable to write validation evidence") from error
    finally:
        if temporary_path and os.path.exists(temporary_path):
            try:
                os.unlink(temporary_path)
            except OSError:
                pass
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
            if _is_link_or_reparse(metadata) or not stat.S_ISDIR(metadata.st_mode):
                raise LocalEvidenceError("local evidence directory is unsafe")
            if _is_windows():
                _secure_windows_path(directory)
            else:
                getuid = getattr(os, "getuid", None)
                if getuid is None or metadata.st_uid != getuid():
                    raise LocalEvidenceError("local evidence directory is unsafe")
                os.chmod(directory, 0o700)
            _verify_private_path(directory, directory=True)
        except LocalEvidenceError:
            raise
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
