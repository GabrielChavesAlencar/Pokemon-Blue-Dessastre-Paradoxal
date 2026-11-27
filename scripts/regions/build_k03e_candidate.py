"""Build and verify K03-E using the real pilot compiler, CI only."""
import json
import os
from audit import ROOT, KANTO, inventory, json_file, load
from k03e_contract import MAPS, TRAINERS, WARPS, ITEMS, candidate_manifest
from pilot import build, SOURCE
from server.ruby_marshal import text

def run():
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise ValueError("K03-E is a disposable CI build only")
    baseline = ROOT/".blue-work/kanto-pilot"
    target = ROOT/".blue-work/kanto-k03e-functional"
    prior = {int(k):v for k,v in json_file(baseline/"Kanto pilot.json")["maps"].items()}
    build(SOURCE, ROOT/"game", target, manifest=candidate_manifest(json_file(KANTO)))
    active = {int(k):v for k,v in json_file(target/"Kanto pilot.json")["maps"].items()}
    if len(active)!=160 or any(active.get(k)!=v for k,v in prior.items()):
        raise ValueError("K03-E changed published allocation")
    _, files = inventory(target)
    def event(sid,eid):
        return load(files[active[sid]]).attrs["@events"][eid]
    for (sid,eid),(dest,x,y,direction) in WARPS.items():
        e = event(sid,eid)
        page = e.attrs["@pages"][0].attrs
        ops = [c.attrs for c in page["@list"]]
        if page["@trigger"] != 1 or not any(c["@code"]==201 and c["@parameters"][:5]==[0,active[dest],x,y,direction] for c in ops):
            raise ValueError(f"K03-E missing real compiled transfer {sid}/{eid}")
    for eid,(kind,name) in TRAINERS.items():
        pages = event(79,eid).attrs["@pages"]
        first, second = (p.attrs for p in pages)
        expected = f'BlueKantoPilot.battle(:BLUE_KANTO_{kind}, "{name}", "KANTO_079_{eid:03d}")'
        if first["@trigger"]!=2 or second["@trigger"]!=0 or not second["@condition"].attrs["@self_switch_valid"] or not any(c.attrs["@code"]==355 and text(c.attrs["@parameters"][0])==expected for c in first["@list"]):
            raise ValueError(f"K03-E invalid trainer event {eid}")
    for eid,item in ITEMS.items():
        e = event(79,eid)
        if not any(c.attrs["@code"]==355 and f"pickup(:{item}," in text(c.attrs["@parameters"][0]) for c in e.attrs["@pages"][0].attrs["@list"]):
            raise ValueError(f"K03-E source item not adapted {eid}/{item}")
    # Preserve original corridor connection and exact draft encounter profiles.
    rows = (target/"PBS/map_connections_kanto.txt").read_text("utf-8").splitlines()
    if f"{active[64]},East,0,{active[79]},West,0" not in rows:
        raise ValueError("K03-E Vermilion east seam absent")
    music = (target/"Data/blue-kanto-music.txt").read_text("utf-8").splitlines()
    if not all(any(row.startswith(f"MAP\t{active[sid]}\t") for row in music) for sid in MAPS):
        raise ValueError("K03-E missing scoped BGM")
    report = {"status":"FUNCTIONAL_CANDIDATE_NOT_PUBLISHED","mapping":{str(i):active[i] for i in MAPS},
              "baseline_ids_preserved":156,"maps":160,"transfers":len(WARPS),
              "trainers":len(TRAINERS),"items":len(ITEMS),"music_maps":4,
              "gatehouse_80":"not installed; no synthetic transfer","manual_gameplay":False}
    (ROOT/".blue-work/kanto-k03e-compiled.json").write_text(json.dumps(report,indent=2),encoding="utf8")
    print("KANTO_K03E_COMPILED_CANDIDATE_REPORT:"+json.dumps(report),flush=True)
    print("KANTO_K03E_COMPILED_160_MAP_CANDIDATE_OK",flush=True)

if __name__ == "__main__":
    run()
