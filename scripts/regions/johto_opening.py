"""Authored repairs for the private Johto QA map set."""
from __future__ import annotations

import struct
from copy import deepcopy

from build_johto_elm_lab_v1 import table_values
from build_johto_events import command, event_page, ruby
from server.ruby_marshal import text

# Both sides of each gate are walkable but separated by a solid building.
GATES = {
    625: (((8, 12), (13, 12)),),
    601: (((74, 24), (79, 24)),),
    627: (((6, 32), (11, 32)),),
    602: (((58, 37), (63, 37)), ((7, 21), (12, 21))),
}
THEMES = {
    682: "104 New Bark Town",
    600: "104 New Bark Town", 674: "104 New Bark Town", 675: "104 New Bark Town",
    676: "107 Elms Lab", 625: "109 Route 29", 601: "113 Cherrygrove City",
    626: "120 Route 30", 627: "120 Route 30", 629: "120 Route 30", 630: "120 Route 30",
    602: "122 Violet City", 677: "142 Pokemon Gym", 681: "115 Poke Center",
    678: "123 Sprout Tower", 679: "123 Sprout Tower", 680: "123 Sprout Tower",
    628: "128 Union Cave", 631: "128 Union Cave", 632: "128 Union Cave", 633: "128 Union Cave",
    603: "133 Azalea Town", 634: "136 Route 34", 604: "141 Goldenrod City",
    639: "166 Route 38", 640: "166 Route 38",
}
BATTLE_THEMES = (
    "110 Battle! (Wild Pokemon Johto)", "111 Victory! (Wild Pokemon)",
    "118 Battle! (Trainer Battle Johto)", "119 Victory! (Trainer Battle)",
    "138 Battle! (Rival)", "143 Battle! (Gym Leader Johto)", "144 Victory! (Gym Leader)",
)
NPCS = (
    (600, 10, 23, "SILVER_WINDOW", "NPC_HGSS_Silver", "silver_window"),
    (676, 13, 10, "ELM_ASSISTANT", "NPC_HGSS_Scientist", "assistant"),
    (601, 63, 22, "CITY_GUIDE", "NPC_HGSS_Gentleman", "guide"),
    (626, 20, 19, "MR_POKEMON", "NPC_HGSS_Gentleman", "mr_pokemon"),
    (629, 28, 8, "FISHERMAN", "trainer_FISHERMAN", "fisherman"),
    (602, 13, 22, "ROCK_SMASH_GUIDE", "NPC_HGSS_Gentleman", "rock_smash_guide"),
)
PICKUPS = (
    (627, 38, 35, "ROUTE31_POTION", "POTION"),
    (629, 22, 68, "ROUTE32_REPEL", "REPEL"),
)


# Only bind field obstacles on audited side paths. The toolkit checks the
# correct local badge and a Pokémon with the move before changing the map.
OBSTACLES = (
    (629, 25, 8, "OPTIONAL_CUT", "Object tree 1", "CUT"),
    (629, 30, 10, "OPTIONAL_ROCK_SMASH", "Object_RockSmash", "ROCK_SMASH"),
    (618, 25, 5, "CAVE_BOULDER", "Object boulder", "STRENGTH"),
)
def add_event(map_data, name, point, page):
    events = map_data.attrs["@events"]
    encoded = name.encode("ascii")
    existing = next((e for e in events.values() if e.attrs["@name"] == encoded), None)
    event_id = existing.attrs["@id"] if existing else max(events, default=0) + 1
    events[event_id] = ruby("RPG::Event", id=event_id, name=encoded,
                            x=point[0], y=point[1], pages=[page])
    return events[event_id]


def set_tiles(map_data, replacements):
    data = map_data.attrs["@data"]
    (width, height, _), values = table_values(data.data, 3)
    cells = list(values)
    for x, y, layer, tile in replacements:
        cells[x + width * (y + height * layer)] = tile
    data.data = data.data[:20] + struct.pack(f"<{len(cells)}H", *cells)


def connect_gate(map_data, map_id, pair, index):
    for side, direction in ((0, 6), (1, 4)):
        x, y = pair[side]
        other_x, other_y = pair[1 - side]
        arrival_x = other_x + (-1 if other_x < x else 1)
        if (map_id, index, side) == (602, 0, 1):
            page = event_page(script=f"BlueJohtoPilot.violet_gate({map_id}, {arrival_x}, {other_y}, {direction})", touch=True)
        elif (map_id, index, side) == (602, 1, 1):
            page = event_page(script=f"BlueJohtoPilot.violet_south_gate({map_id}, {arrival_x}, {other_y}, {direction})", touch=True)
        else:
            page = event_page(warp=(map_id, arrival_x, other_y), touch=True)
            page.attrs["@list"][0].attrs["@parameters"][4] = direction
        add_event(map_data, f"JH_GATE_{index}_{side}", (x, y), page)


def repair_opening(maps, sprites):
    for mid, pairs in GATES.items():
        for index, pair in enumerate(pairs):
            connect_gate(maps[mid], mid, pair, index)
    # The west gate on Route 31 enters a short cul-de-sac. Connect it to
    # the existing trail just east of the ledge using the same route floor.
    set_tiles(maps[627], [(x, 35, layer, 418 if layer == 0 else 0)
                         for x in (34, 35) for layer in range(3)])
    lab = maps[676]
    events = lab.attrs["@events"]
    for event_id, event in list(events.items()):
        name = text(event.attrs["@name"])
        if name.startswith("JH_LAB_BALL_COUNTER_"):
            del events[event_id]
        elif name.startswith("JH_STARTER_"):
            event.attrs["@y"] = 7
            event.attrs["@pages"][0].attrs["@always_on_top"] = True
    set_tiles(lab, [(x, 15, 0, 0) for x in range(1, 19)])
    set_tiles(maps[674], [(5, 1, 2, 0), (6, 1, 2, 0)])
    for mid, x, y, name, sprite, handler in NPCS:
        if sprite in sprites:
            add_event(maps[mid], f"JH_{name}", (x, y), event_page(script=f"BlueJohtoPilot.{handler}", sprite=sprite))
    for mid, x, y, name, sprite, action in OBSTACLES:
        if sprite not in sprites:
            continue
        row = add_event(maps[mid], f"JH_{name}", (x, y), event_page(script="nil", sprite=sprite))
        event_id = row.attrs["@id"]
        call = f'BlueJohtoPilot.field_obstacle("{action}", {event_id})'
        row.attrs["@pages"][0].attrs["@list"][0] = command(355, call.encode("ascii"))
        if action != "STRENGTH":
            hidden = event_page(script="nil", touch=True)
            hidden.attrs["@trigger"] = 0
            hidden.attrs["@condition"].attrs["@self_switch_valid"] = True
            row.attrs["@pages"].append(hidden)
    if "Object_Ball" in sprites:
        for mid, x, y, name, item in PICKUPS:
            row = add_event(maps[mid], f"JH_{name}", (x, y), event_page(script="nil", sprite="Object_Ball"))
            call = f'BlueJohtoPilot.pickup(:{item}, "{name}", {row.attrs["@id"]})'
            row.attrs["@pages"][0].attrs["@list"][0] = command(355, call.encode("ascii"))
            hidden = event_page(script="nil", touch=True)
            hidden.attrs["@trigger"] = 0
            hidden.attrs["@condition"].attrs["@self_switch_valid"] = True
            row.attrs["@pages"].append(hidden)
    for mid, map_data in maps.items():
        if mid in THEMES:
            map_data.attrs["@autoplay_bgm"] = True
            map_data.attrs["@bgm"] = ruby("RPG::AudioFile", name=f"HGSS {THEMES[mid]}".encode("ascii"),
                                         volume=85, pitch=100)


def install_audio(folder, files):
    for theme in sorted(set(THEMES.values()) | set(BATTLE_THEMES)):
        name = f"HGSS {theme}.ogg"
        path = folder / name
        if not path.is_file() or path.is_symlink():
            continue
        content = path.read_bytes()
        if not content.startswith(b"OggS"):
            raise ValueError(f"Áudio HGSS inválido: {name}")
        files["Audio/BGM/" + name] = content
