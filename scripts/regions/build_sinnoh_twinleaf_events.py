#!/usr/bin/env python3
"""Compile only authored Sinnoh opening events on a hashed local geometry preview.

NO donor Ruby event scripts, NO Game.exe/game/ edits, NO invented MapIDs,
coordinates or sprites. All geometry/sprites/arrival points must be reviewed
against the real source before this compiler can produce its isolated overlay.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

from audit_johto import ROOT, read_map_data
from build_johto_events import EVENT_CLASSES, event_page, ruby
from server.ruby_marshal import RubyObject
from sinnoh_staging_transaction import preview as dry_run, stage as create_stage
from stage import serialize

MAPS = (
    "SINNOH_PLAYER_BEDROOM",
    "SINNOH_PLAYER_HOUSE_1F",
    "SINNOH_TWINLEAF_TOWN",
    "SINNOH_BARRY_HOUSE",
    "SINNOH_ROUTE_201",
    "SINNOH_LAKE_VERITY",
    "SINNOH_SANDGEM_TOWN",
    "SINNOH_PROFESSOR_ROWAN_LABORATORY",
    "SINNOH_ROUTE_202",
)
HANDLERS = {
    "mother": "BlueSinnohPilot.mother",
    "barry_intro": "BlueSinnohPilot.barry_intro",
    "rowan_briefcase": "BlueSinnohPilot.rowan_briefcase",
    "barry_rival": "BlueSinnohPilot.barry_rival",
    "rowan_pokedex": "BlueSinnohPilot.rowan_pokedex",
}
STARTERS = ("TURTWIG", "CHIMCHAR", "PIPLUP")
NEEDED_KEYS = {
    "SN_NPC_MOTHER", "SN_NPC_BARRY_INTRO",
    "SN_NPC_ROWAN_BRIEFCASE", "SN_NPC_BARRY_BATTLE",
    "SN_NPC_ROWAN_POKEDEX", "SN_BALL_TURTWIG",
    "SN_BALL_CHIMCHAR", "SN_BALL_PIPLUP",
}
GRAPHIC = re.compile(r"[A-Za-z0-9_ .()-]{1,100}\Z")
KEY = re.compile(r"SN_[A-Z0-9_]{3,75}\Z")
HASH = re.compile(r"[a-f0-9]{64}\Z")
DEFAULT_SPEC = ROOT / "data/regions/sinnoh-twinleaf-events.json"


def fail(message: str):
    raise ValueError("[SINNOH EVENTS] " + message)


def read_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        fail("JSON ausente ou symlink")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        fail("Especificação não é JSON objeto")
    return data


def _candidate_stage_folder(folder: Path, project: Path) -> Path:
    folder = folder.absolute()
    allowed = (project / ".blue-work/sinnoh-stage").absolute()
    if folder == allowed or not folder.is_relative_to(allowed):
        fail("Prévia de geometria deve estar dentro de .blue-work/sinnoh-stage/")
    for part in (folder, *folder.parents):
        if part.is_symlink():
            fail("Symlink no caminho do stage")
    return folder


def _check_source_stage(folder: Path) -> dict[str, str]:
    raw = read_json(folder / "stage-manifest.json")
    if (raw.get("schema"), raw.get("region"), raw.get("mode"),
            raw.get("may_install_into_game"),
            raw.get("writes_to_main_game")) != (
            1, "SINNOH", "LOCAL_STAGE_ONLY", False, False):
        fail("Origem não é prévia isolada de Sinnoh")
    label = raw.get("label")
    plan_sha = raw.get("plan_sha256")
    if (not isinstance(label, str) or not isinstance(plan_sha, str)
            or not HASH.fullmatch(plan_sha)
            or folder.name != f"{label}-{plan_sha[:16]}"):
        fail("Manifesto do stage mudou ou está no diretório errado")
    rows = raw.get("files")
    if not isinstance(rows, list) or len(rows) < len(MAPS) + 2:
        fail("Stage geométrico não possui os 9 mapas e índices")
    names = {}
    for row in rows:
        if not isinstance(row, dict):
            fail("Manifesto de arquivos malformado")
        path = row.get("path")
        hashval = row.get("sha256")
        if (not isinstance(path, str) or path in names
                or not isinstance(hashval, str) or not HASH.fullmatch(hashval)):
            fail("Stage com arquivo repetido/hash inválido")
        names[path] = hashval
    if "Data/MapInfos.rxdata" not in names or "Data/Tilesets.rxdata" not in names:
        fail("Stage de geometria sem MapInfos e Tilesets")
    return names


def compile_events(folder: Path, spec: dict, *, project: Path = ROOT):
    """Compile to in-memory bytes; geometry stage & native game remain unchanged."""
    folder = _candidate_stage_folder(folder, project)
    stage_files = _check_source_stage(folder)
    if (spec.get("schema"), spec.get("region"), spec.get("status"),
            spec.get("approved_for_install"),
            spec.get("gameplay_verified")) != (
            1, "SINNOH", "EVENT_COORDINATES_REQUIRE_REAL_MAP_AUDIT", False, False):
        fail("Especificação de Twinleaf não aprovada/errada")
    entries = spec.get("maps")
    if not isinstance(entries, list) or len(entries) != len(MAPS):
        fail("Exigir nove mapas do núcleo Twinleaf/Verity/Sandgem")
    defined = {}
    for row in entries:
        if not isinstance(row, dict):
            fail("Mapas de eventos inválidos")
        symbol, mid, expect_sha = (row.get("symbol"), row.get("map_id"),
                                   row.get("map_sha256"))
        if (symbol not in MAPS or symbol in defined
                or type(mid) is not int or not 1 <= mid < 600
                or not isinstance(expect_sha, str) or not HASH.fullmatch(expect_sha)):
            fail("MapID/hash/símbolo não confirmado para " + str(symbol))
        file = f"Data/Map{mid:03d}.rxdata"
        if stage_files.get(file) != expect_sha:
            fail("Mapa não confere com SHA-256 do stage: " + str(symbol))
        source_file = folder / file
        if source_file.is_symlink() or not source_file.is_file():
            fail("Mapa real de staging ausente")
        raw = source_file.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expect_sha:
            fail("Mapa de geometria alterado após auditoria")
        obj = read_map_data(source_file)
        if not isinstance(obj, RubyObject) or obj.name != "RPG::Map":
            fail("Arquivo de geometria não contém RPG::Map")
        data = obj.attrs
        if data.get("@events") != {} or data.get("@autoplay_bgm") is not False or data.get("@autoplay_bgs") is not False:
            fail("Prévia não é geometria vazia / sem eventos estrangeiros")
        w, h = data.get("@width"), data.get("@height")
        if any(type(n) is not int for n in (w, h)) or w <= 1 or h <= 1:
            fail("Dimensões de mapa inválidas")
        if not isinstance(row.get("events"), list) or not row["events"]:
            fail("Mapa de início sem eventos ou warps auditados")
        defined[symbol] = (mid, obj, w, h, row["events"])
    if set(defined) != set(MAPS):
        fail("Áreas de Twinleaf/Sandgem ausentes")
    if len(set(v[0] for v in defined.values())) != len(MAPS):
        fail("MapID duplicado entre as áreas do núcleo")

    start = spec.get("start")
    bed = defined["SINNOH_PLAYER_BEDROOM"]
    if (not isinstance(start, dict) or start.get("symbol") != "SINNOH_PLAYER_BEDROOM"
            or start.get("map_id") != bed[0]
            or start.get("verified_position") is not True
            or start.get("passability_verified") is not True
            or type(start.get("x")) is not int
            or type(start.get("y")) is not int
            or not (0 <= start["x"] < bed[2] and 0 <= start["y"] < bed[3])):
        fail("Spawn dentro da casa não auditado: não permitir iniciar na rua")

    keys = set()
    used_handlers = set()
    used_starters = set()
    result_files = {}
    event_counts = {}
    warp_count = 0
    for symbol, (mid, original, w, h, events) in defined.items():
        compiled = {}
        occupied = set()
        for index, row in enumerate(events, start=1):
            if not isinstance(row, dict):
                fail("Evento malformado")
            key, x, y, kind = (row.get("key"), row.get("x"),
                               row.get("y"), row.get("kind"))
            if (not isinstance(key, str) or not KEY.fullmatch(key)
                    or key in keys or type(x) is not int or type(y) is not int
                    or not (0 <= x < w and 0 <= y < h)
                    or row.get("verified_position") is not True
                    or (x, y) in occupied):
                fail("Posição do evento/ID duplicado ou não auditado: " + str(key))
            keys.add(key)
            occupied.add((x, y))
            trigger = row.get("trigger")
            if kind == "warp":
                destination = row.get("destination")
                if trigger != "touch" or destination not in defined:
                    fail("Warp sem destino real/trigger touch")
                dest_id, _, dest_w, dest_h, _ = defined[destination]
                xx, yy = row.get("arrival_x"), row.get("arrival_y")
                if (type(xx) is not int or type(yy) is not int
                        or not 0 <= xx < dest_w or not 0 <= yy < dest_h
                        or row.get("verified_arrival") is not True):
                    fail("Chegada do warp sem verificação real: " + key)
                page = event_page(warp=(dest_id, xx, yy), touch=True)
                warp_count += 1
            elif kind in ("handler", "starter_ball"):
                if trigger not in ("action", "touch"):
                    fail("Tipo de gatilho inválido")
                sprite = row.get("sprite")
                if (not isinstance(sprite, str) or not GRAPHIC.fullmatch(sprite)
                        or row.get("verified_sprite") is not True):
                    fail("Sprite próprio não verificado para " + key)
                if kind == "handler":
                    handler = row.get("handler")
                    if handler not in HANDLERS:
                        fail("Handler externo/não confiável bloqueado")
                    used_handlers.add(handler)
                    script = HANDLERS[handler]
                else:
                    species = row.get("species")
                    if species not in STARTERS or species in used_starters:
                        fail("Poké Bola não pertence aos três iniciais únicos de Sinnoh")
                    used_starters.add(species)
                    script = f"BlueSinnohPilot.choose_starter_from_ball(:{species})"
                page = event_page(script=script, sprite=sprite, touch=(trigger == "touch"))
            else:
                fail("Tipo de evento não permitido: " + str(kind))
            compiled[index] = ruby("RPG::Event", id=index, name=key.encode("ascii"),
                                   x=x, y=y, pages=[page])
        out = copy.deepcopy(original)
        out.attrs["@events"] = compiled
        name = f"Data/Map{mid:03d}.rxdata"
        result_files[name] = serialize(out, EVENT_CLASSES)
        event_counts[symbol] = len(compiled)
    if (not NEEDED_KEYS.issubset(keys) or set(HANDLERS) != used_handlers
            or set(STARTERS) != used_starters or warp_count != 16
            or len(keys) != 24):
        fail("Introdução exige 5 handlers, 3 bolas físicas e 16 warps")
    report = {
        "schema": 1, "region": "SINNOH",
        "status": "AUTHORED_EVENTS_COMPILED_IN_ISOLATED_PREVIEW_NOT_PLAYABLE",
        "not_playable": True, "can_install": False, "gameplay_verified": False,
        "native_game_modified": False, "source_game_events_copied": 0,
        "start": [bed[0], start["x"], start["y"]],
        "event_counts": event_counts, "warp_count": warp_count,
        "starter_balls": sorted(used_starters),
        "author_only_handlers": sorted(used_handlers),
        "files": {name: hashlib.sha256(raw).hexdigest()
                  for name, raw in sorted(result_files.items())},
        "warnings": [
            "Sprites and placements require a real audited Sinnoh source.",
            "The battle with Barry is locked until PBS three versions and marker verified.",
            "No native gameplay, maps, saves or Android tests completed.",
            "Staging uses original Blue Ruby handlers only, never donor event scripts.",
        ],
    }
    return report, result_files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry-stage", required=True, type=Path,
                        help="Só .blue-work/sinnoh-stage/<label>-<hash>")
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--label", default="sinnoh-story")
    parser.add_argument("--stage", action="store_true")
    parser.add_argument("--expected-dry-run", help="SHA-256 do dry-run anterior")
    args = parser.parse_args()
    try:
        spec = read_json(args.spec)
        report, files = compile_events(args.geometry_stage, spec, project=ROOT)
        dry = dry_run(ROOT, args.label, files)
        if args.stage:
            if not args.expected_dry_run:
                fail("Etapa escrita exige --expected-dry-run do dry-run anterior")
            transaction = create_stage(ROOT, args.label, files, args.expected_dry_run)
        else:
            if args.expected_dry_run:
                fail("Não fornecer hash para dry-run sem --stage")
            transaction = dry
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        print("SINNOH_TWINLEAF_EVENTS_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({**report, "transaction": transaction},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
