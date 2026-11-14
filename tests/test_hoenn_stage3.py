"""Hoenn stage-3 event/data contracts, without donor assets or the RPG engine."""
from __future__ import annotations

import tempfile
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from build_johto_events import ruby
from hoenn_stage3 import (
    SOURCE_MAPS_STAGE3, OFFSET_BORDERS, WARP_PAIRS_STAGE3,
    TRAINERS_STAGE3, LAND_ENCOUNTERS_STAGE3, PICKUPS_STAGE3,
    SIGNS_STAGE3, NPCS_STAGE3, FOREST_AQUA_TRIGGERS,
)
from pilot_hoenn import SOURCE_MAPS, WARP_PAIRS, add_stage3_events


class HoennStage3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.game = Path(self.tmp.name)
        sprites = {t[5] for t in TRAINERS_STAGE3} | {t[3] for t in NPCS_STAGE3}
        sprites.update({"NPC_DPP_PokeCenter_Nurse", "NPC_DPP_PokeMart_Man"})
        for name in sprites:
            path = self.game / "Graphics" / "Characters" / f"{name}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"synthetic test fixture; never imported into game")
        self.maps = {key: ruby("RPG::Map", events={}) for key in SOURCE_MAPS_STAGE3}

    def test_map_ids_and_connections_match_emerald_scope(self):
        self.assertEqual(set(SOURCE_MAPS_STAGE3), {16, 17, 18, 19, 20, 104, 105, 106, 156})
        self.assertEqual(len(SOURCE_MAPS), 18)
        self.assertEqual(len(OFFSET_BORDERS), 2)
        self.assertEqual(len(WARP_PAIRS_STAGE3), 11)
        self.assertEqual(len(WARP_PAIRS), 16)
        for a, _, b, _ in WARP_PAIRS_STAGE3:
            self.assertIn(a[0], SOURCE_MAPS)
            self.assertIn(b[0], SOURCE_MAPS)
        self.assertEqual(OFFSET_BORDERS, (
            (102, "West", 0, 16, "East", 10),
            (104, "East", 50, 16, "West", 0),
        ))

    def test_encounters_weights_and_source_location(self):
        self.assertEqual(set(LAND_ENCOUNTERS_STAGE3), {104, 156})
        for mid, table in LAND_ENCOUNTERS_STAGE3.items():
            self.assertEqual(sum(weight for weight, *_ in table), 100)
            self.assertTrue(all(1 <= low <= high <= 100 for _, _, low, high in table))
            self.assertEqual(len({species for _, species, _, _ in table}), len(table))

    def test_trainer_teams_and_woods_story_gate(self):
        self.assertEqual(len(TRAINERS_STAGE3), 9)
        names = [row[4] for row in TRAINERS_STAGE3]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(sum(row[-1] for row in TRAINERS_STAGE3), 1)
        self.assertEqual(FOREST_AQUA_TRIGGERS, ((156, 30, 24), (156, 31, 24)))
        self.assertEqual(len(PICKUPS_STAGE3), 20)
        self.assertEqual(len(SIGNS_STAGE3), 9)

    def test_stage3_templates_have_real_trigger_handlers_and_hide_items(self):
        report = add_stage3_events(self.maps, self.game)
        self.assertEqual(report, {
            "stage3_npcs": 6, "stage3_signs": 9,
            "stage3_pickups": 20, "stage3_trainers": 9, "stage3_aqua_triggers": 2,
        })
        records = {}
        for mid, source in self.maps.items():
            for record in source.attrs["@events"].values():
                name = record.attrs["@name"].decode()
                records[name] = (mid, record)
        self.assertIn("HN3_NPC_20_6_21", records)
        self.assertIn("HN3_NPC_106_9_5", records)
        self.assertIn("HN3_AquaGrunt_30", records)
        self.assertIn("HN3_AquaGrunt_31", records)
        for key in ("ROUTE104_POKE_BALL", "WOODS_GREAT_BALL"):
            mid, event = records["HN3_Item_" + key]
            pages = event.attrs["@pages"]
            self.assertEqual(len(pages), 2)
            self.assertTrue(pages[1].attrs["@condition"].attrs["@self_switch_valid"])
            self.assertEqual(pages[1].attrs["@condition"].attrs["@self_switch_ch"], b"A")
            script = pages[0].attrs["@list"][0].attrs["@parameters"][0].decode()
            self.assertIn("BlueHoennPilot.pickup", script)
        for x in (30, 31):
            self.assertEqual(records[f"HN3_AquaGrunt_{x}"][1].attrs["@pages"][0].attrs["@trigger"], 1)

    def test_missing_native_character_sprite_aborts_before_commit(self):
        missing = self.game / "Graphics/Characters/trainer_FISHERMAN.png"
        missing.unlink()
        with self.assertRaisesRegex(ValueError, "Sprite"):
            add_stage3_events(self.maps, self.game)

    def test_conflicting_event_coordinate_fails_closed(self):
        self.maps[16].attrs["@events"][1] = ruby(
            "RPG::Event", id=1, name=b"CONFLICT", x=17, y=16, pages=[])
        with self.assertRaisesRegex(ValueError, "sobrepõem"):
            add_stage3_events(self.maps, self.game)


if __name__ == "__main__":
    unittest.main()
