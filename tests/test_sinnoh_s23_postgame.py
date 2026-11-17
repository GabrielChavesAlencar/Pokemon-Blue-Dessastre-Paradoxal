"""S23: reject fabricated Battle Zone, legendary events and native rematches."""
from __future__ import annotations
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from audit_sinnoh_s23_postgame import (
    CONTRACT,COVERAGE,TEAMS,STORY,REGISTRY,RUNTIME,STORY_RUBY,
    REGIONS,CAMPAIGN,BLUE_STORY,FIXTURE,audit,EVENT_IDS,ELITE,
)

class SinnohS23PostgameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original={
            "contract":json.loads(CONTRACT.read_text("utf-8")),
            "coverage":json.loads(COVERAGE.read_text("utf-8")),
            "teams":json.loads(TEAMS.read_text("utf-8")),
            "story":json.loads(STORY.read_text("utf-8")),
            "registry":json.loads(REGISTRY.read_text("utf-8")),
            "ruby":RUNTIME.read_text("utf-8"),
            "story_ruby":STORY_RUBY.read_text("utf-8"),
            "regions":REGIONS.read_text("utf-8"),
            "campaign":CAMPAIGN.read_text("utf-8"),
            "blue_story":BLUE_STORY.read_text("utf-8"),
            "fixture":FIXTURE.read_text("utf-8"),
        }

    def check(self,**mods):
        docs=copy.deepcopy(self.original)
        docs.update(mods)
        return audit(**docs)

    def test_01_six_events_fourteen_areas_five_historical_teams_only(self):
        report=self.check()
        self.assertEqual(report["reference_areas"],14)
        self.assertEqual(report["optional_events"],6)
        self.assertEqual(report["historical_elite_champion_reference_rematches"],5)
        self.assertEqual(report["verified_native_rematch_teams"],0)
        self.assertEqual(report["physical_map_ids_verified"],0)
        self.assertEqual(report["native_quests_installed"],0)
        self.assertFalse(report["game_exe_or_joiplay_tested"])
        self.assertFalse(report["gameplay_approved"])
        self.assertEqual([e["id"] for e in self.original["contract"]["events"]],
                         list(EVENT_IDS))

    def test_02_never_forge_native_game_exe_or_joiplay_qa(self):
        for key in self.original["contract"]["verification"]:
            doc=copy.deepcopy(self.original["contract"])
            doc["verification"][key]=True
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,"politica S23"):
                self.check(contract=doc)

    def test_03_no_mapids_pbs_event_items_or_legendary_sources(self):
        for key,data in (
            ("verified_native_sources",["FAKE"]),
            ("installed_postgame_map_ids",[555]),
            ("compiled_rematch_pbs",["CYNTHIA"]),
            ("verified_event_items",["MEMBER_CARD"]),
            ("verified_static_legendary_events",["DARKRAI"]),
        ):
            doc=copy.deepcopy(self.original["contract"])
            doc[key]=data
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,"inventados"):
                self.check(contract=doc)

    def test_04_strongest_requires_global_ten_leagues_and_verified_roster(self):
        for key in (
            "global_world_champion_requires_all_ten_leagues",
            "global_strongest_requires_verified_native_roster",
            "local_historical_rematches_not_blue_full_power",
        ):
            doc=copy.deepcopy(self.original["contract"])
            doc[key]=False
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,"politica S23"):
                self.check(contract=doc)
        doc=copy.deepcopy(self.original["contract"])
        doc["events"][5]["requires_all_ten_leagues"]=False
        with self.assertRaisesRegex(ValueError,"checkpoints"):
            self.check(contract=doc)

    def test_05_optional_legendary_events_cannot_grant_species_or_items(self):
        for key,value in (
            ("no_granted_species",False),("no_rewards_or_items",False),
            ("native_quest_verified",True),("physical_map_id",800),
            ("native_callback_installed",True),
            ("requires_event_item_verification",False),
        ):
            doc=copy.deepcopy(self.original["contract"])
            doc["events"][3][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,"checkpoints"):
                self.check(contract=doc)
        doc=copy.deepcopy(self.original["contract"])
        doc["events"][4]["requires_event_item_verification"]=False
        with self.assertRaisesRegex(ValueError,"checkpoints"):
            self.check(contract=doc)

    def test_06_heatran_requires_battle_zone_and_no_free_arrival(self):
        doc=copy.deepcopy(self.original["contract"])
        doc["events"][1]["requires_previous_event"]=None
        with self.assertRaisesRegex(ValueError,"checkpoints"):
            self.check(contract=doc)
        doc=copy.deepcopy(self.original["contract"])
        doc["events"][0]["reference_area"]="KANTO_PALLET"
        with self.assertRaisesRegex(ValueError,"checkpoints"):
            self.check(contract=doc)

    def test_07_no_repeatable_battle_claim_without_real_npc(self):
        doc=copy.deepcopy(self.original["contract"])
        doc["events"][5]["repeatable_battles_not_falsely_implemented"]=False
        with self.assertRaisesRegex(ValueError,"checkpoints"):
            self.check(contract=doc)
        doc=copy.deepcopy(self.original["contract"])
        doc["restrictions"]["no_repeatable_battle_claim_without_native_handler"]=False
        with self.assertRaisesRegex(ValueError,"politica S23"):
            self.check(contract=doc)

    def test_08_fourteen_reference_areas_not_native_installed(self):
        for name,changes in (
            ("verified",True),
            ("source_map_ids",[150]),
            ("destination_map_ids",[850]),
        ):
            doc=copy.deepcopy(self.original["coverage"])
            phase=next(p for p in doc["phases"] if p["phase"]==10)
            phase["areas"][0][name]=changes
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,"mapa"):
                self.check(coverage=doc)
        doc=copy.deepcopy(self.original["coverage"])
        phase=next(p for p in doc["phases"] if p["phase"]==10)
        phase["areas"].pop()
        with self.assertRaisesRegex(ValueError,"14 areas"):
            self.check(coverage=doc)

    def test_09_six_coverage_events_remain_planned(self):
        doc=copy.deepcopy(self.original["coverage"])
        phase=next(p for p in doc["phases"] if p["phase"]==10)
        phase["events"][0]["verified"]=True
        with self.assertRaisesRegex(ValueError,"seis eventos"):
            self.check(coverage=doc)
        doc=copy.deepcopy(self.original["coverage"])
        phase=next(p for p in doc["phases"] if p["phase"]==10)
        phase["events"].pop()
        with self.assertRaisesRegex(ValueError,"seis eventos"):
            self.check(coverage=doc)

    def test_10_historical_elite_rematch_level_never_runtime_fixed(self):
        doc=copy.deepcopy(self.original["teams"])
        elite=next(t for t in doc["trainers"] if t["id"]=="SINNOH_CYNTHIA")
        elite["historical_rematch"]["levels_are_not_runtime_levels"]=False
        with self.assertRaisesRegex(ValueError,"historica Elite"):
            self.check(teams=doc)
        doc=copy.deepcopy(self.original["contract"])
        doc["original_level_numbers_never_native"]=False
        with self.assertRaisesRegex(ValueError,"politica S23"):
            self.check(contract=doc)

    def test_11_gym_history_must_not_be_made_up(self):
        doc=copy.deepcopy(self.original["teams"])
        roark=next(t for t in doc["trainers"] if t["id"]=="SINNOH_ROARK")
        roark["historical_rematch"]={"source":"UNVERIFIED"}
        with self.assertRaisesRegex(ValueError,"ginasio"):
            self.check(teams=doc)
        doc=copy.deepcopy(self.original["contract"])
        doc["gym_historical_rematch_count"]=8
        with self.assertRaisesRegex(ValueError,"politica S23"):
            self.check(contract=doc)

    def test_12_native_elite_cynthia_full_power_is_not_installed(self):
        for id in ELITE:
            doc=copy.deepcopy(self.original["teams"])
            trainer=next(t for t in doc["trainers"] if t["id"]==id)
            trainer["native_pbs"]["compiled"]=True
            with self.subTest(id=id),self.assertRaisesRegex(ValueError,"Full Power"):
                self.check(teams=doc)
        doc=copy.deepcopy(self.original["teams"])
        trainer=next(t for t in doc["trainers"] if t["id"]=="SINNOH_CYNTHIA")
        trainer["blue_strongest"]["species"]=["GARCHOMP"]
        with self.assertRaisesRegex(ValueError,"Full Power"):
            self.check(teams=doc)

    def test_13_ch14_requires_separate_hall_and_planned_status(self):
        doc=copy.deepcopy(self.original["story"])
        doc["native_hall_of_fame_verified"]=True
        with self.assertRaisesRegex(ValueError,"CH14"):
            self.check(story=doc)
        doc=copy.deepcopy(self.original["story"])
        doc["steps"][-1]["id"]="P10_BATTLE_ZONE_ENTRY"
        with self.assertRaisesRegex(ValueError,"Hall"):
            self.check(story=doc)

    def test_14_ruby_world_champion_and_special_party_gates_mandatory(self):
        for token in (
            "BlueRegions.world_champion?(state)",
            "BlueRegions.profile(state, verified_roster) == :world_champion_rematch",
            "return :special_event_item_not_verified",
            "return :already_recorded if history.include?(event)",
            "VERIFIED_NATIVE_SOURCES = {}.freeze",
            "private_class_method :record_with_sources",
        ):
            with self.subTest(token=token),self.assertRaises(ValueError):
                self.check(ruby=self.original["ruby"].replace(token,""))

    def test_15_shared_engine_ten_leagues_and_normal_master_remain(self):
        for token in (
            '(circuit - state["leagues"]).empty?',
            "local_achievements(state, region, native_badges).length >= 8",
        ):
            with self.subTest(token=token),self.assertRaisesRegex(ValueError,"BlueRegions"):
                self.check(regions=self.original["regions"].replace(token,""))
        doc=self.original["campaign"].replace("master? ? 90 : 70","master? ? 99 : 70")
        with self.assertRaisesRegex(ValueError,"Normal/Master"):
            self.check(campaign=doc)
        doc=self.original["blue_story"].replace("def self.rematches","def self.disabled_rematches")
        with self.assertRaisesRegex(ValueError,"bosses"):
            self.check(blue_story=doc)

    def test_16_required_synthetic_runtime_and_no_fake_battles(self):
        for token in (
            "SINNOH_S23_POSTGAME_QUESTS_HISTORICAL_VS_GLOBAL_REMATCH_IDEMPOTENT_OFFLINE_OK",
            "send(:record_with_sources,",
            "BlueRegions.world_champion?(state)",
            "BlueRegions.allow_specials?(limited, \"SINNOH\")",
        ):
            with self.subTest(token=token),self.assertRaisesRegex(ValueError,"fixture S23"):
                self.check(fixture=self.original["fixture"].replace(token,""))
        doc=copy.deepcopy(self.original["contract"])
        doc["native_playable"]=True
        with self.assertRaisesRegex(ValueError,"campos S23"):
            self.check(contract=doc)

if __name__=="__main__":unittest.main()
