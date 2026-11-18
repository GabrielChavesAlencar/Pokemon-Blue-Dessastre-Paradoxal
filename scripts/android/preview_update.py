"""Explicit, fail-closed preview installer for the connected-map Android patch.

This is NOT the stable Android updater. It only accepts the separate,
pre-release tag supplied by the user and will not choose any other release.
It uses the project's pinned updater and its existing SHA-256 and save guards.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import urllib.request

REPO = "GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal"
API = "https://api.github.com/repos/" + REPO
PREVIEW = re.compile(r"android-map-perf-preview-([0-9a-f]{7})\Z")
FULL_SHA = re.compile(r"[0-9a-f]{40}\Z")


def get_json(url):
    request = urllib.request.Request(url, headers={
        "User-Agent": "Pokemon-Blue-Android-Map-Preview",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def trusted_preview(tag):
    match = PREVIEW.fullmatch(tag)
    if not match:
        raise ValueError("Apenas releases de teste android-map-perf-preview-XXXXXXX são aceitas.")
    release = get_json(API + "/releases/tags/" + tag)
    revision = release.get("target_commitish")
    if (release.get("tag_name") != tag or
            not release.get("prerelease") or release.get("draft") or
            not isinstance(revision, str) or
            not FULL_SHA.fullmatch(revision) or
            revision[:7] != match.group(1)):
        raise ValueError("Identidade, revisão ou tipo da release de teste inválidos.")
    return release, revision


def load_pinned_updater(revision, temporary):
    # Never load a mutable branch or the launcher already installed by JoiPlay:
    # the actual update implementation is pinned to the audited release commit.
    source_url = "https://raw.githubusercontent.com/" + REPO + "/" + revision + "/scripts/android/update_client.py"
    request = urllib.request.Request(source_url, headers={
        "User-Agent": "Pokemon-Blue-Android-Map-Preview",
    })
    with urllib.request.urlopen(request, timeout=45) as response:
        data = response.read(100000)
    if not data.startswith(b'"""Android JoiPlay updater companion') or len(data) >= 100000:
        raise ValueError("Implementação de atualização Android inesperada.")
    filename = temporary / "blue_updater_pinned.py"
    filename.write_bytes(data)
    spec = importlib.util.spec_from_file_location("blue_updater_pinned", filename)
    if spec is None or spec.loader is None:
        raise ValueError("Biblioteca do atualizador indisponível.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.REPO != REPO:
        raise ValueError("Identidade do atualizador não corresponde ao projeto.")
    return module


def install(root, tag, apply=False):
    root = root.expanduser().resolve()
    release, revision = trusted_preview(tag)
    with tempfile.TemporaryDirectory(prefix="blue-map-preview-") as folder:
        module = load_pinned_updater(revision, Path(folder))
        installed = module.read_installed(root)
        if installed["channel"] != "multiregion":
            raise ValueError("Este teste exige a edição Android Decades + Kanto + Hoenn.")
        manifest_name = module.CHANNELS["multiregion"][1]
        manifest_url = module.asset_url(release, manifest_name)
        if not manifest_url:
            raise ValueError("Manifesto do pacote de teste ausente.")
        manifest = module.get_json(manifest_url)
        if (manifest.get("schema") != 1 or
                manifest.get("channel") != "multiregion" or
                manifest.get("revision") != revision or
                not isinstance(manifest.get("files"), dict)):
            raise ValueError("Manifesto de teste inválido ou sem proveniência.")
        module.verify_forward_revision(installed["revision"], revision)
        if installed["revision"] == revision:
            print("A otimização de mapas já está instalada:", revision[:7])
            return 0
        patch = module.compatible_patch(release, installed, manifest)
        if not patch:
            raise ValueError("Não há delta validado para a versão instalada; não baixar ZIP completo.")
        print("Instalado:", installed["revision"][:7])
        print("Teste disponível:", revision[:7])
        print("Patch incremental:", patch["asset"], patch["size"], "bytes")
        if not apply:
            print("Feche completamente o JoiPlay e execute o mesmo comando com --update.")
            return 0
        local = root / ".blue-android-downloads" / patch["asset"]
        try:
            module.download(module.asset_url(release, patch["asset"]), local,
                            patch["sha256"], patch["size"])
            changed, removed, backup = module.apply_patch(root, installed, manifest, local)
            if backup is not None:
                raise ValueError("Atualizador inesperadamente criou backup.")
            print("Patch de mapas instalado:", changed,
                  "arquivos alterados;", removed,
                  "removidos; sem reinstalar nem copiar saves.")
            print("Revisão de teste:", revision)
        finally:
            local.unlink(missing_ok=True)
            if local.parent.is_dir() and not any(local.parent.iterdir()):
                local.parent.rmdir()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--game-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args(argv)
    try:
        return install(args.game_dir, args.tag, args.update)
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as error:
        print("ATUALIZAÇÃO BLOQUEADA:", error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
