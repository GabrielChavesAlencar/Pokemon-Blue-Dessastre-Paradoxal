"""Sinnoh J12E: experimental installer contract and adversarial regression suite.

Runs without any user game, Game.exe launch, save reads or credentials.
"""
from __future__ import annotations
import copy
from pathlib import Path
import json
import os
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"scripts/regions")]
import install_sinnoh_experimental_windows as exp
import generate_sinnoh_original_j10a as five
import generate_sinnoh_four_exteriors_j11b as four
import prepare_sinnoh_nine_original_j11c as j11c
from audit_sinnoh_rxdata import read_marshal
from audit_sinnoh_twinleaf_events import MAPS
from server.ruby_marshal import RubyObject
from stage import serialize

class J12EInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.infos={2:RubyObject("RPG::MapInfo",{
            "@name":b"EXISTING_REGION_UNTOUCHED",
            "@parent_id":0,"@order":2,"@expanded":False,
            "@scroll_x":0,"@scroll_y":0})}
        cls.tiles=[None,j11c.proposal("J10A_INTERIORS","f"*64,1)]
        cls.ids=list(range(442,451))
        cls.mapping=dict(zip(MAPS,cls.ids))
        cls.empty,cls.meta=j11c.mock_or_private_native_overlay(
            cls.infos,cls.tiles,cls.ids,occupied={2},protected=set(),
            synthetic_fixture=True)
        cls.ready,cls.events,cls.start=exp.compile_events(cls.empty,cls.mapping)
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="sinnoh-experimental-synthetic-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.base=self.root/"baseline"
        self.proj=self.root/"source"
        self.base.mkdir();self.proj.mkdir()
        for path in ("Game.exe","Game.ini","mkxp.json","Data/MapInfos.rxdata",
                     "Data/Tilesets.rxdata","Data/System.rxdata","Data/Scripts.rxdata"):
            p=self.base/path
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(b"synthetic test only")
        for dirname in ("Audio","Fonts","Graphics","PBS","Plugins"):
            (self.base/dirname).mkdir()
        (self.base/"Game.ini").write_text("Title=TEST BASE\n",encoding="utf-8")
        (self.base/"mkxp.json").write_text('{"windowTitle":"main","dataPathApp":"BASE_APP","dataPathOrg":"BASE_ORG"}')
        (self.base/"Data/Map002.rxdata").write_bytes(b"base map, do not modify")
        (self.base/"Saves").mkdir()
        (self.base/"Saves/File A.rxdata").write_bytes(b"personal save fixture")
        (self.base/"Data/File A.rxdata").write_bytes(b"personal save Data fixture")
    def reject(self,fn):
        with self.assertRaises((ValueError,OSError,TypeError,KeyError)):fn()

    def test_01_original_scene_count_and_names(self):
        self.assertEqual(set(exp.all_scenes()),set(MAPS))
    def test_02_nine_source_maps_generated_in_memory(self):
        self.assertEqual(len([x for x in self.empty if x.startswith("Data/Map") and x not in ("Data/MapInfos.rxdata",)]),9)
    def test_03_24_events_statically_placed(self):
        self.assertEqual(len(self.events),24)
        self.assertEqual(len({e["key"] for e in self.events}),24)
    def test_04_all_16_warps_have_target_map_ids_and_arrivals(self):
        warps=[x for x in self.events if x["kind"]=="warp"]
        self.assertEqual(len(warps),16)
        self.assertTrue(all(x["destination_map_id"]==self.mapping[x["destination"]] for x in warps))
    def test_05_five_handlers_three_ball_events(self):
        self.assertEqual(sum(x["kind"]=="handler" for x in self.events),5)
        self.assertEqual(sum(x["kind"]=="starter_ball" for x in self.events),3)
    def test_06_no_duplicate_coordinates_per_map(self):
        for symbol in MAPS:
            coords=[tuple(x["position"]) for x in self.events if x["map"]==symbol]
            self.assertEqual(len(coords),len(set(coords)))
    def test_07_all_event_positions_reachable_in_generated_geometry(self):
        sc=exp.all_scenes()
        for row in self.events:
            self.assertIn(tuple(row["position"]),exp.component(sc[row["map"]]))
    def test_08_all_warp_arrivals_reachable_and_not_events(self):
        sc=exp.all_scenes()
        used={symbol:{tuple(e["position"]) for e in self.events if e["map"]==symbol} for symbol in MAPS}
        for row in self.events:
            if row["kind"]=="warp":
                self.assertIn(tuple(row["arrival"]),exp.component(sc[row["destination"]]))
                self.assertNotIn(tuple(row["arrival"]),used[row["destination"]])
    def test_09_start_inside_bedroom_not_on_event(self):
        self.assertIn(self.start,exp.component(exp.all_scenes()["SINNOH_PLAYER_BEDROOM"]))
        self.assertNotIn(self.start,[tuple(r["position"]) for r in self.events if r["map"]=="SINNOH_PLAYER_BEDROOM"])
    def test_10_all_nine_event_maps_have_native_rpg_event_objects(self):
        for symbol,mid in self.mapping.items():
            map_obj=read_marshal(self.ready["Data/Map%03d.rxdata"%mid],"M")
            self.assertEqual(map_obj.name,"RPG::Map")
            self.assertGreater(len(map_obj.attrs["@events"]),0)
            for event in map_obj.attrs["@events"].values():
                self.assertEqual(event.name,"RPG::Event")
    def test_11_all_source_layers_unchanged_after_event_compile(self):
        for s,mid in self.mapping.items():
            src=read_marshal(self.empty["Data/Map%03d.rxdata"%mid],"SRC")
            out=read_marshal(self.ready["Data/Map%03d.rxdata"%mid],"OUT")
            self.assertEqual(src.attrs["@data"].data,out.attrs["@data"].data)
            self.assertEqual(src.attrs["@tileset_id"],out.attrs["@tileset_id"])
    def test_12_events_are_not_human_reviewed_or_native_proven(self):
        self.assertTrue(all(e["model_reachable"] is True for e in self.events))
        self.assertTrue(all(e["human_reviewed"] is False and e["native_engine_verified"] is False for e in self.events))
    def test_13_no_write_during_event_generation(self):
        exp.compile_events(self.empty,self.mapping)
        self.assertFalse((self.root/".blue-work").exists())
    def test_14_client_r07_only_finds_free_ids(self):
        with patch.object(exp,"native_map_ids",return_value={2,443,445,447}):
            ids,mapping,occupied=exp.select_ids(self.base,self.infos)
        self.assertEqual(len(ids),9)
        self.assertTrue(set(ids).isdisjoint(occupied))
    def test_15_client_r07_never_declares_independent_authorization(self):
        self.assertFalse(self.meta["r07_globally_approved"])
    def test_16_reject_r07_without_nine_free_ids(self):
        with patch.object(exp,"native_map_ids",return_value=set(range(442,514))):
            self.reject(lambda:exp.select_ids(self.base,self.infos))
    def test_17_reject_duplicate_id_or_overlay_collision(self):
        self.reject(lambda:j11c.candidate_ids({442},set(),self.ids))
    def test_18_svg_and_png_assets_do_not_include_official_downloads(self):
        self.assertNotIn("requests.get",Path(exp.__file__).read_text())
        self.assertNotIn("urllib.request",Path(exp.__file__).read_text())
    def test_19_original_npc_sprite_is_a_valid_128px_png(self):
        blob=exp.sprite_png("NPC")
        self.assertTrue(blob.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(struct.unpack_from(">II",blob,16),(128,128))
    def test_20_original_ball_sprite_is_independent_of_npc(self):
        self.assertNotEqual(exp.sha(exp.sprite_png("NPC")),exp.sha(exp.sprite_png("BALL")))
    def test_21_sprites_decode_to_rgba_with_actual_drawing(self):
        for kind in ("NPC","BALL"):
            blob=exp.sprite_png(kind)
            off=8;stream=b""
            while off<len(blob):
                size=struct.unpack_from(">I",blob,off)[0]
                tag=blob[off+4:off+8]
                data=blob[off+8:off+8+size]
                self.assertEqual(zlib.crc32(tag+data)&0xffffffff,struct.unpack_from(">I",blob,off+8+size)[0])
                if tag==b"IDAT":stream+=data
                off+=size+12
            pixels=zlib.decompress(stream)
            self.assertEqual(len(pixels),128*(128*4+1))
            self.assertGreater(sum(x!=0 for x in pixels),500)
    def test_22_reject_invalid_sprite_type(self):
        self.reject(lambda:exp.sprite_png("PikachuOfficial"))
    def test_23_save_namespace_has_distinct_app_and_org(self):
        config,ini,profile=exp.runtime_config(self.base,"abc123abc123")
        self.assertNotEqual(profile["dataPathApp"],"BASE_APP")
        self.assertEqual(json.loads(config)["dataPathApp"],profile["dataPathApp"])
        self.assertIn(profile["title"],ini.decode())
    def test_24_reject_explicit_save_path_in_mkxp(self):
        (self.base/"mkxp.json").write_text('{"savePath":"C:/Users/Other/Saves","windowTitle":"X"}')
        self.reject(lambda:exp.runtime_config(self.base,"abc123abc123"))
    def test_25_reject_missing_game_ini_title(self):
        (self.base/"Game.ini").write_text("Library=RGSS104E.dll")
        self.reject(lambda:exp.runtime_config(self.base,"abc123abc123"))
    def test_26_no_save_files_in_snapshot(self):
        files=exp.scan_source(self.base)
        self.assertNotIn("Data/File A.rxdata",files)
        self.assertFalse(any("Saves" in x for x in files))
    def test_27_only_expected_root_files_are_copied(self):
        (self.base/"private-secrets.txt").write_text("do not copy")
        files=exp.scan_source(self.base)
        self.assertNotIn("private-secrets.txt",files)
        self.assertIn("Game.exe",files)
    def test_28_reject_game_file_symlinks(self):
        try:(self.base/"Graphics"/"bad.txt").symlink_to(self.base/"Game.exe")
        except (OSError,NotImplementedError):self.skipTest("Windows runner has no symlink privilege")
        self.reject(lambda:exp.scan_source(self.base))
    def test_29_scanning_existing_game_does_not_modify_base(self):
        before={p:p.read_bytes() for p in self.base.rglob("*") if p.is_file()}
        exp.scan_source(self.base)
        self.assertTrue(all(p.read_bytes()==blob for p,blob in before.items()))
    def test_30_private_copy_only_alters_destination(self):
        token="abc123abc123"
        data={"Data/Map442.rxdata":b"test QA map",
              "Data/MapInfos.rxdata":b"test mapinfos",
              "mkxp.json":b'{"dataPathApp":"Sinnoh-QA-abc123abc123"}'}
        report={"profile_token":token,"mapids":{"TEST":442},
                "save_profile":{"dataPathApp":"Sinnoh-QA-abc123abc123"},
                "file_sha256":{p:exp.sha(raw) for p,raw in data.items()}}
        path=exp.install_copy(self.base,data,report,self.proj)
        self.assertTrue((path/"Game.exe").exists())
        self.assertEqual((self.base/"Data/MapInfos.rxdata").read_bytes(),b"synthetic test only")
        self.assertFalse((path/"Saves").exists())
        self.assertTrue((path/"INICIAR_SINNOH_EXPERIMENTAL.bat").exists())
    def test_31_never_overwrite_old_private_copy(self):
        report={"profile_token":"abc123abc123","mapids":{},
                "save_profile":{},"file_sha256":{}}
        outputs={"mkxp.json":b"QA"}
        exp.install_copy(self.base,outputs,report,self.proj)
        self.reject(lambda:exp.install_copy(self.base,outputs,report,self.proj))
    def test_32_reject_output_collision_with_real_map(self):
        report={"profile_token":"abc123abc123","mapids":{},
                "save_profile":{},"file_sha256":{}}
        self.reject(lambda:exp.install_copy(self.base,{"Data/Map002.rxdata":b"override"},report,self.proj))
    def test_33_reject_output_in_game_source_tree(self):
        report={"profile_token":"abc123abc123","mapids":{},
                "save_profile":{},"file_sha256":{}}
        self.reject(lambda:exp.install_copy(self.base,{"mkxp.json":b"qa"},report,self.base))
    def test_34_compiler_includes_barry_native_three_version_check(self):
        source=Path(exp.__file__).read_text()
        self.assertIn("GameData::Trainer.exists?",source)
        self.assertIn("sinnoh-experimental-compile-error.txt",source)
    def test_35_experimental_game_start_has_sinnoh_scope(self):
        data=exp.experiment_plugin([442,10,8],"abcdef123456").decode()
        self.assertIn('BlueRegions.new_state("SINNOH")',data)
        self.assertIn("start_map_id = START[0]",data)
        self.assertIn("abc",exp.experiment_plugin([442,10,8],"abc123abc123").decode())
    def test_36_public_pilot_status_remains_zero(self):
        x=json.loads((ROOT/"data/regions/sinnoh-playable-progress.json").read_text())
        self.assertEqual(x["status"],"PILOT_NOT_INSTALLED_NOT_PLAYABLE")
        self.assertEqual(x["native_windows_cases_executed"]+x["native_android_cases_executed"],0)
        self.assertFalse(x["main_game_modified"])

if __name__=="__main__":
    unittest.main()
