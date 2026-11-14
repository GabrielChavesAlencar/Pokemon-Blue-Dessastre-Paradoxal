"""QA copy preflight refuses shared saves, tampered PBS, mixed starters."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from build_sinnoh_barry_pbs import PBS_TYPE, PBS_TRAINERS, READY_MARKER, publish
from inspect_sinnoh_qa_copy import inspect_copy, OLD_PLUGIN, NEW_PLUGIN
from test_sinnoh_barry_pbs import fixture


class SinnohQACopyTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.game = fixture(self.root)
        (self.game / "mkxp.json").write_text(
            json.dumps({"dataPathOrg": "Pokemon Blue",
                        "dataPathApp": "Decades Main"}), encoding="utf-8")
        self.draft = self.root / ".blue-work/barry-draft"
        publish(self.game, self.draft, root=self.root)
        self.qa = self.root / "private-sinnoh"
        self.qa.mkdir()
        (self.qa / "Sinnoh pilot.json").write_text(
            json.dumps({"region": "SINNOH"}), encoding="utf-8")
        (self.qa / "mkxp.json").write_text(
            json.dumps({"dataPathOrg": "Sinnoh Testing",
                        "dataPathApp": "Standalone Pilot"}), encoding="utf-8")
        for filename in (PBS_TRAINERS, PBS_TYPE):
            path = self.qa / filename
            path.parent.mkdir(exist_ok=True)
            path.write_bytes((self.draft / filename).read_bytes())

    def inspect(self):
        return inspect_copy(self.game, self.qa, self.draft, root=self.root)

    def test_pbs_with_separate_saves_is_not_engine_approval(self):
        result = self.inspect()
        self.assertTrue(result["pbs_draft_files_match"])
        self.assertTrue(result["qa_profile_distinct_from_main"])
        self.assertEqual(result["pbs_variants_in_draft_verified"], 3)
        self.assertEqual(result["story_plugin_mode"], "NO_SINNOH_STORY_PLUGIN")
        self.assertFalse(result["qa_binary_present"])
        for field in ("compiled_trainer_index_tested", "battle_levels_70_90_tested",
                      "safe_to_create_barry_marker", "gameplay_approved",
                      "may_merge_with_main_game"):
            self.assertFalse(result[field])
        self.assertFalse((self.game / READY_MARKER).exists())

    def test_detects_legacy_dialog_vs_new_three_ball_plugin(self):
        old = self.qa / OLD_PLUGIN
        old.parent.mkdir(parents=True)
        old.write_text("module BlueSinnohPreview; end", encoding="utf-8")
        self.assertEqual(self.inspect()["story_plugin_mode"], "LEGACY_ROWAN_DIALOG")
        new = self.qa / NEW_PLUGIN
        new.write_text("module BlueSinnohPilot; end", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "simultaneamente"):
            self.inspect()
        old.unlink()
        self.assertEqual(self.inspect()["story_plugin_mode"], "AUTHORED_THREE_BALLS")
        self.assertFalse(self.inspect()["gameplay_approved"])

    def test_refuses_pbs_bytes_that_do_not_match_draft(self):
        path = self.qa / PBS_TRAINERS
        path.write_bytes(path.read_bytes() + b"\n# unverified change\n")
        with self.assertRaisesRegex(ValueError, "diverge"):
            self.inspect()

    def test_refuses_shared_save_profile(self):
        path = self.qa / "mkxp.json"
        path.write_bytes((self.game / "mkxp.json").read_bytes())
        with self.assertRaisesRegex(ValueError, "mesmo perfil"):
            self.inspect()
        path.write_text(json.dumps({"dataPathOrg": "Test"}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "independente"):
            self.inspect()

    def test_refuses_barry_marker_before_real_battle(self):
        marker = self.qa / READY_MARKER
        marker.parent.mkdir(parents=True)
        marker.write_text("BLUE_SINNOH_BARRY_V1_READY", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Marcador"):
            self.inspect()

    def test_refuses_main_game_as_qa_copy_or_bad_manifest(self):
        with self.assertRaisesRegex(ValueError, "distinta"):
            inspect_copy(self.game, self.game, self.draft, root=self.root)
        (self.qa / "Sinnoh pilot.json").write_text(
            json.dumps({"region": "KANTO"}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "pilot.json inválido"):
            self.inspect()

    def test_inspection_does_not_write_to_any_game_file(self):
        before = {
            p.relative_to(self.root): p.read_bytes()
            for path in (self.game, self.qa)
            for p in path.rglob("*") if p.is_file()
        }
        self.inspect()
        after = {
            p.relative_to(self.root): p.read_bytes()
            for path in (self.game, self.qa)
            for p in path.rglob("*") if p.is_file()
        }
        self.assertEqual(before, after)

    def test_refuses_symlinked_pbs_file(self):
        path = self.qa / PBS_TYPE
        path.unlink()
        try:
            path.symlink_to(self.draft / PBS_TYPE)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable")
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.inspect()


if __name__ == "__main__":
    unittest.main()
