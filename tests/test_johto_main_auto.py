"""Safety regressions for the non-destructive Johto/Decades readiness hook."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/regions/auto_integrate_johto.py"
SPEC = importlib.util.spec_from_file_location("auto_integrate_johto_test", MODULE)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class AutoJohtoTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.project = Path(self.work.name)
        self.game = self.project / "game"
        self.game.mkdir()

    def test_missing_game_is_safe(self):
        report = mod.integrate(self.project, self.game)
        self.assertEqual("no_game_skipped", report["status"])
        self.assertFalse(report["ready"])
        self.assertFalse((self.game / "Data").exists())

    def test_no_bundle_never_unlocks(self):
        (self.game / "Game.exe").write_bytes(b"sample")
        report = mod.integrate(self.project, self.game)
        self.assertEqual("awaiting_johto_installable_release", report["status"])
        self.assertFalse(report["ready"])
        self.assertFalse((self.game / "Data/blue-johto-start.txt").exists())

    def test_synthetic_offline_bundle_cannot_install(self):
        (self.game / "Game.exe").write_bytes(b"sample")
        package = self.project / mod.BUNDLE_PATHS[0]
        package.parent.mkdir(parents=True)
        with zipfile.ZipFile(package, "w") as archive:
            for name in sorted(mod.OFFLINE_MAPS):
                archive.writestr(name, b"bytes")
            for name in ("Data/MapInfos.rxdata", "Data/Tilesets.rxdata", "johto-offline12-audit.json"):
                archive.writestr(mod.OFFLINE_PREFIX + name, b"metadata")
            archive.writestr(mod.OFFLINE_PREFIX + "johto-stage.json", json.dumps({
                "native_mapinfos_sha256": "0" * 64,
                "native_tilesets_sha256": "1" * 64,
            }))
        sha = hashlib.sha256(package.read_bytes()).hexdigest()
        with patch.object(mod, "ORIGINAL_BUNDLE_SHA256", sha), \
             patch.object(mod, "candidate_bundles", return_value=iter([package])):
            report = mod.integrate(self.project, self.game)
        self.assertEqual("experimental_install_blocked", report["status"])
        self.assertEqual(82, report["bundle"]["map_count"])
        self.assertFalse(report["current_game"]["baseline_compatible"])
        self.assertFalse(report["ready"])
        self.assertFalse((self.game / "Data/blue-johto-install.json").exists())

    def test_johto_map_collisions_require_rebase_not_overwrite(self):
        (self.game / "Data").mkdir()
        (self.game / "Data/MapInfos.rxdata").write_bytes(b"native-mapinfos")
        (self.game / "Data/Tilesets.rxdata").write_bytes(b"native-tilesets")
        (self.game / "Data/Map600.rxdata").write_bytes(b"another-region-map")
        bundle = self.project / "synthetic.zip"
        with zipfile.ZipFile(bundle, "w") as archive:
            archive.writestr(mod.OFFLINE_PREFIX + "johto-stage.json", json.dumps({
                "native_mapinfos_sha256": hashlib.sha256(b"native-mapinfos").hexdigest(),
                "native_tilesets_sha256": hashlib.sha256(b"native-tilesets").hexdigest(),
            }))
        report = mod.inspect_current_baseline(self.game, bundle)
        self.assertTrue(report["rebase_required"])
        self.assertEqual([600], report["map_id_conflicts"])
        self.assertEqual((self.game / "Data/Map600.rxdata").read_bytes(), b"another-region-map")

    def test_download_with_browser_duplicate_suffix_is_detected(self):
        downloads = self.project / "Downloads"
        downloads.mkdir()
        duplicate = downloads / "Johto_Offline_Fase12_Auditoria_Integracao_Privado (2).zip"
        duplicate.write_bytes(b"private-zip")
        with patch.object(mod.Path, "home", return_value=self.project):
            discovered = list(mod.candidate_bundles(self.project))
        self.assertIn(duplicate, discovered)

    def test_invalid_cached_bundle_does_not_hide_valid_download(self):
        (self.game / "Game.exe").write_bytes(b"sample")
        cached = self.project / ".blue-work/johto-offline12-preview.zip"
        cached.parent.mkdir()
        cached.write_bytes(b"invalid")
        original = self.project / "Johto_Offline_Fase12_Auditoria_Integracao_Privado.zip"
        original.write_bytes(b"correct-but-not-real")
        # The second file must still be evaluated (and correctly rejected
        # by SHA-256), instead of aborting on the invalid cached ZIP.
        report = mod.integrate(self.project, self.game)
        self.assertEqual("offline_bundle_invalid", report["status"])
        self.assertIn(original.name, report["reason"])

    def test_unknown_zip_is_rejected(self):
        (self.game / "Game.exe").write_bytes(b"sample")
        package = self.project / mod.BUNDLE_PATHS[0]
        package.parent.mkdir(parents=True)
        package.write_bytes(b"unverified")
        report = mod.integrate(self.project, self.game)
        self.assertEqual("offline_bundle_invalid", report["status"])
        self.assertFalse(report["ready"])

    def test_arbitrary_marker_cannot_unlock_johto(self):
        (self.game / "Game.exe").write_bytes(b"sample")
        (self.game / "Data").mkdir()
        (self.game / "Data/blue-johto-start.txt").write_text("JOHTO,600,6,7")
        report = mod.integrate(self.project, self.game)
        self.assertEqual("existing_install_needs_review", report["status"])
        self.assertFalse(report["ready"])
        self.assertTrue((self.game / "Data/blue-johto-start.txt").is_file())

    def test_installation_hook_is_read_only(self):
        (self.game / "Game.exe").write_bytes(b"sample")
        before = {p.relative_to(self.game): p.read_bytes() for p in self.game.rglob("*") if p.is_file()}
        mod.integrate(self.project, self.game)
        after = {p.relative_to(self.game): p.read_bytes() for p in self.game.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        status = json.loads((self.project / mod.STATUS).read_text("utf-8"))
        self.assertFalse(status["ready"])

    def test_blue_story_calls_johto_after_hoenn(self):
        installer = (ROOT / "scripts/install_game.py").read_text(encoding="utf-8")
        self.assertIn("scripts/regions/auto_integrate_johto.py", installer)
        self.assertGreater(installer.index("auto_integrate_johto.py"),
                           installer.index("auto_integrate_hoenn.py"))
        self.assertIn("if not skip_kanto:", installer)
        self.assertNotIn('"status": "VERIFIED_PLAYABLE"', (ROOT / "scripts/regions/auto_integrate_johto.py").read_text("utf-8"))


if __name__ == "__main__":
    unittest.main()
