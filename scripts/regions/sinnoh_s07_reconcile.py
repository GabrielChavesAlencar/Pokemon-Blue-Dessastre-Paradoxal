#!/usr/bin/env python3
"""S07: reconcile an immutable Sinnoh candidate with LOCAL reservations, read-only.

Never reserves MapIDs, imports a donor asset, changes game/ or claims native QA.
Missing Kanto/Johto/Hoenn evidence returns a BLOCKED result, not approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

from audit_sinnoh_r07_reservations import audit as audit_r07, inspect_native
from plan_sinnoh_remap import make_plan, fail as plan_fail

ROOT=Path(__file__).resolve().parents[2]
MAX_JSON=5_000_000
INPUT_NAMES=("source_audit","candidate","prior")

def blocked(message):
    raise ValueError("SINNOH_S07_RECONCILE_BLOCKED: "+message)

def read_local(project, file):
    """Only immutable user-supplied JSON under ignored .blue-work is accepted."""
    root=Path(project).absolute()
    work=root/".blue-work"
    file=Path(file).absolute()
    if (root.is_symlink() or not root.is_dir() or work.is_symlink() or
        not work.is_dir() or file.is_symlink() or not file.is_file() or
        not file.is_relative_to(work) or
        not file.resolve().is_relative_to(work.resolve()) or
        file.stat().st_size>MAX_JSON):
        blocked("JSON deve existir apenas em .blue-work, sem symlink")
    data=json.loads(file.read_text("utf-8"))
    if type(data) is not dict:
        blocked("JSON deve ser objeto")
    return data

def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,
        ensure_ascii=True,separators=(",",":")).encode("ascii")).hexdigest()

def reconcile(project,source_audit,candidate,prior=None):
    if (type(source_audit) is not dict or type(candidate) is not dict or
        prior is not None and type(prior) is not dict):
        blocked("auditoria e planos precisam ser objetos")
    if (candidate.get("mode")!="REMAP_CANDIDATE_ONLY" or
        candidate.get("region")!="SINNOH" or
        candidate.get("status")!="PENDING_NATIVE_AND_RIGHTS_REVIEW" or
        candidate.get("can_install") is not False or
        candidate.get("may_stage_real_map_data") is not False or
        candidate.get("game_or_saves_modified") is not False or
        candidate.get("four_digit_destination_ids_permitted") is not False or
        candidate.get("other_region_reservations_fully_verified") is not False):
        blocked("plano diz estar instalado/aprovado ou nao e candidato S07")
    request={
        "schema":1,"region":"SINNOH",
        "source_zip_sha256":candidate.get("source_zip_sha256"),
        "source_mapinfos_sha256":candidate.get("source_mapinfos_sha256"),
        "source_tilesets_sha256":candidate.get("source_tilesets_sha256"),
        "source_map_hashes":candidate.get("source_map_hashes"),
        "mapping":candidate.get("mapping"),"symbols":candidate.get("symbols")
    }
    protected=candidate.get("other_region_reservations_listed")
    if type(protected) is not list:
        blocked("reservas declaradas ausentes")
    regenerated=make_plan(source_audit,request,prior=prior,
        reserved={"schema":1,"region":"SINNOH","protected_ids":protected})
    if candidate!=regenerated or fingerprint({k:v for k,v in candidate.items()
            if k!="plan_sha256"})!=candidate.get("plan_sha256"):
        blocked("candidato, SHA, transferencias, snapshots ou MapIDs adulterados")
    # Recheck real installed native inventory, not a caller-provided screenshot.
    root=Path(project).absolute()
    if root.is_symlink() or not root.is_dir():
        blocked("projeto inseguro")
    native=inspect_native(root/"game"/"Data")
    expected=source_audit.get("native",{}).get("occupied_ids")
    if (native.get("status")!="LOCAL_READ_ONLY" or
        type(expected) is not list or
        sorted(expected)!=sorted(native.get("occupied_ids") or [])):
        blocked("snapshot de game/Data mudou; volte a auditar a origem e o jogo")
    r07=audit_r07(root,plan=candidate)
    if (r07.get("r07_complete") is not False or
        r07.get("rights_verified") is not False or
        r07.get("game_or_saves_modified") is not False or
        r07.get("may_apply_to_main_game") is not False):
        blocked("relatorio R07 promoveu indevidamente instalacao")
    ready=r07["candidate_safety_reviewable"] is True
    return {
      "schema":1,"region":"SINNOH","stage":"S07",
      "mode":"LOCAL_RECONCILIATION_READ_ONLY",
      "status":("RECONCILED_FOR_MANUAL_REVIEW_NOT_APPROVED" if ready
                else "BLOCKED_NATIVE_OR_FUTURE_RESERVATIONS"),
      "source_maps":len(candidate["maps"]),
      "static_transfer_rewrites":len(candidate["proposed_static_transfer_rewrites"]),
      "plan_sha256":candidate["plan_sha256"],
      "native_mapinfos_sha256":r07["native_mapinfos_sha256"],
      "native_occupied_count":r07["native_occupied_count"],
      "future_regions_with_evidence":r07["future_regions_with_evidence"],
      "future_regions_required":r07["future_regions_required"],
      "collisions":r07["collisions"],"blockers":r07["blockers"],
      "candidate_safety_reviewable":ready,
      "dynamic_transfers_needing_manual_review":
          candidate["dynamic_transfer_commands_for_manual_review"],
      "rights_verified":False,"r07_complete":False,
      "r08_real_maps_imported":False,"r09_game_exe_joiplay_tested":False,
      "source_assets_copied":False,"map_ids_reserved":False,
      "main_game_or_saves_modified":False,"can_install":False,
      "gameplay_approved":False,"native_qa_approved":False,
    }

def main(argv=None):
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--project",type=Path,default=ROOT)
    cli.add_argument("--source-audit",type=Path,required=True)
    cli.add_argument("--candidate",type=Path,required=True)
    cli.add_argument("--prior",type=Path)
    args=cli.parse_args(argv)
    try:
        source=read_local(args.project,args.source_audit)
        candidate=read_local(args.project,args.candidate)
        previous=read_local(args.project,args.prior) if args.prior else None
        result=reconcile(args.project,source,candidate,previous)
    except (OSError,ValueError,TypeError,KeyError,UnicodeError) as exc:
        print(str(exc),file=sys.stderr)
        return 2
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return 0 if result["candidate_safety_reviewable"] else 2

if __name__=="__main__":
    raise SystemExit(main())
