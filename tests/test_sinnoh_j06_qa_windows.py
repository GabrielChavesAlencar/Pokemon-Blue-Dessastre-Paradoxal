"""J06 Windows QA installer/rollback: SYNTHETIC fixtures only, no Game.exe run.

Nine generated fake maps, PBS, Game.exe bytes, and local mock attestations are
NOT copyright approval, installed maps, native QA, or real-source evidence.
"""
from __future__ import annotations
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
sys.path.insert(0,str(ROOT/"tests"))
from test_sinnoh_qa_install import fixture, PROFILE
from prepare_sinnoh_playable_j06 import (
    create_private_copy,validate_review,receipt_checked,rollback_private_copy,
    qa_copy_path,main,inventory,RECEIPT,digest,
)

def make_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return path

class SinnohJ06PrivateWindowsTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="j06-qa-owned-synthetic-")
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.game,self.overlay,self.spec=fixture(self.root)
        self.work=self.root/".blue-work"
        self.specpath=make_json(self.work/"j06-events.json",self.spec)
        self.report=json.loads((self.overlay/"sinnoh-qa-overlay-report.json").read_text("utf-8"))
        self.exesha=digest((self.game/"Game.exe").read_bytes())
        self.infosh=digest((self.game/"Data/MapInfos.rxdata").read_bytes())
        self.review={
            "schema":1,"region":"SINNOH","stage":"J06",
            "mode":"LOCAL_RIGHTS_REVIEW_NOT_REDISTRIBUTABLE",
            "reviewed_locally":True,
            "redistribution_authorized":False,
            "overlay_report_sha256":digest((self.overlay/"sinnoh-qa-overlay-report.json").read_bytes()),
            "source_game_exe_sha256":self.exesha,
            "source_mapinfos_sha256":self.infosh,
            "spec_sha256":digest(self.specpath.read_bytes()),
            "reviewer_reference":"SYNTHETIC_FIXTURE_ONLY_NO_LICENSE_GRANTED",
            "files":{
                name:{"sha256":sha,"basis":"OWNED_ORIGINAL",
                      "permission_evidence":"SYNTHETIC_GENERATED_TEST_FIXTURE",
                      "private_qa_permitted":True}
                for name,sha in self.report["files_sha256"].items()
            },
        }
        self.reservations={
            "schema":1,"region":"SINNOH","stage":"J06",
            "mode":"PRIVATE_REGIONAL_MAPID_REVIEW",
            "reviewed_locally":True,
            "r07_global_reservations_approved":True,
            "source_mapinfos_sha256":self.infosh,
            "candidate_map_ids":sorted(self.report["geometry_all_map_ids"]),
            "protected_map_ids":[1,300,600,700],
            "reviewer_reference":"SYNTHETIC_LOCAL_QA_ONLY_NO_REAL_R07",
        }
        self.rightspath=self.work/"j06-rights-private.json"
        self.reservepath=self.work/"j06-reservations-private.json"
        self.flush()
        self.qa=qa_copy_path(self.root,PROFILE)
        self.save=self.game/"Saves/File A.rxdata"
        self.original_save=self.save.read_bytes()
        self.mainmap=self.game/"Data/Map001.rxdata"
        self.original_map=self.mainmap.read_bytes()

    def flush(self):
        make_json(self.rightspath,self.review)
        make_json(self.reservepath,self.reservations)

    def plan(self):
        return create_private_copy(self.root,self.overlay,self.specpath,
                                   self.rightspath,self.reservepath,
                                   token=PROFILE,dry_run=True)

    def install(self):
        return create_private_copy(self.root,self.overlay,self.specpath,
                                   self.rightspath,self.reservepath,
                                   token=PROFILE,dry_run=False)

    def blocked(self):
        with self.assertRaises((ValueError,OSError)):
            self.plan()
        self.assertFalse(self.qa.exists())
        self.assertEqual(self.save.read_bytes(),self.original_save)
        self.assertEqual(self.mainmap.read_bytes(),self.original_map)

    def test_01_plan_checks_all_nine_synthetic_maps_and_does_not_create_copy(self):
        r=self.plan()
        self.assertEqual(r["private_map_input_count"],9)
        self.assertEqual(r["events_expected"],24)
        self.assertEqual(r["warps_expected"],16)
        self.assertEqual(r["npc_handlers_expected"],5)
        self.assertEqual(r["starter_balls_expected"],3)
        self.assertTrue(r["private_qa_rights_human_attested"])
        self.assertFalse(r["rights_independently_confirmed_by_chatgpt"])
        self.assertFalse(r["native_barry_pbs_compiled_verified"])
        self.assertFalse(r["can_publish"])
        self.assertFalse(r["game_exe_executed"])
        self.assertFalse(self.qa.exists())

    def test_02_only_pristine_copy_may_rollback(self):
        install=self.install()
        self.assertTrue(self.qa.exists())
        self.assertTrue(install["copy_created"])
        receipt=install["receipt_sha256"]
        r=receipt_checked(self.root,self.qa,receipt,pristine=True)
        self.assertFalse(r["verification"]["playable_approved"])
        self.assertTrue(r["verification"]["save_namespace_verified"])
        self.assertFalse((self.qa/"Saves/File A.rxdata").exists())
        self.assertEqual(self.save.read_bytes(),self.original_save)
        self.assertEqual(self.mainmap.read_bytes(),self.original_map)
        out=rollback_private_copy(self.root,self.qa,receipt,confirm=True)
        self.assertTrue(out["copy_removed"])
        self.assertFalse(out["saves_deleted"])
        self.assertFalse(self.qa.exists())
        self.assertEqual(self.save.read_bytes(),self.original_save)

    def test_03_refuses_rollback_without_explicit_confirmation(self):
        r=self.install()
        with self.assertRaisesRegex(ValueError,"CONFIRMATION"):
            rollback_private_copy(self.root,self.qa,r["receipt_sha256"])
        self.assertTrue(self.qa.exists())

    def test_04_wrong_receipt_sha_does_not_delete(self):
        r=self.install()
        with self.assertRaisesRegex(ValueError,"RECEIPT_CHANGED"):
            rollback_private_copy(self.root,self.qa,"0"*64,confirm=True)
        self.assertTrue(self.qa.exists())

    def test_05_tampered_receipt_cannot_authorize_delete(self):
        r=self.install()
        p=self.qa/RECEIPT
        p.write_bytes(p.read_bytes()+b"changed")
        with self.assertRaisesRegex(ValueError,"RECEIPT_CHANGED"):
            rollback_private_copy(self.root,self.qa,r["receipt_sha256"],confirm=True)
        self.assertTrue(self.qa.exists())

    def test_06_new_save_in_qa_preserved_and_rollback_blocked(self):
        r=self.install()
        save=self.qa/"Saves/File A.rxdata"
        save.parent.mkdir(parents=True)
        save.write_bytes(b"DO NOT DELETE SYNTHETIC USER SAVE")
        with self.assertRaises((ValueError,OSError)):
            rollback_private_copy(self.root,self.qa,r["receipt_sha256"],confirm=True)
        self.assertEqual(save.read_bytes(),b"DO NOT DELETE SYNTHETIC USER SAVE")

    def test_07_modified_copy_preserved_and_rollback_blocked(self):
        r=self.install()
        critical=self.qa/"Game.exe"
        critical.write_bytes(b"changed")
        with self.assertRaises((ValueError,OSError)):
            rollback_private_copy(self.root,self.qa,r["receipt_sha256"],confirm=True)
        self.assertEqual(critical.read_bytes(),b"changed")

    def test_08_extra_qa_file_preserved_and_rollback_blocked(self):
        r=self.install()
        extra=self.qa/"Data/unknown.txt"
        extra.write_bytes(b"foreign extra")
        with self.assertRaisesRegex(ValueError,"QA_CHANGED"):
            rollback_private_copy(self.root,self.qa,r["receipt_sha256"],confirm=True)
        self.assertEqual(extra.read_bytes(),b"foreign extra")

    def test_09_second_install_never_overwrites_qa(self):
        first=self.install()
        with self.assertRaises(ValueError):
            self.install()
        self.assertTrue(self.qa.exists())
        self.assertEqual(digest((self.qa/RECEIPT).read_bytes()),first["receipt_sha256"])

    def test_10_rights_missing_record_is_blocked(self):
        self.review["files"].pop("PBS/trainers_sinnoh_barry.txt")
        self.flush()
        self.blocked()

    def test_11_rights_sha_tampered_is_blocked(self):
        key=next(iter(self.review["files"]))
        self.review["files"][key]["sha256"]="f"*64
        self.flush()
        self.blocked()

    def test_12_rights_unreviewed_is_blocked(self):
        self.review["reviewed_locally"]=False
        self.flush()
        self.blocked()

    def test_13_rights_redistribution_not_assumed(self):
        self.review["redistribution_authorized"]=True
        self.flush()
        self.blocked()

    def test_14_rights_wrong_reference_is_blocked(self):
        self.review["reviewer_reference"]=" "
        self.flush()
        self.blocked()

    def test_15_rights_unsupported_basis_is_blocked(self):
        key=next(iter(self.review["files"]))
        self.review["files"][key]["basis"]="UNKNOWN"
        self.flush()
        self.blocked()

    def test_16_rights_missing_permission_for_one_file_is_blocked(self):
        key=next(iter(self.review["files"]))
        self.review["files"][key]["private_qa_permitted"]=False
        self.flush()
        self.blocked()

    def test_17_rights_overlay_hash_changed_is_blocked(self):
        self.review["overlay_report_sha256"]="a"*64
        self.flush()
        self.blocked()

    def test_18_rights_binds_to_game_exe_hash(self):
        self.review["source_game_exe_sha256"]="a"*64
        self.flush()
        self.blocked()

    def test_19_rights_binds_to_spec_hash(self):
        self.review["spec_sha256"]="a"*64
        self.flush()
        self.blocked()

    def test_20_rights_rejects_symlinked_input(self):
        path=self.rightspath
        path.unlink()
        try: path.symlink_to(self.reservepath)
        except (NotImplementedError,OSError): self.skipTest("Symlink unavailable")
        self.blocked()

    def test_21_review_file_outside_workspace_denied(self):
        with self.assertRaisesRegex(ValueError,"PRIVATE_REVIEW_INPUTS"):
            create_private_copy(self.root,self.overlay,ROOT/"data/regions/sinnoh-twinleaf-events.json",
                self.rightspath,self.reservepath,token=PROFILE)

    def test_22_missing_global_mapid_review_denied(self):
        self.reservations["r07_global_reservations_approved"]=False
        self.flush()
        self.blocked()

    def test_23_reserved_mapid_collision_denied(self):
        mid=self.reservations["candidate_map_ids"][0]
        self.reservations["protected_map_ids"].append(mid)
        self.flush()
        self.blocked()

    def test_24_duplicate_protected_mapids_denied(self):
        self.reservations["protected_map_ids"].append(300)
        self.flush()
        self.blocked()

    def test_25_missing_one_map_from_reservations_denied(self):
        self.reservations["candidate_map_ids"].pop()
        self.flush()
        self.blocked()

    def test_26_wrong_native_mapinfos_sha_denied(self):
        self.reservations["source_mapinfos_sha256"]="f"*64
        self.flush()
        self.blocked()

    def test_27_native_mapid_collision_denied(self):
        # Baseline may include synthetic candidate only after modifying the game;
        # any drift must deny even if the supplied reservation receipt is stale.
        self.game.joinpath("Data/Map500.rxdata").write_bytes(b"occupied")
        self.blocked()

    def test_28_nine_map_spec_incomplete_denied(self):
        spec=copy.deepcopy(self.spec);spec["maps"].pop()
        make_json(self.specpath,spec)
        self.blocked()

    def test_29_one_event_missing_denied(self):
        spec=copy.deepcopy(self.spec);spec["maps"][0]["events"].pop()
        make_json(self.specpath,spec)
        self.blocked()

    def test_30_wrong_mapid_denied(self):
        spec=copy.deepcopy(self.spec)
        spec["maps"][0]["map_id"]=805
        make_json(self.specpath,spec)
        self.blocked()

    def test_31_missing_source_game_exe_denied(self):
        self.game.joinpath("Game.exe").unlink()
        self.blocked()

    def test_32_native_exe_hash_changed_denied(self):
        self.game.joinpath("Game.exe").write_bytes(b"new fake bytes")
        self.blocked()

    def test_33_overlay_file_sha_changed_denied(self):
        self.overlay.joinpath("PBS/trainers_sinnoh_barry.txt").write_bytes(b"modified")
        self.blocked()

    def test_34_extra_overlay_file_denied(self):
        (self.overlay/"junk.dat").write_bytes(b"fake")
        self.blocked()

    def test_35_stage_path_outside_workspace_denied(self):
        with self.assertRaisesRegex(ValueError,"PRIVATE_OVERLAY"):
            self.plan.__func__ if False else validate_review(
                self.root,self.game,self.specpath,self.rightspath,self.reservepath)

    def test_36_missing_input_cli_fails_without_creating_stage(self):
        self.assertEqual(main(["--project",str(self.root)]),2)
        self.assertFalse(self.qa.exists())

    def test_37_windows_only_install_cli_fail_closed_on_linux(self):
        if sys.platform=="win32":self.skipTest("Windows runner tests native-mode guard separately")
        self.assertEqual(main(["--project",str(self.root),"--install",
            "--overlay",str(self.overlay),"--spec",str(self.specpath),
            "--rights",str(self.rightspath),"--reservations",str(self.reservepath)]),2)
        self.assertFalse(self.qa.exists())

    def test_38_qa_copy_must_not_be_main_or_outside_project(self):
        r=self.install()
        for bad in (self.game,self.root):
            with self.assertRaisesRegex(ValueError,"QA_COPY_NOT_ISOLATED"):
                receipt_checked(self.root,bad,r["receipt_sha256"])
        self.assertTrue(self.qa.exists())

    def test_39_pristine_receipt_detects_native_game_change(self):
        r=self.install()
        self.game.joinpath("Game.exe").write_bytes(b"mutated main exe")
        with self.assertRaisesRegex(ValueError,"MAIN_GAME_EXE_CHANGED"):
            receipt_checked(self.root,self.qa,r["receipt_sha256"],pristine=True)
        self.assertTrue(self.qa.exists())

    def test_40_correct_install_is_not_native_gameplay_approval(self):
        r=self.install()
        self.assertFalse(r["native_compilation_executed"])
        self.assertFalse(r["can_publish"])
        self.assertFalse(r["game_exe_executed"])
        check=receipt_checked(self.root,self.qa,r["receipt_sha256"])
        self.assertFalse(check["verification"]["ready_to_launch_for_manual_testing"])
        self.assertFalse(check["verification"]["playable_approved"])
        self.assertFalse((self.qa/"Data/blue-sinnoh-rival-ready.txt").exists())

if __name__=="__main__":
    unittest.main()
