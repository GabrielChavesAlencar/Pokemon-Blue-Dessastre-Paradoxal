"""Offline contracts for the website's automatic Kanto integration.

These fixtures NEVER download FRLG, touch a user's game/ or run Game.exe.
"""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location(
    "kanto_auto_integration", ROOT / "scripts/regions/auto_integrate_kanto.py")
auto = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auto)


class KantoAutoIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="kanto-auto-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name).resolve()
        self.game = self.project / "game"
        (self.game / "PBS").mkdir(parents=True)
        (self.game / "Data").mkdir()
        (self.game / "Game.exe").write_bytes(b"fictional executable")
        (self.game / "PBS/pokemon.txt").write_text("[BULBASAUR]\n")
        self.calls = []

    def invoke(self, argv, project, env):
        self.assertEqual(project, self.project)
        self.assertEqual(env["BLUE_GAME_DIR"], str(self.game))
        self.calls.append(argv)

    def test_fresh_install_bootstraps_pinned_source_then_imports_then_verifies(self):
        result = auto.integrate(self.project, self.game, run=self.invoke)
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

    def test_uses_cached_verified_pilot_without_redownloading_source(self):
        cache = self.project / ".blue-work/kanto-pilot/Kanto pilot.json"
        cache.parent.mkdir(parents=True)
        cache.write_text('{"region":"KANTO"}', encoding="utf8")
        result = auto.integrate(self.project, self.game, run=self.invoke)
        self.assertEqual(result["status"], "integrated")
        self.assertEqual(result["source"], "cached_verified_pilot")
        self.assertTrue(result["ready"])
        self.assertEqual([x[1] for x in self.calls],
                         [auto.KANTO_IMPORTER, auto.KANTO_IMPORTER])
        self.assertIn("--apply", self.calls[0])
        self.assertNotIn(auto.KANTO_SOURCE_BOOTSTRAP, [x[1] for x in self.calls])

    def test_invalid_cached_pilot_falls_back_to_pinned_source(self):
        cache = self.project / ".blue-work/kanto-pilot/Kanto pilot.json"
        cache.parent.mkdir(parents=True)
        cache.write_text('{"obsolete":true}', encoding="utf8")
        def runner(argv, project, env):
            self.calls.append(argv)
            if len(self.calls) == 1:
                raise subprocess.CalledProcessError(1, argv)
        result = auto.integrate(self.project, self.game, run=runner)
        self.assertEqual(result["status"], "integrated")
        self.assertEqual([x[1] for x in self.calls],
                         [auto.KANTO_IMPORTER, auto.KANTO_SOURCE_BOOTSTRAP,
                          auto.KANTO_IMPORTER, auto.KANTO_IMPORTER])

    def test_gary_three_variants_request_exactly_one_native_recompile(self):
        trainers = self.game / "PBS/trainers_kanto.txt"
        kinds = self.game / "PBS/trainer_types_kanto.txt"
        trainers.write_text(
            "[BLUE_KANTO_RIVAL,Blue,11]\nPokemon = CHARMANDER,5\n"
            "[BLUE_KANTO_RIVAL,Blue,12]\nPokemon = SQUIRTLE,5\n"
            "[BLUE_KANTO_RIVAL,Blue,13]\nPokemon = BULBASAUR,5\n",
            encoding="utf8")
        kinds.write_text("[BLUE_KANTO_RIVAL]\nName = Rival\n", encoding="utf8")
        compiled = self.game / "Data/trainers.dat"
        compiled.write_bytes(b"old synthetic Decades data")
        first = auto.ensure_rival_compilation(self.project, self.game)
        self.assertTrue(first)
        self.assertEqual(
            (self.game / "Data/blue-compile-request.txt").read_text("ascii"),
            "compile")
        sig = self.project / auto.RIVAL_COMPILER_STAMP
        self.assertEqual(len(sig.read_text("ascii").strip()), 64)
        # The native game recompiled after first launch: no second request.
        import os
        from time import time
        os.utime(compiled, (time() + 100, time() + 100))
        (self.game / "Data/blue-compile-request.txt").unlink()
        self.assertFalse(auto.ensure_rival_compilation(self.project, self.game))
        self.assertFalse((self.game / "Data/blue-compile-request.txt").exists())
        trainers.write_text(trainers.read_text("utf8") + "\n# new source revision",
                            encoding="utf8")
        self.assertTrue(auto.ensure_rival_compilation(self.project, self.game))
        self.assertEqual(compiled.read_bytes(), b"old synthetic Decades data")

    def test_already_installed_only_verifies_and_never_reinstalls(self):
        (self.game / auto.KANTO_MARKER).write_text("BLUE_KANTO_START_V1,KANTO,300,25,7\n")
        result = auto.integrate(self.project, self.game, run=self.invoke)
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

    def test_known_142_map_install_attempts_migration_then_verifies(self):
        import json
        (self.game / auto.KANTO_MARKER).write_text("installed")
        (self.game / auto.KANTO_MANIFEST).write_text(json.dumps({
            "schema": 1, "source": "Essentials FRLG 21.1",
            "maps": {str(i): i + 300 for i in range(142)}
        }))
        def runner(argv, project, env):
            self.calls.append(argv)
            if len(self.calls) == 1:
                raise subprocess.CalledProcessError(1, argv)
        result = auto.integrate(self.project, self.game, run=runner)
        self.assertTrue(result["ready"])
        self.assertTrue(result["changed"])
        self.assertEqual(result["source"], "verified_142_to_145_migration")
        self.assertIn(auto.KANTO_SOURCE_BOOTSTRAP, self.calls[1])
        self.assertIn("--migrate-existing", self.calls[2])
        self.assertIn("--verify-installed", self.calls[3])

    def test_145_map_install_routes_to_migration_only_when_151_catalogue_active(self):
        import json
        (self.game / auto.KANTO_MARKER).write_text("installed")
        (self.game / auto.KANTO_MANIFEST).write_text(json.dumps({
            "schema": 1, "source": "Essentials FRLG 21.1",
            "maps": {str(i): i + 300 for i in range(145)}
        }))
        def runner(argv, project, env):
            self.calls.append(argv)
            if len(self.calls) == 1:
                raise subprocess.CalledProcessError(1, argv)
        result = auto.integrate(self.project, self.game, run=runner)
        self.assertEqual(result["status"], "manual_migration_required")
        self.assertEqual(len(self.calls), 1)
        self.calls.clear()
        catalogue = self.project / "data/regions/kanto-source.json"
        catalogue.parent.mkdir(parents=True)
        catalogue.write_text(json.dumps({"maps": {str(i): str(i) for i in range(151)}}))
        result = auto.integrate(self.project, self.game, run=runner)
        self.assertEqual(result["source"], "verified_145_to_151_migration")
        self.assertIn("--migrate-existing", self.calls[2])
        self.assertIn("--verify-installed", self.calls[3])

    def test_k03e_automatic_migration_requires_exact_predecessor(self):
        import json
        (self.game / auto.KANTO_MARKER).write_text("installed")
        catalogue = self.project / "data/regions/kanto-source.json"
        catalogue.parent.mkdir(parents=True)
        new = {"23", "79", "81", "82"}
        old = {str(i): i + 300 for i in range(200, 356)}
        target = {**old, **dict.fromkeys(new, "future")}
        catalogue.write_text(json.dumps({"maps": target}))
        for maps, should_migrate in (
            ({**{k: v for k, v in old.items() if k != "355"}, "23": 900}, False),
            ({k: v for k, v in old.items() if k != "355"}, False),
            (old, True),
        ):
            with self.subTest(should_migrate=should_migrate, old_size=len(maps)):
                self.calls.clear()
                (self.game / auto.KANTO_MANIFEST).write_text(json.dumps({
                    "schema": 1, "source": "Essentials FRLG 21.1", "maps": maps,
                }))
                def runner(argv, project, env):
                    self.calls.append(argv)
                    if len(self.calls) == 1:
                        raise ValueError("Old Kanto catalogue")
                result = auto.integrate(self.project, self.game, run=runner)
                if should_migrate:
                    self.assertEqual(result["source"], "verified_156_to_160_migration")
                    self.assertIn("--migrate-existing", self.calls[2])
                    self.assertIn("--verify-installed", self.calls[3])
                else:
                    self.assertEqual(result["status"], "manual_migration_required")
                    self.assertEqual(len(self.calls), 1)

    def test_k05_auto_allows_exact_three_predecessors_only(self):
        import json
        from scripts.regions.k03e_contract import MAPS as diglett
        from scripts.regions.k04_corridor import MAPS as rock
        from scripts.regions.k05_contract import MAPS as lavender
        (self.game / auto.KANTO_MARKER).write_text("installed")
        catalog = self.project / "data/regions/kanto-source.json"
        catalog.parent.mkdir(parents=True)
        maps = {str(i): i+100 for i in range(200,356)}
        map_set = lambda group: {str(i):key for i,key in group.items()}
        variants = [dict(maps)]
        for group in (diglett,rock,lavender):
            maps.update(map_set(group))
            variants.append(dict(maps))
        catalog.write_text(json.dumps({"maps":maps}))
        for old in variants[:-1] + [{**variants[0],"23":600}]:
            self.calls.clear()
            (self.game/auto.KANTO_MANIFEST).write_text(json.dumps({
                "schema":1,"source":"Essentials FRLG 21.1","maps":old}))
            def runner(argv, project, env):
                self.calls.append(argv)
                if len(self.calls)==1:
                    raise ValueError("Previous Kanto catalogue")
            actual=auto.integrate(self.project,self.game,run=runner)
            if len(old)==157:
                self.assertEqual(actual["status"],"manual_migration_required")
                self.assertEqual(len(self.calls),1)
            else:
                self.assertEqual(actual["source"],f"verified_{len(old)}_to_178_migration")
                self.assertIn("--migrate-existing",self.calls[2])

    def test_current_count_broken_cerulean_door_retries_verified_migration(self):
        import json
        (self.game / auto.KANTO_MARKER).write_text("installed")
        maps = {str(i): i + 300 for i in range(152)}
        (self.game / auto.KANTO_MANIFEST).write_text(json.dumps({
            "schema": 1, "source": "Essentials FRLG 21.1", "maps": maps}))
        catalogue = self.project / "data/regions/kanto-source.json"
        catalogue.parent.mkdir(parents=True)
        catalogue.write_text(json.dumps({"maps": maps}))
        def runner(argv, project, env):
            self.calls.append(argv)
            if len(self.calls) == 1:
                raise ValueError("Cerulean door 7 missing or moved in installed map")
        result = auto.integrate(self.project, self.game, run=runner)
        self.assertTrue(result["ready"])
        self.assertIn("--migrate-existing", self.calls[2])
        self.assertIn("--verify-installed", self.calls[3])

    def test_current_count_legacy_ss_anne_retries_verified_migration(self):
        import json
        (self.game / auto.KANTO_MARKER).write_text("installed")
        maps = {str(i): i + 300 for i in range(156)}
        (self.game / auto.KANTO_MANIFEST).write_text(json.dumps({
            "schema": 1, "source": "Essentials FRLG 21.1", "maps": maps}))
        catalogue = self.project / "data/regions/kanto-source.json"
        catalogue.parent.mkdir(parents=True)
        catalogue.write_text(json.dumps({"maps": maps}))
        def runner(argv, project, env):
            self.calls.append(argv)
            if len(self.calls) == 1:
                raise ValueError("S.S. Anne rival gate: missing source lane 22")
        result = auto.integrate(self.project, self.game, run=runner)
        self.assertTrue(result["ready"])
        self.assertIn("--migrate-existing", self.calls[2])
        self.assertIn("--verify-installed", self.calls[3])

    def test_current_count_unrelated_error_never_rebuilds(self):
        import json
        (self.game / auto.KANTO_MARKER).write_text("installed")
        maps = {str(i): i + 300 for i in range(152)}
        (self.game / auto.KANTO_MANIFEST).write_text(json.dumps({
            "schema": 1, "source": "Essentials FRLG 21.1", "maps": maps}))
        catalogue = self.project / "data/regions/kanto-source.json"
        catalogue.parent.mkdir(parents=True)
        catalogue.write_text(json.dumps({"maps": maps}))
        def runner(argv, project, env):
            self.calls.append(argv)
            raise ValueError("Unrelated map integrity error")
        result = auto.integrate(self.project, self.game, run=runner)
        self.assertFalse(result["ready"])
        self.assertEqual(len(self.calls), 1)

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
        second = auto.integrate(self.project, self.game, run=self.invoke)
        self.assertEqual(second["status"], "integrated")
        self.assertTrue(second["ready"])
        self.assertEqual(__import__("json").loads(
            (self.project / auto.STATUS_FILE).read_text(encoding="utf8"))["status"],
            "integrated")

    def test_foreign_path_or_missing_decades_skips(self):
        foreign = self.project / "other-game"
        foreign.mkdir()
        self.assertEqual(auto.integrate(self.project, foreign, run=self.invoke)["status"],
                         "skipped_foreign_path")
        (self.game / "Game.exe").unlink()
        self.assertEqual(auto.integrate(self.project, self.game, run=self.invoke)["status"],
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
