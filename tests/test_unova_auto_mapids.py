"""One-click RUN_UNOVA_MAPIDS: source detection, fail-closed QA and A04/A05."""
from __future__ import annotations

import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from server.ruby_marshal import RubyObject
from stage import serialize
import unova_auto_mapids as runner

NEEDED=(
    "data/regions/unova-a05-mapid-candidates.json",
    "data/regions/sinnoh-b05-mapid-planning.json",
    "data/regions/sinnoh-b01-actual-native.json",
    "data/regions/sinnoh-b03-installer-evidence.json",
    "data/regions/unova-u03-areas.json",
)


class AutoMapIDsTests(unittest.TestCase):
    def setUp(self):
        td=tempfile.TemporaryDirectory(prefix="unova-one-click-")
        self.addCleanup(td.cleanup)
        self.base=Path(td.name)
        self.project=self.base/"repo"
        self.project.mkdir()
        for relative in NEEDED:
            target=self.project/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/relative,target)
        self.appdata=self.base/"AppData"/"Local"
        self.env={"LOCALAPPDATA":str(self.appdata),"USERPROFILE":str(self.base/"user"),
                  "APPDATA":str(self.base/"roaming")}
        self.install=self.appdata/"PokemonBlueDessastreParadoxal"/"game"

    def make_game(self,location=None,extra_ids=()):
        game=location or self.install
        data=game/"Data"
        data.mkdir(parents=True,exist_ok=True)
        (game/"Game.exe").write_bytes(b"test dummy exe never launched")
        ids=list(range(1,23))+list(extra_ids)
        infos={}
        for map_id in ids:
            infos[map_id]=RubyObject(
                "RPG::MapInfo",{"@name":f"Test Map {map_id}".encode("ascii")})
            (data/f"Map{map_id:03}.rxdata").write_bytes(
                ("a synthetic map, no game data "+str(map_id)).encode("ascii"))
        (data/"MapInfos.rxdata").write_bytes(serialize(infos))
        return game

    def test_01_no_install_is_fully_blocked(self):
        result=runner.execute(self.project,self.env)
        self.assertEqual(result["status"],"BLOCKED_NO_AUTOMATIC_GAME_FOUND")
        self.assertIsNone(result["a04_result"])
        self.assertIsNone(result["a05_result"])
        self.assertFalse(result["can_install"])

    def test_02_auto_find_known_localappdata_install(self):
        self.make_game()
        selected,checked,reason=runner.discover(self.project,self.env)
        self.assertEqual(selected,self.install)
        self.assertIsNone(reason)
        self.assertIn("INSTALACAO_PADRAO", [x["label"] for x in checked if x["eligible"]])

    def test_03_game_with_22_maps_runs_a04_then_a05(self):
        self.make_game()
        result=runner.execute(self.project,self.env)
        self.assertEqual(result["status"],"AUTO_A04_A05_DONE_NOT_NATIVE_APPROVED")
        self.assertEqual(result["a04_result"]["observed_or_declared_occupied_count"],22)
        self.assertTrue(result["a05_result"]["a04_report_supplied"])
        self.assertEqual(result["a05_result"]["historical_candidate_count"],174)
        self.assertIsNone(result["a05_result"]["verified_free_mapids"])
        self.assertFalse(result["can_reserve_mapids"])
        self.assertFalse(result["can_install"])
        self.assertEqual(result["a05_result"]["bar_a_completed"],0)
        self.assertTrue(Path(result["a04_report_path"]).exists())
        self.assertTrue(Path(result["a05_report_path"]).exists())

    def test_04_occupied_new_map_518_is_flagged(self):
        self.make_game(extra_ids=(518,))
        result=runner.execute(self.project,self.env)
        self.assertIn(518,result["a05_result"]["a04_observed_candidate_collisions"])
        self.assertFalse(result["a05_result"]["a04_preferred_block_observed_vacant"])
        self.assertFalse(result["a05_result"]["can_reserve_mapids"])

    def test_05_original_game_and_mapinfos_unchanged(self):
        self.make_game(extra_ids=(518,))
        exe=(self.install/"Game.exe").read_bytes()
        info=(self.install/"Data"/"MapInfos.rxdata").read_bytes()
        result=runner.execute(self.project,self.env)
        runner.store_summary(self.project,result)
        self.assertEqual(exe,(self.install/"Game.exe").read_bytes())
        self.assertEqual(info,(self.install/"Data"/"MapInfos.rxdata").read_bytes())
        self.assertFalse((self.install/"Data"/"UNOVA_MAPIDS.json").exists())

    def test_06_summary_is_saved_where_user_can_find_it(self):
        self.make_game()
        result=runner.execute(self.project,self.env)
        path=runner.store_summary(self.project,result)
        text=path.read_text("utf-8-sig")
        self.assertIn("A04",text)
        self.assertIn("A05",text)
        self.assertIn("518-599",text)
        self.assertIn("NENHUM MapID",text)
        self.assertTrue(path.is_relative_to(self.project/".blue-work/unova/audit"))

    def test_07_report_is_repeatable_and_idempotent(self):
        self.make_game()
        first=runner.execute(self.project,self.env)
        second=runner.execute(self.project,self.env)
        self.assertEqual(first["a04_report_path"],second["a04_report_path"])
        self.assertEqual(first["a05_report_path"],second["a05_report_path"])
        self.assertEqual(Path(first["a04_report_path"]).read_bytes(),
                         Path(second["a04_report_path"]).read_bytes())

    def test_08_empty_data_without_mapinfos_not_chosen(self):
        game=self.install
        (game/"Data").mkdir(parents=True)
        (game/"Game.exe").write_bytes(b"fake")
        selected,checks,_=runner.discover(self.project,self.env)
        self.assertIsNone(selected)
        self.assertTrue(any("MapInfos" in x["result"] for x in checks))

    def test_09_game_exe_required_to_avoid_source_snapshot(self):
        self.make_game()
        (self.install/"Game.exe").unlink()
        chosen,_,_=runner.discover(self.project,self.env)
        self.assertIsNone(chosen)

    def test_10_explicit_env_override_is_used(self):
        other=self.make_game(self.base/"another"/"game")
        chosen,_,why=runner.discover(self.project,{
            "BLUE_DECADES_GAME_DIR":str(other),
            **self.env,
        })
        self.assertEqual(chosen,other)
        self.assertIsNone(why)

    def test_11_invalid_explicit_override_never_falls_back(self):
        self.make_game()
        chosen,_,why=runner.discover(self.project,{
            **self.env,"BLUE_DECADES_GAME_DIR":str(self.base/"missing")
        })
        self.assertIsNone(chosen)
        self.assertIsNotNone(why)

    def test_12_known_install_wins_over_old_repo_copy(self):
        self.make_game()
        self.make_game(self.project/"game")
        chosen,_,_=runner.discover(self.project,self.env)
        self.assertEqual(chosen,self.install)

    def test_13_multiple_alternatives_without_known_install_block(self):
        first=self.make_game(self.project/"game")
        second=self.make_game(self.project.parent/"game")
        chosen,_,why=runner.discover(self.project,self.env)
        self.assertIsNone(chosen)
        self.assertIn("varias instalacoes",why)

    def test_14_symlinked_game_is_not_selected(self):
        real=self.make_game(self.base/"source"/"game")
        self.install.parent.mkdir(parents=True)
        try:
            self.install.symlink_to(real,target_is_directory=True)
        except OSError:
            self.skipTest("symlink not supported")
        chosen,_,why=runner.discover(self.project,self.env)
        self.assertIsNone(chosen)
        self.assertIsNotNone(why)

    def test_15_empty_or_small_game_is_rejected(self):
        self.make_game()
        for mid in range(4,23):
            (self.install/"Data"/f"Map{mid:03}.rxdata").unlink()
        chosen,_,_=runner.discover(self.project,self.env)
        self.assertIsNone(chosen)

    def test_16_no_recursive_scan_of_home_or_disks(self):
        possible=runner.candidate_locations(self.project,self.env)
        self.assertLess(len(possible),15)
        self.assertFalse(any(Path(p)==self.base for _,p in possible))
        self.assertFalse(any(p.name=="Downloads" for _,p in possible))

    def test_17_blocked_case_still_produces_useful_summary(self):
        result=runner.execute(self.project,self.env)
        output=runner.store_summary(self.project,result)
        self.assertIn("Nenhuma instalacao",output.read_text("utf-8-sig"))
        self.assertFalse((self.project/"game").exists())

    def test_18_cli_auto_uses_env_and_does_not_open_notepad_without_flag(self):
        self.make_game()
        stdout=io.StringIO()
        with mock.patch.dict(os.environ,self.env,clear=True):
            with contextlib.redirect_stdout(stdout):
                code=runner.main(["--project",str(self.project)])
        self.assertEqual(code,0)
        self.assertIn("AUTO_A04_A05_DONE_NOT_NATIVE_APPROVED",stdout.getvalue())
        self.assertTrue((self.project/runner.SUMMARY).exists())

    def test_19_cli_no_game_returns_nonzero_without_fake_success(self):
        with mock.patch.dict(os.environ,self.env,clear=True):
            with contextlib.redirect_stdout(io.StringIO()):
                code=runner.main(["--project",str(self.project)])
        self.assertEqual(code,2)
        self.assertTrue((self.project/runner.SUMMARY).exists())

    def test_20_never_mutates_user_game_during_failed_a04(self):
        self.make_game()
        before=(self.install/"Data"/"MapInfos.rxdata").read_bytes()
        (self.install/"Data"/"MapInfos.rxdata").write_bytes(b"invalid")
        bad=(self.install/"Data"/"MapInfos.rxdata").read_bytes()
        result=runner.execute(self.project,self.env)
        self.assertEqual(result["status"],"AUTO_A04_OR_A05_BLOCKED")
        self.assertEqual((self.install/"Data"/"MapInfos.rxdata").read_bytes(),bad)
        self.assertNotEqual(before,bad)
        self.assertIsNone(result["a05_result"])

    def test_21_report_summary_symlink_is_blocked(self):
        self.make_game()
        result=runner.execute(self.project,self.env)
        out=self.project/runner.SUMMARY
        outside=self.base/"outside.txt"
        outside.write_text("do not overwrite")
        try:
            out.symlink_to(outside)
        except OSError:
            self.skipTest("symlinks unavailable")
        with self.assertRaises(ValueError):
            runner.store_summary(self.project,result)
        self.assertEqual(outside.read_text(),"do not overwrite")

    def test_22_report_status_does_not_say_reserved(self):
        self.make_game()
        result=runner.execute(self.project,self.env)
        self.assertFalse(result["can_reserve_mapids"])
        self.assertEqual(result["status"],"AUTO_A04_A05_DONE_NOT_NATIVE_APPROVED")
        self.assertFalse(result["a05_result"]["mapid_reservation_confirmed"])
        self.assertFalse(result["a05_result"]["can_install"])


    def test_23_a06_report_is_always_generated_and_failures_visible(self):
        self.make_game()
        report=runner.execute(self.project,self.env)
        self.assertIsNotNone(report["a06_result"])
        self.assertTrue(Path(report["a06_report_path"]).is_file())
        self.assertEqual(report["a06_result"]["map_files_expected"],22)
        self.assertEqual(report["a06_result"]["map_files_parsed"],0)
        self.assertEqual(len(report["a06_result"]["map_read_failures"]),22)
        self.assertFalse(report["a06_result"]["can_reserve_mapids"])
        summary=runner.pretty(report)
        self.assertIn("A06",summary)
        self.assertIn("Falhas na leitura de mapas: 22",summary)


if __name__=="__main__":
    unittest.main()
