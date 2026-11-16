#!/usr/bin/env python3
"""CH10: explicit, fail-closed launcher for an ISOLATED Sinnoh QA copy.

--check: report preflight (does not execute anything)
--compile: start ONLY the verified, pending private QA Game.exe once so its
           native compiler can write the required compiled/engine markers
--launch: start ONLY the private QA Game.exe after native static checks pass

Never starts Decades/Johto or writes to the main game's directory/saves.
This CLI does NOT claim gameplay approval, even when launching for manual QA.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from install_sinnoh_qa_copy import ROOT, verify


def preflight(qa: Path, *, project: Path = ROOT, mode: str = "check") -> dict:
    if mode not in {"check", "compile", "launch"}:
        raise ValueError("Ação QA desconhecida; usar check/compile/launch")
    result = verify(qa, project=project)
    if not result["required_launcher_assets_verified"]:
        raise ValueError("Assets críticos do lançador QA não verificados")
    if mode == "compile" and (
        not result["compile_request_pending"] or
        result["compiled_marker_present"]
    ):
        raise ValueError("Compilação QA não está pendente ou já foi concluída")
    if mode == "launch" and not result["ready_to_launch_for_manual_testing"]:
        raise ValueError("Sinnoh QA bloqueada: compilação/relatório nativo ausente")
    return {
        **result,
        "requested_action": mode,
        "can_launch_private_copy": (
            mode == "compile" and result["compile_request_pending"]
        ) or (
            mode == "launch" and result["ready_to_launch_for_manual_testing"]
        ),
        "is_main_game": False,
        "fallback_to_other_region": False,
        "gameplay_approved": False,
    }


def run(qa: Path, *, project: Path = ROOT, mode: str = "check") -> dict:
    qa = Path(qa).expanduser().absolute()
    report = preflight(qa, project=project, mode=mode)
    if mode == "check":
        return {**report, "process_started": False}
    # Every requested process has ONE exact absolute executable and QA cwd.
    # No shell and no fallback path to the regular Decades/Kanto/Johto game.
    exe = qa / "Game.exe"
    if not exe.is_file() or exe.is_symlink():
        raise ValueError("Game.exe da cópia QA não encontrado")
    process = subprocess.Popen([str(exe)], cwd=str(qa), shell=False)
    return {**report, "process_started": True, "pid": process.pid}


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--qa", required=True, type=Path,
                     help="cópia privada dentro de .blue-work; nunca game/")
    cli.add_argument("--project", type=Path, default=ROOT)
    modes = cli.add_mutually_exclusive_group()
    modes.add_argument("--compile", action="store_true",
                       help="executar somente compilação nativa pendente")
    modes.add_argument("--launch", action="store_true",
                       help="jogar/testar somente após as provas nativas")
    args = cli.parse_args()
    mode = "compile" if args.compile else "launch" if args.launch else "check"
    try:
        result = run(args.qa, project=args.project, mode=mode)
    except (ValueError, OSError, KeyError, TypeError, UnicodeError) as error:
        print("SINNOH_QA_LAUNCH_BLOQUEADO: " + str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
