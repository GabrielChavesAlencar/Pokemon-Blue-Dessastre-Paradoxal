#!/usr/bin/env python3
"""Read-only QA-copy PBS/save/plugin preflight for isolated Sinnoh experiments.

It never compiles PBS, runs an executable, modifies game/PBS or creates ready
markers. It checks pinned draft PBS bytes and detects legacy dialog starter
plugin vs new 3-ball story. Passing this preflight is NOT playable approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from build_sinnoh_barry_pbs import PBS_TRAINERS, PBS_TYPE, READY_MARKER, ROOT
from verify_sinnoh_barry_pbs import inspect as verify_draft

PLUGIN_ROOT = "Plugins/ZZZZZ Blue Sinnoh Pilot"
OLD_PLUGIN = PLUGIN_ROOT + "/SinnohPreview.rb"
NEW_PLUGIN = PLUGIN_ROOT + "/SinnohPilot.rb"


def fail(message: str):
    raise ValueError("[SINNOH QA COPY] " + message)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _regular(path: Path) -> Path:
    if (any(parent.is_symlink() for parent in (path, *path.parents))
            or not path.is_file()):
        fail("Arquivo ausente ou caminho symlink: " + str(path))
    return path


def inspect_copy(main_game: Path, qa_game: Path, draft: Path,
                 *, root: Path = ROOT) -> dict:
    root = root.expanduser().absolute()
    main_game = main_game.expanduser().absolute()
    qa_game = qa_game.expanduser().absolute()
    draft = draft.expanduser().absolute()
    if (root.is_symlink() or main_game.is_symlink() or qa_game.is_symlink()
            or not main_game.is_dir() or not qa_game.is_dir()
            or qa_game == main_game or qa_game in main_game.parents
            or main_game in qa_game.parents or
            qa_game == root or qa_game in root.parents or
            any(p.is_symlink() for p in (qa_game, *qa_game.parents))):
        fail("Cópia QA precisa ser distinta de game/ e do repositório")
    verified = verify_draft(draft, main_game, root=root)
    for rel in (PBS_TYPE, PBS_TRAINERS):
        file = _regular(qa_game / rel)
        if _hash(file) != verified["files_sha256"][rel]:
            fail("PBS no piloto diverge do draft verificado: " + rel)
    marker = qa_game / READY_MARKER
    if marker.exists() or marker.is_symlink():
        fail("Marcador de Barry existe antes das batalhas e QA nativas")
    descriptor = _regular(qa_game / "Sinnoh pilot.json")
    settings = _regular(qa_game / "mkxp.json")
    data = json.loads(descriptor.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or data.get("region") != "SINNOH":
        fail("Sinnoh pilot.json inválido/incompatível")
    conf = json.loads(settings.read_text(encoding="utf-8-sig"))
    if not isinstance(conf, dict):
        fail("mkxp.json inválido")
    profile = (conf.get("dataPathOrg"), conf.get("dataPathApp"))
    if not all(isinstance(s, str) and s.strip() for s in profile):
        fail("Perfil de saves independente não declarado no mkxp.json")
    native_conf = main_game / "mkxp.json"
    if native_conf.exists():
        original = json.loads(_regular(native_conf).read_text(encoding="utf-8-sig"))
        if (not isinstance(original, dict) or
                (original.get("dataPathOrg"), original.get("dataPathApp")) == profile):
            fail("Cópia experimental usa o mesmo perfil de saves do Blue principal")
    old = qa_game / OLD_PLUGIN
    new = qa_game / NEW_PLUGIN
    if old.is_symlink() or new.is_symlink():
        fail("Plugin Sinnoh não pode ser symlink")
    has_old, has_new = old.is_file(), new.is_file()
    if has_old and has_new:
        fail("Os dois scripts de iniciais Sinnoh estão instalados simultaneamente")
    plugin_mode = (
        "LEGACY_ROWAN_DIALOG" if has_old else
        "AUTHORED_THREE_BALLS" if has_new else
        "NO_SINNOH_STORY_PLUGIN"
    )
    binary = qa_game / "Game.exe"
    if binary.is_symlink():
        fail("Executável em cópia não pode ser symlink")
    return {
        "schema": 1, "region": "SINNOH",
        "status": "PRIVATE_PBS_COPY_PREFLIGHT_ONLY",
        "pbs_draft_files_match": True,
        "pbs_variants_in_draft_verified": verified["teams_verified"],
        "qa_save_profile": {"org": profile[0], "app": profile[1]},
        "qa_profile_distinct_from_main": True,
        "qa_binary_present": binary.is_file(),
        "story_plugin_mode": plugin_mode,
        "old_dialog_plugin_present": has_old,
        "new_three_ball_plugin_present": has_new,
        "multi_region_map_ids_verified": False,
        "compiled_trainer_index_tested": False,
        "battle_levels_70_90_tested": False,
        "rival_sprite_verified": False,
        "win_loss_save_load_tested": False,
        "safe_to_create_barry_marker": False,
        "gameplay_approved": False,
        "may_merge_with_main_game": False,
        "required_next": [
            "Retirar piloto de diálogo legado da cópia nova antes de ativar as 3 Poké Bolas",
            "Resolver MapIDs antigos 800–805 vs Johto 600–999",
            "Compilar os 3 PBS no Essentials nativo da cópia experimental",
            "Rodar SinnohBarryNativeProbe.rb dentro do Game.exe isolado",
            "Testar sprites, três escolhas, escalonamento 70/90, vitória/derrota e save/load",
        ],
    }


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--main-game", required=True, type=Path)
    cli.add_argument("--qa-game", required=True, type=Path)
    cli.add_argument("--draft", required=True, type=Path)
    args = cli.parse_args()
    try:
        report = inspect_copy(args.main_game, args.qa_game, args.draft)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        print("SINNOH_QA_COPY_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
