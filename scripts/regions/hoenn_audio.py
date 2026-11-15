"""Hoenn track assignments from the pinned RPG Maker map data."""

from __future__ import annotations

BGM = {
    "BattleTent": "Location - Battle Tent (Battle Maison)",
    "Birch": "Location - Birch Pokemon Lab (Birch Pokemon Lab)",
    "CaveOrigin": "Dungeon - Cave of Origin (Cave of Origin)",
    "Center": "Location - Pokemon Center (Pokemon Center)",
    "Champion": "Battle Music - Steven (Battle! (Steven))",
    "ChampionVictory": "Battle Victory - Steven (Victory! (Steven))",
    "Chimney": "Dungeon - Mt. Chimney (Mt. Chimney)",
    "Contest": "Location - Contest Lobby (Contest Lobby)",
    "Dewford": "City - Dewford (Dewford Town)",
    "Elite": "Battle Music - Elite Four (Battle! (Elite Four))",
    "Evergrande": "City - Evergrande (Evergrande City)",
    "Fallarbor": "City - Fallarbor (Fallarbor Town)",
    "Fortree": "City - Fortree (Fortree City)",
    "GameCorner": "RSE Location - Game Corner (Game Corner)",
    "Gym": "Location - Pokemon Gym (Pokemon Gym)",
    "GymBattle": "Battle Music - Gym Leader (Battle! (Gym Leader))",
    "GymVictory": "Battle Victory - Gym Leader (Victory! (Gym Leader))",
    "HallRoom": "Location - Hall of Fame (Room of Glory)",
    "Hideout": "Location - Hideout (Hideout)",
    "Lilycove": "City - Lilycove (Lilycove City)",
    "LilycoveMuseum": "Location - Lilycove Museum (Museum)",
    "Littleroot": "City - Littleroot (Littleroot Town)",
    "Mart": "Location - Poke Mart (Poke Mart)",
    "OceanicMuseum": "Location - Oceanic Museum (Oceanic Museum)",
    "Oldale": "City - Oldale (Oldale Town)",
    "Petalburg": "City - Petalburg (Petalburg City)",
    "Pyre": "Dungeon - Mt. Pyre (Mt. Pyre)",
    "PyreExterior": "Dungeon - Mt. Pyre Exterior (Mt. Pyre Exterior)",
    "Rival": "Battle Music - Rival (Battle! (Brendan-May))",
    "Route101": "Route 101 (Route 101)",
    "Route104": "Route 104 (Route 104)",
    "Route110": "Route 110 (Route 110)",
    "Route113": "Route 113 (Route 113)",
    "Route119": "Route 119 (Route 119)",
    "Route120": "Route 120 (Route 120)",
    "Rustboro": "City - Rustboro (Rustboro City)",
    "School": "Location - Trainer's School (Trainer's School)",
    "Slateport": "City - Slateport (Slateport City)",
    "Sootopolis": "City - Sootopolis (Sootopolis City)",
    "TeamGrunt": "Battle Music - Team Grunt (Battle! (Team Magma - Team Aqua))",
    "TeamLeader": "Battle Music - Team Leader (Battle! (Team Magma _ Aqua Leader))",
    "TeamVictory": "Battle Victory - Team Magma and Aqua (Victory! (Team Magma - Team Aqua))",
    "Trainer": "Battle Music - Trainer (Battle! (Trainer Battle))",
    "TrainerVictory": "Battle Victory - Trainer (Victory! (Trainer Battle))",
    "Underwater": "Location - Underwater (Dive)",
    "Verdanturf": "City - Verdanturf (Verdanturf Town)",
    "VictoryRoad": "Dungeon - Victory Road (Victory Road)",
    "Wild": "Battle Music - Wild Pokemon (Battle! (Wild Pokemon))",
    "WildVictory": "Battle Victory - Wild Pokemon (Victory! (Wild Pokemon))",
    "Woods": "Dungeon - Petalburg Woods (Petalburg Woods)",
}

RECOVERY = "Audio/ME/ORAS Misc - Pokemon Recovery (Pokemon Healed).ogg"
RECOVERY_DEST = "Audio/ME/BLUE_HOENN_Recovery.ogg"

# Maps that share one theme in the donor use the same audio file and loop.
# Cave of Origin B1F inherits the theme of the floor above it.
MAP_GROUPS = {
    "BattleTent": (40, 52, 57),
    "Birch": (11,),
    "CaveOrigin": (191, 192, 238, 239, 240),
    "Center": (13, 17, 22, 29, 34, 42, 49, 54, 59, 65, 71, 77, 84, 89, 92, 93),
    "Chimney": (178, 179, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 241, 242, 243, 244, 245, 246, 247, 248),
    "Contest": (75,),
    "Dewford": (28, 30, 112),
    "Evergrande": (91, 322),
    "Fallarbor": (53, 56, 126),
    "Fortree": (64, 67),
    "GameCorner": (46,),
    "Gym": (20, 27, 31, 47, 63, 68, 82, 87, 94, 95, 96, 97, 98),
    "HallRoom": (99,),
    "Hideout": (182, 183, 184, 185, 186, 187, 188, 189, 215, 216, 217),
    "Lilycove": (69, 70, 73, 88, 90),
    "LilycoveMuseum": (74,),
    "Littleroot": (7, 8),
    "Mart": (14, 18, 23, 35, 43, 50, 55, 60, 66, 72, 78, 85),
    "OceanicMuseum": (39,),
    "Oldale": (12, 58, 61, 62),
    "Petalburg": (16, 19, 105, 106),
    "Pyre": (206, 207, 208, 209, 210, 211),
    "PyreExterior": (212, 213),
    "Route101": (101, 102, 103),
    "Route104": (104, 108, 111, 130),
    "Route110": (113, 114, 117, 121, 122, 132, 134),
    "Route113": (123, 125, 128),
    "Route119": (135,),
    "Route120": (138, 139, 141, 144, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155),
    "Rustboro": (21, 24, 26, 41, 44, 45, 76, 79, 80, 81, 118, 120, 124, 131, 133, 136, 137),
    "School": (25,),
    "Slateport": (32, 33, 36, 37, 38, 115),
    "Sootopolis": (83, 86),
    "Underwater": (255, 258, 259, 260, 261, 262, 263, 266),
    "Verdanturf": (48, 51),
    "VictoryRoad": (100, 250, 251, 252),
    "Woods": (156, 157, 159, 160, 161, 162, 177, 180),
}

MAP_BGM = {mid: label for label, maps in MAP_GROUPS.items() for mid in maps}
AUDIO_LABELS = tuple(BGM)


def bgm_source(track: str) -> str:
    name = track if track.startswith("RSE ") else f"ORAS {track}"
    return f"Audio/BGM/{name}.ogg"
