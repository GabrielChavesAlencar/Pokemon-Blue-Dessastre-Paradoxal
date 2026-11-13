"""Checks Hoenn source provenance and native ID collision detection without imports."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_hoenn_baseline import PILOT, audit
from build_johto_events import ruby
from stage import serialize


class HoennBaselineTests(unittest.TestCase):
    def test_pinned_bytes_and_native_collisions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            donor, native = root / "source", root / "native"
            donor.mkdir()
            native.mkdir()
            paths = {
                "MapInfos.rxdata": serialize({i: ruby("RPG::MapInfo", name=f"Area {i}".encode())
                                             for i in PILOT}),
                "Tilesets.rxdata": serialize([
                    None, ruby("RPG::Tileset", tileset_name=b"Sample", autotile_names=[])
                ]),
                **{f"Map{i:03}.rxdata": serialize(
                    ruby("RPG::Map", width=20, height=20, tileset_id=1, events={})
                ) for i in PILOT},
            }
            tree = []
            for name, content in paths.items():
                (donor / name).write_bytes(content)
                tree.append({"path": f"Data/{name}", "type": "blob", "sha": hashlib.sha1(
                    f"blob {len(content)}\0".encode("ascii") + content
                ).hexdigest()})
            (native / "MapInfos.rxdata").write_bytes(serialize({7: ruby("RPG::MapInfo")}))
            (native / "Tilesets.rxdata").write_bytes(paths["Tilesets.rxdata"])
            (native / "Map008.rxdata").write_bytes(paths["Map008.rxdata"])
            inventory = root / "tree.json"
            inventory.write_text(json.dumps({
                "revision": "a" * 40, "truncated": False, "tree": tree
            }), encoding="utf-8")
            report = audit(inventory, donor, native)
            self.assertEqual(report["unmapped_collisions"], 2)
            self.assertFalse(report["private_archive_audited"])
            self.assertFalse(report["installation_verified"])
            self.assertEqual(report["pilot"][0]["graphics_missing_from_tree"],
                             ["Graphics/Tilesets/Sample.png"])
            (donor / "Map007.rxdata").write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "revisão pública"):
                audit(inventory, donor, native)


if __name__ == "__main__":
    unittest.main()
