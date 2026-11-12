"""Windows GUI diagnostic for the isolated Pallet-to-Pewter Kanto pilot.

The native GitHub smoke test injects a proof script and mocks battle results;
this command instead launches the original Game.exe in the real game startup.
A visible window is only evidence of boot, NEVER proof of completing gameplay.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path

from audit import ROOT
from pilot import OUTPUT, PILOT_META, SOURCE, build, pilot_is_current, revised_path
from verify_pilot import inspect

LOG_NAMES = ("errorlog.txt", "mkxp.log", "mkxp.txt", "stderr.txt", "stdout.txt")


def windows_for_pid(pid: int) -> list[dict[str, str | int]]:
    """Enumerate real, visible top-level windows owned by a process."""
    if sys.platform != "win32":
        return []
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.EnumWindows.argtypes = (ctypes.c_void_p, wintypes.LPARAM)
    user32.EnumWindows.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetWindowTextLengthW.argtypes = (wintypes.HWND,)
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.IsWindowVisible.argtypes = (wintypes.HWND,)
    user32.IsWindowVisible.restype = wintypes.BOOL
    result = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def visit(hwnd, _):
        owner = wintypes.DWORD(0)
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            title = ctypes.create_unicode_buffer(max(length + 1, 1))
            user32.GetWindowTextW(hwnd, title, len(title))
            result.append({"hwnd": int(hwnd), "title": title.value})
        return True

    if not user32.EnumWindows(visit, 0):
        raise ctypes.WinError(ctypes.get_last_error())
    return result


def tail(path: Path, limit: int = 4500) -> str:
    if not path.is_file():
        return ""
    # Error logs are short. Bound the read in case a game writes large logs.
    with path.open("rb") as stream:
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.seek(max(0, size - limit))
        return stream.read().decode("utf-8", errors="replace")


def classify(window_seen: bool, returncode: int | None, stderr: str, errorlog: str) -> str:
    if "physfs" in (stderr + "\n" + errorlog).lower():
        return "physfs_error"
    if returncode is not None and returncode != 0:
        return "process_failed"
    if not window_seen and returncode is not None:
        return "process_exited_without_visible_window"
    if not window_seen:
        return "no_visible_window"
    return "window_observed_not_gameplay_verified"


def monitor(pilot: Path, seconds: int, probe: bool, report_dir: Path) -> tuple[int, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = report_dir / ("kanto-gui-" + stamp + ".json")
    stdout_path = report_dir / ("kanto-gui-" + stamp + "-stdout.txt")
    stderr_path = report_dir / ("kanto-gui-" + stamp + "-stderr.txt")
    errors = pilot / "errorlog.txt"
    before_error = errors.stat().st_mtime_ns if errors.exists() else None
    seen = False
    titles: set[str] = set()
    started = time.monotonic()
    exited = None
    terminated_by_probe = False
    interrupted_by_user = False
    print("[INFO] Abrindo Game.exe no piloto isolado (nao usa save do Decades).", flush=True)
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen([str(pilot / "Game.exe")], cwd=str(pilot),
                                   stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL)
        try:
            while True:
                exited = process.poll()
                if exited is not None:
                    break
                for window in windows_for_pid(process.pid):
                    seen = True
                    titles.add(str(window["title"]))
                elapsed = time.monotonic() - started
                if probe and elapsed >= seconds:
                    break
                if not probe and not seen and elapsed >= seconds:
                    print("[AVISO] Nenhuma janela detectada. O jogo ainda esta em execucao.", flush=True)
                    print("[INFO] Verifique se esta compilando; feche o jogo para gerar relatorio.", flush=True)
                    # Only report this reminder once.
                    seconds = 10**12
                time.sleep(0.4)
        except KeyboardInterrupt:
            interrupted_by_user = True
            print("[INFO] Interrompido. Fechando somente a copia piloto.", flush=True)
        finally:
            if probe and process.poll() is None:
                terminated_by_probe = True
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            elif process.poll() is None:
                # Interactive mode normally runs until the player closes the game.
                # Ctrl+C is the only reason to stop the child here.
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            exited = process.returncode
    after_error = errors.stat().st_mtime_ns if errors.exists() else None
    error_text = tail(errors) if after_error is not None and after_error != before_error else ""
    stderr_text = tail(stderr_path)
    result = classify(seen, None if terminated_by_probe or interrupted_by_user else exited, stderr_text, error_text)
    # A probe is deliberately stopped after inspecting startup; that termination
    # is NOT a gameplay failure or a successful full playthrough.
    data = {
        "mode": "noninteractive_window_probe" if probe else "interactive_manual_session",
        "status": result,
        "window_seen": seen,
        "window_titles": sorted(titles),
        "duration_seconds": round(time.monotonic() - started, 2),
        "exit_code": exited,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "errorlog_tail": error_text,
        "stderr_tail": stderr_text,
        "notes": "Window detection does not verify movement, collision, battle results, capture or save/load.",
    }
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[DIAGNOSTICO] {result}; janela={seen}; duracao={data['duration_seconds']}s", flush=True)
    print(f"[RELATORIO] {output}", flush=True)
    if error_text:
        print("[ERRO DO MOTOR]\n" + error_text[-2000:], flush=True)
    if stderr_text:
        print("[STDERR]\n" + stderr_text[-2000:], flush=True)
    return (0 if seen and not result.endswith("error") and result != "process_failed" else 2), output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT, help="Pasta isolada do piloto")
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--game", type=Path, default=ROOT / "game")
    parser.add_argument("--probe", action="store_true", help="Testa janela durante N segundos sem controlar o jogo")
    parser.add_argument("--seconds", type=int, default=30, help="Limite de detecao inicial")
    parser.add_argument("--no-build", action="store_true", help="Exige copia ja preparada")
    parser.add_argument("--rebuild", action="store_true", help="Monta nova pasta; nunca substitui a anterior")
    args = parser.parse_args()
    if sys.platform != "win32":
        print("[ERRO] A verificacao grafica do Game.exe exige Windows.", file=sys.stderr)
        return 2
    if not 3 <= args.seconds <= 300:
        parser.error("--seconds deve ficar entre 3 e 300")
    output = args.output.resolve()
    workspace = (ROOT / ".blue-work").resolve()
    if output == workspace or not output.is_relative_to(workspace):
        parser.error("O piloto deve ficar numa subpasta de .blue-work")
    if args.rebuild:
        output = revised_path(output)
    try:
        if output.exists() and not pilot_is_current(output):
            if args.no_build:
                raise ValueError("A copia existente esta desatualizada. Execute sem --no-build ou use --rebuild.")
            replacement = revised_path(output)
            print(f"[INFO] Copia antiga preservada em {output}", flush=True)
            print(f"[INFO] Recriando piloto atualizado em {replacement}", flush=True)
            output = replacement
        if not (output / PILOT_META).is_file():
            if args.no_build:
                raise ValueError("Piloto inexistente; rode sem --no-build para preparar uma copia.")
            print("[INFO] Preparando copia isolada, sem alterar a instalacao principal.", flush=True)
            build(args.source.resolve(), args.game.resolve(), output)
        inspect(output)
        code, _ = monitor(output, args.seconds, args.probe, workspace / "kanto-gui-reports")
        return code
    except (OSError, ValueError, KeyError) as error:
        print(f"[ERRO] {type(error).__name__}: {error}", file=sys.stderr)
        print("[DICA] Confira docs/KANTO_TESTE_WINDOWS.md", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
