"""Pokémon Essentials v21.1 species validation and non-destructive creation.

No hard-coded Pokédex ID limit: official and fan species have distinct symbolic IDs.
This module never rewrites an existing species or uses GBA ROM slots.
"""
from __future__ import annotations

from pathlib import Path
import re

SPECIES_ID = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
HEADER = re.compile(r"^\[([^\]\r\n]+)\]\s*(?:#.*)?$", re.MULTILINE)
FIELD = re.compile(r"^[ \t]*([A-Za-z]\w*)[ \t]*=[ \t]*(.*)$", re.MULTILINE)
STATS = ("HP", "Attack", "Defense", "Speed", "Special Attack", "Special Defense")
DEFAULT_TYPES = ("NORMAL", "FIRE", "WATER", "ELECTRIC", "GRASS", "ICE", "FIGHTING",
                 "POISON", "GROUND", "FLYING", "PSYCHIC", "BUG", "ROCK", "GHOST",
                 "DRAGON", "DARK", "STEEL", "FAIRY")


class PokemonValidationError(ValueError):
    pass


def pbs_catalog(root: Path, prefix: str) -> set[str]:
    folder = root / "PBS"
    result: set[str] = set()
    if not folder.is_dir():
        return result
    for entry in folder.glob(prefix + "*.txt"):
        if not entry.is_file() or entry.is_symlink() or entry.stat().st_size > 10_000_000:
            continue
        text = entry.read_text(encoding="utf-8-sig")
        result.update(match.group(1).strip().upper() for match in HEADER.finditer(text))
    return result


def species_catalog(root: Path) -> set[str]:
    """Enumerate base species in pokemon*.txt, excluding pokemon_forms/metrics."""
    result: set[str] = set()
    folder = root / "PBS"
    for entry in folder.glob("pokemon*.txt"):
        if entry.name.startswith(("pokemon_forms", "pokemon_metrics")) or not entry.is_file():
            continue
        if entry.is_symlink() or entry.stat().st_size > 10_000_000:
            continue
        text = entry.read_text(encoding="utf-8-sig")
        result.update(match.group(1).strip().upper() for match in HEADER.finditer(text))
    return result


def parse_fields(raw: str) -> dict[str, str]:
    return {match.group(1): match.group(2).strip()
            for match in FIELD.finditer(raw)}


def _references(values: str) -> list[str]:
    return [part.strip().upper() for part in values.split(",") if part.strip()]


def validate_pokemon(root: Path, raw: str, *, check_references=True) -> dict:
    if not isinstance(raw, str) or len(raw) > 250_000:
        raise PokemonValidationError("Registro Pokémon vazio ou excessivamente grande.")
    match = HEADER.match(raw.lstrip("\ufeff"))
    if not match:
        raise PokemonValidationError("O registro deve começar com [ID_DA_ESPECIE].")
    species_id = match.group(1).strip().upper()
    if not SPECIES_ID.fullmatch(species_id):
        raise PokemonValidationError("ID inválido. Use letras maiúsculas, números e _.")
    if len(list(HEADER.finditer(raw))) != 1:
        raise PokemonValidationError("Cada cadastro deve conter apenas uma espécie.")
    f = parse_fields(raw)
    name = f.get("Name", "").strip()
    if not 1 <= len(name) <= 48 or any(c in name for c in "\r\n[]"):
        raise PokemonValidationError("Informe o nome do Pokémon (até 48 caracteres).")
    types = _references(f.get("Types", ""))
    if not 1 <= len(types) <= 2:
        raise PokemonValidationError("O Pokémon precisa de um ou dois tipos.")
    stats = _references(f.get("BaseStats", ""))
    if len(stats) != 6 or not all(v.isdigit() and 1 <= int(v) <= 255 for v in stats):
        raise PokemonValidationError("BaseStats exige seis atributos entre 1 e 255.")
    abilities = _references(f.get("Abilities", ""))
    if not abilities:
        raise PokemonValidationError("Informe ao menos uma habilidade em Abilities.")
    move_data = _references(f.get("Moves", ""))
    if len(move_data) % 2:
        raise PokemonValidationError("Moves deve conter pares: nível,golpe.")
    for index in range(0, len(move_data), 2):
        if not move_data[index].isdigit() or not 1 <= int(move_data[index]) <= 100:
            raise PokemonValidationError("Nível de golpe inválido: " + move_data[index])
    for number in ("CatchRate", "HatchSteps", "BaseExp", "Happiness"):
        v = f.get(number)
        if v is not None and (not v.isdigit() or int(v) < 0 or int(v) > 65535):
            raise PokemonValidationError(number + " precisa ser um inteiro positivo.")
    if check_references:
        valid_types = pbs_catalog(root, "types") or set(DEFAULT_TYPES)
        valid_abilities = pbs_catalog(root, "abilities")
        valid_moves = pbs_catalog(root, "moves")
        valid_species = species_catalog(root) | {species_id}
        for value in types:
            if value not in valid_types:
                raise PokemonValidationError("Tipo desconhecido: " + value)
        if valid_abilities:
            for value in abilities + _references(f.get("HiddenAbilities", "")):
                if value not in valid_abilities:
                    raise PokemonValidationError("Habilidade desconhecida: " + value)
        if valid_moves:
            for value in move_data[1::2] + _references(f.get("TutorMoves", "")) + _references(f.get("EggMoves", "")):
                if value not in valid_moves:
                    raise PokemonValidationError("Golpe desconhecido: " + value)
        evolution = _references(f.get("Evolutions", ""))
        if evolution and len(evolution) % 3 != 0:
            raise PokemonValidationError("Evolutions deve usar trios: espécie,método,parâmetro.")
        for value in evolution[0::3]:
            if value not in valid_species:
                raise PokemonValidationError("Evolução para espécie inexistente: " + value)
    return {"id": species_id, "name": name, "types": types, "baseStats": [int(n) for n in stats],
            "totalStats": sum(map(int, stats)), "abilities": abilities, "levelMoves": len(move_data)//2,
            "valid": True}


def make_species_raw(payload: dict) -> str:
    if not isinstance(payload, dict):
        raise PokemonValidationError("Dados do Pokémon inválidos.")
    species_id = str(payload.get("id", "")).upper().strip()
    if not SPECIES_ID.fullmatch(species_id):
        raise PokemonValidationError("ID: use 2 a 64 caracteres A-Z, 0-9 ou _.")
    name = str(payload.get("name", "")).strip()
    def string(key, default=""):
        value = str(payload.get(key, default)).strip()
        if len(value) > 1000 or any(c in value for c in "\r\n[]"):
            raise PokemonValidationError("Caracteres inválidos em " + key)
        return value
    typ1, typ2 = string("type1", "WATER").upper(), string("type2").upper()
    abilities = string("abilities", "SWIFTSWIM").upper()
    moves = string("moves", "1,TACKLE").upper()
    raw_stats = payload.get("stats", [70,70,70,70,70,70])
    if not isinstance(raw_stats, list) or len(raw_stats)!=6:
        raise PokemonValidationError("Informe seis atributos.")
    try:
        stats=[int(n) for n in raw_stats]
    except (TypeError, ValueError) as exc:
        raise PokemonValidationError("Atributos devem ser números.") from exc
    if any(n < 1 or n > 255 for n in stats):
        raise PokemonValidationError("Cada atributo deve ficar entre 1 e 255.")
    entries=[
      "[" + species_id + "]", "Name = " + name,
      "Types = " + ",".join([t for t in (typ1,typ2) if t]),
      "BaseStats = " + ",".join(map(str,stats)),
      "GenderRatio = " + string("gender", "Female50Percent"),
      "GrowthRate = " + string("growth", "Medium"),
      "BaseExp = " + string("baseExp", "150"),
      "EVs = " + string("evs", "ATTACK,1"),
      "CatchRate = " + string("catchRate", "45"),
      "Happiness = " + string("happiness", "70"),
      "Abilities = " + abilities, "Moves = " + moves,
      "EggGroups = " + string("eggGroups", "Field"),
      "HatchSteps = " + string("hatchSteps", "5120"),
      "Height = " + string("height", "1.0"),
      "Weight = " + string("weight", "25.0"),
      "Color = " + string("color", "Blue"),
      "Shape = " + string("shape", "Humanoid"),
      "Category = " + string("category", "Paradox"),
      "Pokedex = " + string("description", "Uma nova espécie."),
      "Generation = " + string("generation", "9"),
    ]
    if string("hiddenAbilities"):
        entries.insert(entries.index("Moves = " + moves), "HiddenAbilities = " + string("hiddenAbilities").upper())
    if string("tutorMoves"):
        entries.insert(entries.index("EggGroups = " + string("eggGroups", "Field")),
                       "TutorMoves = " + string("tutorMoves").upper())
    if string("evolutions"):
        entries.append("Evolutions = " + string("evolutions").upper())
    return "\n".join(entries) + "\n"


def create_species(root, backup_root, payload, *, lock, backup_file, atomic_write, read_text, file_hash):
    """Atomic-enough two-file creation under process lock, rolling back on second write failure."""
    raw = make_species_raw(payload)
    info = validate_pokemon(root, raw)
    root = Path(root)
    primary = root / "PBS" / "pokemon.txt"
    metrics = root / "PBS" / "pokemon_metrics.txt"
    if not primary.is_file():
        raise PokemonValidationError("PBS/pokemon.txt não encontrado. Instale o jogo base primeiro.")
    if not metrics.is_file():
        raise PokemonValidationError("PBS/pokemon_metrics.txt não encontrado.")
    with lock:
        if info["id"] in species_catalog(root):
            raise PokemonValidationError("Este ID já pertence a outra espécie. Escolha outro.")
        old_main, contents = read_text(primary)
        old_metrics, metrics_text = read_text(metrics)
        if any(m.group(1).strip().upper()==info["id"] for m in HEADER.finditer(metrics_text)):
            raise PokemonValidationError("Esse ID já existe em pokemon_metrics.txt.")
        newline = "\r\n" if "\r\n" in contents else "\n"
        append = "#-------------------------------" + newline + raw.replace("\n",newline)
        updated = contents.rstrip("\r\n") + newline + append
        metric = ("#-------------------------------\n[" + info["id"] + "]\n" +
                  "BackSprite = 0,0\nFrontSprite = 0,0\nAnimationSpeed = 0,0\n")
        new_metrics = metrics_text.rstrip("\r\n") + newline + metric.replace("\n",newline)
        def encode(old, data):
            return (b"\xef\xbb\xbf" if old.startswith(b"\xef\xbb\xbf") else b"") + data.encode("utf-8")
        backup_file(backup_root, "pokemon.txt", old_main)
        backup_file(backup_root, "pokemon_metrics.txt", old_metrics)
        atomic_write(primary, encode(old_main, updated))
        try:
            atomic_write(metrics, encode(old_metrics, new_metrics))
        except Exception:
            atomic_write(primary, old_main)
            raise
    return {**info, "created": True, "file": "pokemon.txt",
            "metricsFile": "pokemon_metrics.txt", "noReplacement": True}
