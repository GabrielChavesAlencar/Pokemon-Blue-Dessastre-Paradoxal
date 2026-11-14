"""Compile author-owned Kanto Full Power rematch PBS without changing source teams.

The source FRLG first-challenge roster remains bit-for-bit unchanged. Only
explicit new versions 100..103 are appended to the isolated Kanto pilot.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

VALID_ID = re.compile(r"^[A-Z][A-Z0-9_]*$")


def full_power_draft(manifest: Path, installed_species: set[str], source_trainers: dict) -> str:
    data = json.loads(manifest.read_text(encoding="utf8"))
    if data.get("version") != 1 or data.get("region") != "KANTO":
        raise ValueError("Invalid Full Power manifest version/region")
    if data.get("full_power_offset") != 100:
        raise ValueError("Full Power version offset must be 100")
    profiles = data.get("teams")
    if not isinstance(profiles, list) or len(profiles) != 15:
        raise ValueError("Kanto Full Power requires 8 gym + 4 Elite + 3 Champion profiles")
    original = {(kind, name, version) for kind, name, version in source_trainers.values()}
    seen = set()
    out = ["# Kanto Full Power. Original first-challenge trainers remain unchanged."]
    for entry in profiles:
        kind, name, base_version = entry["kind"], entry["name"], entry["version"]
        species = entry["species"]
        key = (kind, name, base_version)
        if key in seen or key not in original:
            raise ValueError(f"Full Power profile has no original source team: {key}")
        seen.add(key)
        if (not VALID_ID.fullmatch(kind) or not isinstance(name, str) or
                not name or any(ch in name for ch in "\r\n,[]")):
            raise ValueError(f"Invalid trainer identity {key}")
        if (not isinstance(base_version, int) or not 0 <= base_version <= 3 or
                not isinstance(species, list) or len(species) != 6 or
                len(set(species)) != 6):
            raise ValueError(f"Full Power roster must contain 6 distinct Pokemon: {key}")
        for ident in species:
            if not isinstance(ident, str) or not VALID_ID.fullmatch(ident) or ident not in installed_species:
                raise ValueError(f"Full Power Pokemon unavailable in game catalog: {key}/{ident}")
        version = 100 + base_version
        out.append(f"[BLUE_KANTO_{kind},{name},{version}]")
        # Campaign currently scales actual battle level to player-level x 70%
        # (90% on Master). 70 here provides legal high-level natural moves
        # without imposing a fixed battle level on the rematch.
        out.extend(f"Pokemon = {ident},70" for ident in species)
        out.append("")
    return "\n".join(out) + "\n"
