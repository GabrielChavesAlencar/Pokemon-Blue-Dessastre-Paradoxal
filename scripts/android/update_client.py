"""Android JoiPlay updater companion (Termux/Python). Run with the game CLOSED.

No third-party packages. Never overwrite save files or the JoiPlay save profile.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
import urllib.request
import zipfile

REPO = "GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal"
API = "https://api.github.com/repos/" + REPO
MARKER = "Data/blue-update.json"
CHANNELS = {
    "decades": ("Blue-Android-JoiPlay.zip", "Blue-Android-JoiPlay.update.json"),
    "kanto": ("Blue-Android-Kanto-Piloto.zip", "Blue-Android-Kanto-Piloto.update.json"),
}
ALLOWED_ROOTS = {"Audio", "Graphics", "Fonts", "PBS", "Plugins", "Data"}
FORBIDDEN = {"mkxp.json", "Game.ini", "ATUALIZAR-ANDROID.py", MARKER}
MAX_PATCH_BYTES = 1024 * 1024 * 1024  # 1 GiB; larger changes require full installation.


def safe_path(name):
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        return False
    path = PurePosixPath(name)
    if path.is_absolute() or any(p in (".", "..", "") for p in name.split("/")):
        return False
    if name in FORBIDDEN or len(path.parts) < 2 or path.parts[0] not in ALLOWED_ROOTS:
        return False
    if any(p.lower() in ("saves", "save", "backup", "__pycache__") for p in path.parts):
        return False
    base = path.name.lower()
    if base.startswith(("save", "game.", "game_", "autosave", "auto ", "file ", "lastsave", "backup")):
        return False
    if base.endswith((".bak", ".log", ".tmp", ".sav", ".pyc")):
        return False
    if path.parts[0] == "Data" and base.endswith(".rxdata") and (
        base.startswith(("file", "auto", "game", "save"))):
        return False
    return True


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_json(url):
    request = urllib.request.Request(url, headers={
        "User-Agent": "Pokemon-Blue-Android-Updater",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def release_for(channel):
    if channel == "decades":
        release = get_json(API + "/releases/latest")
        if not str(release.get("tag_name", "")).startswith("battle-hub-"):
            raise ValueError("The latest release is not the Decades distribution.")
        return release
    for release in get_json(API + "/releases?per_page=100"):
        if str(release.get("tag_name", "")).startswith("kanto-android-"):
            return release
    raise ValueError("No Kanto Android release found among the 100 most recent releases.")


def asset_url(release, name):
    for asset in release.get("assets", []):
        if asset.get("name") == name and asset.get("state") == "uploaded":
            url = asset.get("browser_download_url", "")
            prefix = "https://github.com/" + REPO + "/releases/download/"
            if url.startswith(prefix) and url.endswith("/" + name):
                return url
    return None


def read_installed(root):
    with (root / MARKER).open("r", encoding="utf8") as stream:
        info = json.load(stream)
    if info.get("schema") != 1 or info.get("channel") not in CHANNELS:
        raise ValueError("Installation has no supported update manifest.")
    if not isinstance(info.get("files"), dict) or not info.get("revision"):
        raise ValueError("Installed manifest is incomplete.")
    return info


def remote_update(info):
    release = release_for(info["channel"])
    _, manifest_name = CHANNELS[info["channel"]]
    url = asset_url(release, manifest_name)
    if not url:
        raise ValueError("The release has no published Android update manifest.")
    manifest = get_json(url)
    if (manifest.get("schema") != 1 or manifest.get("channel") != info["channel"]
            or manifest.get("revision") != release.get("target_commitish")
            or not isinstance(manifest.get("files"), dict)):
        raise ValueError("Release manifest does not match its channel/revision.")
    return release, manifest


def download(url, destination, expected_sha, expected_size):
    if not isinstance(expected_sha, str) or len(expected_sha) != 64:
        raise ValueError("Download SHA-256 is missing.")
    if not isinstance(expected_size, int) or not 0 < expected_size <= MAX_PATCH_BYTES:
        raise ValueError("Patch exceeds the allowed download size.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_name(destination.name + ".part")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Pokemon-Blue-Android-Updater"})
        with urllib.request.urlopen(request, timeout=60) as response, temp.open("wb") as output:
            total = 0
            while True:
                data = response.read(1024 * 1024)
                if not data:
                    break
                total += len(data)
                if total > expected_size:
                    raise ValueError("Patch download exceeds its stated size.")
                output.write(data)
        if total != expected_size or sha256_file(temp) != expected_sha:
            raise ValueError("Patch checksum/size mismatch; refusing installation.")
        os.replace(temp, destination)
    finally:
        temp.unlink(missing_ok=True)


def _verify_paths(old, new, patch):
    changed = patch.get("changed")
    removed = patch.get("removed", [])
    if not isinstance(changed, dict) or not isinstance(removed, list):
        raise ValueError("Malformed patch file table.")
    paths = list(changed) + removed
    if len(paths) != len(set(paths)) or not all(safe_path(p) for p in paths):
        raise ValueError("Unsafe or duplicated update path.")
    if len(paths) > 100000:
        raise ValueError("Too many update files.")
    if not all(p in new and new[p] == meta for p, meta in changed.items()):
        raise ValueError("Patch files differ from the new manifest.")
    if any(p not in old or p in new for p in removed):
        raise ValueError("Patch removal list is not a tracked old file.")
    if (set(changed) != {name for name, meta in new.items() if old.get(name) != meta}
            or set(removed) != set(old) - set(new)):
        raise ValueError("Patch is not a complete delta for this version.")
    for name, meta in changed.items():
        if (not isinstance(meta, dict) or not isinstance(meta.get("size"), int)
                or meta["size"] < 0 or len(str(meta.get("sha256", ""))) != 64):
            raise ValueError("Invalid patch file metadata: " + name)
    return changed, removed


def apply_patch(root, installed, manifest, patch_file):
    if manifest["channel"] != installed["channel"]:
        raise ValueError("Cannot mix Kanto and Decades.")
    if manifest.get("immutable", {}) != installed.get("immutable", {}):
        raise ValueError("Runtime/save configuration changed; a full ZIP is required.")
    with zipfile.ZipFile(patch_file) as archive:
        entries = archive.namelist()
        if len(entries) != len(set(entries)):
            raise ValueError("Duplicate patch entries.")
        patch = json.loads(archive.read("patch.json"))
        if (patch.get("schema") != 1 or patch.get("channel") != installed["channel"]
                or patch.get("from_revision") != installed["revision"]
                or patch.get("to_revision") != manifest["revision"]):
            raise ValueError("Patch does not match this installed version.")
        changed, removed = _verify_paths(installed["files"], manifest["files"], patch)
        if set(entries) != {"patch.json"} | {"files/" + name for name in changed}:
            raise ValueError("Patch contains unexpected files.")
        for name in changed:
            entry = archive.getinfo("files/" + name)
            meta = changed[name]
            if entry.file_size != meta["size"] or entry.file_size > MAX_PATCH_BYTES:
                raise ValueError("Patch file size mismatch: " + name)
            digest = hashlib.sha256()
            with archive.open(entry) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != meta["sha256"]:
                raise ValueError("Patch file checksum mismatch: " + name)
        # Immutable runtime and save profile must still match their baseline.
        for name, meta in installed.get("immutable", {}).items():
            critical = root / name
            if (not critical.is_file() or critical.is_symlink()
                    or sha256_file(critical) != meta["sha256"]):
                raise ValueError("Critical runtime/configuration was modified: " + name)
        # Only touch files owned by the exact installed revision. Protect modifications.
        for name in sorted(set(changed) | set(removed)):
            current = root / name
            previous = installed["files"].get(name)
            if previous:
                if not current.is_file() or current.is_symlink() or sha256_file(current) != previous["sha256"]:
                    raise ValueError("File was modified; update refused: " + name)
            elif current.exists():
                raise ValueError("Refusing to replace untracked file: " + name)
        backups = root / ".blue-android-update-backups"
        backup = backups / (installed["revision"][:12] + "-to-" + manifest["revision"][:12])
        if backup.exists():
            raise ValueError("Existing backup for this update; resolve it first: " + str(backup))
        backup.mkdir(parents=True)
        modified = []
        try:
            for name in sorted(set(changed) | set(removed)):
                destination = root / name
                if destination.exists():
                    saved = backup / name
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(destination, saved)
                modified.append(name)
            for name in sorted(changed):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                fd, temp_path = tempfile.mkstemp(prefix=".blue-update-", dir=target.parent)
                try:
                    with os.fdopen(fd, "wb") as output, archive.open("files/" + name) as source:
                        shutil.copyfileobj(source, output, length=1024 * 1024)
                    os.replace(temp_path, target)
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
            for name in removed:
                (root / name).unlink()
            marker = root / MARKER
            temp_marker = marker.with_name(marker.name + ".tmp")
            temp_marker.write_text(json.dumps({
                "schema": 1, "channel": manifest["channel"], "revision": manifest["revision"],
                "files": manifest["files"], "immutable": manifest.get("immutable", {})},
                sort_keys=True), encoding="utf8")
            os.replace(temp_marker, marker)
            (backup / "BACKUP-INFO.txt").write_text(
                "Previous revision: " + installed["revision"] + "\n"
                "New revision: " + manifest["revision"] + "\n"
                "Do not delete until the game and its saves are tested.\n", encoding="utf8")
        except BaseException:
            for name in reversed(modified):
                original = backup / name
                target = root / name
                if original.is_file():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(original, target)
                else:
                    target.unlink(missing_ok=True)
            raise
    return len(changed), len(removed), backup


def main(argv=None):
    parser = argparse.ArgumentParser(description="Update a CLOSED JoiPlay Blue installation using Termux Python.")
    parser.add_argument("--game-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--update", action="store_true", help="Download and apply a verified incremental update.")
    args = parser.parse_args(argv)
    root = args.game_dir.expanduser().resolve()
    info = read_installed(root)
    release, manifest = remote_update(info)
    if info["revision"] == manifest["revision"]:
        print("O jogo ja esta atualizado:", info["revision"])
        return 0
    print("Versao instalada:", info["revision"])
    print("Versao disponivel:", manifest["revision"])
    patch = manifest.get("patch") or {}
    full = asset_url(release, CHANNELS[info["channel"]][0])
    if (patch.get("from_revision") != info["revision"] or
            manifest.get("immutable", {}) != info.get("immutable", {}) or
            not asset_url(release, patch.get("asset", ""))):
        print("Nao existe patch direto entre essas revisoes.")
        print("Baixe o pacote completo, numa pasta NOVA:", full or release["html_url"])
        return 2
    print("Pacote incremental:", patch["asset"], "(" + str(patch.get("size", 0)) + " bytes)")
    if not args.update:
        print("Feche o JoiPlay e execute novamente com --update para instalar.")
        return 0
    path = root / ".blue-android-downloads" / patch["asset"]
    download(asset_url(release, patch["asset"]), path, patch["sha256"], patch["size"])
    changed, removed, backup = apply_patch(root, info, manifest, path)
    print("Atualizacao aplicada com sucesso:", changed, "arquivos novos/alterados,", removed, "removidos.")
    print("Backup:", backup)
    print("Se o JoiPlay estiver aberto, feche-o completamente antes de reabrir o jogo.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("ATUALIZACAO NAO CONCLUIDA:", error, file=sys.stderr)
        sys.exit(1)
