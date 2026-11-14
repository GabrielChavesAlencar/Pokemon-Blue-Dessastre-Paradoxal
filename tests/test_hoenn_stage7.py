"""Stage 7 contracts: Fallarbor/Magma/Flannery without native Game.exe.

Uses synthetic Ruby objects and placeholder files, not proprietary donor
maps or claims of real gameplay approval.
"""
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from build_johto_events import ruby
from hoenn_stage7 import (
    SOURCE_MAPS_STAGE7, OFFSET_BORDERS_STAGE7, WARP_PAIRS_STAGE7,
    CABLE_POINTS_STAGE7, LAND_ENCOUNTERS_STAGE7, CAVE_ENCOUNTERS_STAGE7,
    TRAINERS_STAGE7, FLANNERY_PBS, FLANNERY_TEAM, MAXIE_PBS, MAXIE_TEAM,
    TABITHA_PBS, TABITHA_TEAM, MAGMA_GRUNTS_STAGE7, MAGMA_GRUNT_EVENTS,
    METEOR_FALLS_CUTSCENE, ROUTE112_MAGMA_BLOCKERS,
    NPCS_STAGE7, FUTURE_GATES_STAGE7, PICKUPS_STAGE7,
    GYM_STEAM_PAIRS_STAGE7,
)
from pilot_hoenn import SOURCE_MAPS, WARP_PAIRS, add_stage7_events


class HoennStage7Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game=Path(self.temp.name)
        art={row[3] for row in NPCS_STAGE7}|{row[5] for row in TRAINERS_STAGE7}
        art.update(("trainer_YOUNGSTER","trainer_LASS","NPC_RSE_MagmaGrunt",
                    "NPC_RSE_Tabitha","NPC_RSE_Maxie","NPC_RSE_Flannery"))
        for sprite in art:
            f=self.game/"Graphics/Characters"/(sprite+".png")
            f.parent.mkdir(parents=True,exist_ok=True)
            f.write_bytes(b"\x89PNG\r\n\x1a\nsynthetic fixture only")
        self.maps={mid:ruby("RPG::Map",events={}) for mid in SOURCE_MAPS_STAGE7}

    def test_27_new_maps_and_conditional_cable(self):
        self.assertEqual(len(SOURCE_MAPS_STAGE7),27)
        self.assertEqual(len(SOURCE_MAPS),110)
        self.assertEqual(len(WARP_PAIRS_STAGE7),23)
        self.assertEqual(len(WARP_PAIRS),130)
        self.assertEqual(len(OFFSET_BORDERS_STAGE7),7)
        self.assertEqual(CABLE_POINTS_STAGE7,((122,8,9),(179,8,9)))
        self.assertFalse(any(a[0]==122 and b[0]==179 or
                             a[0]==179 and b[0]==122
                             for a,_,b,_ in WARP_PAIRS))
        # Donor wrong-exit Bug: Fossil House126 must return to Route114.
        self.assertIn(((125,29,5),(125,29,6),(126,6,10),(126,6,9)),
                      WARP_PAIRS_STAGE7)
        self.assertNotIn(127,SOURCE_MAPS)  # deep Fossil tunnel pending
        self.assertNotIn(181,SOURCE_MAPS)  # Magma hideout pending
        self.assertNotIn(193,SOURCE_MAPS)  # deep Meteor Falls pending

    def test_emerald_teams_and_encounters(self):
        for groups in (LAND_ENCOUNTERS_STAGE7,CAVE_ENCOUNTERS_STAGE7):
            for mid,table in groups.items():
                self.assertEqual(sum(x[0] for x in table),100,mid)
                self.assertTrue(all(low>0 and high>=low
                                    for _,_,low,high in table))
        self.assertEqual(set(CAVE_ENCOUNTERS_STAGE7),{177,191,192})
        self.assertEqual(set(LAND_ENCOUNTERS_STAGE7),{117,121,123,125,180})
        self.assertEqual(FLANNERY_PBS,("BLUE_HOENN_FLANNERY","Flannery",763))
        self.assertEqual(FLANNERY_TEAM,(
            ("NUMEL",24),("SLUGMA",24),("CAMERUPT",26),("TORKOAL",29)))
        self.assertEqual(MAXIE_TEAM,(
            ("MIGHTYENA",24),("ZUBAT",24),("CAMERUPT",25)))
        self.assertEqual(TABITHA_TEAM,(
            ("NUMEL",18),("POOCHYENA",20),("NUMEL",22),("ZUBAT",22)))
        self.assertEqual([x[2] for x in MAGMA_GRUNTS_STAGE7],[780,781])
        self.assertEqual(len(TRAINERS_STAGE7),23)

    def test_event_inventory_and_steam_no_collision(self):
        report=add_stage7_events(self.maps,self.game)
        self.assertEqual(report["new_maps"],27)
        self.assertEqual(report["trainer_events"],28)
        self.assertEqual(report["cutscene_events"],1)
        self.assertEqual(report["pickups"],18)
        self.assertEqual(report["steam_vent_pairs"],11)
        self.assertFalse(report["magma_graphic_placeholder"])
        self.assertFalse(report["gameplay_verified"])
        events={}
        for mid,obj in self.maps.items():
            positions=[(e.attrs["@x"],e.attrs["@y"])
                       for e in obj.attrs["@events"].values()]
            self.assertEqual(len(positions),len(set(positions)),
                             f"Collision on donor map {mid}")
            for e in obj.attrs["@events"].values():
                events[e.attrs["@name"].decode()]=(mid,e)
        for name,mid,handler in (
            ("HN7_Boss_Flannery",63,"BlueHoennPilot.flannery"),
            ("HN7_Boss_Tabitha",178,"BlueHoennPilot.tabitha"),
            ("HN7_Boss_Maxie",178,"BlueHoennPilot.maxie"),
            ("HN7_MeteoriteMachine",178,"BlueHoennPilot.meteorite_machine"),
            ("HN7_MeteorFalls_Ambush",191,"BlueHoennPilot.meteor_falls_ambush"),
        ):
            self.assertEqual(events[name][0],mid)
            script=events[name][1].attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"][0].decode()
            self.assertEqual(script,handler)
        self.assertEqual(len([x for x in events if x.startswith("HN7_SteamFall")]),11)
        self.assertEqual(len([x for x in events if x.startswith("HN7_SteamLaunch")]),11)
        for name,(mid,event) in events.items():
            if name.startswith(("HN7_CableBlocker","HN7_Item_")):
                self.assertEqual(len(event.attrs["@pages"]),2)
                self.assertTrue(event.attrs["@pages"][1].attrs["@through"])
                self.assertTrue(event.attrs["@pages"][1].attrs["@condition"].attrs["@self_switch_valid"])
        for source,landing in GYM_STEAM_PAIRS_STAGE7:
            self.assertNotEqual(source,landing)

    def test_placeholder_art_is_not_approved(self):
        (self.game/"Graphics/Characters/NPC_RSE_MagmaGrunt.png").unlink()
        report=add_stage7_events(self.maps,self.game)
        self.assertTrue(report["magma_graphic_placeholder"])
        self.assertFalse(report["gameplay_verified"])

    def test_overlap_preflight_fails_closed(self):
        self.maps[178].attrs["@events"][1]=ruby(
            "RPG::Event",id=1,name=b"CONFLICT",x=14,y=7,pages=[])
        with self.assertRaisesRegex(ValueError,"sobrepõem"):
            add_stage7_events(self.maps,self.game)


if __name__=="__main__":
    unittest.main()
