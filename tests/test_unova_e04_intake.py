"""E04: source intake is private, inert, idempotent and never a license."""
from __future__ import annotations
import contextlib
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import unova_e04_intake as intake


class UnovaE04SourceIntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="unova-e04-intake-")
        self.addCleanup(self.tmp.cleanup)
        self.project=Path(self.tmp.name)/"project"
        self.project.mkdir()
        self.downloads=Path(self.tmp.name)/"downloads"
        self.downloads.mkdir()
        self.src=self.downloads/"Pokemon_World_V18.zip"
        self.write_zip()
        self.credits=self.downloads/"Credits.txt"
        self.credits.write_text("Thanks to community artists, rights not implied.\n",encoding="utf-8")

    def write_zip(self,n=1):
        with zipfile.ZipFile(self.src,"w",zipfile.ZIP_DEFLATED) as z:
            z.writestr("World/Data/MapInfos.rxdata",b"test")
            z.writestr("World/Data/Tilesets.rxdata",b"test")
            for i in range(1,n+1):
                z.writestr("World/Data/Map%03d.rxdata"%i,b"not a real map")
            z.writestr("World/Graphics/Characters/N.png",b"not a real sprite")

    def target(self):
        return self.project/".blue-work/unova/sources/Pokemon_World_V18.zip"

    def test_01_valid_selected_zip_copied_privately_only(self):
        r=intake.intake(self.project,self.src)
        self.assertTrue(self.target().is_file())
        self.assertEqual(self.target().read_bytes(),self.src.read_bytes())
        self.assertTrue((self.project/".blue-work/unova/audit/e04-intake.json").is_file())
        self.assertFalse((self.project/"game").exists())
        self.assertFalse((self.project/"saves").exists())
        self.assertFalse(r["can_install"])
        self.assertFalse(r["source_origin_verified_by_author"])
        self.assertFalse(r["license_verified"])
        self.assertFalse(r["rights_per_asset_verified"])
        self.assertFalse(r["game_exe_tested"])
        self.assertIsNone(r["unova_map_count"])
        self.assertEqual(r["whole_donor_project_map_count"],1)

    def test_02_credits_selection_never_means_permission(self):
        r=intake.intake(self.project,self.src,self.credits)
        self.assertTrue(r["credits_present"])
        self.assertFalse(r["credits_are_reuse_permission"])
        self.assertFalse(r["license_verified"])
        self.assertEqual(r["credits_sha256"],hashlib.sha256(self.credits.read_bytes()).hexdigest())

    def test_03_without_credits_is_pending(self):
        r=intake.intake(self.project,self.src)
        self.assertFalse(r["credits_present"])
        self.assertIsNone(r["credits_sha256"])

    def test_04_repeated_identical_intake_is_idempotent(self):
        first=intake.intake(self.project,self.src,self.credits)
        before=self.target().read_bytes()
        second=intake.intake(self.project,self.src,self.credits)
        self.assertEqual(first,second)
        self.assertEqual(before,self.target().read_bytes())

    def test_05_different_zip_cannot_replace_previous(self):
        intake.intake(self.project,self.src)
        before=self.target().read_bytes()
        self.write_zip(n=2)
        with self.assertRaises(ValueError):
            intake.intake(self.project,self.src)
        self.assertEqual(before,self.target().read_bytes())

    def test_06_corrupt_zip_does_not_copy(self):
        self.src.write_bytes(b"corrupt zip")
        with self.assertRaises(zipfile.BadZipFile):
            intake.intake(self.project,self.src)
        self.assertFalse(self.target().exists())

    def test_07_oversize_or_bin_credits_block_before_copy(self):
        self.credits.write_bytes(b"\x00bad")
        with self.assertRaises(ValueError):
            intake.intake(self.project,self.src,self.credits)
        self.assertFalse(self.target().exists())

    def test_08_zip_symlink_blocked(self):
        link=self.downloads/"source-alias.zip"
        try:
            link.symlink_to(self.src)
        except OSError:
            self.skipTest("symlink unavailable")
        with self.assertRaises(ValueError):
            intake.intake(self.project,link)

    def test_09_symlink_output_directory_blocked(self):
        work=self.project/".blue-work"
        other=Path(self.tmp.name)/"other"
        other.mkdir()
        try:
            work.symlink_to(other,target_is_directory=True)
        except OSError:
            self.skipTest("symlink unavailable")
        with self.assertRaises(ValueError):
            intake.intake(self.project,self.src)
        self.assertFalse((other/"unova").exists())

    def test_10_symlink_destination_file_blocked(self):
        target=self.target()
        target.parent.mkdir(parents=True)
        outside=Path(self.tmp.name)/"outside"
        outside.write_bytes(b"important")
        try:
            target.symlink_to(outside)
        except OSError:
            self.skipTest("symlink unavailable")
        with self.assertRaises(ValueError):
            intake.intake(self.project,self.src)
        self.assertEqual(outside.read_bytes(),b"important")

    def test_11_local_private_zip_idempotent(self):
        r=intake.intake(self.project,self.src)
        second=intake.intake(self.project,self.target())
        self.assertEqual(r["archive_sha256"],second["archive_sha256"])
        self.assertTrue(self.target().is_file())

    def test_12_reject_bad_extension_before_copy(self):
        bad=self.downloads/"game.exe"
        bad.write_bytes(self.src.read_bytes())
        with self.assertRaises(ValueError):
            intake.intake(self.project,bad)
        self.assertFalse(self.target().exists())

    def test_13_report_cannot_be_overwritten_differently(self):
        intake.intake(self.project,self.src)
        report=self.project/".blue-work/unova/audit/e04-intake.json"
        before=json.loads(report.read_text("utf-8"))
        changed=dict(before,status="ALREADY_INSTALLED")
        report.write_text(json.dumps(changed))
        with self.assertRaises(ValueError):
            intake.intake(self.project,self.src)
        self.assertEqual(json.loads(report.read_text("utf-8"))["status"],"ALREADY_INSTALLED")

    def test_14_cli_absent_source_does_not_create_game(self):
        result=intake.main(["--project",str(self.project)])
        self.assertEqual(result,2)
        self.assertFalse((self.project/"game").exists())

    def test_15_selected_zip_has_no_automatic_author_hash(self):
        r=intake.intake(self.project,self.src,self.credits)
        self.assertFalse(r["published_author_hash_matched"])
        self.assertEqual(r["status"],"ZIP_PRESENT_AND_METADATA_VALIDATED_ORIGIN_NOT_ATTESTED")
        self.assertIn("source_post",r)

if __name__=="__main__":
    unittest.main()
