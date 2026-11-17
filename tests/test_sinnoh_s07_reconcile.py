"""S07: deterministic remap reconciliation, reservations, stage and rollback safety."""
from __future__ import annotations
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from plan_sinnoh_remap import make_plan
from sinnoh_s07_reconcile import reconcile, main
from sinnoh_staging_transaction import preview,stage,rollback
from server.ruby_marshal import RubyObject
from stage import serialize

def audited():
    return {
      "schema":1,"region":"SINNOH","mode":"READ_ONLY_INERT_RMXP",
      "import_allowed":False,"source_map_ids":[7,8],
      "source_zip_sha256":"f"*64,
      "mapinfos_sha256":"c"*64,"tilesets_sha256":"d"*64,
      "native":{"status":"LOCAL_READ_ONLY","occupied_ids":[1]},
      "maps":[
        {"source_id":7,"name":"Test start","sha256":"a"*64,"transfer_targets":[8]},
        {"source_id":8,"name":"Test door","sha256":"b"*64,"transfer_targets":[7]},
      ],
      "missing_map_files":[],"orphan_map_files":[],
      "unresolved_static_transfer_ids":[],"missing_graphics":[],
      "invalid_graphic_names":[],"dynamic_transfer_commands":1,
      "untrusted_script_commands_not_executed":2,
    }

def request():
    return {
      "schema":1,"region":"SINNOH","source_zip_sha256":"f"*64,
      "source_mapinfos_sha256":"c"*64,"source_tilesets_sha256":"d"*64,
      "source_map_hashes":{"7":"a"*64,"8":"b"*64},
      "mapping":{"7":500,"8":501},
      "symbols":{"7":"SINNOH_TEST_START","8":"SINNOH_TEST_ROOM"},
    }

class SinnohS07ReconcileTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="sinnoh-s07-")
        self.addCleanup(tmp.cleanup)
        self.project=Path(tmp.name)
        self.work=self.project/".blue-work"
        self.work.mkdir()
        data=self.project/"game"/"Data"
        data.mkdir(parents=True)
        baseline=serialize({1:RubyObject("RPG::MapInfo",{"@name":b"Decades"})})
        (data/"MapInfos.rxdata").write_bytes(baseline)
        (data/"Map001.rxdata").write_bytes(b"STILL PROTECTED")
        self.base_sha=hashlib.sha256(baseline).hexdigest()
        self.audit=audited()
        self.plan=make_plan(self.audit,request())

    def reservations(self,extra=None):
        folder=self.work/"sinnoh-reservations"
        folder.mkdir(exist_ok=True)
        for region,ids in (("KANTO",[200]),("JOHTO",[600]),("HOENN",[300])):
            if extra and region in extra:ids=extra[region]
            (folder/(region.lower()+".json")).write_text(json.dumps({
              "schema":1,"region":region,
              "kind":"LOCAL_FUTURE_MAP_ID_RESERVATIONS",
              "baseline_mapinfos_sha256":self.base_sha,
              "future_reserved_map_ids":ids,
              "ownership_evidence":"Reviewed locally with source manifest",
              "reviewed_locally":True,"read_only":True,
            }),encoding="utf-8")

    def test_01_missing_future_reservations_is_blocked(self):
        r=reconcile(self.project,self.audit,self.plan)
        self.assertEqual(r["future_regions_with_evidence"],0)
        self.assertFalse(r["candidate_safety_reviewable"])
        self.assertFalse(r["r07_complete"])

    def test_02_full_snapshot_is_still_only_manual_review(self):
        self.reservations()
        r=reconcile(self.project,self.audit,self.plan)
        self.assertTrue(r["candidate_safety_reviewable"])
        self.assertEqual(r["status"],"RECONCILED_FOR_MANUAL_REVIEW_NOT_APPROVED")
        self.assertEqual(r["static_transfer_rewrites"],2)
        self.assertEqual(r["source_maps"],2)
        for field in ("r07_complete","r08_real_maps_imported",
                      "r09_game_exe_joiplay_tested","can_install",
                      "source_assets_copied","main_game_or_saves_modified"):
            self.assertFalse(r[field])

    def test_03_future_reserved_collision(self):
        self.reservations({"HOENN":[501]})
        r=reconcile(self.project,self.audit,self.plan)
        self.assertFalse(r["candidate_safety_reviewable"])
        self.assertIn({"id":501,"reason":"FUTURE_RESERVED_HOENN"},r["collisions"])

    def test_04_stale_native_baseline_blocks(self):
        self.reservations()
        (self.project/"game/Data/Map002.rxdata").write_bytes(b"NEW NATIVE MAP")
        with self.assertRaisesRegex(ValueError,"SINNOH_S07_RECONCILE_BLOCKED"):
            reconcile(self.project,self.audit,self.plan)

    def test_05_plan_map_id_tamper_without_resigning(self):
        p=copy.deepcopy(self.plan);p["mapping"]["7"]=503
        with self.assertRaisesRegex(ValueError,"SINNOH_S07_RECONCILE_BLOCKED"):
            reconcile(self.project,self.audit,p)

    def test_06_plan_transfer_tamper(self):
        p=copy.deepcopy(self.plan);p["proposed_static_transfer_rewrites"].pop()
        with self.assertRaisesRegex(ValueError,"SINNOH_S07_RECONCILE_BLOCKED"):
            reconcile(self.project,self.audit,p)

    def test_07_plan_rehashed_but_would_miss_source_proof(self):
        p=copy.deepcopy(self.plan);p["maps"][0]["source_map_sha256"]="0"*64
        p["plan_sha256"]=hashlib.sha256(json.dumps({
            k:v for k,v in p.items() if k!="plan_sha256"},sort_keys=True,
            ensure_ascii=True,separators=(",",":")).encode("ascii")).hexdigest()
        with self.assertRaisesRegex(ValueError,"SINNOH_S07_RECONCILE_BLOCKED"):
            reconcile(self.project,self.audit,p)

    def test_08_forged_native_approval(self):
        for key in ("can_install","may_stage_real_map_data",
                    "other_region_reservations_fully_verified","game_or_saves_modified"):
            with self.subTest(key=key):
                p=copy.deepcopy(self.plan);p[key]=True
                with self.assertRaisesRegex(ValueError,"SINNOH_S07_RECONCILE_BLOCKED"):
                    reconcile(self.project,self.audit,p)

    def test_09_bad_source_audit_or_hash(self):
        a=copy.deepcopy(self.audit);a["maps"][0]["sha256"]="0"*64
        with self.assertRaises(ValueError):reconcile(self.project,a,self.plan)

    def test_10_prior_map_freeze_is_checked(self):
        prior=copy.deepcopy(self.plan)
        self.reservations()
        self.assertTrue(reconcile(self.project,self.audit,self.plan,prior)["candidate_safety_reviewable"])
        bad=copy.deepcopy(prior);bad["mapping"]["7"]=505
        with self.assertRaises(ValueError):reconcile(self.project,self.audit,self.plan,bad)

    def test_11_protected_destination_rejected_by_original_planner(self):
        req=request();req["mapping"]["7"]=600
        with self.assertRaises(ValueError):make_plan(self.audit,req)
        req=request();req["mapping"]["7"]=1
        with self.assertRaises(ValueError):make_plan(self.audit,req)

    def test_12_no_file_writes_even_on_repeated_reconciliation(self):
        self.reservations()
        before={p.relative_to(self.project).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.project.rglob("*") if p.is_file()}
        for _ in range(3):reconcile(self.project,self.audit,self.plan)
        after={p.relative_to(self.project).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
               for p in self.project.rglob("*") if p.is_file()}
        self.assertEqual(before,after)

    def test_13_stage_preview_and_hash_bound_rollback(self):
        payload={"Data/Map500.rxdata":b"SYNTHETIC","Data/MapInfos.rxdata":b"SYNTHETIC2"}
        dry=preview(self.project,"s07-test",payload)
        created=stage(self.project,"s07-test",payload,dry["plan_sha256"])
        self.assertTrue(created["stage_created"])
        folder=self.project/dry["stage_relative_path"]
        self.assertTrue(folder.is_dir())
        with self.assertRaises(ValueError):rollback(self.project,"s07-test","0"*64)
        self.assertTrue(rollback(self.project,"s07-test",dry["plan_sha256"])["removed_only_stage"])
        self.assertFalse(folder.exists())

    def test_14_tampered_manifest_new_path_blocks_delete(self):
        payload={"Data/Map500.rxdata":b"SYNTHETIC"}
        dry=preview(self.project,"s07-tamper",payload)
        stage(self.project,"s07-tamper",payload,dry["plan_sha256"])
        folder=self.project/dry["stage_relative_path"]
        manifest=folder/"stage-manifest.json"
        raw=manifest.read_bytes()
        bad=json.loads(raw);bad["stage_relative_path"]="../../game"
        manifest.write_text(json.dumps(bad),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"Assinatura|alterado"):
            rollback(self.project,"s07-tamper",dry["plan_sha256"])
        self.assertTrue(folder.is_dir())
        manifest.write_bytes(raw)
        rollback(self.project,"s07-tamper",dry["plan_sha256"])

    def test_15_unknown_dir_or_extra_file_blocks_rollback(self):
        payload={"Data/Map501.rxdata":b"SYNTHETIC"}
        dry=preview(self.project,"s07-extra",payload)
        stage(self.project,"s07-extra",payload,dry["plan_sha256"])
        folder=self.project/dry["stage_relative_path"]
        extra=folder/"Graphics"/"Unexpected"
        extra.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError,"pasta inesperada"):
            rollback(self.project,"s07-extra",dry["plan_sha256"])
        extra.rmdir();extra.parent.rmdir()
        rollback(self.project,"s07-extra",dry["plan_sha256"])

    def test_16_file_size_and_source_hash_enforced_by_rollback(self):
        payload={"Data/Map502.rxdata":b"SYNTHETIC"}
        dry=preview(self.project,"s07-hash",payload)
        stage(self.project,"s07-hash",payload,dry["plan_sha256"])
        folder=self.project/dry["stage_relative_path"]
        p=folder/"Data/Map502.rxdata"
        p.write_bytes(b"CHANGED")
        with self.assertRaisesRegex(ValueError,"Stage modificado"):
            rollback(self.project,"s07-hash",dry["plan_sha256"])
        p.write_bytes(payload["Data/Map502.rxdata"])
        rollback(self.project,"s07-hash",dry["plan_sha256"])

    def test_17_cli_rejects_json_outside_workspace(self):
        location=self.project/"candidate.json"
        location.write_text(json.dumps(self.plan),encoding="utf-8")
        audit=self.work/"audit.json"
        audit.write_text(json.dumps(self.audit),encoding="utf-8")
        rc=main(["--project",str(self.project),
                 "--source-audit",str(audit),"--candidate",str(location)])
        self.assertEqual(rc,2)

    def test_18_staging_missing_source_never_touches_main(self):
        self.assertFalse((self.project/"game/Data/Map500.rxdata").exists())
        r=reconcile(self.project,self.audit,self.plan)
        self.assertFalse(r["r08_real_maps_imported"])
        self.assertFalse((self.project/"game/Data/Map500.rxdata").exists())

    def test_19_status_only_code_and_native_gates_unchanged(self):
        p=json.loads((ROOT/"data/regions/sinnoh-progress.json").read_text("utf-8"))
        self.assertEqual((p["development"]["done"],p["development"]["partial"],
                          p["development"]["pending"],p["development"]["percent_complete"]),
                         (29,3,0,90))
        self.assertEqual(next(x["status"] for x in p["tasks"] if x["id"]=="S07"),"done")
        self.assertEqual(p["remap_workstream"]["complete"],6)
        self.assertEqual(p["remap_workstream"]["total"],9)
        self.assertEqual(p["remap_workstream"]["status"],"PARTIAL_NOT_INSTALLABLE")
        self.assertEqual(p["phase_gates"]["playable_in_game_executable"],0)
        self.assertEqual(p["phase_gates"]["fully_tested_native"],0)

if __name__=="__main__":unittest.main()
