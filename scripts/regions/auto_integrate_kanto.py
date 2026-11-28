"""Automatically integrate Kanto in Blue-Story's shared Decades installation.

Called from scripts/install_game.py after the native Blue plugins are prepared.
Does not run for the Hub-only release, on foreign game paths, or when an old
Kanto import might already own RXDATA/map IDs. A missing/offline FRLG source is
a nonfatal Kanto failure, never a reason to block the native Decades game.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]

# Keep the importer the only writer of Kanto resources: it performs the full
# pilot verification, hash checks, backups, marker-last commit and rollback.
KANTO_IMPORTER = "scripts/regions/install_kanto.py"
KANTO_SOURCE_BOOTSTRAP = "scripts/regions/ensure_source.py"
KANTO_MARKER = Path("Data/blue-kanto-start.txt")
KANTO_MANIFEST = Path("Data/blue-kanto-install.json")
STATUS_FILE = Path(".blue-work/kanto-install-status.json")
LOG_FILE = Path(".blue-work/kanto-install.log")
READY = frozenset({"already_integrated", "integrated", "already_integrated_runtime_preserved"})
RIVAL_COMPILER_STAMP = Path(".blue-work/kanto-gary-pbs-v1.sha256")


def ensure_rival_compilation(project: Path, game: Path) -> bool:
    """Request one normal Essentials recompilation after updating Gary's PBS.

    The previous launcher could show Kanto as installed while the compiled
    trainer data was from an older Decades build. This uses the existing
    compile marker, not direct changes to any trainer/PC/save files.
    """
    files = [game / "PBS/trainers_kanto.txt", game / "PBS/trainer_types_kanto.txt"]
    if any(not path.is_file() for path in files):
        return False
    signature = hashlib.sha256()
    for path in files:
        signature.update(path.name.encode("ascii") + b"\0")
        signature.update(hashlib.sha256(path.read_bytes()).digest())
    value = signature.hexdigest()
    stamp = project / RIVAL_COMPILER_STAMP
    prior = stamp.read_text(encoding="ascii").strip() if stamp.is_file() else ""
    compiled = game / "Data/trainers.dat"
    stale = (not compiled.is_file() or
             compiled.stat().st_mtime < max(path.stat().st_mtime for path in files))
    if prior == value and not stale:
        return False
    request = game / "Data/blue-compile-request.txt"
    request.parent.mkdir(parents=True, exist_ok=True)
    request.write_text("compile", encoding="ascii")
    stamp.parent.mkdir(parents=True, exist_ok=True)
    stamp.write_text(value + "\n", encoding="ascii")
    print("[KANTO AUTO] Recompilacao nativa requisitada para os "
          "3 times de Gary, treinador e tipos Kanto.", flush=True)
    return True



def _persist(project: Path, info: dict) -> dict:
    """Publish the REAL result before the installer decides whether to launch."""
    payload = {**info, "ready": info["status"] in READY,
               "timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "log": str(project / LOG_FILE)}
    target = project / STATUS_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, target)
    return payload


def _failure(phase: str, err: Exception) -> str:
    # The original bootstrap showed a false 'everything is ready' message;
    # always expose which operation failed and the log location.
    description = str(err).strip() or type(err).__name__
    return f"{phase}: {description}"


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
    """Stream subprocess output to both launcher and a persistent log.

    A failing child script previously surfaced only exit code 1. Its actual
    cause (source 403, missing assets, old maps, etc.) must be diagnosable.
    """
    log_path = project / LOG_FILE
    log_path.parent.mkdir(parents=True, exist_ok=True)
    command = " ".join(argv[1:])
    print("[KANTO AUTO] >", command, flush=True)
    with log_path.open("a", encoding="utf-8") as log:
        log.write("\n=== " + datetime.now(timezone.utc).isoformat() + " " + command + " ===\n")
        log.flush()
        tail = []
        with subprocess.Popen(argv, cwd=project, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                              errors="replace", bufsize=1) as process:
            for line in process.stdout:
                print(line, end="", flush=True)
                log.write(line)
                log.flush()
                if line.strip():
                    tail.append(line.strip())
                    tail = tail[-5:]
            returncode = process.wait()
        if returncode:
            detail = " | ".join(tail[-2:])
            raise RuntimeError(
                f"Etapa falhou (codigo {returncode}): {detail}. "
                f"Log: {log_path}"
            )


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
        return _persist(project, {"status": "skipped_foreign_path", "changed": False,
                                  "reason": "Instalacao fora da pasta gerenciada."})
    if not (game / "Game.exe").is_file() or not (game / "PBS/pokemon.txt").is_file():
        return _persist(project, {"status": "skipped_no_game", "changed": False,
                                  "reason": "Base Decades incompleta."})

    run = run or _default_run
    env = {**os.environ, "BLUE_GAME_DIR": str(game), "PYTHONUTF8": "1"}

    def invoke(script: str, *args: str) -> None:
        run([sys.executable, script, *args], project, env)

    state = detect_existing(game)
    if state == "unverified":
        try:
            invoke(KANTO_IMPORTER, "--game", str(game), "--verify-installed")
        except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as err:
            # Only known shipped predecessors may enter the migration.
            # The importer independently checks exact ownership and hashes.
            try:
                legacy = json.loads((game / KANTO_MANIFEST).read_text(encoding="utf-8"))
                catalogue = project / "data/regions/kanto-source.json"
                target_maps = json.loads(catalogue.read_text("utf8"))["maps"] if catalogue.is_file() else {}
                target_count = len(target_maps) if catalogue.is_file() else 145
                old_maps = legacy.get("maps")
                old_count = len(old_maps) if isinstance(old_maps, dict) else 0
                # K03-E's automatic path is only for its exact audited
                # 156-map predecessor. The importer still proves ownership,
                # hashes, allocation and rollback before writing anything.
                k03e_sources = {"23", "79", "81", "82"}
                k03e_migration = (target_count == 160 and old_count == 156 and
                                  k03e_sources <= target_maps.keys() and
                                  set(old_maps) == target_maps.keys() - k03e_sources)
                rock_sources = {"86", "87", "88", "90", "91"}
                k04_migration = (target_count == 165 and old_count == 160 and
                                 rock_sources | k03e_sources <= target_maps.keys() and
                                 set(old_maps) == target_maps.keys() - rock_sources)
                candidate = (legacy.get("schema") == 1 and
                             legacy.get("source") == "Essentials FRLG 21.1" and
                             ((target_count == 145 and old_count == 142) or
                              (target_count == 151 and old_count in (142, 145)) or
                              (target_count == 152 and old_count in (142, 145, 151)) or
                              (target_count == 156 and old_count in (142, 145, 151, 152)) or
                              k03e_migration or k04_migration or
                              (target_count == old_count and target_count >= 151 and
                               ("Cerulean door" in str(err) or
                                "S.S. Anne rival gate:" in str(err)))) and
                             (game / KANTO_MARKER).is_file())
            except (OSError, ValueError, TypeError, AttributeError, KeyError):
                candidate = False
            if candidate:
                try:
                    invoke(KANTO_SOURCE_BOOTSTRAP)
                    invoke(KANTO_IMPORTER, "--game", str(game), "--migrate-existing", "--apply")
                    invoke(KANTO_IMPORTER, "--game", str(game), "--verify-installed")
                    recompiling = ensure_rival_compilation(project, game)
                    return _persist(project, {"status": "integrated", "changed": True,
                                              "source": f"verified_{old_count}_to_{target_count}_migration",
                                              "rival_compile_requested": recompiling})
                except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as migration_error:
                    err = migration_error
            reason = _failure("Verificacao de Kanto existente / migracao segura", err)
            print("[KANTO AUTO]", reason, flush=True)
            print("[KANTO AUTO] Nao sobrescrevi mapas nem saves. O instalador "
                  "nao fara migracao de MapIDs automaticamente.", flush=True)
            return _persist(project, {"status": "manual_migration_required",
                                      "changed": False, "reason": reason})
        try:
            invoke(KANTO_IMPORTER, "--game", str(game), "--sync-runtime", "--apply")
        except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as err:
            # An optional script patch is NOT proof that the map installation
            # failed. Keep the already-verified Kanto available as-is, and
            # never clobber a hand-edited runtime.
            reason = _failure("Atualizacao opcional do plugin Kanto", err)
            print("[KANTO AUTO]", reason, flush=True)
            recompiling = ensure_rival_compilation(project, game)
            return _persist(project, {"status": "already_integrated_runtime_preserved",
                                      "changed": False, "reason": reason,
                                      "rival_compile_requested": recompiling})
        recompiling = ensure_rival_compilation(project, game)
        return _persist(project, {"status": "already_integrated", "changed": False,
                                  "rival_compile_requested": recompiling})

    try:
        print("[KANTO AUTO] Preparando os mapas verificados de Kanto "
              "automaticamente no Decades...", flush=True)
        # Prefer a previously audited Kanto pilot when present. The importer
        # itself checks the full revision signature, Decades MapInfos/Tilesets
        # hashes and the real map/PBS files BEFORE writing to game/. This
        # helps existing players who have a local pilot but lost the RAR or
        # cannot reach the author's Google Drive on the updater's first run.
        cached = project / ".blue-work/kanto-pilot/Kanto pilot.json"
        if cached.is_file():
            try:
                print("[KANTO AUTO] Conferindo piloto local ja preparado...", flush=True)
                invoke(KANTO_IMPORTER, "--game", str(game), "--apply")
                invoke(KANTO_IMPORTER, "--game", str(game), "--verify-installed")
                recompiling = ensure_rival_compilation(project, game)
                return _persist(project, {"status": "integrated", "changed": True,
                                          "source": "cached_verified_pilot",
                                          "rival_compile_requested": recompiling})
            except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as cached_error:
                print("[KANTO AUTO] Piloto em cache nao reutilizavel:", cached_error,
                      flush=True)
                if detect_existing(game) != "absent":
                    raise RuntimeError(
                        "Tentativa com cache deixou arquivos regionais parciais. "
                        "Nao vou importar outra copia por cima.") from cached_error
        # Existing author-hosted source is hash-pinned and extracted as data
        # only by ensure_source.py (no downloaded executable/script is run).
        invoke(KANTO_SOURCE_BOOTSTRAP)
        # The existing installer builds in .blue-work, validates the pilot,
        # checks all map IDs, and atomically commits files into game/.
        invoke(KANTO_IMPORTER, "--game", str(game), "--apply")
        invoke(KANTO_IMPORTER, "--game", str(game), "--verify-installed")
        print("[KANTO AUTO] Kanto integrado. O motor ainda precisa compilar PBS.",
              flush=True)
        recompiling = ensure_rival_compilation(project, game)
        return _persist(project, {"status": "integrated", "changed": True,
                                  "rival_compile_requested": recompiling})
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as err:
        reason = _failure("Download/montagem/instalacao de Kanto", err)
        print("[KANTO AUTO]", reason, flush=True)
        print("[KANTO AUTO] Decades permanece intacto; NAO e correto dizer "
              "que a instalacao regional terminou.", flush=True)
        return _persist(project, {"status": "kanto_unavailable", "changed": False,
                                  "reason": reason})


if __name__ == "__main__":
    import json
    result = integrate()
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result["ready"] else 2)
