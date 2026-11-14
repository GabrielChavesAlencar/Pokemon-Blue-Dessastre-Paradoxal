"""Audited Emerald reference anchors for an ISOLATED Hoenn stage-3 pilot.

All map IDs and event coordinates below come from donor RXDATA at the pinned
source commit. They are source coordinates, not installed Blue IDs. The pilot
must still validate passability, native PBS types/sprites and local Game.exe.
No donor scripts, copyrighted graphics, music or binary maps are checked in.
"""
from __future__ import annotations

SOURCE_MAPS_STAGE3 = {
    16: "Petalburg City",
    17: "Centro Pokémon de Petalburg",
    18: "Poké Mart de Petalburg",
    19: "Casas de Petalburg",
    20: "Ginásio de Petalburg",
    104: "Rota 104",
    105: "Casa de Mr. Briney",
    106: "Pretty Petal Flower Shop",
    156: "Petalburg Woods",
}

# PBS connection source: 102,West,0,16,East,10 and 104,East,50,16,West,0
OFFSET_BORDERS = (
    (102, "West", 0, 16, "East", 10),
    (104, "East", 50, 16, "West", 0),
)

# For each door: (outside event, outside return standing cell,
#                 inside event, inside return standing cell).
# The three woods entrance EVENTS match the donor source. The donor's
# return arrival x=5..32 on Route 104 is blocked/unreachable in the pinned
# atlas. This isolated pilot intentionally chooses passable cells immediately
# south of the matching entrance (x=115..142); Game.exe still needs QA.
WARP_PAIRS_STAGE3 = (
    ((16, 20, 16), (16, 20, 17), (17, 8, 11), (17, 9, 10)),
    ((16, 25, 12), (16, 25, 13), (18, 5, 10), (18, 5, 9)),
    ((16, 7, 5), (16, 7, 6), (19, 41, 10), (19, 41, 9)),
    ((16, 20, 24), (16, 20, 25), (19, 23, 10), (19, 23, 9)),
    ((16, 10, 19), (16, 10, 20), (19, 5, 11), (19, 5, 10)),
    ((16, 15, 8), (16, 15, 9), (20, 6, 26), (20, 6, 25)),
    ((104, 127, 50), (104, 127, 51), (105, 7, 11), (105, 7, 10)),
    ((104, 115, 18), (104, 115, 19), (106, 4, 11), (106, 4, 10)),
    ((104, 120, 38), (104, 120, 39), (156, 20, 39), (156, 20, 38)),
    ((104, 142, 42), (104, 142, 43), (156, 40, 39), (156, 40, 38)),
    ((104, 120, 30), (104, 120, 31), (156, 18, 6), (156, 18, 7)),
)

# Percentages + base levels are Emerald data ONLY; Blue battle scaling wins.
LAND_ENCOUNTERS_STAGE3 = {
    104: (
        (40, "POOCHYENA", 4, 5), (20, "MARILL", 4, 5),
        (20, "WURMPLE", 4, 4), (10, "TAILLOW", 4, 5),
        (10, "WINGULL", 3, 5),
    ),
    156: (
        (25, "WURMPLE", 5, 6), (30, "POOCHYENA", 5, 6),
        (15, "SHROOMISH", 5, 6), (10, "CASCOON", 5, 5),
        (10, "SILCOON", 5, 5), (5, "SLAKOTH", 5, 6),
        (5, "TAILLOW", 5, 6),
    ),
}

# (source map, x, y, native trainer type, name, character sprite, base party, double)
TRAINERS_STAGE3 = (
    (104, 128, 67, "YOUNGSTER", "Billy", "trainer_YOUNGSTER",
     (("ZIGZAGOON", 5), ("SEEDOT", 7)), False),
    (104, 125, 59, "FISHERMAN", "Darian", "trainer_FISHERMAN",
     (("MAGIKARP", 9),), False),
    (104, 121, 44, "LADY", "Cindy", "trainer_LASS",
     (("ZIGZAGOON", 7),), False),
    (104, 131, 25, "RICHBOY", "Winston", "trainer_YOUNGSTER",
     (("ZIGZAGOON", 7),), False),
    (104, 141, 24, "LASS", "Haley", "trainer_LASS",
     (("LOTAD", 6), ("SHROOMISH", 6)), False),
    (104, 137, 15, "TWINS", "Gina & Mia", "trainer_LASS",
     (("SEEDOT", 6), ("LOTAD", 6)), True),
    (104, 139, 8, "FISHERMAN", "Ivan", "trainer_FISHERMAN",
     (("MAGIKARP", 5), ("MAGIKARP", 6), ("MAGIKARP", 7)), False),
    (156, 8, 15, "BUGCATCHER", "James", "trainer_BUGCATCHER",
     (("NINCADA", 6), ("NINCADA", 6)), False),
    (156, 11, 33, "BUGCATCHER", "Lyle", "trainer_BUGCATCHER",
     (("WURMPLE", 3), ("WURMPLE", 3), ("WURMPLE", 3), ("WURMPLE", 3)), False),
)

# Fictional names for flags only. Item positions/species are source-verified;
# hidden items remain invisible rather than being turned into new Poké Balls.
# (map, x, y, key, item, visible)
PICKUPS_STAGE3 = (
    (16, 3, 28, "PETALBURG_ETHER", "ETHER", True),
    (16, 19, 2, "PETALBURG_MAX_REVIVE", "MAXREVIVE", True),
    (16, 11, 29, "PETALBURG_RARE_CANDY", "RARECANDY", False),
    (104, 139, 53, "ROUTE104_POKE_BALL", "POKEBALL", True),
    (104, 147, 22, "ROUTE104_X_ACCURACY", "XACCURACY", True),
    (104, 149, 15, "ROUTE104_PP_UP", "PPUP", True),
    (104, 115, 8, "ROUTE104_POTION", "POTION", True),
    (104, 126, 72, "ROUTE104_ANTIDOTE", "ANTIDOTE", False),
    (104, 126, 64, "ROUTE104_HEART_SCALE", "HEARTSCALE", False),
    (104, 124, 55, "ROUTE104_HIDDEN_POTION", "POTION", False),
    (104, 113, 9, "ROUTE104_HIDDEN_BALL", "POKEBALL", False),
    (104, 117, 6, "ROUTE104_SUPER_POTION", "SUPERPOTION", False),
    (156, 8, 9, "WOODS_ETHER", "ETHER", True),
    (156, 49, 8, "WOODS_GREAT_BALL", "GREATBALL", True),
    (156, 39, 21, "WOODS_X_ATTACK", "XATTACK", True),
    (156, 8, 27, "WOODS_PARALYZE_HEAL", "PARALYZEHEAL", True),
    (156, 30, 7, "WOODS_TINY_MUSHROOM_1", "TINYMUSHROOM", False),
    (156, 8, 20, "WOODS_HIDDEN_POKE_BALL", "POKEBALL", False),
    (156, 44, 30, "WOODS_TINY_MUSHROOM_2", "TINYMUSHROOM", False),
    (156, 43, 36, "WOODS_HIDDEN_POTION", "POTION", False),
)

# (map, x, y, name, Portuguese text), no source dialogue copy/paste.
SIGNS_STAGE3 = (
    (16, 17, 16, "PETALBURG_CITY", "Petalburg: cidade de encontro entre pessoas e natureza."),
    (16, 17, 10, "PETALBURG_GYM", "Ginásio de Petalburg. Líder: Norman, especialista em Pokémon Normais."),
    (16, 8, 9, "WALLY_HOUSE", "Casa de Wally."),
    (104, 137, 66, "ROUTE104_SOUTH", "Rota 104. A leste fica Petalburg."),
    (104, 133, 5, "ROUTE104_NORTH", "Rota 104. Rustboro fica ao norte, em preparação no piloto."),
    (104, 130, 50, "BRINEY_HOUSE", "Casa de Mr. Briney."),
    (104, 117, 20, "FLOWER_SHOP", "Floricultura Pretty Petal."),
    (156, 15, 9, "WOODS_TIPS_PP", "Dica: movimentos consomem PP. Descanse no Centro Pokémon quando necessário."),
    (156, 18, 33, "WOODS_TIPS_EXP", "Dica: todos os Pokémon que participam da batalha podem ganhar experiência."),
)

# (map, x, y, sprite candidate, handler). All NPC dialogue is written by Blue.
NPCS_STAGE3 = (
    (20, 6, 21, "trainer_YOUNGSTER", "BlueHoennPilot.norman_intro"),
    (19, 41, 6, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.wally_family"),
    (106, 9, 5, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.flower_shop"),
    (105, 11, 5, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.briney"),
)

# Sources only; the attack occurs at BOTH columns of the narrow woods path.
FOREST_AQUA_TRIGGERS = ((156, 30, 24), (156, 31, 24))
FOREST_AQUA_PBS = ("BLUE_HOENN_AQUA", "Recruta", 304)
FOREST_AQUA_TEAM = (("POOCHYENA", 9),)
