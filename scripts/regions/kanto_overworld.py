"""Audited, source-grounded Kanto overworld events (no foreign Ruby execution).

The map importer reuses original event coordinates, graphic and EventID, but
generates safe Blue callbacks. Nothing here imports quest state, conditional
switches, trainer battles, or arbitrary scripts from the FRLG source.
"""
from __future__ import annotations

import copy
import re
from server.ruby_marshal import text

ITEM_MARKER = re.compile(r"(?i)^Item:([A-Z0-9_]+)(?:\s*[xX]\s*(\d+))?$")
ITEM_SCRIPT = re.compile(r"^pbItemBall\(\s*:([A-Za-z0-9_]+)(?:\s*,\s*(\d+))?\s*\)$")
LITERAL_MESSAGE = re.compile(r'^pbMessage\(_INTL\("(?:(?:\\.)|[^"\\])*"\)\)$')


class MissingActorGraphic(ValueError):
    """An optional overworld actor references a PNG not shipped with FRLG/Blue."""


def base_page(event):
    if not event.attrs["@pages"]:
        return None
    page = event.attrs["@pages"][0].attrs
    if any(v for k, v in page["@condition"].attrs.items() if k.endswith("_valid")):
        return None
    return page


def source_item_ball(event):
    """Return an exact original (item ID, quantity) from item-ball metadata."""
    page = base_page(event)
    if page is None or page["@trigger"] != 0:
        return None
    marker = ITEM_MARKER.fullmatch(text(event.attrs["@name"]).strip())
    name_item = (marker[1].upper(), int(marker[2] or 1)) if marker else None
    scripts = []
    for op in page["@list"]:
        code, params = op.attrs["@code"], op.attrs["@parameters"]
        raw = None
        if code == 111 and len(params) > 1 and params[0] == 12:
            raw = params[1]
        elif code == 355 and params:
            raw = params[0]
        if raw is not None:
            match = ITEM_SCRIPT.fullmatch(text(raw).strip())
            if match:
                scripts.append((match[1].upper(), int(match[2] or 1)))
    if len(scripts) > 1 or (scripts and name_item and scripts[0] != name_item):
        return None
    item = scripts[0] if scripts else name_item
    if not item or not 1 <= item[1] <= 99:
        return None
    # Never replace an original transfer, trainer, receipt or custom quest.
    codes = {op.attrs["@code"] for op in page["@list"]}
    if codes - {0, 111, 123, 411, 412, 108, 408, 355}:
        return None
    if any(op.attrs["@code"] == 111 and not (
            len(op.attrs["@parameters"]) > 1 and
            op.attrs["@parameters"][0] == 12 and
            ITEM_SCRIPT.fullmatch(text(op.attrs["@parameters"][1]).strip()))
           for op in page["@list"]):
        return None
    if any(op.attrs["@code"] == 355 and op.attrs["@parameters"] and
           not ITEM_SCRIPT.fullmatch(text(op.attrs["@parameters"][0]).strip())
           for op in page["@list"]):
        return None
    return item


def source_obstacle(event):
    """Recognize native Essentials obstacle marker names, not inferred tiles."""
    page = base_page(event)
    if page is None:
        return None
    name = text(event.attrs["@name"]).lower()
    # The audited FRLG source labels trees "Cut Tree" (with a space), but
    # Essentials' hidden move and erasure handlers require /cuttree/i.
    marker = re.sub(r"[\s_\-]+", "", name)
    if "cuttree" in marker:
        return "cut"
    if "strengthboulder" in name:
        return "strength"
    if "smashrock" in name:
        return "rock_smash"
    return None


def source_npc_dialogue(event):
    """Allow read-only literal talk, no choices, scripts, switches or rewards."""
    page = base_page(event)
    if page is None or page["@trigger"] != 0:
        return None
    if not page["@graphic"].attrs["@character_name"]:
        return None
    name = text(event.attrs["@name"])
    if re.search(r"(?i)(Trainer\(|Sight\(|Item:|SmashRock|StrengthBoulder|CutTree)", name):
        return None
    commands = page["@list"]
    codes = {row.attrs["@code"] for row in commands}
    if codes <= {0, 101, 401, 108, 408} and (101 in codes or 401 in codes):
        return [copy.deepcopy(row) for row in commands if row.attrs["@code"] in (101, 401)]
    literal = [row for row in commands if row.attrs["@code"] == 355]
    if literal and codes <= {0, 355, 108, 408} and all(
        row.attrs["@parameters"] and
        LITERAL_MESSAGE.fullmatch(text(row.attrs["@parameters"][0]))
        for row in literal
    ):
        return [copy.deepcopy(row) for row in literal]
    return None


def adapt_source_field_event(event, source_id, event_id, catalogue_items,
                             actor, new_event, command, if_scene):
    """Convert strictly approved events, preserving original EventID/XY."""
    item = source_item_ball(event)
    obstacle = source_obstacle(event) if not item else None
    dialogue = source_npc_dialogue(event) if not item and not obstacle else None
    if not item and not obstacle and not dialogue:
        return None
    graphic = event.attrs["@pages"][0].attrs["@graphic"]
    filename = graphic.attrs["@character_name"]
    character = actor(event) if filename else b""
    if item:
        symbol, quantity = item
        if symbol not in catalogue_items:
            return None
        key = f"KANTO_{source_id:03d}_{event_id:03d}"
        callback = f'BlueKantoPilot.pickup(:{symbol}, "{key}", {event_id}, {quantity})'
        converted = new_event(event, [command(355, callback.encode())], 0, character)
        converted.attrs["@pages"][0].attrs["@graphic"] = copy.deepcopy(graphic)
        # Hidden ground pickups must retain the source walk-over collision,
        # whereas visible balls stay solid until collected.
        converted.attrs["@pages"][0].attrs["@through"] = event.attrs["@pages"][0].attrs["@through"]
        if filename:
            converted.attrs["@pages"][0].attrs["@graphic"].attrs["@character_name"] = character
        hidden = copy.deepcopy(converted.attrs["@pages"][0])
        hidden.attrs["@condition"].attrs.update({
            "@self_switch_valid": True, "@self_switch_ch": b"A",
        })
        hidden.attrs["@graphic"].attrs.update({"@character_name": b"", "@tile_id": 0})
        hidden.attrs.update({"@through": True, "@trigger": 0,
                             "@list": [command(0)]})
        converted.attrs["@pages"].append(hidden)
        return converted, {"kind": "item", "item": symbol, "quantity": quantity}
    if obstacle:
        if obstacle == "cut":
            # Native Essentials Cut honors the Kanto Cascade badge, HM and
            # party move. The v21.1 eraser must receive the facing event.
            commands, trigger = if_scene(b"pbCut", [
                command(355, b"pbSmashEvent(get_self)", indent=1),
            ]), 0
        elif obstacle == "strength":
            commands, trigger = [command(355, b"pbPushThisBoulder")], 1
        else:
            commands, trigger = if_scene(b"pbRockSmash", [
                command(355, b"pbSmashThisEvent", indent=1),
                command(355, b"pbRockSmashRandomEncounter", indent=1),
            ]), 0
        converted = new_event(event, commands, trigger, character)
        converted.attrs["@pages"][0].attrs["@graphic"] = copy.deepcopy(graphic)
        if filename:
            converted.attrs["@pages"][0].attrs["@graphic"].attrs["@character_name"] = character
        converted.attrs["@pages"][0].attrs["@through"] = False
        if obstacle == "cut":
            # Source EventID/coordinates/graphics stay unchanged. Only the
            # runtime event NAME must satisfy Essentials' native /cuttree/i.
            converted.attrs["@name"] = b"CutTree"
        return converted, {"kind": obstacle}
    return new_event(event, dialogue, 0, character), {"kind": "npc_dialogue"}


def safely_adapt_source_field_event(event, source_id, event_id, catalogue_items,
                                    actor, new_event, command, if_scene):
    """Missing *optional* NPC art must not prevent the entire Kanto pilot boot.

    Do not suppress other failures: source quest/story events still use the
    strict actor() path in the caller, and unknown conversion errors surface.
    """
    try:
        adapted = adapt_source_field_event(
            event, source_id, event_id, catalogue_items, actor,
            new_event, command, if_scene)
        return adapted, None
    except MissingActorGraphic as error:
        return None, str(error)
