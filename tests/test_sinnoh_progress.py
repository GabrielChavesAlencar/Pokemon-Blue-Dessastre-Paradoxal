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

    def test_twinleaf_story_prepared_but_never_counted_playable(self):
        record = json.loads((ROOT / "data/regions/sinnoh-progress.json").read_text("utf-8"))
        phase = record["intro_workstream"]
        self.assertEqual(phase["status"], "ORIGINAL_EVENTS_PREPARED_NOT_PLAYABLE")
        self.assertEqual(phase["complete"], 5)
        self.assertEqual(phase["total"], 8)
        self.assertEqual(phase["complete"],
                         sum(bool(item["complete"]) for item in phase["substeps"]))
        self.assertFalse(phase["native_verified"])
        self.assertFalse(phase["assets_verified"])
        self.assertTrue(phase["not_playable"])
        self.assertEqual(record["development"]["done"], 8)
        self.assertEqual(record["development"]["partial"], 7)
        self.assertEqual(record["development"]["pending"], 17)
        self.assertEqual(record["development"]["percent_complete"], 25)
        self.assertEqual({row["id"]: row["status"] for row in record["tasks"]
                          if row["id"] in ("S13", "S14")},
                         {"S13": "partial", "S14": "partial"})
        self.assertTrue(all(not row["complete"] or (
            row["evidence"] and (ROOT / row["evidence"]).is_file()
        ) for row in phase["substeps"]))
        spec = json.loads((ROOT / "data/regions/sinnoh-twinleaf-events.json").read_text("utf-8"))
        self.assertFalse(spec["approved_for_install"])
        self.assertFalse(spec["gameplay_verified"])
        self.assertTrue(all(m["map_id"] is None for m in spec["maps"]))
        panel = (ROOT / "docs/SINNOH_PROGRESSO.md").read_text("utf-8")
        self.assertIn("5/8", panel)
        self.assertGreaterEqual(panel.count("0/13 (0%)"), 3)

    def test_barry_pbs_is_prepared_but_starter_battle_is_still_locked(self):
        record = json.loads((ROOT / "data/regions/sinnoh-progress.json").read_text("utf-8"))
        barry = record["barry_pbs_workstream"]
        self.assertEqual(barry["status"], "PBS_DRAFT_CODE_READY_NATIVE_QA_PENDING")
        self.assertEqual((barry["complete"], barry["total"]), (4, 6))
        self.assertEqual(barry["complete"],
                         sum(bool(item["complete"]) for item in barry["substeps"]))
        self.assertFalse(barry["pbs_compiled"])
        self.assertFalse(barry["marker_created"])
        self.assertFalse(barry["game_playable"])
        for item in barry["substeps"]:
            if item["complete"]:
                self.assertTrue(item["evidence"])
                self.assertTrue((ROOT / item["evidence"]).is_file())
        self.assertEqual(record["intro_workstream"]["complete"], 5)
        self.assertFalse(record["intro_workstream"]["substeps"][6]["complete"])
        self.assertEqual(record["development"]["done"], 8)
        self.assertEqual(record["development"]["partial"], 7)
        self.assertEqual(record["phase_gates"]["playable_in_game_executable"], 0)
        panel = (ROOT / "docs/SINNOH_PROGRESSO.md").read_text("utf-8")
        self.assertIn("4/6", panel)
        self.assertIn("8/32 (25%)", panel)
        self.assertIn("0/13 (0%)", panel)

    def test_legacy_compatibility_qa_is_preparation_not_gameplay(self):
        record = json.loads((ROOT / "data/regions/sinnoh-progress.json").read_text("utf-8"))
        step = record["pilot_compat_qa_workstream"]
        self.assertEqual((step["complete"], step["total"]), (3, 6))
        self.assertEqual(step["complete"],
                         sum(bool(item["complete"]) for item in step["substeps"]))
        self.assertFalse(step["physical_map_ids_verified"])
        self.assertFalse(step["legacy_800_805_migrated"])
        self.assertFalse(step["pbs_compiled"])
        self.assertFalse(step["runtime_verified"])
        self.assertFalse(step["can_merge_into_multiregion"])
        self.assertEqual(record["development"]["done"], 8)
        self.assertEqual(record["phase_gates"]["technically_approved"], 0)
        self.assertEqual(record["phase_gates"]["playable_in_game_executable"], 0)
        for item in step["substeps"]:
            if item["complete"]:
                self.assertTrue((ROOT / item["evidence"]).is_file())
        panel = (ROOT / "docs/SINNOH_PROGRESSO.md").read_text("utf-8")
        self.assertIn("3/6", panel)
        self.assertIn("8/32", panel)

    def test_private_qa_pilot_overlay_is_only_code_preparation(self):
        record = json.loads((ROOT / "data/regions/sinnoh-progress.json").read_text("utf-8"))
        bundle = record["pilot_bundle_workstream"]
        self.assertEqual((bundle["complete"], bundle["total"]), (3, 6))
        self.assertEqual(bundle["complete"],
                         sum(bool(row["complete"]) for row in bundle["substeps"]))
        self.assertFalse(bundle["real_map_pack_processed"])
        self.assertFalse(bundle["pilot_built_in_game_exe"])
        self.assertFalse(bundle["pbs_compiled_in_game"])
        self.assertFalse(bundle["native_qa_approved"])
        self.assertFalse(bundle["main_game_modified"])
        self.assertFalse(bundle["can_install"])
        self.assertEqual(record["development"]["done"], 8)
        self.assertEqual(record["development"]["partial"], 7)
        self.assertEqual(record["phase_gates"]["playable_in_game_executable"], 0)
        self.assertTrue(all(not t["complete"] or (ROOT / t["evidence"]).is_file()
                            for t in bundle["substeps"]))
        panel = (ROOT / "docs/SINNOH_PROGRESSO.md").read_text("utf-8")
        self.assertIn("3/6", panel)
        self.assertIn("8/32 (25%)", panel)

    def test_planned_region_and_unverified_source_remain_blocked(self):
        registry = json.loads((ROOT / "site/public/data/regions.json").read_text("utf-8"))
        provenance = json.loads((ROOT / "data/regions/sinnoh-source.json").read_text("utf-8"))
        self.assertEqual(registry["regions"]["SINNOH"]["status"], "planned")
        self.assertFalse(provenance["import_control"]["imports_enabled"])
        self.assertEqual(provenance["progress"]["technical_approved"], 0)
        self.assertEqual(provenance["progress"]["native_playable_approved"], 0)


if __name__ == "__main__":
    unittest.main()
