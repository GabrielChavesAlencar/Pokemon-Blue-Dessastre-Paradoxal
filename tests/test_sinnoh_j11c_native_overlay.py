"""J11-C: 42 synthetic and fail-closed private QA overlay regressions."""
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
import prepare_sinnoh_nine_original_j11c as j11c
import generate_sinnoh_original_j10a as j10a
import generate_sinnoh_four_exteriors_j11b as j11b
from audit_sinnoh_rxdata import read_marshal
from audit_sinnoh_twinleaf_events import MAPS
from compile_sinnoh_playable_j04 import passable_point
from server.ruby_marshal import RubyObject,RubyData
from stage import serialize

class J11CIsolatedNatives(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pure=j11c.audit_only()
        cls.tiles=[None,j11c.proposal("J10A_INTERIORS","f"*64,1)]
        cls.info={2:RubyObject("RPG::MapInfo",{
            "@name":b"EXISTING_KANTO_DO_NOT_CHANGE",
            "@order":2,"@parent_id":0,"@expanded":False,
            "@scroll_x":0,"@scroll_y":0})}
        cls.ids=list(range(442,451))
        cls.files,cls.manifest=j11c.mock_or_private_native_overlay(
            cls.info,cls.tiles,cls.ids,occupied={2,55},protected={410},
            synthetic_fixture=True)
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix="sinnoh-j11c-synthetic-")
        self.addCleanup(temp.cleanup)
        self.temp=Path(temp.name)
        (self.temp/"game/Data").mkdir(parents=True)
        (self.temp/"game/Saves").mkdir(parents=True)
        (self.temp/"game/Data/Map002.rxdata").write_bytes(b"protected map")
        (self.temp/"game/Saves/user.sav").write_bytes(b"protected save")
    def rejects(self,fn):
        with self.assertRaises((ValueError,TypeError,KeyError,OverflowError)):
            fn()

    def test_01_nine_originals_and_two_tile_groups_audited(self):
        self.assertEqual(len(self.pure["original_nine_source_hashes"]),9)
        self.assertEqual(len(set(self.pure["original_nine_source_hashes"].values())),9)
        self.assertEqual(len(self.pure["tileset_png_shas"]),2)
    def test_02_no_live_mapids_assigned_in_audit_only(self):
        self.assertEqual(self.pure["mapids_reserved"],0)
        self.assertEqual(self.pure["native_tilesets_created_in_real_game"],0)
    def test_03_source_geometry_checks_all_nine(self):
        src,m=j11c.source_audit()
        self.assertEqual(len([p for p in src if p.endswith(".rxdata")]),9)
        self.assertEqual(m["nine_distinct_rxdata_count"],9)
    def test_04_real_rpg_tileset_class_and_id(self):
        tile=j11c.proposal("J10A_INTERIORS","a"*64,33)
        self.assertEqual(tile.name,"RPG::Tileset")
        self.assertEqual(tile.attrs["@id"],33)
        self.assertEqual(j11c.verify_tile(tile,33)["passages_entries"],416)
    def test_05_2d_no_autotiles_in_registered_candidate(self):
        for g in j11c.GRAPHIC:
            a=j11c.proposal(g,"a"*64,1)
            self.assertEqual(a.attrs["@autotile_names"],[b""]*7)
    def test_06_passages_and_priorities_are_ruby_marshal_tables(self):
        a=j11c.proposal("J11B_EXTERIORS","f"*64,2)
        for name in ("@passages","@priorities","@terrain_tags"):
            v=a.attrs[name]
            self.assertEqual(v.name,"Table")
            self.assertEqual(j11c.decode1(v).__len__(),416)
    def test_07_conservative_block_on_unknown_autotiles(self):
        a=j11c.proposal("J10A_INTERIORS","f"*64,2)
        p=j11c.decode1(a.attrs["@passages"])
        self.assertTrue(all(v==15 for v in p[1:384]))
    def test_08_32_authored_tile_priority_classes(self):
        a=j11c.proposal("J11B_EXTERIORS","f"*64,2)
        self.assertEqual(len(j11c.verify_tile(a,2)["blocking_classes"]),len(j11c.FORBIDDEN))
        self.assertTrue(j11c.FORBIDDEN.issuperset({j10a.TREE,j10a.WATER,j10a.ROCK}))
    def test_09_preserves_unchanged_baseline_mapinfo(self):
        staged=read_marshal(self.files["Data/MapInfos.rxdata"],"M")
        self.assertEqual(serialize(staged[2]),serialize(self.info[2]))
    def test_10_preserves_unchanged_baseline_tilesets(self):
        staged=read_marshal(self.files["Data/Tilesets.rxdata"],"T")
        for i,old in enumerate(self.tiles):
            self.assertEqual(serialize(staged[i]),serialize(old))
    def test_11_two_appended_real_rpg_tilesets(self):
        tiles=read_marshal(self.files["Data/Tilesets.rxdata"],"T")
        self.assertEqual(len(tiles),len(self.tiles)+2)
        for group,idx in self.manifest["tileset_ids"].items():
            j11c.verify_tile(tiles[idx],idx)
    def test_12_nine_built_rpg_maps_in_private_overlay(self):
        paths={p for p in self.files if p.startswith("Data/Map") and p.endswith(".rxdata") and p!="Data/MapInfos.rxdata"}
        self.assertEqual(len(paths),9)
    def test_13_both_graphics_are_new_binary_original_pngs(self):
        imgs={name:val for name,val in self.files.items() if name.startswith("Graphics/Tilesets/")}
        self.assertEqual(len(imgs),2)
        self.assertEqual(len({hashlib.sha256(x).hexdigest() for x in imgs.values()}),2)
    def test_14_metadata_remap_respects_nine_symbol_order(self):
        self.assertEqual(list(self.manifest["mapids"]),list(MAPS))
        self.assertEqual(list(self.manifest["mapids"].values()),self.ids)
    def test_15_maps_reference_correct_distinct_tilesets(self):
        for symbol,mid in self.manifest["mapids"].items():
            m=read_marshal(self.files["Data/Map%03d.rxdata"%mid],"M")
            group="J10A_INTERIORS" if symbol in j10a.SYMBOLS else "J11B_EXTERIORS"
            self.assertEqual(m.attrs["@tileset_id"],self.manifest["tileset_ids"][group])
    def test_16_layers_byte_identical_after_remap(self):
        orig,_=j11b.generate()
        for symbol,mid in self.manifest["mapids"].items():
            raw=read_marshal(self.files["Data/Map%03d.rxdata"%mid],"M")
            before=read_marshal(orig[symbol+".rxdata"],"O")
            self.assertEqual(raw.attrs["@data"].data,before.attrs["@data"].data)
    def test_17_no_foreign_events_or_audio(self):
        for mid in self.manifest["mapids"].values():
            raw=read_marshal(self.files["Data/Map%03d.rxdata"%mid],"M")
            self.assertEqual(raw.attrs["@events"],{})
            self.assertFalse(raw.attrs["@autoplay_bgm"])
    def test_18_model_passability_at_candidate_spawn(self):
        raw=read_marshal(self.files["Data/Map442.rxdata"],"M")
        tiles=read_marshal(self.files["Data/Tilesets.rxdata"],"T")
        self.assertTrue(passable_point(raw,tiles,10,13))
    def test_19_all_nine_access_points_checked(self):
        self.assertEqual(self.manifest["candidate_access_points_model_only"],9)
        self.assertFalse(self.manifest["r09_approved"])
    def test_20_full_event_contracts_16_5_3(self):
        t=j11c.event_contract()
        self.assertEqual(len(t["contracts"]),24)
        self.assertEqual((t["counts"]["directional_warps"],t["counts"]["npc_handlers"],
                          t["counts"]["starter_balls"]),(16,5,3))
    def test_21_events_have_no_fabricated_coordinates(self):
        self.assertTrue(all(x["coordinate"] is None for x in j11c.event_contract()["contracts"]))
        self.assertFalse(j11c.event_contract()["native_j04_events_compiled"])
    def test_22_no_install_or_release(self):
        for k in ("can_install","can_publish","r07_globally_approved","r08_approved","r09_approved"):
            self.assertFalse(self.manifest[k])
        self.assertEqual((self.manifest["native_maps_installed"],self.manifest["native_qa_cases_executed"]),(0,0))
    def test_23_no_game_save_or_other_regions_changed(self):
        j11c.audit_only()
        self.assertEqual((self.temp/"game/Data/Map002.rxdata").read_bytes(),b"protected map")
        self.assertEqual((self.temp/"game/Saves/user.sav").read_bytes(),b"protected save")
        self.assertFalse((self.temp/".blue-work").exists())
    def test_24_each_file_has_sha256(self):
        self.assertEqual(set(self.files),set(self.manifest["files_sha256"]))
        for name,binary in self.files.items():
            self.assertEqual(j11c.digest(binary),self.manifest["files_sha256"][name])
    def test_25_portal_progress_zero(self):
        a=json.loads((ROOT/"data/regions/sinnoh-playable-progress.json").read_text())
        b=json.loads((ROOT/"site/public/data/sinnoh-playable-progress.json").read_text())
        self.assertEqual(a,b)
        self.assertEqual(a["status"],"PILOT_NOT_INSTALLED_NOT_PLAYABLE")
        self.assertEqual(a["stages_native_validated"],0)
        self.assertEqual(a["native_windows_cases_executed"],0)
        self.assertEqual(a["native_android_cases_executed"],0)
        self.assertFalse(a["main_game_modified"])

    def test_26_reject_duplicate_r07_ids(self):
        ids=self.ids[:];ids[1]=ids[0]
        self.rejects(lambda:j11c.candidate_ids(set(),set(),ids))
    def test_27_reject_mapid_colliding_with_baseline(self):
        self.rejects(lambda:j11c.candidate_ids({442},set(),self.ids))
    def test_28_reject_mapid_reserved_by_kanto(self):
        self.rejects(lambda:j11c.candidate_ids(set(),{450},self.ids))
    def test_29_reject_id_outside_allowed_sinnoh_range(self):
        ids=self.ids[:];ids[-1]=518
        self.rejects(lambda:j11c.candidate_ids(set(),set(),ids))
    def test_30_reject_boolean_instead_of_id(self):
        ids=self.ids[:];ids[0]=True
        self.rejects(lambda:j11c.candidate_ids(set(),set(),ids))
    def test_31_reject_baseline_with_non_mapinfo_objects(self):
        self.rejects(lambda:j11c.validate_baseline({2:b"not mapinfo"},self.tiles))
    def test_32_reject_invalid_tileset_index_zero(self):
        self.rejects(lambda:j11c.validate_baseline(self.info,[j11c.proposal("J10A_INTERIORS","a"*64,0)]))
    def test_33_reject_tampered_passages(self):
        tile=j11c.proposal("J11B_EXTERIORS","a"*64,2)
        p=j11c.decode1(tile.attrs["@passages"]);p[j10a.TREE]=0
        tile.attrs["@passages"]=j11c.table1(p)
        self.rejects(lambda:j11c.verify_tile(tile,2))
    def test_34_reject_tampered_priorities(self):
        tile=j11c.proposal("J11B_EXTERIORS","a"*64,2)
        p=j11c.decode1(tile.attrs["@priorities"]);p[j10a.TREE]=0
        tile.attrs["@priorities"]=j11c.table1(p)
        self.rejects(lambda:j11c.verify_tile(tile,2))
    def test_35_reject_unknown_autotile_names(self):
        tile=j11c.proposal("J11B_EXTERIORS","a"*64,2)
        tile.attrs["@autotile_names"][0]=b"donor.png"
        self.rejects(lambda:j11c.verify_tile(tile,2))
    def test_36_reject_invalid_passages_table_header(self):
        tile=j11c.proposal("J10A_INTERIORS","a"*64,2)
        tile.attrs["@passages"]=j11c.table1([0,1,2])
        self.rejects(lambda:j11c.verify_tile(tile,2))
    def test_37_reject_source_with_foreign_events(self):
        raw,_=j11b.generate()
        src=read_marshal(raw[MAPS[0]+".rxdata"],"M")
        src.attrs["@events"]={1:"bad"}
        self.rejects(lambda:j11c.sanitize_map(serialize(src),2))
    def test_38_reject_source_prematurely_using_native_tileset(self):
        raw,_=j11b.generate()
        src=read_marshal(raw[MAPS[0]+".rxdata"],"M")
        src.attrs["@tileset_id"]=22
        self.rejects(lambda:j11c.sanitize_map(serialize(src),2))
    def test_39_reject_stage_without_private_baseline(self):
        self.assertEqual(j11c.main(["--project",str(self.temp),"--stage"]),2)
        self.assertFalse((self.temp/".blue-work").exists())
    def test_40_reject_direct_game_data_as_baseline(self):
        self.rejects(lambda:j11c.private_inputs(self.temp,self.temp/"game/Data",
                          self.temp/"r07.json"))
    def test_41_reject_stage_reused_output(self):
        p=self.temp/".blue-work"/j11c.OUTPUT
        p.parent.mkdir();p.mkdir()
        self.rejects(lambda:j11c.build_private(self.temp,
                    self.temp/"game/Data",self.temp/"review.json"))
    def test_42_public_cli_audit_remains_nonmutating(self):
        self.assertEqual(j11c.main(["--project",str(self.temp)]),0)
        self.assertFalse((self.temp/".blue-work").exists())
    def test_43_no_native_rights_applied_by_tests(self):
        self.assertFalse(self.manifest["rights_independently_approved"])
        self.assertTrue(self.manifest["synthetic_baseline_fixture"])
        self.assertFalse(self.manifest["game_exe_tested"])
        self.assertFalse(self.manifest["joiplay_tested"])
    def test_44_two_registered_types_are_actually_RPG_Tileset(self):
        raw=read_marshal(self.files["Data/Tilesets.rxdata"],"T")
        self.assertEqual(raw[-1].name,"RPG::Tileset")
        self.assertEqual(raw[-2].name,"RPG::Tileset")
    def test_45_no_sprites_or_game_scripts_in_overlay(self):
        self.assertFalse(any(n.endswith("Scripts.rxdata") or "Characters/" in n for n in self.files))
    def test_46_invalid_r07_receipt_does_not_approve_real_mapids(self):
        self.assertEqual(self.pure["mapids_reserved"],0)
        self.rejects(lambda:j11c.candidate_ids(set(),set(),[443]*9))

if __name__=="__main__":unittest.main()
