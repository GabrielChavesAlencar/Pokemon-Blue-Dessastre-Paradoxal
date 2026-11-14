"""Read-only regression tests for the multi-region detonado audit."""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/regions/audit_detonados_content.py"
spec = importlib.util.spec_from_file_location("audit_detonados_content", MODULE)
audit_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit_module
spec.loader.exec_module(audit_module)


class DetonadoContentAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit_module.audit(ROOT)

    def test_manifest_is_explicitly_reference_only(self):
        manifest = json.loads((ROOT / audit_module.MANIFEST).read_text(encoding="utf-8"))
        audit_module.validate_manifest(manifest, ROOT)
        for region in manifest["regions"].values():
            self.assertEqual(len(region["leaders"]), 8)
            for area in region["areas"]:
                self.assertNotIn("map_id", area)
                self.assertNotIn("rate", area)
                self.assertNotIn("levels", area)
                self.assertTrue(set(area.get("special_encounters", [])).isdisjoint(area["reference_species"]))

    def test_all_four_regions_have_review_entries(self):
        self.assertEqual(set(self.report["regions"]), {"KANTO", "JOHTO", "HOENN", "SINNOH"})
        for record in self.report["regions"].values():
            self.assertGreater(record["reference_habitats_reviewed"], 0)
            self.assertTrue(all(row["gameplay_verified"] is False for row in record["habitats"]))
            self.assertTrue(all(row["native_battle_verified"] is False for row in record["leaders"]))

    def test_kanto_route_22_original_species_are_present(self):
        records = self.report["regions"]["KANTO"]["habitats"]
        route = next(row for row in records if row["area"] == "Route 22")
        self.assertTrue(route["catalog_locations"])
        self.assertEqual(route["reference_species_not_in_catalog"], [])
        self.assertEqual(route["status"], "CATALOG_SPECIES_PRESENT_REVIEW_NATIVE")

    def test_johto_route_29_existing_species_are_not_marked_missing(self):
        records = self.report["regions"]["JOHTO"]["habitats"]
        route = next(row for row in records if row["area"] == "Route 29")
        self.assertTrue(route["catalog_locations"])
        self.assertEqual(route["reference_species_not_in_catalog"], [])

    def test_hoenn_route_102_is_preserved(self):
        records = self.report["regions"]["HOENN"]["habitats"]
        route = next(row for row in records if row["area"] == "Route 102")
        self.assertTrue(route["catalog_locations"])
        self.assertEqual(route["reference_species_not_in_catalog"], [])

    def test_sinnoh_remains_unverified_without_gameplay_catalog(self):
        records = self.report["regions"]["SINNOH"]["habitats"]
        self.assertTrue(all(row["status"] == "NO_GAMEPLAY_CATALOG" for row in records))
        self.assertEqual(
            len(self.report["regions"]["SINNOH"]["leaders_absent_from_published_catalog"]), 8
        )

    def test_location_names_and_translation(self):
        self.assertTrue(audit_module.location_matches("Route 22", "Rota 22 — acesso ao Plateau"))
        self.assertTrue(audit_module.location_matches("Sprout Tower", "Torre Sprout"))
        self.assertTrue(audit_module.location_matches("Mt. Moon", "Mt. Moon — 1F"))
        self.assertFalse(audit_module.location_matches("Route 22", "Route 23"))


if __name__ == "__main__":
    unittest.main()
