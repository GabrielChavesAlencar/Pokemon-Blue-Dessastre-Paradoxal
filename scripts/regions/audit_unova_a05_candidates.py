#!/usr/bin/env python3
"""Unova A05: plan MapID candidate space from B01/B04 + Sinnoh B05.

Historical occupancy is not a native allocation. Optionally reconcile with
a private A04 read-only report. Never edits game, reserves MapIDs or installs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import audit_sinnoh_b05_mapid_planning as b05
import audit_unova_a04_mapids as a04

ROOT=Path(__file__).resolve().parents[2]
CATALOG=Path("data/regions/unova-a05-mapid-candidates.json")
B05=Path("data/regions/sinnoh-b05-mapid-planning.json")
U03=Path("data/regions/unova-u03-areas.json")
OUT=Path(".blue-work/unova/audit")
REPORT_PATTERN=re.compile(r"a04-mapids-([0-9a-f]{16})\.json\Z")
SHA=re.compile(r"[0-9a-f]{64}\Z")
PREFERRED=set(range(518,600))
SINNOH=set(range(442,518))
LEGACY_OMITTED={1,22,32,33,42,43,48}|set(range(76,100))
REQUIRED_PLAN_FALSE=("future_reservations_verified","can_reserve_mapids",
    "can_install","game_exe_tested","android_tested")
REQUIRED_A04_FALSE=("region_ownership_verified",
    "all_installed_overlays_proven_complete",
    "unova_destination_mapids_allocated","can_reserve_mapids",
    "can_install","game_or_saves_modified","game_exe_tested","android_tested")


def block(reason: str) -> None:
    raise ValueError("UNOVA_A05_BLOQUEADO: "+reason)


def load(path: Path, limit: int=200_000) -> dict:
    path=a04.safe_path(path,file=True)
    if not 0 < path.stat().st_size<=limit:
        block("JSON vazio ou maior que limite")
    data=json.loads(path.read_text("utf-8-sig"))
    if type(data) is not dict:
        block("JSON nao e objeto")
    return data


def ids(ranges: list[dict], cap: int=999) -> set[int]:
    """Strict distinct ranges; source B05 remains the immutable authority."""
    try:
        return b05.expand(ranges,limit=cap)
    except (TypeError,KeyError,ValueError) as exc:
        block("faixas incorretas: "+str(exc))


def validate_plan(root: Path) -> tuple[dict,dict,set[int],set[int]]:
    root=a04.safe_path(root)
    source=load(root/CATALOG)
    b05_source=load(root/B05)
    # Existing B05 validates B01 + B03 + U03, not just the reported MD.
    b05_result=b05.run(root)
    if (b05_result.get("occupied_count")!=648 or
        b05_result.get("unova_physical_candidates_count")!=174 or
        b05_result.get("sinnoh_hold")!=[442,517] or
        b05_result.get("unova_allocated") is not False or
        b05_result.get("r07_complete") is not False):
        block("a evidencia B05 nao protege as condicoes de Sinnoh")
    base_expected={
      "schema":1,"region":"UNOVA","phase":"A05","story_version":"WHITE_BW",
      "status":"HISTORICAL_SNAPSHOT_CANDIDATES_NOT_RESERVED",
      "unova_symbolic_area_catalog":U03.as_posix(),
      "unova_symbolic_areas_count":74,
      "current_native_a04_required":True,
      "non_homologated_mapids_from":1000,
      "bar_a_completed":0,"bar_a_total":8,
    }
    if set(source)!={
        *base_expected,"evidence","sinnoh_administrative_hold",
        "unova_preferred_candidate","unova_other_candidate_ranges",
        "protected_ranges","proposed_area_to_native_mapid",
        "future_reservations_verified","can_reserve_mapids","can_install",
        "game_exe_tested","android_tested","caution"}:
        block("schema A05 desconhecido ou incompleto")
    for key,value in base_expected.items():
        if type(source.get(key)) is not type(value) or source[key]!=value:
            block("A05 mudou status/campo invariante: "+key)
    if any(source.get(k) is not False for k in REQUIRED_PLAN_FALSE):
        block("A05 falsamente autorizou MapIDs, instalacao ou QA")
    if source["proposed_area_to_native_mapid"]!={}:
        block("nao atribuir ID fisico a area simbolica nesta fase")
    if (not isinstance(source.get("caution"),str) or
        len(source["caution"])<50):
        block("aviso de multiplos mapas por area ausente")
    evidence=source.get("evidence",{})
    history=b05_source["evidence"]
    expected={
      "source_type":"B01_B04_SUMMARY_CROSS_REFERENCED_WITH_SINNOH_B05",
      "supplied_md_filename":"MAPIDS_DECADES_SINNOH_UNOVA_2026-11-17(1).md",
      "supplied_md_sha256":"e50ae9a9bbb3a93db54523e0e74c0bd2ad0e0272b87643fad8ee07bd17705c95",
      "cross_reference":B05.as_posix(),
      "b01_archive_sha256":history["b01_inventory_zip_sha256"],
      "b04_archive_sha256":history["b04_provenance_zip_sha256"],
      "historical_mapinfos_sha256":history["mapinfos_sha256"],
      "original_manifest_hashes_independently_verified":False,
      "current_game_mapinfos_verified":False,
      "snapshot_date":"2026-11-17",
      "b01_physical_map_count":648,
      "b04_legacy_count":617,
      "b04_omitted_short_mapid_count":31,
    }
    if evidence!=expected:
        block("proveniencia do MD/B01/B04 divergente")
    if (source["sinnoh_administrative_hold"]!=
        {"start":442,"end":517,"count":76,"not_native_reservation":True}):
        block("retencao administrativa Sinnoh alterada")
    if source["unova_preferred_candidate"]!={
        "start":518,"end":599,"count":82,
        "status":"VACANT_IN_HISTORICAL_SNAPSHOT_ONLY"}:
        block("bloco candidato Unova alterado")
    preferred=ids([{"start":518,"end":599,"count":82}])
    other=ids(sorted(source["unova_other_candidate_ranges"],
                     key=lambda r:r["start"]))
    historical=ids(b05_source["unova"]["candidate_ranges"])
    if len(other)!=92 or len(preferred)!=82 or (preferred|other)!=historical:
        block("174 candidatos divergentes do inventario B05")
    occupied=ids(b05_source["occupied"]["ranges"])
    if len(occupied)!=648 or len(LEGACY_OMITTED)!=31:
        block("inventario B01/B04 incompleto")
    if preferred & SINNOH or other & SINNOH or historical & occupied:
        block("colisao da proposta com Sinnoh ou MapIDs ocupados")
    if (source["protected_ranges"]!=[
        {"start":600,"end":699,"reason":"JOHTO_OCCUPIED"},
        {"start":700,"end":999,"reason":"HOENN_INSTALLER_PROTECTED"}]):
        block("faixas Johto/Hoenn protegidas alteradas")
    areas=load(root/U03,limit=500_000)
    if (areas.get("state")!="PLANNED_REFERENCE_ONLY" or
        areas.get("may_install") is not False or
        len(areas.get("areas",[]))!=74 or
        any(row.get("destination_map_id") is not None for row in areas["areas"])):
        block("areas U03 ja atribuidas ou aprovadas indevidamente")
    return source,b05_source,historical,occupied


def private_a04(root: Path, report_path: Path) -> dict:
    root=a04.safe_path(root)
    target=a04.safe_path(report_path,file=True)
    expected_dir=root/OUT
    if target.parent!=expected_dir or not REPORT_PATTERN.fullmatch(target.name):
        block("relatorio A04 deve estar na pasta privada .blue-work/unova/audit")
    report=load(target,limit=12*1024*1024)
    if (report.get("schema")!=1 or report.get("region")!="UNOVA" or
        report.get("phase")!="A04" or
        report.get("mode")!="READ_ONLY_NATIVE_MAPID_OCCUPANCY_AUDIT" or
        report.get("base_decades_scanned") is not True):
        block("relatorio A04 nao comprova baseline real lida")
    if any(report.get(flag) is not False for flag in REQUIRED_A04_FALSE):
        block("relatorio A04 falsamente declara reserva ou uso autorizado")
    if report.get("available_map_ids_certified") is not None or report.get("bar_a_completed")!=0:
        block("relatorio A04 afirma disponibilidade/aceite nao provado")
    payload=json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True).encode("utf-8")+b"\n"
    if "a04-mapids-"+hashlib.sha256(payload).hexdigest()[:16]+".json"!=target.name:
        block("SHA de conteudo do relatorio A04 nao confere")
    base=report.get("sources",{}).get("DECADES",{})
    if (base.get("label")!="DECADES" or base.get("mapinfos_present") is not True
        or not isinstance(base.get("map_ids_occupied_or_declared"),list) or
        base.get("file_count",0)<1 or not isinstance(base.get("maps"),list)):
        block("A04 sem inventario Decades valido")
    source_ids=base["map_ids_occupied_or_declared"]
    if (any(type(i) is not int or not 1<=i<=99999 for i in source_ids) or
        source_ids!=sorted(set(source_ids)) or
        report.get("observed_or_declared_occupied_count")!=
        len(report.get("observed_or_declared_occupied_map_ids",[]))):
        block("A04 com IDs incorretos/duplicados")
    maps=base["maps"]
    if base["file_count"]!=len(maps) or not maps:
        block("A04 com numero de arquivos divergente")
    physical=set()
    declared=set()
    for row in maps:
        if (type(row) is not dict or type(row.get("id")) is not int or
            not 1<=row["id"]<=99999 or row["id"] in physical or
            type(row.get("bytes")) is not int or not 0<row["bytes"]<=a04.MAX_FILE_BYTES or
            type(row.get("sha256")) is not str or
            not SHA.fullmatch(row["sha256"])):
            block("A04 arquivo de mapa invalido/duplicado")
        physical.add(row["id"])
        if row.get("mapinfo_name") is not None:
            if not isinstance(row["mapinfo_name"],str) or not row["mapinfo_name"].strip():
                block("A04 nome de mapa invalido")
            declared.add(row["id"])
    missing=base.get("missing_map_file_ids")
    if (not isinstance(missing,list) or
        any(type(i) is not int or not 1<=i<=99999 for i in missing) or
        missing!=sorted(set(missing)) or set(missing)&physical):
        block("A04 MapInfos sem arquivos inconsistentes")
    declared.update(missing)
    if (base.get("mapinfos_declared_count")!=len(declared) or
        base.get("orphan_map_file_ids")!=sorted(physical-declared) or
        source_ids!=sorted(physical|declared)):
        block("A04 MapInfos e MapNNN divergentes")
    observed=report["observed_or_declared_occupied_map_ids"]
    if (any(type(i) is not int or not 1<=i<=99999 for i in observed) or
        observed!=sorted(set(observed)) or not set(source_ids)<=set(observed)):
        block("uniao de A04 nao corresponde ao Decades")
    return report


def read_android_occupancy(path: Path) -> tuple[dict, set[int]]:
    """Read tracked map paths from a multiregion manifest as exclusion evidence."""
    path = a04.safe_path(path, file=True)
    with path.open("rb") as stream:
        limit = 12 * 1024 * 1024
        payload = stream.read(limit + 1)
    if not 0 < len(payload) <= limit:
        block("manifesto Android vazio ou acima do limite")
    doc = json.loads(payload)
    if (not isinstance(doc, dict) or doc.get("schema") != 1 or doc.get("channel") != "multiregion"
            or not re.fullmatch(r"[0-9a-f]{40}", str(doc.get("revision", "")))
            or not isinstance(doc.get("files"), dict)):
        block("manifesto Android multirregional invalido")

    def digest(row):
        return (row["sha256"] if isinstance(row, dict) and isinstance(row.get("sha256"), str)
                and SHA.fullmatch(row["sha256"]) else None)

    files = doc["files"]
    mapinfos = digest(files.get("Data/MapInfos.rxdata"))
    occupied = set()
    for name, row in files.items():
        parts = name.split("/")
        if len(parts) != 2 or parts[0].casefold() != "data":
            continue
        mid = a04._map_id(parts[1])
        if mid is None:
            continue
        if mid in occupied or not digest(row):
            block("entrada de mapa Android duplicada ou sem SHA-256")
        occupied.add(mid)
    if not mapinfos or not 0 < len(occupied) <= a04.MAX_MAPS:
        block("manifesto Android sem MapInfos ou mapas rastreados validos")
    return {
        "revision": doc["revision"],
        "manifest_sha256": hashlib.sha256(payload).hexdigest(),
        "mapinfos_sha256_declared": mapinfos,
        "tracked_map_count": len(occupied),
    }, occupied


def audit(root: Path, report_path: Path|None=None, *, android_manifest: Path|None=None) -> dict:
    if android_manifest is not None and report_path is None:
        block("--android-manifest exige --a04-report")
    plan,b05_source,candidates,previous_occupied=validate_plan(root)
    result={
        "schema":1,"region":"UNOVA","phase":"A05",
        "status":"HISTORICAL_SNAPSHOT_CANDIDATES_ONLY",
        "mode":"READ_ONLY_CANDIDATE_POOL_NO_ALLOCATION",
        "evidence_supplied_md_sha256":plan["evidence"]["supplied_md_sha256"],
        "historical_mapinfos_sha256":plan["evidence"]["historical_mapinfos_sha256"],
        "historical_occupied_count":len(previous_occupied),
        "historical_b04_legacy_omissions":31,
        "sinnoh_admin_hold":[442,517],
        "sinnoh_admin_hold_count":len(SINNOH),
        "preferred_candidate_span":[518,599],
        "preferred_candidate_count":len(PREFERRED),
        "candidate_ranges":b05_source["unova"]["candidate_ranges"],
        "historical_candidate_count":len(candidates),
        "historical_candidate_ids":sorted(candidates),
        "potential_expansion_count":len(candidates-PREFERRED),
        "symbolic_unova_area_count":74,
        "area_to_destination_map_id":{},
        "a04_report_supplied":False,
        "a04_snapshot_baseline_hash_matches_b05":None,
        "a04_observed_candidate_collisions":None,
        "a04_preferred_block_observed_vacant":None,
        "a04_overlap_count":None,
        "a04_missing_overlay_snapshots":None,
        "verified_free_mapids":None,
        "future_region_reservations_verified":False,
        "rights_verified":False,
        "mapid_reservation_confirmed":False,"unova_maps_installed":False,
        "can_reserve_mapids":False,"can_install":False,
        "game_or_saves_modified":False,
        "game_exe_tested":False,"android_tested":False,
        "bar_a_completed":0,"bar_a_total":8,
        "blockers":[
            "B01/B04 sao inventarios de snapshot, nao reservas do instalador atual",
            "Sinnoh 442-517 e retencao administrativa, nao mapeamento instalado",
            "Hoenn 700-999 protegido e IDs 1000+ nao homologados",
            "74 areas simbolicas nao equivalem necessariamente a 74 mapas RXDATA",
            "Mapas de Unova, seus IDs de origem e licencas ainda nao confirmados",
        ],
    }
    if report_path is None:
        result["blockers"].append(
            "Relatorio A04 da instalacao atual nao fornecido; nenhuma vaga atual certificada")
        return result
    a04_report=private_a04(root,report_path)
    actual=set(a04_report["observed_or_declared_occupied_map_ids"])
    base=a04_report["sources"]["DECADES"]
    hash_ok=base["mapinfos_sha256"]==plan["evidence"]["historical_mapinfos_sha256"]
    b05_match=set(base["map_ids_occupied_or_declared"])==previous_occupied
    collisions=sorted(actual & candidates)
    result.update({
        "status":("A04_HISTORICAL_BASELINE_MATCHES_STILL_NOT_RESERVED"
                  if hash_ok and b05_match and not collisions and not a04_report["overlaps"]
                  else "A04_DIFFERENT_OR_CONFLICTING_NEEDS_REVIEW"),
        "a04_report_supplied":True,
        "a04_snapshot_baseline_hash_matches_b05":hash_ok,
        "a04_baseline_occupied_ids_match_b05":b05_match,
        "a04_observed_candidate_collisions":collisions,
        "a04_preferred_block_observed_vacant":not bool(PREFERRED&actual),
        "a04_overlap_count":len(a04_report["overlaps"]),
        "a04_missing_overlay_snapshots":a04_report["region_overlay_snapshots_missing"],
    })
    if not hash_ok or not b05_match:
        result["blockers"].append("MapInfos/ocupacao A04 divergem de B01: reauditar baseline atual")
    if collisions:
        result["blockers"].append("Novos candidatos ocupados no A04: "+
                                  ", ".join(map(str,collisions[:35])))
    if android_manifest is not None:
        evidence, android_ids = read_android_occupancy(android_manifest)
        result["android_manifest"] = evidence
        result["android_manifest_candidate_collisions"] = sorted(android_ids & candidates)
        result["cross_platform_candidate_collisions"] = sorted((actual | android_ids) & candidates)
        if PREFERRED <= actual | android_ids:
            result["blockers"].append("Todos os IDs 518-599 aparecem ocupados no A04 ou no manifesto Android")
    if a04_report["overlaps"]:
        result["blockers"].append("Sobreposicoes entre snapshots A04 requerem revisao")
    result["blockers"].append(
        "Mesmo com hash historico igual: auditar reservas futuras, scripts e origem das regioes")
    return result


def save(root: Path, report: dict) -> Path:
    root=a04.safe_path(root)
    dest=root/OUT
    for path in (root/".blue-work",root/".blue-work/unova",dest):
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            block("saida privada e symlink/arquivo")
        path.mkdir(exist_ok=True)
    payload=json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True).encode("utf-8")+b"\n"
    name="a05-candidates-"+hashlib.sha256(payload).hexdigest()[:16]+".json"
    output=dest/name
    if output.is_symlink():
        block("saida via symlink")
    if output.exists():
        if output.read_bytes()!=payload:
            block("nunca sobrescrever evidencia divergente")
    else:
        with output.open("xb") as handle:
            handle.write(payload)
    return output


def choose_gui(root: Path) -> Path|None:
    try:
        import tkinter as tk
        from tkinter import filedialog,messagebox
        win=tk.Tk()
        win.withdraw()
        if not messagebox.askyesno("Unova A05 — somente planejamento",
            "Deseja selecionar um relatorio A04 privado da instalacao atual?\n"
            "Nao = conferir apenas o inventario B01/B04, sem certificar vagas.\n"
            "Sim = comparar com A04, ainda sem reservar IDs.",parent=win):
            win.destroy()
            return None
        file=filedialog.askopenfilename(parent=win,
            title="Escolha a04-mapids-HASH.json",
            initialdir=str(root/OUT),filetypes=[("Relatorio A04 JSON","*.json")])
        win.destroy()
        if not file:
            block("selecao A04 cancelada; nao simular auditoria nativa")
        return Path(file)
    except (OSError,ImportError,RuntimeError) as exc:
        block("seletor Windows indisponivel: "+str(exc))


def main(argv=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--a04-report",type=Path)
    parser.add_argument("--android-manifest", type=Path, help="comparar update.json multiregional com A04")
    parser.add_argument("--gui",action="store_true")
    parser.add_argument("--write",action="store_true")
    args=parser.parse_args(argv)
    try:
        source=args.a04_report
        if args.gui:
            if source is not None:
                block("use --gui ou --a04-report, nao ambos")
            source=choose_gui(Path(args.project).absolute())
        report=audit(args.project,source,android_manifest=args.android_manifest)
        if args.write or args.gui:
            target=save(args.project,report)
            print("A05_RELATORIO_PRIVADO="+str(target),file=sys.stderr)
        summary={k:v for k,v in report.items() if k!="historical_candidate_ids"}
        print(json.dumps(summary,ensure_ascii=False,indent=2))
        return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
