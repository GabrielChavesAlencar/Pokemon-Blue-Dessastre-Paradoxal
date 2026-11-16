"""Versioned, event-preserving Johto map TILE edits.

Only JSON patches belong in GitHub. Native RXDATA/graphics/Saves remain local.
The same patch is used when constructing Johto from OFFLINE12 and when
refreshing an already installed Blue-Story Game.exe.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from build_johto_elm_lab_v1 import table_values
from johto_opening import set_tiles
from server.ruby_marshal import RubyObject, text

REGION_IDS = frozenset(range(600, 700))
SCHEMA = 1
MAX_EDITS = 9000
RELATIVE = Path("data/regions/johto-map-edits")


class PatchError(ValueError):
    pass


def map_id(value):
    if type(value) is not int or value not in REGION_IDS:
        raise PatchError("Somente mapas Johto Map600–Map699 podem ser editados")
    return value


def patch_path(project: Path, mid: int):
    return Path(project) / RELATIVE / f"Map{map_id(mid):03}.json"


def digest(raw: bytes):
    return hashlib.sha256(raw).hexdigest()


def read_patch(project: Path, mid: int):
    path = patch_path(project, mid)
    if not path.is_file():
        return None
    if path.is_symlink() or path.stat().st_size > 800_000:
        raise PatchError("Patch de Johto inválido ou grande demais")
    return validate_patch_format(json.loads(path.read_text("utf-8")), mid)


def validate_patch_format(data: dict, mid: int):
    mid = map_id(mid)
    if not isinstance(data, dict) or data.get("schema") != SCHEMA or data.get("map_id") != mid:
        raise PatchError("Formato ou MapID do patch Johto inválido")
    name = data.get("tileset")
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_ ().-]{1,120}", name):
        raise PatchError("Nome do tileset Johto inválido")
    rows = data.get("edits")
    if not isinstance(rows, list) or len(rows) > MAX_EDITS:
        raise PatchError("Número de alterações Johto inválido")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"x", "y", "z", "before", "after"}:
            raise PatchError("Patch Johto exige x,y,z,before,after")
        if any(type(row[k]) is not int for k in row):
            raise PatchError("Coordenadas/tiles devem ser inteiros")
        if not (0 <= row["x"] < 300 and 0 <= row["y"] < 300
                and 0 <= row["z"] < 3 and 0 <= row["before"] <= 65535
                and 0 <= row["after"] <= 65535):
            raise PatchError("Alteração Johto fora dos limites")
        key = row["x"], row["y"], row["z"]
        if key in seen or row["before"] == row["after"]:
            raise PatchError("Patch Johto duplicado ou sem mudança")
        seen.add(key)
    return data


def encode_patch(data: dict) -> bytes:
    data = validate_patch_format(data, data["map_id"])
    return (json.dumps(data, ensure_ascii=False, sort_keys=True,
                       indent=2) + "\n").encode("utf-8")


def _protected_positions(map_obj, mid):
    protected = {(6, 7)} if mid == 674 else set()
    for event in map_obj.attrs.get("@events", {}).values():
        if not isinstance(event, RubyObject):
            raise PatchError("Evento desconhecido no mapa Johto")
        protected.add((event.attrs.get("@x"), event.attrs.get("@y")))
        for page in event.attrs.get("@pages", []):
            for command in page.attrs.get("@list", []):
                if command.attrs.get("@code") != 201:
                    continue
                vals = command.attrs.get("@parameters", [])
                if len(vals) >= 4 and vals[0] == 0 and vals[1] == mid:
                    protected.add((vals[2], vals[3]))
    return protected


def inspect_map(map_obj, tilesets, mid):
    map_id(mid)
    if not isinstance(map_obj, RubyObject) or map_obj.name != "RPG::Map":
        raise PatchError("Map Johto não é um arquivo RPG::Map válido")
    a = map_obj.attrs
    tid = a.get("@tileset_id")
    if not isinstance(tilesets, list) or type(tid) is not int or not 0 < tid < len(tilesets):
        raise PatchError("Índice do tileset Johto inválido")
    tileset = tilesets[tid]
    if not isinstance(tileset, RubyObject):
        raise PatchError("Tileset Johto inválido")
    name = text(tileset.attrs.get("@tileset_name"))
    (width, height, depth), cells = table_values(a["@data"].data, 3)
    if (width, height, depth) != (a["@width"], a["@height"], 3):
        raise PatchError("Dimensões nativas do mapa divergentes")
    _, flags = table_values(tileset.attrs["@passages"].data, 1)
    return name, width, height, list(cells), flags


def apply_patch(map_obj, tilesets, mid: int, patch: dict):
    """Idempotent. Refuse cells that other changes edited since the patch base."""
    data = validate_patch_format(patch, mid)
    name, w, h, cells, flags = inspect_map(map_obj, tilesets, mid)
    if data["tileset"] != name:
        raise PatchError(f"Map{mid}: tileset alterado, patch não aplicado ({name})")
    protected = _protected_positions(map_obj, mid)
    changes = []
    for item in data["edits"]:
        x, y, z = item["x"], item["y"], item["z"]
        if x >= w or y >= h:
            raise PatchError(f"Map{mid}: coordenada fora do tamanho do mapa")
        old, new = item["before"], item["after"]
        if new >= len(flags) and new != 0:
            raise PatchError(f"Map{mid}: tile não existe nesse tileset: {new}")
        if (x, y) in protected and new and (flags[new] & 15) == 15:
            raise PatchError(f"Map{mid}: tile sólido bloquearia spawn/evento/warp em {x},{y}")
        index = x + w * (y + h * z)
        current = cells[index]
        if current == new:
            continue
        if current != old:
            raise PatchError(f"Map{mid} célula {x},{y},{z}: conflito (atual={current}, esperado={old})")
        changes.append((x, y, z, new))
    if changes:
        set_tiles(map_obj, changes)
    return len(changes)


def apply_project_patches(maps: dict, tilesets: list, project: Path):
    """Use inside Johto builder AFTER map repairs/HGSS import, BEFORE serializing."""
    report = {}
    for mid in sorted(REGION_IDS.intersection(maps)):
        patch = read_patch(project, mid)
        if patch:
            report[mid] = apply_patch(maps[mid], tilesets, mid, patch)
    return report
