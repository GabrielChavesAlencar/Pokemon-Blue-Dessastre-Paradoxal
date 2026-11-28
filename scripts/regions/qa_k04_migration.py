"""Build disposable CI copies and prove K04 exact install and rollback."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path
from unittest.mock import patch

from audit import ROOT, inventory, json_file
import install_kanto as installer
from k04_corridor import published_destinations
from k04_migration import prepare
from pilot import PILOT_META

WORK = ROOT/".blue-work"
GAME = WORK/"kanto-k04-migration-ci/game"
SEED = WORK/"kanto-k04-migration-ci/seed-pilot"
REBUILT = WORK/"kanto-k04-migration-ci/k04-pilot"
RELEASE = WORK/"kanto-release-pilot"
FIXTURE = WORK/"kanto-k04-gameplay"
PROOF = Path("Data/blue-kanto-install.json")
SAVE = Path("saves/K04-SYNTHETIC-SENTINEL.rxdata")


def require(condition, msg):
    if not condition:
        raise ValueError(msg)


def track(game, paths):
    return {p: installer.digest(game/p) if (game/p).is_file() else None for p in paths}


def copy_for_ci(source, target):
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(
        "Game_*.rxdata","Game.rxdata","*.sav","*.rxsave","Save*","Backups"))


def isolate():
    meta = json_file(RELEASE/PILOT_META)
    require(len(meta["maps"]) == 165 and meta["save_app"] == "Kanto Piloto", "Unexpected release fixture")
    copy_for_ci(RELEASE,FIXTURE)
    name = "Kanto K04 Gameplay CI"
    for config in ("Game.ini", "mkxp.json"):
        p = FIXTURE/config
        old = p.read_text(encoding="utf-8-sig")
        require(old.count(meta["save_app"]) == 1, f"Cannot isolate {config}")
        p.write_text(old.replace(meta["save_app"],name),encoding="utf-8")
    meta.update(save_app=name,k04_fixture_only=True)
    (FIXTURE/PILOT_META).write_text(json.dumps(meta),encoding="utf-8")


def seed():
    copy_for_ci(ROOT/"game",GAME)
    (GAME/"Data/blue-k04-ci-isolated.txt").write_text("K04_CI_ONLY",encoding="ascii")
    installer.build(installer.SOURCE,GAME,SEED)
    result = installer.apply_install(GAME,SEED,True)
    require(result["maps"]==160 and installer.verify_installed(GAME)["maps"]==160, "Baseline has wrong scope")
    shutil.rmtree(SEED)


def migrate():
    require((GAME/"Data/blue-k04-ci-isolated.txt").read_text("ascii")=="K04_CI_ONLY", "Not a disposable game")
    legacy = installer.legacy_proof(GAME)
    old = legacy["maps"]
    require(len(old)==160,"Predecessor is not the published K03-E count")
    _, files = inventory(GAME)
    foreign = {p.relative_to(GAME) for mid,p in files.items() if mid not in old.values()}
    (GAME/SAVE).parent.mkdir()
    (GAME/SAVE).write_bytes(b"K04 synthetic save preservation sentinel")
    protected = foreign | {SAVE, Path("Data/System.rxdata"), Path("Game.exe"),
                           Path("Game.ini"), Path("mkxp.json")}
    before = track(GAME,protected)
    installer.build(installer.SOURCE,GAME,REBUILT,existing={int(k):v for k,v in old.items()})
    kept, aide = prepare(GAME,REBUILT,legacy)
    staged, mapping, _ = installer.manifest(REBUILT,GAME,migration=legacy)
    require(len(kept)==159 and len(mapping)==165,"Wrong additive scope")
    require(all(mapping[int(k)]==mid for k,mid in {**old,**published_destinations()}.items()),"MapIDs moved")
    original = track(GAME,set(staged)|{PROOF,installer.READY_GATE,installer.MARKER,
                    Path("Data/PluginScripts.rxdata"),Path("Data/blue-compile-request.txt")})
    real_atomic = installer.atomic
    fired = False
    def failing_atomic(path, raw):
        nonlocal fired
        if not fired and path==GAME/"Data/Map608.rxdata":
            fired = True
            raise IOError("synthetic K04 rollback failure")
        return real_atomic(path,raw)
    try:
        with patch.object(installer,"atomic",side_effect=failing_atomic):
            installer.apply_install(GAME,REBUILT,True,migration=legacy)
    except IOError as exc:
        require(str(exc)=="synthetic K04 rollback failure","Unexpected transaction error")
    require(fired and track(GAME,original)==original and track(GAME,protected)==before,
            "K04 rollback left changes in the installed game")
    result = installer.apply_install(GAME,REBUILT,True,migration=legacy)
    require(result["status"]=="migrated" and installer.verify_installed(GAME)["maps"]==165,"K04 install verification failed")
    require(track(GAME,kept)==kept and track(GAME,protected)==before,"Existing maps or save changed")
    require(installer.digest(GAME/aide)!=original[aide],"Flash aide missing from predecessor")
    report = {"maps":165,"before":160,"old_maps_byte_identical":len(kept),"aide_only":aide.as_posix(),
              "outside_kanto_preserved":len(foreign),"synthetic_save_unchanged":True,"rollback":True}
    (WORK/"kanto-k04-migration-proof.json").write_text(json.dumps(report,indent=2),encoding="utf8")
    shutil.rmtree(REBUILT)
    # Only the dedicated Main test copy, never the product archive.
    config = GAME/"mkxp.json"
    original = config.read_text(encoding="utf-8-sig")
    require(not re.search(r'"dataPath(?:App|Org)"', original), "Existing save identity is unexpected")
    names = json.dumps({"dataPathApp":"Kanto K04 Migrated CI","dataPathOrg":"Dessastre Paradoxal Kanto Testes"})[1:-1]
    config.write_text(original.replace("{","{\n  "+names+",",1),encoding="utf-8")
    print("KANTO_K04_REAL_160_TO_165_MIGRATION_OK:"+json.dumps(report),flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--isolate-pilot",action="store_true")
    mode.add_argument("--seed-baseline",action="store_true")
    mode.add_argument("--migrate",action="store_true")
    args=parser.parse_args()
    require(os.getenv("GITHUB_ACTIONS")=="true" and os.name=="nt","Disposable Windows CI required")
    (isolate if args.isolate_pilot else seed if args.seed_baseline else migrate)()
