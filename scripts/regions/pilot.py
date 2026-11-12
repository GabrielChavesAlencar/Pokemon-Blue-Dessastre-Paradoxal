"""Prepare and launch the Kanto pilot in a separate copy of the installed Blue game."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from audit import KANTO, ROOT, json_file, load
from export_kanto import LOCATION_NAMES
from pbs import read_blocks
from server.ruby_marshal import RubyObject, text
from stage import serialize, stage

SAVE_ORG = "Dessastre Paradoxal Kanto Testes"
SAVE_APP = "Kanto Piloto"
OUTPUT = ROOT / ".blue-work/kanto-pilot"
SOURCE = ROOT / ".blue-work/frlg-source/Essentials FRLG"
PILOT_META = "Kanto pilot.json"
# Changes to any of these inputs require a new isolated pilot build.
PILOT_INPUTS = (
    "scripts/regions/pilot.py",
    "scripts/regions/stage.py",
    "scripts/regions/pbs.py",
    "scripts/regions/export_kanto.py",
    "scripts/regions/KantoPilot.rb",
    "scripts/battle_polish/RegionStart.rb",
    "scripts/battle_polish/Story.rb",
    "data/regions/kanto-source.json",
)


def build_signature():
    digest = hashlib.sha256()
    for relative in PILOT_INPUTS:
        path = ROOT / relative
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def pilot_is_current(output):
    marker = output / PILOT_META
    if not marker.is_file():
        return False
    try:
        return json.loads(marker.read_text(encoding="utf-8"))["build_signature"] == build_signature()
    except (OSError, ValueError, KeyError, TypeError):
        return False


def revised_path(output):
    suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return output.parent / f"{output.name}-revisao-{suffix}"


EVENT_CLASSES = {
    "RPG::Event", "RPG::Event::Page", "RPG::Event::Page::Condition", "RPG::Event::Page::Graphic",
    "RPG::MoveRoute", "RPG::MoveCommand", "RPG::EventCommand",
}
SYSTEM_CLASSES = {"RPG::System", "RPG::System::Words", "RPG::System::TestBattler"}
TYPES = {
    "RIVAL": "RIVAL1", "BUGCATCHER": "BUGCATCHER",
    "CAMPER": "CAMPER", "LEADER": "LEADER_Brock",
    "LASS": "LASS", "YOUNGSTER": "YOUNGSTER",
    "SUPERNERD": "SUPERNERD", "HIKER": "HIKER",
    "ROCKET": "TEAMROCKET_M", "SWIMMER": "SWIMMER2_M",
    "PICNICKER": "PICNICKER", "LEADER_MISTY": "LEADER_Misty",
    "SAILOR": "SAILOR", "ENGINEER": "ENGINEER",
    "GENTLEMAN": "GENTLEMAN", "FISHERMAN": "FISHERMAN",
    "LEADER_SURGE": "ENGINEER",  # Provisional electric-themed battle portrait; original FRLG trainer art not redistributed.
}
TRAINERS = {
    24: {16: ("BUGCATCHER", "Rick"), 17: ("BUGCATCHER", "Doug"), 18: ("BUGCATCHER", "Anthony"),
         19: ("BUGCATCHER", "Charlie"), 20: ("BUGCATCHER", "Sammy")},
    28: {6: ("CAMPER", "Liam"), 7: ("LEADER", "Brock")},
}
# These event IDs and trainer roles come from a read-only source map audit.
TRAINERS.update({
    32: {
        1: ("LASS", "Janice"), 2: ("BUGCATCHER", "Colton"),
        3: ("YOUNGSTER", "Ben"), 4: ("LASS", "Sally"),
        5: ("BUGCATCHER", "Greg"), 6: ("BUGCATCHER", "James"),
        7: ("YOUNGSTER", "Calvin"), 8: ("LASS", "Robin"),
    },
    36: {
        1: ("LASS", "Iris"), 3: ("BUGCATCHER", "Kent"),
        4: ("BUGCATCHER", "Robby"), 5: ("SUPERNERD", "Jovan"),
        7: ("LASS", "Miriam"), 8: ("YOUNGSTER", "Josh"),
        9: ("HIKER", "Marcos"),
    },
    38: {
        5: ("ROCKET", "Grunt", 1), 8: ("ROCKET", "Grunt", 2),
        12: ("ROCKET", "Grunt", 3), 18: ("ROCKET", "Grunt", 4),
        19: ("SUPERNERD", "Miguel"),
    },
    42: {
        1: ("LEADER_MISTY", "Misty"), 11: ("SWIMMER", "Luis"),
        16: ("PICNICKER", "Diana"),
    },
})

TRAINERS.update({
    61: {
        8: ("BUGCATCHER", "Keigo"), 9: ("PICNICKER", "Nancy"),
        10: ("CAMPER", "Ricky"), 12: ("BUGCATCHER", "Elijah"),
        13: ("PICNICKER", "Isabelle"), 14: ("CAMPER", "Jeff"),
    },
    67: {
        1: ("SAILOR", "Dwayne"), 2: ("ENGINEER", "Bailey"),
        3: ("GENTLEMAN", "Tucker"), 5: ("LEADER_SURGE", "Lt. Surge"),
    },
    74: {
        30: ("LASS", "Ann"), 31: ("YOUNGSTER", "Tyler"),
        38: ("GENTLEMAN", "Thomas"), 49: ("GENTLEMAN", "Arthur"),
    },
    75: {
        39: ("GENTLEMAN", "Brooks"), 40: ("FISHERMAN", "Dale"),
        44: ("GENTLEMAN", "Lamar"), 46: ("LASS", "Dawn"),
    },
    77: {
        18: ("FISHERMAN", "Barny"), 19: ("SAILOR", "Phillip"),
        21: ("SAILOR", "Huey"), 23: ("SAILOR", "Dylan"),
        24: ("SAILOR", "Duncan"), 25: ("SAILOR", "Leonard"),
    },
    78: {
        9: ("SAILOR", "Trevor"), 10: ("SAILOR", "Edmond"),
    },
})

SURGE_CANS = {4, 10, *range(22, 35)}
SURGE_LOCKS = {8, *range(11, 20)}

MART = 'pbPokemonMart([:POKEBALL, :POTION, :ANTIDOTE, :PARALYZEHEAL])'


def write_map(path, obj, classes=()):
    path.write_bytes(serialize(obj, classes))


def command(code, *params, indent=0):
    return RubyObject("RPG::EventCommand", {"@code": code, "@indent": indent, "@parameters": list(params)})


def extract_warps(event, mapping):
    for page in event.attrs["@pages"]:
        for op in page.attrs["@list"]:
            row = op.attrs
            if row["@code"] == 201:
                mode, map_id, x, y, direction, fade = row["@parameters"]
                if mode == 0 and map_id in mapping:
                    return command(201, mode, mapping[map_id], x, y, direction, fade)
    return None


def new_event(event, ops, trigger, character):
    clone = copy.deepcopy(event)
    page = clone.attrs["@pages"][0].attrs
    clone.attrs["@pages"] = clone.attrs["@pages"][:1]
    condition = page["@condition"].attrs
    for key in tuple(condition):
        if key.endswith("_valid"):
            condition[key] = False
    graphic = page["@graphic"].attrs
    graphic["@character_name"] = character
    if not character:
        graphic["@tile_id"] = 0
    page["@move_type"] = 0
    page["@move_route"] = RubyObject("RPG::MoveRoute", {
        "@repeat": False, "@skippable": True,
        "@list": [RubyObject("RPG::MoveCommand", {"@code": 0, "@parameters": []})],
    })
    page["@trigger"] = trigger
    page["@through"] = trigger == 1
    page["@direction_fix"] = trigger == 1
    page["@list"] = ops + [command(0)]
    return clone


def find_shopkeeper(events):
    for event_id, event in events.items():
        for page in event.attrs["@pages"]:
            for op in page.attrs["@list"]:
                if op.attrs["@code"] == 355 and b"pbPokemonMart" in op.attrs["@parameters"][0]:
                    return event_id
    raise ValueError("The Viridian shopkeeper event was not found")


def install_events(source, target, mapping):
    event_graphics = source / "Graphics/Characters"
    dest_graphics = target / "Graphics/Characters"

    def actor(event):
        raw = event.attrs["@pages"][0].attrs["@graphic"].attrs["@character_name"]
        name = text(raw)
        if not re.fullmatch(r"[\w .()\-]+", name):
            raise ValueError(f"Invalid actor graphic: {name!r}")
        src = event_graphics / (name + ".png")
        if not src.resolve().is_relative_to(event_graphics.resolve()) or not src.is_file():
            raise ValueError(f"Missing actor graphic: {name}")
        new_name = "FRLG_Pilot_" + name
        shutil.copyfile(src, dest_graphics / (new_name + ".png"))
        return new_name.encode("utf8")

    preview_only = set(json_file(KANTO).get("preview_only", []))
    if preview_only - mapping.keys():
        raise ValueError("Preview-only map ID is missing from the source manifest")
    for original, destination in mapping.items():
        # Phases 09-11 are GEOMETRY ONLY until the user's event analysis finishes.
        # stage() already serializes a blank event table for every imported map.
        if original in preview_only:
            dest_file = target / "Data" / f"Map{destination:03}.rxdata"
            staged_map = load(dest_file)
            if staged_map.attrs["@events"]:
                raise ValueError(f"Phase 09-11 preview map {original} contains foreign events")
            continue
        events = load(source / "Data" / f"Map{original:03}.rxdata").attrs["@events"]
        dest_file = target / "Data" / f"Map{destination:03}.rxdata"
        map_data = load(dest_file)
        selected = {}
        script_events = {6: {15: "BlueKantoPilot.choose_starter", 14: "BlueKantoPilot.rival"},
                         11: {2: "BlueKantoPilot.heal"},
                         26: {2: "BlueKantoPilot.heal"},
                         34: {2: "BlueKantoPilot.heal"},
                         40: {2: "BlueKantoPilot.heal"},
                         36: {18: 'BlueKantoPilot.pickup(:MOONSTONE, "KANTO_036_018")'},
                         65: {2: "BlueKantoPilot.heal"},
                         64: {7: "BlueKantoPilot.ticketmaster"},
                         76: {2: "BlueKantoPilot.captain"}}
        scripts = dict(script_events.get(original, {}))
        if original in (12, 27, 41, 66):
            scripts[find_shopkeeper(events)] = MART
        if original == 64:
            for event_id in (9, 29, 30):
                if event_id not in events:
                    raise ValueError(f"Missing Vermilion harbor gate {event_id}")
                scripts[event_id] = (
                    f"BlueKantoPilot.harbor_gate({mapping[72]}, 9, 7)"
                )
        for event_id, spec in TRAINERS.get(original, {}).items():
            kind, name, *versions = spec
            version = versions[0] if versions else 0
            # Map/event identity prevents two NPCs with the same display name
            # from sharing their victory flag. Never key trainer progress by name.
            key = f"KANTO_{original:03d}_{event_id:03d}"
            arguments = f':BLUE_KANTO_{kind}, "{name}", "{key}"'
            arguments += f", {version}" if version else ""
            scripts[event_id] = f"BlueKantoPilot.battle({arguments})"
        if scripts.keys() - events.keys():
            raise ValueError(f"Missing event anchor in map {original}")
        for event_id, event in events.items():
            if original == 67 and event_id in (SURGE_CANS | SURGE_LOCKS):
                # The foreign gym's puzzle depends on game-wide switches.
                # Translate each trash can to a single audited callback, and
                # each barrier to a local self-switch-driven two-page event.
                is_can = event_id in SURGE_CANS
                script = (f"BlueKantoPilot.surge_can({event_id})" if is_can
                          else "BlueKantoPilot.surge_gate")
                original_graphic = event.attrs["@pages"][0].attrs["@graphic"]
                graphic_name = original_graphic.attrs["@character_name"]
                character = actor(event) if graphic_name else b""
                replacement = new_event(event, [command(355, script.encode())], 0, character)
                if not graphic_name:
                    replacement.attrs["@pages"][0].attrs["@graphic"] = copy.deepcopy(original_graphic)
                if not is_can:
                    opened = copy.deepcopy(replacement.attrs["@pages"][0])
                    c = opened.attrs["@condition"].attrs
                    c["@self_switch_valid"] = True
                    c["@self_switch_ch"] = b"A"
                    g = opened.attrs["@graphic"].attrs
                    g["@tile_id"] = 0
                    g["@character_name"] = b""
                    opened.attrs["@through"] = True
                    opened.attrs["@list"] = [command(0)]
                    replacement.attrs["@pages"].append(opened)
                selected[event_id] = replacement
                continue
            if event_id in scripts:
                floor_trigger = original == 64 and event_id in (9, 29, 30)
                if event_id in TRAINERS.get(original, {}):
                    kind, trainer_name, *_ = TRAINERS[original][event_id]
                    key = f"KANTO_{original:03d}_{event_id:03d}"
                    # Essentials 21.1 only triggers a Trainer(n) line of sight
                    # when the active RPG Event page uses Event Touch (2).
                    # Preserve sight range from the audited FRLG event name;
                    # gym leaders/NPCs without Trainer(n) stay Action Button.
                    source_name = text(event.attrs["@name"])
                    sight = re.search(r"(?i)trainer\\(\\d+\\)", source_name)
                    auto = bool(sight) and not kind.startswith("LEADER")
                    ops = []
                    if auto:
                        ops.append(command(355, f"pbTrainerIntro(:BLUE_KANTO_{kind})".encode()))
                        ops.append(command(355, b"pbNoticePlayer(get_self)"))
                    ops.append(command(355, scripts[event_id].encode()))
                    ops.append(command(355,
                        f'BlueKantoPilot.sync_trainer_event("{key}", "{trainer_name}", {event_id})'.encode()))
                    if auto:
                        ops.append(command(355, b"pbTrainerEnd"))
                    trainer = new_event(event, ops, 2 if auto else 0, actor(event))
                    # Self Switch A is set ONLY after a true battle victory or
                    # recognition of the old pre-ID save flag. The second page
                    # keeps the trainer visible but disables the sight trigger.
                    after_win = copy.deepcopy(trainer.attrs["@pages"][0])
                    condition = after_win.attrs["@condition"].attrs
                    condition["@self_switch_valid"] = True
                    condition["@self_switch_ch"] = b"A"
                    after_win.attrs["@trigger"] = 0
                    after_win.attrs["@through"] = False
                    after_win.attrs["@direction_fix"] = False
                    after_win.attrs["@list"] = [
                        command(355, f'BlueKantoPilot.trainer_repeat("{trainer_name}")'.encode()),
                        command(0)]
                    trainer.attrs["@pages"].append(after_win)
                    selected[event_id] = trainer
                else:
                    selected[event_id] = new_event(
                        event, [command(355, scripts[event_id].encode())],
                        1 if floor_trigger else 0,
                        b"" if floor_trigger else actor(event))
                continue
            if original == 5 and event_id in (11, 13):
                # Professor Oak's original path anchors span the two exit tiles.
                guard = command(111, 12, b"!BlueKantoPilot.rival_done?")
                warp = command(201, 0, mapping[6], 6, 12, 8, 1, indent=1)
                selected[event_id] = new_event(event, [guard, warp, command(0, indent=1), command(412)], 1, b"")
                continue
            warp = extract_warps(event, mapping)
            if warp:
                name = text(event.attrs["@name"])
                # Automatic exits and route gateways are floor tiles. Visible doors use action.
                graphic = event.attrs["@pages"][0].attrs["@graphic"].attrs["@character_name"]
                # Only explicitly supported source door destinations survive. Import no other commands.
                character = actor(event) if graphic else b""
                is_door = "door" in name.lower() and bool(character)
                selected[event_id] = new_event(event, [warp], 0 if is_door else 1, character)
        map_data.attrs["@events"] = selected
        write_map(dest_file, map_data, EVENT_CLASSES)


def copy_game(game, target):
    for name in ("Audio", "Data", "Fonts", "Graphics", "PBS", "Plugins"):
        def ignore(folder, names):
            return [item for item in names if item.startswith("blue-") and item != "blue-trainer-album.dat"]
        shutil.copytree(game / name, target / name, ignore=ignore)
    for path in game.iterdir():
        if path.is_file() and (path.suffix.lower() == ".dll" or path.name in {
                "Game.exe", "Game.ini", "mkxp.json", "preload.rb", "soundfont.sf2", "Credits.txt"}):
            shutil.copyfile(path, target / path.name)


def install_pbs(preview, target, mapping):
    pbs = target / "PBS"
    draft = preview / "drafts"
    for name in ("encounters", "trainers"):
        shutil.copyfile(draft / f"{name}.txt", pbs / f"{name}_kanto.txt")
    shutil.copyfile(preview / "connections-preview.txt", pbs / "map_connections_kanto.txt")

    kinds = read_blocks(pbs / "trainer_types.txt", set(TYPES.values()))
    trainer_types = []
    for kind, base in TYPES.items():
        new_type = f"BLUE_KANTO_{kind}"
        trainer_types.extend([f"[{new_type}]", *kinds[base], ""])
        graphics = target / "Graphics/Trainers"
        sprite = graphics / f"{base}.png"
        shutil.copyfile(sprite, graphics / f"{new_type}.png")
    (pbs / "trainer_types_kanto.txt").write_text("\n".join(trainer_types), encoding="utf8")
    metadata = []
    source_keys = json_file(KANTO)["maps"]
    for source_id, map_id in mapping.items():
        metadata.extend([f"[{map_id:03}]", f"Name = {LOCATION_NAMES[source_keys[str(source_id)]]}"])
        if source_id in (5, 9, 10, 18, 24, 25, 32, 33, 39, 56, 61, 64, 72, 111, 114, 141, 143, 144, 155, 157, 159, 161, 164, 107, 168):
            metadata.extend(["Outdoor = true", "ShowArea = true"])
        metadata.append("")
    (pbs / "map_metadata_kanto.txt").write_text("\n".join(metadata), encoding="utf8")


def install_runtime(target, mapping, game):
    plugin = target / "Plugins/ZZZZZ Blue Kanto Pilot"
    plugin.mkdir()
    shutil.copyfile(ROOT / "scripts/regions/KantoPilot.rb", plugin / "KantoPilot.rb")
    (plugin / "meta.txt").write_text(
        "Name = Blue Kanto Pilot\nVersion = 1.0\nEssentials = 21.1\n"
        "Requires = Blue Battle Presentation and Story\nScripts = KantoPilot.rb\n", encoding="utf8")
    data = target / "Data"
    system = load(data / "System.rxdata")
    system.attrs.update({"@start_map_id": mapping[5], "@start_x": 28, "@start_y": 14})
    write_map(data / "System.rxdata", system, SYSTEM_CLASSES)
    infos = load(data / "MapInfos.rxdata")
    for source_id, key in json_file(KANTO)["maps"].items():
        infos[mapping[int(source_id)]].attrs["@name"] = LOCATION_NAMES[key].encode("utf8")
    write_map(data / "MapInfos.rxdata", infos)
    ini = target / "Game.ini"
    ini.write_text(re.sub(r"(?m)^Title=.*$", f"Title={SAVE_APP}", ini.read_text(encoding="utf-8-sig")), encoding="utf8")
    config = target / "mkxp.json"
    config_text = config.read_text(encoding="utf-8-sig")
    if re.search(r'(?m)^\s*"dataPath(?:App|Org)"', config_text):
        raise ValueError("The base already defines a custom save directory in mkxp.json.")
    isolated = json.dumps({"dataPathApp": SAVE_APP, "dataPathOrg": SAVE_ORG})[1:-1]
    config_text = config_text.replace("{", "{\n  " + isolated + ",", 1)
    config_text = re.sub(r'(?m)^(\s*"windowTitle"\s*:).*$', r'\1 "Pokémon Blue — Piloto de Kanto",', config_text)
    config.write_text(config_text, encoding="utf8")
    # The standalone pilot must always select Kanto automatically on a new
    # game. The main installation uses this marker only after explicit import.
    (data / "blue-kanto-start.txt").write_text(
        f"BLUE_KANTO_START_V1,KANTO,{mapping[5]},28,14\n", encoding="ascii"
    )
    # Experimental shortcuts are available ONLY in this isolated pilot;
    # install_kanto.py never imports this file into the main campaign.
    stops = [
        ("PALLET", "Pallet Town (Oak)", 5, 28, 14),
        ("PEWTER", "Pewter City (Gym)", 25, 19, 21),
        ("ROUTE4", "Route 4 (Mt Moon exit)", 33, 92, 21),
        ("MOON_CENTER", "Mt Moon Pokemon Center", 34, 7, 8),
        ("MOON_1F", "Mt Moon - 1F", 36, 24, 41),
        ("MOON_B1F", "Mt Moon - B1F", 37, 25, 8),
        ("MOON_B2F", "Mt Moon - B2F", 38, 31, 24),
        ("CERULEAN", "Cerulean City (Center)", 39, 22, 20),
        ("MISTY", "Cerulean Gym (Misty)", 42, 8, 18),
        ("ROUTE5", "Route 5 (Underground)", 56, 31, 32),
        ("ROUTE6", "Route 6 (Underground)", 61, 35, 13),
        ("VERMILION", "Vermilion City (Center)", 64, 19, 7),
        ("SURGE", "Vermilion Gym (Lt. Surge)", 67, 5, 19),
        ("HARBOR", "Vermilion Harbor", 72, 9, 7),
        ("SSANNE", "S.S. Anne (1F)", 74, 20, 2),
        ("SSCAPTAIN", "S.S. Anne (Captain)", 76, 4, 8),
        ("SSDECK", "S.S. Anne (Deck)", 78, 58, 3),
        # Phase 09: verified incoming warp coordinates; preview maps have NO events.
        ("ROUTE7", "Rota 7 (cenario, sem eventos)", 111, 15, 25),
        ("CELADON", "Celadon City (cenario)", 114, 48, 17),
        ("ERIKA", "Ginasio Celadon (Erika, sem batalha)", 124, 6, 18),
        ("CEL_CENTER", "Celadon Center (cenario)", 115, 7, 8),
        ("CEL_STORE", "Celadon Loja 1F (cenario)", 117, 2, 14),
        # Phase 10: incoming FRLG warp coordinates, geometry-only.
        ("FUCHSIA", "Fuchsia City (cenario, sem eventos)", 144, 25, 36),
        ("KOGA", "Ginasio Fuchsia Koga (sem batalha)", 147, 7, 21),
        ("FUCH_CENTER", "Fuchsia Centro Pokemon (cenario)", 145, 7, 8),
        ("FUCH_WARDEN", "Casa Warden (cenario)", 152, 6, 9),
        ("SAF_GATE", "Safari Zone Portao (cenario)", 153, 4, 7),
        ("SAF_SOUTH", "Safari Zone Sul (cenario)", 155, 26, 31),
        ("SAF_NORTH", "Safari Zone Norte (cenario)", 159, 25, 6),
        ("SAF_WEST", "Safari Zone Oeste (cenario)", 161, 14, 9),
        ("ROUTE15", "Rota 15 (cenario)", 164, 16, 25),
        # Phase 11: only audited incoming-warp coordinates, geometry only.
        ("ROUTE8", "Rota 8 (cenario)", 107, 3, 25),
        ("SAFF_WEST", "Portaria Oeste Saffron (cenario)", 112, 11, 5),
        ("SAFFRON", "Saffron City (cenario)", 168, 28, 4),
        ("SABRINA", "Ginasio Sabrina (sem batalha)", 171, 15, 23),
        ("SAFF_DOJO", "Fighting Dojo (cenario)", 172, 5, 13),
        ("SAFF_CENTER", "Saffron Centro Pokemon (cenario)", 169, 7, 8),
        ("SILPH_1F", "Silph Co. 1F (cenario)", 178, 8, 20),
        ("SILPH_5F", "Silph Co. 5F (cenario)", 182, 28, 2),
        ("SILPH_11F", "Silph Co. 11F (cenario)", 188, 7, 2),
        ("SILPH_LIFT", "Silph Co. Elevador (cenario)", 189, 2, 5),
    ]
    (data / "blue-kanto-experimental-stops.txt").write_text(
        "".join(f"{code}|{title}|{mapping[old]}|{x}|{y}|2\n"
                for code, title, old, x, y in stops), encoding="utf-8"
    )
    # Force compiler to consume new PBS, but keep a real release-mode title after the first boot.
    (data / "blue-compile-request.txt").write_text("compile", encoding="ascii")
    (data / "PluginScripts.rxdata").unlink(missing_ok=True)
    (target / PILOT_META).write_text(json.dumps({
        "save_app": SAVE_APP, "save_org": SAVE_ORG,
        "maps": mapping, "build_signature": build_signature(),
        "base_data_sha256": {
            name: hashlib.sha256((game / "Data" / name).read_bytes()).hexdigest()
            for name in ("MapInfos.rxdata", "Tilesets.rxdata")
        },
    }), encoding="utf8")


def build(source, game, output):
    output = output.resolve()
    work = (ROOT / ".blue-work").resolve()
    if not output.is_relative_to(work) or output == work or output.exists():
        raise ValueError("Choose a new pilot directory inside .blue-work.")
    if not (game / "Game.exe").is_file():
        raise ValueError("Install and prepare the Blue game first.")
    if not (game / "Plugins/ZZZZ Blue Story and Presentation/Regions.rb").is_file():
        raise ValueError("Prepare the installed Blue game with scripts/launch_game.py --prepare-only first.")
    if not (source / "Data/MapInfos.rxdata").is_file():
        raise ValueError("The editable Essentials FRLG 1.1 project was not found. See docs/CIRCUITO_REGIONAL.md.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".kanto-build-", dir=output.parent) as tmp:
        preview, target = Path(tmp) / "preview", Path(tmp) / "game"
        plan = stage(ROOT, source, game, preview)
        mapping = {row["source_id"]: row["proposed_id"] for row in plan["maps"]}
        target.mkdir()
        copy_game(game, target)
        for folder in ("Data", "Graphics"):
            shutil.copytree(preview / folder, target / folder, dirs_exist_ok=True)
        install_events(source, target, mapping)
        install_pbs(preview, target, mapping)
        install_runtime(target, mapping, game)
        if output.exists():
            raise ValueError("Another pilot already exists at the output path.")
        target.rename(output)
    return output


def launch(output):
    if not (output / PILOT_META).is_file() or not (output / "Game.exe").is_file():
        raise ValueError("This directory is not a prepared Kanto pilot.")
    subprocess.Popen([str(output / "Game.exe")], cwd=output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--game", type=Path, default=ROOT / "game")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--launch", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if args.launch and output.exists() and not pilot_is_current(output):
        replacement = revised_path(output)
        print(f"[INFO] Piloto antigo detectado; preservando {output}", flush=True)
        print(f"[INFO] Preparando nova copia: {replacement}", flush=True)
        output = replacement
    if not args.launch or not output.exists():
        build(args.source.resolve(), args.game.resolve(), output)
        print(f"Piloto de Kanto preparado em {output}")
    if args.launch:
        launch(output)


if __name__ == "__main__":
    main()
