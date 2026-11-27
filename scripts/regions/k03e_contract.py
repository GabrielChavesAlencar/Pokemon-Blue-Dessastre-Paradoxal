"""Pinned K03-E identities; opt-in isolated compiler contract."""
MAPS = {23: "DIGLETT_ENTRANCE_ROUTE_2", 79: "ROUTE_11",
        81: "DIGLETT_ENTRANCE_ROUTE_11", 82: "DIGLETT_TUNNEL"}
NAMES = {"DIGLETT_ENTRANCE_ROUTE_2": "Caverna dos Diglett — entrada Rota 2",
         "ROUTE_11": "Rota 11",
         "DIGLETT_ENTRANCE_ROUTE_11": "Caverna dos Diglett — entrada Rota 11",
         "DIGLETT_TUNNEL": "Caverna dos Diglett — túnel"}
TRAINERS = {2: ("YOUNGSTER", "Dave"), 5: ("YOUNGSTER", "Eddie"),
            7: ("YOUNGSTER", "Dillon"), 9: ("GAMBLER", "Jasper"),
            10: ("ENGINEER", "Bernie"), 11: ("ENGINEER", "Braxton"),
            12: ("GAMBLER", "Hugo"), 13: ("GAMBLER", "Darian"),
            15: ("YOUNGSTER", "Yasu"), 16: ("GAMBLER", "Dirk")}
PBS_TRAINERS = {f"{kind},{name}": (kind, name, 0) for kind, name in TRAINERS.values()}
# Local approved substitutes: the soundtrack catalog has no distinct
# Route 11 or Diglett track. Retain source encounter/battle balance.
MUSIC = [{"map": MAPS[sid], "track": 32 if sid == 79 else 34, "enabled": True}
         for sid in MAPS]
WARPS = {(18,1):(23,10,10,8), (23,2):(82,9,6,0),
         (23,3):(18,33,12,0), (79,1):(81,10,10,8),
         (81,4):(82,88,74,0), (81,6):(79,6,18,0),
         (82,1):(23,12,8,0), (82,2):(81,12,8,0)}
ITEMS = {6:"AWAKENING", 8:"XDEFENSE", 14:"ESCAPEROPE", 17:"GREATBALL"}

def candidate_manifest(baseline):
    if len(baseline["maps"]) != 156 or set(map(int, baseline["maps"])) & MAPS.keys():
        raise ValueError("K03-E baseline changed")
    return {**baseline, "maps": {**baseline["maps"], **{str(i): k for i,k in MAPS.items()}}}

def migration_game(root):
    return (root / ".blue-work/kanto-k03e-migration-ci/game").resolve()

def migration_pilot(root):
    return (root / ".blue-work/kanto-k03e-migration-ci/rebuilt-pilot").resolve()

def require_migration_game(root, game):
    import os
    if os.getenv("GITHUB_ACTIONS") != "true" or game.resolve() != migration_game(root):
        raise ValueError("K03-E candidate migration is restricted to its disposable CI game")
