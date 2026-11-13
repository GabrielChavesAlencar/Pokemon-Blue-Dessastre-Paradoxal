"""As barras de Johto não podem confundir Map Pack com gameplay real."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class JohtoProgressTests(unittest.TestCase):
    def test_source_coverage_is_not_gameplay_approval(self):
        tracker = load("data/regions/johto-progress.json")
        source = load("data/regions/johto-source.json")
        edges = load("data/regions/johto-v1-map-connections.json")
        portal = load("site/public/data/johto-preview.json")
        self.assertEqual((tracker["schema"], tracker["region"]), (1, "JOHTO"))
        count = len(source["maps"])
        self.assertEqual(count, 74)
        self.assertEqual(tracker["progress"]["map_pack_source_maps"]["verified"], count)
        self.assertEqual(tracker["progress"]["map_pack_source_maps"]["total"], count)
        edge_count = len(edges["connections"])
        self.assertEqual(edge_count, 42)
        self.assertEqual(tracker["progress"]["map_pack_connection_rows"]["verified"], edge_count)
        self.assertEqual(tracker["progress"]["map_pack_connection_rows"]["total"], edge_count)
        self.assertEqual(source["source"]["archive_sha256"], edges["source_archive_sha256"])
        self.assertFalse(source["import_enabled"])
        self.assertFalse(source["source"]["distribution_approved"])
        self.assertEqual(portal["maps_installed"], 0)
        self.assertEqual(portal["trainers_compiled"], 0)
        self.assertEqual(tracker["progress"]["technical_phases_fully_approved"], {
            "verified": 0, "total": 16, "meaning": tracker["progress"]["technical_phases_fully_approved"]["meaning"]
        })
        self.assertEqual(tracker["progress"]["gameplay_phases_fully_approved"]["verified"], 0)

    def test_each_phase_has_evidence_and_blockers(self):
        tracker = load("data/regions/johto-progress.json")
        phases = tracker["phases"]
        self.assertEqual([p["id"] for p in phases], list(range(1,17)))
        self.assertEqual(len(phases), 16)
        for phase in phases:
            self.assertEqual(phase["state"], "PARTIAL")
            self.assertTrue(phase["evidence"])
            self.assertTrue(phase["blockers"])
        self.assertIn("game/Data", " ".join(phases[0]["blockers"]))
        self.assertIn("Game.exe", " ".join(phases[1]["blockers"]))

    def test_no_bar_can_claim_acceptance_without_integrated_maps(self):
        tracker = load("data/regions/johto-progress.json")
        m = load("data/regions/johto-source.json")
        assert not m["import_enabled"]
        self.assertEqual(tracker["gameplay_proof"], "NO_WINDOWS_OR_JOIPLAY_GAMEPLAY_APPROVAL")
        self.assertEqual(tracker["progress"]["technical_phases_fully_approved"]["verified"], 0)
        self.assertEqual(tracker["progress"]["gameplay_phases_fully_approved"]["verified"], 0)


if __name__ == "__main__":
    unittest.main()
