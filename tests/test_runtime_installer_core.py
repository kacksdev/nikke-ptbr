from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from runtime_installer_core import (  # noqa: E402
    InjectedFailure,
    InstallerError,
    RuntimeInstallerTransaction,
    SimulatedInterruption,
)
from runtime_release_package import (  # noqa: E402
    compile_runtime_package,
    verify_runtime_package,
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def synthetic_gameassembly(primary: bytes, legacy: bytes) -> bytes:
    data = bytearray(0x9000)
    pe_offset = 0x80
    coff = pe_offset + 4
    optional_size = 0xF0
    section = coff + 20 + optional_size
    struct.pack_into("<I", data, 0x3C, pe_offset)
    data[pe_offset : pe_offset + 4] = b"PE\0\0"
    struct.pack_into("<H", data, coff + 2, 1)
    struct.pack_into("<H", data, coff + 16, optional_size)
    data[section : section + 8] = b".text\0\0\0"
    struct.pack_into("<IIII", data, section + 8, 0x8000, 0x1000, 0x8000, 0x200)
    data[0x434 : 0x434 + len(primary)] = primary
    data[0x4878 : 0x4878 + len(legacy)] = legacy
    return bytes(data)


class InstallerFixture:
    def __init__(self, root: Path, *, mismatched_target: str | None = None) -> None:
        self.root = root
        self.packages = root / "packages"
        self.packages.mkdir()
        self.build = root / "build"
        self.build.mkdir()
        self.evidence_root = root / "evidence"
        self.evidence_root.mkdir()
        self.targets = root / "targets"
        self.targets.mkdir()
        self.target = self.targets / "game"
        self.target.mkdir()
        self.state = root / "state"
        self.artifacts = {
            "winhttp.dll": self.build / "winhttp.dll",
            "NIKKEPTBR-Runtime.dll": self.build / "NIKKEPTBR-Runtime.dll",
            "NIKKEPTBR-Runtime.idx": self.build / "NIKKEPTBR-Runtime.idx",
        }
        for index, (name, path) in enumerate(self.artifacts.items(), start=1):
            path.write_bytes((f"payload-{name}".encode("ascii") + b"\0") * index)
        self.evidence = {"runtime_acceptance": self.evidence_root / "acceptance.json"}
        self.evidence["runtime_acceptance"].write_text(
            json.dumps({"status": "approved"}), encoding="utf-8"
        )
        primary_target = b"P" * 32
        legacy_target = b"L" * 32
        official_files = {
            "nikke.exe": b"synthetic official nikke executable",
            "UnityPlayer.dll": b"synthetic official unity player",
            "GameAssembly.dll": synthetic_gameassembly(primary_target, legacy_target),
        }
        for name, content in official_files.items():
            (self.target / name).write_bytes(content)
        self.critical = {
            name: {"size": len(content), "sha256": digest(content)}
            for name, content in official_files.items()
        }
        self.fingerprints = {
            "primary_table_key_lookup": {
                "module": "GameAssembly.dll",
                "rva": "0x1234",
                "length": 32,
                "bytes_sha256": digest(primary_target),
            },
            "legacy_unity_ui_text_setter": {
                "module": "GameAssembly.dll",
                "rva": "0x5678",
                "length": 32,
                "bytes_sha256": digest(legacy_target),
            },
        }
        if mismatched_target is not None:
            self.fingerprints[mismatched_target]["bytes_sha256"] = digest(
                f"wrong-{mismatched_target}".encode("ascii")
            )
        self.snapshot = {
            name: {"size": record["size"], "sha256": record["sha256"]}
            for name, record in self.critical.items()
        }
        self.package_root = self.packages / "candidate"
        compile_runtime_package(
            package_id="nikke-ptbr-runtime-private-v1",
            mod_version="0.1.0",
            output_root=self.package_root,
            allowed_output_parent=self.packages,
            artifact_sources=self.artifacts,
            evidence_files=self.evidence,
            client_version="150.6.9",
            critical_files=self.critical,
            target_fingerprints=self.fingerprints,
            runtime_catalog={
                "sha256": digest(b"catalog"),
                "translated_occurrences": 533785,
                "translated_units": 427399,
                "source_tables": 34,
                "identity": ["source_table", "source_key", "original_source_text"],
                "fail_open": True,
            },
        )
        self.package = verify_runtime_package(self.package_root)

    def transaction(self, *, state: Path | None = None) -> RuntimeInstallerTransaction:
        transaction = RuntimeInstallerTransaction(
            package=self.package,
            target_root=self.target,
            state_root=state or self.state,
            allowed_target_parent=self.targets,
            process_checker=lambda: [],
        )
        return transaction


class RuntimeInstallerCoreTests(unittest.TestCase):
    def test_both_runtime_target_fingerprints_are_required_before_write(self) -> None:
        for target_name in (
            "primary_table_key_lookup",
            "legacy_unity_ui_text_setter",
        ):
            with self.subTest(target_name=target_name), tempfile.TemporaryDirectory() as temporary:
                fixture = InstallerFixture(
                    Path(temporary), mismatched_target=target_name
                )
                with self.assertRaisesRegex(
                    InstallerError,
                    f"Runtime target fingerprint mismatch: {target_name}",
                ):
                    fixture.transaction().install()
                self.assertTrue(
                    all(
                        not (fixture.target / name).exists()
                        for name in fixture.artifacts
                    )
                )

    def test_updated_official_client_is_rejected_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = InstallerFixture(Path(temporary))
            (fixture.target / "nikke.exe").write_bytes(b"updated official client")
            with self.assertRaisesRegex(
                InstallerError, "Unsupported or updated NIKKE client fingerprint"
            ):
                fixture.transaction().install()
            self.assertTrue(
                all(not (fixture.target / name).exists() for name in fixture.artifacts)
            )

    def test_full_install_verify_idempotent_remove_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = InstallerFixture(Path(temporary))
            transaction = fixture.transaction()
            installed = transaction.install()
            self.assertEqual(installed["changed_files"], 3)
            self.assertTrue(transaction.verify_installed()["installed"])
            self.assertEqual(transaction.install()["result"], "verified_noop")
            removed = transaction.remove()
            self.assertEqual(removed["changed_files"], 3)
            self.assertTrue(transaction.verify_removed()["removed"])
            self.assertEqual(transaction.remove()["result"], "verified_noop")

    def test_unknown_existing_target_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = InstallerFixture(Path(temporary))
            collision = fixture.target / "winhttp.dll"
            collision.write_bytes(b"another mod")
            with self.assertRaisesRegex(InstallerError, "refusing overwrite"):
                fixture.transaction().install()
            self.assertEqual(collision.read_bytes(), b"another mod")

    def test_install_interruption_resumes_without_recopying_valid_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = InstallerFixture(Path(temporary))
            transaction = fixture.transaction()
            with self.assertRaises(SimulatedInterruption):
                transaction.install(interrupt_after=1)
            first = fixture.target / "winhttp.dll"
            first_hash = hashlib.sha256(first.read_bytes()).hexdigest().upper()
            resumed = transaction.install()
            self.assertEqual(resumed["result"], "installed_verified")
            self.assertEqual(hashlib.sha256(first.read_bytes()).hexdigest().upper(), first_hash)
            self.assertTrue(transaction.verify_installed()["installed"])

    def test_install_failure_rolls_back_all_added_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = InstallerFixture(Path(temporary))
            transaction = fixture.transaction()
            with self.assertRaises(InjectedFailure):
                transaction.install(fail_after=1)
            for name in fixture.artifacts:
                self.assertFalse((fixture.target / name).exists())
            journal = json.loads(transaction.journal_path.read_text(encoding="utf-8"))
            self.assertEqual(journal["stage"], "install_rolled_back_verified")

    def test_repair_missing_and_changed_files_with_quarantine(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = InstallerFixture(Path(temporary))
            transaction = fixture.transaction()
            transaction.install()
            (fixture.target / "winhttp.dll").write_bytes(b"changed after install")
            (fixture.target / "NIKKEPTBR-Runtime.dll").unlink()
            repaired = transaction.repair()
            self.assertEqual(repaired["changed_files"], 2)
            self.assertTrue(transaction.verify_installed()["installed"])
            quarantine = list(transaction.quarantine_root.rglob("winhttp.dll"))
            self.assertEqual(len(quarantine), 1)
            self.assertEqual(quarantine[0].read_bytes(), b"changed after install")

    def test_repair_failure_restores_exact_damaged_pre_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = InstallerFixture(Path(temporary))
            transaction = fixture.transaction()
            transaction.install()
            changed = fixture.target / "winhttp.dll"
            missing = fixture.target / "NIKKEPTBR-Runtime.dll"
            changed.write_bytes(b"user changed bytes")
            missing.unlink()
            with self.assertRaises(InjectedFailure):
                transaction.repair(fail_after=1)
            self.assertEqual(changed.read_bytes(), b"user changed bytes")
            self.assertFalse(missing.exists())
            self.assertEqual(
                json.loads(transaction.journal_path.read_text(encoding="utf-8"))["stage"],
                "repair_rolled_back_verified",
            )
            transaction.repair()
            self.assertTrue(transaction.verify_installed()["installed"])

    def test_remove_interruption_resumes_and_failure_rolls_back(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = InstallerFixture(Path(temporary))
            transaction = fixture.transaction()
            transaction.install()
            with self.assertRaises(SimulatedInterruption):
                transaction.remove(interrupt_after=1)
            self.assertTrue(transaction.remove()["removed"])
            self.assertTrue(transaction.verify_removed()["removed"])

        with tempfile.TemporaryDirectory() as temporary:
            fixture = InstallerFixture(Path(temporary))
            transaction = fixture.transaction()
            transaction.install()
            with self.assertRaises(InjectedFailure):
                transaction.remove(fail_after=1)
            self.assertTrue(transaction.verify_installed()["installed"])

    def test_remove_refuses_changed_owned_target_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = InstallerFixture(Path(temporary))
            transaction = fixture.transaction()
            transaction.install()
            changed = fixture.target / "NIKKEPTBR-Runtime.idx"
            changed.write_bytes(b"changed")
            with self.assertRaisesRegex(InstallerError, "Refusing to remove changed"):
                transaction.remove()
            self.assertTrue((fixture.target / "winhttp.dll").exists())
            self.assertEqual(changed.read_bytes(), b"changed")

    def test_runtime_log_is_preserved_and_unknown_output_blocks_remove(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = InstallerFixture(Path(temporary))
            transaction = fixture.transaction()
            transaction.install()
            output = fixture.target / "NIKKEPTBR-Runtime"
            output.mkdir()
            (output / "runtime.log").write_text("runtime evidence\n", encoding="utf-8")
            removed = transaction.remove()
            self.assertEqual(len(removed["runtime_evidence"]), 1)
            evidence_path = Path(removed["runtime_evidence"][0]["path"])
            self.assertEqual(evidence_path.read_text(encoding="utf-8"), "runtime evidence\n")

        with tempfile.TemporaryDirectory() as temporary:
            fixture = InstallerFixture(Path(temporary))
            transaction = fixture.transaction()
            transaction.install()
            output = fixture.target / "NIKKEPTBR-Runtime"
            output.mkdir()
            (output / "unknown.bin").write_bytes(b"unknown")
            with self.assertRaisesRegex(InstallerError, "unknown entries"):
                transaction.remove()
            for payload in fixture.package.payloads:
                target = fixture.target / payload.name
                self.assertTrue(target.is_file())
                self.assertEqual(
                    hashlib.sha256(target.read_bytes()).hexdigest().upper(),
                    payload.sha256,
                )

    def test_state_root_must_remain_outside_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = InstallerFixture(Path(temporary))
            with self.assertRaisesRegex(InstallerError, "disjoint"):
                fixture.transaction(state=fixture.target / "state")


if __name__ == "__main__":
    unittest.main()
