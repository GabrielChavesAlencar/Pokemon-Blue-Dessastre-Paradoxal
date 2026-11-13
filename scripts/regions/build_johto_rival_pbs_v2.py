"""Stage 09: build Silver's three PBS versions using installed Blue learnsets.

No Game.exe, no ready marker, no writes to game/, Kanto, Decades or saves.
Only publish to a NEW private .blue-work folder; battle QA is still required.
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
RIVAL_TYPE = "BLUE_JOHTO_RIVAL"
RIVAL_NAME = "Rival"
BASE_TYPE = "RIVAL1"
STARTERS = ("CHIKORITA", "CYNDAQUIL", "TOTODILE")
ROSTERS = (("CHIKORITA", "CYNDAQUIL"), ("CYNDAQUIL", "TOTODILE"),
           ("TOTODILE", "CHIKORITA"))
LEVEL = 5
SHA = re.compile(r"[0-9a-f]{64}\Z")


def fail(message: str):
    raise ValueError("[JOHTO][PBS 09] " + message)


def source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fields(lines: list[str], *, section: str) -> dict[str, str]:
    result = {}
    for line in lines:
        key, sep, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not sep or not key or not value or key in result:
            fail("Campo PBS ausente/duplicado em " + section)
        result[key] = value
    return result


def level_up_moves(species: str, section: dict[str, str],
                   catalogue_moves: set[str]) -> list[str]:
    """Only moves actually learned from native PBS at or before level 5."""
    raw = section.get("Moves", "")
    pairs = [x.strip() for x in raw.split(",")]
    if not raw or len(pairs) % 2 or any(not x for x in pairs):
        fail("Learnset inválido para " + species)
    learned = []
    for level, move in zip(pairs[0::2], pairs[1::2]):
        if not level.isdecimal() or not 0 <= int(level) <= 100:
            fail("Nível de golpe inválido em " + species)
        if move not in catalogue_moves:
            fail("Golpe do PBS Pokémon não definido em moves*.txt: " + species + ":" + move)
        if int(level) <= LEVEL:
            if move in learned:
                learned.remove(move)
            learned.append(move)
    learned = learned[-4:]
    if not 1 <= len(learned) <= 4:
        fail("Nenhum golpe de nível inicial válido em " + species)
    return learned


def validate_stage08(story_stage: Path | None) -> dict:
    """Optional SHA-pinned reference to the real private stage08, never a QA proof."""
    if story_stage is None:
        return {"linked": False, "story_events_compiled_in_game": False}
    path = story_stage.absolute()
    work = (ROOT / ".blue-work").resolve()
    if path.is_symlink() or not path.resolve().is_relative_to(work) or not path.is_dir():
        fail("Stage08 deve ficar dentro de .blue-work, sem symlink")
    manifest = path / "johto-story-preview.json"
    if not manifest.is_file() or manifest.is_symlink():
        fail("Falta prova de eventos da etapa 08")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    expected_contract = (
        payload.get("region"), payload.get("status"),
        payload.get("original_warps_preserved"), payload.get("story_events_added"),
        payload.get("starter_ball_events"), payload.get("static_starter_ball_tiles_removed"),
        payload.get("can_install"), payload.get("tested_in_game"))
    if expected_contract != (
        "JOHTO", "STORY_EVENTS_COMPILED_OFFLINE_NOT_PLAYABLE", 6, 6, 3, 3,
        False, False):
        fail("Stage08 não é a prévia real de seis eventos e três bolas")
    expected = payload.get("after_map_sha256")
    if not isinstance(expected, dict):
        # The private Ruby-audit builder puts the identical per-map hashes
        # under checks, while the Python stage08 builder uses after_map_sha256.
        checks = payload.get("checks")
        if (not isinstance(checks, list) or len(checks) != 3 or
                {x.get("map_id") for x in checks if isinstance(x, dict)} !=
                {625, 675, 676}):
            fail("Provas de três mapas da etapa 08 ausentes")
        expected = {str(x["map_id"]): x.get("map_sha256") for x in checks}
    if set(expected) != {"625", "675", "676"}:
        fail("Hashes dos três mapas de história não confiáveis")
    for map_id, sha in expected.items():
        native = path / "Data" / ("Map%03d.rxdata" % int(map_id))
        if (not isinstance(sha, str) or not SHA.fullmatch(sha)
                or native.is_symlink() or not native.is_file()
                or source_hash(native) != sha):
            fail("Mapa da etapa 08 diverge do manifesto: " + map_id)
    return {
        "linked": True, "source_story_manifest_sha256": source_hash(manifest),
        "maps_sha256": expected, "story_events_compiled_in_game": False,
        "engine_tested": False,
    }


def read_blocks_from_bytes(data: bytes) -> dict[str, list[str]]:
    parsed = {}
    key = None
    for line in data.decode("utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            key = stripped[1:-1]
            if key in parsed:
                fail("Seção PBS duplicada gerada")
            parsed[key] = []
        elif key is not None and stripped and not stripped.startswith("#"):
            parsed[key].append(line)
    return parsed


def build(game: Path, *, stage08: Path | None = None) -> tuple[dict, dict[str, bytes]]:
    game = game.absolute()
    pbs = game / "PBS"
    work = (ROOT / ".blue-work").resolve()
    if (not pbs.is_dir() or pbs.is_symlink() or game.is_symlink()
            or game.resolve().is_relative_to(work)):
        fail("Fonte deve ser uma instalação Blue com PBS fora de .blue-work")
    native_types, native_pokemon, native_moves = (
        pbs / "trainer_types.txt", pbs / "pokemon.txt", pbs / "moves.txt")
    if any(not f.is_file() or f.is_symlink()
           for f in (native_types, native_pokemon, native_moves)):
        fail("Arquivos trainer_types.txt, pokemon.txt, moves.txt são obrigatórios")
    if any(f.is_symlink() for prefix in ("moves", "pokemon", "trainer_types", "trainers")
           for f in pbs.glob(prefix + "*.txt")):
        fail("PBS contém link simbólico; não auditar atalhos")
    types = read_blocks(native_types)
    if BASE_TYPE not in types:
        fail("RIVAL1 ausente em trainer_types.txt")
    base_fields = fields(types[BASE_TYPE], section=BASE_TYPE)
    if any(k not in base_fields for k in ("Name", "Gender", "BaseMoney")):
        fail("RIVAL1 não possui Name, Gender ou BaseMoney")
    for path in sorted(pbs.glob("trainer_types*.txt")):
        if RIVAL_TYPE in read_blocks(path):
            fail("Tipo de treinador Johto duplicado: " + path.name)
    for path in sorted(pbs.glob("trainers*.txt")):
        if any(key.split(",")[0] == RIVAL_TYPE for key in read_blocks(path)):
            fail("Treinador Johto duplicado: " + path.name)

    sections = read_blocks(native_pokemon, set(STARTERS))
    keys = catalogue(game, "pokemon")
    missing = set(STARTERS) - (set(sections) & keys)
    if missing:
        fail("Espécies do inicial ausentes no PBS: " + ",".join(sorted(missing)))
    moves_catalogue = catalogue(game, "moves")
    if not moves_catalogue:
        fail("Catálogo de golpes do Blue vazio")
    choices = {}
    species_info = {}
    for name in STARTERS:
        item = fields(sections[name], section=name)
        for needed in ("Moves", "Types", "BaseStats", "Abilities"):
            if needed not in item:
                fail("Espécie " + name + " não possui campo " + needed)
        stats = [x.strip() for x in item["BaseStats"].split(",")]
        if (len(stats) != 6 or
                not all(x.isdecimal() and 1 <= int(x) <= 255 for x in stats)):
            fail("BaseStats inválidos para " + name)
        choices[name] = level_up_moves(name, item, moves_catalogue)
        species_info[name] = {
            "types": [x.strip() for x in item["Types"].split(",")],
            "base_stats": [int(x) for x in stats],
            "ability": item["Abilities"].split(",")[0].strip(),
            "learned_by_level_5": choices[name],
            "learnset_source": "PBS/pokemon.txt (only moves learned at <= 5)",
        }

    type_body = "\n".join(["[" + RIVAL_TYPE + "]", *types[BASE_TYPE], ""])
    trainer_lines = []
    versions = []
    for version, (player, rival) in enumerate(ROSTERS):
        moves = choices[rival]
        trainer_lines.extend([
            f"# Johto inicial do jogador: {player} => Silver: {rival}",
            f"[{RIVAL_TYPE},{RIVAL_NAME},{version}]",
            f"Pokemon = {rival},{LEVEL}",
            "    Moves = " + ",".join(moves), "",
        ])
        versions.append({
            "version": version, "player_starter": player,
            "rival_species": rival, "level": LEVEL, "moves": moves,
            "battle_handler": f'TrainerBattle.start(:{RIVAL_TYPE}, "Rival", {version})',
        })
    files = {
        "PBS/trainer_types_johto.txt": (type_body + "\n").encode("utf-8"),
        "PBS/trainers_johto.txt": "\n".join(trainer_lines).encode("utf-8"),
    }
    sections_out = read_blocks_from_bytes(files["PBS/trainers_johto.txt"])
    if set(sections_out) != {f"{RIVAL_TYPE},{RIVAL_NAME},{n}" for n in range(3)}:
        fail("PBS não possui exatamente as 3 versões do rival")
    for v in versions:
        key = f"{RIVAL_TYPE},{RIVAL_NAME},{v['version']}"
        if sections_out[key] != [
            f"Pokemon = {v['rival_species']},{LEVEL}",
            "    Moves = " + ",".join(v["moves"])
        ]:
            fail("PBS gerado perdeu a espécie, nível ou movimentos de " + key)
    report = {
        "schema": 1, "region": "JOHTO",
        "stage": "OFFLINE_09_RIVAL_PBS_LEVEL5_NATIVE_LEARNSET",
        "status": "THREE_VERSIONS_VALIDATED_PBS_NOT_COMPILED_IN_ENGINE",
        "can_install": False, "pbs_compiled": False, "battle_proven": False,
        "gameplay_playable": False, "tested_in_game": False,
        "rival_type": RIVAL_TYPE, "trainer_name": RIVAL_NAME,
        "levels": "LEVEL_5_FIRST_ENCOUNTER_ONLY; future regional cap scaling is not certified",
        "versions": versions, "native_pokemon_details": species_info,
        "native_trainer_type_source": BASE_TYPE,
        "trainer_graphic": "PENDING_GRAPHICS_TRAINERS_RIVAL1_VALIDATION_IN_ENGINE_COPY",
        "source_pbs_sha256": {
            "trainer_types": source_hash(native_types),
            "pokemon": source_hash(native_pokemon),
            "moves": source_hash(native_moves),
        },
        "files_sha256": {name: hashlib.sha256(data).hexdigest()
                         for name, data in files.items()},
        "story_stage08": validate_stage08(stage08),
        "ready_marker_created": False,
        "required_before_enable": [
            "Copiar as tabelas PBS apenas para uma cópia isolada do Game.exe",
            "Verificar sprite de treinador BLUE_JOHTO_RIVAL e compilação real PBS",
            "Confirmar batalha de 3 versões, save/load e escala com level cap",
            "Criar marcador somente após prova no piloto, não no game/ principal",
            "Integrar Blue-Story.exe para instalação automática em etapa posterior",
        ],
    }
    return report, files


def publish(game: Path, output: Path, *, root: Path = ROOT,
            stage08: Path | None = None) -> dict:
    work = (root.resolve() / ".blue-work").resolve()
    output = output.absolute()
    if (work.is_symlink() or output.is_symlink() or output.exists()
            or not output.resolve().is_relative_to(work) or output.resolve() == work):
        fail("Destino deve ser pasta NOVA dentro de .blue-work, nunca game/")
    report, files = build(game, stage08=stage08)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".johto-pbs09-", dir=output.parent) as tmp:
        stage = Path(tmp) / "draft"
        for name, data in files.items():
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (stage / "johto-pbs09-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if output.exists() or output.is_symlink():
            fail("Destino passou a existir durante compilação")
        stage.rename(output)
    return report


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--game", type=Path, default=ROOT / "game")
    cli.add_argument("--output", type=Path, default=ROOT / ".blue-work/johto-rival-pbs09")
    cli.add_argument("--stage08", type=Path, default=None,
                     help="Prévia privada da etapa 08; vincular hashes, opcional")
    args = cli.parse_args(argv)
    try:
        result = publish(args.game, args.output, stage08=args.stage08)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
        print("[JOHTO][BLOQUEADO]", e, file=sys.stderr)
        return 2
    print("[JOHTO] Três equipes PBS do rival geradas com learnsets nativos:")
    for item in result["versions"]:
        print("  jogador", item["player_starter"], "-> Silver", item["rival_species"],
              "L", item["level"], "/", ",".join(item["moves"]))
    print("[JOHTO] Game.exe não executado; sem ready marker ou instalação.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
