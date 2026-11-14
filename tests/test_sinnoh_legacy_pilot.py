"""Legacy Sinnoh standalone source must not be merged with shared Johto IDs."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_sinnoh_legacy_pilot import (
    LEGACY_PY, LEGACY_RB, NEW_RB, PLAN_JSON, audit_repo, examine,
)


def inputs():
    return (
        (ROOT / LEGACY_PY).read_text("utf-8"),
        (ROOT / LEGACY_RB).read_text("utf-8"),
        (ROOT / NEW_RB).read_text("utf-8"),
        json.loads((ROOT / PLAN_JSON).read_text("utf-8")),
    )


class SinnohLegacyPilotTests(unittest.TestCase):
    def test_real_legacy_pilot_is_detected_without_running_donor_assets(self):
        report = audit_repo(ROOT)
        self.assertEqual(report["mode"], "READ_ONLY_LEGACY_RECONCILIATION")
        self.assertEqual(report["legacy"]["legacy_map_ids"],
                         [800, 801, 802, 803, 804, 805])
        self.assertEqual(report["legacy_ids_overlapping_johto"],
                         [800, 801, 802, 803, 804, 805])
        self.assertEqual(report["legacy"]["legacy_start_candidate_map_id"], 801)
        self.assertEqual(report["legacy"]["legacy_start_xy"], [29, 5])
        self.assertEqual(report["legacy_starter_selection"], "ROWAN_DIALOG")
        self.assertEqual(report["new_story_starter_selection"],
                         "THREE_PHYSICAL_BALL_EVENTS")
        self.assertEqual(report["new_story_planned_maps"], 9)
        self.assertEqual(len(report["input_sha256"]), 4)
        for key in ("can_merge_into_shared_campaign", "safe_to_install",
                    "runtime_qa_completed", "migration_completed",
                    "new_map_ids_allocated", "legacy_source_rights_verified"):
            self.assertFalse(report[key], key)

    def test_johto_collision_is_not_labeled_as_safety_in_standalone_copy(self):
        code, old_ruby, new_ruby, spec = inputs()
        result = examine(code, old_ruby, new_ruby, spec,
                         reserved_from=600, reserved_through=700)
        self.assertEqual(result["legacy_ids_overlapping_johto"], [])
        self.assertFalse(result["can_merge_into_shared_campaign"])
        self.assertFalse(result["runtime_qa_completed"])

    def test_refuses_legacy_source_with_retargeted_or_dropped_ids(self):
        code, old_ruby, new_ruby, spec = inputs()
        for poisoned in (
            code.replace("range(800, 806)", "range(800, 804)"),
            code.replace("dict(zip(NAMES, range(800, 806)))",
                         "{32: 5, 102: 6, 42: 7}"),
        ):
            with self.subTest(source=poisoned[:50]):
                with self.assertRaisesRegex(ValueError, "MapIDs|Contagem"):
                    examine(poisoned, old_ruby, new_ruby, spec)

    def test_refuses_false_approval_and_invented_map_ids(self):
        code, old_ruby, new_ruby, spec = inputs()
        spec["approved_for_install"] = True
        with self.assertRaisesRegex(ValueError, "indevidamente"):
            examine(code, old_ruby, new_ruby, spec)
        _, _, _, spec = inputs()
        spec["maps"][0]["map_id"] = 500
        with self.assertRaisesRegex(ValueError, "IDs supostamente reais"):
            examine(code, old_ruby, new_ruby, spec)

    def test_detects_old_vs_new_starter_workflow_mismatch(self):
        code, old_ruby, new_ruby, spec = inputs()
        with self.assertRaisesRegex(ValueError, "diálogo"):
            examine(code, old_ruby.replace("names + [", "something_else"),
                    new_ruby, spec)
        with self.assertRaisesRegex(ValueError, "três Poké Bolas"):
            examine(code, old_ruby,
                    new_ruby.replace("choose_starter_from_ball",
                                     "choose_starter_dialog"), spec)


if __name__ == "__main__":
    unittest.main()
