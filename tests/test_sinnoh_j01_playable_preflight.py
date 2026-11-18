"""J01 native-playable preflight: deterministic read-only tests and tampering denial."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import preflight_sinnoh_playable_j01 as j01

class SinnohJ01Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)
        self.game=self.p/"game"/"Data"
        self.game.mkdir(parents=True)
        for name in ("MapInfos.rxdata","Tilesets.rxdata","Scripts.rxdata","System.rxdata"):
            (self.game/name).write_bytes(b"fixture-metadata-not-native")
        self.src=self.p/"sinnoh-source"
        self.src.mkdir()

    def game_patch(self):
        return patch.object(j01.source_audit, "inspect_native",return_value={
            "status":"LOCAL_READ_ONLY","occupied_count":648,
            "occupied_ids":[1,22,442,600,700], "highest_occupied":700})

    def src_patch(self, *, count=54, template=False):
        return patch.object(j01.source_audit, "inspect_directory",return_value={
            "mode":"LOCAL_DIRECTORY_METADATA_ONLY",
            "project_root_inside_source":"",
            "sha256_zip":None,"map_count":count,
            "source_map_ids":[442,443,444],
            "required_data_present":True,
            "empty_or_template_source":template,
            "source_maps_imported":False,"permission_confirmed":False})

    def test_contract_9_maps_24_events(self):
        c=j01.contracts()
        self.assertEqual(len(c["symbols"]),9)
        self.assertEqual(c["event_counts"],{"warp":16,"handler":5,"starter_ball":3})
        self.assertEqual(c["symbols_bound"],0)

    def test_no_input_fails_without_writes(self):
        r=j01.inspect()
        self.assertEqual(r["status"],"MISSING_INPUTS_OR_NATIVE_EVIDENCE")
        self.assertFalse(r["native_playable"])
        self.assertIn("SOURCE_NOT_PROVIDED",r["blockers"])
        self.assertIn("ABSENT_GAME_DATA",r["blockers"])

    def test_local_game_only_looks_at_metadata(self):
        with self.game_patch():
            r=j01.inspect(game_data=self.game)
        self.assertEqual(r["game"]["occupied_count"],648)
        self.assertEqual(len(r["game"]["mapinfos_sha256"]),64)
        self.assertFalse(r["game_modified"])
        self.assertFalse(r["saves_read_or_modified"])

    def test_two_baselines_recorded_but_not_playable(self):
        with self.game_patch(),self.src_patch():
            r=j01.inspect(game_data=self.game,source=self.src)
        self.assertEqual(r["status"],"BASELINES_OBSERVED_UNVERIFIED")
        self.assertEqual(r["source"]["map_count"],54)
        self.assertEqual(r["unremapped_source_ids_already_occupied_count"],1)
        self.assertFalse(r["can_install"])
        self.assertFalse(r["rights_verified"])
        self.assertFalse(r["runtime_executed"])
        self.assertEqual(r["pilot"]["actual_game_maps_linked"],0)
        self.assertEqual(r["pilot"]["warps_compiled"],0)

    def test_source_is_a_template_not_production(self):
        with self.game_patch(),self.src_patch(count=2,template=True):
            r=j01.inspect(game_data=self.game,source=self.src)
        self.assertEqual(r["source"]["status"],"TEMPLATE_ONLY")
        self.assertEqual(r["status"],"MISSING_INPUTS_OR_NATIVE_EVIDENCE")

    def test_missing_file_never_marks_game_read(self):
        (self.game/"System.rxdata").unlink()
        with self.game_patch():
            r=j01.inspect(game_data=self.game)
        self.assertEqual(r["game"]["status"],"INCOMPLETE")
        self.assertIsNone(r["game"]["mapinfos_sha256"])

    def test_missing_game_directory(self):
        r=j01.inspect(game_data=self.p/"not-there")
        self.assertEqual(r["game"]["status"],"ABSENT")

    def test_source_invalid_stops(self):
        with self.assertRaises(ValueError):
            j01.inspect(source=self.p/"not-there")

    def test_reject_symlink_game_directory(self):
        symlink=self.p/"linked-data"
        try: symlink.symlink_to(self.game,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest("symlinks unavailable")
        with self.assertRaises(ValueError):
            j01.inspect(game_data=symlink)

    def test_reject_symlink_game_file(self):
        file=self.game/"MapInfos.rxdata"
        file.unlink()
        try:file.symlink_to(self.p/"real")
        except (OSError,NotImplementedError):self.skipTest("symlinks unavailable")
        with self.assertRaises(ValueError):
            j01.inspect(game_data=self.game)

    def test_reject_malformed_contract(self):
        with patch.object(j01,"read_json",side_effect=ValueError("corrupt")):
            with self.assertRaises(ValueError):j01.contracts()

    def test_reject_fake_bindings_in_template(self):
        raw=j01.read_json(j01.SOURCE_CONTRACT)
        raw["maps"][0]["map_id"]=444
        raw["maps"][0]["map_sha256"]="0"*64
        spec=j01.SOURCE_CONTRACT
        original=j01.read_json
        def substitute(path):
            return raw if path.name==spec.name else original(path)
        with patch.object(j01,"read_json",side_effect=substitute):
            with self.assertRaises(ValueError):j01.contracts()

    def test_no_save_fields_or_absolute_paths_in_report(self):
        with self.game_patch(),self.src_patch():
            report=j01.inspect(game_data=self.game,source=self.src)
        raw=json.dumps(report)
        self.assertNotIn(str(self.p),raw)
        self.assertNotIn("Save01.rxdata",raw)
        self.assertNotIn("private-baseline",raw)
        self.assertNotIn("game/Data",raw)

    def test_local_report_is_opt_in_non_overwriting(self):
        with self.game_patch(),self.src_patch():
            report=j01.inspect(game_data=self.game,source=self.src)
        j01.write_local_report(self.p,report)
        path=self.p/".blue-work/sinnoh-jogavel/j01-preflight.json"
        self.assertEqual(json.loads(path.read_text())["stage"],"J01")
        with self.assertRaises(FileExistsError):
            j01.write_local_report(self.p,report)
        self.assertTrue((self.game/"MapInfos.rxdata").is_file())

    def test_symlink_output_blocked(self):
        work=self.p/".blue-work"
        try: work.symlink_to(self.game,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest("symlinks unavailable")
        with self.assertRaises(ValueError):
            j01.write_local_report(self.p,{"schema":1})

    def test_main_no_args_fails_closed(self):
        self.assertEqual(j01.main(["--project",str(ROOT)]),2)

    def test_main_rejects_unknown_flags(self):
        with self.assertRaises(SystemExit):
            j01.main(["--execute-game"])

    def test_main_status_zero_only_for_metadata_not_gameplay(self):
        with self.game_patch(),self.src_patch():
            code=j01.main(["--game-data",str(self.game),"--source",str(self.src)])
        self.assertEqual(code,0)

    def test_borrowed_source_native_overlap_not_remapped(self):
        with self.game_patch(),self.src_patch():
            r=j01.inspect(game_data=self.game,source=self.src)
        self.assertEqual(r["unremapped_source_ids_already_occupied_count"],1)
        self.assertFalse(r["mapids_reserved"])

    def test_schema_metadata_not_reviewer_approval(self):
        with self.game_patch(),self.src_patch():
            r=j01.inspect(game_data=self.game,source=self.src)
        self.assertEqual(r["pilot"]["symbols_bound"],0)
        self.assertFalse(r["source_license_accepted"])

if __name__=="__main__":
    unittest.main()
