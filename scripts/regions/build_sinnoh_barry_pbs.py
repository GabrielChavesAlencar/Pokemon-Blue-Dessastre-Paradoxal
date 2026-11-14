#!/usr/bin/env python3
"""Prepare Barry's THREE starter-counter teams from local Blue PBS.

This does not execute Pokémon Essentials, install PBS, create the ready marker
or set a final trainer level. Level 5 is only a legal PBS starter seed; the
installed BlueCampaign/BlueStory runtime must be validated independently
before the pilot is playable (70% normal / 90% Master). Output is a NEW
private directory under .blue-work. Never write game/ or save files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

from pbs import catalogue, read_blocks

ROOT = Path(__file__).resolve().parents[2]
RIVAL_TYPE = "BLUE_SINNOH_RIVAL"
RIVAL_NAME = "Barry"
BASE_TYPE = "RIVAL1"
SEED_LEVEL = 5
STARTERS = ("TURTWIG", "CHIMCHAR", "PIPLUP")
MATCHUPS = (("TURTWIG", "CHIMCHAR"),
            ("CHIMCHAR", "PIPLUP"),
            ("PIPLUP", "TURTWIG"))
FILES = ("trainer_types.txt", "pokemon.txt", "moves.txt")
PBS_TYPE = "PBS/trainer_types_sinnoh_barry.txt"
PBS_TRAINERS = "PBS/trainers_sinnoh_barry.txt"
READY_MARKER = "Data/blue-sinnoh-rival-ready.txt"
SAFE_SYMBOL = re.compile(r"[A-Z][A-Z0-9_]{1,63}\Z")


def fail(message: str):
    raise ValueError("[SINNOH BARRY PBS] " + message)


def sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fields(lines: list[str], section: str) -> dict[str, str]:
    result = {}
    for raw in lines:
        clean = raw.split("#", 1)[0].strip()
        if not clean:
            continue
        key, sep, value = clean.partition("=")
        key, value = key.strip(), value.strip()
        if not sep or not key or not value or key in result:
            fail(f"Campo PBS incompleto/duplicado em {section}")
        result[key] = value
    return result


def legal_moves(species: str, values: dict[str, str], known: set[str]) -> list[str]:
    """Last four species moves learned at 0..5, never guess a learnset."""
    learnset = values.get("Moves", "").split(",")
    items = [part.strip() for part in learnset]
    if not items or len(items) % 2 or any(not x for x in items):
        fail(f"Learnset inválido para {species}")
    learned: list[str] = []
    for level_raw, move in zip(items[0::2], items[1::2]):
        if (not level_raw.isdecimal() or not 0 <= int(level_raw) <= 100
                or not SAFE_SYMBOL.fullmatch(move)):
            fail(f"Nível ou golpe inválido no learnset de {species}")
        if move not in known:
            fail(f"Golpe {move} de {species} não definido em moves*.txt do Blue")
        if int(level_raw) <= SEED_LEVEL:
            if move in learned:
                learned.remove(move)
            learned.append(move)
    if not learned:
        fail(f"Inicial {species} não possui golpe nativo até nível {SEED_LEVEL}")
    return learned[-4:]


def balance_contract(source: Path) -> dict:
    """Static provenance only; running Essentials still needs native QA."""
    if source.is_symlink() or not source.is_file():
        fail("BlueCampaign Balance/Scaling runtime não encontrado")
    body = source.read_text("utf-8")
    needed = (
        "module BlueCampaign",
        "def self.scaled_level(party,percent)",
        "master? ? 90 : 70",
        "def self.trainer_level(trainer,party=$player.party)",
        "level=BlueCampaign.trainer_level(",
        "pkmn.level=level",
        "BlueCampaign.active?",
    )
    if not all(part in body for part in needed):
        fail("Escala nativa 70%/90% do Blue não confirmada; não criar PBS isolado")
    return {
        "source": "scripts/battle_polish/Campaign.rb",
        "sha256": sha_bytes(source.read_bytes()),
        "normal_percent": 70,
        "master_percent": 90,
        "static_source_contract_checked": True,
        "active_in_actual_game_verified": False,
    }


def build(game: Path, *, root: Path = ROOT) -> tuple[dict, dict[str, bytes]]:
    game = game.expanduser().absolute()
    root = root.expanduser().absolute()
    workspace = root / ".blue-work"
    if (game.is_symlink() or not game.is_dir() or
            game.resolve().is_relative_to(workspace.resolve())):
        fail("Exigir instalação local Blue distinta de .blue-work")
    pbs = game / "PBS"
    if pbs.is_symlink() or not pbs.is_dir():
        fail("Pasta PBS real do Blue ausente ou symlink")
    natives = {key: pbs / key for key in FILES}
    for name, path in natives.items():
        if path.is_symlink() or not path.is_file():
            fail(f"PBS/{name} ausente ou symlink")
    # Follow the same requirements as Johto's native-v21 PBS builder.
    base = read_blocks(natives["trainer_types.txt"])
    if BASE_TYPE not in base:
        fail(f"Tipo nativo {BASE_TYPE} ausente em trainer_types.txt")
    rival_fields = fields(base[BASE_TYPE], BASE_TYPE)
    for required in ("Name", "Gender", "BaseMoney"):
        if not rival_fields.get(required):
            fail(f"Tipo {BASE_TYPE} sem campo {required}")
    for prefix in ("trainer_types", "trainers", "pokemon", "moves"):
        for path in sorted(pbs.glob(prefix + "*.txt")):
            if path.is_symlink() or not path.is_file():
                fail("PBS ligado a arquivo externo/symlink")
    for path in sorted(pbs.glob("trainer_types*.txt")):
        if RIVAL_TYPE in read_blocks(path):
            fail("BLUE_SINNOH_RIVAL já existe em trainer_types*.txt")
    for path in sorted(pbs.glob("trainers*.txt")):
        if any(key.split(",")[0] == RIVAL_TYPE for key in read_blocks(path)):
            fail("BLUE_SINNOH_RIVAL já existe em trainers*.txt")
    available = catalogue(game, "pokemon")
    sections = read_blocks(natives["pokemon.txt"], set(STARTERS))
    missing = set(STARTERS) - (available & set(sections))
    if missing:
        fail("Pokémon iniciais ausentes no PBS Blue: " + ", ".join(sorted(missing)))
    move_catalogue = catalogue(game, "moves")
    if not move_catalogue:
        fail("Catálogo moves*.txt está vazio")
    starter_moves = {}
    details = {}
    for species in STARTERS:
        values = fields(sections[species], species)
        for key in ("Types", "BaseStats", "Abilities", "Moves"):
            if not values.get(key):
                fail(f"{species}: PBS não tem {key}")
        stats = [v.strip() for v in values["BaseStats"].split(",")]
        if len(stats) != 6 or not all(v.isdecimal() and 1 <= int(v) <= 255 for v in stats):
            fail(f"{species}: BaseStats nativos inválidos")
        ability = values["Abilities"].split(",")[0].strip()
        types = [part.strip() for part in values["Types"].split(",")]
        if (not types or any(not SAFE_SYMBOL.fullmatch(t) for t in types)
                or not SAFE_SYMBOL.fullmatch(ability)):
            fail(f"{species}: tipos/habilidade do PBS nativo inválidos")
        starter_moves[species] = legal_moves(species, values, move_catalogue)
        details[species] = {
            "types": types, "base_stats": [int(v) for v in stats],
            "ability": ability,
            "learnset_0_to_5": starter_moves[species],
            "native_source": "PBS/pokemon.txt",
        }
    contract = balance_contract(root / "scripts/battle_polish/Campaign.rb")
    trainers = []
    versions = []
    for version, (player, barry) in enumerate(MATCHUPS):
        moves = starter_moves[barry]
        trainers += [
            f"# Sinnoh / inicial {player} => Barry {barry}",
            f"[{RIVAL_TYPE},{RIVAL_NAME},{version}]",
            f"Pokemon = {barry},{SEED_LEVEL}",
            "    Moves = " + ",".join(moves),
            "",
        ]
        versions.append({
            "version": version,
            "player_starter": player,
            "rival_species": barry,
            "seed_level_only": SEED_LEVEL,
            "effective_level": "BlueCampaign.trainer_level(player_party) at runtime",
            "moves_at_seed_level": moves,
            "handler": f'TrainerBattle.start(:{RIVAL_TYPE}, "Barry", {version})',
        })
    type_body = "\n".join([f"[{RIVAL_TYPE}]", *base[BASE_TYPE], ""])
    files = {
        PBS_TYPE: (type_body + "\n").encode("utf-8"),
        PBS_TRAINERS: ("\n".join(trainers)).encode("utf-8"),
    }
    from build_johto_rival_pbs_v2 import read_blocks_from_bytes
    sections_out = read_blocks_from_bytes(files[PBS_TRAINERS])
    if set(sections_out) != {f"{RIVAL_TYPE},{RIVAL_NAME},{i}" for i in range(3)}:
        fail("PBS de Barry não possui exatamente as três versões")
    for item in versions:
        name = f"{RIVAL_TYPE},{RIVAL_NAME},{item['version']}"
        expected = [
            f"Pokemon = {item['rival_species']},{SEED_LEVEL}",
            "    Moves = " + ",".join(item["moves_at_seed_level"]),
        ]
        if sections_out[name] != expected:
            fail("PBS gerado ficou incompleto: " + name)
    report = {
        "schema": 1, "region": "SINNOH",
        "stage": "BARRY_FIRST_RIVAL_3_VERSION_PBS_DRAFT",
        "status": "VALIDATED_NATIVE_PBS_DRAFT_NOT_COMPILED",
        "trainer_type": RIVAL_TYPE, "trainer_name": RIVAL_NAME,
        "versions": versions, "native_starters": details,
        "native_trainer_type_source": BASE_TYPE,
        "pbs_seed_level": SEED_LEVEL,
        "pbs_seed_is_not_final_battle_level": True,
        "balance": contract,
        "source_pbs_sha256": {
            name: sha_bytes(path.read_bytes()) for name, path in natives.items()
        },
        "files_sha256": {
            name: sha_bytes(payload) for name, payload in files.items()
        },
        "can_install": False, "pbs_compiled": False, "battle_proven": False,
        "dynamic_scaling_verified_in_game": False,
        "graphic_verified": False, "save_load_verified": False,
        "ready_marker_created": False,
        "ready_marker_filename": READY_MARKER,
        "ready_marker_allowed": False,
        "required_before_marker": [
            "Verificar os 3 blocos do PBS compilado realmente na cópia isolada do Game.exe",
            "Confirmar gráfico do treinador Barry na cópia experimental",
            "Testar as 3 escolhas e a espécie do rival correspondente no jogo",
            "Validar nível efetivo 70%/90% conforme maior nível, badges e modo Master",
            "Testar save/load e progressão com e sem vitória",
            "Só então permitir marcador no piloto; nunca no game/ principal",
        ],
    }
    return report, files


def publish(game: Path, output: Path, *, root: Path = ROOT) -> dict:
    root = root.expanduser().absolute()
    game = game.expanduser().absolute()
    output = output.expanduser().absolute()
    work = root / ".blue-work"
    if (root.is_symlink() or work.is_symlink() or output.is_symlink()
            or output.exists() or not output.is_relative_to(work)
            or output == work or game == output or game in output.parents):
        fail("Saída deve ser pasta NOVA dentro de .blue-work, fora de game/")
    report, files = build(game, root=root)
    work.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sinnoh-barry-pbs-", dir=output.parent) as tmp:
        stage = Path(tmp) / "stage"
        for path, contents in files.items():
            target = stage / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(contents)
        (stage / "sinnoh-barry-pbs-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if output.exists() or output.is_symlink():
            fail("Destino foi criado antes do commit da transação")
        stage.rename(output)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, default=ROOT / "game",
                        help="Instalação real Blue/PBS (somente leitura)")
    parser.add_argument("--output", type=Path,
                        default=ROOT / ".blue-work/sinnoh-barry-pbs-draft",
                        help="Pasta NOVA, privada, dentro de .blue-work")
    args = parser.parse_args(argv)
    try:
        report = publish(args.game, args.output)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        print("SINNOH_BARRY_PBS_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({
        "versions": report["versions"], "files_sha256": report["files_sha256"],
        "can_install": False, "pbs_compiled": False,
        "ready_marker_created": False, "draft_path": str(args.output)
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
