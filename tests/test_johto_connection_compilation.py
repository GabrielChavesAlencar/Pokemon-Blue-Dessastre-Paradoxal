"""Safe native-PBS remapping of Johto's real 42 border connections.

Pure-code unit tests do not certify walkthroughs or collisions in Game.exe.
"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    from compile_johto_connections import compile_connections, merge_pbs, write_preview
finally:
    sys.path.pop(0)


def source_graph_and_stage():
    source = json.loads((ROOT / "data/regions/johto-source.json")
                        .read_text(encoding="utf-8"))
    graph = json.loads((ROOT / "data/regions/johto-v1-map-connections.json")
                       .read_text(encoding="utf-8"))
    # IDs here are SYNTHETIC & cannot be used in the user's game.
    stage = {
        "schema": 1, "region": "JOHTO", "status": "GEOMETRY_PREVIEW_ONLY",
        "can_install": False, "not_playable": True,
        "source_archive_sha256": source["source"]["archive_sha256"],
        "maps": [
            {"source_id": mid, "symbol": source["maps"][str(mid)],
             "destination_id": 600 + (mid - 79), "events_imported": 0}
            for mid in range(79, 153)
        ],
    }
    return source, graph, stage


class JohtoConnectionCompilationTests(unittest.TestCase):
    def test_remaps_all_real_source_edges_without_kanto(self):
        source, graph, stage = source_graph_and_stage()
        pbs, info = compile_connections(graph, source, stage)
        self.assertEqual(info["status"], "COMPILED_CONNECTIONS_PREVIEW_ONLY")
        self.assertEqual(info["source_count"], 42)
        self.assertEqual(info["compiled_count"], 42)
        self.assertFalse(info["tested_in_game"])
        self.assertFalse(info["can_install"])
        lines = pbs.strip().splitlines()
        self.assertEqual(len(lines), 42)
        self.assertEqual(lines[0], "600,West,13,625,East,0")
        self.assertTrue(all(int(line.split(",")[0]) >= 600 and
                            int(line.split(",")[3]) >= 600 for line in lines))
        self.assertFalse(any(
            {int(line.split(",")[0]), int(line.split(",")[3])} == {601, 625}
            for line in lines))
        self.assertIn("JOHTO_ROUTE_29_TO_CHERRYGROVE", info["missing_required"])

    def test_rejects_unmapped_source_and_unaudited_changes(self):
        source, graph, stage = source_graph_and_stage()
        corrupted = copy.deepcopy(graph)
        corrupted["connections"][0]["to_id"] = 8  # Kanto
        with self.assertRaisesRegex(ValueError, "absent/non-Johto"):
            compile_connections(corrupted, source, stage)
        corrupted = copy.deepcopy(stage)
        corrupted["source_archive_sha256"] = "a"*64
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            compile_connections(graph, source, corrupted)
        corrupted = copy.deepcopy(stage)
        corrupted["maps"].pop()
        with self.assertRaisesRegex(ValueError, "absent/non-Johto"):
            compile_connections(graph, source, corrupted)
        corrupted = copy.deepcopy(stage)
        corrupted["maps"][1]["symbol"] = "JOHTO_FAKE"
        with self.assertRaisesRegex(ValueError, "Untrusted"):
            compile_connections(graph, source, corrupted)

    def test_rejects_inverted_duplicate_edges_and_bad_offsets(self):
        source, graph, stage = source_graph_and_stage()
        bad = copy.deepcopy(graph)
        bad["connections"].append(copy.deepcopy(bad["connections"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            compile_connections(bad, source, stage)
        bad = copy.deepcopy(graph)
        one = copy.deepcopy(bad["connections"][0])
        reverse = {
            "from_id": one["to_id"], "to_id": one["from_id"],
            "from_edge": one["to_edge"], "to_edge": one["from_edge"],
            "from_offset": one["to_offset"], "to_offset": one["from_offset"]}
        bad["connections"].append(reverse)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            compile_connections(bad, source, stage)
        bad = copy.deepcopy(graph)
        bad["connections"][0]["from_offset"] = -1
        with self.assertRaisesRegex(ValueError, "invalid position"):
            compile_connections(bad, source, stage)
        bad = copy.deepcopy(graph)
        bad["connections"][0]["to_edge"] = "West"
        with self.assertRaisesRegex(ValueError, "opposite"):
            compile_connections(bad, source, stage)

    def test_merges_only_in_copy_preserving_kanto_pbs(self):
        source, graph, stage = source_graph_and_stage()
        addon, _ = compile_connections(graph, source, stage)
        base = b"# Map connections of native Decades\n1,East,0,2,West,0\n"
        combined = merge_pbs(base, addon)
        self.assertTrue(combined.startswith(base))
        self.assertEqual(combined.decode().count("600,West,13,625,East,0"), 1)
        self.assertEqual(len(combined.splitlines()), len(base.splitlines()) + 43)
        self.assertEqual(base, b"# Map connections of native Decades\n1,East,0,2,West,0\n")
        with self.assertRaisesRegex(ValueError, "already present"):
            merge_pbs(combined, addon)
        self.assertIn(b"600,West,13,625,East,0", merge_pbs(None, addon))
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            merge_pbs(b"\0" + base, addon)

    def test_write_preview_only_under_blue_work_and_never_overwrite(self):
        source, graph, stage = source_graph_and_stage()
        content, _ = compile_connections(graph, source, stage)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / ".blue-work/preview.txt"
            write_preview(out, content, root=root)
            self.assertEqual(out.read_text("utf-8"), content)
            with self.assertRaisesRegex(ValueError, "NEW"):
                write_preview(out, content, root=root)
            outside = root / "game/PBS/map_connections.txt"
            with self.assertRaisesRegex(ValueError, "NEW"):
                write_preview(outside, content, root=root)
            self.assertFalse(outside.exists())


if __name__ == "__main__":
    unittest.main()
