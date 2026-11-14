"""Read-only trainer/NPC/PBS binding audit for Hoenn and Johto pilots.

The inventory is sourced from this repository, not from a Pokemon detonado.
MapIDs 625-681 are offline Johto stage IDs, not a claim of installed gameplay.
Hoenn donor MapID 102 is dynamically remapped when creating its isolated pilot.

Use --copy with a PRIVATE prepared pilot/staging directory to inspect MapXXX
and PBS trainer headers. Never modifies the source copy or installs trainers.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BINDINGS = "data/regions/trainer-event-bindings-phase1.json"
ROUTES = "data/regions/johto-stage10-routes.json"
VIOLET = "data/regions/johto-stage11-violet.json"
HOENN_BUILDER = "scripts/regions/pilot_hoenn.py"
EXPECTED = {"HOENN": 4, "JOHTO": 9}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def constants(path: Path, name: str):
    """Read a source literal only; never import/execute a pilot builder."""
    syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in syntax.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise ValueError(f"Missing constant {name} in {path}")


def audit_sources(root: Path = ROOT) -> dict:
    """Fail closed on drift in authored NPC/event/PBS source manifests."""
    baseline = read_json(root / BINDINGS)
    if baseline.get("schema") != 1 or baseline.get("state") != "NATIVE_AUDIT_PENDING_NOT_GAMEPLAY":
        raise ValueError("Invalid early trainer binding registry")
    records = baseline["records"]
    if len(records) != 13 or len({row["id"] for row in records}) != len(records):
        raise ValueError("Early trainer bindings are incomplete or duplicated")
    counts = {region: sum(t["region"] == region for t in records) for region in EXPECTED}
    if counts != EXPECTED:
        raise ValueError(f"Expected pilot counts {EXPECTED}, actual {counts}")

    source = constants(root / HOENN_BUILDER, "ROUTE_102_TRAINERS")
    route = read_json(root / ROUTES)
    violet = read_json(root / VIOLET)
    if len(source) != 4 or len(route["trainers"]) != 5 or len(violet["trainers"]) != 4:
        raise ValueError("The native pilot sources changed: review the binding inventory")
    source_text = (root / HOENN_BUILDER).read_text(encoding="utf-8")
    route_text = (root / "scripts/regions/build_johto_routes_stage10.py").read_text(encoding="utf-8")
    violet_text = (root / "scripts/regions/build_johto_violet_stage11.py").read_text(encoding="utf-8")
    route_rb = (root / "scripts/regions/JohtoRouteTrainers.rb").read_text(encoding="utf-8")
    violet_rb = (root / "scripts/regions/JohtoViolet.rb").read_text(encoding="utf-8")
    hoenn_rb = (root / "scripts/regions/HoennPilot.rb").read_text(encoding="utf-8")
    for snippet, text in (
        ('overlay["PBS/trainers_hoenn_pilot.txt"]', source_text),
        ('append_event(maps[102]', source_text),
        ("TrainerBattle.start(trainer_type, name, 102)", hoenn_rb),
        ("PBS/trainers_johto_routes.txt", route_text),
        ("BlueJohtoRouteTrainers.battle", route_text),
        ("BlueJohtoRouteTrainers", route_rb),
        ("PBS/trainers_johto_violet.txt", violet_text),
        ("BlueJohtoViolet", violet_rb),
    ):
        if snippet not in text:
            raise ValueError(f"Required event/PBS code missing: {snippet}")
    routes = {r["symbol"]: r for r in route["routes"]}
    interiors = {row["symbol"]: row for row in violet["interiors"]}
    npcs = {row["key"]: row for row in violet["npcs"]}
    types = {(r["type"], r["name"]) for r in violet["trainers"]}
    found = set()
    for x, y, trainer_type, name, sprite, team in source:
        key = f"HOENN_ROUTE102_{name.upper()}"
        row = next((r for r in records if r["id"] == key), None)
        if not row or (row["region"], row["trainer_type"], row["trainer_name"],
                       row["x"], row["y"], row["map_source_id"],
                       row["event_key"], row["versions"], row["sprite"]) != (
            "HOENN", trainer_type, name, x, y, 102, f"HN_{name}", [102], sprite
        ):
            raise ValueError(f"Hoenn Route 102 trainer binding drift: {name}")
        found.add(key)
    for trainer in route["trainers"]:
        row = next((r for r in records if r["id"] == trainer["key"]), None)
        expected = routes[trainer["symbol"]]
        if not row or (row["region"],row["trainer_type"],row["trainer_name"],
                       row["x"],row["y"],row["map_source_id"],row["map_stage_id"],
                       row["versions"],row["script_call"]) != (
            "JOHTO",trainer["trainer_type"],trainer["name"],
            trainer["x"],trainer["y"],expected["source_id"],trainer["map_id"],
            [0,1],f"BlueJohtoRouteTrainers.battle(:{trainer['key']})"
        ):
            raise ValueError(f"Johto Route trainer drift: {trainer['key']}")
        if trainer["key"] not in route_rb:
            raise ValueError(f"Johto Route trainer not registered by runtime: {trainer['key']}")
        found.add(trainer["key"])
    for trainer in violet["trainers"]:
        matching = [row for row in records if row["trainer_name"] == trainer["name"]
                    and row["region"] == "JOHTO" and row["id"] in npcs]
        if len(matching) != 1 or (trainer["type"], trainer["name"]) not in types:
            raise ValueError(f"Violet trainer binding missing: {trainer['name']}")
        row = matching[0]
        npc = npcs[row["id"]]
        if (row["map_stage_id"],row["x"],row["y"],row["script_call"],
            row["trainer_type"],row["versions"],row["sprite"]) != (
            interiors[npc["source"]]["id"],npc["x"],npc["y"],npc["handler"],
            trainer["type"],[0,1],npc["sprite"]
        ):
            raise ValueError(f"Violet trainer binding drift: {trainer['name']}")
        method = npc["handler"].split(".")[-1].split("(")[0]
        if "module BlueJohtoViolet" not in violet_rb or f"def self.{method}" not in violet_rb:
            raise ValueError(f"Violet trainer handler missing: {npc['handler']}")
        found.add(row["id"])
    if found != {r["id"] for r in records}:
        raise ValueError("Unrecognized trainer in baseline")
    # Do not allow the evidence registry to promote static data to gameplay.
    if any(r["gameplay_verified"] is not False or r["status"] not in {
        "SOURCE_AUTHORED_NEEDS_PRIVATE_NATIVE_AUDIT", "STAGED_OFFLINE_NOT_COMPILED"
    } for r in records):
        raise ValueError("Source-only binding cannot be marked playable")
    return {
        "schema": 1, "status": "STATIC_BINDINGS_MATCH_SOURCE_NOT_NATIVE_GAMEPLAY",
        "source_count": counts, "authored_npc_bindings": len(records),
        "missing_event_candidates": baseline.get("missing_event_candidates", []),
        "native_copy_inspected": False,
        "entries": [{"id":r["id"],"region":r["region"],"name":r["trainer_name"],
                     "area":r["area"],"map_stage_id":r["map_stage_id"],
                     "map_source_id":r["map_source_id"],"event_key":r["event_key"],
                     "status":r["status"],"gameplay_verified":False} for r in records],
    }


def native_map_id(row: dict, copy: Path) -> int | None:
    if row["region"] == "JOHTO":
        return row["map_stage_id"]
    meta = copy / "Hoenn pilot.json"
    if not meta.is_file() or meta.is_symlink():
        return None
    payload = read_json(meta)
    if payload.get("region") != "HOENN" or payload.get("kind") != "ISOLATED_HOENN_TEST":
        raise ValueError("Invalid Hoenn pilot marker; cannot map donor IDs")
    value = payload.get("maps", {}).get(str(row["map_source_id"]))
    if not isinstance(value, int) or not (1 <= value <= 999):
        raise ValueError("Hoenn pilot map remap missing or invalid")
    return value


def trainer_headers(copy: Path) -> set[tuple[str, str, int]]:
    pbs = copy / "PBS"
    if not pbs.is_dir() or pbs.is_symlink():
        return set()
    result = set()
    for file in sorted(pbs.glob("trainers*.txt")):
        if file.is_symlink():
            raise ValueError("PBS trainer symlink not allowed")
        for header in re.findall(r"(?m)^\s*\[([^\]\r\n]+)\]", file.read_text(encoding="utf-8-sig")):
            parts = [p.strip() for p in header.split(",")]
            if len(parts) in (2,3) and (len(parts)==2 or parts[2].isdigit()):
                result.add((parts[0],parts[1],int(parts[2]) if len(parts)==3 else 0))
    return result


def extract_events(map_path: Path) -> list[dict]:
    from server.ruby_marshal import loads, text
    root = loads(map_path.read_bytes())
    if getattr(root, "name", None) != "RPG::Map":
        raise ValueError("Expected RPG::Map")
    result = []
    for event in root.attrs.get("@events", {}).values():
        script = []
        for page in event.attrs.get("@pages", []):
            for command in page.attrs.get("@list", []):
                if command.attrs.get("@code") in (355,655):
                    script.extend(text(x) for x in command.attrs.get("@parameters", []) if x is not None)
        result.append({"name":text(event.attrs["@name"]),
                       "x":event.attrs["@x"],"y":event.attrs["@y"],
                       "script":"\n".join(script)})
    return result


def inspect_private_copy(report: dict, registry: dict, copy: Path) -> dict:
    """Check private RXDATA/PBS bytes. Never write in this game directory."""
    if not copy.is_dir() or copy.is_symlink():
        raise ValueError("Provide a real non-symlinked isolated pilot or stage directory")
    headers = trainer_headers(copy)
    records = {r["id"]:r for r in registry["records"]}
    cache = {}
    results = []
    for existing in report["entries"]:
        row = records[existing["id"]]
        map_id = native_map_id(row, copy)
        map_path = copy / "Data" / f"Map{map_id:03d}.rxdata" if map_id else None
        found = False
        errors = []
        if not map_path or not map_path.is_file():
            errors.append("MAP_NOT_IN_COPY_OR_UNMAPPED")
        elif map_path.is_symlink():
            raise ValueError("Map file symlink not allowed")
        else:
            if map_id not in cache:
                cache[map_id] = extract_events(map_path)
            events = [e for e in cache[map_id] if
                      e["name"] == row["event_key"] and
                      (e["x"],e["y"]) == (row["x"],row["y"]) and
                      row["script_call"] in e["script"]]
            if len(events) != 1:
                errors.append("EVENT_OR_HANDLER_MISSING_OR_DUPLICATE")
            else:
                found = True
        missing_versions = [v for v in row["versions"] if
                            (row["trainer_type"],row["trainer_name"],v) not in headers]
        if missing_versions:
            errors.append("PBS_TRAINER_VERSION_MISSING")
        results.append({**existing, "resolved_map_id":map_id,
                        "event_verified_in_copy":found,
                        "pbs_headers_verified_in_copy":not missing_versions,
                        "missing_versions":missing_versions, "errors":errors,
                        "native_compilation_verified":False,
                        "playtested_in_game":False, "gameplay_verified":False})
    report = {**report, "native_copy_inspected":True,"entries":results}
    report["byte_level_bindings_found"] = sum(
        x["event_verified_in_copy"] and x["pbs_headers_verified_in_copy"] for x in results
    )
    report["status"] = "PRIVATE_MAP_AND_PBS_AUDIT_ONLY_NO_GAMEPLAY_PROOF"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--scope", choices=("ALL","HOENN","JOHTO","JOHTO_ROUTES","JOHTO_VIOLET"),
                        default="ALL", help="Check only the specified regional private pilot segment")
    parser.add_argument("--copy", type=Path,
                        help="PRIVATE isolated stage/pilot (read-only inspection; optional)")
    parser.add_argument("--output", type=Path, help="JSON report outside any game copy")
    parser.add_argument("--strict", action="store_true",
                        help="Fail if a supplied private copy lacks an event/PBS binding")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    registry = read_json(root / BINDINGS)
    report = audit_sources(root)
    if args.scope != "ALL":
        report["entries"] = [row for row in report["entries"] if (
            row["region"] == args.scope or
            (args.scope == "JOHTO_ROUTES" and row["id"].startswith("JH_ROUTE")) or
            (args.scope == "JOHTO_VIOLET" and row["region"] == "JOHTO" and
             not row["id"].startswith("JH_ROUTE"))
        )]
        report["scope"] = args.scope
    if args.copy:
        copy = args.copy.resolve(strict=True)
        report = inspect_private_copy(report, registry, copy)
    if args.output:
        target = args.output.resolve()
        if args.copy and (target == copy or target.is_relative_to(copy)):
            raise ValueError("Report output must not modify the game copy")
        if target.is_relative_to(root / "game"):
            raise ValueError("Do not write reports under live game/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(f"Audit saved: {target}")
    else:
        print(json.dumps(report,ensure_ascii=False,indent=2))
    if args.strict and args.copy and any(e["errors"] for e in report["entries"]):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
