#!/usr/bin/env python3
"""One-click Unova MapID check: find installed Decades, run A04 then A05.

No questions, no directory selection, no Ruby execution, no maps written.
A04 and A05 remain observations only; neither approves MapID allocation.
The summary text is always in .blue-work/unova/audit, and can open in Notepad.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Mapping

import audit_unova_a04_mapids as a04
import audit_unova_a05_candidates as a05
import audit_unova_a06_references as a06
import audit_unova_a07_reference_provenance as a07
import audit_unova_a08_readiness as a08
import audit_unova_a09_intro_and_claims as a09
import audit_unova_a10_dynamic_matrix as a10
import audit_unova_a11_intro_preflight as a11

ROOT = Path(__file__).resolve().parents[2]
SUMMARY = Path(".blue-work/unova/audit/LEIA_AQUI_UNOVA_MAPIDS.txt")
MIN_NATIVE_MAPS = 20
MAX_CANDIDATE_DIR_ENTRIES = 30_000


def deny(message: str) -> None:
    raise ValueError("UNOVA_AUTO_BLOQUEADO: " + message)


def candidate_locations(
    project: Path, environ: Mapping[str, str] | None = None
) -> list[tuple[str, Path]]:
    """Fixed trusted roots, never recursive searching of Downloads/whole disks."""
    env = dict(os.environ if environ is None else environ)
    project = Path(project).absolute()
    explicit = env.get("BLUE_DECADES_GAME_DIR", "").strip().strip('"')
    if explicit:
        # If an override exists, do not silently audit another installation.
        return [("BLUE_DECADES_GAME_DIR", Path(explicit).expanduser().absolute())]
    local = env.get("LOCALAPPDATA", "").strip()
    profile = env.get("USERPROFILE", "").strip()
    roaming = env.get("APPDATA", "").strip()
    locations = []
    if local:
        locations.extend([
            ("INSTALACAO_PADRAO", Path(local)/"PokemonBlueDessastreParadoxal"/"game"),
            ("INSTALACAO_PADRAO_SEM_GAME", Path(local)/"PokemonBlueDessastreParadoxal"),
            ("APP_LOCAL_BLUE_STORY", Path(local)/"Blue-Story"/"game"),
        ])
    if profile:
        locations.append((
            "USERPROFILE_PADRAO", Path(profile)/"AppData"/"Local"/
            "PokemonBlueDessastreParadoxal"/"game"))
    if roaming:
        locations.append((
            "APPDATA_BLUE", Path(roaming)/"PokemonBlueDessastreParadoxal"/"game"))
    locations.extend([
        ("REPOSITORIO_GAME", project/"game"),
        ("REPOSITORIO_GAME_DATA", project/"game"/"Data"),
        ("REPOSITORIO_PAI_GAME", project.parent/"game"),
        ("REPOSITORIO_PAI_BLUE",project.parent/"PokemonBlueDessastreParadoxal"/"game"),
    ])
    dedup: dict[str, tuple[str, Path]] = {}
    for label, path in locations:
        absolute = path.absolute()
        key = os.path.normcase(str(absolute)).casefold()
        if key not in dedup:
            dedup[key] = (label, absolute)
    return list(dedup.values())


def examine_game(path: Path) -> tuple[Path | None, str]:
    """Conservative identity check without parsing or changing data."""
    candidate = Path(path).absolute()
    if not candidate.exists():
        return None, "não encontrado"
    try:
        if candidate.is_symlink():
            return None, "caminho é um link simbólico"
        data = a04.directory_root(candidate)
        game_dir = data.parent
        if not (game_dir/"Game.exe").is_file():
            return None, "Game.exe não encontrado junto à pasta Data"
        mapinfos = data/"MapInfos.rxdata"
        if not mapinfos.is_file() or mapinfos.is_symlink():
            return None, "MapInfos.rxdata ausente ou inseguro"
        count = 0
        total = 0
        for item in data.iterdir():
            total += 1
            if total > MAX_CANDIDATE_DIR_ENTRIES:
                return None, "pasta Data com entradas demais"
            if item.is_symlink():
                return None, "pasta Data contém link simbólico"
            if item.is_file() and a04._map_id(item.name) is not None:
                count += 1
                if count >= MIN_NATIVE_MAPS:
                    break
        if count < MIN_NATIVE_MAPS:
            return None, f"somente {count} arquivos de mapas detectados"
        # a04.scan_dir verifies every file, file size and MapInfos later.
        return game_dir, "Game.exe, MapInfos e mapa(s) detectados"
    except (ValueError, OSError, PermissionError) as exc:
        return None, "não foi possível inspecionar: " + str(exc)[:170]


def discover(
    project: Path, environ: Mapping[str, str] | None = None
) -> tuple[Path | None, list[dict], str | None]:
    candidates = candidate_locations(project, environ)
    checked: list[dict] = []
    found: dict[str, tuple[str, Path]] = {}
    for label, path in candidates:
        selected, comment = examine_game(path)
        checked.append({"label": label,"path": str(path),"result": comment,
                        "eligible": selected is not None})
        if selected is not None:
            key = os.path.normcase(str(selected.absolute())).casefold()
            found.setdefault(key, (label, selected))
    if not found:
        return None, checked, "Nenhuma instalacao com Game.exe, MapInfos e mapas foi encontrada nos locais conhecidos."
    if len(candidates)==1 and candidates[0][0]=="BLUE_DECADES_GAME_DIR":
        return next(iter(found.values()))[1],checked,None
    preferred = next(
        ((label, path) for label, path in found.values()
         if label in ("INSTALACAO_PADRAO","INSTALACAO_PADRAO_SEM_GAME",
                      "USERPROFILE_PADRAO")),None
    )
    if preferred is not None:
        # When the known installed path is valid, prefer it over stale repo copies.
        return preferred[1],checked,None
    if len(found)!=1:
        return None, checked, (
            "Foram encontradas varias instalacoes alternativas. "
            "Para evitar escolher a errada, use BLUE_DECADES_GAME_DIR "
            "com a pasta game correta."
        )
    return next(iter(found.values()))[1],checked,None


def pretty(result: dict) -> str:
    checked = result.get("candidates_checked", [])
    lines = [
        "UNOVA — AUDITORIA AUTOMATICA DE MAPIDS",
        "="*56,
        "Resultado: "+result["status"],
        "Instalacao encontrada: "+str(result.get("game_dir") or "(nenhuma)"),
        "",
    ]
    if result.get("error"):
        lines += ["BLOQUEIO: "+result["error"],""]
    a04_result=result.get("a04_result")
    a05_result=result.get("a05_result")
    a06_result=result.get("a06_result")
    a07_result=result.get("a07_result")
    a08_result=result.get("a08_result")
    a09_result=result.get("a09_result")
    a10_result=result.get("a10_result")
    a11_result=result.get("a11_result")
    if a04_result:
        lines.extend([
            "A04 — inventario da instalacao atual",
            "  Ocupados/declarados observados: "+
                str(a04_result["observed_or_declared_occupied_count"]),
            "  MapInfos SHA-256: "+
                str(a04_result["sources"]["DECADES"]["mapinfos_sha256"]),
            "  Sobreposicoes: "+str(a04_result["overlap_count"]),
            "  Relatorio completo: "+str(result["a04_report_path"]),
            "",
        ])
    if a05_result:
        lines.extend([
            "A05 — comparacao com B01/B04/B05",
            "  Historico B01: 648 ocupados",
            "  B04 V2 (MD atualizado): 648/648 MapIDs consistentes com B01; sem reserva aprovada",
            "  Sinnoh (retencao administrativa): 442-517 (76)",
            "  Unova bloco candidato prioritario: 518-599 (82)",
            "  Outros candidatos historicos: 92",
            "  Colisoes novas com candidatos: "+
                str(len(a05_result["a04_observed_candidate_collisions"] or [])),
            "  IDs em conflito (amostra): "+
                ", ".join(str(x) for x in
                          (a05_result["a04_observed_candidate_collisions"] or [])[:40]),
            "  Bloco 518-599 ainda desocupado nos dados observados? "+
                ("Sim" if a05_result["a04_preferred_block_observed_vacant"] else "Nao"),
            "  MapInfos atual igual ao historico? "+
                ("Sim" if a05_result["a04_snapshot_baseline_hash_matches_b05"] else "Nao"),
            "  Status: "+a05_result["status"],
            "  Relatorio completo: "+str(result["a05_report_path"]),
            "",
        ])
    if a06_result:
        lines.extend([
            "A06 — referencias estaticas em eventos de mapas",
            "  Mapas lidos integralmente: "+
                str(a06_result["map_files_parsed"])+"/"+str(a06_result["map_files_expected"]),
            "  Falhas na leitura de mapas: "+str(len(a06_result["map_read_failures"])),
            "  Transferencias estaticas: "+str(a06_result["static_transfer_command_count"]),
            "  Destinos estaticos ausentes: "+
                ", ".join(map(str,a06_result["static_unresolved_destination_ids"][:35])),
            "  Referencias a candidatos Unova 518-599: "+
                ", ".join(map(str,a06_result["candidate_unova_518_599_referenced"][:35])),
            "  Transferencias dinamicas: "+str(a06_result["dynamic_transfer_commands"]),
            "  Linhas de script de evento sem executar: "+
                str(a06_result["event_script_commands_not_executed"]),
            "  Status: "+a06_result["status"],
            "  Relatorio: "+str(result["a06_report_path"]),
            "",
        ])
    if a07_result:
        lines.extend([
            "A07 — origem de MapID 3 e referencias literais em scripts",
            "  Mapas relidos: "+str(a07_result["map_files_parsed"])+"/"+
                str(a07_result["map_files_expected"]),
            "  Transferencias estaticas ao MapID 3: "+
                str(a07_result["mapid_3_static_reference_count"]),
            "  Origem das transferencias para MapID 3: "+
                "; ".join("map "+str(x.get("source_map_id","CommonEvent"))+
                    ", evento "+str(x.get("event_id",x.get("common_event_index")))+
                    ", pag "+str(x.get("page_index","n/a")) for x in
                    a07_result["static_interest_references"] if x["destination_map_id"]==3)[:500],
            "  Pistas literais em scripts (IDs 3/518-599): "+
                str(len(a07_result["script_literal_hints"])),
            "  CommonEvents: "+a07_result["common_events"]["status"],
            "  Scripts.rxdata: "+a07_result["scripts_rxdata"]["status"],
            "  Pendencias na analise: "+str(a07_result["review_errors_count"]),
            "  Relatorio detalhado: "+str(result["a07_report_path"]),
            "",
        ])
    if a08_result:
        rows=a08_result.get("map001_event_context",[])
        local=a08_result.get("local_region_manifests",{})
        extra=a08_result.get("additional_script_indicators",{})
        lines.extend([
            "A08 — Map001 eventos 1/2 e verificacao de reservas no instalador",
            "  Status: "+a08_result["status"],
            "  Eventos de Map001 descritos: "+str(len(rows)),
            "  MapID 3 presente fisicamente/declarado? "+
                ("Sim" if a08_result.get("mapid3_physically_or_declared_present") else "Nao"),
            "  Transferencias para 3 conferem com A07? "+
                ("Sim" if a08_result.get("mapid3_transfers_reconciled_with_a07") else "Nao"),
            "  Eventos sem dados: "+", ".join(map(str,a08_result.get("map001_target_events_missing",[]))),
            "  Eventos e condicoes (sem executar): "+
                "; ".join("evento "+str(e["event_id"])+": "+e.get("name","")+" ("+
                    str(len(e["pages"]))+" paginas)" for e in rows)[:600],
            "  Colisoes observadas no bloco Unova 518-599: "+
                ", ".join(map(str,a08_result.get("candidate_518_599_occupied_ids",[]))),
            "  Colisoes apontadas por manifestos locais: "+
                ", ".join(map(str,local.get("observed_candidate_overlaps",[]))),
            "  Manifestos locais: "+
                "; ".join(m.get("file","")+":"+m.get("status","") for m in
                           local.get("manifests",[]))[:650],
            "  Pistas de chamadas de transferencia em scripts adicionais: "+
                str(extra.get("transfer_api_name_occurrences","DESCONHECIDO")),
            "  Pendencias para revisao humana: "+
                str(a08_result.get("review_problems_count","DESCONHECIDO")),
            "  Reserva de MapIDs autorizada? Nao",
            "  Relatorio detalhado: "+str(result.get("a08_report_path") or "NAO_GERADO"),
        ])
        if a08_result.get("block_reason"):
            lines.append("  Bloqueio A08: "+a08_result["block_reason"])
        lines.append("")
    if a09_result:
        intro=a09_result.get("intro_event_evidence",{})
        calls=a09_result.get("script_transfer_triage",{})
        counts=calls.get("classification_counts",{})
        manifest=a09_result.get("manifest_provenance",{})
        lines.extend([
            "A09 — introducoes, condicoes, referencias dinamicas e manifestos",
            "  Status: "+a09_result.get("status","UNKNOWN"),
            "  Transferencias do Map001 para MapID 3: "+str(intro.get("static_transfer_to_mapid3_count","DESCONHECIDO")),
            "  Origem confere com A07? "+("Sim" if intro.get("mapid3_origin_matches_a07") else "Nao/Desconhecido"),
            "  Condicoes reais de ativacao executadas? Nao",
        ])
        for event in intro.get("events",[]):
            lines.append("  Evento "+str(event.get("event_id"))+" — "+str(event.get("event_name","")))
            for page in event.get("pages",[])[:10]:
                to3=[x for x in page.get("transfer_evidence",[]) if x.get("destination_map_id")==3]
                gates=", ".join(k+"="+str(v) for k,v in page.get("condition_ids",{}).items())
                lines.append("    Pagina "+str(page.get("page_index"))+", gatilho "+str(page.get("trigger_label"))+
                             ", comandos "+str(page.get("command_total"))+
                             ", transferencias p/3 "+str(len(to3))+
                             ", condicoes "+gates[:120])
        lines.extend([
            "  Chamadas textuais em scripts classificadas: "+
                str(sum(v for k,v in counts.items() if k.isupper())),
            "    Definicoes: "+str(counts.get("DEFINITION",0))+
                "; simbolicas/computadas: "+str(counts.get("SYMBOLIC_OR_COMPUTED",0))+
                "; literal ID 3: "+str(counts.get("LITERAL_TARGET_3",0))+
                "; literal Unova 518-599: "+str(counts.get("LITERAL_UNOVA_CANDIDATE",0)),
            "  Manifestos com colisao observada: "+
                ", ".join(map(str,manifest.get("observed_candidate_collisions",[]))),
            "  Cobertura dos manifestos completa? Nao (reivindicacoes futuras nao verificadas)",
            "  Revisao humana pendente: "+
                ", ".join(a09_result.get("followup_review_flags",[])[:12])[:750],
            "  Reserva autorizada? Nao",
            "  Relatorio completo: "+str(result.get("a09_report_path") or "NAO_GERADO"),
        ])
        if a09_result.get("block_reason"):
            lines.append("  Motivo do bloqueio: "+a09_result["block_reason"])
        lines.append("")
    if a10_result:
        matrix=a10_result.get("matrix_status_counts",{})
        # A10 omits unused histogram keys; zero is known only if all 82
        # candidates were classified and the observed counts sum to 82.
        matrix_complete=(a10_result.get("status")=="DIAGNOSTIC_COMPLETE_RESERVATION_BLOCKED"
                         and a10_result.get("mapids_reviewed")==82
                         and sum(x for x in matrix.values() if type(x) is int)==82)
        def show_count(name):
            return str(matrix.get(name,0)) if matrix_complete else "DESCONHECIDO"
        intro=a10_result.get("intro_transfer_analysis",{})
        dyn=a10_result.get("dynamic_script_references",{})
        manifests=a10_result.get("installer_manifest_analysis",{})
        lines.extend([
            "A10 — destinos dinamicos, intro e matriz de MapIDs 518-599",
            "  Status: "+a10_result.get("status","UNKNOWN"),
            "  IDs avaliados: "+str(a10_result.get("mapids_reviewed","DESCONHECIDO"))+"/82",
            "  Livres apenas no snapshot, NAO reservados: "+
                show_count("OBSERVED_VACANT_NOT_RESERVED"),
            "  IDs ja ocupados: "+show_count("OCCUPIED_IN_CURRENT_SNAPSHOT"),
            "  IDs com reclamacao em manifesto: "+
                show_count("INSTALLER_MANIFEST_CLAIM_REVIEW"),
            "  Referencias estaticas a candidatos: "+
                show_count("STATIC_REFERENCE_REVIEW"),
            "  MapID3: posições de transferencia nos dois eventos: "+
                str(len(intro.get("mapid3_transfer_positions",[]))),
            "  MapID3: mesmas contagens da A09? "+
                ("Sim" if intro.get("matches_a09_count") else "Nao/Desconhecido"),
            "  Condicoes de eventos verificadas em jogo? Nao",
            "  Chamadas computadas ainda nao resolvidas: "+
                str(dyn.get("reported_computed_count","DESCONHECIDO")),
            "  Scripts executados? Nao",
            "  Manifestos locais: "+", ".join(m.get("name","")+":"+
                m.get("status","") for m in manifests.get("files",[]))[:650],
            "  Reivindicacoes futuras Blue-Story conferidas? Nao",
            "  Pendencias: "+", ".join(a10_result.get("unresolved_review_flags",[]))[:750],
            "  Reserva autorizada? Nao",
            "  Relatorio completo: "+str(result.get("a10_report_path") or "NAO_GERADO"),
        ])
        if a10_result.get("block_reason"):
            lines.append("  Bloqueio A10: "+a10_result["block_reason"])
        lines.append("")
    if a11_result:
        pre=a11_result.get("reservation_preflight",{})
        counts=pre.get("status_counts",{})
        intro=a11_result.get("intro_route_review",{})
        dynamic=a11_result.get("computed_reference_review",{})
        lines.extend([
            "A11 — introducoes, referencias computadas e pre-reserva reversivel",
            "  Status: "+a11_result.get("status","DESCONHECIDO"),
            "  Transferencias MapID 3 documentadas: "+
                str(intro.get("transfer_count","DESCONHECIDO")),
            "  Origem dessas transferencias confere com A10? "+
                ("Sim" if intro.get("matches_a10_positions") else "Nao/Desconhecido"),
            "  Condicoes de paginas testadas no Game.exe? Nao",
            "  Substituicao automatica do MapID 3? Nao",
            "  Expressoes computadas (heuristica): "+
                str(dynamic.get("computed_shape_observed","DESCONHECIDO")),
            "  Quantidade confere com A09? "+
                ("Sim" if dynamic.get("counts_match_a09") else "Nao/Desconhecido"),
            "  Classificacao das expressoes: "+", ".join(
                str(k)+"="+str(v) for k,v in sorted(dynamic.get("shape_histogram",{}).items()))[:400],
            "  Manifestos regionais faltantes/nao completos: "+
                ", ".join(a11_result.get("regional_manifest_missing_or_partial",[]))[:400],
            "  Matriz com todos os 82 IDs: "+
                str(pre.get("count","DESCONHECIDO"))+"/82",
            "  Desocupados no snapshot, NAO reservados: "+
                str(counts.get("OBSERVED_VACANT_NOT_RESERVED","DESCONHECIDO")),
            "  Ocupados no snapshot: "+
                str(counts.get("OCCUPIED_IN_CURRENT_SNAPSHOT","DESCONHECIDO")),
            "  Reivindicados em manifestos locais: "+
                str(counts.get("INSTALLER_MANIFEST_CLAIM_REVIEW","DESCONHECIDO")),
            "  Referenciados estaticamente: "+
                str(counts.get("STATIC_REFERENCE_REVIEW","DESCONHECIDO")),
            "  Protocolo de rollback: RASCUNHO — nenhum backup criado",
            "  Pendencias: "+", ".join(a11_result.get("review_flags",[]))[:850],
            "  IDs reservados ou instalados: 0",
            "  Relatorio completo A11: "+str(result.get("a11_report_path") or "NAO_GERADO"),
        ])
        if a11_result.get("block_reason"):
            lines.append("  Motivo bloqueio A11: "+a11_result["block_reason"])
        lines.append("")
    lines.extend([
        "IMPORTANTE:",
        "  Esta ferramenta NAO altera Game.exe, MapInfos, mapas, scripts ou saves.",
        "  NENHUM MapID de Unova foi reservado nem certificado como livre.",
        "  A Barra A continua 0/8 ate validar reservas e instalacao real.",
        "",
        "Para a proxima fase, envie este LEIA_AQUI_UNOVA_MAPIDS.txt",
        "e o arquivo a11-intro-preflight-HASH.json indicado acima.",
        "",
        "Pastas pesquisadas:",
    ])
    for item in checked:
        lines.append(f" - {item['label']}: {item['path']} — {item['result']}")
    return "\n".join(lines) + "\n"


def store_summary(project: Path, report: dict) -> Path:
    project = a04.safe_path(project)
    dest = project/SUMMARY
    parents=[project/".blue-work",project/".blue-work/unova",
             project/".blue-work/unova/audit"]
    for folder in parents:
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            deny("pasta privada de relatorios invalida")
        folder.mkdir(exist_ok=True)
    if dest.is_symlink():
        deny("arquivo de resumo e link simbolico")
    # Summary is a human-readable latest pointer. Original immutable
    # content-addressed A04/A05 JSON reports remain untouched.
    with dest.open("w",encoding="utf-8-sig",newline="\r\n") as file:
        file.write(pretty(report))
    return dest


def execute(project: Path, environ: Mapping[str,str] | None = None) -> dict:
    project = a04.safe_path(project)
    selected, checked, reason = discover(project,environ)
    result: dict = {
        "status":"BLOCKED_NO_AUTOMATIC_GAME_FOUND",
        "game_dir":str(selected) if selected else None,
        "candidates_checked":checked,
        "error":reason,
        "a04_result":None,"a05_result":None,"a06_result":None,"a07_result":None,"a08_result":None,"a09_result":None,"a10_result":None,"a11_result":None,
        "a04_report_path":None,"a05_report_path":None,"a06_report_path":None,"a07_report_path":None,"a08_report_path":None,"a09_report_path":None,"a10_report_path":None,"a11_report_path":None,
        "no_game_files_modified":True,
        "can_reserve_mapids":False,"can_install":False,
    }
    if selected is None:
        return result
    try:
        baseline = a04.scan_source(selected,"DECADES",base=True)
        a04_result = a04.analyze(baseline,{})
        a04_path = a04.write_private(project,a04_result)
        result["a04_report_path"]=str(a04_path)
        result["a04_result"]=a04_result
        # This links the exact A04 content-addressed report to the A05 output.
        a05_result = a05.audit(project,a04_path)
        a05_path = a05.save(project,a05_result)
        a06_result=a06.audit(selected,a04_result)
        a06_path=a06.save(project,a06_result)
        try:
            a07_result=a07.audit(selected,a04_result,a06_result)
        except (ValueError,OSError,KeyError,TypeError) as exc:
            # Keep successful A04/A05/A06 diagnostics when A07 is blocked;
            # explicitly report UNKNOWN values, never imply zero references.
            a07_result={
                "schema":1,"region":"UNOVA","phase":"A07",
                "status":"BLOCKED_A07_INCOMPLETE_NOT_CERTIFIED",
                "map_files_expected":a06_result["map_files_expected"],
                "map_files_parsed":None,
                "mapid_3_static_reference_count":None,
                "static_interest_references":[],
                "script_literal_hints":[],
                "common_events":{"status":"NOT_EXAMINED"},
                "scripts_rxdata":{"status":"NOT_EXAMINED"},
                "review_errors_count":None,
                "block_reason":str(exc)[:300],
                "can_reserve_mapids":False,"can_install":False,
            }
        a07_path=a07.save(project,a07_result)
        try:
            a08_result=a08.audit(selected,project,a04_result,a06_result,a07_result)
        except (ValueError,OSError,KeyError,TypeError,RecursionError) as exc:
            # An incomplete A07/A08 is unknown, never a clean reservation.
            a08_result={
                "schema":1,"region":"UNOVA","phase":"A08",
                "status":"BLOCKED_A08_INCOMPLETE_NOT_CERTIFIED",
                "map001_event_context":[],"map001_target_events_missing":[],
                "mapid3_physically_or_declared_present":None,
                "mapid3_transfers_reconciled_with_a07":False,
                "candidate_518_599_occupied_ids":[],
                "local_region_manifests":{"manifests":[],
                    "observed_candidate_overlaps":[],"manifest_coverage_incomplete":True},
                "additional_script_indicators":{"transfer_api_name_occurrences":None},
                "review_problems_count":None,
                "block_reason":str(exc)[:300],
                "can_reserve_mapids":False,"can_install":False,"bar_a_completed":0,
                "bar_a_total":8
            }
        a08_path=a08.save(project,a08_result)
        try:
            a09_result=a09.audit(selected,project,a04_result,a06_result,a07_result,a08_result)
        except (ValueError,OSError,KeyError,TypeError,IndexError,RecursionError) as exc:
            a09_result={
                "schema":1,"phase":"A09","region":"UNOVA",
                "status":"BLOCKED_A09_INCOMPLETE_NOT_CERTIFIED",
                "intro_event_evidence":{"events":[],"static_transfer_to_mapid3_count":None,
                    "mapid3_origin_matches_a07":False},
                "script_transfer_triage":{"classification_counts":{},"scan_error_count":None},
                "manifest_provenance":{"observed_candidate_collisions":[],
                    "missing_or_unrecognized_coverage":True},
                "followup_review_flags":["A09_BLOCKED"],
                "block_reason":str(exc)[:300],
                "can_reserve_mapids":False,"can_install":False,"bar_a_completed":0,"bar_a_total":8
            }
        a09_path=a09.save(project,a09_result)
        try:
            a10_result=a10.audit(selected,project,a04_result,a06_result,a07_result,a08_result,a09_result)
        except (ValueError,OSError,KeyError,TypeError,RecursionError) as exc:
            a10_result={
                "schema":1,"region":"UNOVA","phase":"A10",
                "status":"BLOCKED_A10_INCOMPLETE_NOT_CERTIFIED",
                "mapids_reviewed":None,"matrix_status_counts":{},
                "intro_transfer_analysis":{},
                "dynamic_script_references":{},
                "installer_manifest_analysis":{"files":[]},
                "unresolved_review_flags":["PREVIOUS_AUDIT_CHAIN_OR_MAPDATA_INVALID"],
                "block_reason":str(exc)[:300],
                "can_reserve_mapids":False,"can_install":False,
                "bar_a_completed":0,"bar_a_total":8,
            }
        a10_path=a10.save(project,a10_result)
        try:
            a11_result=a11.audit(selected,project,a04_result,a06_result,a07_result,
                                 a08_result,a09_result,a10_result)
        except (ValueError,OSError,KeyError,TypeError,RecursionError) as exc:
            a11_result={
                "schema":1,"region":"UNOVA","phase":"A11",
                "status":"BLOCKED_A11_INCOMPLETE_NOT_CERTIFIED",
                "intro_route_review":{},
                "computed_reference_review":{},
                "reservation_preflight":{},
                "regional_manifest_missing_or_partial":[],
                "review_flags":["A11_AUDIT_CHAIN_OR_MAPDATA_INVALID"],
                "block_reason":str(exc)[:300],
                "can_reserve_mapids":False,"can_install":False,
                "bar_a_completed":0,"bar_a_total":8,
            }
        a11_path=a11.save(project,a11_result)
        result.update({
            "status":"AUTO_A04_A05_DONE_NOT_NATIVE_APPROVED",
            "error":None,
            "a05_result":a05_result,
            "a05_report_path":str(a05_path),
            "a06_result":a06_result,
            "a06_report_path":str(a06_path),
            "a07_result":a07_result,
            "a07_report_path":str(a07_path),
            "a08_result":a08_result,
            "a08_report_path":str(a08_path),
            "a09_result":a09_result,
            "a09_report_path":str(a09_path),
            "a10_result":a10_result,
            "a10_report_path":str(a10_path),
            "a11_result":a11_result,
            "a11_report_path":str(a11_path),
        })
    except (ValueError,OSError,KeyError,TypeError) as exc:
        result["status"]="AUTO_A04_OR_A05_BLOCKED"
        result["error"]=str(exc)
    return result


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--open-summary",action="store_true",
                        help="abrir o resumo gerado no Notepad no Windows")
    args=parser.parse_args(argv)
    try:
        result=execute(args.project)
        summary=store_summary(args.project,result)
        print("UNOVA_AUTO_STATUS="+result["status"])
        print("UNOVA_AUTO_RESUMO="+str(summary))
        print("UNOVA_A04="+str(result.get("a04_report_path") or "NAO_GERADO"))
        print("UNOVA_A05="+str(result.get("a05_report_path") or "NAO_GERADO"))
        print("UNOVA_A06="+str(result.get("a06_report_path") or "NAO_GERADO"))
        print("UNOVA_A07="+str(result.get("a07_report_path") or "NAO_GERADO"))
        print("UNOVA_A08="+str(result.get("a08_report_path") or "NAO_GERADO"))
        print("UNOVA_A09="+str(result.get("a09_report_path") or "NAO_GERADO"))
        print("UNOVA_A10="+str(result.get("a10_report_path") or "NAO_GERADO"))
        print("UNOVA_A11="+str(result.get("a11_report_path") or "NAO_GERADO"))
        if result.get("error"):
            print("UNOVA_AUTO_ERRO="+result["error"])
        if args.open_summary and os.name=="nt" and os.environ.get("UNOVA_MAPIDS_HEADLESS")!="1":
            try:
                subprocess.Popen(["notepad.exe",str(summary)],
                                 close_fds=True)
            except OSError as exc:
                print("Nao foi possivel abrir Notepad: "+str(exc),file=sys.stderr)
        return 0 if result["status"]=="AUTO_A04_A05_DONE_NOT_NATIVE_APPROVED" else 2
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print("UNOVA_AUTO_BLOQUEADO: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
