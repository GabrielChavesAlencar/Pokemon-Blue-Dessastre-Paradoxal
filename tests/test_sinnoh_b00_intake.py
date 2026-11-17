"""B00: donor intake checks never import or approve native gameplay."""
from __future__ import annotations
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile,ZipInfo
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts/regions"))
from audit_sinnoh_b00_intake import inspect,load_manifest,inspect_extra_zip,check_credits
from audit_sinnoh_b00_intake import ROOT
from audit_sinnoh_b00_intake import blocked
from unittest.mock import patch

class B00Tests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base=Path(tmp.name)
        self.archive=self.base/"Pokemon_World_V18.zip"
        self.credits=self.base/"Credits.txt"
        self.credits.write_text("Example credit, only a fixture",encoding="utf-8")

    def create(self,files=None):
        files=files or {
          "Pokemon World/Data/MapInfos.rxdata":b"map index",
          "Pokemon World/Data/Tilesets.rxdata":b"tileset index",
          "Pokemon World/Data/Map001.rxdata":b"map1",
          "Pokemon World/Data/Map002.rxdata":b"map2",
          "Pokemon World/Data/Map003.rxdata":b"map3",
          "Pokemon World/Graphics/Tilesets/overworld.png":b"image",
          "Pokemon World/Graphics/Autotiles/water.png":b"image",
          "Pokemon World/Graphics/Characters/player.png":b"image",
          "Pokemon World/PBS/trainers.txt":b"trainer",
          "Pokemon World/Game.rxproj":b"rmxp",
        }
        with ZipFile(self.archive,"w") as f:
            for name,body in files.items():f.writestr(name,body)

    def test_01_no_source_zero_approval(self):
        r=inspect()
        self.assertEqual(r["status"],"AWAITING_USER_FILES")
        self.assertFalse(r["can_import_maps"])
        self.assertEqual(r["phase_b_completed"],0)
        self.assertEqual(r["additional_file_counts"]["tilesets"],0)

    def test_02_donor_archive_is_not_one_region(self):
        self.create()
        r=inspect(self.archive,self.credits)
        self.assertEqual(r["status"],"CANDIDATE_FOR_DEEP_RXDATA_AUDIT_NOT_APPROVED")
        self.assertEqual(r["donor_map_count_all_regions"],3)
        self.assertFalse(r["source_sinnoh_map_ids_identified"])
        self.assertEqual(r["additional_file_counts"],{
            "tilesets":1,"autotiles":1,"characters":1,
            "pbs_text":1,"rpg_project":1})
        self.assertFalse(r["rights_for_individual_assets_confirmed"])
        self.assertFalse(r["can_import_maps"])

    def test_03_missing_credits_blocks_progress(self):
        self.create()
        r=inspect(self.archive)
        self.assertEqual(r["status"],"CREDITS_REQUIRED_FOR_REVIEW")
        self.assertFalse(r["may_publish"])

    def test_04_tiny_template_not_marked_complete(self):
        self.create({
            "Data/MapInfos.rxdata":b"info","Data/Tilesets.rxdata":b"tileset",
            "Data/Map001.rxdata":b"one","Data/Map002.rxdata":b"two"
        })
        self.assertEqual(inspect(self.archive,self.credits)["status"],
                         "SOURCE_TOO_SMALL_OR_TEMPLATE_ONLY")

    def test_05_zip_slip_rejected(self):
        self.create({"../other/file.txt":b"bad",
            "Data/MapInfos.rxdata":b"index","Data/Tilesets.rxdata":b"tileset",
            "Data/Map001.rxdata":b"map1"})
        with self.assertRaises(ValueError):inspect(self.archive,self.credits)

    def test_06_duplicate_casefold_rejected(self):
        self.create({"Data/MapInfos.rxdata":b"m","Data/Tilesets.rxdata":b"t",
                     "Graphics/Tilesets/A.PNG":b"a",
                     "graphics/tilesets/a.png":b"b","Data/Map001.rxdata":b"1"})
        with self.assertRaisesRegex(ValueError,"nomes duplicados"):
            inspect(self.archive,self.credits)

    def test_07_symlink_credit_refused(self):
        target=self.base/"original.txt";target.write_text("test",encoding="utf-8")
        link=self.base/"linked.txt"
        link.symlink_to(target)
        with self.assertRaises(ValueError):check_credits(link)

    def test_08_source_cannot_be_decades_main_game(self):
        with self.assertRaises(ValueError):
            inspect(ROOT/"game")

    def test_09_credits_hash_only_not_rights(self):
        p=check_credits(self.credits)
        self.assertEqual(len(p["sha256"]),64)
        self.assertFalse(p["individual_asset_rights_verified"])

    def test_10_never_writes_or_relabels_source(self):
        self.create()
        before=hashlib.sha256(self.archive.read_bytes()).hexdigest()
        r1=inspect(self.archive,self.credits)
        r2=inspect(self.archive,self.credits)
        self.assertEqual(r1,r2)
        self.assertEqual(hashlib.sha256(self.archive.read_bytes()).hexdigest(),before)

    def test_11_manifest_declares_zero_phase_approvals(self):
        x=load_manifest()
        self.assertEqual(x["phase_b_completed"],0)
        self.assertFalse(x["technical_phase_approved"])
        self.assertFalse(x["source_map_ids_verified"])

    def test_12_symlink_source_rejected(self):
        self.create()
        l=self.base/"source.zip"
        l.symlink_to(self.archive)
        with self.assertRaises(ValueError):inspect(l,self.credits)

if __name__=="__main__":unittest.main()
