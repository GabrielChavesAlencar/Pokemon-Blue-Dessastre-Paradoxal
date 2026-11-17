"""G09: fail-closed cross-stage Sinnoh badge, HM, League and postgame QA."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_g09_progression as g09


class SinnohG09Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs={k:g09.safe_read(ROOT/path) for k,path in g09.DOCUMENTS.items()}
        cls.sources={k:g09.safe_read(ROOT/path,source=True)
                     for k,path in g09.SOURCES.items()}

    def audit(self,mutate=None):
        docs=copy.deepcopy(self.docs)
        sources=copy.deepcopy(self.sources)
        if mutate is not None:
            mutate(docs,sources)
        return g09.audit(docs,sources)

    def assert_blocked(self,mutate):
        with self.assertRaisesRegex(ValueError,"SINNOH_G09_BLOCKED"):
            self.audit(mutate)

    def test_01_static_report_does_not_approve_game(self):
        out=self.audit()
        self.assertEqual(out["status"],
            "CROSS_STAGE_PROGRESSION_AUDITED_OFFLINE_NATIVE_GATES_PENDING")
        self.assertEqual(out["mode"],"PUBLIC_MANIFESTS_AND_OFFLINE_FIXTURES_ONLY")
        for key in ("ready_to_install","gameplay_approved","physical_game_exe_tested",
                    "android_joiplay_tested","r07_complete","r08_complete","r09_complete",
                    "cross_region_hm_transfer_allowed"):
            self.assertFalse(out["safety"][key])
        for k in ("phase_b_approved","phase_c_approved","phase_d_approved"):
            self.assertEqual(out[k],0)

    def test_02_counts_reflect_8_gyms_8_HMs_league_6_postgame(self):
        self.assertEqual(self.audit()["counts"],{
            "gyms":8,"local_hm_pickup_gates":8,"league_checkpoints":8,
            "elite_four_members":4,"champion_battles":1,
            "separate_hall_of_fame_confirmations":1,
            "optional_postgame_gates":6,
            "historical_elite_cynthia_rematch_references":5,
            "native_gym_battles_verified":0,
            "native_hm_pickup_events_verified":0,
            "native_league_battles_verified":0,
            "native_postgame_quests_verified":0,
        })

    def test_03_narrative_order_and_CH11_milestone_order_remain_distinct(self):
        order=self.audit()["badge_vs_hm_order"]
        self.assertEqual(order["narrative_gym_badge_order"],
            ["COAL","FOREST","RELIC","COBBLE","FEN","MINE","ICICLE","BEACON"])
        self.assertEqual(order["registry_and_hm_catalog_badge_order"],
            ["COAL","FOREST","COBBLE","RELIC","FEN","MINE","ICICLE","BEACON"])
        self.assertTrue(order["mapping_by_badge_not_array_position"])

    def test_04_fantina_defog_and_maylene_fly_not_swapped(self):
        rows=self.audit()["gym_progression"]
        self.assertEqual([(r["leader"],r["badge"],r["field_move"],r["hm_item"])
                          for r in rows[2:4]],[
            ("Fantina","RELIC","DEFOG","HM05"),
            ("Maylene","COBBLE","FLY","HM02"),
        ])
        self.assertEqual(rows[3]["prior_badges_required"],["COAL","FOREST","RELIC"])

    def test_05_each_gym_depends_on_prefix_and_all_native_fields_false(self):
        rows=self.audit()["gym_progression"]
        for n,g in enumerate(rows):
            self.assertEqual(g["order"],n+1)
            self.assertEqual(g["prior_badges_required"],
                             [x["badge"] for x in rows[:n]])
            self.assertFalse(g["native_gym_battle_verified"])
            self.assertFalse(g["native_badge_verified"])
            self.assertFalse(g["local_hm_pickup_verified"])
            self.assertEqual(g["region_scoped_HM_gate"],"BADGE_PLUS_LOCAL_PICKUP")

    def test_06_hm_acquisition_requires_local_receipt_not_bag_only(self):
        rows=self.audit()["gym_progression"]
        mapping={r["badge"]:(r["field_move"],r["hm_item"]) for r in rows}
        self.assertEqual(mapping["COAL"],("ROCK_SMASH","HM06"))
        self.assertEqual(mapping["FOREST"],("CUT","HM01"))
        self.assertEqual(mapping["FEN"],("SURF","HM03"))
        self.assertEqual(mapping["MINE"],("STRENGTH","HM04"))
        self.assertEqual(mapping["ICICLE"],("ROCK_CLIMB","HM08"))
        self.assertEqual(mapping["BEACON"],("WATERFALL","HM07"))

    def test_07_league_order_and_S20_entry_gate(self):
        rows=self.audit()["league_progression"]
        self.assertEqual([r["checkpoint"] for r in rows],list(g09.s21.IDS))
        self.assertEqual(rows[0]["previous"],"P08_SAFE_RETURN_FROM_DISTORTION_WORLD")
        self.assertEqual(rows[0]["required_local_badges"],["BEACON"])
        self.assertEqual(set(rows[1]["required_local_badges"]),set(g09.NARRATIVE_BADGES))

    def test_08_cynthia_win_does_not_complete_hall(self):
        out=self.audit()
        last=out["league_progression"][-2:]
        self.assertEqual(last[0]["checkpoint"],"P09_CYNTHIA_BATTLE")
        self.assertEqual(last[0]["outcome"],"battle_won")
        self.assertEqual(last[1]["checkpoint"],"P09_HALL_OF_FAME")
        self.assertEqual(last[1]["previous"],"P09_CYNTHIA_BATTLE")
        self.assertEqual(last[1]["outcome"],"engine_hall_of_fame_confirmed")
        self.assertTrue(last[1]["engine_hall_of_fame_confirmation_required"])
        self.assertTrue(out["safety"]["cynthia_victory_is_not_hall_of_fame"])

    def test_09_all_six_postgame_gates_remain_reference_only(self):
        out=self.audit()
        self.assertEqual([p["checkpoint"] for p in out["postgame_gates"]],
                         list(g09.POSTGAME_IDS))
        for row in out["postgame_gates"]:
            self.assertTrue(row["requires_sinnoh_hall_of_fame"])
            self.assertFalse(row["native_quest_installed"])
            self.assertEqual(row["status"],"REFERENCE_ONLY")

    def test_10_postgame_different_conditions_not_confused(self):
        by={p["checkpoint"]:p for p in self.audit()["postgame_gates"]}
        self.assertEqual(by["P10_HEATRAN_QUEST"]["requires_previous_event"],
                         "P10_BATTLE_ZONE_ENTRY")
        for q in ("P10_DARKRAI_CONDITIONAL_QUEST","P10_SHAYMIN_CONDITIONAL_QUEST"):
            self.assertTrue(by[q]["requires_verified_event_item"])
        last=by["P10_OFFICIAL_STRONGEST_TEAM_REMATCHES"]
        self.assertTrue(last["requires_all_ten_leagues"])
        self.assertTrue(last["requires_verified_native_strongest_roster"])

    def test_11_forged_gym_awards_and_nonnative_levels_rejected(self):
        for fn in (
            lambda d,s:d["gyms"]["gyms"][0].update(badge_award_verified=True),
            lambda d,s:d["gyms"]["gyms"][0].update(physical_map_id=442),
            lambda d,s:d["gyms"].update(native_pbs_compiled=True),
            lambda d,s:d["gyms"].update(approved_for_install=True),
            lambda d,s:d["teams"]["trainers"][0]["native_pbs"].update(compiled=True),
        ):
            with self.subTest(mutation=repr(fn)):
                self.assert_blocked(fn)

    def test_12_badge_order_and_prerequisite_drift_rejected(self):
        for fn in (
            lambda d,s:d["gyms"]["gyms"][2].update(badge="COBBLE"),
            lambda d,s:d["gyms"]["gyms"][3].update(prerequisite_badges=["COAL"]),
            lambda d,s:d["badges"]["rules"][2].update(badge="RELIC"),
            lambda d,s:d["registry"]["regions"]["SINNOH"].update(
                milestones=list(g09.NARRATIVE_BADGES)),
        ):
            with self.subTest(mutation=repr(fn)):
                self.assert_blocked(fn)

    def test_13_hm_local_pickup_or_foreign_ownership_cannot_be_faked(self):
        for fn in (
            lambda d,s:d["hms"]["hms"][2].update(enabled=True),
            lambda d,s:d["hms"]["hms"][3].update(local_receipt_verified=True),
            lambda d,s:d["hms"]["hms"][0].update(hm_item="HM02"),
            lambda d,s:d["hms"]["policy"].update(
                foreign_region_items_never_count=False),
            lambda d,s:d["badges"].update(no_cross_region_key_item_or_hm_transfer=False),
            lambda d,s:s.update(field_policy=s["field_policy"].replace(
                'local_proof = current["current"] == "SINNOH"',
                "local_proof = true")),
        ):
            with self.subTest(mutation=repr(fn)):
                self.assert_blocked(fn)

    def test_14_league_missing_badge_or_wrong_order_blocked(self):
        for fn in (
            lambda d,s:d["league"]["steps"][1].update(requires_local_badges=[]),
            lambda d,s:d["league"]["steps"][0].update(previous=None),
            lambda d,s:d["league"]["steps"][3].update(previous="SINNOH_LEAGUE_BARRY_GATE"),
            lambda d,s:d["league"].update(native_league_installed=True),
            lambda d,s:d["story"].update(native_events_installed=True),
        ):
            with self.subTest(mutation=repr(fn)):
                self.assert_blocked(fn)

    def test_15_hall_victory_cannot_be_treated_as_engine_confirmation(self):
        for fn in (
            lambda d,s:d["league"]["steps"][-1].update(outcome="battle_won"),
            lambda d,s:d["league"]["steps"][-1].update(
                previous="P09_LUCIAN_BATTLE"),
            lambda d,s:d["story"].update(
                hall_of_fame_requires_separate_engine_confirmation=False),
            lambda d,s:d["league"]["restrictions"].update(
                cynthia_victory_alone_never_completes_league=False),
        ):
            with self.subTest(mutation=repr(fn)):
                self.assert_blocked(fn)

    def test_16_postgame_before_HoF_or_without_BattleZone_rejected(self):
        for fn in (
            lambda d,s:d["postgame"].update(requires_separate_hall_of_fame=False),
            lambda d,s:d["postgame"]["events"][0].update(
                requires_completed_sinnoh_hall_of_fame=False),
            lambda d,s:d["postgame"]["events"][1].update(
                requires_previous_event=None),
            lambda d,s:d["postgame"]["verification"].update(gameplay_certified=True),
            lambda d,s:d["postgame"]["events"][1].update(physical_map_id=450),
        ):
            with self.subTest(mutation=repr(fn)):
                self.assert_blocked(fn)

    def test_17_event_items_and_global_ten_leagues_are_required(self):
        for fn in (
            lambda d,s:d["postgame"]["events"][3].update(
                requires_event_item_verification=False),
            lambda d,s:d["postgame"]["events"][4].update(
                requires_event_item_verification=False),
            lambda d,s:d["postgame"]["events"][5].update(
                requires_all_ten_leagues=False),
            lambda d,s:d["postgame"]["events"][5].update(
                requires_native_strongest_team=False),
            lambda d,s:d["postgame"].update(
                global_world_champion_requires_all_ten_leagues=False),
            lambda d,s:d["postgame"].update(
                verified_static_legendary_events=["HEATRAN"]),
        ):
            with self.subTest(mutation=repr(fn)):
                self.assert_blocked(fn)

    def test_18_level_scaling_and_rematch_reference_not_claimed_native(self):
        for fn in (
            lambda d,s:s.update(campaign=s["campaign"].replace(
                "master? ? 90 : 70","master? ? 100 : 70")),
            lambda d,s:d["postgame"].update(
                local_historical_rematches_not_blue_full_power=False),
            lambda d,s:d["postgame"].update(
                elite_champion_historical_rematch_count=4),
            lambda d,s:d["teams"].update(native_pbs_compilation_verified=True),
        ):
            with self.subTest(mutation=repr(fn)):
                self.assert_blocked(fn)

    def test_19_missing_contract_or_unexpected_source_type_rejected(self):
        for fn in (
            lambda d,s:d.pop("hms"),
            lambda d,s:s.pop("league_adapter"),
            lambda d,s:d.update(postgame=[]),
            lambda d,s:s.update(regions=None),
        ):
            with self.subTest(mutation=repr(fn)):
                self.assert_blocked(fn)

    def test_20_cli_metadata_only_and_untrusted_path_block(self):
        path=ROOT/"scripts/regions/audit_sinnoh_g09_progression.py"
        ok=subprocess.run([sys.executable,str(path)],cwd=ROOT,
                          text=True,capture_output=True)
        self.assertEqual(ok.returncode,0,ok.stderr)
        report=json.loads(ok.stdout)
        self.assertEqual(report["stage"],"G09")
        self.assertEqual(report["counts"]["native_league_battles_verified"],0)
        self.assertNotIn("C:\\Users",ok.stdout)
        blocked=subprocess.run([sys.executable,str(path),
            "--game",r"C:\Private\game"],cwd=ROOT,
            text=True,capture_output=True)
        self.assertEqual(blocked.returncode,2)
        self.assertIn("SINNOH_G09_BLOCKED",blocked.stderr)
        self.assertNotIn(r"C:\Private",blocked.stderr)


if __name__=="__main__":
    unittest.main()
