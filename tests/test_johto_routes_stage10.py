"""Offline checks for routes29/30/31 wild PBS and trainers. No Game.exe."""
from __future__ import annotations

import copy
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from build_johto_routes_stage10 import (
    build_pbs,compile_stage,grid_for_map,learn_moves,load_contract,
    publish,validate_contract
)
from audit_johto import checksum,read_map_data
from build_johto_events import EVENT_CLASSES,event_page,ruby
from stage import serialize
from server.ruby_marshal import RubyData,RubyObject

SPEC=json.loads((ROOT/"data/regions/johto-stage10-routes.json").read_text(encoding="utf-8"))


def rmxp_table(d:int,w:int,h:int,z:int,vals:list[int])->RubyData:
    return RubyData("Table",struct.pack("<5I",d,w,h,z,len(vals))+
                    struct.pack(f"<{len(vals)}H",*vals))


def fixture(root:Path):
    game=root/"game";pbs=game/"PBS";pbs.mkdir(parents=True)
    (game/"Graphics/Characters").mkdir(parents=True)
    for name in ("NPC_HGSS_Youngster","NPC_HGSS_Bug_Catcher"):
        (game/"Graphics/Characters"/(name+".png")).write_bytes(b"\x89PNG\r\n\x1a\nstub")
    (pbs/"trainer_types.txt").write_text(
        "[YOUNGSTER]\nName = Youngster\nGender = Male\nBaseMoney = 16\n"
        "[BUGCATCHER]\nName = Bug Catcher\nGender = Male\nBaseMoney = 16\n",encoding="utf-8")
    species={"PIDGEY","SENTRET","RATTATA","HOOTHOOT","SPINARAK",
             "CATERPIE","WEEDLE","BELLSPROUT","LEDYBA"}
    learn="1,TACKLE,3,GROWL,5,QUICKATTACK,7,PECK,9,ROOST"
    (pbs/"pokemon.txt").write_text(
        "\n".join(f"[{mon}]\nName = {mon}\nMoves = {learn}" for mon in species),
        encoding="utf-8")
    (pbs/"moves.txt").write_text(
        "\n".join(f"[{mon}]\nName = {mon}" for mon in
                  ("TACKLE","GROWL","QUICKATTACK","PECK","ROOST")),
        encoding="utf-8")
    (pbs/"trainers.txt").write_text(
        "[YOUNGSTER,Generic]\nPokemon = PIDGEY,4\n",encoding="utf-8")
    return game


def make_story_preview(root:Path):
    stage=root/".blue-work/johto-staging-story-v1"
    (stage/"Data").mkdir(parents=True)
    tiles=[None,RubyObject("RPG::Tileset",{
        "@passages":rmxp_table(1,6000,1,1,[0]*6000)
    })]
    (stage/"Data/Tilesets.rxdata").write_bytes(serialize(tiles))
    (stage/"Data/MapInfos.rxdata").write_bytes(serialize({}))
    rows=[]
    for n in range(600,677):
        symbol=({625:"JOHTO_ROUTE_29",626:"JOHTO_ROUTE_30",
                 627:"JOHTO_ROUTE_31"}.get(n,f"JOHTO_SYNTH_{n}"))
        ev={}
        if n==625:
            page=event_page(script="BlueJohtoPilot.rival",sprite="NPC_HGSS_Silver")
            ev[1]=ruby("RPG::Event",id=1,name=b"JH_ROUTE29_NPC_RIVAL",
                       x=71,y=17,pages=[page])
        width,height=90,70
        obj=RubyObject("RPG::Map",{
            "@width":width,"@height":height,"@tileset_id":1,
            "@data":rmxp_table(3,width,height,3,[0]*(width*height*3)),
            "@events":ev,"@autoplay_bgm":False,"@autoplay_bgs":False
        })
        (stage/"Data"/f"Map{n:03d}.rxdata").write_bytes(
            serialize(obj,EVENT_CLASSES))
        rows.append({"source_id":n-521,"destination_id":n,"symbol":symbol,"events_imported":0})
    (stage/"johto-stage.json").write_text(json.dumps({
        "schema":1,"region":"JOHTO","status":"BLUE_STORY_PREVIEW_ONLY_NOT_PLAYABLE",
        "not_playable":True,"can_install":False,"maps":rows,"warnings":[]
    }),encoding="utf-8")
    (stage/"johto-story-preview.json").write_text(json.dumps({
        "status":"STORY_EVENTS_COMPILED_OFFLINE_NOT_PLAYABLE",
        "original_warps_preserved":6,"story_events_added":6,
        "can_install":False
    }),encoding="utf-8")
    return stage


class JohtoRoutesOfflineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="johto-route10-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.game=fixture(self.root)

    def test_contract_three_routes_six_tables_and_five_trainers(self):
        validate_contract(copy.deepcopy(SPEC))
        self.assertEqual([r["map_id"] for r in SPEC["routes"]],[625,626,627])
        self.assertEqual(sum(len(x["normal"]) for x in SPEC["trainers"]),10)
        self.assertEqual(sum(len(x["master"]) for x in SPEC["trainers"]),20)
        self.assertTrue(all(sum(x[0] for x in r[k])==100
                for r in SPEC["routes"] for k in ("land","night")))

    def test_native_pbs_contains_six_wild_tables_and_ten_trainer_teams(self):
        files,report=build_pbs(SPEC,self.game)
        encounter=files["PBS/encounters_johto_routes.txt"].decode("utf-8")
        trainer=files["PBS/trainers_johto_routes.txt"].decode("utf-8")
        self.assertEqual(encounter.count("Land,21"),3)
        self.assertEqual(encounter.count("LandNight,21"),3)
        self.assertEqual(trainer.count("Pokemon = "),30)
        self.assertEqual(len(report["trainers"]),10)
        self.assertTrue(all(len(t["team"])==(4 if t["version"]==1 else 2)
                        for t in report["trainers"]))
        self.assertFalse(report["can_install"])
        self.assertFalse(report["pbs_compiled"])
        self.assertFalse(report["master_level_scaling_verified"])
        self.assertFalse(report["gameplay_ready_marker_created"])

    def test_moves_learned_not_future_only(self):
        result=learn_moves("1,GROWL,1,TACKLE,4,QUICKATTACK,9,ROOST",
                {"GROWL","TACKLE","QUICKATTACK","ROOST"},5)
        self.assertEqual(result,["GROWL","TACKLE","QUICKATTACK"])
        with self.assertRaisesRegex(ValueError,"learnset|Nível|Pokémon|golpe"):
            learn_moves("12,ROOST",{"ROOST"},5)

    def test_reject_encounter_probability_tamper(self):
        x=copy.deepcopy(SPEC);x["routes"][0]["land"][0][0]=49
        with self.assertRaisesRegex(ValueError,"100%"):
            validate_contract(x)

    def test_reject_master_team_without_four(self):
        x=copy.deepcopy(SPEC);x["trainers"][0]["master"].pop()
        with self.assertRaisesRegex(ValueError,"4 no Master"):
            validate_contract(x)

    def test_reject_missing_species(self):
        file=self.game/"PBS/pokemon.txt"
        file.write_text(file.read_text(encoding="utf-8").replace("[SPINARAK]","[MISSING]"),
                        encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"ausentes"):
            build_pbs(SPEC,self.game)

    def test_reject_duplicate_existing_trainer(self):
        (self.game/"PBS/trainers.txt").write_text(
            "[YOUNGSTER,Johto Mikey,0]\nPokemon = RATTATA,5\n",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"colide"):
            build_pbs(SPEC,self.game)

    def test_reject_unsupported_local_balancing_formula(self):
        x=copy.deepcopy(SPEC);x["balance_policy"]["trainer_master_ratio"]=0.70
        with self.assertRaisesRegex(ValueError,"Balanceamento"):
            validate_contract(x)

    def test_full_stage_adds_five_events_only_and_preserves_silver(self):
        preview=make_story_preview(self.root)
        report=publish(ROOT/"data/regions/johto-stage10-routes.json",
                       self.game,preview,
                       self.root/".blue-work/johto-staging-routes-v1",root=self.root)
        output=self.root/".blue-work/johto-staging-routes-v1"
        self.assertEqual([x["map_id"] for x in report["map_changes"]],[625,626,627])
        self.assertEqual(report["map_count_preserved"],74)
        self.assertEqual(sum(x["events_added"] for x in report["map_changes"]),5)
        for id in (625,626,627):
            old=read_map_data(preview/"Data"/f"Map{id:03d}.rxdata")
            new=read_map_data(output/"Data"/f"Map{id:03d}.rxdata")
            self.assertEqual(len(new.attrs["@events"])-len(old.attrs["@events"]),
                             {625:1,626:2,627:2}[id])
        self.assertEqual(
            checksum(preview/"Data/Map674.rxdata"),
            checksum(output/"Data/Map674.rxdata"))
        self.assertEqual(
            checksum(preview/"Data/MapInfos.rxdata"),
            checksum(output/"Data/MapInfos.rxdata"))
        self.assertEqual(
            checksum(preview/"Data/Tilesets.rxdata"),
            checksum(output/"Data/Tilesets.rxdata"))
        self.assertFalse((output/"Data/blue-johto-routes-ready.txt").exists())
        with self.assertRaisesRegex(ValueError,"Apenas nova pasta"):
            publish(ROOT/"data/regions/johto-stage10-routes.json",self.game,
                    preview,output,root=self.root)

    def test_stage_reject_blocked_npc_tile(self):
        preview=make_story_preview(self.root)
        room=read_map_data(preview/"Data/Map625.rxdata")
        w,h=room.attrs["@width"],room.attrs["@height"]
        data=room.attrs["@data"]
        values=[0]*(w*h*3)
        values[36+w*10]=1
        data.data=struct.pack("<5I",3,w,h,3,len(values))+struct.pack(
            f"<{len(values)}H",*values)
        (preview/"Data/Map625.rxdata").write_bytes(serialize(room,EVENT_CLASSES))
        tilefile=preview/"Data/Tilesets.rxdata"
        tiles=read_map_data(tilefile)
        flags=[0]*6000;flags[1]=15
        tiles[1].attrs["@passages"].data=struct.pack("<5I",1,len(flags),1,1,len(flags))+struct.pack(f"<{len(flags)}H",*flags)
        tilefile.write_bytes(serialize(tiles))
        files,report=build_pbs(SPEC,self.game)
        with self.assertRaisesRegex(ValueError,"colisão"):
            compile_stage(SPEC,preview,self.game,files,report)


if __name__=="__main__":
    unittest.main()
