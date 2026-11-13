#!/usr/bin/env python3
"""Build Sinnoh GEOMETRY-ONLY previews in ignored .blue-work.

No source event Ruby, NPC, script, encounter, music or save is transferred.
No files in game/ are created, patched, deleted or executed. The preview
contains sanitized maps, local-only tileset/graphics and merged *copies* of
MapInfos/Tilesets, never replacements for the installed Decades project.
Requires an explicit, hash-pinned Sinnoh remap candidate and local game/Data.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

from audit_johto import ROOT
from audit_sinnoh_rxdata import Source, audit_rxdata, attrs, read_marshal
from plan_sinnoh_remap import make_plan, read_object
from server.ruby_marshal import RubyData, RubyObject, text
from sinnoh_staging_transaction import preview, stage
from stage import serialize

GRAPHIC = re.compile(r"[A-Za-z0-9_ .()\-]{1,100}\Z")
PNG = b"\x89PNG\r\n\x1a\n"
TILE_ATTRS = {
    "@id", "@name", "@tileset_name", "@tileset_hue", "@autotile_names",
    "@panorama_name", "@panorama_hue", "@fog_name", "@fog_hue",
    "@fog_opacity", "@fog_blend_type", "@fog_zoom", "@fog_sx",
    "@fog_sy", "@battleback_name", "@passages", "@priorities",
    "@terrain_tags"
}


def fail(message: str):
    raise ValueError("[SINNOH GEOMETRY] " + message)


def table_valid(raw, width: int, height: int) -> bool:
    if not isinstance(raw, RubyData) or raw.name != "Table" or len(raw.data) < 20:
        return False
    dimensions, w, h, z, count = struct.unpack_from("<5I", raw.data)
    return (dimensions == 3 and w == width and h == height and z == 3
            and count == width * height * z
            and len(raw.data) == 20 + count * 2)


def silent_audio():
    return RubyObject("RPG::AudioFile", {
        "@name": b"", "@volume": 80, "@pitch": 100,
    })


def graphic_name(raw) -> str:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="strict")
    if not isinstance(raw, str):
        fail("Nome de gráfico não é texto")
    raw = raw.strip()
    if raw and (not GRAPHIC.fullmatch(raw) or raw in (".", "..")):
        fail("Nome de gráfico inseguro")
    return raw


def safe_source(source: Path, game_data: Path, project: Path):
    source = source.expanduser().absolute()
    game_data = game_data.expanduser().absolute()
    project = project.expanduser().absolute()
    if not project.is_dir() or project.is_symlink():
        fail("Pasta do projeto inválida")
    if not game_data.is_dir() or game_data.is_symlink():
        fail("game/Data real é obrigatório para o baseline")
    if source == project or source == game_data or source == game_data.parent:
        fail("A fonte Sinnoh não pode ser a raiz do projeto ou o jogo principal")
    if game_data in source.parents or game_data.parent in source.parents:
        fail("A fonte Sinnoh não pode estar dentro de game/")
    if source.is_dir() and source in game_data.parents:
        fail("A fonte Sinnoh não pode incluir game/Data")
    if not game_data.resolve().is_relative_to(project.resolve()):
        fail("game/Data deve pertencer à instalação local informada")
    return source, game_data, project


def validate_plan_against_source(source: Path, game_data: Path, candidate: dict,
                                 audit: dict) -> dict[int, int]:
    if (candidate.get("schema"), candidate.get("region"), candidate.get("mode"),
            candidate.get("can_install"),
            candidate.get("may_stage_real_map_data")) != (
                1, "SINNOH", "REMAP_CANDIDATE_ONLY", False, False):
        fail("Plano não é candidato Sinnoh exclusivamente de leitura")
    request = {
        "schema": 1, "region": "SINNOH",
        "source_zip_sha256": candidate.get("source_zip_sha256"),
        "source_mapinfos_sha256": candidate.get("source_mapinfos_sha256"),
        "source_tilesets_sha256": candidate.get("source_tilesets_sha256"),
        "source_map_hashes": candidate.get("source_map_hashes"),
        "mapping": candidate.get("mapping"),
        "symbols": candidate.get("symbols"),
    }
    verified = make_plan(audit, request, reserved={
        "schema": 1, "region": "SINNOH",
        "protected_ids": candidate.get("other_region_reservations_listed"),
    })
    if verified["plan_sha256"] != candidate.get("plan_sha256"):
        fail("Plano modificado ou baseline da fonte/instalação mudou")
    if verified["mapping"] != candidate.get("mapping"):
        fail("Destinos alterados após auditoria")
    # These are CANDIDATE IDs; uninstalled Hoenn reservations still matter.
    return {int(k): value for k, value in verified["mapping"].items()}


def build_geometry(source: Path, game_data: Path, candidate: dict,
                   *, project: Path = ROOT) -> tuple[dict[str, bytes], dict]:
    """In-memory ONLY; no side effects on the source, game or workspace."""
    source, game_data, project = safe_source(source, game_data, project)
    audit = audit_rxdata(source, game_data)
    remap = validate_plan_against_source(source, game_data, candidate, audit)
    infos_path = game_data / "MapInfos.rxdata"
    tiles_path = game_data / "Tilesets.rxdata"
    if infos_path.is_symlink() or tiles_path.is_symlink():
        fail("Dados nativos não podem ser symlinks")
    infos_raw, tiles_raw = infos_path.read_bytes(), tiles_path.read_bytes()
    native_infos = read_marshal(infos_raw, "game/MapInfos.rxdata")
    native_tiles = read_marshal(tiles_raw, "game/Tilesets.rxdata")
    if (not isinstance(native_infos, dict)
            or any(type(mid) is not int or mid < 1 or
                   not isinstance(info, RubyObject) or info.name != "RPG::MapInfo"
                   for mid, info in native_infos.items())
            or not isinstance(native_tiles, list)):
        fail("MapInfos/Tilesets nativos incompatíveis")
    if len(native_tiles) > 5000:
        fail("Há tilesets demais; revisar capacidade com Codex")
    # Recheck native files against audit/map plan; staging never writes them.
    physical = set(audit["native"]["occupied_ids"])
    if any(destination in physical for destination in remap.values()):
        fail("MapID escolhido colide com MapInfos ou mapa físico nativo")

    output_infos = copy.deepcopy(native_infos)
    output_tiles = copy.deepcopy(native_tiles)
    blobs: dict[str, bytes] = {}
    tileset_map: dict[int, int] = {}
    graphic_map: dict[str, str] = {}
    original_mapinfos_hash = hashlib.sha256(infos_raw).hexdigest()
    original_tilesets_hash = hashlib.sha256(tiles_raw).hexdigest()
    max_order = max((
        attrs(info).get("@order", 0)
        for info in output_infos.values()
        if type(attrs(info).get("@order", 0)) is int
    ), default=0)

    with Source(source) as donor:
        source_infos = read_marshal(donor.read("Data/MapInfos.rxdata"), "donor MapInfos")
        source_tiles = read_marshal(donor.read("Data/Tilesets.rxdata"), "donor Tilesets")
        if not isinstance(source_infos, dict) or not isinstance(source_tiles, list):
            fail("MapInfos/Tilesets da fonte não suportam esta prévia")
        paths = donor.map_paths()

        def copy_graphic(folder: str, name_obj) -> bytes:
            name = graphic_name(name_obj)
            if not name:
                return b""
            rel = f"Graphics/{folder}/{name}.png"
            raw = donor.read(rel)
            if not raw.startswith(PNG):
                fail(f"{rel}: não é PNG compatível")
            original_hash = hashlib.sha256(raw).hexdigest()
            if rel not in graphic_map:
                new_name = f"SN_Preview_{original_hash[:12]}_{name[:65]}"
                output_file = f"Graphics/{folder}/{new_name}.png"
                if output_file in blobs and blobs[output_file] != raw:
                    fail("Nome de PNG de prévia colidiu")
                blobs[output_file] = raw
                graphic_map[rel] = new_name
            return graphic_map[rel].encode("utf-8")

        for sid, did in sorted(remap.items()):
            raw = donor.read(paths[sid])
            if hashlib.sha256(raw).hexdigest() != candidate["source_map_hashes"][str(sid)]:
                fail(f"Hash da origem Map{sid} mudou durante conversão")
            source_map = read_marshal(raw, f"donor Map{sid}")
            if not isinstance(source_map, RubyObject) or source_map.name != "RPG::Map":
                fail("Map da fonte não é RPG::Map")
            props = attrs(source_map)
            width, height, old_tile = (
                props.get("@width"), props.get("@height"), props.get("@tileset_id"))
            if any(type(v) is not int for v in (width, height, old_tile)):
                fail(f"Mapa {sid} com dimensões/tile inválidos")
            if not (1 <= width <= 500 and 1 <= height <= 500 and old_tile > 0):
                fail(f"Mapa {sid} fora do limite de dimensão")
            if not table_valid(props.get("@data"), width, height):
                fail(f"Map{sid}: tabela de terreno ausente/corrompida")
            if old_tile not in tileset_map:
                if not 0 < old_tile < len(source_tiles):
                    fail(f"Map{sid}: tileset da origem inexistente")
                old_tile_obj = source_tiles[old_tile]
                if not isinstance(old_tile_obj, RubyObject) or old_tile_obj.name != "RPG::Tileset":
                    fail(f"Map{sid}: classe de tileset inválida")
                original_attrs = attrs(old_tile_obj)
                for item in ("@tileset_name", "@autotile_names"):
                    if item not in original_attrs:
                        fail(f"Map{sid}: tileset não possui {item}")
                if not isinstance(original_attrs["@autotile_names"], list):
                    fail(f"Map{sid}: autotiles inválidos")
                new_id = len(output_tiles)
                if new_id > 9999:
                    fail("Limite de tilesets da prévia excedido")
                new_attrs = {
                    key: copy.deepcopy(value) for key, value in original_attrs.items()
                    if key in TILE_ATTRS
                }
                new_attrs["@id"] = new_id
                new_attrs["@name"] = b"Sinnoh geometry preview"
                new_attrs["@tileset_name"] = copy_graphic(
                    "Tilesets", original_attrs["@tileset_name"])
                new_attrs["@autotile_names"] = [
                    copy_graphic("Autotiles", value)
                    for value in original_attrs["@autotile_names"]
                ]
                for setting in ("@panorama_name", "@fog_name", "@battleback_name"):
                    new_attrs[setting] = b""
                output_tiles.append(RubyObject("RPG::Tileset", new_attrs))
                tileset_map[old_tile] = new_id
            new_map = RubyObject("RPG::Map", {
                "@tileset_id": tileset_map[old_tile],
                "@width": width, "@height": height,
                "@autoplay_bgm": False, "@bgm": silent_audio(),
                "@autoplay_bgs": False, "@bgs": silent_audio(),
                "@encounter_list": [], "@encounter_step": 30,
                "@data": copy.deepcopy(props["@data"]),
                "@events": {},
            })
            map_name = text(attrs(source_infos.get(sid)).get("@name", b""))
            new_info = RubyObject("RPG::MapInfo", {
                "@name": ("[Sinnoh geometry] " + map_name[:100]).encode("utf-8"),
                "@parent_id": 0, "@order": max_order + sid,
                "@expanded": False, "@scroll_x": 0, "@scroll_y": 0,
            })
            output_infos[did] = new_info
            data_file = f"Data/Map{did:03d}.rxdata"
            blobs[data_file] = serialize(new_map)
            # Check source-origin events are NEVER present in the serialized map.
            parsed = read_marshal(blobs[data_file], data_file)
            if attrs(parsed).get("@events") != {}:
                fail("Mapa de prévia contém eventos doadores por acidente")

        blobs["Data/MapInfos.rxdata"] = serialize(output_infos)
        blobs["Data/Tilesets.rxdata"] = serialize(output_tiles)

    if hashlib.sha256(infos_path.read_bytes()).hexdigest() != original_mapinfos_hash:
        fail("Game/MapInfos mudou durante o preparo: abortar")
    if hashlib.sha256(tiles_path.read_bytes()).hexdigest() != original_tilesets_hash:
        fail("Game/Tilesets mudou durante o preparo: abortar")

    result = {
        "schema": 1, "region": "SINNOH",
        "mode": "LOCAL_GEOMETRY_ONLY_INERT_PREVIEW",
        "plan_sha256": candidate["plan_sha256"],
        "maps_staged_in_memory": len(remap),
        "tilesets_prepared": len(tileset_map),
        "graphics_prepared": len(graphic_map),
        "static_transfers_rewritten": 0,
        "donor_events_imported": 0,
        "trainers_or_encounters_imported": 0,
        "donor_audio_imported": 0,
        "source_script_commands_executed": 0,
        "native_data_before_sha256": {
            "MapInfos": original_mapinfos_hash, "Tilesets": original_tilesets_hash},
        "writes_to_game_or_saves": False,
        "runtime_playable": False,
        "rights_verified": False,
        "blocked_until_codex": [
            "Verificar autorização/licença de cada imagem e mapa antes de distribuir",
            "Auditar reservas de IDs planejadas em Johto/Hoenn que não estão no jogo local",
            "Criar somente eventos próprios do Blue em posições reais conferidas",
            "Executar testes de colisão, walkability, portais, NPCs e save/load no Game.exe",
        ],
    }
    return blobs, result


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--source", required=True, type=Path, help="RMXP ZIP/pasta legítima")
    cli.add_argument("--game-data", required=True, type=Path, help="game/Data local")
    cli.add_argument("--plan", required=True, type=Path, help="Remap candidato com hashes")
    cli.add_argument("--label", default="geometry", help="Tag privada da prévia")
    cli.add_argument("--stage", action="store_true",
                     help="Criar só uma pasta nova dentro de .blue-work/sinnoh-stage/")
    cli.add_argument("--expected-dry-run", help="Hash de dry-run a confirmar para stage")
    args = cli.parse_args(argv)
    try:
        plan = json.loads(args.plan.read_text("utf-8-sig"))
        files, report = build_geometry(args.source, args.game_data, plan)
        dry = preview(ROOT, args.label, files)
        if args.stage:
            if not args.expected_dry_run:
                fail("Use --expected-dry-run do primeiro dry-run antes de --stage")
            record = stage(ROOT, args.label, files, args.expected_dry_run)
        else:
            if args.expected_dry_run:
                fail("Não forneça --expected-dry-run sem --stage")
            record = dry
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        print("SINNOH_GEOMETRY_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({**report, "transaction": record},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
