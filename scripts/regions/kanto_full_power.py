"""Compile author-owned Kanto Full Power rematch PBS without changing source teams.

The original FRLG first-challenge roster remains bit-for-bit unchanged. Only
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
        levels = entry["levels"]
        key = (kind, name, base_version)
        if key in seen or key not in original:
            raise ValueError(f"Full Power profile has no original source team: {key}")
        seen.add(key)
        if (not VALID_ID.fullmatch(kind) or not isinstance(name, str) or
                not name or any(ch in name for ch in "\r\n,[]")):
            raise ValueError(f"Invalid trainer identity {key}")
        if (not isinstance(base_version, int) or not 0 <= base_version <= 3 or
                not isinstance(species, list) or not 5 <= len(species) <= 6 or
                not isinstance(levels, list) or len(levels) != len(species) or
                not all(type(level) is int and 1 <= level <= 100 for level in levels)):
            raise ValueError(f"Full Power canonical roster must have 5-6 valid members: {key}")
        allow_duplicates = entry.get("allow_duplicates") is True
        if (len(set(species)) != len(species)) != allow_duplicates:
            raise ValueError(f"Full Power duplicate-species policy differs from source: {key}")
        if (entry.get("role_at_time") not in ("gym_leader","elite_four","champion") or
                entry.get("source_game") not in ("FRLG","HGSS","LGPE")):
            raise ValueError(f"Full Power game/cargo metadata is missing: {key}")
        for ident in species:
            if not isinstance(ident, str) or not VALID_ID.fullmatch(ident) or ident not in installed_species:
                raise ValueError(f"Full Power Pokemon unavailable in game catalog: {key}/{ident}")
        version = 100 + base_version
        out.append(f"[BLUE_KANTO_{kind},{name},{version}]")
        # Preserve the historical source level in the separate PBS profile.
        # BlueCampaign rescales the effective battle level at runtime.
        out.extend(f"Pokemon = {ident},{level}" for ident, level in zip(species, levels))
        out.append("")
    return "\n".join(out) + "\n"
