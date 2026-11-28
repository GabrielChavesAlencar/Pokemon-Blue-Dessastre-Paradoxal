#!/usr/bin/env python3
"""Audit the pinned donor's index in isolation. Never import donor files into the game."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from server.ruby_marshal import RubyObject, loads, text

POLICY = ROOT / "qa/kalos_sources/ka01_sources.json"
CITIES = (
    "vaniville", "aquacorde", "santalune", "lumiose", "camphrier", "ambrette", "cyllage",
    "geosenge", "shalour", "coumarine", "laverre", "dendemille", "anistar", "couriway",
    "snowbelle", "kiloude",
)

def validate_policy(policy: dict) -> tuple[int, int]:
    if policy["schema"] != 1 or policy["phase"] != "KA01" or policy["policy"] != "ORIGINAL_GEOMETRY_EXISTING_KANTO_STYLE":
        raise ValueError("Invalid original terrain policy")
    if (policy["external_install_permissions"] or policy["external_redistribution_permissions"]
            or policy["destination_mapids"] or policy["game_files_written"] is not False):
        raise ValueError("KA01 must not approve imports, allocation, or game writes")
    if policy["tiles"] != "LOCAL_EXISTING_ART_REFERENCE_VERIFY_PER_COMPONENT_IN_KA03":
        raise ValueError("Existing tile references are not a license to redistribute")
    spine = policy["opening_spine"]
    keys = [key for key, _ in spine]
    if (len(keys) != len(set(keys)) or not keys or keys[0] != "VANIVILLE_HOME_UPPER"
            or keys[-2:] != ["SANTALUNE_CITY", "SANTALUNE_GYM"] or "ROUTE_04" in keys):
        raise ValueError("The first authored corridor is incomplete or crosses its scope")
    atlas = (ROOT / "docs/KALOS_KD05_ATLAS_VISUAL_E_TILES_KANTO.md").read_text(encoding="utf8")
    references = [r for _, r in spine if r is not None]
    if references != ["C01", "R01", "C02", "R02", "R03", "C03"] or any(f"| {r} |" not in atlas for r in references):
        raise ValueError("A symbolic area lacks its atlas evidence")
    branches = policy["opening_branches"]
    if branches != [["SANTALUNE_CITY","SANTALUNE_CENTER"]] or branches[0][1] in keys:
        raise ValueError("Opening branch would not have a unique return")
    return len(keys) + len(branches), len(keys) - 1 + len(branches)

def validate(policy: dict, data: bytes) -> dict:
    areas, links = validate_policy(policy)
    p = policy["fire_ash_index"]
    if len(data) != p["bytes"] or len(data) > 1024**2 or hashlib.sha256(data).hexdigest() != p["sha256"]:
        raise ValueError("Candidate index is not the pinned observed metadata")
    index = loads(data)
    if (not isinstance(index, dict) or len(index) != p["catalog_entries"] or
            any(type(k) is not int or k < 1 or not isinstance(v, RubyObject) or v.name != "RPG::MapInfo"
                for k, v in index.items())):
        raise ValueError("Candidate index is not the expected RPG Maker map catalogue")
    labels = [text(v.attrs.get("@name", b"")).casefold() for v in index.values()]
    counts = {key: sum(re.search(r"\b" + key + r"\b", label) is not None for label in labels) for key in CITIES}
    if not counts["santalune"] or not counts["lumiose"] or counts["vaniville"] or counts["aquacorde"]:
        raise ValueError("The scope of the observed candidate names changed; review the evidence")
    return {
        "phase": "KA01", "candidate_status": "DENIED_IMPORT_INDEX_ONLY",
        "candidate_index_sha256": p["sha256"], "candidate_index_entries": len(index),
        "city_label_counts_not_coverage": counts, "external_files_approved": 0,
        "authored_symbolic_areas": areas, "authored_bidirectional_links": links,
        "mapids_allocated": 0, "native_geometry": False, "game_files_written": False,
        "reuse_of_kanto_assets_verified_per_component": False,
    }

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    args = parser.parse_args()
    if args.index.is_symlink() or args.index.stat().st_size > 1024**2:
        raise ValueError("Unsafe index input")
    print(json.dumps(validate(json.loads(POLICY.read_text("utf8")), args.index.read_bytes()),
                     indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
