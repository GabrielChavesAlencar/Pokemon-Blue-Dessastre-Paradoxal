"""Regression tests for Hoenn pilot public catalog, scripts and map inventory.

Fixtures are synthetic local JSON/text files. These tests never execute
Game.exe, import donor assets, or modify a native installation.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_hoenn_baseline import PILOT
from audit_hoenn_pilot_contract import AUDIT_VERSION, CATALOG, HANDLERS, REGISTRY, audit
from pilot_hoenn import LAND_ENCOUNTERS, ROUTE_102_TRAINERS, SOURCE_MAPS


class HoennPilotContractTests(unittest.TestCase):
    def test_current_repository_contract_is_consistent_not_gameplay_proof(self):
        report = audit(ROOT)
        self.assertEqual(report["schema"], AUDIT_VERSION)
        self.assertTrue(report["static_contract_validated"], report["errors"])
        self.assertEqual(report["errors"], [])
        self.assertEqual(set(PILOT), set(SOURCE_MAPS))
        self.assertEqual(report["source_maps"], 58)
        self.assertEqual(report["public_catalog_locations"], 58)
        self.assertEqual(report["route_102_trainers"], 4)
        self.assertEqual(report["stage3_trainer_presets"], 10)
        self.assertEqual(report["stage3_pickup_events"], 20)
        self.assertEqual(report["stage4_source_maps"], 10)
        self.assertEqual(report["stage4_trainer_presets"], 16)
        self.assertEqual(report["stage4_pickup_events"], 10)
        self.assertEqual(report["stage4_cut_trees"], 5)
        self.assertEqual(report["stage5_source_maps"], 20)
        self.assertEqual(report["stage5_boat_stops"], 3)
        self.assertEqual(report["stage5_trainer_presets"], 11)
        self.assertEqual(report["stage5_pickup_events"], 2)
        self.assertEqual(report["stage5_cave_maps"], 4)
        self.assertEqual(report["stage6_source_maps"], 10)
        self.assertEqual(report["stage6_trainer_presets"], 27)
        self.assertEqual(report["stage6_pickup_events"], 7)
        self.assertEqual(report["stage6_cycling_gates"], 4)
        self.assertEqual(report["stage6_gym_switches"], 4)
        self.assertEqual(report["stage6_gym_barriers"], 7)
        self.assertEqual(report["cave_route_maps"], [157, 159, 160, 161, 162])
        self.assertEqual(report["wild_route_maps"], [101, 102, 103, 104, 113, 130, 156])
        self.assertEqual(report["wild_slots"], sum(map(len, LAND_ENCOUNTERS.values())))
        self.assertEqual(len(ROUTE_102_TRAINERS), 4)
        self.assertTrue(report["map_graph_connected"])
        self.assertFalse(report["native_assets_examined"])
        self.assertFalse(report["game_exe_tested"])
        self.assertFalse(report["android_tested"])
        self.assertGreaterEqual(len(report["known_story_gaps"]), 5)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for rel in (CATALOG, HANDLERS, REGISTRY):
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, dst)

    def edit_json(self, relative, fn):
        path = self.root / relative
        payload = json.loads(path.read_text(encoding="utf-8"))
        fn(payload)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def test_modified_wild_chance_fails_closed(self):
        def modify(data):
            route = next(row for row in data["locations"] if row["name"] == "Rota 102")
            route["encounters"]["Grama"][0][3] += 1
        self.edit_json(CATALOG, modify)
        errors = audit(self.root)["errors"]
        self.assertTrue(any("grass encounter slots differ" in e for e in errors), errors)

    def test_modified_trainer_party_fails_closed(self):
        def modify(data):
            trainer = next(t for t in data["trainers"] if t["name"] == "Calvin")
            trainer["teams"][0]["pokemon"][0][0] = "RATTATA"
        self.edit_json(CATALOG, modify)
        errors = audit(self.root)["errors"]
        self.assertTrue(any("Trainer Calvin:" in e for e in errors), errors)

    def test_runtime_handler_removed_fails_closed(self):
        path = self.root / HANDLERS
        code = path.read_text(encoding="utf-8")
        self.assertIn("def self.route_birch", code)
        path.write_text(code.replace("def self.route_birch", "def self.missing_route_birch"),
                        encoding="utf-8")
        errors = audit(self.root)["errors"]
        self.assertTrue(any("handler(s) missing" in e for e in errors), errors)

    def test_published_as_playable_fails_closed(self):
        self.edit_json(REGISTRY, lambda data: data["regions"]["HOENN"].update(status="playable"))
        errors = audit(self.root)["errors"]
        self.assertTrue(any("must not be declared playable" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
