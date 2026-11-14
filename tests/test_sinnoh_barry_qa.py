"""Barry QA preflight: verifies COPY only, with no runtime/gameplay claims."""
from __future__ import annotations

import hashlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from build_sinnoh_barry_pbs import READY_MARKER, publish
from preflight_sinnoh_barry_qa import preflight
from test_sinnoh_barry_pbs import fixture


class SinnohBarryQaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.game = fixture(self.root)
        (self.game / "Game.exe").write_bytes(b"native game fixture")
        self.draft = self.root / ".blue-work/sinnoh-draft"
        publish(self.game, self.draft, root=self.root)
        self.qa = self.root / ".blue-work/sinnoh-qa"
        self.qa.mkdir()
        (self.qa / "Game.exe").write_bytes(b"private QA fixture")
        (self.qa / "PBS").mkdir()
        for file in (self.draft / "PBS").iterdir():
            shutil.copyfile(file, self.qa / "PBS" / file.name)
        self.graphic = self.qa / "Graphics/Trainers/BLUE_SINNOH_RIVAL.png"
        self.graphic.parent.mkdir(parents=True)
        self.graphic.write_bytes(b"synthetic test image")

    def test_qa_copy_three_pbs_valid_but_never_auto_approved(self):
        before = {p.relative_to(self.root).as_posix():
                  hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.root.rglob("*") if p.is_file()}
        result = preflight(self.qa, self.draft, self.game, root=self.root)
        self.assertEqual(result["mode"], "ISOLATED_QA_STATIC_PREFLIGHT")
        self.assertTrue(result["qa_copy_not_main_game"])
        self.assertTrue(result["graphic_candidate_file_exists"])
        self.assertFalse(result["graphic_engine_verified"])
        self.assertFalse(result["pbs_compiled_in_essentials"])
        self.assertFalse(result["trainer_versions_loaded_in_engine"])
        self.assertFalse(result["ready_marker_allowed"])
        self.assertFalse(result["can_install_into_main_game"])
        after = {p.relative_to(self.root).as_posix():
                 hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_missing_graphic_is_review_candidate_not_engine_proof(self):
        self.graphic.unlink()
        result = preflight(self.qa, self.draft, self.game, root=self.root)
        self.assertFalse(result["graphic_candidate_file_exists"])
        self.assertFalse(result["graphic_engine_verified"])

    def test_rejects_absent_or_modified_pbs_in_qa_copy(self):
        team = self.qa / "PBS/trainers_sinnoh_barry.txt"
        team.write_text(team.read_text("utf-8") + "\n# edit", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "adulterada"):
            preflight(self.qa, self.draft, self.game, root=self.root)
        team.unlink()
        with self.assertRaises(ValueError):
            preflight(self.qa, self.draft, self.game, root=self.root)

    def test_rejects_marker_on_either_side(self):
        (self.qa / READY_MARKER).parent.mkdir()
        (self.qa / READY_MARKER).write_text("premature", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Marcador"):
            preflight(self.qa, self.draft, self.game, root=self.root)
        (self.qa / READY_MARKER).unlink()
        (self.game / READY_MARKER).parent.mkdir(exist_ok=True)
        (self.game / READY_MARKER).write_text("premature", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Marcador"):
            preflight(self.qa, self.draft, self.game, root=self.root)

    def test_rejects_main_game_as_qa_or_an_outside_folder(self):
        with self.assertRaisesRegex(ValueError, "cópia distinta"):
            preflight(self.game, self.draft, self.game, root=self.root)
        with self.assertRaisesRegex(ValueError, "cópia distinta"):
            preflight(self.root, self.draft, self.game, root=self.root)

    def test_legacy_map_ids_reported_but_not_auto_remapped(self):
        (self.qa / "Data").mkdir()
        (self.qa / "Data/Map800.rxdata").write_bytes(b"synthetic")
        (self.qa / "Data/Map805.rxdata").write_bytes(b"synthetic")
        result = preflight(self.qa, self.draft, self.game, root=self.root)
        self.assertEqual(result["legacy_map_800_805_physically_present_in_qa"],
                         [800, 805])
        self.assertTrue(result["potential_johto_collision_if_merged"])
        self.assertFalse(result["can_install_into_main_game"])

    def test_rejects_symlinked_qa_escape(self):
        symlink = self.root / ".blue-work/escape"
        try:
            symlink.symlink_to(self.game, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Cannot create test symlinks")
        with self.assertRaisesRegex(ValueError, "cópia distinta"):
            preflight(symlink, self.draft, self.game, root=self.root)


if __name__ == "__main__":
    unittest.main()
