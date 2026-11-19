"""Fail-closed proof for Kanto Cerulean content in a compiled JoiPlay ZIP.

A git commit or a green source build alone cannot prove Route 24/25 or the
Cerulean trainer fix reached Android. Check the archive we will release,
including native map files, PBS identities, connections and compiled Journey.
No personal save or FRLG donor is read.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.android.package import compiled_region

SOURCE_MAP_IDS = ("39", "42", "53", "54", "55")
EDGES = (("39", "53"), ("39", "54"), ("53", "54"))
EXPECTED_KANTO_MAPS = 145
EXPECTED_MUSIC_MAPS = 77
JOURNEY = "Plugins/ZZZZ Blue Story and Presentation/Journey.rb"


def assert_delivery(path: Path, channel: str) -> dict:
    roots = {
        "kanto": ("Pokemon-Blue-Kanto-Android/", "Kanto pilot.json"),
        "multiregion": ("Pokemon-Blue-Android/", "Data/blue-kanto-install.json"),
    }
    if channel not in roots:
        raise ValueError("Unrecognized Android channel")
    root, marker = roots[channel]
    with ZipFile(path) as archive:
        files = set(archive.namelist())
        if len(files) != len(archive.namelist()):
            raise ValueError("Duplicated archive entries")
        if root + marker not in files:
            raise ValueError("Missing Kanto map registry in release")
        metadata = json.loads(archive.read(root + marker))
        mapping = metadata.get("maps")
        if (not isinstance(mapping, dict) or
                len(mapping) != EXPECTED_KANTO_MAPS or
                not all(source in mapping for source in SOURCE_MAP_IDS)):
            raise ValueError("Android ZIP lacks the 145-map Kanto/Cerulean revision")
        all_ids = list(mapping.values())
        if (any(type(value) is not int or value <= 0 for value in all_ids)
                or len(set(all_ids)) != len(all_ids)):
            raise ValueError("Kanto destination map IDs are invalid or collide")
        for source in SOURCE_MAP_IDS:
            destination = mapping[source]
            native = root + f"Data/Map{destination:03d}.rxdata"
            if native not in files or archive.getinfo(native).file_size < 128:
                raise ValueError(f"Source Map{source} was not compiled for Android")
        # Native connections must use the DESTINATION MapIDs, never the FRLG
        # donor IDs. This also catches old connected-map files in a new ZIP.
        connections = root + "PBS/map_connections_kanto.txt"
        if connections not in files:
            raise ValueError("Kanto north connections are not packaged")
        edges = set()
        for line in archive.read(connections).decode("utf-8-sig").splitlines():
            row = line.split("#", 1)[0].strip()
            if not row:
                continue
            columns = [value.strip() for value in row.split(",")]
            if len(columns) != 6:
                raise ValueError("Malformed Kanto connection entry")
            try:
                edges.add(frozenset((int(columns[0]), int(columns[3]))))
            except ValueError as error:
                raise ValueError("Non-numeric Kanto connection MapID") from error
        for left, right in EDGES:
            if frozenset((mapping[left], mapping[right])) not in edges:
                raise ValueError(f"Missing Cerulean edge Map{left}/Map{right}")
        trainer_pbs = root + "PBS/trainers_kanto.txt"
        if trainer_pbs not in files:
            raise ValueError("Kanto trainers PBS missing")
        pbs = archive.read(trainer_pbs).decode("utf-8-sig")
        for section in ("[BLUE_KANTO_SWIMMER,Luis,0]",
                        "[BLUE_KANTO_PICNICKER,Diana,0]"):
            if section not in pbs:
                raise ValueError(f"Native trainer is missing from Kanto PBS: {section}")
        if root + JOURNEY not in files:
            raise ValueError("Journey battle adapter missing from Android ZIP")
        source = archive.read(root + JOURNEY)
        if not re.search(rb"kanto_team\s*=\s*args\.flatten\.any\?", source):
            raise ValueError("Luis name-collision guard missing from Android source")
        cache = archive.read(root + "Data/PluginScripts.rxdata")
        compiled_region(cache, "Journey.rb", source)
        music = root + "Data/blue-kanto-music.txt"
        if music not in files:
            raise ValueError("Kanto map music manifest missing")
        count = sum(line.startswith("MAP\t") for line in
                    archive.read(music).decode("utf8").splitlines())
        if count != EXPECTED_MUSIC_MAPS:
            raise ValueError(f"Stale Kanto music scope: {count}, expected 77")
    return {"channel": channel, "kanto_maps": EXPECTED_KANTO_MAPS,
            "cerulean_sources": list(SOURCE_MAP_IDS),
            "music_maps": EXPECTED_MUSIC_MAPS,
            "compiled_journey": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=("kanto", "multiregion"), required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(assert_delivery(args.archive, args.channel), sort_keys=True))


if __name__ == "__main__":
    main()
