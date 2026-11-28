"""Gated Windows installer overlay for existing or freshly seeded K05."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from audit import KANTO, ROOT, json_file
from audit_k06_rocket import summarize
from ensure_source import prepare
from k06_approach_migration import APPROACH, CI_PATH, INSTALL, READY, managed_world_assembly, plan, verify_native_graph

sys.path.insert(0,str(ROOT))
from scripts.android import source_update as journal

RELEASE_FLAG=Path("data/regions/k06-approach-release.json")
COMPILE="Data/blue-compile-request.txt"
STAGE_NAME="K06_APPROACH"


def activation_enabled(project):
    flag=project/RELEASE_FLAG
    if not flag.exists():
        return False
    try:
        valid=json_file(flag)=={"schema":1,"stage":STAGE_NAME,"source_maps":list(APPROACH)}
    except (OSError,ValueError) as exc:
        raise ValueError("O catálogo da passagem de Celadon está inválido.") from exc
    if not valid:
        raise ValueError("O catálogo da passagem de Celadon não corresponde à revisão autorizada.")
    return True


def install(game, *, ci=False):
    game=game.resolve()
    if ci:
        confirmed=os.getenv("GITHUB_ACTIONS")=="true" and os.name=="nt" and game==(ROOT/CI_PATH).resolve()
    else:
        confirmed=(game==(ROOT/"game").resolve() and activation_enabled(ROOT)
                   and (os.name=="nt" or managed_world_assembly(ROOT,game)))
    if not confirmed:
        raise ValueError("Windows K06 is not active on this managed installation.")
    backup_base=ROOT/".blue-backups/k06-approach"
    backup_base.parent.mkdir(exist_ok=True)
    if (game/journal.RECOVERY_FILE).exists():
        with journal.update_lock(game):
            data=journal.recovery_plan(game,record_marker=INSTALL)
            if data is not None:
                journal.recover_under_lock(game,backup_base,data,record_marker=INSTALL)
    before=(game/INSTALL).read_bytes()
    old=json.loads(before)
    if old.get("content_stage")==STAGE_NAME:
        verify_native_graph(game)
        return False
    if old.get("content_stage") is not None:
        raise ValueError("Este instalador não pode regressar uma etapa de Kanto.")
    source=prepare()
    changes,result=plan(game,source,summarize(source,json_file(KANTO)))
    install_stamp=json.loads(changes.pop(INSTALL).decode("utf8"))
    install_stamp["content_stage"]=STAGE_NAME
    result["status"]="K06_APPROACH_CANDIDATE" if ci else STAGE_NAME
    changes[READY]=(json.dumps(result,indent=2)+"\n").encode("utf8")
    changes[COMPILE]=b"compile"
    with TemporaryDirectory(prefix="k06-overlay-",dir=ROOT/".blue-work") as work:
        stage=Path(work).resolve()
        inventory={}
        for name,data in changes.items():
            journal.atomic_file(stage/name,data)
            inventory[name]=journal.manifest_row(stage/name)
        journal.commit_local(game,stage,inventory,json.dumps(install_stamp,indent=2).encode("utf8"),
                             backup_base,verify=verify_native_graph,before_marker=before,
                             baseline="windows-k05",record_marker=INSTALL)
    print("KANTO_K06_WINDOWS_APPROACH_OVERLAY_OK",flush=True)
    return True


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game",type=Path,required=True)
    parser.add_argument("--ci",action="store_true")
    args=parser.parse_args()
    install(args.game,ci=args.ci)
