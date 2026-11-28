"""K05 Channeler adapters driven by the pinned source and no donor Ruby."""
from __future__ import annotations

import copy
import re
import shutil

from audit import ROOT, text
from k04_gameplay import append, sprite
from pbs import catalogue, normalize_encounters, read_blocks, trainer_draft
from pilot import command, new_event

CHANNELERS = {
    102: {1: ("Hope",(10,4)), 3: ("Carly",(7,9)), 4: ("Patricia",(8,14))},
    103: {1: ("Laurel",(15,7)), 2: ("Jody",(13,13)), 6: ("Paula",(2,12))},
    104: {1: ("Ruth",(9,4)), 2: ("Tammy",(17,7)), 3: ("Karina",(5,12)), 5: ("Jody",(9,16))},
    105: {1: ("Angelica",(11,10)), 2: ("Jennifer",(16,6)), 4: ("Emilia",(7,6))},
}
TYPE = "BLUE_KANTO_CHANNELER"
RIVAL_TYPE = "BLUE_KANTO_RIVAL_TOWER"
RIVAL = {3:(15,5),6:(14,6)}
RIVAL_TEAMS = {51:"CHARMELEON",52:"WARTORTLE",53:"IVYSAUR"}
SIGHT = re.compile(r"(?:trainer|sight)\([1-9]\d*\)", re.I)


def profiles(report):
    expected = {(sid,eid):(name,xy) for sid,events in CHANNELERS.items()
                for eid,(name,xy) in events.items()}
    seen = set()
    profiles = {}
    for row in report["actors"]:
        at = row["source"],row["event"]
        observed = row["trainer_profiles"]
        if at not in expected or not observed:
            continue
        name,xy = expected[at]
        key = "CHANNELER," + name
        if (at in seen or row["page"] != 1 or tuple(row["at"]) != xy or row["trigger"] != 2
                or not row["graphic"] or any(k.endswith("_valid") for k in row["requires"])
                or list(observed) != [key]
                or [p["header"] for p in observed[key]] != [key]
                or not observed[key][0]["team"]):
            raise ValueError(f"K05 original Channeler changed {at}")
        seen.add(at)
        profiles[key] = ("CHANNELER",name,0)
    if seen != expected.keys() or len(profiles)!=12:
        raise ValueError("K05 Channeler receipt does not cover all 13 actors and 12 independent rosters")
    approaches={r["event"]:r for r in report["actors"]
                if r["source"]==101 and r["event"] in RIVAL and r["battle_calls"]}
    if approaches.keys()!=RIVAL.keys():
        raise ValueError("K05 original rival approach missing")
    for eid, r in approaches.items():
        roles = [(c["type"],c["name"],c["literal_first_extra_argument"]) for c in r["battle_calls"]]
        teams = {int(p["header"].split(",")[-1]):p["team"]
                 for p in r["trainer_profiles"].get("RIVAL2,Blue",[])}
        if (r["page"]!=1 or r["trigger"]!=2 or r["graphic"] or tuple(r["at"])!=RIVAL[eid]
                or roles!=[("RIVAL2","Blue",v) for v in RIVAL_TEAMS]
                or any(not teams.get(v) or teams[v][-1][0]!=mon for v,mon in RIVAL_TEAMS.items())):
            raise ValueError(f"K05 original rival variants changed at {eid}")
    for version in RIVAL_TEAMS:
        profiles[f"RIVAL2,Blue,{version}"]=("RIVAL_TOWER","Blue",version)
    return profiles


def install_trainer_pbs(source,target,specs):
    def headers(path): return read_blocks(path,{f"BLUE_KANTO_{kind},{name},{version}"
                                               for kind,name,version in specs.values()})
    path = target / "PBS/trainers_kanto.txt"
    types = target / "PBS/trainer_types_kanto.txt"
    silph = "BLUE_KANTO_RIVAL_SILPH"
    source_types=read_blocks(types,{TYPE,silph,RIVAL_TYPE})
    if headers(path) or source_types.keys()!={TYPE,silph}:
        raise ValueError("K05 trainer types absent or conflict with existing profiles")
    append(types,"\n".join([f"[{RIVAL_TYPE}]",*source_types[silph]]))
    sprites = target/"Graphics/Trainers"
    if (sprites/f"{RIVAL_TYPE}.png").exists():
        raise ValueError("K05 rival portrait conflicts with an existing asset")
    shutil.copyfile(sprites/f"{silph}.png",sprites/f"{RIVAL_TYPE}.png")
    st,ms,it = (catalogue(target,key) for key in ("pokemon","moves","items"))
    append(path,trainer_draft(source / "PBS/trainers.txt",st,ms,it,specs))
    if len(headers(path))!=len(specs):
        raise ValueError("K05 roster append did not retain all original names")


def battle_key(sid,eid):
    return f"KANTO_TOWER_{sid:03d}_{eid:03d}"


def install_events(source,target,donor,native,sid):
    originals, events = donor.attrs["@events"],native.attrs["@events"]
    if sid==101:
        for eid,xy in RIVAL.items():
            ev=originals[eid]
            if eid in events or tuple(ev.attrs[k] for k in ("@x","@y"))!=xy:
                raise ValueError("K05 original rival approach moved")
            converted=new_event(ev,[command(355,b"BlueKantoTower.rival")],1,b"")
            done=copy.deepcopy(converted.attrs["@pages"][0])
            done.attrs["@condition"].attrs.update({"@self_switch_valid":True,"@self_switch_ch":b"A"})
            done.attrs.update({"@through":True,"@list":[command(0)]})
            converted.attrs["@pages"].append(done)
            events[eid]=converted
    for eid,(name,xy) in CHANNELERS.get(sid,{}).items():
        event = originals[eid]
        first = event.attrs["@pages"][0].attrs
        if (eid in events or tuple(event.attrs[k] for k in ("@x","@y"))!=xy
                or first["@trigger"]!=2 or not SIGHT.search(text(event.attrs["@name"]))
                or any(v for k,v in first["@condition"].attrs.items() if k.endswith("_valid"))):
            raise ValueError(f"K05 native actor anchor changed {sid}/{eid}")
        lines = [f"pbTrainerIntro(:{TYPE})", "pbNoticePlayer(get_self)",
                 f'BlueKantoTower.channeler({sid}, {eid}, "{name}")', "pbTrainerEnd"]
        converted = new_event(event,[command(355,line.encode("ascii")) for line in lines],
                              2,sprite(source,target,event))
        after = copy.deepcopy(converted.attrs["@pages"][0])
        after.attrs["@condition"].attrs.update({"@self_switch_valid":True,"@self_switch_ch":b"A"})
        after.attrs.update({"@trigger":0,"@through":False,"@direction_fix":False,
            "@list":[command(355,f'BlueKantoPilot.trainer_repeat("{name}", :{TYPE})'.encode("ascii")),command(0)]})
        converted.attrs["@pages"].append(after)
        events[eid] = converted


def install_runtime(target):
    path = target / "Plugins/ZZZZZ Blue Kanto Pilot/KantoPilot.rb"
    field = (ROOT / "scripts/regions/KantoK05Tower.rb").read_bytes()
    path.write_bytes(path.read_bytes() + b"\n" + field.strip() + b"\n")

def install_encounter_pbs(source,target,slots,receipt):
    base=source / "PBS/encounters.txt"
    wanted={sid:slots[sid] for sid in range(102,107)}
    methods={"CaveDay","CaveNight"}
    proven={row["id"]:row["encounter_slots"] for row in receipt["maps"] if row["id"] in wanted}
    if set(proven)!=wanted.keys() or any(len(blocks)!=1 or
           any(k not in {str(sid),f"{sid:03}",f"{sid},0",f"{sid:03},0"} for k in blocks)
           for sid,blocks in proven.items()):
        raise ValueError("K05 must have five original base-version encounter blocks")
    if any(set(block)!=methods or any(not v["slots"] or v["step_chance"]<=0 for v in block.values())
           for blocks in proven.values() for block in blocks.values()):
        raise ValueError("K05 day/night wild encounter witness is missing")
    known={str(mid) for mid in wanted.values()}
    pbs=target / "PBS/encounters_kanto.txt"
    if read_blocks(pbs,known | {f"{mid},0" for mid in known}):
        raise ValueError("K05 tower encounter IDs already exist")
    species=catalogue(target,"pokemon")
    data,count=normalize_encounters(base,wanted,species)
    if count!=5 or set(re.findall(r"(?m)^\[(\d+)(?:,0)?\]",data))!=known:
        raise ValueError("K05 normalized encounters do not match all source floors")
    append(pbs,data)
