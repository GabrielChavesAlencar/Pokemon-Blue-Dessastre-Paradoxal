#!/usr/bin/env python3
"""Verify a Sinnoh Barry PBS draft against its pinned native source (NO ready marker).

Draft integrity checks are NOT battle-engine compilation, playable proof or
permission to activate the rival. Never edit game/, PBS, or saves.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from build_johto_rival_pbs_v2 import read_blocks_from_bytes
from build_sinnoh_barry_pbs import (
    ROOT, FILES, MATCHUPS, PBS_TRAINERS, PBS_TYPE, READY_MARKER,
    RIVAL_NAME, RIVAL_TYPE, SEED_LEVEL, balance_contract,
)


def fail(message: str):
    raise ValueError("[SINNOH BARRY VERIFY] " + message)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def inspect(draft: Path, game: Path, *, root: Path = ROOT) -> dict:
    root = root.expanduser().absolute()
    draft = draft.expanduser().absolute()
    game = game.expanduser().absolute()
    workspace = root / ".blue-work"
    if (root.is_symlink() or workspace.is_symlink() or draft.is_symlink()
            or not draft.is_dir() or not draft.is_relative_to(workspace)
            or draft == workspace or draft == game or draft in game.parents
            or game.is_symlink() or not game.is_dir()):
        fail("Draft deve estar em .blue-work, distinto da instalação real")
    manifest_path = draft / "sinnoh-barry-pbs-report.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        fail("Relatório PBS privado ausente")
    report = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if not isinstance(report, dict):
        fail("Relatório PBS não é objeto JSON")
    if (report.get("schema"), report.get("region"), report.get("stage"),
            report.get("status"), report.get("can_install"),
            report.get("pbs_compiled"), report.get("ready_marker_created"),
            report.get("ready_marker_allowed")) != (
            1, "SINNOH", "BARRY_FIRST_RIVAL_3_VERSION_PBS_DRAFT",
            "VALIDATED_NATIVE_PBS_DRAFT_NOT_COMPILED",
            False, False, False, False):
        fail("Relatório PBS incorreto ou com falsa aprovação")
    files = report.get("files_sha256")
    if not isinstance(files, dict) or set(files) != {PBS_TYPE, PBS_TRAINERS}:
        fail("Relatório não lista exatamente 2 PBS Sinnoh")
    bodies = {}
    for rel, expected in files.items():
        path = draft / rel
        if (path.is_symlink() or not path.is_file() or
                not isinstance(expected, str) or digest(path.read_bytes()) != expected):
            fail("PBS do draft ausente ou SHA-256 modificado: " + rel)
        bodies[rel] = path.read_bytes()
    for secret in (READY_MARKER, "Data/Scripts.rxdata", "Data/System.rxdata"):
        if (draft / secret).exists():
            fail("Draft contém marcador de rival ou binário nativo proibido")
    native = report.get("source_pbs_sha256")
    if not isinstance(native, dict) or set(native) != set(FILES):
        fail("Hashes PBS da instalação de referência incompletos")
    for filename in FILES:
        path = game / "PBS" / filename
        if path.is_symlink() or not path.is_file():
            fail("PBS da instalação real indisponível")
        if digest(path.read_bytes()) != native[filename]:
            fail("PBS de origem mudou; descartar e gerar outro draft")
    runtime = balance_contract(root / "scripts/battle_polish/Campaign.rb")
    if report.get("balance") != runtime:
        fail("Runtime de balanceamento mudou; verificar 70%/90% novamente")
    versions = report.get("versions")
    if (not isinstance(versions, list) or len(versions) != 3 or
            not isinstance(report.get("native_starters"), dict)):
        fail("Não há exatamente três equipes Barry no manifesto")
    types = read_blocks_from_bytes(bodies[PBS_TYPE])
    if set(types) != {RIVAL_TYPE}:
        fail("Arquivo trainer_types tem blocos inesperados")
    trainers = read_blocks_from_bytes(bodies[PBS_TRAINERS])
    expected = {f"{RIVAL_TYPE},{RIVAL_NAME},{i}" for i in range(3)}
    if set(trainers) != expected:
        fail("Os três treinadores de Barry não estão completos")
    for index, (player, rival) in enumerate(MATCHUPS):
        row = versions[index]
        if (not isinstance(row, dict) or
                (row.get("version"), row.get("player_starter"),
                 row.get("rival_species"), row.get("seed_level_only")) != (
                 index, player, rival, SEED_LEVEL)):
            fail("Versão PBS não corresponde à escolha do jogador")
        moves = row.get("moves_at_seed_level")
        if (not isinstance(moves, list) or not (1 <= len(moves) <= 4)
                or any(not isinstance(m, str) or not m for m in moves)):
            fail("Golpes iniciais de Barry incompletos")
        if moves != report["native_starters"].get(rival, {}).get("learnset_0_to_5"):
            fail("Golpes de Barry divergentes do learnset auditado")
        if trainers[f"{RIVAL_TYPE},{RIVAL_NAME},{index}"] != [
            f"Pokemon = {rival},{SEED_LEVEL}",
            "    Moves = " + ",".join(moves),
        ]:
            fail("Trainer PBS da versão " + str(index) + " foi adulterado")
    return {
        "region": "SINNOH", "mode": "DRAFT_INTEGRITY_ONLY",
        "teams_verified": 3, "start_level_is_pbs_seed_only": True,
        "balance_source_checked": True,
        "native_scaling_executed": False,
        "pbs_compiled_in_game": False,
        "ready_marker_allowed": False,
        "may_install_into_game": False,
        "source_pbs_sha256": native,
        "files_sha256": files,
    }


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--draft", required=True, type=Path)
    cli.add_argument("--game", required=True, type=Path)
    args = cli.parse_args()
    try:
        result = inspect(args.draft, args.game)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        print("SINNOH_BARRY_VERIFY_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
