"""Probe the ordinary K05 installer with one isolated, exact historical seed."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from audit import ROOT, inventory, json_file
import install_kanto as installer
from k05_contract import published_destinations
from k05_migration import predecessor_edits
from qa_k04_migration import copy_for_ci, isolated_config, require, save_namespace_valid, track

WORK=ROOT/".blue-work"
PROOF=Path("Data/blue-kanto-install.json")
SAVE=Path("saves/K05-SYNTHETIC-SENTINEL.rxdata")
CONTROL={PROOF,installer.READY_GATE,installer.MARKER,Path("Data/PluginScripts.rxdata"),
         Path("Data/blue-compile-request.txt")}
LATE_WRITE=Path("Data/Map621.rxdata")
READY_COUNT=178
HISTORICAL={
    156:"3f53555ed82b3ffaad86422fae572130b0fca2a2",
    160:"4c21940ae4936adb1919c0052007e3f2812b077d",
}


def locations(size):
    game=WORK/"kanto-k05-migration-ci"/f"from-{size}"
    seed=WORK/"kanto-k05-migration-seeds"/str(size)
    pilot=WORK/"kanto-k05-migration-ci"/f"rebuild-{size}"
    return seed,game,pilot


def require_candidate_game(game):
    target=game.resolve()
    if os.getenv("GITHUB_ACTIONS")!="true" or os.name!="nt":
        raise ValueError("K05 install candidate is Windows Actions only")
    for size in (156,160,165):
        if target==locations(size)[1].resolve():
            return size
    raise ValueError("K05 candidate game path is not a guarded workspace")


def require_candidate_pilot(pilot):
    if os.getenv("GITHUB_ACTIONS")!="true" or os.name!="nt" or pilot.resolve() not in {
        locations(size)[2].resolve() for size in (156,160,165)}:
        raise ValueError("K05 candidate pilot path is not a guarded workspace")


def seed_165():
    # K04 is the still-active exact 165-map recipe. Reuse the signed preboot
    # artifact built earlier against the same game/, not a raw donor archive.
    if os.getenv("GITHUB_ACTIONS")!="true" or os.name!="nt":
        raise ValueError("K05 historical seed requires Windows Actions")
    seed,_,_=locations(165)
    seed.parent.mkdir(parents=True,exist_ok=True)
    copy_for_ci(ROOT/"game",seed)
    result=installer.apply_install(seed,WORK/"kanto-k05-baseline",True)
    require(result["maps"]==165 and installer.verify_installed(seed)["maps"]==165,
            "Could not seed a source-valid 165-map K04 installation")


def seed_historical(size):
    """Build and install with the immutable historical recipes, not mocked PAL."""
    if os.getenv("GITHUB_ACTIONS")!="true" or os.name!="nt" or size not in HISTORICAL:
        raise ValueError("K05 historical setup is Windows Actions only")
    tree=WORK/f"kanto-k05-historical-{size}"
    seed,_,_=locations(size)
    historical_game=tree/"game"
    require(not seed.exists() and not historical_game.exists() and
            tree.resolve().parent==WORK.resolve() and tree.is_dir(),
            "Historical fixture path is not clean")
    observed=subprocess.check_output(
        ["git","rev-parse","HEAD"],cwd=tree,text=True).strip()
    if observed!=HISTORICAL[size] or len(json_file(tree/"data/regions/kanto-source.json")["maps"])!=size:
        raise ValueError("Historical Kanto source recipe is not exactly pinned")
    copy_for_ci(ROOT/"game",historical_game)
    tool=tree/"scripts/regions/install_kanto.py"
    pilot=tree/".blue-work"/"kanto-historical"
    subprocess.run([sys.executable,str(tool),"--game",str(historical_game),"--pilot",str(pilot),
                    "--source",str(installer.SOURCE),"--apply"],cwd=tree,check=True)
    receipt=json_file(historical_game/PROOF)
    require(len(receipt["maps"])==size and
            (historical_game/"Data/blue-kanto-ready.txt").read_bytes()==installer.ready_gate_bytes(
                {int(sid):mid for sid,mid in receipt["maps"].items()}),
            "Historical installer did not produce the exact predecessor")
    seed.parent.mkdir(exist_ok=True)
    historical_game.rename(seed)
    shutil.rmtree(pilot)
    print(f"KANTO_K05_PINNED_PREDECESSOR_{size}_OK:{observed}",flush=True)


def run(size):
    require(os.getenv("GITHUB_ACTIONS")=="true" and os.name=="nt" and size in (156,160,165),
            "K05 migration only runs against known Windows CI workspaces")
    seed,game,pilot=locations(size)
    proof=json_file(seed/PROOF)
    original_maps=proof["maps"]
    require(proof.get("schema")==1 and len(original_maps)==size and not game.exists() and not pilot.exists(),
            "Missing exact staged historical seed")
    copy_for_ci(seed,game)
    (_,files)=inventory(game)
    foreign={p.relative_to(game) for mid,p in files.items() if mid not in original_maps.values()}
    (game/SAVE).parent.mkdir(exist_ok=True)
    (game/SAVE).write_bytes(b"K05 clean test sentinel, never a real save")
    protected=foreign|{SAVE,Path("Game.exe"),Path("Game.ini"),Path("mkxp.json"),Path("Data/System.rxdata")}
    before=track(game,protected)
    original_apply=installer.apply_install
    original_atomic=installer.atomic
    checked={}
    def exercise_copy(target,prepared,commit,*,migration=None,**kwargs):
        require(target==game and prepared==pilot and commit and migration==proof,"Installer chose unexpected migration")
        staged,mapping,_=installer.manifest(prepared,target,migration=migration,candidate="k05")
        mapping={str(sid):mid for sid,mid in mapping.items()}
        edits=predecessor_edits(original_maps,mapping)
        mutated={Path("Data")/f"Map{original_maps[str(sid)]:03}.rxdata" for sid in edits}
        keep={Path("Data")/f"Map{mid:03}.rxdata" for mid in original_maps.values()}-mutated
        hashes=track(game,keep)
        prior=track(game,set(staged)|CONTROL)
        require(LATE_WRITE in staged and prior[LATE_WRITE] is None and len(mapping)==READY_COUNT,
                "K05 rebuild is not an append")
        fired=False
        def fail(path,payload):
            nonlocal fired
            if not fired and path==game/LATE_WRITE:
                fired=True
                raise IOError("synthetic K05 late rollback")
            return original_atomic(path,payload)
        try:
            with patch.object(installer,"atomic",side_effect=fail):
                original_apply(target,prepared,True,migration=migration,**kwargs)
        except IOError as error:
            require(str(error)=="synthetic K05 late rollback","Unexpected installer exception")
        require(fired and track(game,prior)==prior and track(game,protected)==before,
                "K05 rollback left an installed map, proof or unrelated content modified")
        result=original_apply(target,prepared,True,migration=migration,**kwargs)
        require(result["status"]=="migrated" and track(game,hashes)==hashes and track(game,protected)==before,
                "Ordinary K05 installer failed to retain all expected old content")
        require(all(installer.digest(game/p)!=prior[p] for p in mutated),"Expected source-audited event edit missing")
        checked.update({"prior":size,"old_maps_byte_identical":len(keep),"approved_edits":sorted(edits),
                        "other_maps_preserved":len(foreign),"disposable_save_unchanged":True,"rollback":True})
        return result
    with patch.object(installer,"apply_install",side_effect=exercise_copy):
        result=installer.migrate_existing(game,installer.SOURCE,pilot,True,candidate="k05")
    final=json_file(game/PROOF)["maps"]
    require(result["maps"]==READY_COUNT and installer.verify_installed(game,candidate="k05")["maps"]==READY_COUNT and
            all(final.get(k)==v for k,v in {**original_maps,**published_destinations()}.items()),
            "K05 main installed proof did not retain historical identities")
    app=f"Kanto K05 Migrated {size} CI"
    (game/"mkxp.json").write_text(isolated_config((game/"mkxp.json").read_text("utf-8-sig"),app),encoding="utf8")
    require(save_namespace_valid(game,app), "Disposable Game.exe must not see any player profile")
    (game/"Data/blue-k05-ci-isolated.txt").write_text(str(size),encoding="ascii")
    checked["maps"]=READY_COUNT
    out=WORK/f"kanto-k05-migration-{size}.json"
    out.write_text(json.dumps(checked,indent=2)+"\n",encoding="utf8")
    print(f"KANTO_K05_MIGRATION_{size}_TO_178_OK:"+json.dumps(checked),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prior",type=int,choices=[156,160,165])
    parser.add_argument("--seed-165",action="store_true")
    parser.add_argument("--seed-historical",action="store_true")
    a=parser.parse_args()
    if a.seed_165:
        require(a.prior==165,"Wrong seed option")
        seed_165()
    if a.seed_historical:
        seed_historical(a.prior)
    run(a.prior)
