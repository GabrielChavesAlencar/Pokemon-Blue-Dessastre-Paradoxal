#!/usr/bin/env python3
"""Unova E04-E06: cross-check four independently generated PRIVATE reports.

This is a provenance-consistency gate, NOT author authentication, licensing
permission, game integration or native playtesting. Never opens the donor game.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(".blue-work/unova")
NAMES = {
    "intake": "audit/e04-intake.json",
    "zip": "audit/u02-source.json",
    "rxdata": "audit/u02-rxdata-detail.json",
    "crosswalk": "audit/e05-crosswalk.json",
    "rights": "audit/e06-rights-inventory.json",
}
OUT = "audit/e04-e06-evidence-gate.json"
SHA = re.compile(r"[0-9a-f]{64}\Z")
LIMIT = 32 * 1024 * 1024


def error(message: str) -> None:
    raise ValueError("UNOVA_E04_E06_INCONSISTENTE: " + message)


def private_path(project: Path, path: Path) -> Path:
    project = project.absolute()
    root = project / WORK
    target = path.absolute()
    if not target.is_relative_to(root) or target == root:
        error("caminho fora de .blue-work/unova")
    for folder in (project, project/".blue-work", root, target.parent, target):
        if folder.is_symlink():
            error("symlink na origem/saida")
    return target


def json_report(project: Path, name: str) -> dict | None:
    path = private_path(project, project/WORK/NAMES[name])
    if not path.exists():
        return None
    if not path.is_file() or not 0 < path.stat().st_size <= LIMIT:
        error("arquivo de relatorio invalido: " + name)
    data = json.loads(path.read_text("utf-8-sig"))
    if not isinstance(data, dict):
        error("relatorio nao e objeto: " + name)
    return data


def check_bool_false(data: dict, keys: tuple[str, ...], label: str) -> None:
    for key in keys:
        if data.get(key) is not False:
            error(label + " aprovou indevidamente " + key)


def evidence(project: Path) -> dict:
    project = Path(project).absolute()
    reports = {kind: json_report(project, kind) for kind in NAMES}
    missing = [kind for kind in NAMES if reports[kind] is None]

    # No ZIP, no hash, no conditional pass. Missing reports are a blocked
    # diagnostic, not an error concealing an incomplete import.
    if missing:
        return {
            "schema": 1, "region": "UNOVA", "phase": "E04_E05_E06",
            "mode": "PRIVATE_EVIDENCE_COHERENCE_ONLY",
            "status": "BLOCKED_MISSING_SOURCE_EVIDENCE",
            "missing_reports": missing,
            "source_zip_sha256": None,
            "matched_source_hashes": False,
            "map_identity_confirmed": False,
            "credits_rights_verified": False,
            "rights_cleared": False, "can_install": False,
            "game_or_saves_modified": False,
            "game_exe_tested": False, "android_tested": False,
            "bar_e_completed": 4, "bar_e_total": 8,
            "next_action": "Selecionar ZIP original e Credits.txt; executar auditores no mesmo conjunto privado de fonte.",
        }

    intake, zipmeta, rxdata, crosswalk, rights = (
        reports[name] for name in ("intake","zip","rxdata","crosswalk","rights"))
    required = [
        (intake,"E04","LOCAL_USER_SELECTED_PRIVATE_INTAKE","ZIP_PRESENT_AND_METADATA_VALIDATED_ORIGIN_NOT_ATTESTED"),
        (zipmeta,"U02","ZIP_METADATA_READ_ONLY_NO_EXTRACTION","ZIP_METADATA_AUDITED_UNOVA_CONTENT_UNVERIFIED"),
        (rxdata,"U02_E05","READ_ONLY_INERT_SOURCE_INSPECTION","SOURCE_RXDATA_INSPECTED_NOT_APPROVED"),
        (crosswalk,"E05","SOURCE_NAME_CROSSWALK_READ_ONLY","CANDIDATES_ONLY_NOT_SOURCE_ACCEPTANCE"),
        (rights,"E06","PRIVATE_ASSET_PROVENANCE_INDEX_NO_INSTALL","RIGHTS_UNVERIFIED_SOURCE_CONTENT_NOT_CLEARED"),
    ]
    for data, phase, mode, status in required:
        if (data.get("schema"),data.get("region"),data.get("phase"),data.get("mode"),data.get("status")) != (
                1,"UNOVA",phase,mode,status):
            error("relatorio de origem/schema incorreto: "+phase)
    sha = intake.get("archive_sha256")
    if not isinstance(sha,str) or not SHA.fullmatch(sha):
        error("SHA-256 invalido na entrada E04")
    hashes = {
        "intake":sha,
        "zip":zipmeta.get("archive_sha256"),
        "rxdata":rxdata.get("source_zip_sha256"),
        "crosswalk":crosswalk.get("source_zip_sha256"),
        "rights":rights.get("source_zip_sha256"),
    }
    if set(hashes.values()) != {sha}:
        error("relatorios usam ZIPs/fontes diferentes; preservar historico e reauditar")
    check_bool_false(intake,("source_origin_verified_by_author","published_author_hash_matched",
                             "license_verified","rights_per_asset_verified","can_install",
                             "game_or_saves_modified","game_exe_tested","android_tested"),"E04")
    check_bool_false(zipmeta,("rights_per_asset_verified","native_mapinfos_checked",
                              "can_install","game_or_saves_modified","game_exe_tested","android_tested"),"U02")
    check_bool_false(rxdata,("rights_verified","native_mapinfos_verified","can_install",
                             "game_or_saves_modified","game_exe_tested","android_tested"),"RXDATA")
    check_bool_false(crosswalk,("copyright_cleared","can_install","native_mapids_checked",
                                "game_or_saves_modified","game_exe_tested","android_tested"),"E05")
    check_bool_false(rights,("all_assets_rights_cleared","license_verified",
                             "redistribution_approved","game_or_saves_modified",
                             "game_exe_tested","can_install"),"E06")
    original_count = intake.get("whole_donor_project_map_count")
    if (type(original_count) is not int or original_count < 1 or
        original_count != zipmeta.get("all_regions_source_map_count") or
        original_count != rxdata.get("all_regions_source_map_count") or
        original_count != crosswalk.get("whole_donor_project_map_count") or
        original_count != rights.get("whole_donor_project_map_count")):
        error("quantidade de mapas divergente entre relatorios")
    if (intake.get("archive_bytes") != zipmeta.get("archive_size_bytes") or
        rxdata.get("source_mapinfos_sha256") != crosswalk.get("source_mapinfos_sha256")):
        error("tamanho ZIP ou hash MapInfos divergente")
    if (not isinstance(rxdata.get("maps"),list) or len(rxdata["maps"]) != original_count or
        crosswalk.get("symbolic_area_count") != 74 or
        not isinstance(crosswalk.get("areas"),list) or
        len(crosswalk["areas"]) != 74):
        error("inventario de mapas/areas esta incompleto")
    real_ids = {m.get("source_map_id") for m in rxdata["maps"]}
    if len(real_ids) != original_count or any(type(m) is not int or m < 1 for m in real_ids):
        error("MapIDs de origem ausentes/duplicados")
    matches = 0
    unmatched = 0
    states = Counter()
    used_areas = set()
    for row in crosswalk["areas"]:
        if not isinstance(row,dict):
            error("linha crosswalk invalida")
        key = row.get("area_key")
        if not isinstance(key,str) or key in used_areas:
            error("chave de area repetida")
        used_areas.add(key)
        ids = row.get("candidate_source_map_ids")
        if not isinstance(ids,list) or len(set(ids)) != len(ids) or any(mid not in real_ids for mid in ids):
            error("E05 aponta MapIDs nao observados na fonte real")
        hashes = row.get("candidate_source_map_hashes")
        if (not isinstance(hashes,list) or len(hashes) != len(ids) or
            hashes != [next(m["source_sha256"] for m in rxdata["maps"]
                           if m["source_map_id"] == mid) for mid in ids]):
            error("E05 hash de mapa nao confere com RXDATA")
        if (row.get("candidate_only") is not True or row.get("region_identity_confirmed") is not False
            or row.get("rights_verified") is not False or row.get("installed") is not False
            or row.get("game_exe_tested") is not False or row.get("destination_map_id") is not None):
            error("E05 marcou mapa como instalado, licenciado ou testado")
        states[row.get("status","UNKNOWN")] += 1
        matches += bool(ids)
        unmatched += not ids
    assets = rights.get("assets")
    if (not isinstance(assets,list) or not assets or
        rights.get("classified_asset_count") != len(assets)):
        error("E06 nao inclui inventario de assets")
    asset_keys = set()
    for row in assets:
        if not isinstance(row,dict):
            error("E06 contem linha invalida")
        key=row.get("source_path")
        if not isinstance(key,str) or key in asset_keys:
            error("E06 com caminho duplicado ou ausente")
        asset_keys.add(key)
        if (row.get("rights_status") != "REVIEW_REQUIRED_NOT_LICENSED" or
            row.get("can_redistribute") is not False or
            row.get("approved_for_game") is not False or
            row.get("license_url") is not None or
            row.get("reuse_permission_document") is not None):
            error("E06 aprovou recurso sem evidencia de permissao")
    credits=rights.get("credits")
    if not isinstance(credits,dict) or credits.get("credits_are_reuse_permission") is not False:
        error("creditos interpretados incorretamente como licenca")
    if (intake.get("credits_present") != credits.get("credits_file_present") or
        intake.get("credits_sha256") != credits.get("credits_sha256")):
        error("Credits.txt diferente entre E04 e E06")
    return {
        "schema":1,"region":"UNOVA","phase":"E04_E05_E06",
        "mode":"PRIVATE_EVIDENCE_COHERENCE_ONLY",
        "status":"CONSISTENT_PRIVATE_REPORTS_NOT_LICENSED_OR_INSTALLED",
        "missing_reports":[],
        "source_zip_sha256":sha,
        "matched_source_hashes":True,
        "whole_donor_project_map_count":original_count,
        "symbolic_area_count":74,
        "source_name_candidate_area_count":matches,
        "unmatched_name_area_count":unmatched,
        "crosswalk_states":dict(sorted(states.items())),
        "classified_asset_count":len(assets),
        "credits_file_present":credits["credits_file_present"],
        "map_identity_confirmed":False,
        "credits_rights_verified":False,
        "rights_cleared":False,
        "can_install":False,
        "game_or_saves_modified":False,"game_exe_tested":False,"android_tested":False,
        "bar_e_completed":4,"bar_e_total":8,
        "next_action":"Confirmar autoria/versao e revisar manualmente mapas, eventos e direitos; nao instalar automaticamente.",
    }


def save(project: Path, report: dict) -> Path:
    project=Path(project).absolute()
    dest=private_path(project,project/WORK/OUT)
    if dest.parent.is_symlink() or (dest.parent.exists() and not dest.parent.is_dir()):
        error("pasta privada de relatorio invalida")
    dest.parent.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if dest.exists():
        if dest.read_text("utf-8") != payload:
            error("relatorio antigo diferente: preservar evidencia")
    else:
        with dest.open("x",encoding="utf-8") as fh:
            fh.write(payload)
    return dest


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--write",action="store_true")
    args=parser.parse_args(argv)
    try:
        report=evidence(args.project)
        if args.write:
            save(args.project,report)
        print(json.dumps(report,indent=2,ensure_ascii=False))
        return 0 if report["status"].startswith("CONSISTENT_") else 2
    except (ValueError,OSError,KeyError,TypeError,StopIteration) as exc:
        print(str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
