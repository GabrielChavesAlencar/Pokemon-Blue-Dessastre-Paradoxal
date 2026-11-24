"""Sinnoh J12E: experimental installer contract and adversarial regression suite.

Runs without any user game, Game.exe launch, save reads or credentials.
"""
from __future__ import annotations
import copy
from pathlib import Path
import json
import os
import shutil
import subprocess
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
    @unittest.skipUnless(shutil.which("ruby"),"Requires Ruby runtime")
    def test_f02_forest_only_fills_void_respects_maps_and_disposes(self):
        script=(exp.ROOT/"scripts/regions/SinnohForestEdge.rb").read_text("utf-8").replace("__F02_MAP_IDS__","[442,443]")
        fixture=r'''
module BlueSinnohExperimental
  def self.private_copy?; $private; end
end
Map=Struct.new(:map_id)
Tile=Struct.new(:tile_id)
class Bitmap
  attr_reader :disposed
  def initialize(path); raise "wrong art" unless path.end_with?("SNQA_ForestEdge.png"); end
  def disposed?; !!@disposed; end
  def dispose; @disposed=true; end
end
class Rect
  attr_reader :args
  def set(*args); @args=args; end
end
class Sprite
  attr_accessor :bitmap,:z,:zoom_x,:zoom_y,:x,:y,:tone,:color,:visible
  attr_reader :src_rect
  def initialize(viewport); @src_rect=Rect.new; end
  def disposed?; !!@disposed; end
  def dispose; @disposed=true; end
end
class TilemapRenderer
  DISPLAY_TILE_WIDTH=32;DISPLAY_TILE_HEIGHT=32;ZOOM_X=1;ZOOM_Y=1
  attr_reader :tiles
  def initialize
    @viewport=Object.new
    @tiles=[[[Tile.new(0),Tile.new(0),Tile.new(0)],
             [Tile.new(400),Tile.new(0),Tile.new(0)]],
            [[Tile.new(0),Tile.new(49),Tile.new(0)],
             [Tile.new(0),Tile.new(0),Tile.new(0)]]]
    @pixel_offset_x=5;@pixel_offset_y=7
    @tile_offset_x=1;@tile_offset_y=2
    @tone=:night;@color=:flash
  end
  def update; :native_result; end
  def dispose; @native_disposed=true; end
end
load ARGV[0]
$private=false;$game_map=Map.new(442)
BlueSinnohForestEdge.install!
raise "global hook" if TilemapRenderer.ancestors.include?(BlueSinnohForestEdge::Renderer)
$private=true
BlueSinnohForestEdge.install!
BlueSinnohForestEdge.install!
r=TilemapRenderer.new
raise "native update return" unless r.update==:native_result
sprites=r.instance_variable_get(:@blue_sinnoh_forest_sprites)
raise "painted real tiles" unless sprites.keys.sort==[[0,0],[1,1]]
s=sprites[[0,0]]
raise "wrong position" unless [s.x,s.y,s.z,s.src_rect.args]==[-5,-7,-1000,[32,0,32,32]]
raise "wrong tone" unless s.tone==:night && s.color==:flash
r.tiles[0][0][0].tile_id=401
r.update
raise "seam overwritten" if s.visible
r.tiles[0][0][0].tile_id=0
r.update
raise "lost background" unless s.visible && sprites[[0,0]].equal?(s)
$game_map.map_id=999
r.update
raise "foreign map affected" if sprites.values.any?(&:visible)
$game_map.map_id=443
r.update
raise "connected map lost" unless s.visible
$private=false
r.update
raise "outside QA affected" if sprites.values.any?(&:visible)
bitmap=s.bitmap
r.dispose
raise "resource leak" unless bitmap.disposed? && s.disposed? && sprites.empty?
raise "native dispose skipped" unless r.instance_variable_get(:@native_disposed)
'''
        with tempfile.TemporaryDirectory() as tmp:
            rb=Path(tmp)/"edge.rb";rb.write_text(script,encoding="utf-8")
            result=subprocess.run([shutil.which("ruby"),"-e",fixture,str(rb)],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_f01_catalog_has_all_cities_routes_and_no_unverified_ids(self):
        rows=exp.qa_teleport.catalog()
        self.assertEqual(len({r["symbol"] for r in rows}),len(rows))
        self.assertEqual(sum(r["category"]=="Cidades e vilarejos" for r in rows),14)
        self.assertEqual({r["symbol"] for r in rows if r["category"]=="Rotas"},
                         {"SINNOH_ROUTE_"+str(i) for i in range(201,231)})
        self.assertTrue(all("map_id" not in r for r in rows))

    @unittest.skipUnless(shutil.which("ruby"),"Requires Ruby runtime")
    def test_f01_teleport_menu_is_private_and_preserves_story(self):
        rows=[["SINNOH_ROUTE_201","Route 201","Rotas",[442,2,3]],
              ["SINNOH_ROUTE_202","Route 202","Rotas",[443,4,5]],
              ["SINNOH_ROUTE_203","Route 203","Rotas",None]]
        script=r'''
module BlueSinnohExperimental
  def self.private_copy?; $private; end
end
module BlueKantoTitle
  def self.sinnoh_experimental_maps_ready?; $ready; end
end
module MenuHandlers
  def self.add(*args); $registered=args; end
end
Map=Struct.new(:map_id) do
  def autoplay; end
  def refresh; end
end
Global=Struct.new(:blue_regions)
Temp=Struct.new(:in_menu,:player_new_map_id,:player_new_x,:player_new_y,:player_new_direction)
class Game_Event
  attr_reader :map_id,:trigger,:name,:calls
  def initialize(id,trigger,name); @map_id=id;@trigger=trigger;@name=name;@calls=0; end
  def check_event_trigger_auto; @calls+=1; end
end
class Scene
  def transfer_player; $game_map.map_id=$game_temp.player_new_map_id; end
end
class Menu
  attr_reader :closed
  def pbHideMenu; end
  def pbRefresh; end
  def pbShowMenu; end
  def pbEndScene; @closed=true; end
end
def _INTL(s,*args); s; end
def pbMessage(*args); args.length>1 ? $choices.shift : nil; end
def pbConfirmMessage(*args); $confirm; end
def pbFadeOutIn; yield; end
def pbDismountBike; end
load ARGV[0]
$private=false;$ready=true;$player=Object.new;$game_player=Object.new
$game_map=Map.new(442);$PokemonGlobal=Global.new({"current"=>"SINNOH","flags"=>{"starter"=>false}})
$game_temp=Temp.new(true);$scene=Scene.new;$confirm=true
BlueSinnohQATeleport.install!
raise "outside QA registered" if $registered
$private=true
BlueSinnohQATeleport.install!
raise "missing menu" unless $registered[1]==:blue_sinnoh_qa_teleport
before=Marshal.dump($PokemonGlobal.blue_regions)
$choices=[1,2]
raise "pending teleport allowed" if BlueSinnohQATeleport.open(Menu.new)
$choices=[1,1];$confirm=false
raise "cancel failed" if BlueSinnohQATeleport.open(Menu.new)
$choices=[1,1];$confirm=true;$ready=false
raise "hash gate bypass" if BlueSinnohQATeleport.open(Menu.new)
$choices=[1,1];$ready=true
raise "transfer failed" unless BlueSinnohQATeleport.open(Menu.new)
raise "wrong target" unless $game_map.map_id==443 && $game_temp.player_new_x==4 && $game_temp.player_new_y==5
raise "story changed" unless before==Marshal.dump($PokemonGlobal.blue_regions)
event=Game_Event.new(443,3,"SN_DEX_SCENE")
event.check_event_trigger_auto
raise "autorun fired" unless event.calls==0
ordinary=Game_Event.new(443,2,"SN_DEX_SCENE")
ordinary.check_event_trigger_auto
raise "ordinary event suppressed" unless ordinary.calls==1
$game_map.map_id=442
BlueSinnohQATeleport.clear_arrival_if_left
event.check_event_trigger_auto
raise "autorun remained suppressed" unless event.calls==1
$PokemonGlobal.blue_regions["current"]="KANTO"
raise "foreign region exposed" if BlueSinnohQATeleport.available?
'''
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)
            (path/"Data").mkdir()
            (path/"Data/Map443.rxdata").write_bytes(b"fixture")
            rb=path/"teleport.rb";rb.write_bytes(exp.qa_teleport.plugin(rows))
            proc=subprocess.run([shutil.which("ruby"),"-e",script,str(rb)],cwd=path,capture_output=True,text=True,timeout=30)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)

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


    def test_private_connections_and_audio_preserve_pilot_and_base(self):
        pv=exp.private_visual
        # Only synthetic tracks and edges; no third-party media in CI.
        base_rows=[[2,b"N",0,3,b"S",0]]
        old_pbs=b"# original region\n2,N,0,3,S,0\n"
        old_meta=b"[002]\nName = Original\n"
        (self.base/"Data/map_connections.dat").write_bytes(serialize(base_rows))
        (self.base/"PBS/map_connections.txt").write_bytes(old_pbs)
        (self.base/"PBS/map_metadata.txt").write_bytes(old_meta)
        components={}
        for symbol,(_,_,(w,h)) in pv.DONOR.items():
            components[symbol]={(x,y) for x in range(w) for y in range(h)}
        donor_rows=b"194,North,2,193,South,0\n193,East,0,192,West,4\n192,North,0,191,South,6\n191,North,0,106,South,27\n"
        fake_audio=b"OggS"+b"\x01vorbis"+bytes(64)
        def get_member(z,name,*args):
            if name.endswith("map_connections.txt"):return donor_rows
            if name.endswith(".ogg"):return fake_audio
            self.fail(name)
        with patch.object(pv,"verified_archive"),patch.object(pv,"member",side_effect=get_member):
            out,report=pv.bind_audio_and_connections(self.ready,self.mapping,components,"fixture",self.base)
        self.assertEqual(len(report["connections"]),3)
        self.assertEqual(len(report["retired_warp_keys"]),6)
        self.assertEqual(len(report["audio_files"]),7)
        self.assertEqual(set(report["map_music"]),set(self.mapping))
        compiled=read_marshal(out["Data/map_connections.dat"],"FIXTURE_CONNECTIONS")
        self.assertEqual(compiled[0],base_rows[0])
        self.assertEqual(len(compiled),4)
        self.assertTrue(all(row[0] in self.ids and row[3] in self.ids for row in compiled[1:]))
        self.assertTrue(out["PBS/map_connections.txt"].startswith(old_pbs))
        self.assertTrue(out["PBS/map_metadata.txt"].startswith(old_meta))
        self.assertEqual((self.base/"Data/map_connections.dat").read_bytes(),serialize(base_rows))
        self.assertEqual((self.base/"PBS/map_connections.txt").read_bytes(),old_pbs)
        self.assertEqual((self.base/"PBS/map_metadata.txt").read_bytes(),old_meta)
        self.assertEqual(out["Data/MapInfos.rxdata"],self.ready["Data/MapInfos.rxdata"])
        for rel in report["audio_files"]:self.assertEqual(out[rel],fake_audio)
        still_active=0
        for symbol,mid in self.mapping.items():
            path="Data/Map%03d.rxdata"%mid
            old=read_marshal(self.ready[path],"OLD").attrs
            new=read_marshal(out[path],"NEW").attrs
            self.assertEqual(new["@data"],old["@data"])
            self.assertTrue(new["@autoplay_bgm"])
            self.assertEqual(new["@bgm"].attrs["@name"],("SNQA_"+pv.MAP_MUSIC[symbol]).encode())
            self.assertEqual(set(new["@events"]),set(old["@events"]))
            for eid,event in new["@events"].items():
                if event.attrs["@name"].decode() in report["retired_warp_keys"]:
                    self.assertEqual([c.attrs["@code"] for c in event.attrs["@pages"][0].attrs["@list"]],[0])
                else:
                    self.assertEqual(event,old["@events"][eid])
                    still_active+=sum(c.attrs["@code"]==201 for c in event.attrs["@pages"][0].attrs["@list"])
        self.assertEqual(still_active,10)

    @unittest.skipUnless(os.environ.get("BLUE_SINNOH_PRIVATE_SOURCE"),"Requires explicitly supplied private archives")
    def test_live_private_continuity_and_audio(self):
        pv=exp.private_visual
        path=Path(os.environ["BLUE_SINNOH_PRIVATE_SOURCE"])
        (self.base/"Data/map_connections.dat").write_bytes(serialize([]))
        (self.base/"PBS/map_connections.txt").write_bytes(b"# Synthetic isolated baseline\n")
        (self.base/"PBS/map_metadata.txt").write_bytes(b"[002]\nName = Synthetic\n")
        maps=exp.visual.upgrade(self.ready,self.mapping,self.meta["tileset_ids"],self.events,self.start)
        maps,components,_=pv.apply_maps(maps,self.mapping,path)
        maps,events,start=exp.compile_events(maps,self.mapping,components,{**pv.ANCHORS,**pv.INTERIOR_ANCHORS})
        out,report=pv.bind_audio_and_connections(maps,self.mapping,components,path,self.base)
        self.assertEqual([p["reachable_seam_tiles"] for p in report["connections"]],[8,5,6])
        self.assertEqual(len(events),24)
        self.assertEqual(len(report["audio_files"]),7)
        with pv.verified_archive(path,"maps") as z:
            for key,(name,night) in pv.AUDIO.items():
                for suffix in ("","_n") if night else ("",):
                    self.assertEqual(out["Audio/BGM/SNQA_"+key+suffix+".ogg"],
                       pv.member(z,pv.MAP_ROOT+"Audio/BGM/"+name+suffix+".ogg"))
        self.assertEqual(len(read_marshal(out["Data/map_connections.dat"],"LIVE_CONNECTIONS")),3)
        print("SINNOH_REAL_SOURCE_3_SEAMS_7_BGM_9_MAPS_OK",flush=True)

    @unittest.skipUnless(os.environ.get("BLUE_SINNOH_PRIVATE_SOURCE"),"Requires explicitly supplied private archives")
    def test_live_private_continuity_and_audio_lakefront_story(self):
        pv=exp.private_visual
        source=Path(os.environ["BLUE_SINNOH_PRIVATE_SOURCE"])
        mapping={**self.mapping,pv.LAKEFRONT:451}
        (self.base/"Data/map_connections.dat").write_bytes(serialize([]))
        (self.base/"PBS/map_connections.txt").write_bytes(b"# Synthetic isolated baseline\n")
        (self.base/"PBS/map_metadata.txt").write_bytes(b"[002]\nName = Synthetic\n")
        maps=exp.visual.upgrade(self.ready,self.mapping,self.meta["tileset_ids"],self.events,self.start)
        maps,components,imported=pv.apply_maps(maps,mapping,source)
        self.assertEqual(len(imported),10)
        self.assertEqual(imported[pv.LAKEFRONT]["source_id"],195)
        self.assertEqual(len(components[pv.LAKEFRONT]),103)
        maps,events,start=exp.compile_events(maps,mapping,components,{**pv.ANCHORS,**pv.INTERIOR_ANCHORS})
        out,report=pv.bind_audio_and_connections(maps,mapping,components,source,self.base)
        self.assertEqual([p["reachable_seam_tiles"] for p in report["connections"]],[8,5,6,4,0,0])
        self.assertEqual(len(report["audio_files"]),7)
        out,story=pv.extend_lake_story(out,mapping,components)
        self.assertEqual(story["portal_pairs"],2)
        self.assertEqual(story["autoruns"],5)
        self.assertEqual(len(read_marshal(out["Data/map_connections.dat"],"LIVE_CONNECTIONS")),4)
        masks=pv.movement_masks(out,mapping)
        pv.verify_starter_corridor(masks,mapping)
        self.assertEqual(masks[mapping["SINNOH_LAKE_VERITY"]][42][44:46],"..")
        self.assertEqual(masks[mapping["SINNOH_LAKE_VERITY"]][44][44:46],"##")
        self.assertTrue(any("g" in row for row in masks[mapping["SINNOH_ROUTE_201"]]))
        print("SINNOH_REAL_GRASSLESS_STARTER_CORRIDOR_AND_4_NATIVE_SEAMS_OK",flush=True)
        infos=read_marshal(out["Data/MapInfos.rxdata"],"LIVE_INFOS")
        self.assertEqual(infos[451].attrs["@name"],b"Verity Lakefront")
        count=0;autoruns=[]
        for sym,mid in mapping.items():
            m=read_marshal(out["Data/Map%03d.rxdata"%mid],"LIVE_MAP")
            es=m.attrs["@events"];count+=len(es)
            for event in es.values():
                xy=(event.attrs["@x"],event.attrs["@y"])
                self.assertIn(xy,components[sym])
                pages=event.attrs["@pages"]
                if event.attrs["@name"]==b"SN_BEDROOM_TO_1F":
                    ops=pages[0].attrs["@list"]
                    self.assertEqual([c.attrs["@code"] for c in ops],[111,201,0,412,0])
                    self.assertIn(b"BlueSinnohPilot.setup_profile",ops[0].attrs["@parameters"][1])
                if pages[0].attrs["@trigger"]==3:
                    self.assertEqual(len(pages),2)
                    self.assertTrue(pages[1].attrs["@condition"].attrs["@self_switch_valid"])
                    autoruns.append(event.attrs["@name"])
                    if event.attrs["@name"]==b"SN_PROFILE_SETUP" and shutil.which("ruby"):
                        script=pages[0].attrs["@list"][0].attrs["@parameters"][0].decode("ascii")
                        run=subprocess.run([shutil.which("ruby"),"-c"],input=script,text=True,capture_output=True,timeout=15)
                        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            if sym==pv.LAKEFRONT:
                self.assertEqual({(e.attrs["@x"],e.attrs["@y"]) for e in es.values()},{(10,2),(11,2)})
                for e in es.values():
                    ops=e.attrs["@pages"][0].attrs["@list"]
                    self.assertEqual(ops[0].attrs["@code"],111)
                    self.assertEqual(ops[1].attrs["@parameters"][1],mapping["SINNOH_LAKE_VERITY"])
        self.assertEqual(count,32)
        self.assertEqual(len(autoruns),5)
        self.assertIn(b"SN_PROFILE_SETUP",autoruns)
        lake=read_marshal(out["Data/Map%03d.rxdata"%mapping["SINNOH_LAKE_VERITY"]],"LIVE_BALLS")
        balls=[e for e in lake.attrs["@events"].values() if e.attrs["@name"].startswith(b"SN_BALL_")]
        self.assertEqual(len(balls),3)
        for e in balls:
            pages=e.attrs["@pages"]
            self.assertEqual(len(pages),2)
            self.assertEqual(pages[1].attrs["@condition"].attrs["@self_switch_ch"],b"B")
            self.assertEqual(pages[1].attrs["@graphic"].attrs["@character_name"],b"")
            self.assertTrue(pages[1].attrs["@through"])
        lab=read_marshal(out["Data/Map%03d.rxdata"%mapping["SINNOH_PROFESSOR_ROWAN_LABORATORY"]],"LIVE_LAB")
        handlers=[c.attrs["@parameters"][0] for e in lab.attrs["@events"].values() for p in e.attrs["@pages"] for c in p.attrs["@list"] if c.attrs["@code"]==355]
        self.assertEqual(handlers.count(b"BlueSinnohPilot.lab_reward"),2)
        print("SINNOH_REAL_STARTER_PAGES_AND_LAB_HANDLERS_OK",flush=True)
        # Exercise the new coverage layer after preserving all old checks.
        (self.base/"PBS/encounters.txt").write_bytes(b"[002]\nLand,21\n    100,PIDGEY,5\n")
        roster={m for methods in pv.LAND_ROSTER.values() for rows in methods.values() for _,m,_,_ in rows}
        roster.update(m for rows in pv.WATER_ROSTER.values() for _,m,_,_ in rows)
        roster.update(t[3] for t in pv.ROUTE202_TRAINERS)
        with patch("pbs.catalogue",side_effect=lambda base,kind: roster if kind=="pokemon" else {"YOUNGSTER","LASS"}):
            pbs,coverage=pv.coverage_encounters(self.base,mapping,masks)
            trainers=pv.route202_trainer_pbs(self.base)
        self.assertEqual(len(coverage),10)
        self.assertTrue(pbs.startswith(b"[002]\n"))
        self.assertEqual({sym for sym,v in coverage.items() if "Land" in v["methods"]},set(pv.LAND_ROSTER))
        self.assertTrue(all(v["grass_cells"]==0 or "Land" in v["methods"] for v in coverage.values()))
        self.assertIn(b"[YOUNGSTER,Tristan,202]",trainers)
        self.assertIn(b"[LASS,Natalie,202]",trainers)
        self.assertIn(b"[YOUNGSTER,Logan,202]",trainers)
        self.assertIn(b"Pokemon = BURMY,5",trainers)
        expanded,positions=pv.route202_trainer_events(out,mapping,components)
        self.assertEqual(len(positions),3)
        self.assertEqual(len({tuple(t["position"]) for t in positions}),3)
        route=read_marshal(expanded["Data/Map%03d.rxdata"%mapping["SINNOH_ROUTE_202"]],"LIVE_TRAINERS")
        self.assertEqual(len(route.attrs["@events"]),4)
        for t in positions:
            self.assertIn(tuple(t["position"]),components["SINNOH_ROUTE_202"])
            page=route.attrs["@events"][t["event_id"]].attrs["@pages"][0].attrs
            self.assertEqual(page["@trigger"],2)
            self.assertIn(t["key"].encode(),page["@list"][0].attrs["@parameters"][0])
        self.assertEqual(sum(len(read_marshal(expanded["Data/Map%03d.rxdata"%mid],"COVERAGE_MAP").attrs["@events"]) for mid in mapping.values()),35)
        print("SINNOH_REAL_10_MAP_COVERAGE_3_TRAINERS_35_EVENTS_OK",flush=True)
        entries=exp.qa_teleport.build(expanded,mapping,components)
        self.assertEqual(sum(row[3] is not None for row in entries),10)
        self.assertEqual(sum(row[2]=="Rotas" for row in entries),30)
        self.assertEqual(sum(row[2]=="Cidades e vilarejos" for row in entries),14)
        for sym,label,category,dest in entries:
            if dest is None:
                self.assertNotIn(sym,mapping)
                continue
            mid,x,y=dest
            self.assertEqual(mid,mapping[sym])
            self.assertIn((x,y),components[sym])
            world=read_marshal(expanded["Data/Map%03d.rxdata"%mid],"TELEPORT_MAP")
            self.assertFalse(any((x,y)==(e.attrs["@x"],e.attrs["@y"]) for e in world.attrs["@events"].values()))
        if shutil.which("ruby"):
            proc=subprocess.run([shutil.which("ruby"),"-c"],input=exp.qa_teleport.plugin(entries),capture_output=True,timeout=30)
            self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
        print("SINNOH_REAL_10_SAFE_QA_TELEPORT_DESTINATIONS_OK",flush=True)
        before=dict(expanded)
        tex,code,forest=exp.forest_edge.build(expanded,mapping)
        self.assertEqual(before,expanded)
        self.assertEqual(forest["map_ids"],sorted(mapping[sym] for sym in pv.donor_maps(mapping)))
        self.assertEqual(len(forest["map_ids"]),6)
        self.assertFalse(forest["geometry_changed"])
        self.assertEqual(exp.qa_teleport.build(expanded,mapping,components),entries)
        self.assertEqual(pv.movement_masks(expanded,mapping),masks)
        width,height,rgba=exp.forest_edge.atlas_pixels(
            pv.png(256,64,b"\xff"*(256*64*4)))
        self.assertEqual((width,height),(256,64))
        self.assertEqual(pv.dims(tex),(64,64))
        self.assertIn(forest["art"],("local_repeated_green_blocked_donor_patch","original_tree_fallback"))
        # Validate the generated texture is opaque, and syntax of runtime hook.
        import zlib,struct
        pos=8;parts=[]
        while pos+12<=len(tex):
            n=struct.unpack_from(">I",tex,pos)[0]
            if tex[pos+4:pos+8]==b"IDAT":parts.append(tex[pos+8:pos+8+n])
            pos+=n+12
        scan=zlib.decompress(b"".join(parts))
        self.assertEqual(len(scan),64*(64*4+1))
        self.assertTrue(all(scan[y*257+4+x*4]==255 for y in range(64) for x in range(64)))
        if shutil.which("ruby"):
            result=subprocess.run([shutil.which("ruby"),"-c"],input=code,capture_output=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        print("SINNOH_REAL_6_FOREST_EDGES_10_MAPS_35_EVENTS_UNCHANGED_OK",flush=True)
        print("SINNOH_F02_TEXTURE_SOURCE "+forest["art"],flush=True)
        # F04 is append-only: compare all ten original maps, their tile
        # tables, movement masks, connections, and 22 safe destinations.
        city=exp.city_expansion
        all_maps,all_ids,all_components,city_report=city.append(expanded,mapping,components,source,{2})
        self.assertEqual(len(all_ids),22)
        self.assertEqual(len(city_report),12)
        self.assertTrue(all(all_ids[k]==v for k,v in mapping.items()))
        for mid in mapping.values():
            rel="Data/Map%03d.rxdata"%mid
            self.assertEqual(all_maps[rel],expanded[rel])
        self.assertEqual(all_maps["Data/map_connections.dat"],expanded["Data/map_connections.dat"])
        old_tiles=read_marshal(expanded["Data/Tilesets.rxdata"],"OLD_TILES")
        new_tiles=read_marshal(all_maps["Data/Tilesets.rxdata"],"NEW_TILES")
        self.assertEqual(serialize(new_tiles[:len(old_tiles)]),serialize(old_tiles))
        self.assertEqual(len(new_tiles)-len(old_tiles),12)
        all_entries=exp.qa_teleport.build(all_maps,all_ids,all_components)
        self.assertEqual(sum(r[3] is not None for r in all_entries),22)
        self.assertEqual(sum(r[3] is not None and r[2]=="Cidades e vilarejos" for r in all_entries),14)
        previous={r[0]:r[3] for r in entries if r[3] is not None}
        self.assertEqual({r[0]:r[3] for r in all_entries if r[0] in previous},previous)
        self.assertEqual(sum(len(read_marshal(all_maps["Data/Map%03d.rxdata"%mid],"F04_MAP").attrs["@events"]) for mid in all_ids.values()),35)
        all_masks=pv.movement_masks(all_maps,all_ids,extra_symbols=city.CITIES)
        self.assertEqual({mid:all_masks[mid] for mid in masks},masks)
        self.assertEqual(len(all_masks),18)
        for row in all_entries:
            if row[0] in city.CITIES:
                mid,x,y=row[3]
                self.assertEqual(all_masks[mid][y][x],".")
                self.assertEqual(row[3],city_report[row[0]]["safe_spawn"])
        _,all_forest,all_forest_report=exp.forest_edge.build(all_maps,all_ids,extra_symbols=city.CITIES)
        self.assertEqual(len(all_forest_report["map_ids"]),18)
        if shutil.which("ruby"):
            for script in (all_forest,exp.qa_teleport.plugin(all_entries),pv.movement_plugin(all_masks,all_ids["SINNOH_ROUTE_202"])):
                run=subprocess.run([shutil.which("ruby"),"-c"],input=script,capture_output=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        print("SINNOH_REAL_F04_14_CITIES_22_TELEPORTS_35_EVENTS_18_EXTERIORS_OK",flush=True)
        routes=exp.route_expansion
        full_maps,full_ids,full_components,route_report=routes.append(all_maps,all_ids,all_components,source,{2})
        self.assertEqual(len(full_ids),56)
        self.assertEqual(len(route_report),34)
        self.assertEqual({k:full_ids[k] for k in all_ids},all_ids)
        for mid in all_ids.values():
            rel="Data/Map%03d.rxdata"%mid
            self.assertEqual(full_maps[rel],all_maps[rel])
        self.assertEqual(full_maps["Data/map_connections.dat"],all_maps["Data/map_connections.dat"])
        self.assertEqual(full_maps["PBS/map_connections.txt"],all_maps["PBS/map_connections.txt"])
        full_tiles=read_marshal(full_maps["Data/Tilesets.rxdata"],"F05_TILES")
        self.assertEqual(serialize(full_tiles[:len(new_tiles)]),serialize(new_tiles))
        self.assertEqual(len(full_tiles)-len(new_tiles),34)
        full_entries=exp.qa_teleport.build(full_maps,full_ids,full_components)
        self.assertEqual(len(full_entries),139)
        self.assertEqual(sum(r[3] is not None for r in full_entries),56)
        self.assertEqual(sum(r[3] is not None and r[2]=="Rotas" for r in full_entries),36)
        previous={r[0]:r[3] for r in all_entries if r[3] is not None}
        self.assertEqual({r[0]:r[3] for r in full_entries if r[0] in previous},previous)
        self.assertEqual(sum(len(read_marshal(full_maps["Data/Map%03d.rxdata"%mid],"F05_MAP").attrs["@events"]) for mid in full_ids.values()),35)
        full_masks=pv.movement_masks(full_maps,full_ids,extra_symbols=city.CITIES|routes.ROUTES)
        self.assertEqual({mid:full_masks[mid] for mid in all_masks},all_masks)
        self.assertEqual(len(full_masks),52)
        for row in full_entries:
            if row[0] in routes.ROUTES:
                mid,x,y=row[3]
                self.assertEqual(full_masks[mid][y][x],".")
                self.assertEqual(row[3],route_report[row[0]]["safe_spawn"])
        _,full_forest,full_forest_report=exp.forest_edge.build(full_maps,full_ids,extra_symbols=city.CITIES|routes.ROUTES)
        self.assertEqual(len(full_forest_report["map_ids"]),52)
        if shutil.which("ruby"):
            for script in (full_forest,exp.qa_teleport.plugin(full_entries),pv.movement_plugin(full_masks,full_ids["SINNOH_ROUTE_202"])):
                run=subprocess.run([shutil.which("ruby"),"-c"],input=script,capture_output=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        print("SINNOH_REAL_F05_30_ROUTES_56_TELEPORTS_35_EVENTS_52_EXTERIORS_OK",flush=True)





        print("SINNOH_REAL_10_MAPS_4_WALK_SEAMS_2_VISUAL_2_PORTALS_32_EVENTS_OK",flush=True)

    @unittest.skipUnless(shutil.which("ruby"),"Requires Ruby runtime")
    def test_new_profile_dialogue_selects_both_characters_and_names_once(self):
        script=r'''
load ARGV[0]
require "tmpdir"
module BlueSinnohExperimental; TOKEN = "012345abcdef"; end
module GameData
  module PlayerMetadata
    def self.try_get(id); [9,10].include?(id) ? Object.new : nil; end
  end
end
Player = Struct.new(:character_ID,:name)
Global = Struct.new(:blue_regions)
class GamePlayer
  attr_accessor :transparent
  def refresh_charset; @refreshed = true; end
  def refreshed?; @refreshed; end
end
def _INTL(text,*args); text; end
def pbMessage(text,*args)
  return nil if args.empty?
  raise "wrong selection options" unless args[0] == ["Lucas","Dawn"]
  $asked += 1
  $choice
end
def pbChangePlayer(id); $player.character_ID = id; end
module Settings; MAX_PLAYER_NAME_SIZE=12; end
def pbEnterPlayerName(prompt,min,max)
  raise "wrong name limits" unless min==1 && max==12
  $name_failure ? (raise "native name entry failed") : ($cancel_name ? "" : "Teste Sinnoh")
end
def pbTrainerName(name); $named += 1; $player.name = name; end
[0,1].each do |choice|
  $choice=choice; $asked=0; $named=0
  $PokemonGlobal=Global.new({"version"=>1,"initial"=>"SINNOH","current"=>"SINNOH"})
  $player=Player.new(1,"Red"); $game_player=GamePlayer.new
  raise "failed profile" unless BlueSinnohPilot.setup_profile
  raise "wrong character" unless $player.character_ID==9+choice
  raise "wrong name" unless $player.name=="Teste Sinnoh"
  raise "missing refresh" unless $game_player.refreshed? && $game_player.transparent==false
  raise "profile repeated" unless BlueSinnohPilot.setup_profile && $asked==1 && $named==1
  raise "gate missing" if BlueSinnohPilot.lake_entry_allowed?
  BlueSinnohPilot.mother
  raise "gate bypass" if BlueSinnohPilot.lake_entry_allowed?
  BlueSinnohPilot.barry_intro
  raise "gate did not open" unless BlueSinnohPilot.lake_entry_allowed?
end

$choice=0; $asked=0; $named=0
$PokemonGlobal=Global.new({"version"=>1,"initial"=>"SINNOH","current"=>"SINNOH"})
$player=Player.new(1,"Red"); $game_player=GamePlayer.new
$name_failure=true
Dir.mktmpdir do |tmp|
  qa=File.join(tmp,"game-sinnoh-experimental-012345abcdef")
  Dir.mkdir(qa)
  Dir.chdir(qa) do
    File.write("sinnoh-experimental-qa.json","{}")
    raise "exception escaped" if BlueSinnohPilot.setup_profile
    raise "failure marked complete" if $PokemonGlobal.blue_regions["sinnoh_profile_complete"]
    log=File.read("sinnoh-profile-error.txt")
    raise "missing real error context" unless log.include?("SINNOH_PROFILE_STAGE=name_entry") &&
      log.include?("native name entry failed")
  end
end
$name_failure=false; $cancel_name=true
raise "cancel advanced" if BlueSinnohPilot.setup_profile
raise "cancel marked complete" if $PokemonGlobal.blue_regions["sinnoh_profile_complete"]
$cancel_name=false
raise "retry failed" unless BlueSinnohPilot.setup_profile
raise "retry name missing" unless $player.name=="Teste Sinnoh" && $named==1
$PokemonGlobal=Global.new({"version"=>1,"initial"=>"KANTO","current"=>"KANTO"})
raise "foreign save accepted" if BlueSinnohPilot.setup_profile
raise "foreign save changed" if $PokemonGlobal.blue_regions.key?("sinnoh_profile_complete")
puts "SINNOH_PROFILE_2_CHOICES_NAME_AND_GATE_OK"
puts "SINNOH_PROFILE_NATIVE_FAILURE_CANCEL_RETRY_OK"
'''
        proc=subprocess.run([shutil.which("ruby"),"-e",script,str(ROOT/"scripts/regions/SinnohPilot.rb")],
                            text=True,capture_output=True,timeout=30)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
        self.assertIn("SINNOH_PROFILE_2_CHOICES_NAME_AND_GATE_OK",proc.stdout)
        self.assertIn("SINNOH_PROFILE_NATIVE_FAILURE_CANCEL_RETRY_OK",proc.stdout)

    @unittest.skipUnless(shutil.which("ruby"),"Requires Ruby runtime")
    def test_private_new_game_bootstrap_initializes_without_legacy_region_hook(self):
        generated=exp.experiment_plugin([442,10,8],"abc123abc123",True,True,story_profile=True)
        self.assertIn(b"install_fresh_hooks!",generated)
        script=r'''
require "tmpdir"
load ARGV[0]
load ARGV[1]
module BlueKantoTitle
  def self.sinnoh_experimental_maps_ready?; true; end
end
module Settings; MAX_PLAYER_NAME_SIZE=12; end
Player = Struct.new(:character_ID,:name)
class GamePlayer
  attr_accessor :transparent
  def refresh_charset; end
end
def _INTL(text,*args); text; end
def pbMessage(text,*args); args.empty? ? nil : 1; end
def pbChangePlayer(id); $player.character_ID=id; end
def pbEnterPlayerName(*args); "Sinnoh"; end
def pbTrainerName(name); $player.name=name; end
class Meta
  attr_accessor :blue_regions
end
class OldMeta; end
SystemData = Struct.new(:start_map_id,:start_x,:start_y)
$data_system=SystemData.new(1,0,0)
module SaveData
  def self.load_new_game_values
    $PokemonGlobal = $use_old ? OldMeta.new : Meta.new
    $PokemonGlobal.blue_regions = BlueSinnohExperimental.state_template("DECADES") if $default
    :values
  end
end
module Game
  def self.start_new
    SaveData.load_new_game_values
    raise "map factory before regional initialization" unless $PokemonGlobal.blue_regions["current"]=="SINNOH"
    raise "wrong start" unless $data_system.start_map_id==442
    :native_new_game
  end
  def self.load
    $PokemonGlobal = Meta.new
    $PokemonGlobal.blue_regions = {"version"=>1,"current"=>"KANTO"}
  end
end
Dir.mktmpdir do |tmp|
  qa=File.join(tmp,"game-sinnoh-experimental-abc123abc123")
  Dir.mkdir(qa)
  Dir.chdir(qa) do
    File.write("sinnoh-experimental-qa.json","{}")
    BlueSinnohExperimental.install_fresh_hooks!
    BlueSinnohExperimental.install_fresh_hooks!
    $PokemonGlobal=Meta.new
    old=$PokemonGlobal
    old.blue_regions={"version"=>1,"current"=>"KANTO"}
    $use_old=true
    raise "native result lost" unless Game.start_new==:native_new_game
    raise "old save changed" unless old.blue_regions["current"]=="KANTO"
    raise "missing Sinnoh state" unless $PokemonGlobal.blue_regions["initial"]=="SINNOH"
    raise "fresh scope leaked" if BlueSinnohExperimental.fresh?
    $player=Player.new(1,"Red"); $game_player=GamePlayer.new
    raise "bedroom profile failed after old-base initialization" unless BlueSinnohPilot.setup_profile
    raise "wrong profile" unless $player.character_ID==10 && $player.name=="Sinnoh"
    $use_old=false; $default=true
    raise "default initial state not replaced" unless Game.start_new==:native_new_game
    raise "default replacement wrong" unless $PokemonGlobal.blue_regions["current"]=="SINNOH"
    Game.load
    raise "load mutated" unless $PokemonGlobal.blue_regions["current"]=="KANTO"
    raise "load activated fresh" if BlueSinnohExperimental.fresh?
    SaveData.load_new_game_values
    raise "out of scope changed" unless $PokemonGlobal.blue_regions["current"]=="DECADES"
  end
end
puts "SINNOH_NATIVE_FRESH_STATE_WITHOUT_LEGACY_HOOK_OK"
'''
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"generated.rb";path.write_bytes(generated)
            proc=subprocess.run([shutil.which("ruby"),"-e",script,str(path),str(ROOT/"scripts/regions/SinnohPilot.rb")],text=True,capture_output=True,timeout=30)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
        self.assertIn("SINNOH_NATIVE_FRESH_STATE_WITHOUT_LEGACY_HOOK_OK",proc.stdout)

    def test_late_fresh_hook_only_in_private_story_bootstrap(self):
        main_source=b"def boot\n    PluginManager.runPlugins\n    Compiler.main\nend\n"
        raw=b"\x04\x08"+exp.dump([[1,exp.RubyString(b"Main"),exp.RubyString(zlib.compress(main_source))]])
        rows=exp.Marshal(exp.patch_bootstrap(raw,"abc123abc123",self.ids,story_profile=True)).read()
        main=zlib.decompress(next(row[2] for row in rows if row[1]==b"Main")).decode()
        self.assertIn("BlueSinnohExperimental.install_fresh_hooks!",main)
        self.assertLess(main.index("PluginManager.runPlugins"),main.index("BlueSinnohExperimental.install_fresh_hooks!"))
        self.assertLess(main.index("BlueSinnohExperimental.install_fresh_hooks!"),main.index("Compiler.main"))

    @unittest.skipUnless(shutil.which("ruby"),"Requires Ruby runtime")
    def test_private_movement_blocks_forest_and_grass_before_starter(self):
        generated=exp.private_visual.movement_plugin({442:[".g#","..."],443:[".."]})
        script=r'''
module BlueSinnohExperimental
  def self.private_copy?; $private; end
end
Map=Struct.new(:map_id)
Player=Struct.new(:party)
Monster=Struct.new(:egg?)
class Factory
  def getFacingTile(dir,event); $facing; end
end
class Game_Player
  attr_reader :moves
  def initialize; @moves=[]; end
  def move_generic(dir,*args); @moves << dir; end
end
def _INTL(text); text; end
def pbMessage(text); $warnings+=1; end
$private=true;$warnings=0
$game_map=Map.new(442);$map_factory=Factory.new
$player=Player.new([])
load ARGV[0]
BlueSinnohSafeMovement.install!
p=Game_Player.new
$facing=[442,1,0];2.times { p.move_generic(6) }
raise "grass allowed or repeated message" unless p.moves.empty? && $warnings==1
$facing=[442,2,0];p.move_generic(6)
raise "forest allowed" unless p.moves.empty?
$facing=[442,0,1];p.move_generic(2)
raise "safe path blocked" unless p.moves==[2]
$facing=[443,0,0];p.move_generic(4)
raise "valid connected map blocked" unless p.moves==[2,4]
$facing=[442,1,0];$player.party=[Monster.new(true)];p.move_generic(6)
raise "egg allowed" unless p.moves==[2,4]
$player.party=[Monster.new(false)];p.move_generic(6)
raise "grass remained blocked after starter" unless p.moves==[2,4,6]
$facing=[442,99,99];p.move_generic(6)
$facing=nil;p.move_generic(6)
$facing=[900,1,1];p.move_generic(6)
raise "invalid seam allowed" unless p.moves==[2,4,6]
$game_map=Map.new(2);p.move_generic(6)
raise "other region changed" unless p.moves==[2,4,6,6]
$game_map=Map.new(442);$private=false;p.move_generic(6)
raise "non-QA changed" unless p.moves==[2,4,6,6,6]
puts "SINNOH_GRASS_AND_FOREST_MOVEMENT_OK"
'''
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"guard.rb";path.write_bytes(generated)
            proc=subprocess.run([shutil.which("ruby"),"-e",script,str(path)],text=True,capture_output=True,timeout=30)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
        self.assertIn("SINNOH_GRASS_AND_FOREST_MOVEMENT_OK",proc.stdout)

    @unittest.skipUnless(shutil.which("ruby"),"Requires Ruby runtime")
    def test_route202_seam_requires_lab_reward(self):
        code=exp.private_visual.movement_plugin({442:[".."],443:[".."]},443)
        script=r'''
module BlueSinnohExperimental
  def self.private_copy?; true; end
end
module BlueSinnohPilot
  def self.route202_allowed?; $reward; end
end
Map=Struct.new(:map_id)
Player=Struct.new(:party)
class Factory
  def getFacingTile(*args); $facing; end
end
class Game_Player
  attr_reader :moves
  def initialize; @moves=[]; end
  def move_generic(dir,*args); @moves << dir; end
end
def _INTL(text); text; end
def pbMessage(text); $warnings+=1; end
$game_map=Map.new(442);$map_factory=Factory.new;$player=Player.new([Object.new])
$reward=false;$warnings=0;$facing=[443,0,0]
load ARGV[0]
BlueSinnohSafeMovement.install!
p=Game_Player.new
2.times { p.move_generic(8) }
raise "gate bypassed" unless p.moves.empty? && $warnings==1
$reward=true;p.move_generic(8)
raise "gate not released" unless p.moves==[8]
$reward=false;$game_map.map_id=443;$facing=[442,0,0];p.move_generic(2)
raise "return blocked" unless p.moves==[8,2]
'''
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"guard.rb";path.write_bytes(code)
            proc=subprocess.run([shutil.which("ruby"),"-e",script,str(path)],capture_output=True,text=True,timeout=30)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)

    @unittest.skipUnless(shutil.which("ruby"),"Requires Ruby runtime")
    def test_route_trainers_require_lab_and_record_only_wins(self):
        script=r'''
load ARGV[0]
def _INTL(s,*args); s; end
def pbMessage(*args); end
module BlueSinnohExperimental
  def self.private_copy?; $private; end
end
module BlueKantoTitle
  def self.sinnoh_experimental_barry_compiled?; $compiled; end
end
module GameData
  class Trainer
    def self.get(type,name,version)
      raise "wrong version" unless version==202
      mon={"Tristan"=>:STARLY,"Natalie"=>:BIDOOF,"Logan"=>:BURMY}.fetch(name)
      Struct.new(:pokemon).new([{species:mon}])
    end
  end
end
module TrainerBattle
  def self.start(*args); $calls+=1; $result; end
end
Global=Struct.new(:blue_regions)
Player=Struct.new(:has_pokedex)
flags={"mother_intro"=>true,"barry_intro"=>true,"rowan_briefcase_seen"=>true,"starter_received"=>true,
"starter"=>"TURTWIG","rival_fought"=>true,"pokedex_received"=>true}
state={"version"=>1,"initial"=>"SINNOH","current"=>"SINNOH","sinnoh_pilot"=>flags}
$PokemonGlobal=Global.new(state);$player=Player.new(true)
$private=true;$compiled=true;$calls=0;$result=true
raise "gate bypassed" if BlueSinnohPilot.route_trainer("TRISTAN")
state["sinnoh_lab_supplies"]=true
$compiled=false
raise "uncompiled battle" if BlueSinnohPilot.route_trainer("TRISTAN")
$compiled=true;$result=false
raise "loss counted" if BlueSinnohPilot.route_trainer("TRISTAN")
raise "loss persisted" if state["sinnoh_route202_victories"]
$result=true
%w[TRISTAN NATALIE LOGAN].each { |key| raise "battle failed" unless BlueSinnohPilot.route_trainer(key) }
raise "wrong victories" unless state["sinnoh_route202_victories"]==%w[TRISTAN NATALIE LOGAN]
$PokemonGlobal=Marshal.load(Marshal.dump($PokemonGlobal))
raise "repeat dialog failed" unless BlueSinnohPilot.route_trainer("TRISTAN")
raise "duplicate battle" unless $calls==4
'''
        proc=subprocess.run([shutil.which("ruby"),"-e",script,str(ROOT/"scripts/regions/SinnohPilot.rb")],capture_output=True,text=True,timeout=30)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)

    def test_f04_component_prefers_safe_arrival_over_largest_grass_area(self):
        w,h=12,10
        cells=[0]*(w*h*3)
        for y in range(1,9):
            for x in range(1,6):
                cells[y*w+x]=2
        for y in range(2,7):
            for x in range(8,11):
                cells[y*w+x]=1
        self.assertEqual(len(exp.city_expansion.component(cells,w,h,[0,0,0],[0,0,2])),15)
        with self.assertRaisesRegex(ValueError,"NO_SAFE_WALKABLE_COMPONENT"):
            exp.city_expansion.component(cells,w,h,[0,0,0],[0,2,2])

    def test_f05_save_namespace_and_route_segments(self):
        city=exp.city_expansion
        route=exp.route_expansion
        old={k:442+i for i,k in enumerate(sorted(city.OLD))}
        prior=city.allocate(old,{2})
        full=route.allocate(prior,{2})
        self.assertEqual(len(full),56)
        self.assertEqual({k:full[k] for k in prior},prior)
        self.assertEqual(len(route.extra_destinations()),6)
        with self.assertRaises(ValueError):route.allocate(prior,set(range(464,518)))
        token="abc123abc123"
        folder=self.proj/exp.REPO_OUTPUT/(exp.QA_DIR+"-"+token)
        folder.mkdir(parents=True)
        profile=exp.namespace(token)
        files={"Data/Map%03d.rxdata"%mid:("map-%s"%mid).encode() for mid in prior.values()}
        data={"schema":1,"region":"SINNOH","mode":exp.MODE,"profile_token":token,
              "main_game_modified":False,"personal_saves_copied":False,
              "mapids":prior,"base_mapinfos_sha256":"a"*64,"save_profile":profile,
              "file_sha256":{k:exp.sha(v) for k,v in files.items()}}
        (folder/"sinnoh-experimental-qa.json").write_text(json.dumps(data))
        (folder/"mkxp.json").write_text(json.dumps(profile))
        self.assertEqual(exp.compatible_save_token(self.proj,full,"a"*64,files),token)
        self.assertIsNone(exp.compatible_save_token(self.proj,full,"b"*64,files))
        key=next(iter(files))
        self.assertIsNone(exp.compatible_save_token(self.proj,full,"a"*64,{**files,key:b"changed"}))
        bad=dict(full);a,b=list(prior)[:2];bad[a],bad[b]=bad[b],bad[a]
        self.assertIsNone(exp.compatible_save_token(self.proj,bad,"a"*64,files))

    def test_f04_save_namespace_append_only(self):
        city=exp.city_expansion
        old={k:442+i for i,k in enumerate(sorted(city.OLD))}
        new=city.allocate(old,{2})
        self.assertEqual(len(new),22)
        self.assertEqual({k:new[k] for k in old},old)
        with self.assertRaises(ValueError):city.allocate(old,set(range(452,518)))
        with self.assertRaises(ValueError):city.allocate(old,{442})
        token="abc123abc123"
        folder=self.proj/exp.REPO_OUTPUT/(exp.QA_DIR+"-"+token)
        folder.mkdir(parents=True)
        profile=exp.namespace(token)
        files={"Data/Map%03d.rxdata"%mid:("map-%s"%mid).encode() for mid in old.values()}
        data={"schema":1,"region":"SINNOH","mode":exp.MODE,"profile_token":token,
              "main_game_modified":False,"personal_saves_copied":False,
              "mapids":old,"base_mapinfos_sha256":"a"*64,"save_profile":profile,
              "file_sha256":{k:exp.sha(v) for k,v in files.items()}}
        (folder/"sinnoh-experimental-qa.json").write_text(json.dumps(data))
        (folder/"mkxp.json").write_text(json.dumps(profile))
        self.assertEqual(exp.compatible_save_token(self.proj,new,"a"*64,files),token)
        self.assertIsNone(exp.compatible_save_token(self.proj,new,"b"*64,files))
        self.assertIsNone(exp.compatible_save_token(self.proj,new,"a"*64,{}))
        key=next(iter(files))
        self.assertIsNone(exp.compatible_save_token(self.proj,new,"a"*64,{**files,key:b"changed"}))
        bad=dict(new);a,b=list(old)[:2];bad[a],bad[b]=bad[b],bad[a]
        self.assertIsNone(exp.compatible_save_token(self.proj,bad,"a"*64,files))

    def test_save_namespace_reused_only_for_compatible_private_manifest(self):
        token="abc123abc123"
        work=self.proj/exp.REPO_OUTPUT
        folder=work/(exp.QA_DIR+"-"+token)
        folder.mkdir(parents=True)
        profile=exp.namespace(token)
        data={"schema":1,"region":"SINNOH","mode":exp.MODE,"profile_token":token,
              "main_game_modified":False,"personal_saves_copied":False,
              "mapids":self.mapping,"base_mapinfos_sha256":"a"*64,"save_profile":profile}
        (folder/"sinnoh-experimental-qa.json").write_text(json.dumps(data))
        (folder/"mkxp.json").write_text(json.dumps(profile))
        self.assertEqual(exp.compatible_save_token(self.proj,self.mapping,"a"*64),token)
        self.assertIsNone(exp.compatible_save_token(self.proj,self.mapping,"b"*64))
        self.assertIsNone(exp.compatible_save_token(self.proj,{"OTHER":442},"a"*64))
        (folder/"mkxp.json").write_text(json.dumps({"dataPathApp":"MAIN"}))
        self.assertIsNone(exp.compatible_save_token(self.proj,self.mapping,"a"*64))

    def test_route201_pbs_uses_allocated_ids_and_preserves_base(self):
        path=self.base/"PBS/encounters.txt"
        original=b"[002]\nLand,21\n    100,PIDGEY,5\n"
        path.write_bytes(original)
        actual=exp.private_visual.route201_encounters(self.base,self.mapping)
        self.assertTrue(actual.startswith(original))
        self.assertIn(("[%03d] # Route 201"%self.mapping["SINNOH_ROUTE_201"]).encode(),actual)
        self.assertIn(b"50,STARLY,2,3",actual)
        self.assertIn(b"50,BIDOOF,2,3",actual)
        self.assertEqual(path.read_bytes(),original)
        path.write_bytes(("[%03d,1]\n"%self.mapping["SINNOH_ROUTE_201"]).encode())
        with self.assertRaisesRegex(ValueError,"BASE_ENCOUNTER_ID_COLLISION"):
            exp.private_visual.route201_encounters(self.base,self.mapping)

    @unittest.skipUnless(shutil.which("ruby"),"Requires Ruby runtime")
    def test_lab_reward_once_and_starter_visibility_persist(self):
        script=r'''
load ARGV[0]
def _INTL(s,*args); s; end
def pbMessage(*args); end
Global=Struct.new(:blue_regions)
Player=Struct.new(:has_pokedex)
Map=Struct.new(:map_id,:events)
Event=Struct.new(:name,:hidden) do
  def refresh; self.hidden=true; end
  def erase; self.hidden=true; end
end
class Bag
  attr_accessor :capacity,:count
  def initialize; @capacity=true; @count=2; end
  def quantity(item); @count; end
  def can_add?(item,n); @capacity; end
  def add(item,n); @count+=n; true; end
  def remove(item,n); @count-=n; true; end
end
flags={"mother_intro"=>true,"barry_intro"=>true,"rowan_briefcase_seen"=>true,
       "starter_received"=>true,"starter"=>"TURTWIG","rival_fought"=>true}
state={"version"=>1,"initial"=>"SINNOH","current"=>"SINNOH","sinnoh_pilot"=>flags}
$PokemonGlobal=Global.new(state);$player=Player.new(false);$bag=Bag.new
$game_map=Map.new(442,{1=>Event.new("SN_BALL_TURTWIG",false),
  2=>Event.new("SN_BALL_CHIMCHAR",false),3=>Event.new("SN_BALL_PIPLUP",false),
  4=>Event.new("SN_NPC_ROWAN_BRIEFCASE",false)})
$game_self_switches={}
raise "gate open too soon" if BlueSinnohPilot.route202_allowed?
raise "hide failed" unless BlueSinnohPilot.hide_starter_balls
raise "wrong events hidden" unless $game_self_switches.keys.sort==[[442,1,"B"],[442,2,"B"],[442,3,"B"]] && !$game_map.events[4].hidden
$bag.capacity=false
raise "reward granted with full bag" if BlueSinnohPilot.lab_reward
raise "failed grant advanced story" if $player.has_pokedex || BlueSinnohPilot.route202_allowed? || $bag.count!=2
$bag.capacity=true
raise "reward failed" unless BlueSinnohPilot.lab_reward && $bag.count==7 && $player.has_pokedex
raise "gate remains locked" unless BlueSinnohPilot.route202_allowed?
BlueSinnohPilot.lab_reward
raise "duplicate reward" unless $bag.count==7
# Serialized regional flags retain entitlement even after spending the balls.
$PokemonGlobal=Marshal.load(Marshal.dump($PokemonGlobal))
$bag.count=0
raise "gate relocked after spending items" unless BlueSinnohPilot.route202_allowed?
BlueSinnohPilot.lab_reward
raise "duplicate after reload" unless $bag.count==0
puts "SINNOH_LAB_REWARD_AND_STARTER_HIDE_OK"
'''
        proc=subprocess.run([shutil.which("ruby"),"-e",script,str(ROOT/"scripts/regions/SinnohPilot.rb")],
                            text=True,capture_output=True,timeout=30)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
        self.assertIn("SINNOH_LAB_REWARD_AND_STARTER_HIDE_OK",proc.stdout)

    def test_expanded_profile_only_runs_after_map_initialization(self):
        code=exp.experiment_plugin([442,10,8],"abc123abc123",True,True,story_profile=True).decode()
        self.assertNotIn("pbChangePlayer(",code)
        self.assertIn("bedroom autorun",code)
        source=(ROOT/"scripts/regions/SinnohPilot.rb").read_text("utf-8")
        self.assertIn("pbTrainerName",source)
        self.assertIn('state["sinnoh_profile_complete"] = true',source)
        self.assertIn('["Lucas", "Dawn"]',source)

    def test_private_connection_plan_rejects_missing_duplicate_and_blocked_edges(self):
        pv=exp.private_visual
        raw=b"194,N,2,193,S,0\n193,E,0,192,W,4\n192,N,0,191,S,6\n"
        rows=pv.parse_connections(raw)
        components={s:{(x,y) for x in range(w) for y in range(h)}
                    for s,(_,_,(w,h)) in pv.DONOR.items()}
        self.assertEqual(len(pv.connection_plan(self.mapping,components,rows)),3)
        for bad in (rows[:-1],rows+[rows[0]]):
            with self.assertRaisesRegex(ValueError,"SOURCE_CONNECTION_MISSING_OR_DUPLICATE"):
                pv.connection_plan(self.mapping,components,bad)
        components["SINNOH_TWINLEAF_TOWN"]={(18,1)}
        with self.assertRaisesRegex(ValueError,"SOURCE_CONNECTION_NO_REACHABLE_SEAM"):
            pv.connection_plan(self.mapping,components,rows)

    def test_private_connection_merge_rejects_collision_with_existing_map_ids(self):
        pv=exp.private_visual
        (self.base/"Data/map_connections.dat").write_bytes(serialize([[self.ids[0],b"N",0,2,b"S",0]]))
        (self.base/"PBS/map_connections.txt").write_bytes(b"")
        with self.assertRaisesRegex(ValueError,"BASE_CONNECTION_ID_COLLISION"):
            pv.merge_connections(self.base,[],self.mapping)

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
