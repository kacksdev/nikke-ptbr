from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Iterable


FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def atomic_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def source_files(root: Path, prefix: str) -> Iterable[tuple[str, Path]]:
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().lower()):
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            yield f"{prefix}/{relative}", path


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 0
    info.external_attr = 0o644 << 16
    return info


def metadata_source(*, zip_hash: str, zip_size: int, build_id: str) -> bytes:
    source = f'''namespace NIKKEPTBR.Installer
{{
    internal static class BootstrapMetadata
    {{
        public const string ResourceName = "NIKKEPTBR.Bootstrap.zip";
        public const string ExpectedSha256 = "{zip_hash}";
        public const long ExpectedSize = {zip_size};
        public const string BuildId = "{build_id}";
        public const string CoreRelativePath = "core/NIKKEPTBR-Core.exe";
        public const string PackageRelativePath = "package";
    }}
}}
'''
    return source.encode("utf-8")


def build(
    *,
    core_root: Path,
    package_root: Path,
    output: Path,
    metadata_output: Path,
    report_output: Path | None,
) -> dict[str, Any]:
    core_root = core_root.resolve(strict=True)
    package_root = package_root.resolve(strict=True)
    if not (core_root / "NIKKEPTBR-Core.exe").is_file():
        raise RuntimeError("NIKKEPTBR-Core.exe is missing from the frozen core.")
    package_manifest_path = package_root / "NIKKE-PTBR-PACKAGE.json"
    package_manifest = json.loads(package_manifest_path.read_text(encoding="utf-8"))
    package_identity = str(package_manifest["package_identity_sha256"]).upper()

    inputs = [*source_files(core_root, "core"), *source_files(package_root, "package")]
    records = [
        {
            "path": name,
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for name, path in inputs
    ]
    build_id = hashlib.sha256(
        canonical_bytes(
            {
                "schema_version": 1,
                "package_identity_sha256": package_identity,
                "files": records,
            }
        )
    ).hexdigest().upper()[:24]
    manifest = {
        "schema_version": 1,
        "build_id": build_id,
        "package_identity_sha256": package_identity,
        "core_relative_path": "core/NIKKEPTBR-Core.exe",
        "package_relative_path": "package",
        "files": records,
    }
    manifest_bytes = canonical_bytes(manifest) + b"\n"

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
    if temporary.exists():
        temporary.unlink()
    try:
        with zipfile.ZipFile(
            temporary,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
            allowZip64=True,
        ) as archive:
            archive.writestr(zip_info("bootstrap-manifest.json"), manifest_bytes)
            for (name, path), record in zip(inputs, records):
                if name != record["path"]:
                    raise RuntimeError("Bootstrap input ordering changed unexpectedly.")
                archive.writestr(zip_info(name), path.read_bytes())
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()

    zip_hash = sha256_file(output)
    zip_size = output.stat().st_size
    atomic_bytes(
        metadata_output,
        metadata_source(zip_hash=zip_hash, zip_size=zip_size, build_id=build_id),
    )
    report = {
        "schema_version": 1,
        "status": "approved_for_installer_build",
        "build_id": build_id,
        "package_identity_sha256": package_identity,
        "file_count": len(records),
        "uncompressed_bytes": sum(record["size"] for record in records),
        "bootstrap_zip": {
            "path": str(output),
            "size": zip_size,
            "sha256": zip_hash,
        },
        "metadata_source": {
            "path": str(metadata_output),
            "size": metadata_output.stat().st_size,
            "sha256": sha256_file(metadata_output),
        },
    }
    if report_output is not None:
        atomic_bytes(report_output, json.dumps(report, indent=2).encode("utf-8") + b"\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic embedded installer bootstrap")
    parser.add_argument("--core-root", required=True, type=Path)
    parser.add_argument("--package-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--metadata-output", required=True, type=Path)
    parser.add_argument("--report-output", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                core_root=args.core_root,
                package_root=args.package_root,
                output=args.output,
                metadata_output=args.metadata_output,
                report_output=args.report_output,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
