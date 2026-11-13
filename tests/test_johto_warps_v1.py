"""Offline New Bark warp tests; no native executable, source maps or private assets."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from build_johto_warps_v1 import Grid, compile_plan, event_page, ruby, EVENT_CLASSES
from stage import serialize
from server.ruby_marshal import loads

IDS = {
    "JOHTO_NEW_BARK_PLAYER_HOME_2F": 674,
    "JOHTO_NEW_BARK_PLAYER_HOME_1F": 675,
    "JOHTO_NEW_BARK_ELM_LAB": 676,
    "JOHTO_NEW_BARK_TOWN": 600,
    "JOHTO_ROUTE_29": 625,
}
PBS = "600,West,13,625,East,0\n"


def fresh():
    spec = json.loads((ROOT / "data/regions/johto-stage07-warps.json").read_text(encoding="utf-8"))
    grid = Grid(40, 50, (0,) * (40 * 50 * 3), (0,))
    return spec, {sym: grid for sym in IDS if sym != "JOHTO_ROUTE_29"}


class NewBarkWarpOfflineTests(unittest.TestCase):
    def test_six_warps_reciprocal_and_separate_from_pbs(self):
        spec, grids = fresh()
        report = compile_plan(spec, IDS, grids, PBS)
        self.assertEqual(len(report["warps"]), 6)
        self.assertEqual(report["edge_connection_pbs"], PBS.strip())
        self.assertEqual(len(report["static_reachable_tiles"]), 4)
        self.assertFalse(report["can_install"])
        self.assertFalse(report["tested_in_game"])
        self.assertFalse(report["gameplay_playable"])

    def test_static_blocked_trigger_is_rejected(self):
        spec, grids = fresh()
        a = IDS["JOHTO_NEW_BARK_PLAYER_HOME_2F"]
        self.assertEqual(a, 674)
        cells = [0] * (40 * 50 * 3)
        cells[9 + 40 * 8] = 1
        grids["JOHTO_NEW_BARK_PLAYER_HOME_2F"] = Grid(40, 50, tuple(cells), (0, 15))
        with self.assertRaisesRegex(ValueError, "passabilidade"):
            compile_plan(spec, IDS, grids, PBS)

    def test_two_warps_on_same_cell_rejected(self):
        spec, grids = fresh()
        w = next(w for w in spec["warps"] if w["key"] == "JH_HOME1F_TO_TOWN")
        w.update({"x": 11, "y": 9})
        with self.assertRaisesRegex(ValueError, "mesma célula"):
            compile_plan(spec, IDS, grids, PBS)

    def test_missing_inverse_mapping_rejected(self):
        spec, grids = fresh()
        spec["warps"][0]["reverse_key"] = "JH_TOWN_TO_HOME1F"
        with self.assertRaisesRegex(ValueError, "sem retorno"):
            compile_plan(spec, IDS, grids, PBS)

    def test_spawn_on_warp_event_rejected(self):
        spec, grids = fresh()
        spec["spawn"].update({"x": 9, "y": 8})
        with self.assertRaisesRegex(ValueError, "Spawn sobre"):
            compile_plan(spec, IDS, grids, PBS)

    def test_arrival_on_another_warp_loop_rejected(self):
        spec, grids = fresh()
        w = next(w for w in spec["warps"] if w["key"] == "JH_HOME1F_TO_2F")
        w["arrival_x"], w["arrival_y"] = 9, 8
        with self.assertRaisesRegex(ValueError, "loop imediato"):
            compile_plan(spec, IDS, grids, PBS)

    def test_absent_border_pbs_rejected(self):
        spec, grids = fresh()
        with self.assertRaisesRegex(ValueError, "faltando"):
            compile_plan(spec, IDS, grids, "601,North,21,626,South,0\n")

    def test_border_pbs_duplicate_rejected(self):
        spec, grids = fresh()
        with self.assertRaisesRegex(ValueError, "duplicada"):
            compile_plan(spec, IDS, grids, PBS + PBS)

    def test_coords_outside_map_rejected(self):
        spec, grids = fresh()
        spec["warps"][0]["x"] = 80
        with self.assertRaisesRegex(ValueError, "passabilidade"):
            compile_plan(spec, IDS, grids, PBS)

    def test_falsely_verified_in_engine_rejected(self):
        spec, grids = fresh()
        spec["warps"][2]["verified_in_engine"] = True
        with self.assertRaisesRegex(ValueError, "marcado como testado"):
            compile_plan(spec, IDS, grids, PBS)

    def test_static_wall_separating_anchors_rejected(self):
        spec, grids = fresh()
        cells = [0] * (40 * 50 * 3)
        for y in range(50):
            cells[10 + 40*y] = 1
        grids["JOHTO_NEW_BARK_TOWN"] = Grid(40, 50, tuple(cells), (0, 15))
        with self.assertRaisesRegex(ValueError, "não estão conectadas"):
            compile_plan(spec, IDS, grids, PBS)

    def test_rmxp_warp_has_only_code_201_after_serialization(self):
        page = event_page(warp=(675, 11, 8), touch=True)
        obj = ruby("RPG::Event", id=1, name=b"JH_HOME2F_TO_1F",
                   x=9, y=8, pages=[page])
        rebuilt = loads(serialize(obj, EVENT_CLASSES))
        commands = rebuilt.attrs["@pages"][0].attrs["@list"]
        self.assertEqual([op.attrs["@code"] for op in commands], [201, 0])
        self.assertEqual(commands[0].attrs["@parameters"][:4], [0, 675, 11, 8])


if __name__ == "__main__":
    unittest.main()
