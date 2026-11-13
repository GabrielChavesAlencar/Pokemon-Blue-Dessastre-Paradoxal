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
        self.assertEqual(tracker["progress"]["playable_gameplay_phases"]["verified"], 0)
        self.assertEqual(tracker["progress"]["tested_gameplay_phases"]["verified"], 0)

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

    def test_distinct_bars_playable_and_native_qa_have_independent_rules(self):
        tracker = load("data/regions/johto-progress.json")
        progress = tracker["progress"]
        phases = tracker["phases"]
        eligible = [p for p in phases if p["id"] >= 4]
        infrastructure = [p for p in phases if p["id"] < 4]
        self.assertEqual(len(eligible), 13)
        self.assertEqual(len(infrastructure), 3)
        self.assertEqual([p["id"] for p in eligible], list(range(4, 17)))
        self.assertEqual(
            progress["playable_gameplay_phases"]["total"], len(eligible))
        self.assertEqual(
            progress["tested_gameplay_phases"]["total"], len(eligible))
        self.assertEqual(
            progress["playable_gameplay_phases"]["verified"],
            sum(p["gameplay_playable"] is True for p in eligible))
        self.assertEqual(
            progress["tested_gameplay_phases"]["verified"],
            sum(p["gameplay_tested"] is True for p in eligible))
        self.assertTrue(all(p["gameplay_tested"] is not True or
                            p["gameplay_playable"] is True for p in eligible))
        self.assertTrue(all(p["gameplay_playable"] is None and
                            p["gameplay_tested"] is None for p in infrastructure))
        self.assertTrue(all(p["gameplay_playable"] is False and
                            p["gameplay_tested"] is False for p in eligible))
        self.assertEqual(tracker["progress_labels"]["playable"],
                         "Fases jogáveis no Game.exe")
        self.assertIn("QA", tracker["progress_labels"]["tested"])

    def test_technical_code_tests_have_full_coverage_but_are_not_native_gameplay(self):
        tracker = load("data/regions/johto-progress.json")
        phases = tracker["phases"]
        paths = [p["automated_code_test"] for p in phases]
        self.assertEqual(len(set(paths)), 16)
        self.assertTrue(all((ROOT / path).is_file() for path in paths))
        self.assertTrue(all(path.startswith("tests/test_") and
                            path.endswith(".py") for path in paths))
        coverage = tracker["progress"]["automated_code_test_coverage"]
        self.assertEqual(coverage["verified"], len(paths))
        self.assertEqual(coverage["total"], len(paths))
        self.assertEqual(coverage["total"], 16)
        self.assertEqual(tracker["progress"]["playable_gameplay_phases"]["verified"], 0)
        self.assertEqual(tracker["progress"]["tested_gameplay_phases"]["verified"], 0)
        document = (ROOT / "docs/JOHTO_ETAPAS.md").read_text("utf-8")
        self.assertIn("Fases JOGÁVEIS", document)
        self.assertIn("Fases TESTADAS", document)
        self.assertIn("0/13", document)
        self.assertIn("16/16", document)

    def test_no_bar_can_claim_acceptance_without_integrated_maps(self):
        tracker = load("data/regions/johto-progress.json")
        m = load("data/regions/johto-source.json")
        assert not m["import_enabled"]
        self.assertEqual(tracker["gameplay_proof"], "NO_WINDOWS_OR_JOIPLAY_GAMEPLAY_APPROVAL")
        self.assertEqual(tracker["progress"]["technical_phases_fully_approved"]["verified"], 0)
        self.assertEqual(tracker["progress"]["gameplay_phases_fully_approved"]["verified"], 0)


if __name__ == "__main__":
    unittest.main()
