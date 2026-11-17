#!/usr/bin/env python3
"""Pokemon Blue: atualizador Android (iniciador de arquivo unico).

Coloque este arquivo na pasta do Game.exe e execute com Python/Termux.
Busca o cliente oficial mais recente e aplica apenas um patch compatível,
sem backup automático. Não baixa ZIP completo sem --full --update.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.request

OFFICIAL_SOURCE = (
    "https://raw.githubusercontent.com/GabrielChavesAlencar/"
    "Pokemon-Blue-Dessastre-Paradoxal/main/scripts/android/update_client.py"
)


def main():
    game_dir = Path(__file__).resolve().parent
    request = urllib.request.Request(
        OFFICIAL_SOURCE,
        headers={"User-Agent": "Pokemon-Blue-Android-Updater/1.0"},
    )
    print("Buscando atualizador Android oficial...", flush=True)
    with urllib.request.urlopen(request, timeout=45) as response:
        source = response.read(1024 * 1024 + 1)
    if (len(source) > 1024 * 1024
            or b"def apply_patch(" not in source
            or b"def compatible_patch(" not in source
            or b"def verify_forward_revision(" not in source):
        raise ValueError("A fonte oficial do atualizador esta ausente ou invalida.")
    fd, temporary = tempfile.mkstemp(prefix="blue-android-client-", suffix=".py")
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(source)
        args = sys.argv[1:]
        if "--game-dir" not in args:
            args = ["--game-dir", str(game_dir), *args]
        return subprocess.call([sys.executable, temporary, *args], cwd=str(game_dir))
    finally:
        Path(temporary).unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as exc:
        print("Nao foi possivel iniciar o atualizador:", exc, file=sys.stderr)
        sys.exit(1)
