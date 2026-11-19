"""Fail closed if release discovery is limited to one GitHub page."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/kanto-pilot-check.yml"

class KantoReleaseHistoryTests(unittest.TestCase):
    def test_kanto_manifest_sources_use_all_pages(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        marker = "- name: Gerar manifesto e atualização incremental de Kanto"
        self.assertEqual(text.count(marker), 1)
        block = text.split(marker, 1)[1].split("- name: Guardar ZIP de testes de Kanto", 1)[0]
        self.assertIn("gh api --paginate --slurp", block)
        self.assertIn("ForEach-Object { $_ }", block)
        self.assertIn("Blue-Android-Kanto-Piloto.update.json", block)
        self.assertIn("--previous-manifest", block)
        self.assertIn("kanto-android-*", block)

if __name__ == "__main__":
    unittest.main()
