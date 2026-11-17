"""L00 synthetic only: sanitized receipt, SHA and fail-closed native QA guards."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_l00_readiness as l00


class SinnohL00ReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template=l00.read_json(ROOT,l00.TEMPLATE)
        cls.contracts={k:l00.read_json(ROOT,p) for k,p in l00.CONTRACTS.items()}
        cls.handoff=l00.read_json(ROOT,l00.g12.HANDOFF)
        cls.final=l00.g12.run(ROOT)

    def audited(self,change=None):
        bundle=copy.deepcopy(self.template)
        contracts=copy.deepcopy(self.contracts)
        handoff=copy.deepcopy(self.handoff)
        final=copy.deepcopy(self.final)
        if change:change(bundle,contracts,handoff,final)
        return l00.audit(bundle,contracts,handoff,final)

    def rejected(self,change):
        with self.assertRaisesRegex(ValueError,"SINNOH_L00_BLOCKED"):
            self.audited(change)

    @staticmethod
    def sha(ch="a"):
        return ch*64

    @classmethod
    def fixture(cls):
        c=cls.contracts
        plan=cls.sha()
        return {
            "B09":{
                "stage":"B09",
                "status":"PRIVATE_NATIVE_QA_CLONE_CREATED_NOT_RUNNABLE_YET",
                "plan_sha256":plan,
                "native_inventory_sha256":c["B09"]["native_inventory_sha256"],
                "map_ids_clone_total":702,
                "b08_maps_validated":54,"b08_pngs_validated":14,
                "saves_copied":False,"game_exe_executed":False,
                "safe_to_launch":False,"can_install_live_game":False,
                "r07_complete":False,"phase_b_approved":0,
            },
            "B10":{
                "stage":"B10","status":"WSB_CONFIG_PREPARED_NOT_LAUNCHED",
                "source_clone_sha256":plan,
                "native_map_ids":648,"sinnoh_terrain_map_ids":54,
                "expected_total_maps":702,"all_cloned_files_sha_verified":True,
                "sandbox_feature_enabled_on_host":True,
                "mapped_folders_read_only":True,
                "internet_networking_enabled":False,
                "clipboard_enabled":False,"sandbox_session_started":False,
                "game_exe_started":False,"host_save_directories_mapped":False,
                "save_write_isolation_runtime_verified":False,
                "rights_verified":False,"r07_complete":False,
                "phase_b_approved":0,
            },
            "B11":{
                "stage":"B11",
                "before":{
                    "status":"HOST_SAVE_SNAPSHOT_BEFORE_RECORDED_SANDBOX_NOT_RUN",
                    "monitored_directories_count":2,"scope_selection_mode":"explicit",
                    "default_scopes_not_monitored":None,"monitored_files_before":3,
                    "paths_names_and_saves_in_report":False,
                    "windows_sandbox_started":False,"Game_exe_started":False,
                    "host_saves_runtime_isolation_confirmed":False,
                    "coverage_is_partial":True,"r07_complete":False,
                    "phase_b_approved":0,
                },
                "after":{
                    "status":"HOST_WATCHED_FILES_UNCHANGED_LIMITED_EVIDENCE",
                    "monitored_directories_count":2,"scope_selection_mode":"explicit",
                    "default_scopes_not_monitored":None,
                    "monitored_files_before":3,"monitored_files_after":3,
                    "files_added":0,"files_removed":0,"files_changed":0,
                    "watch_unchanged":True,"coverage_is_partial":True,
                    "guest_observation_self_reported":"not_run",
                    "guest_vm_execution_independently_verified":False,
                    "complete_host_save_coverage_verified":False,
                    "true_runtime_save_path_in_source_verified":False,
                    "host_saves_globally_isolated_proven":False,
                    "assets_rights_verified":False,"R07_R08_R09_approved":False,
                    "gameplay_approved":False,
                    "phase_b_approved":0,"phase_c_approved":0,
                    "phase_d_approved":0,
                    "paths_names_and_saves_in_report":False,
                },
            },
            "R07":{
                "stage":"R07",
                "status":"BLOCKED_MISSING_NATIVE_RESERVATION_EVIDENCE",
                "native_snapshot_present":False,
                "native_occupied_count":None,"native_mapinfos_sha256":None,
                "future_regions_with_evidence":0,
                "future_regions_required":["KANTO","JOHTO","HOENN"],
                "collisions_count":0,"candidate_safety_reviewable":False,
                "r07_complete":False,"may_apply_to_main_game":False,
                "rights_verified":False,
            },
            "R08":{
                "stage":"R08","status":"RIGHTS_REVIEW_PENDING",
                "source_expected_png_count":14,
                "per_asset_licenses_reviewed_count":0,
                "source_asset_rights_verified":False,
                "physical_maps_approved":False,
                "twinleaf_map_bindings_verified":False,
                "twinleaf_warps_verified":False,
                "barry_pbs_compiled":False,
                "r08_complete":False,"can_install":False,
            },
        }

    def with_fixture(self):
        return self.audited(lambda b,c,h,f:b["reports"].update(self.fixture()))

    def reject_record(self,stage,mutate):
        self.rejected(lambda b,c,h,f:(
            b["reports"].update(self.fixture()),
            mutate(b["reports"][stage]),
        ))

    def test_01_default_only_public_inputs_no_proven_native(self):
        r=self.audited()
        self.assertEqual((r["received_reports"],r["missing_reports"]),(0,5))
        self.assertTrue(all(r["sources"][k]["status"]=="MISSING_REPORT"
                            for k in l00.STAGES))
        self.assertEqual(r["native_cases_total"],44)
        self.assertEqual(r["completed_native_cases"],0)
        self.assertEqual(r["independently_accepted_cases"],0)
        self.assertEqual(r["status"],"NO_NATIVE_READINESS_APPROVAL_GITHUB_ONLY")

    def test_02_all_synthetic_report_types_are_received_not_approved(self):
        r=self.with_fixture()
        self.assertEqual((r["received_reports"],r["missing_reports"]),(5,0))
        for k in l00.STAGES:
            self.assertEqual(r["sources"][k]["status"],
                             "RECEIVED_SANITIZED_REPORT_UNVERIFIED")
            self.assertRegex(r["sources"][k]["sanitized_report_sha256"],r"[a-f0-9]{64}")
            self.assertFalse(r["sources"][k]["independent_physical_review_accepted"])
        self.assertFalse(r["native_approved"])

    def test_03_r07_reviewable_is_not_license_or_allocation(self):
        f=self.fixture()
        f["R07"].update(status="CANDIDATE_READY_FOR_MANUAL_REVIEW_NOT_APPROVED",
                        native_snapshot_present=True,native_occupied_count=648,
                        native_mapinfos_sha256=self.contracts["B09"]["native_baseline_mapinfos_sha256"],
                        future_regions_with_evidence=3,collisions_count=0,
                        candidate_safety_reviewable=True)
        r=self.audited(lambda b,c,h,o:b["reports"].update(f))
        self.assertTrue(r["r07_candidate_reviewable_is_not_allocated_mapids"])
        self.assertFalse(r["r07_complete"])
        self.assertFalse(r["may_install_live_game"])

    def test_04_B11_changed_save_counts_still_never_approve(self):
        f=self.fixture()
        d=f["B11"]["after"]
        d.update(status="HOST_WATCHED_FILES_CHANGED_REVIEW_REQUIRED",
                 files_changed=1,watch_unchanged=False,
                 guest_observation_self_reported="save_inside_vm")
        r=self.audited(lambda b,c,h,o:b["reports"].update(f))
        self.assertEqual(r["sources"]["B11"]["status"],
                         "RECEIVED_SANITIZED_REPORT_UNVERIFIED")
        self.assertFalse(r["host_save_isolation_globally_proven"])

    def test_05_B10_different_plan_sha_rejected(self):
        self.reject_record("B10",lambda r:r.update(source_clone_sha256=self.sha("b")))

    def test_06_B09_unsafe_flags_rejected(self):
        for key in ("saves_copied","game_exe_executed","safe_to_launch",
                    "can_install_live_game","r07_complete"):
            with self.subTest(flag=key):
                self.reject_record("B09",lambda r,key=key:r.update({key:True}))

    def test_07_B09_sha_counts_and_status_mismatch_rejected(self):
        for name,val in (("plan_sha256","short"),
                         ("native_inventory_sha256",self.sha("b")),
                         ("map_ids_clone_total",703),
                         ("b08_maps_validated",53),
                         ("b08_pngs_validated",15),
                         ("phase_b_approved",1),
                         ("status","NATIVE_APPROVED")):
            with self.subTest(field=name):
                self.reject_record("B09",lambda r,n=name,v=val:r.update({n:v}))

    def test_08_B10_network_clipboard_autostart_and_writable_mounts_rejected(self):
        for key,val in (("internet_networking_enabled",True),
                        ("clipboard_enabled",True),
                        ("sandbox_session_started",True),
                        ("game_exe_started",True),
                        ("host_save_directories_mapped",True),
                        ("save_write_isolation_runtime_verified",True),
                        ("mapped_folders_read_only",False),
                        ("all_cloned_files_sha_verified",False),
                        ("rights_verified",True),
                        ("phase_b_approved",1)):
            with self.subTest(field=key):
                self.reject_record("B10",lambda r,k=key,v=val:r.update({k:v}))

    def test_09_B11_false_global_isolation_or_VM_proof_rejected(self):
        for key in ("guest_vm_execution_independently_verified",
                    "complete_host_save_coverage_verified",
                    "true_runtime_save_path_in_source_verified",
                    "host_saves_globally_isolated_proven","assets_rights_verified",
                    "R07_R08_R09_approved","gameplay_approved",
                    "paths_names_and_saves_in_report"):
            with self.subTest(key=key):
                self.reject_record("B11",lambda r,k=key:r["after"].update({k:True}))

    def test_10_B11_partial_coverage_never_downgraded(self):
        self.reject_record("B11",lambda r:r["after"].update(coverage_is_partial=False))
        self.reject_record("B11",lambda r:r["before"].update(coverage_is_partial=False))

    def test_11_B11_snapshot_before_after_counts_must_match(self):
        for change in (
            lambda x:x["after"].update(monitored_directories_count=3),
            lambda x:x["after"].update(monitored_files_before=4),
            lambda x:x["after"].update(monitored_files_after=4),
            lambda x:x["after"].update(scope_selection_mode="default"),
            lambda x:x["after"].update(default_scopes_not_monitored=3),
            lambda x:x["after"].update(files_changed=-1),
        ):
            with self.subTest(change=repr(change)):
                self.reject_record("B11",change)

    def test_12_B11_corrupted_watch_unchanged_and_changed_status_rejected(self):
        for change in (
            lambda x:x["after"].update(watch_unchanged=False),
            lambda x:x["after"].update(status="NATIVE_APPROVED"),
            lambda x:x["after"].update(files_changed=1),
            lambda x:x["before"].update(status="NATIVE_APPROVED"),
            lambda x:x["after"].update(phase_c_approved=1),
            lambda x:x["before"].update(Game_exe_started=True),
        ):
            with self.subTest(change=repr(change)):
                self.reject_record("B11",change)

    def test_13_R07_forged_complete_wrong_baseline_rejected(self):
        for name,val in (("r07_complete",True),
                         ("rights_verified",True),
                         ("may_apply_to_main_game",True),
                         ("future_regions_with_evidence",4),
                         ("native_snapshot_present",True),
                         ("status","NATIVE_APPROVED")):
            with self.subTest(key=name):
                self.reject_record("R07",lambda x,k=name,v=val:x.update({k:v}))

    def test_14_R07_wrong_regions_and_collision_readiness_rejected(self):
        self.reject_record("R07",lambda x:x.update(future_regions_required=["KANTO","JOHTO"]))
        self.reject_record("R07",lambda x:x.update(candidate_safety_reviewable=True))
        f=self.fixture()
        f["R07"].update(
            status="CANDIDATE_READY_FOR_MANUAL_REVIEW_NOT_APPROVED",
            native_snapshot_present=True,native_occupied_count=648,
            native_mapinfos_sha256=self.contracts["B09"]["native_baseline_mapinfos_sha256"],
            future_regions_with_evidence=3,collisions_count=1,
            candidate_safety_reviewable=True)
        self.rejected(lambda b,c,h,o:b["reports"].update(f))

    def test_15_R08_rights_asset_and_release_forgery_rejected(self):
        for key in ("source_asset_rights_verified","physical_maps_approved",
                    "twinleaf_map_bindings_verified","twinleaf_warps_verified",
                    "barry_pbs_compiled","r08_complete","can_install"):
            with self.subTest(key=key):
                self.reject_record("R08",lambda x,k=key:x.update({k:True}))

    def test_16_R08_license_progress_does_not_approve_rights(self):
        f=self.fixture()
        f["R08"]["per_asset_licenses_reviewed_count"]=14
        r=self.audited(lambda b,c,h,o:b["reports"].update(f))
        self.assertTrue(r["r08_licenses_review_count_is_not_rights_approval"])
        self.assertFalse(r["r08_complete"])
        self.reject_record("R08",lambda x:x.update(per_asset_licenses_reviewed_count=15))

    def test_17_unknown_fields_paths_private_baseline_and_saves_rejected(self):
        for stage,payload in (("B09",{"relative_path":"C:\\Users\\tester\\game"}),
                              ("B10",{"guest_instructions":"Run Game.exe"}),
                              ("B11",{"private-baseline.json":"secret"}),
                              ("R07",{"ownership_evidence":"C:\\Users\\tester"}),
                              ("R08",{"asset_path":"Save01.rxdata"})):
            with self.subTest(stage=stage):
                self.reject_record(stage,lambda x,p=payload:x.update(p))

    def test_18_bundle_or_contract_mutation_rejected(self):
        self.rejected(lambda b,c,h,f:b["reports"].update(XTRA=None))
        self.rejected(lambda b,c,h,f:b.update(mode="PRIVATE_DATA"))
        self.rejected(lambda b,c,h,f:c["B10"].update(network_disabled=False))
        self.rejected(lambda b,c,h,f:c["B09"].update(expected_qa_clone_map_count=703))
        self.rejected(lambda b,c,h,f:c["R08"]["received_real_source"].update(source_rights_verified=True))
        self.rejected(lambda b,c,h,f:c["R07"].update(all_future_reservations_verified=True))

    def test_19_G12_44_and_zero_native_gate_cannot_change(self):
        self.rejected(lambda b,c,h,f:h.update(completed_native_cases=1))
        self.rejected(lambda b,c,h,f:h.update(game_exe_tested=True))
        self.rejected(lambda b,c,h,f:f.update(completed_native_cases=44))
        self.rejected(lambda b,c,h,f:f.update(can_install_live_game=True))

    def test_20_report_omission_must_not_crash_or_make_readiness(self):
        f=self.fixture()
        f["B09"]=None
        f["B10"]=None
        r=self.audited(lambda b,c,h,o:b["reports"].update(f))
        self.assertEqual(r["missing_reports"],2)
        self.assertEqual(r["received_reports"],3)
        self.assertFalse(r["may_start_game_in_vm"])

    def test_21_cli_default_metadata_only_and_clean_stdout(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_l00_readiness.py")],
            cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(p.returncode,0,p.stderr)
        d=json.loads(p.stdout)
        self.assertEqual(d["status"],"NO_NATIVE_READINESS_APPROVAL_GITHUB_ONLY")
        self.assertEqual(d["missing_reports"],5)
        self.assertEqual(d["native_cases_total"],44)
        self.assertFalse(d["native_approved"])
        for forbidden in ("C:\\Users","Save01.rxdata","private-baseline.json",
                          "hmac_key","source_zip_sha256"):
            self.assertNotIn(forbidden,p.stdout)

    def test_22_cli_arbitrary_paths_rejected(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_l00_readiness.py"),
            "--reports",r"C:\Users\tester\Save01.rxdata"],
            cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertNotEqual(p.returncode,0)
        self.assertNotIn("C:\\Users",p.stdout)
        self.assertNotIn("C:\\Users",p.stderr)

    def test_23_workspaces_only_explicit_exact_file_no_scan(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/".blue-work/sinnoh-l00-input").mkdir(parents=True)
            file=root/l00.PRIVATE_REPORT
            file.write_text(json.dumps({**self.template,"reports":self.fixture()}),
                            encoding="utf-8")
            output=l00.read_json(root,l00.PRIVATE_REPORT,maxsize=65536)
            self.assertEqual(output["reports"]["B09"]["map_ids_clone_total"],702)
            (root/"game").mkdir()
            (root/"game/Game.exe").write_bytes(b"MZnever executed")
            self.assertFalse(l00.audit(output,self.contracts,self.handoff,self.final)["game_exe_tested"])

    def test_24_workspace_symlink_and_oversized_reports_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            target=root/".blue-work/sinnoh-l00-input/public-reports.json"
            target.parent.mkdir(parents=True)
            target.write_text("x"*65537,encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"SINNOH_L00_BLOCKED"):
                l00.read_json(root,l00.PRIVATE_REPORT,maxsize=65536)
            target.unlink()
            try:target.symlink_to(root/"no-such-file")
            except (OSError,NotImplementedError):return
            with self.assertRaisesRegex(ValueError,"SINNOH_L00_BLOCKED"):
                l00.read_json(root,l00.PRIVATE_REPORT,maxsize=65536)


if __name__=="__main__":
    unittest.main()
