"""Regression of GitHub Releases pagination for Kanto Android deltas."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.android.select_previous_kanto_releases import select_releases

WORKFLOW = ROOT / ".github/workflows/kanto-pilot-check.yml"
MANIFEST = "Blue-Android-Kanto-Piloto.update.json"


def release(number, published, *, manifest=True, draft=False, uploaded=True):
    return {
        "tag_name": f"kanto-android-{number}-1234abc",
        "draft": draft,
        "published_at": published,
        "assets": [{"name": MANIFEST,
                    "state": "uploaded" if uploaded else "starter"}] if manifest else [],
    }


class KantoReleaseHistoryTests(unittest.TestCase):
    def test_fourth_page_is_not_lost_and_oldest_is_retained(self):
        # Battle Hub releases fill three whole API pages.
        unrelated = {"tag_name": "battle-hub-1-1234abc",
                     "published_at": "2026-11-19T00:00:00Z",
                     "assets": [{"name": MANIFEST, "state": "uploaded"}]}
        pages = [[unrelated.copy() for _ in range(100)] for _ in range(3)]
        historical = [release(i, f"2026-11-{i:02}T12:00:00Z")
                      for i in (12, 13, 14, 15, 16)]
        pages.append(historical)
        tags, count, matches = select_releases(pages)
        self.assertEqual(count, 4)
        self.assertEqual(matches, 5)
        self.assertEqual(tags, [
            "kanto-android-16-1234abc",
            "kanto-android-15-1234abc",
            "kanto-android-14-1234abc",
            "kanto-android-13-1234abc",
            "kanto-android-12-1234abc",
        ])

    def test_filter_drafts_unpublished_unuploaded_and_wrong_assets(self):
        pages = [[
            release(5, "2026-11-05T12:00:00Z", draft=True),
            release(4, "2026-11-04T12:00:00Z", uploaded=False),
            release(3, "2026-11-03T12:00:00Z", manifest=False),
            release(2, None),
            release(1, "2026-11-01T12:00:00Z"),
        ]]
        tags, count, matches = select_releases(pages)
        self.assertEqual((count, matches), (1, 1))
        self.assertEqual(tags, ["kanto-android-1-1234abc"])

    def test_unexpected_pagination_shape_blocks_publication(self):
        for payload in ([], {}, None, ["not a page"],
                        [[{"tag_name": "battle-hub-3"}], {"bad": "page"}],
                        [[False]], [[{"tag_name": "kanto-android-1-1234abc"}]]):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                select_releases(payload)

    def test_single_page_and_duplicate_records_are_safe(self):
        newer = release(3, "2026-11-03T12:00:00Z")
        older = release(1, "2026-11-01T12:00:00Z")
        tags, count, matches = select_releases([newer, newer, older])
        self.assertEqual((count, matches), (1, 2))
        self.assertEqual(tags, ["kanto-android-3-1234abc",
                                "kanto-android-1-1234abc"])

    def test_workflow_requires_real_parsed_baselines_and_delta_zip(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        marker = "- name: Gerar manifesto e atualização incremental de Kanto"
        self.assertEqual(text.count(marker), 1)
        block = text.split(marker, 1)[1].split(
            "- name: Guardar ZIP de testes de Kanto", 1)[0]
        self.assertIn("gh api --paginate --slurp", block)
        self.assertIn("python scripts/android/select_previous_kanto_releases.py", block)
        self.assertIn("$selected.Count -eq 0", block)
        self.assertIn("gh release download $tag", block)
        self.assertIn("--previous-manifest", block)
        self.assertIn("Blue-Android-Kanto-Piloto*.patch.zip", block)
        self.assertIn("No incremental Kanto patch generated; publication blocked", block)
        self.assertNotIn("ConvertFrom-Json | ForEach-Object", block)


if __name__ == "__main__":
    unittest.main()
