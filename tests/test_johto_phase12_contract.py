"""Phase 12: symbolic Ice Path/Blackthorn/Clair contract, no installed-map claims."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class JohtoPhase12ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = load("data/regions/johto-phase12.json")
        cls.previous = load("data/regions/johto-phase11.json")
        cls.source = load("data/regions/johto-source.json")
        cls.johto = load("site/public/data/regions.json")["regions"]["JOHTO"]
        cls.ruby = (ROOT / "scripts/regions/JohtoBlackthorn.rb").read_text(
            encoding="utf-8"
        )

    def test_route44_ice_path_blackthorn_symbolic_continuity(self):
        current = self.current
        self.assertEqual(current["phase"], "12/16")
        self.assertEqual(current["region"], "JOHTO")
        self.assertEqual(current["requires_completed_phase"], "11/16")
        expected = [
            "JOHTO_MAHOGANY_TOWN", "JOHTO_ROUTE_44_GATE", "JOHTO_ROUTE_44",
            "JOHTO_ICE_PATH_1F_WEST", "JOHTO_ICE_PATH_B1F",
            "JOHTO_ICE_PATH_B2F", "JOHTO_ICE_PATH_1F_EAST",
            "JOHTO_BLACKTHORN_CITY"
        ]
        self.assertEqual([x["key"] for x in current["corridor"]], expected)
        older = {x["key"] for x in self.previous["corridor"] +
                 self.previous["required_interiors"]}
        self.assertIn(expected[0], older)
        self.assertIn(expected[1], older)
        all_nodes = current["corridor"] + current["required_interiors"]
        keys = [x["key"] for x in all_nodes]
        self.assertEqual(len(keys), len(set(keys)))
        graph = {(x["from"], x["to"]) for x in current["links"]}
        for start, end in zip(expected, expected[1:]):
            self.assertIn((start, end), graph)
        for row in current["links"]:
            self.assertTrue(row["two_way"])
            self.assertEqual(row["kind"], "symbolic_only_no_warp")
            self.assertIn(row["from"], keys)
            self.assertIn(row["to"], keys)
        for node in all_nodes:
            for forbidden in ("map_id", "source_id", "coordinates", "x", "y"):
                self.assertNotIn(forbidden, node)

    def test_gym_dragon_den_route45_46_and_dark_cave_are_planned(self):
        required = {x["key"] for x in self.current["required_interiors"]}
        self.assertTrue({
            "JOHTO_BLACKTHORN_GYM", "JOHTO_BLACKTHORN_GYM_PUZZLE",
            "JOHTO_DRAGONS_DEN_ENTRANCE", "JOHTO_DRAGONS_DEN_MAIN",
            "JOHTO_DRAGON_SHRINE", "JOHTO_ROUTE_45",
            "JOHTO_ROUTE_46", "JOHTO_DARK_CAVE_ROUTE45_GATE",
            "JOHTO_DARK_CAVE_ROUTE46_GATE"
        }.issubset(required))
        self.assertTrue({
            "DARK_CAVE_ENTRANCE", "ICE_PATH_PHYSICAL_SLIDING",
            "CRYSTAL_DRAGON_FANG_VARIANT", "TOHJO_FALLS_LEAGUE",
        }.issubset(set(self.current["future_not_implemented"])))
        self.assertIn("return false unless record", self.ruby)
        self.assertIn("def self.dark_cave_entry", self.ruby)

    def test_rising_is_eighth_badge_and_waterfall_is_local(self):
        badge = self.current["badge"]
        self.assertEqual(badge, {
            "key": "RISING", "region": "JOHTO", "ordinal": 8,
            "award_source": "BlueRegions.award",
            "max_awards_per_save": 1, "grants_field_action": "WATERFALL"
        })
        self.assertEqual(
            self.johto["milestones"],
            ["ZEPHYR", "HIVE", "PLAIN", "FOG",
             "STORM", "MINERAL", "GLACIER", "RISING"]
        )
        self.assertEqual(
            self.johto["field"]["WATERFALL"]["badge"], "JOHTO:RISING"
        )
        self.assertTrue(self.johto["field"]["WATERFALL"]["tool"])
        self.assertEqual(self.johto["field"]["STRENGTH"]["badge"], "JOHTO:PLAIN")
        self.assertEqual(self.johto["field"]["WHIRLPOOL"]["badge"],
                         "JOHTO:GLACIER")
        self.assertIn('BlueRegions.award(state, REGION, BADGE)', self.ruby)
        self.assertIn('BlueRegions.allow_specials?(state, REGION)', self.ruby)
        self.assertIn('BlueRegions.field_access(state, REGION, "WATERFALL", tool_ready)',
                      self.ruby)

    def test_clair_defeat_not_badge_and_master_approval_required(self):
        self.assertIn('TrainerBattle.start(CLAIR_TYPE, "Clair", 0)', self.ruby)
        self.assertIn('flags["blackthorn_clair_defeated"] = true', self.ruby)
        self.assertIn('flags["dragon_master_approved"] = true', self.ruby)
        self.assertIn('flags["blackthorn_rising_claimed"] = true', self.ruby)
        self.assertIn("def self.clair_rising_badge", self.ruby)
        self.assertEqual(
            self.current["trainer_requirements"][0]["trainer_type"],
            "BLUE_JOHTO_CLAIR"
        )
        self.assertTrue(all(not t["compiled"]
                            for t in self.current["trainer_requirements"]))
        self.assertEqual(
            self.current["items"],
            [{
                "key": "HM07", "role": "Waterfall on Ice Path",
                "status": "CANDIDATE_UNVERIFIED",
                "marker": "Data/blue-johto-waterfall-item-ready.txt"
            }]
        )
        self.assertIn("BLUE_JOHTO_DRAGON_MASTER_V1_READY", self.ruby)
        self.assertIn("BLUE_JOHTO_BLACKTHORN_GYM_V1_READY", self.ruby)
        self.assertIn("BLUE_JOHTO_ICE_BOULDERS_V1_READY", self.ruby)

    def test_league_is_only_handoff_and_source_is_still_not_imported(self):
        self.assertEqual(
            self.current["league_handoff"]["status"],
            "PREVIEW_ONLY_NOT_TRAVEL"
        )
        self.assertEqual(
            len(self.current["league_handoff"]["requires"]), 8
        )
        self.assertFalse(self.current["league_handoff"]["league_completed"])
        self.assertEqual(self.current["status"],
                         "SPECIFICATION_ONLY_NOT_INSTALLED")
        self.assertFalse(self.current["integrated"])
        self.assertEqual(set(self.current["validation"].values()), {False})
        self.assertFalse(self.source["import_enabled"])
        self.assertFalse(self.source["mapping_verified"])
        self.assertEqual(self.source["maps"], {})
        self.assertIsNone(self.source["source"]["archive_sha256"])


if __name__ == "__main__":
    unittest.main()
