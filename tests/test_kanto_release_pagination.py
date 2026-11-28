"""Regression of GitHub Releases pagination for Kanto Android deltas."""
from pathlib import Path
import io
import json
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.android.select_previous_kanto_releases import (select_releases,
                                                            fetch_release_pages)

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

    def test_python_http_fetches_all_pages_without_native_pipe(self):
        calls = []
        base = {"tag_name": "battle-hub-1", "draft": False}
        pages = [[base] * 100,
                 [release(12, "2026-11-12T12:00:00Z"),
                  release(13, "2026-11-13T12:00:00Z")]]
        def opener(request, timeout):
            calls.append((request.full_url, request.get_header("Authorization"), timeout))
            index = len(calls) - 1
            return io.BytesIO(json.dumps(pages[index]).encode("utf-8"))
        received = fetch_release_pages(
            "GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal",
            "fake-token", opener=opener)
        tags, pages_count, matches = select_releases(received)
        self.assertEqual(pages_count, 2)
        self.assertEqual(matches, 2)
        self.assertEqual(tags, ["kanto-android-13-1234abc",
                                "kanto-android-12-1234abc"])
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0][0].endswith("per_page=100&page=1"))
        self.assertTrue(calls[1][0].endswith("per_page=100&page=2"))
        self.assertEqual(calls[0][1], "Bearer fake-token")
        self.assertEqual(calls[0][2], 45)

    @patch("scripts.android.select_previous_kanto_releases.time.sleep")
    def test_transient_gateway_failure_retries_same_page_and_preserves_history(self, sleep):
        old = release(1, "2026-11-01T12:00:00Z")
        calls = []
        def opener(request, timeout):
            page = request.full_url.rpartition("=")[2]
            calls.append(page)
            if page == "1":
                return io.BytesIO(json.dumps([{"tag_name": "other"}] * 100).encode())
            if calls.count("2") == 1:
                raise HTTPError(request.full_url, 502, "Bad Gateway", {}, None)
            return io.BytesIO(json.dumps([old]).encode())
        repo = "GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal"
        pages = fetch_release_pages(repo, "fake", opener=opener)
        self.assertEqual(calls, ["1", "2", "2"])
        self.assertEqual(pages[1], [old])
        sleep.assert_called_once_with(2)

    @patch("scripts.android.select_previous_kanto_releases.time.sleep")
    def test_permanent_error_is_not_retried_and_gateway_retry_is_bounded(self, sleep):
        repo = "GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal"
        for code, count in ((403, 1), (502, 4)):
            calls = []
            def opener(request, timeout):
                calls.append(request.full_url)
                raise HTTPError(request.full_url, code, "simulated", {}, None)
            with self.subTest(code=code), self.assertRaises(HTTPError):
                fetch_release_pages(repo, "fake", opener=opener)
            self.assertEqual(len(calls), count)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [2, 5, 12])

    def test_api_http_blocks_missing_token_invalid_shape_and_truncated_history(self):
        repo = "GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal"
        with self.assertRaisesRegex(ValueError, "GH_TOKEN"):
            fetch_release_pages(repo, "", opener=lambda *_a, **_kw: None)
        with self.assertRaisesRegex(ValueError, "Invalid GitHub repository"):
            fetch_release_pages("../bad", "fake", opener=lambda *_a, **_kw: None)
        for invalid in ({}, None, [{"x": 1}] * 101, [False]):
            with self.subTest(invalid=invalid):
                def opener(*_args, **_kwargs):
                    return io.BytesIO(json.dumps(invalid).encode("utf-8"))
                with self.assertRaises(ValueError):
                    fetch_release_pages(repo, "fake", opener=opener)
        def never_ends(*_args, **_kwargs):
            return io.BytesIO(json.dumps([{"tag_name": "battle-hub-1"}] * 100).encode("utf-8"))
        with self.assertRaisesRegex(ValueError, "pagination limit"):
            fetch_release_pages(repo, "fake", opener=never_ends, max_pages=2)

    def test_workflow_requires_real_parsed_baselines_and_delta_zip(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        marker = "- name: Gerar manifesto e atualização incremental de Kanto"
        self.assertEqual(text.count(marker), 1)
        block = text.split(marker, 1)[1].split(
            "- name: Guardar ZIP de testes de Kanto", 1)[0]
        self.assertIn("python scripts/android/select_previous_kanto_releases.py --fetch-github", block)
        self.assertNotIn("gh api --paginate --slurp", block)
        self.assertIn("python scripts/android/select_previous_kanto_releases.py", block)
        self.assertIn("$selected.Count -eq 0", block)
        self.assertIn("gh release download $tag", block)
        self.assertIn("--previous-manifest", block)
        self.assertIn("Blue-Android-Kanto-Piloto*.patch.zip", block)
        self.assertIn("No incremental Kanto patch generated; publication blocked", block)
        self.assertNotIn("ConvertFrom-Json | ForEach-Object", block)


if __name__ == "__main__":
    unittest.main()
