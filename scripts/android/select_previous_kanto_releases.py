"""Select previous Kanto Android releases from all GitHub API pages.

Input: --fetch-github loads authenticated GitHub Releases from Python HTTP;
       stdin JSON remains available for deterministic offline tests.
Output: verified release tags, one per line, newest four plus oldest baseline.
The query must fail closed when older Kanto releases exist but none are selected.
Do not access or change user games/saves, and never download game sources.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

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


def fetch_release_pages(repo: str, token: str, *,
                        opener=None, max_pages: int = 100) -> list[list[dict]]:
    """Query complete GitHub release history without a PowerShell native pipe.

    Windows gh-to-python pipeline supplied zero bytes to stdin in the actual
    Kanto release run. Use Python HTTP directly and refuse incomplete data.
    """
    if (not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo or "")
            or any(part in (".", "..") for part in repo.split("/"))):
        raise ValueError("Invalid GitHub repository")
    if not token:
        raise ValueError("GH_TOKEN missing; release discovery refused")
    if opener is None:
        opener = urllib.request.urlopen
    pages: list[list[dict]] = []
    for page in range(1, max_pages + 1):
        url = (f"https://api.github.com/repos/{repo}/releases"
               f"?per_page=100&page={page}")
        request = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "User-Agent": "Blue-Kanto-Android-Release-Selector",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        with opener(request, timeout=45) as response:
            items = json.load(response)
        if not isinstance(items, list) or len(items) > 100 or not all(
                isinstance(entry, dict) for entry in items):
            raise ValueError(f"GitHub release page {page} is malformed")
        pages.append(items)
        if len(items) < 100:
            return pages
    raise ValueError("GitHub release history exceeded pagination limit; refused")


def main(argv: list[str] | None = None) -> int:
    args = argparse.ArgumentParser(description="Select verified Kanto Android baselines")
    args.add_argument("--fetch-github", action="store_true",
                      help="Fetch every release page via authenticated Python HTTP")
    options = args.parse_args(argv)
    try:
        if options.fetch_github:
            pages = fetch_release_pages(os.environ.get("GITHUB_REPOSITORY", ""),
                                        os.environ.get("GH_TOKEN", ""))
        else:
            pages = json.load(sys.stdin)
        tags, page_count, candidate_count = select_releases(pages)
    except (ValueError, TypeError, OSError, urllib.error.URLError) as error:
        print("Kanto Android baseline selection blocked: " + str(error), file=sys.stderr)
        return 1
    # Keep stdout pure: one tag per line for the Windows PowerShell array.
    # PS 5.1 with ErrorActionPreference=Stop can treat native stderr as a failure.
    for tag in tags:
        print(tag)
    return 0


if __name__ == "__main__":
    sys.exit(main())
