"""S12: offline-only installer tests; all Game.exe and map files are fixtures."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))

import sinnoh_s12_installer as s12
from install_sinnoh_qa_copy import verify
from test_sinnoh_qa_install import fixture, PROFILE


class S12PrivateInstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sinnoh-s12-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.game, self.overlay, self.source_spec = fixture(self.root)
        self.spec = self.root / ".blue-work/sinnoh-qa-spec.json"
        self.spec.write_text(json.dumps(self.source_spec, ensure_ascii=False),
                             encoding="utf-8")
        self.target = self.root / ".blue-work/game-sinnoh-qa-abcdef123456"

    def plan(self, *, install=False, spec=None, overlay=None):
        return s12.execute(
            self.root, overlay=self.overlay if overlay is None else overlay,
            spec=self.spec if spec is None else spec, do_install=install,
            token=PROFILE)

    def source_hashes(self):
        return {
            f.relative_to(self.game).as_posix():
            hashlib.sha256(f.read_bytes()).hexdigest()
            for f in self.game.rglob("*") if f.is_file()
        }

    def test_preflight_default_is_read_only_and_no_native_approval(self):
        before = self.source_hashes()
        out = self.plan()
        self.assertEqual(out["status"], "DRY_RUN_VALIDATED_NOT_INSTALLED")
        self.assertFalse(out["created"])
        self.assertIsNone(out["qa_directory"])
        self.assertFalse(out["game_exe_executed"])
        self.assertFalse(out["joiplay_executed"])
        self.assertFalse(out["native_gameplay_verified"])
        self.assertFalse(out["native_qa_approved"])
        self.assertFalse(out["main_game_or_user_saves_modified"])
        self.assertFalse(out["save_migration"])
        self.assertFalse(self.target.exists())
        self.assertEqual(before, self.source_hashes())

    def test_auto_discovery_needs_one_hashed_overlay_and_local_spec(self):
        overlay, spec = s12.select_auto(self.root)
        self.assertEqual(overlay, self.overlay)
        self.assertEqual(spec, self.spec)
        self.assertEqual(s12.existing_qa(self.root), [])

    def test_installs_private_copy_only_with_nonplayable_compile_request(self):
        before = self.source_hashes()
        out = self.plan(install=True)
        self.assertEqual(out["status"], "PRIVATE_QA_INSTALLED_NATIVE_COMPILATION_PENDING")
        self.assertTrue(out["created"])
        self.assertTrue(out["save_namespace_verified"])
        self.assertTrue(out["compile_request_pending"])
        self.assertTrue(out["verified_file_hashes"])
        self.assertEqual(Path(out["qa_directory"]), self.target)
        self.assertTrue((self.target / "Game.exe").is_file())
        self.assertTrue((self.target / "Data/blue-sinnoh-qa-compile-request.txt").is_file())
        self.assertFalse((self.target / "Data/blue-sinnoh-qa-compiled.txt").exists())
        self.assertFalse((self.target / "Data/blue-sinnoh-rival-ready.txt").exists())
        self.assertFalse((self.target / "Saves/File A.rxdata").exists())
        self.assertFalse((self.target / "Data/File A.rxdata").exists())
        report = verify(self.target, project=self.root)
        self.assertFalse(report["playable_approved"])
        self.assertFalse(report["native_save_reload_verified"])
        self.assertEqual(before, self.source_hashes())

    def test_second_install_must_not_overwrite_first_qa_or_saves(self):
        self.plan(install=True)
        marker = self.target / "Saves/my-private-save.bin"
        marker.parent.mkdir(exist_ok=True)
        marker.write_bytes(b"DO NOT TOUCH NEW PRIVATE SAVE")
        with self.assertRaisesRegex(ValueError, "ja existe copia"):
            self.plan(install=True)
        self.assertEqual(marker.read_bytes(), b"DO NOT TOUCH NEW PRIVATE SAVE")
        self.assertEqual(len(s12.existing_qa(self.root)), 1)

    def test_auto_selector_rejects_missing_spec_and_missing_overlay(self):
        self.spec.unlink()
        with self.assertRaisesRegex(ValueError, "especificacao privada"):
            s12.select_auto(self.root)
        self.spec.write_text(json.dumps(self.source_spec), encoding="utf-8")
        (self.overlay / "sinnoh-qa-overlay-report.json").unlink()
        with self.assertRaisesRegex(ValueError, "exatamente um overlay"):
            s12.select_auto(self.root)

    def test_auto_selector_rejects_multiple_overlay_candidates(self):
        other = self.root / ".blue-work/second-overlay"
        other.mkdir()
        shutil.copy2(self.overlay / "sinnoh-qa-overlay-report.json",
                     other / "sinnoh-qa-overlay-report.json")
        with self.assertRaisesRegex(ValueError, "exatamente um overlay"):
            s12.select_auto(self.root)

    def test_missing_or_tampered_overlay_does_not_generate_game_maps(self):
        file = self.overlay / "PBS/trainers_sinnoh_barry.txt"
        original = file.read_bytes()
        file.write_bytes(original + b"TAMPER")
        before = self.source_hashes()
        with self.assertRaises(ValueError):
            self.plan(install=True)
        self.assertFalse(self.target.exists())
        self.assertEqual(before, self.source_hashes())

    def test_invented_map_coordinate_fails_closed(self):
        data = json.loads(self.spec.read_text(encoding="utf-8"))
        data["maps"][0]["events"][0]["x"] += 1
        self.spec.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Evento/coordenada"):
            self.plan(install=True)
        self.assertFalse(self.target.exists())

    def test_foreign_region_spec_rejected_and_does_not_modify_main(self):
        data = json.loads(self.spec.read_text(encoding="utf-8"))
        data["region"] = "JOHTO"
        self.spec.write_text(json.dumps(data), encoding="utf-8")
        before = self.source_hashes()
        with self.assertRaisesRegex(ValueError, "nao pertence a Sinnoh"):
            self.plan(install=True)
        self.assertEqual(before, self.source_hashes())

    def test_no_overlay_from_main_game_or_spec_outside_private_workspace(self):
        with self.assertRaises(ValueError):
            self.plan(overlay=self.game, install=True)
        with self.assertRaises(ValueError):
            self.plan(spec=self.root / "outside-spec.json", install=True)
        self.assertFalse(self.target.exists())

    def test_rejects_source_manifest_symlink_without_following(self):
        link = self.root / ".blue-work/sinnoh-qa-link.json"
        try:
            link.symlink_to(self.spec)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks indisponiveis")
        with self.assertRaises(ValueError):
            self.plan(spec=link, install=True)
        self.assertFalse(self.target.exists())

    def test_atomic_install_rolls_back_temporary_copy_if_copy_fails(self):
        before = self.source_hashes()
        # Fail after preflight, inside the existing atomic copy transaction.
        with patch("install_sinnoh_qa_copy.shutil.copy2",
                   side_effect=OSError("SIMULATED COPY FAILURE")):
            with self.assertRaisesRegex(OSError, "SIMULATED COPY FAILURE"):
                self.plan(install=True)
        self.assertEqual(before, self.source_hashes())
        self.assertFalse(self.target.exists())
        self.assertFalse(any(p.name.startswith(".sinnoh-qa-pending-")
                             for p in (self.root / ".blue-work").iterdir()))

    def test_cli_auto_check_does_not_write_private_qa(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            rc = s12.main(["--project", str(self.root), "--auto"])
        self.assertEqual(rc, 0)
        self.assertFalse(json.loads(stream.getvalue())["created"])
        self.assertFalse(self.target.exists())

    def test_cli_auto_install_only_when_opt_in(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            rc = s12.main(["--project", str(self.root), "--auto", "--install"])
        self.assertEqual(rc, 0)
        report = json.loads(stream.getvalue())
        self.assertEqual(report["status"],
                         "PRIVATE_QA_INSTALLED_NATIVE_COMPILATION_PENDING")
        self.assertTrue(self.target.exists())
        self.assertFalse(report["native_qa_approved"])

    def test_cli_missing_overlay_and_spec_blocked_with_no_side_effects(self):
        stream = io.StringIO()
        with contextlib.redirect_stderr(stream):
            rc = s12.main(["--project", str(self.root), "--install"])
        self.assertEqual(rc, 2)
        self.assertIn("SINNOH_S12_BLOQUEADO", stream.getvalue())
        self.assertFalse(self.target.exists())

    def test_batch_installer_is_windows_double_click_and_no_dangerous_fallback(self):
        raw = (ROOT / "SINNOH_INSTALAR_EXPERIMENTAL.bat").read_bytes()
        bat = raw.decode("utf-8")
        self.assertIn(b"\r\n", raw)
        self.assertIn('cd /d "%~dp0"', bat)
        self.assertIn('"scripts\\regions\\sinnoh_s12_installer.py" --auto %SINNOH_MODE%', bat)
        self.assertIn('set "SINNOH_MODE=--install"', bat)
        self.assertIn('--check', bat)
        self.assertIn("DisableDelayedExpansion", bat)
        self.assertNotIn("game\\Game.exe", bat)
        self.assertNotIn("start Game.exe", bat.lower())
        for forbidden in ("powershell", "git clone", "rmdir", "del /q",
                          "pip install", "robocopy", "curl ", "wget "):
            self.assertNotIn(forbidden, bat.lower())


if __name__ == "__main__":
    unittest.main()
