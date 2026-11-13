"""Sinnoh transfer graph contracts: only real audited source IDs, no writes."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from graph_sinnoh_maps import make_graph


def example():
    return {
        "region": "SINNOH", "mode": "READ_ONLY_INERT_RMXP",
        "import_allowed": False, "source_map_ids": [1, 2, 3, 4],
        "maps": [
            {"source_id": 1, "name": "Twinleaf", "transfer_targets": [2, 99]},
            {"source_id": 2, "name": "Route 201", "transfer_targets": [1, 3]},
            {"source_id": 3, "name": "Sandgem", "transfer_targets": []},
            {"source_id": 4, "name": "Unconnected interior", "transfer_targets": []},
        ],
        "unresolved_static_transfer_ids": [99],
        "dynamic_transfer_commands": 2,
        "untrusted_script_commands_not_executed": 3,
        "missing_map_files": [7], "orphan_map_files": [4],
    }


class SinnohGraphTests(unittest.TestCase):
    def test_graph_detects_dangling_edges_but_does_not_claim_playability(self):
        result = make_graph(example(), start_map=1)
        self.assertEqual(result["mode"], "STATIC_MAP_GRAPH_NO_INSTALL")
        self.assertEqual(result["map_count"], 4)
        self.assertEqual(result["static_transfer_count"], 4)
        self.assertEqual(result["static_valid_transfer_count"], 3)
        self.assertEqual(result["dangling_target_ids"], [99])
        self.assertEqual(result["weakly_connected_groups"], [[1, 2, 3], [4]])
        self.assertEqual(result["isolated_map_ids"], [4])
        self.assertEqual(result["unreachable_from_selected_start"], [4])
        self.assertEqual(result["dynamic_transfer_commands_needing_manual_review"], 2)
        self.assertEqual(result["untrusted_script_commands_not_executed"], 3)
        self.assertEqual(result["missing_mapinfos_ids"], [7])
        self.assertEqual(result["orphan_map_file_ids"], [4])
        self.assertFalse(result["safe_to_install"])
        self.assertFalse(result["map_ids_allocated"])

    def test_no_start_map_does_not_invent_twinleaf_location(self):
        result = make_graph(example())
        self.assertIsNone(result["start_map_selected"])
        self.assertIsNone(result["unreachable_from_selected_start"])
        self.assertTrue(all(node["reachable_from_selected_start"] is None
                            for node in result["nodes"]))

    def test_requires_a_verified_actual_start_map(self):
        with self.assertRaisesRegex(ValueError, "ID REAL"):
            make_graph(example(), start_map=20)
        with self.assertRaisesRegex(ValueError, "ID REAL"):
            make_graph(example(), start_map=0)

    def test_detects_report_inconsistency_and_duplicate_map_ids(self):
        report = example()
        report["unresolved_static_transfer_ids"] = []
        with self.assertRaisesRegex(ValueError, "divergentes"):
            make_graph(report)
        report = example()
        report["maps"].append(dict(report["maps"][0]))
        with self.assertRaisesRegex(ValueError, "repetido"):
            make_graph(report)

    def test_rejects_non_sinnoh_or_claimed_import(self):
        report = example()
        report["import_allowed"] = True
        with self.assertRaisesRegex(ValueError, "inerte"):
            make_graph(report)
        report = example()
        report["region"] = "JOHTO"
        with self.assertRaisesRegex(ValueError, "inerte"):
            make_graph(report)

    def test_one_way_transfer_and_dynamic_warp_are_only_review_candidates(self):
        report = example()
        report["maps"] = [
            {"source_id": 1, "name": "A", "transfer_targets": [2]},
            {"source_id": 2, "name": "B", "transfer_targets": []},
        ]
        report["source_map_ids"] = [1, 2]
        report["unresolved_static_transfer_ids"] = []
        result = make_graph(report, start_map=1)
        self.assertEqual(result["unreachable_from_selected_start"], [])
        self.assertEqual(result["weakly_connected_groups"], [[1, 2]])
        self.assertEqual(result["nodes"][1]["outbound_count"], 0)
        self.assertFalse(result["safe_to_install"])


if __name__ == "__main__":
    unittest.main()
