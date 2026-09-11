#!/usr/bin/env python3
"""Transactional installer core for the approved NIKKE PT-BR runtime loader.

The core owns only three files that are absent from an official installation.
It never patches, replaces or backs up official client files. Compatibility is
checked before install and repair; removal is limited to exact package-owned
hashes so an official update cannot turn an uninstall into an unsafe write.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import tempfile
from typing import Any, Callable, Iterable
import uuid

from runtime_release_package import (
    VerifiedRuntimePackage,
    RuntimePayload,
    sha256_file,
    verify_runtime_package,
)


RELEVANT_PROCESSES = {
    "nikke.exe",
    "nikke_launcher.exe",
    "assistant.exe",
    "startup_runner.exe",
    "ace-service64.exe",
    "ace-setup64.exe",
}
RUNTIME_OUTPUT_DIRECTORY = "NIKKEPTBR-Runtime"
ALLOWED_RUNTIME_OUTPUT_FILES = {"runtime.log"}


class InstallerError(RuntimeError):
    """The requested operation cannot continue safely."""


class InjectedFailure(RuntimeError):
    """Deterministic harness failure that must trigger rollback."""


class SimulatedInterruption(BaseException):
    """Deterministic process interruption that leaves a resumable journal."""


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def atomic_copy(source: Path, destination: Path, expected_hash: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with source.open("rb") as input_stream, os.fdopen(
            descriptor, "wb"
        ) as output_stream:
            shutil.copyfileobj(input_stream, output_stream, length=4 * 1024 * 1024)
            output_stream.flush()
            os.fsync(output_stream.fileno())
        if sha256_file(temporary) != expected_hash:
            raise InstallerError(f"Staged payload hash mismatch: {destination.name}")
        temporary.replace(destination)
        if sha256_file(destination) != expected_hash:
            raise InstallerError(f"Installed payload hash mismatch: {destination.name}")
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InstallerError(f"Cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise InstallerError(f"{label} root must be an object.")
    return value


def running_relevant_processes() -> list[dict[str, Any]]:
    if os.name != "nt":
        return []
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    invalid = ctypes.c_void_p(-1).value
    if snapshot == invalid:
        raise OSError(ctypes.get_last_error(), "CreateToolhelp32Snapshot failed")
    kernel32.Process32FirstW.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(PROCESSENTRY32W),
    ]
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(PROCESSENTRY32W),
    ]
    kernel32.Process32NextW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    result: list[dict[str, Any]] = []
    try:
        available = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while available:
            name = entry.szExeFile
            if name.lower() in RELEVANT_PROCESSES:
                result.append({"name": name, "pid": int(entry.th32ProcessID)})
            available = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    return result


def rva_to_offset(header: bytes, rva: int) -> int:
    if len(header) < 0x40:
        raise InstallerError("GameAssembly PE header is truncated.")
    pe = struct.unpack_from("<I", header, 0x3C)[0]
    coff = pe + 4
    if len(header) < coff + 20:
        raise InstallerError("GameAssembly COFF header is truncated.")
    section_count = struct.unpack_from("<H", header, coff + 2)[0]
    optional_size = struct.unpack_from("<H", header, coff + 16)[0]
    sections = coff + 20 + optional_size
    for index in range(section_count):
        offset = sections + index * 40
        if len(header) < offset + 40:
            raise InstallerError("GameAssembly section table is truncated.")
        virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
            "<IIII", header, offset + 8
        )
        if virtual_address <= rva < virtual_address + max(virtual_size, raw_size):
            return raw_offset + (rva - virtual_address)
    raise InstallerError(f"Target RVA 0x{rva:X} is outside PE sections.")


def new_transaction_id() -> str:
    return (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:12]
    )


class RuntimeInstallerTransaction:
    """Install, verify, repair and remove a verified runtime package."""

    def __init__(
        self,
        *,
        package: VerifiedRuntimePackage,
        target_root: Path,
        state_root: Path,
        allowed_target_parent: Path | None = None,
        forbidden_roots: Iterable[Path] = (),
        process_checker: Callable[[], list[dict[str, Any]]] = running_relevant_processes,
    ) -> None:
        self.package = verify_runtime_package(package.root)
        self.target_root = target_root.resolve(strict=True)
        self.state_root = state_root.resolve(strict=False)
        self.allowed_target_parent = (
            allowed_target_parent.resolve(strict=True)
            if allowed_target_parent is not None
            else None
        )
        self.forbidden_roots = tuple(
            path.resolve(strict=False) for path in forbidden_roots
        )
        self.process_checker = process_checker
        self._validate_roots()
        self.state_root.mkdir(parents=True, exist_ok=True)
        self.state_root = self.state_root.resolve(strict=True)
        self.journal_path = self.state_root / "transaction-journal.json"
        self.installation_state_path = self.state_root / "installation-state.json"
        self.receipts_root = self.state_root / "receipts"
        self.quarantine_root = self.state_root / "quarantine"

    def _validate_roots(self) -> None:
        if not self.target_root.is_dir():
            raise InstallerError("Target root is not a directory.")
        if self.allowed_target_parent is not None and not is_inside(
            self.target_root, self.allowed_target_parent
        ):
            raise InstallerError("Target escaped its explicitly allowed parent.")
        if self.target_root == self.state_root or is_inside(
            self.target_root, self.state_root
        ) or is_inside(self.state_root, self.target_root):
            raise InstallerError("Target and installer state roots must be disjoint.")
        if is_inside(self.package.root, self.target_root):
            raise InstallerError("Package source must remain outside the client root.")
        for forbidden in self.forbidden_roots:
            if self.target_root == forbidden or is_inside(self.target_root, forbidden):
                raise InstallerError("Target is inside a forbidden root.")
            if self.state_root == forbidden or is_inside(self.state_root, forbidden):
                raise InstallerError("Installer state is inside a forbidden root.")

    def _require_processes_closed(self) -> None:
        running = self.process_checker()
        if running:
            raise InstallerError(f"NIKKE processes must be closed: {running}")

    def _payload(self, name: str) -> RuntimePayload:
        for payload in self.package.payloads:
            if payload.name == name:
                return payload
        raise InstallerError(f"Unknown package payload: {name}")

    def _target(self, name: str) -> Path:
        candidate = (self.target_root / name).resolve(strict=False)
        if candidate.parent != self.target_root:
            raise InstallerError("Owned target escaped the client root.")
        return candidate

    def _read_installation_state(self, *, required: bool = False) -> dict[str, Any] | None:
        if not self.installation_state_path.exists():
            if required:
                raise InstallerError("Matching installation state is required.")
            return None
        state = read_json(self.installation_state_path, "installation state")
        if state.get("schema_version") != 1:
            raise InstallerError("Installation state schema mismatch.")
        return state

    def _matching_state(self, state: dict[str, Any] | None) -> bool:
        return bool(
            state
            and state.get("package_id") == self.package.package_id
            and state.get("package_identity_sha256") == self.package.package_identity
            and Path(str(state.get("target_root", ""))).resolve(strict=False)
            == self.target_root
        )

    def _load_journal(self) -> dict[str, Any] | None:
        if not self.journal_path.exists():
            return None
        journal = read_json(self.journal_path, "transaction journal")
        if journal.get("schema_version") != 1:
            raise InstallerError("Transaction journal schema mismatch.")
        if journal.get("package_identity_sha256") != self.package.package_identity:
            raise InstallerError("Pending journal belongs to another package.")
        if Path(str(journal.get("target_root", ""))).resolve(strict=False) != self.target_root:
            raise InstallerError("Pending journal belongs to another target.")
        return journal

    def _save_journal(self, journal: dict[str, Any]) -> None:
        journal["updated_at"] = utc_now()
        atomic_json(self.journal_path, journal)

    def _new_journal(self, operation: str) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "transaction_id": new_transaction_id(),
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "operation": operation,
            "stage": f"{operation}_prepared",
            "package_id": self.package.package_id,
            "package_identity_sha256": self.package.package_identity,
            "target_root": str(self.target_root),
            "official_snapshot": self._verify_client_compatibility(),
            "added": [],
            "repaired": [],
            "removed": [],
            "pre_states": {},
            "quarantine": {},
            "next_action": operation,
        }

    def _critical_contract(self) -> dict[str, dict[str, Any]]:
        records = self.package.manifest["client_compatibility"][
            "critical_official_files"
        ]
        return {str(record["name"]): record for record in records}

    def _verify_client_compatibility(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for name, expected in self._critical_contract().items():
            path = self.target_root / name
            if not path.is_file():
                raise InstallerError(f"Required official client file is missing: {name}")
            actual = {
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            if actual["size"] != int(expected["size"]) or actual["sha256"] != str(
                expected["sha256"]
            ).upper():
                raise InstallerError(
                    f"Unsupported or updated NIKKE client fingerprint: {name}"
                )
            result[name] = actual

        fingerprints = self.package.manifest["client_compatibility"][
            "target_fingerprints"
        ]
        headers: dict[str, bytes] = {}
        for fingerprint in fingerprints:
            name = str(fingerprint["name"])
            module = str(fingerprint["module"])
            path = self.target_root / module
            if module not in result or not path.is_file():
                raise InstallerError(f"Runtime target module is not authorized: {name}")
            if module not in headers:
                with path.open("rb") as stream:
                    headers[module] = stream.read(1024 * 1024)
            rva = int(str(fingerprint["rva"]), 16)
            length = int(fingerprint["length"])
            offset = rva_to_offset(headers[module], rva)
            with path.open("rb") as stream:
                stream.seek(offset)
                target_bytes = stream.read(length)
            if len(target_bytes) != length:
                raise InstallerError(f"Runtime target fingerprint is truncated: {name}")
            actual_target = hashlib.sha256(target_bytes).hexdigest().upper()
            if actual_target != str(fingerprint["bytes_sha256"]).upper():
                raise InstallerError(f"Runtime target fingerprint mismatch: {name}")
        return result

    def _require_official_snapshot(self, expected: dict[str, Any]) -> None:
        if self._verify_client_compatibility() != expected:
            raise InstallerError("Official client snapshot changed during transaction.")

    def _scan_runtime_output(self) -> list[str]:
        output = self.target_root / RUNTIME_OUTPUT_DIRECTORY
        if not output.exists():
            return []
        if not output.is_dir():
            raise InstallerError("Runtime output path is not a directory.")
        unknown = sorted(
            entry.name
            for entry in output.iterdir()
            if not entry.is_file() or entry.name not in ALLOWED_RUNTIME_OUTPUT_FILES
        )
        if unknown:
            raise InstallerError(
                "Runtime output contains unknown entries: " + ", ".join(unknown)
            )
        return sorted(entry.name for entry in output.iterdir())

    def _artifact_states(self) -> dict[str, dict[str, Any]]:
        states: dict[str, dict[str, Any]] = {}
        for payload in self.package.payloads:
            target = self._target(payload.name)
            if not target.exists():
                states[payload.name] = {"state": "missing", "sha256": None}
            elif not target.is_file():
                states[payload.name] = {"state": "unknown", "sha256": None}
            else:
                actual = sha256_file(target)
                states[payload.name] = {
                    "state": "exact" if actual == payload.sha256 else "changed",
                    "sha256": actual,
                }
        return states

    def _write_installation_state(self, status: str) -> dict[str, Any]:
        state = {
            "schema_version": 1,
            "updated_at": utc_now(),
            "status": status,
            "package_id": self.package.package_id,
            "package_identity_sha256": self.package.package_identity,
            "mod_version": self.package.manifest["mod_version"],
            "client_version": self.package.manifest["client_compatibility"]["version"],
            "target_root": str(self.target_root),
            "owned_files": {
                payload.name: {
                    "size": payload.size,
                    "sha256": payload.sha256,
                    "original_state": "absent",
                }
                for payload in self.package.payloads
            },
        }
        atomic_json(self.installation_state_path, state)
        return state

    def _copy_payload(self, payload: RuntimePayload) -> None:
        if sha256_file(payload.source) != payload.sha256:
            raise InstallerError(f"Package payload changed after verification: {payload.name}")
        atomic_copy(payload.source, self._target(payload.name), payload.sha256)

    def _maybe_fault(
        self,
        completed: int,
        *,
        interrupt_after: int | None,
        fail_after: int | None,
    ) -> None:
        if interrupt_after is not None and completed == interrupt_after:
            raise SimulatedInterruption("simulated resumable interruption")
        if fail_after is not None and completed == fail_after:
            raise InjectedFailure("injected transactional failure")

    def _install_rollback(self, journal: dict[str, Any]) -> None:
        for name in reversed(list(journal.get("added", []))):
            payload = self._payload(name)
            target = self._target(name)
            if not target.exists():
                continue
            if not target.is_file() or sha256_file(target) != payload.sha256:
                journal["stage"] = "install_rollback_blocked_unknown_state"
                journal["next_action"] = "manual_inspection_required"
                self._save_journal(journal)
                raise InstallerError(f"Refusing to remove changed owned target: {name}")
            target.unlink()
        self._require_official_snapshot(journal["official_snapshot"])
        journal["stage"] = "install_rolled_back_verified"
        journal["next_action"] = "install"
        self._save_journal(journal)

    def install(
        self,
        *,
        interrupt_after: int | None = None,
        fail_after: int | None = None,
    ) -> dict[str, Any]:
        self._require_processes_closed()
        verify_runtime_package(self.package.root)
        state = self._read_installation_state()
        states = self._artifact_states()
        self._scan_runtime_output()
        if self._matching_state(state) and state.get("status") == "installed":
            if all(record["state"] == "exact" for record in states.values()):
                self._verify_client_compatibility()
                return {"result": "verified_noop", "installed": True, "changed_files": 0}
            raise InstallerError("Installed package requires repair, not install.")

        journal = self._load_journal()
        if journal and journal.get("operation") == "install" and journal.get("stage") == "installing":
            pass
        else:
            if journal and str(journal.get("stage", "")).endswith("_prepared") is False and journal.get("stage") not in {
                "install_rolled_back_verified",
                "removed_verified",
            }:
                raise InstallerError("Another transaction is pending.")
            collisions = [name for name, record in states.items() if record["state"] != "missing"]
            if collisions:
                raise InstallerError(
                    "Unknown existing mod targets; refusing overwrite: " + ", ".join(collisions)
                )
            output = self.target_root / RUNTIME_OUTPUT_DIRECTORY
            if output.exists():
                raise InstallerError("Runtime output collision; refusing install.")
            journal = self._new_journal("install")
            journal["stage"] = "installing"
            journal["next_action"] = "resume_install_or_rollback"
            self._save_journal(journal)

        completed = len(journal.get("added", []))
        try:
            for payload in self.package.payloads:
                target = self._target(payload.name)
                if target.exists():
                    if not target.is_file() or sha256_file(target) != payload.sha256:
                        raise InstallerError(
                            f"Unexpected target state during install: {payload.name}"
                        )
                    if payload.name not in journal["added"]:
                        journal["added"].append(payload.name)
                        self._save_journal(journal)
                    continue
                self._copy_payload(payload)
                journal["added"].append(payload.name)
                completed += 1
                self._save_journal(journal)
                self._maybe_fault(
                    completed,
                    interrupt_after=interrupt_after,
                    fail_after=fail_after,
                )
            self._require_official_snapshot(journal["official_snapshot"])
            self._write_installation_state("installed")
            journal["stage"] = "installed_verified"
            journal["next_action"] = "verify_or_launch"
            self._save_journal(journal)
            return {
                "result": "installed_verified",
                "installed": True,
                "changed_files": len(journal["added"]),
                "transaction_id": journal["transaction_id"],
            }
        except SimulatedInterruption:
            raise
        except Exception as error:
            journal["error"] = str(error)
            self._save_journal(journal)
            self._install_rollback(journal)
            raise

    def verify_installed(self) -> dict[str, Any]:
        official = self._verify_client_compatibility()
        states = self._artifact_states()
        runtime_output = self._scan_runtime_output()
        state = self._read_installation_state(required=True)
        installed = bool(
            self._matching_state(state)
            and state.get("status") == "installed"
            and all(record["state"] == "exact" for record in states.values())
        )
        return {
            "installed": installed,
            "artifact_states": states,
            "runtime_output": runtime_output,
            "official_snapshot": official,
        }

    def _repair_rollback(self, journal: dict[str, Any]) -> None:
        for name, pre in journal.get("pre_states", {}).items():
            payload = self._payload(name)
            target = self._target(name)
            pre_state = pre["state"]
            if pre_state == "exact":
                continue
            if pre_state == "missing":
                if not target.exists():
                    continue
                if not target.is_file() or sha256_file(target) != payload.sha256:
                    journal["stage"] = "repair_rollback_blocked_unknown_state"
                    journal["next_action"] = "manual_inspection_required"
                    self._save_journal(journal)
                    raise InstallerError(f"Cannot roll back changed repair target: {name}")
                target.unlink()
            elif pre_state == "changed":
                quarantine_record = journal["quarantine"].get(name)
                if not quarantine_record:
                    raise InstallerError(f"Missing repair quarantine record: {name}")
                source = Path(quarantine_record["path"])
                if not source.is_file() or sha256_file(source) != quarantine_record["sha256"]:
                    raise InstallerError(f"Repair quarantine is invalid: {name}")
                if target.is_file() and sha256_file(target) == quarantine_record["sha256"]:
                    continue
                if target.exists() and (
                    not target.is_file() or sha256_file(target) != payload.sha256
                ):
                    journal["stage"] = "repair_rollback_blocked_unknown_state"
                    journal["next_action"] = "manual_inspection_required"
                    self._save_journal(journal)
                    raise InstallerError(f"Cannot roll back changed repair target: {name}")
                atomic_copy(source, target, quarantine_record["sha256"])
        self._require_official_snapshot(journal["official_snapshot"])
        self._write_installation_state("installed")
        journal["stage"] = "repair_rolled_back_verified"
        journal["next_action"] = "repair"
        self._save_journal(journal)

    def repair(
        self,
        *,
        interrupt_after: int | None = None,
        fail_after: int | None = None,
    ) -> dict[str, Any]:
        self._require_processes_closed()
        verify_runtime_package(self.package.root)
        state = self._read_installation_state(required=True)
        if not self._matching_state(state) or state.get("status") != "installed":
            raise InstallerError("Repair requires a matching installed package state.")
        self._scan_runtime_output()
        journal = self._load_journal()
        if journal and journal.get("operation") == "repair" and journal.get("stage") == "repairing":
            pass
        else:
            if journal and journal.get("stage") not in {
                "installed_verified",
                "repair_rolled_back_verified",
                "repair_verified",
            }:
                raise InstallerError("Another transaction is pending.")
            journal = self._new_journal("repair")
            journal["stage"] = "repairing"
            states = self._artifact_states()
            journal["pre_states"] = states
            tx_quarantine = self.quarantine_root / journal["transaction_id"]
            for name, record in states.items():
                if record["state"] != "changed":
                    continue
                source = self._target(name)
                destination = tx_quarantine / name
                atomic_copy(source, destination, str(record["sha256"]))
                journal["quarantine"][name] = {
                    "path": str(destination),
                    "sha256": record["sha256"],
                    "size": source.stat().st_size,
                }
            journal["next_action"] = "resume_repair_or_rollback"
            self._save_journal(journal)

        completed = len(journal.get("repaired", []))
        try:
            for payload in self.package.payloads:
                target = self._target(payload.name)
                exact = target.is_file() and sha256_file(target) == payload.sha256
                if exact:
                    continue
                if target.exists() and not target.is_file():
                    raise InstallerError(f"Repair target is not a file: {payload.name}")
                self._copy_payload(payload)
                if payload.name not in journal["repaired"]:
                    journal["repaired"].append(payload.name)
                completed += 1
                self._save_journal(journal)
                self._maybe_fault(
                    completed,
                    interrupt_after=interrupt_after,
                    fail_after=fail_after,
                )
            self._require_official_snapshot(journal["official_snapshot"])
            self._write_installation_state("installed")
            journal["stage"] = "repair_verified"
            journal["next_action"] = "verify_or_launch"
            self._save_journal(journal)
            return {
                "result": "repair_verified",
                "installed": True,
                "changed_files": len(journal["repaired"]),
                "transaction_id": journal["transaction_id"],
            }
        except SimulatedInterruption:
            raise
        except Exception as error:
            journal["error"] = str(error)
            self._save_journal(journal)
            self._repair_rollback(journal)
            raise

    def _preserve_runtime_log(self, transaction_id: str) -> list[dict[str, Any]]:
        output = self.target_root / RUNTIME_OUTPUT_DIRECTORY
        entries = self._scan_runtime_output()
        if not entries:
            return []
        evidence_root = self.receipts_root / transaction_id / "runtime-evidence"
        evidence_root.mkdir(parents=True, exist_ok=True)
        preserved: list[dict[str, Any]] = []
        for name in entries:
            source = output / name
            destination = evidence_root / name
            shutil.copy2(source, destination)
            preserved.append(
                {
                    "name": name,
                    "path": str(destination),
                    "size": source.stat().st_size,
                    "sha256": sha256_file(source),
                }
            )
        return preserved

    def _remove_rollback(self, journal: dict[str, Any]) -> None:
        for name in journal.get("removed", []):
            payload = self._payload(name)
            target = self._target(name)
            if target.exists():
                if not target.is_file() or sha256_file(target) != payload.sha256:
                    raise InstallerError(f"Cannot restore removed target safely: {name}")
                continue
            self._copy_payload(payload)
        self._write_installation_state("installed")
        journal["stage"] = "remove_rolled_back_to_installed"
        journal["next_action"] = "remove"
        self._save_journal(journal)

    def remove(
        self,
        *,
        interrupt_after: int | None = None,
        fail_after: int | None = None,
    ) -> dict[str, Any]:
        self._require_processes_closed()
        state = self._read_installation_state()
        states = self._artifact_states()
        if self._matching_state(state) and state.get("status") == "removed":
            if all(record["state"] == "missing" for record in states.values()):
                return {"result": "verified_noop", "removed": True, "changed_files": 0}
        if not self._matching_state(state) or state.get("status") != "installed":
            raise InstallerError("Removal requires a matching installed package state.")
        unknown = [
            name for name, record in states.items() if record["state"] not in {"exact", "missing"}
        ]
        if unknown:
            raise InstallerError(
                "Refusing to remove changed owned targets: " + ", ".join(unknown)
            )
        self._scan_runtime_output()

        journal = self._load_journal()
        if journal and journal.get("operation") == "remove" and journal.get("stage") == "removing":
            pass
        else:
            if journal and journal.get("stage") not in {
                "installed_verified",
                "repair_verified",
                "remove_rolled_back_to_installed",
            }:
                raise InstallerError("Another transaction is pending.")
            journal = self._new_journal("remove")
            journal["stage"] = "removing"
            journal["runtime_evidence"] = self._preserve_runtime_log(
                journal["transaction_id"]
            )
            journal["next_action"] = "resume_remove_or_rollback"
            self._save_journal(journal)

        completed = len(journal.get("removed", []))
        try:
            for payload in self.package.payloads:
                target = self._target(payload.name)
                if not target.exists():
                    continue
                if not target.is_file() or sha256_file(target) != payload.sha256:
                    raise InstallerError(
                        f"Owned target changed during removal: {payload.name}"
                    )
                target.unlink()
                if payload.name not in journal["removed"]:
                    journal["removed"].append(payload.name)
                completed += 1
                self._save_journal(journal)
                self._maybe_fault(
                    completed,
                    interrupt_after=interrupt_after,
                    fail_after=fail_after,
                )
            output = self.target_root / RUNTIME_OUTPUT_DIRECTORY
            if output.exists():
                for name in self._scan_runtime_output():
                    (output / name).unlink()
                if not any(output.iterdir()):
                    output.rmdir()
            self._write_installation_state("removed")
            journal["stage"] = "removed_verified"
            journal["next_action"] = "install"
            self._save_journal(journal)
            return {
                "result": "removed_verified",
                "removed": True,
                "changed_files": len(journal["removed"]),
                "runtime_evidence": journal.get("runtime_evidence", []),
                "transaction_id": journal["transaction_id"],
            }
        except SimulatedInterruption:
            raise
        except Exception as error:
            journal["error"] = str(error)
            self._save_journal(journal)
            self._remove_rollback(journal)
            raise

    def rollback_pending(self) -> dict[str, Any]:
        self._require_processes_closed()
        journal = self._load_journal()
        if not journal:
            return {"result": "no_pending_transaction"}
        stage = str(journal.get("stage"))
        if journal.get("operation") == "install" and stage == "installing":
            self._install_rollback(journal)
        elif journal.get("operation") == "repair" and stage == "repairing":
            self._repair_rollback(journal)
        elif journal.get("operation") == "remove" and stage == "removing":
            self._remove_rollback(journal)
        else:
            return {"result": "no_pending_transaction", "stage": stage}
        return {"result": "rollback_verified", "stage": journal["stage"]}

    def verify_removed(self) -> dict[str, Any]:
        states = self._artifact_states()
        state = self._read_installation_state(required=True)
        output = self.target_root / RUNTIME_OUTPUT_DIRECTORY
        removed = bool(
            self._matching_state(state)
            and state.get("status") == "removed"
            and all(record["state"] == "missing" for record in states.values())
            and not output.exists()
        )
        return {
            "removed": removed,
            "artifact_states": states,
            "runtime_output_exists": output.exists(),
        }
