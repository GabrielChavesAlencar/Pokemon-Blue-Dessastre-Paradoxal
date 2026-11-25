"""Read-only F12B3 Blue-Story eligibility diagnostic.
A source candidate is never a runtime proof. The existing QA copy is built
without Windworks until a reviewed access/event implementation is available.
"""
import hashlib
from pathlib import Path
import sinnoh_f12b2_windworks_evidence as evidence
import sinnoh_f12b_windworks as wind

ROOT=Path(__file__).resolve().parents[2]

def blocked(reason):
    return {"status":"WINDWORKS_BLOCKED","blockers":[reason],
            "runtime_install_enabled":False,"new_maps":0,"new_portals":0,
            "native_bindings":0,"items_granted":0,"native_verified":False,
            "saves_accessed":False}

def assess(report, mapping):
    if set(mapping)!=wind.gym.GYM_SETS[7] or len(mapping)!=139 or len(set(mapping.values()))!=139:
        return blocked("requires_full_f11h_baseline")
    if not isinstance(report,dict) or report.get("status")!="EVIDENCE_ONLY" or report.get("baseline_maps")!=139 or report.get("baseline_preserved") is not True or report.get("native_verified") is not False:
        return blocked("invalid_evidence_report")
    events=report.get("windworks_events",[])
    if len(events)!=5 or len({r["event_id"] for r in events})!=5 or any(r.get("binding_approved") is not False for r in events):
        return blocked("invalid_five_event_inventory")
    source=[r for r in report.get("nearby_source_maps",[]) if r.get("source_id")==111]
    if len(source)!=1 or source[0].get("source_sha256")!=wind.HASH:
        return blocked("windworks_source_hash_not_verified")
    result=blocked("reviewed_access_geometry_and_event_implementation_required")
    incoming=report.get("incoming_static_transfers",[])
    seams=report.get("windworks_source_seams",[])
    mars=report.get("mars_literal_candidates",[])
    key=report.get("works_key_script_candidates",[])
    pbs=report.get("source_pbs_files",[])
    if not incoming and not seams:result["blockers"].append("no_source_access_candidate")
    if not mars:result["blockers"].append("mars_identity_not_found")
    if not key:result["blockers"].append("works_key_script_not_found")
    if not pbs:result["blockers"].append("source_trainer_item_pbs_missing")
    result.update(source_events_reviewed=5,source_hash=wind.HASH,
                  incoming_candidates=len(incoming),seam_candidates=len(seams),
                  mars_candidates=len(mars),works_key_candidates=len(key),
                  source_pbs_files=len(pbs),baseline_maps=139,
                  baseline_preserved=True)
    return result

def preflight(blobs,mapping,path,root=ROOT):
    if set(mapping)!=wind.gym.GYM_SETS[7] or len(mapping)!=139:
        return blocked("requires_full_f11h_baseline")
    # The audit consumes only the verified source archive and the in-memory
    # generated baseline. It does not open the native game or its save files.
    before={k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()}
    try:
        report=evidence.audit(blobs,mapping,path,root)
        result=assess(report,mapping)
    except (OSError,ValueError,TypeError,KeyError,UnicodeError) as exc:
        # Failure is explicit; Windworks stays unavailable. Do not deny
        # access to already validated F11 maps on an optional F12 failure.
        result=blocked("source_audit_failed:"+type(exc).__name__)
    if before!={k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()}:
        raise ValueError("F12B3_BASELINE_MUTATED")
    return result
