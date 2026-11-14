"""Isolated Hoenn stage9 contract tests; no native Game.exe acceptance."""
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from build_johto_events import ruby,command
from hoenn_stage9 import (
    SOURCE_MAPS_STAGE9,SURF_BORDERS_STAGE9,STAGE9_MAP_GRAPH_EDGES,
    TATE_LIZA_PBS,TATE_LIZA_TEAM,MATT_PBS,MATT_TEAM,
    MAXIE_HIDEOUT_PBS,MAXIE_HIDEOUT_TEAM,MAXIE_SPACE_TEAM,
    TABITHA_HIDEOUT_TEAM,TRAINERS_STAGE9,PYRE_AQUA_GRUNTS,
    MAGMA_HIDEOUT_GRUNTS,AQUA_HIDEOUT_GRUNTS,SPACE_GRUNT_EVENTS,
    NPCS_STAGE9,TATE_LIZA_EVENTS,
)
from pilot_hoenn import (
    SOURCE_MAPS,WARP_PAIRS,scan_stage9_source_events,add_stage9_events,
)

class HoennStage9Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game=Path(self.temp.name)
        sprites=({row[3] for row in NPCS_STAGE9} |
                 {row[5] for row in TRAINERS_STAGE9}|
                 {"trainer_YOUNGSTER","trainer_LASS","trainer_FISHERMAN",
                  "NPC_RSE_Tate","NPC_RSE_Liza","NPC_RSE_Archie",
                  "NPC_RSE_Tabitha","NPC_RSE_Maxie","NPC_RSE_Matt",
                  "NPC_RSE_Steven","NPC_RSE_AquaGrunt","NPC_RSE_MagmaGrunt"})
        for sprite in sprites:
            f=self.game/"Graphics/Characters"/(sprite+".png")
            f.parent.mkdir(parents=True,exist_ok=True)
            f.write_bytes(b"\x89PNG\r\n\x1a\nstage9-synthetic-test-only")
        dimensions={mid:(360,40) if mid==76 else (40,40)
                    for mid in SOURCE_MAPS_STAGE9}
        dimensions.update({81:(60,20),82:(40,45),206:(30,30),207:(20,20),
                           216:(60,40),217:(40,30),69:(80,40),180:(30,48)})
        self.maps={mid:ruby("RPG::Map",width=dimensions.get(mid,(40,40))[0],
                            height=dimensions.get(mid,(40,40))[1],events={})
                   for mid in set(SOURCE_MAPS_STAGE9)|{69,180}}
        self.sample_warps=[
            (141,22,29,206,16,20,"Mt. Pyre Entrance"),
            (206,16,21,141,22,29,"Cave Exit"),
            (216,22,6,216,34,21,"Warp Tile A1"),
            (215,14,30,69,70,5,"Cave Exit"),
        ]
        self.sample_pickups=[(207,2,12,"ULTRABALL",True)]

    def test_source_inventory_and_coastal_gates(self):
        self.assertEqual(len(SOURCE_MAPS_STAGE9),28)
        self.assertEqual(len(SOURCE_MAPS),138)
        self.assertEqual(len(WARP_PAIRS),130)
        self.assertEqual(set(SURF_BORDERS_STAGE9),{
            (139,"South",20,141,"North",0),
            (144,"West",10,69,"East",0),
            (144,"East",40,76,"West",0)})
        self.assertEqual(len(STAGE9_MAP_GRAPH_EDGES),29)
        self.assertIn((141,206),STAGE9_MAP_GRAPH_EDGES)
        self.assertIn((180,182),STAGE9_MAP_GRAPH_EDGES)
        self.assertIn((69,215),STAGE9_MAP_GRAPH_EDGES)
        self.assertNotIn(83,SOURCE_MAPS)  # Sootopolis is Stage10
        self.assertNotIn(227,SOURCE_MAPS) # Seafloor Cavern Stage10

    def test_boss_party_and_source_anchor_contract(self):
        self.assertEqual(TATE_LIZA_PBS,("BLUE_HOENN_TATE_LIZA","Tate & Liza",982))
        self.assertEqual(TATE_LIZA_TEAM,(("CLAYDOL",41),("XATU",41),
                                         ("LUNATONE",42),("SOLROCK",42)))
        self.assertEqual(TATE_LIZA_EVENTS,((82,25,11),(82,26,11)))
        self.assertEqual(MATT_PBS,("BLUE_HOENN_MATT","Matt",917))
        self.assertEqual(MATT_TEAM,(("MIGHTYENA",34),("GOLBAT",34)))
        self.assertEqual(MAXIE_HIDEOUT_PBS,("BLUE_HOENN_MAXIE","Maxie",989))
        self.assertEqual(MAXIE_HIDEOUT_TEAM,(("MIGHTYENA",37),("CROBAT",38),
                                            ("CAMERUPT",39)))
        self.assertEqual(MAXIE_SPACE_TEAM,(("MIGHTYENA",42),("CROBAT",43),
                                          ("CAMERUPT",44)))
        self.assertEqual(TABITHA_HIDEOUT_TEAM,(("NUMEL",26),("MIGHTYENA",28),
                                               ("ZUBAT",30),("CAMERUPT",33)))
        self.assertEqual(len(TRAINERS_STAGE9),18)
        self.assertEqual(len(PYRE_AQUA_GRUNTS),4)
        self.assertEqual(len(MAGMA_HIDEOUT_GRUNTS),7)
        self.assertEqual(len(AQUA_HIDEOUT_GRUNTS),5)
        self.assertEqual(len(SPACE_GRUNT_EVENTS),2)

    def _source_event(self,name,x,y,*commands):
        return ruby("RPG::Event",name=name.encode("utf-8"),x=x,y=y,
                    pages=[ruby("RPG::Event::Page",list=list(commands))])

    def test_source_scanner_only_reads_static_direct_warps_and_real_items(self):
        originals={
            141:{1:self._source_event("Mt. Pyre Entrance",22,29,
                                     command(201,0,206,16,20,0))},
            206:{1:self._source_event("Cave Exit",16,21,
                                     command(201,0,141,22,29,0))},
            207:{1:self._source_event("Item",2,12,
                                     command(355,b"pbItemBall(:ULTRABALL)"))},
            216:{
                1:self._source_event("Warp Tile A1",22,6,
                                     command(201,0,216,34,21,0)),
                2:self._source_event("Warp Tile E activate",23,6,
                                     command(201,0,216,30,6,0)),
                3:self._source_event("Delta Episode Cutscene Controller",5,2,
                                     command(201,0,69,70,5,0)),
                4:self._source_event("Teleport outside stage",35,6,
                                     command(201,0,9999,2,3,0)),
            }
        }
        warp,items=scan_stage9_source_events(originals,self.maps)
        self.assertEqual(len(warp),3)
        self.assertEqual({(m,x,y,n) for m,x,y,d,dx,dy,n in warp},{
            (141,22,29,"Mt. Pyre Entrance"),
            (206,16,21,"Cave Exit"),
            (216,22,6,"Warp Tile A1")})
        self.assertEqual(items,[(207,2,12,"ULTRABALL",True)])

    def test_event_creation_and_collisions(self):
        report=add_stage9_events(self.maps,self.game,
                                 self.sample_warps,self.sample_pickups)
        self.assertEqual(report["new_maps"],28)
        self.assertEqual(report["auto_source_warp_events"],4)
        self.assertEqual(report["auto_source_item_events"],1)
        self.assertEqual(report["ordinary_trainers"],18)
        self.assertEqual(report["aqua_grunts"],9)
        self.assertEqual(report["magma_grunts"],9)
        self.assertFalse(report["aqua_placeholder"])
        self.assertFalse(report["magma_placeholder"])
        self.assertFalse(report["native_space_partner_battle_approved"])
        self.assertFalse(report["native_gameplay_verified"])
        names={}
        for mid,m in self.maps.items():
            events=m.attrs["@events"].values()
            places=[(e.attrs["@x"],e.attrs["@y"]) for e in events]
            self.assertEqual(len(places),len(set(places)),f"overlap {mid}")
            for e in events:names[e.attrs["@name"].decode()]=(mid,e)
        for n,mid in (("HN9_Boss_Tate",82),("HN9_Boss_Liza",82),
                      ("HN9_Boss_Archie",213),("HN9_Boss_Matt",217),
                      ("HN9_Boss_SpaceSteven",81),("HN9_Gate_MagmaEntry",180),
                      ("HN9_Gate_AquaEntry",69),
                      ("HN9_SourceWarp_141_22_29",141),
                      ("HN9_SourceItem_207_2_12",207)):
            self.assertEqual(names[n][0],mid)
        ev=names["HN9_SourceWarp_141_22_29"][1]
        script=ev.attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"][0].decode()
        self.assertEqual(script,"BlueHoennPilot.stage9_transfer(141,206,16,20)")
        item_ev=names["HN9_SourceItem_207_2_12"][1]
        self.assertEqual(len(item_ev.attrs["@pages"]),2)
        self.assertTrue(item_ev.attrs["@pages"][1].attrs["@through"])

    def test_future_asset_fallback_explicit(self):
        (self.game/"Graphics/Characters/NPC_RSE_Tate.png").unlink()
        (self.game/"Graphics/Characters/NPC_RSE_AquaGrunt.png").unlink()
        report=add_stage9_events(self.maps,self.game,
                                 self.sample_warps,self.sample_pickups)
        self.assertTrue(report["boss_graphics"]["Tate"]["placeholder"])
        self.assertTrue(report["aqua_placeholder"])
        self.assertFalse(report["native_gym_switch_puzzle_approved"])

    def test_source_coord_collision_refuses_to_overwrite(self):
        self.maps[82].attrs["@events"][1]=ruby(
            "RPG::Event",id=1,name=b"PREEXISTING",x=25,y=11,pages=[])
        with self.assertRaisesRegex(ValueError,"sobrepõem"):
            add_stage9_events(self.maps,self.game,
                              self.sample_warps,self.sample_pickups)


if __name__=="__main__":unittest.main()
