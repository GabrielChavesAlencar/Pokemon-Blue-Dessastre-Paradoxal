"""Deterministic offline tests of a geometry-only Johto staging transaction."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    import audit_johto
    from plan_johto import plan
    from stage_johto import stage
    from verify_johto import inspect
    from stage import serialize
    from server.ruby_marshal import RubyObject, loads
finally:
    sys.path.pop(0)

PNG = b"\x89PNG\r\n\x1a\n" + b"synthetic-joh"


def dump(path: Path, value, extra=()):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(serialize(value, extra))


def fixture(root: Path):
    work = root / ".blue-work"
    source = work / "johto-source"
    game = root / "game"
    src_data = source / "Data"
    game_data = game / "Data"
    src_data.mkdir(parents=True)
    game_data.mkdir(parents=True)

    native = {599: RubyObject("RPG::MapInfo", {"@name": b"Native Decades", "@order": 1}),
              600: RubyObject("RPG::MapInfo", {"@name": b"Installed Kanto", "@order": 2})}
    dump(game_data / "MapInfos.rxdata", native)
    dump(game_data / "Tilesets.rxdata", [None, RubyObject("RPG::Tileset", {"@id": 1})])
    (game_data / "Map599.rxdata").write_bytes(b"old Decades map")
    (game_data / "Map600.rxdata").write_bytes(b"old Kanto map")
    (game_data / "System.rxdata").write_bytes(b"system kept native")
    dump(src_data / "MapInfos.rxdata", {
        3: RubyObject("RPG::MapInfo", {"@name": b"New Bark Town",
                                     "@parent_id": 0, "@order": 1})})
    tile = RubyObject("RPG::Tileset", {
        "@id": 1, "@name": b"Johto Exterior",
        "@tileset_name": b"JohtoTerrain",
        "@autotile_names": [b"JohtoAuto", b""],
        "@panorama_name": b"foreign_panorama",
        "@fog_name": b"foreign_fog",
        "@battleback_name": b"foreign_back"})
    dump(src_data / "Tilesets.rxdata", [None, tile])
    event = RubyObject("RPG::Event", {"@pages": []})
    bgm = RubyObject("RPG::AudioFile", {"@name": b"foreign-music"})
    bgs = RubyObject("RPG::AudioFile", {"@name": b"foreign-ambience"})
    level = RubyObject("RPG::Map", {
        "@width": 20, "@height": 15, "@tileset_id": 1,
        "@events": {1: event}, "@autoplay_bgm": True,
        "@autoplay_bgs": True, "@bgm": bgm, "@bgs": bgs})
    dump(src_data / "Map003.rxdata", level, ("RPG::Event",))
    for folder, name in [("Tilesets", "JohtoTerrain"), ("Autotiles", "JohtoAuto")]:
        path = source / "Graphics" / folder / (name + ".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(PNG)
    archive = work / "johto_pack.zip"
    archive.write_bytes(b"synthetic original Johto archive")
    manifest = {"schema": 1, "region": "JOHTO",
                "mapping_verified": True, "import_enabled": False,
                "source": {"name": "Synthetic Johto RMXP fixture",
                           "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest()},
                "maps": {"3": "JOHTO_NEW_BARK_TOWN"}}
    manifest_path = work / "johto-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    report = audit_johto.audit(source, manifest_path, game=game, archive=archive)
    audit_path = work / "audit.json"
    audit_path.write_text(json.dumps(report), encoding="utf-8")
    proposal = plan(manifest, report)
    plan_path = work / "plan.json"
    plan_path.write_text(json.dumps(proposal), encoding="utf-8")
    return dict(root=root, source=source, game=game, archive=archive,
                manifest_path=manifest_path, audit_path=audit_path,
                plan_path=plan_path, output=work / "johto-stage")


class JohtoStageTests(unittest.TestCase):
    def test_stage_strips_events_music_and_preserves_native_data_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            kwargs = fixture(Path(tmp))
            native = kwargs["game"] / "Data"
            protected = {name: (native / name).read_bytes() for name in
                         ("MapInfos.rxdata", "Tilesets.rxdata", "Map599.rxdata",
                          "Map600.rxdata", "System.rxdata")}
            original_source = (kwargs["source"] / "Data/Map003.rxdata").read_bytes()
            result = stage(**kwargs)
            self.assertEqual(result["status"], "GEOMETRY_PREVIEW_ONLY")
            self.assertEqual(result["maps"][0]["destination_id"], 601)
            self.assertFalse(result["can_install"])
            preview = kwargs["output"]
            map_data = loads((preview / "Data/Map601.rxdata").read_bytes())
            self.assertEqual(map_data.attrs["@events"], {})
            self.assertFalse(map_data.attrs["@autoplay_bgm"])
            self.assertFalse(map_data.attrs["@autoplay_bgs"])
            self.assertEqual(map_data.attrs["@bgm"].attrs["@name"], b"")
            self.assertEqual(map_data.attrs["@bgs"].attrs["@name"], b"")
            infos = loads((preview / "Data/MapInfos.rxdata").read_bytes())
            self.assertEqual(set(infos), {599, 600, 601})
            self.assertEqual(infos[601].attrs["@name"], b"[Johto preview] New Bark Town")
            tiles = loads((preview / "Data/Tilesets.rxdata").read_bytes())
            self.assertEqual(tiles[2].attrs["@tileset_name"], b"BLUE_JOHTO_PREVIEW_JohtoTerrain")
            self.assertTrue((preview / "Graphics/Tilesets/BLUE_JOHTO_PREVIEW_JohtoTerrain.png").exists())
            self.assertFalse((preview / "Game.exe").exists())
            self.assertFalse((preview / "Data/Scripts.rxdata").exists())
            proof = inspect(preview, kwargs["game"], root=kwargs["root"])
            self.assertEqual(proof["status"], "STRUCTURAL_PREVIEW_VALIDATED_NOT_PLAYABLE")
            self.assertEqual(proof["events_imported"], 0)
            self.assertEqual((kwargs["source"] / "Data/Map003.rxdata").read_bytes(), original_source)
            for name, before in protected.items():
                self.assertEqual((native / name).read_bytes(), before, name)
            with self.assertRaisesRegex(ValueError, "NEW output"):
                stage(**kwargs)

    def test_edited_source_is_blocked_before_writing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            kwargs = fixture(Path(tmp))
            (kwargs["source"] / "Data/Map003.rxdata").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "modified after audit"):
                stage(**kwargs)
            self.assertFalse(kwargs["output"].exists())

    def test_changed_native_tilesets_are_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            kwargs = fixture(Path(tmp))
            (kwargs["game"] / "Data/Tilesets.rxdata").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "changed since audit"):
                stage(**kwargs)
            self.assertFalse(kwargs["output"].exists())

    def test_not_verified_archive_or_unapproved_mapping_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            kwargs = fixture(Path(tmp))
            kwargs["archive"].write_bytes(b"other archive")
            with self.assertRaisesRegex(ValueError, "hash is not verified"):
                stage(**kwargs)
            self.assertFalse(kwargs["output"].exists())
        with tempfile.TemporaryDirectory() as tmp:
            kwargs = fixture(Path(tmp))
            m = json.loads(kwargs["manifest_path"].read_text())
            m["mapping_verified"] = False
            kwargs["manifest_path"].write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError, "mapping must be confirmed"):
                stage(**kwargs)

    def test_verifier_blocks_foreign_event_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            kwargs = fixture(Path(tmp))
            stage(**kwargs)
            target = kwargs["output"] / "Data/Map601.rxdata"
            obj = loads(target.read_bytes())
            obj.attrs["@events"] = {8: RubyObject("RPG::Event", {"@pages": []})}
            target.write_bytes(serialize(obj, ("RPG::Event",)))
            with self.assertRaisesRegex(ValueError, "Foreign events"):
                inspect(kwargs["output"], kwargs["game"], root=kwargs["root"])

    def test_verifier_rejects_modifications_to_native_kanto(self):
        with tempfile.TemporaryDirectory() as tmp:
            kwargs = fixture(Path(tmp))
            stage(**kwargs)
            (kwargs["game"] / "Data/MapInfos.rxdata").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "Native MapInfos changed"):
                inspect(kwargs["output"], kwargs["game"], root=kwargs["root"])

    def test_external_output_forbidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            kwargs = fixture(Path(tmp))
            kwargs["output"] = Path(tmp) / "game/Data/Johto"
            with self.assertRaisesRegex(ValueError, "inside .blue-work"):
                stage(**kwargs)


if __name__ == "__main__":
    unittest.main()
