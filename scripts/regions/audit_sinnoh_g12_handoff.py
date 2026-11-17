#!/usr/bin/env python3
"""G12: public final Sinnoh GitHub handoff, always unapproved for native play.

Cross-check existing G01–G11 documentation, G11 B07–B11 contract audit,
CH20's authoritative 44 case checklist and the versioned G12 handoff.
Read ONLY public repository text/metadata. Never inspect the user's PC, game,
WSB guest, save files, private stage, real PNG, or runtime executable.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_android_ch20 as ch20
import audit_sinnoh_g11_ci_chain as g11
import audit_sinnoh_playtest as playtest

HANDOFF="data/regions/sinnoh-g12-native-handoff.json"
LEDGER="data/regions/sinnoh-progress.json"
DOCUMENTS={
    "G01":"docs/SINNOH_G01_AUDITOR_RECUPERACAO_B09.md",
    "G02":"docs/SINNOH_G02_B09_PROGRESSO_CI_ACEITE.md",
    "G03":"docs/SINNOH_G03_MATRIZ_MAPIDS_REGIONAIS.md",
    "G04":"docs/SINNOH_G04_SEGURANCA_WINDOWS_SANDBOX.md",
    "G05":"docs/SINNOH_G05_AUDITORIA_PRIVADA_SAVES_B11.md",
    "G06":"docs/SINNOH_G06_AUDITORIA_GRAFICA_PNG_TILESETS.md",
    "G07":"docs/SINNOH_G07_VINCULOS_FISICOS_TWINLEAF.md",
    "G08":"docs/SINNOH_G08_ROWAN_BARRY_INICIAIS_BALANCEAMENTO.md",
    "G09":"docs/SINNOH_G09_GINASIOS_HMS_LIGA_POSJOGO.md",
    "G10":"docs/SINNOH_G10_PORTAL_EVIDENCIAS_IMPLANTACAO.md",
    "G11":"docs/SINNOH_G11_INTEGRACAO_CI_B07_B11.md",
}
COUNTS={"starter":3,"barry":12,"save_reload":3,"warp":16,
        "npc":5,"regression":4,"android":1}
GATES=("L01","L02","L03","L04","L05")
EVIDENCE_REQUIREMENTS={
    "starter":"Windows: captura da escolha na Poké Bola física, espécie recebida e segunda bola rejeitada",
    "barry":"Windows: espécie/versão do Barry, nível observado 70%/90%, resultado e canLose com registro de batalha",
    "save_reload":"Windows: perfil QA isolado, persistência do inicial, equipe e Pokédex após carregar",
    "warp":"Windows: passagem real e retorno, mapa de origem/destino vinculados, coordenadas e passabilidade verificadas",
    "npc":"Windows: sprite e handler autoral executados no mapa físico, flags e ausência de duplicidade",
    "regression":"Windows: viagem de região e isolamento de saves, HMs, itens-chave, Pokémon e flags",
    "android":"Android/JoiPlay: build isolada autorizada, início, entrada em mapas, save/load e logs/capturas em dispositivo",
}


def blocked(reason):
    raise ValueError("SINNOH_G12_BLOCKED: "+reason)


def safe_text(root,relative):
    f=root/relative
    if f.is_symlink() or not f.is_file() or f.stat().st_size>250_000:
        blocked("source document missing, symlinked or oversized")
    try:
        return f.read_text(encoding="utf-8-sig")
    except (OSError,UnicodeError):
        blocked("invalid public document")


def expected_rows(ch20_cases):
    expected=[]
    for row in ch20_cases:
        kind=row["kind"]
        key=row["id"]
        e={"id":key,"kind":kind,
           "platform":"android" if kind=="android" else "windows",
           "native_status":"pending","evidence":None,"observation":None}
        if kind=="starter":
            species=key.removeprefix("ball-")
            e.update(starter=species,expected_species=species,
                     second_ball_must_be_denied=True)
        elif kind=="barry":
            species=key.split("-")[1]
            e.update(starter=species,expected_rival=row["expected_rival"],
                     mode=row["mode"],outcome=row["outcome"],
                     expected_scaling_percent=row["expected_scaling_percent"])
        elif kind=="save_reload":
            e.update(starter=key.removeprefix("save-reload-"))
        elif kind=="warp":
            e.update(from_symbol=row["from_symbol"],to_symbol=row["to_symbol"])
        elif kind=="npc":
            e.update(map_symbol=row["map_symbol"],handler=row["handler"])
        elif kind=="regression":
            e.update(region=row["region"])
        elif kind=="android":
            e.update(independent_save_required=True)
        else:
            blocked("unexpected CH20 category")
        expected.append(e)
    return expected


def audit(handoff,android_report,chain_report,ledger,docs):
    if (type(handoff) is not dict or type(android_report) is not dict or
            type(chain_report) is not dict or type(ledger) is not dict or
            type(docs) is not dict or set(docs)!=set(DOCUMENTS)):
        blocked("missing final handoff input")
    expected_handoff_keys={
        "schema","region","stage","version","status","original_case_source",
        "native_evidence_validator","b10_contract","b11_contract",
        "qa_prerequisites","category_counts","total_cases","windows_cases",
        "android_cases","completed_native_cases","manually_reviewed_cases",
        "real_b10_execution_verified","real_b11_save_isolation_verified",
        "real_map_ids_and_events_verified","asset_rights_verified",
        "native_pbs_compiled_verified","game_exe_tested","joiplay_tested",
        "r07_complete","r08_complete","r09_complete",
        "phase_b_approved","phase_c_approved","phase_d_approved",
        "can_launch_game_now","can_install_live_game","cases",
    }
    if set(handoff)!=expected_handoff_keys:
        blocked("unexpected or missing versioned handoff property")
    if (handoff.get("schema")!=1 or handoff.get("region")!="SINNOH" or
            handoff.get("stage")!="G12" or type(handoff.get("version")) is not int or
            handoff["version"]!=1 or
            handoff.get("status")!="GITHUB_HANDOFF_ONLY_NATIVE_QA_NOT_STARTED" or
            handoff.get("original_case_source")!="scripts/regions/audit_sinnoh_android_ch20.py" or
            handoff.get("native_evidence_validator")!="scripts/regions/audit_sinnoh_playtest.py" or
            handoff.get("b10_contract")!="data/regions/sinnoh-b10-save-isolation.json" or
            handoff.get("b11_contract")!="data/regions/sinnoh-b11-host-save-audit.json"):
        blocked("handoff version/source identity changed")
    if (android_report.get("region")!="SINNOH" or android_report.get("chapter")!="CH20" or
            android_report.get("mode")!="STATIC_JOIPLAY_PREFLIGHT_NOT_NATIVE_QA" or
            android_report.get("checklist_total")!=44 or
            android_report.get("by_kind")!=COUNTS or
            android_report.get("completed_native_cases")!=0 or
            android_report.get("package",{}).get("status")!="NOT_PROVIDED" or
            android_report.get("native_gameplay_verified") is not False or
            android_report.get("manual_evidence_accepted") is not False or
            android_report.get("game_exe_tested") is not False or
            android_report.get("joiplay_tested") is not False):
        blocked("CH20 incorrectly reports a completed native test")
    raw_cases=android_report.get("cases")
    if (not isinstance(raw_cases,list) or len(raw_cases)!=44 or
            len({x.get("id") for x in raw_cases if isinstance(x,dict)})!=44 or
            Counter(x.get("kind") for x in raw_cases if isinstance(x,dict))!=COUNTS or
            any(not isinstance(x,dict) or x.get("native_status")!="pending" or
                x.get("evidence") is not None for x in raw_cases)):
        blocked("CH20 case IDs, distribution or pending state forged")
    expected=expected_rows(raw_cases)
    actual=handoff.get("cases")
    if type(actual) is not list or actual!=expected:
        blocked("G12 44-case matrix drift, duplicate, forged native status or evidence")
    if (type(handoff.get("category_counts")) is not dict or
            handoff["category_counts"]!=COUNTS or
            handoff.get("total_cases")!=44 or
            handoff.get("windows_cases")!=43 or
            handoff.get("android_cases")!=1 or
            handoff.get("completed_native_cases")!=0 or
            handoff.get("manually_reviewed_cases")!=0):
        blocked("native case count or approval forged")
    for field in ("real_b10_execution_verified",
                  "real_b11_save_isolation_verified",
                  "real_map_ids_and_events_verified",
                  "asset_rights_verified","native_pbs_compiled_verified",
                  "game_exe_tested","joiplay_tested",
                  "r07_complete","r08_complete","r09_complete",
                  "can_launch_game_now","can_install_live_game"):
        if handoff.get(field) is not False:
            blocked("G12 claim of native runtime, rights or gameplay")
    for phase in ("b","c","d"):
        if type(handoff.get("phase_"+phase+"_approved")) is not int or handoff["phase_"+phase+"_approved"]!=0:
            blocked("native phase approval fabricated")
    prereq=handoff.get("qa_prerequisites")
    if (not isinstance(prereq,list) or len(prereq)!=5 or
            [p.get("id") for p in prereq if isinstance(p,dict)]!=list(GATES) or
            any(not isinstance(p,dict) or set(p)!={"id","name","status","required"} or
                p["status"]!="pending" or not isinstance(p["name"],str) or
                not isinstance(p["required"],str) or
                len(p["name"])<5 or len(p["required"])<40
                for p in prereq)):
        blocked("unsafe handoff gate status or missing evidence checklist")
    # Derive expected case classification from the actual CH20-generated IDs.
    if (tuple(playtest.STARS)!=tuple(ch20.STARTERS) or
            tuple(playtest.RIVALS)!=tuple(ch20.RIVALS) or
            tuple(playtest.REGIONS)!=tuple(ch20.REGIONS) or
            tuple(playtest.MODES)!=("normal","master")):
        blocked("native playtest and CH20 source drift")

    if (chain_report.get("stage")!="G11" or
            chain_report.get("status")!="B07_B11_PUBLIC_CONTRACT_CHAIN_RECONCILED_SYNTHETIC_ONLY" or
            [x["stage"] for x in chain_report.get("chain",[])]!=["B07","B08","B09","B10","B11"] or
            chain_report.get("expected_synthetic_clone_map_count")!=702 or
            chain_report.get("candidate_terrain_maps")!=54 or
            chain_report.get("private_pngs_required_by_B08")!=14 or
            chain_report.get("public_report_only") is not True or
            chain_report.get("game_exe_tested") is not False or
            chain_report.get("joiplay_tested") is not False or
            chain_report.get("can_install_live_game") is not False or
            chain_report.get("sandbox_run_performed") is not False or
            chain_report.get("save_snapshot_coverage_proven") is not False or
            chain_report.get("private_baseline_uploaded") is not False):
        blocked("G11 B07–B11 chain is not safe for G12 handoff")
    if (ledger.get("schema")!=1 or ledger.get("region")!="SINNOH" or
            ledger.get("development",{}).get("done")!=32 or
            ledger.get("development",{}).get("total")!=32 or
            ledger.get("chat_direct_workstream",{}).get("done")!=20 or
            ledger.get("chat_direct_workstream",{}).get("total")!=20 or
            ledger.get("phase_gates",{}).get("total")!=13 or
            any(ledger["phase_gates"].get(k)!=0 for k in
                ("technically_approved","playable_in_game_executable","fully_tested_native")) or
            ledger.get("remap_workstream",{}).get("complete")!=6 or
            ledger.get("remap_workstream",{}).get("total")!=9 or
            ledger.get("intro_workstream",{}).get("native_verified") is not False or
            ledger.get("barry_pbs_workstream",{}).get("pbs_compiled") is not False or
            ledger.get("native_playtest_workstream",{}).get("manual_evidence_accepted") is not False or
            ledger.get("native_playtest_workstream",{}).get("native_qa_approved") is not False):
        blocked("ledger incorrectly claims native progress")
    incomplete={x["id"]:x["complete"] for x in ledger["remap_workstream"]["substeps"]}
    if incomplete.get("R07") is not False or incomplete.get("R08") is not False or incomplete.get("R09") is not False:
        blocked("R07–R09 must remain incomplete until physical evidence")
    published={}
    for stage,content in docs.items():
        if (not isinstance(content,str) or len(content)<250 or
                "G"+stage[1:] not in content or not content.lstrip().startswith("#")):
            blocked("earlier GitHub evidence is missing or altered")
        published[stage]={"path":DOCUMENTS[stage],
                          "sha256":hashlib.sha256(content.encode("utf-8")).hexdigest(),
                          "github_documentation_present":True,
                          "native_approval_from_document":False}
    return {
        "schema":1,"region":"SINNOH","stage":"G12",
        "status":"GITHUB_G01_G12_HANDOFF_PREPARED_NATIVE_ACCEPTANCE_PENDING",
        "mode":"PUBLIC_SOURCES_ONLY_ZERO_NATIVE_EVIDENCE",
        "github_stages_audited":11,
        "github_stages_with_versioned_handoff":12,
        "stage_documents":published,
        "chain_status":chain_report["status"],
        "chain_stages":["B07","B08","B09","B10","B11"],
        "physical_clone_expected_map_count":702,
        "terrain_candidates_not_installed":54,
        "actual_donor_png_bytes_inspected":0,
        "native_case_source":"CH20",
        "native_case_hash_sha256":android_report["checklist_sha256"],
        "case_counts":COUNTS.copy(),
        "native_cases_total":44,"windows_cases":43,"android_cases":1,
        "completed_native_cases":0,"evidence_accepted_cases":0,
        "native_case_matrix":[{
            "id":case["id"],"kind":case["kind"],
            "platform":case["platform"],"status":"pending",
            "evidence":None,"required_human_evidence":EVIDENCE_REQUIREMENTS[case["kind"]],
        } for case in expected],
        "local_gates":[{
            "id":p["id"],"status":"pending",
            "description":p["name"],"required":p["required"],
        } for p in prereq],
        "blocked_until_physical_evidence":[
            "B09 real map/asset provenance and all future regional MapIDs confirmed",
            "R08 individual asset licenses, 9 symbolic map bindings and 16 real warps",
            "B10 host Windows Sandbox availability, supported Windows edition and readonly isolation",
            "B11 independently reviewed host-save path coverage and unchanged baseline",
            "Barry PBS and all authored events compiled in independent QA profile",
            "43 Windows cases and 1 Android/JoiPlay case executed and manually reviewed",
        ],
        "main_game_or_user_saves_modified":False,
        "real_windows_sandbox_started":False,
        "game_exe_tested":False,"joiplay_tested":False,
        "r07_complete":False,"r08_complete":False,"r09_complete":False,
        "may_launch_native_on_host":False,
        "can_install_live_game":False,"gameplay_approved":False,
        "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
        "github_delivery_completion_is_not_gameplay_completion":True,
    }


def run(root=ROOT):
    root=Path(root)
    handoff=json.loads(safe_text(root,HANDOFF))
    ledger=json.loads(safe_text(root,LEDGER))
    docs={k:safe_text(root,path) for k,path in DOCUMENTS.items()}
    # Both auditable inputs are computed using existing public validators.
    return audit(handoff,ch20.audit(root),g11.run(root),ledger,docs)


def main(argv=None):
    try:
        if argv not in (None,[]):
            blocked("G12 does not accept local paths, saves or native evidence")
        print(json.dumps(run(),ensure_ascii=False,indent=2))
        return 0
    except (ValueError,OSError,TypeError,KeyError,IndexError,UnicodeError,AttributeError):
        print("SINNOH_G12_BLOCKED: public evidence, handoff or native-case matrix inconsistent",
              file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main(sys.argv[1:]))
