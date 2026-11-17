"""Unova G05.2 — additive regional crystals and special-Pokemon gates, offline only."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_g05_badges_specials as mod

class UnovaG052Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data,cls.registry,cls.report=mod.load_project()
        cls.gym=mod.load_json(ROOT,cls.data["sources"]["gym_contract"])
        cls.items=mod.load_json(ROOT,cls.data["sources"]["regional_items"])
        cls.tracker=mod.load_json(ROOT,cls.data["sources"]["tracker"])
        cls.regions_rb=mod.read_source(ROOT,cls.data["sources"]["regions_runtime"])
        cls.travel_rb=mod.read_source(ROOT,cls.data["sources"]["travel_runtime"])
        cls.field_rb=mod.read_source(ROOT,cls.data["sources"]["field_runtime"])

    def mon(self,key="COMMON",flags=None,base_flags=None,form=0,egg=False,fainted=False):
        return {"id":"FIXTURE_"+key,"flags":list(flags or []),
                "base_flags":list(base_flags or []),"form":form,
                "egg":egg,"fainted":fainted}
    def state(self,region="UNOVA",unova_count=3,kanto_count=2,native=3,party=None,slots=None):
        return {"scope":mod.SIMULATION["scope"],"version":1,"current":region,
                "achievements":{"UNOVA":list(mod.BADGES[:unova_count]),
                   "KANTO":self.registry["regions"]["KANTO"]["milestones"][:kanto_count]},
                "native_decades_badge_count":native,"hisui_complete":False,
                "party": [self.mon(),self.mon("LEGEND",["Legendary"]),
                          self.mon("PARADOX",["Paradox"])] if party is None else party,
                "free_box_slots":["FIXTURE_BOX_A","FIXTURE_BOX_B"] if slots is None else slots}
    def invalid_state(self,mutator):
        st=self.state();mutator(st)
        with self.assertRaises(ValueError):mod.validate_fixture(st,self.registry)
    def invalid_catalog(self,mutator):
        data=copy.deepcopy(self.data);mutator(data)
        with self.assertRaises(ValueError):
            mod.validate_catalog(data,self.registry,self.gym,self.items,self.tracker,
                  self.regions_rb,self.travel_rb,self.field_rb)
    def preview(self,unova_count=7,region="KANTO",slots=None,party=None):
        st=self.state(region=region,unova_count=unova_count,slots=slots,party=party)
        return mod.preview_transfer(self.data,st,self.registry,"UNOVA")

    def test_001_phase(self):self.assertEqual(self.data["phase"],"G05.2")
    def test_002_campaign(self):self.assertEqual(self.data["campaign"],"WHITE_BW")
    def test_003_planned(self):self.assertEqual(self.registry["regions"]["UNOVA"]["status"],"planned")
    def test_004_eight_unova_badges(self):self.assertEqual(self.report["unova_badges"],8)
    def test_005_badge_order_matches_registry(self):
        self.assertEqual([x["badge"] for x in self.data["badges"]],self.registry["regions"]["UNOVA"]["milestones"])
    def test_006_badge_order_matches_g02(self):
        self.assertEqual([x["badge"] for x in self.data["badges"]],[g["badge"] for g in self.gym["gyms"]])
    def test_007_no_native_badge_indices(self):
        self.assertTrue(all(x["native_badge_index"] is None for x in self.data["badges"]))
    def test_008_no_native_switch_ids(self):
        self.assertTrue(all(x["native_switch_id"] is None for x in self.data["badges"]))
    def test_009_no_reward_items(self):
        self.assertTrue(all(x["native_reward_item_id"] is None for x in self.data["badges"]))
    def test_010_no_verified_gym_events(self):
        self.assertTrue(all(x["native_event_id"] is None and not x["gym_battle_verified"] for x in self.data["badges"]))
    def test_011_no_installed_gym_battles(self):
        self.assertTrue(all(not x["installed"] for x in self.data["badges"]))
    def test_012_no_source_proof_forgery(self):
        self.assertTrue(all(x is None for x in self.data["native_evidence"].values()))
    def test_013_native_saves_untouched(self):self.assertFalse(self.data["native_saves_modified"])
    def test_014_native_game_untouched(self):self.assertFalse(self.data["native_game_modified"])
    def test_015_native_badges_untouched(self):self.assertFalse(self.data["native_badges_modified"])
    def test_016_native_items_not_granted(self):self.assertFalse(self.data["native_items_granted"])
    def test_017_game_exe_not_tested(self):self.assertFalse(self.data["game_exe_tested"])
    def test_018_joiplay_not_tested(self):self.assertFalse(self.data["android_tested"])
    def test_019_unova_cannot_install(self):self.assertFalse(self.data["can_install"])
    def test_020_native_bar_zero(self):
        self.assertEqual(self.tracker["native_technical_bar"]["completed"],0)
    def test_021_playable_bar_zero(self):
        self.assertEqual(self.tracker["native_playable_bar"]["completed"],0)
    def test_022_source_region_methods_present(self):
        self.assertIn("def self.crystal_total(state, native_total)",self.regions_rb)
    def test_023_special_metadata_flags(self):
        self.assertEqual(self.data["special_policy"]["special_flags"],list(mod.SPECIAL))
    def test_024_sinnoh_hm_contract_unchanged(self):
        self.assertEqual(self.items["phase"],"G05.1")
    def test_025_derived_crystals_additive(self):
        self.assertEqual(mod.crystal_total(self.state(),self.registry),3+3+2)
    def test_026_native_zero_valid(self):
        self.assertEqual(mod.crystal_total(self.state(native=0),self.registry),5)
    def test_027_native_count_not_overwritten(self):
        state=self.state(native=7)
        out=mod.award_fixture(state,self.registry,region="UNOVA",badge="BOLT")
        self.assertEqual(out["fixture"]["native_decades_badge_count"],7)
    def test_028_no_hisui_circuit_crystals(self):
        s=self.state();s["hisui_complete"]=True
        self.assertEqual(mod.crystal_total(s,self.registry),8)
    def test_029_unova_badges_counted_once(self):
        s=self.state(unova_count=8)
        self.assertEqual(mod.crystal_total(s,self.registry),3+8+2)
    def test_030_kanto_badges_counted_once(self):
        s=self.state(kanto_count=8)
        self.assertEqual(mod.crystal_total(s,self.registry),3+3+8)
    def test_031_other_region_additive(self):
        s=self.state()
        s["achievements"]["HOENN"]=self.registry["regions"]["HOENN"]["milestones"][:2]
        self.assertEqual(mod.crystal_total(s,self.registry),10)
    def test_032_registry_order_retained_in_local_badges(self):
        s=self.state();s["achievements"]["UNOVA"]=["INSECT","TRIO"]
        self.assertEqual(mod.local_badges(s,self.registry,"UNOVA"),["TRIO","INSECT"])
    def test_033_no_decades_achievements_lookup(self):
        with self.assertRaises(ValueError):mod.local_badges(self.state(),self.registry,"DECADES")
    def test_034_unknown_region_lookup(self):
        with self.assertRaises(ValueError):mod.local_badges(self.state(),self.registry,"FUTURE")
    def test_035_foreign_award_blocked(self):
        with self.assertRaises(ValueError):mod.award_fixture(self.state(),self.registry,region="KANTO",badge="BOULDER")
    def test_036_no_nonexistent_unova_badge(self):
        with self.assertRaises(ValueError):mod.award_fixture(self.state(),self.registry,region="UNOVA",badge="RAINBOW")
    def test_037_no_native_decades_awards(self):
        with self.assertRaises(ValueError):mod.award_fixture(self.state(region="DECADES"),self.registry,region="DECADES",badge="NONE")
    def test_038_correct_4th_unova_award(self):
        s=self.state()
        result=mod.award_fixture(s,self.registry,region="UNOVA",badge="BOLT")
        self.assertEqual(result["status"],"SIMULATED_CLAIM_NO_NATIVE_AWARD")
        self.assertEqual(result["after_crystals"],result["before_crystals"]+1)
    def test_039_replay_same_badge_idempotent(self):
        s=self.state()
        result=mod.award_fixture(s,self.registry,region="UNOVA",badge="TRIO")
        self.assertEqual(result["status"],"ALREADY_RECORDED_SYNTHETIC_NO_OP")
        self.assertEqual(result["after_crystals"],result["before_crystals"])
    def test_040_award_does_not_mutate_input(self):
        s=self.state();before=copy.deepcopy(s)
        mod.award_fixture(s,self.registry,region="UNOVA",badge="BOLT")
        self.assertEqual(s,before)
    def test_041_award_no_native_save(self):
        result=mod.award_fixture(self.state(),self.registry,region="UNOVA",badge="BOLT")
        self.assertFalse(result["native_saves_modified"])
    def test_042_award_no_native_badges(self):
        result=mod.award_fixture(self.state(),self.registry,region="UNOVA",badge="BOLT")
        self.assertFalse(result["native_badges_modified"])
    def test_043_7_unova_locked(self):
        self.assertFalse(mod.allow_specials(self.state(unova_count=7),self.registry,"UNOVA"))
    def test_044_8_unova_unlocked(self):
        self.assertTrue(mod.allow_specials(self.state(unova_count=8),self.registry,"UNOVA"))
    def test_045_0_unova_locked(self):
        self.assertFalse(mod.allow_specials(self.state(unova_count=0),self.registry,"UNOVA"))
    def test_046_global_crystals_do_not_unlock_unova(self):
        s=self.state(unova_count=0,kanto_count=8,native=40)
        self.assertFalse(mod.allow_specials(s,self.registry,"UNOVA"))
    def test_047_foreign_region_badges_do_not_unlock(self):
        s=self.state(unova_count=0,kanto_count=8)
        self.assertFalse(mod.allow_specials(s,self.registry,"UNOVA"))
    def test_048_unova_eight_do_not_unlock_kanto(self):
        s=self.state(unova_count=8,kanto_count=2)
        self.assertFalse(mod.allow_specials(s,self.registry,"KANTO"))
    def test_049_kanto_eight_local_unlock(self):
        s=self.state(kanto_count=8)
        self.assertTrue(mod.allow_specials(s,self.registry,"KANTO"))
    def test_050_hisui_remains_quest_based(self):
        self.assertFalse(mod.allow_specials(self.state(),self.registry,"HISUI"))
    def test_051_hisui_quest_gate_unlock(self):
        s=self.state();s["hisui_complete"]=True
        self.assertTrue(mod.allow_specials(s,self.registry,"HISUI"))
    def test_052_decades_native_unlock_not_assumed(self):
        with self.assertRaises(ValueError):
            mod.allow_specials(self.state(),self.registry,"DECADES")
    def test_053_unknown_destination_unlock_rejected(self):
        with self.assertRaises(ValueError):
            mod.allow_specials(self.state(),self.registry,"UNKNOWN")
    def test_054_legendary_flag_classified(self):
        self.assertTrue(mod.special_pokemon(self.mon(flags=["Legendary"])))
    def test_055_mythical_flag_classified(self):
        self.assertTrue(mod.special_pokemon(self.mon(flags=["Mythical"])))
    def test_056_ultrabeast_flag_classified(self):
        self.assertTrue(mod.special_pokemon(self.mon(flags=["UltraBeast"])))
    def test_057_paradox_flag_classified(self):
        self.assertTrue(mod.special_pokemon(self.mon(flags=["Paradox"])))
    def test_058_common_not_classified(self):
        self.assertFalse(mod.special_pokemon(self.mon(flags=["FIXTURE_NON_SPECIAL"])))
    def test_059_high_bst_without_special_flag_not_classified(self):
        self.assertFalse(mod.special_pokemon(self.mon(flags=["FIXTURE_HIGH_BST"])))
    def test_060_two_special_flags_still_one_pokemon(self):
        self.assertTrue(mod.special_pokemon(self.mon(flags=["Mythical","Legendary"])))
    def test_061_nonzero_form_inherits_base_flag(self):
        self.assertTrue(mod.special_pokemon(self.mon(form=1,base_flags=["Legendary"])))
    def test_062_base_flag_ignored_for_form_zero(self):
        self.assertFalse(mod.special_pokemon(self.mon(form=0,base_flags=["Paradox"])))
    def test_063_special_form_flag_alone_classified(self):
        self.assertTrue(mod.special_pokemon(self.mon(form=2,flags=["Paradox"])))
    def test_064_restricted_below_eight_on_arrival(self):
        result=self.preview()
        self.assertEqual(result["restricted_party_ids"],["FIXTURE_LEGEND","FIXTURE_PARADOX"])
    def test_065_eight_unova_no_restrictions(self):
        result=self.preview(unova_count=8)
        self.assertEqual(result["restricted_party_ids"],[])
    def test_066_seven_unova_preview_status(self):
        self.assertEqual(self.preview()["status"],"SYNTHETIC_PREVIEW_ONLY_NEVER_NATIVE_TRAVEL")
    def test_067_seven_unova_reserve_two_slots(self):
        self.assertEqual(len(self.preview()["reservations"]),2)
    def test_068_reservations_preserve_order(self):
        reservations=self.preview()["reservations"]
        self.assertEqual([row["slot"] for row in reservations],["FIXTURE_BOX_A","FIXTURE_BOX_B"])
    def test_069_normal_pokemon_retained_usable(self):
        self.assertEqual(self.preview()["usable_party_after_preview"],["FIXTURE_COMMON"])
    def test_070_no_usable_survivor_blocks(self):
        party=[self.mon("SPECIAL",["Legendary"])]
        r=self.preview(party=party)
        self.assertEqual(r["status"],"NO_USABLE_PARTY_BLOCKED")
    def test_071_only_egg_survivor_blocks(self):
        party=[self.mon("EGG",egg=True),self.mon("SPECIAL",["Mythical"])]
        r=self.preview(party=party)
        self.assertEqual(r["status"],"NO_USABLE_PARTY_BLOCKED")
    def test_072_only_fainted_survivor_blocks(self):
        party=[self.mon("DOWN",fainted=True),self.mon("SPECIAL",["Paradox"])]
        r=self.preview(party=party)
        self.assertEqual(r["status"],"NO_USABLE_PARTY_BLOCKED")
    def test_073_zero_party_blocks(self):
        self.assertEqual(self.preview(party=[])["status"],"NO_USABLE_PARTY_BLOCKED")
    def test_074_insufficient_slots_blocks(self):
        self.assertEqual(self.preview(slots=["FIXTURE_BOX_A"])["status"],"INSUFFICIENT_BOX_SLOTS_BLOCKED")
    def test_075_no_slots_blocks(self):
        self.assertEqual(self.preview(slots=[])["status"],"INSUFFICIENT_BOX_SLOTS_BLOCKED")
    def test_076_insufficient_slots_no_reservations(self):
        self.assertEqual(self.preview(slots=[])["reservations"],[])
    def test_077_enough_slots_allow_preview(self):
        self.assertEqual(len(self.preview(slots=["FIXTURE_BOX_A","FIXTURE_BOX_B"])["reservations"]),2)
    def test_078_all_local_badges_no_box_reservation(self):
        self.assertEqual(self.preview(unova_count=8,slots=[])["reservations"],[])
    def test_079_preview_never_moves_native_party(self):
        self.assertFalse(self.preview()["native_party_modified"])
    def test_080_preview_never_moves_boxes(self):
        self.assertFalse(self.preview()["native_boxes_modified"])
    def test_081_preview_never_changes_native_badges(self):
        self.assertFalse(self.preview()["native_badges_modified"])
    def test_082_preview_never_claims_installation(self):
        self.assertFalse(self.preview()["can_install"])
    def test_083_preview_does_not_mutate_source(self):
        s=self.state(region="KANTO",unova_count=7)
        before=copy.deepcopy(s)
        mod.preview_transfer(self.data,s,self.registry,"UNOVA")
        self.assertEqual(s,before)
    def test_084_same_region_preview_blocked(self):
        s=self.state(region="UNOVA")
        with self.assertRaises(ValueError):
            mod.preview_transfer(self.data,s,self.registry,"UNOVA")
    def test_085_native_decades_preview_refused(self):
        with self.assertRaises(ValueError):
            mod.preview_transfer(self.data,self.state(),self.registry,"DECADES")
    def test_086_unknown_preview_destination_blocked(self):
        with self.assertRaises(ValueError):
            mod.preview_transfer(self.data,self.state(),self.registry,"UNKNOWN")
    def test_087_real_save_scope_rejected(self):
        self.invalid_state(lambda s:s.update(scope="NATIVE_SAVE"))
    def test_088_version_migration_rejected(self):
        self.invalid_state(lambda s:s.update(version=2))
    def test_089_duplicate_unova_badge_ledger_rejected(self):
        self.invalid_state(lambda s:s["achievements"]["UNOVA"].append("TRIO"))
    def test_090_foreign_unova_badge_ledger_rejected(self):
        self.invalid_state(lambda s:s["achievements"]["UNOVA"].append("BOULDER"))
    def test_091_forged_decades_achievement_rejected(self):
        self.invalid_state(lambda s:s["achievements"].update(DECADES=["NATIVE"]))
    def test_092_unknown_region_achievement_rejected(self):
        self.invalid_state(lambda s:s["achievements"].update(FUTURE=["FAKE"]))
    def test_093_native_count_boolean_rejected(self):
        self.invalid_state(lambda s:s.update(native_decades_badge_count=True))
    def test_094_negative_native_count_rejected(self):
        self.invalid_state(lambda s:s.update(native_decades_badge_count=-1))
    def test_095_hisui_flag_integer_rejected(self):
        self.invalid_state(lambda s:s.update(hisui_complete=1))
    def test_096_pokemon_real_identifier_rejected(self):
        self.invalid_state(lambda s:s["party"][0].update(id="MEWTWO"))
    def test_097_duplicate_party_identity_rejected(self):
        self.invalid_state(lambda s:s["party"][0].update(id="FIXTURE_LEGEND"))
    def test_098_unknown_special_flag_rejected(self):
        self.invalid_state(lambda s:s["party"][0].update(flags=["Ultra Beast"]))
    def test_099_duplicate_special_flag_rejected(self):
        self.invalid_state(lambda s:s["party"][1].update(flags=["Legendary","Legendary"]))
    def test_100_invalid_form_rejected(self):
        self.invalid_state(lambda s:s["party"][0].update(form=-1))
    def test_101_non_bool_egg_rejected(self):
        self.invalid_state(lambda s:s["party"][0].update(egg=0))
    def test_102_more_than_six_party_rejected(self):
        self.invalid_state(lambda s:s["party"].extend([
            self.mon("FOUR"),self.mon("FIVE"),self.mon("SIX"),self.mon("SEVEN")]))
    def test_103_duplicate_box_slot_rejected(self):
        self.invalid_state(lambda s:s["free_box_slots"].append("FIXTURE_BOX_A"))
    def test_104_real_box_slot_rejected(self):
        self.invalid_state(lambda s:s["free_box_slots"].append("Box000"))
    def test_105_catalog_native_badge_id_forgery_rejected(self):
        self.invalid_catalog(lambda d:d["badges"][0].update(native_badge_index=1))
    def test_106_catalog_badge_order_forgery_rejected(self):
        self.invalid_catalog(lambda d:d["badges"].reverse())
    def test_107_catalog_native_event_forgery_rejected(self):
        self.invalid_catalog(lambda d:d["badges"][0].update(native_event_id=42))
    def test_108_catalog_native_provenance_forgery_rejected(self):
        self.invalid_catalog(lambda d:d["native_evidence"].update(source_unova_native_provenance_sha256="fake"))
    def test_109_catalog_game_exe_qa_forgery_rejected(self):
        self.invalid_catalog(lambda d:d.update(game_exe_tested=True))
    def test_110_catalog_can_install_forgery_rejected(self):
        self.invalid_catalog(lambda d:d.update(can_install=True))
    def test_111_catalog_global_crystal_formula_drift_rejected(self):
        self.invalid_catalog(lambda d:d["progress_policy"].update(total_formula="ALL_REGION_BADGES_PLUS_EVERYTHING"))
    def test_112_catalog_special_threshold_drift_rejected(self):
        self.invalid_catalog(lambda d:d["special_policy"].update(unova_local_milestones_required=7))
    def test_113_catalog_unknown_field_rejected(self):
        self.invalid_catalog(lambda d:d.update(playable=True))
    def test_114_gym_contract_drift_rejected(self):
        g=copy.deepcopy(self.gym);g["gyms"][0]["badge"]="BOULDER"
        with self.assertRaises(ValueError):
            mod.validate_catalog(self.data,self.registry,g,self.items,self.tracker,
                                 self.regions_rb,self.travel_rb,self.field_rb)
    def test_115_runtime_special_flag_drift_rejected(self):
        with self.assertRaises(ValueError):
            mod.validate_runtime(self.regions_rb,
                self.travel_rb.replace("SPECIAL_FLAGS = %w[Legendary Mythical UltraBeast Paradox].freeze","SPECIAL_FLAGS = []"),
                self.field_rb)
    def test_116_runtime_crystal_formula_drift_rejected(self):
        with self.assertRaises(ValueError):
            mod.validate_runtime(self.regions_rb.replace(
                'native_total + (circuit - ["DECADES"]).sum',
                'native_total + circuit.sum'),self.travel_rb,self.field_rb)
    def test_117_demo_proves_local_not_global_unlock(self):
        d=mod.demo(self.data,self.registry)
        self.assertEqual(d["before"]["unova_badges"],7)
        self.assertEqual(d["after"]["unova_badges"],8)
        self.assertTrue(d["after"]["specials_unlocked_in_unova"])
        self.assertEqual(len(d["after"]["restricted_when_entering_kanto"]),2)
    def test_118_demo_never_changes_native_save(self):
        d=mod.demo(self.data,self.registry)
        self.assertFalse(d["native_save_modified"])
        self.assertFalse(d["can_install"])
    def test_119_cli_check(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g05_badges_specials.py"),
             "--check"],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(json.loads(p.stdout)["unova_badges"],8)
    def test_120_cli_demo(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g05_badges_specials.py"),
             "--simulate-demo"],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertTrue(json.loads(p.stdout)["fixture_only"])

if __name__=="__main__":
    unittest.main()
