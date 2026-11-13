"""Audita a prontidao do primeiro piloto Johto com mapas/portas reais.

Somente LÊ arquivos em .blue-work/ e game/. Produz relatório em .blue-work/.
NAO compila o jogo, aprova coordenadas automaticamente ou libera o menu Johto.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from audit_johto import ROOT, checksum, read_map_data
from server.ruby_marshal import RubyObject

REQUIRED = {
    "JOHTO_NEW_BARK_PLAYER_HOME_2F",
    "JOHTO_NEW_BARK_PLAYER_HOME_1F",
    "JOHTO_NEW_BARK_TOWN",
    "JOHTO_NEW_BARK_ELM_LAB",
    "JOHTO_ROUTE_29",
}
BORDER = {"JH_TOWN_TO_ROUTE29", "JH_ROUTE29_TO_NEW_BARK"}
EXPECTED_KEYS = {
    "JH_HOME2F_TO_1F", "JH_NPC_MOTHER", "JH_HOME1F_TO_2F",
    "JH_HOME1F_TO_TOWN", "JH_TOWN_TO_HOME1F",
    "JH_TOWN_TO_ELM_LAB", "JH_TOWN_TO_ROUTE29",
    "JH_NPC_ELM", "JH_ELM_STARTER_DISPLAY", "JH_LAB_TO_TOWN",
    "JH_ROUTE29_NPC_RIVAL", "JH_ROUTE29_TO_NEW_BARK",
}
EXPECTED_TOPOLOGY = {
    "JH_HOME2F_TO_1F": ("JOHTO_NEW_BARK_PLAYER_HOME_2F", "warp", "JOHTO_NEW_BARK_PLAYER_HOME_1F"),
    "JH_NPC_MOTHER": ("JOHTO_NEW_BARK_PLAYER_HOME_1F", "handler", "mother"),
    "JH_HOME1F_TO_2F": ("JOHTO_NEW_BARK_PLAYER_HOME_1F", "warp", "JOHTO_NEW_BARK_PLAYER_HOME_2F"),
    "JH_HOME1F_TO_TOWN": ("JOHTO_NEW_BARK_PLAYER_HOME_1F", "warp", "JOHTO_NEW_BARK_TOWN"),
    "JH_TOWN_TO_HOME1F": ("JOHTO_NEW_BARK_TOWN", "warp", "JOHTO_NEW_BARK_PLAYER_HOME_1F"),
    "JH_TOWN_TO_ELM_LAB": ("JOHTO_NEW_BARK_TOWN", "warp", "JOHTO_NEW_BARK_ELM_LAB"),
    "JH_TOWN_TO_ROUTE29": ("JOHTO_NEW_BARK_TOWN", "warp", "JOHTO_ROUTE_29"),
    "JH_NPC_ELM": ("JOHTO_NEW_BARK_ELM_LAB", "handler", "elm"),
    "JH_ELM_STARTER_DISPLAY": ("JOHTO_NEW_BARK_ELM_LAB", "handler", "starter"),
    "JH_LAB_TO_TOWN": ("JOHTO_NEW_BARK_ELM_LAB", "warp", "JOHTO_NEW_BARK_TOWN"),
    "JH_ROUTE29_NPC_RIVAL": ("JOHTO_ROUTE_29", "handler", "rival"),
    "JH_ROUTE29_TO_NEW_BARK": ("JOHTO_ROUTE_29", "warp", "JOHTO_NEW_BARK_TOWN"),
}
SHA = re.compile(r"[a-f0-9]{64}\Z")
SPRITE = re.compile(r"[A-Za-z0-9_ -]{1,100}\Z")
CONNECTION = re.compile(r"(\d+),(North|South|East|West),(\d+),(\d+),(North|South|East|West),(\d+)\Z")


def assess(stage: dict, spec: dict, dimensions: dict, sprite_names: set[str],
           *, with_connections: bool = False, connections: str = "") -> dict:
    """Computa checklist; sucesso significa pronto para COMPILAR, jamais gameplay."""
    if (stage.get("schema"), stage.get("region"), stage.get("status"),
            stage.get("can_install"), stage.get("not_playable")) != (
            1, "JOHTO", "GEOMETRY_PREVIEW_ONLY", False, True):
        raise ValueError("Somente geometria Johto isolada e nao jogavel")
    if (spec.get("schema"), spec.get("region"), spec.get("status")) != (
            1, "JOHTO", "EVENT_COORDINATES_REQUIRE_REAL_AUDIT"):
        raise ValueError("Template de eventos de Johto incompativel")
    rows = stage.get("maps")
    events_maps = spec.get("maps")
    if not isinstance(rows, list) or not isinstance(events_maps, list):
        raise ValueError("Manifesto de mapas ou eventos invalido")
    staged = {}
    seen_ids = set()
    for row in rows:
        sym, mid = row.get("symbol"), row.get("destination_id")
        if (not isinstance(sym, str) or type(mid) is not int
                or sym in staged or mid in seen_ids or not 600 <= mid <= 999
                or row.get("events_imported") != 0):
            raise ValueError("Mapa nao auditado, duplicado ou fora do namespace Johto")
        staged[sym] = mid
        seen_ids.add(mid)
    if not REQUIRED.issubset(staged):
        raise ValueError("Faltam os cinco mapas simbolicos do piloto")
    by_symbol = {}
    all_keys = set()
    for row in events_maps:
        symbol = row.get("symbol")
        if symbol not in REQUIRED or symbol in by_symbol:
            raise ValueError("Mapa inesperado/duplicado na especificacao")
        by_symbol[symbol] = row
        if (row.get("map_id") != staged[symbol]
                or row.get("map_sha256") != dimensions.get(symbol, {}).get("sha256")):
            raise ValueError("MapID ou SHA-256 diverge da geometria: " + symbol)
        if not isinstance(row.get("events"), list):
            raise ValueError("Lista de eventos invalida: " + symbol)
        for event in row["events"]:
            key = event.get("key")
            if key not in EXPECTED_KEYS or key in all_keys:
                raise ValueError("Evento faltante, duplicado ou desconhecido: " + str(key))
            owner, kind, target = EXPECTED_TOPOLOGY[key]
            if (symbol != owner or event.get("kind") != kind
                    or event.get("destination" if kind == "warp" else "handler") != target):
                raise ValueError("Topologia de evento/handler alterada: " + key)
            all_keys.add(key)
    if set(by_symbol) != REQUIRED or all_keys != EXPECTED_KEYS:
        raise ValueError("Devem existir exatamente cinco mapas e doze eventos New Bark")
    checks = []
    outstanding = []
    coordinates = {}
    for symbol, row in by_symbol.items():
        room = dimensions[symbol]
        width, height = room.get("width"), room.get("height")
        if (type(width) is not int or type(height) is not int
                or width < 2 or height < 2):
            raise ValueError("Dimensoes RMXP invalidas")
        occupied = set()
        for event in row["events"]:
            key, kind = event["key"], event.get("kind")
            skipped = with_connections and key in BORDER
            problems = []
            if not skipped:
                x, y = event.get("x"), event.get("y")
                if type(x) is not int or type(y) is not int:
                    problems.append("COORDENADA_XY_AUSENTE")
                elif not (0 <= x < width and 0 <= y < height):
                    problems.append("COORDENADA_FORA_DO_MAPA")
                elif (x, y) in occupied:
                    problems.append("COORDENADA_OCUPADA")
                else:
                    occupied.add((x, y))
                if event.get("verified_position") is not True:
                    problems.append("POSICAO_NAO_CONFIRMADA")
                if kind == "handler":
                    sprite = event.get("sprite")
                    if not isinstance(sprite, str) or not SPRITE.fullmatch(sprite):
                        problems.append("SPRITE_NAO_DEFINIDO")
                    elif sprite not in sprite_names:
                        problems.append("SPRITE_PNG_NAO_ENCONTRADO")
                elif kind == "warp":
                    target = event.get("destination")
                    if target not in REQUIRED:
                        problems.append("DESTINO_DESCONHECIDO")
                    else:
                        dest_room = dimensions[target]
                        ax, ay = event.get("arrival_x"), event.get("arrival_y")
                        if type(ax) is not int or type(ay) is not int:
                            problems.append("CHEGADA_XY_AUSENTE")
                        elif not (0 <= ax < dest_room["width"] and
                                  0 <= ay < dest_room["height"]):
                            problems.append("CHEGADA_FORA_DO_MAPA")
                else:
                    problems.append("TIPO_DESCONHECIDO")
            checks.append({"event": key, "map": symbol, "skipped_by_real_border": skipped,
                           "ready": not problems, "issues": problems})
            for problem in problems:
                outstanding.append({"event": key, "problem": problem})
        coordinates[symbol] = occupied

    start = spec.get("start")
    spawn_issues = []
    if not isinstance(start, dict) or start.get("symbol") != "JOHTO_NEW_BARK_PLAYER_HOME_2F":
        raise ValueError("Inicio precisa ser no quarto 2F")
    bedroom = dimensions[start["symbol"]]
    x, y = start.get("x"), start.get("y")
    if type(x) is not int or type(y) is not int:
        spawn_issues.append("SPAWN_XY_AUSENTE")
    elif not (0 <= x < bedroom["width"] and 0 <= y < bedroom["height"]):
        spawn_issues.append("SPAWN_FORA_DO_MAPA")
    elif (x, y) in coordinates[start["symbol"]]:
        spawn_issues.append("SPAWN_SOBRE_EVENTO")
    if start.get("verified_position") is not True:
        spawn_issues.append("SPAWN_NAO_CONFIRMADO")
    if start.get("passability_verified") is not True:
        spawn_issues.append("PASSABILIDADE_SPAWN_NAO_TESTADA")
    for problem in spawn_issues:
        outstanding.append({"event": "PLAYER_SPAWN", "problem": problem})

    border_issues = []
    if with_connections:
        mid_town = staged["JOHTO_NEW_BARK_TOWN"]
        mid_29 = staged["JOHTO_ROUTE_29"]
        candidate = f"{mid_town},West,13,{mid_29},East,0"
        reverse = f"{mid_29},East,0,{mid_town},West,13"
        links = [x.strip() for x in connections.splitlines()
                 if x.strip() and not x.strip().startswith("#")]
        if not links or any(CONNECTION.fullmatch(x) is None for x in links):
            border_issues.append("PBS_CONEXOES_AUSENTE_OU_INVALIDO")
        elif sum(x in (candidate, reverse) for x in links) != 1:
            border_issues.append("LIGACAO_NEW_BARK_ROUTE29_NAO_UNICA")
        if border_issues:
            for problem in border_issues:
                outstanding.append({"event": "PBS_BORDER", "problem": problem})

    status = ("READY_FOR_ISOLATED_ASSEMBLY_NOT_PLAYABLE" if not outstanding
              else "PENDING_NATIVE_REVIEW_NOT_PLAYABLE")
    return {
        "schema": 1, "region": "JOHTO", "phase": 4,
        "status": status, "with_connections": with_connections,
        "events_total": len(checks), "events_ready": sum(x["ready"] for x in checks),
        "checks": checks, "spawn_issues": spawn_issues, "border_issues": border_issues,
        "outstanding": outstanding, "ready_for_isolated_assembly": not outstanding,
        "gameplay_playable": False, "gameplay_tested": False, "can_install": False,
        "warning": ("Aprovacao de coords/sprites so orienta compilacao. "
                    "O Game.exe isolado ainda deve demonstrar inicio, portas, "
                    "Elm, inicial, rival, Route29 e save/reload. Nunca elevar 1/13 aqui."),
    }


def read_spec(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError("Manifesto ausente ou link simbolico: " + str(path))
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError("Manifesto JSON invalido")
    return result


def inspect_native(preview: Path, game: Path, *, root: Path = ROOT):
    from verify_johto import inspect
    root = root.resolve()
    work = (root / ".blue-work").resolve()
    if (preview.is_symlink() or not preview.resolve().is_relative_to(work)
            or game.is_symlink() or game.resolve() != (root / "game").resolve()):
        raise ValueError("Usar apenas preview em .blue-work/ e game/ original")
    proof = inspect(preview, game, root=root)
    if proof.get("status") != "STRUCTURAL_PREVIEW_VALIDATED_NOT_PLAYABLE":
        raise ValueError("Staging nao possui prova estrutural")
    staged = read_spec(preview / "johto-stage.json")
    dimensions = {}
    for row in staged["maps"]:
        symbol, mid = row["symbol"], row["destination_id"]
        if symbol not in REQUIRED:
            continue
        file = preview / "Data" / f"Map{mid:03d}.rxdata"
        world = read_map_data(file)
        if not isinstance(world, RubyObject) or world.name != "RPG::Map":
            raise ValueError("Mapa RMXP invalido: " + symbol)
        dimensions[symbol] = {
            "width": world.attrs.get("@width"),
            "height": world.attrs.get("@height"),
            "sha256": checksum(file),
        }
    sprites = set()
    for base in (game, preview):
        directory = base / "Graphics/Characters"
        if directory.is_symlink():
            raise ValueError("Characters nao pode ser symlink")
        if directory.is_dir():
            for file in directory.glob("*.png"):
                if file.is_symlink():
                    raise ValueError("Sprite symlink proibido")
                with file.open("rb") as f:
                    if f.read(8) == b"\x89PNG\r\n\x1a\n":
                        sprites.add(file.stem)
    return staged, dimensions, sprites


def write_report(path: Path, data: dict, *, root: Path = ROOT):
    work = (root.resolve() / ".blue-work").resolve()
    if (path.is_symlink() or path.exists() or path.resolve() == work
            or not path.resolve().is_relative_to(work)):
        raise ValueError("Relatorio deve ser NOVO dentro de .blue-work/")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", type=Path,
                        default=ROOT / ".blue-work/johto-staging-interiors")
    parser.add_argument("--game", type=Path, default=ROOT / "game")
    parser.add_argument("--spec", type=Path,
                        default=ROOT / ".blue-work/johto-new-bark-bound.json")
    parser.add_argument("--connections", type=Path,
                        default=ROOT / ".blue-work/johto-connections-preview.txt")
    parser.add_argument("--with-connections", action="store_true")
    parser.add_argument("--output", type=Path,
                        default=ROOT / ".blue-work/johto-phase04-acceptance.json")
    args = parser.parse_args(argv)
    try:
        stage, rooms, sprites = inspect_native(args.preview, args.game)
        spec = read_spec(args.spec)
        text = ""
        if args.with_connections:
            if not args.connections.resolve().is_relative_to(
                    (ROOT / ".blue-work").resolve()):
                raise ValueError("PBS de conexoes precisa estar no workspace")
            text = args.connections.read_text(encoding="utf-8")
        review = assess(stage, spec, rooms, sprites,
                        with_connections=args.with_connections, connections=text)
        write_report(args.output, review)
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("[JOHTO][BLOQUEADO]", exc, file=sys.stderr)
        return 2
    print("[JOHTO]", review["status"], "- eventos:", review["events_ready"],
          "/", review["events_total"], "- pendencias:", len(review["outstanding"]))
    print("[JOHTO] Relatorio:", args.output)
    print("[JOHTO] Fases jogaveis 0/13 e testadas 0/13 ate prova real.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
