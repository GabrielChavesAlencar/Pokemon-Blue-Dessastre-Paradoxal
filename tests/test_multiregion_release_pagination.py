"""Offline regression: multiregion Android must find prior manifest beyond page 1."""
from pathlib import Path
import io
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.android.select_previous_multiregion_releases import select_releases

WORKFLOW = ROOT / ".github/workflows/android-multiregion.yml"
MANIFEST = "Blue-Android-Decades-Kanto-Hoenn.update.json"


def release(tag, stamp, *, draft=False, asset=True, uploaded=True):
    return {
        "tag_name": tag,
        "published_at": stamp,
        "draft": draft,
        "assets": ([{"name": MANIFEST,
                     "state": "uploaded" if uploaded else "pending"}]
                   if asset else []),
    }


class MultiregionReleasePaginationTests(unittest.TestCase):
    def test_current_released_hotfix_is_not_lost_under_battle_hub_pages(self):
        # The repository may publish 300 non-multiregion releases first.
        unrelated = release("battle-hub-2000-abcdef0", "2026-11-19T20:00:00Z")
        pages = [[unrelated.copy() for _ in range(100)] for _ in range(3)]
        pages.append([
            release("android-multiregion-hotfix-30-ba020a5", "2026-11-19T01:04:03Z"),
            release("android-multiregion-hotfix-29-547a839", "2026-11-19T00:44:01Z"),
            release("android-multiregion-hotfix-2-5d0cc84", "2026-11-14T00:00:00Z"),
        ])
        tags, num_pages, count = select_releases(pages)
        self.assertEqual((num_pages, count), (4, 3))
        self.assertEqual(tags[0], "android-multiregion-hotfix-30-ba020a5")
        self.assertIn("android-multiregion-hotfix-29-547a839", tags)
        self.assertIn("android-multiregion-hotfix-2-5d0cc84", tags)

    def test_latest_five_and_oldest_remain_available_for_repair(self):
        rows = [
            release(f"android-multiregion-{number}-abc1234",
                    f"2026-11-{number:02d}T10:00:00Z")
            for number in (12, 13, 14, 15, 16, 17, 18)
        ]
        tags, _, count = select_releases([rows])
        self.assertEqual(count, 7)
        self.assertEqual(tags, [
            "android-multiregion-18-abc1234",
            "android-multiregion-17-abc1234",
            "android-multiregion-16-abc1234",
            "android-multiregion-15-abc1234",
            "android-multiregion-14-abc1234",
            "android-multiregion-12-abc1234",
        ])

    def test_draft_missing_assets_wrong_channel_or_unuploaded_are_rejected(self):
        rows = [
            release("android-multiregion-6-abcdef0", "2026-11-06T10:00:00Z", draft=True),
            release("android-multiregion-5-abcdef0", "2026-11-05T10:00:00Z", asset=False),
            release("android-multiregion-4-abcdef0", "2026-11-04T10:00:00Z", uploaded=False),
            release("kanto-android-3-abcdef0", "2026-11-03T10:00:00Z"),
            release("android-multiregion-2-abcdef0", None),
            release("android-multiregion-1-abcdef0", "2026-11-01T10:00:00Z"),
        ]
        tags, _, matches = select_releases([rows])
        self.assertEqual(matches, 1)
        self.assertEqual(tags, ["android-multiregion-1-abcdef0"])

    def test_fail_closed_for_malformed_history_and_no_valid_previous_release(self):
        for value in ([], {}, None, ["bad"], [[None]], [[{"tag_name": "battle-hub-1"}]]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                select_releases(value)

    def test_release_workflow_always_selects_paginated_old_manifests(self):
        text = WORKFLOW.read_text("utf8")
        self.assertIn(
            "python scripts/android/select_previous_multiregion_releases.py --fetch-github",
            text)
        self.assertNotIn('gh api "repos/$env:GITHUB_REPOSITORY/releases?per_page=100"',
                         text)
        self.assertIn("$selected.Count -eq 0", text)
        self.assertIn("gh release download $tag", text)
        self.assertIn("--previous-manifest", text)
        self.assertIn("android-map-perf-preview-02e8e5a", text)
        self.assertIn(
            "python scripts/android/verify_kanto_cerulean.py --channel multiregion",
            text)
        self.assertIn("Delta da preview para a main nao gerado", text)


if __name__ == "__main__":
    unittest.main()
