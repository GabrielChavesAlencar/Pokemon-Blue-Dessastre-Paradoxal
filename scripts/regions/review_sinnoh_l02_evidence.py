#!/usr/bin/env python3
"""Sinnoh L02: fail-closed documentary review of ALREADY SANITIZED L00/L01 JSON.

Reads only the public L00 template by default, or one fixed optional private
workspace JSON explicitly selected by --workspace-reports. Uses the original
L00 and G12 public contract validators. No game files, personal saves, VM,
PNG, executable, source ZIP, network, timestamp inference or upload.
An L00 summary is SELF-REPORTED, never independently authenticated evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_l00_readiness as l00

STAGES=l00.STAGES
STATUS_MISSING="MISSING_REPORT"
STATUS_BLOCKED="CONFLICTING_EVIDENCE_BLOCKED"
STATUS_DEPENDENCY="PREREQUISITE_MISSING_BLOCKED"
STATUS_UNVERIFIED="SELF_REPORTED_AWAITING_HUMAN_REVIEW"
STAGE_CHECKS={
    "B09":"Confirmar a identidade e a integridade física do clone e a origem dos recibos fora do GitHub",
    "B10":"Conferir na máquina o vínculo B09→B10, WSB somente leitura e Sandbox desativada no relatório",
    "B11":"Revisar cobertura dos diretórios monitorados e vínculo privado da sessão B11 com B10",
    "R07":"Conferir inventário e todas as reservas regionais com revisor humano",
    "R08":"Confirmar direitos por ativo e mapa, independentemente da contagem de revisões",
}
GENERAL_CHECKS=(
    "Revisar a origem e a autenticidade de cada relatório sanitizado: um SHA do JSON não é assinatura",
    "Confirmar cronologia e vínculo de sessão B11 usando evidência privada local: nenhum timestamp/watch_id é exportado",
    "Não transferir arquivos do jogo, PNGs reais, snapshots de saves, HMAC ou logs privados",
    "Não iniciar Game.exe, Windows Sandbox ou JoiPlay pela auditoria documental",
)

def blocked(reason):
    # No raw values, path strings or JSON fragments in the exception.
    raise ValueError("SINNOH_L02_BLOCKED: "+reason)

def load_sources(root=ROOT,*,workspace=False):
    root=Path(root)
    src=l00.PRIVATE_REPORT if workspace else l00.TEMPLATE
    bundle=l00.read_json(root,src,maxsize=65536)
    docs={stage:l00.read_json(root,path) for stage,path in l00.CONTRACTS.items()}
    handoff=l00.read_json(root,l00.g12.HANDOFF)
    final=l00.g12.run(root)
    return bundle,docs,handoff,final

def _valid_stage(stage,raw,docs,reports):
    if stage=="B10" and reports["B09"] is None:
        # Validate B10 against its own literal SHA to check all local policy,
        # but NEVER treat a self-matching SHA as B09 provenance. The stage
        # remains blocked on the missing independent B09 receipt.
        surrogate={"B09":{"plan_sha256":raw.get("source_clone_sha256")}}
        l00.check_report(stage,raw,docs,surrogate)
    else:
        l00.check_report(stage,raw,docs,reports)

def review(bundle,contracts,handoff,g12_report):
    """Return ONLY public fixed-key findings; never copy a receipt value."""
    # First trust-check the versioned public contracts and 44-case handoff,
    # using the original L00 baseline guard with an empty report envelope.
    template={
        "schema":1,"region":"SINNOH","stage":"L00",
        "mode":"SANITIZED_REPORTS_NOT_INDEPENDENT_PROOF",
        "reports":dict.fromkeys(STAGES),
    }
    try:
        l00.audit(template,contracts,handoff,g12_report)
        l00.exact(bundle,{"schema","region","stage","mode","reports"})
        if (type(bundle["schema"]) is not int or bundle["schema"]!=1
            or bundle["region"]!="SINNOH" or bundle["stage"]!="L00"
            or bundle["mode"]!="SANITIZED_REPORTS_NOT_INDEPENDENT_PROOF"):
            blocked("input envelope identity invalid")
        raw=bundle["reports"]
        l00.exact(raw,STAGES)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError):
        blocked("source contracts, envelope, or G12 native gates inconsistent")
    results={}
    for stage in STAGES:
        receipt=raw[stage]
        if receipt is None:
            status=STATUS_MISSING
            code="NO_SANITIZED_RECEIPT_PROVIDED"
        else:
            try:
                _valid_stage(stage,receipt,contracts,raw)
            except (ValueError,TypeError,KeyError,IndexError,AttributeError):
                status=STATUS_BLOCKED
                code="INVALID_SCHEMA_HASH_COUNTER_OR_NATIVE_ASSERTION"
            else:
                if stage=="B10" and results["B09"]["status"]!=STATUS_UNVERIFIED:
                    status=STATUS_DEPENDENCY
                    code="B09_VALIDATED_RECEIPT_REQUIRED_BEFORE_B10"
                elif stage=="B11" and (
                    results["B09"]["status"]!=STATUS_UNVERIFIED
                    or results["B10"]["status"]!=STATUS_UNVERIFIED
                ):
                    status=STATUS_DEPENDENCY
                    code="B09_AND_B10_VALIDATED_RECEIPTS_REQUIRED_BEFORE_B11"
                else:
                    status=STATUS_UNVERIFIED
                    code="WELL_FORMED_SELF_REPORTED_NOT_AUTHENTICATED"
        results[stage]={
            "status":status,
            "reason_code":code,
            "human_review_required":True,
            "physical_origin_authenticated":False,
            "native_approval":False,
            "next_human_action":STAGE_CHECKS[stage],
        }
    totals={
        STATUS_MISSING:sum(v["status"]==STATUS_MISSING for v in results.values()),
        STATUS_BLOCKED:sum(v["status"]==STATUS_BLOCKED for v in results.values()),
        STATUS_DEPENDENCY:sum(v["status"]==STATUS_DEPENDENCY for v in results.values()),
        STATUS_UNVERIFIED:sum(v["status"]==STATUS_UNVERIFIED for v in results.values()),
    }
    # Never make readiness contingent solely on the shape of JSON. Even five
    # well-formed receipts cannot authorize Game.exe or local save access.
    if totals[STATUS_BLOCKED]:
        overall="BLOCKED_CONFLICTING_OR_UNSAFE_REPORTS"
    elif totals[STATUS_DEPENDENCY]:
        overall="BLOCKED_MISSING_CHAIN_PREREQUISITES"
    elif totals[STATUS_MISSING]:
        overall="INCOMPLETE_DOCUMENTARY_HANDOFF"
    else:
        overall="DOCUMENTARY_REVIEW_ONLY_NATIVE_APPROVAL_PENDING"
    return {
        "schema":1,"region":"SINNOH","stage":"L02",
        "status":overall,
        "mode":"OFFLINE_SANITIZED_METADATA_REVIEW_ONLY",
        "reports":results,
        "counts":{
            "total":5,"missing":totals[STATUS_MISSING],
            "conflicting":totals[STATUS_BLOCKED],
            "missing_prerequisite":totals[STATUS_DEPENDENCY],
            "self_reported_unverified":totals[STATUS_UNVERIFIED],
            "independently_accepted":0,
        },
        "chronology_dates_in_sanitized_sources_available":False,
        "b11_session_link_in_sanitized_sources_available":False,
        "independent_receipt_authenticity_proven":False,
        "documentary_review_cannot_schedule_native_QA":True,
        "github_checklist_only":list(GENERAL_CHECKS),
        "technical_blocks":[
            "B09/B10 clone SHA relation is a declaration, not physical proof",
            "B11 counts prove only explicitly monitored scope, never global save isolation",
            "R07 map reservations are not confirmed by self-report",
            "R08 license-review counts are not grants of rights",
            "R09 Windows and Android native QA needs independently reviewed evidence",
        ],
        "native_cases_total":44,"windows_cases":43,"android_cases":1,
        "native_cases_completed":0,"native_cases_approved":0,
        "local_qa_gates":{f"L{i:02}":"PENDING" for i in range(1,6)},
        "r07_complete":False,"r08_complete":False,"r09_complete":False,
        "game_exe_tested":False,"joiplay_tested":False,
        "windows_sandbox_executed":False,
        "host_saves_accessed":False,"host_saves_globally_isolated_proven":False,
        "game_installed":False,"sinnoh_playable":False,
        "may_start_game_in_host":False,"may_start_game_in_vm":False,
        "may_install_live_game":False,
        "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
        "result_contains_private_paths_or_hashes":False,
        "auto_uploaded":False,
    }

def run(root=ROOT,*,workspace=False):
    return review(*load_sources(root,workspace=workspace))

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    # argparse would echo unknown --file C:\Users... values; pre-screen.
    if argv not in ([],["--workspace-reports"],["--help"],["-h"]):
        print("SINNOH_L02_BLOCKED: unsupported option",file=sys.stderr)
        return 2
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace-reports",action="store_true",
                   help="ONLY inspect fixed, manually prepared .blue-work L00 sanitized input")
    args=p.parse_args(argv)
    try:
        result=run(workspace=args.workspace_reports)
        print(json.dumps(result,ensure_ascii=True,indent=2,sort_keys=True))
        if result["counts"]["conflicting"] or result["counts"]["missing_prerequisite"]:
            return 2
        return 0  # Only JSON consistency success; NOT native acceptance.
    except (ValueError,OSError,TypeError,KeyError,IndexError,UnicodeError,AttributeError):
        print("SINNOH_L02_BLOCKED: source unavailable or fails protected public schema",
              file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
