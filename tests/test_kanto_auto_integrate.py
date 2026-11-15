"""Offline contracts for the website's automatic Kanto integration.

These fixtures NEVER download FRLG, touch a user's game/ or run Game.exe.
"""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "kanto_auto_integration", ROOT / "scripts/regions/auto_integrate_kanto.py")
auto = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auto)


class KantoAutoIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="kanto-auto-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        self.game = self.project / "game"
        (self.game / "PBS").mkdir(parents=True)
        (self.game / "Data").mkdir()
        (self.game / "Game.exe").write_bytes(b"fictional executable")
        (self.game / "PBS/pokemon.txt").write_text("[BULBASAUR]\n")
        self.calls = []

    def run(self, argv, project, env):
        self.assertEqual(project, self.project)
        self.assertEqual(env["BLUE_GAME_DIR"], str(self.game))
        self.calls.append(argv)

    def test_fresh_install_bootstraps_pinned_source_then_imports_then_verifies(self):
        result = auto.integrate(self.project, self.game, run=self.run)
        self.assertEqual(result["status"], "integrated")
        self.assertTrue(result["ready"])
        self.assertTrue(result["changed"])
        self.assertEqual(result["log"], str(self.project / auto.LOG_FILE))
        self.assertEqual(result, __import__("json").loads(
            (self.project / auto.STATUS_FILE).read_text(encoding="utf8")))
        self.assertEqual([argv[1] for argv in self.calls], [
            auto.KANTO_SOURCE_BOOTSTRAP, auto.KANTO_IMPORTER, auto.KANTO_IMPORTER])
        self.assertIn("--apply", self.calls[1])
        self.assertIn("--verify-installed", self.calls[2])

    def test_already_installed_only_verifies_and_never_reinstalls(self):
        (self.game / auto.KANTO_MARKER).write_text("BLUE_KANTO_START_V1,KANTO,300,25,7\n")
        result = auto.integrate(self.project, self.game, run=self.run)
        self.assertEqual(result["status"], "already_integrated")
        self.assertTrue(result["ready"])
        self.assertFalse(result["changed"])
        self.assertEqual(len(self.calls), 2)
        self.assertIn("--verify-installed", self.calls[0])
        self.assertIn("--sync-runtime", self.calls[1])
        self.assertIn("--apply", self.calls[1])

    def test_old_install_blocked_and_decades_keeps_running(self):
        (self.game / auto.KANTO_MARKER).write_text("old Kanto 25 maps\n")
        def broken(argv, project, env):
            self.calls.append(argv)
            raise subprocess.CalledProcessError(2, argv)
        result = auto.integrate(self.project, self.game, run=broken)
        self.assertEqual(result["status"], "manual_migration_required")
        self.assertFalse(result["ready"])
        self.assertFalse(result["changed"])
        self.assertIn("Verificacao", result["reason"])
        self.assertEqual(len(self.calls), 1)
        self.assertTrue((self.game / auto.KANTO_MARKER).is_file())

    def test_partial_import_without_marker_is_not_overwritten(self):
        partial = self.game / "PBS/trainers_kanto.txt"
        partial.write_text("existing user Kanto data")
        def runner(argv, project, env):
            raise subprocess.CalledProcessError(5, argv)
        result = auto.integrate(self.project, self.game, run=runner)
        self.assertEqual(result["status"], "manual_migration_required")
        self.assertEqual(partial.read_text(), "existing user Kanto data")

    def test_offline_author_source_does_not_block_native_decades(self):
        def offline(argv, project, env):
            self.calls.append(argv)
            raise subprocess.CalledProcessError(1, argv)
        result = auto.integrate(self.project, self.game, run=offline)
        self.assertEqual(result["status"], "kanto_unavailable")
        self.assertFalse(result["ready"])
        self.assertFalse(result["changed"])
        self.assertIn("Download/montagem", result["reason"])
        self.assertEqual(len(self.calls), 1)
        self.assertTrue((self.game / "Game.exe").is_file())

    def test_verified_kanto_still_playable_when_optional_runtime_sync_fails(self):
        (self.game / auto.KANTO_MARKER).write_text("BLUE_KANTO_START_V1,KANTO,300,25,7\\n")
        def runner(argv, project, env):
            self.calls.append(argv)
            if "--sync-runtime" in argv:
                raise subprocess.CalledProcessError(7, argv)
        result = auto.integrate(self.project, self.game, run=runner)
        self.assertEqual(result["status"], "already_integrated_runtime_preserved")
        self.assertTrue(result["ready"])
        self.assertEqual(len(self.calls), 2)

    def test_status_is_rewritten_on_every_attempt(self):
        def fail(argv, project, env):
            raise RuntimeError("Fonte FRLG indisponivel: HTTP 403")
        first = auto.integrate(self.project, self.game, run=fail)
        self.assertEqual(first["status"], "kanto_unavailable")
        self.assertIn("403", first["reason"])
        second = auto.integrate(self.project, self.game, run=self.run)
        self.assertEqual(second["status"], "integrated")
        self.assertTrue(second["ready"])
        self.assertEqual(__import__("json").loads(
            (self.project / auto.STATUS_FILE).read_text(encoding="utf8"))["status"],
            "integrated")

    def test_foreign_path_or_missing_decades_skips(self):
        foreign = self.project / "other-game"
        foreign.mkdir()
        self.assertEqual(auto.integrate(self.project, foreign, run=self.run)["status"],
                         "skipped_foreign_path")
        (self.game / "Game.exe").unlink()
        self.assertEqual(auto.integrate(self.project, self.game, run=self.run)["status"],
                         "skipped_no_game")
        self.assertEqual(self.calls, [])

    def test_public_site_bootstrap_calls_regular_story_installer(self):
        bootstrap = (ROOT / "scripts/windows/Bootstrap.cs").read_text(encoding="utf-8")
        installer = (ROOT / "scripts/install_game.py").read_text(encoding="utf-8")
        self.assertIn('new List<string>{"scripts/install_game.py","--apply"}', bootstrap)
        self.assertIn("auto_integrate_kanto.py", installer)
        self.assertIn("result=auto.integrate(project,game)", installer)
        self.assertIn("if result['changed']:", installer)


if __name__ == "__main__":
    unittest.main()
