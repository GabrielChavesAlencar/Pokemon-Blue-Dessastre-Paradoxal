"""G12: public evidence cross-audit, 44 native cases and fail-closed handoff."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_g12_handoff as g12


class SinnohG12HandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.handoff=json.loads(g12.safe_text(ROOT,g12.HANDOFF))
        cls.android=g12.ch20.audit(ROOT)
        cls.chain=g12.g11.run(ROOT)
        cls.ledger=json.loads(g12.safe_text(ROOT,g12.LEDGER))
        cls.docs={k:g12.safe_text(ROOT,p) for k,p in g12.DOCUMENTS.items()}

    def audited(self,mutate=None):
        h=copy.deepcopy(self.handoff)
        a=copy.deepcopy(self.android)
        c=copy.deepcopy(self.chain)
        l=copy.deepcopy(self.ledger)
        d=copy.deepcopy(self.docs)
        if mutate:mutate(h,a,c,l,d)
        return g12.audit(h,a,c,l,d)

    def reject(self,mutate):
        with self.assertRaisesRegex(ValueError,"SINNOH_G12_BLOCKED"):
            self.audited(mutate)

    def test_01_report_only_public_metadata_never_native_approval(self):
        r=self.audited()
        self.assertEqual(r["stage"],"G12")
        self.assertEqual(r["status"],
            "GITHUB_G01_G12_HANDOFF_PREPARED_NATIVE_ACCEPTANCE_PENDING")
        self.assertEqual(r["github_stages_audited"],11)
        self.assertEqual(r["github_stages_with_versioned_handoff"],12)
        self.assertTrue(r["github_delivery_completion_is_not_gameplay_completion"])
        self.assertEqual(r["mode"],"PUBLIC_SOURCES_ONLY_ZERO_NATIVE_EVIDENCE")

    def test_02_official_CH20_category_counts_and_44_are_exact(self):
        r=self.audited()
        self.assertEqual(r["native_cases_total"],44)
        self.assertEqual(r["case_counts"],g12.COUNTS)
        self.assertEqual(r["windows_cases"],43)
        self.assertEqual(r["android_cases"],1)
        self.assertEqual(r["completed_native_cases"],0)
        self.assertEqual(r["evidence_accepted_cases"],0)
        self.assertEqual(len(r["native_case_matrix"]),44)
        self.assertEqual(r["native_case_hash_sha256"],
                         self.android["checklist_sha256"])

    def test_03_ids_and_kind_order_match_CH20_exactly(self):
        r=self.audited()
        self.assertEqual([x["id"] for x in r["native_case_matrix"]],
                         [x["id"] for x in self.android["cases"]])
        self.assertEqual(r["native_case_matrix"][0]["id"],"ball-TURTWIG")
        self.assertEqual(r["native_case_matrix"][-1]["id"],"android-joi-play")
        self.assertEqual(len({x["id"] for x in r["native_case_matrix"]}),44)

    def test_04_win_loss_and_normal_master_are_not_skipped(self):
        cases=[x for x in self.handoff["cases"] if x["kind"]=="barry"]
        self.assertEqual(len(cases),12)
        for species,counter in zip(g12.ch20.STARTERS,g12.ch20.RIVALS):
            subset=[x for x in cases if x["starter"]==species]
            self.assertEqual(len(subset),4)
            self.assertEqual({(x["mode"],x["outcome"]) for x in subset},
                {("normal","win"),("normal","loss"),
                 ("master","win"),("master","loss")})
            self.assertEqual({x["expected_rival"] for x in subset},{counter})
            self.assertEqual({x["expected_scaling_percent"] for x in subset
                              if x["mode"]=="normal"},{70})
            self.assertEqual({x["expected_scaling_percent"] for x in subset
                              if x["mode"]=="master"},{90})

    def test_05_all_44_require_human_evidence_and_no_native_ids(self):
        r=self.audited()
        for c in r["native_case_matrix"]:
            self.assertEqual(c["status"],"pending")
            self.assertIsNone(c["evidence"])
            self.assertGreater(len(c["required_human_evidence"]),35)
            self.assertNotIn("map_id",c)
            self.assertNotIn("arrival_x",c)
            self.assertNotIn("x",c)
        self.assertEqual(sum(x["platform"]=="android" for x in r["native_case_matrix"]),1)

    def test_06_all_11_GitHub_documents_available_and_hashed(self):
        r=self.audited()
        self.assertEqual(set(r["stage_documents"]),{f"G{i:02}" for i in range(1,12)})
        for stage,row in r["stage_documents"].items():
            self.assertEqual(row["path"],g12.DOCUMENTS[stage])
            self.assertEqual(row["sha256"],
                hashlib.sha256(self.docs[stage].encode("utf-8")).hexdigest())
            self.assertFalse(row["native_approval_from_document"])

    def test_07_gates_do_not_authorize_game_or_mark_rights(self):
        r=self.audited()
        self.assertEqual([x["id"] for x in r["local_gates"]],list(g12.GATES))
        self.assertTrue(all(x["status"]=="pending" for x in r["local_gates"]))
        for field in ("main_game_or_user_saves_modified",
                      "real_windows_sandbox_started","game_exe_tested",
                      "joiplay_tested","r07_complete","r08_complete",
                      "r09_complete","may_launch_native_on_host",
                      "can_install_live_game","gameplay_approved"):
            self.assertIs(r[field],False)
        self.assertEqual((r["phase_b_approved"],r["phase_c_approved"],
                          r["phase_d_approved"]),(0,0,0))

    def test_08_forged_CH20_approval_and_package_rejected(self):
        for change in (
            lambda h,a,c,l,d:a.update(completed_native_cases=44),
            lambda h,a,c,l,d:a.update(game_exe_tested=True),
            lambda h,a,c,l,d:a.update(joiplay_tested=True),
            lambda h,a,c,l,d:a.update(manual_evidence_accepted=True),
            lambda h,a,c,l,d:a["package"].update(status="STRUCTURE_PRESENT_UNVERIFIED"),
        ):
            with self.subTest(change=repr(change)):self.reject(change)

    def test_09_missing_duplicate_or_reordered_native_case_rejected(self):
        for change in (
            lambda h,a,c,l,d:h["cases"].pop(),
            lambda h,a,c,l,d:h["cases"].append(copy.deepcopy(h["cases"][0])),
            lambda h,a,c,l,d:h["cases"].reverse(),
            lambda h,a,c,l,d:h["cases"][0].update(id="ball-CHARMANDER"),
        ):
            with self.subTest(change=repr(change)):self.reject(change)

    def test_10_false_accepted_case_and_screenshot_not_published(self):
        for change in (
            lambda h,a,c,l,d:h["cases"][0].update(native_status="passed"),
            lambda h,a,c,l,d:h["cases"][0].update(evidence={"sha256":"a"*64}),
            lambda h,a,c,l,d:h["cases"][1].update(observation={"pass":True}),
            lambda h,a,c,l,d:h.update(completed_native_cases=1),
            lambda h,a,c,l,d:h.update(manually_reviewed_cases=1),
        ):
            with self.subTest(change=repr(change)):self.reject(change)

    def test_11_platform_swap_or_Rival_wrong_percent_rejected(self):
        for change in (
            lambda h,a,c,l,d:h["cases"][0].update(platform="android"),
            lambda h,a,c,l,d:h["cases"][-1].update(platform="windows"),
            lambda h,a,c,l,d:h["cases"][1].update(expected_scaling_percent=90),
            lambda h,a,c,l,d:h["cases"][1].update(expected_rival="TURTWIG"),
            lambda h,a,c,l,d:h["cases"][-1].update(independent_save_required=False),
        ):
            with self.subTest(change=repr(change)):self.reject(change)

    def test_12_unchanged_CH20_source_cannot_be_forged(self):
        for change in (
            lambda h,a,c,l,d:a["cases"][0].update(native_status="passed"),
            lambda h,a,c,l,d:a["cases"].pop(),
            lambda h,a,c,l,d:a["cases"][0].update(evidence="faked"),
            lambda h,a,c,l,d:a.update(checklist_total=43),
            lambda h,a,c,l,d:a.update(by_kind={"starter":44}),
        ):
            with self.subTest(change=repr(change)):self.reject(change)

    def test_13_L01_L05_status_or_count_mutation_rejected(self):
        for change in (
            lambda h,a,c,l,d:h["qa_prerequisites"][0].update(status="passed"),
            lambda h,a,c,l,d:h["qa_prerequisites"].pop(),
            lambda h,a,c,l,d:h["qa_prerequisites"][4].update(id="L04"),
            lambda h,a,c,l,d:h["qa_prerequisites"][1].update(required="test"),
            lambda h,a,c,l,d:h.update(windows_cases=44),
        ):
            with self.subTest(change=repr(change)):self.reject(change)

    def test_14_runtime_rights_or_released_marker_forgery_rejected(self):
        for field in ("real_b10_execution_verified","real_b11_save_isolation_verified",
                      "real_map_ids_and_events_verified","asset_rights_verified",
                      "native_pbs_compiled_verified","game_exe_tested",
                      "joiplay_tested","r07_complete","r08_complete","r09_complete",
                      "can_launch_game_now","can_install_live_game"):
            with self.subTest(field=field):
                self.reject(lambda h,a,c,l,d,field=field:h.update({field:True}))

    def test_15_phase_gates_b_c_d_cannot_advance(self):
        for phase in ("b","c","d"):
            with self.subTest(phase=phase):
                self.reject(lambda h,a,c,l,d,phase=phase:
                            h.update({"phase_"+phase+"_approved":1}))
        self.reject(lambda h,a,c,l,d:h.update(phase_b_approved=True))

    def test_16_G11_B07_B11_provenance_mutation_rejected(self):
        for change in (
            lambda h,a,c,l,d:c.update(expected_synthetic_clone_map_count=703),
            lambda h,a,c,l,d:c.update(candidate_terrain_maps=55),
            lambda h,a,c,l,d:c.update(game_exe_tested=True),
            lambda h,a,c,l,d:c.update(save_snapshot_coverage_proven=True),
            lambda h,a,c,l,d:c.update(private_baseline_uploaded=True),
            lambda h,a,c,l,d:c["chain"][3].update(stage="B09"),
        ):
            with self.subTest(change=repr(change)):self.reject(change)

    def test_17_progress_32_20_and_R07_R09_stay_pending(self):
        for change in (
            lambda h,a,c,l,d:l["phase_gates"].update(technically_approved=1),
            lambda h,a,c,l,d:l["phase_gates"].update(playable_in_game_executable=1),
            lambda h,a,c,l,d:l["phase_gates"].update(fully_tested_native=1),
            lambda h,a,c,l,d:l["remap_workstream"]["substeps"][6].update(complete=True),
            lambda h,a,c,l,d:l["intro_workstream"].update(native_verified=True),
            lambda h,a,c,l,d:l["barry_pbs_workstream"].update(pbs_compiled=True),
            lambda h,a,c,l,d:l["native_playtest_workstream"].update(native_qa_approved=True),
        ):
            with self.subTest(change=repr(change)):self.reject(change)

    def test_18_document_missing_or_unknown_json_fields_blocked(self):
        self.reject(lambda h,a,c,l,d:d.pop("G07"))
        self.reject(lambda h,a,c,l,d:d.update(G06="hi"))
        self.reject(lambda h,a,c,l,d:h.update(unknown_gameplay_approved=True))
        self.reject(lambda h,a,c,l,d:h.update(status="NATIVE_APPROVED"))

    def test_19_cli_outputs_public_report_and_no_host_save_identifiers(self):
        p=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/audit_sinnoh_g12_handoff.py")],
            cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(p.returncode,0,p.stderr)
        obj=json.loads(p.stdout)
        self.assertEqual(obj["stage"],"G12")
        self.assertEqual(len(obj["native_case_matrix"]),44)
        self.assertEqual(obj["completed_native_cases"],0)
        self.assertFalse(obj["game_exe_tested"])
        for secret in (r"C:\Users","Save01.rxdata","private-baseline.json",
                       "hmac_key","source_zip_sha256","raw_game_path"):
            self.assertNotIn(secret,p.stdout)

    def test_20_cli_rejects_private_input_without_revealing_it(self):
        p=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/audit_sinnoh_g12_handoff.py"),
            "--user-save",r"C:\Users\tester\Save01.rxdata"],
            cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(p.returncode,2)
        self.assertIn("SINNOH_G12_BLOCKED",p.stderr)
        self.assertNotIn("Save01.rxdata",p.stderr)
        self.assertNotIn(r"C:\Users",p.stderr)


if __name__=="__main__":
    unittest.main()
