"""Export only the audited pilot facts and rosters for the public Kanto guide."""
import argparse
import json
from pathlib import Path

from audit import KANTO, ROOT, json_file
from pilot_catalog import prepared_plan
from pbs import read_blocks

LOCATION_NAMES = {
    "PALLET_TOWN": "Pallet Town",
    "OAK_LAB": "Laboratório do Professor Oak",
    "PLAYER_HOME": "Casa do jogador",
    "ROUTE_1": "Rota 1",
    "VIRIDIAN_CITY": "Viridian City",
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
    "ROUTE_5": "Rota 5",
    "UNDERGROUND_NORTH": "Passagem Subterrânea — entrada norte",
    "UNDERGROUND_TUNNEL": "Passagem Subterrânea — túnel",
    "ROUTE_6": "Rota 6",
    "UNDERGROUND_SOUTH": "Passagem Subterrânea — entrada sul",
    "VERMILION_CITY": "Vermilion City",
    "VERMILION_CENTER": "Centro Pokémon de Vermilion",
    "VERMILION_MART": "Poké Mart de Vermilion",
    "VERMILION_GYM": "Ginásio de Vermilion",
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
    "FUCHSIA_WARDEN_HOUSE": "Casa do Warden (prévia)",
    "FUCHSIA_SAFARI_GATE": "Portão da Safari Zone — entrada de captura indisponível",
    "SAFARI_SOUTH": "Safari Zone — setor sul (prévia)",
    "SAFARI_REST_SOUTH": "Safari Zone — casa de descanso sul (prévia)",
    "SAFARI_EAST": "Safari Zone — setor leste (prévia)",
    "SAFARI_REST_EAST": "Safari Zone — casa de descanso leste (prévia)",
    "SAFARI_NORTH": "Safari Zone — setor norte (prévia)",
    "SAFARI_REST_NORTH": "Safari Zone — casa de descanso norte (prévia)",
    "SAFARI_WEST": "Safari Zone — setor oeste (prévia)",
    "SAFARI_REST_WEST": "Safari Zone — casa de descanso oeste (prévia)",
    "SAFARI_SECRET_HOUSE": "Safari Zone — Secret House (prévia)",
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
    "SAFFRON_CITY": "Saffron City (prévia)",
    "SAFFRON_CENTER": "Centro Pokémon de Saffron (prévia)",
    "SAFFRON_MART": "Poké Mart de Saffron (prévia)",
    "SAFFRON_GYM": "Ginásio de Saffron — Sabrina não ativa (prévia)",
    "SAFFRON_DOJO": "Fighting Dojo (prévia)",
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
    "SILPH_ELEVATOR": "Silph Co. — elevador (prévia)",
    "SILPH_1F": "Silph Co. — 1F (prévia)",
    "SILPH_2F": "Silph Co. — 2F (prévia)",
    "SILPH_3F": "Silph Co. — 3F (prévia)",
    "SILPH_4F": "Silph Co. — 4F (prévia)",
    "SILPH_5F": "Silph Co. — 5F (prévia)",
    "SILPH_6F": "Silph Co. — 6F (prévia)",
    "SILPH_7F": "Silph Co. — 7F (prévia)",
    "SILPH_8F": "Silph Co. — 8F (prévia)",
    "SILPH_9F": "Silph Co. — 9F (prévia)",
    "SILPH_10F": "Silph Co. — 10F (prévia)",
    "SILPH_11F": "Silph Co. — 11F (prévia)",
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


STARTERS = {11: "BULBASAUR", 12: "CHARMANDER", 13: "SQUIRTLE"}


def slug(key):
    return "kanto-" + key.lower().replace("_", "-")


def export(preview: Path):
    manifest = json_file(KANTO)
    if (preview / "plan.json").is_file():
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
    if set(keys_by_id.values()) != set(LOCATION_NAMES) or len(keys_by_id) != len(LOCATION_NAMES):
        raise ValueError("Kanto map catalog differs from the audited preview.")
    locations = {
        key: {"id": slug(key), "name": name, "methods": [], "trainers": []}
        for key, name in LOCATION_NAMES.items()
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
        if any(sum(slot["chance"] for slot in method["slots"]) != 100 for method in methods):
            raise ValueError(f"Invalid encounter chances in {header}")

    trainers = {}
    for header, lines in read_blocks(trainer_file).items():
        trainer_type, name, version = header.split(",")
        kind = trainer_type.removeprefix("BLUE_KANTO_")
        key, role = TRAINER_LOCATIONS.get((kind, name), TRAINER_LOCATIONS.get(kind, (None, None)))
        if key is None:
            raise ValueError(f"Trainer location has not been audited: {header}")
        trainer_id = slug(name)
        if trainer_id not in trainers:
            trainers[trainer_id] = {"id": trainer_id, "name": name, "role": role,
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
    return {"version": 1, "source": {"name": manifest["name"], "url": manifest["source"],
                                      "author": manifest["author"]},
            "locations": list(locations.values()), "trainers": list(trainers.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", type=Path, default=ROOT / ".blue-work/kanto-preview")
    parser.add_argument("--output", type=Path, default=ROOT / "site/public/data/kanto.json")
    parser.add_argument("--print-preview-chunks", action="store_true",
                        help="Emit source-derived website JSON for manual review in CI logs")
    args = parser.parse_args()
    data = export(args.preview)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if args.print_preview_chunks:
        raw = json.dumps(data, ensure_ascii=True, separators=(",", ":"))
        for index in range(0, len(raw), 2500):
            print(f"KANTO_PORTAL_PART_{index // 2500:03d}:" + raw[index:index + 2500])


if __name__ == "__main__":
    main()
