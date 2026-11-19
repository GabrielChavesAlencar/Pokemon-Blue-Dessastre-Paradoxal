"""Compare Kanto's entire source tree with the integration catalog, read-only.

Does not execute donor events, install maps or certify gameplay. Source IDs in
this report are FRLG IDs, never destination IDs to insert into a saved game.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

from audit import KANTO, ROOT, commands, inventory, json_file, load


def map_name(info):
    value = info.attrs["@name"]
    if not isinstance(value, bytes):
        return str(value)
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return value.decode("cp1252")


def placeholder(attrs, has_children):
    """Identify blank hierarchy candidates; not a claim they are playable."""
    if not has_children or attrs["@events"]:
        return False
    raw = attrs["@data"].data
    if len(raw) < 20:
        raise ValueError("Invalid source map tile table")
    _, width, height, depth, count = struct.unpack("<5i", raw[:20])
    if (width, height, depth) != (20, 15, 3) or count != 900:
        return False
    if len(raw) != 20 + count * 2:
        raise ValueError("Invalid source map tile table length")
    cells = struct.unpack("<900h", raw[20:])
    return len(set(cells[:300])) == 1 and not any(cells[300:])


def audit(source: Path, manifest: dict, root_id=4) -> dict:
    infos, files = inventory(source)
    if root_id not in infos:
        raise ValueError("Kanto source hierarchy root is missing")
    wanted = set(map(int, manifest["maps"]))
    previews = set(manifest.get("preview_only", []))
    if not previews <= wanted:
        raise ValueError("Preview IDs are outside the integration catalog")

    def in_kanto(mid):
        seen = set()
        while mid in infos:
            if mid == root_id:
                return True
            if mid in seen:
                raise ValueError("Cyclic source map hierarchy")
            seen.add(mid)
            mid = infos[mid].attrs["@parent_id"]
        return False

    scope = {mid for mid in infos if mid != root_id and in_kanto(mid)}
    parents = {info.attrs["@parent_id"] for info in infos.values()}
    omitted, hierarchy = [], []
    missing_files = sorted((scope | wanted) - files.keys())
    for mid in sorted(scope - wanted):
        if mid not in files:
            continue
        attrs = load(files[mid]).attrs
        row = {"source_id": mid, "name": map_name(infos[mid]),
               "dimensions": [attrs["@width"], attrs["@height"]],
               "events": len(attrs["@events"])}
        (hierarchy if placeholder(attrs, mid in parents) else omitted).append(row)

    # Group all direct exits from imported maps into uncatalogued source maps.
    # These are reference boundaries; imported events can intentionally block
    # them, so they are not evidence of an in-game crash or a walkable path.
    boundary = {}

    def edge(left, right, kind):
        if left in wanted and right in scope - wanted:
            boundary.setdefault(right, set()).add((left, kind))

    for line in (source / "PBS/map_connections.txt").read_text("utf-8-sig").splitlines():
        row = line.split("#", 1)[0].strip()
        if not row:
            continue
        parts = [part.strip() for part in row.split(",")]
        if len(parts) != 6:
            raise ValueError("Malformed source map connection")
        left, right = int(parts[0]), int(parts[3])
        edge(left, right, "connection")
        edge(right, left, "connection")
    for mid in sorted(wanted & files.keys()):
        for _, _, _, command in commands(load(files[mid])):
            params = command["@parameters"]
            if command["@code"] == 201 and params[0] == 0:
                edge(mid, params[1], "transfer")

    return {
        "source_archive_sha256_expected": manifest["sha256"],
        "source_kanto_entries": len(scope), "catalogued_maps": len(wanted),
        "preview_only_maps": len(previews),
        "omitted_content_count": len(omitted), "omitted_content": omitted,
        "hierarchy_candidate_count": len(hierarchy), "hierarchy_candidates": hierarchy,
        "source_files_missing": missing_files,
        "catalog_ids_outside_kanto": sorted(wanted - scope),
        "catalog_ids_missing_from_source_index": sorted(wanted - infos.keys()),
        "boundaries": [
            {"missing_source_id": target, "name": map_name(infos[target]),
             "from": [{"source_id": origin, "kind": kind}
                      for origin, kind in sorted(origins)]}
            for target, origins in sorted(boundary.items())],
        "gameplay_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
                        default=ROOT / ".blue-work/frlg-source/Essentials FRLG")
    args = parser.parse_args()
    result = audit(args.source, json_file(KANTO))
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if (result["source_files_missing"] or result["catalog_ids_outside_kanto"] or
            result["catalog_ids_missing_from_source_index"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
