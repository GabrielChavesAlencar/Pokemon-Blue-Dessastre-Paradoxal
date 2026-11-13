"""Pure offline safeguards for Johto ID allocation; never reads actual game saves."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    from plan_johto import plan
finally:
    sys.path.pop(0)

DIGEST = hashlib.sha256(b"locally verified archive").hexdigest()


def make_report():
    def row(num, name):
        return {"source_id": num, "name": name, "sha256": hashlib.sha256(name.encode()).hexdigest()}
    return {
        "schema": 1, "region": "JOHTO", "mode": "READ_ONLY_NO_INSTALL",
        "can_install": False, "maps": [row(3, "New Bark Town"), row(40, "Violet City"),
                                      row(72, "Johto Route 29")],
        "game": {"present": True, "existing_ids": [1, 301, 599, 600, 605],
                 "registered_ids": [610], "protected_hashes":
                     {"Data/System.rxdata": hashlib.sha256(b"native game").hexdigest()}},
        "source_archive_sha256": DIGEST, "archive_hash_pinned_and_verified": True,
        "missing_tileset_ids": [], "orphan_map_files": [], "missing_map_files": []
    }


def make_manifest():
    return {"schema": 1, "region": "JOHTO", "mapping_verified": True,
            "import_enabled": False,
            "source": {"archive_sha256": DIGEST},
            "maps": {"3": "JOHTO_NEW_BARK_TOWN", "72": "JOHTO_ROUTE_29"}}


class JohtoMapPlanTests(unittest.TestCase):
    def test_baseline_does_not_enable_unverified_johto(self):
        m = json.loads((ROOT / "data/regions/johto-source.json").read_text("utf-8"))
        report = make_report()
        # A real v1 archive has been audited, but a fake synthetic source
        # report must not be accepted as its matching Game.exe baseline.
        self.assertEqual(len(m["maps"]), 74)
        self.assertTrue(m["mapping_verified"])
        with self.assertRaisesRegex(ValueError, "Unverified"):
            plan(m, report)

    def test_allocates_above_all_existing_and_registered_ids(self):
        result = plan(make_manifest(), make_report())
        self.assertEqual(result["status"], "READY_FOR_GEOMETRY_PREVIEW")
        self.assertEqual(result["mapping"], {"3": 611, "72": 612})
        self.assertFalse(result["can_install"])
        self.assertEqual(result["symbols"]["3"], "JOHTO_NEW_BARK_TOWN")
        self.assertIn("Data/System.rxdata", result["protected_game_hashes"])

    def test_prior_mapping_is_frozen_even_if_new_source_id_is_lower(self):
        original = plan(make_manifest(), make_report())
        manifest = make_manifest()
        manifest["maps"]["40"] = "JOHTO_VIOLET_CITY"
        again = plan(manifest, make_report(), previous=original)
        self.assertEqual(again["mapping"], {"3": 611, "40": 613, "72": 612})
        self.assertEqual(again["mapping"]["72"], original["mapping"]["72"])
        self.assertEqual(plan(manifest, make_report(), previous=again)["mapping"], again["mapping"])

    def test_refuse_renumbering_or_removing_existing_johto_map(self):
        original = plan(make_manifest(), make_report())
        renamed = make_manifest()
        renamed["maps"]["3"] = "JOHTO_ANOTHER_TOWN"
        with self.assertRaisesRegex(ValueError, "symbolic"):
            plan(renamed, make_report(), previous=original)
        removed = make_manifest()
        del removed["maps"]["3"]
        with self.assertRaisesRegex(ValueError, "disappeared"):
            plan(removed, make_report(), previous=original)

    def test_conflicts_with_game_map_ids_abort_plan(self):
        original = plan(make_manifest(), make_report())
        report = make_report()
        report["game"]["existing_ids"].append(611)
        with self.assertRaisesRegex(ValueError, "conflict"):
            plan(make_manifest(), report, previous=original)

    def test_prevent_fake_or_corrupt_map_selection(self):
        fake = make_manifest()
        fake["maps"]["999"] = "JOHTO_FAKE"
        with self.assertRaisesRegex(ValueError, "Unverified"):
            plan(fake, make_report())
        fake = make_manifest()
        fake["maps"]["40"] = "JOHTO_ROUTE_29"
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            plan(fake, make_report())
        report = make_report()
        report["maps"][0]["sha256"] = "some-hash"
        with self.assertRaisesRegex(ValueError, "corrupt"):
            plan(make_manifest(), report)

    def test_no_game_or_invalid_source_is_blocked(self):
        report = make_report()
        report["game"]["present"] = False
        with self.assertRaisesRegex(ValueError, "snapshot"):
            plan(make_manifest(), report)
        report = make_report()
        report["mode"] = "GAME_INSTALL"
        with self.assertRaisesRegex(ValueError, "read-only"):
            plan(make_manifest(), report)

    def test_only_explicit_unselected_intro_mapinfo_can_be_missing(self):
        m = make_manifest()
        m["source"]["accepted_missing_mapinfo_ids"] = [1]
        report = make_report()
        report["missing_map_files"] = [1]
        result = plan(m, report)
        self.assertEqual(result["status"], "READY_FOR_GEOMETRY_PREVIEW")
        self.assertFalse(result["can_install"])

        report["missing_map_files"] = [1, 99]
        missing = plan(m, report)
        self.assertEqual(missing["status"], "BLOCKED")
        self.assertIn("MAPINFOS_MISMATCH", missing["blocking_reasons"])

        m["source"]["accepted_missing_mapinfo_ids"] = [3]
        with self.assertRaisesRegex(ValueError, "Invalid selected"):
            plan(m, report)

    def test_unverified_pack_cannot_get_ready_status(self):
        report = make_report()
        report["archive_hash_pinned_and_verified"] = False
        result = plan(make_manifest(), report)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("SOURCE_ARCHIVE_HASH_NOT_VERIFIED", result["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
