"""Build a non-executable Johto geometry preview under .blue-work/ only.

Safe by design:
- Requires a verified archive, pinned source map hashes and frozen slots.
- Copies no source scripts, events, saves or music.
- Never opens game/ for writing and never replaces existing maps.
- Staged MapInfos/Tilesets are merged in memory with native data, not copied
  wholesale from the foreign project.
This is NOT a playable Johto pilot or an installer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

from audit_johto import ROOT, project_data, map_files, read_map_data, checksum
from plan_johto import read_json
from stage import serialize
from server.ruby_marshal import RubyObject, text

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
IMAGE_NAME = re.compile(r"^[\w .()\-]+$", re.UNICODE)
DEST_NAMESPACE = "BLUE_JOHTO_PREVIEW_"


def check_workspace(root: Path, source: Path, game: Path, output: Path, archive: Path):
    work = (root / ".blue-work").resolve()
    source_resolved = source.resolve()
    game_resolved = game.resolve()
    output_resolved = output.resolve()
    archive_resolved = archive.resolve()
    if not work.is_dir():
        raise ValueError("Expected .blue-work workspace")
    if not (source_resolved.is_relative_to(work) and
            archive_resolved.is_relative_to(work) and
            output_resolved.is_relative_to(work) and output_resolved != work):
        raise ValueError("Source, archive and output must be inside .blue-work/")
    if game_resolved != (root / "game").resolve():
        raise ValueError("Base game must be project/game, never a pilot or unknown game")
    if (output.exists() or output.is_symlink() or
            source.is_symlink() or archive.is_symlink() or
            output_resolved.is_relative_to(source_resolved)):
        raise ValueError("Stage requires a NEW output folder and no linked inputs")
    if not archive.is_file():
        raise FileNotFoundError("Original archived map pack is required")
    if not game.is_dir():
        raise FileNotFoundError("Native game/ does not exist; stage cannot replace it")


def stage(*, root: Path, source: Path, game: Path, output: Path,
          manifest_path: Path, audit_path: Path, plan_path: Path,
          archive: Path) -> dict:
    """Create new preview atomically. Only synthetic safe map geometry is staged."""
    root = root.resolve()
    source = source.resolve()
    game = game.resolve()
    output = output.absolute()
    archive = archive.absolute()
    check_workspace(root, source, game, output, archive)
    manifest, report, proposed = (
        read_json(manifest_path), read_json(audit_path), read_json(plan_path))
    pinned = manifest.get("source", {}).get("archive_sha256")
    if (not isinstance(pinned, str) or not re.fullmatch(r"[a-f0-9]{64}", pinned) or
            checksum(archive) != pinned or
            report.get("source_archive_sha256") != pinned or
            report.get("archive_hash_pinned_and_verified") is not True):
        raise ValueError("Original Johto source archive hash is not verified")
    if (proposed.get("schema"), proposed.get("region"),
        proposed.get("status"), proposed.get("can_install")) != (
            1, "JOHTO", "READY_FOR_GEOMETRY_PREVIEW", False):
        raise ValueError("A complete READY_FOR_GEOMETRY_PREVIEW plan is required")
    if manifest.get("mapping_verified") is not True:
        raise ValueError("Johto mapping must be confirmed by source audit")
    selection = manifest.get("maps", {})
    mapping = {int(k): v for k, v in proposed.get("mapping", {}).items()}
    if (not mapping or set(mapping) != {int(k) for k in selection}
            or len(set(mapping.values())) != len(mapping)
            or any(v < 600 or v > 999 for v in mapping.values())):
        raise ValueError("Unsafe or incomplete Johto map allocation")
    if proposed.get("symbols") != selection or (
            proposed.get("source_archive_sha256") != pinned):
        raise ValueError("Johto frozen map symbols or package changed since planning")

    data = project_data(source)
    source_maps = map_files(data)
    source_infos = read_map_data(data / "MapInfos.rxdata")
    source_tiles = read_map_data(data / "Tilesets.rxdata")
    native_data = game / "Data"
    infos_path, tiles_path = native_data / "MapInfos.rxdata", native_data / "Tilesets.rxdata"
    expected_hashes = proposed.get("protected_game_hashes", {})
    if (not isinstance(expected_hashes, dict) or
            expected_hashes.get("Data/MapInfos.rxdata") != checksum(infos_path) or
            expected_hashes.get("Data/Tilesets.rxdata") != checksum(tiles_path)):
        raise ValueError("Native maps or tilesets changed since audit; rebuild baseline")
    dest_infos = read_map_data(infos_path)
    dest_tiles = read_map_data(tiles_path)
    if (not isinstance(dest_infos, dict) or not isinstance(dest_tiles, list)
            or not isinstance(source_infos, dict) or not isinstance(source_tiles, list)):
        raise ValueError("Unsupported RMXP map/tileset representation")
    existing_ids = set(dest_infos)
    existing_ids.update(map_files(native_data))
    if existing_ids & set(mapping.values()):
        raise ValueError("Johto destination MapIDs collide with native/Kanto map IDs")

    original_hashes = proposed.get("source_map_hashes", {})
    if not isinstance(original_hashes, dict) or set(original_hashes) != set(selection):
        raise ValueError("Missing audited source map hashes")
    source_art = data.parent / "Graphics"
    new_tiles = {}
    assets: dict[Path, bytes] = {}
    assets_casefold = set()
    summary = []

    def safe_image(folder: str, source_stem: bytes | str | None) -> bytes:
        stem = text(source_stem).strip() if source_stem else ""
        if not stem:
            return b""
        if not IMAGE_NAME.fullmatch(stem) or stem in (".", ".."):
            raise ValueError("Unsafe Johto graphic filename: " + stem)
        filename = f"{DEST_NAMESPACE}{stem}.png"
        input_file = source_art / folder / (stem + ".png")
        if (input_file.is_symlink() or not input_file.is_file()
                or not input_file.resolve().is_relative_to(source.resolve())):
            raise ValueError("Missing or unsafe Johto graphic: " + str(input_file))
        data_png = input_file.read_bytes()
        if not data_png.startswith(PNG_MAGIC):
            raise ValueError("Invalid PNG in Johto map pack: " + str(input_file))
        relative = Path("Graphics") / folder / filename
        if (game / relative).exists():
            raise ValueError("Johto preview asset clashes with installed game: " + str(relative))
        key = str(relative).casefold()
        if key in assets_casefold and relative not in assets:
            raise ValueError("Case-insensitive Johto graphic collision: " + filename)
        assets_casefold.add(key)
        if relative in assets and assets[relative] != data_png:
            raise ValueError("Conflicting Johto graphics: " + filename)
        assets[relative] = data_png
        return filename[:-4].encode("utf-8")

    for sid, did in sorted(mapping.items(), key=lambda item: item[1]):
        original = source_maps.get(sid)
        if original is None or checksum(original) != original_hashes[str(sid)]:
            raise ValueError("Johto map missing or modified after audit: " + str(sid))
        m = read_map_data(original)
        if not isinstance(m, RubyObject) or m.name != "RPG::Map":
            raise ValueError("Source is not an RMXP map: " + str(sid))
        tid = m.attrs.get("@tileset_id")
        if (type(tid) is not int or tid <= 0 or tid >= len(source_tiles)
                or not isinstance(source_tiles[tid], RubyObject)):
            raise ValueError("Missing Johto source tileset " + str(tid))
        if tid not in new_tiles:
            tile = source_tiles[tid]
            attrs = tile.attrs
            number = len(dest_tiles)
            attrs["@id"] = number
            attrs["@name"] = b"Johto preview " + attrs.get("@name", b"")
            attrs["@tileset_name"] = safe_image("Tilesets", attrs.get("@tileset_name"))
            autotiles = attrs.get("@autotile_names", [])
            if not isinstance(autotiles, list):
                raise ValueError("Johto tileset has invalid autotile list")
            attrs["@autotile_names"] = [safe_image("Autotiles", x) for x in autotiles]
            for name in ("@panorama_name", "@fog_name", "@battleback_name"):
                if name in attrs:
                    attrs[name] = b""
            dest_tiles.append(tile)
            new_tiles[tid] = number

        m.attrs["@tileset_id"] = new_tiles[tid]
        m.attrs["@events"] = {}
        m.attrs["@autoplay_bgm"] = m.attrs["@autoplay_bgs"] = False
        for audio in ("@bgm", "@bgs"):
            current = m.attrs.get(audio)
            if isinstance(current, RubyObject):
                current.attrs["@name"] = b""
        assets[Path("Data") / f"Map{did:03d}.rxdata"] = serialize(m)

        info = source_infos.get(sid)
        if not isinstance(info, RubyObject) or info.name != "RPG::MapInfo":
            raise ValueError("Missing Johto source MapInfo " + str(sid))
        info.attrs["@name"] = b"[Johto preview] " + info.attrs.get("@name", b"")
        info.attrs["@parent_id"] = mapping.get(info.attrs.get("@parent_id"), 0)
        info.attrs["@order"] = max((obj.attrs.get("@order", 0)
                                    for obj in dest_infos.values()), default=0) + 1
        dest_infos[did] = info
        summary.append({"source_id": sid, "destination_id": did,
                        "symbol": selection[str(sid)], "events_imported": 0,
                        "tileset_id": new_tiles[tid]})

    assets[Path("Data/MapInfos.rxdata")] = serialize(dest_infos)
    assets[Path("Data/Tilesets.rxdata")] = serialize(dest_tiles)
    result = {"schema": 1, "region": "JOHTO", "status": "GEOMETRY_PREVIEW_ONLY",
              "not_playable": True, "can_install": False, "maps": summary,
              "native_mapinfos_sha256": expected_hashes["Data/MapInfos.rxdata"],
              "native_tilesets_sha256": expected_hashes["Data/Tilesets.rxdata"],
              "source_archive_sha256": pinned,
              "warnings": ["No foreign events, BGM/ME, switches or transfer events imported",
                           "Do not copy preview into game/ or activate the title until gameplay exists",
                           "Missing interiors and Mt. Silver still require real implementation"]}
    assets[Path("johto-stage.json")] = (json.dumps(result, ensure_ascii=False, indent=2)+"\n").encode()
    assets[Path("LEIA-ME.txt")] = (
        "JOHTO GEOMETRY PREVIEW - not a playable pilot.\n"
        "No event scripts, Pokemon, BGM or save files from the source were imported.\n"
        "DO NOT COPY this folder directly over game/Data.\n"
        "Map art remains subject to original authors' licenses and credits.\n").encode()

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".johto-stage-", dir=output.parent) as work:
        temporary = Path(work) / "preview"
        for relative, blob in assets.items():
            destination = temporary / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(blob)
        if output.exists() or output.is_symlink():
            raise ValueError("Johto stage destination already exists; refusing overwrite")
        temporary.rename(output)
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=ROOT / ".blue-work/johto-source")
    p.add_argument("--game", type=Path, default=ROOT / "game")
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--audit", type=Path, default=ROOT / ".blue-work/johto-audit.json")
    p.add_argument("--plan", type=Path, default=ROOT / ".blue-work/johto-map-plan.json")
    p.add_argument("--manifest", type=Path, default=ROOT / "data/regions/johto-source.json")
    p.add_argument("--output", type=Path, default=ROOT / ".blue-work/johto-staging")
    args = p.parse_args(argv)
    try:
        result = stage(root=ROOT, source=args.source, game=args.game,
                       archive=args.archive, audit_path=args.audit,
                       plan_path=args.plan, manifest_path=args.manifest,
                       output=args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("[JOHTO][BLOQUEADO] " + str(error), file=sys.stderr)
        return 2
    print("[JOHTO] Preview de terreno seguro: %d mapas; ZERO eventos importados." % len(result["maps"]))
    print("[JOHTO] Nenhuma alteracao no game/ principal; Jogabilidade ainda pendente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
