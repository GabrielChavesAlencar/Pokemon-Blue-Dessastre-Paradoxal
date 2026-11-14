"""Hoenn Stage 07: R111/112/113/114, Fallarbor, Meteor Falls, Mt. Chimney,
Jagged Pass and Lavaridge. All data is original integration metadata.

Source coordinates correspond to pinned original donor RXDATA. Game graphics,
maps, PBS music and other donor assets are NEVER committed; they are read only
from the separately acquired local donor ZIP. Nothing is installed into
the primary Blue/Decades game; this is an ISOLATED pilot.
"""
SOURCE_MAPS_STAGE7 = {
    53: "Fallarbor Town", 54: "Centro Pokémon de Fallarbor",
    55: "Poké Mart de Fallarbor", 56: "Casas de Fallarbor",
    57: "Battle Tent de Fallarbor",
    58: "Lavaridge Town", 59: "Centro Pokémon de Lavaridge",
    60: "Poké Mart de Lavaridge", 61: "Casas de Lavaridge",
    62: "Loja de ervas de Lavaridge", 63: "Ginásio de Lavaridge",
    117: "Rota 111", 118: "Casa dos Winstrate", 120: "Casa de descanso da Rota 111",
    121: "Rota 112", 122: "Estação inferior do teleférico",
    123: "Rota 113", 124: "Oficina de vidro vulcânico",
    125: "Rota 114", 126: "Casa do Fossil Maniac", 128: "Casa de Lanette",
    177: "Fiery Path", 178: "Mt. Chimney",
    179: "Estação superior do teleférico", 180: "Jagged Pass",
    191: "Meteor Falls 1F", 192: "Meteor Falls - interior",
}
# Route 111/112/113/114, Fallarbor and Lavaridge use donor PBS true offsets.
# Each of these seven boundaries was checked against the private RXDATA:
# 20, 21, 10, 11, 11, 7, 1 passable pairs respectively.
OFFSET_BORDERS_STAGE7 = (
    (117, "South", 0, 41, "North", 0),
    (117, "West", 20, 121, "East", 0),
    (123, "East", 0, 117, "West", 0),
    (123, "West", 0, 53, "East", 0),
    (125, "East", 0, 53, "West", 0),
    (121, "West", 40, 58, "East", 0),
    (123, "South", 60, 121, "North", 0),
)

# (door source/standing, opposite door source/standing)
# All standing tiles were confirmed passable in donor at pinned revision.
# The original House126 *exit* incorrectly targets Map117 in this donor;
# our isolated pilot returns it to Route114 Map125.
WARP_PAIRS_STAGE7 = (
    ((53,14,7),(53,14,8),(54,8,11),(54,8,10)),
    ((53,15,15),(53,15,16),(55,5,10),(55,5,9)),
    ((53,1,6),(53,1,7),(56,5,10),(56,5,9)),
    ((53,6,17),(53,6,18),(56,24,11),(56,24,10)),
    ((53,8,7),(53,8,8),(57,8,12),(57,8,11)),
    ((58,9,6),(58,9,7),(59,8,11),(59,8,10)),
    ((58,15,5),(58,15,6),(60,5,10),(60,5,9)),
    ((58,12,15),(58,12,16),(62,5,10),(62,5,9)),
    ((58,16,15),(58,16,16),(61,5,10),(61,5,9)),
    ((58,5,15),(58,5,16),(63,15,25),(63,15,24)),
    ((117,13,113),(117,13,114),(118,5,10),(118,5,9)),
    ((117,26,18),(117,26,19),(120,5,10),(120,5,9)),
    ((121,11,36),(121,11,37),(177,32,41),(177,32,40)),
    ((121,22,10),(121,22,11),(177,32,9),(177,32,8)),
    ((121,28,27),(121,28,28),(122,8,14),(122,8,13)),
    ((123,33,5),(123,33,6),(124,5,11),(124,5,10)),
    ((125,29,5),(125,29,6),(126,6,10),(126,6,9)),
    ((125,27,36),(125,27,37),(128,7,10),(128,7,9)),
    ((125,8,63),(125,8,64),(191,34,22),(191,34,21)),
    ((191,17,6),(191,17,7),(192,14,34),(192,14,33)),
    ((178,18,37),(178,18,38),(179,8,14),(179,8,13)),
    ((178,21,42),(178,21,43),(180,13,6),(180,13,7)),
    ((180,14,41),(180,14,42),(121,6,46),(121,6,47)),
)
# Source Map122 and Map179 are intentionally connected by SCRIPTED CABLE,
# never an unconditional door (Meteor Falls storyline must be completed).
CABLE_POINTS_STAGE7 = ((122,8,9),(179,8,9))

LAND_ENCOUNTERS_STAGE7 = {
    117: ((35,"SANDSHREW",19,21),(35,"TRAPINCH",19,21),
          (24,"BALTOY",19,21),(6,"CACNEA",20,22)),
    121: ((75,"NUMEL",14,16),(25,"MARILL",14,16)),
    123: ((70,"SPINDA",14,16),(25,"SLUGMA",14,16),(5,"SKARMORY",16,16)),
    # Donor Route114 totals 200 relative slots: normalize by two, round
    # while preserving every species and exactly 100 total PBS probability.
    125: ((40,"SWABLU",15,17),(15,"LOTAD",15,16),(15,"SEEDOT",15,16),
          (5,"LOMBRE",16,18),(5,"NUZLEAF",16,18),(10,"SEVIPER",15,17),
          (9,"ZANGOOSE",15,17),(1,"SURSKIT",15,15)),
    180: ((55,"NUMEL",20,22),(25,"MACHOP",20,22),
          (19,"SPOINK",20,22),(1,"COMBUSKEN",20,20)),
}
CAVE_ENCOUNTERS_STAGE7 = {
    # Donor Fiery Path 200 relative slots; normalized without dropping species.
    177: ((30,"NUMEL",15,16),(14,"GRIMER",15,16),(13,"KOFFING",15,16),
          (15,"MACHOP",15,16),(10,"SLUGMA",15,15),(18,"TORKOAL",14,16)),
    191: ((80,"ZUBAT",14,20),(10,"LUNATONE",14,18),(10,"SOLROCK",14,18)),
    192: ((65,"GOLBAT",33,40),(18,"LUNATONE",33,39),(17,"SOLROCK",33,39)),
}

# Source MapID,x,y,native Blue trainer class,name,overworld sprite,party,double
# Only trainer anchors/team species confirmed on actual source event+PBS.
TRAINERS_STAGE7 = (
    (117,28,51,"LASS","Heidi","trainer_LASS",(("SANDSHREW",22),("BALTOY",22)),False),
    (117,16,119,"YOUNGSTER","Hayden","trainer_YOUNGSTER",(("NUMEL",18),),False),
    (117,19,121,"LASS","Bianca","trainer_LASS",(("SHROOMISH",18),),False),
    (121,29,49,"YOUNGSTER","Larry","trainer_YOUNGSTER",(("NUZLEAF",18),),False),
    (121,31,7,"YOUNGSTER","Bryant","trainer_YOUNGSTER",(("NUMEL",18),("SLUGMA",18)),False),
    (121,24,34,"HIKER","Brice","trainer_HIKER",(("NUMEL",17),("MACHOP",17)),False),
    (123,21,11,"YOUNGSTER","Dillon","trainer_YOUNGSTER",(("ARON",19),),False),
    (123,75,3,"YOUNGSTER","Wyatt","trainer_YOUNGSTER",(("ARON",18),("ARON",18)),False),
    (123,7,6,"LASS","Sophie","trainer_LASS",(("MARILL",17),("LOMBRE",19)),False),
    (125,25,6,"FISHERMAN","Nolan","trainer_FISHERMAN",(("BARBOACH",19),),False),
    (125,19,35,"LASS","Nancy","trainer_LASS",(("MARILL",18),("LOMBRE",18)),False),
    (125,15,65,"HIKER","Lenny","trainer_HIKER",(("GEODUDE",18),("MACHOP",18)),False),
    (125,30,72,"HIKER","Lucas","trainer_HIKER",(("GEODUDE",18),("NUMEL",18)),False),
    (180,14,26,"LASS","Autumn","trainer_LASS",(("SHROOMISH",21),),False),
    (180,16,36,"YOUNGSTER","Ethan","trainer_YOUNGSTER",(("ZIGZAGOON",20),("TAILLOW",20)),False),
    (63,30,12,"YOUNGSTER","Keegan","trainer_YOUNGSTER",(("SLUGMA",23),),False),
    (63,5,20,"YOUNGSTER","Cole","trainer_YOUNGSTER",(("NUMEL",23),),False),
    (63,40,23,"YOUNGSTER","Jeff","trainer_YOUNGSTER",(("SLUGMA",22),("SLUGMA",22)),False),
    (63,5,16,"YOUNGSTER","Axle","trainer_YOUNGSTER",(("NUMEL",23),),False),
    (63,31,24,"YOUNGSTER","Jace","trainer_YOUNGSTER",(("SLUGMA",23),),False),
    (63,31,22,"HIKER","Eli","trainer_HIKER",(("NUMEL",23),),False),
    (63,7,8,"LASS","Danielle","trainer_LASS",(("MEDITITE",23),),False),
    (63,4,21,"YOUNGSTER","Gerald","trainer_YOUNGSTER",(("KECLEON",23),),False),
)

FLANNERY_PBS = ("BLUE_HOENN_FLANNERY","Flannery",763)
FLANNERY_TEAM = (("NUMEL",24),("SLUGMA",24),
                 ("CAMERUPT",26),("TORKOAL",29))
TABITHA_PBS = ("BLUE_HOENN_TABITHA","Tabitha",778)
TABITHA_TEAM = (("NUMEL",18),("POOCHYENA",20),
                ("NUMEL",22),("ZUBAT",22))
MAXIE_PBS = ("BLUE_HOENN_MAXIE","Maxie",779)
MAXIE_TEAM = (("MIGHTYENA",24),("ZUBAT",24),("CAMERUPT",25))
MAGMA_GRUNTS_STAGE7 = (
    ("BLUE_HOENN_MAGMA","Recruta",780,(("NUMEL",20),)),
    ("BLUE_HOENN_MAGMA","Recruta",781,(("ZUBAT",20),)),
)
MAGMA_GRUNT_EVENTS = ((178,14,17,1),(178,10,17,2))
TABITHA_EVENT = (178,13,12)
MAXIE_EVENT = (178,14,7)
METEORITE_MACHINE_EVENT = (178,15,7)
METEOR_FALLS_CUTSCENE = (191,21,21)
FLANNERY_EVENT = (63,15,15)
ROUTE112_MAGMA_BLOCKERS = ((121,26,30),(121,27,30))

# The selected safe sprites are from user's native Blue game. If missing,
# no item, map or foreign art is copied into the repository.
# Source-matched floor / steam launch pairs (all 22 landing tiles checked
# passable). Touching Fall teleports to Launch; returning is action-only to
# prevent two touch events from endlessly bouncing the player.
# Unpaired donor vents C/J/L/M/O remain a native-acceptance gap.
GYM_STEAM_PAIRS_STAGE7 = (
    ((12,24),(37,24)), ((10,15),(35,15)),
    ((7,20),(32,20)), ((2,23),(27,23)),
    ((3,20),(28,20)), ((2,16),(27,16)),
    ((2,12),(27,12)), ((4,9),(29,9)),
    ((9,8),(34,8)), ((14,9),(39,9)),
    ((14,18),(39,18)),
)

NPCS_STAGE7 = (
    (54,9,4,"NPC_DPP_PokeCenter_Nurse","BlueHoennPilot.heal"),
    (55,3,5,"NPC_DPP_PokeMart_Man","BlueHoennPilot.mart"),
    (59,9,4,"NPC_DPP_PokeCenter_Nurse","BlueHoennPilot.heal"),
    (60,3,5,"NPC_DPP_PokeMart_Man","BlueHoennPilot.mart"),
    (122,8,8,"trainer_YOUNGSTER","BlueHoennPilot.cable_car"),
    (179,8,8,"trainer_YOUNGSTER","BlueHoennPilot.cable_car"),
    (124,7,5,"NPC_DPP_PokeMart_Man","BlueHoennPilot.glass_workshop"),
    (126,5,4,"trainer_YOUNGSTER","BlueHoennPilot.fossil_house"),
)

# Four crucial main-story/optional gates to unimplemented donor maps.
FUTURE_GATES_STAGE7 = (
    (117,19,58,"MIRAGE_TOWER"),
    (180,16,19,"MAGMA_HIDEOUT"),
    (191,12,7,"METEOR_DEEP"),
    (191,13,43,"METEOR_ROUTE115"),
    (126,6,3,"FOSSIL_TUNNEL"),
)

PICKUPS_STAGE7 = (
    (117,3,114,"ROUTE111_HPUP","HPUP",True),
    (117,19,118,"ROUTE111_ELIXIR","ELIXIR",True),
    (117,12,54,"ROUTE111_STARDUST","STARDUST",True),
    (121,14,43,"ROUTE112_NUGGET","NUGGET",True),
    (123,53,7,"ROUTE113_MAXETHER","MAXETHER",True),
    (123,66,3,"ROUTE113_ETHER","ETHER",False),
    (123,73,3,"ROUTE113_NUGGET","NUGGET",False),
    (123,79,5,"ROUTE113_SUPERREPEL","SUPERREPEL",True),
    (125,7,6,"ROUTE114_RARECANDY","RARECANDY",True),
    (125,20,57,"ROUTE114_CARBOS","CARBOS",False),
    (177,13,36,"FIERY_PATH_FIRESTONE","FIRESTONE",True),
    (180,23,25,"JAGGED_PASS_ITEM","FULLHEAL",True),
)

SIGNS_STAGE7 = (
    (53,10,11,"FALLARBOR","Fallarbor: cidade calma ao norte de Hoenn."),
    (58,13,8,"LAVARIDGE","Lavaridge: cidade das fontes termais."),
    (58,7,15,"LAVARIDGE_GYM","Ginásio de Lavaridge, líder Flannery, Pokémon de Fogo."),
    (117,13,6,"ROUTE111","Rota 111: deserto e trilhas para Mt. Chimney."),
    (121,19,44,"MT_CHIMNEY","Mt. Chimney: use o teleférico para subir."),
    (123,12,9,"FALLARBOR_SIGN","A Rota 113 liga as cinzas vulcânicas a Fallarbor."),
    (125,7,64,"METEOR_FALLS","Meteor Falls: entrada da caverna."),
    (178,25,38,"JAGGED_PASS","Jagged Pass fica abaixo do topo de Mt. Chimney."),
)
