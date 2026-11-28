"""Probe the ordinary K05 installer with one isolated, exact historical seed."""
from __future__ import annotations

import argparse
import json
import os
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


def locations(size):
    game=WORK/"kanto-k05-migration-ci"/f"from-{size}"
    seed=WORK/"kanto-k05-migration-seeds"/str(size)
    pilot=WORK/"kanto-k05-migration-ci"/f"rebuild-{size}"
    return seed,game,pilot


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
        staged,mapping,_=installer.manifest(prepared,target,migration=migration)
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
                original_apply(target,prepared,True,migration=migration)
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
        result=installer.migrate_existing(game,installer.SOURCE,pilot,True)
    final=json_file(game/PROOF)["maps"]
    require(result["maps"]==READY_COUNT and installer.verify_installed(game)["maps"]==READY_COUNT and
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
    run(parser.parse_args().prior)
