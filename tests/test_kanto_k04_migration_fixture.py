"""The migrated Main boot gets its own namespace, not commented defaults."""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/regions"))
from qa_k04_migration import isolated_config, save_namespace_valid, MIGRATED_PROFILE


class K04MigrationFixtureTests(unittest.TestCase):
    def test_comment_only_defaults_are_not_active_and_other_options_survive(self):
        raw = '''// configured via engine defaults: {"dataPathApp": "Game"}
{
  // "dataPathOrg": "Example",
  /* "dataPathApp": "Example", */
  "url": "https://example.com",
  "sleep": true,
}
'''
        result = json.loads(isolated_config(raw))
        self.assertEqual(result["sleep"], True)
        self.assertEqual(result["url"], "https://example.com")
        self.assertEqual(result["dataPathApp"], MIGRATED_PROFILE)
        self.assertEqual(result["dataPathOrg"], "Dessastre Paradoxal Kanto Testes")
        with TemporaryDirectory() as d:
            game = Path(d)
            (game / "mkxp.json").write_text(raw, encoding="utf8")
            self.assertFalse(save_namespace_valid(game, MIGRATED_PROFILE))
            (game / "mkxp.json").write_text(isolated_config(raw), encoding="utf8")
            self.assertTrue(save_namespace_valid(game, MIGRATED_PROFILE))
            self.assertFalse(save_namespace_valid(game, "Kanto K04 Gameplay CI"))

    def test_real_existing_profile_is_rejected(self):
        for key in ("dataPathOrg", "dataPathApp"):
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError, "Existing active save identity"):
                    isolated_config(json.dumps({key: "existing game"}))
