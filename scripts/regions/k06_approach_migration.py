"""Prepare the seven-map K06 approach migration on an owned K05 registry."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from audit import ROOT, inventory, json_file, load
from build_k05_city import digest
from build_k06_approach import APPROACH, EXACT_SEAMS, TEMP_GATES, TRANSFERS, apply_events, planned_connections, verify_source
from install_kanto import apply_install, atomic, recorded_hashes, verify_installed
from pilot import EVENT_CLASSES, write_map
from qa_k04_migration import copy_for_ci, isolated_config, save_namespace_valid

CI_PATH = ".blue-work/kanto-k06-integrated"
CI_PROFILE = "Kanto K06 Integrated Migration CI"
INSTALL = "Data/blue-kanto-install.json"
CONNECTIONS = "PBS/map_connections_kanto.txt"
READY = "Data/blue-kanto-k06-approach.json"
SAVE = "saves/K06-SYNTHETIC-SENTINEL.rxdata"
SOURCE = ROOT / ".blue-work/frlg-source/Essentials FRLG"


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def checked_file(root, rel):
    path=root/rel
    if path.resolve()!=path or not path.is_file():
        raise ValueError(f"Missing owned K05 file: {rel}")
    return path


def require_hashes(game, paths, hashes):
    for rel in paths:
        if digest(checked_file(game,rel))!=hashes.get(rel):
            raise ValueError(f"Installed K05 file is not the recorded baseline: {rel}")


def plan(game, source, receipt, trusted_files=None):
    """Prepare only proven chart changes; do not modify the base or its saves."""
    game=game.resolve()
    verify_source(receipt)
    if verify_installed(game)["maps"]!=178 or (game/READY).exists():
        raise ValueError("K06 needs an unmodified installed K05 baseline (178 maps)")
    stamp=json_file(checked_file(game,INSTALL))
    mapping={int(k):v for k,v in stamp["maps"].items()}
    edited={sid:f"Data/Map{mapping[sid]:03}.rxdata" for sid in APPROACH}
    # Windows has the Kanto install receipt; the Android updater supplies
    # its independently authenticated per-file installed inventory.
    hashes=recorded_hashes(stamp) if trusted_files is None else trusted_files
    require_hashes(game,[*edited.values(),CONNECTIONS],hashes)
    _,donors=inventory(source)
    witness={row["source"]:row["sha256"] for row in receipt["maps"]}
    changes={}
    with TemporaryDirectory() as temp:
        for sid,rel in edited.items():
            donor=donors[sid]
            if digest(donor)!=witness.get(sid):
                raise ValueError(f"Original K06 approach source digest mismatch for {sid}")
            native=load(game/rel)
            apply_events(load(donor),native,sid,mapping)
            out=Path(temp)/Path(rel).name
            write_map(out,native,EVENT_CLASSES)
            if load(out)!=native:
                raise ValueError(f"Round-trip failed for K06 approach {sid}")
            changes[rel]=out.read_bytes()
    connections,removed=planned_connections((game/CONNECTIONS).read_text("utf-8-sig"),mapping)
    changes[CONNECTIONS]=connections.encode("utf8")
    before={rel:hashes[rel] for rel in changes}
    after={rel:sha_bytes(data) for rel,data in changes.items()}
    keys={str(k).replace(chr(92),"/"):k for k in stamp["installed_sha256"]}
    if not set(changes)<=keys.keys():
        raise ValueError("Kanto install receipt does not own the exact approach files")
    stamp["installed_sha256"].update({keys[rel]:value for rel,value in after.items()})
    changes[INSTALL]=(json.dumps(stamp,indent=2)+"\n").encode("utf8")
    result={"status":"K06_APPROACH_CANDIDATE","population":178,
            "before":before,"after":after,"source_ids":list(APPROACH),
            "destinations":edited,"removed_preview_only_links":removed,
            "published":False,"requires_native_compilation":True}
    changes[READY]=(json.dumps(result,indent=2)+"\n").encode("utf8")
    return changes,result


def verify_native_graph(game, compiled=False, *, mapping=None):
    """Verify compiled K06 contents, no paths to Saffron or later sublots."""
    game=game.resolve()
    if mapping is None:
        stamp=json_file(checked_file(game,INSTALL))
        mapping={int(k):v for k,v in stamp["maps"].items()}
    if len(mapping)!=178 or mapping.get(93)!=609 or len(set(mapping.values()))!=178:
        raise ValueError("K06 compiled registry no longer preserves the 178 K05 IDs")
    controlled={mapping[i] for i in APPROACH}
    expected=[(mapping[a],side,n,mapping[b],other,z) for a,side,n,b,other,z in EXACT_SEAMS]
    text=checked_file(game,CONNECTIONS).read_text("utf-8-sig")
    _,rows=planned_connections(text,mapping)
    if rows!=[",".join(map(str,row)) for row in expected]:
        raise ValueError("K06 active PBS contains a shortcut or missing seam")
    for sid in APPROACH:
        native=load(checked_file(game,f"Data/Map{mapping[sid]:03}.rxdata")).attrs["@events"]
        owned={e:(at,dst,xy,direction) for (s,e),(at,dst,xy,direction) in TRANSFERS.items() if s==sid}
        if set(native)!=owned.keys():
            raise ValueError(f"K06 unexpected native events on {sid}")
        for eid,(at,dst,xy,direction) in owned.items():
            e=native[eid].attrs
            pages=e["@pages"]
            if (e["@x"],e["@y"])!=at or len(pages)!=1 or pages[0].attrs["@trigger"]!=1:
                raise ValueError(f"K06 native door position or trigger changed: {sid}/{eid}")
            ops=[command.attrs for command in pages[0].attrs["@list"]]
            warps=[x["@parameters"][:5] for x in ops if x["@code"]==201]
            if (sid,eid) in TEMP_GATES:
                if warps or not any(x["@code"]==355 and b"Saffron" in x["@parameters"][0] for x in ops):
                    raise ValueError(f"K06 closed Saffron guard changed: {sid}/{eid}")
            elif warps!=[[0,mapping[dst],*xy,direction]]:
                raise ValueError(f"K06 exact native transfer changed: {sid}/{eid}: {warps}")
    if compiled:
        data=load(checked_file(game,"Data/map_connections.dat"))
        got=[frozenset((r[0],r[3])) for r in data if {r[0],r[3]}&controlled]
        wanted=[frozenset((r[0],r[3])) for r in expected]
        if len(got)!=len(wanted) or set(got)!=set(wanted):
            raise ValueError("K06 compiled connections differ from its two approved seams")
    return {"count":len(mapping),"seams":len(expected),"compiled":compiled}


def verify_k05_android_predecessor(game):
    """Use the device's verified K05 inventory, never the CI's file hashes."""
    from scripts.android.source_update import (
        PRODUCT_REVISION, installed_provenance, protected_map_inventory, RECOVERY_FILE
    )
    from scripts.android.update_client import read_installed
    game=game.resolve()
    if (game/RECOVERY_FILE).exists():
        raise ValueError("Complete the interrupted K05 update before attempting K06.")
    installed=read_installed(game)
    stamp=installed.get("source_update")
    recipe="4bda388e0f6d07763c95cfd9877ce337e61f9cb9"
    if (installed["channel"]!="multiregion" or installed["revision"]!=PRODUCT_REVISION
            or stamp!=installed_provenance(installed["files"],recipe)):
        raise ValueError("K06 requires the verified source-built K05 predecessor.")
    regions,paths=protected_map_inventory(game,installed)
    if len(regions["kanto"])!=178 or len(regions["hoenn"])!=199:
        raise ValueError("K06 predecessor does not have the two complete regional registries.")
    return installed,paths


def stage_ci():
    """Apply the plan only to a fresh throwaway Windows CI installation."""
    if os.getenv("GITHUB_ACTIONS")!="true" or os.name!="nt":
        raise ValueError("K06 integrated approach staging is disposable Windows CI only")
    game=(ROOT/CI_PATH).resolve()
    source=SOURCE
    report=ROOT/"k06-source-receipts"
    receipt=json_file(report/"kanto-k06-source.json")
    baseline=ROOT/".blue-work/kanto-k06-baseline"
    copy_for_ci(ROOT/"game",game)
    apply_install(game,baseline,commit=True)
    before=json_file(game/INSTALL)
    guard=game/SAVE
    guard.parent.mkdir(exist_ok=True)
    guard.write_bytes(b"test save marker; not actual game data")
    _,files=inventory(game)
    state={p.relative_to(game).as_posix():digest(p) for p in files.values()}
    for rel in (SAVE,"Data/MapInfos.rxdata","Data/Tilesets.rxdata","Game.ini","mkxp.json"):
        state[rel]=digest(checked_file(game,rel))
    changes,result=plan(game,source,receipt)
    exact=set(result["destinations"].values())|{INSTALL,READY,CONNECTIONS}
    if set(changes)!=exact:
        raise ValueError("Unexpected K06 migration scope")
    from k06_windows_approach import install as apply_windows_overlay
    if not apply_windows_overlay(game,ci=True) or apply_windows_overlay(game,ci=True):
        raise ValueError("K06 Windows update failed first apply or was not idempotent")
    for name,data in changes.items():
        if name not in {INSTALL,READY} and (game/name).read_bytes()!=data:
            raise ValueError(f"Windows launcher wrote different approach data: {name}")
    verify_native_graph(game)
    if (before["maps"]!=json_file(game/INSTALL)["maps"] or verify_installed(game)["maps"]!=178
            or any(digest(game/rel)!=value for rel,value in state.items() if rel not in exact)):
        raise ValueError("A K06 migration changed unrelated maps, runtime configuration or save")
    cfg=game/"mkxp.json"
    cfg.write_text(isolated_config(cfg.read_text("utf-8-sig"),CI_PROFILE),encoding="utf8")
    if not save_namespace_valid(game,CI_PROFILE):
        raise ValueError("Cannot isolate K06 approach CI")
    result.update(unrelated_map_count=len(files)-len(APPROACH),save_sentinel_sha256=state[SAVE])
    (report/"kanto-k06-integrated-plan.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    print("KANTO_K06_INTEGRATED_APPROACH_READY:"+json.dumps(result),flush=True)


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-compiled-ci",action="store_true")
    args=parser.parse_args()
    if args.verify_compiled_ci:
        if os.getenv("GITHUB_ACTIONS")!="true" or os.name!="nt":
            raise ValueError("K06 integrated native verification is CI only")
        proof=verify_native_graph(ROOT/CI_PATH,compiled=True)
        print("KANTO_K06_INTEGRATED_COMPILED_GRAPH_OK:"+json.dumps(proof))
    else:
        stage_ci()
