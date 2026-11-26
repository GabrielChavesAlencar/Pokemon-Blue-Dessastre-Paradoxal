"""K03-A: pin source Day Care identity and transfers before installing it.

Only reads the verified local FRLG source. Never executes source Ruby, copies
maps or emits dialogue/scripts. This is an installation prerequisite, not a
claim that the Day Care mechanic is implemented.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit import inventory, load, json_file, KANTO
from server.ruby_marshal import text

def require(value, message):
    if not value:
        raise ValueError(message)

def describe(source):
    infos, files = inventory(source)
    ids = [39, 56, 58, 59, 60, 61, 63, 64, 65]
    require(all(mid in infos and mid in files for mid in ids), "K03-A source map missing")
    maps = {mid: load(files[mid]).attrs for mid in ids}
    registry = json_file(KANTO)
    require(registry["maps"].get("58") == "DAY_CARE", "Day Care not catalogued")
    require(all(str(mid) in registry["maps"] for mid in ids if mid != 58),
            "K03-A installed corridor registry incomplete")
    name = text(infos[58].attrs["@name"])
    require(re.search(r"day\s*care", name, re.I), "Source Map058 is not Day Care")
    def inspect(mid):
        rows = []
        for eid, ev in sorted(maps[mid]["@events"].items()):
            attrs = ev.attrs
            pages = []
            for i, page in enumerate(attrs["@pages"], 1):
                p = page.attrs
                codes, transfers, api_tokens = [], [], set()
                for cmd in p["@list"]:
                    code = cmd.attrs["@code"]
                    args = cmd.attrs["@parameters"]
                    codes.append(code)
                    if code == 201 and len(args) >= 4 and args[0] == 0:
                        transfers.append({"map": args[1], "xy": args[2:4]})
                    if code in (111, 355, 655):
                        for arg in args:
                            if isinstance(arg, (str, bytes)):
                                api_tokens.update(re.findall(r"\b(?:pbDayCare\w*|DayCare|day_care|daycare)\b",
                                                             text(arg), re.I))
                pages.append({"page": i, "trigger": p["@trigger"],
                              "opcodes": sorted(set(codes)), "transfers": transfers,
                              "daycare_api_tokens": sorted(api_tokens),
                              "conditions": sorted(k for k,v in p["@condition"].attrs.items()
                                                   if k.endswith("_valid") and v)})
            rows.append({"id": eid, "xy": [attrs["@x"], attrs["@y"]], "pages": pages})
        return rows
    events = {mid: inspect(mid) for mid in ids}
    def transfers(origin, target):
        result = []
        for event in events[origin]:
            for page in event["pages"]:
                for warp in page["transfers"]:
                    if warp["map"] != target:
                        continue
                    x,y = warp["xy"]
                    require(0 <= x < maps[target]["@width"] and 0 <= y < maps[target]["@height"],
                            "Day Care source transfer outside map bounds")
                    result.append({"event": event["id"], "source_xy": event["xy"],
                                   "page": page["page"], "trigger": page["trigger"],
                                   "landing": warp["xy"]})
        return result
    entrance, exit_rows = transfers(56,58), transfers(58,56)
    report = {"status": "SOURCE_IDENTIFIED", "source_id": 58, "name": name,
              "size": [maps[58]["@width"], maps[58]["@height"]],
              "entrance": entrance, "return": exit_rows, "events": events[58],
              "catalogued": True, "physical_gameplay": False}
    report["direct_reciprocal_transfers"] = bool(entrance and exit_rows)
    report["mechanic_api_observed"] = any(p["daycare_api_tokens"] for e in events[58] for p in e["pages"])
    return report

if __name__ == "__main__":
    report = describe(ROOT / ".blue-work/frlg-source/Essentials FRLG")
    out = ROOT / ".blue-work/kanto-k03a-daycare-source.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf8")
    print("KANTO_K03A_DAYCARE_SOURCE_REPORT:" + json.dumps(report, ensure_ascii=True))
    if not report["direct_reciprocal_transfers"] or not report["mechanic_api_observed"]:
        raise SystemExit("K03-A direct Day Care transfers not proven; inspect source report")
    print("KANTO_K03A_DAYCARE_SOURCE_IDENTITY_OK")
