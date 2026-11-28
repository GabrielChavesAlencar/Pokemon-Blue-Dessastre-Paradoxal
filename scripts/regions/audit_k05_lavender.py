"""Audit Lavender first-visit source; do not install any maps or donor scripts."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from audit import KANTO, ROOT, allocate_kanto_ids, inventory, json_file, stable_source_order
from audit_cerulean_interiors import inspect_events, transfers
from audit_k04_rock_tunnel import read_blocks
from k04_corridor import LAVENDER_BOUNDARY, publication_catalog, published_destinations

CITY = tuple(range(93, 99))
TOWER = tuple(range(100, 107))
K05 = CITY + TOWER
UNACTIVATED = {83, 84, 85, 92, 99, 129, 131, 132, 133, 134, 135}
CALL = re.compile(r'\b([A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*[!?]?)?)\s*\(')
TRAINER = re.compile(r'(?:TrainerBattle\.start|pbTrainerBattle)\(\s*:(\w+)\s*,\s*"([^"\r\n]+)"')
SCRIPT_OPS = {111, 355, 655}
WITNESS = re.compile(r'(?i)\b(SILPHSCOPE|POKEFLUTE|MAROWAK|GHOST|MRFUJI|BLUE|RIVAL1|TEAMROCKET_[MF])\b')


def propose_slots(catalog, occupied):
    active = {int(k) for k in catalog["maps"]}
    if publication_catalog(catalog["maps"]) != 165 or active & {*K05, *UNACTIVATED}:
        raise ValueError("K05 requires the exact pre-Lavender K04 catalog")
    if set(catalog.get("preview_only", ())) & set(K05):
        raise ValueError("K05 may not repurpose a protected preview")
    proposed = active | set(K05)
    if stable_source_order(proposed) != [*stable_source_order(active), *K05]:
        raise ValueError("Lavender would relocate released source roles")
    base = allocate_kanto_ids(active, occupied)
    full = allocate_kanto_ids(proposed, occupied)
    if any(full[sid] != mid for sid,mid in base.items()):
        raise ValueError("Lavender would relocate a released MapID")
    if any(base[int(s)] != mid for s,mid in published_destinations().items()):
        raise ValueError("K04 MapIDs changed before K05")
    return {sid: full[sid] for sid in K05}


def scoped_links(path, existing):
    links = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        row = line.partition("#")[0].strip()
        if not row:
            continue
        cols = [s.strip() for s in row.split(",")]
        a, b = int(cols[0]), int(cols[3])
        if a in K05 or b in K05:
            links.append({"source_row": [a, cols[1], int(cols[2]), b, cols[4], int(cols[5])],
                          "both_ends_in_first_visit": {a,b} <= set(existing) | set(K05)})
    observed = {tuple(r["source_row"]) for r in links}
    if LAVENDER_BOUNDARY not in observed:
        raise ValueError("Source no longer proves Lavender north ↔ Route 10 south at zero offset")
    return links


def page_scripts(page):
    for op in page["commands"]:
        if op["code"] in SCRIPT_OPS:
            for value in op["parameters"]:
                if isinstance(value, str):
                    yield op["code"], op["indent"], value


def role(name):
    lower = name.lower()
    if re.search(r'(?:pbhealall|pbpokecenter|pbsetpokemoncenter|heal_party)', lower):
        return "center"
    if re.search(r'(?:pbpokemonmart)', lower):
        return "mart"
    if re.search(r'(?:name.?rater|rename|enterpokemonname)', lower):
        return "nickname"
    if re.search(r'(?:trainerbattle\.start|pbtrainerbattle|pbnotic[e]?player)', lower):
        return "trainer"
    if re.search(r'(?:wildbattle|pbwildbattle)', lower):
        return "wild_battle"
    if re.search(r'(?:pbitemball|pbreceiveitem|pbadditem|add_item)', lower):
        return "item_write"
    if re.search(r'(?:quantity|has\?|pbhaveitem|\.has\()', lower):
        return "bag_guard"
    return None


def block_meta(blocks, sid):
    return [{ "section": key, "keys": re.findall(r"(?m)^([A-Za-z_]\w*)\s*=", raw) }
            for key, parts in blocks.items() if key.split(",")[0].isdecimal() and int(key.split(",")[0]) == sid
            for raw in parts]


def encounter_methods(blocks, sid):
    return sorted({method for row in block_meta(blocks, sid)
                   for raw in blocks[row["section"]]
                   for method in re.findall(r"(?m)^([A-Za-z][A-Za-z0-9]+)(?:,\d+)?\s*$", raw)})


def assemble(source, inspected, catalog, slots):
    active = {int(k) for k in catalog["maps"]}
    if set(inspected) != set(map(str,K05)) or set(slots) != set(K05):
        raise ValueError("K05 source scope must include six service maps and seven tower floors")
    links = scoped_links(source / "PBS/map_connections.txt", active)
    metadata = read_blocks(source / "PBS/map_metadata.txt")
    encounters = read_blocks(source / "PBS/encounters.txt")
    trainers = read_blocks(source / "PBS/trainers.txt")
    rows, edges, actors = [], [], []
    for sid in K05:
        area = inspected[str(sid)]
        rows.append({"id":sid, "name":area["name"],"dimensions":area["dimensions"],
                     "sha256":area["source_sha256"],"slot_unreserved":slots[sid],
                     "event_count":len(area["events"]),"metadata":block_meta(metadata,sid),
                     "encounter_methods":encounter_methods(encounters,sid)})
        for event in area["events"]:
            for warp in transfers(event):
                edges.append({"source":sid,"event":event["id"],"at":event["xy"],**warp,
                    "scope":("city" if warp["destination"] in CITY else "tower" if warp["destination"] in TOWER
                             else "existing" if warp["destination"] in active else "defer")})
            for page in event["pages"]:
                scripts = list(page_scripts(page))
                flags = sorted({f for _,_,script in scripts for f in WITNESS.findall(script)})
                roles = sorted({t for _,_,script in scripts for w in CALL.findall(script) if (t:=role(w))})
                identity = sorted({f"{kind},{name}" for _,_,script in scripts
                                   for kind,name in TRAINER.findall(script)})
                graphic = page["graphic"].get("@character_name")
                opcodes = sorted({op["code"] for op in page["commands"] if op["code"]})
                if roles or flags or identity or (graphic and opcodes):
                    profiles = {}
                    for prefix in identity:
                        profiles[prefix] = [{"header":header,"team":re.findall(
                            r"(?m)^Pokemon\s*=\s*([A-Za-z0-9_]+)\s*,\s*(\d+)\s*$",raw)}
                            for header,blocks in trainers.items() if header==prefix or header.startswith(prefix+",")
                            for raw in blocks]
                    actors.append({"source":sid,"event":event["id"],"page":page["page"],"at":event["xy"],
                                   "trigger":page["trigger"],"graphic":bool(graphic),"opcodes":opcodes,
                                   "requires":{k:v for k,v in page["condition"].items()
                                               if (isinstance(v,bool) and v) or
                                                  (isinstance(v,int) and not isinstance(v,bool) and v)},
                                   "roles":roles,"references":flags,"trainer_profiles":profiles})
    definite = {(a["source"],a["destination"]) for a in edges}
    expected_links = [(93,interior) for interior in (*CITY[1:],TOWER[0])]
    expected_links.extend((floor,floor+1) for floor in TOWER[:-1])
    missing_static_links = sorted((a,b) for x,y in expected_links
                                  for a,b in ((x,y),(y,x)) if (a,b) not in definite)
    return {"status":"K05_SOURCE_ONLY_NOT_PLAYABLE","baseline_catalog":165,
            "activation_blocked":True,"manual_gameplay":False,
            "maps":rows,"links":links,"transfers":edges,"actors":actors,
            "expected_doors_not_proven_as_constant_warps":missing_static_links,
            "excluded_source_ids":sorted(UNACTIVATED),
            "later_rewards":["Silph Scope in K06","Marowak, Fuji and Poké Flute in K07"]}


def run():
    source = ROOT / ".blue-work/frlg-source/Essentials FRLG"
    game = ROOT / "game"
    cat = json_file(KANTO)
    infos, files = inventory(game)
    slots = propose_slots(cat, infos.keys() | files.keys())
    observed = {game / "Data" / key for key in ("MapInfos.rxdata","Tilesets.rxdata")}
    before = {p: hashlib.sha256(p.read_bytes()).digest() for p in observed}
    report = assemble(source,inspect_events(source,K05),cat,slots)
    if any(hashlib.sha256(p.read_bytes()).digest()!=h for p,h in before.items()):
        raise ValueError("Source audit unexpectedly changed the game registry")
    target = ROOT / ".blue-work/kanto-k05-source.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    print("KANTO_K05_SOURCE_INVENTORY_OK:"+json.dumps({
        "maps":len(report["maps"]),"links":len(report["links"]),"transfers":len(report["transfers"]),
        "audited_actor_pages":len(report["actors"]),"activation_blocked":True}),flush=True)


if __name__=="__main__":
    run()
