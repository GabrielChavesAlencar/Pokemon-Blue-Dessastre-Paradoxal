"""G08: read-only Rowan/Barry physical ball and PBS policy integration."""
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
import audit_sinnoh_g08_opening_qa as g08
from build_sinnoh_barry_pbs import MATCHUPS, READY_MARKER, publish
from verify_sinnoh_barry_pbs import inspect as inspect_pbs
from test_sinnoh_barry_pbs import fixture


class SinnohG08OpeningQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents={name:g08.load_public(ROOT/path)
                       for name,path in g08.DATA_FILES.items()}
        cls.sources={name:g08.load_public(ROOT/path,text=True)
                     for name,path in g08.CODE_FILES.items()}

    def audited(self,mutate=None):
        docs=copy.deepcopy(self.documents)
        sources=copy.deepcopy(self.sources)
        if mutate:
            mutate(docs,sources)
        return g08.audit(docs,sources)

    def reject(self,mutate):
        with self.assertRaisesRegex(ValueError,"SINNOH_G08_BLOCKED"):
            self.audited(mutate)

    def test_01_baseline_approved_only_as_offline_contract(self):
        out=self.audited()
        self.assertEqual(out["stage"],"G08")
        self.assertEqual(out["status"],
            "ROWAN_BARRY_OFFLINE_CONTRACTS_CROSSCHECKED_NATIVE_BATTLE_PENDING")
        self.assertEqual(out["mode"],"READ_ONLY_GITHUB_STATIC_AND_SYNTHETIC_QA")
        for key in ("game_exe_tested","joiplay_tested","r07_complete",
                    "r08_complete","r09_complete","can_install_live_game",
                    "gameplay_approved","real_game_data_or_saves_accessed"):
            self.assertIs(out[key],False)
        for key in ("phase_b_approved","phase_c_approved","phase_d_approved"):
            self.assertEqual(out[key],0)

    def test_02_six_intro_flags_match_rowan_barry_pokedex_order(self):
        self.assertEqual(self.audited()["story_checkpoint_order"],[
            "mother_intro","barry_intro","rowan_briefcase_seen",
            "starter_received","rival_fought","pokedex_received",
        ])

    def test_03_three_physical_balls_and_rival_versions(self):
        out=self.audited()
        rows=out["player_choices"]
        self.assertEqual([(r["starter"],r["rival_species"])
                          for r in rows],list(MATCHUPS))
        self.assertEqual([r["rival_pbs_version"] for r in rows],[0,1,2])
        self.assertEqual([r["pbs_seed_level_not_battle_level"] for r in rows],[5]*3)
        for row in rows:
            self.assertEqual(row["location_symbol"],"SINNOH_LAKE_VERITY")
            self.assertFalse(row["native_pbs_compilation_verified"])
            self.assertFalse(row["battle_binding_verified"])
        self.assertEqual([r["ball_event_key"] for r in rows],
                         ["SN_BALL_TURTWIG","SN_BALL_CHIMCHAR","SN_BALL_PIPLUP"])

    def test_04_nine_offline_outcome_scenarios_expected(self):
        out=self.audited()
        cases=out["offline_battle_matrix"]
        self.assertEqual(len(cases),9)
        for name in ("TURTWIG","CHIMCHAR","PIPLUP"):
            three=[x for x in cases if x["player_starter"]==name]
            self.assertEqual([x["battle_result"] for x in three],
                             [True,False,None])
            self.assertEqual([x["expected_story_progresses"] for x in three],
                             [True,True,False])
            self.assertEqual([x["expected_heal_after_confirmed_battle"] for x in three],
                             [True,True,False])
            self.assertTrue(all(not x["native_result_verified"] for x in three))

    def test_05_dynamic_levels_do_not_republish_pbs_seed(self):
        p=self.audited()["balance"]
        self.assertEqual((p["normal_percent"],p["master_percent"]),(70,90))
        self.assertEqual(p["pbs_seed_level_only"],5)
        self.assertIsNone(p["numeric_fixed_trainer_level"])
        self.assertTrue(p["highest_non_egg_party_level"])
        self.assertEqual(p["rounding"],"integer_floor")
        self.assertEqual(p["master_requires_stage"],3)
        self.assertEqual(p["master_team_target"],4)
        self.assertEqual(p["max_opponents_per_side"],6)
        self.assertFalse(p["real_runtime_scaling_verified_in_game"])

    def test_06_only_static_offline_proofs_are_enabled(self):
        out=self.audited()
        gates=out["gates"]
        for key in ("three_physical_balls_no_rowan_dialog",
                    "story_order_and_state_dependencies_checked",
                    "no_duplicate_starter_intent_checked",
                    "barry_three_counter_versions_checked",
                    "nil_battle_must_not_advance",
                    "can_lose_false_is_completed_battle",
                    "pokedex_only_after_confirmed_barry",
                    "region_save_separation_required"):
            self.assertIs(gates[key],True)
        for key in ("ready_marker_generated","compiled_pbs_from_real_game_verified",
                    "map_ids_and_event_positions_verified",
                    "sprite_assets_verified","native_runtime_qc_executed"):
            self.assertIs(gates[key],False)

    def test_07_ch06_g07_rejects_early_mapids_or_forged_spawns(self):
        for change in (
            lambda d,s:d["events"]["maps"][0].update(map_id=442),
            lambda d,s:d["events"]["start"].update(
                verified_position=True,x=12,y=11),
            lambda d,s:d["b09"].update(can_mark_native_playable=True),
        ):
            self.subTest(repr(change))
            self.reject(change)

    def test_08_s13_rejects_skipped_rowan_or_dex(self):
        for f in (
            lambda d,s:d["intro"]["steps"][2].update(needs=[]),
            lambda d,s:d["intro"]["steps"][5].update(
                needs=["starter_received"]),
            lambda d,s:d["intro"]["steps"][4].update(
                native_callback_verified=True),
            lambda d,s:d["intro"].update(native_barry_pbs_compiled=True),
        ):
            with self.subTest(change=repr(f)):
                self.reject(f)

    def test_09_s14_rejects_wrong_counter_or_seed(self):
        for f in (
            lambda d,s:d["starters"]["balls"][0].update(
                rival_species="TURTWIG"),
            lambda d,s:d["starters"]["balls"][1].update(
                rival_pbs_version=2),
            lambda d,s:d["starters"].update(grant_seed_level=8),
            lambda d,s:d["starters"]["balls"][2].update(
                event_compiled=True),
            lambda d,s:d["starters"].update(
                compiled_pbs_barry_verified=True),
        ):
            with self.subTest(change=repr(f)):
                self.reject(f)

    def test_10_s17_rejects_relabeling_70_90_or_master(self):
        for f in (
            lambda d,s:d["s17"]["rules"].update(normal_percent=90),
            lambda d,s:d["s17"]["rules"].update(master_percent=70),
            lambda d,s:d["s17"]["rules"].update(master_requires_stage=2),
            lambda d,s:d["s17"]["rules"].update(master_team_target=6),
            lambda d,s:d["s17"]["rules"].update(no_fixed_trainer_levels_published=False),
            lambda d,s:d["s17"].update(native_trainer_pbs_verified=True),
            lambda d,s:d["s17"].update(real_trainer_levels=[40]),
        ):
            with self.subTest(change=repr(f)):
                self.reject(f)

    def test_11_ch12_ch15_cannot_fake_fixed_level_cap_or_blue_pbs(self):
        for f in (
            lambda d,s:d["ch12"]["level_cap"].update(regional_numeric_cap_in_save=28),
            lambda d,s:d["ch12"]["level_cap"].update(bst_cap_is_not_a_level_cap=False),
            lambda d,s:d["ch15"].update(native_pbs_compilation_verified=True),
            lambda d,s:d["ch15"]["dynamic_balance"].update(normal_percent=75),
        ):
            with self.subTest(change=repr(f)):
                self.reject(f)

    def test_12_cannot_remove_canlose_or_nil_result_guard(self):
        for original in (
            'setBattleRule("canLose")',
            'return false unless result == true || result == false',
            'return false unless commit_flag("rival_fought")',
            'return false unless commit_flag("pokedex_received")',
        ):
            self.reject(lambda d,s,original=original:
                s.update(pilot=s["pilot"].replace(original,"# removed")))

    def test_13_cannot_remove_runtime_starter_safety_guard(self):
        for original in (
            "return false if @starter_grant_in_progress",
            "return false unless pbAddPokemonSilent(requested, 5)",
            "return false unless scope && regional_state.equal?(scope) && starter == chosen",
        ):
            self.reject(lambda d,s,original=original:
                s.update(pilot=s["pilot"].replace(original,"# removed")))

    def test_14_campaign_runtime_source_cannot_deviate(self):
        self.reject(lambda d,s:s.update(
            campaign=s["campaign"].replace("master? ? 90 : 70","master? ? 70 : 70")))
        self.reject(lambda d,s:s.update(
            balance_fixture=s["balance_fixture"].replace(
                "Marshal.dump(trainers)","marshal_missing(trainers)")))

    def test_15_missing_contract_or_wrong_source_types_fail(self):
        self.reject(lambda d,s:d.pop("starters"))
        self.reject(lambda d,s:s.pop("campaign"))
        self.reject(lambda d,s:s.update(pilot={"unexpected":True}))
        self.reject(lambda d,s:d.update(s17=[]))

    def test_16_cli_json_is_machine_readable_without_private_paths(self):
        p=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/audit_sinnoh_g08_opening_qa.py")],
            cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(p.returncode,0,p.stderr)
        report=json.loads(p.stdout)
        self.assertEqual(report["stage"],"G08")
        self.assertEqual(len(report["offline_battle_matrix"]),9)
        self.assertFalse(report["can_install_live_game"])
        self.assertNotIn("Game.exe",p.stdout)
        self.assertNotIn("C:\\Users",p.stdout)

    def test_17_cli_rejects_untrusted_paths(self):
        p=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/audit_sinnoh_g08_opening_qa.py"),
            "--source","C:\\Private\\Save01.rxdata"],
            cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(p.returncode,2)
        self.assertIn("SINNOH_G08_BLOCKED",p.stderr)
        self.assertNotIn("C:\\Private",p.stderr)

    def test_18_barry_synthetic_PBS_draft_is_hash_checked_but_not_ready(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            game=fixture(root)
            output=root/".blue-work/g08-synthetic-draft"
            result=publish(game,output,root=root)
            checked=inspect_pbs(output,game,root=root)
            self.assertEqual(checked["teams_verified"],3)
            self.assertFalse(checked["ready_marker_allowed"])
            self.assertFalse(checked["pbs_compiled_in_game"])
            self.assertFalse(checked["may_install_into_game"])
            self.assertFalse(result["can_install"])
            self.assertFalse((output/READY_MARKER).exists())
            self.assertFalse((game/READY_MARKER).exists())

    def test_19_tampered_PBS_and_manifest_do_not_grant_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            game=fixture(root)
            output=root/".blue-work/g08-draft-corrupted"
            publish(game,output,root=root)
            manifest=output/"sinnoh-barry-pbs-report.json"
            report=json.loads(manifest.read_text("utf-8"))
            report["battle_proven"]=True
            manifest.write_text(json.dumps(report),encoding="utf-8")
            with self.assertRaises(ValueError):
                inspect_pbs(output,game,root=root)
            self.assertFalse((output/READY_MARKER).exists())

    def test_20_ruby_runtime_requires_real_execution_by_CI(self):
        r=self.audited()
        self.assertIn("tests/sinnoh_g08_opening_runtime.rb",r["offline_fixture_runs_required"])
        self.assertIs(r["gates"]["native_runtime_qc_executed"],False)
        self.assertFalse(r["game_exe_tested"])


if __name__=="__main__":
    unittest.main()
