"""Read-only FRLG Fuchsia core audit, prior to selective gameplay adaptation.

Print exact MapID/EventID, names and source-roster metadata. Do not import
foreign Ruby scripts or dialogues into the main Decades game.
"""
from __future__ import annotations

import re
from audit import ROOT, load
from pbs import read_blocks
from server.ruby_marshal import text

SOURCE = ROOT / ".blue-work/frlg-source/Essentials FRLG"
MAPS = (144, 145, 146, 147, 152, 153, 155, 157, 159, 161, 163)
TRAINER = re.compile(r"(?i)(trainerbattle|trainerintro|pbtrainer|trainer\.start)")
HEADER = re.compile(r"^\[([^]]+)\]\s*(?:#.*)?$")


def main():
    gym_trainers = set()
    for mapid in MAPS:
        m = load(SOURCE / "Data" / f"Map{mapid:03}.rxdata").attrs
        print(f"KANTO_FUCHSIA_CORE_MAP:{mapid}|{m['@width']}x{m['@height']}|events={len(m['@events'])}")
        for eid, event in sorted(m["@events"].items()):
            name = text(event.attrs["@name"])
            page = event.attrs["@pages"][0].attrs
            graphic = text(page["@graphic"].attrs["@character_name"])
            warps = set()
            for x in event.attrs["@pages"]:
                for cmd in x.attrs["@list"]:
                    op = cmd.attrs
                    if op["@code"] == 201 and len(op["@parameters"]) >= 4:
                        args = op["@parameters"]
                        if args[0] == 0:
                            warps.add((int(args[1]), int(args[2]), int(args[3])))
            # Print only gym characters, interior transit, Safari entry and
            # Warden/Secret House -- not every ordinary NPC dialogue.
            if (mapid in (145, 146, 147, 152, 153, 163) or warps
                    or (mapid == 144 and "Gym" in name)):
                print(f"KANTO_FUCHSIA_CORE_EVENT:{mapid}|{eid}|{name}|"
                      f"trigger={page['@trigger']}|graphic={graphic}|"
                      f"warps={','.join('%s:%s:%s' % x for x in sorted(warps))}")
            if mapid == 147 and eid != 9 and (
                    "trainer" in name.lower() or "sight(" in name.lower()):
                m = re.match(r"(?i)(?:leader\s+)?(\w+)\s+(.+?)(?:\s+Sight\(\d+\))?$", name)
                if m:
                    gym_trainers.add(m[2].strip())
    print("KANTO_FUCHSIA_CORE_GYM_NAMES:" + "|".join(sorted(gym_trainers)))
    selected = {}
    for raw in (SOURCE / "PBS/trainers.txt").read_text(encoding="utf-8-sig").splitlines():
        m = HEADER.fullmatch(raw.strip())
        if m:
            key = m[1]
            # Full source has duplicate Rocket headers. Only select Koga and
            # exact named NPCs from gym events; retain version suffix.
            if "koga" in key.lower() or (
                    len(key.split(",")) >= 2 and key.split(",")[1] in gym_trainers):
                selected[key] = True
    blocks = read_blocks(SOURCE / "PBS/trainers.txt", set(selected))
    for key, lines in sorted(blocks.items()):
        print("KANTO_FUCHSIA_CORE_ROSTER:" + key + "|" +
              "|".join(line.strip() for line in lines if line.strip())[:2200])
    print("KANTO_FUCHSIA_CORE_ROSTER_COUNT:" + str(len(blocks)))


if __name__ == "__main__":
    main()
