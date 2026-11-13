"""Tests for the isolated Hoenn source ZIP importer (no donor assets required)."""
from __future__ import annotations

import importlib.util
import json
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/regions/prepare_hoenn_source.py"
spec = importlib.util.spec_from_file_location("prepare_hoenn_source", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HoennSourcePreparationTests(unittest.TestCase):
    BASE = "The Pokémon World Project - Hoenn/"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = self.root / "hoenn.zip"

    def make_zip(self, extra=None):
        files = {
            self.BASE + "Data/Map001.rxdata": b"fictional fixture map",
            self.BASE + "Data/MapInfos.rxdata": b"fictional metadata",
            self.BASE + "Data/Tilesets.rxdata": b"fictional tilesets",
            self.BASE + "Data/Scripts.rxdata": b"SHOULD_NOT_EXTRACT",
            self.BASE + "Graphics/Tilesets/grass.png": b"fixture",
            self.BASE + "PBS/encounters.txt": b"fixture encounter",
            self.BASE + "Audio/BGM/route.mp3": b"fixture audio",
            self.BASE + "Game.exe": b"SHOULD_NOT_EXTRACT",
        }
        if extra:
            files.update(extra)
        with zipfile.ZipFile(self.archive, "w") as z:
            for name, value in files.items():
                z.writestr(name, value)

    def test_default_audit_is_read_only_and_selects_exact_sources(self):
        self.make_zip()
        result = module.inspect_zip(self.archive, root=self.root)
        self.assertEqual(result["source_maps"], 1)
        self.assertEqual(result["categories"]["maps"], 1)
        self.assertEqual(result["categories"]["map_dependencies"], 2)
        self.assertEqual(result["categories"]["graphics"], 1)
        self.assertEqual(result["categories"]["pbs_reference"], 1)
        self.assertNotIn("audio_reference", result["categories"])
        self.assertFalse(result["public_git_upload_allowed"])
        self.assertFalse((self.root / ".blue-work").exists())
        names = {row["path"] for row in result["files"]}
        self.assertNotIn("Data/Scripts.rxdata", names)
        self.assertNotIn("Game.exe", names)

    def test_extract_writes_only_into_isolated_workdir(self):
        self.make_zip()
        first = module.inspect_zip(self.archive, root=self.root, extract=True)
        stage = self.root / first["local_stage"]
        self.assertEqual(first["written"], 5)
        self.assertTrue((stage / "Data/Map001.rxdata").is_file())
        self.assertTrue((stage / "Graphics/Tilesets/grass.png").is_file())
        self.assertTrue((stage / "PBS/encounters.txt").is_file())
        self.assertTrue((stage / "inventory.json").is_file())
        self.assertFalse((stage / "Data/Scripts.rxdata").exists())
        self.assertFalse((stage / "Audio/BGM/route.mp3").exists())
        self.assertFalse((self.root / "game").exists())
        saved = json.loads((stage / "inventory.json").read_text(encoding="utf-8"))
        self.assertFalse(saved["public_git_upload_allowed"])
        second = module.inspect_zip(self.archive, root=self.root, extract=True)
        self.assertEqual(second["written"], 0)
        self.assertEqual(second["reused"], 5)

    def test_audio_needs_explicit_opt_in(self):
        self.make_zip()
        result = module.inspect_zip(self.archive, root=self.root,
                                    include_audio=True, extract=True)
        self.assertEqual(result["categories"]["audio_reference"], 1)
        self.assertTrue((self.root / result["local_stage"] /
                         "Audio/BGM/route.mp3").is_file())

    def test_modified_staged_resource_is_never_overwritten(self):
        self.make_zip()
        result = module.inspect_zip(self.archive, root=self.root, extract=True)
        (self.root / result["local_stage"] / "Data/Map001.rxdata").write_bytes(
            b"changed after staging")
        with self.assertRaisesRegex(ValueError, "Different file"):
            module.inspect_zip(self.archive, root=self.root, extract=True)

    def test_parent_traversal_is_rejected(self):
        self.make_zip({self.BASE + "../Data/Map002.rxdata": b"malicious"})
        with self.assertRaisesRegex(ValueError, "Unsafe ZIP"):
            module.inspect_zip(self.archive, root=self.root, extract=True)
        self.assertFalse((self.root / ".blue-work").exists())

    def test_duplicate_case_insensitive_names_are_rejected(self):
        self.make_zip({self.BASE + "Data/map001.rxdata": b"duplicate"})
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            module.inspect_zip(self.archive, root=self.root)

    def test_zip_symlink_is_rejected(self):
        self.make_zip()
        symlink = zipfile.ZipInfo(self.BASE + "Data/Map999.rxdata")
        symlink.create_system = 3
        symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(self.archive, "a") as z:
            z.writestr(symlink, "target")
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            module.inspect_zip(self.archive, root=self.root)

    def test_non_hoenn_areas_not_selected(self):
        self.make_zip({
            "The Pokémon World Project - Kanto/Data/Map555.rxdata": b"kanto",
            "The Pokémon World Project - Johto/Graphics/Tilesets/x.png": b"johto",
        })
        result = module.inspect_zip(self.archive, root=self.root)
        paths = {row["path"] for row in result["files"]}
        self.assertNotIn("Data/Map555.rxdata", paths)
        self.assertNotIn("Graphics/Tilesets/x.png", paths)


if __name__ == "__main__":
    unittest.main()
