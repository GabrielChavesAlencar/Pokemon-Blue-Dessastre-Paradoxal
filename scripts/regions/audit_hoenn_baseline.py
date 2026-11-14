"""Read-only Hoenn source/baseline check; no map allocation or installation."""
from __future__ import annotations

import argparse
import hashlib
import zipfile
import json
import re
from pathlib import Path

from audit_johto import ROOT, checksum, map_files, read_map_data
from prepare_hoenn_source import inspect_zip
from server.ruby_marshal import RubyObject, text

PILOT = {7: "Littleroot", 8: "Casa do jogador", 11: "Laboratório do Birch",
         101: "Rota 101", 12: "Oldale", 13: "Centro Pokémon de Oldale",
         14: "Poké Mart de Oldale", 102: "Rota 102", 103: "Rota 103"}


def inspect_map_data(data: Path) -> tuple[dict, list]:
    infos = read_map_data(data / "MapInfos.rxdata")
    tilesets = read_map_data(data / "Tilesets.rxdata")
    if not isinstance(infos, dict) or not isinstance(tilesets, list):
        raise ValueError("MapInfos/Tilesets incompatíveis com RPG Maker XP")
    return infos, tilesets


def audit(tree_path: Path, source_data: Path, game_data: Path, archive: Path | None = None) -> dict:
    tree = json.loads(tree_path.read_text("utf-8"))
    revision = tree["revision"]
    if tree.get("truncated") is not False or not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("Inventário Git incompleto ou sem revisão fixa")
    known = {row["path"].casefold() for row in tree["tree"] if row.get("type") == "blob"}
    donor = {int(m[1]) for row in tree["tree"]
             if row.get("type") == "blob" and
             (m := re.fullmatch(r"Data/Map(\d+)\.rxdata", row["path"]))}
    files = {row["path"]: row["sha"] for row in tree["tree"] if row.get("type") == "blob"}
    for name in ("MapInfos.rxdata", "Tilesets.rxdata", *(f"Map{i:03}.rxdata" for i in PILOT)):
        raw = (source_data / name).read_bytes()
        git_blob = hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()
        if files.get(f"Data/{name}") != git_blob:
            raise ValueError(f"{name}: arquivo não corresponde à revisão pública registrada")
    infos, tiles = inspect_map_data(source_data)
    if donor != set(infos):
        raise ValueError("MapInfos doador diverge do inventário Git")
    native, _ = inspect_map_data(game_data)
    occupied = set(map_files(game_data)) | set(native)
    pilot = []
    for mid, label in PILOT.items():
        path = source_data / f"Map{mid:03}.rxdata"
        obj = read_map_data(path)
        if (mid not in infos or not isinstance(obj, RubyObject) or obj.name != "RPG::Map"
                or not isinstance(obj.attrs.get("@events"), dict)):
            raise ValueError(f"Mapa piloto ausente ou inválido: {mid}")
        attrs = obj.attrs
        tid = attrs["@tileset_id"]
        if not 0 < tid < len(tiles) or not isinstance(tiles[tid], RubyObject):
            raise ValueError(f"Tileset ausente no mapa piloto: {mid}")
        tile = tiles[tid].attrs
        graphics = [f"Graphics/Tilesets/{text(tile['@tileset_name'])}.png"]
        graphics += [f"Graphics/Autotiles/{text(name)}.png"
                     for name in tile["@autotile_names"] if name]
        pilot.append({
            "source_map_id": mid, "area": label, "source_name": text(infos[mid].attrs["@name"]),
            "dimensions": [attrs["@width"], attrs["@height"]], "source_tileset": tid,
            "source_event_count": len(attrs["@events"]), "sha256": checksum(path),
            "graphics_refs": graphics,
            "graphics_missing_from_tree": [name for name in graphics if name.casefold() not in known],
        })
    original = inspect_zip(archive) if archive else None
    return {
        "schema": 1, "region": "HOENN", "mode": "READ_ONLY",
        "upstream_revision": revision, "source_map_count": len(donor),
        "source_tileset_count": sum(x is not None for x in tiles),
        "source_mapinfos_sha256": checksum(source_data / "MapInfos.rxdata"),
        "source_tilesets_sha256": checksum(source_data / "Tilesets.rxdata"),
        "native_physical_maps": len(map_files(game_data)),
        "native_mapinfos_count": len(native), "native_highest_id": max(occupied),
        "unmapped_collisions": len(occupied & donor),
        "johto_reserved_collision": sorted(occupied & set(range(600, 682))),
        "pilot": pilot, "private_archive_audited": original is not None,
        "private_archive_sha256": original["archive_sha256"] if original else None,
        "distribution_approved": False, "installation_verified": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tree", required=True, type=Path, help="Git tree completo do subdiretório Hoenn")
    p.add_argument("--source-data", required=True, type=Path)
    p.add_argument("--game-data", required=True, type=Path)
    p.add_argument("--archive", type=Path, help="ZIP privado; auditado separadamente da revisão pública")
    args = p.parse_args()
    try:
        print(json.dumps(audit(args.tree, args.source_data, args.game_data, args.archive),
                         ensure_ascii=True, indent=2))
    except (OSError, ValueError, KeyError, TypeError, IndexError, zipfile.BadZipFile) as exc:
        p.exit(2, f"Auditoria bloqueada: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
