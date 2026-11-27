"""K04 review reads source facts without altering released identities."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_k04_rock_tunnel import K04, candidate_mapping, summarize


class K04AuditTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT / "data/regions/kanto-source.json").read_text("utf8"))

    def test_candidate_appends_to_released_160(self):
        occupied = set(range(1, 300))
        result = candidate_mapping(self.catalog, occupied)
        self.assertEqual(result, {"86": 604, "87": 605, "88": 606, "90": 607, "91": 608})
        self.assertEqual(len(self.catalog["maps"]), 160)
        self.assertFalse(set(map(str, K04)) & self.catalog["maps"].keys())

    def test_rejects_stale_or_partly_activated_catalog(self):
        for drop, put in (("79", None), ("79", "86")):
            catalog = copy.deepcopy(self.catalog)
            catalog["maps"].pop(drop)
            if put:
                catalog["maps"][put] = "UNREVIEWED"
            with self.assertRaises(ValueError):
                candidate_mapping(catalog, {1, 2, 3})

    def test_review_records_warps_teams_and_flash_without_copying_event_scripts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pbs = root / "PBS"
            pbs.mkdir()
            for f, data in (
                ("map_connections.txt", "86,East,0,87,West,0\n"),
                ("trainers.txt", '[HIKER,Test,0]\nPokemon = GEODUDE,18\n'),
                ("encounters.txt", "[090]\nCave,4\n100,ZUBAT,10,14\n"),
                ("map_metadata.txt", "[090]\nDarkMap = true\n"),
            ):
                (pbs / f).write_text(data, encoding="utf8")
            maps = {str(n): {"name": str(n), "dimensions": [20, 20],
                             "source_sha256": "x", "events": []} for n in K04}
            maps["90"]["events"].append({"id": 1, "xy": [1, 2], "pages": [
                {"page": 1, "commands": [
                    {"code": 201, "parameters": [0, 91, 6, 6, 2, 0]},
                    {"code": 111, "parameters": [12, 'TrainerBattle.start(:HIKER, "Test")']},
                    {"code": 355, "parameters": ["pbFlash"]},
                ]}
            ]})
            report = summarize(root, maps, candidate_mapping(self.catalog, set(range(1, 300))))
            self.assertEqual(report["transfers"][0]["destination"], 91)
            self.assertIn("90/1", report["trainers"])
            self.assertEqual(report["flash_event_references"], [{"map": 90, "event": 1, "page": 1, "opcode": 355}])
            self.assertNotIn("TrainerBattle.start", json.dumps(report))
            self.assertFalse(report["manual_gameplay"])
            self.assertEqual(report["status"], "SOURCE_REVIEW_ONLY")


if __name__ == "__main__":
    unittest.main()
