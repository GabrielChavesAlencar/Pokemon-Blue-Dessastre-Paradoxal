"""Blue-Story Johto Map Studio auto-install beside EXE and game folder."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.windows.install_johto_editor import (
    FOLDER, MARKER, SOURCES, ENTRYPOINTS, digest, install
)


class BlueStoryEditorFolderTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.project = self.base / "Local AppData" / "PokemonBlueDessastreParadoxal"
        self.exe_dir = self.base / "Downloads" / "Blue Story"
        self.exe_dir.mkdir(parents=True)
        (self.exe_dir / "Blue-Story.exe").write_bytes(b"fake EXE no game content")
        (self.project / "scripts").mkdir(parents=True)
        (self.project / "scripts/install_game.py").write_text("print('game')", "utf-8")
        for relative in set(SOURCES.values()) | set(ENTRYPOINTS.values()):
            target = self.project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("genuine public source: " + relative, encoding="utf-8")

    def test_installs_auto_updated_folder_beside_blue_story_and_managed_game(self):
        first = install(self.project, self.exe_dir)
        self.assertTrue(first["ready"])
        self.assertEqual(len(first["installed"]), 2)
        self.assertFalse(first["warnings"])
        for location in (self.project, self.exe_dir):
            studio = location / FOLDER
            self.assertTrue(studio.is_dir())
            for relative in SOURCES:
                self.assertEqual((studio / relative).read_bytes(),
                                 (self.project / SOURCES[relative]).read_bytes())
            self.assertIn(str(self.project.resolve()),
                          (studio / "EDITAR_MAPAS_JOHTO.bat").read_text("utf-8"))
            self.assertIn("CONECTAR_GITHUB_EDITOR_JOHTO.bat",
                          (studio / "CONECTAR_GITHUB_EDITOR_JOHTO.bat").read_text("utf-8"))
            self.assertIn("Nao edite manualmente", (studio / "LEIA-ME.txt").read_text("utf-8"))
            marker = json.loads((studio / MARKER).read_text("utf-8"))
            self.assertEqual(marker["owner"], "BLUE_STORY_JOHTO_MAP_STUDIO")
            self.assertEqual(marker["files"]["editor/johto-map-editor.html"],
                             digest((self.project / "web/johto-map-editor.html").read_bytes()))

        second = install(self.project, self.exe_dir)
        self.assertTrue(second["ready"])
        self.assertEqual(len(second["installed"]), 2)
        self.assertFalse(second["warnings"])
        self.assertEqual((self.exe_dir / "Blue-Story.exe").read_bytes(),
                         b"fake EXE no game content")

    def test_editor_update_refreshes_existing_files_without_changing_user_game(self):
        install(self.project, self.exe_dir)
        modified = self.project / "web/johto-map-editor.html"
        modified.write_text("NEW MAIN VERSION", "utf-8")
        game = self.project / "game/Saves"
        game.mkdir(parents=True)
        (game / "File.rxdata").write_bytes(b"MY SAVE")
        target = self.exe_dir / FOLDER / "editor/johto-map-editor.html"
        target.write_bytes(b"LOCAL USER EDIT OF MIRROR")
        output = install(self.project, self.exe_dir)
        self.assertTrue(output["ready"])
        self.assertEqual(target.read_bytes(), b"NEW MAIN VERSION")
        self.assertEqual((game / "File.rxdata").read_bytes(), b"MY SAVE")
        backups = list((self.project / ".blue-backups").glob(
            "johto-editor-shortcut-*/editor/johto-map-editor.html"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), b"LOCAL USER EDIT OF MIRROR")

    def test_preexisting_unmanaged_exe_folder_is_not_overwritten(self):
        folder = self.exe_dir / FOLDER
        folder.mkdir()
        (folder / "projeto.txt").write_text("leave my files alone", "utf-8")
        result = install(self.project, self.exe_dir)
        self.assertTrue(result["ready"])
        self.assertEqual(len(result["installed"]), 1)
        self.assertEqual(len(result["warnings"]), 1)
        self.assertEqual((folder / "projeto.txt").read_text("utf-8"),
                         "leave my files alone")
        self.assertFalse((folder / MARKER).exists())
        self.assertTrue((self.project / FOLDER / "EDITAR_MAPAS_JOHTO.bat").exists())

    def test_reject_symlink_editor_folder_and_never_touch_game(self):
        location = self.exe_dir / FOLDER
        location.symlink_to(self.project, target_is_directory=True)
        result = install(self.project, self.exe_dir)
        self.assertTrue(result["ready"])
        self.assertEqual(len(result["warnings"]), 1)
        self.assertIn("symlink", result["warnings"][0]["reason"])
        self.assertFalse((self.project / "game").exists())

    def test_no_reinstall_if_python_assets_not_present(self):
        (self.project / "web/johto-map-editor.html").unlink()
        with self.assertRaisesRegex(ValueError, "não encontrado"):
            install(self.project, self.exe_dir)
        self.assertFalse((self.exe_dir / FOLDER).exists())


if __name__ == "__main__":
    unittest.main()
