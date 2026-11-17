"""S10: tests for an isolated Windows BAT launcher (never start real Game.exe)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import launch_sinnoh_qa as launcher


class SinnohS10LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sinnoh-s10-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / ".blue-work"
        self.work.mkdir()
        self.main_game = self.root / "game"
        self.main_game.mkdir()
        (self.main_game / "Game.exe").write_bytes(b"MAIN MUST NEVER START")

    def make_qa(self, token="abcdef123456"):
        qa = self.work / ("game-sinnoh-qa-" + token)
        qa.mkdir()
        (qa / "Game.exe").write_bytes(b"FAKE FIXTURE - NOT EXECUTABLE")
        return qa

    @staticmethod
    def proof(*, pending=True, ready=False, compiled=False):
        return {
            "region": "SINNOH", "required_launcher_assets_verified": True,
            "compile_request_pending": pending, "compiled_marker_present": compiled,
            "ready_to_launch_for_manual_testing": ready,
            "save_profile_isolated_in_config": True,
            "playable_approved": False,
        }

    def test_missing_qa_fails_closed_and_never_falls_back_to_main(self):
        with patch.object(launcher.subprocess, "Popen") as spawn:
            with self.assertRaisesRegex(ValueError, "ausente"):
                launcher.run_auto(project=self.root, mode="start")
            spawn.assert_not_called()
        self.assertTrue((self.main_game / "Game.exe").exists())

    def test_one_private_qa_is_selected_exactly_without_searching_main(self):
        qa = self.make_qa()
        self.assertEqual(launcher.discover_private_qa(self.root), qa)
        self.assertNotEqual(qa, self.main_game)
        self.assertTrue(str(qa).startswith(str(self.work)))

    def test_multiple_qa_copies_require_explicit_choice(self):
        self.make_qa()
        self.make_qa("000000000001")
        with self.assertRaisesRegex(ValueError, "Multiplas"):
            launcher.discover_private_qa(self.root)

    def test_insecure_names_and_symlinks_rejected(self):
        bogus = self.work / "game-sinnoh-qa-invalid"
        bogus.mkdir()
        with self.assertRaisesRegex(ValueError, "insegura"):
            launcher.discover_private_qa(self.root)
        bogus.rmdir()
        try:
            (self.work / "game-sinnoh-qa-123456abcdef").symlink_to(
                self.main_game, target_is_directory=True)
        except (NotImplementedError, OSError):
            self.skipTest("symlinks indisponiveis")
        with self.assertRaisesRegex(ValueError, "insegura"):
            launcher.discover_private_qa(self.root)

    def test_symlink_work_folder_is_rejected(self):
        self.work.rmdir()
        try:
            self.work.symlink_to(self.main_game, target_is_directory=True)
        except (NotImplementedError, OSError):
            self.skipTest("symlink indisponivel")
        with self.assertRaisesRegex(ValueError, "link simbolico"):
            launcher.discover_private_qa(self.root)

    def test_check_is_read_only_and_never_opens_executable(self):
        self.make_qa()
        with patch.object(launcher, "verify", return_value=self.proof()), patch.object(
            launcher.subprocess, "Popen") as spawn:
            result = launcher.run_auto(project=self.root, mode="check")
        self.assertFalse(result["process_started"])
        self.assertFalse(result["gameplay_approved"])
        self.assertFalse(result["is_main_game"])
        self.assertFalse(result["fallback_to_other_region"])
        self.assertEqual(result["selection_mode"], "private_qa_auto")
        spawn.assert_not_called()

    def test_start_compiles_pending_qa_only_without_shell(self):
        qa = self.make_qa()
        with patch.object(launcher, "verify", return_value=self.proof()), patch.object(
            launcher.subprocess, "Popen", return_value=Mock(pid=321)) as spawn:
            result = launcher.run_auto(project=self.root, mode="start")
        self.assertEqual(result["auto_selected_action"], "compile")
        self.assertEqual(result["requested_action"], "compile")
        self.assertTrue(result["process_started"])
        self.assertFalse(result["gameplay_approved"])
        spawn.assert_called_once_with([str(qa / "Game.exe")], cwd=str(qa), shell=False)
        self.assertEqual((self.main_game / "Game.exe").read_bytes(), b"MAIN MUST NEVER START")

    def test_start_launches_only_after_static_compile_proof(self):
        qa = self.make_qa()
        report = self.proof(pending=False, ready=True, compiled=True)
        with patch.object(launcher, "verify", return_value=report), patch.object(
            launcher.subprocess, "Popen", return_value=Mock(pid=321)) as spawn:
            result = launcher.run_auto(project=self.root, mode="start")
        self.assertEqual(result["auto_selected_action"], "launch")
        self.assertTrue(result["process_started"])
        self.assertFalse(result["gameplay_approved"])
        spawn.assert_called_once_with([str(qa / "Game.exe")], cwd=str(qa), shell=False)

    def test_absent_compile_proof_prevents_launch(self):
        self.make_qa()
        with patch.object(launcher, "verify", return_value=self.proof(
            pending=False, ready=False, compiled=False)), patch.object(
                launcher.subprocess, "Popen") as spawn:
            with self.assertRaisesRegex(ValueError, "bloqueada"):
                launcher.run_auto(project=self.root, mode="start")
            spawn.assert_not_called()

    def test_unverified_assets_cannot_trigger_any_process(self):
        self.make_qa()
        report = self.proof()
        report["required_launcher_assets_verified"] = False
        with patch.object(launcher, "verify", return_value=report), patch.object(
                launcher.subprocess, "Popen") as spawn:
            with self.assertRaisesRegex(ValueError, "Assets"):
                launcher.run_auto(project=self.root, mode="start")
            spawn.assert_not_called()

    def test_tampered_real_qa_manifest_fails_before_process(self):
        self.make_qa()
        # An actual copy needs installer proof and sha256-pinned files.
        with patch.object(launcher.subprocess, "Popen") as spawn:
            with self.assertRaises((ValueError, OSError)):
                launcher.run_auto(project=self.root, mode="start")
            spawn.assert_not_called()

    def test_no_game_exe_even_with_mocked_positive_report(self):
        qa = self.make_qa()
        (qa / "Game.exe").unlink()
        with patch.object(launcher, "verify", return_value=self.proof()), patch.object(
                launcher.subprocess, "Popen") as spawn:
            with self.assertRaisesRegex(ValueError, "Game.exe"):
                launcher.run_auto(project=self.root, mode="start")
            spawn.assert_not_called()

    def test_bat_uses_python_verifier_and_does_not_directly_start_main(self):
        bat = (ROOT / "SINNOH_JOGAR_EXPERIMENTAL.bat").read_text(encoding="utf-8")
        self.assertIn('cd /d "%~dp0"', bat)
        self.assertIn('launch_sinnoh_qa.py" --auto', bat)
        self.assertIn('set "SINNOH_MODE=--start"', bat)
        self.assertIn('--check', bat)
        self.assertIn("DisableDelayedExpansion", bat)
        self.assertNotIn("game\\Game.exe", bat)
        self.assertNotIn("START GAME.EXE", bat.upper())
        for unsafe in ("git clone", "rmdir", "del /q", "xcopy", "robocopy",
                       "pip install", "powershell", "start /b"):
            self.assertNotIn(unsafe, bat.casefold())

    def test_cli_auto_without_qa_returns_blocked_code(self):
        with patch.object(sys, "argv", ["launcher", "--auto", "--start",
                                        "--project", str(self.root)]), patch.object(
                launcher.subprocess, "Popen") as spawn:
            self.assertEqual(launcher.main(), 2)
            spawn.assert_not_called()

    def test_auto_start_rejects_unknown_mode_without_changes(self):
        self.make_qa()
        with self.assertRaisesRegex(ValueError, "invalida"):
            launcher.run_auto(project=self.root, mode="delete")
        self.assertEqual((self.main_game / "Game.exe").read_bytes(), b"MAIN MUST NEVER START")


if __name__ == "__main__":
    unittest.main()
