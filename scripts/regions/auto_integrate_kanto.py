"""Automatically integrate Kanto in Blue-Story's shared Decades installation.

Called from scripts/install_game.py after the native Blue plugins are prepared.
Does not run for the Hub-only release, on foreign game paths, or when an old
Kanto import might already own RXDATA/map IDs. A missing/offline FRLG source is
a nonfatal Kanto failure, never a reason to block the native Decades game.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]

# Keep the importer the only writer of Kanto resources: it performs the full
# pilot verification, hash checks, backups, marker-last commit and rollback.
KANTO_IMPORTER = "scripts/regions/install_kanto.py"
KANTO_SOURCE_BOOTSTRAP = "scripts/regions/ensure_source.py"
KANTO_MARKER = Path("Data/blue-kanto-start.txt")
KANTO_MANIFEST = Path("Data/blue-kanto-install.json")


def detect_existing(game: Path) -> str:
    """Returns 'installed', 'unverified', or 'absent' WITHOUT modifying game."""
    # The manifest is tied to a map registry, not an arbitrary JSON written
    # by the launcher. It must be reverified by install_kanto.py every time.
    if (game / KANTO_MARKER).exists() or (game / KANTO_MANIFEST).exists():
        return "unverified"

    # An interrupted import or an older manual integration can have no final
    # marker. Never auto-allocate new IDs on top of these partial resources.
    checks = (
        game / "Plugins/ZZZZZ Blue Kanto Pilot",
        game / "Data/blue-kanto-locale.dat",
        game / "PBS/encounters_kanto.txt",
        game / "PBS/trainers_kanto.txt",
        game / "PBS/map_metadata_kanto.txt",
        game / "PBS/map_connections_kanto.txt",
    )
    if any(p.exists() or p.is_symlink() for p in checks):
        return "unverified"
    data = game / "Data"
    if data.is_dir() and any(data.glob("blue-kanto-*")):
        return "unverified"
    return "absent"


def _default_run(argv: list[str], project: Path, env: dict[str, str]) -> None:
    print("[KANTO AUTO] >", " ".join(argv[1:]), flush=True)
    subprocess.run(argv, cwd=project, env=env, check=True)


def integrate(project: Path = ROOT, game: Path | None = None,
              *, run: Callable | None = None) -> dict:
    """Idempotent and fail-soft integration for the Windows website installer.

    Test seams accept an injected runner, so CI never downloads the source,
    launches the game or operates on real saves.
    """
    project = Path(project).resolve()
    game = Path(game if game is not None else project / "game").resolve()
    # Both installer and source bootstrap assume the project's own game/.
    if game != (project / "game").resolve():
        return {"status": "skipped_foreign_path", "changed": False}
    if not (game / "Game.exe").is_file() or not (game / "PBS/pokemon.txt").is_file():
        return {"status": "skipped_no_game", "changed": False}

    run = run or _default_run
    env = {**os.environ, "BLUE_GAME_DIR": str(game), "PYTHONUTF8": "1"}

    def invoke(script: str, *args: str) -> None:
        run([sys.executable, script, *args], project, env)

    state = detect_existing(game)
    if state == "unverified":
        try:
            invoke(KANTO_IMPORTER, "--game", str(game), "--verify-installed")
            # New releases also refresh Kanto's OWN Ruby runtime, but only
            # when its current SHA-256 matches the manifest of the old import.
            # The runtime updater never replaces maps, PBS, saves or user edits.
            invoke(KANTO_IMPORTER, "--game", str(game), "--sync-runtime", "--apply")
            return {"status": "already_integrated", "changed": False}
        except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as err:
            print("[KANTO AUTO] Instalacao antiga/parcial ou verificacao falhou:", err, flush=True)
            print("[KANTO AUTO] Nao sobrescrevi mapas nem saves. Consulte "
                  "docs/KANTO_INTEGRACAO_DECADES.md para migracao segura.", flush=True)
            return {"status": "manual_migration_required", "changed": False}

    try:
        print("[KANTO AUTO] Preparando os mapas verificados de Kanto "
              "automaticamente no Decades...", flush=True)
        # Existing author-hosted source is hash-pinned and extracted as data
        # only by ensure_source.py (no downloaded executable/script is run).
        invoke(KANTO_SOURCE_BOOTSTRAP)
        # The existing installer builds in .blue-work, validates the pilot,
        # checks all map IDs, and atomically commits files into game/.
        invoke(KANTO_IMPORTER, "--game", str(game), "--apply")
        invoke(KANTO_IMPORTER, "--game", str(game), "--verify-installed")
        print("[KANTO AUTO] Kanto integrado. A compilacao nativa ainda sera "
              "conferida ao abrir Game.exe.", flush=True)
        return {"status": "integrated", "changed": True}
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as err:
        print("[KANTO AUTO] Nao foi possivel concluir Kanto:", err, flush=True)
        print("[KANTO AUTO] Decades continua disponivel. O instalador "
              "nao removeu saves nem forçou a migracao de mapas.", flush=True)
        return {"status": "kanto_unavailable", "changed": False}


if __name__ == "__main__":
    import json
    result = integrate()
    print(json.dumps(result, ensure_ascii=False))
    # No failure exit: missing third-party Kanto assets must not block Decades.
