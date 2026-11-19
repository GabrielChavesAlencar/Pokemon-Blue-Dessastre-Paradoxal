"""Select previous Kanto Android releases from all GitHub API pages.

Input: JSON written by gh api --paginate --slurp .../releases?per_page=100
Output: verified release tags, one per line, newest four plus oldest baseline.
The query must fail closed when older Kanto releases exist but none are selected.
Do not access or change user games/saves, and never download game sources.
"""
from __future__ import annotations

import json
import re
import sys

MANIFEST = "Blue-Android-Kanto-Piloto.update.json"
TAG = re.compile(r"^kanto-android-[0-9]+-[a-f0-9]{7,40}$")


def select_releases(payload: object) -> tuple[list[str], int, int]:
    """Accept --slurp's array-of-pages, not a PowerShell-flattened page object."""
    if not isinstance(payload, list) or not payload:
        raise ValueError("GitHub release pages are missing or malformed")
    if all(isinstance(page, list) for page in payload):
        pages = payload
    elif all(isinstance(item, dict) for item in payload):
        pages = [payload]  # JSON API fixture or an un-slurped single page.
    else:
        raise ValueError("Unexpected GitHub release pagination shape")

    matches: dict[str, dict] = {}
    for page in pages:
        if not isinstance(page, list):
            raise ValueError("A GitHub release page is not a list")
        for release in page:
            if not isinstance(release, dict):
                raise ValueError("Malformed GitHub release entry")
            tag = release.get("tag_name")
            if not isinstance(tag, str) or not TAG.fullmatch(tag):
                continue
            if release.get("draft") or not release.get("published_at"):
                continue
            assets = release.get("assets")
            if not isinstance(assets, list):
                continue
            if not any(isinstance(asset, dict)
                       and asset.get("name") == MANIFEST
                       and asset.get("state") == "uploaded" for asset in assets):
                continue
            matches[tag] = release

    if not matches:
        raise ValueError("No published Kanto Android baseline with uploaded manifest found")

    ordered = sorted(matches.values(),
                     key=lambda release: (str(release["published_at"]),
                                          str(release["tag_name"])),
                     reverse=True)
    selected = ordered[:4]
    if len(ordered) > 4 and ordered[-1]["tag_name"] not in {
            item["tag_name"] for item in selected}:
        selected.append(ordered[-1])
    tags = [item["tag_name"] for item in selected]
    if len(tags) != len(set(tags)):
        raise ValueError("Duplicate Kanto Android baseline")
    return tags, len(pages), len(matches)


def main() -> int:
    try:
        tags, page_count, candidate_count = select_releases(json.load(sys.stdin))
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        print("Kanto Android baseline selection blocked: " + str(error), file=sys.stderr)
        return 1
    print(f"Kanto Android baselines: {candidate_count} verified across {page_count} pages; "
          f"selected {len(tags)}", file=sys.stderr)
    for tag in tags:
        print(tag)
    return 0


if __name__ == "__main__":
    sys.exit(main())
