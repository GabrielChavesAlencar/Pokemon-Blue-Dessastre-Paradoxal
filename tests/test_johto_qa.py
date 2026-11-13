"""Contract fixtures for the isolated QA transaction; no Game.exe execution."""
import json
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from build_johto_events import EVENT_CLASSES, event_page, ruby
from package_johto_offline12 import expected_events
from stage import serialize
from test_johto_offline12 import connections, mock_pbs
import johto_qa as qa


class JohtoQATests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.work = Path(tmp.name) / ".blue-work"
        self.work.mkdir()
        self.base = self.work.parent / "game"
        self.bundle = self.work / "johto-offline12-preview.zip"
        self.source_hash = json.loads((ROOT / "data/regions/johto-source.json").read_text(
            "utf-8"))["source"]["archive_sha256"]
        base_infos = {1: ruby("RPG::MapInfo", name=b"Decades", parent_id=0, order=1)}
        tiles = [None, ruby("RPG::Tileset", tileset_name=b"Inside", autotile_names=[])]
        original = {
            "Data/MapInfos.rxdata": serialize(base_infos),
            "Data/Tilesets.rxdata": serialize(tiles),
            "Data/System.rxdata": serialize(ruby("RPG::System", start_map_id=1, start_x=1, start_y=1),
                                            qa.SYSTEM_CLASSES),
            "Data/Scripts.rxdata": b"\x04\x08" + qa.dump([
                [1, qa.RubyString(b"Main"), qa.RubyString(zlib.compress(
                    b"def main\n    PluginManager.runPlugins\n    Compiler.main\nend\n"
                ))]
            ]),
            "Data/Map001.rxdata": b"base map",
            "Audio/a.txt": b"audio",
            "Fonts/f.txt": b"font",
            "Game.exe": b"fixture only",
            "Game.ini": b"[Game]\nTitle=Decades\n",
            "mkxp.json": b'{\n // comment\n "iconPath": "https://example.invalid/"\n}\n',
            "PBS/trainer_types.txt": b"[YOUNGSTER]\nName = Youngster\n",
            "PBS/map_connections.txt": b"# existing\n",
            f"{qa.STORY}/RegionStart.rb": b"# base\n",
            f"{qa.STORY}/meta.txt": b"Name = Blue Battle Presentation and Story\n",
            "Data/File A.rxdata": b"save sentinel",
            "Graphics/Tilesets/Inside.png": qa.PNG + b"fixture",
        }
        original.update({f"Graphics/Trainers/{v}.png": qa.PNG + v.encode()
                         for v in qa.TRAINER_SPRITES.values()})
        for name, blob in original.items():
            self.write_base(name, blob)
        self.original = original

        actions, warps = expected_events(ROOT)
        named = {value[0] for value in (*actions.values(), *warps.values())}
        by_symbol = dict(zip(sorted(named), range(650, 650 + len(named))))
        by_symbol.update(JOHTO_NEW_BARK_PLAYER_HOME_2F=674)
        for i in qa.MAP_IDS - set(by_symbol.values()):
            by_symbol[f"FILL_{i}"] = i
        maps = {i: ruby("RPG::Map", width=100, height=100, tileset_id=1, events={})
                for i in qa.MAP_IDS}
        for name, spec in sorted({**actions, **warps}.items()):
            symbol, (x, y), *args = spec
            if name in actions:
                page = event_page(script=args[0])
            else:
                target, (dx, dy), _ = args
                page = event_page(warp=(by_symbol[target], dx, dy), touch=True)
            events = maps[by_symbol[symbol]].attrs["@events"]
            event_id = len(events) + 1
            events[event_id] = ruby("RPG::Event", id=event_id, x=x, y=y,
                                    name=name.encode(), pages=[page])
        staged_infos = serialize({**base_infos, **{
            i: ruby("RPG::MapInfo", name=s.encode(), parent_id=0, order=i)
            for s, i in by_symbol.items()
        }})
        pbs, rival = mock_pbs(self.work.parent)
        pbs_blobs = {rel: ((pbs if (pbs / rel).is_file() else rival) / rel).read_bytes()
                     for rel in qa.PBS}
        self.members = {
            "stage/Data/MapInfos.rxdata": staged_infos,
            "stage/Data/Tilesets.rxdata": original["Data/Tilesets.rxdata"],
            "stage/" + qa.CONNECTIONS: connections(self.work.parent).read_bytes() + b"601,East,12,625,West,0\n602,East,6,627,West,0\n",
            **{f"stage/{rel}": blob for rel, blob in pbs_blobs.items()},
            **{f"stage/Data/Map{i:03}.rxdata": serialize(obj, EVENT_CLASSES)
               for i, obj in maps.items()},
            "review_only/Ruby/JohtoPilot.rb": b"raise 'must never be copied'",
            "stage/johto-stage.json": qa.json_bytes({
                "status": "BLUE_OFFLINE12_PREVIEW_ONLY_NOT_INSTALLABLE",
                "can_install": False, "not_playable": True, "source_archive_sha256": self.source_hash,
                "native_mapinfos_sha256": qa.hash_bytes(original["Data/MapInfos.rxdata"]),
                "native_tilesets_sha256": qa.hash_bytes(original["Data/Tilesets.rxdata"]),
                "maps": [{"symbol": s, "destination_id": i, "events_imported": 0} for s, i in by_symbol.items()],
            }),
            "johto-offline12-audit.json": qa.json_bytes({
                "milestone": "OFFLINE_12_OF_12", "can_install": False, "gameplay_playable": False,
                "source_archive_sha256": self.source_hash,
                "stage11_mapinfos_sha256": qa.hash_bytes(staged_infos),
                "stage11_tilesets_sha256": qa.hash_bytes(original["Data/Tilesets.rxdata"]),
                "pbs": {"sha256": {Path(rel).name: qa.hash_bytes(b) for rel, b in pbs_blobs.items()}},
                "packaged_map_sha256": {str(i): qa.hash_bytes(serialize(obj, EVENT_CLASSES))
                                        for i, obj in maps.items()},
            }),
        }
        self.write_bundle()

    def write_base(self, name, blob):
        path = self.base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)

    def write_bundle(self):
        with zipfile.ZipFile(self.bundle, "w") as z:
            for name, blob in self.members.items():
                z.writestr(name, blob)

    def plan(self):
        report = {}
        native, overlay = qa.plan(self.base, self.bundle, ROOT, report)
        return native, overlay, report

    def assert_base_unchanged(self):
        self.assertEqual({k: (self.base / k).read_bytes() for k in self.original}, self.original)

    def test_dry_run_then_stage_and_reversible_archive(self):
        native, overlay, report = self.plan()
        target = self.work / qa.TARGET
        self.assertFalse(target.exists())
        self.assertNotIn("Data/File A.rxdata", native)
        self.assertEqual(report["maps"], 82)
        self.assertEqual(report["events"], 32)
        qa.publish_copy(self.work, self.base, native, overlay, report)
        self.assertEqual((target / "Data/Map001.rxdata").read_bytes(), b"base map")
        self.assertEqual((target / "_johto_backup/Game.ini").read_bytes(), self.original["Game.ini"])
        self.assertFalse((target / "Data/File A.rxdata").exists())
        self.assertIn(b"module BlueJohtoPilot", (target / qa.PLUGIN / "Boot.rb").read_bytes())
        self.assertNotIn(b"must never be copied", (target / qa.PLUGIN / "Boot.rb").read_bytes())
        self.assertFalse((target / "Data/blue-johto-start.txt").exists())
        self.assertFalse((target / "Data/blue-johto-rival-ready.txt").exists())
        config = json.loads((target / "mkxp.json").read_bytes())
        self.assertTrue(config["dataPathApp"].startswith("Johto QA "))
        self.assertEqual(config["iconPath"], "https://example.invalid/")
        with self.assertRaisesRegex(ValueError, "use --rollback"):
            qa.publish_copy(self.work, self.base, native, overlay, report)
        archived = qa.rollback(self.work)
        self.assertFalse(target.exists())
        self.assertTrue((archived / qa.MARKER).is_file())
        self.assert_base_unchanged()

    def test_failed_copy_leaves_no_partial_target(self):
        native, overlay, report = self.plan()
        with patch.object(qa.shutil, "copy2", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(OSError, "disk full"):
                qa.publish_copy(self.work, self.base, native, overlay, report)
        self.assertFalse((self.work / qa.TARGET).exists())
        self.assertFalse(list(self.work.glob(".johto-qa-pending-*")))
        self.assert_base_unchanged()

    def test_collision_and_modified_pbs_are_rejected(self):
        self.write_base("Data/Map600.rxdata", b"another region")
        with self.assertRaisesRegex(ValueError, "MapIDs Johto colidem"):
            self.plan()
        (self.base / "Data/Map600.rxdata").unlink()
        self.members["stage/PBS/trainers_johto.txt"] += b"# tamper"
        self.write_bundle()
        with self.assertRaisesRegex(ValueError, "divergem dos hashes"):
            self.plan()

    def test_zip_traversal_is_rejected(self):
        self.members["stage/../Game.exe"] = b"must not extract"
        self.write_bundle()
        with self.assertRaisesRegex(ValueError, "ZIP insegura"):
            self.plan()


if __name__ == "__main__":
    unittest.main()
