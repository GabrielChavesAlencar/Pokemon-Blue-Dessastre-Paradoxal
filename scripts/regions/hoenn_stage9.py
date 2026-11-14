"""Hoenn Stage 09 — Mt. Pyre, Magma/Aqua hideouts, Mossdeep and Mind Badge.

Only integration definitions. The donor source RXDATA, images, music, saves and
proprietary game binaries are NOT committed. Locations and named event anchors
were verified by a read-only audit of pinned donor MapInfos and event pages:
GitHub Actions "Hoenn Stage 09 - auditoria read-only doador".

Native Game.exe / Android gameplay, original gym switch puzzle, Steven double
partner battle and Dive field mechanics remain unapproved.
"""
SOURCE_MAPS_STAGE9 = {
    76:"Mossdeep City",77:"Centro Pokémon de Mossdeep",
    78:"Poké Mart de Mossdeep",79:"Casas de Mossdeep",
    80:"Mossdeep Game Corner",81:"Centro Espacial de Mossdeep",
    82:"Ginásio de Mossdeep",
    141:"Rota 122",144:"Rota 124",
    182:"Esconderijo Magma 1F",
    183:"Esconderijo Magma 2F-1",
    184:"Esconderijo Magma 2F-2",
    185:"Esconderijo Magma 2F-3",
    186:"Esconderijo Magma 3F-1",
    187:"Esconderijo Magma 3F-2",
    188:"Esconderijo Magma 3F-3",
    189:"Esconderijo Magma 4F",
    206:"Mt. Pyre 1F",
    207:"Mt. Pyre 2F",
    208:"Mt. Pyre 3F",
    209:"Mt. Pyre 4F",
    210:"Mt. Pyre 5F",
    211:"Mt. Pyre 6F",
    212:"Mt. Pyre Exterior",
    213:"Mt. Pyre Summit",
    215:"Esconderijo Aqua 1F",
    216:"Esconderijo Aqua B1F",
    217:"Esconderijo Aqua B2F",
}
# Surf-dependent raw PBS borders. Unlike ordinary land paths, water requires
# the engine field move and is deliberately NOT treated as a free walking edge.
SURF_BORDERS_STAGE9 = (
    (139,"South",20,141,"North",0),
    (144,"West",10,69,"East",0),
    (144,"East",40,76,"West",0),
)
# Script-only entry gates replace Stage7/Stage8 "future" placeholders.
MT_PYRE_ROUTE121_GATE=(139,32,14)   # opening is a sea crossing, not a teleport
MAGMA_HIDEOUT_GATE=(180,16,19)     # Jagged Pass cave threshold
AQUA_HIDEOUT_GATE=(69,70,5)        # Lilycove entrance
# Donor Map 206 (Mt Pyre 1F) and Map 141 door are parsed dynamically
# from their ORIGINAL direct transfer events; no invented coordinates.

TATE_LIZA_EVENTS=((82,25,11),(82,26,11))
TATE_LIZA_PBS=("BLUE_HOENN_TATE_LIZA","Tate & Liza",982)
TATE_LIZA_TEAM=(("CLAYDOL",41),("XATU",41),("LUNATONE",42),("SOLROCK",42))
# Party is an Emerald FOUR-Pokémon double-battle team (two active together).
# Blue's scaling rules are authoritative; PBS levels are reference only.
MATT_PBS=("BLUE_HOENN_MATT","Matt",917)
MATT_TEAM=(("MIGHTYENA",34),("GOLBAT",34))
MAXIE_HIDEOUT_PBS=("BLUE_HOENN_MAXIE","Maxie",989)
MAXIE_HIDEOUT_TEAM=(("MIGHTYENA",37),("CROBAT",38),("CAMERUPT",39))
TABITHA_HIDEOUT_PBS=("BLUE_HOENN_TABITHA","Tabitha",988)
TABITHA_HIDEOUT_TEAM=(("NUMEL",26),("MIGHTYENA",28),
                       ("ZUBAT",30),("CAMERUPT",33))
MAXIE_SPACE_PBS=("BLUE_HOENN_MAXIE","Maxie",992)
MAXIE_SPACE_TEAM=(("MIGHTYENA",42),("CROBAT",43),("CAMERUPT",44))
TABITHA_SPACE_PBS=("BLUE_HOENN_TABITHA","Tabitha",993)
TABITHA_SPACE_TEAM=(("CAMERUPT",36),("MIGHTYENA",38),("GOLBAT",40))
# In the source Emerald, Steven is a partner in the Space Center. Native
# 2-on-2 trainer pairing is not claimed; our event has guarded sequential
# bosses as a provisional scripted fallback.
ARCHIE_ORB_EVENT=(213,22,11)      # orb-steal cutscene trigger (player touch)
MT_PYRE_ARCHIE=(213,22,10)
MT_PYRE_OLD_LADY=(213,23,9)
TABITHA_HIDEOUT_EVENT=(189,27,6)
MAXIE_HIDEOUT_EVENT=(189,21,23)
GROUDON_CUTSCENE_EVENT=(189,21,19)
MATT_HIDEOUT_EVENT=(217,25,21)
SUBMARINE_EVENT=(217,19,22)
SPACE_MAXIE_EVENT=(81,27,11)
SPACE_STEVEN_EVENT=(81,27,10)     # Steven in the upper room
SPACE_GRUNT_EVENTS=(
    (81,13,8,991,(("NUMEL",31),("ZUBAT",31))),
    (81,14,11,994,(("POOCHYENA",31),("NUMEL",31))),
)
# Map82 trainers with source-matched anchors and Emerald PBS teams.
TRAINERS_STAGE9=(
    (82,6,33,"LASS","Maura","trainer_LASS",(("KADABRA",36),),False),
    (82,11,12,"YOUNGSTER","Nate","trainer_YOUNGSTER",(("SPOINK",36),),False),
    (82,3,34,"YOUNGSTER","Preston","trainer_YOUNGSTER",(("KIRLIA",36),),False),
    (82,8,7,"LASS","Hannah","trainer_LASS",(("KIRLIA",36),),False),
    (82,8,13,"YOUNGSTER","Virgil","trainer_YOUNGSTER",(("RALTS",36),),False),
    (82,27,29,"LASS","Macey","trainer_LASS",(("NATU",36),),False),
    (82,7,24,"YOUNGSTER","Blake","trainer_YOUNGSTER",(("GIRAFARIG",36),),False),
    (82,6,27,"LASS","Samantha","trainer_LASS",(("XATU",36),),False),
    (207,5,8,"YOUNGSTER","Mark","trainer_YOUNGSTER",(("RHYHORN",31),),False),
    (207,8,8,"LASS","Leah","trainer_LASS",(("SPOINK",31),),False),
    (207,8,11,"YOUNGSTER","Zander","trainer_YOUNGSTER",(("HARIYAMA",31),),False),
    (208,3,6,"YOUNGSTER","William","trainer_YOUNGSTER",(("RALTS",26),("RALTS",26),("KIRLIA",26)),False),
    (208,8,6,"LASS","Gabrielle","trainer_LASS",(("SKITTY",26),("POOCHYENA",26),
                    ("ZIGZAGOON",26),("LOTAD",26),("SEEDOT",26),("TAILLOW",26)),False),
    (208,13,6,"LASS","Kayla","trainer_LASS",(("WOBBUFFET",26),("NATU",26),("KADABRA",26)),False),
    (209,13,9,"LASS","Tasha","trainer_LASS",(("SHUPPET",32),),False),
    (210,5,9,"YOUNGSTER","Atsushi","trainer_YOUNGSTER",(("HARIYAMA",32),),False),
    (211,12,5,"YOUNGSTER","Cedric","trainer_YOUNGSTER",(("WOBBUFFET",32),),False),
    (211,8,5,"LASS","Valerie","trainer_LASS",(("SABLEYE",32),),False),
)
# Historical donor event positions audited. Provisional grunt teams below
# are explicitly NOT exact PBS party mappings; each variant needs donor event
# TrainerBattle version verification before playable approval.
PYRE_AQUA_GRUNTS=(
    (213,21,19,920,(("POOCHYENA",32),("CARVANHA",32))),
    (213,25,22,921,(("ZUBAT",32),("POOCHYENA",32))),
    (213,21,15,922,(("CARVANHA",32),)),
    (213,25,15,923,(("ZUBAT",32),("CARVANHA",32))),
)
MAGMA_HIDEOUT_GRUNTS=(
    (182,9,9,940,(("NUMEL",33),("GOLBAT",33))),
    (182,35,24,941,(("POOCHYENA",33),("NUMEL",33))),
    (183,25,15,942,(("NUMEL",34),("POOCHYENA",34),("GOLBAT",34))),
    (183,16,18,943,(("NUMEL",34),("GOLBAT",34))),
    (184,9,13,944,(("MIGHTYENA",34),("NUMEL",34))),
    (189,35,15,945,(("GOLBAT",35),("CAMERUPT",35))),
    (189,31,15,946,(("MIGHTYENA",35),("NUMEL",35))),
)
AQUA_HIDEOUT_GRUNTS=(
    (216,8,8,950,(("CARVANHA",33),("MIGHTYENA",33))),
    (216,22,20,951,(("ZUBAT",33),("POOCHYENA",33))),
    (216,30,18,952,(("CARVANHA",34),("ZUBAT",34))),
    (217,9,7,953,(("MIGHTYENA",34),("ZUBAT",34))),
    (217,25,12,954,(("CARVANHA",34),("POOCHYENA",34))),
)
NPCS_STAGE9=(
    (77,9,4,"NPC_DPP_PokeCenter_Nurse","BlueHoennPilot.heal"),
    (78,3,5,"NPC_DPP_PokeMart_Man","BlueHoennPilot.mart"),
    (79,8,7,"trainer_YOUNGSTER","BlueHoennPilot.steven_house_stage9"),
    (79,44,6,"trainer_FISHERMAN","BlueHoennPilot.super_rod_stage9"),
    (81,8,8,"NPC_DPP_PokeMart_Man","BlueHoennPilot.mossdeep_space_scientist"),
)
SIGNS_STAGE9=(
    (76,34,9,"MOSSDEEP_GYM","Ginásio de Mossdeep: Tate e Liza, batalha dupla."),
    (76,66,16,"SPACE_CENTER","Centro Espacial de Mossdeep: pesquisas e foguetes."),
    (76,25,16,"MOSSDEEP","Mossdeep City: porto espacial de Hoenn."),
)
FUTURE_GATES_STAGE9=(
    (215,10,6,"AQUA_DEEP"), # unverified inner-side continuation, disabled
)
# Actual source-owned item events (pbItemBall) are discovered by read-only
# scanner in pilot_hoenn.py rather than hardcoding unverified item identities.
# Animated submarine / Groudon are PLACEHOLDERS, not wild encounters.
