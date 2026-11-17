#!/usr/bin/env python3
"""S31: cross-check CH20's 44-case plan with a verified private QA ledger.

This is a READ-ONLY technical reporting tool. No Game.exe or Android access,
no release marker, no user saves, no native gameplay certification.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
if str(ROOT / "scripts/regions") not in sys.path:
    sys.path.insert(0,str(ROOT / "scripts/regions"))
from audit_sinnoh_android_ch20 import audit as audit_static
from audit_sinnoh_android_ch20 import EXPECTED_COUNTS
from audit_sinnoh_playtest import checked_qa, expected_cases, audit as audit_private

CONTRACT = ROOT / "data/regions/sinnoh-s31-acceptance.json"
EXPECTED = {
  "schema": 1,
  "region": "SINNOH",
  "task": "S31",
  "status": "ACCEPTANCE_TOOLING_READY_NATIVE_EVIDENCE_MISSING",
  "technical_scope": "OFFLINE_READ_ONLY_REPORT_ONLY",
  "source_checks": {
    "android": "scripts/regions/audit_sinnoh_android_ch20.py",
    "native": "scripts/regions/audit_sinnoh_playtest.py",
    "progress": "data/regions/sinnoh-progress.json",
    "intro": "data/regions/sinnoh-twinleaf-events.json",
    "plan": "docs/SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md"
  },
  "expected_cases": 44,
  "expected_by_kind": {
    "starter": 3,
    "barry": 12,
    "save_reload": 3,
    "warp": 16,
    "npc": 5,
    "regression": 4,
    "android": 1
  },
  "windows_cases_required": 43,
  "android_cases_required": 1,
  "qa_t_substeps_complete": 4,
  "qa_t_substeps_total": 7,
  "native_observations_verified": 0,
  "native_game_exe_tested": False,
  "native_joiplay_tested": False,
  "independent_human_review": False,
  "release_marker_allowed": False,
  "source_rights_verified": False,
  "physical_maps_verified": False,
  "gameplay_playable": False,
  "auto_accept": False,
  "phase_approval_allowed": False,
  "source_assets_copied": False,
  "policies": {
    "require_isolated_qa_profile": True,
    "strict_compile_token_and_profile": True,
    "compare_all_44_case_ids": True,
    "never_use_android_for_windows_case": True,
    "require_evidence_file_and_sha256": True,
    "reject_unknown_or_reordered_cases": True,
    "require_independent_human_review": True,
    "no_release_marker_from_tool": True,
    "no_native_gate_update_from_ci": True,
    "do_not_modify_main_game_or_saves": True,
    "require_rights_and_real_map_assets": True
  },
  "notes": "S31 entrega apenas protocolo de aceite offline e comparador dos roteiros CH20/QA. Nao implica executar Game.exe Windows, JoiPlay, mapas reais ou auditar licencas. T05/T06/T07 e I06/I07/I08 permanecem pendentes. Mesmo 44 evidencias registradas por um operador exigem revisao humana independente e nao liberam publicacao automaticamente."
};

def blocked(msg):
    raise ValueError("SINNOH_S31_BLOCKED: " + msg)

def check_contract(spec, progress, static):
    if not isinstance(spec,dict) or set(spec)!=set(EXPECTED):
        blocked("contrato S31 incompleto ou adulterado")
    for key,wanted in EXPECTED.items():
        if type(spec[key]) is not type(wanted) or spec[key]!=wanted:
            blocked("status/contagem/gate/direitos adulterados: "+key)
    if (not isinstance(static,dict) or static.get("checklist_total")!=44
            or static.get("by_kind")!=EXPECTED_COUNTS
            or static.get("mode")!="STATIC_JOIPLAY_PREFLIGHT_NOT_NATIVE_QA"
            or static.get("completed_native_cases")!=0
            or static.get("native_gameplay_verified") is not False
            or static.get("joiplay_tested") is not False
            or static.get("ready_marker_created") is not False
            or len(static.get("cases",[]))!=44):
        blocked("preflight CH20 nao e checklist estatico e integro")
    if (not isinstance(progress,dict) or progress.get("region")!="SINNOH"
            or progress.get("development",{}).get("total")!=32
            or progress.get("development",{}).get("done")!=32
            or progress.get("development",{}).get("partial")!=0
            or progress.get("development",{}).get("pending")!=0
            or progress.get("development",{}).get("percent_complete")!=100):
        blocked("Barra A da engenharia nao coincide com S31")
    tasks=progress.get("tasks",[])
    if (not isinstance(tasks,list) or len(tasks)!=32
            or [x.get("id") for x in tasks]!=[f"S{i:02}" for i in range(1,33)]
            or any(x.get("status")!="done" for x in tasks)):
        blocked("tarefas S01..S32 invalidas")
    gates=progress.get("phase_gates",{})
    if (gates.get("total")!=13 or any(gates.get(k)!=0 for k in
        ("technically_approved","playable_in_game_executable","fully_tested_native"))):
        blocked("aceite nativo falsamente aprovado pela Barra A")
    ledger=progress.get("native_playtest_workstream",{})
    if (ledger.get("complete")!=4 or ledger.get("total")!=7
            or [x.get("complete") for x in ledger.get("substeps",[])]!=
                [True,True,True,True,False,False,False]):
        blocked("T05/T06/T07 ainda dependem de teste real")
    for key in ("native_qa_approved","android_joi_play_tested",
                "manual_evidence_accepted","real_game_exe_playtest",
                "ready_marker_created","main_game_or_user_saves_modified"):
        if ledger.get(key) is not False:
            blocked("ledger nativo foi promovido sem QA: "+key)
    if progress.get("intro_workstream",{}).get("complete")!=5 or (
            progress.get("remap_workstream",{}).get("complete")!=6):
        blocked("I06-I08 ou R07-R09 ainda requerem prova fisica")
    if not isinstance(static.get("checklist_sha256"),str) or len(static["checklist_sha256"])!=64:
        blocked("identidade do roteiro CH20 invalida")
    case_ids=[case.get("id") for case in static["cases"]]
    if len(set(case_ids))!=44:
        blocked("44 IDs unicos obrigatorios")
    return case_ids

def reconcile(spec,progress,static, *,qa=None,qa_project=None):
    case_ids=check_contract(spec,progress,static)
    observed=0
    by_kind={k:{"complete":0,"total":v} for k,v in EXPECTED_COUNTS.items()}
    bound_profile=False
    if qa is not None:
        # Never trust user-pasted observations. The existing native auditor
        # verifies the private QA copy, exact token, profile and hashed files.
        if qa_project is None: qa_project=ROOT
        checked,meta=checked_qa(qa,Path(qa_project))
        native_ids=[case["id"] for case in expected_cases(meta)]
        if case_ids!=native_ids:
            blocked("44 casos CH20 e QA diferem ou foram reordenados")
        result=audit_private(checked,project=Path(qa_project))
        if (result.get("total")!=44 or
                result.get("automatically_approved_gameplay") is not False or
                result.get("native_game_executed_independently_proven") is not False or
                result.get("may_create_barry_ready_marker") is not False):
            blocked("auditor QA alegou aprovacao que nao pode certificar")
        observed=result["completed"]
        if type(observed) is not int or not 0<=observed<=44:
            blocked("contagem nativa invalida")
        if not isinstance(result.get("by_kind"),dict):
            blocked("resumo de evidencias ausente")
        for kind,total in EXPECTED_COUNTS.items():
            row=result["by_kind"].get(kind)
            if not isinstance(row,dict) or row.get("total")!=total or (
                type(row.get("complete")) is not int or not 0<=row["complete"]<=total):
                blocked("resumo QA invalido: "+kind)
            by_kind[kind]=row
        if sum(v["complete"] for v in by_kind.values())!=observed:
            blocked("evidencias por categoria inconsistentes")
        bound_profile=True
    status=("BLOCKED_NO_COMPILED_QA" if not bound_profile else
            "PENDING_REAL_QA_EVIDENCE" if observed<44 else
            "ALL_44_RECORDED_MANUAL_REVIEW_AND_RIGHTS_STILL_REQUIRED")
    return {
        "schema":1,"region":"SINNOH","task":"S31",
        "status":status,"technical_contract_ready":True,
        "expected_native_cases":44,"observations_with_consistent_evidence":observed,
        "remaining_cases":44-observed,"by_kind":by_kind,
        "checklist_sha256":static["checklist_sha256"],
        "private_compiled_qa_profile_checked":bound_profile,
        "missing":["auditoria de direitos e mapas realmente autorizados",
                   "I06-I08 (5/8) e R07-R09 (6/9)",
                   "T05-T07 (4/7) e revisao independente Windows/JoiPlay"],
        "native_game_exe_independently_verified":False,
        "joiplay_independently_verified":False,
        "release_marker_allowed":False,"can_merge_native_assets":False,
        "can_mark_playable":False,"automatic_approval":False,
        "game_or_user_saves_modified":False,
        "interpretation":"32/32 sao entregaveis de engenharia; 0/13 barras nativas ate QA externo"
    }

def run(*,root=ROOT,qa=None,qa_project=None):
    root=Path(root)
    spec=json.loads((root/"data/regions/sinnoh-s31-acceptance.json").read_text("utf-8"))
    progress=json.loads((root/"data/regions/sinnoh-progress.json").read_text("utf-8"))
    static=audit_static(root=root)
    return reconcile(spec,progress,static,qa=qa,qa_project=qa_project or root)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qa",type=Path,help="copia QA local .blue-work apos compilacao verificada")
    parser.add_argument("--qa-project",type=Path,help="raiz local que contem a copia QA")
    parser.add_argument("--require-native",action="store_true",
                        help="falhar se nao houver 44 evidencias; nao aprova jogo")
    args=parser.parse_args(argv)
    try:
        report=run(qa=args.qa,qa_project=args.qa_project)
        print(json.dumps(report,indent=2,ensure_ascii=False))
        # Even all 44 screenshots cannot substitute independent human review.
        if args.require_native and report["remaining_cases"]:
            return 2
        return 0
    except (OSError,ValueError,TypeError,KeyError,IndexError) as e:
        print(str(e),file=sys.stderr)
        return 2

if __name__=="__main__": raise SystemExit(main())
