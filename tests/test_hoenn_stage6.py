"""Stage 06 Route110/Mauville tests with synthetic graphics, not a Game.exe."""
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from build_johto_events import ruby
from hoenn_stage6 import (
    SOURCE_MAPS_STAGE6, OFFSET_BORDERS_STAGE6, WARP_PAIRS_STAGE6,
    CYCLE_TRANSFERS_STAGE6, LAND_ENCOUNTERS_STAGE6, TRAINERS_STAGE6,
    WATTSON_PBS, WATTSON_TEAM, WALLY_PBS, WALLY_TEAM,
    RIVAL_110_TEAMS, RIVAL_110_EVENT, RIVAL_110_TRIGGERS,
    WALLY_EVENT, WATTSON_EVENT, NPCS_STAGE6, PICKUPS_STAGE6,
    GYM_GATES_STAGE6, GYM_SWITCHES_STAGE6, MAUVILLE_FUTURE_GATES,
)
from pilot_hoenn import SOURCE_MAPS, WARP_PAIRS, add_stage6_events


class HoennStage6Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game = Path(self.temp.name)
        names = ({row[3] for row in NPCS_STAGE6} |
                 {row[5] for row in TRAINERS_STAGE6} |
                 {"NPC_RSE_Wally", "NPC_RSE_Wattson", "OBJ_RSE_Electric Gate H",
                  "OBJ_RSE_Electric Gate V", "Object_Ball", "trainer_LASS"})
        for name in names:
            path = self.game / "Graphics/Characters" / f"{name}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"\x89PNG\r\n\x1a\nsynthetic fixture")
        self.maps = {mid:ruby("RPG::Map",events={}) for mid in SOURCE_MAPS_STAGE6}

    def test_source_maps_edges_and_bicycle_gate_contracts(self):
        self.assertEqual(set(SOURCE_MAPS_STAGE6), {41,42,43,44,45,46,47,113,114,115})
        self.assertEqual(len(SOURCE_MAPS), 58)
        self.assertEqual(len(WARP_PAIRS), 68)
        self.assertEqual(len(WARP_PAIRS_STAGE6), 9)
        self.assertEqual(OFFSET_BORDERS_STAGE6, (
            (113, "South", 0, 32, "North", 0),
            (113, "North", 0, 41, "South", 0),
        ))
        self.assertEqual(len(CYCLE_TRANSFERS_STAGE6), 4)
        self.assertTrue(all(src in (114,115) and dest in (114,115)
                            for src, _, _, _, _, dest, _, _ in CYCLE_TRANSFERS_STAGE6))
        # A guarded bike route never becomes an unconditional warp.
        self.assertFalse(any(a[0] == 114 or b[0] == 114 for a, _, b, _ in WARP_PAIRS_STAGE6))
        self.assertNotIn(117, SOURCE_MAPS)  # Route 111
        self.assertNotIn(134, SOURCE_MAPS)  # Route 118

    def test_emerald_battles_and_normalized_encounters(self):
        self.assertEqual(sum(row[0] for row in LAND_ENCOUNTERS_STAGE6[113]),100)
        self.assertEqual({r[1] for r in LAND_ENCOUNTERS_STAGE6[113]},
                         {"ELECTRIKE","POOCHYENA","GULPIN","ODDISH",
                          "WINGULL","PLUSLE","MINUN"})
        self.assertEqual(WATTSON_PBS,("BLUE_HOENN_WATTSON","Wattson",647))
        self.assertEqual(WATTSON_TEAM,(
            ("VOLTORB",20),("ELECTRIKE",20),("MAGNETON",22),("MANECTRIC",24)))
        self.assertEqual(WALLY_PBS,("BLUE_HOENN_WALLY","Wally",641))
        self.assertEqual(WALLY_TEAM,(("RALTS",16),))
        self.assertEqual({team[-1][0] for _,team in RIVAL_110_TEAMS.values()},
                         {"COMBUSKEN","MARSHTOMP","GROVYLE"})
        self.assertEqual({ver for ver,_ in RIVAL_110_TEAMS.values()},{610,611,612})
        self.assertEqual(len(TRAINERS_STAGE6),19)
        self.assertEqual(len(PICKUPS_STAGE6),7)
        self.assertEqual(len(GYM_GATES_STAGE6),7)
        self.assertEqual(len(GYM_SWITCHES_STAGE6),4)

    def test_stage6_authored_events_and_persistent_gate_pages(self):
        report = add_stage6_events(self.maps,self.game,"trainer_LASS")
        self.assertEqual(report["new_maps"],10)
        self.assertEqual(report["trainers"],27)
        self.assertEqual(report["gym_switches"],4)
        self.assertEqual(report["gym_gates"],7)
        self.assertEqual(report["cycling_gate_events"],4)
        self.assertFalse(report["wattson_sprite_placeholder"])
        self.assertFalse(report["gate_graphic_placeholders"]["H"])
        self.assertFalse(report["gameplay_verified"])
        named = {}
        for mid, map_data in self.maps.items():
            coordinates = [(e.attrs["@x"],e.attrs["@y"])
                           for e in map_data.attrs["@events"].values()]
            self.assertEqual(len(coordinates),len(set(coordinates)),f"map overlap {mid}")
            for event in map_data.attrs["@events"].values():
                named[event.attrs["@name"].decode()] = (mid,event)
        self.assertEqual(named["HN6_Leader_Wattson"][0],47)
        self.assertEqual(named["HN6_Rival110"][0],113)
        self.assertIn("BlueHoennPilot.rydel_bikes",
                      named["HN6_NPC_45_4_7"][1].attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"][0].decode())
        for color in ("blue","pink"):
            gates=[ev for key,(_mid,ev) in named.items()
                   if key.startswith(f"HN6_Gate_{color}_")]
            self.assertTrue(gates)
            for gate in gates:
                pages=gate.attrs["@pages"]
                self.assertEqual(len(pages),2)
                self.assertTrue(pages[1].attrs["@condition"].attrs["@self_switch_valid"])
                self.assertTrue(pages[1].attrs["@through"])
        for row in GYM_SWITCHES_STAGE6:
            _,x,y=row
            ev=named[f"HN6_GymSwitch_{x}_{y}"][1]
            script=ev.attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"][0].decode()
            self.assertIn("BlueHoennPilot.wattson_switch",script)
            self.assertIn("[",script)
            self.assertEqual(ev.attrs["@pages"][0].attrs["@trigger"],1)
        for mid,x,y,_,_,_,_,_ in CYCLE_TRANSFERS_STAGE6:
            ev=named[f"HN6_CyclingGate_{mid}_{x}_{y}"][1]
            self.assertIn("BlueHoennPilot.cycling_gate",
                          ev.attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"][0].decode())
        for mid,x,y,key,item,visible in PICKUPS_STAGE6:
            ev=named[f"HN6_Item_{key}"][1]
            self.assertEqual(len(ev.attrs["@pages"]),2)
            self.assertTrue(ev.attrs["@pages"][1].attrs["@through"])

    def test_placeholder_graphics_are_not_native_gameplay_approval(self):
        for prefix in ("OBJ_RSE_Electric Gate H","OBJ_RSE_Electric Gate V","NPC_RSE_Wattson"):
            (self.game/"Graphics/Characters"/f"{prefix}.png").unlink()
        report=add_stage6_events(self.maps,self.game,"trainer_LASS")
        self.assertTrue(report["wattson_sprite_placeholder"])
        self.assertTrue(report["gate_graphic_placeholders"]["H"])
        self.assertTrue(report["gate_graphic_placeholders"]["V"])
        self.assertFalse(report["gameplay_verified"])

    def test_overlapping_rival_trigger_fails_closed(self):
        self.maps[113].attrs["@events"][1]=ruby(
            "RPG::Event",id=1,name=b"EXISTING",x=34,y=56,pages=[])
        with self.assertRaisesRegex(ValueError,"sobrepõem"):
            add_stage6_events(self.maps,self.game,"trainer_LASS")


if __name__=="__main__":
    unittest.main()
