from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


TOOLS = Path(__file__).parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from runtime_release_package import (  # noqa: E402
    PACKAGE_MANIFEST_NAME,
    PackageError,
    compile_runtime_package,
    verify_runtime_package,
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


class RuntimePackageFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.output_parent = root / "packages"
        self.output_parent.mkdir()
        self.build = root / "build"
        self.build.mkdir()
        self.evidence_root = root / "evidence"
        self.evidence_root.mkdir()
        self.artifacts = {
            "winhttp.dll": self.build / "winhttp.dll",
            "NIKKEPTBR-Runtime.dll": self.build / "NIKKEPTBR-Runtime.dll",
            "NIKKEPTBR-Runtime.idx": self.build / "NIKKEPTBR-Runtime.idx",
        }
        for index, (name, path) in enumerate(self.artifacts.items(), start=1):
            path.write_bytes((name.encode("ascii") + b"\0") * index)
        self.evidence = {
            "runtime_acceptance": self.evidence_root / "acceptance.json",
            "offline_validation": self.evidence_root / "offline.json",
        }
        for name, path in self.evidence.items():
            path.write_text(json.dumps({"status": "approved", "name": name}), encoding="utf-8")
        self.critical = {
            "nikke.exe": {"size": 101, "sha256": digest(b"nikke")},
            "UnityPlayer.dll": {"size": 102, "sha256": digest(b"unity")},
            "GameAssembly.dll": {"size": 103, "sha256": digest(b"assembly")},
        }
        self.fingerprints = {
            "primary_table_key_lookup": {
                "module": "GameAssembly.dll",
                "rva": "0x1234",
                "length": 32,
                "bytes_sha256": digest(b"primary-target"),
            },
            "legacy_unity_ui_text_setter": {
                "module": "GameAssembly.dll",
                "rva": "0x5678",
                "length": 32,
                "bytes_sha256": digest(b"legacy-target"),
            },
        }
        self.catalog = {
            "sha256": digest(b"catalog"),
            "translated_occurrences": 533785,
            "translated_units": 427399,
            "source_tables": 34,
            "identity": ["source_table", "source_key", "original_source_text"],
            "fail_open": True,
        }

    @property
    def output(self) -> Path:
        return self.output_parent / "nikke-ptbr-runtime-private-v1"

    def compile(self) -> dict[str, object]:
        return compile_runtime_package(
            package_id="nikke-ptbr-runtime-private-v1",
            mod_version="0.1.0-dev",
            output_root=self.output,
            allowed_output_parent=self.output_parent,
            artifact_sources=self.artifacts,
            evidence_files=self.evidence,
            client_version="150.6.9",
            critical_files=self.critical,
            target_fingerprints=self.fingerprints,
            runtime_catalog=self.catalog,
        )


class RuntimeReleasePackageTests(unittest.TestCase):
    def test_compile_and_verify_closed_three_file_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RuntimePackageFixture(Path(temporary))
            manifest = fixture.compile()
            package = verify_runtime_package(
                fixture.output,
                expected_evidence_files=fixture.evidence,
            )
            self.assertEqual(len(package.payloads), 3)
            self.assertEqual(manifest["schema_version"], 2)
            self.assertEqual(
                [
                    record["name"]
                    for record in manifest["client_compatibility"]["target_fingerprints"]
                ],
                ["primary_table_key_lookup", "legacy_unity_ui_text_setter"],
            )
            self.assertEqual(manifest["payload"]["official_files_included"], 0)
            self.assertTrue(manifest["release_gate"]["private_installable_candidate"])
            self.assertFalse(manifest["release_gate"]["public_distribution_authorized"])

    def test_payload_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RuntimePackageFixture(Path(temporary))
            fixture.compile()
            (fixture.output / "payload" / "NIKKEPTBR-Runtime.idx").write_bytes(b"tampered")
            with self.assertRaisesRegex(PackageError, "Payload size mismatch|Payload hash mismatch"):
                verify_runtime_package(fixture.output)

    def test_extra_and_missing_payload_files_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RuntimePackageFixture(Path(temporary))
            fixture.compile()
            (fixture.output / "payload" / "extra.bin").write_bytes(b"extra")
            with self.assertRaisesRegex(PackageError, "Package file set mismatch"):
                verify_runtime_package(fixture.output)

        with tempfile.TemporaryDirectory() as temporary:
            fixture = RuntimePackageFixture(Path(temporary))
            fixture.compile()
            (fixture.output / "payload" / "winhttp.dll").unlink()
            with self.assertRaisesRegex(PackageError, "Missing package payload"):
                verify_runtime_package(fixture.output)

    def test_external_provenance_change_is_rejected_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RuntimePackageFixture(Path(temporary))
            fixture.compile()
            fixture.evidence["runtime_acceptance"].write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(PackageError, "Provenance size mismatch|Provenance hash mismatch"):
                verify_runtime_package(
                    fixture.output,
                    expected_evidence_files=fixture.evidence,
                )

    def test_manifest_identity_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RuntimePackageFixture(Path(temporary))
            fixture.compile()
            manifest_path = fixture.output / PACKAGE_MANIFEST_NAME
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["mod_version"] = "9.9.9"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PackageError, "Package identity mismatch"):
                verify_runtime_package(fixture.output)

    def test_incomplete_target_fingerprint_contract_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RuntimePackageFixture(Path(temporary))
            del fixture.fingerprints["legacy_unity_ui_text_setter"]
            with self.assertRaisesRegex(PackageError, "fingerprint set"):
                fixture.compile()

    def test_output_must_be_new_and_inside_allowed_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = RuntimePackageFixture(Path(temporary))
            fixture.compile()
            with self.assertRaisesRegex(PackageError, "already exists"):
                fixture.compile()

            outside = fixture.root / "outside"
            with self.assertRaisesRegex(PackageError, "escaped"):
                compile_runtime_package(
                    package_id="outside",
                    mod_version="0.1.0-dev",
                    output_root=outside,
                    allowed_output_parent=fixture.output_parent,
                    artifact_sources=fixture.artifacts,
                    evidence_files=fixture.evidence,
                    client_version="150.6.9",
                    critical_files=fixture.critical,
                    target_fingerprints=fixture.fingerprints,
                    runtime_catalog=fixture.catalog,
                )


if __name__ == "__main__":
    unittest.main()
