"""ZIP-only safety tests for local Johto source intake; no actual game assets."""
from __future__ import annotations

import hashlib
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    from prepare_johto_source import prepare
    from audit_johto import project_data
    from stage import serialize
    from server.ruby_marshal import RubyObject
finally:
    sys.path.pop(0)


def small_rmxp():
    return serialize(RubyObject("RPG::Map", {"@width": 10, "@height": 8,
                                           "@tileset_id": 1, "@events": {}}))


def source_archive(root: Path, *, extra=None) -> tuple[Path, Path]:
    work = root / ".blue-work/johto-source"
    work.mkdir(parents=True)
    archive = work / "original.zip"
    target = work / "project"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
        prefix = "Map Pack v3/"
        package.writestr(prefix + "Data/MapInfos.rxdata", serialize({
            1: RubyObject("RPG::MapInfo", {"@name": b"New Bark Town"})}))
        package.writestr(prefix + "Data/Tilesets.rxdata",
                         serialize([None, RubyObject("RPG::Tileset", {})]))
        package.writestr(prefix + "Data/Map001.rxdata", small_rmxp())
        package.writestr(prefix + "Graphics/Tilesets/Johto.png",
                         b"\x89PNG\r\n\x1a\n" + b"fictional test image")
        package.writestr(prefix + "Scripts/unsafe.rb", b"system('not executed')")
        package.writestr(prefix + "Game.exe", b"do not extract")
        if extra is not None:
            package.writestr(*extra)
    return archive, target


class JohtoSourcePrepareTests(unittest.TestCase):
    def test_only_safe_data_and_png_extracted_in_ignored_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, target = source_archive(root)
            old = archive.read_bytes()
            output = prepare(archive, target, root=root)
            self.assertEqual(output["content"]["maps"], 1)
            self.assertEqual(output["content"]["files"], 4)
            self.assertEqual(output["source_archive_sha256"], hashlib.sha256(old).hexdigest())
            self.assertEqual(output["game_files_changed"], 0)
            self.assertEqual(project_data(target.parent), target / "Data")
            self.assertTrue((target / "Data/Map001.rxdata").is_file())
            self.assertTrue((target / "Graphics/Tilesets/Johto.png").is_file())
            self.assertFalse((target / "Scripts/unsafe.rb").exists())
            self.assertFalse((target / "Game.exe").exists())
            self.assertFalse((root / "game").exists())
            self.assertFalse(output["rights_verified"])
            self.assertFalse(output["maps_audited"])
            self.assertEqual(archive.read_bytes(), old)
            with self.assertRaisesRegex(ValueError, "NEW output"):
                prepare(archive, target, root=root)

    def test_refuses_archive_traversal_even_if_member_would_not_be_selected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, target = source_archive(root, extra=("../../escape.rb", b"evil"))
            with self.assertRaisesRegex(ValueError, "Unsafe path"):
                prepare(archive, target, root=root)
            self.assertFalse(target.exists())
            self.assertFalse((root / "escape.rb").exists())

    def test_refuses_symlink_archive_member(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, target = source_archive(root)
            with zipfile.ZipFile(archive, "a") as zipout:
                info = zipfile.ZipInfo("Map Pack v3/scripts/link")
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                zipout.writestr(info, "../Data/MapInfos.rxdata")
            with self.assertRaisesRegex(ValueError, "Symlinks"):
                prepare(archive, target, root=root)
            self.assertFalse(target.exists())

    def test_refuses_writing_to_game_or_rereading_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, target = source_archive(root)
            with self.assertRaisesRegex(ValueError, "inside .blue-work"):
                prepare(archive, root / "game/Data", root=root)
            target.mkdir(parents=True)
            (target / "original.txt").write_text("important", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "NEW output"):
                prepare(archive, target, root=root)
            self.assertEqual((target / "original.txt").read_text(), "important")

    def test_rejects_non_zip_sources_without_extracting_anything(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, target = source_archive(root)
            wrong = archive.with_suffix(".rar")
            wrong.write_bytes(b"not a zip")
            with self.assertRaisesRegex(ValueError, "Only ZIP"):
                prepare(wrong, target, root=root)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
