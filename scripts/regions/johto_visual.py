"""Build the HGSS-inspired opening maps using installed tile art and local saves' map IDs."""

from __future__ import annotations

import json
import struct
from copy import deepcopy

from build_johto_elm_lab_v1 import decode_png, encode_png, table_values, tile
from build_johto_events import event_page, ruby
from johto_opening import add_event, set_tiles
from server.ruby_marshal import text

CHERRYGROVE_BUSINESSES = {
    684: ("Centro Pokémon de Cherrygrove", (65, 22), "doors6"),
    685: ("Loja Pokémon de Cherrygrove", (69, 10), "doors4"),
}
CHERRYGROVE_HOUSES = {
    686: ((47, 10), "NPC_HGSS_Elder"),
    687: ((57, 10), "NPC_HGSS_Young_Couple_Woman"),
    688: ((54, 19), "NPC_HGSS_Teacher"),
    689: ((43, 26), "NPC_HGSS_Youngster"),
    690: ((54, 28), "NPC_HGSS_Gentleman"),
    691: ((62, 30), "NPC_HGSS_Young_Couple_Man"),
}
# Facades checked against the outdoor sheet. The landing is one tile south.
REGIONAL_DOORS = (
    (602, (17, 27), "Casa de Violet", "house"),
    (602, (24, 30), "Casa de Violet perto do Centro", "house"),
    (602, (36, 41), "Casa ao sul de Violet", "house"),
    (602, (47, 38), "Loja Pokémon de Violet", "mart"),
    (603, (39, 17), "Casa de Azalea", "house"),
    (603, (33, 21), "Loja Pokémon de Azalea", "mart"),
    (603, (27, 28), "Centro Pokémon de Azalea", "center"),
    (605, (37, 35), "Casa em Ecruteak", "house"),
    (606, (28, 13), "Casa de Olivine", "house"),
    (606, (35, 20), "Casa de Olivine perto do porto", "house"),
    (608, (24, 28), "Casa de Mahogany", "house"),
    (608, (32, 28), "Casa em Mahogany", "house"),
    (608, (17, 35), "Centro Pokémon de Mahogany", "center"),
    (608, (29, 35), "Loja Pokémon de Mahogany", "mart"),
    (609, (31, 30), "Centro Pokémon de Blackthorn", "center"),
    (609, (46, 56), "Casa em Blackthorn", "house"),
    (626, (23, 41), "Casa da Rota 30", "house"),
)
REGIONAL_INTERIORS = dict(enumerate(REGIONAL_DOORS, 692))
SIGNS = {
    600: ((3, 21, "Laboratório do Professor Elm"), (8, 26, "New Bark Town"),
          (11, 23, "Casa do jogador"), (10, 33, "New Bark Town / Rota 29 a oeste")),
    601: ((34, 18, "Mirante de Cherrygrove"), (83, 22, "Rota 29"), (62, 25, "Cherrygrove City / Rota 30 ao norte")),
    602: ((28, 30, "Violet City"), (47, 31, "Ginásio Pokémon de Violet / Falkner"), (44, 38, "Rota 31 a leste / Rota 36 a oeste")),
    625: ((17, 10, "Rota 29 / Cherrygrove a oeste"), (71, 12, "Rota 29 / New Bark a leste")),
    626: ((18, 21, "Rota 30 / Casa do Sr. Pokémon"),),
    627: ((20, 30, "Rota 31 / Violet City"), (51, 30, "Rota 31 / Dark Cave")),
}
OLD_WEST_CONNECTION = "630,East,0,602,West,124"
VIOLET_WEST_CONNECTION = "602,West,13,637,East,0"

NEW_MAPS = {
    682: ("Casa da vizinha de New Bark", 600),
    683: ("Casa ao sul de New Bark", 600),
    **{mid: (name, 601) for mid, (name, _, _) in CHERRYGROVE_BUSINESSES.items()},
    **{mid: (f"Casa de Cherrygrove {mid - 685}", 601) for mid in CHERRYGROVE_HOUSES},
    **{mid: (label, parent) for mid, (parent, _, label, _) in REGIONAL_INTERIORS.items()},
}
BASE_MAPS = {600, 601, 602, 625, 626, 627, 629, 637, 674, 675, 676, 681} | {
    parent for parent, _, _, _ in REGIONAL_DOORS
}
TABLES = ("@passages", "@priorities", "@terrain_tags")


def furniture(x, y, row, col, width, height, layer=2):
    return [(x + dx, y + dy, layer, tile(row + dy, col + dx))
            for dy in range(height) for dx in range(width)]


def floor_area(x, y, width, height, first, second):
    return [(x + dx, y + dy, 0, first if (dx + dy) % 2 == 0 else second)
            for dy in range(height) for dx in range(width)]


def extend_tileset(sets, source_id, name, png, chips, flags):
    """Append matching graphics, passage, priority and terrain rows."""
    w, h, rows = decode_png(png, expected_width=256)
    if h % 32 or len(chips) != len(flags):
        raise ValueError(f"Dimensões inválidas do tileset de Johto: {name}")
    used = len(chips)
    padded = (used + 7) // 8 * 8
    source = sets[source_id].attrs
    new = deepcopy(sets[source_id])
    new.attrs.update({"@id": len(sets), "@name": name.encode("ascii"),
                      "@tileset_name": name.encode("ascii")})
    first = 384 + h // 32 * 8
    for idx, field in enumerate(TABLES):
        shape, existing = table_values(source[field].data, 1)
        if shape != (first, 1, 1):
            raise ValueError(f"Tabela {field} incompatível com {name}")
        values = (*existing, *(entry[idx] for entry in flags), *(0 for _ in range(padded - used)))
        new.attrs[field].data = struct.pack("<5I", 1, len(values), 1, 1, len(values)) + struct.pack(
            f"<{len(values)}H", *values
        )
    for index in range(0, padded, 8):
        band = [*chips[index:index + 8], *([bytes(128)] * 32 for _ in range(max(0, index + 8 - used)))]
        rows.extend(b"".join(chip[y] for chip in band) for y in range(32))
    sets.append(new)
    return encode_png(w, rows), first


def rug_tiles(color, edge):
    """Nine transparent tiles forming a 3x3 oval with a woven border."""
    result = []
    for ty in range(3):
        for tx in range(3):
            chip = []
            for y in range(32):
                row = bytearray()
                for x in range(32):
                    px, py = tx * 32 + x, ty * 32 + y
                    radius = ((px - 47.5) / 46) ** 2 + ((py - 47.5) / 39) ** 2
                    if radius >= 1:
                        row.extend((0, 0, 0, 0))
                    elif radius >= 0.79:
                        row.extend((*edge, 255))
                    else:
                        grain = 8 if ((px + py) // 6 + (px - py) // 6) % 2 else 0
                        row.extend((*(value + grain for value in color), 255))
                chip.append(bytes(row))
            result.append(chip)
    return result


def prop(source_rows, tile_id):
    y, x = divmod(tile_id - 384, 8)
    return [row[x * 128:(x + 1) * 128] for row in source_rows[y * 32:y * 32 + 32]]


def style_route(maps, sets, assets, read_graphic):
    route = maps[625]
    native = sets[route.attrs["@tileset_id"]].attrs
    exterior = read_graphic("Tilesets", text(native["@tileset_name"]))
    _, _, rows = decode_png(exterior, expected_width=256)
    edge_caps = (670, 671, 678, 679)
    priority = table_values(native["@priorities"].data, 1)[1]
    name = "BLUE_JOHTO_ROUTE_EDGE"
    assets[f"Graphics/Tilesets/{name}.png"], first = extend_tileset(
        sets, route.attrs["@tileset_id"], name, exterior,
        [prop(rows, tid) for tid in edge_caps], [(15, priority[tid], 0) for tid in edge_caps]
    )
    route.attrs["@tileset_id"] = len(sets) - 1
    # The route duplicates a cropped Center and high-rise at its western edge.
    # Replace those pieces with coherent tree rows and retain the road/gate lane.
    updates = [(x, y, 1, 0) for x in range(3) for y in range(7, 12)]
    updates += [(x, y, 2, 0) for x in range(3) for y in range(7, 12)]
    for y, pair in enumerate(((656, 657), (656, 657), (664, 665), (672, 673),
                              (680, 681), (670, 671), (678, 679)), 13):
        for x in range(4):
            updates.extend(((x, y, 0, 396), (x, y, 1, pair[x % 2]), (x, y, 2, 0)))
    set_tiles(route, updates)
    (w, h, _), values = table_values(route.attrs["@data"].data, 3)
    replacements = {tid: first + idx for idx, tid in enumerate(edge_caps)}
    set_tiles(route, [(x, y, z, replacements[tid])
                      for z in (1, 2) for y in range(18, h) for x in range(w)
                      if (tid := values[x + w * (y + h * z)]) in replacements])
    # Clear the canopy only in the traversable three tiles forming the New
    # Bark seam. The forest outside that opening keeps its natural outline.
    set_tiles(maps[600], [(x, y, 1, 0) for x in range(2) for y in (27, 28)])
    # Cherrygrove's west lookout stairs need a traversable strip through
    # both side walls. Keep the stair artwork on the two center rows.
    set_tiles(maps[601], [(x, 16, z, 396 if z == 0 else 0)
                          for x in (34, 35, 36, 37) for z in range(3)])
    for mid, x, y in ((602, 0, 21), (637, 75, 8)):
        set_tiles(maps[mid], [(x, y, 1, 0)])

    # The northern shop sat behind a solid band of trees. Open a two-tile
    # path from the eastern lane before creating its entrance.
    set_tiles(maps[601], [(x, y, z, 96 if z == 0 else 0)
                          for x in (69, 70) for y in range(11, 23) for z in range(3)])
    # Remove the canopy directly in front of the isolated northeastern home.
    set_tiles(maps[601], [(57, 11, 2, 0)])


def set_door(outside, inside, name, from_id, to_id, position, sprite, entrance, exit_at):
    x, y = position
    add_event(outside, f"JH_{name}_ENTER", position,
              event_page(warp=(to_id, *entrance), sprite=sprite, touch=True))
    add_event(inside, f"JH_{name}_EXIT", exit_at,
              event_page(warp=(from_id, x, y + 1), touch=True))


def style_interiors(maps, sets, assets, read_graphic):
    home = maps[675]
    original_set = home.attrs["@tileset_id"]
    native = read_graphic("Tilesets", text(sets[original_set].attrs["@tileset_name"]))
    _, _, rows = decode_png(native, expected_width=256)
    chips = [prop(rows, tile(r, c)) for r, c in ((84, 0), (85, 0), (85, 1), (80, 0))]
    chips.extend(rug_tiles((88, 137, 174), (53, 92, 133)))
    chips.extend(rug_tiles((121, 151, 109), (79, 112, 82)))
    name = "BLUE_JOHTO_OPENING_INSIDE"
    assets[f"Graphics/Tilesets/{name}.png"], first = extend_tileset(
        sets, original_set, name, native, chips, [(0, 0, 0)] * len(chips)
    )
    tid = len(sets) - 1
    for mid in (674, 675, 676, 681):
        maps[mid].attrs["@tileset_id"] = tid
    _, teal, teal_alt, mat = (first + i for i in range(4))

    def oval(x, y, offset):
        return [(x + dx, y + dy, 1, first + offset + dy * 3 + dx)
                for dy in range(3) for dx in range(3)]

    room = maps[674]
    set_tiles(room, [(x, y, 2, 0) for x in range(2, 13) for y in range(3, 6)])
    set_tiles(room, furniture(2, 6, 275, 0, 2, 3)
              + furniture(2, 1, 280, 4, 3, 2) + furniture(8, 1, 297, 0, 1, 2)
              + furniture(10, 1, 279, 2, 2, 1) + furniture(5, 1, 198, 6, 2, 1)
              + furniture(12, 8, 270, 3, 1, 2) + oval(5, 5, 4))

    set_tiles(home, floor_area(1, 2, 14, 10, tile(88, 0), tile(88, 1)))
    set_tiles(home, [(x, y, 2, 0) for x in range(1, 15) for y in range(2, 12)
                     if (x, y) not in {(12, 8), (13, 8), (12, 9), (13, 9)}])
    set_tiles(home, furniture(2, 1, 257, 0, 4, 3) + furniture(11, 1, 251, 4, 3, 3)
              + furniture(8, 2, 297, 0, 1, 2) + oval(6, 5, 13)
              + furniture(7, 6, 275, 4, 2, 1) + furniture(6, 6, 276, 6, 1, 2)
              + furniture(9, 6, 276, 7, 1, 2)
              + furniture(1, 8, 270, 3, 1, 2) + furniture(14, 8, 270, 3, 1, 2)
              + [(7, 9, 1, mat)])

    lab = maps[676]
    set_tiles(lab, floor_area(1, 2, 18, 13, teal, teal_alt))
    set_tiles(lab, [(x, y, 2, 0) for x in range(1, 19) for y in range(2, 15)]
              + [(x, y, 1, 0) for x in range(6, 16) for y in (6, 7)])
    set_tiles(lab, furniture(3, 1, 302, 0, 2, 1) + furniture(7, 1, 305, 3, 2, 1)
              + furniture(10, 1, 301, 2, 1, 3) + furniture(15, 1, 296, 4, 2, 3)
              + furniture(3, 6, 307, 3, 2, 2) + furniture(15, 6, 307, 3, 3, 2)
              + furniture(1, 10, 270, 3, 1, 2) + furniture(18, 10, 270, 3, 1, 2)
              + [(9, 12, 1, mat)])
    for x in (7, 10, 13):
        # Place the furniture behind the ball, leaving the counter's front
        # walkable and each ball accessible from the aisle.
        set_tiles(lab, furniture(x, 6, 283, 0, 2, 1, 1))

    center = maps[681]
    set_tiles(center, [(x, y, 2, 0) for x in range(1, 19) for y in range(2, 14)])
    set_tiles(center, floor_area(1, 2, 18, 13, teal, teal_alt)
              + furniture(9, 2, 296, 6, 2, 2)
              + furniture(7, 6, 300, 0, 4, 1)
              + furniture(11, 6, 300, 1, 2, 1)
              + furniture(3, 4, 297, 0, 1, 2)
              + [(9, 13, 1, mat)])
    # Essentials recognizes the counter bit when interacting from its front.
    field = sets[tid].attrs["@passages"]
    _, values = table_values(field.data, 1)
    passage = list(values)
    for column in range(4):
        passage[tile(300, column)] |= 0x8F
    field.data = field.data[:20] + struct.pack(f"<{len(passage)}H", *passage)


def add_interiors(maps):
    town, cherry, home = (maps[mid] for mid in (600, 601, 675))
    # The blue house to the northeast matches the HGSS player home. Use its
    # existing facade opening and preserve the old south house's coordinates.
    player_door = town.attrs["@events"][1]
    player_door.attrs.update({"@x": 14, "@y": 23})
    player_door.attrs["@pages"][0].attrs["@graphic"].attrs["@character_name"] = b"doors8"
    return_warp = home.attrs["@events"][2].attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"]
    return_warp[2:4] = [14, 24]
    town.attrs["@events"][2].attrs["@pages"][0].attrs["@graphic"].attrs["@character_name"] = b"doors4"

    start, exit_at = (7, 8), (7, 9)
    houses = [(682, 600, (4, 31), "NPC_HGSS_Young_Couple_Woman"),
              (683, 600, (13, 33), "NPC_HGSS_Young_Couple_Man")]
    houses.extend((mid, 601, point, sprite) for mid, (point, sprite) in CHERRYGROVE_HOUSES.items())
    for mid, parent, point, resident in houses:
        room = deepcopy(home)
        room.attrs["@events"] = {}
        room.attrs["@bgm"] = deepcopy(maps[parent].attrs["@bgm"])
        # Ground-floor-only interiors reuse the furniture; remove the stairs.
        set_tiles(room, [(x, y, 2, 0) for x in (12, 13) for y in (8, 9)])
        name = "SILVER_HOUSE" if mid == 682 else f"HOUSE_{mid}"
        set_door(maps[parent], room, name, parent, mid, point, "doors8", start, exit_at)
        call = "neighbor" if parent == 600 else "cherrygrove_resident"
        add_event(room, f"JH_{name}_RESIDENT", (6, 8),
                  event_page(script=f"BlueJohtoPilot.{call}", sprite=resident))
        maps[mid] = room

    for mid, (_, point, sprite) in CHERRYGROVE_BUSINESSES.items():
        room = deepcopy(maps[681])
        room.attrs["@events"] = {}
        if mid == 685:
            room.attrs["@bgm"] = deepcopy(cherry.attrs["@bgm"])
            set_tiles(room, furniture(3, 2, 295, 4, 2, 5)
                      + furniture(14, 2, 295, 4, 2, 5))
            clerk, handler = "NPC_DPP_PokeMart_Man", "BlueJohtoPilot.cherrygrove_mart"
        else:
            clerk, handler = "NPC_DPP_PokeCenter_Nurse", "BlueJohtoViolet.center_clerk"
        add_event(room, f"JH_CHERRYGROVE_CLERK_{mid}", (10, 5), event_page(script=handler, sprite=clerk))
        set_door(cherry, room, f"CHERRYGROVE_{mid}", 601, mid, point, sprite, (9, 12), (9, 13))
        maps[mid] = room


def add_regional_doors(maps):
    for mid, (parent, point, _, kind) in REGIONAL_INTERIORS.items():
        template, start, exit_at, sprite = {
            "house": (682, (7, 8), (7, 9), "doors8"),
            "mart": (685, (9, 12), (9, 13), "doors4"),
            "center": (684, (9, 12), (9, 13), "doors6"),
        }[kind]
        room = deepcopy(maps[template])
        room.attrs["@events"] = {key: event for key, event in room.attrs["@events"].items()
                                  if not event.attrs["@name"].endswith(b"_EXIT")}
        if kind == "house":
            for event in room.attrs["@events"].values():
                event.attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"] = [
                    b"BlueJohtoPilot.regional_resident"]
        set_door(maps[parent], room, f"HOUSE_{mid}", parent, mid, point, sprite, start, exit_at)
        maps[mid] = room


def add_signs(maps, infos):
    edited = set()
    for mid in sorted(set(maps) & set(range(600, 674))):
        attrs = maps[mid].attrs
        # Tiles 385/388 are physical signs on the shared exterior sheet.
        # Route 29 uses the derivative with the same original tile indices.
        if attrs["@tileset_id"] not in (maps[600].attrs["@tileset_id"], maps[625].attrs["@tileset_id"]):
            continue
        (width, height, depth), tiles = table_values(attrs["@data"].data, 3)
        named = {(x, y): label for x, y, label in SIGNS.get(mid, ())}
        occupied = {(event.attrs["@x"], event.attrs["@y"]) for event in attrs["@events"].values()}
        default = text(infos[mid].attrs["@name"]).removeprefix("[Johto preview] ")
        tile_count = width * height
        for i in range(tile_count):
            if not any(tiles[i + layer * tile_count] in (385, 388) for layer in range(depth)):
                continue
            x, y = i % width, i // width
            if (x, y) in occupied:
                continue
            label = named.get((x, y), default)
            script = f"BlueJohtoPilot.sign({json.dumps(label, ensure_ascii=True)})"
            add_event(maps[mid], f"JH_SIGN_{x}_{y}", (x, y), event_page(script=script))
            edited.add(mid)
    return edited

def revise_connections(blob):
    original = OLD_WEST_CONNECTION.encode("ascii")
    if blob.count(original) != 1:
        raise ValueError("Conexão oeste de Violet não corresponde ao pacote de Johto")
    return blob.replace(original, VIOLET_WEST_CONNECTION.encode("ascii"))


def johto_metadata(maps, infos):
    rows = []
    for mid in sorted(set(maps) & {*range(600, 674), *NEW_MAPS}):
        label = text(infos[mid].attrs["@name"]).removeprefix("[Johto preview] ")
        rows += [f"[{mid:03}]", f"Name = {label}", "ShowArea = true", "SnapEdges = true", ""]
    return "\n".join(rows).encode("utf-8")


def repair_visual_layout(maps, infos, sets, assets, read_graphic):
    style_route(maps, sets, assets, read_graphic)
    style_interiors(maps, sets, assets, read_graphic)
    add_interiors(maps)
    add_regional_doors(maps)
    # The staircase beside Cherrygrove's fountain spans two offset
    # elevations. Its middle tile shares a solid cliff tile; bridge the
    # landing on either side without making the surrounding cliff walkable.
    for side, (position, landing, direction) in enumerate((
        ((36, 17), (33, 16), 4), ((34, 16), (37, 16), 6)
    )):
        page = event_page(warp=(601, *landing), touch=True)
        page.attrs["@list"][0].attrs["@parameters"][4] = direction
        add_event(maps[601], f"JH_CHERRYGROVE_STAIR_{side}", position, page)
    sign_maps = add_signs(maps, infos)
    for event_id, sprite in ((1, "doors8"), (2, "doors4"), (3, "doors6")):
        event = maps[602].attrs["@events"].get(event_id)
        if event and b"JH_VIOLET_TOWN_TO_" in event.attrs["@name"]:
            event.attrs["@pages"][0].attrs["@graphic"].attrs["@character_name"] = sprite.encode("ascii")
    # Route 32's original north edge meets trees on both maps. Use an
    # authored connection from Violet's southern trail to the Route 32 lane.
    add_event(maps[602], "JH_VIOLET_ROUTE32", (42, 44), event_page(
        script="BlueJohtoPilot.violet_south_gate(629, 7, 3, 6)", touch=True))
    add_event(maps[629], "JH_ROUTE32_VIOLET", (6, 3), event_page(
        warp=(602, 42, 43), touch=True))

    next_order = max(info.attrs["@order"] for info in infos.values()) + 1
    for order, (mid, (label, parent)) in enumerate(NEW_MAPS.items(), next_order):
        infos[mid] = ruby("RPG::MapInfo", name=label.encode("utf-8"), parent_id=parent,
                         order=order, expanded=False, scroll_x=0, scroll_y=0)

    return sign_maps


def audit_tilesets(maps, sets, read_graphic):
    """Check every Johto map's sheet, used autotile slots and tile metadata bounds."""
    checked = {}
    for mid, data in maps.items():
        key = data.attrs["@tileset_id"]
        if key not in checked:
            atlas = sets[key].attrs
            w, h = struct.unpack_from(">II", read_graphic("Tilesets", text(atlas["@tileset_name"])), 16)
            limit = 384 + (h // 32) * 8
            if w != 256 or h % 32 or any(table_values(atlas[k].data, 1)[0][0] != limit for k in TABLES):
                raise ValueError(f"Tileset {key} com dimensões ou tabelas incompatíveis")
            slots = atlas["@autotile_names"]
            for name in slots:
                if name:
                    read_graphic("Autotiles", text(name))
            checked[key] = limit, slots
        limit, slots = checked[key]
        _, tiles = table_values(data.attrs["@data"].data, 3)
        for tid in set(tiles):
            if tid >= limit or (48 <= tid < 384 and not slots[tid // 48 - 1]):
                raise ValueError(f"Mapa {mid}: tile {tid} sem correspondência no tileset {key}")
    return len(maps), len(checked)

