"""Offline regression: multiregion Android must find prior manifest beyond page 1."""
from pathlib import Path
import io
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.android.select_previous_multiregion_releases import (
    REQUIRED_BASELINES, select_releases,
)

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

    def test_reported_cerulean_install_survives_release_window_churn(self):
        # More than five newer releases, plus an unrelated oldest release.
        rows = [
            release(f"android-multiregion-{n}-abcdef0",
                    f"2026-11-25T{n - 60:02d}:00:00Z")
            for n in range(61, 74)
        ]
        old = release("android-multiregion-1-abcdef0", "2026-11-01T00:00:00Z")
        pinned = [
            release("android-multiregion-hotfix-2-5d0cc84", "2026-11-14T00:00:00Z"),
            release("android-multiregion-hotfix-30-ba020a5", "2026-11-19T01:04:03Z"),
            release("android-multiregion-hotfix-31-e7200ef", "2026-11-26T19:30:00Z"),
            release("android-multiregion-82-e23ff33", "2026-11-26T15:00:00Z"),
        ]
        tags, _, count = select_releases([rows, [old, *pinned]],
                                         require_known_baselines=True)
        self.assertEqual(count, 18)
        self.assertEqual(tags[0], "android-multiregion-hotfix-31-e7200ef")
        self.assertEqual(len(tags), len(set(tags)))
        for tag in REQUIRED_BASELINES:
            self.assertIn(tag, tags)
        self.assertIn(old["tag_name"], tags)

    def test_required_baseline_missing_or_unuploaded_blocks_production(self):
        newest = release("android-multiregion-73-abcdef0", "2026-11-26T00:00:00Z")
        first = release(REQUIRED_BASELINES[0], "2026-11-14T00:00:00Z")
        missing = release(REQUIRED_BASELINES[1], "2026-11-19T00:00:00Z",
                          uploaded=False)
        for rows in ([newest, first], [newest, first, missing]):
            with self.subTest(rows=rows), self.assertRaisesRegex(ValueError, "ba020a5"):
                select_releases(rows, require_known_baselines=True)

    def test_required_baseline_already_recent_is_not_duplicated(self):
        rows = [release(tag, "2026-11-19T00:00:00Z") for tag in REQUIRED_BASELINES]
        tags, _, _ = select_releases(rows, require_known_baselines=True)
        self.assertCountEqual(tags, REQUIRED_BASELINES)

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

    def test_withdrawn_hotfix_and_previous_good_release_remain_required(self):
        rows = [release(tag, "2026-11-26T19:30:00Z") for tag in REQUIRED_BASELINES]
        tags, _, _ = select_releases(rows, require_known_baselines=True)
        self.assertIn("android-multiregion-hotfix-31-e7200ef", tags)
        self.assertIn("android-multiregion-82-e23ff33", tags)
        with self.assertRaisesRegex(ValueError, "hotfix-31"):
            select_releases([row for row in rows if "hotfix-31" not in row["tag_name"]],
                            require_known_baselines=True)

    def test_legacy_repack_cannot_publish_and_portal_build_precedes_tests(self):
        old = (ROOT / ".github/workflows/android-multiregion-repack.yml").read_text("utf8")
        self.assertIn("contents: read", old)
        self.assertNotIn("contents: write", old)
        self.assertNotIn("gh release create", old)
        self.assertNotIn("gh release upload", old)
        self.assertIn("python -m unittest discover", old)
        portal = (ROOT / ".github/workflows/android-multiregion-tests.yml").read_text("utf8")
        self.assertLess(portal.index("npm run build --prefix site"), portal.index("npm test --prefix site"))

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
        self.assertIn("--fetch-github --require-known-baselines", text)
        self.assertIn("ba020a57052e2952de308dbb4166aad760b1e72c", text)
        self.assertIn("Delta incremental obrigatorio ausente ou duplicado", text)
        self.assertIn("Integridade do delta obrigatorio falhou", text)
        self.assertNotIn("$_.tag_name -eq $specific", text)


if __name__ == "__main__":
    unittest.main()
