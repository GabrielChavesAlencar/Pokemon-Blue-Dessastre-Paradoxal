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


