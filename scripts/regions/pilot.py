"""Prepare and launch the Kanto pilot in a separate copy of the installed Blue game."""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import subprocess
import tempfile
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
EVENT_CLASSES = {
    "RPG::Event", "RPG::Event::Page", "RPG::Event::Page::Condition", "RPG::Event::Page::Graphic",
    "RPG::MoveRoute", "RPG::MoveCommand", "RPG::EventCommand",
}
SYSTEM_CLASSES = {"RPG::System", "RPG::System::Words", "RPG::System::TestBattler"}
TYPES = {"RIVAL": "RIVAL1", "BUGCATCHER": "BUGCATCHER", "CAMPER": "CAMPER", "LEADER": "LEADER_Brock"}
TRAINERS = {
    24: {16: ("BUGCATCHER", "Rick"), 17: ("BUGCATCHER", "Doug"), 18: ("BUGCATCHER", "Anthony"),
         19: ("BUGCATCHER", "Charlie"), 20: ("BUGCATCHER", "Sammy")},
    28: {6: ("CAMPER", "Liam"), 7: ("LEADER", "Brock")},
}
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

    for original, destination in mapping.items():
        events = load(source / "Data" / f"Map{original:03}.rxdata").attrs["@events"]
        dest_file = target / "Data" / f"Map{destination:03}.rxdata"
        map_data = load(dest_file)
        selected = {}
        script_events = {6: {15: "BlueKantoPilot.choose_starter", 14: "BlueKantoPilot.rival"},
                         11: {2: "BlueKantoPilot.heal"}}
        scripts = dict(script_events.get(original, {}))
        if original == 12:
            scripts[find_shopkeeper(events)] = MART
        for event_id, (kind, name) in TRAINERS.get(original, {}).items():
            scripts[event_id] = f'BlueKantoPilot.battle(:BLUE_KANTO_{kind}, "{name}")'
        if scripts.keys() - events.keys():
            raise ValueError(f"Missing event anchor in map {original}")
        for event_id, event in events.items():
            if event_id in scripts:
                selected[event_id] = new_event(event, [command(355, scripts[event_id].encode())], 0, actor(event))
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
        if source_id in (5, 9, 10, 18, 24, 25):
            metadata.extend(["Outdoor = true", "ShowArea = true"])
        metadata.append("")
    (pbs / "map_metadata_kanto.txt").write_text("\n".join(metadata), encoding="utf8")


def install_runtime(target, mapping):
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
    # Force compiler to consume new PBS, but keep a real release-mode title after the first boot.
    (data / "blue-compile-request.txt").write_text("compile", encoding="ascii")
    (data / "PluginScripts.rxdata").unlink(missing_ok=True)
    (target / PILOT_META).write_text(json.dumps({"save_app": SAVE_APP, "save_org": SAVE_ORG, "maps": mapping}),
                                    encoding="utf8")


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
        install_runtime(target, mapping)
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
    if not args.launch or not output.exists():
        build(args.source.resolve(), args.game.resolve(), output)
        print(f"Piloto de Kanto preparado em {output}")
    if args.launch:
        launch(output)


if __name__ == "__main__":
    main()
