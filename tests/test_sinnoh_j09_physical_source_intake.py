"""J09 source/R07/R08 gates: SYNTHETIC maps, no donor/game/test console execution."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"scripts/regions"),str(ROOT/"tests")]
import test_sinnoh_j03_private_staging as j03_fixture
import audit_sinnoh_playable_j09 as j09
from build_johto_events import ruby,EVENT_CLASSES
from server.ruby_marshal import RubyData
from stage import serialize

def save(path:Path,raw:bytes):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(raw)
    return path

def record(path:Path,obj:dict):
    return save(path,(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode())

class SinnohJ09SyntheticIntakeTests(unittest.TestCase):
    def setUp(self):
        self.fixture=j03_fixture.TestJ03PrivateOverlay(
            methodName="test_real_catalog_remains_four_of_nine_and_no_rights")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.project=self.fixture.root
        self.work=self.project/".blue-work"
        self.work.mkdir(exist_ok=True)
        self.archive=self.work/"test-only-b00-source.zip"
        with zipfile.ZipFile(self.archive,"w",compression=zipfile.ZIP_STORED) as z:
            for p in (self.fixture.source/"Data").iterdir():
                z.write(p,arcname="PrivateSynthetic/Data/"+p.name)
        self.cat=copy.deepcopy(json.loads((ROOT/j09.CATALOG).read_text()))
        self.cat["source_archive_sha256"]=j09.checksum(self.archive.read_bytes())
        self.cat["source_mapinfos_sha256"]=j09.checksum(self.fixture.source_info)
        for row in self.cat["maps"]:
            if row["source_id"] is not None:
                raw=(self.fixture.source/"Data"/f"Map{row['source_id']:03d}.rxdata").read_bytes()
                row["source_sha256"]=j09.checksum(raw)
                row["source_dimensions"]=[3,3]
        self.patcher=patch.object(j09,"source_catalog",return_value=self.cat)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.dir=self.work/j09.STAGE_DIR
        self.dir.mkdir()
        self.missing=[r["symbol"] for r in self.cat["maps"] if r["source_id"] is None]
        self.rights=self.work/"j09-r08-review.json"
        self.r07=self.work/"j09-r07-review.json"
        self.make_five()
        self.make_reviews()

    def fake_map(self,num,*,nonzero=True,events=False):
        w,h=12,10
        values=([384+num]*40+[0]*(w*h*3-40)) if nonzero else [0]*(w*h*3)
        table=RubyData("Table",struct.pack("<5I",3,w,h,3,len(values))+
                       struct.pack("<"+str(len(values))+"H",*values))
        event_map={1:ruby("RPG::Event",pages=[])} if events else {}
        return serialize(ruby("RPG::Map",width=w,height=h,tileset_id=1,
                              data=table,events=event_map),EVENT_CLASSES)

    def make_five(self):
        for i,symbol in enumerate(self.missing):
            save(self.dir/(symbol+".rxdata"),self.fake_map(i))

    def original(self):
        return j09.verify_original_zip(self.archive,self.cat)

    def five(self):
        return j09.authored_five(self.project,self.dir,self.cat)

    def hashes(self):
        return {**{k:v["sha256"] for k,v in self.original()["original_four"].items()},
                **{k:v["sha256"] for k,v in self.five().items()}}

    def make_reviews(self):
        src=self.hashes()
        self.r08doc={
            "schema":1,"region":"SINNOH","stage":"J09",
            "mode":"LOCAL_R08_MAP_RIGHTS_NOT_REDISTRIBUTABLE",
            "locally_reviewed":True,"redistribution_authorized":False,
            "review_reference":"SYNTHETIC_PERMISSIONS_NOT_REAL",
            "maps":{k:{"sha256":v,"basis":"ORIGINAL_USER_AUTHORED",
                       "permission_evidence":"SYNTHETIC_CI_ONLY_NOT_LICENSE",
                       "private_qa_permitted":True} for k,v in src.items()},
        }
        record(self.rights,self.r08doc)
        from bind_sinnoh_playable_j02 import game_inventory
        self.game=self.project/"game"/"Data"
        sha,occupied=game_inventory(self.game)
        self.r07doc={
            "schema":1,"region":"SINNOH","stage":"J09",
            "mode":"LOCAL_R07_RESERVATIONS_NOT_NATIVE_APPROVAL",
            "baseline_mapinfos_sha256":sha,
            "occupied_ids":sorted(occupied),
            "candidate_sinnoh_ids":list(range(442,451)),
            "reserved_by_region":{"DECADES":[100],"KANTO":[300],"JOHTO":[600],
                                  "HOENN":[700],"UNOVA":[518]},
            "locally_reviewed":True,"review_reference":"SYNTHETIC_CASES_NOT_REAL_R07",
        }
        record(self.r07,self.r07doc)

    def audit(self,all_inputs=True):
        return j09.audit(self.project,source=self.archive,
                         authored=self.dir if all_inputs else None,
                         game_data=self.game if all_inputs else None,
                         r07_review=self.r07 if all_inputs else None,
                         r08_review=self.rights if all_inputs else None)

    def refuse(self,pattern=None):
        if pattern:
            with self.assertRaisesRegex(ValueError,pattern):
                self.audit()
        else:
            with self.assertRaises((ValueError,OSError,KeyError,TypeError)):
                self.audit()

    def test_01_four_zip_sources_match_reference_shas(self):
        value=self.original()
        self.assertEqual(len(value["original_four"]),4)
        self.assertEqual(value["archive_sha256"],self.cat["source_archive_sha256"])
        self.assertEqual(value["mapinfos_sha256"],self.cat["source_mapinfos_sha256"])

    def test_02_missing_source_five_stays_blocked(self):
        report=self.audit(all_inputs=False)
        self.assertEqual(report["historical_exteriors_verified_this_run"],4)
        self.assertEqual(report["authored_missing_maps_verified_this_run"],0)
        self.assertEqual(report["total_original_source_candidates_verified"],4)
        self.assertEqual(report["missing_source_symbols"],self.missing)
        self.assertFalse(report["can_install"])

    def test_03_all_nine_synthetic_maps_cannot_approve_native(self):
        r=self.audit()
        self.assertEqual(r["total_original_source_candidates_verified"],9)
        self.assertEqual(r["authored_missing_maps_verified_this_run"],5)
        self.assertEqual(r["status"],"NINE_SOURCE_MAPS_VERIFIED_PRIVATELY_R07_R08_R09_PENDING")
        self.assertFalse(r["native_playable"])
        self.assertFalse(r["can_install"])
        self.assertFalse(r["can_publish"])
        self.assertFalse(r["r07"]["r07_independently_approved"])
        self.assertFalse(r["r08"]["r08_independently_approved"])
        self.assertEqual(r["r09_windows_native_cases_verified"],0)
        self.assertEqual(r["r09_android_joiplay_cases_verified"],0)
        self.assertFalse(r["source_assets_exported"])

    def test_04_catalog_only_no_game_touch(self):
        r=j09.audit(self.project)
        self.assertEqual(r["total_original_source_candidates_verified"],0)
        self.assertEqual(r["historical_exteriors_verified_this_run"],0)
        self.assertFalse(r["native_playable"])
        self.assertFalse(r["main_game_or_saves_modified"])

    def test_05_wrong_donor_map_sha_refused(self):
        self.cat["maps"][2]["source_sha256"]="0"*64
        self.refuse("DONOR_MAP_SHA_DIMENSIONS_OR_GEOMETRY_CHANGED")

    def test_06_donor_archive_truncated_refused(self):
        self.archive.write_bytes(b"not a zip")
        self.refuse()

    def test_07_donor_archive_changed_hash_refused(self):
        self.cat["source_archive_sha256"]="1"*64
        self.refuse("DONOR_ZIP_OR_MAPINFOS_SHA_NOT_B00")

    def test_08_five_maps_folder_missing_refused(self):
        shutil.rmtree(self.dir)
        self.refuse("PRIVATE_AUTHORED_FOLDER_REQUIRED")

    def test_09_four_of_five_authored_rejected(self):
        (self.dir/(self.missing[0]+".rxdata")).unlink()
        self.refuse("ALL_FIVE_EXACT_AUTHORED_MAPS_REQUIRED")

    def test_10_extra_fake_source_file_rejected(self):
        save(self.dir/"Untrusted.rxdata",b"extra")
        self.refuse("ALL_FIVE_EXACT_AUTHORED_MAPS_REQUIRED")

    def test_11_blank_20x15_placeholder_rejected(self):
        save(self.dir/(self.missing[0]+".rxdata"),self.fake_map(1,nonzero=False))
        self.refuse("TERRAIN_EMPTY_OR_PLACEHOLDER")

    def test_12_single_tile_placeholder_rejected(self):
        w,h=12,10
        v=[0]*(w*h*3);v[0]=384
        table=RubyData("Table",struct.pack("<5I",3,w,h,3,len(v))+
                       struct.pack("<"+str(len(v))+"H",*v))
        payload=serialize(ruby("RPG::Map",width=w,height=h,tileset_id=1,
                              data=table,events={}),EVENT_CLASSES)
        save(self.dir/(self.missing[0]+".rxdata"),payload)
        self.refuse("TERRAIN_EMPTY_OR_PLACEHOLDER")

    def test_13_untrusted_script_events_blocked(self):
        save(self.dir/(self.missing[0]+".rxdata"),self.fake_map(0,events=True))
        self.refuse("AUTHORED_SCENE_HAS_FOREIGN_EVENTS")

    def test_14_duplicate_scene_bytes_blocked(self):
        p=self.dir/(self.missing[0]+".rxdata")
        (self.dir/(self.missing[1]+".rxdata")).write_bytes(p.read_bytes())
        self.refuse("DUPLICATED_MAP_BYTES_NOT_DISTINCT_SCENE")

    def test_15_fake_non_marshal_map_rejected(self):
        save(self.dir/(self.missing[0]+".rxdata"),b"not real marshal source")
        self.refuse()

    def test_16_symlink_to_another_map_rejected(self):
        first=self.dir/(self.missing[0]+".rxdata")
        first.unlink()
        try:first.symlink_to(self.dir/(self.missing[1]+".rxdata"))
        except (OSError,NotImplementedError):self.skipTest("symlink creation unavailable")
        self.refuse("SYMLINK_OR_DIRECTORY|PRIVATE_AUTHORED")

    def test_17_maps_must_stay_in_private_blue_work(self):
        self.dir=self.fixture.source/"Data"
        self.refuse("PRIVATE_AUTHORED_MAPS_PATH_REQUIRED")

    def test_18_r07_mapid_collides_with_candidate(self):
        self.r07doc["reserved_by_region"]["KANTO"].append(442)
        record(self.r07,self.r07doc)
        self.refuse("R07_SINNOH_MAPID_COLLISION_OR_FABRICATION")

    def test_19_r07_mapid_overlaps_hoenn(self):
        self.r07doc["reserved_by_region"]["HOENN"].append(300)
        record(self.r07,self.r07doc)
        self.refuse("R07_OVERLAPPING_REGIONAL_RESERVATIONS")

    def test_20_r07_baseline_must_match_current_mapinfos(self):
        self.r07doc["baseline_mapinfos_sha256"]="0"*64
        record(self.r07,self.r07doc)
        self.refuse("R07_BASELINE_OR_HUMAN_REVIEW_MISSING")

    def test_21_r07_unapproved_local_review_rejected(self):
        self.r07doc["locally_reviewed"]=False
        record(self.r07,self.r07doc)
        self.refuse("R07_BASELINE_OR_HUMAN_REVIEW_MISSING")

    def test_22_r07_missing_future_region_rejected(self):
        self.r07doc["reserved_by_region"].pop("UNOVA")
        record(self.r07,self.r07doc)
        self.refuse("R07_REGION_COVERAGE_INCOMPLETE")

    def test_23_r07_occupied_changed_baseline_detected(self):
        self.r07doc["occupied_ids"].append(999)
        record(self.r07,self.r07doc)
        self.refuse("R07_BASELINE_OR_HUMAN_REVIEW_MISSING")

    def test_24_r07_invalid_destination_range_rejected(self):
        self.r07doc["candidate_sinnoh_ids"][0]=600
        record(self.r07,self.r07doc)
        self.refuse("R07_SINNOH_MAPID_COLLISION_OR_FABRICATION")

    def test_25_r08_file_sha_wrong_rejected(self):
        self.r08doc["maps"][self.missing[0]]["sha256"]="0"*64
        record(self.rights,self.r08doc)
        self.refuse("R08_RIGHTS_MISSING_OR_MAP_SHA_CHANGED")

    def test_26_r08_missing_permission_rejected(self):
        self.r08doc["maps"][self.missing[0]]["private_qa_permitted"]=False
        record(self.rights,self.r08doc)
        self.refuse("R08_RIGHTS_MISSING_OR_MAP_SHA_CHANGED")

    def test_27_r08_missing_author_rejected(self):
        self.r08doc["maps"].pop(self.missing[0])
        record(self.rights,self.r08doc)
        self.refuse("R08_NINE_MAPS_PER_ASSET_REQUIRED")

    def test_28_r08_unreviewed_rejected(self):
        self.r08doc["locally_reviewed"]=False
        record(self.rights,self.r08doc)
        self.refuse("R08_LOCAL_REVIEW_REQUIRED")

    def test_29_r08_redistribution_flag_rejected(self):
        self.r08doc["redistribution_authorized"]=True
        record(self.rights,self.r08doc)
        self.refuse("R08_LOCAL_REVIEW_REQUIRED")

    def test_30_r08_mismatch_rewritten_map_rejected(self):
        first=self.dir/(self.missing[0]+".rxdata")
        save(first,self.fake_map(8))
        self.refuse("R08_RIGHTS_MISSING_OR_MAP_SHA_CHANGED")

    def test_31_require_complete_refuses_missing_source(self):
        status=j09.main(["--project",str(ROOT),"--require-complete"])
        self.assertEqual(status,2)

    def test_32_report_must_stay_private(self):
        with self.assertRaisesRegex(ValueError,"REPORT_MUST_STAY_UNDER_BLUE_WORK"):
            j09.save_private_receipt(self.project,self.work/"private" / "report.json",self.audit())

    def test_33_report_never_overwrites_existing(self):
        dest=self.work/"sinnoh-j09-source-intake.json"
        j09.save_private_receipt(self.project,dest,self.audit())
        with self.assertRaisesRegex(ValueError,"NO_REPORT_OVERWRITE"):
            j09.save_private_receipt(self.project,dest,self.audit())

    def test_34_report_is_sanitized_metadata_only(self):
        report=self.audit()
        out=self.work/"sinnoh-j09-source-intake.json"
        j09.save_private_receipt(self.project,out,report)
        value=out.read_text("utf-8")
        self.assertIn("SINNOH_PLAYER_BEDROOM",value)
        self.assertNotIn("RPG::Map",value)
        self.assertNotIn("Game.exe",value)
        self.assertFalse((self.project/"game"/"Save01.rxdata").exists() is False)
        self.assertEqual(value.count("native_playable"),1)

    def test_35_private_review_cannot_be_read_outside_workspace(self):
        self.rights=self.project/"public-review.json"
        self.refuse("PRIVATE_REVIEW_PATH_REQUIRED")

if __name__=="__main__":
    unittest.main()
