"""Trusted install catalog and shared Hoenn manifest format."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = json.loads((ROOT / "data/regions/hoenn-map-catalog.json").read_text("utf-8"))
UPSTREAM = CATALOG["source_commit"]
CATALOG_REVISION = CATALOG["active_revision"]
LEGACY_SOURCE_IDS = frozenset(CATALOG["revisions"]["1"])
MAP_RANGE = range(700, 1000)
INSTALL_STATUS = "INTEGRATED_FILES_READY_FOR_NATIVE_QA"


def approved_source_ids(revision: int) -> frozenset[int]:
    if type(revision) is not int or str(revision) not in CATALOG["revisions"]:
        raise ValueError("Revisão desconhecida do catálogo de Hoenn.")
    source_ids = CATALOG["revisions"][str(revision)]
    if (any(type(source) is not int or source < 1 for source in source_ids) or
            len(source_ids) != len(set(source_ids)) or
            not LEGACY_SOURCE_IDS.issubset(source_ids)):
        raise ValueError("O catálogo de Hoenn não preserva os MapKeys legados.")
    return frozenset(source_ids)


def validate_mapping(maps: dict, expected: frozenset[int]) -> dict[int, int]:
    if (not isinstance(maps, dict) or set(maps) != {str(src) for src in expected} or
            any(type(dest) is not int or dest not in MAP_RANGE for dest in maps.values()) or
            len(set(maps.values())) != len(expected)):
        raise ValueError("Manifesto Hoenn inválido ou mapas remapeados.")
    return {int(source): dest for source, dest in maps.items()}


def validate_manifest(proof: dict) -> dict[int, int]:
    if (not isinstance(proof, dict) or type(proof.get("schema")) is not int or
            proof["schema"] not in (1, 2) or proof.get("region") != "HOENN" or
            proof.get("source_commit") != UPSTREAM or proof.get("status") != INSTALL_STATUS):
        raise ValueError("Manifesto Hoenn inválido ou versão desconhecida.")
    version = proof["schema"]
    expected = LEGACY_SOURCE_IDS if version == 1 else approved_source_ids(proof.get("catalog_revision"))
    maps = validate_mapping(proof.get("maps"), expected)
    if version == 2:
        legacy = validate_mapping(proof.get("legacy_maps"), LEGACY_SOURCE_IDS)
        if any(maps[src] != dest for src, dest in legacy.items()):
            raise ValueError("A migração de Hoenn remapeou um MapID legado.")
    start, town = proof.get("start"), proof.get("town")
    if (start != [maps[8], 25, 6, 2] or
            not isinstance(town, list) or len(town) != 4 or
            not all(type(value) is int for value in start + town) or
            town[0] != maps[7] or min(town[1:3]) < 0 or town[3] not in (2, 4, 6, 8)):
        raise ValueError("Pontos iniciais de Hoenn inválidos.")
    return maps


def marker_bytes(proof: dict) -> dict[str, bytes]:
    maps = validate_manifest(proof)
    version = proof["schema"]
    start, town = proof["start"], proof["town"]
    home = ",".join(map(str, start[:3]))
    rows = [f"BLUE_HOENN_PILOT_V{version}", home]
    rows.extend(f"{source},{dest}" for source, dest in maps.items())
    return {
        "Data/blue-hoenn-start.txt": f"BLUE_HOENN_START_V{version},HOENN,{home}\n".encode("ascii"),
        "Data/blue-hoenn-ready.txt": (
            f"BLUE_HOENN_READY_V{version},{len(maps)},{start[0]},{','.join(map(str, town))}\n"
        ).encode("ascii"),
        "Data/blue-hoenn-pilot.txt": ("\n".join(rows) + "\n").encode("ascii"),
    }


def verify_markers(read, proof: dict, *, compact: bool = True) -> None:
    for name, expected in marker_bytes(proof).items():
        if name.endswith("-pilot.txt") and not compact:
            continue
        raw = read(name)
        if name.endswith("-pilot.txt"):
            entries, wanted = raw.splitlines(), expected.splitlines()
            valid = (entries[:2] == wanted[:2] and len(entries) == len(wanted) and
                     set(entries[2:]) == set(wanted[2:]))
        else:
            valid = raw.strip() == expected.strip()
        if name.endswith("-pilot.txt") and proof["schema"] == 2:
            installed = proof.get("installed_sha256")
            valid = (valid and isinstance(installed, dict) and
                     installed.get(name) == hashlib.sha256(raw).hexdigest())
        if not valid:
            raise ValueError(f"Marcador de Hoenn não corresponde ao manifesto: {name}")
