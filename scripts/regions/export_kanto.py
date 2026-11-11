"""Export only the audited pilot facts and rosters for the public Kanto guide."""
import argparse
import json
from pathlib import Path

from audit import KANTO, ROOT, json_file
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
}
TRAINER_LOCATIONS = {
    "RIVAL": ("OAK_LAB", "Rival"),
    "BUGCATCHER": ("VIRIDIAN_FOREST", "Caçador de insetos"),
    "CAMPER": ("PEWTER_GYM", "Campista"),
    "LEADER": ("PEWTER_GYM", "Líder de ginásio"),
}
STARTERS = {11: "BULBASAUR", 12: "CHARMANDER", 13: "SQUIRTLE"}


def slug(key):
    return "kanto-" + key.lower().replace("_", "-")


def export(preview: Path):
    plan = json_file(preview / "plan.json")
    manifest = json_file(KANTO)
    if plan["package_sha256"] != manifest["sha256"] or plan["region"] != manifest["region"]:
        raise ValueError("Kanto preview source does not match the project manifest.")
    keys_by_id = {row["proposed_id"]: row["key"].removeprefix("KANTO_") for row in plan["maps"]}
    if set(keys_by_id.values()) != set(LOCATION_NAMES) or len(keys_by_id) != len(LOCATION_NAMES):
        raise ValueError("Kanto map catalog differs from the audited preview.")
    locations = {
        key: {"id": slug(key), "name": name, "methods": [], "trainers": []}
        for key, name in LOCATION_NAMES.items()
    }
    for header, lines in read_blocks(preview / "drafts/encounters.txt").items():
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
    for header, lines in read_blocks(preview / "drafts/trainers.txt").items():
        trainer_type, name, version = header.split(",")
        kind = trainer_type.removeprefix("BLUE_KANTO_")
        key, role = TRAINER_LOCATIONS[kind]
        trainer_id = slug(name)
        if trainer_id not in trainers:
            trainers[trainer_id] = {"id": trainer_id, "name": name, "role": role,
                                    "location": slug(key), "leader": kind == "LEADER",
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
    args = parser.parse_args()
    data = export(args.preview)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()
