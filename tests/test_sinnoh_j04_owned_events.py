"""J04: synthetic-owned complete nine-map event compiler and denial suite.

No donor assets, saves, ROMs or private paths are used by CI.
"""
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
sys.path.insert(0,str(ROOT/"scripts/regions"))
from build_johto_events import ruby
from server.ruby_marshal import RubyData,loads
from stage import serialize
from sinnoh_staging_transaction import preview,stage,rollback
import compile_sinnoh_playable_j04 as j04

SHA=lambda b:hashlib.sha256(b).hexdigest()
PNG=b"\x89PNG\r\n\x1a\nowned-synthetic-pixel-data"
W=16
H=16
SAMPLES=("BlueNPC","BlueBall")
SAMPLE_SPRITES={
    "Graphics/Characters/BlueNPC.png":SHA(PNG),
    "Graphics/Characters/BlueBall.png":SHA(PNG),
}

def area(w=W,h=H,ground=384):
    n=w*h*3
    vals=[ground]*(w*h)+[0]*(n-w*h)
    return RubyData("Table",struct.pack("<5I",3,w,h,3,n)
                    +struct.pack("<"+str(n)+"H",*vals))

def put(root,rel,data):
    path=root/rel
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data)
    return path

class J04OwnedEventTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.game=self.root/"game"/"Data"
        self.game.mkdir(parents=True)
        self.native_infos={1:ruby("RPG::MapInfo",name=b"Decades",order=1)}
        self.native_tiles=[None,ruby("RPG::Tileset",id=1,name=b"Original",
            passages=[0]*400)]
        put(self.root,"game/Data/MapInfos.rxdata",serialize(self.native_infos))
        put(self.root,"game/Data/Tilesets.rxdata",serialize(self.native_tiles))
        put(self.root,"game/Data/Map001.rxdata",b"original-main-game")
        put(self.root,"game/Save01.rxdata",b"personal-save-unchanged")
        self.game_sha=SHA((self.game/"MapInfos.rxdata").read_bytes())
        self.original={
            "mapinfos":(self.game/"MapInfos.rxdata").read_bytes(),
            "tiles":(self.game/"Tilesets.rxdata").read_bytes(),
            "map":(self.game/"Map001.rxdata").read_bytes(),
            "save":(self.root/"game/Save01.rxdata").read_bytes(),
        }
        with (ROOT/"data/regions/sinnoh-twinleaf-events.json").open("r",encoding="utf-8") as f:
            self.spec=json.load(f)
        self.spec["start"].update({
            "map_id":442,"x":9,"y":9,
            "verified_position":True,"passability_verified":True
        })
        self.mapids={}
        self.maps={}
        self.source_infos=copy.deepcopy(self.native_infos)
        self.tilesets=copy.deepcopy(self.native_tiles)
        self.tilesets.append(ruby("RPG::Tileset",id=2,
            name=b"OwnSynthetic",passages=[0]*400,autotile_names=[],
            tileset_name=b"SyntheticOwned"))
        self.files={}
        for i,row in enumerate(self.spec["maps"]):
            mid=442+i
            self.mapids[row["symbol"]]=mid
            world=ruby("RPG::Map",width=W,height=H,tileset_id=2,
                       data=area(),events={},autoplay_bgm=False,autoplay_bgs=False,
                       encounter_list=[])
            raw=serialize(world)
            self.files[f"Data/Map{mid:03d}.rxdata"]=raw
            self.maps[mid]=world
            row["map_id"]=mid
            row["map_sha256"]=SHA(raw)
            self.source_infos[mid]=ruby("RPG::MapInfo",
                name=row["symbol"].encode("ascii"),order=10000+mid)
            for n,e in enumerate(row["events"]):
                e["x"]=n+1
                e["y"]=2
                e["verified_position"]=True
                if e["kind"]=="warp":
                    e["arrival_x"]=9
                    e["arrival_y"]=9
                    e["verified_arrival"]=True
                else:
                    e["sprite"]="BlueBall" if e["kind"]=="starter_ball" else "BlueNPC"
                    e["verified_sprite"]=True
        self.files["Data/MapInfos.rxdata"]=serialize(self.source_infos)
        self.files["Data/Tilesets.rxdata"]=serialize(self.tilesets)
        for name in SAMPLES:
            self.files[f"Graphics/Characters/{name}.png"]=PNG
        dry=preview(self.root,"j04-source",self.files)
        stage(self.root,"j04-source",self.files,dry["plan_sha256"])
        self.input_sha=dry["plan_sha256"]
        self.reservations={
            "schema":1,"region":"SINNOH","mode":"LOCAL_RESERVATIONS_CANDIDATE",
            "baseline_mapinfos_sha256":self.game_sha,
            "protected_ids":[2,600,700],
        }
        self.review={
            "schema":1,"region":"SINNOH","mode":"J04_PRIVATE_SPRITE_REVIEW",
            "baseline_mapinfos_sha256":self.game_sha,
            "map_stage_plan_sha256":self.input_sha,
            "reviewed_locally":True,
            "sprite_sha256":copy.deepcopy(SAMPLE_SPRITES),
        }
        self.patcher=patch.object(j04,"game_inventory",
                                 return_value=(self.game_sha,{1}))
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def compiled(self):
        return j04.compile_private_events(
            self.root,"j04-source",self.input_sha,self.spec,self.review,
            self.game,self.reservations)

    def denied(self):
        with self.assertRaises(ValueError):
            self.compiled()

    def test_compiles_16_warps_5_npcs_three_balls_on_nine_synthetic_maps(self):
        files,info=self.compiled()
        self.assertEqual(info["events_compiled"],24)
        self.assertEqual(info["warps_compiled"],16)
        self.assertEqual(info["npc_handlers_compiled"],5)
        self.assertEqual(info["starter_balls_compiled"],3)
        self.assertEqual(info["maps_in_source_stage_verified"],9)
        self.assertEqual(info["sprite_files_hash_checked"],2)
        self.assertEqual(info["donor_events_imported"],0)
        self.assertFalse(info["can_install"])
        self.assertFalse(info["native_playable"])
        self.assertFalse(info["story_handlers_runtime_verified"])
        self.assertEqual(len([k for k in files if k.startswith("Data/Map") and k.endswith(".rxdata") and "Infos" not in k]),9)

    def test_all_24_commands_from_allowlist_and_transfers_real_mapids(self):
        files,info=self.compiled()
        scripts=set()
        transfers=0
        count=0
        for sym,mid in self.mapids.items():
            world=loads(files[f"Data/Map{mid:03d}.rxdata"])
            self.assertEqual(world.attrs["@autoplay_bgm"],False)
            self.assertEqual(world.attrs["@encounter_list"],[])
            for e in world.attrs["@events"].values():
                count+=1
                p=e.attrs["@pages"][0]
                op=p.attrs["@list"][0]
                if op.attrs["@code"]==201:
                    transfers+=1
                    params=op.attrs["@parameters"]
                    self.assertIn(params[1],list(self.mapids.values()))
                    self.assertLess(params[2],W)
                    self.assertLess(params[3],H)
                else:
                    self.assertEqual(op.attrs["@code"],355)
                    scripts.add(op.attrs["@parameters"][0].decode("ascii"))
        self.assertEqual(count,24)
        self.assertEqual(transfers,16)
        self.assertEqual(scripts,{
            "BlueSinnohPilot.mother","BlueSinnohPilot.barry_intro",
            "BlueSinnohPilot.rowan_briefcase","BlueSinnohPilot.barry_rival",
            "BlueSinnohPilot.rowan_pokedex",
            "BlueSinnohPilot.choose_starter(:TURTWIG)",
            "BlueSinnohPilot.choose_starter(:CHIMCHAR)",
            "BlueSinnohPilot.choose_starter(:PIPLUP)",
        })

    def test_preview_output_has_same_input_images_and_main_game_unchanged(self):
        files,report=self.compiled()
        self.assertEqual(files["Graphics/Characters/BlueNPC.png"],PNG)
        self.assertEqual(loads(files["Data/MapInfos.rxdata"])[1].attrs["@name"],b"Decades")
        self.assertEqual(loads(files["Data/Tilesets.rxdata"])[1].attrs["@name"],b"Original")
        self.assertEqual((self.game/"MapInfos.rxdata").read_bytes(),self.original["mapinfos"])
        self.assertEqual((self.game/"Tilesets.rxdata").read_bytes(),self.original["tiles"])
        self.assertEqual((self.root/"game/Save01.rxdata").read_bytes(),self.original["save"])

    def test_output_stage_receipt_verify_and_exact_rollback(self):
        files,report=self.compiled()
        dry=preview(self.root,"j04-events",files)
        out=stage(self.root,"j04-events",files,dry["plan_sha256"])
        self.assertTrue((self.root/out["stage_relative_path"]).is_dir())
        verified=j04.stage_verify(self.root,"j04-events",dry["plan_sha256"])
        self.assertFalse(verified["native_playable"])
        self.assertEqual(verified["files_verified"],len(files))
        res=rollback(self.root,"j04-events",dry["plan_sha256"])
        self.assertTrue(res["removed_only_stage"])
        self.assertFalse((self.root/out["stage_relative_path"]).exists())
        self.assertEqual((self.root/"game/Save01.rxdata").read_bytes(),self.original["save"])

    def test_wrong_dry_run_hash_does_not_create_output(self):
        files,_=self.compiled()
        with self.assertRaises(ValueError):
            stage(self.root,"j04-events",files,"a"*64)
        self.assertFalse(any((self.root/".blue-work/sinnoh-stage").glob("j04-events-*")))

    def test_tampered_output_refuses_verify_and_rollback(self):
        files,_=self.compiled()
        dry=preview(self.root,"j04-events",files)
        out=stage(self.root,"j04-events",files,dry["plan_sha256"])
        folder=self.root/out["stage_relative_path"]
        (folder/"Data/Map442.rxdata").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            j04.stage_verify(self.root,"j04-events",dry["plan_sha256"])
        with self.assertRaises(ValueError):
            rollback(self.root,"j04-events",dry["plan_sha256"])
        self.assertTrue(folder.exists())

    def test_one_missing_map_in_stage_fails_closed(self):
        folder=self.root/".blue-work/sinnoh-stage"/f"j04-source-{self.input_sha[:16]}"
        (folder/"Data/Map443.rxdata").unlink()
        self.denied()

    def test_one_source_stage_extra_file_fails_closed(self):
        folder=self.root/".blue-work/sinnoh-stage"/f"j04-source-{self.input_sha[:16]}"
        (folder/"private.zip").write_bytes(b"NO")
        self.denied()

    def test_bad_input_hash_denied(self):
        with self.assertRaises(ValueError):
            j04.compile_private_events(self.root,"j04-source","0"*64,
                self.spec,self.review,self.game,self.reservations)

    def test_wrong_input_label_denied(self):
        with self.assertRaises(ValueError):
            j04.compile_private_events(self.root,"../../game",self.input_sha,
                self.spec,self.review,self.game,self.reservations)

    def test_missing_one_symbol_denied(self):
        self.spec["maps"].pop()
        self.denied()

    def test_duplicate_mapid_denied(self):
        self.spec["maps"][1]["map_id"]=442
        self.denied()

    def test_outside_assigned_range_denied(self):
        for bad in (0,441,518,805,True,"442",-1,999):
            with self.subTest(bad=bad):
                self.spec["maps"][0]["map_id"]=bad
                self.denied()
        self.spec["maps"][0]["map_id"]=442

    def test_protected_mapid_denied(self):
        self.reservations["protected_ids"].append(442)
        self.denied()

    def test_duplicate_reserved_id_denied(self):
        self.reservations["protected_ids"]=[600,600]
        self.denied()

    def test_stale_baseline_sha_denied(self):
        self.reservations["baseline_mapinfos_sha256"]="f"*64
        self.denied()

    def test_stale_game_baseline_changed_denied(self):
        (self.game/"MapInfos.rxdata").write_bytes(b"new")
        self.denied()

    def test_map_hash_tampered_denied(self):
        self.spec["maps"][0]["map_sha256"]="a"*64
        self.denied()

    def test_missing_npc_sprite_denied(self):
        self.review["sprite_sha256"].pop("Graphics/Characters/BlueNPC.png")
        self.denied()

    def test_sprite_rights_not_reviewed_denied(self):
        self.review["reviewed_locally"]=False
        self.denied()

    def test_sprite_shas_changed_denied(self):
        self.review["sprite_sha256"]["Graphics/Characters/BlueBall.png"]="a"*64
        self.denied()

    def test_sprite_extra_denied(self):
        self.review["sprite_sha256"]["Graphics/Characters/Extras.png"]="a"*64
        self.denied()

    def test_sprite_name_path_escape_denied(self):
        self.spec["maps"][1]["events"][0]["sprite"]="../../etc/passwd"
        self.denied()

    def test_missing_real_sprite_denied(self):
        folder=self.root/".blue-work/sinnoh-stage"/f"j04-source-{self.input_sha[:16]}"
        (folder/"Graphics/Characters/BlueNPC.png").unlink()
        self.denied()

    def test_npc_handler_not_allowlisted_denied(self):
        for row in self.spec["maps"]:
            for e in row["events"]:
                if e["kind"]=="handler":
                    e["handler"]="exec_external_code"
                    self.denied()
                    return
        self.fail("No handlers")

    def test_missing_one_starter_ball_denied(self):
        for row in self.spec["maps"]:
            if row["symbol"]=="SINNOH_LAKE_VERITY":
                row["events"]=[e for e in row["events"] if e["key"]!="SN_BALL_PIPLUP"]
        self.denied()

    def test_duplicate_starter_denied(self):
        for row in self.spec["maps"]:
            for e in row["events"]:
                if e["key"]=="SN_BALL_PIPLUP":
                    e["species"]="TURTWIG"
                    self.denied()
                    return
        self.fail("No Piplup")

    def test_orphan_warp_denied(self):
        for row in self.spec["maps"]:
            for e in row["events"]:
                if e["kind"]=="warp":
                    e["destination"]="SINNOH_UNKNOWN_AREA"
                    self.denied()
                    return
        self.fail("No warps")

    def test_warp_arrival_oob_denied(self):
        for row in self.spec["maps"]:
            for e in row["events"]:
                if e["kind"]=="warp":
                    e["arrival_x"]=W
                    self.denied()
                    return

    def test_unverified_warp_arrival_denied(self):
        for row in self.spec["maps"]:
            for e in row["events"]:
                if e["kind"]=="warp":
                    e["verified_arrival"]=False
                    self.denied()
                    return

    def test_event_position_oob_denied(self):
        self.spec["maps"][0]["events"][0]["x"]=W
        self.denied()

    def test_duplicate_event_position_denied(self):
        e=self.spec["maps"][5]["events"]
        e[1]["x"]=e[0]["x"]
        self.denied()

    def test_unverified_event_position_denied(self):
        self.spec["maps"][0]["events"][0]["verified_position"]=False
        self.denied()

    def test_spawn_wrong_map_denied(self):
        self.spec["start"]["map_id"]=447
        self.denied()

    def test_spawn_not_verified_denied(self):
        self.spec["start"]["passability_verified"]=False
        self.denied()

    def test_event_blocked_by_real_passages_denied(self):
        world=copy.deepcopy(self.maps[442])
        tile=copy.deepcopy(self.tilesets)
        tile[2].attrs["@passages"][384]=15
        with self.assertRaises(ValueError):
            j04.passable_point(world,tile,1,2)

    def test_event_void_terrain_denied(self):
        world=copy.deepcopy(self.maps[442])
        world.attrs["@data"]=j04.RubyData("Table",
            struct.pack("<5I",3,W,H,3,W*H*3)+struct.pack("<"+str(W*H*3)+"H",*([0]*(W*H*3))))
        with self.assertRaises(ValueError):
            j04.passable_point(world,self.tilesets,1,2)

    def test_missing_tile_passage_denied(self):
        world=copy.deepcopy(self.maps[442])
        tile=copy.deepcopy(self.tilesets)
        tile[2].attrs["@passages"]=[0]*32
        with self.assertRaises(ValueError):
            j04.passable_point(world,tile,1,2)

    def test_invalid_native_tilemap_baseline_denied(self):
        (self.game/"Tilesets.rxdata").write_bytes(b"fake")
        self.denied()

    def test_native_infos_preservation_mismatch_denied(self):
        stage_info=copy.deepcopy(self.source_infos)
        stage_info[1]=ruby("RPG::MapInfo",name=b"Tampered Decades")
        with self.assertRaises(ValueError):
            j04._preserve_native_infos(stage_info,self.native_infos,{1},list(self.mapids.values()))

    def test_unverified_source_stage_non_rmxp_map_denied(self):
        # Only a synthetic unit mutation; hash mismatch triggers before marshal.
        path=self.root/".blue-work/sinnoh-stage"/f"j04-source-{self.input_sha[:16]}"/"Data/Map442.rxdata"
        path.write_bytes(b"NO")
        self.denied()

    def test_draft_without_maps_terminates_without_writes(self):
        report=j04.no_real_inputs(ROOT)
        self.assertEqual(report["compiled_native_events"],0)
        self.assertEqual(report["planned_warps"],16)
        self.assertEqual(report["planned_npc_handlers"],5)
        self.assertEqual(report["planned_starter_balls"],3)
        self.assertFalse(report["native_playable"])

    def test_cli_no_inputs_returns_blocked(self):
        self.assertEqual(j04.main(["--project",str(ROOT)]),2)

    def test_cli_cannot_pass_install_into_game(self):
        with self.assertRaises(SystemExit):
            j04.main(["--install-into-main-game"])

    def test_cli_without_real_assets_cannot_stage(self):
        self.assertEqual(j04.main(["--project",str(ROOT),"--stage"]),2)

    def test_no_user_saves_or_other_regions_touched(self):
        files,info=self.compiled()
        self.assertEqual((self.root/"game/Save01.rxdata").read_bytes(),self.original["save"])
        self.assertEqual((self.game/"Map001.rxdata").read_bytes(),self.original["map"])
        self.assertEqual((self.game/"MapInfos.rxdata").read_bytes(),self.original["mapinfos"])
        self.assertFalse(info["game_modified"])
        self.assertFalse(info["saves_read_or_modified"])

if __name__=="__main__":
    unittest.main()
