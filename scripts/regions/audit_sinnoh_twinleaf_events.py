#!/usr/bin/env python3
"""CH06: read-only Twinleaf event-schema and topology auditor.

JSON Schema 2020-12 is evaluated using the *specific keyword subset* in the
checked-in schema; no external pip installation is required for CI.
No Game.exe, private maps, native save or asset-rights validation is implied.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "data/regions/sinnoh-twinleaf-events.json"
SCHEMA = ROOT / "data/regions/sinnoh-twinleaf-events.schema.json"
MAPS = (
    "SINNOH_PLAYER_BEDROOM", "SINNOH_PLAYER_HOUSE_1F", "SINNOH_TWINLEAF_TOWN",
    "SINNOH_BARRY_HOUSE", "SINNOH_ROUTE_201", "SINNOH_LAKE_VERITY",
    "SINNOH_SANDGEM_TOWN", "SINNOH_PROFESSOR_ROWAN_LABORATORY",
    "SINNOH_ROUTE_202",
)
HANDLERS = {
    "SN_NPC_MOTHER": ("SINNOH_PLAYER_HOUSE_1F", "mother"),
    "SN_NPC_BARRY_INTRO": ("SINNOH_BARRY_HOUSE", "barry_intro"),
    "SN_NPC_ROWAN_BRIEFCASE": ("SINNOH_LAKE_VERITY", "rowan_briefcase"),
    "SN_NPC_BARRY_BATTLE": ("SINNOH_LAKE_VERITY", "barry_rival"),
    "SN_NPC_ROWAN_POKEDEX": ("SINNOH_PROFESSOR_ROWAN_LABORATORY", "rowan_pokedex"),
}
BALLS = {
    "SN_BALL_TURTWIG": ("SINNOH_LAKE_VERITY", "TURTWIG"),
    "SN_BALL_CHIMCHAR": ("SINNOH_LAKE_VERITY", "CHIMCHAR"),
    "SN_BALL_PIPLUP": ("SINNOH_LAKE_VERITY", "PIPLUP"),
}
# Eight intentional bidirectional crossings; return trips are legitimate.
PAIRS = frozenset({
    frozenset(("SINNOH_PLAYER_BEDROOM", "SINNOH_PLAYER_HOUSE_1F")),
    frozenset(("SINNOH_PLAYER_HOUSE_1F", "SINNOH_TWINLEAF_TOWN")),
    frozenset(("SINNOH_TWINLEAF_TOWN", "SINNOH_BARRY_HOUSE")),
    frozenset(("SINNOH_TWINLEAF_TOWN", "SINNOH_ROUTE_201")),
    frozenset(("SINNOH_ROUTE_201", "SINNOH_LAKE_VERITY")),
    frozenset(("SINNOH_ROUTE_201", "SINNOH_SANDGEM_TOWN")),
    frozenset(("SINNOH_SANDGEM_TOWN", "SINNOH_PROFESSOR_ROWAN_LABORATORY")),
    frozenset(("SINNOH_SANDGEM_TOWN", "SINNOH_ROUTE_202")),
})


def fail(reason):
    raise ValueError("[SINNOH CH06] " + reason)


def read_json(path):
    if path.is_symlink() or not path.is_file():
        fail("arquivo JSON ausente/symlink: " + str(path))
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        fail("arquivo JSON precisa ser objeto")
    return data


def _type(value, expected):
    return {
        "object": lambda: isinstance(value, dict),
        "array": lambda: isinstance(value, list),
        "integer": lambda: type(value) is int,
        "boolean": lambda: type(value) is bool,
        "string": lambda: isinstance(value, str),
        "null": lambda: value is None,
    }[expected]()


def _check(value, rules, definitions, where="$"):
    """Evaluate the finite JSON Schema subset used in this repository."""
    if "$ref" in rules:
        ref = rules["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/$defs/"):
            fail(where + ": referência externa do schema não permitida")
        key = ref[len("#/$defs/"):]
        if key not in definitions:
            fail(where + ": definição não encontrada no schema")
        return _check(value, definitions[key], definitions, where)
    if "oneOf" in rules:
        success = 0
        for variant in rules["oneOf"]:
            try:
                _check(value, variant, definitions, where)
                success += 1
            except ValueError:
                pass
        if success != 1:
            fail(where + ": campo/tipo de evento não obedece a exatamente um contrato")
        return
    if "type" in rules and not _type(value, rules["type"]):
        fail(where + ": tipo inválido, esperado " + rules["type"])
    if "const" in rules and (
            type(value) is not type(rules["const"]) or value != rules["const"]):
        fail(where + ": valor fixo inválido")
    if "enum" in rules and value not in rules["enum"]:
        fail(where + ": opção fora da lista permitida")
    if "minimum" in rules and value < rules["minimum"]:
        fail(where + ": número abaixo do mínimo")
    if "maximum" in rules and value > rules["maximum"]:
        fail(where + ": número acima do máximo")
    if isinstance(value, str):
        if len(value) < rules.get("minLength", 0):
            fail(where + ": texto incompleto")
        if "pattern" in rules and re.fullmatch(rules["pattern"], value) is None:
            fail(where + ": formato inválido")
    if isinstance(value, dict):
        missing = set(rules.get("required", [])) - set(value)
        if missing:
            fail(where + ": campos obrigatórios ausentes " + str(sorted(missing)))
        props = rules.get("properties", {})
        if rules.get("additionalProperties") is False and (set(value) - set(props)):
            fail(where + ": campos extras proibidos " + str(sorted(set(value)-set(props))))
        for k, v in value.items():
            if k in props:
                _check(v, props[k], definitions, where + "." + k)
    if isinstance(value, list):
        if len(value) < rules.get("minItems", 0):
            fail(where + ": lista menor que o mínimo")
        if "maxItems" in rules and len(value) > rules["maxItems"]:
            fail(where + ": lista maior que o máximo")
        if "items" in rules:
            for i, v in enumerate(value):
                _check(v, rules["items"], definitions, f"{where}[{i}]")


def validate_schema(spec, schema):
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("não é JSON Schema Draft 2020-12")
    definitions = schema.get("$defs")
    if not isinstance(definitions, dict) or set(definitions) != {
            "start", "map", "warp", "handler", "starter_ball"}:
        fail("schema incompleto")
    _check(spec, schema, definitions)


def check_dimensions(raw):
    if raw is None:
        return None
    if not isinstance(raw, dict) or set(raw) != set(MAPS):
        fail("dimensões devem cobrir exatamente os 9 mapas simbólicos")
    result = {}
    for symbol, shape in raw.items():
        if (not isinstance(shape, list) or len(shape) != 2
                or any(type(n) is not int or n <= 1 for n in shape)):
            fail("dimensões inválidas para " + symbol)
        result[symbol] = tuple(shape)
    return result


def point(x, y, dimensions, label):
    if type(x) is not int or type(y) is not int:
        fail(label + ": coordenadas não verificadas")
    width, height = dimensions
    if not (0 <= x < width and 0 <= y < height):
        fail(label + ": coordenadas fora dos limites do mapa")


def audit(spec, schema, *, dimensions=None):
    """Validate draft and optional *declared* geometry; NEVER authorize install."""
    validate_schema(spec, schema)
    sizes = check_dimensions(dimensions)
    entries = spec["maps"]
    names = [m["symbol"] for m in entries]
    if len(names) != 9 or set(names) != set(MAPS) or len(set(names)) != 9:
        fail("nove mapas simbólicos ausentes ou duplicados")
    by_name = {row["symbol"]: row for row in entries}
    ids = [m["map_id"] for m in entries]
    if sizes is None:
        if any(mid is not None or row["map_sha256"] is not None
               for mid, row in zip(ids, entries)):
            fail("IDs e hashes sem dimensões não são comprovados")
    else:
        if any(type(mid) is not int or row["map_sha256"] is None
               for mid, row in zip(ids, entries)):
            fail("com dimensões, os 9 MapIDs e hashes são obrigatórios")
        if len(set(ids)) != 9:
            fail("MapIDs duplicados")
    start = spec["start"]
    if sizes is None:
        if any(start[k] is not None for k in ("map_id", "x", "y")) or (
                start["verified_position"] or start["passability_verified"]):
            fail("spawn não pode ser verificado sem geometria")
    else:
        if start["map_id"] != by_name["SINNOH_PLAYER_BEDROOM"]["map_id"]:
            fail("spawn aponta MapID de outro mapa")
        if not start["verified_position"] or not start["passability_verified"]:
            fail("spawn não foi verificado")
        point(start["x"], start["y"], sizes["SINNOH_PLAYER_BEDROOM"], "spawn")

    keys, handler_keys, ball_keys, directed = set(), set(), set(), set()
    counts = Counter()
    for m in entries:
        source = m["symbol"]
        occupied = set()
        for e in m["events"]:
            key, kind = e["key"], e["kind"]
            if key in keys:
                fail("ID de evento duplicado: " + key)
            keys.add(key)
            counts[kind] += 1
            if sizes is None:
                if (e["x"] is not None or e["y"] is not None
                        or e["verified_position"]):
                    fail(key + ": posição sem geometria deve ficar null/false")
            else:
                if not e["verified_position"]:
                    fail(key + ": posição não verificada")
                point(e["x"], e["y"], sizes[source], key)
                pos = (e["x"], e["y"])
                if pos in occupied:
                    fail("dois eventos na mesma coordenada: " + source)
                occupied.add(pos)
            if kind == "warp":
                dest = e["destination"]
                if dest not in by_name:
                    fail("warp órfão: destino inexistente: " + key)
                if dest == source:
                    fail("warp circular para o próprio mapa: " + key)
                if (source, dest) in directed:
                    fail("warp duplicado entre dois mapas: " + key)
                directed.add((source, dest))
                if sizes is None:
                    if (e["arrival_x"] is not None or e["arrival_y"] is not None
                            or e["verified_arrival"]):
                        fail(key + ": chegada sem geometria deve ficar null/false")
                else:
                    if not e["verified_arrival"]:
                        fail(key + ": chegada não verificada")
                    point(e["arrival_x"], e["arrival_y"], sizes[dest], key + " arrival")
            else:
                if sizes is None:
                    if e["sprite"] is not None or e["verified_sprite"]:
                        fail(key + ": sprite sem fonte verificada deve ficar null/false")
                elif e["sprite"] is None or not e["verified_sprite"]:
                    fail(key + ": sprite não verificado")
                if kind == "handler":
                    if HANDLERS.get(key) != (source, e["handler"]):
                        fail("handler/chave/local inválido: " + key)
                    handler_keys.add(key)
                if kind == "starter_ball":
                    if BALLS.get(key) != (source, e["species"]):
                        fail("Poké Bola/chave/local inválido: " + key)
                    ball_keys.add(key)
    if counts != Counter(warp=16, handler=5, starter_ball=3) or len(keys) != 24:
        fail("exigir 24 eventos: 16 warps, 5 handlers, 3 Poké Bolas")
    if handler_keys != set(HANDLERS) or ball_keys != set(BALLS):
        fail("handler ou Poké Bola ausente/extra")
    for source, destination in directed:
        if (destination, source) not in directed:
            fail("transferência órfã: warp sem retorno " + source + " -> " + destination)
    links = {frozenset((source, destination)) for source, destination in directed}
    if links != PAIRS:
        fail("topologia divergente dos 8 pares previstos Twinleaf/Sandgem")
    connected = {"SINNOH_PLAYER_BEDROOM"}
    queue = deque(connected)
    graph = {m: set() for m in MAPS}
    for a, b in directed:
        graph[a].add(b)
    while queue:
        for neighbor in graph[queue.popleft()]:
            if neighbor not in connected:
                connected.add(neighbor)
                queue.append(neighbor)
    if connected != set(MAPS):
        fail("mapas inacessíveis do quarto: " + repr(sorted(set(MAPS)-connected)))
    return {
        "schema": 1, "region": "SINNOH",
        "mode": "READ_ONLY_STATIC_SCHEMA_AND_GRAPH",
        "status": "TEMPLATE_STRUCTURE_VALID_NOT_PLAYABLE",
        "maps": 9, "events": 24, "warps": 16, "handlers": 5,
        "starter_balls": 3, "bidirectional_pairs": 8,
        "all_maps_reachable_from_bedroom": True,
        "coordinates_mode": ("NULL_UNVERIFIED_TEMPLATE" if sizes is None
                             else "BOUNDS_FROM_SUPPLIED_DIMENSIONS_ONLY"),
        "actual_geometry_verified": False,
        "native_game_verified": False,
        "can_install": False, "game_modified": False,
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--spec", type=Path, default=SPEC)
    cli.add_argument("--schema", type=Path, default=SCHEMA)
    cli.add_argument("--dimensions", type=Path,
                     help="opcional JSON {SIMBOLO: [largura, altura]}, não prova Game.exe")
    args = cli.parse_args()
    try:
        result = audit(read_json(args.spec), read_json(args.schema),
                       dimensions=read_json(args.dimensions) if args.dimensions else None)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as error:
        print("SINNOH_CH06_BLOQUEADO: " + str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
