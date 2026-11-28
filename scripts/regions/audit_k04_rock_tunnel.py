"""Read-only K04 source inventory; do not import raw events or activate maps."""
from __future__ import annotations

import json
import re
from pathlib import Path

from audit import KANTO, ROOT, allocate_kanto_ids, inventory, json_file, load, stable_source_order, text
from audit_cerulean_interiors import inspect_events, transfers
from kanto_overworld import source_obstacle

K04 = (86, 87, 88, 90, 91)
FORBIDDEN = {89, 92}  # hierarchy and Power Plant, a later delivery
TRAINER = re.compile(r'TrainerBattle\.start\(\s*:(\w+)\s*,\s*"([^"]+)"')


def candidate_mapping(published, occupied):
    active = set(map(int, published["maps"]))
    if len(active) != 160 or not {23, 79, 81, 82} <= active or active.intersection(K04):
        raise ValueError("K04 requires the released K03-E source catalog")
    if set(published["preview_only"]) & set(K04):
        raise ValueError("K04 must not alter existing previews")
    proposed = active | set(K04)
    before = allocate_kanto_ids(active, occupied)
    after = allocate_kanto_ids(proposed, occupied)
    if stable_source_order(proposed) != [*stable_source_order(active), *K04]:
        raise ValueError("K04 would change published source order")
    if any(after[k] != v for k, v in before.items()):
        raise ValueError("K04 would change a published destination ID")
    return {str(i): after[i] for i in K04}


def source_connections(source: Path):
    connections = []
    for line in (source / "PBS/map_connections.txt").read_text("utf-8-sig").splitlines():
        body = line.partition("#")[0].strip()
        if not body:
            continue
        if body.startswith("["):
            continue
        left, side, offset, right, reverse_side, reverse_offset = map(str.strip, body.split(","))
        if int(left) in K04 or int(right) in K04:
            connections.append([int(left), side, int(offset), int(right), reverse_side, int(reverse_offset)])
    return connections


def read_blocks(source: Path):
    blocks = {}
    file = source.read_text("utf-8-sig")
    for raw in re.split(r"(?m)(?=^\[)", file):
        header = re.match(r"\[([^\]]+)\]", raw)
        if header:
            blocks.setdefault(header[1], []).append(raw.strip())
    return blocks


def summarize(source, maps, mapping):
    internal = set(K04)
    if set(maps) != set(map(str, K04)):
        raise ValueError("K04 source map inventory changed")
    rows, warps, flash, teams = [], [], [], {}
    pbs = read_blocks(source / "PBS/trainers.txt")
    encounters = read_blocks(source / "PBS/encounters.txt")
    metadata = read_blocks(source / "PBS/map_metadata.txt")
    for raw_id, location in maps.items():
        mid = int(raw_id)
        methods = [section for header, sections in encounters.items()
                   if header.split(",")[0].isdecimal() and int(header.split(",")[0]) == mid
                   for section in sections]
        properties = [section for header, sections in metadata.items()
                      if header.isdecimal() and int(header) == mid for section in sections]
        rows.append({"id": mid, "name": location["name"], "destination_candidate": mapping[raw_id],
                     "dimensions": location["dimensions"], "sha256": location["source_sha256"],
                     "event_ids": [e["id"] for e in location["events"]],
                     "encounter_blocks": methods, "metadata": properties})
        for event in location["events"]:
            for warp in transfers(event):
                warps.append({"source": mid, "event": event["id"], "at": event["xy"],
                              **warp, "in_scope": warp["destination"] in internal})
            for page in event["pages"]:
                for command in page["commands"]:
                    for p in command["parameters"]:
                        if not isinstance(p, str):
                            continue
                        for kind, name in TRAINER.findall(p):
                            profiles = {k: v for k, v in pbs.items()
                                        if k in {f"{kind},{name}", f"{kind},{name},0"}
                                        or k.startswith(f"{kind},{name},")}
                            if not profiles:
                                raise ValueError(f"K04 trainer event has no source PBS party: {mid}/{event['id']}")
                            teams[f"{mid}/{event['id']}"] = profiles
                        if re.search(r"\b(?:FLASH|HM05|Darkness|LightRadius|pbFlash)\b", p, re.I):
                            flash.append({"map": mid, "event": event["id"], "page": page["page"],
                                          "opcode": command["code"]})
    links = source_connections(source)
    if not links or not any(w["in_scope"] and w["source"] != w["destination"] for w in warps):
        raise ValueError("K04 has no source-proven connection or internal transfer")
    return {"status": "SOURCE_REVIEW_ONLY", "manual_gameplay": False,
            "released_catalog": 160, "candidate_catalog": 165, "maps": rows,
            "connections": links, "transfers": warps, "flash_event_references": flash,
            "trainers": teams, "external_stub_ids": sorted(FORBIDDEN)}



def flash_acquisition(source):
    """Report anchored HM references without exporting any donor script text."""
    _, paths = inventory(source)
    pattern = re.compile(r"\b(HM05|HMFLASH)\b",re.I)
    hits = []
    for source_id, path in sorted(paths.items()):
        events = load(path).attrs["@events"]
        for eid, event in events.items():
            for number, page in enumerate(event.attrs["@pages"],1):
                for cmd in page.attrs["@list"]:
                    params = cmd.attrs["@parameters"]
                    if cmd.attrs["@code"] not in (111,355,655):
                        continue
                    for param in params:
                        if not isinstance(param,(str,bytes)):
                            continue
                        script = text(param)
                        ids = sorted({p.upper() for p in pattern.findall(script)})
                        if ids:
                            hits.append({"source":source_id,"event":eid,"page":number,
                                         "xy":[event.attrs["@x"],event.attrs["@y"]],
                                         "trigger":page.attrs["@trigger"],"item_ids":ids,
                                         "reward_call": bool(re.search(r"\b(?:pbReceiveItem|pbItemBall)\b",script))})
    return hits


def main():
    source = ROOT / ".blue-work/frlg-source/Essentials FRLG"
    infos, files = inventory(ROOT / "game")
    candidate = candidate_mapping(json_file(KANTO), infos.keys() | files.keys())
    report = summarize(source, inspect_events(source, K04), candidate)
    report["flash_acquisition"] = flash_acquisition(source)
    print("KANTO_K04_FLASH_HM_ANCHORS:" + json.dumps(report["flash_acquisition"]), flush=True)
    _, by_id = inventory(source)
    report["cut_anchors"] = {
        str(sid): [{"event": eid, "xy": [ev.attrs["@x"], ev.attrs["@y"]]}
                   for eid, ev in load(by_id[sid]).attrs["@events"].items()
                   if source_obstacle(ev) == "cut"] for sid in (39, 86, 87)
    }
    flash_page = load(by_id[21]).attrs["@events"][2].attrs["@pages"][0].attrs
    # Report guard names and numeric inputs, not raw source Ruby.
    report["route2_flash_branch_guards"] = [
        {"native_kind": op.attrs["@parameters"][0],
         "tokens": sorted(set(re.findall(r"(?i)(?:pokedex|(?:owned|seen)(?:_?count)?|HM05|HMFLASH|\d+)",
                                       text(op.attrs["@parameters"][-1]))))}
        for op in flash_page["@list"] if op.attrs["@code"] == 111 and op.attrs["@parameters"]
    ]
    print("KANTO_K04_ROUTE2_FLASH_GUARDS:" + json.dumps(report["route2_flash_branch_guards"]), flush=True)
    print("KANTO_K04_SOURCE_CUT_ANCHORS:" + json.dumps(report["cut_anchors"]), flush=True)
    # Source scripts and engine files are not included in the receipt.
    target = ROOT / ".blue-work/kanto-k04-source.json"
    target.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print("KANTO_K04_SOURCE_INVENTORY_OK:" + json.dumps({
        "maps": [(r["id"], r["name"], r["destination_candidate"]) for r in report["maps"]],
        "connections": len(report["connections"]), "transfers": len(report["transfers"]),
        "trainer_events": len(report["trainers"]), "blocked_from_release": True,
    }, ensure_ascii=True), flush=True)


if __name__ == "__main__":
    main()
