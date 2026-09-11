#!/usr/bin/env python3
"""Compile and verify the private NIKKE PT-BR runtime release package.

The package is intentionally self-contained and contains only the three files
owned by the mod. Official client files are fingerprinted as compatibility
dependencies, never copied into the package.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from typing import Any, Mapping


PACKAGE_MANIFEST_NAME = "NIKKE-PTBR-PACKAGE.json"
PACKAGE_STATUS = "private_runtime_release_candidate"
PAYLOAD_DIRECTORY = "payload"
EXPECTED_PAYLOAD_NAMES = (
    "winhttp.dll",
    "NIKKEPTBR-Runtime.dll",
    "NIKKEPTBR-Runtime.idx",
)
EXPECTED_CRITICAL_FILES = (
    "nikke.exe",
    "UnityPlayer.dll",
    "GameAssembly.dll",
)
EXPECTED_TARGET_FINGERPRINT_NAMES = (
    "primary_table_key_lookup",
    "legacy_unity_ui_text_setter",
)
TARGET_FINGERPRINT_LENGTH = 32


class PackageError(RuntimeError):
    """The package failed a closed contract check."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def safe_relative_path(raw: str) -> Path:
    normalized = raw.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if not normalized.strip() or pure.is_absolute():
        raise PackageError(f"Unsafe package path: {raw!r}")
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise PackageError(f"Unsafe package path: {raw!r}")
    return Path(*pure.parts)


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PackageError(f"Cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise PackageError(f"{label} root must be an object.")
    return value


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


def require_file(path: Path, label: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise PackageError(f"Missing {label}: {path}") from error
    if not resolved.is_file():
        raise PackageError(f"{label} is not a regular file: {resolved}")
    return resolved


def package_identity(identity_input: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(identity_input)).hexdigest().upper()


@dataclass(frozen=True)
class RuntimePayload:
    name: str
    source: Path
    size: int
    sha256: str


@dataclass(frozen=True)
class VerifiedRuntimePackage:
    root: Path
    manifest: dict[str, Any]
    payloads: tuple[RuntimePayload, ...]

    @property
    def package_id(self) -> str:
        return str(self.manifest["package_id"])

    @property
    def package_identity(self) -> str:
        return str(self.manifest["package_identity_sha256"])


def _normalize_critical_files(
    critical_files: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if set(critical_files) != set(EXPECTED_CRITICAL_FILES):
        raise PackageError("Critical official file set does not match the contract.")
    normalized: list[dict[str, Any]] = []
    for name in EXPECTED_CRITICAL_FILES:
        record = critical_files[name]
        size = int(record["size"])
        sha256 = str(record["sha256"]).upper()
        if size <= 0 or len(sha256) != 64:
            raise PackageError(f"Invalid critical fingerprint: {name}")
        normalized.append({"name": name, "size": size, "sha256": sha256})
    return normalized


def _normalize_target_fingerprints(
    target_fingerprints: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if set(target_fingerprints) != set(EXPECTED_TARGET_FINGERPRINT_NAMES):
        raise PackageError("Runtime target fingerprint set does not match the contract.")
    normalized: list[dict[str, Any]] = []
    for name in EXPECTED_TARGET_FINGERPRINT_NAMES:
        record = target_fingerprints[name]
        if set(record) != {"module", "rva", "length", "bytes_sha256"}:
            raise PackageError(f"Malformed runtime target fingerprint: {name}")
        module = str(record["module"])
        if module != "GameAssembly.dll":
            raise PackageError(f"Unsupported runtime target module: {name}")
        try:
            rva_value = int(str(record["rva"]), 16)
        except ValueError as error:
            raise PackageError(f"Invalid runtime target RVA: {name}") from error
        if rva_value <= 0:
            raise PackageError(f"Invalid runtime target RVA: {name}")
        length = int(record["length"])
        if length != TARGET_FINGERPRINT_LENGTH:
            raise PackageError(f"Invalid runtime target length: {name}")
        sha256 = str(record["bytes_sha256"]).upper()
        try:
            digest_bytes = bytes.fromhex(sha256)
        except ValueError as error:
            raise PackageError(f"Invalid runtime target fingerprint: {name}") from error
        if len(digest_bytes) != 32:
            raise PackageError(f"Invalid runtime target fingerprint: {name}")
        normalized.append(
            {
                "name": name,
                "module": module,
                "rva": f"0x{rva_value:X}",
                "length": length,
                "bytes_sha256": sha256,
            }
        )
    return normalized


def compile_runtime_package(
    *,
    package_id: str,
    mod_version: str,
    output_root: Path,
    allowed_output_parent: Path,
    artifact_sources: Mapping[str, Path],
    evidence_files: Mapping[str, Path],
    client_version: str,
    critical_files: Mapping[str, Mapping[str, Any]],
    target_fingerprints: Mapping[str, Mapping[str, Any]],
    runtime_catalog: Mapping[str, Any],
) -> dict[str, Any]:
    """Materialize a closed private candidate without touching the client."""

    allowed_output_parent = allowed_output_parent.resolve(strict=True)
    output_root = output_root.resolve(strict=False)
    if not is_inside(output_root, allowed_output_parent) or output_root == allowed_output_parent:
        raise PackageError("Package output escaped its explicitly allowed parent.")
    if output_root.exists():
        raise PackageError(f"Package output already exists: {output_root}")
    if not package_id.strip() or not mod_version.strip():
        raise PackageError("Package id and mod version are required.")
    if set(artifact_sources) != set(EXPECTED_PAYLOAD_NAMES):
        raise PackageError("Runtime artifact set does not match the closed contract.")

    payload_records: list[dict[str, Any]] = []
    resolved_sources: dict[str, Path] = {}
    for name in EXPECTED_PAYLOAD_NAMES:
        source = require_file(Path(artifact_sources[name]), f"runtime artifact {name}")
        resolved_sources[name] = source
        payload_records.append(
            {
                "name": name,
                "path": f"{PAYLOAD_DIRECTORY}/{name}",
                "target": name,
                "size": source.stat().st_size,
                "sha256": sha256_file(source),
                "original_state": "absent",
            }
        )

    provenance: dict[str, dict[str, Any]] = {}
    for logical_name, raw_path in sorted(evidence_files.items()):
        evidence_path = require_file(Path(raw_path), f"provenance {logical_name}")
        provenance[logical_name] = {
            "size": evidence_path.stat().st_size,
            "sha256": sha256_file(evidence_path),
        }
    if not provenance:
        raise PackageError("At least one provenance record is required.")

    critical = _normalize_critical_files(critical_files)
    fingerprints = _normalize_target_fingerprints(target_fingerprints)

    catalog = {
        "sha256": str(runtime_catalog["sha256"]).upper(),
        "translated_occurrences": int(runtime_catalog["translated_occurrences"]),
        "translated_units": int(runtime_catalog["translated_units"]),
        "source_tables": int(runtime_catalog["source_tables"]),
        "identity": list(runtime_catalog["identity"]),
        "fail_open": bool(runtime_catalog["fail_open"]),
    }
    if catalog["translated_occurrences"] <= 0 or catalog["translated_units"] <= 0:
        raise PackageError("Runtime catalog cardinality is invalid.")

    identity_input = {
        "schema_version": 2,
        "package_id": package_id,
        "mod_version": mod_version,
        "client_version": client_version,
        "critical_official_files": critical,
        "target_fingerprints": fingerprints,
        "payload": payload_records,
        "runtime_catalog": catalog,
        "provenance": provenance,
    }
    manifest: dict[str, Any] = {
        "schema_version": 2,
        "generated_at": utc_now(),
        "project": "nikke-ptbr",
        "package_id": package_id,
        "package_identity_sha256": package_identity(identity_input),
        "mod_version": mod_version,
        "status": PACKAGE_STATUS,
        "client_compatibility": {
            "version": client_version,
            "critical_official_files": critical,
            "target_fingerprints": fingerprints,
            "unknown_client_policy": "refuse_install_and_preserve_official_behavior",
        },
        "payload": {
            "files": payload_records,
            "file_count": len(payload_records),
            "bytes": sum(record["size"] for record in payload_records),
            "official_files_included": 0,
        },
        "runtime_catalog": catalog,
        "provenance": provenance,
        "transaction_contract": {
            "owned_targets": list(EXPECTED_PAYLOAD_NAMES),
            "original_state": "all_owned_targets_absent",
            "collision_policy": "refuse_unknown_existing_target",
            "repair_policy": "repair_only_with_matching_installation_state_and_quarantine",
            "remove_policy": "remove_only_exact_owned_payload_hashes",
            "runtime_output_directory": "NIKKEPTBR-Runtime",
            "allowed_runtime_output_files": ["runtime.log"],
        },
        "release_gate": {
            "private_installable_candidate": True,
            "public_distribution_authorized": False,
            "pending": [
                "private package transaction harness",
                "professional installer interface",
                "end-user-equivalent acceptance",
                "documentation and private distribution preparation",
            ],
        },
    }

    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_root.name}.", dir=allowed_output_parent)
    ).resolve(strict=True)
    if not is_inside(staging, allowed_output_parent):
        raise PackageError("Package staging escaped its allowed parent.")
    try:
        payload_root = staging / PAYLOAD_DIRECTORY
        payload_root.mkdir()
        for record in payload_records:
            destination = payload_root / record["name"]
            shutil.copy2(resolved_sources[record["name"]], destination)
            if destination.stat().st_size != record["size"]:
                raise PackageError(f"Payload size mismatch while staging {record['name']}.")
            if sha256_file(destination) != record["sha256"]:
                raise PackageError(f"Payload hash mismatch while staging {record['name']}.")
        atomic_json(staging / PACKAGE_MANIFEST_NAME, manifest)
        staging.replace(output_root)
    except BaseException:
        if staging.exists() and is_inside(staging, allowed_output_parent):
            shutil.rmtree(staging)
        raise
    return manifest


def verify_runtime_package(
    package_root: Path,
    *,
    expected_evidence_files: Mapping[str, Path] | None = None,
) -> VerifiedRuntimePackage:
    package_root = package_root.resolve(strict=True)
    if not package_root.is_dir():
        raise PackageError("Package root is not a directory.")
    manifest_path = require_file(package_root / PACKAGE_MANIFEST_NAME, "package manifest")
    manifest = read_json(manifest_path, "package manifest")
    if manifest.get("schema_version") != 2 or manifest.get("status") != PACKAGE_STATUS:
        raise PackageError("Package status or schema is not approved.")
    if manifest.get("project") != "nikke-ptbr":
        raise PackageError("Package project identity mismatch.")

    compatibility = manifest.get("client_compatibility")
    if not isinstance(compatibility, dict):
        raise PackageError("Missing client compatibility contract.")
    critical_records = compatibility.get("critical_official_files")
    if not isinstance(critical_records, list):
        raise PackageError("Missing critical official fingerprints.")
    critical_map = {
        str(record.get("name")): record
        for record in critical_records
        if isinstance(record, dict)
    }
    _normalize_critical_files(critical_map)
    target_records = compatibility.get("target_fingerprints")
    if not isinstance(target_records, list):
        raise PackageError("Missing runtime target fingerprints.")
    target_map: dict[str, dict[str, Any]] = {}
    for record in target_records:
        if not isinstance(record, dict):
            raise PackageError("Malformed runtime target fingerprint record.")
        name = str(record.get("name"))
        if name in target_map:
            raise PackageError("Duplicate runtime target fingerprint record.")
        target_map[name] = {
            key: value for key, value in record.items() if key != "name"
        }
    normalized_targets = _normalize_target_fingerprints(target_map)
    if target_records != normalized_targets:
        raise PackageError("Runtime target fingerprints are not canonical.")

    payload = manifest.get("payload")
    if not isinstance(payload, dict) or not isinstance(payload.get("files"), list):
        raise PackageError("Missing payload contract.")
    records = payload["files"]
    if len(records) != len(EXPECTED_PAYLOAD_NAMES):
        raise PackageError("Payload cardinality mismatch.")
    payloads: list[RuntimePayload] = []
    declared_files = {PACKAGE_MANIFEST_NAME}
    seen_names: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise PackageError("Malformed payload record.")
        name = str(record.get("name"))
        target = str(record.get("target"))
        relative = safe_relative_path(str(record.get("path")))
        if name not in EXPECTED_PAYLOAD_NAMES or target != name or name in seen_names:
            raise PackageError("Payload target set does not match the closed contract.")
        if relative.as_posix() != f"{PAYLOAD_DIRECTORY}/{name}":
            raise PackageError(f"Unexpected payload path for {name}.")
        if record.get("original_state") != "absent":
            raise PackageError(f"Invalid original-state contract for {name}.")
        source = require_file(package_root / relative, f"package payload {name}")
        expected_size = int(record["size"])
        expected_hash = str(record["sha256"]).upper()
        if source.stat().st_size != expected_size:
            raise PackageError(f"Payload size mismatch: {name}")
        if sha256_file(source) != expected_hash:
            raise PackageError(f"Payload hash mismatch: {name}")
        payloads.append(
            RuntimePayload(name=name, source=source, size=expected_size, sha256=expected_hash)
        )
        declared_files.add(relative.as_posix())
        seen_names.add(name)
    if seen_names != set(EXPECTED_PAYLOAD_NAMES):
        raise PackageError("Payload target set is incomplete.")

    actual_files = {
        path.relative_to(package_root).as_posix()
        for path in package_root.rglob("*")
        if path.is_file()
    }
    if actual_files != declared_files:
        raise PackageError(
            "Package file set mismatch; extra or missing files are not allowed."
        )
    if payload.get("file_count") != len(payloads):
        raise PackageError("Manifest payload count mismatch.")
    if payload.get("bytes") != sum(item.size for item in payloads):
        raise PackageError("Manifest payload byte count mismatch.")
    if payload.get("official_files_included") != 0:
        raise PackageError("Official client files must not be included.")

    catalog = manifest.get("runtime_catalog")
    if not isinstance(catalog, dict):
        raise PackageError("Missing runtime catalog contract.")
    required_catalog = {
        "source_tables": 34,
        "identity": ["source_table", "source_key", "original_source_text"],
        "fail_open": True,
    }
    if any(catalog.get(key) != value for key, value in required_catalog.items()):
        raise PackageError("Runtime catalog contract mismatch.")
    translated_units = int(catalog.get("translated_units", 0))
    translated_occurrences = int(catalog.get("translated_occurrences", 0))
    if translated_units <= 0 or translated_occurrences < translated_units:
        raise PackageError("Runtime catalog cardinality is invalid.")
    catalog_sha256 = str(catalog.get("sha256", "")).upper()
    try:
        catalog_digest = bytes.fromhex(catalog_sha256)
    except ValueError as error:
        raise PackageError("Runtime catalog fingerprint is invalid.") from error
    if len(catalog_digest) != 32:
        raise PackageError("Runtime catalog fingerprint is invalid.")

    provenance = manifest.get("provenance")
    if not isinstance(provenance, dict) or not provenance:
        raise PackageError("Missing package provenance.")
    if expected_evidence_files is not None:
        if set(expected_evidence_files) != set(provenance):
            raise PackageError("Expected provenance set mismatch.")
        for logical_name, raw_path in expected_evidence_files.items():
            evidence = require_file(Path(raw_path), f"provenance {logical_name}")
            record = provenance[logical_name]
            if evidence.stat().st_size != int(record["size"]):
                raise PackageError(f"Provenance size mismatch: {logical_name}")
            if sha256_file(evidence) != str(record["sha256"]).upper():
                raise PackageError(f"Provenance hash mismatch: {logical_name}")

    identity_input = {
        "schema_version": 2,
        "package_id": manifest["package_id"],
        "mod_version": manifest["mod_version"],
        "client_version": compatibility["version"],
        "critical_official_files": critical_records,
        "target_fingerprints": target_records,
        "payload": records,
        "runtime_catalog": catalog,
        "provenance": provenance,
    }
    if package_identity(identity_input) != manifest.get("package_identity_sha256"):
        raise PackageError("Package identity mismatch.")
    release_gate = manifest.get("release_gate", {})
    if release_gate.get("private_installable_candidate") is not True:
        raise PackageError("Private installable candidate gate is closed.")
    if release_gate.get("public_distribution_authorized") is not False:
        raise PackageError("Public distribution state is invalid for this candidate.")

    return VerifiedRuntimePackage(
        root=package_root,
        manifest=manifest,
        payloads=tuple(payloads),
    )
