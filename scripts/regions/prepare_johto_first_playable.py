"""Single-command, READ-ONLY game preflight for Johto's first playable area.

Builds native-ID-safe Johto geometry and remapped connection PBS under
.blue-work/. It NEVER writes game/, unlocks Testar Johto, or claims QA.
New Bark interiors and spawn remain blocked until manually reviewed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from audit_johto import ROOT, audit, checksum, write_report
from compile_johto_connections import build as build_connections, write_preview
from plan_johto import plan, read_json
from prepare_johto_source import prepare as unpack
from stage_johto import stage
from verify_johto import inspect

SOURCE = "data/regions/johto-source.json"
GRAPH = "data/regions/johto-v1-map-connections.json"


def run(*, root: Path = ROOT) -> dict:
    root = root.resolve()
    work = root / ".blue-work"
    game = root / "game"
    source = work / "johto-source"
    archive = source / "original.zip"
    extracted = source / "project"
    auditor = work / "johto-audit.json"
    allocation = work / "johto-map-plan.json"
    preview = work / "johto-staging"
    connections = work / "johto-connections-preview.txt"
    readiness = work / "johto-first-playable-readiness.json"
    if work.is_symlink() or source.is_symlink() or game.is_symlink():
        raise ValueError("Johto source/work/game symlinks are not permitted")
    if not archive.is_file() or archive.is_symlink():
        raise FileNotFoundError("Coloque o Map Pack v1 em .blue-work/johto-source/original.zip")
    if not (game / "Data/MapInfos.rxdata").is_file() or not (
            game / "Data/Tilesets.rxdata").is_file():
        raise FileNotFoundError(
            "Falta game/Data de Blue/Decades; nao e possivel alocar MapIDs seguros")
    manifest = read_json(root / SOURCE)
    wanted_sha = manifest.get("source", {}).get("archive_sha256")
    if checksum(archive) != wanted_sha:
        raise ValueError("ZIP v1 nao corresponde ao SHA-256 publicado em johto-source.json")
    for path in (auditor, allocation, preview, connections, readiness):
        if path.exists() or path.is_symlink():
            raise ValueError("Saida ja existe; preservar auditoria anterior: " + str(path))
    if extracted.exists():
        marker = extracted / "johto-source-extraction.json"
        if not marker.is_file() or marker.is_symlink():
            raise ValueError("Extracao preexistente sem manifesto verificavel")
        proof = read_json(marker)
        if proof.get("source_archive_sha256") != wanted_sha:
            raise ValueError("A extracao nao corresponde ao ZIP original auditado")
    else:
        # Only RMXP and PNG data, no source Ruby/EXE, unpacked into ignored work.
        unpack(archive, extracted, root=root)
    # All subsequent steps only READ game/; every output stays in .blue-work.
    result = audit(source, root / SOURCE, game=game, archive=archive)
    if not result.get("archive_hash_pinned_and_verified"):
        raise ValueError("Arquivo-fonte nao auditado")
    write_report(auditor, result)
    graph = read_json(root / GRAPH)
    proposed = plan(manifest, result)
    if proposed.get("status") != "READY_FOR_GEOMETRY_PREVIEW":
        raise ValueError("MapIDs da previa bloqueados: " +
                         ", ".join(proposed.get("blocking_reasons", [])))
    write_report(allocation, proposed)
    staged = stage(root=root, source=source, game=game, archive=archive,
                   output=preview, manifest_path=root / SOURCE,
                   audit_path=auditor, plan_path=allocation)
    verified = inspect(preview, game, root=root)
    content, conns = build_connections(preview, game, graph, manifest, root=root)
    write_preview(connections, content, root=root)
    remap = proposed["mapping"]
    status = {
        "schema": 1, "region": "JOHTO",
        "status": "GEOMETRY_READY_NEW_BARK_PLAYABILITY_PENDING",
        "maps_staged": len(staged["maps"]), "connections_generated": conns["compiled_count"],
        "gameplay_playable": False, "gameplay_tested": False,
        "game_files_modified": 0, "can_install": False,
        "source_archive_sha256": wanted_sha,
        "new_bark_source_id": 79, "new_bark_destination_id": remap["79"],
        "route_29_source_id": 104, "route_29_destination_id": remap["104"],
        "cherrygrove_source_id": 80, "cherrygrove_destination_id": remap["80"],
        "verified_geometry": verified["status"],
        "missing_before_playable": [
            "Criar e inspecionar os 3 interiores a partir de templates nativos",
            "Revisar sprites e coordenadas reais dos 12 eventos de New Bark",
            "Confirmar passabilidade de spawn, portas e conexoes de borda",
            "Construir Route 29 -> Cherrygrove (nao existe no PBS do ZIP)",
            "Compilar rival/PBS e executar Game.exe da copia isolada",
            "Testar save/reload e manter Kanto/Decades intactos"
        ],
        "outputs": {
            "audit": str(auditor.relative_to(root)),
            "plan": str(allocation.relative_to(root)),
            "preview": str(preview.relative_to(root)),
            "connections": str(connections.relative_to(root))
        }
    }
    write_report(readiness, status)
    return status


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        data = run(root=args.root)
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print("[JOHTO][BLOQUEADO] " + str(exc), file=sys.stderr)
        print("[JOHTO] Game.exe e saves originais nao foram modificados.", file=sys.stderr)
        return 2
    print("[JOHTO] Mapas:", data["maps_staged"], "Conexoes:", data["connections_generated"])
    print("[JOHTO] New Bark ID no piloto:", data["new_bark_destination_id"])
    print("[JOHTO] Status:", data["status"])
    print("[JOHTO] Proximo: construir interiores, configurar eventos e testar Game.exe isolado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
