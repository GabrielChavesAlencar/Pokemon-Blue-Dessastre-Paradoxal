#!/usr/bin/env python3
"""Read-only graph of Sinnoh's REAL RMXP map transfers.

Requires audit_sinnoh_rxdata (inert Ruby Marshal parser). Does not create maps,
assign IDs, import scripts or modify the source, game or saves. Optional
--start-map must be a verified donor MapID; no fictional Twinleaf ID assumed.
"""
from __future__ import annotations

import argparse
from collections import deque
import json
import sys
from pathlib import Path

from audit_sinnoh_rxdata import audit_rxdata


def make_graph(audit: dict, start_map: int | None = None) -> dict:
    if (audit.get("region"), audit.get("mode"), audit.get("import_allowed")) != (
        "SINNOH", "READ_ONLY_INERT_RMXP", False
    ):
        raise ValueError("O grafo exige auditoria RXDATA Sinnoh inerte")
    rows = audit.get("maps")
    if not isinstance(rows, list) or not rows or len(rows) > 5000:
        raise ValueError("Auditoria sem inventário de mapas válido")
    found: dict[int, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Entrada de mapa inválida")
        mid = row.get("source_id")
        if type(mid) is not int or mid <= 0 or mid in found:
            raise ValueError("MapID de origem inválido ou repetido")
        edges = row.get("transfer_targets")
        if (not isinstance(edges, list) or len(edges) > 5000
                or any(type(dst) is not int or dst < 0 for dst in edges)):
            raise ValueError("Transferências sem formato estático válido")
        if len(set(edges)) != len(edges):
            raise ValueError("Transferência duplicada no mapa")
        found[mid] = row
    if set(found) != set(audit.get("source_map_ids", [])):
        raise ValueError("Inventário de mapas diverge da auditoria RXDATA")
    if start_map is not None and (type(start_map) is not int or start_map not in found):
        raise ValueError("Mapa inicial deve ser ID REAL presente na fonte")

    ids = set(found)
    edges: list[dict] = []
    adjacency: dict[int, set[int]] = {i: set() for i in ids}
    reverse: dict[int, set[int]] = {i: set() for i in ids}
    dangling: set[int] = set()
    for mid, row in sorted(found.items()):
        for target in sorted(row["transfer_targets"]):
            valid = target in ids
            edges.append({
                "from_source_id": mid, "to_source_id": target,
                "from_name": row.get("name", ""),
                "to_name": found[target].get("name", "") if valid else None,
                "source_present": True, "target_present": valid
            })
            if valid:
                adjacency[mid].add(target)
                reverse[target].add(mid)
            else:
                dangling.add(target)
    reported = audit.get("unresolved_static_transfer_ids")
    if reported is not None and set(reported) != dangling:
        raise ValueError("Referências ausentes divergentes da auditoria RXDATA")

    # Connectivity is directional; one-way warps and scripted transitions may
    # be intentional. An unreachable map is only a manual-review candidate.
    reachable: set[int] | None = None
    if start_map is not None:
        reachable = set()
        queue = deque([start_map])
        while queue:
            mid = queue.popleft()
            if mid in reachable:
                continue
            reachable.add(mid)
            queue.extend(sorted(adjacency[mid] - reachable))

    # Weakly connected groups help locate disconnected islands without claiming
    # the campaign is broken. Dynamic/scripted warps are intentionally omitted.
    groups = []
    unseen = set(ids)
    while unseen:
        seed = min(unseen)
        group = set()
        queue = deque([seed])
        while queue:
            mid = queue.popleft()
            if mid in group:
                continue
            group.add(mid)
            unseen.discard(mid)
            queue.extend(sorted((adjacency[mid] | reverse[mid]) - group))
        groups.append(sorted(group))

    nodes = []
    for mid in sorted(found):
        nodes.append({
            "source_id": mid,
            "name": found[mid].get("name", ""),
            "inbound_count": len(reverse[mid]),
            "outbound_count": len(adjacency[mid]),
            "dangling_outbound": sorted(set(found[mid]["transfer_targets"]) - ids),
            "is_isolated_in_static_graph": not (adjacency[mid] or reverse[mid]),
            "reachable_from_selected_start": mid in reachable if reachable is not None else None,
        })
    return {
        "schema": 1, "region": "SINNOH", "mode": "STATIC_MAP_GRAPH_NO_INSTALL",
        "map_count": len(ids), "static_transfer_count": len(edges),
        "static_valid_transfer_count": sum(1 for e in edges if e["target_present"]),
        "dangling_target_ids": sorted(dangling),
        "isolated_map_ids": sorted(i for i in ids if not adjacency[i] and not reverse[i]),
        "weakly_connected_groups": groups,
        "start_map_selected": start_map,
        "unreachable_from_selected_start": (
            sorted(ids - reachable) if reachable is not None else None),
        "dynamic_transfer_commands_needing_manual_review":
            audit.get("dynamic_transfer_commands", 0),
        "untrusted_script_commands_not_executed":
            audit.get("untrusted_script_commands_not_executed", 0),
        "missing_mapinfos_ids": audit.get("missing_map_files", []),
        "orphan_map_file_ids": audit.get("orphan_map_files", []),
        "nodes": nodes, "edges": edges,
        "safe_to_install": False, "map_ids_allocated": False,
        "note": (
            "Graph includes ONLY literal transfer commands in map event pages. "
            "Scripted/common-event/variable transfers, conditional access, "
            "doors without transfer commands, walkability and save/load require "
            "separate audits. Do not treat disconnected maps as definite bugs "
            "or use this graph as permission to import source assets."
        )
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="ZIP autorizado ou diretório fonte RMXP; apenas leitura")
    parser.add_argument("--game-data", type=Path,
                        help="Pasta game/Data local; apenas comparação de IDs")
    parser.add_argument("--start-map", type=int,
                        help="MapID inicial REAL confirmado pelo MapInfos doador")
    args = parser.parse_args(argv)
    try:
        graph = make_graph(audit_rxdata(args.source, args.game_data), args.start_map)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("SINNOH_GRAPH_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(graph, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
