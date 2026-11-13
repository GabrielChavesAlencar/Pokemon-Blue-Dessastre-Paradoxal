"""Testes offline com mapas RMXP artificiais: sem assets HGSS ou executáveis."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    import audit_johto
    import inventory_johto
    from stage import serialize
    from server.ruby_marshal import RubyObject
finally:
    sys.path.pop(0)


def obj(class_name, **props):
    return RubyObject(class_name, {"@" + key: value for key, value in props.items()})


def make_source(base: Path, *, bad_warp=False):
    src = base / ".blue-work/johto-source"
    data = src / "Data"
    data.mkdir(parents=True)
    infos = {
        1: obj("RPG::MapInfo", name=b"New Bark Town", parent_id=0),
        2: obj("RPG::MapInfo", name=b"Route 29", parent_id=0),
    }
    data.joinpath("MapInfos.rxdata").write_bytes(serialize(infos))
    data.joinpath("Tilesets.rxdata").write_bytes(
        serialize([None, obj("RPG::Tileset")]))
    target = 9 if bad_warp else 2
    commands = [
        obj("RPG::EventCommand", code=101, parameters=[b"teste: nao exportar dialogo"]),
        obj("RPG::EventCommand", code=126, parameters=[1, 0, 0, 1]),
        obj("RPG::EventCommand", code=301, parameters=[1, 1, 0]),
        obj("RPG::EventCommand", code=201, parameters=[0, target, 3, 4, 2, 0]),
        obj("RPG::EventCommand", code=355, parameters=[b"Kernel.system('NAO_EXECUTAR')"]),
    ]
    pages = [obj("RPG::Event::Page", trigger=0, list=commands)]
    events = {7: obj("RPG::Event", name=b"Elm", x=4, y=5, pages=pages)}
    extras = ("RPG::Event", "RPG::Event::Page", "RPG::EventCommand")
    data.joinpath("Map001.rxdata").write_bytes(serialize(obj(
        "RPG::Map", width=20, height=18, tileset_id=1, events=events), extras))
    data.joinpath("Map002.rxdata").write_bytes(serialize(obj(
        "RPG::Map", width=20, height=18, tileset_id=1, events={}), extras))
    return src


class JohtoInventoryTests(unittest.TestCase):
    def make_report(self, source):
        return audit_johto.audit(
            source, ROOT / "data/regions/johto-source.json")

    def test_area_scope_is_explicit_and_not_marked_complete(self):
        scope = inventory_johto.area_scope(
            ROOT / "data/regions/johto-area-scope.json")
        self.assertGreaterEqual(len(scope), 70)
        self.assertEqual(len({a["key"] for a in scope}), len(scope))
        self.assertIn("JOHTO_NEW_BARK_TOWN", {a["key"] for a in scope})
        self.assertIn("JOHTO_MT_SILVER", {a["key"] for a in scope})
        self.assertIn("JOHTO_BLACKTHORN_GYM", {a["key"] for a in scope})

    def test_reads_pages_items_trainers_warps_without_executing_scripts(self):
        with tempfile.TemporaryDirectory() as temp:
            source = make_source(Path(temp))
            file = source / "Data/Map001.rxdata"
            before = hashlib.sha256(file.read_bytes()).hexdigest()
            report = self.make_report(source)
            areas = inventory_johto.area_scope(inventory_johto.DEFAULT_AREAS)
            found = inventory_johto.create_inventory(source, report, areas)
            self.assertFalse(found["can_install"])
            self.assertFalse(found["source_hash_verified"])
            self.assertEqual(found["status"], "SOURCE_INVENTORY_NOT_PLAYABLE")
            self.assertEqual(found["totals"]["maps"], 2)
            self.assertEqual(found["totals"]["events"], 1)
            self.assertEqual(found["totals"]["event_pages"], 1)
            self.assertEqual(found["totals"]["item_change_commands"], 1)
            self.assertEqual(found["totals"]["native_battle_commands"], 1)
            self.assertEqual(found["totals"]["untrusted_script_commands"], 1)
            event = found["maps"][0]["source_events"][0]
            self.assertEqual((event["source_event_id"], event["x"], event["y"]),
                             (7, 4, 5))
            self.assertEqual(event["pages"][0]["static_or_dynamic_warps"][0]["map_id"], 2)
            self.assertTrue(event["pages"][0]["requires_manual_reconstruction"])
            serialized = json.dumps(found)
            self.assertNotIn("NAO_EXECUTAR", serialized)
            self.assertNotIn("teste: nao exportar", serialized)
            self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(), before)
            new_bark = next(a for a in found["areas"]
                            if a["key"] == "JOHTO_NEW_BARK_TOWN")
            self.assertEqual(new_bark["candidate_source_ids"], [1])
            self.assertFalse(new_bark["npcs_verified"])
            self.assertFalse(new_bark["gameplay_verified"])
            self.assertTrue(all(a["status"] == "NEEDS_MANUAL_HGSS_RECONSTRUCTION"
                                for a in found["areas"]))

    def test_reports_dangling_transfer_without_validating_gameplay(self):
        with tempfile.TemporaryDirectory() as temp:
            source = make_source(Path(temp), bad_warp=True)
            found = inventory_johto.create_inventory(
                source, self.make_report(source),
                inventory_johto.area_scope(inventory_johto.DEFAULT_AREAS))
            self.assertIn("TRANSFER_TARGET_MISSING", found["maps"][0]["warnings"])
            self.assertFalse(found["can_install"])

    def test_source_change_after_audit_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            source = make_source(Path(temp))
            report = self.make_report(source)
            (source / "Data/Map001.rxdata").write_bytes(b"alterado")
            with self.assertRaisesRegex(ValueError, "alterado"):
                inventory_johto.create_inventory(
                    source, report, inventory_johto.area_scope(
                        inventory_johto.DEFAULT_AREAS))

    def test_audit_can_never_authorize_installation(self):
        with tempfile.TemporaryDirectory() as temp:
            source = make_source(Path(temp))
            report = self.make_report(source)
            report["can_install"] = True
            with self.assertRaisesRegex(ValueError, "read-only"):
                inventory_johto.create_inventory(
                    source, report, inventory_johto.area_scope(
                        inventory_johto.DEFAULT_AREAS))

    def test_invalid_area_catalog_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "areas.json"
            path.write_text(json.dumps({"schema": 1, "region": "JOHTO",
                "areas": [
                    {"key": "JOHTO_SAME", "aliases": ["Town"], "required": True},
                    {"key": "JOHTO_SAME", "aliases": ["Town"], "required": True},
                ]}), "utf-8")
            with self.assertRaisesRegex(ValueError, "duplicada"):
                inventory_johto.area_scope(path)

    def test_report_writer_rejects_game_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            source = make_source(Path(temp))
            found = inventory_johto.create_inventory(
                source, self.make_report(source),
                inventory_johto.area_scope(inventory_johto.DEFAULT_AREAS))
            with patch.object(audit_johto, "ROOT", Path(temp)):
                out = Path(temp) / ".blue-work/inventory.json"
                audit_johto.write_report(out, found)
                audit_johto.write_report(out, found)
                self.assertEqual(json.loads(out.read_text("utf-8"))["totals"]["maps"], 2)
                with self.assertRaisesRegex(ValueError, "inside .blue-work"):
                    audit_johto.write_report(Path(temp) / "game/Data/Map001.rxdata", found)


    def test_windows_helper_stays_read_only(self):
        batch = (ROOT / "JOHTO_PREPARAR_MAPAS.bat").read_text("utf-8").lower()
        self.assertIn("inventory_johto.py", batch)
        self.assertIn("audit_johto.py", batch)
        self.assertIn("prepare_johto_source.py", batch)
        self.assertIn("original.zip", batch)
        self.assertNotIn("--apply", batch)
        self.assertNotIn("install_johto.py", batch)
        self.assertNotIn("copy /", batch)

if __name__ == "__main__":
    unittest.main()
