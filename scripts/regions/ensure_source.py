"""Prepare the hash-pinned editable FRLG map source for Kanto test mode.

Runs ONLY after a user chose Testar Kanto or its standalone BAT. Never alters
Decades game/, save slots or a pre-existing edited source directory.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

from audit import KANTO, ROOT, json_file

# Same original author-hosted download and SHA256 used by kanto-pilot-check.yml.
SOURCE_URL = (
    "https://drive.usercontent.google.com/download"
    "?id=1dsqD8lEJCz-lioEruRqQycWJLCUVxVtI&export=download&confirm=t"
)
RELATIVE_SOURCE = Path(".blue-work/frlg-source/Essentials FRLG")
RELATIVE_ARCHIVE = Path(".blue-work/frlg-source/FRLG.rar")
MAX_DOWNLOAD = 2 * 1024 * 1024 * 1024
ALLOWED = (
    re.compile(r"^Essentials FRLG/Data/(?:Map[0-9]+|MapInfos|Tilesets|System)\.rxdata$"),
    re.compile(r"^Essentials FRLG/PBS/(?:encounters|trainers|map_connections|map_metadata)\.txt$"),
    re.compile(r"^Essentials FRLG/Graphics/(?:Characters|Tilesets|Autotiles)/[^/]+\.png$"),
)
REQUIRED = (
    "Data/MapInfos.rxdata", "Data/Tilesets.rxdata", "Data/System.rxdata",
    "Data/Map005.rxdata", "Data/Map032.rxdata", "Data/Map036.rxdata",
    "Data/Map037.rxdata", "Data/Map038.rxdata", "Data/Map039.rxdata",
    "Data/Map042.rxdata",
    "PBS/encounters.txt", "PBS/trainers.txt", "PBS/map_connections.txt",
    "PBS/map_metadata.txt",
)


def complete(source: Path) -> bool:
    return source.is_dir() and all((source / name).is_file() for name in REQUIRED)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_pinned(url: str, archive: Path, expected: str) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.is_file():
        if sha256(archive) == expected:
            print("[OK] Pacote FRLG previamente baixado e verificado.")
            return
        raise RuntimeError("Existe FRLG.rar com hash diferente. Nenhum arquivo foi substituído.")

    part = archive.with_name(archive.name + ".part")
    if part.exists():
        raise RuntimeError("Download FRLG parcial encontrado. Confira .blue-work/frlg-source/FRLG.rar.part.")
    print("[KANTO] Baixando a fonte FRLG do autor original; pode exigir internet.", flush=True)
    digest = hashlib.sha256()
    size = 0
    try:
        request = Request(url, headers={"User-Agent": "PokemonBlueKantoTest/1.0"})
        with urlopen(request, timeout=120) as response, part.open("xb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_DOWNLOAD:
                    raise RuntimeError("Fonte FRLG excedeu o limite máximo de tamanho.")
                digest.update(chunk)
                output.write(chunk)
        if digest.hexdigest() != expected:
            raise RuntimeError("O hash da fonte FRLG não confere com o manifesto fixado; download recusado.")
        os.replace(part, archive)
    except BaseException:
        part.unlink(missing_ok=True)
        raise
    print("[OK] Fonte FRLG verificada por SHA-256.", flush=True)


def selected_members(listing: str) -> list[str]:
    # Only the project's known data, PBS and graphics; never executables,
    # scripts, absolute paths, traversals, links to another top-level folder.
    names = []
    seen = set()
    for raw in listing.splitlines():
        item = raw.replace("\\", "/").rstrip("\r")
        if item in seen:
            raise RuntimeError("Entrada duplicada no pacote FRLG: " + item)
        if item.startswith("/") or ".." in item.split("/") or "\x00" in item:
            raise RuntimeError("Caminho inseguro no pacote FRLG.")
        if any(pattern.fullmatch(item) for pattern in ALLOWED):
            seen.add(item)
            names.append(item)
    if len(names) < 200:
        raise RuntimeError("Arquivo FRLG não contém os mapas e gráficos esperados.")
    for name in REQUIRED:
        if "Essentials FRLG/" + name not in seen:
            raise RuntimeError("Falta arquivo obrigatório na fonte FRLG: " + name)
    return names


def find_tar() -> str:
    candidate = shutil.which("tar")
    if candidate:
        return candidate
    for directory in (ROOT / "tools").glob("git-*/usr/bin/tar.exe"):
        if directory.is_file():
            return str(directory)
    raise RuntimeError("O extrator tar do Windows não foi encontrado.")


def prepare(root: Path = ROOT, url: str = SOURCE_URL) -> Path:
    manifest = json_file(KANTO)
    expected = manifest["sha256"].lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise RuntimeError("Hash da fonte FRLG inválido no manifesto.")
    source = (root / RELATIVE_SOURCE).resolve()
    archive = (root / RELATIVE_ARCHIVE).resolve()
    if complete(source):
        print("[OK] Fonte editável FRLG já preparada para o teste de Kanto.", flush=True)
        return source
    if source.exists():
        raise RuntimeError("Fonte FRLG já existe mas está incompleta. Não vou sobrescrever alterações locais.")

    download_pinned(url, archive, expected)
    tar = find_tar()
    listing = subprocess.run([tar, "-tf", str(archive)], text=True,
                             encoding="utf-8", errors="replace", capture_output=True, check=True)
    names = selected_members(listing.stdout)
    source.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".frlg-stage-", dir=source.parent) as temporary:
        stage = Path(temporary)
        members = stage / "members.txt"
        members.write_text("\n".join(names) + "\n", encoding="utf-8")
        subprocess.run([tar, "-xf", str(archive), "-C", str(stage), "-T", str(members)],
                       check=True, capture_output=True)
        extracted = stage / "Essentials FRLG"
        if not complete(extracted):
            raise RuntimeError("A extração da fonte FRLG não contém todos os arquivos exigidos.")
        for entry in extracted.rglob("*"):
            if entry.is_symlink() or not entry.resolve().is_relative_to(extracted.resolve()):
                raise RuntimeError("A extração encontrou um caminho externo ou link simbólico.")
        if source.exists():
            raise RuntimeError("A fonte FRLG apareceu durante a preparação. Não vou sobrescrevê-la.")
        extracted.rename(source)
    print("[OK] Fonte FRLG preparada sem modificar o jogo ou os saves do Decades.", flush=True)
    return source


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()
    try:
        prepare()
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print("[ERRO] Fonte de Kanto:", error, file=sys.stderr)
        print("[AJUDA] Ver docs/KANTO_TESTE_EXPERIMENTAL.md.", file=sys.stderr)
        raise SystemExit(2)
