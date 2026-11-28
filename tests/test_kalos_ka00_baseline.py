import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from qa.kalos import ka00_baseline as baseline

class KalosBaselineTests(unittest.TestCase):
    def test_project_claims_are_holds_not_allocations(self):
        report = baseline.static_controls()
        self.assertEqual(report["protected"]["JOHTO"]["end"], 699)
        self.assertEqual(report["protected"]["HOENN"]["start"], 700)
        self.assertEqual(report["protected"]["KANTO_CELADON_PR_395_CONSERVATIVE_HOLD"], [276,277,278,279])
        self.assertFalse(report["allocation_allowed"])
        self.assertFalse(report["four_digit_ids_verified"])

    def test_bad_historical_artifact_stops_before_deserialization(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset = Path(tmp) / "artifact.zip"
            asset.write_bytes(b"corrupted")
            with patch.object(baseline, "ANDROID_247_BYTES", len(b"corrupted")), patch.object(baseline, "scan_source") as scan:
                with self.assertRaisesRegex(ValueError, "SHA mismatch"):
                    baseline.file_report(asset, "android-247-historical")
            scan.assert_not_called()

    def test_verified_source_preserves_unbacked_and_orphan_ids_without_leaking_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset = Path(tmp) / "artifact.zip"
            content = b"synthetic, not a game"
            asset.write_bytes(content)
            fake = {
                "mapinfos_present": True, "file_count": 2, "mapinfos_declared_count": 2,
                "mapinfos_sha256": "a" * 64, "map_ids_occupied_or_declared": [1, 2, 3],
                "missing_map_file_ids": [2], "orphan_map_file_ids": [3],
                "maps": [{"id": n, "bytes": 1, "sha256": "b" * 64,
                          "mapinfo_name": "never publish caller names"} for n in (1, 3)],
            }
            with patch.object(baseline, "ANDROID_247_BYTES", len(content)), patch.object(
                baseline, "ANDROID_247_SHA256", hashlib.sha256(content).hexdigest()
            ), patch.object(baseline, "scan_source", return_value=fake), patch.object(baseline, "read_markers", return_value={}):
                report = baseline.file_report(asset, "android-247-historical")
            self.assertEqual(report["occupied_or_declared_ids"], [1, 2, 3])
            self.assertEqual(report["declared_without_file_ids"], [2])
            self.assertEqual(report["files_absent_from_index_ids"], [3])
            self.assertFalse(report["fresh_multiregion_verified"])
            self.assertFalse(report["physical_phone_tested"])
            self.assertFalse(report["allocation_allowed"])
            self.assertNotIn("never publish", json.dumps(report))
            self.assertNotIn(tmp, json.dumps(report))

    def test_region_collision_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Two regional"):
            baseline.ownership(
                {"blue-kanto-install.json": {"maps": {"1": 4}},
                 "blue-hoenn-install.json": {"maps": {"12": 4}}},
                {4}, {4})
        got = baseline.ownership({"blue-kanto-install.json": {"maps": {"1": 4}}}, {4,5}, {4,5})
        self.assertEqual(got["by_region"], {"KANTO": [4]})
        self.assertEqual(got["not_observed"], ["HOENN","JOHTO","SINNOH"])
        self.assertEqual(got["unattributed_physical"], [5])

    def test_wrong_decades_commit_is_not_a_baseline(self):
        with patch.object(baseline.subprocess, "check_output", return_value="f" * 40):
            with self.assertRaisesRegex(ValueError, "exact official commit"):
                baseline.file_report(Path("decades"), "decades-clean")

if __name__ == "__main__":
    unittest.main()
