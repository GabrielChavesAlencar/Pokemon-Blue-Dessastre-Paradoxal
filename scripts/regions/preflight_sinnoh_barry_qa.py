#!/usr/bin/env python3
"""Read-only Barry PBS integration preflight in a SEPARATE Sinnoh QA copy.

The output cannot certify compilation, native level scaling, in-game battles,
or release a ready marker. It inspects only files and SHA-256 values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from build_sinnoh_barry_pbs import ROOT, PBS_TRAINERS, PBS_TYPE, READY_MARKER
from verify_sinnoh_barry_pbs import inspect as inspect_draft

TRAINER_GRAPHIC = re.compile(r"[A-Za-z0-9_ -]{1,90}\.png\Z")
LEGACY_IDS = set(range(800, 806))


def fail(message: str) -> None:
    raise ValueError("[SINNOH BARRY QA] " + message)


def digest(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        fail("Arquivo local ausente ou symlink: " + str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight(
    qa: Path, draft: Path, game: Path, *,
    root: Path = ROOT,
    graphic: str = "BLUE_SINNOH_RIVAL.png",
) -> dict:
    root = root.expanduser().absolute()
    qa = qa.expanduser().absolute()
    draft = draft.expanduser().absolute()
    game = game.expanduser().absolute()
    work = root / ".blue-work"
    if (not qa.is_dir() or qa.is_symlink() or game.is_symlink()
            or not game.is_dir() or qa == game
            or qa in game.parents or game in qa.parents
            or qa == work or not qa.is_relative_to(work)
            or not qa.resolve().is_relative_to(work.resolve())
            or any(part.is_symlink() for part in (qa, *qa.parents))):
        fail("QA deve estar em cópia distinta dentro de .blue-work, nunca em game/")
    if not TRAINER_GRAPHIC.fullmatch(graphic):
        fail("Nome de sprite de treinador inválido")
    draft_report = inspect_draft(draft, game, root=root)
    for rel, expected in draft_report["files_sha256"].items():
        file = qa / rel
        if digest(file) != expected:
            fail("Cópia PBS ausente/adulterada em QA: " + rel)
    if (qa / READY_MARKER).exists() or (game / READY_MARKER).exists():
        fail("Marcador de batalha de Barry prematuro na cópia QA ou game/")
    if not (qa / "Game.exe").is_file() or (qa / "Game.exe").is_symlink():
        fail("Cópia QA sem executável nativo")
    if not (qa / "PBS").is_dir() or (qa / "PBS").is_symlink():
        fail("PBS da QA ausente")
    # A present file is not proof Essentials has compiled it, or that the
    # battle engine recognizes a distinct custom trainer type by this name.
    candidate = qa / "Graphics/Trainers" / graphic
    has_graphic = candidate.is_file() and not candidate.is_symlink()
    map_conflicts = []
    maps = qa / "Data"
    if maps.is_dir():
        for mapfile in maps.iterdir():
            if (match := re.fullmatch(r"Map([0-9]+)\.rxdata", mapfile.name)):
                mid = int(match.group(1))
                if mid in LEGACY_IDS:
                    map_conflicts.append(mid)
    map_conflicts.sort()
    return {
        "schema": 1,
        "region": "SINNOH",
        "mode": "ISOLATED_QA_STATIC_PREFLIGHT",
        "draft_integrity": "THREE_PBS_VERSIONS_HASH_VERIFIED",
        "qa_copy_not_main_game": True,
        "trainer_type_pbs_sha256": draft_report["files_sha256"][PBS_TYPE],
        "trainer_team_pbs_sha256": draft_report["files_sha256"][PBS_TRAINERS],
        "graphic_candidate_file_exists": has_graphic,
        "graphic_asset_name": graphic,
        "graphic_engine_verified": False,
        "legacy_map_800_805_physically_present_in_qa": map_conflicts,
        "potential_johto_collision_if_merged": bool(map_conflicts),
        "pbs_compiled_in_essentials": False,
        "trainer_versions_loaded_in_engine": False,
        "level_scaling_verified_in_game": False,
        "save_load_verified": False,
        "ready_marker_created": False,
        "ready_marker_allowed": False,
        "can_install_into_main_game": False,
        "files_modified": False,
        "next_manual_steps": [
            "Confirmar sprite trainer no engine e o tipo BLUE_SINNOH_RIVAL",
            "Compilar PBS no Essentials na cópia de QA; conferir três GameData::Trainer",
            "Validar 70% normal e 90% master com nível real observado",
            "Verificar os três starters, vitória/derrota, save/load",
            "Resolver sobreposição 800..805 de Johto antes de qualquer merge multi-região",
            "Registrar evidências; só liberar marcador depois da QA nativa completa",
        ],
    }


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--qa", required=True, type=Path)
    cli.add_argument("--draft", required=True, type=Path)
    cli.add_argument("--game", required=True, type=Path)
    cli.add_argument("--graphic", default="BLUE_SINNOH_RIVAL.png")
    args = cli.parse_args()
    try:
        report = preflight(args.qa, args.draft, args.game, graphic=args.graphic)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print("SINNOH_BARRY_QA_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
