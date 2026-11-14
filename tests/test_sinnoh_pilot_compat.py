"""Fail-closed static reconciliation of the old Sinnoh pilot and Johto range."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_sinnoh_pilot_compat import audit_compat, scan_project


def sources():
    return [
        (ROOT / "scripts/regions/pilot_sinnoh.py").read_text("utf-8"),
        (ROOT / "scripts/regions/SinnohPreview.rb").read_text("utf-8"),
        (ROOT / "scripts/battle_polish/TitleKanto.rb").read_text("utf-8"),
        (ROOT / "scripts/regions/SinnohPilot.rb").read_text("utf-8"),
    ]


class SinnohPilotCompatibilityTests(unittest.TestCase):
    def test_legacy_ids_are_reported_as_johto_collision_not_remapped(self):
        result = scan_project(ROOT)
        self.assertEqual(result["legacy_source_ids"], [32, 102, 42, 43, 104, 96])
        self.assertEqual(result["legacy_destination_ids"], [800, 801, 802, 803, 804, 805])
        self.assertEqual(result["overlap_johto_reserved"],
                         [800, 801, 802, 803, 804, 805])
        self.assertIsNone(result["overlap_physical_installed"])
        self.assertFalse(result["multi_region_merge_safe"])
        self.assertFalse(result["isolated_legacy_pilot_tested"])
        self.assertTrue(result["no_map_ids_allocated"])
        self.assertTrue(result["no_saves_migrated"])
        self.assertTrue(result["no_files_written"])
        self.assertEqual(result["legacy_start_choice"], "ROWAN_DIALOG")
        self.assertEqual(result["new_start_choice"], "THREE_PHYSICAL_BALLS")

    def test_physical_ids_are_optional_but_never_invented(self):
        report = audit_compat(*sources(), installed_ids=[1, 2, 801, 950])
        self.assertEqual(report["overlap_physical_installed"], [801])
        self.assertEqual(report["overlap_johto_reserved"],
                         [800, 801, 802, 803, 804, 805])
        with self.assertRaisesRegex(ValueError, "IDs instalados"):
            audit_compat(*sources(), installed_ids=[1, 1])
        with self.assertRaisesRegex(ValueError, "IDs instalados"):
            audit_compat(*sources(), installed_ids=["801"])

    def test_migrated_ids_must_be_reaudited_not_guessed(self):
        old, preview, title, new = sources()
        changed = old.replace("range(800, 806)", "range(1050, 1056)")
        result = audit_compat(changed, preview, title, new)
        self.assertEqual(result["legacy_destination_ids"],
                         [1050, 1051, 1052, 1053, 1054, 1055])
        self.assertEqual(result["overlap_johto_reserved"], [])
        self.assertFalse(result["multi_region_merge_safe"])
        self.assertTrue(result["no_map_ids_allocated"])

    def test_rejects_dynamic_or_unknown_id_allocation(self):
        old, preview, title, new = sources()
        with self.assertRaisesRegex(ValueError, "remapeamento legado"):
            audit_compat(old.replace("IDS = dict(zip(NAMES, range(800, 806)))",
                                      "IDS = from_database()"),
                         preview, title, new)
        with self.assertRaisesRegex(ValueError, "incompleto"):
            audit_compat(old.replace("range(800, 806)", "range(800, 804)"),
                         preview, title, new)

    def test_missing_legacy_or_new_event_handlers_block_audit(self):
        old, preview, title, new = sources()
        with self.assertRaisesRegex(ValueError, "piloto antigo"):
            audit_compat(old.replace("BlueSinnohPreview.rowan",
                                     "UnverifiedForeignScript.rowan"),
                         preview, title, new)
        with self.assertRaisesRegex(ValueError, "três bolas"):
            audit_compat(old, preview, title,
                         new.replace("choose_starter_from_ball", "fake_starter_choice"))
        with self.assertRaisesRegex(ValueError, "Testar Sinnoh"):
            audit_compat(old, preview, title.replace("Testar Sinnoh", "Unknown region"), new)


if __name__ == "__main__":
    unittest.main()
