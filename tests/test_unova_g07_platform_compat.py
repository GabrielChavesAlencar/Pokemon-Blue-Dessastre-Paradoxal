"""G07.4 Windows/Blue-Story and Android/JoiPlay offline compatibility contracts.

All fixtures are in memory. We do not import/run either native updater.
"""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_g07_platform_compat as mod
import audit_unova_g07_incremental_manifest as g72
import audit_unova_g07_transaction as g73

class UnovaG074Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit=mod.audit_contract()
        cls.contract=g72.j(ROOT,mod.FILE)
        cls.board=g72.j(ROOT,g72.TRACKER)

    def fixture(self,platform="windows"):
        pkg,manifest,old,new=g73.multi_file_fixture()
        state=g73.base_fixture(pkg,manifest,old)
        req=mod.fixture_request(platform,pkg,state)
        return req,pkg,manifest,old,new,state

    def execute(self,platform="windows",**kwargs):
        req,pkg,manifest,old,new,state=self.fixture(platform)
        return mod.preview(platform,req,pkg,manifest,old,new,state,**kwargs)

    def bad_req(self,edit,platform="windows"):
        req,pkg,manifest,old,new,state=self.fixture(platform)
        edit(req)
        with self.assertRaises(ValueError):
            mod.preview(platform,req,pkg,manifest,old,new,state)

    def bad_package(self,edit,platform="windows"):
        req,pkg,manifest,old,new,state=self.fixture(platform)
        edit(pkg)
        pkg["package_sha256"]=g72.package_digest(pkg)
        with self.assertRaises(ValueError):
            mod.preview(platform,req,pkg,manifest,old,new,state)

    def test_001_phase(self):
        self.assertEqual(self.audit["phase"],"G07.4")
    def test_002_profiles_exact(self):
        self.assertEqual(self.audit["platforms"],["windows","android"])
    def test_003_windows_source_zip_not_hash_pinned(self):
        self.assertIs(self.contract["platforms"]["windows"]["existing_source_download_digest_pinned"],False)
    def test_004_android_source_checksum_not_applicable(self):
        self.assertIsNone(self.contract["platforms"]["android"]["existing_source_download_digest_pinned"])
    def test_005_windows_not_installed(self):
        self.assertFalse(self.audit["windows_native_compatible"])
    def test_006_android_not_installed(self):
        self.assertFalse(self.audit["android_native_compatible"])
    def test_007_joiplay_not_tested(self):
        self.assertFalse(self.audit["joiplay_runtime_tested"])
    def test_008_g072_source_still_checks(self):
        self.assertEqual(g72.validate_catalog()["phase"],"G07.2")
    def test_009_g073_source_still_checks(self):
        self.assertEqual(g73.audit_contract()["phase"],"G07.3")
    def test_010_schema_only(self):
        self.assertFalse(self.contract["can_install"])
    def test_011_no_source_files_modified(self):
        self.assertFalse(self.audit["native_installers_modified"])
    def test_012_no_save_write(self):
        self.assertFalse(self.contract["save_modified"])
    def test_013_unova_planned(self):
        self.assertEqual(g72.j(ROOT,g72.REGISTRY)["regions"]["UNOVA"]["status"],"planned")
    def test_014_technical_zero(self):
        self.assertEqual(self.board["native_technical_bar"]["completed"],0)
    def test_015_playable_zero(self):
        self.assertEqual(self.board["native_playable_bar"]["completed"],0)
    def test_016_G073_done(self):
        self.assertEqual(self.board["groups"][6]["tasks"][2]["status"],"done")
    def test_017_G074_recorded(self):
        self.assertEqual(self.board["groups"][6]["tasks"][3]["id"],"G07.4")
    def test_018_android_real_channels(self):
        self.assertEqual(self.contract["platforms"]["android"]["existing_update_channels"],
                         ["decades","kanto","multiregion"])
    def test_019_android_unova_not_channel(self):
        self.assertNotIn("unova",self.contract["platforms"]["android"]["existing_update_channels"])
    def test_020_windows_source_zip_channel_not_native(self):
        self.assertEqual(mod.WIN["existing_update_channel"],"github-main-source-zip")
        self.assertFalse(mod.WIN["native_patch_supported"])
    def test_021_android_no_backup(self):
        self.assertIn("without-backup",mod.ANDROID["existing_source_backup_behavior"])
    def test_022_windows_unverified_rollback(self):
        self.assertIn("without-certified-atomic-rollback",mod.WIN["existing_source_backup_behavior"])
    def test_023_rights_absent(self):
        self.assertTrue(all(x is None for x in self.contract["native_evidence"].values()))
    def test_024_source_paths_pinned(self):
        self.assertEqual(self.contract["sources"],mod.SOURCE_PATHS)
    def test_025_protected_resources(self):
        self.assertIn("Game.exe",self.contract["protected_resources"])
        self.assertIn("JoiPlay save profile",self.contract["protected_resources"])
    def test_026_no_runtime_test_claim(self):
        self.assertFalse(mod.POLICY["joiplay_unova_runtime_tested"])
    def test_027_no_native_release_claim(self):
        self.assertFalse(mod.POLICY["android_unova_channel_published"])
    def test_028_no_download(self):
        self.assertTrue(mod.POLICY["never_download_or_extract"])
    def test_029_no_installer_invocation(self):
        self.assertTrue(mod.POLICY["never_invoke_installers"])
    def test_030_no_game_save_write(self):
        self.assertTrue(mod.POLICY["never_write_saves_or_game_exe"])
    def test_031_windows_accepted_preview(self):
        self.assertEqual(self.execute("windows")["status"],"PLATFORM_DOCS_PREVIEW_NOT_INSTALLABLE")
    def test_032_android_accepted_preview(self):
        self.assertEqual(self.execute("android")["status"],"PLATFORM_DOCS_PREVIEW_NOT_INSTALLABLE")
    def test_033_windows_preview_synthetic_commit(self):
        self.assertEqual(self.execute("windows")["transaction_status"],"SIMULATED_ATOMIC_COMMIT_NOT_INSTALLED")
    def test_034_android_preview_synthetic_commit(self):
        self.assertEqual(self.execute("android")["transaction_status"],"SIMULATED_ATOMIC_COMMIT_NOT_INSTALLED")
    def test_035_platform_no_native_files(self):
        for p in mod.PLATFORMS:self.assertEqual(self.execute(p)["native_files_written"],0)
    def test_036_platform_no_bytes_written(self):
        for p in mod.PLATFORMS:self.assertEqual(self.execute(p)["bytes_written"],0)
    def test_037_platform_no_installer_called(self):
        for p in mod.PLATFORMS:
            self.assertFalse(self.execute(p)["blue_story_invoked"])
            self.assertFalse(self.execute(p)["joiplay_invoked"])
    def test_038_platform_safe_fallback(self):
        for p in mod.PLATFORMS:
            self.assertEqual(self.execute(p)["fallback"],"KEEP_EXISTING_INSTALLATION_UNCHANGED")
    def test_039_platform_no_release(self):
        for p in mod.PLATFORMS:
            self.assertFalse(self.execute(p)["release_allowed"])
            self.assertFalse(self.execute(p)["install_allowed"])
    def test_040_platform_copied_snapshot(self):
        for p in mod.PLATFORMS:
            req,pkg,m,old,new,state=self.fixture(p)
            original=copy.deepcopy(state)
            mod.preview(p,req,pkg,m,old,new,state)
            self.assertEqual(original,state)
    def test_041_source_files_from_two_docs_only(self):
        req,pkg,m,old,new,state=self.fixture()
        self.assertEqual(len(pkg["files"]),2)
        self.assertTrue(all(g72.path_ok(x) for x in new))
    def test_042_windows_staged_two_files(self):
        self.assertEqual(len(self.execute("windows")["backup_manifest"]),2)
    def test_043_android_staged_two_files(self):
        self.assertEqual(len(self.execute("android")["backup_manifest"]),2)
    def test_044_result_preserves_all_protected(self):
        for p in mod.PLATFORMS:
            req,pkg,m,old,new,state=self.fixture(p)
            self.assertEqual(mod.preview(p,req,pkg,m,old,new,state)["state"]["protected"],
                             state["protected"])
    def test_045_invalid_platform(self):
        with self.assertRaises(ValueError):
            mod.fixture_request("unova_native",self.fixture()[1],self.fixture()[5])
    def test_046_unknown_platform_preview(self):
        req,pkg,m,old,new,state=self.fixture()
        with self.assertRaises(ValueError):
            mod.preview("unknown",req,pkg,m,old,new,state)
    def test_047_request_is_exact(self):
        req,pkg,m,old,new,state=self.fixture()
        self.assertEqual(set(req),mod.REQUEST_KEYS)
        self.assertEqual(mod.validate_request(req,"windows",pkg,state)["platform"],"windows")
    def test_048_android_not_run_real_updater(self):
        self.assertEqual(self.execute("android")["mode"],"documentation_fixture_simulation_only")
    def test_049_windows_not_run_real_extractor(self):
        self.assertEqual(self.execute("windows")["mode"],"documentation_fixture_simulation_only")
    def test_050_cli_check(self):
        ret=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g07_platform_compat.py"),"--check"],capture_output=True,text=True)
        self.assertEqual(ret.returncode,0,ret.stdout+ret.stderr)
        self.assertFalse(json.loads(ret.stdout)["can_install"])
    def test_051_cli_demo(self):
        ret=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g07_platform_compat.py"),"--simulate-demo"],capture_output=True,text=True)
        self.assertEqual(ret.returncode,0,ret.stdout+ret.stderr)
        out=json.loads(ret.stdout)
        self.assertFalse(out["unova_playable"])
        self.assertEqual(set(out["platforms"]),{"windows","android"})
    def test_052_missing_rights_rejected_windows(self):
        self.bad_package(lambda p:p["rights"].pop("license_id"))
    def test_053_missing_rights_rejected_android(self):
        self.bad_package(lambda p:p["files"][0]["rights"].pop("license_id"),"android")
    def test_054_invalid_hash_rejected_windows(self):
        self.bad_package(lambda p:p["files"][0].update(sha256="0"*64))
    def test_055_invalid_hash_rejected_android(self):
        self.bad_package(lambda p:p["files"][0].update(source_sha256="f"*64),"android")
    def test_056_cross_region_payload_rejected(self):
        self.bad_package(lambda p:p["files"][0].update(path="game/Data/Map518.rxdata"))
    def test_057_real_SAV_rejected(self):
        self.bad_package(lambda p:p["files"][0].update(path="saves/File A.rxdata"))
    def test_058_joi_play_backslash_traversal(self):
        self.bad_package(lambda p:p["files"][0].update(path="docs\\..\\Data\\Map518.rxdata"),"android")
    def test_059_manifest_wrong_revision_rejected(self):
        self.bad_package(lambda p:p["source"].update(target_revision="invalid"))
    def test_060_no_unsupported_protocol(self):
        self.bad_package(lambda p:p["compatibility"].update(protocol_version=2))
    def test_061_no_foreign_release_channel(self):
        self.bad_req(lambda q:q.update(channel="multiregion"),"android")
    def test_062_windows_source_not_unova_patch(self):
        self.bad_req(lambda q:q.update(channel="github-main-source-zip"),"windows")
    def test_063_save_protected_conflict_windows(self):
        req,pkg,m,old,new,state=self.fixture("windows")
        after=copy.deepcopy(state)
        after["protected"]["saves"]["FIXTURE_SAVES_LEDGER"]="FIXTURE_CHANGED"
        out=mod.preview("windows",req,pkg,m,old,new,state,observed_after_staging=after)
        self.assertEqual(out["transaction_status"],"CONFLICT_CAS_CONCURRENT_EDIT")
        self.assertEqual(out["state"],state)
    def test_064_save_protected_conflict_android(self):
        req,pkg,m,old,new,state=self.fixture("android")
        after=copy.deepcopy(state)
        after["protected"]["saves"]["FIXTURE_SAVES_LEDGER"]="FIXTURE_CHANGED"
        out=mod.preview("android",req,pkg,m,old,new,state,observed_before_publish=after)
        self.assertEqual(out["transaction_status"],"CONFLICT_CAS_CONCURRENT_EDIT")
        self.assertEqual(out["state"],state)
    def test_065_platform_snapshots_are_private(self):
        req,pkg,m,old,new,state=self.fixture()
        out=mod.preview("windows",req,pkg,m,old,new,state)
        out["state"]["protected"]["saves"]["FIXTURE_SAVES_LEDGER"]="FIXTURE_EDITED_RESULT_ONLY"
        self.assertNotEqual(out["state"]["protected"],state["protected"])
    def test_066_mode_rejected_as_native(self):
        self.bad_req(lambda q:q.update(mode="native_install"))
    def test_067_permission_claim_rejected(self):
        self.bad_req(lambda q:q.update(redistribution_approved=True))
    def test_068_android_version_downgrade_rejected(self):
        self.bad_req(lambda q:q.update(package_version="0.0.0"),"android")
    def test_069_invalid_generation_rejected(self):
        self.bad_req(lambda q:q.update(expected_generation=-1))
    def test_070_stale_expected_etag_rejected(self):
        self.bad_req(lambda q:q.update(expected_snapshot_sha256="f"*64))

for _profile in mod.PLATFORMS:
    for _point in g73.FAULTS:
        def _rollback(self,p=_profile,f=_point):
            req,pkg,m,old,new,state=self.fixture(p)
            original=copy.deepcopy(state)
            result=mod.preview(p,req,pkg,m,old,new,state,fail_at=f)
            self.assertEqual(result["transaction_status"],"SIMULATED_ROLLBACK_COMPLETE")
            self.assertEqual(result["state"],original)
            self.assertEqual(state,original)
            self.assertFalse(result["install_allowed"])
            self.assertEqual(result["native_files_written"],0)
        setattr(UnovaG074Tests,"test_rollback_"+_profile+"_"+_point,_rollback)

_REQUEST_ATTACKS={
 "native_install":lambda q:q.update(native_install_requested=True),
 "download":lambda q:q.update(download_requested=True),
 "save_write":lambda q:q.update(save_write_requested=True),
 "game_exe_write":lambda q:q.update(game_exe_write_requested=True),
 "unova_release":lambda q:q.update(unova_release_channel="unova"),
 "fake_runtime_qa":lambda q:q.update(runtime_qa={"passed":True}),
 "fake_mapid":lambda q:q.update(approved_native_mapids=[518]),
 "zip_hash_claim":lambda q:q.update(source_archive_sha256="a"*64),
 "dry_run_false":lambda q:q.update(dry_run_only=False),
 "source_manifest":lambda q:q.update(source_manifest_sha256="b"*64),
 "source_revision":lambda q:q.update(source_revision="b"*40),
 "target_revision":lambda q:q.update(target_revision="c"*40),
 "package_id":lambda q:q.update(package_id="UNOVA_NATIVE"),
 "package_sha":lambda q:q.update(package_sha256="f"*64),
 "foreign_region_channel":lambda q:q.update(channel="kanto"),
 "wrong_platform":lambda q:q.update(platform_id="OTHER"),
 "wrong_version":lambda q:q.update(package_version="0.0.2-planned"),
 "missing_rights":lambda q:q.pop("rights_status"),
 "wrong_rights":lambda q:q.update(rights_status="approved"),
 "missing_generation":lambda q:q.pop("expected_generation"),
 "unknown_field":lambda q:q.update(commit_real_files=True),
 "wrong_paths":lambda q:q.update(requested_paths=["Data/Map518.rxdata"]),
 "paths_not_in_manifest":lambda q:q.update(requested_paths=["docs/unova-package-fixtures/other.txt"]),
 "empty_paths":lambda q:q.update(requested_paths=[]),
 "extra_path":lambda q:q.update(requested_paths=q["requested_paths"]+["docs/unova-package-fixtures/extra.txt"]),
 "bool_generation":lambda q:q.update(expected_generation=True),
 "unknown_etag":lambda q:q.update(expected_snapshot_sha256="short"),
 "missing_runtime_qa_field":lambda q:q.pop("runtime_qa"),
 "false_source_digest":lambda q:q.update(source_archive_sha256=False),
}
for _profile in mod.PLATFORMS:
    for _name,_edit in _REQUEST_ATTACKS.items():
        def _invalid(self,p=_profile,mutate=_edit):
            self.bad_req(mutate,p)
        setattr(UnovaG074Tests,"test_reject_"+_profile+"_"+_name,_invalid)

for _namespace in g73.PROTECTED:
    for _profile in mod.PLATFORMS:
        def _conflict(self,p=_profile,namespace=_namespace):
            req,pkg,m,old,new,state=self.fixture(p)
            other=copy.deepcopy(state)
            key=next(iter(other["protected"][namespace]))
            other["protected"][namespace][key]="FIXTURE_CONCURRENT_EDIT"
            for kw in ("observed_after_staging","observed_before_publish"):
                out=mod.preview(p,req,pkg,m,old,new,state,**{kw:other})
                self.assertEqual(out["transaction_status"],"CONFLICT_CAS_CONCURRENT_EDIT")
                self.assertEqual(out["state"],state)
        setattr(UnovaG074Tests,"test_conflict_"+_profile+"_"+_namespace,_conflict)

if __name__=="__main__":unittest.main()
