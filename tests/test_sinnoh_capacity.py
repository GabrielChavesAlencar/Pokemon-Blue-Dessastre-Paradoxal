"""Sinnoh capacity checker must never allocate native, Johto or Hoenn IDs."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from plan_sinnoh_capacity import capacity


def report(ids=(1, 2, 3), native=(1, 2, 600, 681, 999)):
    return {
        "schema": 1, "region": "SINNOH", "mode": "READ_ONLY_INERT_RMXP",
        "import_allowed": False, "source_map_ids": list(ids),
        "native": {"status": "LOCAL_READ_ONLY", "occupied_ids": list(native)},
    }


class SinnohCapacityTests(unittest.TestCase):
    def test_never_allocates_slots_and_preserves_johto_600_999(self):
        result = capacity(report())
        self.assertEqual(result["mapping"], {})
        self.assertFalse(result["safe_to_allocate"])
        self.assertEqual(result["protected_johto_range"], [600, 999])
        self.assertFalse(result["four_digit_ids_verified_on_runtime"])
        self.assertFalse(result["hoenn_reserved_ids_fully_audited"])
        self.assertTrue(all(i < 600 for i in result["provisional_unclaimed_legacy_ids"]))
        self.assertNotIn(1, result["provisional_unclaimed_legacy_ids"])
        self.assertNotIn(2, result["provisional_unclaimed_legacy_ids"])

    def test_detects_shortfall_without_leaking_into_johto(self):
        remaining = tuple(range(1, 600))
        result = capacity(report(ids=(1, 2, 3), native=remaining))
        self.assertEqual(result["upper_bound_unclaimed_ids_at_or_below_999"], 0)
        self.assertEqual(result["minimum_legacy_id_shortfall_if_only_these_ids_were_available"], 3)
        self.assertEqual(result["mapping"], {})

    def test_requires_local_baseline_not_fabricated(self):
        missing = report()
        missing["native"]["status"] = "NOT_CHECKED"
        with self.assertRaisesRegex(ValueError, "game/Data"):
            capacity(missing)
        absent = report()
        absent["native"]["occupied_ids"] = None
        with self.assertRaisesRegex(ValueError, "inventariados"):
            capacity(absent)

    def test_rejects_unverified_audit(self):
        mocked = report()
        mocked["mode"] = "ZIP_METADATA_ONLY"
        with self.assertRaisesRegex(ValueError, "inerte"):
            capacity(mocked)
        mocked = report()
        mocked["import_allowed"] = True
        with self.assertRaisesRegex(ValueError, "inerte"):
            capacity(mocked)

    def test_rejects_duplicated_and_invalid_source_ids(self):
        with self.assertRaisesRegex(ValueError, "repetida"):
            capacity(report(ids=(1, 1, 2)))
        with self.assertRaisesRegex(ValueError, "repetida"):
            capacity(report(ids=(0, 2)))


if __name__ == "__main__":
    unittest.main()
