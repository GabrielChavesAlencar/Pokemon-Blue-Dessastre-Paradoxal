"""Contrato offline: pacote v1 real auditado, tolerâncias estritamente comprovadas."""
from __future__ import annotations

import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    import audit_johto
    from plan_johto import plan
    from stage_johto import autotile_slot_used, stage
    from server.ruby_marshal import RubyData, RubyObject, loads
    from stage import serialize
    from test_johto_stage import fixture, dump
finally:
    sys.path.pop(0)


def prepare_missing_autotile(root: Path, *, use_slot: bool):
    args = fixture(root)
    source = args["source"] / "Data"
    tiles_path = source / "Tilesets.rxdata"
    tiles = loads(tiles_path.read_bytes())
    tiles[1].attrs["@autotile_names"] = [b"JohtoAuto", b"R49Water"]
    dump(tiles_path, tiles)

    path = source / "Map003.rxdata"
    world = loads(path.read_bytes())
    count = 20 * 15 * 3
    tiles_bytes = bytearray(b"\x00\x00" * count)
    if use_slot:
        struct.pack_into("<H", tiles_bytes, 0, 96)  # autotile slot 2 (96..143)
    world.attrs["@data"] = RubyData("Table", struct.pack(
        "<5I", 3, 20, 15, 3, count) + tiles_bytes)
    dump(path, world, ("RPG::Event",))
    m = json.loads(args["manifest_path"].read_text("utf-8"))
    a = audit_johto.audit(args["source"], args["manifest_path"],
                          game=args["game"], archive=args["archive"])
    args["audit_path"].write_text(json.dumps(a), encoding="utf-8")
    p = plan(m, a)
    args["plan_path"].write_text(json.dumps(p), encoding="utf-8")
    return args


class JohtoV1RealSourceContractTests(unittest.TestCase):
    def test_verified_v1_scope_and_external_map_edges_remain_non_installable(self):
        manifest = json.loads((ROOT / "data/regions/johto-source.json")
                              .read_text("utf-8"))
        graph = json.loads((ROOT / "data/regions/johto-v1-map-connections.json")
                           .read_text("utf-8"))
        self.assertEqual(set(map(int, manifest["maps"])), set(range(79, 153)))
        self.assertEqual(manifest["maps"]["79"], "JOHTO_NEW_BARK_TOWN")
        self.assertEqual(manifest["maps"]["104"], "JOHTO_ROUTE_29")
        self.assertEqual(manifest["maps"]["103"], "JOHTO_MT_SILVER_PEAK")
        self.assertEqual(len(set(manifest["maps"].values())), 74)
        self.assertEqual(manifest["source"]["archive_sha256"],
                         graph["source_archive_sha256"])
        self.assertFalse(manifest["import_enabled"])
        self.assertFalse(manifest["source"]["distribution_approved"])
        self.assertFalse(graph["can_install"])
        self.assertEqual(len(graph["connections"]), 42)
        for edge in graph["connections"]:
            self.assertIn(str(edge["from_id"]), manifest["maps"])
            self.assertIn(str(edge["to_id"]), manifest["maps"])
            self.assertIn(edge["from_edge"], ("North", "South", "East", "West"))
            self.assertIn(edge["to_edge"], ("North", "South", "East", "West"))
            self.assertGreaterEqual(edge["from_offset"], 0)
            self.assertGreaterEqual(edge["to_offset"], 0)
        self.assertTrue(any({c["from_id"], c["to_id"]} == {79, 104}
                            for c in graph["connections"]))
        self.assertFalse(any({c["from_id"], c["to_id"]} == {80, 104}
                             for c in graph["connections"]))

    def test_unused_missing_autotile_cleared_without_invented_graphics(self):
        with tempfile.TemporaryDirectory() as temp:
            args = prepare_missing_autotile(Path(temp), use_slot=False)
            report = stage(**args)
            self.assertEqual(report["status"], "GEOMETRY_PREVIEW_ONLY")
            self.assertFalse(report["can_install"])
            self.assertEqual(report["unused_missing_autotiles_cleared"], [{
                "tileset_id": 1, "slot": 2, "name": "R49Water",
                "action": "CLEARED_UNUSED_AUTOTILE_SLOT"
            }])
            dest = loads((args["output"] / "Data/Tilesets.rxdata").read_bytes())
            self.assertEqual(dest[2].attrs["@autotile_names"][1], b"")
            self.assertFalse((args["output"] /
                              "Graphics/Autotiles/BLUE_JOHTO_PREVIEW_R49Water.png").exists())

    def test_missing_used_autotile_blocks_and_preserves_game(self):
        with tempfile.TemporaryDirectory() as temp:
            args = prepare_missing_autotile(Path(temp), use_slot=True)
            with self.assertRaisesRegex(ValueError, "IS USED"):
                stage(**args)
            self.assertFalse(args["output"].exists())
            self.assertTrue((args["game"] / "Data/Map599.rxdata").exists())

    def test_invalid_table_never_proves_missing_asset_unused(self):
        area = RubyObject("RPG::Map", {
            "@width": 20, "@height": 15, "@data": RubyData("Table", b"bad")})
        with self.assertRaisesRegex(ValueError, "RMXP Table"):
            autotile_slot_used(area, 6)


if __name__ == "__main__":
    unittest.main()
