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
from server.ruby_marshal import loads, RubyObject
from scripts.regions.kanto_wall_atlas import render_wall_atlas

SOURCE_MAP_IDS = ("39", "42", "43", "44", "45", "46", "47", "48", "53", "54", "55", "58")
EDGES = (("39", "53"), ("39", "54"), ("53", "54"))
EXPECTED_KANTO_MAPS = 152
EXPECTED_MUSIC_MAPS = 84
JOURNEY = "Plugins/ZZZZ Blue Story and Presentation/Journey.rb"
KANTO_RUNTIME = "Plugins/ZZZZZ Blue Kanto Pilot/KantoPilot.rb"
KANTO_ATLAS = "Plugins/ZZZZZ Blue Kanto Pilot/KantoWallMap.png"


# Exact source-authored city event identity, coordinates and remapped
# transfer landings; this checks RXDATA bytes shipped to the player.
CERULEAN_DOORS = {
    3: ("44", (10, 9), (3, 2)),
    7: ("43", (13, 28), (5, 8)),
    8: ("46", (15, 17), (4, 7)),
    9: ("48", (30, 11), (3, 7)),
    10: ("44", (10, 11), (3, 8)),
    11: ("45", (17, 11), (4, 7)),
    12: ("47", (23, 28), (4, 7)),
    27: ("48", (31, 9), (4, 2)),
}


def verify_cerulean_doors(native: bytes, mapping: dict) -> None:
    city = loads(native)
    events = city.attrs.get("@events") if isinstance(city, RubyObject) else None
    if not isinstance(events, dict):
        raise ValueError("Cerulean city RXDATA has no event table")
    for event_id, (source, xy, landing) in CERULEAN_DOORS.items():
        event = events.get(event_id)
        if (not isinstance(event, RubyObject) or
                (event.attrs.get("@x"), event.attrs.get("@y")) != xy):
            raise ValueError(f"Cerulean door {event_id} missing or moved in installed map")
        pages = event.attrs.get("@pages", [])
        if not any(page.attrs.get("@trigger") == 1 and any(
                op.attrs.get("@code") == 201 and
                op.attrs.get("@parameters", [])[:4] == [0, mapping[source], *landing]
                for op in page.attrs.get("@list", [])) for page in pages):
            raise ValueError(f"Cerulean door {event_id} missing native transfer in installed map")


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
            raise ValueError("Android ZIP lacks the 152-map Kanto/Day Care revision")
        all_ids = list(mapping.values())
        if (any(type(value) is not int or value <= 0 for value in all_ids)
                or len(set(all_ids)) != len(all_ids)):
            raise ValueError("Kanto destination map IDs are invalid or collide")
        # Every registered map must actually reach the ZIP. Checking only
        # Cerulean allowed an unrelated missing Kanto map to pass this gate.
        for source in mapping:
            destination = mapping[source]
            native = root + f"Data/Map{destination:03d}.rxdata"
            if native not in files or archive.getinfo(native).file_size < 128:
                raise ValueError(f"Source Map{source} was not compiled for Android")
        verify_cerulean_doors(archive.read(root + f"Data/Map{mapping['39']:03}.rxdata"), mapping)
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
                        "[BLUE_KANTO_PICNICKER,Diana,0]",
                        "[BLUE_KANTO_ROCKET,Grunt,6]",
                        *(f"[BLUE_KANTO_RIVAL,Blue,{version}]" for version in (31, 32, 33))):
            if section not in pbs:
                raise ValueError(f"Native trainer is missing from Kanto PBS: {section}")
        if root + JOURNEY not in files:
            raise ValueError("Journey battle adapter missing from Android ZIP")
        source = archive.read(root + JOURNEY)
        if not re.search(rb"kanto_team\s*=\s*args\.flatten\.any\?", source):
            raise ValueError("Luis name-collision guard missing from Android source")
        cache = archive.read(root + "Data/PluginScripts.rxdata")
        compiled_region(cache, "Journey.rb", source)
        if root + KANTO_RUNTIME not in files:
            raise ValueError("Cerulean Gary runtime missing from Android ZIP")
        rival = archive.read(root + KANTO_RUNTIME)
        if (b"def self.cerulean_rival_crossing?" not in rival or
                b"Game_Event.prepend(BlueKantoPilot::CeruleanRivalActor)" not in rival):
            raise ValueError("Cerulean Gary movement/actor fix missing")
        for callback in (b"def self.cerulean_bike_exchange", b"def self.cerulean_rocket", b"def self.cerulean_house_entry?", b"def self.cerulean_door_contact"):
            if callback not in rival:
                raise ValueError("Cerulean interiors runtime missing")
        for callback in (b"def self.daycare_deposit", b"def self.daycare_withdraw", b"def self.daycare_menu", b"PokemonGlobalMetadata.prepend(BlueKantoDayCareMetadata)"):
            if callback not in rival:
                raise ValueError("Kanto Day Care runtime missing")
        compiled_region(cache, "KantoPilot.rb", rival)
        if root + KANTO_ATLAS not in files or archive.read(root + KANTO_ATLAS) != render_wall_atlas():
            raise ValueError("Kanto authored atlas absent or differs from release policy")
        # Verify the actual compiled native item, not merely a PBS section.
        catalog = loads(archive.read(root + "Data/items.dat"))
        ticket = catalog.get("BLUE_KANTO_SSTICKET") if isinstance(catalog, dict) else None
        if (not isinstance(ticket, RubyObject) or ticket.name != "GameData::Item"
                or ticket.attrs.get("@id") != "BLUE_KANTO_SSTICKET"
                or ticket.attrs.get("@pocket") != 8
                or ticket.attrs.get("@price") != 0
                or ticket.attrs.get("@consumable") is not False
                or not any(flag in ("KeyItem", b"KeyItem") for flag in ticket.attrs.get("@flags", []))):
            raise ValueError("Compiled Kanto S.S. Ticket key item missing or invalid")
        for key in ("BIKEVOUCHER", "BICYCLE"):
            item = catalog.get(key)
            if (not isinstance(item, RubyObject) or item.name != "GameData::Item"
                    or item.attrs.get("@id") != key
                    or item.attrs.get("@consumable") is not False
                    or not any(flag in ("KeyItem", b"KeyItem") for flag in item.attrs.get("@flags", []))):
                raise ValueError(f"Compiled Cerulean key item missing or invalid: {key}")
        tm = catalog.get("TM28")
        if (not isinstance(tm, RubyObject) or tm.name != "GameData::Item"
                or tm.attrs.get("@id") != "TM28" or tm.attrs.get("@move") != "DIG"
                or tm.attrs.get("@field_use") not in (3, 5)):
            raise ValueError("Compiled Cerulean TM28/DIG machine missing or invalid")
        if b"pilot_bill_ticket_item_granted" not in rival:
            raise ValueError("Legacy digital ticket upgrade missing")
        if channel == "multiregion":
            # The former inline PowerShell python -c lost embedded quoting
            # on Windows and failed with SyntaxError after native compilation.
            # Keep BOTH checks in this regular Python module, fail-closed:
            # accelerated map dispatcher present and the runtime cache exact.
            travel_path = (root +
                           "Plugins/ZZZZ Blue Story and Presentation/RegionTravel.rb")
            if travel_path not in files:
                raise ValueError("Optimized regional map dispatcher missing")
            travel = archive.read(travel_path)
            if b"def self.agent_map_id(region)" not in travel:
                raise ValueError("Optimized regional map dispatcher was removed")
            compiled_region(cache, "RegionTravel.rb", travel)
        music = root + "Data/blue-kanto-music.txt"
        if music not in files:
            raise ValueError("Kanto map music manifest missing")
        count = sum(line.startswith("MAP\t") for line in
                    archive.read(music).decode("utf8").splitlines())
        if count != EXPECTED_MUSIC_MAPS:
            raise ValueError(f"Stale Kanto music scope: {count}, expected {EXPECTED_MUSIC_MAPS}")
    return {"channel": channel, "kanto_maps": EXPECTED_KANTO_MAPS,
            "cerulean_sources": list(SOURCE_MAP_IDS),
            "music_maps": EXPECTED_MUSIC_MAPS,
            "compiled_journey": True, "compiled_cerulean_gary": True,
            "compiled_kanto_ss_ticket": True, "compiled_cerulean_bike_items": True,
            "compiled_cerulean_dig_machine": True, "cerulean_city_doors": 8}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=("kanto", "multiregion"), required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(assert_delivery(args.archive, args.channel), sort_keys=True))


if __name__ == "__main__":
    main()
