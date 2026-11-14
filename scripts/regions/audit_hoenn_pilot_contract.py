#!/usr/bin/env python3
"""Audit the public Hoenn pilot against its own source definitions (read-only).

This check uses committed scripts and site JSON only. It DOES NOT inspect the
private donor ZIP, native Data/*.rxdata, installed Game.exe, save files, or a
running RPG Maker XP engine. Passing this check is never gameplay approval.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import deque
from pathlib import Path

from audit_hoenn_baseline import PILOT
from pilot_hoenn import (
    BGM, BORDERS, LAND_ENCOUNTERS, MAP_BGM, OUTDOORS, PEOPLE,
    ROUTE_102_TRAINERS, RIVAL_NAMES, RIVAL_TEAMS, SOURCE_MAPS, START, UPSTREAM, WARP_PAIRS,
)

ROOT = Path(__file__).resolve().parents[2]
CATALOG = "site/public/data/hoenn-pilot.json"
REGISTRY = "site/public/data/regions.json"
HANDLERS = "scripts/regions/HoennPilot.rb"
AUDIT_VERSION = 1


def audit(root: Path = ROOT) -> dict:
    """Return every inconsistency rather than treating public catalog as proof."""
    root = Path(root)
    catalog = json.loads((root / CATALOG).read_text(encoding="utf-8"))
    registry = json.loads((root / REGISTRY).read_text(encoding="utf-8"))
    plugin = (root / HANDLERS).read_text(encoding="utf-8")
    errors: list[str] = []
    source_ids = set(SOURCE_MAPS)
    if source_ids != set(PILOT):
        errors.append(f"Baseline/source MapIDs differ: {sorted(source_ids ^ set(PILOT))}")
    if not re.fullmatch(r"[a-f0-9]{40}", UPSTREAM):
        errors.append("Unpinned or invalid upstream revision")
    if START[0] not in source_ids:
        errors.append("Starting source map is not part of the pilot")
    if catalog.get("region") != "hoenn" or catalog.get("schema") != 1:
        errors.append("Wrong Hoenn site catalog identity/schema")
    if registry["regions"]["HOENN"]["status"] not in ("planned", "prototype"):
        errors.append("Hoenn must not be declared playable by a static audit")

    locations = catalog.get("locations", [])
    names = [row.get("name") for row in locations]
    if len(names) != len(set(names)):
        errors.append("Duplicate locations in the site catalog")
    if set(names) != set(SOURCE_MAPS.values()):
        errors.append(f"Map catalog differs from pilot source: {sorted(set(names) ^ set(SOURCE_MAPS.values()))}")
    by_name = {row["name"]: row for row in locations}
    for map_id, name in SOURCE_MAPS.items():
        if name not in by_name:
            continue
        expected = LAND_ENCOUNTERS.get(map_id, ())
        actual = by_name[name].get("encounters", {})
        expected_slots = sorted((species, low, high, weight) for weight, species, low, high in expected)
        actual_slots = sorted(tuple(row) for row in actual.get("Grama", []))
        if expected_slots != actual_slots:
            errors.append(f"Map {map_id} ({name}): grass encounter slots differ from native pilot generator")
        if set(actual) - {"Grama"}:
            errors.append(f"Map {map_id} ({name}): unsupported encounter method in public catalog")
    for map_id, encounters in LAND_ENCOUNTERS.items():
        if map_id not in source_ids:
            errors.append(f"Encounter route {map_id} has no imported map")
        if sum(weight for weight, *_ in encounters) != 100:
            errors.append(f"Encounter weights on map {map_id} do not total 100")
        if any(weight <= 0 or low <= 0 or high < low for weight, _, low, high in encounters):
            errors.append(f"Invalid encounter chance/level bounds on map {map_id}")
        if len({species for _, species, _, _ in encounters}) != len(encounters):
            errors.append(f"Duplicate species slot on map {map_id}")

    native_trainers = {name: tuple(team) for _, _, _, name, _, team in ROUTE_102_TRAINERS}
    published = catalog.get("trainers", [])
    names_published = [row.get("name") for row in published]
    if len(names_published) != len(set(names_published)):
        errors.append("Duplicate trainers in published Hoenn pilot")
    if set(names_published) != set(native_trainers):
        errors.append(f"Published trainers differ from pilot: {sorted(set(names_published) ^ set(native_trainers))}")
    if len(native_trainers) != len(ROUTE_102_TRAINERS):
        errors.append("Duplicate trainer definitions in native pilot")
    for row in published:
        name = row.get("name")
        if name not in native_trainers:
            continue
        teams = row.get("teams", [])
        party = [tuple(pokemon) for pokemon in teams[0].get("pokemon", [])] if len(teams) == 1 else []
        if row.get("area") != SOURCE_MAPS[102] or party != list(native_trainers[name]):
            errors.append(f"Trainer {name}: team/area differs from pilot generator")
        if row.get("leader") is not False or row.get("badge") is not None:
            errors.append(f"Trainer {name}: wrongly advertised as gym leader")

    all_edges = [tuple(pair) for pair in BORDERS]
    if any(a not in source_ids or b not in source_ids for a, _, b, _ in all_edges):
        errors.append("A border connection references an unknown source map")
    if any(a[0] not in source_ids or b[0] not in source_ids
           for a, _, b, _ in WARP_PAIRS):
        errors.append("A door/ladder references an unknown source map")
    adjacency = {mid: set() for mid in source_ids}
    for a, _, b, _ in BORDERS:
        if a in adjacency and b in adjacency:
            adjacency[a].add(b)
            adjacency[b].add(a)
    for a, _, b, _ in WARP_PAIRS:
        if a[0] in adjacency and b[0] in adjacency:
            adjacency[a[0]].add(b[0])
            adjacency[b[0]].add(a[0])
    seen = {START[0]}
    queue = deque(seen)
    while queue:
        for nxt in adjacency.get(queue.popleft(), ()):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    if seen != source_ids:
        errors.append(f"Disconnected pilot map nodes: {sorted(source_ids - seen)}")

    occupied: dict[tuple[int, int, int], str] = {}
    points = (
        [(mid, x, y, f"NPC:{name}") for mid, x, y, name, _, _ in PEOPLE]
        + [(a[0], a[1], a[2], "warp") for a, _, b, _ in WARP_PAIRS]
        + [(b[0], b[1], b[2], "warp") for a, _, b, _ in WARP_PAIRS]
        + [(102, x, y, f"trainer:{name}") for x, y, _, name, _, _ in ROUTE_102_TRAINERS]
        + [(8, 25, 6, "profile"), (8, 26, 3, "clock"),
           (101, 10, 18, "Birch rescue"), (101, 11, 18, "Birch rescue")]
    )
    for mid, x, y, label in points:
        if mid not in source_ids:
            errors.append(f"Event {label} references missing map {mid}")
        key = (mid, x, y)
        if key in occupied:
            errors.append(f"Overlapping events on {key}: {occupied[key]} vs {label}")
        occupied[key] = label

    defined = set(re.findall(r"(?m)^\s*def self\.([a-z_]+)\b", plugin))
    required = {"state", "choose_profile", "choose_starter", "route_birch",
                "choose_birch_ball", "rescue_birch_battle", "rival_103",
                "rival_name", "birch", "mother", "mart", "heal", "clock",
                "battle", "verify_compilation"}
    required.update(re.match(r"BlueHoennPilot\.([a-z_]+)", handler).group(1)
                    for *_, handler in PEOPLE)
    if missing := required - defined:
        errors.append(f"Hoenn runtime handler(s) missing: {sorted(missing)}")
    if any(mid not in source_ids for mid in MAP_BGM):
        errors.append("Regional BGM references missing pilot map")
    if any(label not in BGM for label in MAP_BGM.values()):
        errors.append("Regional BGM refers to an unknown pilot track alias")
    if not set(OUTDOORS).issubset(source_ids):
        errors.append("Outdoor metadata refers to missing maps")
    if set(RIVAL_TEAMS) != {"TREECKO", "TORCHIC", "MUDKIP"} or set(RIVAL_NAMES) != {"May", "Brendan"}:
        errors.append("Wrong rival starter/gender variants")
    if len({version for _, version in RIVAL_TEAMS.values()}) != 3:
        errors.append("Duplicate rival trainer PBS versions")
    if any(starter == enemy for starter, (enemy, _) in RIVAL_TEAMS.items()):
        errors.append("Rival must choose counter-starter species")


    # Prepared scripts are not a substitute for a Game.exe proof.
    gaps = [
        "Caminhão/introdução visual de Emerald ainda não construídos; spawn é na casa.",
        "Posições das três Poké Bolas e rival exigem geometria RXDATA da cópia isolada e teste real.",
        "Rival 103 depende de seis variantes RIVAL1 compiladas e sprite nativo auditado.",
        "Pokédex, cinco Poké Bolas e Tênis de Corrida têm lógica Ruby; save/reload nativo exige teste.",
        "Rota 102 termina o recorte: Petalburg, Wally e Norman não fazem parte dos nove mapas.",
        "Placas, itens de chão e NPCs secundários não foram auditados nos RXDATA reais.",
    ]
    return {
        "schema": AUDIT_VERSION,
        "region": "HOENN",
        "mode": "READ_ONLY_REPOSITORY_CONTRACT",
        "source_revision": UPSTREAM,
        "source_maps": len(source_ids),
        "source_ids": list(SOURCE_MAPS),
        "public_catalog_locations": len(locations),
        "route_102_trainers": len(ROUTE_102_TRAINERS),
        "rival_pbs_variants_prepared": len(RIVAL_NAMES) * len(RIVAL_TEAMS),
        "three_physical_starter_ball_events_prepared": True,
        "rival_route103_event_prepared": True,
        "pokedex_running_shoes_handlers_prepared": True,
        "wild_route_maps": sorted(LAND_ENCOUNTERS),
        "wild_slots": sum(len(entries) for entries in LAND_ENCOUNTERS.values()),
        "map_graph_connected": seen == source_ids,
        "runtime_handlers_checked": len(required),
        "static_contract_validated": not errors,
        "native_assets_examined": False,
        "game_exe_tested": False,
        "android_tested": False,
        "errors": errors,
        "known_story_gaps": gaps,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, help="Write JSON report at this path")
    parser.add_argument("--strict", action="store_true", help="Exit 2 if any source/catalog contract fails")
    args = parser.parse_args()
    report = audit(args.root)
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"Hoenn audit written to: {args.output}")
    else:
        print(output, end="")
    return 2 if args.strict and report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
