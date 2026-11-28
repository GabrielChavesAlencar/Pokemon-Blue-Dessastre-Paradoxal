"""Prepare the seven-map K06 approach migration on an owned K05 registry."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from audit import ROOT, inventory, json_file, load
from build_k05_city import digest
from build_k06_approach import APPROACH, apply_events, planned_connections, verify_source
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
    for rel,data in changes.items():
        atomic(game/rel,data)
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
    stage_ci()
