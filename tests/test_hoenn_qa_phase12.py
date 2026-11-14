"""QA12: integrated Hoenn technical release gate must fail closed."""
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/regions"))

from hoenn_qa_phase12 import (
    AUDITS, PLATFORMS, NATIVE_SCENARIOS,
    accepted_reports, audit_generated, backlog, manual_template,
    report_filename, verify_copy,
)
from pilot_hoenn import SOURCE_MAPS, UPSTREAM


def valid_reports() -> dict[str, dict]:
    reports = {}
    for phase, _key, status in AUDITS:
        row = {"region": "HOENN", "status": status, "errors": [],
               "native_game_exe_approved": False}
        if phase == "01":
            row["copy"] = {"maps_present": 199,
                           "distinct_save_profile": "Hoenn QA Fase12"}
        elif phase == "02":
            row["maps_read"] = 199
        elif phase == "07":
            row["gym_source_map_ids"] = list(range(8))
        elif phase == "09":
            row["pbs_reference_party_sizes"] = [5, 5, 5, 5, 6]
        elif phase == "10":
            row["expected_neighbor_unlocks"] = ["JOHTO", "SINNOH"]
        elif phase == "11":
            row["maps_with_ptbr_display_label"] = 199
            row["map_bgms_assigned"] = 199
        reports[phase] = row
    return reports


def valid_manifest() -> dict:
    return {
        "region": "HOENN", "source_commit": UPSTREAM,
        "maps": {mid: 700 + i for i, mid in enumerate(SOURCE_MAPS)},
        "qa3": {"source_events": {"unimplemented_source_event_candidates": [
            {"name": "Unreviewed original NPC"}
        ]}},
        "qa4": {"source_obstacles_needing_review": [
            {"source_map_id": 250}
        ]},
        "stage10": {"boss_battle_art_placeholder": {
            "Sidney": True, "Wallace": False
        }},
        **{f"qa{i}": {} for i in range(5, 12)},
    }


class IntegratedHoennQA12Tests(unittest.TestCase):
    def test_all_eleven_stage_reports_required(self):
        rows = accepted_reports(valid_reports())
        self.assertEqual(len(rows), 11)
        self.assertEqual(rows[-1]["phase"], "11/12")
        self.assertIn("STATICALLY_VERIFIED", rows[-1]["status"])

    def test_cannot_skip_any_failed_or_missing_stage(self):
        for phase, _, _ in AUDITS:
            rows = valid_reports()
            rows.pop(phase)
            with self.subTest(phase=phase), self.assertRaisesRegex(ValueError, "11 relatórios"):
                accepted_reports(rows)
        rows = valid_reports()
        rows["08"]["status"] = "BLOCKED"
        with self.assertRaisesRegex(ValueError, "Fase08"):
            accepted_reports(rows)

    def test_integrated_gate_rejects_claims_of_native_approval(self):
        for flag in ("native_game_exe_approved", "native_approved",
                     "android_approved", "gameplay_accepted",
                     "phase_fully_approved", "game_exe_tested_here"):
            rows = valid_reports()
            rows["09"][flag] = True
            with self.subTest(flag=flag), self.assertRaisesRegex(ValueError, "nativa"):
                accepted_reports(rows)

    def test_regional_and_stage_specific_proofs_are_mandatory(self):
        for phase, key, value in (
            ("01", "distinct_save_profile", "other"),
            ("02", "maps_read", 198),
            ("07", "gym_source_map_ids", [1,2,3]),
            ("09", "pbs_reference_party_sizes", [6,5,5,5,5]),
            ("10", "expected_neighbor_unlocks", ["KANTO"]),
            ("11", "map_bgms_assigned", 198),
        ):
            rows = valid_reports()
            target = rows[phase]["copy"] if phase == "01" else rows[phase]
            target[key] = value
            with self.subTest(phase=phase, key=key), self.assertRaises(ValueError):
                accepted_reports(rows)

    def test_manifest_accepts_builder_int_and_json_str_map_keys(self):
        report = valid_manifest()
        first = audit_generated(report)
        report["maps"] = {str(key): val for key,val in report["maps"].items()}
        second = audit_generated(report)
        self.assertEqual(first, second)
        self.assertEqual(first["maps_expected"], 199)
        self.assertTrue(first["all_native_scenarios_pending"])
        self.assertFalse(first["native_story_approved"])
        self.assertFalse(first["all_12_phases_playable_approved"])
        self.assertEqual(first["unresolved_backlog"]["unimplemented_original_npc_trainer_sign_candidates"], 1)
        self.assertEqual(first["unresolved_backlog"]["stage10_boss_graphics_using_placeholders"], ["Sidney"])

    def test_duplicate_or_unknown_source_map_rejected(self):
        m = valid_manifest()
        keys = list(m["maps"])
        m["maps"][keys[-1]] = m["maps"][keys[0]]
        with self.assertRaisesRegex(ValueError, "199"):
            audit_generated(m)
        m = valid_manifest()
        m["maps"].pop(keys[0])
        m["maps"][999] = 705
        with self.assertRaisesRegex(ValueError, "199"):
            audit_generated(m)

    def test_missing_source_candidate_backlog_never_silently_dropped(self):
        m=valid_manifest()
        m["qa3"]["source_events"]["unimplemented_source_event_candidates"] = None
        with self.assertRaisesRegex(ValueError, "backlog"):
            backlog(m)
        m=valid_manifest()
        m["qa4"]["source_obstacles_needing_review"] = None
        with self.assertRaisesRegex(ValueError, "backlog"):
            backlog(m)

    def test_checklist_is_both_platforms_with_no_auto_pass(self):
        template = manual_template()
        self.assertEqual(template["kind"], "MANUAL_NATIVE_QA_ONLY")
        self.assertIs(template["native_approved"], False)
        cases = template["tests"]
        self.assertEqual(len(cases), len(NATIVE_SCENARIOS)*2)
        self.assertEqual({x["platform"] for x in cases}, set(PLATFORMS))
        self.assertEqual(len({x["id"] for x in cases}), len(cases))
        self.assertTrue(all(x["status"] == "pending_native" and not x["evidence"] for x in cases))
        self.assertTrue(any(x["scope"].startswith("Salvar") for x in cases))

    def test_all_artifact_report_names_are_separate(self):
        names = [report_filename(key) for _phase,key,_status in AUDITS]
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(name.startswith("hoenn-qa-fase12-") for name in names))
        self.assertNotIn("hoenn-qa-fase12-report.json", names)

    def test_private_copy_gate_rejects_any_external_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, ".blue-work"):
                verify_copy(Path(tmp))


if __name__ == "__main__":
    unittest.main()
