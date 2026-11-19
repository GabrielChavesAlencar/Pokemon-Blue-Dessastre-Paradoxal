#!/usr/bin/env python3
"""Launch Sinnoh J12-E from Blue-Story's own Windows UI (not a separate BAT).

This orchestrator only PREPARES a separate QA copy; the caller may explicitly
launch its private compilation/entrypoint. Does not access saves, install
Sinnoh into the main game, change region status or assert native QA.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "regions"))
import install_sinnoh_experimental_windows as installer

RECEIPT_NAME = "blue-story-sinnoh-launch.json"
MODE = "SINNOH_PRIVATE_EXPERIMENTAL_COPY_NOT_APPROVED"

def prepare(project: Path, game: Path, receipt: Path) -> dict:
    project = installer.safe_path(Path(project).absolute())
    game = installer.safe_path(Path(game).absolute())
    receipt = installer.safe_path(Path(receipt).absolute())
    work = installer.safe_path(project / ".blue-work")
    if not project.is_dir() or not (project / "scripts" / "install_game.py").is_file():
        installer.fail("BLUE_STORY_PROJECT_ROOT_INVALID")
    if game != project / "game" or not game.is_dir():
        installer.fail("BLUE_STORY_ONLY_MANAGED_READONLY_GAME")
    if receipt != work / RECEIPT_NAME or receipt.exists() or receipt.is_symlink():
        installer.fail("BLUE_STORY_RECEIPT_NOT_NEW_OR_UNSAFE")
    # J12-E's source preflight validates MapInfos/Tilesets/PBS and allocates
    # private, collision-free, provisional MapIDs. No writes to the source.
    files, report = installer.build_files(game, project)
    if report.get("native_maps_installed", 0) or report.get("main_game_modified"):
        installer.fail("J12E_SOURCE_GAME_MUTATION_CLAIM")
    if report.get("r09_native_qa_executed") != 0:
        installer.fail("NATIVE_QA_MUST_REMAIN_UNVERIFIED")
    dest = installer.install_copy(game, files, report, project)
    dest = installer.safe_path(dest)
    target_name = dest.name
    if (dest.parent != work or not target_name.startswith(installer.QA_DIR + "-")
        or not dest.is_dir() or
        not (dest / "INICIAR_SINNOH_EXPERIMENTAL.bat").is_file() or
        not (dest / "sinnoh-experimental-qa.json").is_file()):
        installer.fail("INCOMPLETE_OR_UNSAFE_QA_COPY")
    info = {
        "schema": 1,
        "mode": MODE,
        "blue_story_menu": "Testar piloto Sinnoh",
        "source_readonly_game": str(game),
        "qa_directory": str(dest),
        "launcher": str(dest / "INICIAR_SINNOH_EXPERIMENTAL.bat"),
        "main_game_modified": False,
        "personal_saves_copied": False,
        "native_maps_installed_in_main": 0,
        "native_qa_cases_approved": 0,
        "R07_approved": False,
        "R08_approved": False,
        "R09_approved": False,
        "playable_verified": False,
        "requires_native_validation": True,
    }
    work.mkdir(parents=True, exist_ok=True)
    if work.is_symlink():
        installer.fail("QA_WORKSPACE_SYMLINK")
    with receipt.open("x", encoding="utf-8") as stream:
        json.dump(info, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")
    return info

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", type=Path, required=True)
    p.add_argument("--game-dir", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        result = prepare(args.project_root, args.game_dir, args.receipt)
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        print("BLUE_STORY_SINNOH_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({
        "mode": MODE,
        "qa_copy_created": True,
        "installed_in_main": False,
        "native_qa_approved": False,
        "path": result["qa_directory"],
    }, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
