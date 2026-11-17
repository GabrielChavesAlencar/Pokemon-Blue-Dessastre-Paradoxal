"""G05.3 — synthetic NPC travel permissions, installed proofs, return, rollback."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_unova_g05_travel as mod


class UnovaG053Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.reg, cls.it, cls.sp, cls.report = mod.load_project()
        cls.tracker = mod.load_json(ROOT, cls.data["sources"]["tracker"])
        cls.ruby = {name: mod.source(ROOT, cls.data["sources"][name])
                    for name in mod.RUNTIME_SIGNATURES}

    def item(self, name="HM_KANTO", kind="HM", qty=1):
        return {"id": "FIXTURE_" + name, "kind": kind, "qty": qty}

    def mon(self, name="NORMAL", flags=None, *, fainted=False, egg=False):
        return {"id": "FIXTURE_" + name, "flags": list(flags or []),
                "base_flags": [], "form": 0, "egg": egg, "fainted": fainted}

    def snapshot(self, current="KANTO", *, with_special=True):
        party = [self.mon("NORMAL")]
        if with_special:
            party.append(self.mon("SPECIAL", ["Paradox"]))
        return {
            "scope": mod.SIMULATION["scope"], "version": 1,
            "current": current, "npc_event_context": True,
            "at_initial_town": True, "campaign_active": True, "arena_mode": False,
            "safe_context": {key: key in mod.SAFE_TRUE for key in mod.SAFE_FLAGS},
            "install_proofs": {key: True for key in mod.ROUTABLE},
            "arrival_proofs": {key: True for key in mod.ROUTABLE},
            "position": mod.ORIGINS.get(current, "FIXTURE_UNKNOWN_ROUTE"),
            "decades_return": None,
            "bag_state": {
                "scope": mod.items.SCOPE, "current": current,
                "bag": [self.item("HM_KANTO"), self.item("GLOBAL_TM", "TM"),
                        self.item("KANTO_KEY", "KEY_ITEM")],
                "pc": [self.item("KANTO_PC_KEY", "KEY_ITEM")],
                "registered": ["FIXTURE_HM_KANTO", "FIXTURE_GLOBAL_TM"],
                "vault": {"HOENN": {
                    "items": [self.item("HOENN_HM")],
                    "registered": ["FIXTURE_HOENN_HM"],
                    "pc_items": [self.item("HOENN_PC_KEY", "KEY_ITEM")],
                }},
                "bag_capacity": 16, "pc_capacity": 16, "badges": [],
            },
            "party_state": {
                "scope": mod.specials.SIMULATION["scope"],
                "version": 1, "current": current,
                "achievements": {},
                "native_decades_badge_count": 0, "hisui_complete": False,
                "party": party, "free_box_slots": ["FIXTURE_BOX_A"],
            },
            "pc_boxes": {},
            "travel_history": [], "mechanics_by_region": {},
            "current_mechanics": {"FIXTURE_MEGA": True},
        }

    def check(self, state=None, destination="HOENN", **kwargs):
        return mod.preflight(self.data, self.reg, self.it, self.sp,
                             self.snapshot() if state is None else state,
                             destination, **kwargs)

    def travel(self, state=None, destination="HOENN", **kwargs):
        return mod.simulate(self.data, self.reg, self.it, self.sp,
                            self.snapshot() if state is None else state,
                            destination, **kwargs)

    def expected(self, status, state=None, destination="HOENN", **kwargs):
        self.assertEqual(self.check(state, destination, **kwargs)["status"], status)

    def invalid_fixture(self, change):
        s = self.snapshot()
        change(s)
        with self.assertRaises(ValueError):
            mod.validate_fixture(s, self.reg)

    def invalid_catalog(self, change):
        d = copy.deepcopy(self.data)
        change(d)
        with self.assertRaises(ValueError):
            mod.validate_catalog(d, self.reg, self.it, self.sp,
                                 self.tracker, self.ruby)

    def test_001_own_phase(self):
        self.assertEqual(self.report["phase"], "G05.3")
    def test_002_unova_not_installed(self):
        self.assertFalse(self.data["native_npc_installed"])
    def test_003_unova_planned(self):
        self.assertEqual(self.reg["regions"]["UNOVA"]["status"], "planned")
    def test_004_technical_bar_unchanged(self):
        self.assertEqual(self.tracker["native_technical_bar"]["completed"], 0)
    def test_005_playable_bar_unchanged(self):
        self.assertEqual(self.tracker["native_playable_bar"]["completed"], 0)
    def test_006_no_game_writes(self):
        self.assertFalse(self.data["native_saves_modified"])
        self.assertFalse(self.data["can_install"])
    def test_007_no_native_mapids(self):
        self.assertTrue(all(value is None for value in self.data["native_evidence"].values()))
    def test_008_existing_route_allowlist(self):
        self.assertEqual(tuple(self.data["routable_runtime_regions"]), mod.ROUTABLE)
    def test_009_seven_planned_only_regions(self):
        self.assertEqual(len(self.data["planned_only_regions"]), 7)
    def test_010_unova_in_planned_only(self):
        self.assertIn("UNOVA", self.data["planned_only_regions"])
    def test_011_no_mandatory_league_victory(self):
        self.assertTrue(self.data["policy"]["no_hall_of_fame_gate"])
        self.assertTrue(self.data["policy"]["league_victory_not_required_by_current_runtime"])
    def test_012_hisui_not_native_destination(self):
        self.assertIn("HISUI", self.data["planned_only_regions"])
    def test_013_explicit_main_campaign_required(self):
        self.assertTrue(self.data["policy"]["campaign_not_arena"])
    def test_014_no_native_save_adapter(self):
        self.assertTrue(self.data["simulation"]["no_native_save_adapter"])
    def test_015_ruby_rollback_signatures_audited(self):
        self.assertIn('$player.party.replace(old_party)', self.ruby["runtime_travel"])
    def test_016_ruby_NPC_event_context_audited(self):
        self.assertIn("return false unless @npc_event_context", self.ruby["runtime_travel"])
    def test_017_source_documents_planned_only(self):
        self.assertEqual(self.report["native_unova_npc_installed"], False)
    def test_018_preflight_allowed_synthetic_installed_hoenn(self):
        self.expected("SIMULATED_PREFLIGHT_NOT_NATIVE")
    def test_019_preflight_does_not_transfer(self):
        r = self.check()
        self.assertFalse(r["native_transfer"])
        self.assertFalse(r["can_install"])
    def test_020_preflight_safe_littleroot_fixture_label(self):
        self.assertEqual(self.check()["point"], "FIXTURE_HOENN_LITTLEROOT")
    def test_021_absent_npc_context(self):
        s = self.snapshot(); s["npc_event_context"] = False
        self.expected("NPC_EVENT_REQUIRED", s)
    def test_022_absent_actual_npc_interaction(self):
        self.expected("NPC_EVENT_REQUIRED", npc_from_event=False)
    def test_023_quiet_never_bypasses_npc(self):
        self.expected("NPC_EVENT_REQUIRED", npc_from_event=False, quiet=True)
    def test_024_quiet_cannot_bypass_destination(self):
        self.expected("DESTINATION_NOT_INSTALLED_OR_SUPPORTED",
                      destination="UNOVA", quiet=True)
    def test_025_not_in_initial_town(self):
        s = self.snapshot(); s["at_initial_town"] = False
        self.expected("INITIAL_TOWN_REQUIRED", s)
    def test_026_route_location_blocked_even_if_town_flag_true(self):
        s = self.snapshot(); s["position"] = "FIXTURE_ROUTE_01"
        self.expected("INITIAL_TOWN_REQUIRED", s)
    def test_027_arena_mode_blocked(self):
        s = self.snapshot(); s["arena_mode"] = True
        self.expected("MAIN_CAMPAIGN_REQUIRED", s)
    def test_028_inactive_campaign_blocked(self):
        s = self.snapshot(); s["campaign_active"] = False
        self.expected("MAIN_CAMPAIGN_REQUIRED", s)
    def test_029_battle_context_blocked(self):
        s = self.snapshot(); s["safe_context"]["in_battle"] = True
        self.expected("UNSAFE_SCENE_BLOCKED", s)
    def test_030_player_transfer_in_progress_blocked(self):
        s = self.snapshot(); s["safe_context"]["player_transferring"] = True
        self.expected("UNSAFE_SCENE_BLOCKED", s)
    def test_031_message_window_blocked(self):
        s = self.snapshot(); s["safe_context"]["message_window_showing"] = True
        self.expected("UNSAFE_SCENE_BLOCKED", s)
    def test_032_transition_processing_blocked(self):
        s = self.snapshot(); s["safe_context"]["transition_processing"] = True
        self.expected("UNSAFE_SCENE_BLOCKED", s)
    def test_033_interpreter_running_blocked_without_safe_NPC(self):
        s = self.snapshot(); s["safe_context"]["interpreter_running"] = True
        self.expected("UNSAFE_SCENE_BLOCKED", s)
    def test_034_missing_scene_blocked(self):
        s = self.snapshot(); s["safe_context"]["scene_present"] = False
        self.expected("UNSAFE_SCENE_BLOCKED", s)
    def test_035_scene_without_transfer_support_blocked(self):
        s = self.snapshot(); s["safe_context"]["scene_can_transfer"] = False
        self.expected("UNSAFE_SCENE_BLOCKED", s)
    def test_036_source_install_not_proven(self):
        s = self.snapshot(); s["install_proofs"]["KANTO"] = False
        self.expected("SOURCE_NOT_INSTALLED_OR_SUPPORTED", s)
    def test_037_destination_install_not_proven(self):
        s = self.snapshot(); s["install_proofs"]["HOENN"] = False
        self.expected("DESTINATION_INSTALL_OR_POINT_UNVERIFIED", s)
    def test_038_arrival_point_not_proven(self):
        s = self.snapshot(); s["arrival_proofs"]["HOENN"] = False
        self.expected("DESTINATION_INSTALL_OR_POINT_UNVERIFIED", s)
    def test_039_unova_not_available_even_if_circuit(self):
        self.expected("DESTINATION_NOT_INSTALLED_OR_SUPPORTED", destination="UNOVA")
    def test_040_sinnoh_not_native_destination(self):
        self.expected("DESTINATION_NOT_INSTALLED_OR_SUPPORTED", destination="SINNOH")
    def test_041_hisui_not_native_destination(self):
        self.expected("DESTINATION_NOT_INSTALLED_OR_SUPPORTED", destination="HISUI")
    def test_042_johto_fixture_needs_proof(self):
        s = self.snapshot(); s["install_proofs"]["JOHTO"] = False
        self.expected("DESTINATION_INSTALL_OR_POINT_UNVERIFIED", s, "JOHTO")
    def test_043_johto_fixture_safe_point(self):
        s = self.snapshot()
        self.assertEqual(self.check(s, "JOHTO")["point"], "FIXTURE_JOHTO_NEW_BARK")
    def test_044_self_destination_refused(self):
        self.expected("SAME_REGION_NO_TRAVEL", destination="KANTO")
    def test_045_native_badge_total_not_required_to_travel(self):
        s = self.snapshot(); s["party_state"]["native_decades_badge_count"] = 0
        self.expected("SIMULATED_PREFLIGHT_NOT_NATIVE", s)
    def test_046_no_League_field_in_travel_fixture(self):
        self.assertNotIn("league", self.snapshot())
    def test_047_box_full_blocks_special_deposit(self):
        s = self.snapshot(); s["party_state"]["free_box_slots"] = []
        self.expected("BOX_CAPACITY_BLOCKED", s)
    def test_048_only_special_Pokemon_blocks_travel(self):
        s = self.snapshot(); s["party_state"]["party"] = [self.mon("ONLY", ["Paradox"])]
        self.expected("NO_USABLE_PARTY_BLOCKED", s)
    def test_049_egg_survivor_not_usable(self):
        s = self.snapshot(); s["party_state"]["party"] = [
            self.mon("EGG", egg=True), self.mon("SPECIAL", ["Legendary"])]
        self.expected("NO_USABLE_PARTY_BLOCKED", s)
    def test_050_fainted_survivor_not_usable(self):
        s = self.snapshot(); s["party_state"]["party"] = [
            self.mon("FAINTED", fainted=True), self.mon("SPECIAL", ["Mythical"])]
        self.expected("NO_USABLE_PARTY_BLOCKED", s)
    def test_051_insufficient_Bag_capacity_blocks(self):
        s = self.snapshot(); s["bag_state"]["bag_capacity"] = 3
        s["bag_state"]["vault"]["HOENN"]["items"].extend([
            self.item("MORE_HOENN_KEY", "KEY_ITEM"),
            self.item("OTHER_HOENN_HM", "HM"),
        ])
        self.expected("BAG_OR_ITEM_PC_PREVIEW_BLOCKED", s)
    def test_052_insufficient_item_PC_capacity_blocks(self):
        s = self.snapshot(); s["bag_state"]["pc_capacity"] = 1
        s["bag_state"]["vault"]["HOENN"]["pc_items"].append(
            self.item("SECOND_PC_HOENN", "KEY_ITEM"))
        self.expected("BAG_OR_ITEM_PC_PREVIEW_BLOCKED", s)
    def test_053_unova_source_cannot_depart(self):
        s = self.snapshot(current="UNOVA")
        self.expected("SOURCE_NOT_INSTALLED_OR_SUPPORTED", s)
    def test_054_unknown_destination_is_rejected(self):
        with self.assertRaises(ValueError): self.check(destination="FAKEREGION")
    def test_055_same_region_kanto_even_if_quiet(self):
        self.expected("SAME_REGION_NO_TRAVEL", destination="KANTO", quiet=True)
    def test_056_successful_hoenn_fixture_arrival(self):
        self.assertEqual(self.travel()["status"], "SIMULATED_SUCCESS_NOT_NATIVE_TRAVEL")
    def test_057_success_sets_current_region(self):
        self.assertEqual(self.travel()["fixture"]["current"], "HOENN")
    def test_058_success_sets_new_position(self):
        self.assertEqual(self.travel()["fixture"]["position"], "FIXTURE_HOENN_LITTLEROOT")
    def test_059_success_records_one_history(self):
        self.assertEqual(len(self.travel()["fixture"]["travel_history"]), 1)
    def test_060_success_history_uses_fixture_locations(self):
        row = self.travel()["fixture"]["travel_history"][0]
        self.assertEqual(row["source"], "KANTO")
        self.assertEqual(row["destination"], "HOENN")
        self.assertEqual(row["from_point"], mod.ORIGINS["KANTO"])
    def test_061_success_boxes_special(self):
        self.assertEqual(self.travel()["fixture"]["pc_boxes"]["FIXTURE_BOX_A"], "FIXTURE_SPECIAL")
    def test_062_success_removes_special_from_party(self):
        self.assertEqual([m["id"] for m in self.travel()["fixture"]["party_state"]["party"]],
                         ["FIXTURE_NORMAL"])
    def test_063_success_reserves_taken_box(self):
        self.assertEqual(self.travel()["fixture"]["party_state"]["free_box_slots"], [])
    def test_064_success_restores_destination_HM(self):
        self.assertIn("FIXTURE_HOENN_HM",
                      [m["id"] for m in self.travel()["fixture"]["bag_state"]["bag"]])
    def test_065_success_saves_source_HM_in_vault(self):
        self.assertIn("FIXTURE_HM_KANTO",
                      [m["id"] for m in self.travel()["fixture"]["bag_state"]["vault"]["KANTO"]["items"]])
    def test_066_success_preserves_global_TM(self):
        self.assertIn("FIXTURE_GLOBAL_TM",
                      [m["id"] for m in self.travel()["fixture"]["bag_state"]["bag"]])
    def test_067_success_restores_Hoenn_PC_key_item(self):
        self.assertIn("FIXTURE_HOENN_PC_KEY",
                      [m["id"] for m in self.travel()["fixture"]["bag_state"]["pc"]])
    def test_068_success_save_state_and_party_state_consistent(self):
        s = self.travel()["fixture"]
        self.assertEqual(s["party_state"]["current"], s["bag_state"]["current"])
    def test_069_success_preserves_origin_input_immutably(self):
        state = self.snapshot()
        before = copy.deepcopy(state)
        self.travel(state)
        self.assertEqual(state, before)
    def test_070_success_no_native_transfer(self):
        result = self.travel()
        self.assertFalse(result["native_transfer"])
        self.assertFalse(result["can_install"])
    def test_071_return_to_kanto_fixture(self):
        first = self.travel()["fixture"]
        second = self.travel(first, "KANTO")
        self.assertEqual(second["status"], "SIMULATED_SUCCESS_NOT_NATIVE_TRAVEL")
        self.assertEqual(second["fixture"]["current"], "KANTO")
    def test_072_return_recovers_Kanto_HM(self):
        second = self.travel(self.travel()["fixture"], "KANTO")
        self.assertIn("FIXTURE_HM_KANTO",
                      [m["id"] for m in second["fixture"]["bag_state"]["bag"]])
    def test_073_return_does_not_automatically_withdraw_special(self):
        second = self.travel(self.travel()["fixture"], "KANTO")
        self.assertNotIn("FIXTURE_SPECIAL",
                         [m["id"] for m in second["fixture"]["party_state"]["party"]])
        self.assertIn("FIXTURE_SPECIAL", second["fixture"]["pc_boxes"].values())
    def test_074_return_restores_Kanto_PC_key_item(self):
        second = self.travel(self.travel()["fixture"], "KANTO")
        self.assertIn("FIXTURE_KANTO_PC_KEY",
                      [m["id"] for m in second["fixture"]["bag_state"]["pc"]])
    def test_075_return_appends_history_not_overwrites(self):
        second = self.travel(self.travel()["fixture"], "KANTO")
        self.assertEqual(len(second["fixture"]["travel_history"]), 2)
    def test_076_hoenn_source_with_proof_can_return(self):
        self.assertEqual(self.travel(self.travel()["fixture"], "KANTO")["status"],
                         "SIMULATED_SUCCESS_NOT_NATIVE_TRAVEL")
    def test_077_empty_Party_with_no_special_blocks(self):
        s = self.snapshot(with_special=False)
        s["party_state"]["party"] = []
        self.expected("NO_USABLE_PARTY_BLOCKED", s)
    def test_078_success_mechanics_saved_by_source(self):
        s = self.travel()["fixture"]
        self.assertEqual(s["mechanics_by_region"]["KANTO"], {"FIXTURE_MEGA": True})
    def test_079_success_not_give_unknown_mechanics(self):
        self.assertEqual(self.travel()["fixture"]["current_mechanics"], {})
    def test_080_stored_decades_return_from_town_only(self):
        s = self.snapshot("DECADES", with_special=False)
        result = self.travel(s, "KANTO")
        self.assertEqual(result["status"], "SIMULATED_SUCCESS_NOT_NATIVE_TRAVEL")
        self.assertEqual(result["fixture"]["decades_return"], mod.ORIGINS["DECADES"])
    def test_081_return_to_decades_from_stored_town(self):
        s = self.snapshot("DECADES", with_special=False)
        out = self.travel(s, "KANTO")["fixture"]
        back = self.travel(out, "DECADES")
        self.assertEqual(back["position"], mod.ORIGINS["DECADES"])
    def test_082_decades_return_without_stored_point_safe_fallback(self):
        s = self.snapshot("KANTO", with_special=False)
        back = self.travel(s, "DECADES")
        self.assertEqual(back["position"], mod.DECADES_SAFE)
    def test_083_decades_special_without_native_badges_blocked(self):
        self.expected("DECADES_NATIVE_SPECIAL_GATE_UNKNOWN", destination="DECADES")
    def test_084_decades_intro_never_accepted(self):
        self.invalid_fixture(lambda s: s.update(decades_return="FIXTURE_DECADES_INTRO"))
    def test_085_invalid_return_point_refused(self):
        self.invalid_fixture(lambda s: s.update(decades_return="FIXTURE_KANTO_PALLET"))
    def test_086_no_native_mapid_accepted_as_position(self):
        self.invalid_fixture(lambda s: s.update(position=77))
    def test_087_unknown_version_rejected(self):
        self.invalid_fixture(lambda s: s.update(version=2))
    def test_088_native_save_scope_rejected(self):
        self.invalid_fixture(lambda s: s.update(scope="NATIVE_GAME_SAVE"))
    def test_089_boolean_source_proof_required(self):
        self.invalid_fixture(lambda s: s["install_proofs"].update(KANTO=1))
    def test_090_extra_installer_proof_rejected(self):
        self.invalid_fixture(lambda s: s["install_proofs"].update(UNOVA=True))
    def test_091_unknown_scene_flag_rejected(self):
        self.invalid_fixture(lambda s: s["safe_context"].update(debug_force=True))
    def test_092_non_boolean_scene_flag_rejected(self):
        self.invalid_fixture(lambda s: s["safe_context"].update(in_battle=1))
    def test_093_tampered_PC_contents_rejected(self):
        self.invalid_fixture(lambda s: s["bag_state"]["bag"][0].update(qty=0))
    def test_094_bad_party_flags_rejected(self):
        self.invalid_fixture(lambda s: s["party_state"]["party"][0].update(flags=["no_valid"]))
    def test_095_active_region_mismatch_rejected(self):
        self.invalid_fixture(lambda s: s["party_state"].update(current="HOENN"))
    def test_096_duplicate_box_occupancy_rejected(self):
        self.invalid_fixture(lambda s: s["pc_boxes"].update(FIXTURE_BOX_A="FIXTURE_NORMAL"))
    def test_097_reserved_slot_already_occupied_rejected(self):
        self.invalid_fixture(lambda s: s["pc_boxes"].update(FIXTURE_BOX_A="FIXTURE_BOXED"))
    def test_098_invalid_mechanics_key_rejected(self):
        self.invalid_fixture(lambda s: s["current_mechanics"].update(mega=True))
    def test_099_rollback_after_party(self):
        s = self.snapshot()
        result = self.travel(s, fail_at="after_party")
        self.assertEqual(result["status"], "SIMULATED_TRANSFER_FAILED_ROLLED_BACK")
        self.assertEqual(result["fixture"], s)
    def test_100_rollback_after_region(self):
        s = self.snapshot()
        result = self.travel(s, fail_at="after_region")
        self.assertEqual(result["fixture"], s)
    def test_101_rollback_after_bag(self):
        s = self.snapshot()
        result = self.travel(s, fail_at="after_bag")
        self.assertEqual(result["fixture"], s)
    def test_102_rollback_after_pc(self):
        s = self.snapshot()
        result = self.travel(s, fail_at="after_pc")
        self.assertEqual(result["fixture"], s)
    def test_103_rollback_after_position(self):
        s = self.snapshot()
        result = self.travel(s, fail_at="after_position")
        self.assertEqual(result["fixture"], s)
    def test_104_failure_does_not_modify_snapshot(self):
        s = self.snapshot()
        original = copy.deepcopy(s)
        self.travel(s, fail_at="after_position")
        self.assertEqual(s, original)
    def test_105_failed_transfer_returns_original_position(self):
        s = self.snapshot()
        result = self.travel(s, fail_at="after_position")
        self.assertEqual(result["restored_position"], mod.ORIGINS["KANTO"])
    def test_106_failed_transfer_does_not_claim_native_mutation(self):
        result = self.travel(fail_at="after_pc")
        self.assertFalse(result["native_save_modified"])
        self.assertFalse(result["native_transfer"])
    def test_107_failed_transfer_preserves_Bag_and_PC(self):
        s = self.snapshot()
        result = self.travel(s, fail_at="after_pc")
        self.assertEqual(result["fixture"]["bag_state"], s["bag_state"])
    def test_108_failed_transfer_preserves_party_and_boxes(self):
        s = self.snapshot()
        result = self.travel(s, fail_at="after_party")
        self.assertEqual(result["fixture"]["pc_boxes"], s["pc_boxes"])
        self.assertEqual(result["fixture"]["party_state"], s["party_state"])
    def test_109_failed_transfer_preserves_history_and_mechanics(self):
        s = self.snapshot()
        result = self.travel(s, fail_at="after_region")
        self.assertEqual(result["fixture"]["travel_history"], s["travel_history"])
        self.assertEqual(result["fixture"]["mechanics_by_region"], s["mechanics_by_region"])
    def test_110_invalid_failure_injection_refused(self):
        with self.assertRaises(ValueError): self.travel(fail_at="delete_saves")
    def test_111_synthetic_NPC_quiet_still_valid_not_native(self):
        self.assertEqual(self.travel(quiet=True)["status"],
                         "SIMULATED_SUCCESS_NOT_NATIVE_TRAVEL")
        self.assertFalse(self.travel(quiet=True)["native_transfer"])
    def test_112_bad_catalog_claims_unova_installed(self):
        self.invalid_catalog(lambda d: d.update(native_npc_installed=True))
    def test_113_bad_catalog_forges_unova_point(self):
        self.invalid_catalog(lambda d: d["native_evidence"].update(unova_approved_arrival_point=518))
    def test_114_bad_catalog_forges_installer_proof(self):
        self.invalid_catalog(lambda d: d["native_evidence"].update(unova_native_installer_proof="fake"))
    def test_115_bad_catalog_changes_no_league_rule(self):
        self.invalid_catalog(lambda d: d["policy"].update(no_hall_of_fame_gate=False))
    def test_116_bad_catalog_adds_unova_to_allowlist(self):
        self.invalid_catalog(lambda d: d["routable_runtime_regions"].append("UNOVA"))
    def test_117_bad_catalog_removes_safe_fallback(self):
        self.invalid_catalog(lambda d: d.update(decades_safe_fallback=None))
    def test_118_bad_catalog_claims_game_exe_verified(self):
        self.invalid_catalog(lambda d: d.update(game_exe_tested=True))
    def test_119_bad_catalog_injects_native_install(self):
        self.invalid_catalog(lambda d: d.update(can_install=True))
    def test_120_bad_catalog_extra_field_refused(self):
        self.invalid_catalog(lambda d: d.update(native_travel_complete=True))
    def test_121_runtime_NPC_guard_drift_refused(self):
        rb = copy.deepcopy(self.ruby)
        rb["runtime_travel"] = rb["runtime_travel"].replace(
            "return false unless @npc_event_context", "return true")
        with self.assertRaises(ValueError):
            mod.validate_catalog(self.data, self.reg, self.it, self.sp,
                                 self.tracker, rb)
    def test_122_runtime_rollback_drift_refused(self):
        rb = copy.deepcopy(self.ruby)
        rb["runtime_travel"] = rb["runtime_travel"].replace(
            '$player.party.replace(old_party)', "nil")
        with self.assertRaises(ValueError):
            mod.validate_catalog(self.data, self.reg, self.it, self.sp,
                                 self.tracker, rb)
    def test_123_demo_denies_native_unova(self):
        self.assertEqual(mod.demo(self.data, self.reg, self.it, self.sp)
                         ["unova_native_entry"], "DESTINATION_NOT_INSTALLED_OR_SUPPORTED")
    def test_124_demo_restores_kanto_HM(self):
        self.assertTrue(mod.demo(self.data, self.reg, self.it, self.sp)["kanto_hm_restored"])
    def test_125_demo_rolls_back(self):
        self.assertTrue(mod.demo(self.data, self.reg, self.it, self.sp)["rollback_preserved"])
    def test_126_cli_check(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/regions/audit_unova_g05_travel.py"), "--check"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertFalse(json.loads(result.stdout)["native_unova_npc_installed"])
    def test_127_cli_demo(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/regions/audit_unova_g05_travel.py"), "--simulate-demo"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertTrue(json.loads(result.stdout)["kanto_hm_restored"])


if __name__ == "__main__":
    unittest.main()
