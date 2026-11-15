"""Offline contract tests for SAFE Hoenn -> main Decades integration.

No donor archive, native Game.exe or user save is read or written.
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import install_hoenn as hoenn
import auto_integrate_hoenn as auto

class HoennMainIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="hoenn-main-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / "game"
        (self.game / "Data").mkdir(parents=True)
        (self.game / "PBS").mkdir()
        (self.game / "Data/MapInfos.rxdata").write_bytes(b"native mapinfos")
        (self.game / "Data/Tilesets.rxdata").write_bytes(b"native tilesets")
        (self.game / "PBS/map_connections.txt").write_bytes(b"native map connections")
        self.maps = {str(mid): 700 + n for n, mid in enumerate(hoenn.SOURCE_MAPS)}
        self.start = [self.maps["8"], 25, 6, 2]
        self.town = [self.maps["7"], 5, 10, 2]

    def test_isolated_hoenn_plugin_must_not_override_main_new_game(self):
        ruby = (ROOT / "scripts/regions/HoennPilot.rb").read_text(encoding="utf-8")
        start = ruby.split("  module Start", 1)[1].split(
            "  BlueRegionStart.singleton_class.prepend(Start)", 1)[0]
        self.assertIn('File.file?("Hoenn pilot.json")', start)
        self.assertIn("return super unless @new_game", start)
        self.assertIn("BlueHoennPilot::MARKER", start)

    def test_contract_excludes_pilot_boot_and_save_settings(self):
        required = {"Data/System.rxdata", "Data/Scripts.rxdata",
                    "Game.ini", "mkxp.json", "Hoenn pilot.json"}
        self.assertTrue(required.issubset(hoenn.FORBIDDEN))
        self.assertNotIn("Data/MapInfos.rxdata", hoenn.FORBIDDEN)
        self.assertTrue(hoenn.ALLOWED_REPLACE.issubset({
            "Data/MapInfos.rxdata", "Data/Tilesets.rxdata", "PBS/map_connections.txt"}))
        self.assertIn("c59233b", hoenn.UPSTREAM)
        self.assertEqual(len(hoenn.SOURCE_MAPS), 199)

    def test_littleroot_point_must_be_source_verified(self):
        rows = ["BLUE_HOENN_TEST_STOPS_V1"]
        for source, new in self.maps.items():
            rows.append(f"{source}|{new}|5|10|2|Hoenn Map {source}")
        raw = ("\n".join(rows)+"\n").encode("utf8")
        report = {"maps": {int(k): v for k,v in self.maps.items()}}
        self.assertEqual(hoenn.vetted_town(report, {"Data/blue-hoenn-test-stops.txt":raw}),
                         self.town)
        bogus = raw.replace(f"7|{self.maps['7']}|".encode(),
                            f"7|{self.maps['7']+1}|".encode())
        with self.assertRaises(ValueError):
            hoenn.vetted_town(report, {"Data/blue-hoenn-test-stops.txt":bogus})

    def test_forged_release_or_modified_pbs_is_rejected(self):
        for rel in hoenn.REQUIRED:
            path = self.game / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"verified fixture")
        for mid in self.maps.values():
            (self.game / f"Data/Map{mid:03}.rxdata").write_bytes(b"authored fixture")
        hashes = {
            rel: hoenn.sha((self.game / rel).read_bytes()) for rel in (
                hoenn.PLUGIN,"Data/blue-hoenn-pilot.txt",
                "PBS/trainers_hoenn_pilot.txt", "PBS/encounters_hoenn_pilot.txt")
        }
        proof = {
            "schema":1,"region":"HOENN",
            "source_commit":hoenn.UPSTREAM,
            "status":"INTEGRATED_FILES_READY_FOR_NATIVE_QA",
            "maps":self.maps,"start":self.start,"town":self.town,
            "installed_sha256":hashes
        }
        (self.game / hoenn.MANIFEST).write_text(json.dumps(proof))
        (self.game / hoenn.READY_MARKER).write_text(
            f"BLUE_HOENN_READY_V1,199,{self.start[0]},{self.town[0]},{self.town[1]},{self.town[2]},{self.town[3]}\n")
        (self.game / hoenn.START_MARKER).write_text(
            f"BLUE_HOENN_START_V1,HOENN,{self.start[0]},25,6\n")
        status=hoenn.verify_installed(self.game)
        self.assertEqual(status["maps"],199)
        self.assertFalse(status["game_exe_tested_here"])
        (self.game / "PBS/trainers_hoenn_pilot.txt").write_bytes(b"modified")
        with self.assertRaisesRegex(ValueError,"modificada"):
            hoenn.verify_installed(self.game)
        (self.game / "PBS/trainers_hoenn_pilot.txt").write_bytes(b"verified fixture")
        proof["source_commit"]="0"*40
        (self.game / hoenn.MANIFEST).write_text(json.dumps(proof))
        with self.assertRaisesRegex(ValueError,"inválido"):
            hoenn.verify_installed(self.game)

    def test_reuses_original_pinned_stage_without_private_zip(self):
        directory = self.root / ".blue-work/hoenn-source/0123456789abcdef"
        directory.mkdir(parents=True)
        with patch.object(hoenn, "ROOT", self.root), \
             patch("hoenn_qa_phase1.load_tree", return_value={}) as inventory, \
             patch.object(hoenn, "check_tree") as tree, \
             patch.object(hoenn, "Source") as source_cls, \
             patch.object(hoenn, "check_source") as audit:
            source, origin = hoenn.validated_local_source(
                self.root / "missing-private.zip", self.root / ".blue-work/pinned-tree.json"
            )
        self.assertEqual(origin, "audited_staged_source")
        self.assertIs(source, source_cls.return_value)
        self.assertEqual(source_cls.call_args.args[0], directory)
        inventory.assert_called_once()
        tree.assert_called_once()
        audit.assert_called_once_with(source)

    def test_staged_source_never_bypasses_hash_audit(self):
        directory = self.root / ".blue-work/hoenn-source/0123456789abcdef"
        directory.mkdir(parents=True)
        with patch.object(hoenn, "ROOT", self.root), \
             patch("hoenn_qa_phase1.load_tree", return_value={}), \
             patch.object(hoenn, "check_tree"), \
             patch.object(hoenn, "check_source", side_effect=ValueError("wrong donor hash")):
            with self.assertRaisesRegex(ValueError, "hashes"):
                hoenn.validated_local_source(
                    self.root / "missing-private.zip", self.root / ".blue-work/pinned-tree.json"
                )

    def test_partial_hoenn_is_never_automatically_reallocated(self):
        self.assertEqual(hoenn.detect_existing(self.game),"absent")
        (self.game / "PBS/trainers_hoenn_pilot.txt").write_text("partial")
        self.assertEqual(hoenn.detect_existing(self.game),"partial")
        with patch.object(hoenn,"MAIN",self.game), patch.object(hoenn,"verify_kanto"):
            (self.game / "Game.exe").write_bytes(b"fixture")
            with self.assertRaisesRegex(ValueError, "Revisão manual"):
                hoenn.apply(self.game,self.root/"missing.zip",self.root/"missing.json",commit=True)

    def test_hoenn_overlay_rejects_collision_and_never_installs_boot_files(self):
        generated={f"Data/Map{mid:03}.rxdata":b"authored map" for mid in self.maps.values()}
        generated.update({
            "Data/MapInfos.rxdata":b"with Hoenn mapinfos",
            "Data/Tilesets.rxdata":b"with Hoenn tilesets",
            "PBS/map_connections.txt":b"native + Hoenn connections",
            "Data/System.rxdata":b"FORBIDDEN",
            "Data/Scripts.rxdata":b"FORBIDDEN",
            "Game.ini":b"FORBIDDEN",
            "mkxp.json":b"FORBIDDEN",
            "Hoenn pilot.json":b"FORBIDDEN",
            "Data/blue-hoenn-compile-request.txt":b"pilot only",
            "Data/blue-hoenn-test-stops.txt":(
                "BLUE_HOENN_TEST_STOPS_V1\n" +
                "".join(f"{src}|{mid}|5|10|2|Hoenn Map\n" for src,mid in self.maps.items())
            ).encode(),
        })
        report={"region":"HOENN","source_commit":hoenn.UPSTREAM,
                "maps":{int(k):v for k,v in self.maps.items()},"qa12":{"status":"STATIC"}}
        with patch.object(hoenn,"build_overlay",return_value=(generated,report)):
            files, proof=hoenn.prepare_overlay(self.game,None)
        self.assertEqual(len(proof["maps"]),199)
        self.assertEqual(proof["town"],self.town)
        self.assertFalse(hoenn.FORBIDDEN & set(files))
        self.assertIn("Data/MapInfos.rxdata",files)
        (self.game / f"Data/Map{self.maps['7']:03}.rxdata").write_bytes(b"foreign-map")
        with patch.object(hoenn,"build_overlay",return_value=(generated,report)):
            with self.assertRaisesRegex(ValueError,"sobrescrito"):
                hoenn.prepare_overlay(self.game,None)


class HoennAutoInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="hoenn-auto-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.game=self.root/"game"
        self.game.mkdir()
        (self.game/"Game.exe").write_bytes(b"fixture")
        (self.game/"Data").mkdir()
        self.patches=[
            patch.object(auto,"ROOT",self.root),
            patch.object(auto,"ZIP",self.root/"The Pokémon World Project - Hoenn.zip"),
            patch.object(auto,"STATUS",self.root/".blue-work/status.json"),
            patch.object(auto,"LOG",self.root/".blue-work/log.txt"),
            patch.object(auto,"SOURCE_CACHE",self.root/".blue-work/hoenn-source")
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def test_absent_zip_does_not_fake_a_success_or_run_installer(self):
        with patch.object(auto,"invoke") as invoke:
            result=auto.integrate(self.root,self.game)
        invoke.assert_not_called()
        self.assertEqual(result["status"],"awaiting_local_source")
        self.assertFalse(result["ready"])
        self.assertFalse(result["changed"])
        self.assertEqual((self.game / auto.GAME_STATUS).read_text().strip(),
                         "awaiting_local_source")

    def test_cached_source_triggers_import_even_without_zip(self):
        auto.SOURCE_CACHE.mkdir(parents=True)
        calls = []
        with patch.object(auto, "invoke", side_effect=lambda *args: calls.append(args)):
            result = auto.integrate(self.root, self.game)
        self.assertEqual(result["status"], "integrated")
        self.assertEqual([call[-1] for call in calls], ["--apply", "--verify-installed"])
        self.assertEqual((self.game / auto.GAME_STATUS).read_text().strip(), "integrated")

    def test_source_available_only_marks_ready_after_apply_and_verify(self):
        auto.ZIP.write_bytes(b"private fixture (never uploaded)")
        calls=[]
        with patch.object(auto,"invoke",side_effect=lambda *args:calls.append(args)):
            result=auto.integrate(self.root,self.game)
        self.assertEqual(result["status"],"integrated")
        self.assertEqual([call[-1] for call in calls],["--apply","--verify-installed"])
        self.assertTrue(result["changed"])

    def test_existing_invalid_install_is_not_automatically_overwritten(self):
        (self.game / auto.PROOF).parent.mkdir()
        (self.game / auto.PROOF).write_text("{}")
        with patch.object(auto,"invoke",side_effect=RuntimeError("bad proof")):
            result=auto.integrate(self.root,self.game)
        self.assertEqual(result["status"],"existing_install_needs_review")
        self.assertFalse(result["ready"])


if __name__=="__main__":
    unittest.main()
