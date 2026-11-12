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
