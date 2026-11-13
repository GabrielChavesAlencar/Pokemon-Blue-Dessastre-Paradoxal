"""Preparar três equipes do rival de New Bark para o motor de batalha Blue.

Gera APENAS PBS separado sob .blue-work/. Não compila no Game.exe nem cria
blue-johto-rival-ready.txt. A instalação isolada deve compilar PBS, verificar
espécies/sprite e batalhar de fato antes de ativar o marcador no PILOTO.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

from audit_johto import ROOT
from pbs import read_blocks, catalogue

RIVAL_TYPE = "BLUE_JOHTO_RIVAL"
BASE_TYPE = "RIVAL1"
RIVAL_NAME = "Rival"
ROSTERS = (
    ("CHIKORITA", "CYNDAQUIL"),  # jogador → rival / versão 0
    ("CYNDAQUIL", "TOTODILE"),   # versão 1
    ("TOTODILE", "CHIKORITA"),   # versão 2
)
LEVEL = 5


def build(game: Path) -> tuple[dict, dict[str, bytes]]:
    pbs = game / "PBS"
    if not pbs.is_dir() or (game / "PBS").is_symlink():
        raise ValueError("É necessária a instalação local do Blue com PBS")
    types = pbs / "trainer_types.txt"
    if not types.is_file() or types.is_symlink():
        raise ValueError("Arquivo PBS/trainer_types.txt ausente ou ligado")
    native = read_blocks(types)
    if BASE_TYPE not in native or not native[BASE_TYPE]:
        raise ValueError("Tipo RIVAL1 da battle engine não está instalado")
    species = catalogue(game, "pokemon")
    needed = {mon for pair in ROSTERS for mon in pair}
    if not needed.issubset(species):
        raise ValueError("Pokémon iniciais ausentes na Pokédex Blue: " +
                         ",".join(sorted(needed - species)))
    # Não permitir nomes de treinador em conflito com outras áreas/regiões.
    for filename in sorted(pbs.glob("trainer_types*.txt")):
        if filename.is_symlink():
            raise ValueError("PBS trainer_types ligado por symlink")
        if RIVAL_TYPE in read_blocks(filename):
            raise ValueError("Já existe BLUE_JOHTO_RIVAL em PBS")
    for filename in sorted(pbs.glob("trainers*.txt")):
        if filename.is_symlink():
            raise ValueError("PBS trainers ligado por symlink")
        if any(row.startswith(RIVAL_TYPE + ",") or row == RIVAL_TYPE
               for row in read_blocks(filename)):
            raise ValueError("Treinador rival de Johto já existe no PBS")
    trainer_type = "\n".join([
        f"[{RIVAL_TYPE}]", *native[BASE_TYPE], "",
    ])
    trainers = []
    for version, (player, rival) in enumerate(ROSTERS):
        trainers.extend([
            f"# Início Johto: escolha {player} => rival {rival}",
            f"[{RIVAL_TYPE},{RIVAL_NAME},{version}]",
            f"Pokemon = {rival},{LEVEL}",
            "",
        ])
    data = {
        "PBS/trainer_types_johto.txt": trainer_type.encode("utf-8"),
        "PBS/trainers_johto.txt": ("\n".join(trainers)).encode("utf-8"),
    }
    return ({
        "schema": 1, "region": "JOHTO", "stage": "FIRST_RIVAL_PBS_DRAFT",
        "can_install": False, "pbs_compiled": False, "battle_proven": False,
        "type": RIVAL_TYPE, "name": RIVAL_NAME, "versions": [
            {"version": v, "player_starter": player, "rival_species": rival,
             "level": LEVEL}
            for v, (player, rival) in enumerate(ROSTERS)
        ],
        "files_sha256": {p: hashlib.sha256(data[p]).hexdigest() for p in data},
        "required_before_enable": [
            "Copiar PBS somente para a cópia isolada do Game.exe",
            "Compilar no Essentials real e verificar Graphics/Trainers do rival",
            "Confirmar as três versões e o resultado de TrainerBattle.start",
            "Só então criar ready marker no PILOTO, nunca no jogo principal",
        ],
    }, data)


def publish(game: Path, output: Path, *, root: Path = ROOT) -> dict:
    work = (root / ".blue-work").resolve()
    output = output.absolute()
    if (output.is_symlink() or not output.resolve().is_relative_to(work)
            or output.resolve() == work or output.exists()):
        raise ValueError("Escolha destino NOVO dentro de .blue-work/")
    # game deve ser a instalação do Blue, não uma pasta de saída dentro dela.
    game = game.absolute()
    if game.resolve().is_relative_to(work):
        raise ValueError("PBS de referência devem vir de uma instalação game/ distinta")
    result, files = build(game)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".johto-pbs-", dir=output.parent) as tmp:
        staging = Path(tmp) / "result"
        for relative, payload in files.items():
            dest = staging / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(payload)
        (staging / "johto-pbs-draft.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if output.exists() or output.is_symlink():
            raise ValueError("Destino mudou durante compilação")
        staging.rename(output)
    return result


def main(argv=None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--game", type=Path, default=ROOT / "game")
    cli.add_argument("--output", type=Path, default=ROOT / ".blue-work/johto-rival-pbs")
    args = cli.parse_args(argv)
    try:
        result = publish(args.game, args.output)
    except (OSError, TypeError, KeyError, ValueError) as e:
        print("[JOHTO][BLOQUEADO] " + str(e), file=sys.stderr)
        return 2
    print("[JOHTO] Criadas 3 equipes de rival de nível 5. NÃO INSTALADAS.")
    print("[JOHTO] PBS real e Game.exe devem confirmar as batalhas antes de ativar o marcador.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
