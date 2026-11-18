"""Fail-closed verification for the freshly compiled native Android multiregion ZIP.

Run on both Linux and Windows. Do not execute Game.exe, load saves, change
maps, or use PowerShell-quoted inline Python expressions. This verifier reads
only the already built ZIP and update manifest. It must run before publishing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import zipfile

from scripts.android.package import compiled_region

PREFIX = "Pokemon-Blue-Android/"
TRAVEL = "Plugins/ZZZZ Blue Story and Presentation/RegionTravel.rb"
CACHE = "Data/PluginScripts.rxdata"
MUSIC = "Data/blue-kanto-music.txt"
KANTO_INSTALL = "Data/blue-kanto-install.json"
PREVIEW_REVISION = "02e8e5addc7a7f2c4a9f71195fcae7f49631ed54"
TRACKS = {
    "33": "Kanto/1-32. Road to Cerulean City - Leaving Mt. Moon.mp3",
    "39": "Kanto/1-50. Fuchsia City.mp3",
}


def verify_zip(archive_path: Path, expected_revision: str) -> dict:
    """Verify actual Kanto BGM, compiled map router and source-to-cache parity."""
    with zipfile.ZipFile(archive_path) as source:
        names = source.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate path inside native Android archive.")
        plugin = source.read(PREFIX + TRAVEL)
        if b"module BlueRegionTravel" not in plugin or b"def self.agent_map_id(region)" not in plugin:
            raise ValueError("Optimized regional map dispatcher missing from native Android ZIP.")
        compiled_region(source.read(PREFIX + CACHE), "RegionTravel.rb", plugin)
        text = source.read(PREFIX + MUSIC).decode("utf-8")
        rows = [line.split("\t") for line in text.splitlines() if line.startswith("MAP\t")]
        if len(rows) != 74 or len({r[1] for r in rows if len(r) >= 3}) != 74:
            raise ValueError("Native Android music must contain 74 unique Kanto MAP rows.")
        keyed = {row[1]: row[2] for row in rows if len(row) >= 3}
        kanto = json.loads(source.read(PREFIX + KANTO_INSTALL))
        mapping = kanto.get("maps")
        if (not isinstance(mapping, dict) or len(mapping) != 142 or
                len(set(mapping.values())) != 142):
            raise ValueError("Unverified integrated Kanto MapID mapping.")
        for original_id, track in TRACKS.items():
            map_id = mapping.get(original_id)
            if not isinstance(map_id, int) or keyed.get(str(map_id)) != track:
                raise ValueError("Kanto music missing on verified source map " + original_id)
        installed = json.loads(source.read(PREFIX + "Data/blue-update.json"))
        if installed.get("revision") != expected_revision or installed.get("channel") != "multiregion":
            raise ValueError("Native Android ZIP revision/channel differs from the build.")
    return {"music_maps": len(rows), "kanto_maps": len(mapping), "optimized": True}


def verify_manifest(manifest_path: Path, expected_revision: str) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("schema") != 1 or manifest.get("channel") != "multiregion" or
            manifest.get("revision") != expected_revision):
        raise ValueError("Published update manifest does not match this native Android revision.")
    patches = manifest.get("patches")
    if not isinstance(patches, list):
        raise ValueError("Native Android patch list missing.")
    previews = [row for row in patches if
                isinstance(row, dict) and row.get("from_revision") == PREVIEW_REVISION]
    if len(previews) != 1:
        raise ValueError("No unique, safe incremental patch from map-performance preview.")
    patch = previews[0]
    if (not isinstance(patch.get("size"), int) or
            patch["size"] <= 0 or patch["size"] > 20 * 1024 * 1024 or
            not isinstance(patch.get("asset"), str) or
            not re.fullmatch(r"Blue-Android-Decades-Kanto-Hoenn(?:\.from-[a-f0-9]{12})?\.patch\.zip",
                             patch["asset"]) or
            not isinstance(patch.get("sha256"), str) or
            not re.fullmatch(r"[a-f0-9]{64}", patch["sha256"])):
        raise ValueError("Native preview patch entry is malformed or oversized.")
    return {"preview_delta": patch["asset"], "bytes": patch["size"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[a-f0-9]{40}", args.revision):
        raise ValueError("Expected full 40-character GitHub commit SHA.")
    report = verify_zip(args.zip, args.revision)
    if args.manifest is not None:
        report.update(verify_manifest(args.manifest, args.revision))
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
