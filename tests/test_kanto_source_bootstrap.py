"""Offline regression for the hash-pinned source bootstrap used by Blue-Story.exe."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    import ensure_source
finally:
    sys.path.remove(str(ROOT / "scripts/regions"))


class KantoSourceBootstrapTests(unittest.TestCase):
    def test_selected_members_allow_only_pinned_frlg_game_assets(self):
        names = ["Essentials FRLG/" + p for p in ensure_source.REQUIRED]
        names.extend(f"Essentials FRLG/Graphics/Characters/person_{i:03}.png" for i in range(200))
        names += [
            "Essentials FRLG/Game.exe",  # forbidden
            "Essentials FRLG/Scripts/backdoor.rb",  # forbidden
            "unrelated/Game.exe",  # forbidden
        ]
        selected = ensure_source.selected_members("\n".join(names))
        self.assertEqual(len(selected), len(ensure_source.REQUIRED) + 200)
        self.assertNotIn("Essentials FRLG/Game.exe", selected)
        self.assertNotIn("Essentials FRLG/Scripts/backdoor.rb", selected)
        self.assertTrue(all(item.startswith("Essentials FRLG/") for item in selected))

    def test_missing_required_map_is_rejected(self):
        names = ["Essentials FRLG/" + p for p in ensure_source.REQUIRED if p != "Data/Map042.rxdata"]
        names.extend(f"Essentials FRLG/Graphics/Characters/person_{i:03}.png" for i in range(200))
        with self.assertRaisesRegex(RuntimeError, "Map042"):
            ensure_source.selected_members("\n".join(names))

    def test_archive_path_traversal_is_rejected(self):
        names = ["Essentials FRLG/" + p for p in ensure_source.REQUIRED]
        names.extend(f"Essentials FRLG/Graphics/Characters/person_{i:03}.png" for i in range(200))
        names.append("Essentials FRLG/../../game/Game.rxdata")
        with self.assertRaisesRegex(RuntimeError, "inseguro"):
            ensure_source.selected_members("\n".join(names))

    def test_existing_archive_with_wrong_hash_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "FRLG.rar"
            archive.write_bytes(b"private local archive")
            with self.assertRaisesRegex(RuntimeError, "hash diferente"):
                ensure_source.download_pinned(
                    "https://example.invalid/FRLG.rar", archive, "0" * 64)
            self.assertEqual(archive.read_bytes(), b"private local archive")

    def test_source_already_prepared_does_not_download_or_modify(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / ensure_source.RELATIVE_SOURCE
            folder.mkdir(parents=True)
            for file in ensure_source.REQUIRED:
                path = folder / file
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"original source data")
            with patch.object(ensure_source, "download_pinned",
                              side_effect=AssertionError("must not download")):
                self.assertEqual(ensure_source.prepare(root), folder)
            self.assertEqual((folder / "Data/Map042.rxdata").read_bytes(),
                             b"original source data")

    def test_bat_uses_portable_python_from_story_installer(self):
        bat = (ROOT / "KANTO_JOGAR_EXPERIMENTAL.bat").read_text("utf-8")
        self.assertIn("tools\\python-*", bat)
        self.assertIn('"%PYTHON_EXE%" %PYTHON_EXTRA% -X utf8', bat)
        self.assertIn("scripts\\regions\\ensure_source.py", bat)
        self.assertLess(bat.index("ensure_source.py"), bat.index("gui_diagnostics.py"))


if __name__ == "__main__":
    unittest.main()
