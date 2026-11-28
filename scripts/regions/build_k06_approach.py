"""Disposable K06 approach: restore only audited physical roads and underground doors."""
from __future__ import annotations

import json
import os
from pathlib import Path

from audit import ROOT, inventory, json_file, load
from build_k05_city import digest, isolate
from pilot import EVENT_CLASSES, PILOT_META, command, new_event, write_map
from qa_k04_migration import copy_for_ci

APPROACH=tuple(range(107,114))
EXACT_SEAMS=((93,"West",0,107,"East",15),(114,"East",0,111,"West",0))
SAVE_APP="Kanto K06 Approach CI"
PROOF="k06_approach_fixture_only"
MAP_DIR="kanto-k06-approach"
TRANSFERS={
    (107,5):((2,25),108,(11,5),0), (107,13):((9,19),109,(6,8),8),
    (108,1):((12,5),107,(3,25),0), (108,2):((0,5),168,(52,25),0),
    (109,1):((6,4),110,(76,3),0), (109,3):((6,9),107,(9,20),0),
    (110,1):((2,4),113,(7,4),0), (110,2):((77,3),109,(7,4),0),
    (111,1):((16,25),112,(1,5),0), (111,2):((7,29),113,(6,8),8),
    (112,1):((0,5),111,(15,25),0), (112,2):((12,5),168,(2,25),0),
    (113,1):((6,4),110,(3,4),6), (113,3):((6,9),111,(7,30),0),
}
TEMP_GATES={(108,2),(112,2)}


def planned_connections(text,mapping):
    """The disposable test can't inherit outdoor shortcuts from the preview."""
    controlled={mapping[i] for i in APPROACH}
    removed=[]
    kept=[]
    for raw in text.splitlines():
        body=raw.split("#",1)[0].strip()
        if body:
            parts=[s.strip() for s in body.split(",")]
            if len(parts)!=6 or not (parts[0].isdigit() and parts[3].isdigit()):
                raise ValueError("Formato de ligação nativa desconhecido.")
            if controlled&{int(parts[0]),int(parts[3])}:
                removed.append(body)
                continue
        kept.append(raw)
    for a,side,n,b,opposite,z in EXACT_SEAMS:
        kept.append(",".join(map(str,(mapping[a],side,n,mapping[b],opposite,z))))
    return "\n".join(kept)+"\n",removed


def verify_source(report):
    checked={(r["source"],r["event"]):(tuple(r["at"]),r["destination"],tuple(r["xy"]),r["direction"])
             for r in report["warps"] if r["source"] in APPROACH}
    if len([r for r in report["warps"] if r["source"] in APPROACH])!=len(TRANSFERS) or checked!=TRANSFERS:
        raise ValueError("Original Route 8 / underground / Route 7 door data differs.")
    if not set(EXACT_SEAMS)<={tuple(row) for row in report["connections"]}:
        raise ValueError("Missing original Lavender and Celadon physical edges.")


def apply_events(donor,native,sid,mapping):
    source,native=donor.attrs,native.attrs
    if any(source[k]!=native[k] for k in ("@width","@height","@data")) or native["@events"]:
        raise ValueError(f"K06 requires the intact event-free published preview for {sid}")
    for (area,eid),(at,destination,xy,direction) in TRANSFERS.items():
        if area!=sid:
            continue
        event=source["@events"][eid]
        if (event.attrs["@x"],event.attrs["@y"])!=at:
            raise ValueError(f"Original source door moved: {sid}/{eid}")
        if (area,eid) in TEMP_GATES:
            ops=[command(355,b'pbMessage(BlueKantoPilot.t("The gate to Saffron is closed. Use the Underground Path.", "A portaria de Saffron esta fechada. Use a Passagem Subterranea."))')]
        else:
            ops=[command(201,0,mapping[destination],*xy,direction,0)]
        native["@events"][eid]=new_event(event,ops,1,b"")


def run():
    if os.getenv("GITHUB_ACTIONS")!="true":
        raise ValueError("K06 approach staging is Windows CI only")
    w=ROOT/".blue-work"
    baseline=w/"kanto-k06-baseline"
    output=w/MAP_DIR
    source=w/"frlg-source/Essentials FRLG"
    receipt=json_file(ROOT/"k06-source-receipts/kanto-k06-source.json")
    verify_source(receipt)
    meta=json_file(baseline/PILOT_META)
    mapping={int(k):v for k,v in meta["maps"].items()}
    if len(mapping)!=178 or mapping.get(93)!=609:
        raise ValueError("K06 approach must start from the released K05 catalog.")
    _,base_files=inventory(baseline)
    _,donors=inventory(source)
    fingerprints={p.relative_to(baseline):digest(p) for p in base_files.values()}
    changed={base_files[mapping[sid]].relative_to(baseline) for sid in APPROACH}
    known_hashes={r["source"]:r["sha256"] for r in receipt["maps"]}
    copy_for_ci(baseline,output)
    for sid in APPROACH:
        path=base_files[mapping[sid]].relative_to(baseline)
        if digest(donors[sid])!=known_hashes[sid]:
            raise ValueError(f"K06 source digest drift for map {sid}.")
        donor,native=load(donors[sid]),load(output/path)
        apply_events(donor,native,sid,mapping)
        write_map(output/path,native,EVENT_CLASSES)
        if load(output/path)!=native:
            raise ValueError(f"K06 native event serialization failed for map {sid}.")
    seams=output/"PBS/map_connections_kanto.txt"
    text,removed=planned_connections(seams.read_text("utf-8-sig"),mapping)
    seams.write_text(text,encoding="utf8")
    if any(digest(baseline/p)!=checksum or (p not in changed and digest(output/p)!=checksum)
           for p,checksum in fingerprints.items()):
        raise ValueError("K06 wrote outside its seven existing preview maps.")
    isolate(output,meta,profile=SAVE_APP,fixture=PROOF)
    (output/"Data/blue-compile-request.txt").write_text("compile",encoding="ascii")
    (output/"Data/PluginScripts.rxdata").unlink(missing_ok=True)
    result={"append_new_maps":0,"modified_preview_source_ids":list(APPROACH),
            "new_seams_source":EXACT_SEAMS,"native_source_transfers":len(TRANSFERS)-len(TEMP_GATES),
            "temporary_saffron_gate_blocks":sorted(TEMP_GATES),
            "removed_preview_only_seams":removed,"other_maps_byte_identical":len(fingerprints)-len(changed),
            "rocket_hideout_activated":False,"native_gameplay":False,"published":False}
    (ROOT/"k06-source-receipts/kanto-k06-approach-stage.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("KANTO_K06_APPROACH_STAGE_OK:"+json.dumps(result),flush=True)


if __name__=="__main__":
    run()
