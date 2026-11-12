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

    def test_full_qa_report_has_all_sections_but_never_self_approves(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with patch.object(kanto_feedback, "ROOT", root):
                folder=root/".blue-work"/"reports"
                checks={key:"pass" for key,_ in kanto_feedback.CHECKS}
                summary=kanto_feedback.report_summary(checks)
                self.assertEqual(summary["passed_reported"],len(kanto_feedback.CHECKS))
                self.assertFalse(summary["accepted_integrally"])
                self.assertTrue(summary["manual_review_required"])
                report=kanto_feedback.write_report(checks,"Teste manual pendente de revisão",
                                                   folder,platform="windows",scope="all")
                doc=report.read_text("utf-8")
                self.assertIn("### Liga",doc)
                self.assertIn("### Android",doc)
                self.assertIn("Aceite integral: NÃO ATESTADO",doc)
                companion=json.loads(report.with_suffix(".json").read_text("utf-8"))
                self.assertEqual(companion["schema"],2)
                self.assertEqual(companion["checks"]["route23"],"pass")
                self.assertFalse(companion["summary"]["accepted_integrally"])
                self.assertEqual(companion["type"],"manual_observation_unreviewed")

    def test_android_subset_cannot_implicitly_pass_windows_checks(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with patch.object(kanto_feedback, "ROOT", root):
                report=kanto_feedback.write_report(
                    {"joiplay_boot":"pass","joiplay_input":"fail"}, "",root/".blue-work",
                    platform="joiplay",scope="android")
                content=report.read_text("utf-8")
                self.assertIn("sessão experimental JoiPlay",content)
                self.assertIn("abrir",content.lower())
                self.assertIn(" — FALHOU",content)
                self.assertIn(" — NÃO TESTADO",content)
                summary=kanto_feedback.report_summary({"joiplay_boot":"pass"})
                self.assertEqual(summary["passed_reported"],1)
                self.assertEqual(summary["not_tested"],len(kanto_feedback.CHECKS)-1)

    def test_rejects_invalid_states_and_unsanctioned_check_ids(self):
        with self.assertRaisesRegex(ValueError,"estados inválidos"):
            kanto_feedback.report_summary({"route23":"auto_success"})
        with self.assertRaisesRegex(ValueError,"IDs desconhecidos"):
            kanto_feedback.report_summary({"fake_ci_pass":"pass"})
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with patch.object(kanto_feedback,"ROOT",root):
                with self.assertRaisesRegex(ValueError,"Plataforma ou seção"):
                    kanto_feedback.write_report({},"",root/".blue-work",platform="unknown")


if __name__ == "__main__":
    unittest.main()
