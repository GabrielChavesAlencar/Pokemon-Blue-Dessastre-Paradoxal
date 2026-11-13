"""Synthetic RMXP tests for New Bark stage08; no Game.exe or foreign data."""
from __future__ import annotations
import copy
import hashlib
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from build_johto_story_v1 import (validate_spec,compile_story,build,WARP_KEYS,
                                   REQUIRED_BALLS,LAB,walkable)
from build_johto_events import EVENT_CLASSES,event_page,ruby
from stage import serialize
from audit_johto import checksum,read_map_data
from server.ruby_marshal import RubyData,RubyObject,loads

WARP_SPEC=json.loads((ROOT/"data/regions/johto-stage07-warps.json").read_text("utf-8"))
STORY_SPEC=json.loads((ROOT/"data/regions/johto-stage08-story.json").read_text("utf-8"))
IDS={"JOHTO_NEW_BARK_TOWN":600,"JOHTO_ROUTE_29":625,
     "JOHTO_NEW_BARK_PLAYER_HOME_2F":674,
     "JOHTO_NEW_BARK_PLAYER_HOME_1F":675,LAB:676}
W,H=84,38


def tab(d,w,h,z,cells):
    return RubyData("Table",struct.pack("<5I",d,w,h,z,len(cells))+
                    struct.pack(f"<{len(cells)}H",*cells))


def make_fixture(root:Path):
    preview=root/".blue-work/johto-staging-warps-v1"
    (preview/"Data").mkdir(parents=True)
    (root/"game/Graphics/Characters").mkdir(parents=True)
    for name in ("NPC_GSC_Mom","NPC_HGSS_Professor_Elm",
                 "NPC_HGSS_Silver","Object_Ball"):
        (root/"game/Graphics/Characters"/f"{name}.png").write_bytes(b"\x89PNG\r\n\x1a\n"+"x".encode())
    tiles=[None,RubyObject("RPG::Tileset",{"@passages":tab(1,5336,1,1,[0]*5336)})]
    (preview/"Data/Tilesets.rxdata").write_bytes(serialize(tiles))
    (preview/"Data/MapInfos.rxdata").write_bytes(serialize({}))
    warps_by_src={sym:[] for sym in IDS}
    for w in WARP_SPEC["warps"]:
        warps_by_src[w["source"]].append(w)
    rows=[]
    warp_hashes={}
    for mid in range(600,677):
        sym=next((s for s,ident in IDS.items() if ident==mid),f"JOHTO_SYNTH_{mid}")
        cells=[0]*(W*H*3)
        if mid==676:
            for x,y,z in ((7,6,5328),(10,6,5329),(13,6,5330)):
                cells[x+W*(y+H*2)]=z
        existing={}
        for idx,w in enumerate(warps_by_src.get(sym,[]),1):
            page=event_page(warp=(IDS[w["target"]],w["arrival_x"],w["arrival_y"]),touch=True)
            existing[idx]=ruby("RPG::Event",id=idx,name=w["key"].encode("ascii"),
                x=w["x"],y=w["y"],pages=[page])
        mapobj=RubyObject("RPG::Map",{
            "@width":W,"@height":H,"@tileset_id":1,
            "@data":tab(3,W,H,3,cells),"@events":existing,
            "@autoplay_bgm":False,"@autoplay_bgs":False
        })
        path=preview/"Data"/f"Map{mid:03d}.rxdata"
        path.write_bytes(serialize(mapobj,EVENT_CLASSES))
        if existing:
            warp_hashes[str(mid)]=checksum(path)
        rows.append({"symbol":sym,"destination_id":mid,"events_imported":0,
                     **({"blue_authored_warps":len(existing)} if existing else {})})
    stage={
        "schema":1,"region":"JOHTO","status":"BLUE_WARP_PREVIEW_ONLY_NOT_PLAYABLE",
        "not_playable":True,"can_install":False,"source_archive_sha256":"a"*64,
        "native_mapinfos_sha256":checksum(preview/"Data/MapInfos.rxdata"),
        "native_tilesets_sha256":checksum(preview/"Data/Tilesets.rxdata"),
        "maps":rows,"warnings":[]
    }
    (preview/"johto-stage.json").write_text(json.dumps(stage),encoding="utf-8")
    proof={
        "schema":1,"region":"JOHTO",
        "status":"SIX_BLUE_WARPS_STATIC_AUDIT_NOT_ENGINE_TESTED",
        "can_install":False,"tested_in_game":False,
        "warps":[{**w,"source_id":IDS[w["source"]],
                  "destination_id":IDS[w["target"]]} for w in WARP_SPEC["warps"]],
        "warped_map_sha256":warp_hashes
    }
    (preview/"johto-warp-preview.json").write_text(json.dumps(proof),encoding="utf-8")
    contract=root/"data/regions/johto-stage08-story.json"
    contract.parent.mkdir(parents=True)
    contract.write_text(json.dumps(STORY_SPEC),encoding="utf-8")
    return preview,root/"game/Graphics/Characters",contract


class JohtoStoryEventsOfflineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="johto-story-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.preview,self.sprites,self.specfile=make_fixture(self.base)

    def test_contract_has_three_unique_balls_and_three_npcs(self):
        npcs,balls=validate_spec(copy.deepcopy(STORY_SPEC))
        self.assertEqual(len(npcs),3)
        self.assertEqual(len(balls),3)
        self.assertEqual({x["species"] for x in balls},
                         {"CHIKORITA","CYNDAQUIL","TOTODILE"})
        self.assertTrue(all(x["y"]==x["static_tile_y"]+1 for x in balls))

    def test_compilation_preserves_all_six_warps_and_creates_six_events(self):
        report,blobs=compile_story(STORY_SPEC,self.preview,self.sprites)
        self.assertEqual(report["original_warps_preserved"],6)
        self.assertEqual(report["story_events_added"],6)
        self.assertEqual(report["starter_ball_events"],3)
        self.assertEqual(report["static_starter_ball_tiles_removed"],3)
        self.assertEqual(sorted(blobs),[625,675,676])
        self.assertEqual(report["other_maps_preserved"],74)
        self.assertFalse(report["gameplay_playable"])
        self.assertFalse(report["tested_in_game"])
        for mid,expected in ((625,1),(675,3),(676,5)):
            new=loads(blobs[mid]);old=read_map_data(self.preview/"Data"/f"Map{mid:03d}.rxdata")
            self.assertEqual(len(new.attrs["@events"]),expected)
            original=old.attrs["@events"]
            self.assertTrue(all(new.attrs["@events"][i]==ev for i,ev in original.items()))
        lab=loads(blobs[676])
        dims,values=self.decode_table(lab.attrs["@data"].data)
        self.assertEqual(dims,(W,H,3))
        for ball in STORY_SPEC["starter_balls"]:
            self.assertEqual(values[ball["static_tile_x"]+
                                    W*(ball["static_tile_y"]+H*2)],0)
        names={ev.attrs["@name"] for ev in lab.attrs["@events"].values()}
        self.assertIn(b"JH_STARTER_CHIKORITA",names)
        self.assertIn(b"JH_STARTER_CYNDAQUIL",names)
        self.assertIn(b"JH_STARTER_TOTODILE",names)

    @staticmethod
    def decode_table(raw):
        d,w,h,z,count=struct.unpack_from("<5I",raw)
        return (w,h,z),struct.unpack_from(f"<{count}H",raw,20)

    def test_explicit_starter_scripts_not_elm_menu(self):
        report,blobs=compile_story(STORY_SPEC,self.preview,self.sprites)
        lab=loads(blobs[676])
        scripts={}
        for ev in lab.attrs["@events"].values():
            commands=ev.attrs["@pages"][0].attrs["@list"]
            scripts[ev.attrs["@name"]]=commands[0].attrs["@parameters"][0]
        self.assertEqual(scripts[b"JH_STARTER_CHIKORITA"],
                         b"BlueJohtoPilot.choose_starter_from_ball(:CHIKORITA)")
        self.assertEqual(scripts[b"JH_STARTER_CYNDAQUIL"],
                         b"BlueJohtoPilot.choose_starter_from_ball(:CYNDAQUIL)")
        self.assertEqual(scripts[b"JH_STARTER_TOTODILE"],
                         b"BlueJohtoPilot.choose_starter_from_ball(:TOTODILE)")
        self.assertFalse(any(b"BlueJohtoPilot.choose_starter("==value for value in scripts.values()))

    def test_incorrect_static_ball_fails_closed(self):
        obj=read_map_data(self.preview/"Data/Map676.rxdata")
        shape,cells=self.decode_table(obj.attrs["@data"].data)
        change=list(cells);change[7+W*(6+H*2)]=0
        obj.attrs["@data"].data=struct.pack("<5I",3,*shape,len(change))+struct.pack(
            f"<{len(change)}H",*change)
        (self.preview/"Data/Map676.rxdata").write_bytes(serialize(obj,EVENT_CLASSES))
        with self.assertRaisesRegex(ValueError,"estática"):
            compile_story(STORY_SPEC,self.preview,self.sprites)

    def test_missing_existing_warp_rejected(self):
        obj=read_map_data(self.preview/"Data/Map675.rxdata")
        obj.attrs["@events"].pop(1)
        (self.preview/"Data/Map675.rxdata").write_bytes(serialize(obj,EVENT_CLASSES))
        with self.assertRaisesRegex(ValueError,"faltam/excedem"):
            compile_story(STORY_SPEC,self.preview,self.sprites)

    def test_duplicate_species_or_ball_location_rejected(self):
        s=copy.deepcopy(STORY_SPEC)
        s["starter_balls"][1]["species"]="CHIKORITA"
        with self.assertRaisesRegex(ValueError,"adulterada"):
            validate_spec(s)

    def test_fake_engine_approval_rejected(self):
        s=copy.deepcopy(STORY_SPEC)
        s["approval"]["tested_in_game"]=True
        with self.assertRaisesRegex(ValueError,"certificar"):
            validate_spec(s)
        s=copy.deepcopy(STORY_SPEC)
        s["starter_balls"][0]["engine_verified"]=True
        with self.assertRaisesRegex(ValueError,"adulterada"):
            validate_spec(s)

    def test_missing_sprite_rejected(self):
        (self.sprites/"NPC_HGSS_Silver.png").unlink()
        with self.assertRaisesRegex(ValueError,"Sprite PNG"):
            compile_story(STORY_SPEC,self.preview,self.sprites)

    def test_stage_status_rejected_if_not_warps_preview(self):
        path=self.preview/"johto-stage.json"
        manifest=json.loads(path.read_text("utf-8"))
        manifest["status"]="BLUE_STORY_PREVIEW_ONLY_NOT_PLAYABLE"
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,"etapa 07"):
            compile_story(STORY_SPEC,self.preview,self.sprites)

    def test_preview_build_keeps_unmodified_maps_and_metadata(self):
        output=self.base/".blue-work/johto-staging-story-v1"
        before={p.name:checksum(p) for p in (self.preview/"Data").glob("Map*.rxdata")}
        result=build(root=self.base,preview=self.preview,output=output,
                     spec_path=self.specfile,sprites=self.sprites)
        self.assertEqual(result["story_events_added"],6)
        self.assertTrue(output.is_dir())
        after={p.name:checksum(p) for p in (output/"Data").glob("Map*.rxdata")}
        changed={name for name in before if before[name]!=after[name]}
        self.assertEqual(changed,{"Map625.rxdata","Map675.rxdata","Map676.rxdata"})
        for file in ("MapInfos.rxdata","Tilesets.rxdata"):
            self.assertEqual(checksum(output/"Data"/file),
                             checksum(self.preview/"Data"/file))
        with self.assertRaisesRegex(ValueError,"novo destino|Só é permitido"):
            build(root=self.base,preview=self.preview,output=output,
                  spec_path=self.specfile,sprites=self.sprites)

if __name__=="__main__":
    unittest.main()
