"""Install a genuine 151-species Kanto Regional Pokédex beside the National Dex.

Only the isolated Kanto pilot's PBS is modified. Existing Dex sections keep
their IDs and order. The Blue National species registry is source of truth.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REGIONAL = re.compile(r"^\s*\[(\d+)]\s*(?:#.*)?$")
PBS_ALIASES = {"NIDORANFE": "NIDORANfE", "NIDORANMA": "NIDORANmA"}


def first_151(project: Path):
    data = json.loads((project / "data/national-species.json").read_text("utf8"))
    numbers = {int(n): name for name, n in data.items() if int(n) <= 151}
    if len(numbers) != 151 or set(numbers) != set(range(1, 152)):
        raise ValueError("National species registry does not cover canonical Kanto #001-#151")
    if (numbers[1], numbers[4], numbers[7], numbers[151]) != (
            "BULBASAUR", "CHARMANDER", "SQUIRTLE", "MEW"):
        raise ValueError("Kanto species start/end or starter order is invalid")
    return [PBS_ALIASES.get(numbers[i], numbers[i]) for i in range(1, 152)]


def sections(raw: str):
    found = {}
    current = None
    for line in raw.splitlines():
        label = REGIONAL.fullmatch(line.strip())
        if label:
            current = int(label[1])
            if current in found:
                raise ValueError("Duplicate regional dex section in installed Blue PBS")
            found[current] = []
            continue
        clean = line.split("#", 1)[0].strip()
        if clean and current is not None:
            found[current].extend(p.strip() for p in clean.split(",") if p.strip())
    if found and set(found) != set(range(max(found) + 1)):
        raise ValueError("Installed Blue regional Dex IDs are not contiguous")
    return found


def install_pilot_kantodex(project: Path, target: Path):
    pbs = target / "PBS/regional_dexes.txt"
    raw = pbs.read_text(encoding="utf-8-sig") if pbs.is_file() else ""
    existing = sections(raw)
    species = first_151(project)
    canonical = [s.upper() for s in species]
    match = next((index for index, items in existing.items()
                  if [s.upper() for s in items] == canonical), None)
    added = match is None
    index = len(existing) if added else match
    if added:
        # The final National dex is implicit in Essentials. Never make an
        # extra [National] section or overwrite another regional list.
        addition = "\n".join([f"[{index}]", *species]) + "\n"
        pbs.write_text(raw.rstrip() + ("\n\n" if raw.strip() else "") +
                       "# Blue KantoDex: 151 original Kanto species\n" + addition,
                       encoding="utf-8")
    manifest = {
        "schema": 1, "index": index, "added": added,
        "previous_regional_count": len(existing),
        "length": len(species), "first": species[0], "last": species[-1],
        "national_dex_unchanged": True,
    }
    (target / "Data/blue-kanto-dex.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    # The embedded mkxp Ruby runtime may not ship JSON. Keep a tiny ASCII
    # marker for runtime access; retain JSON for Python audits only.
    (target / "Data/blue-kanto-dex-index.txt").write_text(
        f"{index}|{1 if added else 0}|{len(existing)}\n", encoding="ascii")
    return manifest
