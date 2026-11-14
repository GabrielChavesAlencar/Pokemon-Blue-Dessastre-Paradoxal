"""Build the HGSS-inspired opening maps using installed tile art and local saves' map IDs."""

from __future__ import annotations

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
NEW_MAPS = {
    682: ("Casa da vizinha de New Bark", 600),
    683: ("Casa ao sul de New Bark", 600),
    **{mid: (name, 601) for mid, (name, _, _) in CHERRYGROVE_BUSINESSES.items()},
    **{mid: (f"Casa de Cherrygrove {mid - 685}", 601) for mid in CHERRYGROVE_HOUSES},
}
BASE_MAPS = {600, 601, 625, 674, 675, 676, 681}
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
    for y, pair in enumerate(((680, 681), (656, 657), (664, 665), (672, 673),
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
    tan, teal, teal_alt, mat = (first + i for i in range(4))

    def oval(x, y, offset):
        return [(x + dx, y + dy, 1, first + offset + dy * 3 + dx)
                for dy in range(3) for dx in range(3)]

    room = maps[674]
    set_tiles(room, [(x, y, 2, 0) for x in range(2, 13) for y in range(3, 6)])
    set_tiles(room, furniture(2, 6, 275, 0, 2, 3)
              + furniture(2, 1, 280, 4, 3, 2) + furniture(8, 1, 297, 0, 1, 2)
              + furniture(10, 1, 279, 2, 2, 1) + furniture(5, 1, 198, 6, 2, 1)
              + furniture(12, 8, 270, 3, 1, 2) + oval(5, 5, 4))

    set_tiles(home, floor_area(1, 2, 14, 10, tan, tile(85, 2)))
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
    set_tiles(center, [(3, 3, 2, 0), (15, 3, 2, 0)])
    set_tiles(center, floor_area(1, 2, 18, 13, tan, tile(85, 2))
              + furniture(9, 2, 296, 6, 2, 2)
              + furniture(8, 6, 300, 0, 4, 1)
              + furniture(3, 4, 297, 0, 1, 2)
              + [(9, 13, 1, mat)])
    # Interaction across the center counter also works from its front.
    # The nurse stands in its central opening.
    set_tiles(center, [(10, 6, 2, 0)])


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


def repair_visual_layout(maps, infos, sets, assets, read_graphic):
    style_route(maps, sets, assets, read_graphic)
    style_interiors(maps, sets, assets, read_graphic)
    add_interiors(maps)
    next_order = max(info.attrs["@order"] for info in infos.values()) + 1
    for order, (mid, (label, parent)) in enumerate(NEW_MAPS.items(), next_order):
        infos[mid] = ruby("RPG::MapInfo", name=label.encode("utf-8"), parent_id=parent,
                         order=order, expanded=False, scroll_x=0, scroll_y=0)


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

