#!/usr/bin/env python3
"""Hoenn QA 02/12: read-only physical warp and PBS border audit.

Only reads the isolated pilot copy, never native game/, saves or donor scripts.
A green report is a DATA contract, not proof of movement in Game.exe.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from hoenn_qa_phase1 import ROOT, WORK, require_private_path
from pilot_hoenn import (
    BORDERS, OFFSET_BORDERS, WARP_PAIRS, UPSTREAM, validate_pilot_mapping,
)
from hoenn_stage4 import OFFSET_BORDERS_STAGE4
from hoenn_stage5 import OFFSET_BORDERS_STAGE5
from hoenn_stage6 import OFFSET_BORDERS_STAGE6
from hoenn_stage7 import OFFSET_BORDERS_STAGE7
from hoenn_stage8 import OFFSET_BORDERS_STAGE8
from hoenn_stage9 import SURF_BORDERS_STAGE9
from hoenn_stage10 import SURF_BORDERS_STAGE10
from server.ruby_marshal import RubyObject, loads, text

SIDES = frozenset(("North", "South", "East", "West"))
OPPOSITES = {"North": "South", "South": "North",
             "East": "West", "West": "East"}
SCRIPT_WARP = re.compile(
    r"\bBlueHoennPilot\.(stage9_transfer|stage10_transfer)\("
    r"\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)"
)
# Most native RMXP transfers are code 201 with [0, map_id, x, y, direction, fade].
ALL_BORDERS = (
    *((a, ea, 0, b, eb, 0) for a, ea, b, eb in BORDERS),
    *OFFSET_BORDERS, *OFFSET_BORDERS_STAGE4, *OFFSET_BORDERS_STAGE5,
    *OFFSET_BORDERS_STAGE6, *OFFSET_BORDERS_STAGE7, *OFFSET_BORDERS_STAGE8,
    *SURF_BORDERS_STAGE9, *SURF_BORDERS_STAGE10,
)


def read_marker(copy: Path) -> tuple[dict[int, int], dict]:
    """Reject stale or fake mapping without trusting filenames alone."""
    metadata_path = copy / "Hoenn pilot.json"
    info = json.loads(metadata_path.read_text("utf-8"))
    if (info.get("region") != "HOENN" or
            info.get("kind") != "ISOLATED_HOENN_TEST" or
            info.get("source_commit") != UPSTREAM):
        raise ValueError("Relatório da cópia não corresponde à origem fixada de Hoenn")
    mapping = validate_pilot_mapping(info)
    marker = (copy / "Data/blue-hoenn-pilot.txt").read_text("ascii").splitlines()
    if (len(marker) != len(mapping) + 2 or
            marker[:2] != ["BLUE_HOENN_PILOT_V1", f"{mapping[8]},25,6"] or
            set(marker[2:]) != {f"{src},{dst}" for src, dst in mapping.items()}):
        raise ValueError("Marcador RXDATA difere da tabela remapeada")
    return mapping, info


def tile_bounds(mid: int, maps: dict[int, RubyObject], x: int, y: int) -> bool:
    obj = maps[mid]
    return (type(x) is int and type(y) is int
            and 0 <= x < obj.attrs["@width"]
            and 0 <= y < obj.attrs["@height"])


def audit_map(old: int, obj: RubyObject, all_maps: dict[int, RubyObject],
              mapping: dict[int, int]) -> dict:
    """Inspect events physically, incl. native and Blue scripted transfers."""
    if not isinstance(obj, RubyObject) or obj.name != "RPG::Map":
        raise ValueError(f"Hoenn Map{old:03}: não é RPG::Map")
    width, height = obj.attrs.get("@width"), obj.attrs.get("@height")
    if (type(width) is not int or type(height) is not int or
            not (0 < width <= 4000) or not (0 < height <= 4000)):
        raise ValueError(f"Hoenn Map{old:03}: dimensões inválidas")
    events = obj.attrs.get("@events")
    if not isinstance(events, dict):
        raise ValueError(f"Hoenn Map{old:03}: eventos RXDATA ausentes")
    ids = set(mapping.values())
    inverse = {native: donor for donor, native in mapping.items()}
    points = {}
    warps = []
    scripting = []
    for eid, ev in events.items():
        if not isinstance(ev, RubyObject) or ev.name != "RPG::Event":
            raise ValueError(f"Mapa {old}: evento {eid} não é RPG::Event")
        if type(eid) is not int or eid != ev.attrs.get("@id"):
            raise ValueError(f"Mapa {old}: índice e ID do evento divergentes ({eid})")
        ex, ey = ev.attrs.get("@x"), ev.attrs.get("@y")
        if not tile_bounds(old, all_maps, ex, ey):
            raise ValueError(f"Mapa {old}: evento {eid} fora dos limites ({ex},{ey})")
        if (ex,ey) in points:
            raise ValueError(f"Mapa {old}: eventos sobrepostos ({ex},{ey})")
        points[(ex,ey)] = eid
        for page in ev.attrs.get("@pages", []):
            if not isinstance(page, RubyObject) or page.name != "RPG::Event::Page":
                raise ValueError(f"Mapa {old}: página de evento {eid} inválida")
            for cmd in page.attrs.get("@list", []):
                if not isinstance(cmd, RubyObject) or cmd.name != "RPG::EventCommand":
                    raise ValueError(f"Mapa {old}: comando do evento {eid} inválido")
                code = cmd.attrs.get("@code")
                params = cmd.attrs.get("@parameters", [])
                if code == 201:
                    if (not isinstance(params, list) or len(params) < 4 or
                            params[0] != 0):
                        # Variable-based transfer is deliberately not called valid.
                        raise ValueError(f"Mapa {old}: transferência indireta/ilegível no evento {eid}")
                    dest, x, y = params[1:4]
                    if type(dest) is not int or dest not in ids:
                        raise ValueError(f"Mapa {old}: warp para MapID fora do piloto: {dest}")
                    donor_dest = inverse[dest]
                    if not tile_bounds(donor_dest, all_maps, x, y):
                        raise ValueError(f"Mapa {old}: warp fora dos limites: {donor_dest}/{x}/{y}")
                    warps.append((old,ex,ey,donor_dest,x,y,"native_201"))
                elif code in (355, 655):
                    for raw in params:
                        if not isinstance(raw, (bytes,str)):
                            continue
                        body = text(raw)
                        for m in SCRIPT_WARP.finditer(body):
                            src, dest, x, y = map(int, m.groups()[1:])
                            if src != old or dest not in all_maps:
                                raise ValueError(
                                    f"Mapa {old}: transferência Blue de origem/destino divergente no evento {eid}")
                            if not tile_bounds(dest, all_maps, x, y):
                                raise ValueError(
                                    f"Mapa {old}: destino Blue fora de limites: {dest}/{x}/{y}")
                            scripting.append((src,ex,ey,dest,x,y,m.group(1)))
    return {"events":len(events), "direct_warps":warps,"script_warps":scripting,
            "dimensions":[width,height]}


def inspect_connections(contents: str, mapping: dict[int, int],
                        maps: dict[int, RubyObject]) -> dict:
    """Reconcile exact intended PBS borders with the 199 remapped map IDs."""
    actual = set()
    seen = set()
    inverse = {v:k for k,v in mapping.items()}
    unrelated = 0
    for line in contents.splitlines():
        row = line.split("#", 1)[0].strip()
        if not row:
            continue
        values = [field.strip() for field in row.split(",")]
        if len(values) != 6 or not (values[0].isdecimal() and values[3].isdecimal()):
            # The compiler may support other entries in the Decades base;
            # report them without asserting they are Hoenn physical edges.
            unrelated += 1
            continue
        src, dest = int(values[0]), int(values[3])
        if src not in inverse and dest not in inverse:
            unrelated += 1
            continue
        if src not in inverse or dest not in inverse:
            raise ValueError(f"Conexão Hoenn -> mapa nativo inesperado: {row}")
        a, b = inverse[src], inverse[dest]
        side_a, side_b = values[1], values[4]
        if side_a not in SIDES or side_b not in SIDES:
            raise ValueError(f"Borda inválida em PBS: {row}")
        if OPPOSITES[side_a] != side_b:
            raise ValueError(f"Direções incompatíveis em PBS: {row}")
        try:
            off_a, off_b = int(values[2]), int(values[5])
        except ValueError as exc:
            raise ValueError(f"Deslocamento inválido em PBS: {row}") from exc
        limit_a = maps[a].attrs["@width" if side_a in ("North","South") else "@height"]
        limit_b = maps[b].attrs["@width" if side_b in ("North","South") else "@height"]
        if not (0 <= off_a < limit_a and 0 <= off_b < limit_b):
            raise ValueError(f"Deslocamento fora das dimensões do mapa: {row}")
        if min(limit_a-off_a,limit_b-off_b) < 1:
            raise ValueError(f"Sem sobreposição entre bordas: {row}")
        key = (a,side_a,off_a,b,side_b,off_b)
        if key in seen:
            raise ValueError(f"Conexão Hoenn duplicada em PBS: {row}")
        seen.add(key)
        actual.add(key)
    expected = set(ALL_BORDERS)
    if len(expected) != len(ALL_BORDERS):
        raise ValueError("Conexões planejadas Hoenn contêm duplicatas")
    if missing := expected - actual:
        raise ValueError(f"Faltam {len(missing)} conexões PBS de Hoenn: {sorted(missing)[:5]}")
    if extra := actual - expected:
        raise ValueError(f"Conexões PBS Hoenn não autorizadas: {sorted(extra)[:5]}")
    return {"verified_border_records":len(actual),
            "base_unrelated_records":unrelated,
            "surf_only_border_records":len(SURF_BORDERS_STAGE9)+len(SURF_BORDERS_STAGE10),
            "field_moves_tested_in_engine":False}



def check_required_doors(direct: list[tuple]) -> int:
    """Verify exact landing coordinates, not just destination map identity."""
    expected = {}
    for a, a_arrival, b, b_arrival in WARP_PAIRS:
        expected[(a[0],a[1],a[2],b[0])] = b_arrival[1:]
        expected[(b[0],b[1],b[2],a[0])] = a_arrival[1:]
    physical = {(mid,x,y,dest):(dx,dy)
                for mid,x,y,dest,dx,dy,kind in direct if kind == "native_201"}
    for key, landing in expected.items():
        if key not in physical:
            raise ValueError(f"Porta nativa obrigatória ausente: {key}")
        if physical[key] != landing:
            raise ValueError(
                f"Porta Hoenn {key} tem destino {physical[key]}, esperado {landing}")
    return len(expected)


def map_link_diagnostics(direct: list[tuple], scripted: list[tuple],
                         mapping: dict[int,int]) -> dict:
    """Observe only emitted transfers; never turn the planning graph into proof."""
    adjacency={src:set() for src in mapping}
    for mid,_,_,dest,*_ in (*direct,*scripted):
        if mid in adjacency and dest in adjacency:
            adjacency[mid].add(dest)
    for a,_,_,b,_,_ in ALL_BORDERS:
        if a in adjacency and b in adjacency:
            adjacency[a].add(b)
            adjacency[b].add(a)
    no_outbound = sorted(mid for mid, targets in adjacency.items() if not targets)
    return {
        "maps_without_observed_outbound_transfer":no_outbound,
        "observed_outbound_transfer_map_count":len(mapping)-len(no_outbound),
        "planned_graph_is_not_physical_proof":True,
        "custom_field_move_paths_may_not_be_discovered":True,
    }



def audit(copy: Path) -> dict:
    """Inspect only an existing generated isolated copy with all 199 maps."""
    copy = require_private_path(copy)
    mapping, info = read_marker(copy)
    infos = loads((copy / "Data/MapInfos.rxdata").read_bytes())
    if not isinstance(infos, dict):
        raise ValueError("MapInfos compilado é inválido")
    missing = [dest for dest in mapping.values() if dest not in infos]
    if missing:
        raise ValueError(f"MapInfos da cópia não contém {len(missing)} entradas")
    maps = {}
    for old, new in mapping.items():
        raw = (copy / f"Data/Map{new:03}.rxdata").read_bytes()
        obj = loads(raw)
        if not isinstance(obj, RubyObject):
            raise ValueError(f"Map{new:03} não é RXDATA")
        maps[old] = obj
    events = 0
    direct, scripted = [], []
    for old, obj in maps.items():
        data = audit_map(old, obj, maps, mapping)
        events += data["events"]
        direct.extend(data["direct_warps"])
        scripted.extend(data["script_warps"])
    required_doors = check_required_doors(direct)
    observed = map_link_diagnostics(direct, scripted, mapping)
    # Stage9/10 source transfer events are authored as BlueHoennPilot
    # stage*_transfer calls; audit only these scripts without executing them.
    counts = inspect_connections(
        (copy / "PBS/map_connections.txt").read_text("utf-8-sig"),
        mapping,maps,
    )
    if not scripted:
        raise ValueError("Cópia sem os warps autorais de Stage9/10")
    return {
        "schema":1, "region":"HOENN", "qa_phase":"02/12",
        "status":"STATIC_MAP_CONNECTIONS_AUDITED",
        "maps_read":len(maps), "mapinfo_matches":len(mapping),
        "events_indexed":events, "native_door_transfers":len(direct),
        "audited_stage9_10_transfer_scripts":len(scripted),
        "required_early_door_pairs":required_doors,
        **observed,
        **counts,
        "native_game_exe_approved":False, "android_approved":False,
        "surf_dive_waterfall_proven":False,
        "conditional_puzzles_proven":False,
        "limitations":[
            "O scanner confirma IDs, coordenadas e PBS, NÃO passabilidade 2D real.",
            "Portas ativadas por flags, transições com Ruby customizado e Dive exigem teste nativo.",
            "Grafo conectado não comprova caminho acessível sem HMs, badges ou puzzles.",
        ],
        "errors":[],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copy",type=Path,default=WORK/"hoenn-qa-fase01")
    parser.add_argument("--report",type=Path,default=WORK/"hoenn-qa-fase02-report.json")
    args = parser.parse_args(argv)
    try:
        report_path = require_private_path(args.report)
        result = audit(args.copy)
        code = 0
    except (OSError, ValueError, TypeError, KeyError, IndexError,
            json.JSONDecodeError) as exc:
        result = {"schema":1,"region":"HOENN","qa_phase":"02/12",
                  "status":"BLOCKED","native_game_exe_approved":False,
                  "errors":[str(exc)]}
        code = 2
        try:
            report_path = require_private_path(args.report)
        except ValueError:
            report_path = None
    if report_path is not None:
        report_path.parent.mkdir(parents=True,exist_ok=True)
        report_path.write_text(
            json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return code


if __name__=="__main__":
    raise SystemExit(main())
