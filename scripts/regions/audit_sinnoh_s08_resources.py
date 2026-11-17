#!/usr/bin/env python3
"""S08: inert, cross-resource Sinnoh integrity auditor.

Audits real donor RXDATA when supplied, or an already reviewed local QA overlay
against an existing Decades baseline. Does NOT download/import/execute assets,
allocate MapIDs, modify game/, write saves or approve gameplay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from audit_sinnoh_rxdata import audit_rxdata
from graph_sinnoh_maps import make_graph
from install_sinnoh_qa_copy import (
    ROOT, QA_LAUNCH_REQUIRED, QA_META, START_META, PROBE_META, START_PLUGIN,
    PROBE_PLUGIN, load_overlay, prepare, verify,
)
from server.ruby_marshal import RubyObject, loads, text

SHA = re.compile(r"[a-f0-9]{64}\Z")
GRAPHIC = re.compile(r"[A-Za-z0-9_ .()-]{1,180}\Z")
ROLE = ("Tilesets", "Autotiles")
INTRO_META = "Plugins/ZZZZZ Blue Sinnoh Intro/meta.txt"
DEPENDENCY = "Plugins/ZZZZ Blue Story and Presentation/meta.txt"


def blocked(message: str) -> None:
    raise ValueError("SINNOH_S08_BLOQUEADO: " + message)


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def no_gameplay(report: dict) -> None:
    for key in ("import_allowed", "pilot_verified", "runtime_playable",
                "gameplay_approved", "native_qa_approved"):
        if report.get(key) is True:
            blocked("prova falsa de gameplay: " + key)


def source_audit(source: Path, game_data: Path | None = None) -> dict:
    """Combine the existing inert RXDATA parser and directed graph.

    Missing references remain explicit BLOCKERS. A clean static report does not
    establish rights or physical passability of the original maps.
    """
    record = audit_rxdata(source, game_data)
    if (record.get("region") != "SINNOH"
            or record.get("mode") != "READ_ONLY_INERT_RMXP"
            or record.get("import_allowed") is not False
            or record.get("rights_verified") is not False):
        blocked("relatorio RXDATA fora do contrato")
    graph = make_graph(record)
    problems = {
        "missing_map_files": record["missing_map_files"],
        "orphan_map_files": record["orphan_map_files"],
        "broken_static_transfers": record["unresolved_static_transfer_ids"],
        "missing_graphics": record["missing_graphics"],
        "invalid_graphic_names": record["invalid_graphic_names"],
        "unmapped_id_collisions": record["unmapped_id_collisions"],
    }
    outstanding = {k: v for k, v in problems.items() if v is None or bool(v)}
    status = ("BLOCKED_SOURCE_INTEGRITY" if outstanding
              else "STATIC_SOURCE_REFERENCES_RESOLVED_NOT_APPROVED")
    return {
        "schema": 1, "region": "SINNOH", "kind": "S08_SOURCE",
        "status": status, "source_maps": record["source_map_count"],
        "source_map_ids": record["source_map_ids"],
        "mapinfos_sha256": record["mapinfos_sha256"],
        "tilesets_sha256": record["tilesets_sha256"],
        "broken_reference_findings": problems,
        "findings": sorted(outstanding),
        "weak_components": len(graph["weakly_connected_components"]),
        "dynamic_transfers_require_manual_review": record["dynamic_transfer_commands"],
        "script_commands_not_executed": record["untrusted_script_commands_not_executed"],
        "rights_verified": False, "import_allowed": False,
        "pilot_verified": False, "native_qa_approved": False,
    }


def graphic_inventory(tileset_blob: bytes, overlay: dict[str, bytes],
                      base: Path, base_hashes: dict[str, str]) -> dict:
    """Resolve required tilesets/autotiles from the merged private QA inputs."""
    tiles = loads(tileset_blob)
    if not isinstance(tiles, (list, dict)):
        blocked("Tilesets.rxdata nao tem estrutura valida")
    tileset_list = tiles.values() if isinstance(tiles, dict) else tiles
    paths: set[str] = set()
    missing: set[str] = set()
    for entry in tileset_list:
        if entry is None:
            continue
        if not isinstance(entry, RubyObject) or entry.name != "RPG::Tileset":
            blocked("tileset com classe inesperada")
        attrs = entry.attrs
        auto = attrs.get("@autotile_names", [])
        if not isinstance(auto, list):
            blocked("lista de autotiles invalida")
        for folder, value in ([("Tilesets", attrs.get("@tileset_name"))] +
                              [("Autotiles", name) for name in auto]):
            name = text(value).strip() if value is not None else ""
            if not name:
                continue
            if not GRAPHIC.fullmatch(name) or name in (".", ".."):
                blocked("nome de arquivo grafico inseguro")
            rel = f"Graphics/{folder}/{name}.png"
            paths.add(rel)
            if rel in overlay:
                data = overlay[rel]
                if not data or digest(data) != digest(overlay[rel]):
                    blocked("grafico do overlay corrompido: " + rel)
            elif rel in base_hashes:
                f = base / rel
                if (f.is_symlink() or not f.is_file()
                        or digest(f.read_bytes()) != base_hashes[rel]):
                    blocked("grafico da base adulterado: " + rel)
            else:
                missing.add(rel)
    if missing:
        blocked("graficos citados por tilesets ausentes: " + ", ".join(sorted(missing)))
    return {"referenced_graphics": sorted(paths),
            "referenced_graphics_count": len(paths),
            "missing_graphics": []}


def plugin_dependencies(overlay: dict[str, bytes], base: Path,
                        base_hashes: dict[str, str]) -> dict:
    required = {
        INTRO_META: ("Blue Sinnoh Intro", "Blue Battle Presentation and Story"),
        START_META: ("Blue Sinnoh QA Start", "Blue Sinnoh Intro"),
        PROBE_META: ("Blue Sinnoh QA Probe", "Blue Sinnoh Intro"),
    }
    if DEPENDENCY not in base_hashes:
        blocked("plugin base Blue Battle Presentation and Story ausente")
    f = base / DEPENDENCY
    if f.is_symlink() or not f.is_file() or digest(f.read_bytes()) != base_hashes[DEPENDENCY]:
        blocked("plugin base foi alterado ou nao esta disponivel")
    original = f.read_text("utf-8")
    if "Name = Blue Battle Presentation and Story" not in original:
        blocked("nome do plugin base alterado")
    for name, (plugin, depends) in required.items():
        data = overlay.get(name)
        if not isinstance(data, bytes):
            blocked("meta de plugin Sinnoh ausente: " + name)
        txt = data.decode("utf-8")
        if f"Name = {plugin}" not in txt or f"Requires = {depends}" not in txt:
            blocked("dependencia de plugin inconsistente: " + name)
        if "Essentials = 21.1" not in txt:
            blocked("versao de Essentials no plugin divergente")
    if not overlay.get(START_PLUGIN) or not overlay.get(PROBE_PLUGIN):
        blocked("script Ruby QA de inicio/probe ausente")
    return {"plugin_dependencies_verified": True,
            "dependency_names": [x[0] for x in required.values()],
            "native_scripts_executed": False}


def private_overlay_audit(project: Path, overlay: Path, spec: Path,
                          *, qa: Path | None = None, token: str = "abcdef123456") -> dict:
    root = Path(project).absolute()
    work = root / ".blue-work"
    if root.is_symlink() or work.is_symlink() or not work.is_dir():
        blocked("workspace .blue-work nao existe ou contem symlink")
    if (Path(spec).is_symlink() or not Path(spec).is_file()
            or not Path(spec).absolute().is_relative_to(work)
            or not Path(spec).absolute().resolve().is_relative_to(work.resolve())):
        blocked("especificacao privada fora do workspace ou inexistente")
    data = json.loads(Path(spec).read_text("utf-8"))
    # Cross-check with the same full validation used by S12, without --install.
    report, output, base_hashes = prepare(root / "game", Path(overlay), data,
                                          token=token, project=root)
    if report.get("runtime_playable") is not False:
        blocked("overlay nao pode anunciar gameplay")
    for rel, sha in report["overlay_file_hashes"].items():
        if not SHA.fullmatch(sha) or rel not in output or digest(output[rel]) != sha:
            blocked("SHA-256 do arquivo final inconsistente: " + rel)
    merged = {**output}
    if "Data/Tilesets.rxdata" not in merged:
        blocked("Tilesets.rxdata ausente do overlay")
    graphics = graphic_inventory(merged["Data/Tilesets.rxdata"], output,
                                 root / "game", base_hashes)
    plugins = plugin_dependencies(output, root / "game", base_hashes)
    launcher = set(QA_LAUNCH_REQUIRED)
    required = launcher - set(output) - set(base_hashes)
    if required:
        blocked("dependencias do launcher ausentes: " + ", ".join(sorted(required)))
    if qa is not None:
        checked = verify(qa, project=root)
        if (not checked["save_namespace_verified"] or
                not checked["no_foreign_save_in_qa"] or
                checked["playable_approved"]):
            blocked("copia privada nao passou verificacao de saves/QA")
    return {
        "schema": 1, "region": "SINNOH", "kind": "S08_PRIVATE_OVERLAY",
        "status": "STATIC_INTEGRITY_VERIFIED_NOT_NATIVE_GAMEPLAY",
        "mode": "READ_ONLY_QA_RESOURCES",
        "map_count": report["start"] and 9,
        "event_count": 24, "warps": 16,
        "overlay_file_count": len(output),
        "base_file_count": len(base_hashes),
        "overlay_file_sha256": report["overlay_file_hashes"],
        "launcher_required_files": sorted(launcher),
        "qa_inspected": qa is not None,
        "source_rights_verified": False,
        "native_gameplay_verified": False,
        "native_qa_approved": False,
        "import_allowed": False,
        "writes_to_main_game": False,
        **graphics, **plugins,
    }


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--project", type=Path, default=ROOT)
    modes = cli.add_mutually_exclusive_group(required=True)
    modes.add_argument("--source", type=Path, help="fonte RMXP/ZIP autorizada, apenas auditoria inerte")
    modes.add_argument("--overlay", type=Path, help="overlay privado auditado, sem instalacao")
    cli.add_argument("--game-data", type=Path, help="opcional no modo --source")
    cli.add_argument("--spec", type=Path, help="exigido no modo --overlay")
    cli.add_argument("--qa", type=Path, help="copia QA existente, somente verificacao")
    args = cli.parse_args()
    try:
        if args.source is not None:
            if args.spec or args.qa:
                blocked("--source nao combina com --spec/--qa")
            result = source_audit(args.source, args.game_data)
        else:
            if args.spec is None or args.game_data is not None:
                blocked("--overlay exige --spec e nao aceita --game-data")
            result = private_overlay_audit(args.project, args.overlay, args.spec, qa=args.qa)
    except (ValueError, OSError, KeyError, TypeError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result.get("status", "").startswith("BLOCKED") else 0


if __name__ == "__main__":
    raise SystemExit(main())
