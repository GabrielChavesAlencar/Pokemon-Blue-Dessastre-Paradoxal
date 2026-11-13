"""Compile six static-checked New Bark stair/door warps into an ISOLATED Johto preview.

Never touches installed game/, Kanto, Decades, saves or Game.exe.
The generated warp events are own RGSS data (code 201, no Ruby scripts).
Coordinates are PROPOSALS, not engine-verified walkability.
Stage 08 must merge story/initial events without duplicating these warps.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from audit_johto import ROOT, checksum, read_map_data
from build_johto_elm_lab_v1 import table_values
from build_johto_events import EVENT_CLASSES, event_page, ruby
from stage import serialize
from verify_johto import inspect
from server.ruby_marshal import RubyData, RubyObject, loads

DEFAULT_SPEC = ROOT / "data/regions/johto-stage07-warps.json"
DEFAULT_PREVIEW = ROOT / ".blue-work/johto-staging-elm-lab-v1"
DEFAULT_OUTPUT = ROOT / ".blue-work/johto-staging-warps-v1"
DEFAULT_CONNECTIONS = ROOT / ".blue-work/johto-connections-preview.txt"

EXPECTED = {
    "JH_HOME2F_TO_1F": ("JOHTO_NEW_BARK_PLAYER_HOME_2F", "JOHTO_NEW_BARK_PLAYER_HOME_1F"),
    "JH_HOME1F_TO_2F": ("JOHTO_NEW_BARK_PLAYER_HOME_1F", "JOHTO_NEW_BARK_PLAYER_HOME_2F"),
    "JH_HOME1F_TO_TOWN": ("JOHTO_NEW_BARK_PLAYER_HOME_1F", "JOHTO_NEW_BARK_TOWN"),
    "JH_TOWN_TO_HOME1F": ("JOHTO_NEW_BARK_TOWN", "JOHTO_NEW_BARK_PLAYER_HOME_1F"),
    "JH_TOWN_TO_ELM_LAB": ("JOHTO_NEW_BARK_TOWN", "JOHTO_NEW_BARK_ELM_LAB"),
    "JH_LAB_TO_TOWN": ("JOHTO_NEW_BARK_ELM_LAB", "JOHTO_NEW_BARK_TOWN"),
}
REQUIRED_ORIGINS = {
    "JOHTO_NEW_BARK_PLAYER_HOME_2F": "BLUE_AUTHORED_OFFLINE_BEDROOM_V1",
    "JOHTO_NEW_BARK_PLAYER_HOME_1F": "BLUE_AUTHORED_OFFLINE_HOME1F_V1",
    "JOHTO_NEW_BARK_ELM_LAB": "BLUE_AUTHORED_OFFLINE_ELM_LAB_V1",
}
TOWN = "JOHTO_NEW_BARK_TOWN"
ROUTE = "JOHTO_ROUTE_29"
HASH = re.compile(r"^[0-9a-f]{64}$")
CONNECTION = re.compile(r"^\d+,(North|South|East|West),\d+,\d+,(North|South|East|West),\d+$")


def fail(message: str):
    raise ValueError("[JOHTO][OFFLINE 07] " + message)


@dataclass(frozen=True)
class Grid:
    width: int
    height: int
    cells: tuple[int, ...]
    passages: tuple[int, ...]

    def walkable(self, x: int, y: int) -> bool:
        if (type(x) is not int or type(y) is not int
                or not 0 <= x < self.width or not 0 <= y < self.height):
            return False
        for z in range(3):
            tile = self.cells[x + self.width * (y + self.height * z)]
            if tile < 0 or tile >= len(self.passages) or (self.passages[tile] & 0x0F):
                return False
        return True

    def reachable(self, start: tuple[int, int]) -> set[tuple[int, int]]:
        if not self.walkable(*start):
            fail("Ponto de partida bloqueado pela tabela estática: " + str(start))
        reached, todo = {start}, [start]
        while todo:
            x, y = todo.pop()
            for candidate in ((x-1,y), (x+1,y), (x,y-1), (x,y+1)):
                if candidate not in reached and self.walkable(*candidate):
                    reached.add(candidate)
                    todo.append(candidate)
        return reached


def read_grid(path: Path, tilesets: list) -> tuple[RubyObject, Grid]:
    room = read_map_data(path)
    if not isinstance(room, RubyObject) or room.name != "RPG::Map":
        fail("Dados RPG::Map ausentes: " + path.name)
    if room.attrs.get("@events") != {}:
        fail("Mapa já possui eventos: recusar duplicação de warps em " + path.name)
    width, height, tid = (room.attrs.get("@width"), room.attrs.get("@height"),
                          room.attrs.get("@tileset_id"))
    if (any(type(n) is not int for n in (width, height, tid))
            or width < 5 or height < 5 or not 0 < tid < len(tilesets)):
        fail("Dimensões/tileset incorretos em " + path.name)
    tile = tilesets[tid]
    raw = room.attrs.get("@data")
    passage = tile.attrs.get("@passages") if isinstance(tile, RubyObject) else None
    if (not isinstance(raw, RubyData) or raw.name != "Table"
            or not isinstance(passage, RubyData) or passage.name != "Table"):
        fail("Mapa ou tileset sem RGSS Table: " + path.name)
    shape, cells = table_values(raw.data, dimension=3)
    pshape, flags = table_values(passage.data, dimension=1)
    if shape != (width, height, 3) or pshape[1:] != (1, 1) or max(cells, default=0) >= len(flags):
        fail("RGSS Table/flags inconsistentes: " + path.name)
    return room, Grid(width, height, cells, flags)


def compile_plan(spec: dict, ids: dict[str, int], grids: dict[str, Grid],
                 connections: str) -> dict:
    if (spec.get("schema"), spec.get("region"), spec.get("status")) != (
            1, "JOHTO", "STATIC_WARP_COORDINATES_PROPOSED_NOT_ENGINE_VERIFIED"):
        fail("Especificação de warps desconhecida")
    if not ({TOWN, ROUTE} | {x for pair in EXPECTED.values() for x in pair}) <= set(ids):
        fail("MapID/símbolo de Johto faltando")
    if any(type(mid) is not int or not 600 <= mid <= 999 for mid in ids.values()):
        fail("MapID fora do namespace Johto")
    warps = spec.get("warps")
    if not isinstance(warps, list) or len(warps) != 6:
        fail("Exatamente seis warps autorizados")
    keys = [w.get("key") for w in warps if isinstance(w, dict)]
    if len(set(keys)) != 6 or set(keys) != set(EXPECTED):
        fail("Chaves de warps desconhecidas/duplicadas")
    by_key = {w["key"]: w for w in warps}
    occupied: dict[str, set[tuple[int, int]]] = {sym: set() for sym in grids}
    anchor_points: dict[str, set[tuple[int, int]]] = {sym: set() for sym in grids}
    target_points: dict[str, set[tuple[int, int]]] = {sym: set() for sym in grids}
    for w in warps:
        key = w["key"]
        src, dst = EXPECTED[key]
        if ((w.get("source"), w.get("target")) != (src, dst)
                or w.get("verified_in_engine") is not False):
            fail("Warp mal classificado ou marcado como testado: " + key)
        for field in ("x","y","arrival_x","arrival_y"):
            if type(w.get(field)) is not int:
                fail("Coordenadas precisam ser inteiros: " + key)
        xy, arrival = (w["x"], w["y"]), (w["arrival_x"], w["arrival_y"])
        if not grids[src].walkable(*xy) or not grids[dst].walkable(*arrival):
            fail("Trigger/chegada sem passabilidade estática: " + key)
        if xy in occupied[src]:
            fail("Dois warps na mesma célula: " + key)
        occupied[src].add(xy)
        anchor_points[src].add(xy)
        anchor_points[dst].add(arrival)
        target_points[dst].add(arrival)
        reverse = by_key.get(w.get("reverse_key"))
        if (not isinstance(reverse, dict) or reverse.get("reverse_key") != key or
                reverse.get("source") != dst or reverse.get("target") != src):
            fail("Warp sem retorno pareado: " + key)
    for sym, arrivals in target_points.items():
        if arrivals & occupied[sym]:
            fail("Chegada sobre um gatilho de warp (loop imediato): " + sym)

    start = spec.get("spawn")
    if (not isinstance(start, dict)
            or start.get("symbol") != "JOHTO_NEW_BARK_PLAYER_HOME_2F"
            or start.get("verified_in_engine") is not False
            or type(start.get("x")) is not int or type(start.get("y")) is not int):
        fail("Spawn de 2F ausente/inadequadamente aprovado")
    spawn = (start["x"], start["y"])
    if spawn in occupied[start["symbol"]] or not grids[start["symbol"]].walkable(*spawn):
        fail("Spawn sobre bloqueio/gatilho")
    anchor_points[start["symbol"]].add(spawn)
    reach = {}
    for sym, points in anchor_points.items():
        if not points:
            continue
        connected = grids[sym].reachable(next(iter(sorted(points))))
        if not points <= connected:
            fail("Portas e chegadas do mapa não estão conectadas nos tiles: " + sym)
        reach[sym] = len(connected)

    # New Bark/Route 29 already uses map_connections PBS, NEVER a duplicate event.
    border = spec.get("border_connection")
    expected = f"{ids[TOWN]},West,13,{ids[ROUTE]},East,0"
    reverse = f"{ids[ROUTE]},East,0,{ids[TOWN]},West,13"
    if (not isinstance(border, dict)
            or border.get("method") != "PBS_MAP_CONNECTION_NOT_EVENT"
            or border.get("verified_in_engine") is not False
            or border.get("format") != "{a},West,13,{b},East,0"):
        fail("Fronteira New Bark / Route 29 não é PBS")
    records = [line.split("#",1)[0].strip().replace(" ", "")
               for line in connections.splitlines()]
    lines = [line for line in records if line]
    if not lines or any(CONNECTION.fullmatch(line) is None for line in lines):
        fail("PBS de conexões inválido")
    duplicates = [line for line in lines if line in (expected, reverse)]
    if len(duplicates) != 1:
        fail("Conexão New Bark/Route29 faltando ou duplicada no PBS")
    # Reject even another offset between the same two maps.
    for line in lines:
        fields = line.split(",")
        if {fields[0], fields[3]} == {str(ids[TOWN]), str(ids[ROUTE])} and line not in duplicates:
            fail("Conexão da fronteira duplicada com offsets diferentes")
    if any(x.get("gameplay_playable") is not False for x in (spec.get("status_policy", {}),)):
        fail("Fonte da fase 7 não pode marcar jogabilidade aprovada")
    return {
        "schema": 1, "region": "JOHTO",
        "status": "SIX_BLUE_WARPS_STATIC_AUDIT_NOT_ENGINE_TESTED",
        "can_install": False, "not_playable": True,
        "tested_in_game": False, "gameplay_playable": False,
        "map_ids": {key: ids[key] for key in sorted(anchor_points)},
        "spawn_proposal": start,
        "warps": [{**w, "source_id": ids[w["source"]],
                    "destination_id": ids[w["target"]], "static_passability_verified": True}
                  for w in warps],
        "static_reachable_tiles": reach,
        "edge_connection_pbs": duplicates[0],
        "edge_connection_engine_verified": False,
        "story_npcs_compiled": 0,
        "warning": "Eventos do tipo warp compilados em prévia isolada; Game.exe, sprites, save e história pendentes.",
    }


def build(*, root: Path = ROOT, preview: Path | None = None,
          output: Path | None = None, spec_path: Path | None = None,
          connections_path: Path | None = None) -> dict:
    root = root.resolve()
    work = (root / ".blue-work").resolve()
    preview = (preview or DEFAULT_PREVIEW).absolute()
    output = (output or DEFAULT_OUTPUT).absolute()
    spec_path = (spec_path or DEFAULT_SPEC).absolute()
    connections_path = (connections_path or DEFAULT_CONNECTIONS).absolute()
    game = root / "game"
    if (work.is_symlink() or preview.is_symlink() or output.is_symlink()
            or connections_path.is_symlink() or output.exists()
            or not preview.resolve().is_relative_to(work)
            or not connections_path.resolve().is_relative_to(work)
            or not output.resolve().is_relative_to(work)
            or output.resolve() in (work, preview.resolve())
            or output.resolve().is_relative_to(preview.resolve())
            or preview.resolve().is_relative_to(output.resolve())):
        fail("Entradas/saída devem ser distintas e seguras em .blue-work/")
    if inspect(preview, game, root=root).get("status") != "STRUCTURAL_PREVIEW_VALIDATED_NOT_PLAYABLE":
        fail("Prévia original de 77 mapas não aprovada estruturalmente")
    stage = json.loads((preview / "johto-stage.json").read_text(encoding="utf-8"))
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if (stage.get("status"), stage.get("can_install"), stage.get("not_playable")) != (
            "GEOMETRY_PREVIEW_ONLY", False, True):
        fail("Stage de origem não é apenas geometria")
    ids = {row["symbol"]: row["destination_id"] for row in stage["maps"]}
    if len(ids) != len(stage["maps"]) or len(set(ids.values())) != len(ids):
        fail("MapIDs duplicados no stage de origem")
    by_symbol = {row["symbol"]: row for row in stage["maps"]}
    if any(by_symbol.get(sym, {}).get("origin") != origin
           for sym, origin in REQUIRED_ORIGINS.items()):
        fail("Etapas offline 04, 05 e 06 não encontradas na fonte")
    source_tiles = read_map_data(preview / "Data/Tilesets.rxdata")
    if not isinstance(source_tiles, list):
        fail("Tilesets de Johto não são um array RMXP")
    relevant = {x for pair in EXPECTED.values() for x in pair}
    rooms = {}
    grids = {}
    for sym in sorted(relevant):
        map_file = preview / "Data" / f"Map{ids[sym]:03d}.rxdata"
        rooms[sym], grids[sym] = read_grid(map_file, source_tiles)
    plan = compile_plan(spec, ids, grids,
                        connections_path.read_text(encoding="utf-8"))
    rebuilt = {}
    for sym in sorted(relevant):
        rows = [w for w in plan["warps"] if w["source"] == sym]
        if not rows:
            continue
        room = copy.deepcopy(rooms[sym])
        events = {}
        for index, w in enumerate(rows, 1):
            page = event_page(warp=(w["destination_id"], w["arrival_x"], w["arrival_y"]),
                              touch=True)
            events[index] = ruby("RPG::Event", id=index,
                                 name=w["key"].encode("ascii"), x=w["x"], y=w["y"],
                                 pages=[page])
        room.attrs["@events"] = events
        binary = serialize(room, EVENT_CLASSES)
        reloaded = loads(binary)
        commands = [e.attrs["@pages"][0].attrs["@list"][0]
                    for e in reloaded.attrs["@events"].values()]
        if (len(commands) != len(rows) or any(
                c.attrs.get("@code") != 201 or c.attrs.get("@parameters")[:2] !=
                [0, rows[i]["destination_id"]] or
                c.attrs.get("@parameters")[2:4] != [rows[i]["arrival_x"], rows[i]["arrival_y"]]
                for i, c in enumerate(commands))):
            fail("Roundtrip Ruby Marshal alterou os eventos de warp: " + sym)
        rebuilt[ids[sym]] = binary

    report = dict(plan)
    report["source_archive_sha256"] = stage["source_archive_sha256"]
    report["source_stage_manifest_sha256"] = checksum(preview / "johto-stage.json")
    report["input_map_sha256"] = {
        str(mid): checksum(preview / "Data" / f"Map{mid:03d}.rxdata")
        for mid in rebuilt
    }
    report["warped_map_sha256"] = {
        str(mid): hashlib.sha256(binary).hexdigest()
        for mid, binary in rebuilt.items()
    }
    report["original_stage_maps_preserved"] = len(stage["maps"]) - len(rebuilt)
    if len(rebuilt) != 4 or len(stage["maps"]) != 77:
        fail("A etapa 07 só pode alterar 4 dos 77 mapas")
    new_manifest = copy.deepcopy(stage)
    new_manifest["status"] = "BLUE_WARP_PREVIEW_ONLY_NOT_PLAYABLE"
    new_manifest["not_playable"] = True
    new_manifest["can_install"] = False
    new_manifest["static_warp_preview"] = {
        "manifest": "johto-warp-preview.json",
        "warps_added": len(plan["warps"]), "maps_modified": len(rebuilt),
        "gameplay_playable": False, "tested_in_game": False,
    }
    for row in new_manifest["maps"]:
        if row["destination_id"] in rebuilt:
            row["blue_authored_warps"] = sum(
                x["source_id"] == row["destination_id"] for x in plan["warps"])
            # events_imported is 0: zero third-party events imported.
    new_manifest["warnings"].append(
        "Etapa 07: somente warps autorais; geometria original e saves preservados."
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".johto-warp-stage-", dir=output.parent) as temp:
        target = Path(temp) / "stage"
        shutil.copytree(preview, target)
        for mid, blob in rebuilt.items():
            (target / "Data" / f"Map{mid:03d}.rxdata").write_bytes(blob)
        (target / "johto-stage.json").write_text(
            json.dumps(new_manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        (target / "johto-warp-preview.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        # Strong post-copy guards: no native geometry/MapInfos/Tilesets changed.
        for name in ("MapInfos.rxdata", "Tilesets.rxdata"):
            if checksum(preview / "Data" / name) != checksum(target / "Data" / name):
                fail("Metadados nativos alterados: " + name)
        for row in stage["maps"]:
            mid = row["destination_id"]
            if mid not in rebuilt and checksum(preview / "Data" / f"Map{mid:03d}.rxdata") != (
                    checksum(target / "Data" / f"Map{mid:03d}.rxdata")):
                fail("Mapa fora de New Bark alterado")
        if output.exists() or output.is_symlink():
            fail("Diretório de saída passou a existir; impedir overwrite")
        target.rename(output)
    return report


def main(argv=None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--root", type=Path, default=ROOT)
    cli.add_argument("--preview", type=Path)
    cli.add_argument("--output", type=Path)
    cli.add_argument("--spec", type=Path)
    cli.add_argument("--connections", type=Path)
    args = cli.parse_args(argv)
    try:
        result = build(root=args.root, preview=args.preview, output=args.output,
                       spec_path=args.spec, connections_path=args.connections)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("[JOHTO][BLOQUEADO]", error, file=sys.stderr)
        return 2
    print("[JOHTO] Seis warps autorais em quatro mapas de New Bark (PREVIA ISOLADA).")
    print("[JOHTO] Spawn estático proposto:", result["spawn_proposal"])
    print("[JOHTO] New Bark/Route29 via PBS:", result["edge_connection_pbs"])
    print("[JOHTO] Game.exe, game/ e saves não modificados; testadas 0/13.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
