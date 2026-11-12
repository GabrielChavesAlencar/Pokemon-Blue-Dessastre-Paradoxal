"""Read-only core event audit for Celadon (source FRLG 1.1).

Emit event IDs, page triggers, names, and *trainer command identifiers* only;
never run source Ruby, import source dialogue, or activate Rocket/Game Corner.
"""
from __future__ import annotations

import re
from audit import ROOT, load
from pbs import read_blocks
from server.ruby_marshal import text

ROOT_SOURCE = ROOT / ".blue-work/frlg-source/Essentials FRLG"
CORE = (111, 114, 115, 117, 124)
TRAINER_SCRIPT = re.compile(
    r"(?:pbTrainerBattle|TrainerBattle|pbDoubleTrainerBattle|pbTrainerIntro)"
)


def main():
    for source_id in CORE:
        m = load(ROOT_SOURCE / "Data" / f"Map{source_id:03}.rxdata").attrs
        print(f"KANTO_CELADON_CORE_MAP:{source_id}|{m['@width']}x{m['@height']}|{len(m['@events'])} events")
        for event_id, event in sorted(m["@events"].items()):
            pages = event.attrs["@pages"]
            name = text(event.attrs["@name"])
            first = pages[0].attrs
            graphic = text(first["@graphic"].attrs["@character_name"])
            scripts = []
            for page in pages:
                for cmd in page.attrs["@list"]:
                    if cmd.attrs["@code"] in (355, 655):
                        raw = text(cmd.attrs["@parameters"][0])
                        if TRAINER_SCRIPT.search(raw):
                            # Metadata only: trainer-command line, no dialogue.
                            scripts.append(raw.split("\n", 1)[0][:160])
            print(f"KANTO_CELADON_CORE_EVENT:{source_id}|{event_id}|{name}|"
                  f"trigger={first['@trigger']}|pages={len(pages)}|graphic={graphic}|"
                  f"trainer={';'.join(scripts[:2])}")
    # The full FRLG source contains repeated unrelated Rocket headers. Read
    # only the eight verified gym trainer identities; never parse all rosters.
    selected = {
        "LEADER_Erika,Erika", "PICNICKER,Tina", "LASS,Kay",
        "BEAUTY,Bridget", "BEAUTY,Tamia", "BEAUTY,Lori",
        "LASS,Lisa", "COOLTRAINER_F,Mary",
    }
    blocks = read_blocks(ROOT_SOURCE / "PBS/trainers.txt", selected)
    for key, lines in sorted(blocks.items()):
        print("KANTO_CELADON_CORE_ROSTER:" + key + "|" +
              "|".join(line for line in lines if line.strip())[:2600])
    print("KANTO_CELADON_CORE_ROSTER_COUNT:" + str(len(blocks)))


if __name__ == "__main__":
    main()
