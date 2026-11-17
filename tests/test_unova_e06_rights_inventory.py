"""E06 rights inventory tests: assets remain pending even with Credits.txt."""
from __future__ import annotations
import copy
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_e06_rights_inventory as rights


class RightsInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="unova-rights-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.folder=self.root/".blue-work/unova/sources"
        self.folder.mkdir(parents=True)
        self.source=self.folder/"Pokemon_World_V18.zip"
        self.credits=self.folder/"Credits.txt"
        self.members={
            "World/Data/MapInfos.rxdata":b"infos",
            "World/Data/Tilesets.rxdata":b"tiles",
            "World/Data/Map001.rxdata":b"map",
            "World/Graphics/Characters/N.png":b"png",
            "World/Graphics/Tilesets/City.png":b"png",
            "World/Audio/BGM/N.mp3":b"audio",
            "World/PBS/trainers.txt":b"trainers",
            "World/Plugins/legacy.rb":b"scripts",
            "World/Game.exe":b"never executed",
        }
        self.makezip()

    def makezip(self):
        with zipfile.ZipFile(self.source,"w") as z:
            for name,data in self.members.items():
                z.writestr(name,data)

    def test_01_asset_groups_are_pending_not_approved(self):
        report=rights.inspect(self.root,self.source)
        self.assertEqual(report["whole_donor_project_map_count"],1)
        self.assertEqual(report["classified_asset_count"],8)
        self.assertFalse(report["all_assets_rights_cleared"])
        self.assertFalse(report["can_install"])
        self.assertFalse(report["game_or_saves_modified"])
        self.assertFalse(report["game_exe_tested"])
        self.assertFalse(report["credits"]["credits_file_present"])
        self.assertIn("audio_bgm_bgs",{row["category"] for row in report["assets"]})
        self.assertIn("character_sprites",{row["category"] for row in report["assets"]})
        self.assertNotIn("World/Game.exe",{row["source_path"] for row in report["assets"]})
        self.assertTrue(all(row["rights_status"]=="REVIEW_REQUIRED_NOT_LICENSED" and
                            not row["can_redistribute"] and not row["approved_for_game"]
                            for row in report["assets"]))

    def test_02_credits_file_does_not_grant_license(self):
        self.credits.write_text("Author A: credits, not distribution permission\n",encoding="utf-8")
        report=rights.inspect(self.root,self.source)
        self.assertTrue(report["credits"]["credits_file_present"])
        self.assertEqual(report["credits"]["credits_lines"],1)
        self.assertFalse(report["credits"]["credits_are_reuse_permission"])
        self.assertFalse(report["redistribution_approved"])
        self.assertFalse(report["license_verified"])
        self.assertFalse(any(row["approved_for_game"] for row in report["assets"]))

    def test_03_external_credits_path_blocked(self):
        outside=self.root/"Credits.txt"
        outside.write_text("x")
        with self.assertRaises(ValueError):
            rights.credits_status(self.root,outside)

    def test_04_symlink_credits_blocked(self):
        outside=self.root/"outside"
        outside.write_text("x")
        try:
            self.credits.symlink_to(outside)
        except OSError:
            self.skipTest("symlink unavailable")
        with self.assertRaises(ValueError):
            rights.inspect(self.root,self.source)

    def test_05_missing_donor_zip_blocks(self):
        self.source.unlink()
        with self.assertRaises(ValueError):
            rights.inspect(self.root,self.source)

    def test_06_zip_traversal_blocks(self):
        self.members["../escape"]=b"bad"
        self.makezip()
        with self.assertRaises(ValueError):
            rights.inspect(self.root,self.source)

    def test_07_no_unverified_executables_in_game(self):
        report=rights.inspect(self.root,self.source)
        self.assertEqual(report["all_file_count_in_zip"],9)
        self.assertFalse((self.root/"game").exists())
        self.assertFalse((self.root/"saves").exists())

    def test_08_report_write_is_private_and_idempotent(self):
        r=rights.inspect(self.root,self.source)
        output=rights.save(self.root,r)
        before=output.read_bytes()
        self.assertTrue(output.is_relative_to(self.root/".blue-work/unova/audit"))
        rights.save(self.root,r)
        self.assertEqual(before,output.read_bytes())
        changed=dict(r,status="RIGHTS_APPROVED")
        with self.assertRaises(ValueError):
            rights.save(self.root,changed)
        self.assertEqual(before,output.read_bytes())

    def test_09_symlink_report_folder_blocks(self):
        dest=self.root/".blue-work/unova/audit"
        outside=self.root/"external"
        outside.mkdir()
        try:
            dest.symlink_to(outside,target_is_directory=True)
        except OSError:
            self.skipTest("symlink unavailable")
        with self.assertRaises(ValueError):
            rights.save(self.root,rights.inspect(self.root,self.source))

    def test_10_never_infer_credits_from_asset_filenames(self):
        self.members["World/Graphics/Pictures/Credits.png"]=b"pictures"
        self.makezip()
        report=rights.inspect(self.root,self.source)
        self.assertFalse(report["credits"]["credits_file_present"])
        self.assertFalse(report["redistribution_approved"])

if __name__=="__main__":
    unittest.main()
