"""Regression for the opt-in experimental Windows gameplay report."""
from __future__ import annotations
import sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    import kanto_feedback
finally:
    sys.path.remove(str(ROOT / "scripts/regions"))


class KantoExperimentalFeedbackTests(unittest.TestCase):
    def test_writes_only_inside_workspace_and_preserves_unverified_cases(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / ".blue-work"
            folder = workspace / "kanto-gui-reports"
            with patch.object(kanto_feedback, "ROOT", root):
                path = kanto_feedback.write_report(
                    {"initial": "pass", "misty": "fail"}, "Ginásio: combate não abriu", folder
                )
                body = path.read_text("utf-8")
                self.assertIn("- [x] Nova partida abre Pallet", body)
                self.assertIn(" — FALHOU", body)
                self.assertIn(" — NÃO TESTADO", body)
                self.assertIn("Ginásio: combate não abriu", body)
                self.assertNotIn("concluída automaticamente", body)
                with self.assertRaises(ValueError):
                    kanto_feedback.write_report({}, "", root / "game")


if __name__ == "__main__":
    unittest.main()
