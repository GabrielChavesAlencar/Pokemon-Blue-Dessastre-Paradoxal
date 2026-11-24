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
from server.ruby_marshal import RubyObject, RubyData
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
    def test_visual_upgrade_all_nine_and_metadata(self):
        visual=exp.visual
        out=visual.upgrade(self.ready,self.mapping,self.meta["tileset_ids"],self.events,self.start)
        ts=read_marshal(out["Data/Tilesets.rxdata"],"VISUAL_TEST")
        old=read_marshal(self.ready["Data/Tilesets.rxdata"],"OLD_TEST")
        self.assertEqual(serialize(ts[1]),serialize(old[1]))
        self.assertEqual(out["Data/MapInfos.rxdata"],self.ready["Data/MapInfos.rxdata"])
        for sym,mid in self.mapping.items():
            rel="Data/Map%03d.rxdata"%mid
            a=read_marshal(out[rel],"VISUAL_MAP_TEST").attrs
            b=read_marshal(self.ready[rel],"ORIGINAL_MAP_TEST").attrs
            self.assertEqual((a["@width"],a["@height"]),(b["@width"],b["@height"]))
            self.assertEqual(set(a["@events"]),set(b["@events"]))
            self.assertNotEqual(a["@data"].data,b["@data"].data)
            group="J11B_EXTERIORS" if sym in visual.OUTSIDE else "J10A_INTERIORS"
            self.assertEqual(a["@tileset_id"],self.meta["tileset_ids"][group])
            tile=ts[a["@tileset_id"]].attrs
            for table in ("@passages","@priorities","@terrain_tags"):
                self.assertEqual(struct.unpack_from("<5I",tile[table].data),(1,448,1,1,448))
            ids=struct.unpack_from("<"+str(a["@width"]*a["@height"]*3)+"H",a["@data"].data,20)
            self.assertTrue(all(t==0 or 48<=t<192 or 384<=t<448 for t in ids))
        self.assertEqual(struct.unpack_from(">II",out["Graphics/Autotiles/SNQA_WaterV2.png"],16),(288,128))
        for kind in ("Path","Grass"):
            self.assertEqual(struct.unpack_from(">II",out["Graphics/Autotiles/SNQA_"+kind+"V2.png"],16),(96,128))
        for symbol in ("SINNOH_ROUTE_201","SINNOH_ROUTE_202"):
            a=read_marshal(out["Data/Map%03d.rxdata"%self.mapping[symbol]],"ROUTE_VISUAL").attrs
            ids=struct.unpack_from("<"+str(a["@width"]*a["@height"]*3)+"H",a["@data"].data,20)
            self.assertTrue(any(96<=t<144 for t in ids))
            self.assertTrue(any(144<=t<192 for t in ids))
            ts_data=ts[a["@tileset_id"]].attrs
            self.assertEqual(ts_data["@autotile_names"][:3],[b"SNQA_WaterV2",b"SNQA_PathV2",b"SNQA_GrassV2"])
            p=struct.unpack_from("<448H",ts_data["@passages"].data,20)
            tags=struct.unpack_from("<448H",ts_data["@terrain_tags"].data,20)
            self.assertTrue(all(p[t]==0 and tags[t]==0 for t in range(96,192)))
        for group,(_,name) in j11c.GRAPHIC.items():
            self.assertEqual(struct.unpack_from(">II",out["Graphics/Tilesets/"+name+".png"],16),(256,256))
        sprites=[out["Graphics/Characters/SNQA_"+n+".png"] for n in ("MOTHER","BARRY","ROWAN")]
        self.assertEqual(len(set(sprites)),3)
        self.assertEqual(set(e["sprite"] for e in self.events if e["kind"]=="handler"),
                         {"SNQA_MOTHER","SNQA_BARRY","SNQA_ROWAN"})

    def test_ground_autotile_all_47_topologies(self):
        shape=exp.visual.autotile_shape
        self.assertEqual({shape(s,c) for s in range(16) for c in range(16)},set(range(47)))
        self.assertEqual(shape(0,0),0)
        self.assertEqual(shape(0,15),15)
        self.assertEqual(shape(15,15),46)
        self.assertEqual(shape(10,15),32)
        self.assertEqual(shape(5,15),33)
        with self.assertRaises(ValueError):shape(16,0)

    def test_visual_reciprocal_portals_land_near_other_end(self):
        for e in self.events:
            if e["kind"]!="warp":continue
            other=next(x for x in self.events if x["kind"]=="warp" and
                       x["map"]==e["destination"] and x["destination"]==e["map"])
            reach=exp.component(exp.all_scenes()[e["destination"]])
            used={tuple(x["position"]) for x in self.events if x["map"]==e["destination"]}
            self.assertEqual(tuple(e["arrival"]),exp.choose_point(reach,tuple(other["position"]),used))

    def test_visual_variants_keep_semantics_and_water_animation(self):
        visual=exp.visual
        self.assertEqual(visual.parent(35),16)
        self.assertEqual(visual.parent(48),6)
        self.assertNotEqual(visual.atlas(False),visual.atlas(True))
        self.assertEqual(visual.atlas(True),visual.atlas(True))
        self.assertEqual(visual.remap_cells([402,0,0],1,1,True),[48,0,0])
        with self.assertRaises(ValueError):visual.remap_cells([999,0,0],1,1,True)

    def test_private_map_source_contract_and_platinum_player(self):
        pv=exp.private_visual
        self.assertEqual(len(pv.DONOR),5)
        self.assertEqual({v[0] for v in pv.DONOR.values()},{191,192,193,194,196})
        self.assertEqual(set(pv.SPRITES),{"MOTHER","BARRY","ROWAN"})
        self.assertIn("pbChangePlayer(9)",exp.experiment_plugin([442,10,8],"abc123abc123",True).decode())
        self.assertNotIn("pbChangePlayer(9)",exp.experiment_plugin([442,10,8],"abc123abc123").decode())
        dual=exp.experiment_plugin([442,10,8],"abc123abc123",True,True).decode()
        self.assertIn('["Lucas", "Dawn"]',dual)
        self.assertIn("pbChangePlayer(choice == 1 ? 10 : 9)",dual)
        self.assertIn("pbChangePlayer(10)",exp.experiment_plugin([442,10,8],"abc123abc123",False,True).decode())

    def test_private_map_component_rejects_blocked_seed_and_disconnected_tiles(self):
        pv=exp.private_visual
        p=[0]*386;p[385]=15
        cells=[384,385,384,384,385,384]+[0]*12
        self.assertEqual(pv.connected(cells,3,2,p,(0,0)),{(0,0),(0,1)})
        with self.assertRaisesRegex(ValueError,"DONOR_SEED_BLOCKED"):
            pv.connected(cells,3,2,p,(1,0))

    def test_private_compact_atlas_keeps_exact_source_pixels_and_indices(self):
        pv=exp.private_visual
        rows=[bytes([10,20,30,255])*32+bytes([40,50,60,255])*32+bytes(768) for _ in range(32)]
        with patch.object(pv,"rgba_rows",return_value=iter(rows)):
            blob,remap=pv.compact_atlas(b"synthetic",{384,385})
        self.assertEqual(remap,{384:384,385:385})
        self.assertEqual(pv.dims(blob),(256,32))
        off=8;payload=b""
        while off<len(blob):
            n=struct.unpack_from(">I",blob,off)[0]
            if blob[off+4:off+8]==b"IDAT":payload+=blob[off+8:off+8+n]
            off+=n+12
        raw=zlib.decompress(payload)
        self.assertEqual(raw[1:257],rows[0][:256])
        with self.assertRaises(ValueError):pv.compact_atlas(b"",{383})

    def test_private_full_import_rebuilds_nine_maps_and_all_events(self):
        # Synthetic donor: same structural shape, no downloaded assets in CI.
        pv=exp.private_visual
        tables=[None]*26
        for tid,name in ((24,b"outdoors"),(25,b"indoors")):
            ts=copy.deepcopy(self.tiles[1]);ts.attrs.update({
                "@id":tid,"@name":name,"@tileset_name":name,
                "@autotile_names":[b"A"]*7 if tid==24 else [b""]*7})
            for key in ("@passages","@priorities","@terrain_tags"):
                ts.attrs[key]=j11c.table1([0]*7880)
            tables[tid]=ts
        infos={}
        members={}
        for symbol,(mid,name,(w,h)) in pv.DONOR.items():
            infos[mid]=RubyObject("RPG::MapInfo",{"@name":name})
            original=read_marshal(self.empty["Data/Map%03d.rxdata"%self.mapping[symbol]],"SYNTHETIC_DONOR")
            original.attrs.update({"@width":w,"@height":h,"@tileset_id":24,
                "@data":RubyData("Table",struct.pack("<5I",3,w,h,3,w*h*3)+
                       struct.pack("<%dH"%(w*h*3),*([384]*(w*h)+[0]*(2*w*h))))})
            members[pv.MAP_ROOT+"Data/Map%03d.rxdata"%mid]=serialize(original)
        members[pv.MAP_ROOT+"Data/MapInfos.rxdata"]=serialize(infos)
        members[pv.MAP_ROOT+"Data/Tilesets.rxdata"]=serialize(tables)
        fake_png=exp.visual.png(32,32,bytes(32*32*4))
        for name in ("Tilesets/outdoors.png","Tilesets/indoors.png","Autotiles/A.png"):
            members[pv.MAP_ROOT+"Graphics/"+name]=fake_png
        def compact(raw,ids):
            remap={t:384+i for i,t in enumerate(sorted(ids))}
            h=((len(ids)+7)//8)*32
            return exp.visual.png(256,h,bytes(256*h*4)),remap
        old=exp.visual.upgrade(self.ready,self.mapping,self.meta["tileset_ids"],self.events,self.start)
        with patch.object(pv,"verified_archive"),patch.object(pv,"member",side_effect=lambda z,n,*a:members[n]),patch.object(pv,"compact_atlas",side_effect=compact):
            maps,components,report=pv.apply_maps(old,self.mapping,"synthetic")
        self.assertEqual(set(report),set(self.mapping))
        self.assertEqual(set(components),set(self.mapping))
        self.assertEqual(maps["Data/MapInfos.rxdata"],old["Data/MapInfos.rxdata"])
        for symbol in pv.INTERIOR_SIZES:
            self.assertIsNone(report[symbol]["source_id"])
            self.assertTrue(report[symbol]["authored_layout"])
        maps,events,start=exp.compile_events(maps,self.mapping,components,{**pv.ANCHORS,**pv.INTERIOR_ANCHORS})
        self.assertEqual(len(events),24)
        self.assertEqual(sum(e["kind"]=="warp" for e in events),16)
        self.assertEqual({e["key"] for e in events},{e["key"] for e in self.events})
        self.assertIn(start,components["SINNOH_PLAYER_BEDROOM"])
        for e in events:
            self.assertIn(tuple(e["position"]),components[e["map"]])
            if e["kind"]=="warp":self.assertIn(tuple(e["arrival"]),components[e["destination"]])
        for symbol,mid in self.mapping.items():
            m=read_marshal(maps["Data/Map%03d.rxdata"%mid],"FINAL_PRIVATE")
            self.assertEqual(len(m.attrs["@events"]),sum(e["map"]==symbol for e in events))
        old_tiles=read_marshal(old["Data/Tilesets.rxdata"],"OLD_PRIVATE")
        new_tiles=read_marshal(maps["Data/Tilesets.rxdata"],"NEW_PRIVATE")
        self.assertEqual(new_tiles[:len(old_tiles)],old_tiles)
        self.assertEqual(len(new_tiles),len(old_tiles)+2)

    def test_private_interior_layouts_are_complete_and_in_range(self):
        pv=exp.private_visual
        self.assertEqual(len(pv.INTERIOR_SIZES),4)
        for symbol,(w,h) in pv.INTERIOR_SIZES.items():
            cells=pv.interior_cells(symbol)
            self.assertEqual(len(cells),w*h*3)
            self.assertTrue(all(384<=t<7880 for t in cells[:w*h]))
            self.assertTrue(all(t==0 or 384<=t<7880 for t in cells))
            self.assertGreater(len(set(cells)),25)
            self.assertGreater(sum(t!=0 for t in cells[w*h:]),10)

    def test_private_archives_are_hash_pinned_and_not_extracted(self):
        pv=exp.private_visual
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"Sinnoh Maps.zip";path.write_bytes(b"not the original")
            with self.assertRaisesRegex(ValueError,"ARCHIVE_SHA256_MISMATCH"):
                pv.verified_archive(path,"maps")

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

    def test_37_blues_story_managed_game_subfolder_can_make_private_qa_copy(self):
        # Real Blue-Story layout: project/game is the read-only input;
        # project/.blue-work is the ONLY destination. Old overlap guard
        # incorrectly rejected every user installation in this layout.
        project=self.root/"managed-BlueStory"
        game=project/"game"
        game.mkdir(parents=True)
        for relative in ("Game.exe","Game.ini","mkxp.json","Data/MapInfos.rxdata",
                         "Data/Tilesets.rxdata","Data/Scripts.rxdata","Data/System.rxdata"):
            dst=game/relative
            dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_bytes(b"synthetic original - never changed")
        saves=game/"Saves"/"File A.rxdata"
        saves.parent.mkdir()
        saves.write_bytes(b"private synthetic save")
        data={"Data/Map442.rxdata":b"synthetic QA map",
              "Data/MapInfos.rxdata":b"synthetic QA infos",
              "mkxp.json":b'{"dataPathApp":"SinnohQA"}'}
        report={"profile_token":"a1b2c3d4e5f6","mapids":{"QA":442},
                "save_profile":{"dataPathApp":"SinnohQA"},
                "file_sha256":{k:exp.sha(v) for k,v in data.items()}}
        out=exp.install_copy(game,data,report,project)
        self.assertTrue((out/"INICIAR_SINNOH_EXPERIMENTAL.bat").is_file())
        self.assertTrue(out.is_relative_to(project/".blue-work"))
        self.assertEqual((game/"Data/MapInfos.rxdata").read_bytes(),
                         b"synthetic original - never changed")
        self.assertEqual(saves.read_bytes(),b"private synthetic save")
        self.assertFalse((out/"Saves").exists())
        self.assertEqual((out/"Data/Map442.rxdata").read_bytes(),b"synthetic QA map")

    def test_38_reject_any_other_nested_game_directory(self):
        project=self.root/"managed-BlueStory"
        game=project/"other-game"
        game.mkdir(parents=True)
        self.reject(lambda:exp.install_copy(game,{},{"profile_token":"aaa"},project))

    def test_39_reject_qa_workdir_inside_game_source(self):
        project=self.root/"custom-root"
        game=project/"game"
        game.mkdir(parents=True)
        # Even if a future layout points at the game's own directory,
        # direct copies into the source tree must never be accepted.
        self.reject(lambda:exp.install_copy(game,{},{"profile_token":"aaa"},game))

    def test_40_private_qa_only_updates_title_plugin_not_original(self):
        title=exp.QA_TITLE_PLUGIN
        original=b"legacy test menu - no new routing"
        source=b"updated standalone QA TitleKanto - project owned"
        installed=self.base/title
        installed.parent.mkdir(parents=True,exist_ok=True)
        installed.write_bytes(original)
        project_source=self.proj/"scripts/battle_polish/TitleKanto.rb"
        project_source.parent.mkdir(parents=True,exist_ok=True)
        project_source.write_bytes(source)
        outputs={title:source}
        report={"profile_token":"abc123abc123","mapids":{},
                "save_profile":{},"file_sha256":{title:exp.sha(source)}}
        qa=exp.install_copy(self.base,outputs,report,self.proj)
        self.assertEqual((qa/title).read_bytes(),source)
        self.assertEqual(installed.read_bytes(),original)
        self.assertFalse((qa/"Saves").exists())

    def test_41_reject_untrusted_title_plugin_replacement(self):
        title=exp.QA_TITLE_PLUGIN
        path=self.base/title
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(b"legacy")
        project_source=self.proj/"scripts/battle_polish/TitleKanto.rb"
        project_source.parent.mkdir(parents=True,exist_ok=True)
        project_source.write_bytes(b"reviewed")
        report={"profile_token":"abc123abc123","mapids":{},
                "save_profile":{},"file_sha256":{}}
        self.reject(lambda:exp.install_copy(self.base,
                    {title:b"tampered or unrelated code"},report,self.proj))
        self.assertEqual(path.read_bytes(),b"legacy")

    def test_42_new_qa_pilot_uses_reviewed_title_source(self):
        script=(ROOT/"scripts/regions/install_sinnoh_experimental_windows.py").read_text("utf-8")
        self.assertIn('QA_TITLE_PLUGIN:(project/"scripts/battle_polish/TitleKanto.rb").read_bytes()',script)
        self.assertIn('QA_TITLE_PLUGIN="Plugins/ZZZZ Blue Story and Presentation/TitleKanto.rb"',script)
        self.assertIn('QA_TITLE_PLUGIN_OVERRIDE_NOT_TRUSTED',script)

    def test_43_map_only_bootstrap_never_uses_barry_marker_to_authorize_new_game(self):
        script=exp.experiment_plugin([442,10,8],"abc123abc123").decode()
        self.assertIn('BlueKantoTitle.sinnoh_experimental_maps_ready?',script)
        self.assertNotIn('raise "Sinnoh QA: compile o PBS de Barry antes de Novo Jogo"',script)
        self.assertIn('raise "Sinnoh QA: mapas ou perfil privado invalidos"',script)

    def test_44_barry_battle_remains_separately_restricted(self):
        src=(ROOT/"scripts/regions/SinnohPilot.rb").read_text("utf-8")
        self.assertIn('BlueKantoTitle.sinnoh_experimental_barry_compiled?',src)
        self.assertIn('BlueKantoTitle.sinnoh_experimental_maps_ready?',src)
        self.assertIn('all_rival_versions_valid?',src)
        self.assertIn('compiled_rival_valid?',src)

    def test_45_private_launcher_does_not_block_map_testing_when_barry_missing(self):
        root=self.root/"qa-bat-test"
        game=root/"game"
        project=root
        game.mkdir(parents=True)
        (game/"Game.exe").write_bytes(b"synthetic Game.exe")
        (game/"Game.ini").write_text("Title=synthetic game\n")
        (game/"mkxp.json").write_text('{"windowTitle":"synthetic"}')
        (game/"Data").mkdir()
        (game/"Data/MapInfos.rxdata").write_bytes(b"original")
        for fname in ("Tilesets.rxdata","Scripts.rxdata","System.rxdata"):
            (game/"Data"/fname).write_bytes(b"synthetic")
        (game/"Data/Map002.rxdata").write_bytes(b"main map")
        report={"profile_token":"abc123abc123","mapids":{},
                "save_profile":{},"file_sha256":{}}
        qa=exp.install_copy(game,{},report,project)
        launcher=(qa/"INICIAR_SINNOH_EXPERIMENTAL.bat").read_text("utf-8")
        self.assertIn("Apenas EXPLORACAO dos 9 mapas QA.",launcher)
        self.assertIn("Batalha contra Barry bloqueada",launcher)
        self.assertNotIn("nao iniciar Novo Jogo",launcher)
        self.assertNotIn("pause",launcher.lower())
        self.assertNotIn("exit /b 2",launcher)
        self.assertEqual((game/"Data/MapInfos.rxdata").read_bytes(),b"original")

    def test_46_pristine_tilesets_are_included_in_manifest_hashes(self):
        # No system game or native map/saves are needed for this contract.
        source=Path(exp.__file__).read_text("utf-8")
        self.assertIn('final["Data/sinnoh-experimental-tilesets-pristine.bin"]=final["Data/Tilesets.rxdata"]',source)
        self.assertIn('sha(content) for path,content in final.items()',source)
        self.assertIn('File.delete("Data/sinnoh-experimental-compile-request.txt")',source)
        content=b"RPG Tilesets synthetic fixture, exact byte preservation"
        report={"profile_token":"abc123abc123","mapids":{},
                "save_profile":{},"file_sha256":{}}
        outputs={"Data/Tilesets.rxdata":content,
                 "Data/sinnoh-experimental-tilesets-pristine.bin":content}
        qa=exp.install_copy(self.base,outputs,report,self.proj)
        self.assertEqual((qa/"Data/Tilesets.rxdata").read_bytes(),content)
        self.assertEqual((qa/"Data/sinnoh-experimental-tilesets-pristine.bin").read_bytes(),content)
        self.assertNotEqual((qa/"Data/Tilesets.rxdata").stat().st_ino,
                            (qa/"Data/sinnoh-experimental-tilesets-pristine.bin").stat().st_ino)

if __name__=="__main__":
    unittest.main()
