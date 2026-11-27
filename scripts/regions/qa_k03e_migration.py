"""K03-E: real transactional 156->160 migration in disposable Windows CI.
Use the installed 156-map main registry; never touch a user's game or saves.
"""
from __future__ import annotations
import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch
from audit import ROOT, KANTO, inventory, json_file, load
import install_kanto as installer
from k03e_contract import MAPS, candidate_manifest, migration_game, migration_pilot

REPORT = ROOT/".blue-work/kanto-k03e-migration-proof.json"
def require(condition,message):
    if not condition:
        raise ValueError(message)

def snapshot(game, paths):
    return {str(p): installer.digest(game/p) if (game/p).is_file() else None for p in paths}

def run():
    if os.getenv("GITHUB_ACTIONS")!="true" or os.name!="nt":
        raise ValueError("K03-E migration is restricted to Windows CI")
    original = ROOT/"game"
    require(installer.verify_installed(original)["maps"]==156,"K03-E baseline is not installed")
    game,pilot = migration_game(ROOT),migration_pilot(ROOT)
    require(not game.parent.exists(),"K03-E migration workspace exists")
    shutil.copytree(original,game)
    proof_path = Path("Data/blue-kanto-install.json")
    old = json_file(game/proof_path)["maps"]
    _, files = inventory(game)
    foreign = [p.relative_to(game) for mid,p in files.items() if mid not in old.values()]
    protected = [Path(p) for p in ("Data/System.rxdata","Game.exe","Game.ini","mkxp.json")] + foreign
    before_original = snapshot(original,protected)
    sentinel = Path("saves/K03E-CI-SENTINEL.rxdata")
    (game/sentinel).parent.mkdir(exist_ok=True)
    (game/sentinel).write_bytes(b"K03-E synthetic save preservation sentinel")
    protected.append(sentinel)
    before_protected = snapshot(game,protected)
    legacy = installer.legacy_proof(game,candidate=True)
    require(legacy["maps"]==old and len(old)==156,"K03-E ownership mismatch")
    installer.build(installer.SOURCE,game,pilot,existing={int(k):v for k,v in old.items()},
                    manifest=candidate_manifest(json_file(KANTO)))
    files,mapping,_=installer.manifest(pilot,game,migration=legacy,candidate=True)
    require(len(mapping)==160 and all(mapping[int(k)]==v for k,v in old.items()),"K03-E changed MapIDs")
    require(set(mapping)-set(map(int,old))==set(MAPS),"K03-E new source set differs")
    require(not set(mapping.values()).intersection(int(p.stem[3:]) for p in foreign),"K03-E foreign map collision")
    # Map bytes can differ because new tilesets are appended. Compare native
    # original geometry and every previous event, allowing only the new door.
    for sid,mid in old.items():
        path=Path(f"Data/Map{mid:03d}.rxdata")
        old_map=load(game/path).attrs
        new_map=load(pilot/path).attrs
        require(all(old_map[k]==new_map[k] for k in ("@width","@height","@data")),f"K03-E changed baseline geometry {sid}")
        old_events,new_events=old_map["@events"],new_map["@events"]
        if sid=="18":
            require(set(new_events)-set(old_events)=={1} and all(new_events[k]==v for k,v in old_events.items()),"K03-E Route2 changed unrelated events")
        else:
            require(old_events==new_events,f"K03-E changed baseline events {sid}")
    touched=list(files)+[proof_path,installer.READY_GATE,installer.MARKER,Path("Data/blue-compile-request.txt"),Path("Data/PluginScripts.rxdata")]
    before=snapshot(game,touched+protected)
    # Actual writes and rollback, failure injected only at final verification.
    with patch.object(installer,"verify_installed",side_effect=ValueError("K03-E injected final verification failure")):
        try:
            installer.apply_install(game,pilot,True,migration=legacy,candidate=True)
        except ValueError as error:
            require(str(error)=="K03-E injected final verification failure",str(error))
        else:
            raise ValueError("K03-E rollback injection did not abort")
    require(snapshot(game,touched+protected)==before,"K03-E rollback hashes differ")
    result=installer.apply_install(game,pilot,True,migration=legacy,candidate=True)
    require(result["status"]=="migrated" and installer.verify_installed(game,candidate=True)["maps"]==160,"K03-E final verification failed")
    require(snapshot(game,protected)==before_protected and snapshot(original,protected[:-1])==before_original,"K03-E changed protected files")
    final=snapshot(game,touched+protected)
    try:
        installer.apply_install(game,pilot,True)
    except ValueError as error:
        require("Kanto ja instalado" in str(error),str(error))
    else:
        raise ValueError("K03-E duplicate installation accepted")
    require(snapshot(game,touched+protected)==final,"K03-E duplicate install changed files")
    require(not (game/"Kanto pilot.json").exists() and not (game/"Data/blue-kanto-experimental-stops.txt").exists(),"K03-E leaked pilot markers")
    report={"status":"PASS","old_maps":156,"new_maps":160,"preserved_map_ids":156,
            "baseline_geometry_preserved":156,"baseline_events_preserved_except_route2_door":True,
            "new_mapping":{str(sid):mapping[sid] for sid in MAPS},"foreign_maps_preserved":len(foreign),
            "rollback_hashes_equal":True,"synthetic_save_preserved":True,"native_system_config_preserved":True,
            "duplicate_install_rejected":True,"original_game_preserved":True,"manual_gameplay":False,
            "revision":os.getenv("GITHUB_SHA")}
    REPORT.write_text(json.dumps(report,indent=2),encoding="utf8")
    print("KANTO_K03E_REAL_MIGRATION_REPORT:"+json.dumps(report),flush=True)
    print("KANTO_K03E_REAL_156_TO_160_MIGRATION_FIXTURE_OK",flush=True)

if __name__=="__main__":
    try:
        run()
    except Exception as error:
        REPORT.write_text(json.dumps({"status":"FAIL","error":str(error)},indent=2),encoding="utf8")
        raise
