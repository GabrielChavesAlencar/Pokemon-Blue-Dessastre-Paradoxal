"""Rebuild the confirmed Sootopolis ice cells without donor switches or scripts."""

from server.ruby_marshal import text
from build_johto_events import command, event_page

MAP_ID = 87


def _fall_offset(pages):
    """Recognize the donor's self-switch A -> break -> local basement pattern."""
    if len(pages) != 3:
        return None
    attrs = [page.attrs for page in pages]
    for i, (page, switch) in enumerate(zip(attrs, (None, "A", "B"))):
        condition = page["@condition"].attrs
        if (page["@trigger"] != (0 if i == 2 else 1) or not page["@through"] or
                any(condition.get(key) for key in (
                    "@switch1_valid", "@switch2_valid", "@variable_valid",
                    "@item_valid", "@actor_valid")) or
                bool(condition.get("@self_switch_valid")) != bool(switch) or
                switch and text(condition["@self_switch_ch"]) != switch):
            return None
    first = [(c.attrs["@code"], c.attrs["@parameters"]) for c in attrs[0]["@list"]]
    damaged = [(c.attrs["@code"], c.attrs["@parameters"]) for c in attrs[1]["@list"]]
    last = [c.attrs["@code"] for c in attrs[2]["@list"]]
    needed = [(122, [1, 1, 0, 7, 0]), (122, [2, 2, 0, 6, -1, 0]),
              (122, [3, 3, 0, 6, -1, 1]), (122, [2, 2, 1, 0, 24]),
              (201, [1, 1, 2, 3, 2, 1])]
    if (not first or first[0] != (123, [b"A", 0]) or not damaged or
            damaged[0] != (123, [b"B", 0]) or
            [c for c in damaged if c[0] in (122, 201)] != needed or last != [0]):
        return None
    graphics = [page["@graphic"].attrs for page in attrs]
    if any(g["@character_name"] for g in graphics):
        return None
    if [g["@tile_id"] for g in graphics] != [0, 1006, 998]:
        return None
    return 24


def install_sootopolis_ice(original, world, tileset, mapped_id, open_tile, append_event):
    """Keep old IDs and omit any cell whose return or landing is uncertain."""
    events = world.attrs["@events"]
    occupied = {(event.attrs["@x"], event.attrs["@y"]): event for event in events.values()}
    results = {"installed": [], "pending": []}
    # Never add a fall before confirming the two real ladder connections.
    def existing_ladder(x, y, dx, dy):
        event = occupied.get((x, y))
        if not event:
            return False
        target = f"BlueHoennPilot.stage10_transfer(87,87,{dx},{dy})".encode("ascii")
        return any(c.attrs["@code"] == 355 and c.attrs["@parameters"] == [target]
                   for page in event.attrs["@pages"] for c in page.attrs["@list"])

    ladder = existing_ladder(13, 24, 38, 24) and existing_ladder(38, 24, 13, 24)
    for source_id, event in original.items():
        attrs = event.attrs
        if text(attrs["@name"]) != "Ice Floor Puzzle":
            continue
        x, y = attrs["@x"], attrs["@y"]
        offset = _fall_offset(attrs["@pages"])
        entry = {"source_event_id": source_id, "xy": [x, y]}
        reason = None
        if not offset:
            reason = "unrecognized_source_pages"
        elif not ladder:
            reason = "basement_return_unverified"
        elif (x, y) in occupied or (x + offset, y) in occupied:
            reason = "event_overlap"
        elif not open_tile(world, tileset, x, y) or not open_tile(world, tileset, x + offset, y):
            reason = "blocked_floor_or_landing"
        if reason:
            results["pending"].append({**entry, "reason": reason})
            continue
        # Repeated entry steps trigger pages; interacting from the next tile
        # does nothing. The switches belong to the generated Hoenn event only.
        first = event_page(script="nil", touch=True)
        eid = append_event(world, f"HN_IMP2_Ice_{source_id}", x, y, first)
        first.attrs["@list"] = [
            command(355, f"BlueHoennPilot.crack_ice({eid},{x},{y})".encode("ascii")), command(0)]
        cracked = event_page(script="nil", touch=True)
        cracked.attrs["@condition"].attrs["@self_switch_valid"] = True
        cracked.attrs["@graphic"].attrs["@tile_id"] = 1006
        cracked.attrs["@list"] = [
            command(355, f"BlueHoennPilot.fall_through_ice({eid},{x},{y},{x+offset})".encode("ascii")),
            command(0)]
        gap = event_page(script="nil", touch=True)
        gap.attrs["@condition"].attrs.update({"@self_switch_valid": True, "@self_switch_ch": b"B"})
        gap.attrs["@graphic"].attrs["@tile_id"] = 998
        gap.attrs["@list"] = cracked.attrs["@list"]
        events[eid].attrs["@pages"].extend((cracked, gap))
        results["installed"].append({**entry, "final_map_id": mapped_id,
                                     "final_event_id": eid, "landing": [x + offset, y]})
    return results
