#!/usr/bin/env python3
"""CH04: fail closed when a standalone Sinnoh pilot leaks into shared Decades.

This module reads only filenames and small text/Ruby plugin files. It never
removes or migrates files and never audits or touches the separate pilot copy.
"""
from __future__ import annotations
import re
from collections.abc import Mapping
from pathlib import Path

LEGACY_FILE = "sinnohpreview.rb"
LEGACY_FOLDER = "zzzzz blue sinnoh pilot"
LEGACY_MODULE = re.compile(rb"(?m)^[ \t]*module[ \t]+BlueSinnohPreview\b")
LEGACY_META = re.compile(rb"(?im)^\s*Scripts\s*=\s*SinnohPreview\.rb\s*$")
MARKERS = frozenset({
    "sinnoh pilot.json",
    "data/blue-sinnoh-compile-request.txt",
    "data/blue-sinnoh-compiled.txt",
    "data/blue-sinnoh-rival-ready.txt",
    "data/blue-sinnoh-qa-compile-request.txt",
    "data/blue-sinnoh-qa-compiled.txt",
    "data/blue-sinnoh-qa-engine-check.json",
})
TITLE = re.compile(r"(?im)^\s*Title\s*=\s*Sinnoh Piloto\s*$")
SAVE = re.compile(r'(?i)"dataPathApp"\s*:\s*"Sinnoh Piloto"')


def fail(reason: str) -> None:
    raise ValueError(
        "[SINNOH CH04] SinnohPreview.rb / BlueSinnohPreview legado não permitido "
        "na instalação compartilhada: " + reason +
        ". Preserve piloto e saves em cópia isolada; nenhuma exclusão automática."
    )


def entry(folder: Path, name: str) -> Path | None:
    if folder.is_symlink():
        fail("pasta symlink não auditável: " + str(folder))
    if not folder.is_dir():
        return None
    items = [x for x in folder.iterdir() if x.name.casefold() == name.casefold()]
    if len(items) > 1:
        fail("nomes duplicados por caixa: " + name)
    return items[0] if items else None


def read_small(path: Path, *, max_size: int = 262144) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > max_size:
        fail("arquivo de plugin/configuração não auditável: " + str(path))
    return path.read_bytes()


def assert_no_legacy_sinnoh_shared(game: Path) -> None:
    """No writes; do not infer ownership of existing Map800–805 from IDs."""
    game = Path(game)
    if game.is_symlink():
        fail("game/ é symlink")
    if not game.exists():
        return
    if not game.is_dir():
        fail("game/ não é diretório")
    for rel in sorted(MARKERS):
        parent, name = rel.rsplit("/", 1) if "/" in rel else ("", rel)
        # Case-insensitive lookup of each path segment (Data vs data on Linux).
        folder = entry(game, parent) if parent else game
        marker = entry(folder, name) if folder is not None else None
        if marker is not None:
            fail("marcador de perfil piloto encontrado: " + str(marker))
    plugins = entry(game, "Plugins")
    if plugins is not None:
        if plugins.is_symlink() or not plugins.is_dir():
            fail("diretório Plugins inválido")
        for package in plugins.iterdir():
            if package.is_symlink():
                fail("plugin symlink: " + str(package))
            if package.name.casefold() == LEGACY_FOLDER:
                fail("pasta do piloto legado: " + str(package))
            if package.is_file() and package.name.casefold() == LEGACY_FILE:
                fail("script legado: " + str(package))
            if not package.is_dir():
                continue
            for item in package.iterdir():
                if item.is_symlink():
                    fail("plugin possui symlink: " + str(item))
                if not item.is_file():
                    continue
                low = item.name.casefold()
                if low == LEGACY_FILE:
                    fail("script legado: " + str(item))
                if low == "meta.txt" and LEGACY_META.search(read_small(item)):
                    fail("meta.txt aponta para SinnohPreview.rb: " + str(item))
                if low.endswith(".rb") and item.stat().st_size <= 4 * 1024 * 1024:
                    if LEGACY_MODULE.search(item.read_bytes()):
                        fail("módulo BlueSinnohPreview: " + str(item))
    for filename, pattern, label in (("Game.ini", TITLE, "título"),
                                     ("mkxp.json", SAVE, "saves")):
        config = entry(game, filename)
        if config is not None and pattern.search(read_small(config).decode("utf-8-sig", "replace")):
            fail("configuração do piloto independente (" + label + "): " + str(config))


def assert_no_legacy_sinnoh_overlay(files: Mapping[str, bytes]) -> None:
    """Reject plugin, launcher, save-profile and marker files in shared overlay."""
    if not isinstance(files, Mapping):
        fail("overlay inválido")
    for path, data in files.items():
        if not isinstance(path, str) or not isinstance(data, bytes):
            fail("overlay com arquivo inválido")
        name = path.replace("\\", "/").casefold()
        if name in MARKERS:
            fail("overlay inclui marcador piloto: " + path)
        if name.startswith("plugins/"):
            if name.endswith("/" + LEGACY_FILE) or name.startswith("plugins/" + LEGACY_FOLDER + "/"):
                fail("overlay inclui plugin legado: " + path)
            if name.endswith("/meta.txt") and LEGACY_META.search(data):
                fail("overlay meta.txt aponta SinnohPreview.rb")
            if name.endswith(".rb") and LEGACY_MODULE.search(data):
                fail("overlay inclui módulo BlueSinnohPreview")
        if name == "game.ini" and TITLE.search(data.decode("utf-8-sig", "replace")):
            fail("overlay inclui título do piloto")
        if name == "mkxp.json" and SAVE.search(data.decode("utf-8-sig", "replace")):
            fail("overlay inclui perfil de save do piloto")
        if name == "data/scripts.rxdata":
            fail("overlay tenta copiar Scripts.rxdata de piloto isolado")
