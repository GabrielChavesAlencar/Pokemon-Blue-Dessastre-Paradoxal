"""Hoenn isolated pilot, Stage 08 — Balance, Surf, Weather Institute, Feather,
Fortree, Routes 117-121 and Lilycove. No donor assets are redistributed.

Coordinates (including doors, pickups, Gym and Weather events) were audited
against the pinned original Hoenn RXDATA/MapInfos and PBS. Levels are Emerald
reference values only; Blue/Decades runtime keeps ownership of level scaling.
"""
SOURCE_MAPS_STAGE8 = {
    48:"Verdanturf Town",49:"Centro Pokémon de Verdanturf",
    50:"Poké Mart de Verdanturf",51:"Casas de Verdanturf",
    52:"Battle Tent de Verdanturf",
    64:"Fortree City",65:"Centro Pokémon de Fortree",
    66:"Poké Mart de Fortree",67:"Casas suspensas de Fortree",
    68:"Ginásio de Fortree",
    69:"Lilycove City",70:"Porto de Lilycove",
    71:"Centro Pokémon de Lilycove",72:"Department Store de Lilycove",
    73:"Casas e motel de Lilycove",74:"Museu de Lilycove",
    75:"Contest Hall de Lilycove",
    132:"Rota 117",133:"Day Care da Rota 117",
    134:"Rota 118",135:"Rota 119",
    136:"Casas da Rota 119",137:"Weather Institute",
    138:"Rota 120",139:"Rota 121",
}

# Selected source PBS links that have passable pairs on BOTH sides. The
# donor also lists long overlapping 135->48, 135->132, 135->41 borders and
# 134 East->64 West(140) whose physical endpoints are IMPASSABLE: omit them.
OFFSET_BORDERS_STAGE8 = (
    (41,"West",0,132,"East",0),
    (132,"West",0,48,"East",0),
    (134,"West",0,41,"East",0),
    (135,"South",0,134,"North",40),
    (135,"East",0,64,"West",0),
    (138,"West",0,64,"East",0),
    (139,"West",0,138,"East",80),
    (139,"East",0,69,"West",10),
)

# a=source door, a_arrival=adjacent standing cell, b=other door etc.
# The Daycare in donor Route119 strangely links to Route117 Map133;
# avoid that duplicate/incorrect entrance, keep the real Route117 access.
WARP_PAIRS_STAGE8 = (
    ((48,16,3),(48,16,4),(49,9,10),(49,9,9)),
    ((48,12,3),(48,12,4),(50,5,9),(50,5,8)),
    ((48,1,14),(48,1,15),(51,5,9),(51,5,8)),
    ((48,10,14),(48,10,15),(51,28,9),(51,28,8)),
    ((48,17,15),(48,17,16),(51,49,10),(51,49,9)),
    ((48,3,7),(48,3,8),(52,8,11),(52,8,10)),
    ((48,8,1),(48,8,2),(157,34,21),(157,34,20)),
    ((132,51,5),(132,51,6),(133,4,10),(133,4,9)),
    ((64,5,6),(64,5,7),(65,9,10),(65,9,9)),
    ((64,4,14),(64,4,15),(66,5,9),(66,5,8)),
    ((64,10,3),(64,10,4),(67,5,7),(67,5,6)),
    ((64,17,3),(64,17,4),(67,21,7),(67,21,6)),
    ((64,25,3),(64,25,4),(67,37,7),(67,37,6)),
    ((64,32,2),(64,32,3),(67,53,7),(67,53,6)),
    ((64,12,13),(64,12,14),(67,69,7),(67,69,6)),
    ((64,37,13),(64,37,14),(67,85,7),(67,85,6)),
    ((64,22,11),(64,22,12),(68,17,26),(68,17,25)),
    ((69,24,14),(69,24,15),(71,9,10),(71,9,9)),
    ((69,27,6),(69,27,7),(72,10,9),(72,10,8)),
    ((69,12,32),(69,12,33),(70,13,16),(70,13,15)),
    ((69,11,5),(69,11,6),(74,11,15),(74,11,14)),
    ((69,23,24),(69,23,25),(75,16,13),(75,16,12)),
    ((69,12,14),(69,12,15),(73,5,10),(73,5,9)),
    ((69,42,6),(69,42,7),(73,60,10),(73,60,9)),
    ((69,36,6),(69,36,7),(73,41,9),(73,41,8)),
    ((69,37,24),(69,37,25),(73,7,27),(73,7,26)),
    ((69,55,15),(69,55,16),(73,59,26),(73,59,25)),
    ((69,11,22),(69,11,23),(73,22,9),(73,22,8)),
    ((135,6,32),(135,6,33),(137,11,14),(137,11,13)),
    ((135,33,109),(135,33,110),(136,5,11),(136,5,10)),
    ((72,18,3),(72,18,4),(72,44,3),(72,44,4)),
    ((72,41,3),(72,41,4),(72,67,3),(72,67,4)),
    ((72,70,3),(72,70,4),(72,96,3),(72,96,4)),
    ((72,93,3),(72,93,4),(72,119,3),(72,119,4)),
    ((72,122,3),(72,122,4),(72,23,28),(72,23,29)),
    ((73,4,20),(73,4,21),(73,24,20),(73,24,21)),
    ((74,18,3),(74,18,4),(74,44,3),(74,44,4)),
    ((75,11,3),(75,11,4),(75,60,34),(75,60,33)),
    ((75,23,3),(75,23,4),(75,72,34),(75,72,33)),
)
LAND_ENCOUNTERS_STAGE8 = {
    # 200 relative weight in donor Map132: normalized without dropping species.
    132: ((10,"ODDISH",13,14),(30,"POOCHYENA",13,14),
          (10,"MARILL",13,13),(30,"ROSELIA",13,14),
          (9,"ILLUMISE",13,14),(9,"VOLBEAT",13,14),
          (1,"SEEDOT",13,13),(1,"SURSKIT",13,13)),
    134: ((30,"ELECTRIKE",24,26),(30,"ZIGZAGOON",24,26),
          (19,"WINGULL",25,27),(10,"LINOONE",26,26),
          (10,"MANECTRIC",26,26),(1,"KECLEON",25,25)),
    135: ((30,"LINOONE",25,27),(30,"ODDISH",24,27),
          (30,"ZIGZAGOON",25,27),(8,"TROPIUS",25,27),
          (1,"KECLEON",25,25),(1,"GROVYLE",25,25)),
    # Source Map138 has 200 slots; round one Poochyena slot downward so
    # the eight species, including 1%-rare Seedot/Surskit, remain present.
    138: ((25,"ODDISH",25,27),(15,"MARILL",25,27),
          (30,"MIGHTYENA",25,27),(19,"POOCHYENA",25,25),
          (8,"ABSOL",25,27),(1,"KECLEON",25,25),
          (1,"SEEDOT",25,25),(1,"SURSKIT",25,25)),
    139: ((15,"SHUPPET",26,28),(15,"DUSKULL",26,28),
          (20,"MIGHTYENA",26,28),(20,"POOCHYENA",26,26),
          (15,"ODDISH",26,28),(5,"GLOOM",28,28),
          (9,"WINGULL",26,28),(1,"KECLEON",25,25)),
}

# Existing Norman gym is Map020 from Stage3 — never duplicate donor map.
NORMAN_EVENT = (20,6,4)
NORMAN_PBS = ("BLUE_HOENN_NORMAN","Norman",820)
NORMAN_TEAM = (("SPINDA",27),("VIGOROTH",27),("LINOONE",29),("SLAKING",31))
WINONA_EVENT = (68,17,4)
WINONA_PBS = ("BLUE_HOENN_WINONA","Winona",868)
WINONA_TEAM = (("SWABLU",29),("TROPIUS",29),("PELIPPER",30),
               ("SKARMORY",31),("ALTARIA",33))
SHELLY_EVENT = (137,34,8)
SHELLY_PBS = ("BLUE_HOENN_SHELLY","Shelly",837)
SHELLY_TEAM = (("CARVANHA",28),("MIGHTYENA",28))
AQUA_INSTITUTE = (
    (137,12,7,851,(("POOCHYENA",27),("CARVANHA",27))),
    (137,17,5,852,(("ZUBAT",27),("POOCHYENA",27))),
    (137,40,10,853,(("POOCHYENA",26),("ZUBAT",26),("CARVANHA",26))),
    (137,49,8,854,(("ZUBAT",27),("CARVANHA",27))),
)
RIVAL_119_EVENT=(135,25,31)
RIVAL_LILYCOVE_EVENT=(69,27,7)
# Player starter -> (version, Emerald reference team) for May/Brendan.
RIVAL_119_TEAMS={
    "TREECKO":(819,(("PELIPPER",29),("LOMBRE",29),("COMBUSKEN",31))),
    "TORCHIC":(820,(("LOMBRE",29),("SLUGMA",29),("MARSHTOMP",31))),
    "MUDKIP":(821,(("SLUGMA",29),("PELIPPER",29),("GROVYLE",31))),
}
RIVAL_LILYCOVE_TEAMS={
    "TREECKO":(822,(("TROPIUS",31),("PELIPPER",32),("LUDICOLO",32),("COMBUSKEN",34))),
    "TORCHIC":(823,(("TROPIUS",31),("LUDICOLO",32),("SLUGMA",32),("MARSHTOMP",34))),
    "MUDKIP":(824,(("TROPIUS",31),("SLUGMA",32),("PELIPPER",32),("GROVYLE",34))),
}
# "normal" trainer types below are native Blue fallback battle art; Emerald's
# source classes are documented but not misrepresented as exact native sprites.
TRAINERS_STAGE8=(
    (20,40,21,"LASS","Alexia","trainer_LASS",(("WIGGLYTUFF",26),),False),
    (20,57,21,"YOUNGSTER","George","trainer_YOUNGSTER",(("SLAKOTH",26),),False),
    (20,32,5,"LASS","Jody","trainer_LASS",(("ZANGOOSE",26),),False),
    (20,32,37,"YOUNGSTER","Randall","trainer_YOUNGSTER",(("SWELLOW",26),),False),
    (20,49,37,"LASS","Mary","trainer_LASS",(("DELCATTY",26),),False),
    (20,23,21,"YOUNGSTER","Parker","trainer_YOUNGSTER",(("SPINDA",26),),False),
    (20,49,5,"YOUNGSTER","Berke","trainer_YOUNGSTER",(("VIGOROTH",26),),False),
    (68,3,12,"YOUNGSTER","Darius","trainer_YOUNGSTER",(("TROPIUS",30),),False),
    (68,11,10,"YOUNGSTER","Edwardo","trainer_YOUNGSTER",(("DODUO",29),("PELIPPER",29)),False),
    (68,12,12,"YOUNGSTER","Flint","trainer_YOUNGSTER",(("SWELLOW",29),("XATU",29)),False),
    (68,6,16,"YOUNGSTER","Jared","trainer_YOUNGSTER",(("DODUO",27),("SKARMORY",27),("TROPIUS",27)),False),
    (68,7,19,"LASS","Ashley","trainer_LASS",(("SWABLU",27),("SWABLU",27),("SWABLU",27)),False),
    (68,6,25,"YOUNGSTER","Humberto","trainer_YOUNGSTER",(("SKARMORY",30),),False),
    (134,14,14,"FISHERMAN","Wade","trainer_FISHERMAN",(("TENTACOOL",16),),False),
    (134,64,10,"YOUNGSTER","Perry","trainer_YOUNGSTER",(("WINGULL",26),),False),
    (134,17,11,"YOUNGSTER","Dalton","trainer_YOUNGSTER",(("MAGNEMITE",15),("WHISMUR",15)),False),
    (135,10,50,"YOUNGSTER","Hugh","trainer_YOUNGSTER",(("WINGULL",25),("TROPIUS",25)),False),
    (135,19,49,"YOUNGSTER","Takashi","trainer_YOUNGSTER",(("NINJASK",25),("KOFFING",25)),False),
    (135,16,52,"YOUNGSTER","Dayton","trainer_YOUNGSTER",(("SLUGMA",25),("NUMEL",25)),False),
    (135,7,74,"YOUNGSTER","Jackson","trainer_YOUNGSTER",(("BRELOOM",27),),False),
    (135,35,83,"LASS","Catherine","trainer_LASS",(("GLOOM",26),("ROSELIA",26)),False),
    (135,8,68,"LASS","Rachel","trainer_LASS",(("GOLDEEN",26),),False),
    (138,14,34,"YOUNGSTER","Leonel","trainer_YOUNGSTER",(("MANECTRIC",30),),False),
    (138,18,34,"LASS","Angelica","trainer_LASS",(("CASTFORM",30),),False),
    (138,10,72,"YOUNGSTER","Keigo","trainer_YOUNGSTER",(("KOFFING",28),("NINJASK",28)),False),
    (138,16,6,"LASS","Clarissa","trainer_LASS",(("ROSELIA",28),("WAILMER",28)),False),
    (139,11,6,"YOUNGSTER","Cale","trainer_YOUNGSTER",(("DUSTOX",29),("BEAUTIFLY",29)),False),
    (139,11,11,"LASS","Tammy","trainer_LASS",(("DUSKULL",29),("SHUPPET",29)),False),
    (139,22,5,"LASS","Jessica","trainer_LASS",(("KECLEON",29),("SEVIPER",29)),False),
)
# Two Kecleon NPCs require Devon Scope; no free access through Fortree.
STEVEN_SCOPE_EVENT=(138,13,15)
FORTREE_KECLEON_EVENT=(64,25,8)
ROUTE120_KECLEON_EVENT=(138,12,16)
# Staff in the Institute reward Castform only after Shelly.
WEATHER_REWARD_EVENT=(137,31,8)
NPCS_STAGE8=(
    (49,9,4,"NPC_DPP_PokeCenter_Nurse","BlueHoennPilot.heal"),
    (50,3,5,"NPC_DPP_PokeMart_Man","BlueHoennPilot.mart"),
    (65,9,4,"NPC_DPP_PokeCenter_Nurse","BlueHoennPilot.heal"),
    (66,3,5,"NPC_DPP_PokeMart_Man","BlueHoennPilot.mart"),
    (71,9,4,"NPC_DPP_PokeCenter_Nurse","BlueHoennPilot.heal"),
    (133,4,4,"NPC_DPP_PokeMart_Man","BlueHoennPilot.daycare_info"),
    (134,28,8,"trainer_FISHERMAN","BlueHoennPilot.good_rod_fisherman"),
    (70,10,12,"NPC_DPP_PokeMart_Man","BlueHoennPilot.harbor_stage8"),
    (75,16,4,"NPC_DPP_PokeMart_Man","BlueHoennPilot.contest_stage8"),
)
# Source Map020 Gym room switches are discrete doors in one large RXDATA.
# The pilot does not turn them into fictitious routes: gym's 7 trainers and
# Norman are authored but original trapdoors and room doors need native QA.
FUTURE_GATES_STAGE8=(
    (69,70,5,"AQUA_HIDEOUT"),
    (139,37,5,"SAFARI_ZONE"),
    (138,19,23,"SCORCHED_SLAB"),
    (139,32,14,"MT_PYRE_PIER"),
)
SIGNS_STAGE8=(
    (48,14,6,"VERDANTURF","Verdanturf: cidade tranquila ligada a Mauville."),
    (64,26,10,"FORTREE_GYM","Ginásio de Fortree, líder Winona, Pokémon Voadores."),
    (64,6,9,"FORTREE","Fortree: casas erguidas entre árvores."),
    (69,6,15,"LILYCOVE","Lilycove: cidade costeira com lojas e museu."),
    (69,29,7,"LILYCOVE_STORE","Department Store de Lilycove."),
    (135,9,33,"WEATHER_INSTITUTE","Instituto Meteorológico: a Equipe Aqua está no interior."),
    (139,39,6,"SAFARI","Safari Zone: conteúdo a ser integrado."),
)
# Carefully transcribed from original RXDATA 111 script pbItemBall(:ITEM).
# (map,x,y,key,item,visible) -> true items present only when native Blue ID exists.
PICKUPS_STAGE8=(
    (69,61,7,"LILYCOVE_PPUP","PPUP",False),
    (69,36,31,"LILYCOVE_HEARTSCALE","HEARTSCALE",False),
    (69,64,31,"LILYCOVE_POKEBALL","POKEBALL",False),
    (69,61,36,"LILYCOVE_MAXREPEL","MAXREPEL",True),
    (132,9,1,"ROUTE117_REVIVE","REVIVE",True),
    (132,3,18,"ROUTE117_REPEL","REPEL",False),
    (132,16,18,"ROUTE117_GREATBALL","GREATBALL",True),
    (134,12,14,"ROUTE118_HEARTSCALE","HEARTSCALE",False),
    (134,31,13,"ROUTE118_IRON","IRON",False),
    (134,69,7,"ROUTE118_HYPERPOTION","HYPERPOTION",True),
    (135,29,53,"ROUTE119_ELIXIR_A","ELIXIR",True),
    (135,33,117,"ROUTE119_HYPERPOTION_A","HYPERPOTION",True),
    (135,3,56,"ROUTE119_HYPERPOTION_B","HYPERPOTION",True),
    (135,19,5,"ROUTE119_NUGGET","NUGGET",True),
    (135,26,120,"ROUTE119_FULLHEAL","FULLHEAL",False),
    (135,38,62,"ROUTE119_ULTRABALL","ULTRABALL",False),
    (135,8,18,"ROUTE119_RARECANDY","RARECANDY",True),
    (135,12,121,"ROUTE119_SUPERREPEL","SUPERREPEL",True),
    (135,25,76,"ROUTE119_LEAFSTONE","LEAFSTONE",True),
    (135,20,29,"ROUTE119_MAXETHER","MAXETHER",False),
    (135,17,82,"ROUTE119_CALCIUM","CALCIUM",False),
    (135,24,42,"ROUTE119_ELIXIR_B","ELIXIR",True),
    (135,4,96,"ROUTE119_ZINC","ZINC",True),
    (138,20,55,"ROUTE120_NUGGET","NUGGET",True),
    (138,9,1,"ROUTE120_RARECANDY_A","RARECANDY",False),
    (138,23,82,"ROUTE120_HYPERPOTION","HYPERPOTION",True),
    (138,31,11,"ROUTE120_REVIVE","REVIVE",False),
    (138,0,86,"ROUTE120_RARECANDY_B","RARECANDY",False),
    (138,22,13,"ROUTE120_NESTBALL","NESTBALL",True),
    (138,7,89,"ROUTE120_FULLHEAL","FULLHEAL",True),
    (138,24,33,"ROUTE120_REVIVE_B","REVIVE",True),
    (138,24,42,"ROUTE120_ZINC","ZINC",False),
    (139,55,10,"ROUTE121_CARBOS","CARBOS",True),
    (139,58,3,"ROUTE121_NUGGET","NUGGET",False),
    (139,60,10,"ROUTE121_REVIVE","REVIVE",True),
    (139,68,8,"ROUTE121_MAXREVIVE","MAXREVIVE",False),
    (139,23,10,"ROUTE121_HPUP","HPUP",False),
    (139,72,5,"ROUTE121_FULLHEAL","FULLHEAL",False),
    (139,38,13,"ROUTE121_ZINC","ZINC",True),
)
