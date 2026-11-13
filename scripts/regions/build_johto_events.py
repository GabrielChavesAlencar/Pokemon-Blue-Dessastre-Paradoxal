"""Compila eventos próprios do início de Johto sobre uma PRÉVIA RMXP auditada.

NÃO instala no Game.exe, NÃO habilita 'Testar Johto', NÃO escreve em game/,
NÃO executa scripts externos e NÃO mistura dados de Kanto/Decades.
Somente aceita handlers Ruby da allowlist do BlueJohtoPilot.
Coordenadas e MapIDs são preenchidos após auditoria REAL da geometria.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

from audit_johto import ROOT, read_map_data, checksum
from stage import serialize
from server.ruby_marshal import RubyObject

DEFAULT_SPEC = ROOT / "data/regions/johto-new-bark-events.json"
DEFAULT_OUTPUT = ROOT / ".blue-work/johto-new-bark-events"
HANDLERS = {
    "mother": "BlueJohtoPilot.mother",
    "elm": "BlueJohtoPilot.elm",
    "starter": "BlueJohtoPilot.choose_starter",
    "rival": "BlueJohtoPilot.rival",
}
NEEDED_HANDLERS = set(HANDLERS)
SYMBOL = re.compile(r"JOHTO_[A-Z0-9_]{3,70}\Z")
KEY = re.compile(r"JH_[A-Z0-9_]{3,70}\Z")
HASH = re.compile(r"[a-f0-9]{64}\Z")
GRAPHIC = re.compile(r"[A-Za-z0-9_ -]{1,100}\Z")
EVENT_CLASSES = ("RPG::Event", "RPG::Event::Page",
                 "RPG::Event::Page::Condition", "RPG::Event::Page::Graphic",
                 "RPG::EventCommand", "RPG::MoveRoute", "RPG::MoveCommand")


def fail(msg: str):
    raise ValueError("[JOHTO] " + msg)


def ruby(name: str, **fields):
    return RubyObject(name, {"@" + key: val for key, val in fields.items()})


def command(code: int, *parameters):
    return ruby("RPG::EventCommand", code=code, indent=0, parameters=list(parameters))


def event_page(*, script: str | None = None, warp: tuple[int, int, int] | None = None,
               sprite: str = "", touch: bool = False):
    if (script is None) == (warp is None):
        fail("Evento deve ter exatamente um handler OU uma transferência")
    condition = ruby(
        "RPG::Event::Page::Condition", switch1_valid=False,
        switch2_valid=False, variable_valid=False, self_switch_valid=False,
        switch1_id=1, switch2_id=1, variable_id=1, variable_value=0,
        self_switch_ch=b"A",
    )
    graphic = ruby(
        "RPG::Event::Page::Graphic", tile_id=0,
        character_name=sprite.encode("utf-8"), character_hue=0,
        direction=2, pattern=0, opacity=255, blend_type=0,
    )
    route = ruby("RPG::MoveRoute", repeat=True, skippable=True,
                 list=[ruby("RPG::MoveCommand", code=0, parameters=[])])
    ops = ([command(355, script.encode("ascii"))] if script is not None
           else [command(201, 0, warp[0], warp[1], warp[2], 2, 0)])
    ops.append(command(0))
    return ruby(
        "RPG::Event::Page", condition=condition, graphic=graphic,
        move_type=0, move_speed=3, move_frequency=3, move_route=route,
        walk_anime=True, step_anime=False, direction_fix=touch,
        through=touch, always_on_top=False, trigger=1 if touch else 0,
        list=ops,
    )


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        fail("Especificação JSON inválida")
    return value


def normalized_maps(stage: dict) -> dict:
    if (stage.get("schema"), stage.get("region"), stage.get("status"),
            stage.get("not_playable"), stage.get("can_install")) != (
            1, "JOHTO", "GEOMETRY_PREVIEW_ONLY", True, False):
        fail("Entrada deve ser exclusivamente uma prévia geométrica de Johto")
    result = {}
    for row in stage.get("maps", []):
        symbol, mid = row.get("symbol"), row.get("destination_id")
        if (not isinstance(symbol, str) or not SYMBOL.fullmatch(symbol)
                or type(mid) is not int or mid < 600 or mid > 999
                or symbol in result or mid in result.values()
                or row.get("events_imported") != 0):
            fail("Mapa de staging inválido ou duplicado")
        result[symbol] = mid
    if not result:
        fail("Staging não contém mapas")
    return result


def compile_events(preview: Path, spec: dict, *, work_root: Path = ROOT) -> tuple[dict, dict[str, bytes]]:
    """Retorna manifesto e bytes em memória, nunca toca na instalação."""
    preview = preview.absolute()
    workspace = (work_root / ".blue-work").resolve()
    if (preview.is_symlink() or not preview.resolve().is_relative_to(workspace)
            or preview.resolve() == workspace):
        fail("Preview fora do workspace isolado ou ligado por symlink")
    stage_file = preview / "johto-stage.json"
    if not stage_file.is_file() or stage_file.is_symlink():
        fail("Manifesto da prévia geométrica ausente")
    stage = read_json(stage_file)
    mapping = normalized_maps(stage)
    pinned = stage.get("source_archive_sha256")
    if not isinstance(pinned, str) or not HASH.fullmatch(pinned):
        fail("SHA-256 do pacote de origem não validado")
    if (spec.get("schema"), spec.get("region"), spec.get("status")) != (
            1, "JOHTO", "EVENT_COORDINATES_REQUIRE_REAL_AUDIT"):
        fail("Especificação de eventos/versão inválida")
    maps = spec.get("maps")
    if not isinstance(maps, list) or not maps:
        fail("Nenhum mapa de eventos especificado")
    defined = {}
    all_keys = set()
    handler_uses = set()
    for row in maps:
        symbol = row.get("symbol")
        map_id = row.get("map_id")
        digest = row.get("map_sha256")
        if (symbol not in mapping or symbol in defined
                or type(map_id) is not int or map_id != mapping[symbol]
                or not isinstance(digest, str) or not HASH.fullmatch(digest)):
            fail("MapID/hash não auditado para " + str(symbol))
        map_file = preview / "Data" / f"Map{map_id:03d}.rxdata"
        if map_file.is_symlink() or not map_file.is_file() or checksum(map_file) != digest:
            fail("Mapa ausente ou alterado desde o registro: " + str(symbol))
        world = read_map_data(map_file)
        if not isinstance(world, RubyObject) or world.name != "RPG::Map":
            fail("Arquivo de mapa inválido")
        a = world.attrs
        if a.get("@events") != {}:
            fail("Preview já contém eventos; não sobrepor eventos existentes")
        if a.get("@autoplay_bgm") or a.get("@autoplay_bgs"):
            fail("Preview com áudio original não é fonte segura")
        width, height = a.get("@width"), a.get("@height")
        if (type(width) is not int or width < 2 or
                type(height) is not int or height < 2):
            fail("Dimensões inválidas")
        events = row.get("events")
        if not isinstance(events, list) or not events:
            fail("Mapa não possui eventos conferidos: " + symbol)
        defined[symbol] = (map_id, world, width, height, events)
    output = {}
    used_tiles = {}
    for symbol, (mid, world, width, height, events) in defined.items():
        compiled = {}
        tile_positions = set()
        for n, row in enumerate(events, start=1):
            key = row.get("key")
            x, y = row.get("x"), row.get("y")
            kind = row.get("kind")
            if (not isinstance(key, str) or not KEY.fullmatch(key)
                    or key in all_keys or type(x) is not int or type(y) is not int
                    or not 0 <= x < width or not 0 <= y < height
                    or (x, y) in tile_positions):
                fail("Evento/posição não confirmados: " + str(key))
            if row.get("verified_position") is not True:
                fail("Posição não verificada visualmente: " + key)
            all_keys.add(key)
            tile_positions.add((x, y))
            if kind == "handler":
                handler = row.get("handler")
                sprite = row.get("sprite")
                if (handler not in HANDLERS or
                        not isinstance(sprite, str) or not GRAPHIC.fullmatch(sprite)):
                    fail("Handler/sprite não confiável ou não definido: " + key)
                handler_uses.add(handler)
                page = event_page(script=HANDLERS[handler], sprite=sprite)
            elif kind == "warp":
                target = row.get("destination")
                xx, yy = row.get("arrival_x"), row.get("arrival_y")
                if (target not in defined or type(xx) is not int or type(yy) is not int):
                    fail("Destino de warp desconhecido: " + key)
                did, _, dw, dh, _ = defined[target]
                if not (0 <= xx < dw and 0 <= yy < dh):
                    fail("Warp chega fora do mapa: " + key)
                page = event_page(warp=(did, xx, yy), touch=True)
            else:
                fail("Tipo de evento não permitido: " + str(kind))
            compiled[n] = ruby("RPG::Event", id=n,
                               name=key.encode("ascii"), x=x, y=y,
                               pages=[page])
        target = copy.deepcopy(world)
        target.attrs["@events"] = compiled
        relative = f"Data/Map{mid:03d}.rxdata"
        output[relative] = serialize(target, EVENT_CLASSES)
        used_tiles[symbol] = len(tile_positions)
    if not NEEDED_HANDLERS.issubset(handler_uses):
        fail("Início de New Bark exige mãe, Elm, inicial e rival (sem equipe PBS presumida)")
    return ({
        "schema": 1, "region": "JOHTO",
        "status": "AUTHORED_EVENT_MAPS_NOT_PLAYABLE",
        "can_install": False, "not_playable": True,
        "source_archive_sha256": pinned,
        "map_ids": {k: v[0] for k, v in defined.items()},
        "events_per_map": used_tiles,
        "files": {path: hashlib.sha256(data).hexdigest()
                  for path, data in sorted(output.items())},
        "warnings": [
            "Os eventos foram COMPILADOS EM ISOLAMENTO, não instalados no Game.exe.",
            "TrainerBattle/PBS do rival ainda requer compilação e prova real.",
            "Sprites, colisões, portas, saves e gatilhos ainda requerem testes nativos.",
            "Nenhum manifesto VERIFIED_PLAYABLE, música ou save foi emitido.",
        ],
    }, output)


def publish(preview: Path, output: Path, spec: dict, *, work_root: Path = ROOT) -> dict:
    workspace = (work_root / ".blue-work").resolve()
    output = output.absolute()
    if (output.is_symlink() or not output.resolve().is_relative_to(workspace)
            or output.resolve() == workspace or output.exists()):
        fail("Destino deve ser diretório NOVO dentro de .blue-work")
    report, files = compile_events(preview, spec, work_root=work_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".johto-events-", dir=output.parent) as tmp:
        staging = Path(tmp) / "content"
        for name, data in files.items():
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (staging / "johto-event-build.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if output.exists() or output.is_symlink():
            fail("Destino passou a existir durante compilação")
        staging.rename(output)
    return report


def main(argv=None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--preview", type=Path, default=ROOT / ".blue-work/johto-staging-v1")
    cli.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    cli.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = cli.parse_args(argv)
    try:
        result = publish(args.preview, args.output, read_json(args.spec))
    except (OSError, ValueError, KeyError, TypeError) as e:
        print("[JOHTO][BLOQUEADO] " + str(e), file=sys.stderr)
        return 2
    print(f"[JOHTO] {len(result['map_ids'])} mapas tiveram eventos próprios compilados em cópia isolada.")
    print("[JOHTO] Game.exe NÃO foi modificado. Próximo: integrar PBS/sprites e validar gameplay.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
