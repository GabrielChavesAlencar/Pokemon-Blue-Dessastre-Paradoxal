"""Stage 05: Dewford, Granite Cave, Slateport — ISOLATED Blue Hoenn pilot.

The map/event anchor coordinates were examined in the pinned donor RXDATA
(revision c59233bdbaac4fbfeca6aa01c7f05be628da2a92). They are ORIGINAL
source IDs, not Blue destination IDs. No donor graphics, dialogue or code are
included here. Reuse only native Blue assets, validate geometry on staging.

The coast is reached through Briney's scripted boat, NOT an invented Surf
route. Sea routes 105/107/108 and their islands stay deferred.
"""
SOURCE_MAPS_STAGE5 = {
    28: "Dewford Town",
    29: "Centro Pokémon de Dewford",
    30: "Casas de Dewford",
    31: "Ginásio de Dewford",
    32: "Slateport City",
    33: "Porto de Slateport",
    34: "Centro Pokémon de Slateport",
    35: "Poké Mart de Slateport",
    36: "Casas de Slateport",
    37: "Pokémon Fan Club",
    38: "Estaleiro do Capitão Stern",
    39: "Museu Oceânico",
    40: "Battle Tent de Slateport",
    108: "Rota 106",
    111: "Rota 109",
    112: "Casa da Praia",
    159: "Granite Cave 1F",
    160: "Granite Cave B1F",
    161: "Granite Cave B2F",
    162: "Sala de Steven em Granite Cave",
}

# Source PBS: 108,South,170,28,North,0 and 111,North,0,32,South,0.
OFFSET_BORDERS_STAGE5 = (
    (108, "South", 170, 28, "North", 0),
    (111, "North", 0, 32, "South", 0),
)

# Three verified, walkable cells. Boat travel is checked separately against
# game-story flags. Only these three terminals are connected in the validator.
BOAT_POINTS_STAGE5 = ((105, 11, 6), (28, 12, 10), (111, 21, 23))

# For each pair: (door event, outside standing cell, opposite door event,
#                 inside standing cell). Mirror transforms through the pilot.
# All points are adjacent to REAL donor door/ladder events.
WARP_PAIRS_STAGE5 = (
    ((28, 2, 10), (28, 2, 11), (29, 8, 11), (29, 9, 10)),
    ((28, 8, 17), (28, 8, 18), (31, 7, 30), (31, 7, 29)),
    ((28, 17, 14), (28, 17, 15), (30, 5, 10), (30, 5, 9)),
    ((28, 8, 8), (28, 8, 9), (30, 23, 11), (30, 23, 10)),
    ((28, 3, 3), (28, 3, 4), (30, 43, 11), (30, 43, 10)),
    ((32, 19, 19), (32, 19, 20), (34, 8, 11), (34, 9, 10)),
    ((32, 13, 26), (32, 13, 27), (35, 5, 10), (35, 5, 9)),
    ((32, 21, 44), (32, 21, 45), (36, 5, 28), (36, 5, 27)),
    ((32, 26, 38), (32, 26, 39), (38, 4, 17), (38, 4, 16)),
    ((32, 30, 26), (32, 30, 27), (39, 11, 11), (39, 11, 10)),
    ((32, 4, 26), (32, 4, 27), (37, 8, 13), (37, 8, 12)),
    ((32, 5, 19), (32, 5, 20), (36, 5, 10), (36, 5, 9)),
    ((32, 10, 12), (32, 10, 13), (40, 8, 12), (40, 8, 11)),
    ((32, 28, 12), (32, 28, 13), (33, 13, 17), (33, 13, 16)),
    ((111, 12, 5), (111, 12, 6), (112, 8, 12), (112, 8, 11)),
    ((108, 158, 16), (108, 158, 17), (159, 42, 16), (159, 42, 15)),
    ((159, 22, 14), (159, 22, 15), (160, 11, 26), (160, 11, 25)),
    ((159, 40, 6), (159, 40, 7), (160, 32, 18), (160, 32, 17)),
    ((160, 36, 18), (160, 36, 19), (161, 36, 18), (161, 36, 17)),
    ((160, 35, 26), (160, 35, 27), (161, 35, 26), (161, 35, 25)),
    ((160, 15, 10), (160, 15, 11), (161, 15, 10), (161, 15, 11)),
    ((160, 19, 8), (160, 19, 7), (161, 19, 8), (161, 19, 7)),
    ((160, 36, 7), (160, 36, 8), (161, 36, 7), (161, 36, 8)),
    ((159, 10, 14), (159, 10, 15), (162, 11, 6), (162, 11, 7)),
    ((38, 5, 3), (38, 5, 4), (38, 34, 3), (38, 34, 4)),
    ((39, 8, 3), (39, 8, 4), (39, 36, 3), (39, 36, 4)),
)

CAVE_ENCOUNTERS_STAGE5 = {
    159: ((50, "MAKUHITA", 6, 10), (30, "ZUBAT", 7, 8),
          (10, "ABRA", 8, 8), (10, "GEODUDE", 6, 9)),
    160: ((40, "ARON", 9, 11), (30, "ZUBAT", 9, 10),
          (10, "ABRA", 9, 9), (10, "MAKUHITA", 10, 10),
          (5, "MAWILE", 9, 11), (5, "SABLEYE", 9, 11)),
    161: ((40, "ARON", 10, 12), (30, "ZUBAT", 10, 11),
          (10, "ABRA", 10, 10), (10, "MAWILE", 10, 12),
          (10, "SABLEYE", 10, 11)),
    162: ((50, "MAKUHITA", 6, 10), (30, "ZUBAT", 7, 8),
          (10, "ABRA", 8, 8), (10, "ARON", 7, 8)),
}

# 6 gym and 2 coast trainers. Museum Aqua is authored separately.
# Coordinates and teams correspond to donor events/PBS, using safe native
# trainer class substitutions until the true sprites can be proved in Game.exe.
# mid,x,y,kind,name,overworld Blue sprite,base team,double
TRAINERS_STAGE5 = (
    (31, 14, 27, "LASS", "Laura", "trainer_LASS", (("MEDITITE", 13),), False),
    (31, 4, 20, "YOUNGSTER", "Takao", "trainer_YOUNGSTER", (("MACHOP", 13),), False),
    (31, 16, 14, "FISHERMAN", "Brenden", "trainer_FISHERMAN", (("MACHOP", 13),), False),
    (31, 18, 11, "LASS", "Lilith", "trainer_LASS", (("MEDITITE", 13),), False),
    (31, 9, 10, "YOUNGSTER", "Cristian", "trainer_YOUNGSTER", (("MAKUHITA", 13),), False),
    (31, 17, 5, "LASS", "Jocelyn", "trainer_LASS", (("MEDITITE", 13),), False),
    (108, 161, 14, "FISHERMAN", "Elliot", "trainer_FISHERMAN",
     (("MAGIKARP", 10), ("TENTACOOL", 7), ("MAGIKARP", 10)), False),
    (108, 175, 14, "FISHERMAN", "Ned", "trainer_FISHERMAN",
     (("TENTACOOL", 11),), False),
)
BRAWLY_PBS = ("BLUE_HOENN_BRAWLY", "Brawly", 531)
BRAWLY_TEAM = (("MACHOP", 16), ("MEDITITE", 16), ("MAKUHITA", 19))
MUSEUM_AQUA = (
    ("BLUE_HOENN_AQUA", "Recruta", 539, (("CARVANHA", 15),)),
    ("BLUE_HOENN_AQUA", "Recruta", 540, (("ZUBAT", 14), ("CARVANHA", 14))),
)

# Limited new NPCs, all positions sourced from the pinned donor:
# mid,x,y,pre-existing Blue graphic,plugin handler
NPCS_STAGE5 = (
    (29, 9, 4, "NPC_DPP_PokeCenter_Nurse", "BlueHoennPilot.heal"),
    (28, 12, 9, "trainer_FISHERMAN", "BlueHoennPilot.dewford_boat"),
    (31, 6, 5, "trainer_YOUNGSTER", "BlueHoennPilot.brawly"),
    (34, 9, 4, "NPC_DPP_PokeCenter_Nurse", "BlueHoennPilot.heal"),
    (35, 3, 5, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.mart"),
    (111, 21, 24, "trainer_FISHERMAN", "BlueHoennPilot.slateport_boat"),
    (159, 41, 12, "trainer_HIKER", "BlueHoennPilot.flash_hiker"),
    (162, 11, 11, "trainer_YOUNGSTER", "BlueHoennPilot.steven_letter"),
    (38, 14, 13, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.shipyard"),
    (39, 43, 8, "trainer_FISHERMAN", "BlueHoennPilot.stern"),
    (37, 8, 4, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.soothe_bell"),
    (111, 25, 18, "NPC_DPP_PokeMart_Man", "BlueHoennPilot.soft_sand"),
)

# Museum fee gate at the same logical threshold as the donor's 2-tile entrance.
MUSEUM_FEE_GATE = ((39, 11, 9), (39, 12, 9))
# The bridge leading north to Route 110 is NOT a playable next-stage gateway.
# No edge to Map113 is generated; a story gate informs the player.
SLATEPORT_NORTH_GATE = ((32, 18, 1), (32, 19, 1))

SIGNS_STAGE5 = (
    (28, 11, 16, "DEWFORD_GYM", "Ginásio de Dewford: Brawly é especialista em Pokémon Lutadores."),
    (28, 3, 15, "DEWFORD_TOWN", "Dewford: um porto tranquilo perto de Granite Cave."),
    (31, 7, 26, "BRAWLY_GYM", "Brawly: conquistar a Knuckle Badge libera Flash em Hoenn."),
    (32, 16, 22, "SLATEPORT_CITY", "Slateport: porto movimentado, mercado e Museu Oceânico."),
    (32, 23, 38, "SLATEPORT_SHIPYARD", "Estaleiro de Stern: verifique o pacote da Devon."),
    (32, 24, 12, "SLATEPORT_HARBOR", "Porto de Slateport. Passagens futuras dependem da história."),
    (32, 8, 26, "POKEMON_FAN_CLUB", "Clube dos Fãs de Pokémon."),
    (32, 14, 26, "SLATEPORT_MART", "Poké Mart de Slateport."),
    (39, 14, 3, "OCEANIC_MUSEUM", "Museu Oceânico: navegação, mares e pesquisa."),
    (108, 150, 16, "GRANITE_CAVE", "Granite Cave: cavernas profundas próximas a Dewford."),
    (111, 13, 5, "SEASIDE_HOUSE", "Casa da Praia: uma parada agradável na Rota 109."),
)

# Visible/hidden items; one-time regional flags prevent duplication.
PICKUPS_STAGE5 = (
    (108, 139, 14, "ROUTE106_PEARL", "PEARL", True),
    (159, 22, 10, "GRANITE_1F_ESCAPE_ROPE", "ESCAPEROPE", True),
    (111, 25, 18, "ROUTE109_SOFT_SAND", "SOFTSAND", False),
)
