"""G01: synthetic metadata-only B09 receipt, strict failure and privacy tests."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_g01_b09_receipt as g01


class G01ReceiptTests(unittest.TestCase):
    @staticmethod
    def contract():
        return {"region": "SINNOH", "stage": "B09",
                "expected_installed_native_map_count": 648,
                "expected_sinnoh_terrain_maps_in_clone": 54,
                "expected_qa_clone_map_count": 702, "expected_png_count": 14,
                "can_install_live_game": False, "can_mark_native_playable": False,
                "phase_b_approved": 0}

    @staticmethod
    def receipt():
        return {"status": g01.STATUS, "relative_path": g01.STAGE_BASE + "a"*16,
                "files_reused": 999, "files_copied": 68, "files_repaired": 1,
                "native_file_count": 1000, "sinnoh_overlay_files": 70,
                "map_ids_clone_total": 702, "saves_copied": False,
                "game_exe_executed": False, "safe_to_launch": False,
                "phase_b_approved": 0, "r07_complete": False,
                "b08_maps_validated": 54, "b08_pngs_validated": 14,
                "b08_nonzero_terrain_cells": 484722,
                "future_reservations_verified": False, "native_game_tested": False,
                "joiplay_tested": False, "can_install_live_game": False}

    @staticmethod
    def dry_run():
        return {"status": "B09_DRY_RUN_NO_FILES_WRITTEN", "plan_sha256": "a"*64,
                "native_files_count": 1000, "overlay_files_count": 70,
                "estimated_bytes": 1500000, "expected_map_count": 702,
                "excluded_private_files": 4,
                "game_exe_will_be_copied_but_not_launched": True,
                "source_game_untouched": True, "phase_b_approved": 0,
                "b08_maps_validated": 54, "b08_pngs_validated": 14,
                "b08_nonzero_terrain_cells": 484722,
                "future_reservations_verified": False, "native_game_tested": False,
                "joiplay_tested": False, "can_install_live_game": False,
                "r07_complete": False}

    def test_01_valid_receipt_is_only_metadata(self):
        result = g01.audit_receipt(self.receipt(), self.contract())
        self.assertEqual(result["status"], "B09_RECEIPT_METADATA_CONSISTENT_NOT_PLAYABLE")
        self.assertEqual(result["logical_plan_entries"], 1070)
        self.assertEqual(result["accounted_unique_file_operations"], 1068)
        self.assertFalse(result["receipt_authenticity_proven"])
        self.assertFalse(result["linked_to_supplied_dry_run"])
        self.assertFalse(result["safe_to_launch"])
        self.assertEqual(result["phase_b_approved"], 0)
        self.assertNotIn("relative_path", result)

    def test_02_valid_sha_binding_does_not_certify_clone(self):
        result = g01.audit_receipt(self.receipt(), self.contract(), self.dry_run())
        self.assertTrue(result["linked_to_supplied_dry_run"])
        self.assertFalse(result["private_clone_independently_audited"])

    def test_03_missing_and_extra_fields_fail_closed(self):
        for change in ("missing", "extra"):
            receipt = self.receipt()
            if change == "missing": del receipt["files_repaired"]
            else: receipt["secret_path"] = "private"
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "SINNOH_G01_BLOCKED"):
                g01.audit_receipt(receipt, self.contract())

    def test_04_safety_flags_must_be_literal_false(self):
        for field in g01.FALSE_RECEIPT:
            receipt = self.receipt()
            receipt[field] = True
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, field):
                g01.audit_receipt(receipt, self.contract())

    def test_05_false_status_and_phase_gate_rejected(self):
        for field, value in (("status", "PLAYABLE"),
                             ("phase_b_approved", 1), ("phase_b_approved", False)):
            receipt = self.receipt()
            receipt[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                g01.audit_receipt(receipt, self.contract())

    def test_06_corrupt_numbers_rejected(self):
        for field, value in (("files_reused", 1000), ("files_copied", -1),
                             ("files_repaired", True), ("native_file_count", 1),
                             ("sinnoh_overlay_files", 69), ("map_ids_clone_total", 703),
                             ("b08_maps_validated", 53), ("b08_pngs_validated", 13),
                             ("b08_nonzero_terrain_cells", 484721)):
            receipt = self.receipt()
            receipt[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                g01.audit_receipt(receipt, self.contract())

    def test_07_reject_absolute_traversal_and_unapproved_paths(self):
        paths = (r"C:\Temp\clone", "/tmp/clone", "../native-" + "a"*16,
                 g01.STAGE_BASE + "a"*16 + "/../save",
                 ".blue-work/sinnoh-b08-qa/native-" + "a"*16,
                 g01.STAGE_BASE + "A"*16)
        for path in paths:
            receipt = self.receipt()
            receipt["relative_path"] = path
            with self.subTest(path=path), self.assertRaises(ValueError):
                g01.audit_receipt(receipt, self.contract())

    def test_08_dry_run_sha_or_metadata_must_match(self):
        for field, value in (("plan_sha256", "b"*64),
                             ("native_files_count", 1001),
                             ("overlay_files_count", 69),
                             ("expected_map_count", 701),
                             ("source_game_untouched", False)):
            dry = self.dry_run()
            dry[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                g01.audit_receipt(self.receipt(), self.contract(), dry)

    def test_09_dry_run_false_approval_rejected(self):
        for field in g01.FALSE_DRY_RUN:
            dry = self.dry_run()
            dry[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                g01.audit_receipt(self.receipt(), self.contract(), dry)

    def test_10_contract_cannot_override_native_approval(self):
        for field, value in (("expected_qa_clone_map_count", 703),
                             ("can_install_live_game", True),
                             ("can_mark_native_playable", True),
                             ("phase_b_approved", True)):
            contract = self.contract()
            contract[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                g01.audit_receipt(self.receipt(), contract)

    def test_11_invalid_json_missing_large_symlink_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            broken = base / "broken.json"
            broken.write_text("{broken", encoding="utf-8")
            with self.assertRaises(ValueError): g01.read_json(broken)
            with self.assertRaises(ValueError): g01.read_json(base / "missing.json")
            big = base / "large.json"
            big.write_text(" " * 65537, encoding="utf-8")
            with self.assertRaises(ValueError): g01.read_json(big)
            link = base / "link.json"
            try:
                link.symlink_to(broken)
            except (OSError, NotImplementedError):
                pass
            else:
                with self.assertRaises(ValueError): g01.read_json(link)

    def test_12_distinct_synthetic_recovery_counts_reconcile(self):
        receipt = self.receipt()
        receipt.update(files_reused=1200, files_copied=366,
                       files_repaired=2, native_file_count=1500)
        result = g01.audit_receipt(receipt, self.contract())
        self.assertEqual(result["accounted_unique_file_operations"], 1568)
        self.assertEqual(result["logical_plan_entries"], 1570)
        self.assertEqual(result["expected_overlay_replacements"], 2)
        self.assertFalse(result["private_clone_independently_audited"])

    def test_13_output_cannot_leak_relative_path_or_user_secrets(self):
        result = json.dumps(g01.audit_receipt(self.receipt(), self.contract()))
        self.assertNotIn("relative_path", result)
        self.assertNotIn(g01.STAGE_BASE, result)
        self.assertNotIn("Game.exe", result)
        self.assertNotIn("C:\\Users", result)

    def test_14_input_never_mutated(self):
        receipt = self.receipt()
        original = copy.deepcopy(receipt)
        g01.audit_receipt(receipt, self.contract(), self.dry_run())
        self.assertEqual(receipt, original)


if __name__ == "__main__":
    unittest.main()
