"""Find published multiregion JoiPlay patch baselines across every release page.

A single GitHub Releases page is dominated by Blue Battle Hub downloads and
can omit the most recent *multiregion* release. An absent baseline makes the
Android updater refuse to patch an otherwise valid installed game.

Only select real published releases with an uploaded channel-specific manifest;
no ROMs, game assets, user saves, or local files are downloaded here.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import urllib.error

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.android.select_previous_kanto_releases import fetch_release_pages

MANIFEST = "Blue-Android-Decades-Kanto-Hoenn.update.json"
TAG = re.compile(
    r"^android-multiregion-(?:hotfix-)?[0-9]+-[a-f0-9]{7,40}$"
)


def select_releases(payload: object) -> tuple[list[str], int, int]:
    if not isinstance(payload, list) or not payload:
        raise ValueError("Missing GitHub release history")
    if all(isinstance(p, list) for p in payload):
        pages = payload
    elif all(isinstance(x, dict) for x in payload):
        pages = [payload]
    else:
        raise ValueError("Malformed GitHub release pages")
    valid: dict[str, dict] = {}
    for page in pages:
        if not isinstance(page, list):
            raise ValueError("Malformed release page")
        for row in page:
            if not isinstance(row, dict):
                raise ValueError("Malformed release record")
            tag = row.get("tag_name")
            if not isinstance(tag, str) or not TAG.fullmatch(tag):
                continue
            if row.get("draft") or not row.get("published_at"):
                continue
            assets = row.get("assets")
            if not isinstance(assets, list) or not any(
                isinstance(asset, dict) and asset.get("name") == MANIFEST
                and asset.get("state") == "uploaded"
                for asset in assets
            ):
                continue
            valid[tag] = row
    if not valid:
        raise ValueError("No published multiregion baseline with uploaded manifest")
    ordered = sorted(valid.values(),
                     key=lambda x: (str(x["published_at"]), str(x["tag_name"])),
                     reverse=True)
    selected = ordered[:5]
    if len(ordered) > 5 and ordered[-1]["tag_name"] not in {
            item["tag_name"] for item in selected}:
        selected.append(ordered[-1])
    tags = [row["tag_name"] for row in selected]
    if len(set(tags)) != len(tags):
        raise ValueError("Duplicate multiregion baseline")
    return tags, len(pages), len(ordered)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-github", action="store_true")
    args = parser.parse_args(argv)
    try:
        pages = (fetch_release_pages(os.environ.get("GITHUB_REPOSITORY", ""),
                                     os.environ.get("GH_TOKEN", ""))
                 if args.fetch_github else json.load(sys.stdin))
        tags, page_count, candidate_count = select_releases(pages)
        print_tags = tags
    except (ValueError, TypeError, OSError, urllib.error.URLError) as error:
        print("Multiregion Android baseline selection blocked: " + str(error),
              file=sys.stderr)
        return 1
    for tag in print_tags:
        print(tag)
    return 0


if __name__ == "__main__":
    sys.exit(main())
