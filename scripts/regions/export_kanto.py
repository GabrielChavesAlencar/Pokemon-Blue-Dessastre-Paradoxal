"""Export only the audited pilot facts and rosters for the public Kanto guide."""
import argparse
import json
from pathlib import Path

from audit import KANTO, ROOT, json_file
from pilot_catalog import prepared_plan
from pbs import read_blocks, ENCOUNTER_REVIEW_SOURCE_IDS
from k03e_contract import MAPS, NAMES, TRAINERS, candidate_manifest
from k04_corridor import MAPS as K04_MAPS, NAMES as K04_NAMES, TRAINERS as K04_TRAINERS, publication_catalog

LOCATION_NAMES = {
    "PALLET_TOWN": "Pallet Town",
    "OAK_LAB": "Laboratório do Professor Oak",
    "PLAYER_HOME": "Casa do jogador",
    "ROUTE_1": "Rota 1",
    "VIRIDIAN_CITY": "Viridian City",
    "VIRIDIAN_GYM": "Ginásio de Viridian — Giovanni",
    "VIRIDIAN_CENTER": "Centro Pokémon de Viridian",
    "VIRIDIAN_MART": "Poké Mart de Viridian",
    "ROUTE_2": "Rota 2",
    "FOREST_GATE_SOUTH": "Portaria sul da Floresta de Viridian",
    "FOREST_GATE_NORTH": "Portaria norte da Floresta de Viridian",
    "VIRIDIAN_FOREST": "Floresta de Viridian",
    "PEWTER_CITY": "Pewter City",
    "PEWTER_GYM": "Ginásio de Pewter",
    "PEWTER_CENTER": "Centro Pokémon de Pewter",
    "PEWTER_MART": "Poké Mart de Pewter",
    "ROUTE_3": "Rota 3",
    "ROUTE_4": "Rota 4",
    "MT_MOON_CENTER": "Centro Pokémon de Mt. Moon",
    "MT_MOON_1F": "Mt. Moon — 1F",
    "MT_MOON_B1F": "Mt. Moon — B1F",
    "MT_MOON_B2F": "Mt. Moon — B2F",
    "CERULEAN_CITY": "Cerulean City",
    "CERULEAN_CENTER": "Centro Pokémon de Cerulean",
    "CERULEAN_MART": "Poké Mart de Cerulean",
    "CERULEAN_GYM": "Ginásio de Cerulean",
    "CERULEAN_BIKE_SHOP": "Loja de bicicletas de Cerulean",
    "CERULEAN_HOUSE_A": "Casa de Cerulean (A)",
    "CERULEAN_HOUSE_B": "Casa de Cerulean (B)",
    "CERULEAN_HOUSE_C": "Casa de Cerulean (C)",
    "CERULEAN_HOUSE_D": "Casa de Cerulean (D)",
    "CERULEAN_RANSACKED_HOUSE": "Casa roubada de Cerulean",
    "ROUTE_24": "Rota 24 — Nugget Bridge",
    "ROUTE_25": "Rota 25 — caminho para Bill",
    "BILL_COTTAGE": "Casa do Bill",
    "DAY_CARE": "Creche Pokémon",
    "ROUTE_5": "Rota 5",
    "UNDERGROUND_NORTH": "Passagem Subterrânea — entrada norte",
    "UNDERGROUND_TUNNEL": "Passagem Subterrânea — túnel",
    "ROUTE_6": "Rota 6",
    "UNDERGROUND_SOUTH": "Passagem Subterrânea — entrada sul",
    "VERMILION_CITY": "Vermilion City",
    "VERMILION_CENTER": "Centro Pokémon de Vermilion",
    "VERMILION_MART": "Poké Mart de Vermilion",
    "VERMILION_GYM": "Ginásio de Vermilion",
    "VERMILION_FAN_CLUB": "Fã-Clube Pokémon de Vermilion",
    "VERMILION_HOUSE_A": "Casa de Vermilion A",
    "VERMILION_HOUSE_B": "Casa de Vermilion B",
    "VERMILION_FISHERMAN_HOUSE": "Casa do pescador de Vermilion",
    "VERMILION_HARBOR": "Porto de Vermilion",
    "SS_ANNE_1F": "S.S. Anne — 1F",
    "SS_ANNE_2F": "S.S. Anne — 2F",
    "SS_ANNE_CAPTAIN": "S.S. Anne — cabine do capitão",
    "SS_ANNE_B1F": "S.S. Anne — B1F",
    "SS_ANNE_DECK": "S.S. Anne — convés",
    "ROUTE_7": "Rota 7",
    "CELADON_CITY": "Celadon City",
    "CELADON_CENTER": "Centro Pokémon de Celadon",
    "CELADON_DEPT_1F": "Loja de Celadon — 1F (prévia)",
    "CELADON_DEPT_2F": "Loja de Celadon — 2F (prévia)",
    "CELADON_DEPT_3F": "Loja de Celadon — 3F (prévia)",
    "CELADON_DEPT_4F": "Loja de Celadon — 4F (prévia)",
    "CELADON_DEPT_5F": "Loja de Celadon — 5F (prévia)",
    "CELADON_DEPT_ROOF": "Loja de Celadon — terraço (prévia)",
    "CELADON_DEPT_ELEVATOR": "Loja de Celadon — elevador (prévia)",
    "CELADON_GYM": "Ginásio de Celadon — Erika",
    "ROUTE_18_FUCHSIA": "Rota 18 — trecho Fuchsia (prévia)",
    "ROUTE_18_GATE": "Portaria da Rota 18 (prévia)",
    "ROUTE_18_CYCLING": "Rota 18 — trecho Cycling Road (prévia)",
    "FUCHSIA_CITY": "Fuchsia City",
    "FUCHSIA_CENTER": "Centro Pokémon de Fuchsia",
    "FUCHSIA_MART": "Poké Mart de Fuchsia",
    "FUCHSIA_GYM": "Ginásio de Fuchsia — Koga",
    "FUCHSIA_WARDEN_HOUSE": "Casa do Warden",
    "FUCHSIA_SAFARI_GATE": "Portão da Safari Zone",
    "SAFARI_SOUTH": "Safari Zone — setor sul",
    "SAFARI_REST_SOUTH": "Safari Zone — casa de descanso sul",
    "SAFARI_EAST": "Safari Zone — setor leste",
    "SAFARI_REST_EAST": "Safari Zone — casa de descanso leste",
    "SAFARI_NORTH": "Safari Zone — setor norte",
    "SAFARI_REST_NORTH": "Safari Zone — casa de descanso norte",
    "SAFARI_WEST": "Safari Zone — setor oeste",
    "SAFARI_REST_WEST": "Safari Zone — casa de descanso oeste",
    "SAFARI_SECRET_HOUSE": "Safari Zone — Secret House",
    "ROUTE_15": "Rota 15 (prévia)",
    "ROUTE_15_GATE": "Portaria da Rota 15 (prévia)",
    "SAFFRON_GATE_NORTH": "Portaria norte de Saffron (prévia)",
    "SAFFRON_GATE_SOUTH": "Portaria sul de Saffron (prévia)",
    "ROUTE_8": "Rota 8 (prévia)",
    "SAFFRON_GATE_EAST": "Portaria leste de Saffron (prévia)",
    "UNDERGROUND_ROUTE8_EAST": "Passagem Subterrânea leste — entrada (prévia)",
    "UNDERGROUND_ROUTE8_TUNNEL": "Passagem Subterrânea leste — túnel (prévia)",
    "SAFFRON_GATE_WEST": "Portaria oeste de Saffron (prévia)",
    "UNDERGROUND_ROUTE7_WEST": "Passagem Subterrânea oeste — entrada (prévia)",
    "SAFFRON_CITY": "Saffron City",
    "SAFFRON_CENTER": "Centro Pokémon de Saffron",
    "SAFFRON_MART": "Poké Mart de Saffron",
    "SAFFRON_GYM": "Ginásio de Saffron — Sabrina",
    "SAFFRON_DOJO": "Fighting Dojo",
    "SAFFRON_HOUSE_A": "Casa de Saffron A (prévia)",
    "SAFFRON_HOUSE_B": "Casa de Saffron B (prévia)",
    "SAFFRON_HOUSE_C": "Casa de Saffron C (prévia)",
    "SAFFRON_TRAINER_FAN_CLUB": "Clube de Treinadores Pokémon de Saffron (prévia)",
    "RIVALS_HOUSE": "Casa do rival em Pallet",
    "VIRIDIAN_HOUSE_NORTH": "Casa de Viridian — entrada norte",
    "VIRIDIAN_HOUSE_SOUTH": "Casa de Viridian — entrada sul",
    "ROUTE2_SECRET_GATEHOUSE": "Portaria secreta da Rota 2",
    "ROUTE2_HIDDEN_HOUSE": "Casa escondida da Rota 2",
    "PEWTER_MUSEUM": "Museu de Pewter",
    "PEWTER_HOUSE_NORTH": "Casa de Pewter — entrada norte",
    "PEWTER_HOUSE_SOUTH": "Casa de Pewter — entrada sul",
    "SILPH_LOBBY": "Silph Co. — recepção (prévia)",
    "SILPH_ELEVATOR": "Silph Co. — elevador",
    "SILPH_1F": "Silph Co. — 1F",
    "SILPH_2F": "Silph Co. — 2F",
    "SILPH_3F": "Silph Co. — 3F",
    "SILPH_4F": "Silph Co. — 4F",
    "SILPH_5F": "Silph Co. — 5F",
    "SILPH_6F": "Silph Co. — 6F",
    "SILPH_7F": "Silph Co. — 7F",
    "SILPH_8F": "Silph Co. — 8F",
    "SILPH_9F": "Silph Co. — 9F",
    "SILPH_10F": "Silph Co. — 10F",
    "SILPH_11F": "Silph Co. — 11F",
    "ROUTE_19": "Rota 19 (prévia aquática)",
    "ROUTE_20": "Rota 20 (prévia aquática)",
    "SEAFOAM_1F": "Seafoam Islands — 1F (prévia)",
    "SEAFOAM_B1F": "Seafoam Islands — B1F (prévia)",
    "SEAFOAM_B2F": "Seafoam Islands — B2F (prévia)",
    "SEAFOAM_B3F": "Seafoam Islands — B3F (prévia)",
    "SEAFOAM_B4F": "Seafoam Islands — B4F (prévia)",
    "ROUTE_21": "Rota 21 (prévia aquática)",
    "CINNABAR_ISLAND": "Cinnabar Island",
    "CINNABAR_CENTER": "Centro Pokémon de Cinnabar",
    "CINNABAR_MART": "Poké Mart de Cinnabar",
    "CINNABAR_GYM": "Ginásio de Cinnabar — Blaine",
    "CINNABAR_LAB": "Laboratório de Cinnabar (prévia de salas)",
    "MANSION_1F": "Pokémon Mansion — 1F",
    "MANSION_2F": "Pokémon Mansion — 2F",
    "MANSION_3F": "Pokémon Mansion — 3F",
    "MANSION_B1F": "Pokémon Mansion — B1F",
    "ROUTE_22": "Rota 22 — acesso ao Plateau",
    "INDIGO_GATE": "Portaria da Liga Pokémon",
    "ROUTE_23": "Rota 23 — oito postos de insígnias",
    "VICTORY_ROAD_HUB": "Victory Road — hub vazio (prévia)",
    "VICTORY_ROAD_1F": "Victory Road — 1F",
    "VICTORY_ROAD_2F": "Victory Road — 2F",
    "VICTORY_ROAD_3F": "Victory Road — 3F",
    "INDIGO_PLATEAU": "Indigo Plateau",
    "INDIGO_LOBBY": "Indigo Plateau — Saguão da Liga",
    "ELITE_LORELEI_ROOM": "Elite Four — sala de Lorelei",
    "ELITE_BRUNO_ROOM": "Elite Four — sala de Bruno",
    "ELITE_AGATHA_ROOM": "Elite Four — sala de Agatha",
    "ELITE_LANCE_ROOM": "Elite Four — sala de Lance",
    "CHAMPION_HALL": "Sala do Campeão Blue",
    "HALL_OF_FAME": "Hall of Fame — Kanto",
}
TRAINER_LOCATIONS = {
    "RIVAL": ("OAK_LAB", "Rival"),
    "BUGCATCHER": ("VIRIDIAN_FOREST", "Caçador de insetos"),
    "CAMPER": ("PEWTER_GYM", "Campista"),
    "LEADER": ("PEWTER_GYM", "Líder de ginásio"),
}
TRAINER_LOCATIONS.update({
    **{("BUGCATCHER", name): ("ROUTE_3", "Caçador de insetos")
       for name in ("Colton", "Greg", "James")},
    **{("BUGCATCHER", name): ("MT_MOON_1F", "Caçador de insetos")
       for name in ("Kent", "Robby")},
    **{("LASS", name): ("ROUTE_3", "Treinadora")
       for name in ("Janice", "Sally", "Robin")},
    **{("LASS", name): ("MT_MOON_1F", "Treinadora")
       for name in ("Iris", "Miriam")},
    **{("YOUNGSTER", name): ("ROUTE_3", "Jovem treinador")
       for name in ("Ben", "Calvin")},
    ("YOUNGSTER", "Josh"): ("MT_MOON_1F", "Jovem treinador"),
    ("SUPERNERD", "Jovan"): ("MT_MOON_1F", "Super Nerd"),
    ("SUPERNERD", "Miguel"): ("MT_MOON_B2F", "Super Nerd"),
    ("HIKER", "Marcos"): ("MT_MOON_1F", "Montanhista"),
    ("ROCKET", "Grunt"): ("MT_MOON_B2F", "Equipe Rocket"),
    ("SWIMMER", "Luis"): ("CERULEAN_GYM", "Nadador"),
    ("PICNICKER", "Diana"): ("CERULEAN_GYM", "Piqueniqueira"),
    ("LEADER_MISTY", "Misty"): ("CERULEAN_GYM", "Líder de ginásio"),
})


TRAINER_LOCATIONS.update({
    **{("BUGCATCHER", name): ("ROUTE_6", "Caçador de insetos")
       for name in ("Keigo", "Elijah")},
    **{("PICNICKER", name): ("ROUTE_6", "Piqueniqueira")
       for name in ("Nancy", "Isabelle")},
    **{("CAMPER", name): ("ROUTE_6", "Campista")
       for name in ("Ricky", "Jeff")},
    ("SAILOR", "Dwayne"): ("VERMILION_GYM", "Marinheiro"),
    ("ENGINEER", "Bailey"): ("VERMILION_GYM", "Engenheiro"),
    ("GENTLEMAN", "Tucker"): ("VERMILION_GYM", "Cavalheiro"),
    ("LEADER_SURGE", "Lt. Surge"): ("VERMILION_GYM", "Líder de ginásio"),
    **{("GENTLEMAN", name): ("SS_ANNE_1F", "Cavalheiro")
       for name in ("Thomas", "Arthur")},
    ("LASS", "Ann"): ("SS_ANNE_1F", "Treinadora"),
    ("YOUNGSTER", "Tyler"): ("SS_ANNE_1F", "Jovem treinador"),
    ("GENTLEMAN", "Brooks"): ("SS_ANNE_2F", "Cavalheiro"),
    ("GENTLEMAN", "Lamar"): ("SS_ANNE_2F", "Cavalheiro"),
    ("FISHERMAN", "Dale"): ("SS_ANNE_2F", "Pescador"),
    ("LASS", "Dawn"): ("SS_ANNE_2F", "Treinadora"),
    ("FISHERMAN", "Barny"): ("SS_ANNE_B1F", "Pescador"),
    **{("SAILOR", name): ("SS_ANNE_B1F", "Marinheiro")
       for name in ("Phillip", "Huey", "Dylan", "Duncan", "Leonard")},
    **{("SAILOR", name): ("SS_ANNE_DECK", "Marinheiro")
       for name in ("Trevor", "Edmond")},
})


TRAINER_LOCATIONS.update({
    ("LEADER_ERIKA", "Erika"): ("CELADON_GYM", "Líder de ginásio"),
    ("PICNICKER", "Tina"): ("CELADON_GYM", "Piqueniqueira"),
    ("LASS", "Kay"): ("CELADON_GYM", "Treinadora"),
    ("BEAUTY", "Bridget"): ("CELADON_GYM", "Beauty"),
    ("BEAUTY", "Tamia"): ("CELADON_GYM", "Beauty"),
    ("BEAUTY", "Lori"): ("CELADON_GYM", "Beauty"),
    ("LASS", "Lisa"): ("CELADON_GYM", "Treinadora"),
    ("COOLTRAINER_F", "Mary"): ("CELADON_GYM", "Treinadora experiente"),
})


TRAINER_LOCATIONS.update({
    ("LEADER_KOGA", "Koga"): ("FUCHSIA_GYM", "Líder de ginásio"),
    **{("JUGGLER", name): ("FUCHSIA_GYM", "Malabarista")
       for name in ("Nate", "Kayden", "Kirk", "Shawn")},
    **{("TAMER", name): ("FUCHSIA_GYM", "Domador")
       for name in ("Edgar", "Phil")},
})


TRAINER_LOCATIONS.update({
    ("LEADER_SABRINA", "Sabrina"): ("SAFFRON_GYM", "Líder de ginásio"),
    **{("PSYCHIC", name): ("SAFFRON_GYM", "Psíquico")
       for name in ("Cameron", "Preston", "Johan", "Tyron")},
    **{("CHANNELER", name): ("SAFFRON_GYM", "Médium")
       for name in ("Tasha", "Stacy", "Amanda")},
    **{("BLACKBELT", name): ("SAFFRON_DOJO", "Lutador")
       for name in ("Hideki", "Hitoshi", "Aaron", "Mike", "Koichi")},
    ("ROCKETBOSS", "Giovanni"): ("SILPH_11F", "Chefe da Equipe Rocket"),
    ("RIVAL_SILPH", "Blue"): ("SILPH_7F", "Rival"),
})

TRAINER_LOCATIONS.update({
    ("LEADER_BLAINE", "Blaine"): ("CINNABAR_GYM", "Líder de ginásio"),
    **{("BURGLAR", name): ("CINNABAR_GYM", "Ladrão")
       for name in ("Quinn", "Ramon", "Dusty")},
    **{("SUPERNERD", name): ("CINNABAR_GYM", "Super Nerd")
       for name in ("Erik", "Avery", "Derek", "Zac")},
    ("YOUNGSTER", "Johnson"): ("MANSION_1F", "Jovem treinador"),
    ("SCIENTIST", "Ted"): ("MANSION_1F", "Cientista"),
    ("BURGLAR", "Arnie"): ("MANSION_2F", "Ladrão"),
    ("BURGLAR", "Simon"): ("MANSION_3F", "Ladrão"),
    ("SCIENTIST", "Braydon"): ("MANSION_3F", "Cientista"),
    ("BURGLAR", "Lewis"): ("MANSION_B1F", "Ladrão"),
    ("SCIENTIST", "Ivan"): ("MANSION_B1F", "Cientista"),
})

TRAINER_LOCATIONS.update({
    ("LEADER_GIOVANNI", "Giovanni"): ("VIRIDIAN_GYM", "Líder de ginásio"),
    **{("BLACKBELT", name): ("VIRIDIAN_GYM", "Lutador")
       for name in ("Takashi", "Kiyo", "Atsushi")},
    **{("COOLTRAINER_M", name): ("VIRIDIAN_GYM", "Treinador experiente")
       for name in ("Samuel", "Yuji", "Warren")},
    **{("TAMER", name): ("VIRIDIAN_GYM", "Domador")
       for name in ("Cole", "Jason")},
})

TRAINER_LOCATIONS.update({
    **{("COOLTRAINER_F", name): (area, "Treinadora experiente")
       for area, names in (("VICTORY_ROAD_1F",("Naomi",)),
                           ("VICTORY_ROAD_3F",("Alexa","Caroline")))
       for name in names},
    **{("COOLTRAINER_M", name): (area, "Treinador experiente")
       for area, names in (("VICTORY_ROAD_1F",("Rolando",)),
                           ("VICTORY_ROAD_3F",("George","Colby")))
       for name in names},
    ("BLACKBELT","Daisuke"): ("VICTORY_ROAD_2F","Lutador"),
    ("TAMER","Vincent"): ("VICTORY_ROAD_2F","Domador"),
    ("JUGGLER","Nelson"): ("VICTORY_ROAD_2F","Malabarista"),
    ("JUGGLER","Gregory"): ("VICTORY_ROAD_2F","Malabarista"),
    ("POKEMANIAC","Dawson"): ("VICTORY_ROAD_2F","Pokémaníaco"),
    ("COOLCOUPLE","Ray & Tyra"): ("VICTORY_ROAD_3F","Dupla"),
    ("ELITE_LORELEI","Lorelei"): ("ELITE_LORELEI_ROOM","Elite Four"),
    ("ELITE_BRUNO","Bruno"): ("ELITE_BRUNO_ROOM","Elite Four"),
    ("ELITE_AGATHA","Agatha"): ("ELITE_AGATHA_ROOM","Elite Four"),
    ("ELITE_LANCE","Lance"): ("ELITE_LANCE_ROOM","Elite Four"),
    ("CHAMPION_BLUE","Blue"): ("CHAMPION_HALL","Campeão"),
})


# Source Map053/054: native FRLG teams and locations, no fabricated rosters.
TRAINER_LOCATIONS.update({
    **{(kind, name): ("ROUTE_24", role)
       for kind, role, names in (
           ("CAMPER", "Campista", ("Ethan", "Shane")),
           ("LASS", "Treinadora", ("Ali", "Reli")),
           ("YOUNGSTER", "Jovem treinador", ("Timmy",)),
           ("BUGCATCHER", "Caçador de insetos", ("Cale",)),
       ) for name in names},
    **{(kind, name): ("ROUTE_25", role)
       for kind, role, names in (
           ("HIKER", "Montanhista", ("Franklin", "Wayne", "Nob")),
           ("LASS", "Treinadora", ("Haley",)),
           ("YOUNGSTER", "Jovem treinador", ("Chad", "Joey", "Dan")),
           ("CAMPER", "Campista", ("Flint",)),
           ("PICNICKER", "Piqueniqueira", ("Kelsey",)),
       ) for name in names},
})

SILPH_GRUNT_FLOORS = {
    21: "SILPH_2F", 22: "SILPH_2F", 23: "SILPH_3F",
    24: "SILPH_4F", 25: "SILPH_4F", 26: "SILPH_5F",
    27: "SILPH_5F", 28: "SILPH_6F", 29: "SILPH_6F",
    30: "SILPH_7F", 31: "SILPH_7F", 32: "SILPH_7F",
    33: "SILPH_8F", 34: "SILPH_8F", 35: "SILPH_9F",
    36: "SILPH_9F", 37: "SILPH_10F",
    38: "SILPH_11F", 39: "SILPH_11F",
}


STARTERS = {1: "BULBASAUR", 2: "CHARMANDER", 3: "SQUIRTLE",
            11: "BULBASAUR", 12: "CHARMANDER", 13: "SQUIRTLE",
            41: "BULBASAUR", 42: "CHARMANDER", 43: "SQUIRTLE",
            51: "BULBASAUR", 52: "CHARMANDER", 53: "SQUIRTLE"}


def slug(key):
    return "kanto-" + key.lower().replace("_", "-")


def location_names(manifest):
    size = publication_catalog(manifest["maps"])
    names = {**LOCATION_NAMES, **NAMES} if size >= 160 else LOCATION_NAMES
    if size>=165:
        names={**names,**dict(zip(K04_MAPS.values(),K04_NAMES))}
    if size==178:
        from k05_contract import NAMES as lavender
        names={**names,**lavender}
    return names


def export(preview: Path, *, k03e=False, k05=False, manifest=None):
    manifest = json_file(KANTO) if manifest is None else manifest
    if k05:
        from build_k05_product import append_candidate
        manifest=append_candidate(manifest)
    if k03e:
        manifest = candidate_manifest(manifest)
    names = location_names(manifest)
    route11_roles = {}
    if "ROUTE_11" in names:
        roles = {"YOUNGSTER": "Jovem treinador", "GAMBLER": "Jogador", "ENGINEER": "Engenheiro"}
        route11_roles = {(kind, name): roles[kind] for kind, name in TRAINERS.values()}
    rock_roles = {}
    if "ROCK_TUNNEL_1F" in names:
        roles = {"PICNICKER": "Piqueniqueira", "HIKER": "Montanhista", "CAMPER": "Campista",
                 "BUGCATCHER": "Caça-Insetos", "POKEMANIAC": "Pokémaníaco"}
        for source, events in K04_TRAINERS.items():
            for profile in events.values():
                kind, name = profile.split(",")
                rock_roles[kind, name] = (K04_MAPS[source], roles[kind])
    tower_roles={}
    if "POKEMON_TOWER_1F" in names:
        from k05_contract import TOWER
        from k05_tower_actors import CHANNELERS
        for sid,rows in CHANNELERS.items():
            for name,_ in rows.values():
                tower_roles.setdefault(name,[]).append(TOWER[sid])
    if not k03e and not rock_roles and (preview / "plan.json").is_file():
        plan = json_file(preview / "plan.json")
        encounter_file = preview / "drafts/encounters.txt"
        trainer_file = preview / "drafts/trainers.txt"
    else:
        # The CI cleans the intermediate source staging directory. Export only
        # audited, compiled PBS from the final isolated Kanto pilot instead.
        plan = prepared_plan(preview, manifest)
        encounter_file = preview / "PBS/encounters_kanto.txt"
        trainer_file = preview / "PBS/trainers_kanto.txt"
    if plan["package_sha256"] != manifest["sha256"] or plan["region"] != manifest["region"]:
        raise ValueError("Kanto preview source does not match the project manifest.")
    keys_by_id = {row["proposed_id"]: row["key"].removeprefix("KANTO_") for row in plan["maps"]}
    if set(keys_by_id.values()) != set(names) or len(keys_by_id) != len(names):
        raise ValueError("Kanto map catalog differs from the audited preview.")
    # Release/UI flags are derived from the audited source manifest, never
    # from whether a preview happens to have visible encounters or trainers.
    preview_source_ids = set(manifest.get("preview_only", []))
    keys_by_source = {row["source_id"]: row["key"].removeprefix("KANTO_")
                      for row in plan["maps"]}
    status_by_key = {
        key: ("preview" if source in preview_source_ids else
              "encounter_review" if source in ENCOUNTER_REVIEW_SOURCE_IDS else
              "experimental")
        for source, key in keys_by_source.items()
    }
    locations = {
        key: {"id": slug(key), "name": name, "status": status_by_key[key],
              "methods": [], "trainers": []}
        for key, name in names.items()
    }
    for header, lines in read_blocks(encounter_file).items():
        key = keys_by_id[int(header)]
        methods = locations[key]["methods"]
        for line in lines:
            fields = line.strip().split(",")
            if fields[0].isdecimal():
                chance, species, lower, upper = fields
                methods[-1]["slots"].append({"species": species, "chance": int(chance),
                                             "min": int(lower), "max": int(upper)})
            else:
                methods.append({"id": fields[0], "slots": []})
        for method in methods:
            # The source FRLG kit uses explicit allowed-level lists. A slot
            # with gaps is expanded losslessly by integer weight scaling
            # before the game compiles PBS; totals then may be >100 (e.g.
            # 200 for an exact 45% / 55% encounter). The UI "chance" is
            # ALWAYS a normalized percentage, never the raw engine weight.
            total = sum(slot["chance"] for slot in method["slots"])
            if not total or any(slot["chance"] < 1 for slot in method["slots"]):
                raise ValueError(f"Invalid relative encounter weights in {header}")
            method["weightTotal"] = total
            for slot in method["slots"]:
                weight = slot["chance"]
                slot["weight"] = weight
                slot["chance"] = round(weight * 100 / total, 12)
            if abs(sum(slot["chance"] for slot in method["slots"]) - 100) > 1e-7:
                raise ValueError(f"Encounter percentage normalization drift: {header}")

    trainers = {}
    for header, lines in read_blocks(trainer_file).items():
        trainer_type, name, version = header.split(",")
        kind = trainer_type.removeprefix("BLUE_KANTO_")
        if kind == "RIVAL_TOWER" and int(version) in (51,52,53):
            key,role="POKEMON_TOWER_2F","Rival de Kanto"
            trainer_id,shown_name=slug("blue-tower"),"Gary (Pokémon Tower)"
        elif kind=="CHANNELER" and name in tower_roles and version=="0":
            key,role=tower_roles[name][0],"Médium"
            trainer_id,shown_name=slug(f"{key}-{name}"),name
        elif kind == "RIVAL" and int(version) in (31, 32, 33):
            key, role = "CERULEAN_CITY", "Rival de Kanto"
            trainer_id, shown_name = slug("blue_cerulean"), "Gary (Cerulean)"
        elif kind == "RIVAL" and int(version) in (41, 42, 43):
            key, role = "SS_ANNE_2F", "Rival de Kanto"
            trainer_id, shown_name = slug("blue_ss_anne"), "Gary (S.S. Anne)"
        elif kind == "ROCKET" and int(version) == 6:
            key, role = "CERULEAN_CITY", "Equipe Rocket"
            trainer_id, shown_name = slug("rocket_cerulean_house"), "Grunt (Cerulean)"
        elif kind == "ROCKET" and int(version) == 5:
            key, role = "ROUTE_24", "Equipe Rocket"
            trainer_id, shown_name = slug("rocket_route_24"), "Grunt (Nugget Bridge)"
        elif (kind, name) in route11_roles and version == "0":
            key, role = "ROUTE_11", route11_roles[kind, name]
            trainer_id, shown_name = slug(f"route-11-{name}"), name
        elif (kind, name) in rock_roles and version == "0":
            key, role = rock_roles[kind, name]
            trainer_id, shown_name = slug(f"{key}-{name}"), name
        elif kind == "ROCKET" and int(version) in SILPH_GRUNT_FLOORS:
            key, role = SILPH_GRUNT_FLOORS[int(version)], "Equipe Rocket"
            trainer_id, shown_name = slug(f"grunt-silph-{version}"), f"Grunt {version}"
        else:
            key, role = TRAINER_LOCATIONS.get((kind, name), TRAINER_LOCATIONS.get(kind, (None, None)))
            trainer_id = (slug("blue_champion") if kind == "CHAMPION_BLUE"
                           else slug("ray-tyra") if kind == "COOLCOUPLE"
                           else slug("giovanni_viridian") if kind == "LEADER_GIOVANNI"
                          else slug("blue_silph") if kind == "RIVAL_SILPH"
                          else slug(name))
            shown_name = "Blue (Silph)" if kind == "RIVAL_SILPH" else name
        if key is None:
            raise ValueError(f"Trainer location has not been audited: {header}")
        if trainer_id not in trainers:
            trainers[trainer_id] = {"id": trainer_id, "name": shown_name, "role": role,
                                    "location": slug(key), "leader": kind.startswith("LEADER"),
                                    "variants": []}
            locations[key]["trainers"].append(trainer_id)
        roster = []
        for line in lines:
            field, _, value = line.strip().partition(" = ")
            if field == "Pokemon":
                species, level = value.split(",")
                roster.append({"species": species, "level": int(level)})
            elif field == "Moves":
                roster[-1]["moves"] = value.split(",")
        if not roster:
            raise ValueError(f"Empty Kanto team for {header}")
        trainers[trainer_id]["variants"].append({"starter": STARTERS.get(int(version)), "team": roster})
    # Jody shares one compiled trainer profile but has separate native
    # encounters, event keys and locations on floors 4 and 5.
    for name,keys in tower_roles.items():
        if len(keys)<=1:
            continue
        original=trainers[slug(f"{keys[0]}-{name}")]
        for key in keys[1:]:
            ident=slug(f"{key}-{name}")
            trainers[ident]={**original,"id":ident,"location":slug(key)}
            locations[key]["trainers"].append(ident)
    return {"version": 1, "source": {"name": manifest["name"], "url": manifest["source"],
                                      "author": manifest["author"]},
            "locations": list(locations.values()), "trainers": list(trainers.values())}


def k03e_portal_delta(baseline: dict, candidate: dict) -> dict:
    """Only the four K03-E maps and their ten roster entries, never game assets."""
    from k03e_contract import MAPS, TRAINERS
    added_locations = {slug(key) for key in MAPS.values()}
    expected_trainers = {slug(f"route-11-{name}") for _, name in TRAINERS.values()}

    def indexed(data, key):
        values = {row["id"]: row for row in data[key]}
        if len(values) != len(data[key]):
            raise ValueError(f"Duplicate K03-E portal IDs: {key}")
        return values

    for key, expected in (("locations", added_locations), ("trainers", expected_trainers)):
        before, after = indexed(baseline, key), indexed(candidate, key)
        if after.keys() - before.keys() != expected or any(after.get(i) != row for i, row in before.items()):
            raise ValueError(f"K03-E portal changed historic {key} or missed audited additions")
    locations = [row for row in candidate["locations"] if row["id"] in added_locations]
    trainers = [row for row in candidate["trainers"] if row["id"] in expected_trainers]
    route = next(row for row in locations if row["id"] == slug("ROUTE_11"))
    cave = next(row for row in locations if row["id"] == slug("DIGLETT_TUNNEL"))
    if (set(route["trainers"]) != expected_trainers or len(route["trainers"]) != len(expected_trainers)
            or len(route["methods"]) != 6 or len(cave["methods"]) != 2
            or any(row["status"] != "experimental" for row in locations)):
        raise ValueError("K03-E portal route, tunnel or trainer evidence incomplete")
    return {"version": 1, "status": "CANDIDATE_NOT_PUBLISHED", "locations": locations, "trainers": trainers}



def k05_portal_delta(baseline, candidate):
    """Require old portal results byte-equivalent as data, with 14 new actors."""
    from k05_contract import MAPS, TOWER
    from k05_tower_actors import CHANNELERS
    locations={slug(k) for k in MAPS.values()}
    trainers={slug(f"{TOWER[sid]}-{name}") for sid,rows in CHANNELERS.items()
              for name,_ in rows.values()} | {slug("blue-tower")}
    added={}
    for field,new_ids in (("locations",locations),("trainers",trainers)):
        old={row["id"]:row for row in baseline[field]}
        final={row["id"]:row for row in candidate[field]}
        if (len(old)!=len(baseline[field]) or len(final)!=len(candidate[field]) or
                final.keys()-old.keys()!=new_ids or any(final.get(k)!=r for k,r in old.items())):
            raise ValueError(f"K05 changed released portal data or missed audited {field}")
        added[field]=[r for r in candidate[field] if r["id"] in new_ids]
    by_id={r["id"]:r for r in added["locations"]}
    for floor in range(1,8):
        record=by_id[slug(f"POKEMON_TOWER_{floor}F")]
        expected={"CaveDay","CaveNight"} if floor>=3 else set()
        if {m["id"] for m in record["methods"]}!=expected:
            raise ValueError(f"Unexpected K05 encounter table at floor {floor}")
    rival=next(r for r in added["trainers"] if r["id"]==slug("blue-tower"))
    versions={v["starter"]:v["team"][-1]["species"] for v in rival["variants"]}
    if versions!={"BULBASAUR":"CHARMELEON","CHARMANDER":"WARTORTLE","SQUIRTLE":"IVYSAUR"}:
        raise ValueError("K05 portal does not reflect the three original rival profiles")
    return {"status":"K05_PORTAL_NOT_PUBLISHED",**added}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", type=Path, default=ROOT / ".blue-work/kanto-preview")
    parser.add_argument("--output", type=Path, default=ROOT / "site/public/data/kanto.json")
    parser.add_argument("--print-preview-chunks", action="store_true",
                        help="Emit source-derived website JSON for manual review in CI logs")
    parser.add_argument("--k05-product-ci",action="store_true",help="Export isolated candidate to .blue-work only")
    args = parser.parse_args()
    if args.k05_product_ci:
        import os
        if (os.getenv("GITHUB_ACTIONS")!="true" or args.preview.resolve()!=(ROOT/".blue-work/kanto-k05-product").resolve()
                or args.output.resolve()!=(ROOT/".blue-work/kanto-k05-portal.json").resolve()):
            raise ValueError("K05 candidate portal must not overwrite published data")
    data = export(args.preview,k05=args.k05_product_ci)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if args.k05_product_ci:
        delta=k05_portal_delta(json_file(ROOT/"site/public/data/kanto.json"),data)
        args.output.with_name("kanto-k05-portal-delta.json").write_text(
            json.dumps(delta,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print("KANTO_K05_PORTAL_178_VERIFIED")
    if args.print_preview_chunks:
        raw = json.dumps(data, ensure_ascii=True, separators=(",", ":"))
        for index in range(0, len(raw), 2500):
            print(f"KANTO_PORTAL_PART_{index // 2500:03d}:" + raw[index:index + 2500])


if __name__ == "__main__":
    main()
