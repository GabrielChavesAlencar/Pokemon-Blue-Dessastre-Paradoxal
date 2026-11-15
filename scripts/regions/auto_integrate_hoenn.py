"""Optional, fail-soft Hoenn import for the shared Blue-Story/Decades updater.

Only runs when the author's LOCAL ZIP exists. Never downloads or publishes
third-party maps/graphics. An unavailable or unverified Hoenn does not prevent
Decades/Kanto from launching and is NEVER advertised as playable.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZIP = ROOT / "The Pokémon World Project - Hoenn.zip"
INSTALLER = ROOT / "scripts/regions/install_hoenn.py"
PROOF = Path("Data/blue-hoenn-install.json")
MARKER = Path("Data/blue-hoenn-start.txt")
STATUS = ROOT / ".blue-work/hoenn-main-install-status.json"
LOG = ROOT / ".blue-work/hoenn-main-install.log"


def record(status: str, changed: bool = False, reason: str = "") -> dict:
    value = {"status": status, "ready": status in {"integrated", "already_integrated"},
             "changed": changed, "reason": reason,
             "timestamp_utc": datetime.now(timezone.utc).isoformat(),
             "log": str(LOG)}
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATUS.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, STATUS)
    return value


def invoke(game: Path, *flags: str) -> None:
    cmd = [sys.executable, str(INSTALLER), "--game", str(game), *flags]
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as log:
        log.write("\n" + datetime.now(timezone.utc).isoformat() + " " +
                  " ".join(cmd[2:]) + "\n")
        log.flush()
        run = subprocess.run(cmd, cwd=ROOT, stdout=log,
                             stderr=subprocess.STDOUT, text=True,
                             encoding="utf-8", errors="replace", check=False)
    if run.returncode:
        tail = LOG.read_text(encoding="utf-8").splitlines()[-4:]
        raise RuntimeError("; ".join(tail))


def integrate(project: Path = ROOT, game: Path | None = None) -> dict:
    project = Path(project).resolve()
    game = Path(game or project / "game").resolve()
    if project != ROOT.resolve() or game != (ROOT / "game").resolve():
        return record("foreign_game_skipped", reason="Only the managed main game is supported")
    if not (game / "Game.exe").is_file():
        return record("no_game_skipped", reason="Decades base is not installed")
    if (game / PROOF).exists() or (game / MARKER).exists():
        try:
            invoke(game, "--verify-installed")
            return record("already_integrated")
        except (RuntimeError, OSError) as error:
            return record("existing_install_needs_review", reason=str(error))
    if not ZIP.is_file():
        return record("awaiting_local_source", reason=
            "Coloque o ZIP original The Pokémon World Project - Hoenn.zip na raiz do projeto. "
            "Hoenn não foi instalada; Decades/Kanto permanecem intactos.")
    try:
        invoke(game, "--apply")
        invoke(game, "--verify-installed")
    except (RuntimeError, OSError, ValueError) as error:
        return record("integration_blocked", reason=str(error))
    return record("integrated", changed=True)


if __name__ == "__main__":
    print(json.dumps(integrate(), ensure_ascii=False, indent=2))
