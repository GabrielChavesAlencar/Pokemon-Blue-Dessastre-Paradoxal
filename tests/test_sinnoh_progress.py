"""Keep Sinnoh's preparation bar separate from actual playable/native QA gates."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SinnohProgressTests(unittest.TestCase):
    def test_progress_ledger_is_complete_and_consistent(self):
        obj = json.loads((ROOT / "data/regions/sinnoh-progress.json").read_text("utf-8"))
        self.assertEqual((obj["schema"], obj["region"]), (1, "SINNOH"))
        tasks = obj["tasks"]
        ids = [t["id"] for t in tasks]
        self.assertEqual(ids, [f"S{i:02}" for i in range(1, 33)])
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(t["status"] in ("done", "partial", "pending") for t in tasks))
        development = obj["development"]
        self.assertEqual(development["total"], len(tasks))
        for name in ("done", "partial", "pending"):
            self.assertEqual(development[name],
                             sum(t["status"] == name for t in tasks))
        self.assertEqual(sum(development[name] for name in ("done", "partial", "pending")), 32)
        self.assertEqual(development["percent_complete"], 100 * development["done"] // 32)
        members = [identifier for group in development["groups"] for identifier in group["tasks"]]
        self.assertEqual(sorted(members), sorted(ids))
        for row in tasks:
            if row["status"] == "done":
                path = row["evidence_path"]
                self.assertTrue(path and (ROOT / path).is_file(),
                                f"Done without an actual artifact: {row['id']}")
        self.assertEqual(obj["phase_gates"]["total"], 13)
        for name in ("technically_approved", "playable_in_game_executable",
                     "fully_tested_native"):
            self.assertEqual(obj["phase_gates"][name], 0)

    def test_markdown_bar_matches_json(self):
        obj = json.loads((ROOT / "data/regions/sinnoh-progress.json").read_text("utf-8"))
        md = (ROOT / "docs/SINNOH_PROGRESSO.md").read_text("utf-8")
        progress = obj["development"]
        self.assertIn(f'{progress["done"]}/{progress["total"]} ({progress["percent_complete"]}%)', md)
        self.assertIn(f'**Parciais:** {progress["partial"]}', md)
        self.assertIn(f'**Pendentes:** {progress["pending"]}', md)
        for t in obj["tasks"]:
            if t["status"] == "done":
                self.assertRegex(md, rf'\b{re.escape(t["id"])}\b')
        self.assertGreaterEqual(md.count("0/13 (0%)"), 3)

    def test_remap_substeps_do_not_inflate_main_or_playable_bars(self):
        record = json.loads((ROOT / "data/regions/sinnoh-progress.json").read_text("utf-8"))
        work = record["remap_workstream"]
        substeps = work["substeps"]
        self.assertEqual(work["task_id"], "S07")
        self.assertEqual(work["status"], "PARTIAL_NOT_INSTALLABLE")
        self.assertEqual(work["total"], len(substeps))
        self.assertEqual(work["complete"], sum(row["complete"] for row in substeps))
        self.assertEqual(work["complete"], 6)
        self.assertEqual(work["total"], 9)
        self.assertEqual(record["development"]["done"], 8)
        self.assertEqual(record["development"]["percent_complete"], 25)
        self.assertEqual(next(t["status"] for t in record["tasks"]
                              if t["id"] == "S07"), "partial")
        self.assertTrue(all(not row["complete"] or
                            (row["evidence"] and (ROOT / row["evidence"]).is_file())
                            for row in substeps))
        panel = (ROOT / "docs/SINNOH_PROGRESSO.md").read_text("utf-8")
        self.assertIn("6/9", panel)

    def test_planned_region_and_unverified_source_remain_blocked(self):
        registry = json.loads((ROOT / "site/public/data/regions.json").read_text("utf-8"))
        provenance = json.loads((ROOT / "data/regions/sinnoh-source.json").read_text("utf-8"))
        self.assertEqual(registry["regions"]["SINNOH"]["status"], "planned")
        self.assertFalse(provenance["import_control"]["imports_enabled"])
        self.assertEqual(provenance["progress"]["technical_approved"], 0)
        self.assertEqual(provenance["progress"]["native_playable_approved"], 0)


if __name__ == "__main__":
    unittest.main()
