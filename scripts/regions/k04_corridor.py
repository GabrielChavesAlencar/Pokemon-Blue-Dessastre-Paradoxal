"""Source contract for K04; reserved destinations are not a release."""
from __future__ import annotations

MAPS = {86: "ROUTE_9", 87: "ROUTE_10", 88: "ROCK_TUNNEL_CENTER",
        90: "ROCK_TUNNEL_1F", 91: "ROCK_TUNNEL_B1F"}
NAMES = ("Route 9", "Route 10", "Rock Tunnel Pokémon Center",
         "Rock Tunnel - 1F", "Rock Tunnel - B1F")
DARK = frozenset({90, 91})
# Original directed transfers. The out-of-scope 87/7 and 87/9 lead to
# Power Plant (92) and are NOT allowed. Lavender (93) is not installed.
WARPS = {
    (87, 12): (90, 24, 7, 8), (87, 13): (90, 24, 42, 8),
    (87, 22): (88, 7, 8, 8), (88, 1): (87, 13, 31, 0),
    (90, 1): (87, 8, 30, 2), (90, 13): (91, 40, 8, 0),
    (90, 14): (91, 34, 17, 0), (90, 15): (91, 45, 33, 0),
    (90, 16): (91, 9, 8, 0), (90, 17): (87, 8, 68, 0),
    (91, 27): (90, 52, 26, 0), (91, 28): (90, 27, 18, 0),
    (91, 29): (90, 11, 7, 0), (91, 30): (90, 52, 7, 0),
}
SEAMS = ((86, "West", 0, 39, "East", 0), (87, "West", 0, 86, "East", 0))
LAVENDER_BOUNDARY = (93, "North", 0, 87, "South", 0)


def connections(mapping):
    return [[mapping[a], sa, oa, mapping[b], sb, ob]
            for a, sa, oa, b, sb, ob in SEAMS]


def verify_source(report):
    if tuple((m["id"], m["name"]) for m in report["maps"]) != tuple(zip(MAPS, NAMES)):
        raise ValueError("K04 audited source identities changed")
    rows = [r for r in report["transfers"] if r["in_scope"]]
    actual = {(r["source"], r["event"]): (r["destination"], *r["xy"], r["direction"])
              for r in rows}
    if len(rows) != len(WARPS) or actual != WARPS:
        raise ValueError("K04 source differs from the 14 audited transfers")
    seen = set(tuple(r) for r in report["connections"])
    if not {*SEAMS, LAVENDER_BOUNDARY} <= seen:
        raise ValueError("K04 source corridor or deferred Lavender boundary changed")
    dark = {m["id"] for m in report["maps"]
            if any("DarkMap = true" in r.splitlines() for r in m["metadata"])}
    if dark != DARK:
        raise ValueError("K04 source must mark only both tunnel floors dark")
