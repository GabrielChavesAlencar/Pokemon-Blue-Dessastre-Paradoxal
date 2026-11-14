"""Offline verification of Barry drafts never grants marker or playable approval."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))

from build_sinnoh_barry_pbs import PBS_TRAINERS, READY_MARKER, publish
from verify_sinnoh_barry_pbs import inspect
from test_sinnoh_barry_pbs import fixture


class SinnohBarryIntegrityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.game = fixture(self.root)
        self.output = self.root / ".blue-work/sinnoh-barry"
        publish(self.game, self.output, root=self.root)

    def test_three_teams_integrity_is_not_a_game_battle_proof(self):
        result = inspect(self.output, self.game, root=self.root)
        self.assertEqual(result["teams_verified"], 3)
        self.assertEqual(result["mode"], "DRAFT_INTEGRITY_ONLY")
        self.assertTrue(result["balance_source_checked"])
        self.assertFalse(result["native_scaling_executed"])
        self.assertFalse(result["pbs_compiled_in_game"])
        self.assertFalse(result["ready_marker_allowed"])
        self.assertFalse(result["may_install_into_game"])
        self.assertFalse((self.output / READY_MARKER).exists())
        self.assertFalse((self.game / READY_MARKER).exists())

    def test_rejects_tampered_content_by_hash(self):
        path = self.output / PBS_TRAINERS
        path.write_text(path.read_text("utf-8").replace(
            "Pokemon = CHIMCHAR,5", "Pokemon = PIPLUP,5", 1),
            encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            inspect(self.output, self.game, root=self.root)

    def test_rejects_incomplete_team_even_if_manifest_hash_also_changed(self):
        path = self.output / PBS_TRAINERS
        lines = path.read_text("utf-8")
        path.write_text(lines.replace("[BLUE_SINNOH_RIVAL,Barry,2]",
                                      "[BLUE_SINNOH_RIVAL,Barry,7]"),
                        encoding="utf-8")
        manifest = self.output / "sinnoh-barry-pbs-report.json"
        data = json.loads(manifest.read_text("utf-8"))
        data["files_sha256"][PBS_TRAINERS] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "três treinadores"):
            inspect(self.output, self.game, root=self.root)

    def test_rejects_marker_even_inside_private_draft(self):
        marker = self.output / READY_MARKER
        marker.parent.mkdir(parents=True)
        marker.write_text("BLUE_SINNOH_BARRY_V1_READY", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "marcador"):
            inspect(self.output, self.game, root=self.root)

    def test_changes_to_real_blue_pbs_require_new_draft(self):
        path = self.game / "PBS/pokemon.txt"
        path.write_text(path.read_text("utf-8") + "\n# changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "mudou"):
            inspect(self.output, self.game, root=self.root)

    def test_changes_to_dynamic_balance_source_require_new_draft(self):
        path = self.root / "scripts/battle_polish/Campaign.rb"
        path.write_text(path.read_text("utf-8") + "\n# edited", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Runtime"):
            inspect(self.output, self.game, root=self.root)

    def test_prevents_using_game_or_arbitrary_directory_as_draft(self):
        with self.assertRaisesRegex(ValueError, "Draft deve estar"):
            inspect(self.game, self.game, root=self.root)
        with self.assertRaisesRegex(ValueError, "Draft deve estar"):
            inspect(self.root / "unrelated", self.game, root=self.root)

    def test_refuses_symlinked_parent_escape(self):
        redirect = self.root / ".blue-work/malicious"
        try:
            redirect.symlink_to(self.game, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation unavailable")
        (self.game / "fake-draft").mkdir()
        with self.assertRaisesRegex(ValueError, "Draft deve estar"):
            inspect(redirect / "fake-draft", self.game, root=self.root)


if __name__ == "__main__":
    unittest.main()
