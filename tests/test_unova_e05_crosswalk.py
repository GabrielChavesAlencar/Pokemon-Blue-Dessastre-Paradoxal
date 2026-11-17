"""E05 tests: crosswalk is evidence for human review, never an installer."""
from __future__ import annotations
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_unova_e05_crosswalk as crosswalk


def maprow(mid, name, **changes):
    row = {
        "source_map_id":mid, "name":name,
        "source_sha256":format(mid,"064x"),
        "event_count":2, "event_pages":3,
        "static_transfer_commands":1, "dynamic_transfer_commands":0,
        "static_transfer_target_ids":[2],
        "untrusted_script_commands_not_executed":1,
        "candidate_confirmed_as_unova":False,
        "destination_map_id":None, "rights_verified":False,
        "compiled_in_game":False
    }
    row.update(changes)
    return row


def report(maps):
    return {
        "schema":1, "region":"UNOVA", "phase":"U02_E05",
        "mode":"READ_ONLY_INERT_SOURCE_INSPECTION",
        "status":"SOURCE_RXDATA_INSPECTED_NOT_APPROVED",
        "source_zip_sha256":"a"*64, "source_mapinfos_sha256":"b"*64,
        "all_regions_source_map_count":len(maps),
        "confirmed_unova_map_count":None,
        "rights_verified":False, "native_mapinfos_verified":False,
        "can_install":False, "game_or_saves_modified":False,
        "game_exe_tested":False,"android_tested":False,
        "maps":maps, "unresolved_transfer_ids":[999]
    }


class CrosswalkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=json.loads((ROOT/"data/regions/unova-u03-areas.json").read_text("utf-8"))

    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        (self.root/".blue-work/unova/audit").mkdir(parents=True)
        self.out=self.root/".blue-work/unova/audit/e05-crosswalk.json"
        self.rows=[maprow(1,"Nuvema Town"),maprow(2,"Route 1"),
                   maprow(3,"Victory Road"),maprow(4,"Elsewhere")]

    def target(self, output, name):
        return next(x for x in output["areas"] if x["area_key"]==name)

    def test_01_unique_nuvema_is_only_candidate(self):
        o=crosswalk.classify(report(self.rows),self.catalog)
        candidate=self.target(o,"UNOVA_NUVEMA_TOWN")
        self.assertEqual(candidate["status"],"SINGLE_NAME_CANDIDATE_UNCONFIRMED")
        self.assertEqual(candidate["candidate_source_map_ids"],[1])
        self.assertFalse(candidate["region_identity_confirmed"])
        self.assertFalse(candidate["installed"])
        self.assertIsNone(candidate["destination_map_id"])
        self.assertFalse(o["can_install"])
        self.assertEqual(o["confirmed_unova_map_count"],0)
        self.assertEqual(o["symbolic_area_count"],74)

    def test_02_route_name_is_generic_ambiguous(self):
        o=crosswalk.classify(report(self.rows),self.catalog)
        item=self.target(o,"UNOVA_ROUTE_01")
        self.assertEqual(item["status"],"GENERIC_NAME_UNRESOLVED")
        self.assertFalse(item["region_identity_confirmed"])

    def test_03_victory_road_is_generic(self):
        o=crosswalk.classify(report(self.rows),self.catalog)
        self.assertEqual(self.target(o,"UNOVA_VICTORY_ROAD")["status"],"GENERIC_NAME_UNRESOLVED")

    def test_04_duplicate_name_is_ambiguous(self):
        rows=self.rows+[maprow(5,"Nuvema Town")]
        o=crosswalk.classify(report(rows),self.catalog)
        item=self.target(o,"UNOVA_NUVEMA_TOWN")
        self.assertEqual(item["status"],"MULTIPLE_NAME_MATCHES_UNRESOLVED")
        self.assertEqual(item["candidate_source_map_ids"],[1,5])

    def test_05_no_name_match_does_not_prove_missing(self):
        o=crosswalk.classify(report(self.rows),self.catalog)
        self.assertEqual(self.target(o,"UNOVA_NIMBASA_CITY")["status"],
                         "NO_NAME_MATCH_NOT_PROOF_OF_ABSENCE")

    def test_06_reject_claims_that_maps_or_rights_are_installed(self):
        for key,bad in [("can_install",True),("rights_verified",True),
                        ("game_or_saves_modified",True),("game_exe_tested",True)]:
            r=report(self.rows)
            r[key]=bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                crosswalk.classify(r,self.catalog)

    def test_07_fake_map_destination_blocked(self):
        rows=copy.deepcopy(self.rows)
        rows[0]["destination_map_id"]=900
        with self.assertRaises(ValueError):
            crosswalk.classify(report(rows),self.catalog)

    def test_08_duplicate_source_mapid_blocked(self):
        rows=self.rows+[maprow(1,"Driftveil City")]
        with self.assertRaises(ValueError):
            crosswalk.classify(report(rows),self.catalog)

    def test_09_invalid_hash_and_wrong_schema_blocked(self):
        r=report(self.rows)
        r["source_zip_sha256"]="xyz"
        with self.assertRaises(ValueError):
            crosswalk.classify(r,self.catalog)
        r=report(self.rows)
        r["mode"]="READY_FOR_INSTALL"
        with self.assertRaises(ValueError):
            crosswalk.classify(r,self.catalog)

    def test_10_catalog_falsely_playable_blocked(self):
        cat=copy.deepcopy(self.catalog)
        cat["areas"][0]["state"]="playable"
        with self.assertRaises(ValueError):
            crosswalk.classify(report(self.rows),cat)

    def test_11_unknown_malformed_transfer_ids_blocked(self):
        rows=copy.deepcopy(self.rows)
        rows[0]["static_transfer_target_ids"]=[-1]
        with self.assertRaises(ValueError):
            crosswalk.classify(report(rows),self.catalog)

    def test_12_safe_output_and_immutability(self):
        out=crosswalk.classify(report(self.rows),self.catalog)
        crosswalk.save(self.root,self.out,out)
        before=self.out.read_bytes()
        crosswalk.save(self.root,self.out,out)
        self.assertEqual(self.out.read_bytes(),before)
        altered=dict(out,status="INTEGRATED")
        with self.assertRaises(ValueError):
            crosswalk.save(self.root,self.out,altered)
        self.assertEqual(self.out.read_bytes(),before)
        self.assertFalse((self.root/"game").exists())

    def test_13_path_outside_workspace_is_rejected(self):
        with self.assertRaises(ValueError):
            crosswalk.inside(self.root,self.root/"game/Data/Map001.rxdata","audit")

    def test_14_symlink_output_blocked(self):
        elsewhere=self.root/"elsewhere"
        elsewhere.write_text("x")
        try:
            self.out.symlink_to(elsewhere)
        except OSError:
            self.skipTest("symlinks unavailable")
        with self.assertRaises(ValueError):
            crosswalk.save(self.root,self.out,report(self.rows))

if __name__=="__main__":
    unittest.main()
