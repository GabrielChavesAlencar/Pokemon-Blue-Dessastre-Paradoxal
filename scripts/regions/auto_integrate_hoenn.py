"""Automatic, pinned Hoenn integration for Blue-Story.exe / main Decades.

Follows the Kanto updater model: fetch only reviewed source assets from a
fixed public Git revision if there is no private local ZIP, validate hashes,
merge into the shared main game and request recompilation. No separate BAT
or save profile is required. A failed download is never fake availability.
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
SOURCE_BOOTSTRAP = ROOT / "scripts/regions/ensure_hoenn_source.py"
PROOF = Path("Data/blue-hoenn-install.json")
MARKER = Path("Data/blue-hoenn-start.txt")
STATUS = ROOT / ".blue-work/hoenn-main-install-status.json"
LOG = ROOT / ".blue-work/hoenn-main-install.log"
GAME_STATUS = Path("Data/blue-hoenn-install-status.txt")
SOURCE_CACHE = ROOT / ".blue-work/hoenn-source"


def record(status: str, changed: bool = False, reason: str = "",
           source: str = "") -> dict:
    value = {"status": status, "ready": status in {"integrated", "already_integrated"},
             "changed": changed, "source": source, "reason": reason,
             "timestamp_utc": datetime.now(timezone.utc).isoformat(),
             "log": str(LOG)}
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATUS.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, STATUS)
    game = ROOT / "game"
    if (game / "Game.exe").is_file() and (game / "Data").is_dir():
        marker = game / GAME_STATUS
        if not marker.is_symlink() and not marker.parent.is_symlink():
            temp = marker.with_name(marker.name + ".tmp")
            temp.write_text(status + "\n", encoding="ascii")
            os.replace(temp, marker)
    return value


def invoke(game: Path, *flags: str) -> None:
    """Stream progress instead of hiding slow first-time Hoenn downloads."""
    script = SOURCE_BOOTSTRAP if flags == ("--bootstrap-source",) else INSTALLER
    args = [] if script == SOURCE_BOOTSTRAP else ["--game", str(game), *flags]
    cmd = [sys.executable, "-X", "utf8", str(script), *args]
    LOG.parent.mkdir(parents=True, exist_ok=True)
    print("[HOENN AUTO] >", " ".join(str(x) for x in cmd[3:]), flush=True)
    with LOG.open("a", encoding="utf-8") as log:
        log.write("\n=== " + datetime.now(timezone.utc).isoformat() + " " +
                  " ".join(cmd[3:]) + " ===\n")
        log.flush()
        recent = []
        env = {**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}
        with subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True,
                              encoding="utf-8", errors="replace", bufsize=1) as process:
            for line in process.stdout:
                print(line, end="", flush=True)
                log.write(line)
                log.flush()
                if line.strip():
                    recent.append(line.strip())
                    recent = recent[-5:]
            result = process.wait()
        if result:
            raise RuntimeError(
                f"Etapa Hoenn falhou (código {result}): {' | '.join(recent[-3:])}. "
                f"Log: {LOG}"
            )


def integrate(project: Path = ROOT, game: Path | None = None) -> dict:
    project = Path(project).resolve()
    game = Path(game or project / "game").resolve()
    if project != ROOT.resolve() or game != (ROOT / "game").resolve():
        return record("foreign_game_skipped", reason="Only the managed main game is supported")
    if not (game / "Game.exe").is_file():
        return record("no_game_skipped", reason="Decades base is not installed")
    if (game / PROOF).exists() or (game / MARKER).exists():
        try:
            proof = game / PROOF
            before = proof.read_bytes() if proof.is_file() and not proof.is_symlink() else None
            invoke(game, "--apply")
            after = proof.read_bytes()
            return record("already_integrated", changed=(before != after))
        except (RuntimeError, OSError) as error:
            return record("existing_install_needs_review", reason=str(error))

    # Do not ask players to locate a ZIP or open a separate installer.
    # Prefer any original local ZIP, otherwise fetch ONLY the files from the
    # previously pinned public Hoenn commit; never download a donor EXE.
    source = "audited_local_zip" if ZIP.is_file() else "pinned_public_git"
    try:
        if not ZIP.is_file():
            print("[HOENN AUTO] Obtendo automaticamente os recursos de Hoenn "
                  "da revisão pública auditada. Nenhum ZIP manual necessário.",
                  flush=True)
            invoke(game, "--bootstrap-source")
        invoke(game, "--apply")
        invoke(game, "--verify-installed")
    except (RuntimeError, OSError, ValueError) as error:
        return record("integration_blocked", reason=str(error), source=source)
    return record("integrated", changed=True, source=source)


if __name__ == "__main__":
    print(json.dumps(integrate(), ensure_ascii=False, indent=2))
