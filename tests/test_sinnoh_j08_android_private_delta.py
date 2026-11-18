"""J08: SYNTHETIC fixture-only Android delta tests, no JoiPlay, saves, ROM, or network."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"scripts/regions"),str(ROOT/"tests")]
from test_sinnoh_j07_windows_harness import J07SyntheticWindowsHarnessTests,save_json
from prepare_sinnoh_playable_j06 import file_digest, digest
import prepare_sinnoh_playable_j08 as j08

def write(path:Path,data:bytes):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data)
    return path

class J08SyntheticAndroidDeltaTests(unittest.TestCase):
    def setUp(self):
        # J07's synthetic fixture has a fake Game.exe and mock rights. This
        # is deliberately NOT evidence of real play or legal permission.
        self.fx=J07SyntheticWindowsHarnessTests(methodName=
            "test_01_compiled_private_preflight_requires_g12_cases_and_j06_seal")
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.fx.initialize()
        for row in self.fx.pre["cases"]:
            if row["platform"]=="windows":self.fx.record(row["id"])
        self.root=self.fx.root
        self.work=self.root/".blue-work"
        self.token=self.fx.qa.name[-12:]
        self.base=self.work/("sinnoh-j08-android-base-"+self.token)
        self.stage=self.work/("sinnoh-j08-android-qa-"+self.token)
        self.profile={
            "dataPathApp":"Sinnoh-QA-Android-"+self.token,
            "dataPathOrg":"Dessastre-Sinnoh-Android-QA-"+self.token,
            "windowTitle":"Sinnoh Android QA "+self.token,
        }
        for directory in (self.base,self.stage):
            directory.mkdir()
            save_json(directory/"mkxp.json",self.profile)
            write(directory/"Game.ini",
                  ("[Game]\nTitle="+self.profile["windowTitle"]+"\n").encode())
        for name,data in (
            ("Data/MapInfos.rxdata",b"SYNTHETIC BASE ANDROID MAPINFOS"),
            ("Data/System.rxdata",b"SYNTHETIC ANDROID BASE SYSTEM"),
            ("Data/PluginScripts.rxdata",b"SYNTHETIC ANDROID BASE CACHE"),
        ):
            write(self.base/name,data)
            write(self.stage/name,data)
        # The private target is a *fresh compiled candidate*, not an applied
        # update. Do not change or delete any baseline files.
        from_qa=["Data/MapInfos.rxdata","Data/System.rxdata"]
        maps=[f"Data/Map{row['id']:03d}.rxdata"
              for row in self.fx.meta["event_contract"]]
        self.maps=maps
        extras=["PBS/trainers_sinnoh_barry.txt",
                "PBS/trainer_types_sinnoh_barry.txt"]
        sprites=sorted({f"Graphics/Characters/{e['sprite']}.png"
            for m in self.fx.meta["event_contract"] for e in m["events"]
            if e["kind"] in ("handler","starter_ball")})
        plugins=[p.relative_to(self.fx.qa).as_posix()
                 for p in (self.fx.qa/"Plugins").rglob("SinnohPilot.rb")]
        self.plugins=plugins
        self.assertEqual(len(plugins),1)
        for rel in from_qa+maps+extras+sprites+plugins:
            write(self.stage/rel,(self.fx.qa/rel).read_bytes())
        write(self.stage/"Data/PluginScripts.rxdata",
              b"SYNTHETIC_COMPILED_ANDROID_PLUGIN_CACHE_NOT_A_REAL_GAME")
        self.windows_review=self.work/"j08-windows-review.json"
        self.android_review=self.work/"j08-android-review.json"
        self.win={
            "schema":1,"region":"SINNOH","stage":"J08",
            "mode":j08.REVIEW_MODES["windows"],
            "session_sha256":self.fx.ssha,
            "j06_receipt_sha256":self.fx.receipt,
            "independent_human_reviewed":True,
            "reviewer_reference":"SYNTHETIC_ONLY_NO_REAL_WINDOWS_RUN",
            "cases":{r["id"]:{
                    "record_sha256":file_digest(
                        self.fx.sess/"records"/(r["id"]+".json")),
                    "evidence_checked":True,
                    "native_windows_run_observed":True,
                 } for r in self.fx.pre["cases"] if r["platform"]=="windows"},
        }
        save_json(self.windows_review,self.win)
        self.refresh_android_review()

    def refresh_android_review(self):
        target,profile,_=j08.inspect_snapshot(self.root,self.stage,"qa")
        base,_,_=j08.inspect_snapshot(self.root,self.base,"base")
        changed={k:v for k,v in target.items() if base.get(k)!=v}
        self.andreview={
            "schema":1,"region":"SINNOH","stage":"J08",
            "mode":j08.REVIEW_MODES["android"],
            "reviewed_locally":True,
            "redistribution_authorized":False,
            "j06_receipt_sha256":self.fx.receipt,
            "j07_session_sha256":self.fx.ssha,
            "windows_review_sha256":file_digest(self.windows_review),
            "android_stage_profile_sha256":profile["sha256"],
            "android_plugin_cache_sha256":target["Data/PluginScripts.rxdata"]["sha256"],
            "android_mapinfos_sha256":target["Data/MapInfos.rxdata"]["sha256"],
            "reviewer_reference":"SYNTHETIC_ANDROID_TEST_REVIEW_NOT_LICENSE",
            "files":{rel:{"sha256":info["sha256"],
                          "permission_evidence":"SYNTHETIC_GENERATED_TEST_ONLY",
                          "private_qa_permitted":True}
                     for rel,info in changed.items()}
        }
        save_json(self.android_review,self.andreview)

    def call(self):
        return j08.preflight(
            self.root,self.fx.qa,self.fx.receipt,
            self.fx.fixt.overlay,self.fx.fixt.specpath,
            self.fx.fixt.rightspath,self.fx.fixt.reservepath,
            self.fx.sess,self.fx.ssha,self.windows_review,
            self.stage,self.base,self.android_review)

    def blocked(self,contains=None):
        if contains is None:
            with self.assertRaises((OSError,ValueError,TypeError,KeyError)):
                self.call()
        else:
            with self.assertRaisesRegex((OSError,ValueError,TypeError,KeyError),contains):
                self.call()
        self.assertFalse((self.work/"sinnoh-j08-candidates").exists())
        self.assertEqual(self.fx.fixt.save.read_bytes(),self.fx.fixt.original_save)

    def test_01_preflight_full_private_delta_only(self):
        p=self.call()
        out=j08.plan(p)
        self.assertTrue(out["no_backup"])
        self.assertTrue(out["no_saves_read"])
        self.assertEqual(out["real_joiplay_cases_verified"],0)
        self.assertFalse(out["can_publish"])
        self.assertTrue(set(self.maps).issubset(set(p["changed"])))
        self.assertEqual(p["windows_evidence_files_present"],43)
        self.assertFalse(p["windows_native_independently_verified_by_chatgpt"])
        self.assertFalse((self.work/"sinnoh-j08-candidates").exists())

    def test_02_only_changed_assets_in_zip_no_game_ini_or_saves(self):
        p=self.call()
        out=j08.package(self.root,p)
        self.assertEqual(out["status"],"PRIVATE_QA_DELTA_CREATED_UNRELEASED")
        self.assertFalse(out["joiplay_real_test_executed"])
        self.assertFalse(out["main_android_install_modified"])
        f=Path(out["path"])
        with zipfile.ZipFile(f) as z:
            names=z.namelist()
            self.assertEqual(set(names)-{"J08-delta.json"},set(p["changed"]))
            self.assertNotIn("Game.ini",names)
            self.assertNotIn("mkxp.json",names)
            self.assertFalse(any("Save" in n or n.endswith(".exe") for n in names))
            descriptor=json.loads(z.read("J08-delta.json"))
            self.assertTrue(descriptor["no_deletions"])
            self.assertTrue(descriptor["no_backup_created"])
            self.assertFalse(descriptor["joiplay_real_test_executed"])
        self.assertTrue(j08.verify_candidate(self.root,f,out["zip_sha256"])["verified_zip_structure"])
        self.assertEqual(self.fx.fixt.save.read_bytes(),self.fx.fixt.original_save)

    def test_03_identical_baseline_files_absent_from_delta(self):
        p=self.call()
        self.assertNotIn("mkxp.json",p["changed"])
        self.assertNotIn("Game.ini",p["changed"])
        self.assertNotIn("Data/System.rxdata",p["changed"])
        self.assertEqual(p["previous"]["Data/System.rxdata"],
                         p["target"]["Data/System.rxdata"])

    def test_04_can_discard_only_unapplied_candidate(self):
        out=j08.package(self.root,self.call())
        f=Path(out["path"])
        with self.assertRaisesRegex(ValueError,"EXPLICIT_DISCARD"):
            j08.discard_candidate(self.root,f,out["zip_sha256"],False)
        self.assertTrue(f.is_file())
        removed=j08.discard_candidate(self.root,f,out["zip_sha256"],True)
        self.assertTrue(removed["discarded_only_unapplied_zip"])
        self.assertFalse(f.exists())
        self.assertEqual(self.fx.fixt.save.read_bytes(),self.fx.fixt.original_save)

    def test_05_bad_zip_sha_refuses_verify_and_discard(self):
        out=j08.package(self.root,self.call())
        f=Path(out["path"])
        with self.assertRaisesRegex(ValueError,"ANDROID_DELTA_SHA_MISMATCH"):
            j08.verify_candidate(self.root,f,"0"*64)
        with self.assertRaisesRegex(ValueError,"ANDROID_DELTA_SHA_MISMATCH"):
            j08.discard_candidate(self.root,f,"0"*64,True)
        self.assertTrue(f.exists())

    def test_06_missing_five_map_file_refused(self):
        (self.stage/self.maps[0]).unlink()
        self.blocked("ANDROID_NINE_PHYSICAL_RXDATA_MISSING")

    def test_07_stale_map_byte_against_j06_refused(self):
        (self.stage/self.maps[0]).write_bytes(b"stale fake map")
        self.refresh_android_review()
        self.blocked("ANDROID_MAP_PBS_OR_SPRITE_DIFFERS_FROM_J06")

    def test_08_changed_barry_pbs_refused(self):
        (self.stage/"PBS/trainers_sinnoh_barry.txt").write_bytes(b"stale synthetic")
        self.refresh_android_review()
        self.blocked("ANDROID_MAP_PBS_OR_SPRITE_DIFFERS_FROM_J06")

    def test_09_missing_blue_pilot_plugin_refused(self):
        (self.stage/self.plugins[0]).unlink()
        self.blocked("ANDROID_BLUE_SINNOH_PLUGIN_MISSING")

    def test_10_missing_sprite_refused(self):
        found=next((self.stage/"Graphics/Characters").glob("*.png"))
        found.unlink()
        self.blocked("ANDROID_NPC_STARTER_ARTWORK_MISSING")

    def test_11_cache_sha_change_not_approved_refused(self):
        (self.stage/"Data/PluginScripts.rxdata").write_bytes(b"tamper cached compiled")
        self.blocked("ANDROID_PRIVATE_RIGHTS_PER_FILE_MISSING")

    def test_12_wrong_mapinfos_hash_refused(self):
        self.andreview["android_mapinfos_sha256"]="0"*64
        save_json(self.android_review,self.andreview)
        self.blocked("ANDROID_PRIVATE_RIGHTS_PER_FILE_MISSING")

    def test_13_per_file_rights_missing_refused(self):
        self.andreview["files"].pop(self.maps[0])
        save_json(self.android_review,self.andreview)
        self.blocked("ANDROID_PRIVATE_RIGHTS_PER_FILE_MISSING")

    def test_14_false_permission_for_map_refused(self):
        self.andreview["files"][self.maps[0]]["private_qa_permitted"]=False
        save_json(self.android_review,self.andreview)
        self.blocked("ANDROID_ASSET_PERMISSION_OR_HASH_INVALID")

    def test_15_wrong_file_sha_permission_refused(self):
        self.andreview["files"][self.maps[0]]["sha256"]="a"*64
        save_json(self.android_review,self.andreview)
        self.blocked("ANDROID_ASSET_PERMISSION_OR_HASH_INVALID")

    def test_16_no_windows_independent_human_review_refused(self):
        self.win["independent_human_reviewed"]=False
        save_json(self.windows_review,self.win)
        self.blocked("INDEPENDENT_NATIVE_WINDOWS_HUMAN_REVIEW_MISSING")

    def test_17_only_42_windows_cases_denied(self):
        self.win["cases"].pop(next(iter(self.win["cases"])))
        save_json(self.windows_review,self.win)
        self.blocked("43_WINDOWS_CASE_REVIEWS_REQUIRED")

    def test_18_fake_windows_record_hash_denied(self):
        name=next(iter(self.win["cases"]))
        self.win["cases"][name]["record_sha256"]="f"*64
        save_json(self.windows_review,self.win)
        self.blocked("WINDOWS_REVIEW_RECORD_CHANGED_OR_UNVERIFIED")

    def test_19_windows_review_attestation_bad_receipt_denied(self):
        self.win["j06_receipt_sha256"]="f"*64
        save_json(self.windows_review,self.win)
        self.blocked("INDEPENDENT_NATIVE_WINDOWS_HUMAN_REVIEW_MISSING")

    def test_20_android_stage_inside_game_forbidden(self):
        self.stage=self.fx.fixt.game
        self.blocked("ANDROID_SNAPSHOT_MUST_BE_ISOLATED")

    def test_21_android_save_path_never_read_or_packed(self):
        write(self.stage/"Saves/File A.rxdata",b"new sensitive synthetic save")
        self.blocked("ANDROID_UNSAFE_ENTRY_OR_DUPLICATE")

    def test_22_android_executable_cannot_be_packed(self):
        write(self.stage/"Data/Game.exe",b"synthetic binary")
        self.blocked("ANDROID_UNSAFE_ENTRY_OR_DUPLICATE")

    def test_23_android_stage_symlink_refused(self):
        link=self.stage/"Graphics/Characters/linked.png"
        try:link.symlink_to(next((self.stage/"Graphics/Characters").glob("*.png")))
        except (OSError,NotImplementedError):self.skipTest("symlink not supported")
        self.blocked("SYMLINK_OR_REPARSE_POINT_DENIED")

    def test_24_no_deletions_of_old_android_files(self):
        (self.stage/"Data/System.rxdata").unlink()
        self.blocked("ANDROID_REQUIRED_BASE_AND_BARRY_PBS_REQUIRED")

    def test_25_android_reserved_mapid_present_in_baseline_denied(self):
        write(self.base/self.maps[0],b"occupied other-region fake map")
        self.blocked("ANDROID_MAPID_ALREADY_PRESENT_IN_BASELINE")

    def test_26_separate_android_save_profile_required(self):
        modified=dict(self.profile);modified["dataPathApp"]="Decades"
        save_json(self.stage/"mkxp.json",modified)
        self.blocked("ANDROID_PRIVATE_SAVE_NAMESPACE_INVALID")

    def test_27_changed_android_profile_from_base_denied(self):
        write(self.stage/"Game.ini",
              ("[Game]\nTitle="+self.profile["windowTitle"]+"\nExtra=x\n").encode())
        self.blocked("ANDROID_PROFILE_CHANGED_OR_NOT_ISOLATED")

    def test_28_source_windows_rights_revoked_denied(self):
        self.fx.fixt.review["reviewed_locally"]=False
        self.fx.fixt.flush()
        self.blocked()

    def test_29_j07_session_manifest_not_bound_denied(self):
        self.fx.ssha="a"*64
        self.blocked()

    def test_30_native_evidence_missing_denied(self):
        (self.fx.sess/"records"/"ball-TURTWIG.json").unlink()
        self.blocked()

    def test_31_no_replacing_live_android_or_autoupdater_channels(self):
        p=self.call()
        self.assertNotIn("ATUALIZAR-ANDROID.py",p["changed"])
        self.assertNotIn("Data/blue-update.json",p["changed"])
        self.assertTrue(all(j08.valid_entry(x) for x in p["changed"]))
        self.assertFalse(p["android_native_test_executed"])

    def test_32_cli_without_private_sources_returns_blocked(self):
        self.assertEqual(j08.main(["--project",str(ROOT)]),2)
        self.assertFalse((self.work/"sinnoh-j08-candidates").exists())

    def test_33_tampering_zip_refused_even_with_new_outer_sha(self):
        p=self.call()
        out=j08.package(self.root,p)
        z=Path(out["path"])
        new=Path(self.work/"altered.tmp")
        with zipfile.ZipFile(z) as src,zipfile.ZipFile(new,"w") as dest:
            for name in src.namelist():
                value=src.read(name)
                if name==self.maps[0]:value=b"tampered nine map"
                dest.writestr(name,value)
        new.replace(z)
        with self.assertRaisesRegex(ValueError,"ANDROID_ZIP_CONTENT_CHANGED"):
            j08.verify_candidate(self.root,z,file_digest(z))

    def test_34_refuse_changed_source_during_zip_write(self):
        p=self.call()
        (self.stage/self.maps[0]).write_bytes(b"changed after review")
        with self.assertRaisesRegex(ValueError,"SOURCE_CHANGED_DURING_PACKAGING"):
            j08.package(self.root,p)
        directory=self.work/"sinnoh-j08-candidates"
        self.assertFalse(list(directory.glob("*.zip")))

    def test_35_pure_private_zip_never_approves_joiplay(self):
        p=self.call()
        descriptor=j08.candidate_manifest(p)
        self.assertFalse(descriptor["can_publish"])
        self.assertFalse(descriptor["can_install_into_main_android"])
        self.assertFalse(descriptor["joiplay_real_test_executed"])
        self.assertTrue(descriptor["no_backup_created"])
        self.assertEqual(self.fx.fixt.save.read_bytes(),self.fx.fixt.original_save)
        self.assertFalse((self.fx.qa/"Data/blue-sinnoh-rival-ready.txt").exists())

if __name__=="__main__":
    unittest.main()
