"""Fail-closed Cerulean city door check for installed and packaged RXDATA."""
from server.ruby_marshal import loads, RubyObject

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
    try:
        city = loads(native)
    except (ValueError, TypeError, IndexError, KeyError) as error:
        raise ValueError("Cerulean door gate: invalid city RXDATA") from error
    events = city.attrs.get("@events") if isinstance(city, RubyObject) else None
    if not isinstance(events, dict):
        raise ValueError("Cerulean door gate: city RXDATA has no event table")
    verify_cerulean_police(events)
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

def verify_cerulean_police(events: dict) -> None:
    """Both source guard pages must be native even before any Ruby hook."""
    for event_id, active_index in ((13, 0), (25, 1)):
        event = events.get(event_id)
        pages = event.attrs.get("@pages", []) if isinstance(event, RubyObject) else []
        if len(pages) != 2:
            raise ValueError(f"Cerulean police {event_id}: expected two native pages")
        for index, page in enumerate(pages):
            attrs = page.attrs
            graphic = attrs["@graphic"].attrs
            condition = attrs["@condition"].attrs
            commands = attrs["@list"]
            codes = [op.attrs["@code"] for op in commands]
            active = index == active_index
            if (attrs["@trigger"] != 0 or bool(graphic["@character_name"]) != active
                    or bool(attrs["@through"]) == active
                    or bool(condition.get("@self_switch_valid")) != bool(index)
                    or (index and condition.get("@self_switch_ch") not in ("A", b"A"))
                    or codes != ([101, 0] if active else [0])):
                raise ValueError(f"Cerulean police {event_id}: unsafe or incorrect page {index}")
            if active:
                params = commands[0].attrs["@parameters"]
                if len(params) != 1 or not isinstance(params[0], (bytes, str)) or not params[0].strip():
                    raise ValueError(f"Cerulean police {event_id}: missing native dialogue")
