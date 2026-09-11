from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "installer" / "core"))

from runtime_installer_cli import (  # noqa: E402
    attach_journal_progress,
    classify_inspection,
    friendly_error,
)
from tests.test_runtime_installer_core import InstallerFixture  # noqa: E402


class RuntimeInstallerCliTests(unittest.TestCase):
    def test_clean_client_is_reported_as_not_installed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = InstallerFixture(Path(temporary))
            transaction = fixture.transaction()
            inspection = classify_inspection(transaction)
            self.assertEqual(inspection["health"], "not_installed")
            self.assertEqual(inspection["recommended_action"], "install")

    def test_installed_and_damaged_states_are_distinguished(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = InstallerFixture(Path(temporary))
            transaction = fixture.transaction()
            transaction.install()
            installed = classify_inspection(transaction)
            self.assertEqual(installed["health"], "installed_verified")

            (fixture.target / "NIKKEPTBR-Runtime.dll").unlink()
            damaged = classify_inspection(transaction)
            self.assertEqual(damaged["health"], "repair_required")
            self.assertEqual(damaged["recommended_action"], "repair")

    def test_interrupted_install_is_reported_as_resumable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = InstallerFixture(Path(temporary))
            transaction = fixture.transaction()
            events = []
            attach_journal_progress(transaction, events.append)
            with self.assertRaises(BaseException):
                transaction.install(interrupt_after=1)
            inspection = classify_inspection(transaction)
            self.assertEqual(inspection["health"], "recovery_required")
            self.assertEqual(inspection["recommended_action"], "install")
            self.assertTrue(any(event.get("stage") == "installing" for event in events))

    def test_friendly_error_preserves_safe_user_guidance(self) -> None:
        message = friendly_error(RuntimeError("NIKKE processes must be closed: nikke.exe"))
        self.assertIn("Feche o jogo", message)
        collision = friendly_error(RuntimeError("Unknown existing mod targets; refusing overwrite"))
        self.assertIn("recusou sobrescrevê-lo", collision)


if __name__ == "__main__":
    unittest.main()
