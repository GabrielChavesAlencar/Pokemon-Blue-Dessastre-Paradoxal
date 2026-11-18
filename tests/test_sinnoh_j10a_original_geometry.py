"""J10-A tests: original procedure and inert RMXP artifacts, NOT real-game QA."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"scripts/regions")]
import generate_sinnoh_original_j10a as g
import audit_sinnoh_playable_j09 as j09
from author_sinnoh_playable_j10 import parse_png
from audit_sinnoh_rxdata import attrs,read_marshal
from server.ruby_marshal import RubyData

class J10AOriginalGeometryTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="j10a-private-synthetic-")
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        directory=self.root/"scripts/regions"
        directory.mkdir(parents=True)
        (directory/"author_sinnoh_playable_j10.py").write_text("test-only repository marker\n")
        (self.root/"game/Data").mkdir(parents=True)
        (self.root/"game/Data/Map209.rxdata").write_bytes(b"protected-map-fixture")
        (self.root/"game/Saves").mkdir()
        (self.root/"game/Saves/primary.sav").write_bytes(b"protected-save-fixture")

    def test_01_five_independent_nonempty_marshal_maps(self):
        out,report=g.generate()
        self.assertEqual(report["map_count"],5)
        self.assertEqual(len([f for f in out if f.endswith(".rxdata")]),5)
        self.assertEqual(len({report["map_sources"][s]["rxdata_sha256"] for s in g.SYMBOLS}),5)
        for s in g.SYMBOLS:
            info=j09.audit_map(out[s+".rxdata"])
            self.assertGreater(info["nonzero_tiles"],120)
            self.assertEqual(info["foreign_events_not_imported"],0)

    def test_02_original_png_dimensions_crc_and_sha(self):
        files,report=g.generate()
        self.assertEqual(parse_png(files["OriginalJ10A.png"]),(256,256))
        self.assertEqual(g.checksum(files["OriginalJ10A.png"]),report["tileset_sha256"])

    def test_03_layers_rmxp_table_roundtrip(self):
        files,_=g.generate()
        for s in g.SYMBOLS:
            obj=read_marshal(files[s+".rxdata"],"J10A_TEST")
            m=attrs(obj)
            table=m["@data"]
            self.assertIsInstance(table,RubyData)
            self.assertEqual(table.name,"Table")
            dims=struct.unpack_from("<5I",table.data,0)
            self.assertEqual(dims,(3,m["@width"],m["@height"],3,m["@width"]*m["@height"]*3))

    def test_04_j09_can_read_five_original_nonhuman_generated_sources(self):
        files,_=g.generate()
        folder=self.root/".blue-work"/j09.STAGE_DIR
        folder.mkdir(parents=True)
        for s in g.SYMBOLS:(folder/(s+".rxdata")).write_bytes(files[s+".rxdata"])
        result=j09.authored_five(self.root,folder,j09.source_catalog(ROOT))
        self.assertEqual(set(result),set(g.SYMBOLS))
        self.assertTrue(all(x["foreign_events_not_imported"]==0 for x in result.values()))

    def test_05_generated_scenes_have_real_original_dimensions(self):
        self.assertEqual([g.SIZES[s] for s in g.SYMBOLS],
            [(20,15),(25,19),(23,18),(38,27),(29,21)])
        self.assertTrue(all(x["walkable_reachable"]>10 for x in g.scenes()))

    def test_06_all_five_show_unverified_r07_r08_r09(self):
        _,r=g.generate()
        self.assertFalse(r["r07_approved"])
        self.assertFalse(r["r08_approved"])
        self.assertFalse(r["r09_native_verified"])
        self.assertFalse(r["can_install"])
        self.assertFalse(r["can_publish_game"])
        self.assertEqual(r["native_maps_installed"],0)
        self.assertEqual(r["native_windows_cases_executed"],0)
        self.assertEqual(r["native_android_cases_executed"],0)
        self.assertFalse(r["actual_human_authorship_attested"])

    def test_07_no_native_mapids_or_human_review_claim(self):
        _,r=g.generate()
        for src in r["map_sources"].values():
            self.assertIsNone(src["r07_destination_mapid"])
            self.assertFalse(src["r08_independent_asset_review"])
            self.assertFalse(src["j11_real_tileset_passability_verified"])
            self.assertEqual(src["source_kind"],"PROGRAMMATIC_ORIGINAL_NOT_HUMAN_ATTESTED")

    def test_08_map_schematics_are_generated_as_five_svg_previews(self):
        files,_=g.generate()
        self.assertEqual(len([x for x in files if x.endswith(".svg")]),5)
        for symbol in g.SYMBOLS:
            raw=files["previews/"+symbol+".svg"].decode()
            self.assertIn("<svg",raw)
            self.assertIn(symbol,raw)
            self.assertGreater(raw.count("<rect"),50)
            self.assertNotIn("<script",raw)

    def test_09_generated_hashes_are_repeatable(self):
        a,ar=g.generate();b,br=g.generate()
        self.assertEqual({p:g.checksum(v) for p,v in a.items()},
                         {p:g.checksum(v) for p,v in b.items()})
        self.assertEqual(ar["tileset_sha256"],br["tileset_sha256"])

    def test_10_manifest_verifies_every_binary_and_preview(self):
        files,r=g.generate()
        data=json.loads(files["manifest.json"])
        self.assertEqual(data["output_checksums"],r["output_checksums"])
        for path,sha in data["output_checksums"].items():
            self.assertEqual(g.checksum(files[path]),sha)

    def test_11_build_private_creates_only_new_ignored_directory(self):
        report=g.build_private(self.root)
        target=self.root/".blue-work"/g.OUTPUT
        self.assertTrue(target.is_dir())
        self.assertEqual(report["private_generated_rxdata_count"],5)
        self.assertEqual(len(list(target.rglob("*.rxdata"))),5)
        self.assertFalse((self.root/".blue-work"/j09.STAGE_DIR).exists())
        self.assertEqual((self.root/"game/Data/Map209.rxdata").read_bytes(),b"protected-map-fixture")
        self.assertEqual((self.root/"game/Saves/primary.sav").read_bytes(),b"protected-save-fixture")

    def test_12_refuse_second_build_without_overwriting(self):
        g.build_private(self.root)
        with self.assertRaisesRegex(ValueError,"OUTPUT_MUST_BE_NEW"):
            g.build_private(self.root)
        self.assertEqual(len(list((self.root/".blue-work"/g.OUTPUT).rglob("*.rxdata"))),5)

    def test_13_no_partial_output_when_generation_fails(self):
        with patch.object(g,"generate",side_effect=ValueError("blocked")):
            with self.assertRaises(ValueError):g.build_private(self.root)
        self.assertFalse((self.root/".blue-work"/g.OUTPUT).exists())

    def test_14_refuse_unsafe_missing_repo_root(self):
        (self.root/"scripts/regions/author_sinnoh_playable_j10.py").unlink()
        with self.assertRaisesRegex(ValueError,"REPOSITORY_ROOT"):
            g.build_private(self.root)

    def test_15_reject_blocked_access_node(self):
        scene=g.decorate_bedroom()
        x,y=scene["access"][0]
        g.at(scene,1,x,y,g.WALL)
        with self.assertRaisesRegex(ValueError,"ACCESS_OR_LANDMARK"):
            g.validate_scene(scene)

    def test_16_reject_disconnected_landmark(self):
        scene=g.decorate_house()
        x,y=scene["landmarks"][0]
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            g.at(scene,1,x+dx,y+dy,g.WALL)
        with self.assertRaisesRegex(ValueError,"POTENTIAL_WALKABILITY_DISCONNECTED"):
            g.validate_scene(scene)

    def test_17_reject_missing_three_layer_geometry(self):
        scene=g.decorate_lab()
        scene["layers"].pop()
        with self.assertRaisesRegex(ValueError,"THREE_FULL_LAYERS"):
            g.validate_scene(scene)

    def test_18_reject_forged_tile_range(self):
        scene=g.decorate_barry_house()
        scene["layers"][0][0]=9999
        with self.assertRaisesRegex(ValueError,"TILE_RANGE"):
            g.validate_scene(scene)

    def test_19_reject_empty_placeholders(self):
        scene=g.decorate_bedroom()
        scene["layers"]=[[0]*(scene["width"]*scene["height"]) for _ in range(3)]
        with self.assertRaisesRegex(ValueError,"TRIVIAL_OR_PLACEHOLDER"):
            g.validate_scene(scene)

    def test_20_without_build_mode_no_private_files_are_created(self):
        self.assertEqual(g.main(["--project",str(self.root)]),0)
        self.assertFalse((self.root/".blue-work"/g.OUTPUT).exists())
        self.assertFalse((self.root/".blue-work"/j09.STAGE_DIR).exists())

    def test_21_private_work_symlink_refused(self):
        outside=self.root/"elsewhere"
        outside.mkdir()
        work=self.root/".blue-work"
        try:work.symlink_to(outside,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest("symlink unavailable")
        with self.assertRaisesRegex(ValueError,"OUTPUT_MUST_BE_NEW"):
            g.build_private(self.root)

    def test_22_reject_symlink_as_target(self):
        outside=self.root/"some-folder";outside.mkdir()
        work=self.root/".blue-work";work.mkdir()
        try:(work/g.OUTPUT).symlink_to(outside,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest("symlink unavailable")
        with self.assertRaisesRegex(ValueError,"OUTPUT_MUST_BE_NEW"):
            g.build_private(self.root)

    def test_23_no_user_files_or_libraries_are_accessed(self):
        before=((self.root/"game/Data/Map209.rxdata").read_bytes(),
                (self.root/"game/Saves/primary.sav").read_bytes())
        g.build_private(self.root)
        after=((self.root/"game/Data/Map209.rxdata").read_bytes(),
               (self.root/"game/Saves/primary.sav").read_bytes())
        self.assertEqual(before,after)

    def test_24_j10a_code_has_no_donor_archive_extraction(self):
        script=(ROOT/"scripts/regions/generate_sinnoh_original_j10a.py").read_text()
        self.assertNotIn("zipfile",script)
        self.assertNotIn("subprocess",script)
        self.assertNotIn("requests",script)
        self.assertNotIn("urllib.request",script)
        self.assertNotIn("os.system",script)

    def test_25_j10a_does_not_claim_native_qa(self):
        script=(ROOT/"scripts/regions/generate_sinnoh_original_j10a.py").read_text()
        self.assertIn('"native_maps_installed":0',script)
        self.assertIn('"r09_native_verified":False',script)
        self.assertIn('"can_install":False',script)

if __name__=="__main__":unittest.main()
