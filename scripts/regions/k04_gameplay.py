"""Source-validated K04 conversion shared by the isolated proof and future integration.

These helpers write to a prepared copy; they never operate on a source archive.
"""
from __future__ import annotations

import copy
import re

from audit import ROOT, load, text
from k04_flash import SOURCE_ID as FLASH_MAP, EVENT_ID as FLASH_EVENT, install_flash_aide
from kanto_overworld import adapt_source_field_event, source_obstacle
from pbs import catalogue, normalize_encounters, read_blocks, trainer_draft
from pilot import EVENT_CLASSES, TYPES, command, if_scene, new_event, write_map

TRAINERS = {
    86: {2: "PICNICKER,Alicia", 3: "HIKER,Jeremy", 4: "CAMPER,Chris",
         5: "BUGCATCHER,Brent", 6: "CAMPER,Drew", 7: "BUGCATCHER,Conner",
         8: "HIKER,Brice", 9: "PICNICKER,Caitlin", 10: "HIKER,Alan"},
    87: {5: "PICNICKER,Heidi", 10: "POKEMANIAC,Mark", 16: "PICNICKER,Carol",
         17: "HIKER,Clark", 18: "HIKER,Trent", 21: "POKEMANIAC,Herman"},
    90: {2: "HIKER,Lenny", 3: "HIKER,Oliver", 6: "POKEMANIAC,Ashton",
         8: "HIKER,Lucas", 9: "PICNICKER,Leah", 10: "PICNICKER,Ariana", 12: "PICNICKER,Dana"},
    91: {1: "HIKER,Allen", 2: "HIKER,Eric", 3: "POKEMANIAC,Steve",
         19: "POKEMANIAC,Winston", 21: "PICNICKER,Martha", 22: "PICNICKER,Sofia",
         25: "HIKER,Allen", 26: "POKEMANIAC,Cooper"},
}
NURSE = re.compile(r"\b(?:pbPokeCenter|pbPokemonCenter|pbHealAll|pbSetPokemonCenter)\b|\$player\.heal_party")


def trainer_profiles(report):
    expected = {f"{sid}/{eid}": k for sid, rows in TRAINERS.items() for eid, k in rows.items()}
    if {eid: list(profiles) for eid, profiles in report["trainers"].items()} != {
            eid: [kind_name] for eid, kind_name in expected.items()}:
        raise ValueError("K04 trainer event or source profile changed")
    specs = {}
    for spec in expected.values():
        kind, name = spec.split(",")
        if kind not in TYPES or not re.fullmatch(r"[A-Za-z]+", name):
            raise ValueError(f"Unsupported K04 trainer identity {spec}")
        specs[spec] = (kind, name, 0)
    return specs


def clean_trainer_source(source, destination, specs):
    blocks = read_blocks(source, specs)
    # Exactly one pinned stray line follows Alicia's lose text. It isn't a
    # property, and no other malformed input is discarded.
    alicia = blocks["PICNICKER,Alicia"]
    if (alicia.count("x") != 1 or alicia.index("x") == 0
            or not alicia[alicia.index("x") - 1].startswith("LoseText =")):
        raise ValueError("K04 Alicia's source normalization no longer matches")
    alicia.remove("x")
    destination.write_text("".join(f"[{key}]\n" + "\n".join(lines) + "\n"
                                   for key, lines in blocks.items()), encoding="utf-8")


def sprite(source, target, event):
    graphic = text(event.attrs["@pages"][0].attrs["@graphic"].attrs["@character_name"])
    if not re.fullmatch(r"[\w .()\-]+", graphic) or graphic in (".", ".."):
        raise ValueError(f"Invalid K04 actor graphic {graphic!r}")
    name = "FRLG_Pilot_" + graphic
    folder = source / "Graphics/Characters"
    src = folder / (graphic + ".png")
    if not src.resolve().is_relative_to(folder.resolve()):
        raise ValueError("K04 actor points outside the pinned source")
    dst = target / "Graphics/Characters" / (name + ".png")
    if not src.is_file():
        src = target / "Graphics/Characters" / (graphic + ".png")
    raw = src.read_bytes()
    if not raw.startswith(b"\x89PNG\r\n\x1a\n") or (dst.exists() and dst.read_bytes() != raw):
        raise ValueError(f"Invalid K04 actor graphic or asset collision: {graphic}")
    if not dst.exists():
        dst.write_bytes(raw)
    return name.encode("utf-8")


def trainer_event(event, source_id, event_id, spec, graphic):
    kind, name = spec.split(",")
    key = f"KANTO_{source_id:03d}_{event_id:03d}"
    first = event.attrs["@pages"][0].attrs
    if any(value for field, value in first["@condition"].attrs.items() if field.endswith("_valid")):
        raise ValueError(f"K04 trainer requires authored conditions at {source_id}/{event_id}")
    label = text(event.attrs["@name"])
    auto = first["@trigger"] == 2 and re.search(r"(?i)(?:trainer|sight)\([1-9]\d*\)", label)
    intro = [f"pbTrainerIntro(:BLUE_KANTO_{kind})", "pbNoticePlayer(get_self)"] if auto else []
    calls = [*intro, f'BlueKantoPilot.battle(:BLUE_KANTO_{kind}, "{name}", "{key}")',
             f'BlueKantoPilot.sync_trainer_event("{key}", "{name}", {event_id})']
    if auto:
        calls.append("pbTrainerEnd")
    native = new_event(event, [command(355, c.encode("ascii")) for c in calls], 2 if auto else 0, graphic)
    after = copy.deepcopy(native.attrs["@pages"][0])
    after.attrs["@condition"].attrs.update({"@self_switch_valid": True, "@self_switch_ch": b"A"})
    after.attrs.update({"@trigger": 0, "@through": False, "@direction_fix": False,
                        "@list": [command(355, f'BlueKantoPilot.trainer_repeat("{name}", :BLUE_KANTO_{kind})'.encode("ascii")), command(0)]})
    native.attrs["@pages"].append(after)
    return native


def center_anchor(donor):
    def visible_service(event):
        pages = event.attrs["@pages"]
        visible = bool(pages[0].attrs["@graphic"].attrs["@character_name"])
        return visible and any(
            NURSE.search(text(op.attrs["@parameters"][0]))
            for pg in pages for op in pg.attrs["@list"]
            if op.attrs["@code"] in (355, 655) and len(op.attrs["@parameters"]) == 1)
    events = donor.attrs["@events"]
    candidates = [eid for eid, ev in events.items() if visible_service(ev)]
    if len(candidates) != 1:
        raise ValueError(f"K04 expected one original visible nurse, found {candidates}")
    return candidates[0]


def append(path, addition):
    with path.open("a", encoding="utf-8") as f:
        f.write("\n" + addition.strip() + "\n")


def install_actors(source, target, donor, native, source_id, report):
    """Populate a prepared native map with the approved actors and Cut obstacles."""
    actor_report, cut_report = {}, {}
    source_events, events = donor.attrs["@events"], native.attrs["@events"]
    declared = TRAINERS.get(source_id, {})
    occupied = {tuple(event.attrs[k] for k in ("@x", "@y")) for event in events.values()}
    for eid, spec in declared.items():
        event = source_events[eid]
        xy = tuple(event.attrs[k] for k in ("@x", "@y"))
        if xy in occupied or eid in events:
            raise ValueError(f"K04 trainer conflicts with an event at {source_id}/{eid}")
        occupied.add(xy)
        events[eid] = trainer_event(event, source_id, eid, spec, sprite(source, target, event))
        actor_report[f"{source_id}/{eid}"] = {"profile": spec, "xy": xy,
            "sight": events[eid].attrs["@pages"][0].attrs["@trigger"] == 2}
    if source_id in (86,87):
        source_cut = {eid: ev for eid, ev in source_events.items()
                      if source_obstacle(ev) == "cut"}
        expected_cut = {r["event"]: r["xy"] for r in report["cut_anchors"][str(source_id)]}
        if {eid: [ev.attrs["@x"], ev.attrs["@y"]] for eid,ev in source_cut.items()} != expected_cut:
            raise ValueError("K04 Cut anchors no longer match audited source")
        for eid,ev in source_cut.items():
            if eid in events:
                raise ValueError(f"K04 Cut anchor overlaps a native event {source_id}/{eid}")
            converted, evidence = adapt_source_field_event(
                ev,source_id,eid,set(),lambda actor: sprite(source,target,actor),
                new_event,command,if_scene)
            if evidence != {"kind":"cut"}:
                raise ValueError(f"K04 Cut conversion absent at {source_id}/{eid}")
            events[eid] = converted
        cut_report[source_id] = expected_cut
    nurse_id = None
    if source_id == 88:
        nurse_id = center_anchor(donor)
        if nurse_id in events:
            raise ValueError("K04 nurse conflicts with a transfer")
        ev = source_events[nurse_id]
        events[nurse_id] = new_event(ev, [command(355, b"BlueKantoPilot.heal")], 0, sprite(source, target, ev))
    return actor_report, cut_report, nurse_id


def install_aide_and_runtime(source, target, source_maps, mapping):
    """Update just the authored Route 2 event and provide the plugin it invokes."""
    gate_path = target / "Data" / f"Map{mapping[FLASH_MAP]:03d}.rxdata"
    gate_baseline = load(gate_path)
    source_aide = load(source_maps[FLASH_MAP]).attrs["@events"][FLASH_EVENT]
    gate = install_flash_aide(gate_baseline, source_aide, sprite(source,target,source_aide))
    write_map(gate_path, gate, EVENT_CLASSES)
    if load(gate_path) != gate:
        raise ValueError("K04 Flash aide did not survive native Map Marshal round trip")
    plugin = target / "Plugins/ZZZZZ Blue Kanto Pilot/KantoPilot.rb"
    append(plugin, (ROOT / "scripts/regions/KantoK04Field.rb").read_text("utf-8"))
    return gate_path


def install_pbs_payload(source, target, tmp, specs, delta):
    """Append only the audited new profiles and four original encounter tables."""
    species, moves, items = (catalogue(target, k) for k in ("pokemon", "moves", "items"))
    pbs = target / "PBS"
    fixed = tmp / "k04-trainer-subset.txt"
    clean_trainer_source(source / "PBS/trainers.txt", fixed, specs)
    trainer_pbs = pbs / "trainers_kanto.txt"
    native_profiles = {f"BLUE_KANTO_{kind},{name},{version}" for kind, name, version in specs.values()}
    if read_blocks(trainer_pbs, native_profiles):
        raise ValueError("K04 trainer profile would replace a released profile")
    append(trainer_pbs, trainer_draft(fixed, species, moves, items, specs))
    wild, tables = normalize_encounters(source / "PBS/encounters.txt", delta, species)
    if tables != 4 or {int(n) for n in re.findall(r"(?m)^\[(\d+)(?:,\d+)?\]", wild)} != {
            delta[i] for i in (86, 87, 90, 91)}:
        raise ValueError("K04 must retain exactly the four original encounter tables")
    append(pbs / "encounters_kanto.txt", wild)
    return tables
