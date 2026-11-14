"""Rustboro/Rusturf Stage 04 contracts for an ISOLATED Emerald pilot.

MapIDs, entrances, cut trees, items, trainer coordinates and encounter weights
are from the donor's pinned RMXP maps + PBS. Does not redistribute their bytes.
All data are source coordinates; the pilot remaps IDs and checks passability.
"""
from __future__ import annotations

SOURCE_MAPS_STAGE4 = {
    21: "Rustboro City",
    22: "Centro Pokémon de Rustboro",
    23: "Poké Mart de Rustboro",
    24: "Casas de Rustboro",
    25: "Escola de Treinadores de Rustboro",
    26: "Devon Corporation",
    27: "Ginásio de Rustboro",
    130: "Rota 116",
    131: "Casa dos Escavadores",
    157: "Rusturf Tunnel",
}

# Audited donor PBS:
# 104,North,110,21,South,0 ; 130,West,0,21,East,0.
OFFSET_BORDERS_STAGE4 = (
    (104, "North", 110, 21, "South", 0),
    (130, "West", 0, 21, "East", 0),
)

# Every tuple: (door event, standing tile next to door, matching door event,
#               standing tile next to matching door).
# Rustboro Gym exits into Rustboro 21: the donor's map27 Exit instead points
# to Petalburg 16 (15,8), which is wrong for this isolated pilot.
# Devon floor-to-floor warps use a single 80x20 shared atlas.
WARP_PAIRS_STAGE4 = (
    ((21, 16, 38), (21, 16, 39), (22, 8, 11), (22, 9, 10)),
    ((21, 16, 45), (21, 16, 46), (23, 5, 10), (23, 5, 9)),
    ((21, 27, 19), (21, 27, 20), (27, 7, 22), (27, 7, 21)),
    ((21, 27, 34), (21, 27, 35), (25, 7, 13), (25, 7, 12)),
    ((21, 11, 15), (21, 11, 16), (26, 7, 11), (26, 7, 10)),
    ((21, 5, 51), (21, 5, 52), (24, 4, 66), (24, 4, 65)),
    ((21, 9, 38), (21, 9, 39), (24, 7, 49), (24, 7, 48)),
    ((21, 26, 46), (21, 26, 47), (24, 26, 49), (24, 26, 48)),
    ((21, 13, 30), (21, 13, 31), (24, 8, 26), (24, 8, 25)),
    ((21, 30, 28), (21, 30, 29), (24, 29, 27), (24, 29, 26)),
    ((21, 33, 19), (21, 33, 20), (24, 29, 10), (24, 29, 9)),
    ((130, 38, 8), (130, 38, 9), (131, 6, 11), (131, 6, 10)),
    ((130, 47, 8), (130, 47, 9), (157, 9, 16), (157, 9, 15)),
    ((130, 65, 10), (130, 65, 11), (157, 23, 26), (157, 23, 25)),
    ((26, 16, 3), (26, 16, 4), (26, 43, 3), (26, 43, 4)),
    ((26, 31, 3), (26, 31, 4), (26, 58, 3), (26, 58, 4)),
)

LAND_ENCOUNTERS_STAGE4 = {
    130: (
        (20, "NINCADA", 6, 7), (20, "TAILLOW", 6, 8),
        (20, "WHISMUR", 6, 6), (28, "POOCHYENA", 6, 8),
        (10, "ABRA", 7, 7), (2, "SKITTY", 7, 8),
    ),
}
CAVE_ENCOUNTERS_STAGE4 = {157: ((100, "WHISMUR", 5, 8),)}

# (source map, x, y, Blue native type, name, Blue native *overworld* sprite,
#  historical species/level pairs, double battle)
TRAINERS_STAGE4 = (
    (27, 7, 15, "YOUNGSTER", "Josh", "trainer_YOUNGSTER",
     (("GEODUDE", 10),), False),
    (27, 5, 11, "YOUNGSTER", "Tommy", "trainer_YOUNGSTER",
     (("GEODUDE", 8), ("GEODUDE", 8)), False),
    (27, 3, 8, "HIKER", "Marc", "trainer_HIKER",
     (("GEODUDE", 8), ("GEODUDE", 8)), False),
    (130, 12, 7, "YOUNGSTER", "Joey", "trainer_YOUNGSTER",
     (("MACHOP", 9),), False),
    (130, 13, 17, "BUGCATCHER", "Jose", "trainer_BUGCATCHER",
     (("WURMPLE", 8), ("NINCADA", 8)), False),
    (130, 22, 16, "LASS", "Karen", "trainer_LASS",
     (("SHROOMISH", 9),), False),
    (130, 26, 6, "LASS", "Janice", "trainer_LASS",
     (("MARILL", 9),), False),
    (130, 28, 8, "YOUNGSTER", "Jerry", "trainer_YOUNGSTER",
     (("RALTS", 9),), False),
    (130, 33, 5, "RICHBOY", "Dawson", "trainer_YOUNGSTER",
     (("ZIGZAGOON", 8), ("POOCHYENA", 8)), False),
    (130, 33, 8, "LADY", "Sarah", "trainer_LASS",
     (("LOTAD", 8), ("ZIGZAGOON", 8)), False),
    (130, 36, 13, "YOUNGSTER", "Johnson", "trainer_YOUNGSTER",
     (("SHROOMISH", 8), ("LOTAD", 8)), False),
    (130, 36, 17, "HIKER", "Clark", "trainer_HIKER",
     (("GEODUDE", 8),), False),
    (130, 42, 13, "HIKER", "Devan", "trainer_HIKER",
     (("GEODUDE", 8), ("GEODUDE", 8)), False),
    (157, 37, 18, "HIKER", "Mike", "trainer_HIKER",
     (("GEODUDE", 16), ("GEODUDE", 16), ("MACHOP", 16)), False),
)

ROXANNE_PBS = ("BLUE_HOENN_ROXANNE", "Roxanne", 427)
ROXANNE_TEAM = (("GEODUDE", 12), ("GEODUDE", 12), ("NOSEPASS", 15))
TUNNEL_AQUA_PBS = ("BLUE_HOENN_AQUA", "Recruta", 405)
TUNNEL_AQUA_TEAM = (("POOCHYENA", 11),)

# IDs/positions verified against donor map event source, without changing
# native Blue item definitions. All are individual, non-repeatable prizes.
# map, x, y, flag key, Essentials item, visible?
PICKUPS_STAGE4 = (
    (21, 36, 51, "RUSTBORO_X_DEFENSE", "XDEFENSE", True),
    (130, 10, 17, "ROUTE116_REPEL", "REPEL", True),
    (130, 19, 6, "ROUTE116_ETHER", "ETHER", True),
    (130, 22, 9, "ROUTE116_HIDDEN_SUPER_POTION", "SUPERPOTION", False),
    (130, 34, 7, "ROUTE116_POTION", "POTION", True),
    (130, 55, 12, "ROUTE116_X_SP_ATK", "XSPATK", True),
    (130, 70, 13, "ROUTE116_BLACKGLASSES", "BLACKGLASSES", False),
    (130, 80, 8, "ROUTE116_HP_UP", "HPUP", True),
    (157, 8, 6, "RUSTURF_POKE_BALL", "POKEBALL", True),
    (157, 35, 7, "RUSTURF_MAX_ETHER", "MAXETHER", True),
)

# Event coordinates are authentic; descriptions are freshly written in PT-BR.
# map, x, y, script-key, informational Portuguese text
SIGNS_STAGE4 = (
    (21, 20, 49, "RUSTBORO_CITY", "Rustboro: cidade de ciência, escolas e ginásios."),
    (21, 23, 19, "RUSTBORO_GYM", "Ginásio de Rustboro. Líder Roxanne, tipo Pedra."),
    (21, 17, 20, "DEVON_CORP", "Devon Corporation: pesquisa e tecnologia."),
    (21, 25, 35, "TRAINER_SCHOOL", "Escola de Treinadores: aprenda sobre tipos e condições."),
    (21, 12, 38, "CUTTER_HOUSE", "Casa do especialista na técnica Cut."),
    (21, 30, 8, "RUSTURF_TUNNEL", "Túnel Rusturf: siga pela Rota 116 ao leste."),
    (130, 16, 12, "ROUTE116_TIPS", "Dica: use a Bolsa para organizar os itens."),
    (130, 29, 10, "ROUTE116_TRAINERS", "Dica: treine seus Pokémon antes de explorar o túnel."),
    (130, 40, 9, "TUNNELERS_HOUSE", "Casa dos Escavadores."),
    (130, 48, 9, "RUSTURF_ENTRANCE", "Entrada do Túnel Rusturf."),
)

# map, x, y, native sprite fallback, Ruby hook
NPCS_STAGE4 = (
    (22, 9, 4, "NPC_DPP_PokeCenter_Nurse", "BlueHoennPilot.heal"),
    (23, 3, 5, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.mart"),
    (24, 9, 45, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.cutter"),
    (25, 7, 5, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.teacher"),
    (26, 59, 7, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.devon_employee"),
    (26, 73, 7, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.mr_stone"),
    (130, 46, 9, "trainer_FISHERMAN", "BlueHoennPilot.briney_route116"),
    (130, 46, 11, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.devon_route116"),
    (157, 20, 9, "trainer_FISHERMAN", "BlueHoennPilot.peeko"),
    (131, 5, 8, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.tunnelers"),
)

CUT_TREES_STAGE4 = (
    (130, 21, 6), (130, 24, 9), (130, 28, 11),
    (130, 30, 5), (130, 32, 10),
)
RUSTBORO_THEFT_TRIGGERS = ((21, 29, 10), (21, 30, 12), (21, 31, 10))
TUNNEL_AQUA_EVENT = (157, 20, 10)
ROXANNE_EVENT = (27, 7, 4)
TUNNEL_VERDANTURF_GATE = (157, 34, 22)
