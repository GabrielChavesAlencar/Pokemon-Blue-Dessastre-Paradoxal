"""Stage8 isolated Hoenn pilot data/events. No Windows Game.exe run is implied."""
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from build_johto_events import ruby
from hoenn_stage8 import (
    SOURCE_MAPS_STAGE8,OFFSET_BORDERS_STAGE8,WARP_PAIRS_STAGE8,
    LAND_ENCOUNTERS_STAGE8,NORMAN_EVENT,NORMAN_PBS,NORMAN_TEAM,
    WINONA_EVENT,WINONA_PBS,WINONA_TEAM,SHELLY_PBS,SHELLY_TEAM,
    AQUA_INSTITUTE,RIVAL_119_TEAMS,RIVAL_LILYCOVE_TEAMS,
    TRAINERS_STAGE8,NORMAN_GYM_DOORS,PICKUPS_STAGE8,
    NPCS_STAGE8,WEATHER_REWARD_EVENT,
)
from pilot_hoenn import SOURCE_MAPS,WARP_PAIRS,add_stage8_events


class HoennStage8Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game=Path(self.temp.name)
        sprites=({row[3] for row in NPCS_STAGE8} |
                 {row[5] for row in TRAINERS_STAGE8} |
                 {"trainer_YOUNGSTER","trainer_LASS","trainer_FISHERMAN",
                  "Object_Ball","NPC_RSE_Norman","NPC_RSE_Winona",
                  "NPC_RSE_Shelly","NPC_RSE_AquaGrunt","NPC_RSE_Steven",
                  "NPC_RSE_Kecleon"})
        for sprite in sprites:
            f=self.game/"Graphics/Characters"/f"{sprite}.png"
            f.parent.mkdir(parents=True,exist_ok=True)
            f.write_bytes(b"\x89PNG\r\n\x1a\nsynthetic test png")
        ids=set(SOURCE_MAPS_STAGE8)|{20,157}
        self.maps={mid:ruby("RPG::Map",events={}) for mid in ids}

    def test_map_and_source_connections(self):
        self.assertEqual(len(SOURCE_MAPS_STAGE8),25)
        self.assertEqual(len(SOURCE_MAPS),110)
        self.assertEqual(len(WARP_PAIRS_STAGE8),39)
        self.assertEqual(len(WARP_PAIRS),130)
        self.assertEqual(len(OFFSET_BORDERS_STAGE8),8)
        self.assertIn((135,"South",0,134,"North",40),OFFSET_BORDERS_STAGE8)
        self.assertIn((139,"East",0,69,"West",10),OFFSET_BORDERS_STAGE8)
        self.assertNotIn((134,"East",0,64,"West",140),OFFSET_BORDERS_STAGE8)
        self.assertIn(((48,8,1),(48,8,2),(157,34,21),(157,34,20)),WARP_PAIRS_STAGE8)
        self.assertNotIn(140,SOURCE_MAPS)  # Safari entrance is not enabled.
        self.assertNotIn(215,SOURCE_MAPS)  # Aqua Hideout is future stage.

    def test_emerald_encounters_and_boss_teams(self):
        self.assertEqual(set(LAND_ENCOUNTERS_STAGE8),{132,134,135,138,139})
        for mid,table in LAND_ENCOUNTERS_STAGE8.items():
            self.assertEqual(sum(row[0] for row in table),100,mid)
            self.assertTrue(all(low>0 and high>=low
                                for _,_,low,high in table))
        self.assertEqual(NORMAN_PBS,("BLUE_HOENN_NORMAN","Norman",820))
        self.assertEqual(NORMAN_TEAM,(("SPINDA",27),("VIGOROTH",27),
                                      ("LINOONE",29),("SLAKING",31)))
        self.assertEqual(WINONA_PBS,("BLUE_HOENN_WINONA","Winona",868))
        self.assertEqual(WINONA_TEAM,(("SWABLU",29),("TROPIUS",29),
                                      ("PELIPPER",30),("SKARMORY",31),("ALTARIA",33)))
        self.assertEqual(SHELLY_PBS,("BLUE_HOENN_SHELLY","Shelly",837))
        self.assertEqual(SHELLY_TEAM,(("CARVANHA",28),("MIGHTYENA",28)))
        self.assertEqual([x[3] for x in AQUA_INSTITUTE],[851,852,853,854])
        self.assertEqual(len(TRAINERS_STAGE8),29)
        self.assertEqual({version for version,_ in RIVAL_119_TEAMS.values()}, {819,820,821})
        self.assertEqual({version for version,_ in RIVAL_LILYCOVE_TEAMS.values()}, {822,823,824})
        self.assertEqual(len(PICKUPS_STAGE8),39)
        self.assertEqual(len(NORMAN_GYM_DOORS),24)

    def test_event_templates_nonoverlap_bosses_and_pickups(self):
        report=add_stage8_events(self.maps,self.game,"trainer_LASS")
        self.assertEqual(report["new_maps"],25)
        self.assertEqual(report["ordinary_trainer_events"],29)
        self.assertEqual(report["aqua_institute_battles"],5)
        self.assertEqual(report["rival_pbs_variants"],12)
        self.assertEqual(report["gym_norman_room_warps"],24)
        self.assertEqual(report["pickup_events"],39)
        self.assertFalse(report["boss_graphics"]["Norman"]["placeholder"])
        self.assertFalse(report["boss_graphics"]["Winona"]["placeholder"])
        self.assertFalse(report["kecleon_placeholder"])
        self.assertFalse(report["gameplay_verified"])
        by_name={}
        for mid,mp in self.maps.items():
            events=list(mp.attrs["@events"].values())
            pts=[(e.attrs["@x"],e.attrs["@y"]) for e in events]
            self.assertEqual(len(pts),len(set(pts)),f"Collision map {mid}")
            for ev in events:
                by_name[ev.attrs["@name"].decode()]=(mid,ev)
        for name,mid in (
            ("HN8_Boss_Norman",20),("HN8_Boss_Winona",68),
            ("HN8_Boss_Shelly",137),("HN8_rival_119",135),
            ("HN8_rival_lilycove",69),("HN8_WeatherScientist",137),
            ("HN8_StevenScope",138)):
            self.assertEqual(by_name[name][0],mid)
        self.assertEqual(len([k for k in by_name if k.startswith("HN8_NormanDoor")]),24)
        for key,(mid,ev) in by_name.items():
            if key.startswith(("HN8_Item_","HN8_Kecleon_")):
                pages=ev.attrs["@pages"]
                self.assertEqual(len(pages),2,key)
                self.assertTrue(pages[1].attrs["@through"])
                self.assertTrue(pages[1].attrs["@condition"].attrs["@self_switch_valid"])

    def test_placeholder_art_remains_unapproved(self):
        (self.game/"Graphics/Characters/NPC_RSE_Winona.png").unlink()
        (self.game/"Graphics/Characters/NPC_RSE_Kecleon.png").unlink()
        report=add_stage8_events(self.maps,self.game,"trainer_LASS")
        self.assertTrue(report["boss_graphics"]["Winona"]["placeholder"])
        self.assertTrue(report["kecleon_placeholder"])
        self.assertFalse(report["native_surf_fly_verified"])
        self.assertFalse(report["gameplay_verified"])

    def test_overlap_preflight_fails_closed(self):
        self.maps[137].attrs["@events"][1]=ruby(
            "RPG::Event",id=1,name=b"EXISTING",x=34,y=8,pages=[])
        with self.assertRaisesRegex(ValueError,"sobrepõem"):
            add_stage8_events(self.maps,self.game,"trainer_LASS")


if __name__=="__main__":
    unittest.main()
