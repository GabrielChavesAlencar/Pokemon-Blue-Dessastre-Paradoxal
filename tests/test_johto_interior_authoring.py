"""Validação sintética de interiores Johto: geometria, tilesets, IDs e rollback."""
import copy
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    from build_johto_interiors import build, parse_layouts
    from audit_johto import checksum, read_map_data
    from stage import serialize
    from verify_johto import inspect
    from server.ruby_marshal import RubyData, RubyObject
    from test_johto_pilot_assembly import make_prepared, rmxp
finally:
    sys.path.pop(0)

REQUIRED = (
    "JOHTO_NEW_BARK_PLAYER_HOME_2F",
    "JOHTO_NEW_BARK_PLAYER_HOME_1F",
    "JOHTO_NEW_BARK_ELM_LAB",
)


def table(width=12, height=10):
    count = width * height * 3
    # RPG Maker Table Marshal includes the dimension tuple and 16-bit tiles.
    return RubyData("Table", struct.pack("<5I", 3, width, height, 3, count) +
                    b"\x00\x00" * count)


def make_data(root):
    game, preview, unused_spec = make_prepared(root)
    data = game / "Data"
    graphic = game / "Graphics/Tilesets"
    auto = game / "Graphics/Autotiles"
    graphic.mkdir()
    auto.mkdir()
    for path in (graphic / "NativeRoom.png", auto / "NativeFloor.png"):
        path.write_bytes(b"\x89PNG\r\n\x1a\nsynthetic-graphics")
    tiles = read_map_data(data / "Tilesets.rxdata")
    tiles[1].attrs.update({
        "@name": b"Native room sheet",
        "@tileset_name": b"NativeRoom",
        "@autotile_names": [b"NativeFloor"],
    })
    (data / "Tilesets.rxdata").write_bytes(serialize(tiles))
    native_infos = read_map_data(data / "MapInfos.rxdata")
    for idx in range(1, 4):
        room = rmxp("RPG::Map", width=12, height=10, tileset_id=1,
                    data=table(), events={
                        9: rmxp("RPG::Event", name=b"UNTRUSTED_NATIVE_HANDLER", pages=[])
                    }, autoplay_bgm=True, autoplay_bgs=True,
                    bgm=rmxp("RPG::AudioFile", name=b"NATIVE_BGM"),
                    bgs=rmxp("RPG::AudioFile", name=b"NATIVE_BGS"),
                    encounter_list=[b"not copied"], encounter_step=5)
        (data / f"Map{idx:03d}.rxdata").write_bytes(
            serialize(room, ("RPG::Event",)))
        native_infos[idx] = rmxp("RPG::MapInfo",
                                 name=f"Native room {idx}".encode(),
                                 parent_id=0, order=idx)
    (data / "MapInfos.rxdata").write_bytes(serialize(native_infos))

    stage_file = preview / "johto-stage.json"
    stage = json.loads(stage_file.read_text("utf-8"))
    stage["maps"] = [row for row in stage["maps"]
                     if row["symbol"] in {"JOHTO_NEW_BARK_TOWN", "JOHTO_ROUTE_29"}]
    for mid in (601, 602, 604):
        (preview / "Data" / f"Map{mid:03d}.rxdata").unlink()
    stage_infos = read_map_data(preview / "Data/MapInfos.rxdata")
    stage_infos = {k: v for k, v in stage_infos.items() if k in (603, 605)}
    stage_infos.update(native_infos)
    (preview / "Data/MapInfos.rxdata").write_bytes(serialize(stage_infos))
    staged_tiles = read_map_data(preview / "Data/Tilesets.rxdata")
    staged_tiles[:len(tiles)] = tiles
    (preview / "Data/Tilesets.rxdata").write_bytes(serialize(staged_tiles))
    stage["native_mapinfos_sha256"] = checksum(data / "MapInfos.rxdata")
    stage["native_tilesets_sha256"] = checksum(data / "Tilesets.rxdata")
    stage_file.write_text(json.dumps(stage), encoding="utf-8")

    template = parse_layouts(ROOT / "data/regions/johto-interior-templates.json")
    for idx, row in enumerate(template["interiors"], 1):
        row["native_map_id"] = idx
        row["native_map_sha256"] = checksum(data / f"Map{idx:03d}.rxdata")
        row["destination_id"] = 605 + idx
        row["native_template_reviewed"] = True
        row["room_geometry_reviewed"] = True
    return game, preview, template


class JohtoInteriorsTests(unittest.TestCase):
    def test_default_templates_have_no_fictitious_ids_or_reviews(self):
        spec = parse_layouts(ROOT / "data/regions/johto-interior-templates.json")
        self.assertEqual({row["symbol"] for row in spec["interiors"]}, set(REQUIRED))
        for row in spec["interiors"]:
            self.assertIsNone(row["native_map_id"])
            self.assertIsNone(row["destination_id"])
            self.assertIsNone(row["native_map_sha256"])
            self.assertFalse(row["native_template_reviewed"])
            self.assertFalse(row["room_geometry_reviewed"])

    def test_creates_three_preview_rooms_and_revalidates_geometry(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game, preview, spec = make_data(root)
            preexisting = {str(p.relative_to(game)): checksum(p)
                           for p in game.rglob("*") if p.is_file()}
            old_preview = {str(p.relative_to(preview)): checksum(p)
                           for p in preview.rglob("*") if p.is_file()}
            output = root / ".blue-work/johto-interior-preview"
            report = build(preview, game, output, spec, root=root)
            self.assertEqual(report["native_interior_geometry_drafts"], 3)
            self.assertEqual(report["status"], "GEOMETRY_PREVIEW_ONLY")
            self.assertFalse(report["can_install"])
            self.assertTrue(report["not_playable"])
            ids = {row["symbol"]: row["destination_id"] for row in report["maps"]}
            self.assertEqual([ids[key] for key in REQUIRED], [606, 607, 608])
            self.assertEqual(inspect(output, game, root=root)["maps"], 5)
            for idx in range(1, 4):
                new_map = read_map_data(output / "Data" / f"Map{605+idx:03d}.rxdata")
                self.assertEqual(new_map.attrs["@events"], {})
                self.assertFalse(new_map.attrs["@autoplay_bgm"])
                self.assertFalse(new_map.attrs["@autoplay_bgs"])
                self.assertEqual(new_map.attrs["@bgm"].attrs["@name"], b"")
                self.assertEqual(new_map.attrs["@bgs"].attrs["@name"], b"")
                self.assertEqual(new_map.attrs["@encounter_list"], [])
                self.assertEqual(new_map.attrs["@data"].data, table().data)
            merged = read_map_data(output / "Data/MapInfos.rxdata")
            self.assertEqual(merged[606].attrs["@parent_id"], 607)
            self.assertEqual(merged[607].attrs["@parent_id"], 603)
            self.assertEqual(merged[608].attrs["@parent_id"], 603)
            stage_tiles = read_map_data(output / "Data/Tilesets.rxdata")
            self.assertEqual(len(stage_tiles), 5)
            self.assertEqual(stage_tiles[4].attrs["@tileset_name"], b"NativeRoom")
            self.assertEqual(preexisting, {str(p.relative_to(game)): checksum(p)
                                           for p in game.rglob("*") if p.is_file()})
            self.assertEqual(old_preview, {str(p.relative_to(preview)): checksum(p)
                                           for p in preview.rglob("*") if p.is_file()})
            self.assertFalse((game / "Data/Map606.rxdata").exists())
            with self.assertRaisesRegex(ValueError, "NOVA"):
                build(preview, game, output, spec, root=root)

    def test_not_approved_template_wrong_sha_or_collision_blocks_build(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game, preview, spec = make_data(root)
            out = root / ".blue-work/interiors"
            bad = copy.deepcopy(spec)
            bad["interiors"][0]["room_geometry_reviewed"] = False
            with self.assertRaisesRegex(ValueError, "não foi inspecionado"):
                build(preview, game, out, bad, root=root)
            bad = copy.deepcopy(spec)
            bad["interiors"][0]["native_map_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "pinado"):
                build(preview, game, out, bad, root=root)
            bad = copy.deepcopy(spec)
            bad["interiors"][1]["destination_id"] = 603
            with self.assertRaisesRegex(ValueError, "sem MapID"):
                build(preview, game, out, bad, root=root)
            self.assertFalse(out.exists())

    def test_corrupt_tile_table_or_missing_native_tileset_asset_blocks_build(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game, preview, spec = make_data(root)
            out = root / ".blue-work/interiors"
            src = game / "Data/Map001.rxdata"
            original = src.read_bytes()
            room = read_map_data(src)
            room.attrs["@data"] = RubyData("Table", b"\x00" * 20)
            src.write_bytes(serialize(room, ("RPG::Event",)))
            spec["interiors"][0]["native_map_sha256"] = checksum(src)
            with self.assertRaisesRegex(ValueError, "Tabela de tiles"):
                build(preview, game, out, spec, root=root)
            src.write_bytes(original)
            spec["interiors"][0]["native_map_sha256"] = checksum(src)
            (game / "Graphics/Tilesets/NativeRoom.png").unlink()
            with self.assertRaisesRegex(ValueError, "ausente"):
                build(preview, game, out, spec, root=root)
            self.assertFalse(out.exists())

    def test_no_write_to_main_or_preview_and_block_foreign_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game, preview, spec = make_data(root)
            with self.assertRaisesRegex(ValueError, "NOVA"):
                build(preview, game, game / "Data/new-maps", spec, root=root)
            with self.assertRaisesRegex(ValueError, "NOVA"):
                build(preview, game, preview / "Data/nested", spec, root=root)
            self.assertFalse((game / "Data/new-maps").exists())


if __name__ == "__main__":
    unittest.main()
