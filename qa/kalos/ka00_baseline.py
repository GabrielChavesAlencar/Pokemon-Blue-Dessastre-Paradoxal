#!/usr/bin/env python3
"""Collect conservative, metadata-only snapshots for Kalos KA00. Never allocate or edit maps."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.regions.audit_unova_a04_mapids import scan_source, sha256_file
from scripts.regions.hoenn_catalog import CATALOG_REVISION, MAP_RANGE, approved_source_ids
from scripts.install_game import BASE_COMMIT
from scripts.regions.k05_contract import published_destinations

KANTO_CELADON_IN_FLIGHT = (276, 277, 278, 279)
ANDROID_247_SHA256 = "0469d877818490a31f6e0a080d8f2d942f954dc65568d5aec38ef3235606f87b"
ANDROID_247_BYTES = 1401504567
ANDROID_247_TAG = "android-multiregion-247-02732ea"
CONTROLS = (
    "scripts/battle_polish/RegionStart.rb", "scripts/battle_polish/RegionTravel.rb",
    "scripts/battle_polish/RegionalRespawn.rb", "scripts/install_game.py",
    "scripts/android/source_update.py", "scripts/android/update_client.py",
    "scripts/regions/k05_contract.py", "scripts/regions/install_kanto.py", "scripts/regions/install_hoenn.py",
    "data/regions/hoenn-map-catalog.json", "data/regions/sinnoh-shared-mapids.json",
    "data/regions/unova-a05-mapid-candidates.json", "site/public/data/regions.json",
)

def document(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def span(start: int, end: int) -> dict:
    return {"start": start, "end": end, "count": end - start + 1}

def static_controls() -> dict:
    catalog = document("site/public/data/regions.json")
    assert catalog["regions"]["KALOS"]["status"] == "planned", "Kalos state changed"
    data = document("data/regions/unova-a05-mapid-candidates.json")
    sinnoh = data["sinnoh_administrative_hold"]
    unova = data["unova_preferred_candidate"]
    assert sinnoh == {**span(442, 517), "not_native_reservation": True}
    assert (unova["start"], unova["end"], unova["count"]) == (518, 599, 82)
    assert data["can_reserve_mapids"] is False and data["current_native_a04_required"] is True
    reservations = document("data/regions/sinnoh-map-id-reservations.json")
    reviewed = {(r["owner"], r["start"], r["end"]) for r in reservations["documented_shared_reservations"]}
    assert ("JOHTO", 600, 699) in reviewed and ("HOENN", 700, 999) in reviewed
    assert (MAP_RANGE.start, MAP_RANGE.stop) == (700, 1000)
    actual_sinnoh = document("data/regions/sinnoh-shared-mapids.json")
    if any(type(n) is not int or not 1 <= n <= 999 for n in actual_sinnoh.values()):
        raise ValueError("Unexpected value in previously installed Sinnoh MapID record")
    return {
        "schema": 1, "phase": "KA00", "mode": "STATIC_PROTECTION_NOT_ALLOCATION",
        "protected": {
            "KANTO_K05_PUBLISHED": sorted(published_destinations().values()),
            "KANTO_CELADON_PR_395_CONSERVATIVE_HOLD": list(KANTO_CELADON_IN_FLIGHT),
            "JOHTO": span(600, 699), "HOENN": span(700, 999),
            "SINNOH_STAGING_HOLD": span(442, 517),
            "SINNOH_MAPPED_DESTINATIONS": sorted(set(actual_sinnoh.values())),
            "UNOVA_CONTIGUOUS_CANDIDATE": span(518, 599),
        },
        "hoenn_current_catalog_revision": CATALOG_REVISION,
        "hoenn_current_catalog_count": len(approved_source_ids(CATALOG_REVISION)),
        "decades_pin": BASE_COMMIT,
        "four_digit_ids_verified": False, "allocation_allowed": False,
        "controls": {name: sha256_file(ROOT / name) for name in CONTROLS},
    }

def ownership(markers: dict, physical: set[int], declared: set[int]) -> dict:
    """The Hoenn H00 ownership rule, extended with explicit missing markers."""
    formats = {
        "blue-kanto-install.json": ("KANTO", "maps"),
        "blue-johto-main-preview.json": ("JOHTO", "map_ids"),
        "blue-johto-install.json": ("JOHTO", "file_hashes"),
        "blue-hoenn-install.json": ("HOENN", "maps"),
        "blue-sinnoh-shared.json": ("SINNOH", "map_ids"),
    }
    present: dict[str, set[int]] = {}
    for name, proof in markers.items():
        if name not in formats:
            continue
        owner, field = formats[name]
        raw = proof.get(field) if isinstance(proof, dict) else None
        if field == "maps" and isinstance(raw, dict):
            values = list(raw.values())
        elif field == "file_hashes" and isinstance(raw, dict):
            values = [int(m[1]) for path in raw if (m := re.fullmatch(r"Data/Map([0-9]{3,})\.rxdata", path))]
        elif field == "map_ids" and isinstance(raw, list):
            values = raw
        else:
            raise ValueError("Malformed regional ownership marker: " + name)
        if not values or any(type(n) is not int or n < 1 for n in values):
            raise ValueError("Invalid ownership IDs: " + name)
        ids = set(values)
        if len(ids) != len(values) or not ids <= (physical & declared):
            raise ValueError("Ownership without a unique physical and indexed map: " + name)
        if any(ids & current for other, current in present.items() if other != owner):
            raise ValueError("Two regional markers share an occupied MapID: " + name)
        present.setdefault(owner, set()).update(ids)
    return {
        "by_region": {name: sorted(ids) for name, ids in present.items()},
        "not_observed": sorted({owner for owner, _ in formats.values()} - present.keys()),
        "unattributed_physical": sorted(physical - set().union(*present.values())),
    }

def read_markers(path: Path, profile: str) -> dict:
    names = (
        "blue-kanto-install.json", "blue-johto-main-preview.json", "blue-johto-install.json",
        "blue-hoenn-install.json", "blue-sinnoh-shared.json",
    )
    if profile == "decades-clean":
        result = {}
        for name in names:
            p = path / "Data" / name
            if p.is_symlink():
                raise ValueError("Unexpected indirect ownership marker")
            if p.is_file():
                if p.stat().st_size > 2 * 1024 * 1024:
                    raise ValueError("Ownership marker too large")
                result[name] = json.loads(p.read_text("utf-8-sig"))
        return result
    result = {}
    with zipfile.ZipFile(path) as archive:
        for name in names:
            try:
                entry = archive.getinfo("Pokemon-Blue-Android/Data/" + name)
            except KeyError:
                continue
            if entry.file_size > 2 * 1024 * 1024:
                raise ValueError("Ownership marker too large")
            result[name] = json.loads(archive.read(entry).decode("utf-8-sig"))
    return result

def file_report(path: Path, profile: str) -> dict:
    if profile == "decades-clean":
        ref = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
        if ref != BASE_COMMIT:
            raise ValueError("Decades checkout is not the exact official commit")
        if path.is_symlink() or not (path / "Game.exe").is_file() or not (path / "PBS/pokemon.txt").is_file():
            raise ValueError("Verified Decades game and PBS are missing")
        proof = {"source_revision": ref,
                 "runtime_sha256": sha256_file(path / "Game.exe"),
                 "tilesets_sha256": sha256_file(path / "Data/Tilesets.rxdata")}
    else:
        if path.is_symlink() or not path.is_file() or path.stat().st_size != ANDROID_247_BYTES:
            raise ValueError("Historical Android fixture byte count mismatch")
        if sha256_file(path) != ANDROID_247_SHA256:
            raise ValueError("Historical Android fixture SHA mismatch")
        proof = {"source_release": ANDROID_247_TAG, "archive_sha256": ANDROID_247_SHA256}
    source = scan_source(path, profile, base=True)
    if not source["mapinfos_present"] or source["file_count"] < 1:
        raise ValueError("Physical map inventory is incomplete")
    ids = source["map_ids_occupied_or_declared"]
    files = {m["id"] for m in source["maps"]}
    declared = set(ids) - set(source["orphan_map_file_ids"])
    tagged = ownership(read_markers(path, profile), files, declared)
    return {
        "schema": 1, "phase": "KA00", "mode": profile, "source_proof": proof,
        "owned": tagged,
        "file_count": source["file_count"], "declared_count": source["mapinfos_declared_count"],
        "mapinfos_sha256": source["mapinfos_sha256"],
        "occupied_or_declared_ids": ids,
        "declared_without_file_ids": source["missing_map_file_ids"],
        "files_absent_from_index_ids": source["orphan_map_file_ids"],
        "map_files_inventory_sha256": hashlib.sha256(
            json.dumps([(m["id"], m["bytes"], m["sha256"]) for m in source["maps"]],
                       separators=(",", ":")).encode()
        ).hexdigest(),
        "fresh_multiregion_verified": False, "physical_phone_tested": False,
        "allocation_allowed": False,
    }

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=("static", "decades-clean", "android-247-historical"))
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()
    if args.profile == "static" and args.input is None:
        result = static_controls()
    elif args.profile != "static" and args.input:
        result = file_report(args.input.absolute(), args.profile)
    else:
        parser.error("An explicit input is mandatory only for physical inventories")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
