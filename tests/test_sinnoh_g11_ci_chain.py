"""G11: B07→B11 synthetic integration; never run or inspect a native Game.exe."""
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
import audit_sinnoh_g11_ci_chain as g11
import audit_sinnoh_b11_host_saves as b11
import prepare_sinnoh_b10_save_isolation as b10


class SinnohG11ChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs={k:g11.b06.load(path) for k,path in g11.CONTRACT_PATHS.items()}
        cls.sources={k:(ROOT/p).read_text(encoding="utf-8") for k,p in g11.SUITES.items()}

    def audited(self,change=None):
        docs=copy.deepcopy(self.docs)
        sources=dict(self.sources)
        if change:change(docs,sources)
        return g11.audit(docs,sources)

    def reject(self,change):
        with self.assertRaisesRegex(ValueError,"SINNOH_G11_BLOCKED"):
            self.audited(change)

    def chain(self):
        # Reuse the existing B07→B08→B09→B10 synthetic helpers *without*
        # importing their TestCase at module scope (no redundant discovery).
        from test_sinnoh_b10_save_isolation import B10Tests
        helper=B10Tests("test_01_metadata_preflight_with_unapproved_B09")
        helper.setUpClass()
        self.addCleanup(helper.doCleanups)
        project,game,files,dry,plan,result,native_b01,proof=helper.audit_fixture()
        return helper,project,game,files,dry,plan,result,native_b01,proof

    def test_01_contracts_chained_with_expected_IDs(self):
        r=self.audited()
        self.assertEqual(r["stage"],"G11")
        self.assertEqual([x["stage"] for x in r["chain"]],
                         ["B07","B08","B09","B10","B11"])
        self.assertEqual(r["expected_terrain_candidate_ids"],[442,495])
        self.assertEqual(r["expected_synthetic_clone_map_count"],702)
        self.assertEqual(r["candidate_terrain_maps"],54)
        self.assertEqual(r["private_pngs_required_by_B08"],14)
        self.assertEqual(r["png_bytes_of_real_donor_inspected_in_CI"],0)

    def test_02_each_existing_suite_is_detected_not_claimed_executed_by_manifest(self):
        r=self.audited()
        assert len(r["chain"])==5
        self.assertTrue(all(x["source_contract_verified"] and
                            x["discovered_test_methods"]>=8 and
                            not x["native_runtime_verified"]
                            for x in r["chain"]))
        self.assertGreaterEqual(r["integration_suite"]["discovered_test_methods"],15)
        self.assertTrue(r["integration_suite"]["includes_synthetic_full_chain"])

    def test_03_runtime_rights_and_game_gates_stay_at_zero(self):
        r=self.audited()
        for k in ("game_exe_tested","joiplay_tested","sandbox_run_performed",
                  "r07_complete","r08_complete","r09_complete",
                  "can_install_live_game","save_snapshot_coverage_proven",
                  "assumed_installed_or_playable","private_baseline_uploaded"):
            self.assertIs(r[k],False)
        self.assertEqual((r["phase_b_approved"],r["phase_c_approved"],
                          r["phase_d_approved"]),(0,0,0))

    def test_04_wsb_policy_two_readonly_offline_mappings(self):
        r=self.audited()
        for k in ("wsb_template_readonly","wsb_template_network_disabled",
                  "wsb_template_clipboard_disabled","no_game_autostart",
                  "saves_excluded_from_B09"):
            self.assertIs(r[k],True)

    def test_05_source_sha_and_manifest_drift_cannot_pass(self):
        for change in (
            lambda d,s:d["b08"].update(b07_source_sha256="0"*64),
            lambda d,s:d["b09"].update(native_inventory_sha256="f"*64),
            lambda d,s:d["b10"].update(native_b01_inventory_sha256="f"*64),
            lambda d,s:d["b11"].update(b10_status="IN_USE"),
        ):
            with self.subTest(change=repr(change)):
                self.reject(change)

    def test_06_map_count_and_empty_placeholders_never_promoted(self):
        for change in (
            lambda d,s:d["b07"]["candidate_terrain_destinations"].append(496),
            lambda d,s:d["b08"].update(expected_staged_maps=55),
            lambda d,s:d["b09"].update(expected_qa_clone_map_count=703),
            lambda d,s:d["b10"].update(expected_original_maps=649),
            lambda d,s:d["b11"].update(expected_clone_maps=703),
        ):
            with self.subTest(change=repr(change)):
                self.reject(change)

    def test_07_forged_regional_rights_reservation_and_native_QA_are_blocked(self):
        for stage in ("b07","b08","b09","b10","b11"):
            for field in ("r07_complete","r08_complete","r09_complete",
                          "phase_b_approved","phase_c_approved","phase_d_approved"):
                with self.subTest(stage=stage,field=field):
                    self.reject(lambda d,s,stage=stage,field=field:
                        d[stage].update({field:1 if field.startswith("phase") else True}))

    def test_08_no_imported_donor_events_and_no_autostart(self):
        for change in (
            lambda d,s:d["b07"].update(imports_donor_events=True),
            lambda d,s:d["b07"].update(imports_donor_scripts=True),
            lambda d,s:d["b07"].update(imports_donor_pbs=True),
            lambda d,s:d["b08"].update(overlay_is_a_non_runnable_private_copy=False),
            lambda d,s:d["b09"].update(never_launches_executable=False),
            lambda d,s:d["b10"].update(no_logon_command=False),
            lambda d,s:d["b11"].update(no_autostart_Game_exe=False),
        ):
            with self.subTest(change=repr(change)):
                self.reject(change)

    def test_09_save_boundary_mutations_cannot_pass(self):
        for change in (
            lambda d,s:d["b07"].update(preserves_saves=False),
            lambda d,s:d["b09"].update(excludes_saved_games_and_user_profiles=False),
            lambda d,s:d["b10"].update(host_data_and_saves_never_mapped=False),
            lambda d,s:d["b11"].update(host_saves_never_copied=False),
            lambda d,s:d["b11"].update(
                host_saves_unchanged_after_native_test_confirmed=True),
        ):
            with self.subTest(change=repr(change)):
                self.reject(change)

    def test_10_missing_contract_or_changed_test_source_fails_closed(self):
        self.reject(lambda d,s:d.pop("b08"))
        self.reject(lambda d,s:d.update(b11=[]))
        self.reject(lambda d,s:s.pop("B10"))
        self.reject(lambda d,s:s.update(B11="not valid python :-"))
        self.reject(lambda d,s:s.update(G11="class Empty: pass"))

    def test_11_cli_refuses_private_paths_and_does_not_echo_them(self):
        cmd=[sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_g11_ci_chain.py")]
        p=subprocess.run(cmd+["--game-data",r"C:\Users\tester\Save01.rxdata"],
                         cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(p.returncode,2)
        self.assertIn("SINNOH_G11_BLOCKED",p.stderr)
        self.assertNotIn("Save01.rxdata",p.stderr)
        self.assertNotIn(r"C:\Users",p.stderr)

    def test_12_cli_emits_public_json_with_no_personal_data(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_g11_ci_chain.py")],
                         cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(p.returncode,0,p.stderr)
        r=json.loads(p.stdout)
        self.assertEqual(r["status"],
            "B07_B11_PUBLIC_CONTRACT_CHAIN_RECONCILED_SYNTHETIC_ONLY")
        self.assertTrue(r["public_report_only"])
        for forbidden in (r"C:\Users", "Save01.rxdata","private-baseline.json",
                          "synthetic save 1","hmac_key","source_zip_sha256"):
            self.assertNotIn(forbidden,p.stdout)

    def test_13_fixture_builds_B07_B08_B09_in_private_clone_without_saves(self):
        helper,project,game,files,dry,plan,result,native_b01,proof=self.chain()
        clone=project/result["relative_path"]
        self.assertTrue((clone/"Data/Map442.rxdata").is_file())
        self.assertTrue((clone/"Data/Map495.rxdata").is_file())
        self.assertTrue((clone/"Game.exe").is_file())  # inert bytes, not run
        self.assertFalse((clone/"Save01.rxdata").exists())
        self.assertFalse((clone/"Saves").exists())
        self.assertTrue((game/"Save01.rxdata").is_file())
        self.assertEqual(proof["clone_total_map_ids"],702)
        self.assertEqual(proof["sinnoh_map_ids_confirmed"],54)
        self.assertFalse(result["safe_to_launch"])

    def test_14_fixture_private_B10_to_B11_unmodified_snapshot(self):
        helper,project,game,files,dry,plan,result,native_b01,proof=self.chain()
        clone=project/result["relative_path"]
        prepared=b10.prepare_session(project,clone,plan["plan_sha256"],proof,
                                    {"supported":True,"feature_enabled":True})
        self.assertFalse(prepared["game_exe_started"])
        self.assertFalse(prepared["sandbox_session_started"])
        b11.b10_session(project,plan["plan_sha256"])
        with tempfile.TemporaryDirectory(prefix="g11-mock-save-") as path:
            save=Path(path)/"Save01.rxdata"
            save.write_bytes(b"G11 MOCK GAME SAVE NOT PRIVATE")
            before=b11.prepare_before(project,plan["plan_sha256"],[Path(path)])
            after=b11.inspect_after(project,before["watch_id"],"not_run")
            self.assertEqual(before["monitored_files_before"],1)
            self.assertEqual(after["files_changed"],0)
            self.assertTrue(after["watch_unchanged"])
            self.assertFalse(after["host_saves_globally_isolated_proven"])
            self.assertFalse(after["guest_vm_execution_independently_verified"])
            self.assertFalse(after["gameplay_approved"])
            share=json.dumps({"before":before,"after":after})
            self.assertNotIn(str(Path(path)),share)
            self.assertNotIn("Save01.rxdata",share)
            self.assertNotIn("G11 MOCK GAME SAVE",share)
            self.assertFalse(before["paths_names_and_saves_in_report"])

    def test_15_fixture_same_size_save_mutation_is_detected_without_approving(self):
        helper,project,game,files,dry,plan,result,native_b01,proof=self.chain()
        clone=project/result["relative_path"]
        b10.prepare_session(project,clone,plan["plan_sha256"],proof,
                            {"supported":True,"feature_enabled":True})
        with tempfile.TemporaryDirectory(prefix="g11-mock-save-") as path:
            file=Path(path)/"Save01.rxdata"
            original=b"G11 MOCK SAVE CONTENT ONLY"
            file.write_bytes(original)
            baseline=b11.prepare_before(project,plan["plan_sha256"],[Path(path)])
            file.write_bytes(b"x"*len(original))
            after=b11.inspect_after(project,baseline["watch_id"],"not_run")
            self.assertEqual(after["files_changed"],1)
            self.assertFalse(after["watch_unchanged"])
            self.assertEqual(after["status"],
                "HOST_WATCHED_FILES_CHANGED_REVIEW_REQUIRED")
            self.assertFalse(after["host_saves_globally_isolated_proven"])

    def test_16_fixture_tampered_B09_clone_blocked_before_B10_session(self):
        helper,project,game,files,dry,plan,result,native_b01,proof=self.chain()
        clone=project/result["relative_path"]
        (clone/"Data/Map442.rxdata").write_bytes(b"modified")
        with self.assertRaisesRegex(ValueError,"SINNOH_B10_BLOCKED"):
            b10.audit_clone(project,clone,plan["plan_sha256"],
                            helper.c,helper.c09,native_b01,helper.b05)
        self.assertFalse((project/".blue-work/sinnoh-b10-sandbox").exists())

    def test_17_fixture_sandbox_config_mutation_blocks_B11_before_snapshot(self):
        helper,project,game,files,dry,plan,result,native_b01,proof=self.chain()
        clone=project/result["relative_path"]
        prepared=b10.prepare_session(project,clone,plan["plan_sha256"],proof,
                                     {"supported":True,"feature_enabled":True})
        cfg=project/prepared["config_relative_path"]
        cfg.write_text("<Configuration><Networking>Enable</Networking></Configuration>",
                       encoding="utf-8")
        with tempfile.TemporaryDirectory(prefix="g11-mock-save-") as path:
            (Path(path)/"Save01.rxdata").write_bytes(b"G11 MOCK")
            with self.assertRaisesRegex(ValueError,"SINNOH_B11_BLOCKED"):
                b11.prepare_before(project,plan["plan_sha256"],[Path(path)])
        self.assertFalse((project/".blue-work/sinnoh-b11-save-audit").exists())

    def test_18_fixture_executables_are_never_called_and_no_fake_host_approval(self):
        helper,project,game,files,dry,plan,result,native_b01,proof=self.chain()
        self.assertEqual(proof["clone_total_map_ids"],702)
        self.assertFalse(proof.get("game_exe_tested",False))
        self.assertFalse(proof.get("host_saves_runtime_isolation_verified",False))
        self.assertFalse(result.get("safe_to_launch",False))
        self.assertFalse((project/".blue-work/sinnoh-b10-sandbox").exists())
        # Source game copy is inert synthetic data: no process execution.
        self.assertEqual((game/"Game.exe").read_bytes(),
            b"MZ\x00synthetic executable - never run")


if __name__=="__main__":
    unittest.main()
