"""Hoenn Stage 10: author-owned campaign ending in isolated Blue pilot.

Pinned donor audit: inspect_hoenn_stage10_donor.py, 14 Nov 2026.
Locations are real donor MapIDs; no donor events or scripts are copied.
Levels in these Emerald rosters are references, not fixed Blue battle levels.
World traversal, field-move puzzles and Game.exe remain UNVERIFIED.
"""

SOURCE_MAPS_STAGE10 = {
    83: "Sootopolis City", 84: "Centro Pokémon de Sootopolis",
    85: "Poké Mart de Sootopolis", 86: "Casas de Sootopolis",
    87: "Ginásio de Sootopolis", 88: "Pacifidlog Town",
    89: "Centro Pokémon de Pacifidlog", 90: "Casas de Pacifidlog",
    91: "Ever Grande City Sul", 92: "Centro Pokémon de Ever Grande",
    93: "Liga Pokémon de Hoenn", 94: "Elite Four - Sidney",
    95: "Elite Four - Phoebe", 96: "Elite Four - Glacia",
    97: "Elite Four - Drake", 98: "Sala do Campeão Wallace",
    99: "Hall of Fame de Hoenn", 100: "Corredores da Elite Four",
    146: "Rota 125", 147: "Rota 126", 148: "Rota 127",
    149: "Rota 128", 150: "Rota 129", 151: "Rota 130",
    152: "Rota 131", 153: "Rota 132", 154: "Rota 133",
    155: "Rota 134", 227: "Seafloor Cavern - Entrada",
    228: "Seafloor Cavern 1", 229: "Seafloor Cavern 2",
    230: "Seafloor Cavern 3", 231: "Seafloor Cavern 4",
    232: "Seafloor Cavern 5", 233: "Seafloor Cavern 6",
    234: "Seafloor Cavern 7", 235: "Seafloor Cavern 8",
    236: "Seafloor Cavern 9", 238: "Cave of Origin - Entrada",
    239: "Cave of Origin 1F", 240: "Cave of Origin B1F",
    241: "Sky Pillar - Exterior", 242: "Sky Pillar - Entrada",
    243: "Sky Pillar 1F", 244: "Sky Pillar 2F",
    245: "Sky Pillar 3F", 246: "Sky Pillar 4F",
    247: "Sky Pillar 5F", 248: "Sky Pillar - Topo",
    250: "Victory Road 1F", 251: "Victory Road B1F",
    252: "Victory Road B2F", 255: "Sootopolis Submersa",
    258: "Rota 125 Submersa", 259: "Rota 126 Submersa",
    260: "Rota 127 Submersa", 261: "Rota 128 Submersa",
    262: "Rota 129 Submersa", 263: "Rota 134 Submersa",
    266: "Seafloor Cavern Submersa", 322: "Ever Grande City Norte",
}

# These original records were shipped in V1, but the connected sides have
# zero shared tiles at the authored offsets. They identify the legacy layout.
LEGACY_VOID_SURF_BORDERS = (
    (147,"North",80,76,"South",0),
    (148,"West",0,144,"East",80),
    (149,"West",0,144,"East",160),
    (150,"North",120,91,"South",0),
    (152,"East",0,147,"West",120),
)

# These additional rows are present verbatim in the pinned source. Together
# with the retained borders they join the same coastal map components.
RESTORED_SURF_BORDERS = (
    (148,"West",0,147,"East",0),
    (149,"South",0,150,"North",0),
    (152,"East",0,151,"West",0),
)

SURF_BORDERS_STAGE10 = (
    (146,"South",0,76,"North",0),
    (148,"North",0,76,"South",0),
    (146,"West",0,144,"East",0),
    (147,"North",0,144,"South",0),
    (149,"East",0,91,"West",0),
    (152,"West",0,88,"East",0),
    (153,"East",0,88,"West",0),
    (154,"West",0,155,"East",0),
    (154,"East",0,153,"West",0),
    (148,"South",0,149,"North",0),
    (150,"West",0,151,"East",0),
    *RESTORED_SURF_BORDERS,
)

# These undirected relationships are either direct donor transfers, PBS
# geography, or DIVE/Waterfall-related field paths that remain native QA.
# They do not independently certify a traversable campaign.
STAGE10_MAP_GRAPH_EDGES = (
    (83,84),(83,85),(83,86),(83,87),(83,238),
    (88,89),(88,90),(91,92),(91,250),(250,251),(251,252),
    (250,322),(322,93),(93,100),(100,94),(100,95),
    (100,96),(100,97),(100,98),(98,99),
    (238,239),(239,240),(152,242),(242,241),
    (241,243),(243,244),(244,245),(245,246),(246,247),(247,248),
    (261,266),(266,227),(227,228),(228,229),(228,232),
    (229,231),(229,233),(229,234),(230,233),(230,234),
    (230,235),(231,232),(235,236),(236,149),
    (83,255),(255,259),(146,258),(147,259),(148,260),
    (149,261),(150,262),(155,263),
)

# Audited real original event anchors (MapID, tile x, tile y).
JUAN_EVENT=(87,10,4)
SOOTOPOLIS_CRISIS_EVENT=(83,32,33)
ORIGIN_WALLACE_EVENT=(240,11,16)
SKY_PILLAR_WALLACE_EVENT=(241,13,8)
RAYQUAZA_EVENT=(248,15,15)
SEAFLOOR_AWAKENING_EVENT=(236,23,46)
WALLY_VICTORY_ROAD_EVENT=(250,8,26)
LEAGUE_EXIT_EVENT=(98,8,4)
HALL_OF_FAME_EVENT=(99,9,18)
ELITE_EVENTS=((94,8,7),(95,8,7),(96,8,7),(97,8,7))
CHAMPION_EVENT=(98,8,7)
STAGE10_SIGNS=(
    (83,34,37,"SOOTOPOLIS_GYM"),
    (322,23,16,"LEAGUE_GATE"),
)

JUAN_PBS=("BLUE_HOENN_JUAN","Juan",1087)
JUAN_TEAM=(("LUVDISC",41),("WHISCASH",41),("SEALEO",43),
           ("CRAWDAUNT",43),("KINGDRA",46))
ARCHIE_PBS=("BLUE_HOENN_ARCHIE","Archie",1026)
ARCHIE_TEAM=(("MIGHTYENA",41),("CROBAT",41),("SHARPEDO",43))
WALLY_ROAD_PBS=("BLUE_HOENN_WALLY","Wally",1025)
WALLY_ROAD_TEAM=(("ALTARIA",44),("DELCATTY",43),("ROSELIA",44),
                 ("MAGNETON",41),("GARDEVOIR",45))
ELITE_PBS=(
    ("BLUE_HOENN_ELITE","Sidney",1094),
    ("BLUE_HOENN_ELITE","Phoebe",1095),
    ("BLUE_HOENN_ELITE","Glacia",1096),
    ("BLUE_HOENN_ELITE","Drake",1097),
)
ELITE_TEAMS=(
    (("MIGHTYENA",46),("SHIFTRY",48),("CACTURNE",46),
     ("CRAWDAUNT",48),("ABSOL",49)),
    (("DUSCLOPS",48),("BANETTE",49),("SABLEYE",50),
     ("BANETTE",49),("DUSCLOPS",51)),
    (("SEALEO",50),("GLALIE",50),("SEALEO",52),
     ("GLALIE",52),("WALREIN",53)),
    (("SHELGON",52),("ALTARIA",54),("KINGDRA",53),
     ("FLYGON",53),("SALAMENCE",55)),
)
CHAMPION_PBS=("BLUE_HOENN_CHAMPION","Wallace",1098)
CHAMPION_TEAM=(("WAILORD",57),("TENTACRUEL",55),("LUDICOLO",56),
               ("WHISCASH",56),("GYARADOS",56),("MILOTIC",58))

# No ordinary route trainers or cave encounters are guessed from map names.
# Source source-scripted Ice puzzle, Strength rocks, Rayquaza cinematic,
# Dive/Waterfall and native Hall of Fame are not yet reproduced.
