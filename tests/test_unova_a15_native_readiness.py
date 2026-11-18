"""A15: source-grounded Unova native-readiness refusals.

No real maps, user saves, local audit reports, Game.exe or downloads accessed.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_a15_native_readiness as a15

class UnovaA15Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix=a15.read_json(ROOT,a15.FILE)
        cls.report=a15.validate_document(cls.matrix)
        cls.board=a15.read_json(ROOT,a15.SOURCES["github_tracker"])
        cls.registry=a15.read_json(ROOT,a15.SOURCES["region_registry"])

    def reject(self,modify):
        matrix=copy.deepcopy(self.matrix)
        modify(matrix)
        with self.assertRaises(ValueError):
            a15.validate_document(matrix)

    def source_mutation(self,path,mutate):
        original=a15.source
        baseline=json.loads(original(ROOT,path))
        mutate(baseline)
        def reader(root,filename):
            if filename==path:
                return json.dumps(baseline)
            return original(root,filename)
        with patch.object(a15,"source",side_effect=reader):
            with self.assertRaises(ValueError):
                a15.validate_document(self.matrix)

    def test_001_phase(self):
        self.assertEqual(self.report["phase"],"A15")
    def test_002_native_blocked(self):
        self.assertEqual(self.report["status"],"SOURCE_GATES_VERIFIED_NATIVE_BLOCKED")
    def test_003_github_g_complete(self):
        self.assertEqual(self.report["github_g_bar"],32)
    def test_004_a_bar_zero(self):
        self.assertEqual(self.report["native_a_bar"],0)
    def test_005_playable_bar_zero(self):
        self.assertEqual(self.report["native_playable_bar"],0)
    def test_006_unova_planned(self):
        self.assertEqual(self.registry["regions"]["UNOVA"]["status"],"planned")
    def test_007_not_installable(self):
        self.assertFalse(self.report["can_install"])
    def test_008_reservation_blocked(self):
        self.assertFalse(self.report["can_reserve_mapids"])
    def test_009_game_exe_not_tested(self):
        self.assertFalse(self.report["game_exe_tested"])
    def test_010_joiplay_not_tested(self):
        self.assertFalse(self.report["joiplay_tested"])
    def test_011_no_native_write(self):
        self.assertEqual(self.report["native_files_written"],0)
    def test_012_no_native_save_read(self):
        self.assertFalse(self.report["saves_read"])
    def test_013_eleven_phases_present(self):
        self.assertEqual(self.report["a04_to_a14_tools_present"],11)
    def test_014_eight_gates_pending(self):
        self.assertEqual(self.report["pending_native_gates"],8)
    def test_015_source_artifacts_all_present(self):
        for item in self.matrix["steps"]:
            self.assertIn("def ",a15.source(ROOT,item["tool_path"]))
            self.assertIn("Unova",a15.source(ROOT,item["doc_path"]))
    def test_016_phase_order_no_gaps(self):
        self.assertEqual([x["id"] for x in self.matrix["steps"]],list(a15.STAGES))
    def test_017_technical_ids_ordered(self):
        self.assertEqual([x["id"] for x in self.matrix["technical_gates"]],list(a15.GATES))
    def test_018_all_native_receipts_explicitly_null(self):
        self.assertTrue(all(s["verified_receipt"] is None for s in self.matrix["steps"]))
    def test_019_native_evidence_all_null(self):
        self.assertTrue(all(v is None for v in self.matrix["required_native_evidence"].values()))
    def test_020_gates_have_no_approval(self):
        self.assertTrue(all(g["approved"] is False for g in self.matrix["technical_gates"]))
    def test_021_contract_keys_exhaustive(self):
        self.assertEqual(set(self.matrix),a15.ROOT_FIELDS)
    def test_022_history_hash_derived(self):
        self.assertEqual(self.report["historical_mapids"],648)
        self.assertRegex(self.matrix["historical_snapshot"]["mapinfos_sha256"],r"^[0-9a-f]{64}$")
    def test_023_historical_82_unreserved(self):
        self.assertEqual(self.report["historical_unova_candidates"],82)
        self.assertFalse(self.matrix["historical_snapshot"]["candidate_block_native_reserved"])
    def test_024_historical_92_other(self):
        self.assertEqual(self.report["historical_unova_other_candidates"],92)
    def test_025_sinnoh_hold_76(self):
        self.assertEqual(self.report["sinnoh_hold"],76)
    def test_026_symbolic_areas_74(self):
        self.assertEqual(self.report["area_symbols"],74)
    def test_027_mapid3_unresolved(self):
        self.assertTrue(self.report["mapid3_unresolved"])
    def test_028_two_map001_intro_claims_reported_not_approved(self):
        self.assertEqual(self.matrix["historical_snapshot"]["map001_intro_refs_to_3_reported"],2)
    def test_029_computed_expressions_not_executed(self):
        self.assertEqual(self.matrix["historical_snapshot"]["computed_expressions_a09_reported"],20)
    def test_030_github_only_provenance(self):
        self.assertFalse(self.matrix["historical_snapshot"]["independently_verified_native_mapids_from_repo"])
    def test_031_operator_reports_not_authorized(self):
        self.assertTrue(all(s["operator_only_required"] for s in self.matrix["steps"]))
    def test_032_A13_is_copy_procedure_not_game_QA(self):
        self.assertFalse(self.matrix["steps"][9]["game_exe_qa_verified"])
    def test_033_A14_is_sandbox_preflight_not_runtime_QA(self):
        self.assertFalse(self.matrix["steps"][10]["game_exe_qa_verified"])
    def test_034_no_licenses_approved(self):
        self.assertIsNone(self.matrix["required_native_evidence"]["per_asset_rights_approval"])
    def test_035_native_release_requires_licenses_and_QA(self):
        keys=set(k for g in self.matrix["technical_gates"] for k in g["evidence_keys"])
        for key in ("per_asset_rights_approval","native_mapids_reserved_review",
                    "native_atomic_rollback_qa","windows_release_manifest_and_qa",
                    "android_joiplay_release_manifest_and_qa",
                    "independent_human_approval"):
            self.assertIn(key,keys)
    def test_036_A05_mapping_empty(self):
        a05=a15.read_json(ROOT,a15.SOURCES["historical_mapids"])
        self.assertEqual(a05["proposed_area_to_native_mapid"],{})
    def test_037_no_future_reservation_proof(self):
        self.assertFalse(a15.read_json(ROOT,a15.SOURCES["historical_mapids"])["future_reservations_verified"])
    def test_038_known_registry_separate_from_game_install(self):
        self.assertEqual(self.board["native_technical_bar"]["completed"],0)
        self.assertEqual(self.board["native_playable_bar"]["completed"],0)
    def test_039_redacted_next_action(self):
        n=self.matrix["safe_next_action"]
        self.assertEqual(n["id"],"A16")
        self.assertFalse(n["auto_approve_rights"])
        self.assertFalse(n["auto_reserve_mapids"])
        self.assertFalse(n["auto_install"])
    def test_040_no_game_or_saves_collection(self):
        n=self.matrix["safe_next_action"]
        self.assertIn("Game.exe",n["do_not_collect"])
        self.assertIn("Saves",n["do_not_collect"])
    def test_041_cli_check_passes_blocked(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_a15_native_readiness.py"),"--check"],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        out=json.loads(p.stdout)
        self.assertEqual(out["pending_native_gates"],8)
        self.assertFalse(out["can_install"])
    def test_042_cli_matrix_lists_unapproved_gates(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_a15_native_readiness.py"),"--matrix"],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        d=json.loads(p.stdout)
        self.assertEqual(len(d["blockers"]),11)
        self.assertEqual(len(d["technical_gates"]),8)
        self.assertFalse(d["can_reserve_mapids"])
    def test_043_only_reads_trusted_repo_paths(self):
        for bad in ("../saves/File A.rxdata","Game.exe","/tmp/private","docs/../saves"):
            with self.assertRaises(ValueError):
                a15.source(ROOT,bad)
    def test_044_repo_source_not_written(self):
        before=a15.source(ROOT,a15.FILE)
        a15.validate_document(self.matrix)
        self.assertEqual(before,a15.source(ROOT,a15.FILE))
    def test_045_no_mutation_during_audit(self):
        before=copy.deepcopy(self.matrix)
        a15.validate_document(self.matrix)
        self.assertEqual(before,self.matrix)
    def test_046_BarraG_32_is_not_native_acceptance(self):
        self.assertEqual(sum(t["status"]=="done" for g in self.board["groups"] for t in g["tasks"]),32)
        self.assertFalse(self.matrix["can_install"])
    def test_047_no_auto_release(self):
        self.assertIs(self.matrix["can_release"],False)
    def test_048_gates_cover_regional_safety(self):
        self.assertEqual(self.matrix["cross_region_safeguards"],
            ["DECADES","KANTO","JOHTO","HOENN","SINNOH","UNOVA"])

# All these adversarial edits MUST fail without opening a native game file.
_TAMPERS={
 "schema":lambda d:d.update(schema_version=2),
 "phase":lambda d:d.update(phase="A15_NATIVE_PASSED"),
 "campaign":lambda d:d.update(campaign="WHITE_DONE"),
 "promoted_status":lambda d:d.update(status="NATIVE_APPROVED"),
 "unknown_field":lambda d:d.update(ready=True),
 "missing_evidence":lambda d:d.pop("required_native_evidence"),
 "forged_rights":lambda d:d["required_native_evidence"].update(per_asset_rights_approval=True),
 "forged_install":lambda d:d["required_native_evidence"].update(native_mapids_reserved_review="passed"),
 "fake_mapid3":lambda d:d["required_native_evidence"].update(mapid_3_design_and_runtime_resolution="approved"),
 "fake_windows":lambda d:d["required_native_evidence"].update(windows_release_manifest_and_qa={"pass":True}),
 "unknown_receipt":lambda d:d["required_native_evidence"].update(unaudited=True),
 "missing_rights_gate":lambda d:d["required_native_evidence"].pop("per_asset_rights_approval"),
 "native_technical_one":lambda d:d.update(native_technical_completed=1),
 "native_playable_one":lambda d:d.update(native_playable_completed=1),
 "g_overflow":lambda d:d.update(g_github_completed=33),
 "can_install_true":lambda d:d.update(can_install=True),
 "can_release_true":lambda d:d.update(can_release=True),
 "can_reserve_true":lambda d:d.update(can_reserve_mapids=True),
 "native_game_write":lambda d:d.update(native_game_files_modified=True),
 "saves_read":lambda d:d.update(saves_read=True),
 "saves_written":lambda d:d.update(saves_modified=True),
 "executable_run":lambda d:d.update(tests_game_exe_executed=True),
 "joiplay_run":lambda d:d.update(tests_joiplay_executed=True),
 "alter_snapshot_mapids":lambda d:d["historical_snapshot"].update(physically_observed_mapids=647),
 "move_candidate_range":lambda d:d["historical_snapshot"].update(unova_candidate_start=442),
 "invent_map_reserved":lambda d:d["historical_snapshot"].update(candidate_block_native_reserved=True),
 "claim_future_reservations":lambda d:d["historical_snapshot"].update(future_mapid_reservations_verified=True),
 "claim_independent_source":lambda d:d["historical_snapshot"].update(independently_verified_native_mapids_from_repo=True),
 "mapid3_resolved":lambda d:d["historical_snapshot"].update(mapid_3_missing_reported=False),
 "missing_stage":lambda d:d["steps"].pop(),
 "extra_stage":lambda d:d["steps"].append(copy.deepcopy(d["steps"][-1])),
 "wrong_stage_order":lambda d:d["steps"].reverse(),
 "stage_fake_receipt":lambda d:d["steps"][0].update(verified_receipt="A04_APPROVED"),
 "stage_installed":lambda d:d["steps"][7].update(can_install=True),
 "stage_reserved":lambda d:d["steps"][1].update(can_reserve=True),
 "stage_qagame":lambda d:d["steps"][10].update(game_exe_qa_verified=True),
 "stage_qaandroid":lambda d:d["steps"][9].update(android_qa_verified=True),
 "stage_human_approval":lambda d:d["steps"][10].update(native_acceptance="NATIVE_APPROVED"),
 "dependency_deleted":lambda d:d["steps"][1].update(depends_on=[]),
 "missing_source_path":lambda d:d["steps"][4].update(tool_path="scripts/regions/missing.py"),
 "unexpected_note":lambda d:d.update(provenance_notes=[]),
 "unlisted_gate":lambda d:d["technical_gates"][0].update(id="A_TECH_09"),
 "skip_license_gate":lambda d:d["technical_gates"][0].update(depends_on=[]),
 "skip_human_review":lambda d:d["technical_gates"][7].update(depends_on=["A_TECH_07"]),
 "remove_gate":lambda d:d["technical_gates"].pop(),
 "gate_approved":lambda d:d["technical_gates"][0].update(approved=True),
 "gate_done":lambda d:d["technical_gates"][4].update(status="COMPLETE"),
 "gate_install":lambda d:d["technical_gates"][3].update(can_install=True),
 "gate_missing_proof":lambda d:d["technical_gates"][7].update(evidence_keys=[]),
 "A16_auto_reserve":lambda d:d["safe_next_action"].update(auto_reserve_mapids=True),
 "A16_auto_install":lambda d:d["safe_next_action"].update(auto_install=True),
 "A16_not_redacted":lambda d:d["safe_next_action"].update(accept_only=["Game.exe"]),
 "A16_approve_rights":lambda d:d["safe_next_action"].update(auto_approve_rights=True),
 "source_changed":lambda d:d["sources"].update(historical_mapids="game/Data/MapInfos.rxdata"),
 "other_region_omitted":lambda d:d["cross_region_safeguards"].remove("SINNOH"),
}
for _name,_change in _TAMPERS.items():
    def _case(self,change=_change):
        self.reject(change)
    setattr(UnovaA15Tests,"test_negative_"+_name,_case)

# In-memory substitutions deliberately model stale or malicious source facts.
_SOURCE_CASES={
 "A05_reserve":(a15.SOURCES["historical_mapids"],
   lambda j:j.update(can_reserve_mapids=True)),
 "A05_invent_physical_map":(a15.SOURCES["historical_mapids"],
   lambda j:j["evidence"].update(b01_physical_map_count=700)),
 "A05_assign_mapid":(a15.SOURCES["historical_mapids"],
   lambda j:j["proposed_area_to_native_mapid"].update({"UNOVA_NUVEMA":518})),
 "A05_shift_candidates":(a15.SOURCES["historical_mapids"],
   lambda j:j["unova_preferred_candidate"].update(start=442)),
 "A05_more_candidates":(a15.SOURCES["historical_mapids"],
   lambda j:j["unova_preferred_candidate"].update(count=90)),
 "A05_sinnoh_overlap":(a15.SOURCES["historical_mapids"],
   lambda j:j["sinnoh_administrative_hold"].update(end=599)),
 "A05_future_claims":(a15.SOURCES["historical_mapids"],
   lambda j:j.update(future_reservations_verified=True)),
 "region_playable":(a15.SOURCES["region_registry"],
   lambda j:j["regions"]["UNOVA"].update(status="playable")),
 "tracker_native_one":(a15.SOURCES["github_tracker"],
   lambda j:j["native_playable_bar"].update(completed=1)),
 "tracker_technical_one":(a15.SOURCES["github_tracker"],
   lambda j:j["native_technical_bar"].update(completed=1)),
 "G08_native":(a15.SOURCES["prior_G08"],
   lambda j:j.update(can_install=True)),
}
for _name,(_path,_mutate) in _SOURCE_CASES.items():
    def _case(self,path=_path,mutate=_mutate):
        self.source_mutation(path,mutate)
    setattr(UnovaA15Tests,"test_source_tamper_"+_name,_case)

if __name__=="__main__":
    unittest.main()
