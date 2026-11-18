"""J07: synthetic-only native Windows QA receipt harness, NEVER executes Game.exe."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"scripts/regions"),str(ROOT/"tests")]
from test_sinnoh_j06_qa_windows import SinnohJ06PrivateWindowsTests
from test_sinnoh_qa_install import simulate_native_report
from install_sinnoh_qa_copy import COMPILED,COMPILE_REQUEST,ENGINE_REPORT
from prepare_sinnoh_playable_j07 import (
    approved_catalog,inspect_private_qa,create_session,check_session,
    record_case,audit_session,session_path,sha_obj,
    G12,SESSION,CASE_DIR,INPUT_DIR,main
)
from prepare_sinnoh_playable_j06 import digest

def save_json(p:Path,obj:dict):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n",
                 encoding="utf-8")
    return p

class J07SyntheticWindowsHarnessTests(unittest.TestCase):
    def setUp(self):
        # Reuse the J06 fixture: all images, maps, EXE and rights declarations
        # are SYNTHETIC, never real sources or native approval.
        self.fixt=SinnohJ06PrivateWindowsTests(
            methodName="test_01_plan_checks_all_nine_synthetic_maps_and_does_not_create_copy")
        self.fixt.setUp()
        self.addCleanup(self.fixt.doCleanups)
        self.root,self.qa=self.fixt.root,self.fixt.qa
        self.receipt=self.fixt.install()["receipt_sha256"]
        self.meta=simulate_native_report(self.qa)
        (self.qa/COMPILED).write_text(self.meta["compile_token"]+"\n",encoding="ascii")
        (self.qa/COMPILE_REQUEST).unlink()
        self.g12_path=self.root/G12
        self.g12_path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/G12,self.g12_path)
        self.pre=self.inspect()
        self.sid="0123456789abcdef"
        self.sess=None
        self.ssha=None

    def inspect(self):
        return inspect_private_qa(
            self.root,self.qa,self.receipt,
            overlay=self.fixt.overlay,spec=self.fixt.specpath,
            rights=self.fixt.rightspath,reservations=self.fixt.reservepath)

    def initialize(self):
        r=create_session(self.root,self.pre,sid=self.sid)
        self.sess=Path(r["session_directory"])
        self.ssha=r["session_sha256"]
        return r

    def attach_case(self,ident,observed=None,attachment_text="synthetic QA log bytes"):
        if self.sess is None:self.initialize()
        dynamic=self.pre["derived"][ident]
        if observed is None:observed=self.valid_observation(dynamic)
        p=save_json(self.sess/INPUT_DIR/(ident+".json"),observed)
        evidence=self.sess/INPUT_DIR/(ident+".txt")
        evidence.write_text(attachment_text,encoding="utf-8")
        return (p,digest(p.read_bytes()),evidence,digest(evidence.read_bytes()))

    def valid_observation(self,case):
        kind=case["kind"]
        o={"platform":"windows","pass":True}
        if kind=="starter":
            o.update(species=case["starter"],second_ball_denied=True)
        elif kind=="barry":
            top=10
            o.update(species=case["opponent"],version=case["version"],
                outcome=case["outcome"],highest_party_level=top,
                enemy_level=top*case["percent"]//100,
                growth_rate_max_level=100,
                enemy_party_size=4 if case["mode"]=="master" else 1)
        elif kind=="save_reload":
            o.update(starter_before=case["starter"],starter_after=case["starter"],
                same_profile_after_reload=True,
                same_party_after_reload=True,pokedex_kept_after_reload=True)
        elif kind=="warp":
            o.update(destination_map_id=case["destination_map_id"],
                arrival_x=case["arrival_x"],arrival_y=case["arrival_y"])
        elif kind=="npc":
            o["handler"]=case["handler"]
        elif kind=="regression":
            o.update(region=case["region"],save_untouched=True)
        else:raise AssertionError(kind)
        return o

    def record(self,ident,observed=None):
        p,ph,log,lh=self.attach_case(ident,observed)
        return record_case(self.root,self.pre,self.sess,self.ssha,ident,p,ph,log,lh)

    def reject_inspect(self):
        with self.assertRaises((ValueError,OSError,KeyError,TypeError)):
            self.inspect()
        self.assertEqual((self.fixt.save).read_bytes(),self.fixt.original_save)

    def test_01_compiled_private_preflight_requires_g12_cases_and_j06_seal(self):
        p=self.pre
        self.assertEqual(len(p["cases"]),44)
        self.assertEqual(len(p["derived"]),44)
        self.assertEqual(len([x for x in p["cases"] if x["platform"]=="windows"]),43)
        self.assertEqual(len([x for x in p["cases"] if x["platform"]=="android"]),1)
        self.assertTrue(p["state"]["save_namespace_verified"])
        self.assertFalse(p["state"]["playable_approved"])
        self.assertEqual((self.fixt.save).read_bytes(),self.fixt.original_save)

    def test_02_init_creates_only_separate_private_session_not_QA_game(self):
        before=set(p.relative_to(self.qa).as_posix() for p in self.qa.rglob("*"))
        r=self.initialize()
        self.assertEqual(r["windows_cases_pending"],43)
        self.assertEqual(r["native_cases_independently_verified"],0)
        self.assertFalse(r["may_publish"])
        self.assertEqual(before,set(p.relative_to(self.qa).as_posix() for p in self.qa.rglob("*")))
        self.assertTrue(self.sess.is_dir())
        self.assertTrue(str(self.sess).startswith(str(self.root/".blue-work")))
        self.assertFalse((self.sess/"Game.exe").exists())

    def test_03_unfilled_audit_does_not_approve_or_create_ready_marker(self):
        self.initialize()
        result=audit_session(self.root,self.pre,self.sess,self.ssha)
        self.assertEqual(result["windows_evidence_submitted_unreviewed"],0)
        self.assertEqual(result["native_windows_cases_independently_verified"],0)
        self.assertEqual(result["native_android_cases_independently_verified"],0)
        self.assertFalse(result["gameplay_approved"])
        self.assertFalse(result["can_publish_or_merge_qa_into_main_game"])
        self.assertFalse((self.qa/"Data/blue-sinnoh-rival-ready.txt").exists())

    def test_04_all_43_windows_observations_are_only_unreviewed(self):
        self.initialize()
        for case in self.pre["cases"]:
            if case["platform"]=="windows":self.record(case["id"])
        result=audit_session(self.root,self.pre,self.sess,self.ssha)
        self.assertEqual(result["windows_evidence_submitted_unreviewed"],43)
        self.assertEqual(sum(result["by_kind_evidence_submitted"].values()),43)
        self.assertEqual(result["g12_android_cases_reserved"],1)
        self.assertEqual(result["native_windows_cases_independently_verified"],0)
        self.assertFalse(result["gameplay_approved"])
        self.assertEqual((self.fixt.save).read_bytes(),self.fixt.original_save)

    def test_05_cannot_create_same_session_twice(self):
        self.initialize()
        with self.assertRaisesRegex(ValueError,"SESSION_ALREADY_EXISTS"):
            self.initialize()

    def test_06_missing_compiled_marker_blocks_qa(self):
        (self.qa/COMPILED).unlink()
        self.reject_inspect()

    def test_07_missing_engine_report_blocks_qa(self):
        (self.qa/ENGINE_REPORT).unlink()
        self.reject_inspect()

    def test_08_tampered_engine_report_blocks_qa(self):
        path=self.qa/ENGINE_REPORT
        data=json.loads(path.read_text("utf-8"))
        data["gameplay_approved"]=True
        save_json(path,data)
        self.reject_inspect()

    def test_09_wrong_j06_receipt_hash_blocks_qa(self):
        self.receipt="a"*64
        self.reject_inspect()

    def test_10_base_mapinfos_mutation_blocks_qa(self):
        p=self.fixt.game/"Data/MapInfos.rxdata"
        p.write_bytes(p.read_bytes()+b"tamper")
        self.reject_inspect()

    def test_11_game_exe_changed_blocks_qa(self):
        (self.fixt.game/"Game.exe").write_bytes(b"tampered fake exe")
        self.reject_inspect()

    def test_12_rights_changed_since_j06_blocks_qa(self):
        self.fixt.review["reviewer_reference"]="DIVERGENT_SYNTHETIC_REVIEW_REFERENCE"
        self.fixt.flush()
        self.reject_inspect()

    def test_13_reserved_ids_changed_since_j06_blocks_qa(self):
        self.fixt.reservations["protected_map_ids"].append(890)
        self.fixt.flush()
        self.reject_inspect()

    def test_14_missing_real_legal_review_blocks_qa(self):
        self.fixt.review["reviewed_locally"]=False
        self.fixt.flush()
        self.reject_inspect()

    def test_15_reserved_mapid_collision_blocks_qa(self):
        self.fixt.reservations["protected_map_ids"].append(500)
        self.fixt.flush()
        self.reject_inspect()

    def test_16_missing_nine_map_source_overlay_blocks_qa(self):
        (self.fixt.overlay/"Data/Map500.rxdata").unlink()
        self.reject_inspect()

    def test_17_fake_g12_completion_refused(self):
        g12=json.loads(self.g12_path.read_text("utf-8"))
        g12["completed_native_cases"]=1
        save_json(self.g12_path,g12)
        self.reject_inspect()

    def test_18_g12_removed_case_refused(self):
        g12=json.loads(self.g12_path.read_text("utf-8"))
        g12["cases"].pop()
        save_json(self.g12_path,g12)
        self.reject_inspect()

    def test_19_duplicate_case_id_refused(self):
        g12=json.loads(self.g12_path.read_text("utf-8"))
        g12["cases"][1]["id"]=g12["cases"][0]["id"]
        save_json(self.g12_path,g12)
        self.reject_inspect()

    def test_20_g12_unapproved_master_scale_refused(self):
        g12=json.loads(self.g12_path.read_text("utf-8"))
        barry=next(x for x in g12["cases"] if x["id"]=="barry-TURTWIG-master-win")
        barry["expected_scaling_percent"]=70
        save_json(self.g12_path,g12)
        self.reject_inspect()

    def test_21_g12_regression_region_removed_refused(self):
        g12=json.loads(self.g12_path.read_text("utf-8"))
        regression=next(x for x in g12["cases"] if x["id"]=="regression-KANTO")
        regression["region"]="UNKNOWN"
        save_json(self.g12_path,g12)
        self.reject_inspect()

    def test_22_missing_android_row_denied(self):
        g12=json.loads(self.g12_path.read_text("utf-8"))
        g12["cases"]=[x for x in g12["cases"] if x["id"]!="android-joi-play"]
        save_json(self.g12_path,g12)
        self.reject_inspect()

    def test_23_unregistered_external_session_rejected(self):
        self.initialize()
        with self.assertRaisesRegex(ValueError,"SESSION_OUTSIDE"):
            audit_session(self.root,self.pre,self.fixt.game,self.ssha)

    def test_24_wrong_session_sha_rejected(self):
        self.initialize()
        with self.assertRaisesRegex(ValueError,"SESSION_MANIFEST_HASH"):
            audit_session(self.root,self.pre,self.sess,"a"*64)

    def test_25_session_manifest_claim_native_approval_rejected(self):
        self.initialize()
        path=self.sess/SESSION
        data=json.loads(path.read_text("utf-8"))
        data["native_gameplay_verified"]=True
        save_json(path,data)
        with self.assertRaises((ValueError,OSError)):
            audit_session(self.root,self.pre,self.sess,self.ssha)

    def test_26_session_manifest_bound_to_original_g12(self):
        self.initialize()
        g12=json.loads(self.g12_path.read_text("utf-8"))
        g12["status"]="FAKE"
        save_json(self.g12_path,g12)
        with self.assertRaises((ValueError,OSError)):
            refreshed=self.inspect()
            audit_session(self.root,refreshed,self.sess,self.ssha)

    def test_27_cannot_record_android_case_in_windows(self):
        self.initialize()
        with self.assertRaisesRegex(ValueError,"ONLY_43_WINDOWS"):
            self.record("android-joi-play")

    def test_28_unknown_case_denied(self):
        self.initialize()
        with self.assertRaisesRegex(ValueError,"ONLY_43_WINDOWS"):
            self.record("barry-UNKNOWN")

    def test_29_duplicate_case_record_denied(self):
        self.record("ball-TURTWIG")
        with self.assertRaisesRegex(ValueError,"CASE_ALREADY_RECORDED"):
            self.record("ball-TURTWIG")

    def test_30_missing_evidence_denied(self):
        self.initialize()
        p,ph,log,lh=self.attach_case("ball-TURTWIG")
        log.unlink()
        with self.assertRaises((ValueError,OSError)):
            record_case(self.root,self.pre,self.sess,self.ssha,
                        "ball-TURTWIG",p,ph,log,lh)

    def test_31_wrong_evidence_sha_denied(self):
        self.initialize()
        p,ph,log,lh=self.attach_case("ball-TURTWIG")
        with self.assertRaisesRegex(ValueError,"EVIDENCE_CHANGED"):
            record_case(self.root,self.pre,self.sess,self.ssha,
                        "ball-TURTWIG",p,"0"*64,log,lh)

    def test_32_evidence_outside_local_session_denied(self):
        self.initialize()
        p,ph,log,lh=self.attach_case("ball-TURTWIG")
        with self.assertRaisesRegex(ValueError,"EVIDENCE_MUST_BE"):
            record_case(self.root,self.pre,self.sess,self.ssha,
                        "ball-TURTWIG",p,ph,self.fixt.save,lh)

    def test_33_wrong_named_observation_denied(self):
        self.initialize()
        p,ph,log,lh=self.attach_case("ball-TURTWIG")
        renamed=p.with_name("other.json");p.rename(renamed)
        with self.assertRaisesRegex(ValueError,"OBSERVATION_FILENAME"):
            record_case(self.root,self.pre,self.sess,self.ssha,
                        "ball-TURTWIG",renamed,digest(renamed.read_bytes()),log,lh)

    def test_34_symlink_evidence_denied(self):
        self.initialize()
        p,ph,log,lh=self.attach_case("ball-TURTWIG")
        link=self.sess/INPUT_DIR/"linked.txt"
        try:link.symlink_to(log)
        except (OSError,NotImplementedError):self.skipTest("symlinks unavailable")
        with self.assertRaises((ValueError,OSError)):
            record_case(self.root,self.pre,self.sess,self.ssha,
                        "ball-TURTWIG",p,ph,link,lh)

    def test_35_bad_starter_duplicate_grant_denied(self):
        case="ball-TURTWIG"
        o=self.valid_observation(self.pre["derived"][case])
        o["second_ball_denied"]=False
        with self.assertRaises((ValueError,OSError)):
            self.record(case,o)

    def test_36_wrong_barry_70_percent_denied(self):
        case="barry-TURTWIG-normal-win"
        o=self.valid_observation(self.pre["derived"][case])
        o["enemy_level"]=9
        with self.assertRaises((ValueError,OSError)):
            self.record(case,o)

    def test_37_wrong_barry_90_percent_denied(self):
        case="barry-CHIMCHAR-master-loss"
        o=self.valid_observation(self.pre["derived"][case])
        o["enemy_level"]=7
        with self.assertRaises((ValueError,OSError)):
            self.record(case,o)

    def test_38_wrong_barry_species_denied(self):
        case="barry-PIPLUP-normal-loss"
        o=self.valid_observation(self.pre["derived"][case])
        o["species"]="PIPLUP"
        with self.assertRaises((ValueError,OSError)):
            self.record(case,o)

    def test_39_wrong_warp_arrival_denied(self):
        case=next(c["id"] for c in self.pre["cases"] if c["kind"]=="warp")
        o=self.valid_observation(self.pre["derived"][case])
        o["arrival_x"]+=1
        with self.assertRaises((ValueError,OSError)):
            self.record(case,o)

    def test_40_wrong_npc_handler_denied(self):
        case=next(c["id"] for c in self.pre["cases"] if c["kind"]=="npc")
        o=self.valid_observation(self.pre["derived"][case])
        o["handler"]="UnknownHandler"
        with self.assertRaises((ValueError,OSError)):
            self.record(case,o)

    def test_41_save_reload_foreign_profile_denied(self):
        case="save-reload-TURTWIG"
        o=self.valid_observation(self.pre["derived"][case])
        o["same_profile_after_reload"]=False
        with self.assertRaises((ValueError,OSError)):
            self.record(case,o)

    def test_42_kanto_regression_save_touched_denied(self):
        case="regression-KANTO"
        o=self.valid_observation(self.pre["derived"][case])
        o["save_untouched"]=False
        with self.assertRaises((ValueError,OSError)):
            self.record(case,o)

    def test_43_gameplay_approval_forged_in_record_denied(self):
        case="ball-TURTWIG"
        self.record(case)
        p=self.sess/CASE_DIR/(case+".json")
        data=json.loads(p.read_text("utf-8"))
        data["independent_native_proof"]=True
        save_json(p,data)
        with self.assertRaisesRegex(ValueError,"CASE_RECORD_TAMPERED"):
            audit_session(self.root,self.pre,self.sess,self.ssha)

    def test_44_recorded_evidence_modified_after_submission_denied(self):
        case="ball-TURTWIG"
        self.record(case)
        p=self.sess/INPUT_DIR/(case+".txt")
        p.write_bytes(p.read_bytes()+b"tamper")
        with self.assertRaisesRegex(ValueError,"RECORDED_EVIDENCE_CHANGED"):
            audit_session(self.root,self.pre,self.sess,self.ssha)

    def test_45_recorded_observation_modified_after_submission_denied(self):
        case="ball-TURTWIG"
        self.record(case)
        p=self.sess/INPUT_DIR/(case+".json")
        p.write_bytes(p.read_bytes()+b"\n")
        with self.assertRaisesRegex(ValueError,"RECORDED_EVIDENCE_CHANGED"):
            audit_session(self.root,self.pre,self.sess,self.ssha)

    def test_46_unknown_record_injected_denied(self):
        self.initialize()
        (self.sess/CASE_DIR/"untrusted.json").write_text("{}")
        with self.assertRaisesRegex(ValueError,"UNEXPECTED_OR_ANDROID"):
            audit_session(self.root,self.pre,self.sess,self.ssha)

    def test_47_android_record_injected_denied(self):
        self.initialize()
        (self.sess/CASE_DIR/"android-joi-play.json").write_text("{}")
        with self.assertRaisesRegex(ValueError,"UNEXPECTED_OR_ANDROID"):
            audit_session(self.root,self.pre,self.sess,self.ssha)

    def test_48_main_cli_without_private_game_fails_closed(self):
        self.assertEqual(main(["--project",str(ROOT),"--qa",str(self.qa),
            "--receipt-sha","0"*64,
            "--overlay",str(self.fixt.overlay),"--spec",str(self.fixt.specpath),
            "--rights",str(self.fixt.rightspath),
            "--reservations",str(self.fixt.reservepath)]),2)

    def test_49_no_real_game_launch_from_non_windows_runner(self):
        if sys.platform=="win32":self.skipTest("Windows ephemeral tests preflight only")
        argv=["--project",str(self.root),"--qa",str(self.qa),
            "--receipt-sha",self.receipt,
            "--overlay",str(self.fixt.overlay),
            "--spec",str(self.fixt.specpath),
            "--rights",str(self.fixt.rightspath),
            "--reservations",str(self.fixt.reservepath),
            "--init"]
        self.assertEqual(main(argv),2)

    def test_50_all_static_checks_do_not_edit_main_saves_or_decades(self):
        self.initialize()
        self.record("ball-TURTWIG")
        audit_session(self.root,self.pre,self.sess,self.ssha)
        self.assertEqual((self.fixt.save).read_bytes(),self.fixt.original_save)
        self.assertEqual((self.fixt.mainmap).read_bytes(),self.fixt.original_map)
        self.assertFalse((self.qa/"Data/blue-sinnoh-rival-ready.txt").exists())
        self.assertFalse((self.qa/"sinnoh-native-playtest.json").exists())

if __name__=="__main__":
    unittest.main()
