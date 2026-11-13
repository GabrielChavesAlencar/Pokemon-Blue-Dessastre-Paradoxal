"""Phase 14: verified contracts for planned Johto legends, never real map claims."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class JohtoPhase14ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = load("data/regions/johto-phase14.json")
        cls.previous = load("data/regions/johto-phase13.json")
        cls.phase10 = load("data/regions/johto-phase10.json")
        cls.source = load("data/regions/johto-source.json")
        cls.registry = load("site/public/data/regions.json")["regions"]["JOHTO"]
        cls.script = (ROOT / "scripts/regions/JohtoLegendaries.rb").read_text("utf-8")
        cls.regions = (ROOT / "scripts/battle_polish/Regions.rb").read_text("utf-8")

    def test_versions_are_explicit_and_primary_mascots_differ(self):
        v = self.phase["version_selection"]
        self.assertEqual(v["versions"], ["HEARTGOLD", "SOULSILVER", "CRYSTAL"])
        self.assertTrue(v["locked_after_choice"])
        self.assertTrue(v["requires_manual_new_game_configuration"])
        self.assertEqual(v["heartgold"]["primary"], "HOOH")
        self.assertEqual(v["heartgold"]["secondary"], "LUGIA")
        self.assertEqual(v["heartgold"]["primary_items"],
                         ["RAINBOWWING", "CLEARBELL"])
        self.assertEqual(v["soulsilver"]["primary"], "LUGIA")
        self.assertEqual(v["soulsilver"]["secondary"], "HOOH")
        self.assertEqual(v["soulsilver"]["primary_items"],
                         ["SILVERWING", "TIDALBELL"])
        self.assertEqual(v["crystal"]["status"],
                         "SEPARATE_VARIANT_NOT_IMPLEMENTED")
        self.assertEqual(v["crystal"]["suicune"], "TIN_TOWER")
        self.assertFalse(v["crystal"]["hgss_kimono_flow"])
        self.assertIn("HGSS_PRELEAGUE_MASCOT_GATE",
                      self.phase["future_not_installed"])
        self.assertIn('VERSION_TOKEN = "BLUE_JOHTO_VERSION_V1_READY"', self.script)
        self.assertIn('WINGS = {"HEARTGOLD"=>:RAINBOWWING', self.script)
        self.assertIn('BELLS = {"HEARTGOLD"=>:CLEARBELL', self.script)

    def test_bell_tower_four_whirl_entrances_and_safe_return_are_symbolic(self):
        phase = self.phase
        keys = [x["key"] for x in phase["corridor"]]
        self.assertEqual(len(keys), len(set(keys)))
        expected = {
            "JOHTO_BELL_TOWER_ENTRANCE", "JOHTO_BELL_TOWER_ROOF",
            "JOHTO_WHIRL_NW", "JOHTO_WHIRL_NE",
            "JOHTO_WHIRL_SW", "JOHTO_WHIRL_SE",
            "JOHTO_WHIRL_LUGIA_CHAMBER", "JOHTO_RUINS_OF_ALPH_CHAMBERS",
            "JOHTO_MT_SILVER_UNAVAILABLE", "JOHTO_RED_UNAVAILABLE",
        }
        self.assertTrue(expected.issubset(keys))
        for edge in phase["links"]:
            self.assertEqual(edge["kind"], "symbolic_only_no_warp")
            self.assertFalse(edge["physically_installed"])
            self.assertIn(edge["from"], keys)
            self.assertIn(edge["to"], keys)
        for node in phase["corridor"]:
            for invalid in ("map_id", "coordinates", "x", "y", "source_id"):
                self.assertNotIn(invalid, node)
        self.assertEqual(
            len(self.phase10["whirl_islands"]["candidate_entrances"]), 4
        )
        self.assertEqual(self.phase10["whirl_islands"]["entrance_warps"], [])
        self.assertIn("SAFE_EXIT_TOKEN", self.script)
        self.assertIn("BLUE_JOHTO_LEGENDARY_EXITS_V1_READY", self.script)
        self.assertIn("return false unless flags && version", self.script)

    def test_beasts_legendaries_suicune_and_ruins_do_not_spawn(self):
        legend = self.phase["legendary_contract"]
        self.assertEqual(legend["roamers"], ["RAIKOU", "ENTEI"])
        self.assertEqual(legend["starts_after"],
                         "burned_tower_beasts_awakened")
        self.assertTrue(legend["capture_does_not_duplicate"])
        self.assertFalse(legend["suicune_hgss"]["accessible"])
        self.assertFalse(legend["suicune_crystal"]["accessible"])
        self.assertEqual(legend["defeated_not_captured"],
                         "awaiting_verified_rematch")
        self.assertEqual(self.phase["kimono_girls"]["count"], 5)
        self.assertEqual(self.phase["kimono_girls"]["pbs_versions"],
                         [0, 1, 2, 3, 4])
        self.assertFalse(self.phase["kimono_girls"]["compiled"])
        self.assertEqual(self.phase["ruins_of_alph"]["puzzle_count"], 4)
        self.assertFalse(self.phase["ruins_of_alph"]["unown_encounters_installed"])
        self.assertIn("def self.register_roamer(species, result)", self.script)
        self.assertIn("def self.legendary_result(species, outcome)", self.script)
        self.assertIn("def self.hgss_suicune_route25", self.script)
        self.assertIn("def self.crystal_suicune", self.script)
        self.assertNotIn("pbWildBattle", self.script)
        self.assertNotIn("pbAddPokemon(", self.script)

    def test_johto_eight_badges_and_no_world_rematches_spoofing(self):
        self.assertEqual(self.registry["milestones"],
                         ["ZEPHYR", "HIVE", "PLAIN", "FOG",
                          "STORM", "MINERAL", "GLACIER", "RISING"])
        self.assertEqual(self.registry["field"]["WHIRLPOOL"]["badge"],
                         "JOHTO:GLACIER")
        self.assertEqual(self.registry["field"]["SURF"]["badge"],
                         "JOHTO:FOG")
        self.assertIn('BlueRegions.allow_specials?(state, REGION)', self.script)
        self.assertIn('BlueRegions.field_access(state, REGION, action, tool_ready)',
                      self.script)
        for resource, method in (
            ("bug_catching_contest", "bug_contest"),
            ("pokeathlon", "pokeathlon"),
            ("mt_silver", "mt_silver"),
            ("red_battle", "red_battle"),
        ):
            self.assertIn(f"def self.{method}", self.script)
            self.assertFalse(self.phase["optional_postgame"][resource]["installed"])

    def test_unverified_maps_stay_non_playable(self):
        self.assertEqual(self.phase["region"], "JOHTO")
        self.assertEqual(self.phase["phase"], "14/16")
        self.assertEqual(self.phase["requires_completed_phase"], "13/16")
        self.assertEqual(self.phase["status"], "SPECIFICATION_ONLY_NOT_INSTALLED")
        self.assertFalse(self.phase["integrated"])
        self.assertEqual(set(self.phase["validation"].values()), {False})
        self.assertTrue(all(not x["installed"] for x in
                            self.phase["readiness_markers"]))
        for item in self.phase["readiness_markers"]:
            self.assertIn(item["token"], self.script)
        self.assertFalse(self.source["import_enabled"])
        self.assertFalse(self.source["mapping_verified"])
        self.assertEqual(self.source["maps"], {})
        self.assertIsNone(self.source["source"]["archive_sha256"])
        self.assertIn("MT_SILVER", self.source["missing_required"])
        self.assertEqual(self.previous["regional_completion"]["completed_entry"],
                         "JOHTO")


if __name__ == "__main__":
    unittest.main()
