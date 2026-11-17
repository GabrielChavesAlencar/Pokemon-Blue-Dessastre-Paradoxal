"""Publish per-channel verified Android manifests and (when possible) small delta ZIPs.

The full game archive is the only source of truth. Previous releases contribute
only a published manifest, not untrusted game files. Never include saves.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.android.update_client import (MARKER, CHANNELS, safe_path, sha256_file,
                                         sha256_bytes, _patchable_immutables,
                                         _old_patch_files)


def from_archive(path: Path, channel: str):
    _, root = {"decades": (None, "Pokemon-Blue-Android/"),
               "multiregion": (None, "Pokemon-Blue-Android/"),
               "kanto": (None, "Pokemon-Blue-Kanto-Android/")}[channel]
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or not all(n.startswith(root) for n in names):
            raise ValueError("Invalid game archive entries.")
        marker = json.loads(archive.read(root + MARKER))
        if (marker.get("schema") != 1 or marker.get("channel") != channel
                or not isinstance(marker.get("files"), dict)):
            raise ValueError("Missing installed update manifest in game ZIP.")
        actual = {n[len(root):] for n in names if safe_path(n[len(root):])}
        if actual != set(marker["files"]):
            raise ValueError("Game archive and installed update manifest differ.")
        for name, meta in marker.get("immutable", {}).items():
            if (name not in {entry[len(root):] for entry in names} or
                    meta != {"sha256": sha256_bytes(archive.read(root + name)),
                             "size": archive.getinfo(root + name).file_size}):
                raise ValueError("Unpatchable root file differs from manifest: " + name)
        for name, meta in marker["files"].items():
            if (not safe_path(name) or
                    meta != {"sha256": sha256_bytes(archive.read(root + name)),
                             "size": archive.getinfo(root + name).file_size}):
                raise ValueError("Source ZIP file differs from hash manifest: " + name)
    return marker, root


def verified_previous(path: Path, channel: str):
    if not path.is_file():
        return None
    previous = json.loads(path.read_text(encoding="utf8"))
    if (previous.get("schema") != 1 or previous.get("channel") != channel
            or not isinstance(previous.get("files"), dict)
            or not isinstance(previous.get("revision"), str)):
        raise ValueError("Invalid previous-channel manifest.")
    if any(not safe_path(name) for name in previous["files"]):
        raise ValueError("Unsafe prior file list.")
    return previous


def publish(archive_path: Path, channel: str, previous_path: Path | None = None,
            additional_previous_paths=()):
    """Publish an exact file delta for every supplied previous game revision.

    --previous-manifest can be repeated for older installs. No old ZIP needed:
    each patch is built against that revision's verified SHA inventory.
    """
    filename, manifest_name = CHANNELS[channel]
    if archive_path.name != filename:
        raise ValueError("Unexpected full archive name.")
    current, prefix = from_archive(archive_path, channel)
    revision = current["revision"]
    result = {
        "schema": 1, "channel": channel, "revision": revision,
        "files": current["files"], "immutable": current.get("immutable", {}),
        "patch": None, "patches": [],
        "full": {
            "asset": archive_path.name,
            "size": archive_path.stat().st_size,
            "sha256": sha256_file(archive_path),
        },
    }
    paths = ([previous_path] if previous_path is not None else []) + list(additional_previous_paths)
    seen = set()
    previous_entries = []
    for path in paths:
        previous = verified_previous(path, channel)
        if not previous:
            continue
        earlier = previous["revision"]
        if earlier in seen or earlier == revision:
            continue
        seen.add(earlier)
        if not _patchable_immutables(previous.get("immutable", {}), current.get("immutable", {})):
            continue
        old, new = _old_patch_files(previous, current["files"]), current["files"]
        changed = {name: meta for name, meta in new.items() if old.get(name) != meta}
        removed = sorted(set(old) - set(new))
        previous_entries.append((earlier, changed, removed))
    with zipfile.ZipFile(archive_path) as source:
        for index, (earlier, changed, removed) in enumerate(previous_entries):
            # Preserve the legacy filename for the FIRST patch so older
            # updater versions can still use manifest["patch"].
            patch_name = (archive_path.stem + ".patch.zip" if index == 0 else
                          archive_path.stem + ".from-" + earlier[:12] + ".patch.zip")
            patch_file = archive_path.parent / patch_name
            patch_meta = {
                "schema": 1, "channel": channel,
                "from_revision": earlier, "to_revision": revision,
                "changed": changed, "removed": removed,
            }
            with zipfile.ZipFile(patch_file, "w", compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=6, allowZip64=True) as patch:
                patch.writestr("patch.json", json.dumps(patch_meta, sort_keys=True))
                for name in sorted(changed):
                    patch.writestr("files/" + name, source.read(prefix + name))
            if (patch_file.stat().st_size >= min(1024 * 1024 * 1024,
                                               archive_path.stat().st_size * .95)):
                patch_file.unlink()
                continue
            row = {
                "asset": patch_file.name, "from_revision": earlier,
                "size": patch_file.stat().st_size,
                "sha256": sha256_file(patch_file),
            }
            result["patches"].append(row)
            if result["patch"] is None:
                result["patch"] = row
    (archive_path.parent / manifest_name).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")), encoding="utf8")
    return {
        "channel": channel, "revision": revision,
        "patch": result["patch"], "patches": result["patches"],
        "manifest": manifest_name,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=CHANNELS, required=True)
    parser.add_argument("--full-zip", type=Path, required=True)
    parser.add_argument("--previous-manifest", type=Path, action="append", default=[])
    args = parser.parse_args()
    print(json.dumps(publish(args.full_zip, args.channel,
                             args.previous_manifest[0] if args.previous_manifest else None,
                             args.previous_manifest[1:])))


if __name__ == "__main__":
    main()
