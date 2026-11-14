"""Stage10 isolated Hoenn contracts; NO native Game.exe acceptance."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from build_johto_events import ruby,command
from hoenn_stage10 import (
    SOURCE_MAPS_STAGE10,SURF_BORDERS_STAGE10,
    JUAN_EVENT,JUAN_PBS,JUAN_TEAM,ARCHIE_PBS,ARCHIE_TEAM,
    ELITE_EVENTS,ELITE_PBS,ELITE_TEAMS,CHAMPION_PBS,CHAMPION_TEAM,
    STAGE10_MAP_GRAPH_EDGES,
)
from pilot_hoenn import (
    SOURCE_MAPS,scan_stage9_source_events,add_stage10_events,
)


class Stage10ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game=Path(self.temp.name)
        for sprite in ("trainer_YOUNGSTER","trainer_LASS"):
            f=self.game/"Graphics/Characters"/(sprite+".png")
            f.parent.mkdir(parents=True,exist_ok=True)
            f.write_bytes(b"\x89PNG\r\n\x1a\nstage10 synthetic only")
        self.maps={mid:ruby("RPG::Map",width=100,height=90,events={})
                   for mid in SOURCE_MAPS_STAGE10}
        self.maps[144]=ruby("RPG::Map",width=100,height=90,events={})

    def _ev(self,name,x,y,*cmds):
        return ruby("RPG::Event",name=name.encode("utf-8"),x=x,y=y,
                    pages=[ruby("RPG::Event::Page",list=list(cmds))])

    def test_map_inventory_and_canonical_teams(self):
        self.assertEqual(len(SOURCE_MAPS_STAGE10),61)
        self.assertEqual(len(SOURCE_MAPS),199)
        self.assertEqual(len(SURF_BORDERS_STAGE10),16)
        self.assertEqual(JUAN_EVENT,(87,10,4))
        self.assertEqual(JUAN_PBS,("BLUE_HOENN_JUAN","Juan",1087))
        self.assertEqual(JUAN_TEAM[-1],("KINGDRA",46))
        self.assertEqual(ARCHIE_PBS,("BLUE_HOENN_ARCHIE","Archie",1026))
        self.assertEqual(ARCHIE_TEAM[-1],("SHARPEDO",43))
        self.assertEqual(len(ELITE_PBS),4)
        self.assertEqual(len(ELITE_EVENTS),4)
        self.assertEqual(tuple(x[1] for x in ELITE_PBS),
                         ("Sidney","Phoebe","Glacia","Drake"))
        self.assertEqual(tuple(len(x) for x in ELITE_TEAMS),(5,5,5,5))
        self.assertEqual(CHAMPION_PBS,("BLUE_HOENN_CHAMPION","Wallace",1098))
        self.assertEqual(CHAMPION_TEAM[-1],("MILOTIC",58))
        self.assertIn((98,99),STAGE10_MAP_GRAPH_EDGES)

    def test_read_only_warp_scanner_avoids_invented_destinations(self):
        originals={
            100:{1:self._ev("Sidney Entrance",7,4,
                            command(201,0,94,8,15,0))},
            92:{1:self._ev("Exit",8,11,
                           command(201,0,91,27,98,0))},
            250:{1:self._ev("Wally Entrance Battle Trigger",8,26,
                            command(201,0,94,8,15,0)),
                 2:self._ev("Item",14,12,
                            command(355,b"pbItemBall(:ULTRABALL)"))},
        }
        warps,items=scan_stage9_source_events(
            originals,self.maps,allowed_maps=SOURCE_MAPS_STAGE10,
            strict=False)
        self.assertEqual(warps,[(100,7,4,94,8,15,"Sidney Entrance")])
        self.assertEqual(items,[(250,14,12,"ULTRABALL",True)])

    def test_story_events_are_placed_without_overlap(self):
        warps=[(100,7,4,94,8,15,"Sidney Entrance"),
               (238,10,6,239,11,17,"Cave Entrance")]
        items=[(250,14,12,"ULTRABALL",True)]
        report=add_stage10_events(self.maps,self.game,warps,items)
        self.assertEqual(report["new_maps"],61)
        self.assertEqual(report["original_direct_warps"],2)
        self.assertEqual(report["original_audited_item_events"],1)
        self.assertFalse(report["native_gameplay_verified"])
        self.assertFalse(report["hall_of_fame_ui_native_verified"])
        names={}
        for mid,mp in self.maps.items():
            coords=set()
            for ev in mp.attrs["@events"].values():
                point=(ev.attrs["@x"],ev.attrs["@y"])
                self.assertNotIn(point,coords,mid)
                coords.add(point)
                names[ev.attrs["@name"].decode()]=mid
        for name,mid in (("HN10_Boss_Juan",87),
                         ("HN10_Boss_Archie",236),
                         ("HN10_Boss_Wallace",98),
                         ("HN10_Boss_Sidney",94),
                         ("HN10_Story_HallOfFame",99)):
            self.assertEqual(names[name],mid)

    def test_no_silent_overwrite_on_collision(self):
        self.maps[87].attrs["@events"][1]=ruby(
            "RPG::Event",id=1,name=b"Existing",x=10,y=4,pages=[])
        with self.assertRaisesRegex(ValueError,"sobrepõem"):
            add_stage10_events(self.maps,self.game,[],[])


if __name__=="__main__":
    unittest.main()
