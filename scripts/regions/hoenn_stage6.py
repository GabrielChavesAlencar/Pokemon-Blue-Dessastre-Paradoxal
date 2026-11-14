"""Stage 06 — Route 110, Mauville, Wattson and optional Cycling Road.

SOURCE MapIDs and anchor coordinates were audited against the pinned
The Pokémon World Project - Hoenn RXDATA/PBS (revision recorded in
pilot_hoenn.py). This catalog is original authored integration data;
it DOES NOT contain or redistribute the donor's maps/assets/dialogues.
All source IDs are remapped inside a disposable isolated Blue copy.
"""
from __future__ import annotations

SOURCE_MAPS_STAGE6 = {
    41: "Mauville City",
    42: "Centro Pokémon de Mauville",
    43: "Poké Mart de Mauville",
    44: "Casas de Mauville",
    45: "Rydel's Cycles",
    46: "Mauville Game Corner",
    47: "Ginásio de Mauville",
    113: "Rota 110",
    114: "Cycling Road (Rota 110-C)",
    115: "Portaria da Cycling Road",
}

# Both borders occur literally in PBS/map_connections.txt at pinned HEAD.
OFFSET_BORDERS_STAGE6 = (
    (113, "South", 0, 32, "North", 0),  # Route 110 / Slateport
    (113, "North", 0, 41, "South", 0),  # Route 110 / Mauville
)

# Donor source doorway/exit positions with adjacent standing cells.
# Cycling Road's gated right-hand doors are handled by CYCLE_TRANSFERS;
# including them as unconditional warps would bypass the bicycle check.
WARP_PAIRS_STAGE6 = (
    ((41, 22, 5), (41, 22, 6), (42, 8, 11), (42, 9, 10)),
    ((41, 23, 14), (41, 23, 15), (43, 5, 10), (43, 5, 9)),
    ((41, 19, 14), (41, 19, 15), (44, 5, 11), (44, 5, 10)),
    ((41, 32, 14), (41, 32, 15), (44, 23, 10), (44, 23, 9)),
    ((41, 35, 5), (41, 35, 6), (45, 5, 11), (45, 5, 10)),
    ((41, 8, 13), (41, 8, 14), (46, 13, 13), (46, 13, 12)),
    ((41, 8, 5), (41, 8, 6), (47, 6, 23), (47, 6, 22)),
    ((113, 15, 16), (113, 15, 17), (115, 3, 8), (115, 3, 7)),
    ((113, 16, 88), (113, 16, 89), (115, 3, 22), (115, 3, 21)),
)

# (source MapID, event x,y, landing x,y, destination MapID, destination x,y)
# Optional cycling route is never an unconditional warp.
CYCLE_TRANSFERS_STAGE6 = (
    (115, 14, 8, 14, 7, 114, 18, 16),    # gate north -> cycle road
    (115, 14, 22, 14, 21, 114, 19, 88),  # gate south -> cycle road
    (114, 18, 16, 18, 17, 115, 14, 7),   # bike route -> north office
    (114, 19, 88, 19, 89, 115, 14, 21),  # bike route -> south office
)

# Original Route110 donor weights sum to 200, because they are multi-slot
# relative weights, not a 100%-normalized distribution. Re-expressed for
# the isolated Blue encounter PBS without changing the seven species:
# 60,40,30,20,20,15,15 -> 30,20,15,10,10,8,7.
LAND_ENCOUNTERS_STAGE6 = {
    113: (
        (30, "ELECTRIKE", 12, 13),
        (20, "POOCHYENA", 12, 12),
        (15, "GULPIN", 12, 13),
        (10, "ODDISH", 13, 13),
        (10, "WINGULL", 12, 12),
        (8, "PLUSLE", 13, 13),
        (7, "MINUN", 13, 13),
    ),
}

# Only teams whose source event and PBS were both confirmed. Field level
# scaling remains owned by Blue/Decades; these are historical base levels.
# source map, x,y, native Blue type, name, native overworld sprite, party, double
TRAINERS_STAGE6 = (
    (113, 3, 39, "YOUNGSTER", "Edward", "trainer_YOUNGSTER", (("ABRA", 15),), False),
    (113, 34, 40, "RICHBOY", "Edwin", "trainer_YOUNGSTER", (("LOMBRE", 14), ("NUZLEAF", 14)), False),
    (113, 36, 40, "YOUNGSTER", "Joseph", "trainer_YOUNGSTER", (("ELECTRIKE", 14), ("VOLTORB", 14)), False),
    (113, 33, 69, "YOUNGSTER", "Timmy", "trainer_YOUNGSTER", (("ARON", 15), ("ELECTRIKE", 13)), False),
    (113, 33, 15, "LASS", "Jaclyn", "trainer_LASS", (("ABRA", 16),), False),
    (113, 10, 19, "FISHERMAN", "Dale", "trainer_FISHERMAN", (("TENTACOOL", 11), ("WAILMER", 14), ("TENTACOOL", 11), ("WAILMER", 14)), False),
    (113, 7, 76, "YOUNGSTER", "Kaleb", "trainer_YOUNGSTER", (("MINUN", 14), ("PLUSLE", 14)), False),
    (113, 10, 76, "LASS", "Isabel", "trainer_LASS", (("PLUSLE", 14), ("MINUN", 14)), False),
    (114, 19, 31, "YOUNGSTER", "Anthony", "trainer_YOUNGSTER", (("MAGNEMITE", 14), ("MAGNEMITE", 14), ("MAGNEMITE", 16)), False),
    (114, 30, 31, "LASS", "Abigail", "trainer_LASS", (("MAGNEMITE", 16),), False),
    (114, 16, 55, "YOUNGSTER", "Benjamin", "trainer_YOUNGSTER", (("MAGNEMITE", 16),), False),
    (114, 16, 73, "LASS", "Jasmine", "trainer_LASS", (("MAGNEMITE", 14), ("MAGNEMITE", 14), ("VOLTORB", 6)), False),
    (114, 21, 78, "YOUNGSTER", "Jacob", "trainer_YOUNGSTER", (("VOLTORB", 6), ("VOLTORB", 6), ("MAGNEMITE", 14)), False),
    (114, 15, 39, "LASS", "Alyssa", "trainer_LASS", (("MAGNEMITE", 15),), False),
    (47, 3, 18, "LASS", "Vivian", "trainer_LASS", (("MEDITITE", 17), ("MEDITITE", 17)), False),
    (47, 3, 15, "YOUNGSTER", "Kirk", "trainer_YOUNGSTER", (("ELECTRIKE", 17), ("VOLTORB", 17)), False),
    (47, 7, 12, "YOUNGSTER", "Ben", "trainer_YOUNGSTER", (("ZIGZAGOON", 17), ("GULPIN", 17)), False),
    (47, 9, 12, "BUGCATCHER", "Angelo", "trainer_BUGCATCHER", (("ILLUMISE", 17), ("VOLBEAT", 17)), False),
    (47, 9, 10, "YOUNGSTER", "Shawn", "trainer_YOUNGSTER", (("VOLTORB", 17), ("MAGNEMITE", 17)), False),
)

WATTSON_PBS = ("BLUE_HOENN_WATTSON", "Wattson", 647)
WATTSON_TEAM = (
    ("VOLTORB", 20), ("ELECTRIKE", 20), ("MAGNETON", 22), ("MANECTRIC", 24),
)
WALLY_PBS = ("BLUE_HOENN_WALLY", "Wally", 641)
WALLY_TEAM = (("RALTS", 16),)

# Rival 110: complete 3-Pokémon teams in pinned RSE donor (starter evolution
# has type advantage over the player's starter).
RIVAL_110_TEAMS = {
    "TREECKO": (610, (("WINGULL", 18), ("LOMBRE", 18), ("COMBUSKEN", 20))),
    "TORCHIC": (611, (("LOMBRE", 18), ("SLUGMA", 18), ("MARSHTOMP", 20))),
    "MUDKIP": (612, (("SLUGMA", 18), ("WINGULL", 18), ("GROVYLE", 20))),
}
RIVAL_110_EVENT = (113, 34, 54)
RIVAL_110_TRIGGERS = ((113, 33, 56), (113, 34, 56), (113, 35, 56))
WALLY_EVENT = (41, 8, 6)
WALLY_UNCLE_EVENT = (41, 9, 6)
WATTSON_EVENT = (47, 7, 4)
RYDEL_EVENT = (45, 4, 7)

# Donor Electric Gate graphics: original character names, NO asset binaries.
# If they're missing from private Blue game, generator must mark fallback
# art as not visually approved; exact barrier collision needs Game.exe QA.
GYM_GATES_STAGE6 = (
    (47, 5, 15, "pink", "V"), (47, 6, 13, "pink", "H"),
    (47, 9, 13, "pink", "H"), (47, 6, 16, "blue", "H"),
    (47, 3, 13, "blue", "H"), (47, 8, 12, "blue", "V"),
    (47, 6, 9, "blue", "H"),
)
GYM_SWITCHES_STAGE6 = (
    (47, 2, 17), (47, 6, 14), (47, 5, 11), (47, 10, 11),
)

NPCS_STAGE6 = (
    (42, 9, 4, "NPC_DPP_PokeCenter_Nurse", "BlueHoennPilot.heal"),
    (43, 3, 5, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.mart"),
    (44, 24, 6, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.rock_smash_teacher"),
    (45, 4, 7, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.rydel_bikes"),
    (41, 9, 6, "trainer_YOUNGSTER", "BlueHoennPilot.wally_uncle_mauville"),
)

PICKUPS_STAGE6 = (
    # Exact items and coordinates confirmed from the original Map041/113
    # pbItemBall commands. Each event has a one-time Hoenn self-switch.
    (41, 28, 19, "MAUVILLE_X_SPEED", "XSPEED", True),
    (113, 30, 69, "ROUTE110_DIRE_HIT", "DIREHIT", True),
    (113, 26, 47, "ROUTE110_RARE_CANDY", "RARECANDY", True),
    (113, 6, 38, "ROUTE110_ELIXIR", "ELIXIR", True),
    (113, 37, 67, "ROUTE110_HIDDEN_FULL_HEAL", "FULLHEAL", False),
    (113, 33, 45, "ROUTE110_HIDDEN_GREAT_BALL", "GREATBALL", False),
    (113, 35, 39, "ROUTE110_HIDDEN_REVIVE", "REVIVE", False),
)

SIGNS_STAGE6 = (
    (41, 19, 7, "MAUVILLE", "Mauville: cidade dos encontros e da eletricidade."),
    (41, 11, 6, "MAUVILLE_GYM", "Ginásio Mauville. Líder Wattson, tipo Elétrico."),
    (41, 33, 6, "RYDEL", "Rydel's Cycles: Mach Bike e Acro Bike disponíveis."),
    (113, 14, 88, "CYCLING_SIGN", "Cycling Road: a bicicleta é obrigatória."),
    (113, 13, 16, "CYCLING_NORTH_SIGN", "Cycling Road. Entrada norte."),
    (113, 8, 67, "TRICK_HOUSE", "Trick House: conteúdo em preparação."),
    (113, 10, 94, "SLATEPORT_DIRECTION", "Slateport fica ao sul."),
    (113, 3, 17, "MAUVILLE_DIRECTION", "Mauville fica ao norte."),
)

# North of Mauville to Route 111 and east to Route 118 are not in this stage.
# The gate blocks those map exits without pretending they are playable.
MAUVILLE_FUTURE_GATES = ((41, 10, 0), (41, 11, 0), (41, 39, 11), (41, 39, 12))
