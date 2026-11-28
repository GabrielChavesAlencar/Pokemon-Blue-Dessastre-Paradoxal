"""Entry point of the code-only Android setup ZIP."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


REMOTE = "https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal.git"
TAG = re.compile(r"refs/tags/android-source-world-([1-9][0-9]*)-([a-f0-9]{7})")
SHA = re.compile(r"[a-f0-9]{40}")
INSTALLER = "ATUALIZAR-ANDROID.py"
INSTALL_NAME = "Pokemon-Blue-Android"
MARKER = "Data/blue-update.json"


def git(*args, cwd=None):
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    return subprocess.check_output(["git", *args], cwd=cwd, env=env, text=True, encoding="utf8").strip()


def release_revisions(output):
    revisions = {}
    for line in output.splitlines():
        sha, _, name = line.partition("\t")
        tag = TAG.fullmatch(name)
        if tag and SHA.fullmatch(sha) and sha.startswith(tag[2]):
            number = int(tag[1])
            if number in revisions and revisions[number] != sha:
                raise ValueError("O GitHub devolveu duas receitas com a mesma versão.")
            revisions[number] = sha
    if not revisions:
        raise ValueError("Nenhuma versão pela fonte foi publicada.")
    return revisions


def recipe_checkout(parent, revision):
    parent.mkdir(parents=True, exist_ok=True)
    target = parent / revision
    if target.resolve() != target:
        raise ValueError("Caminho de cache de receita inválido.")
    if not target.exists():
        staging = Path(tempfile.mkdtemp(prefix=".blue-recipe-", dir=parent))
        try:
            git("init", "--quiet", cwd=staging)
            git("remote", "add", "origin", REMOTE, cwd=staging)
            git("fetch", "--quiet", "--depth=1", "--no-tags", "origin", revision, cwd=staging)
            git("checkout", "--quiet", "--detach", revision, cwd=staging)
            staging.rename(target)
        except Exception:
            if staging.resolve().parent == parent and staging.name.startswith(".blue-recipe-"):
                shutil.rmtree(staging)
            raise
    if (git("rev-parse", "HEAD", cwd=target) != revision or
            git("status", "--porcelain", "--untracked-files=no", cwd=target)):
        raise ValueError("A receita local diverge da revisão publicada.")
    return target


def installed_root(folder):
    if (folder / MARKER).is_file() or (folder / "Game.exe").is_file():
        return folder
    return folder / INSTALL_NAME


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, help="Pasta da instalação criada pela fonte.")
    parser.add_argument("--update", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    launcher = Path(__file__).resolve()
    root = (args.game_dir or installed_root(launcher.parent)).expanduser().absolute()
    if root != root.resolve():
        raise ValueError("A pasta do jogo deve ser um caminho local direto.")
    if not shutil.which("git") or (os.name != "nt" and not shutil.which("bsdtar")):
        raise ValueError("No Termux, instale python, git e bsdtar (pacote libarchive).")
    pending = root.with_name(root.name + "-Compilar-Fontes") / "receita.json"
    if pending.is_symlink() or pending.resolve() != pending:
        raise ValueError("Recibo de compilação indireto.")
    if pending.is_file():
        state = json.loads(pending.read_text("utf8"))
        release, revision = state["release"], state["revision"]
        if type(release) is not int or release < 1 or not SHA.fullmatch(revision):
            raise ValueError("Recibo de compilação inválido.")
        # Resume the audited revision even if a newer recipe appeared mid-install.
        refs = git("ls-remote", "--refs", "--tags", REMOTE,
                   f"refs/tags/android-source-world-{release}-{revision[:7]}")
        if release_revisions(refs).get(release) != revision:
            raise ValueError("A receita da compilação deixou de estar disponível no canal oficial.")
    else:
        releases = release_revisions(git("ls-remote", "--refs", "--tags", REMOTE,
                                         "refs/tags/android-source-world-*"))
        release = max(releases)
        revision = releases[release]
    identity = hashlib.sha256(str(root).encode("utf8")).hexdigest()[:24]
    cache = (Path.home() / ".cache/pokemon-blue-android/fontes" / identity).resolve()
    recipe = recipe_checkout(cache, revision)
    return subprocess.run([sys.executable, str(recipe / "scripts/android/world_source_update.py"),
                           str(root), str(release), revision], cwd=recipe, check=False).returncode


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        print("INSTALAÇÃO NÃO CONCLUÍDA:", error, file=sys.stderr)
        sys.exit(1)
