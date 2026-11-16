"""Private, author-creditable HGSS indoor tile importer for integrated Johto.

The repository deliberately does not redistribute other people's PNGs.
A local .blue-work/johto-hgss-tiles/manifest.json selects exact rectangles
from the author's original sheets, and makes per-tileset RMXP atlases.
No source download, guesswork, automated visual classification or global
Kanto/Hoenn/Decades tileset replacement is ever performed.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from build_johto_elm_lab_v1 import decode_png
from johto_opening import set_tiles
from johto_visual import extend_tileset
from server.ruby_marshal import text

FOLDER = Path(".blue-work/johto-hgss-tiles")
MANIFEST = FOLDER / "manifest.json"
INTERIORS = frozenset(range(674, 700))
VERSION = 1
IDS = ("akizakura16", "donlawride", "sirmalo")
MAX_CHIPS = 256
MAX_PLACEMENTS = 900

# The central source of truth for new/regional interiors is Johto's own
# physical MapIDs; Map700+ is owned by Hoenn in the combined Game.exe.
def map_kind(mid):
    if mid == 674: return "bedroom"
    if mid == 675: return "home"
    if mid == 676: return "lab"
    if mid == 677: return "gym"
    if 678 <= mid <= 680: return "tower"
    if mid in (681, 684): return "center"
    if mid == 685: return "mart"
    if mid in (682, 683, 686, 687, 688, 689, 690, 691): return "house"
    from johto_visual import REGIONAL_INTERIORS
    if mid in REGIONAL_INTERIORS:
        return REGIONAL_INTERIORS[mid][3]
    return None


def private_sources(project: Path):
    """Return (manifest, sources) or (None, {}) if the owner has none."""
    folder = project / FOLDER
    source_manifest = project / MANIFEST
    if not source_manifest.exists():
        return None, {}
    if source_manifest.is_symlink() or folder.is_symlink():
        raise ValueError("Manifesto HGSS privado não pode ser symlink")
    spec = json.loads(source_manifest.read_text("utf-8"))
    if spec.get("schema") != VERSION or not isinstance(spec.get("sources"), dict):
        raise ValueError("Manifesto HGSS privado: schema ou sources inválidos")
    if set(spec["sources"]) - set(IDS):
        raise ValueError("Manifesto HGSS contém fonte não reconhecida")
    result = {}
    for identifier, source in spec["sources"].items():
        if not isinstance(source, dict) or set(source) != {"filename", "sha256", "tile_px", "credit"}:
            raise ValueError("Fonte HGSS exige filename, sha256, tile_px e credit")
        filename = source["filename"]
        if (not isinstance(filename, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}\.png", filename)):
            raise ValueError("Nome de fonte HGSS inválido")
        path = folder / filename
        if path.is_symlink() or not path.is_file() or path.resolve().parent != folder.resolve():
            raise ValueError("Tileset HGSS privado não encontrado: " + filename)
        binary = path.read_bytes()
        if not re.fullmatch(r"[a-f0-9]{64}", str(source["sha256"])) or hashlib.sha256(binary).hexdigest() != source["sha256"]:
            raise ValueError("Checksum HGSS original diferente: " + filename)
        if source["tile_px"] not in (16, 32) or not source["credit"]:
            raise ValueError("Tamanho do tile ou créditos HGSS inválidos")
        w, h, rows = decode_png(binary)
        px = source["tile_px"]
        if w % px or h % px or w > 512 or h > 20000:
            raise ValueError("PNG HGSS deve ser alinhado à grade 16/32 px")
        result[identifier] = (w, h, rows, px, source["credit"], source["sha256"])
    return spec, result


def extract(rows, width, x, y, cell):
    """Copy one genuine donor tile, never resynthesize graphics from prompts."""
    if not isinstance(x, int) or not isinstance(y, int) or x < 0 or y < 0:
        raise ValueError("Coordenada do tile HGSS inválida")
    if x * cell + cell > width or y * cell + cell > len(rows):
        raise ValueError("Tile HGSS fora do PNG original")
    rect = [row[x*cell*4:(x+1)*cell*4] for row in rows[y*cell:(y+1)*cell]]
    if cell == 16:
        rect = [b"".join(pixel*2 for pixel in (row[i:i+4] for i in range(0, len(row), 4)))
                for row in rect for _ in range(2)]
    return rect


def compile_private_art(maps, sets, outputs, read_graphic, project: Path):
    """Inject author-owned tiles ONLY into selected Johto indoor maps.

    Manifest placement: {map: 674 | kind: "house", source: "akizakura16",
    sheet_col: 1, sheet_row: 2, x: 3, y: 4, layer: 2,
    passable: false, priority: 0}. A kind target repeats on all existing
    interiors of the requested kind. No semantic pixel positions are guessed.
    """
    spec, sources = private_sources(project)
    if spec is None:
        return {"status": "no_private_art", "maps": [], "credits": []}
    placements = spec.get("placements")
    if not isinstance(placements, list) or not 0 < len(placements) <= MAX_PLACEMENTS:
        raise ValueError("Nenhum posicionamento HGSS auditado no manifesto privado")
    per_map = {}
    for item in placements:
        if not isinstance(item, dict) or item.get("source") not in sources:
            raise ValueError("Fonte de tile HGSS desconhecida")
        if (("map" in item) == ("kind" in item) or type(item.get("x")) is not int
                or type(item.get("y")) is not int or type(item.get("layer")) is not int
                or item["layer"] not in (0, 1, 2)
                or type(item.get("sheet_col")) is not int
                or type(item.get("sheet_row")) is not int
                or type(item.get("passable")) is not bool
                or type(item.get("priority", 0)) is not int):
            raise ValueError("Posicionamento HGSS inválido")
        if "map" in item:
            targets = [item["map"]] if type(item["map"]) is int else []
        else:
            targets = [mid for mid in INTERIORS if map_kind(mid) == item["kind"]]
        if not targets or any(mid not in INTERIORS or mid not in maps for mid in targets):
            raise ValueError("HGSS deve atuar só em interiores Johto instalados")
        for mid in targets:
            obj = maps[mid]
            a = obj.attrs
            x, y, layer = item["x"], item["y"], item["layer"]
            if not 0 <= x < a["@width"] or not 0 <= y < a["@height"]:
                raise ValueError(f"HGSS Map{mid}: posicionamento fora do mapa")
            if layer == 2 and not item["passable"]:
                event_positions = {(e.attrs["@x"], e.attrs["@y"])
                                   for e in a["@events"].values()}
                if (x, y) in event_positions or (mid == 674 and (x, y) == (6, 7)):
                    raise ValueError(f"HGSS Map{mid}: objeto bloqueia evento/spawn")
            per_map.setdefault(mid, []).append(item)

    # Share a single appended tileset per native source ID, to avoid bloating
    # 20+ independent copies; all source tile references stay unchanged.
    by_native = {}
    for mid in per_map:
        by_native.setdefault(maps[mid].attrs["@tileset_id"], []).append(mid)

    new_assets = {}
    for old_tid, mids in by_native.items():
        orig = sets[old_tid].attrs
        if not orig.get("@tileset_name"):
            raise ValueError("Interior Johto sem tileset nativo")
        original_png = read_graphic("Tilesets", text(orig["@tileset_name"]))
        chips, flags, indexes, updates = [], [], {}, {}
        for mid in mids:
            for item in per_map[mid]:
                source = item["source"]
                width, _, rows, px, _, _ = sources[source]
                key = (source, item["sheet_col"], item["sheet_row"],
                       item["passable"], item.get("priority", 0))
                if key not in indexes:
                    indexes[key] = len(chips)
                    chips.append(extract(rows, width, item["sheet_col"], item["sheet_row"], px))
                    flags.append((0 if item["passable"] else 15, item.get("priority", 0), 0))
                    if len(chips) > MAX_CHIPS:
                        raise ValueError("Muitos tiles HGSS para um tileset")
                updates.setdefault(mid, []).append((item["x"], item["y"], item["layer"], indexes[key]))
        name = f"BLUE_JOHTO_HGSS_PRIVATE_{old_tid}"
        artifact, first = extend_tileset(sets, old_tid, name, original_png, chips, flags)
        new_assets[f"Graphics/Tilesets/{name}.png"] = artifact
        new_tid = len(sets) - 1
        for mid in mids:
            maps[mid].attrs["@tileset_id"] = new_tid
            set_tiles(maps[mid], [(x,y,layer,first+offset)
                                  for x,y,layer,offset in updates[mid]])

    outputs.update(new_assets)
    credits = sorted({source[4] for source in sources.values()})
    return {"status": "private_art_compiled",
            "maps": sorted(per_map),
            "tiles": sum(len(v) for v in by_native.values()),
            "credits": credits,
            "source_digests": {name: source[5] for name, source in sources.items()},
            "manifest_sha256": hashlib.sha256((project / MANIFEST).read_bytes()).hexdigest()}
