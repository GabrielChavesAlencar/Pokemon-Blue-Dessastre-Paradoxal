#!/usr/bin/env python3
"""Fase jogável Hoenn 01/12: prepare/audit an isolated 199-map test copy.

Never writes into the original Blue game or publishes any third-party assets.
All donor files must match the pinned public Git tree byte-for-byte.
An installed directory is NOT proof of compilation or playable Game.exe.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

from prepare_hoenn_source import inspect_zip
from pilot_hoenn import BGM, PNG, PROFILE, ROOT, SOURCE_MAPS, Source, UPSTREAM, stage
from server.ruby_marshal import RubyObject, loads, text

# The Hoenn subdirectory tree, not the whole repository's root tree.
PINNED_TREE = "c3876ecea7545eb3a91b9c8748d7e2b13f07805d"
TREE_URL = ("https://api.github.com/repos/SocomSeal/The-PMon-World-Project/"
            "git/trees/" + PINNED_TREE + "?recursive=1")
WORK = ROOT / ".blue-work"
EXPECTED_MAPS = 199
PINNED_MAPINFOS_SHA256 = "7a69152de41a8b70df3199182e09d04e2f1be2db73a2ab509137571e4d8ade15"
PINNED_TILESETS_SHA256 = "6812832c71da1b6b27585f45212135afcd74bd578e5127caa4d5296ee1126a9b"


def require_private_path(path: Path, *, work: Path = WORK) -> Path:
    """All generated reports, copies and inventory stay within ignored .blue-work."""
    absolute = path.absolute()
    sandbox = work.absolute()
    if not absolute.is_relative_to(sandbox) or absolute == sandbox:
        raise ValueError("Saída e relatórios devem ficar dentro de .blue-work/ (não em game/)")
    for item in (sandbox, *absolute.parents, absolute):
        if item.is_symlink():
            raise ValueError(f"Link simbólico não permitido para saída: {item}")
    return absolute


def check_tree(tree: dict) -> dict:
    if (not isinstance(tree, dict) or tree.get("revision") != UPSTREAM or
            tree.get("sha") != PINNED_TREE or tree.get("truncated") is not False or
            not isinstance(tree.get("tree"), list)):
        raise ValueError("Inventário Git incompleto ou diferente da revisão Hoenn fixa")
    blobs = {}
    for row in tree["tree"]:
        if row.get("type") != "blob":
            continue
        path, sha = row.get("path"), row.get("sha")
        if not isinstance(path, str) or not re.fullmatch(r"[a-f0-9]{40}", str(sha)):
            raise ValueError("Inventário Git inclui blob inválido")
        if path in blobs:
            raise ValueError("Inventário contém arquivo repetido")
        blobs[path] = sha
    needed = {f"Data/Map{mid:03}.rxdata" for mid in SOURCE_MAPS}
    needed.update(("Data/MapInfos.rxdata", "Data/Tilesets.rxdata", "PBS/map_connections.txt"))
    needed.update(f"Audio/BGM/ORAS {track}.ogg" for track in BGM.values())
    missing = sorted(needed - set(blobs))
    if missing:
        raise ValueError(f"Revisão Hoenn sem {len(missing)} recursos exigidos: {missing[:7]}")
    if len(SOURCE_MAPS) != EXPECTED_MAPS:
        raise ValueError(f"Gerador não contém {EXPECTED_MAPS} mapas ({len(SOURCE_MAPS)})")
    return {"revision": UPSTREAM, "tree_sha": PINNED_TREE,
            "source_maps": EXPECTED_MAPS, "required_pinned_files": len(needed),
            "git_blob_files": len(blobs)}


def load_tree(path: Path, *, offline: bool = False) -> dict:
    if path.is_symlink():
        raise ValueError("Inventário por link simbólico não é permitido")
    if path.exists():
        tree = json.loads(path.read_text("utf-8"))
    else:
        if offline:
            raise FileNotFoundError(f"Inventário fixo não encontrado offline: {path}")
        req = Request(TREE_URL, headers={"Accept": "application/vnd.github+json",
                                         "User-Agent": "Blue-Hoenn-Stage1-ReadOnly"})
        with urlopen(req, timeout=90) as response:
            tree = json.load(response)
        if not isinstance(tree, dict):
            raise ValueError("Resposta de árvore Git inválida")
        tree["revision"] = UPSTREAM
        check_tree(tree)  # Do NOT cache untrusted or truncated inventory.
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(tree, ensure_ascii=False), encoding="utf-8")
    check_tree(tree)
    return tree


def check_game(game: Path) -> dict:
    if game.is_symlink() or not game.is_dir():
        raise ValueError("Pasta game/ original não existe ou é link simbólico")
    required = (
        "Game.exe", "Game.ini", "mkxp.json", "Data/Scripts.rxdata",
        "Data/System.rxdata", "Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
        "Plugins/ZZZZ Blue Story and Presentation/RegionStart.rb",
    )
    missing = [rel for rel in required if not (game / rel).is_file()]
    if missing:
        raise ValueError(f"Blue base incompleta, sem: {missing}")
    if not list((game / "PBS").glob("trainers*.txt")):
        raise ValueError("Não foi localizado PBS/trainers*.txt no Blue original")
    if not list((game / "PBS").glob("trainer_types*.txt")):
        raise ValueError("Não foi localizado PBS/trainer_types*.txt no Blue original")
    info = loads((game / "Data/MapInfos.rxdata").read_bytes())
    if not isinstance(info, dict):
        raise ValueError("MapInfos.rxdata base inválido")
    from pilot_hoenn import preflight_route102_trainers
    preflight_route102_trainers(game)
    used = {int(match[1]) for f in (game / "Data").iterdir()
            if (match := re.fullmatch(r"Map(\d+)\.rxdata", f.name, re.I))}
    used.update(info)
    for path in (game / "PBS").glob("*.txt"):
        body = path.read_text("utf-8-sig")
        if path.stem.startswith(("encounters", "map_metadata")):
            used.update(int(m[1]) for m in re.finditer(r"(?m)^\s*\[(\d+)", body))
        elif path.stem.startswith("map_connections"):
            for row in body.splitlines():
                fields = row.split("#", 1)[0].split(",")
                if len(fields) == 6:
                    used.update(int(fields[i]) for i in (0, 3)
                                if fields[i].strip().isdecimal())
    free = [n for n in range(700, 1000) if n not in used and n not in range(600, 682)]
    if len(free) < EXPECTED_MAPS:
        raise ValueError(f"Somente {len(free)} MapIDs livres (necessários: {EXPECTED_MAPS})")
    return {"native_mapinfo_entries": len(info), "free_pilot_mapids": len(free),
            "required_free_mapids": EXPECTED_MAPS,
            "game_exe_present": True, "game_exe_tested": False}


def check_source(source: Source) -> dict:
    """Read actual pinned bytes, including every RXDATA and its image/audio deps."""
    infos = source.read("Data/MapInfos.rxdata")
    tiles_blob = source.read("Data/Tilesets.rxdata")
    if hashlib.sha256(infos).hexdigest() != PINNED_MAPINFOS_SHA256:
        raise ValueError("MapInfos não corresponde ao SHA-256 auditado")
    if hashlib.sha256(tiles_blob).hexdigest() != PINNED_TILESETS_SHA256:
        raise ValueError("Tilesets não corresponde ao SHA-256 auditado")
    map_infos, tiles = loads(infos), loads(tiles_blob)
    if not isinstance(map_infos, dict) or not isinstance(tiles, list):
        raise ValueError("RXDATA de origem possui estrutura inválida")
    used_tiles, images = set(), set()
    for mid in SOURCE_MAPS:
        if mid not in map_infos:
            raise ValueError(f"MapInfos de Hoenn não contém Map{mid:03}")
        obj = loads(source.read(f"Data/Map{mid:03}.rxdata"))
        if not isinstance(obj, RubyObject) or obj.name != "RPG::Map":
            raise ValueError(f"Map{mid:03} não é RPG::Map")
        tid = obj.attrs["@tileset_id"]
        if not isinstance(tid, int) or not (0 < tid < len(tiles)) or tiles[tid] is None:
            raise ValueError(f"Tileset doador inválido: mapa {mid}, tileset {tid}")
        used_tiles.add(tid)
    for tid in used_tiles:
        ts = tiles[tid]
        if not isinstance(ts, RubyObject):
            raise ValueError(f"Tileset {tid} não é RPG::Tileset")
        tile_name = text(ts.attrs["@tileset_name"])
        names = [("Tilesets", tile_name)] if tile_name else []
        names.extend(("Autotiles", text(name)) for name in ts.attrs["@autotile_names"] if name)
        for folder, name in names:
            if not re.fullmatch(r"[A-Za-z0-9_ ()-]+", name):
                raise ValueError(f"Gráfico de origem incompatível no tileset {tid}: {name}")
            rel = f"Graphics/{folder}/{name}.png"
            if rel in images:
                continue
            if not source.read(rel).startswith(PNG):
                raise ValueError(f"PNG fonte inválido: {rel}")
            images.add(rel)
    source.read("PBS/map_connections.txt")
    for label, track in BGM.items():
        rel = f"Audio/BGM/ORAS {track}.ogg"
        if not source.read(rel).startswith(b"OggS"):
            raise ValueError(f"BGM de Hoenn inválida: {label}")
    return {"real_map_rxdata_hashes_verified": EXPECTED_MAPS,
            "source_tilesets_used": len(used_tiles),
            "source_graphics_hashes_verified": len(images),
            "source_bgm_hashes_verified": len(BGM),
            "native_events_executed": False,
            "redistribution_approved": False}


def verify_copy(output: Path, game: Path) -> dict:
    if output.is_symlink() or not output.is_dir():
        raise ValueError(f"Cópia de Hoenn não encontrada: {output}")
    path = output / "Hoenn pilot.json"
    report = json.loads(path.read_text("utf-8"))
    maps = report.get("maps", {})
    expected_profiles = {
        "hoenn-qa-fase04": "Hoenn QA Fase04",
        "hoenn-qa-fase05": "Hoenn QA Fase05",
        "hoenn-qa-fase06": "Hoenn QA Fase06",
    }
    expected_profile = expected_profiles.get(output.name, PROFILE)
    if (report.get("kind") != "ISOLATED_HOENN_TEST" or
            report.get("source_commit") != UPSTREAM or
            report.get("save_profile") != expected_profile or
            len(maps) != EXPECTED_MAPS or
            set(maps) != {str(mid) for mid in SOURCE_MAPS}):
        raise ValueError("Relatório da cópia não corresponde ao piloto de 199 mapas")
    ids = list(maps.values())
    if len(set(ids)) != EXPECTED_MAPS or not all(isinstance(n, int) and 700 <= n <= 999 for n in ids):
        raise ValueError("MapIDs remapeados inválidos ou duplicados")
    missing = [n for n in ids if not (output / f"Data/Map{n:03}.rxdata").is_file()]
    if missing:
        raise ValueError(f"Cópia sem {len(missing)} mapas remapeados, exemplos: {missing[:8]}")
    marker = (output / "Data/blue-hoenn-pilot.txt").read_text("ascii").splitlines()
    expected = {f"{old},{maps[str(old)]}" for old in SOURCE_MAPS}
    if marker[0] != "BLUE_HOENN_PILOT_V1" or set(marker[2:]) != expected:
        raise ValueError("Marcador dos MapIDs de Hoenn inválido")
    required = (
        "Data/System.rxdata", "Data/Scripts.rxdata", "Data/MapInfos.rxdata",
        "Data/Tilesets.rxdata", "PBS/trainers_hoenn_pilot.txt",
        "PBS/trainer_types_hoenn_pilot.txt", "PBS/encounters_hoenn_pilot.txt",
        "PBS/map_metadata_hoenn_pilot.txt", "Plugins/ZZZZZ Blue Hoenn Pilot/HoennPilot.rb",
    )
    absent = [name for name in required if not (output / name).is_file()]
    if absent:
        raise ValueError(f"Arquivos obrigatórios não presentes na cópia: {absent}")
    trainers = (output / "PBS/trainers_hoenn_pilot.txt").read_text("utf-8")
    for name in ("[BLUE_HOENN_JUAN,Juan,1087]",
                 "[BLUE_HOENN_ARCHIE,Archie,1026]",
                 "[BLUE_HOENN_WALLY,Wally,1025]",
                 "[BLUE_HOENN_ELITE,Sidney,1094]",
                 "[BLUE_HOENN_ELITE,Phoebe,1095]",
                 "[BLUE_HOENN_ELITE,Glacia,1096]",
                 "[BLUE_HOENN_ELITE,Drake,1097]",
                 "[BLUE_HOENN_CHAMPION,Wallace,1098]"):
        if name not in trainers:
            raise ValueError(f"Treinador final de Hoenn não encontrado: {name}")
    if expected_profile not in (output / "mkxp.json").read_text("utf-8-sig"):
        raise ValueError("Perfil de save isolado de Hoenn não configurado")
    if (output / "Game.exe").read_bytes() != (game / "Game.exe").read_bytes():
        raise ValueError("Game.exe da cópia é diferente da base local Blue")
    return {
        "isolated_copy_prepared": True, "maps_present": EXPECTED_MAPS,
        "trainer_boss_pbs_entries": 8, "distinct_save_profile": expected_profile,
        "compile_request_pending": (output / "Data/blue-hoenn-compile-request.txt").exists(),
        "compiled_marker_present": (output / "Data/blue-hoenn-compiled.txt").is_file(),
        "game_exe_tested": False, "gameplay_accepted": False,
    }


def build(args) -> dict:
    result = {"schema": 1, "region": "HOENN", "phase": "01/12",
              "phase_name": "Preparar cópia isolada", "source_commit": UPSTREAM,
              "map_inventory": EXPECTED_MAPS,
              "game_exe_tested_here": False, "android_tested_here": False,
              "phase_fully_approved": False, "errors": []}
    args.output = require_private_path(args.output)
    args.report = require_private_path(args.report)
    args.inventory = require_private_path(args.inventory)
    # Audit the native base before creating any donor source artifacts.
    result["base"] = check_game(args.game)
    if args.output.exists():
        result["copy"] = verify_copy(args.output, args.game)
        result["status"] = "COPY_READY_FOR_NATIVE_TEST"
        return result
    if not args.prepare:
        result["status"] = "SOURCE_AND_COPY_NOT_PREPARED"
        return result
    if not args.archive.is_file():
        raise FileNotFoundError(
            "ZIP privado ausente: " + str(args.archive) +
            ". Coloque o ZIP original na raiz, sem substituir por mapas fictícios.")
    tree = load_tree(args.inventory, offline=args.offline)
    result["tree"] = check_tree(tree)
    extracted = inspect_zip(args.archive, extract=True, include_audio=True)
    source_path = ROOT / extracted["local_stage"]
    result["archive_sha256_local_only"] = extracted["archive_sha256"]
    source = Source(source_path, args.inventory)
    result["donor"] = check_source(source)
    game_files = ("Game.exe", "Game.ini", "mkxp.json", "Data/MapInfos.rxdata",
                  "Data/Tilesets.rxdata", "Data/System.rxdata", "Data/Scripts.rxdata")
    original = {name: hashlib.sha256((args.game / name).read_bytes()).hexdigest()
                for name in game_files}
    # stage() refuses existing destinations and builds the copy transactionally.
    result["pilot"] = {"start": stage(args.game, source, args.output)["start"]}
    for name, digest in original.items():
        if hashlib.sha256((args.game / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Instalação principal foi alterada: {name}")
    result["copy"] = verify_copy(args.output, args.game)
    result["status"] = "COPY_READY_FOR_NATIVE_TEST"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, default=ROOT / "game")
    parser.add_argument("--archive", type=Path,
                        default=ROOT / "The Pokémon World Project - Hoenn.zip")
    parser.add_argument("--inventory", type=Path,
                        default=WORK / "hoenn-tree-pinned.json")
    parser.add_argument("--output", type=Path,
                        default=WORK / "hoenn-qa-fase01")
    parser.add_argument("--report", type=Path,
                        default=WORK / "hoenn-qa-fase01-report.json")
    parser.add_argument("--prepare", action="store_true",
                        help="Extraia ZIP local e construa a cópia, sem alterar game/")
    parser.add_argument("--offline", action="store_true",
                        help="Não buscar árvore fixa do GitHub; exige --inventory existente")
    args = parser.parse_args(argv)
    try:
        result = build(args)
        status = 0 if result.get("copy", {}).get("isolated_copy_prepared") else 2
    except (OSError, ValueError, KeyError, TypeError, IndexError,
            RuntimeError, json.JSONDecodeError) as error:
        result = {"schema": 1, "region": "HOENN", "phase": "01/12",
                  "status": "BLOCKED", "phase_fully_approved": False,
                  "game_exe_tested_here": False,
                  "errors": [str(error)]}
        status = 2
    # Always produce a local, Git-ignored diagnostic when output path is safe.
    try:
        path = require_private_path(args.report)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    except (ValueError, OSError):
        pass
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
