"""Cria 3 INTERIORES GEOMÉTRICOS de Johto em nova prévia, sem eventos.

Reaproveita apenas três mapas de interiores, tilesets e PNG já instalados no
Blue. A pessoa que audita confirma cada template/mapa/SHA/destino.
Os interiores clonados NÃO são salas HGSS recriadas: exigem revisão visual,
portas, colisões, NPCs, story e testes antes de qualquer jogabilidade.
Nenhum script é executado e nunca se escreve em game/.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import struct
import sys
import tempfile
from pathlib import Path

from audit_johto import ROOT, checksum, map_files, read_map_data
from stage import serialize
from verify_johto import inspect
from server.ruby_marshal import RubyData, RubyObject, text

DEFAULT_LAYOUTS = ROOT / "data/regions/johto-interior-templates.json"
DEFAULT_PREVIEW = ROOT / ".blue-work/johto-staging"
DEFAULT_OUTPUT = ROOT / ".blue-work/johto-staging-interiors"
REQUIRED = {
    "JOHTO_NEW_BARK_PLAYER_HOME_2F",
    "JOHTO_NEW_BARK_PLAYER_HOME_1F",
    "JOHTO_NEW_BARK_ELM_LAB",
}
SHA = re.compile(r"[0-9a-f]{64}\Z")
SYMBOL = re.compile(r"JOHTO_[A-Z0-9_]{3,70}\Z")
PNG = b"\x89PNG\r\n\x1a\n"


def parse_layouts(path: Path) -> dict:
    if path.is_symlink():
        raise ValueError("Arquivo de layout não pode ser symlink")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if ((data.get("schema"), data.get("region"), data.get("status")) !=
            (1, "JOHTO", "NATIVE_INTERIOR_TEMPLATES_REQUIRE_REAL_REVIEW")):
        raise ValueError("Manifesto de interiores Johto desconhecido")
    rows = data.get("interiors")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("Exigir exatamente os três interiores do núcleo New Bark")
    keys = [row.get("symbol") for row in rows]
    if set(keys) != REQUIRED or len(keys) != len(set(keys)):
        raise ValueError("Os três símbolos de interior precisam ser estáveis")
    return data


def require_png(game: Path, folder: str, name: bytes | str | None) -> None:
    candidate = text(name).strip() if name else ""
    if not candidate:
        return
    if (not re.fullmatch(r"[A-Za-z0-9_ .()\-]{1,100}", candidate)
            or candidate in (".", "..")):
        raise ValueError("Nome de gráfico nativo inseguro: " + candidate)
    path = game / "Graphics" / folder / (candidate + ".png")
    if path.is_symlink() or not path.is_file() or path.read_bytes()[:8] != PNG:
        raise ValueError("Tileset/autotile nativo ausente ou PNG inválido: " + str(path))
    if not path.resolve().is_relative_to(game.resolve()):
        raise ValueError("Gráfico nativo fora do jogo")


def confirm_tile_table(room: RubyObject) -> None:
    width, height = room.attrs.get("@width"), room.attrs.get("@height")
    if (type(width) is not int or type(height) is not int
            or not 5 <= width <= 300 or not 5 <= height <= 300):
        raise ValueError("Dimensões de interior RMXP inválidas")
    table = room.attrs.get("@data")
    if not isinstance(table, RubyData) or table.name != "Table":
        raise ValueError("Template não contém tabela de tiles RMXP")
    raw = table.data
    if len(raw) < 20:
        raise ValueError("Tabela de tiles incompleta")
    dimensions, x, y, z, count = struct.unpack("<5I", raw[:20])
    if (dimensions, x, y, z, count) != (3, width, height, 3, width * height * 3):
        raise ValueError("Tabela de tiles não corresponde à geometria do mapa")
    if len(raw) != 20 + 2 * count:
        raise ValueError("Tamanho da tabela de tiles não confere")


def build(preview: Path, game: Path, output: Path, layouts: dict,
          *, root: Path = ROOT) -> dict:
    root = root.resolve()
    work = (root / ".blue-work").resolve()
    preview, game, output = preview.absolute(), game.absolute(), output.absolute()
    if (preview.is_symlink() or not preview.resolve().is_relative_to(work)
            or output.is_symlink() or not output.resolve().is_relative_to(work)
            or output.resolve() == work or output.exists()
            or output.resolve() == preview.resolve()
            or output.resolve().is_relative_to(preview.resolve())
            or preview.resolve().is_relative_to(output.resolve())):
        raise ValueError("Entrada/saída de interiores deve ser prévia separada e NOVA em .blue-work")
    if game.is_symlink() or game.resolve() != (root / "game").resolve():
        raise ValueError("Templates nativos devem vir somente do game/ local")
    # Checks original provenance and makes sure there are no imported scripts,
    # foreign events or changed native MapInfos/Tilesets.
    validation = inspect(preview, game, root=root)
    if validation["status"] != "STRUCTURAL_PREVIEW_VALIDATED_NOT_PLAYABLE":
        raise ValueError("Preview não auditada")

    stage_file = preview / "johto-stage.json"
    staged = json.loads(stage_file.read_text(encoding="utf-8"))
    digest = staged.get("source_archive_sha256")
    if not isinstance(digest, str) or not SHA.fullmatch(digest):
        raise ValueError("Pacote de Johto sem SHA-256 no staging")
    base_maps = {row["symbol"]: row["destination_id"] for row in staged["maps"]}
    if "JOHTO_NEW_BARK_TOWN" not in base_maps:
        raise ValueError("Necessário mapear New Bark Town primeiro")
    if REQUIRED & set(base_maps):
        raise ValueError("Um interior já existe no Map Pack; não substituir")
    parsed = layouts.get("interiors")
    if (layouts.get("schema"), layouts.get("region"), layouts.get("status")) != (
            1, "JOHTO", "NATIVE_INTERIOR_TEMPLATES_REQUIRE_REAL_REVIEW"):
        raise ValueError("Manifesto de interiores não aprovado para leitura")
    if not isinstance(parsed, list) or len(parsed) != 3 or {
            row.get("symbol") for row in parsed} != REQUIRED:
        raise ValueError("Devem existir exatamente três templates de New Bark")

    native_data = game / "Data"
    native_infos = read_map_data(native_data / "MapInfos.rxdata")
    native_tiles = read_map_data(native_data / "Tilesets.rxdata")
    stage_infos = read_map_data(preview / "Data/MapInfos.rxdata")
    stage_tiles = read_map_data(preview / "Data/Tilesets.rxdata")
    if (not isinstance(native_infos, dict) or not isinstance(stage_infos, dict)
            or not isinstance(native_tiles, list) or not isinstance(stage_tiles, list)):
        raise ValueError("MapInfos ou Tilesets RMXP inválidos")
    reserved = set(native_infos) | set(map_files(native_data)) | set(stage_infos)
    used_source, used_target = set(), set()
    prepared = []
    for row in parsed:
        symbol = row.get("symbol")
        src, did = row.get("native_map_id"), row.get("destination_id")
        if (symbol not in REQUIRED or not isinstance(row.get("display_name"), str)
                or not 6 <= len(row["display_name"]) <= 90
                or type(src) is not int or src not in native_infos
                or src in used_source or type(did) is not int
                or did not in range(600, 1000) or did in reserved
                or did in used_target):
            raise ValueError("Interior sem MapID nativo/destino único auditado: " + str(symbol))
        if (row.get("native_template_reviewed") is not True
                or row.get("room_geometry_reviewed") is not True):
            raise ValueError("Layout nativo ainda não foi inspecionado: " + symbol)
        digest_map = row.get("native_map_sha256")
        source = native_data / f"Map{src:03d}.rxdata"
        if (not isinstance(digest_map, str) or not SHA.fullmatch(digest_map)
                or checksum(source) != digest_map):
            raise ValueError("Template nativo não está pinado por SHA-256: " + symbol)
        raw = read_map_data(source)
        if not isinstance(raw, RubyObject) or raw.name != "RPG::Map":
            raise ValueError("Template de interior não é RPG::Map")
        confirm_tile_table(raw)
        tid = raw.attrs.get("@tileset_id")
        if (type(tid) is not int or tid < 1 or tid >= len(native_tiles)
                or not isinstance(native_tiles[tid], RubyObject)
                or native_tiles[tid].name != "RPG::Tileset"):
            raise ValueError("Tileset nativo inválido para interior: " + symbol)
        tile = native_tiles[tid]
        require_png(game, "Tilesets", tile.attrs.get("@tileset_name"))
        names = tile.attrs.get("@autotile_names", [])
        if not isinstance(names, list):
            raise ValueError("Autotiles nativos inválidos")
        for n in names:
            require_png(game, "Autotiles", n)
        parent = row.get("parent_symbol")
        expected = ("JOHTO_NEW_BARK_PLAYER_HOME_1F"
                    if symbol == "JOHTO_NEW_BARK_PLAYER_HOME_2F"
                    else "JOHTO_NEW_BARK_TOWN")
        if parent != expected or not SYMBOL.fullmatch(parent):
            raise ValueError("Hierarquia de sala incorreta: " + symbol)
        prepared.append((row, raw, tid))
        used_source.add(src)
        used_target.add(did)

    result = copy.deepcopy(staged)
    infos, tiles = copy.deepcopy(stage_infos), copy.deepcopy(stage_tiles)
    remap = {}
    extra = {}
    new_ids = {row["symbol"]: row["destination_id"] for row, _, _ in prepared}
    order = max((x.attrs.get("@order", 0) for x in infos.values()
                 if isinstance(x, RubyObject)), default=0)
    for index, (row, source_room, source_tid) in enumerate(prepared, start=1):
        symbol, did = row["symbol"], row["destination_id"]
        if source_tid not in remap:
            native_tile = copy.deepcopy(native_tiles[source_tid])
            new_tid = len(tiles)
            native_tile.attrs["@id"] = new_tid
            native_tile.attrs["@name"] = (
                b"[Blue Johto interior draft] " + native_tile.attrs.get("@name", b""))
            for key in ("@panorama_name", "@fog_name", "@battleback_name"):
                if key in native_tile.attrs:
                    native_tile.attrs[key] = b""
            tiles.append(native_tile)
            remap[source_tid] = new_tid
        cloned = copy.deepcopy(source_room)
        cloned.attrs["@tileset_id"] = remap[source_tid]
        cloned.attrs["@events"] = {}
        cloned.attrs["@encounter_list"] = []
        cloned.attrs["@autoplay_bgm"] = False
        cloned.attrs["@autoplay_bgs"] = False
        for key in ("@bgm", "@bgs"):
            audio = cloned.attrs.get(key)
            if isinstance(audio, RubyObject):
                audio.attrs["@name"] = b""
        extra[Path("Data") / f"Map{did:03d}.rxdata"] = serialize(cloned)

        parent = row["parent_symbol"]
        native_info = native_infos[row["native_map_id"]]
        if not isinstance(native_info, RubyObject) or native_info.name != "RPG::MapInfo":
            raise ValueError("MapInfo de template não é válido")
        new_info = copy.deepcopy(native_info)
        new_info.attrs["@name"] = ("[Johto draft] " + row["display_name"]).encode("utf-8")
        new_info.attrs["@parent_id"] = new_ids.get(parent, base_maps.get(parent))
        new_info.attrs["@order"] = order + index
        infos[did] = new_info
        result["maps"].append({
            "source_id": None, "destination_id": did,
            "symbol": symbol, "events_imported": 0,
            "tileset_id": remap[source_tid],
            "origin": "BLUE_NATIVE_INTERIOR_TEMPLATE",
            "layout_is_hgss_verified": False,
            "native_map_id": row["native_map_id"],
            "native_map_sha256": row["native_map_sha256"],
        })

    extra[Path("Data/MapInfos.rxdata")] = serialize(infos)
    extra[Path("Data/Tilesets.rxdata")] = serialize(tiles)
    warnings = result.get("warnings", [])
    if not isinstance(warnings, list):
        raise ValueError("Avisos da prévia de Johto inválidos")
    result["warnings"] = warnings
    warnings.append(
        "Three native room GEOMETRY DRAFTS. Not faithful HGSS interiors; "
        "must author tiles, collisions, NPC events, audio and verify in Game.exe.")
    result["status"] = "GEOMETRY_PREVIEW_ONLY"
    result["can_install"] = False
    result["not_playable"] = True
    result["native_interior_geometry_drafts"] = len(prepared)
    extra[Path("johto-stage.json")] = (
        json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".johto-interiors-", dir=output.parent) as temp:
        temp_output = Path(temp) / "preview"
        shutil.copytree(preview, temp_output, symlinks=False)
        for name, content in extra.items():
            file = temp_output / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(content)
        # Reuse the same stage validator after adding the 3 authored rooms.
        proof = inspect(temp_output, game, root=root)
        if proof["maps"] != len(result["maps"]) or proof["events_imported"] != 0:
            raise ValueError("Preview de interiores não passou verificação estrutural")
        if output.exists() or output.is_symlink():
            raise ValueError("Destino já foi criado por outro processo")
        temp_output.rename(output)
    return result


def main(argv=None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--preview", type=Path, default=DEFAULT_PREVIEW)
    cli.add_argument("--game", type=Path, default=ROOT / "game")
    cli.add_argument("--layouts", type=Path, default=DEFAULT_LAYOUTS)
    cli.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = cli.parse_args(argv)
    try:
        layouts = parse_layouts(args.layouts)
        output = build(args.preview, args.game, args.output, layouts)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("[JOHTO][BLOQUEADO] " + str(error), file=sys.stderr)
        return 2
    print("[JOHTO] Prévia de", output["native_interior_geometry_drafts"],
          "interiores Blue nativos; ZERO eventos. NÃO é Johto jogável.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
