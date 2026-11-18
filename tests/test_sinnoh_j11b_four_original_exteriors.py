"""J11-B: original four-exterior and combined nine-map negative regression tests."""
from __future__ import annotations
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"scripts/regions")]
import generate_sinnoh_original_j10a as j10a
import generate_sinnoh_four_exteriors_j11b as j11b
import audit_sinnoh_playable_j11 as j11
from audit_sinnoh_playable_j09 import audit_map
from audit_sinnoh_twinleaf_events import MAPS

class OriginalFourExteriorsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files,cls.report=j11b.generate()
        cls.scenes=j11b.scenes()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="j11b-qa-synthetic-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/"scripts/regions").mkdir(parents=True)
        (self.root/"scripts/regions/generate_sinnoh_original_j10a.py").write_text("marker for synthetic test")
        (self.root/"game/Data").mkdir(parents=True)
        (self.root/"game/Data/Map209.rxdata").write_bytes(b"protected main")
        (self.root/"game/Saves").mkdir()
        (self.root/"game/Saves/user.sav").write_bytes(b"protected save")

    def assert_blocked(self,call):
        with self.assertRaises((ValueError,KeyError,TypeError)):
            call()

    def test_01_exactly_four_new_exteriors_are_created(self):
        self.assertEqual(set(j11b.EXTERIORS),{s["symbol"] for s in self.scenes})
        self.assertEqual([j11b.EXTERIORS[s["symbol"]] for s in self.scenes],
                         [(44,34),(50,24),(46,34),(36,46)])
    def test_02_nine_different_rxdata_exist(self):
        binaries={x:b for x,b in self.files.items() if x.endswith(".rxdata")}
        self.assertEqual(len(binaries),9)
        self.assertEqual(set(x.removesuffix(".rxdata") for x in binaries),set(MAPS))
        self.assertEqual(len({hashlib.sha256(x).hexdigest() for x in binaries.values()}),9)
    def test_03_nine_svg_visual_previews(self):
        svgs={x for x in self.files if x.endswith(".svg")}
        self.assertEqual(len(svgs),9)
        self.assertEqual(svgs,{"previews/"+s+".svg" for s in MAPS})
    def test_04_two_separate_original_pngs(self):
        pngs=[(x,b) for x,b in self.files.items() if x.endswith(".png")]
        self.assertEqual(len(pngs),2)
        self.assertNotEqual(j11b.sha(pngs[0][1]),j11b.sha(pngs[1][1]))
        self.assertTrue(all(j11.verify_png(p)["unique_drawn_tile_count"]>=24 for n,p in pngs))
    def test_05_original_b00_donor_is_never_used(self):
        meta=json.loads(self.files["nine-map-source-plan.json"])
        self.assertEqual(meta["historical_source_maps_used"],0)
        self.assertFalse(meta["donor_assets_used"])
        self.assertTrue(all(v["source"]=="ORIGINAL_GENERATOR" for v in meta["maps"]))
    def test_06_catalog_order_is_stable(self):
        meta=json.loads(self.files["nine-map-source-plan.json"])
        self.assertEqual(meta["nine_map_symbols_ordered"],list(MAPS))
        self.assertEqual([r["symbol"] for r in meta["maps"]],list(MAPS))
    def test_07_j10a_five_are_byte_identical_to_existing_generator(self):
        old,_=j10a.generate()
        for name,data in old.items():
            if name!="manifest.json":
                self.assertEqual(self.files[name],data,name)
    def test_08_each_new_map_roundtrips_to_exact_three_layer_pixels(self):
        for scene in self.scenes:
            data=self.files[scene["symbol"]+".rxdata"]
            j11b.audit_nine(*j10a.generate(),self.scenes,
                            self.files["ExteriorJ11B.png"],self.files)
            self.assertEqual(audit_map(data)["foreign_events_not_imported"],0)
    def test_09_exteriors_are_nonempty_nonplaceholder(self):
        for scene in self.scenes:
            obj=audit_map(self.files[scene["symbol"]+".rxdata"])
            self.assertGreater(obj["nonzero_tiles"],scene["width"]*scene["height"])
            self.assertGreater(len({v for layer in scene["layers"] for v in layer if v}),7)
    def test_10_all_edge_candidates_reachable(self):
        for scene in self.scenes:
            self.assertGreater(j11b.reachable(scene),100)
            self.assertGreater(len(scene["landmarks"]),2)
    def test_11_maps_are_not_copies_of_official_layouts(self):
        self.assertNotIn("zipfile",Path(j11b.__file__).read_text())
        self.assertNotIn("urllib.request",Path(j11b.__file__).read_text())
        self.assertNotIn("subprocess",Path(j11b.__file__).read_text())
    def test_12_exterior_artwork_is_deterministic(self):
        self.assertEqual(j11b.original_png(),j11b.original_png())
    def test_13_artwork_has_independent_palette_from_j10a(self):
        self.assertNotEqual(j11b.COLORS,j10a.PALETTE)
    def test_14_manifest_sha256_covers_every_nonmanifest_output(self):
        meta=json.loads(self.files["manifest.json"])
        self.assertEqual(meta["files_sha256"],self.report["files_sha256"])
        for path,sha in meta["files_sha256"].items():
            self.assertEqual(j11b.sha(self.files[path]),sha)
    def test_15_manifest_never_promotes_native_status(self):
        self.assertEqual(self.report["native_maps_installed"],0)
        self.assertEqual(self.report["native_qa_cases_executed"],0)
        self.assertEqual(self.report["mapids_assigned"],0)
        self.assertFalse(self.report["can_install"])
        self.assertFalse(self.report["can_publish_game"])
    def test_16_no_human_or_rights_attestation(self):
        self.assertEqual(self.report["source_authorship"],"PROGRAMMATIC_NOT_HUMAN_ATTESTED")
        self.assertFalse(self.report["r07_approved"])
        self.assertFalse(self.report["r08_approved"])
        self.assertFalse(self.report["r09_approved"])
    def test_17_passability_table_is_only_proposed_not_natively_registered(self):
        reg=json.loads(self.files["tileset-registration-proposal.json"])
        self.assertFalse(reg["native_tilesets_rxdata_generated"])
        self.assertFalse(reg["can_install"])
        self.assertEqual(len(reg["tilesets"]),2)
        self.assertTrue(all(len(v["proposed_tiles"])==32 for v in reg["tilesets"].values()))
        self.assertTrue(all(v["candidate_tileset_id"] is None for v in reg["tilesets"].values()))
    def test_18_tile_passages_are_explicitly_hypothetical(self):
        reg=json.loads(self.files["tileset-registration-proposal.json"])
        for x in reg["tilesets"].values():
            self.assertFalse(x["native_passages_reviewed"])
            self.assertFalse(x["native_priorities_reviewed"])
            self.assertTrue(all(row["verified_in_engine"] is False for row in x["proposed_tiles"]))
    def test_19_each_map_requires_native_tileset_remap(self):
        plan=json.loads(self.files["nine-map-source-plan.json"])
        self.assertEqual({r["provisional_embedded_tileset_id"] for r in plan["maps"]},{1})
        self.assertTrue(all(r["native_tileset_id"] is None for r in plan["maps"]))
        self.assertEqual({r["tileset_group"] for r in plan["maps"]},{"J10A_INTERIORS","J11B_EXTERIORS"})
    def test_20_events_remain_unpositioned(self):
        plan=json.loads(self.files["nine-map-source-plan.json"])
        self.assertEqual(plan["event_contract_counts"],{"warps":16,"npcs":5,"starter_balls":3})
        self.assertFalse(plan["event_coordinates_reviewed"])
    def test_21_r07_without_real_isolated_baseline_is_unverified(self):
        result=j11b.r07_optional(self.root,None,None)
        self.assertFalse(result["checked"])
        self.assertFalse(result["independently_approved"])
    def test_22_r07_partial_input_is_rejected(self):
        self.assert_blocked(lambda:j11b.r07_optional(self.root,self.root/"game/Data",None))
    def test_23_r07_unapproved_baseline_cannot_be_reused_from_live_game(self):
        self.assert_blocked(lambda:j11b.r07_optional(self.root,self.root/"game/Data",
                                                     self.root/"some-review.json"))
    def test_24_r07_local_validation_does_not_grant_independent_approval(self):
        with patch.object(j11,"check_r07",return_value={"r07_independent_approval":False}):
            result=j11b.r07_optional(self.root,self.root/"private-baseline",
                                     self.root/"private-review")
        self.assertFalse(result["independently_approved"])
    def test_25_originals_do_not_have_native_event_scripting(self):
        for s in self.scenes:
            assert audit_map(self.files[s["symbol"]+".rxdata"])["foreign_events_not_imported"]==0
    def test_26_reject_invalid_or_unknown_exterior_symbol(self):
        self.assert_blocked(lambda:j11b.scene("MAP_999"))
    def test_27_reject_blocked_entry(self):
        s=copy.deepcopy(self.scenes[0]);x,y=s["access"][0]
        j10a.at(s,1,x,y,j10a.TREE)
        self.assert_blocked(lambda:j11b.reachable(s))
    def test_28_reject_blocked_exit(self):
        s=copy.deepcopy(self.scenes[1]);x,y=s["edge_candidates"][0]
        j10a.at(s,1,x,y,j10a.TREE)
        self.assert_blocked(lambda:j11b.reachable(s))
    def test_29_reject_isolated_landmark(self):
        s=copy.deepcopy(self.scenes[2]);x,y=s["landmarks"][0]
        for dx,dy in ((0,1),(0,-1),(1,0),(-1,0)):
            j10a.at(s,1,x+dx,y+dy,j10a.WALL)
        self.assert_blocked(lambda:j11b.reachable(s))
    def test_30_reject_nine_map_byte_corruption(self):
        files=copy.deepcopy(self.files)
        symbol="SINNOH_ROUTE_202";files[symbol+".rxdata"]+=b"tamper"
        self.assert_blocked(lambda:j11b.audit_nine(*j10a.generate(),self.scenes,
                                                   files["ExteriorJ11B.png"],files))
    def test_31_reject_svg_preview_tampering(self):
        files=copy.deepcopy(self.files)
        symbol="SINNOH_SANDGEM_TOWN"
        files["previews/"+symbol+".svg"]+=b"modified"
        self.assert_blocked(lambda:j11b.audit_nine(*j10a.generate(),self.scenes,
                                                   files["ExteriorJ11B.png"],files))
    def test_32_private_bundle_only_under_ignored_workspace(self):
        result=j11b.private_build(self.root)
        path=self.root/".blue-work"/j11b.OUTPUT
        self.assertTrue(path.is_dir())
        self.assertEqual(len(list(path.rglob("*.rxdata"))),9)
        self.assertEqual(len(list(path.rglob("*.png"))),2)
        self.assertEqual(len(list(path.rglob("*.svg"))),9)
        self.assertFalse(result["can_install"])
        self.assertFalse((self.root/"game/Data/Map210.rxdata").exists())
    def test_33_reject_private_bundle_overwrite(self):
        j11b.private_build(self.root)
        self.assert_blocked(lambda:j11b.private_build(self.root))
    def test_34_reject_symlink_workdir(self):
        outside=self.root/"other";outside.mkdir()
        try:(self.root/".blue-work").symlink_to(outside,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest("symlink not available")
        self.assert_blocked(lambda:j11b.private_build(self.root))
    def test_35_reject_symlink_target(self):
        work=self.root/".blue-work";work.mkdir()
        outside=self.root/"other";outside.mkdir()
        try:(work/j11b.OUTPUT).symlink_to(outside,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest("symlink not available")
        self.assert_blocked(lambda:j11b.private_build(self.root))
    def test_36_no_user_game_or_saves_modified_by_build(self):
        j11b.private_build(self.root)
        self.assertEqual((self.root/"game/Data/Map209.rxdata").read_bytes(),b"protected main")
        self.assertEqual((self.root/"game/Saves/user.sav").read_bytes(),b"protected save")
    def test_37_build_outputs_have_manifest_integrity(self):
        j11b.private_build(self.root)
        path=self.root/".blue-work"/j11b.OUTPUT
        manifest=json.loads((path/"manifest.json").read_text())
        for name,sha in manifest["files_sha256"].items():
            self.assertEqual(j11b.sha((path/name).read_bytes()),sha)
    def test_38_no_native_running_engine_in_generator(self):
        contents=Path(j11b.__file__).read_text()
        self.assertNotIn("Game.exe",contents)
        self.assertNotIn("JoiPlay",contents)
    def test_39_public_progress_stays_nine_zero(self):
        a=json.loads((ROOT/"data/regions/sinnoh-playable-progress.json").read_text())
        b=json.loads((ROOT/"site/public/data/sinnoh-playable-progress.json").read_text())
        self.assertEqual(a,b)
        self.assertEqual(a["status"],"PILOT_NOT_INSTALLED_NOT_PLAYABLE")
        self.assertEqual(a["stages_native_validated"],0)
        self.assertEqual(a["native_windows_cases_executed"],0)
        self.assertEqual(a["native_android_cases_executed"],0)
        self.assertFalse(a["main_game_modified"])
    def test_40_no_private_files_written_by_in_memory_generate(self):
        j11b.generate()
        self.assertFalse((self.root/".blue-work").exists())

if __name__=="__main__":
    unittest.main()
