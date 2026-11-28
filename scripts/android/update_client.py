"""Android JoiPlay updater companion (Termux/Python). Run with the game CLOSED.

No third-party packages. Never overwrite save files or the JoiPlay save profile.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

REPO = "GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal"
API = "https://api.github.com/repos/" + REPO
MARKER = "Data/blue-update.json"
# This hotfix mislabeled a 142-map historical ZIP as the 151-map revision.
# Preserve its manifest for migration, not as a candidate for installation.
WITHDRAWN_MULTIREGION_TAGS = frozenset({"android-multiregion-hotfix-31-e7200ef"})
CHANNELS = {
    "decades": ("Blue-Android-JoiPlay.zip", "Blue-Android-JoiPlay.update.json"),
    "kanto": ("Blue-Android-Kanto-Piloto.zip", "Blue-Android-Kanto-Piloto.update.json"),
    "multiregion": ("Blue-Android-Decades-Kanto-Hoenn.zip", "Blue-Android-Decades-Kanto-Hoenn.update.json"),
}
ALLOWED_ROOTS = {"Audio", "Graphics", "Fonts", "PBS", "Plugins", "Data"}
FORBIDDEN = {"mkxp.json", "Game.ini", MARKER}
MAX_PATCH_BYTES = 1024 * 1024 * 1024  # 1 GiB; larger changes require full installation.
MAX_FULL_BYTES = 2 * 1024 * 1024 * 1024  # GitHub release asset upper bound.
MAX_UNPACKED_BYTES = 12 * 1024 * 1024 * 1024



def safe_path(name):
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        return False
    path = PurePosixPath(name)
    if path.is_absolute() or any(p in (".", "..", "") for p in name.split("/")):
        return False
    # Kanto's map/event inventory changes whenever its source is updated.
    # It is game data (not the JoiPlay save profile) and must be patchable.
    if name in ("ATUALIZAR-ANDROID.py", "Kanto pilot.json", "LEIA-ME-ANDROID.txt",
                "LEIA-ME-ANDROID-KANTO.txt"):
        return True
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
    prefix = "kanto-android-" if channel == "kanto" else "android-multiregion-"
    # GitHub's global release list is NOT ordered by publication time across
    # all workflow types. On 15/11/2026 it returned multiregion-9 BEFORE
    # multiregion-15 and the previous client downgraded the installed game.
    # Examine every retrieved page and choose the newest *published* release.
    candidates = []
    # The archive can be pushed to page four or later by unrelated releases.
    # Continue until GitHub returns a short page; never silently accept a
    # partial history when the scan limit is reached.
    for page in range(1, 101):
        url = API + "/releases?per_page=100" + ("&page=" + str(page) if page > 1 else "")
        entries = get_json(url)
        if not isinstance(entries, list):
            break
        for release in entries:
            if (str(release.get("tag_name", "")).startswith(prefix) and
                    not (channel == "multiregion" and release.get("tag_name") in WITHDRAWN_MULTIREGION_TAGS) and
                    not release.get("draft", False) and
                    asset_url(release, CHANNELS[channel][0]) and
                    asset_url(release, CHANNELS[channel][1])):
                candidates.append(release)
        if len(entries) < 100:
            break
    else:
        raise ValueError("GitHub release history exceeds the safe scan limit; update refused.")
    if not candidates:
        raise ValueError("No verified Android release found for channel: " + channel)
    # published_at is authoritative: tag numbers and GitHub result order are not.
    return max(candidates, key=lambda r: (r.get("published_at") or
                                          r.get("created_at") or "",
                                          str(r.get("tag_name", ""))))


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


def verify_forward_revision(installed_revision, candidate_revision):
    """Fail closed if the server offers an older or divergent build.

    A newer publication timestamp is not proof of newer source code.
    Use GitHub's commit ancestry comparison before any patch/full download.
    """
    if installed_revision == candidate_revision:
        return
    for revision in (installed_revision, candidate_revision):
        if (not isinstance(revision, str) or len(revision) != 40 or
                any(char not in "0123456789abcdef" for char in revision.lower())):
            raise ValueError("Invalid Android release revision; update refused.")
    comparison = get_json(API + "/compare/" + installed_revision + "..." +
                          candidate_revision)
    status = comparison.get("status") if isinstance(comparison, dict) else None
    if status != "ahead":
        raise ValueError(
            "Atualizacao BLOQUEADA: a versao oferecida nao e posterior "
            "a instalada (GitHub: {}). Nenhum arquivo foi alterado.".format(
                status or "inconclusivo"))


def download(url, destination, expected_sha, expected_size, max_bytes=MAX_PATCH_BYTES):
    if not isinstance(expected_sha, str) or len(expected_sha) != 64:
        raise ValueError("Download SHA-256 is missing.")
    if not isinstance(expected_size, int) or not 0 < expected_size <= max_bytes:
        raise ValueError("Download exceeds the allowed size.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_name(destination.name + ".part")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Pokemon-Blue-Android-Updater"})
        with urllib.request.urlopen(request, timeout=60) as response, temp.open("wb") as output:
            total = 0
            next_progress = 10
            while True:
                data = response.read(1024 * 1024)
                if not data:
                    break
                total += len(data)
                if total > expected_size:
                    raise ValueError("Patch download exceeds its stated size.")
                output.write(data)
                if total * 100 >= expected_size * next_progress:
                    print("Baixando atualizacao: {}%".format(min(100, total * 100 // expected_size)), flush=True)
                    next_progress = (total * 100 // expected_size // 10 + 1) * 10
        if total != expected_size or sha256_file(temp) != expected_sha:
            raise ValueError("Patch checksum/size mismatch; refusing installation.")
        os.replace(temp, destination)
    finally:
        temp.unlink(missing_ok=True)


def _patchable_immutables(old, new):
    """Only the updater itself may migrate from legacy immutable to mutable.

    Game.exe, the JoiPlay save profile and all other root files stay protected.
    """
    earlier = dict(old)
    later = dict(new)
    earlier.pop("ATUALIZAR-ANDROID.py", None)
    later.pop("ATUALIZAR-ANDROID.py", None)
    return earlier == later


def _old_patch_files(info, updated_files):
    """Expose the old updater as a tracked item only during its migration."""
    old = dict(info["files"])
    updater = info.get("immutable", {}).get("ATUALIZAR-ANDROID.py")
    if ("ATUALIZAR-ANDROID.py" in updated_files and updater and
            "ATUALIZAR-ANDROID.py" not in old):
        old["ATUALIZAR-ANDROID.py"] = updater
    return old


def _preserve_shared_sinnoh(old, new):
    # A shared save can be standing on a Sinnoh map when JoiPlay is closed.
    marker = "Data/blue-sinnoh-shared.txt"
    if marker not in old:
        return
    required = {marker, "Data/blue-sinnoh-shared.json"}
    required.update(f"Data/Map{mid:03d}.rxdata" for mid in range(442, 600) if f"Data/Map{mid:03d}.rxdata" in old)
    required.update(name for name in old if
                    name.startswith("Plugins/ZZZZZ Blue Sinnoh Shared/") or
                    (name.startswith(("Graphics/","Audio/")) and
                     name.rsplit("/",1)[-1].startswith(("SNQA_","SNSH_"))) or
                    (name.startswith("PBS/") and "_sinnoh" in name))
    if not required <= set(new):
        raise ValueError("A atualização removeria Sinnoh de um save compartilhado.")


def _verify_paths(old, new, patch):
    _preserve_shared_sinnoh(old, new)
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


def _local_target(root, name):
    """Refuse symlink parents: never write outside the selected JoiPlay folder."""
    if (not isinstance(name, str) or not name or "\x00" in name or
            "\\" in name or name.startswith("/") or
            any(part in ("", ".", "..") for part in name.split("/"))):
        raise ValueError("Unsafe Android update path: " + str(name))
    target = root.joinpath(*PurePosixPath(name).parts)
    cursor = target
    while cursor != root:
        if cursor.is_symlink():
            raise ValueError("A symbolic link blocks the update: " + name)
        cursor = cursor.parent
    return target


def _replace_from_zip(archive, member, destination, expected):
    """One-file atomic replacement; no backup and no half-written target."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".blue-update-", dir=destination.parent)
    try:
        digest = hashlib.sha256()
        size = 0
        with os.fdopen(fd, "wb") as output, archive.open(member) as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                size += len(chunk)
                digest.update(chunk)
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        if size != expected["size"] or digest.hexdigest() != expected["sha256"]:
            raise ValueError("Downloaded file failed verification: " + member)
        os.replace(name, destination)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _write_installed_revision(root, manifest, mode="patch"):
    """Commit the new revision and actual installation timestamp LAST."""
    now_utc=datetime.now(timezone.utc)
    now_local=now_utc.astimezone()
    marker = _local_target(root, MARKER)
    marker.parent.mkdir(parents=True, exist_ok=True)
    fd, filename = tempfile.mkstemp(prefix=".blue-update-manifest-", dir=marker.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf8") as output:
            json.dump({
                "schema": 1, "channel": manifest["channel"],
                "revision": manifest["revision"], "files": manifest["files"],
                "immutable": manifest.get("immutable", {}),
                "applied_at_utc": now_utc.isoformat(timespec="seconds").replace("+00:00", "Z"),
                "applied_at_local": now_local.isoformat(timespec="seconds"),
                "update_mode": mode
            }, output, sort_keys=True)
            output.flush()
            os.fsync(output.fileno())
        os.replace(filename, marker)
    finally:
        if os.path.exists(filename):
            os.unlink(filename)


# The single-file launcher shared with Android players on 17 Nov 2026
# intentionally downloads this client from GitHub instead of embedding it.
# Players manually replaced ATUALIZAR-ANDROID.py with that known launcher;
# the old installed manifest still expects the original packaged updater.
# It is safe to migrate ONLY the exact known launcher after the signed
# release's patch metadata and every new file digest were validated.
KNOWN_ANDROID_LAUNCHERS = frozenset({
    "0dcf2bc93d7b92e66a6b9366569b2f831d8f5941ccf5cde72b9f9022387468a1",
})


def _trusted_local_updater(path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 1024 * 1024:
        return False
    return sha256_file(path) in KNOWN_ANDROID_LAUNCHERS


def _check_local_changes(root, old, new, changed, removed):
    """Allow OLD or ALREADY-UPDATED hashes so interrupted patches can resume."""
    actions = []
    for name in sorted(changed):
        target = _local_target(root, name)
        expected = new[name]
        if target.is_file() and sha256_file(target) == expected["sha256"]:
            continue
        prior = old.get(name)
        if prior is None:
            if target.exists():
                raise ValueError("Refusing to replace untracked file: " + name)
        elif not target.is_file():
            raise ValueError("File was modified; update refused: " + name)
        elif sha256_file(target) != prior["sha256"]:
            if name != "ATUALIZAR-ANDROID.py" or not _trusted_local_updater(target):
                raise ValueError("File was modified; update refused: " + name)
            print("Reconhecido iniciador Android oficial instalado manualmente; "
                  "atualizando somente o proprio atualizador.", flush=True)
        actions.append(name)
    for name in removed:
        target = _local_target(root, name)
        if not target.exists():
            continue  # An interrupted earlier attempt already removed it.
        prior = old[name]
        if not target.is_file() or sha256_file(target) != prior["sha256"]:
            raise ValueError("File was modified; update refused: " + name)
    return actions


def apply_patch(root, installed, manifest, patch_file):
    """Install only the changed files. No backup and safely resumable."""
    if manifest["channel"] != installed["channel"]:
        raise ValueError("Cannot mix Kanto and Decades.")
    if not _patchable_immutables(installed.get("immutable", {}), manifest.get("immutable", {})):
        raise ValueError("Runtime/save configuration changed; a full ZIP is required.")
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Invalid installed game directory.")
    with zipfile.ZipFile(patch_file) as archive:
        entries = archive.namelist()
        if len(entries) != len(set(entries)):
            raise ValueError("Duplicate patch entries.")
        patch = json.loads(archive.read("patch.json"))
        if (patch.get("schema") != 1 or patch.get("channel") != installed["channel"]
                or patch.get("from_revision") != installed["revision"]
                or patch.get("to_revision") != manifest["revision"]):
            raise ValueError("Patch does not match this installed version.")
        old_files = _old_patch_files(installed, manifest["files"])
        changed, removed = _verify_paths(old_files, manifest["files"], patch)
        if set(entries) != {"patch.json"} | {"files/" + name for name in changed}:
            raise ValueError("Patch contains unexpected files.")
        for name in changed:
            entry = archive.getinfo("files/" + name)
            meta = changed[name]
            if entry.is_dir() or entry.flag_bits & 1:
                raise ValueError("Unexpected ZIP member: " + name)
            if entry.file_size != meta["size"] or entry.file_size > MAX_PATCH_BYTES:
                raise ValueError("Patch file size mismatch: " + name)
            digest = hashlib.sha256()
            with archive.open(entry) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != meta["sha256"]:
                raise ValueError("Patch file checksum mismatch: " + name)
        for name, meta in installed.get("immutable", {}).items():
            if name == "ATUALIZAR-ANDROID.py":
                continue  # Verified as a changed/unchanged file below.
            critical = _local_target(root, name)
            if (not critical.is_file() or
                    sha256_file(critical) != meta["sha256"]):
                raise ValueError("Critical runtime/configuration was modified: " + name)
        # Validate every local target before the first write. Existing NEW
        # files come from an interrupted update and need not be written again.
        todo = _check_local_changes(root, old_files,
                                    manifest["files"], changed, removed)
        for index, name in enumerate(todo, 1):
            _replace_from_zip(archive, "files/" + name,
                              _local_target(root, name), changed[name])
            print("Atualizando arquivos: {}/{}".format(index, len(todo)), flush=True)
        for name in removed:
            _local_target(root, name).unlink(missing_ok=True)
        _write_installed_revision(root, manifest)
    return len(todo), len(removed), None  # No backup directory is ever created.


def _save_file(relative):
    """Detect saves that must never be modified by any update mode.

    In-place updates preserve all save files and untracked user files.
    Saves held outside the game by JoiPlay are untouched as well.
    """
    parts = relative.parts
    if not parts or any(p.startswith(".blue-") for p in parts):
        return False
    name = parts[-1].lower()
    if any(p.lower() in ("save", "saves", "savedata") for p in parts[:-1]):
        return name.endswith((".rxdata", ".bak", ".sav"))
    if not name.endswith((".rxdata", ".bak")):
        return False
    stem = name.removesuffix(".bak").removesuffix(".rxdata")
    return (stem == "game" or
            (stem.startswith("file ") and stem[5:] in "abcdefgh") or
            (stem.startswith("auto ") and stem[5:] in "123"))


def _zip_members(archive, channel, manifest):
    """Check the entire full package before extracting anything."""
    prefix = ("Pokemon-Blue-Kanto-Android/" if channel == "kanto"
              else "Pokemon-Blue-Android/")
    tracked = manifest["files"]
    immutable = manifest.get("immutable", {})
    if not isinstance(tracked, dict) or not isinstance(immutable, dict):
        raise ValueError("Invalid full ZIP manifest.")
    expected = set(tracked) | set(immutable) | {MARKER}
    if not {"Game.exe", "ATUALIZAR-ANDROID.py"} <= expected:
        raise ValueError("Full ZIP is missing the game or its updater.")
    members = {}
    total = 0
    for entry in archive.infolist():
        name = entry.filename
        if (not name.startswith(prefix) or "\\" in name or "\x00" in name
                or entry.flag_bits & 1):
            raise ValueError("Unsafe entry in full ZIP.")
        rel = name[len(prefix):]
        if entry.is_dir():
            if rel and (rel.endswith("/") and
                        any(p in ("", ".", "..") for p in rel[:-1].split("/"))):
                raise ValueError("Invalid directory path in full ZIP.")
            continue
        if (not rel or rel.startswith("/") or
                any(p in ("", ".", "..") for p in rel.split("/"))):
            raise ValueError("Invalid file path in full ZIP.")
        mode = entry.external_attr >> 16
        if stat.S_IFMT(mode) not in (0, stat.S_IFREG):
            raise ValueError("Links and special files are forbidden in full ZIP.")
        if rel in members or rel not in expected:
            raise ValueError("Unexpected or duplicate full ZIP entry: " + rel)
        total += entry.file_size
        if total > MAX_UNPACKED_BYTES or len(members) >= 100000:
            raise ValueError("Full ZIP exceeds safe extraction limits.")
        members[rel] = entry
    if set(members) != expected:
        raise ValueError("Full ZIP file inventory does not match its manifest.")
    installed = json.loads(archive.read(members[MARKER]))
    if (installed.get("schema") != 1 or
            installed.get("channel") != manifest["channel"] or
            installed.get("revision") != manifest["revision"] or
            installed.get("files") != tracked or
            installed.get("immutable", {}) != immutable):
        raise ValueError("Full ZIP contains the wrong installed version.")
    return members


def apply_full_archive(root, installed, manifest, archive_path):
    """Manual full-ZIP repair, modifying only differing files in place.

    No old-installation copy, sibling backup, staged duplicate of the whole
    game, or save migration. All unrelated files and saves stay where they are.
    """
    if installed["channel"] != manifest["channel"]:
        raise ValueError("Cannot change Android update channels.")
    _preserve_shared_sinnoh(installed["files"], manifest["files"])
    if not root.is_dir() or root.is_symlink() or root.parent == root:
        raise ValueError("Invalid installed game directory.")
    with zipfile.ZipFile(archive_path) as archive:
        members = _zip_members(archive, installed["channel"], manifest)
        old = {**installed.get("immutable", {}), **installed["files"]}
        new = {**manifest.get("immutable", {}), **manifest["files"]}
        changes = {name: meta for name, meta in new.items() if old.get(name) != meta}
        removed = sorted(set(old) - set(new))
        if any(_save_file(PurePosixPath(name)) for name in set(changes) | set(removed)):
            raise ValueError("Refusing to change local save files.")
        # Prevalidate the current installation before touching anything.
        todo = _check_local_changes(root, old, new, changes, removed)
        for index, name in enumerate(todo, 1):
            _replace_from_zip(archive, members[name], _local_target(root, name),
                              changes[name])
            if index % max(1, len(todo) // 10) == 0 or index == len(todo):
                print("Atualizando arquivos: {}%".format(index * 100 // len(todo)), flush=True)
        for name in removed:
            _local_target(root, name).unlink(missing_ok=True)
        _write_installed_revision(root, manifest, mode="full-manual")
    return None, len(todo)  # Compatibility: no backup; number of files updated.


def install_full_from_release(root, installed, release, manifest):
    """EXPLICIT --full only: downloads large ZIP but never recreates the folder."""
    asset_name = CHANNELS[installed["channel"]][0]
    meta = manifest.get("full")
    url = asset_url(release, asset_name)
    if (not isinstance(meta, dict) or meta.get("asset") != asset_name
            or not url):
        raise ValueError("No verified full Android ZIP was published.")
    cache = root.parent / (".blue-android-downloads-" + root.name)
    archive_path = cache / asset_name
    download(url, archive_path, meta.get("sha256"), meta.get("size"),
             max_bytes=MAX_FULL_BYTES)
    try:
        return apply_full_archive(root, installed, manifest, archive_path)
    finally:
        archive_path.unlink(missing_ok=True)
        if cache.is_dir() and not any(cache.iterdir()):
            cache.rmdir()


def compatible_patch(release, installed, manifest):
    """Choose a verified release delta for THIS installed revision."""
    if not _patchable_immutables(installed.get("immutable", {}),
                                 manifest.get("immutable", {})):
        return None
    candidates = manifest.get("patches", [])
    if not isinstance(candidates, list):
        raise ValueError("Invalid release patch list.")
    legacy = manifest.get("patch")
    if isinstance(legacy, dict):
        candidates = [legacy, *candidates]
    matching = []
    for item in candidates:
        if (isinstance(item, dict) and
                item.get("from_revision") == installed["revision"] and
                asset_url(release, item.get("asset", "")) and
                isinstance(item.get("size"), int) and item["size"] > 0 and
                isinstance(item.get("sha256"), str) and
                len(item["sha256"]) == 64):
            matching.append(item)
    return min(matching, key=lambda row: row["size"]) if matching else None


def cerulean_integrity(root, installed, manifest):
    """Audit the actual map, runtime and compiled cache, not just the marker."""
    if installed["channel"] != "multiregion" or manifest["channel"] != "multiregion":
        raise ValueError("Diagnostico Cerulean exige o canal multirregional.")
    if installed["revision"] != manifest["revision"]:
        raise ValueError("Atualize para a revisao publicada antes do diagnostico.")
    registry_name = "Data/blue-kanto-install.json"
    registry = _local_target(root, registry_name)
    tracked = manifest["files"]
    names = [registry_name, "Data/PluginScripts.rxdata", "Data/Scripts.rxdata",
             "Data/blue-mobile-build.txt", "Data/blue-mobile.txt",
             "Plugins/ZZZZZ Blue Kanto Pilot/KantoPilot.rb",
             "Plugins/ZZZZ Blue Story and Presentation/Regions.rb"]
    registry_meta = tracked.get(registry_name)
    if (registry_meta and registry.is_file() and
            sha256_file(registry) == registry_meta["sha256"]):
        mapping = json.loads(registry.read_text(encoding="utf8"))["maps"]
        for source in ("39", "43", "44", "45", "46", "47", "48"):
            mid = mapping.get(source)
            if type(mid) is not int or not 0 < mid < 1000:
                raise ValueError("MapID de Cerulean invalido: " + source)
            names.append(f"Data/Map{mid:03d}.rxdata")
    else:
        print("Registro de mapas divergente: nao sera usado para escolher MapIDs.")
    mismatches = []
    print("Pasta auditada:", root)
    print("Revisao declarada:", installed["revision"])
    for name in names:
        expected = tracked.get(name) or manifest.get("immutable", {}).get(name)
        if not expected:
            print("SEM REFERENCIA:", name)
            continue
        target = _local_target(root, name)
        good = (target.is_file() and target.stat().st_size == expected["size"] and
                sha256_file(target) == expected["sha256"])
        print("OK:" if good else "DIVERGENTE:", name, flush=True)
        if not good:
            mismatches.append(name)
    return mismatches


def cerulean_logs(root):
    for name in ("Data/blue-mobile-build.txt", "Data/blue-android-runtime.txt",
                 "Data/blue-android-event-error.txt", "Data/blue-android-cerulean-runtime.txt", "errorlog.txt"):
        path = _local_target(root, name)
        print("\n--- " + name + " ---")
        if not path.is_file():
            print("Nao encontrado.")
            continue
        with path.open("rb") as stream:
            stream.seek(max(0, path.stat().st_size - 24000))
            content = stream.read().decode("utf-8", errors="replace")
        print("\n".join(content.splitlines()[-65:]))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Fast incremental updates for a CLOSED JoiPlay installation, without backups.")
    parser.add_argument("--game-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--update", action="store_true",
                        help="Download/apply ONLY changed files from a compatible delta.")
    parser.add_argument("--full", action="store_true",
                        help="Explicit fallback: download full ZIP but replace only changed files, no backup.")
    parser.add_argument("--diagnose-cerulean", action="store_true",
                        help="Read-only audit of Cerulean map files, compiled scripts and local error logs.")
    parser.add_argument("--source", action="store_true",
                        help="Use a receita Kanto fixada em vez de um ZIP do jogo.")
    parser.add_argument("--source-stage", choices=("k05","k06"),
                        help="Escolher a etapa de uma receita oficial já obtida.")
    parser.add_argument("--source-work-dir", type=Path,
                        help="Pasta separada para compilar com o JoiPlay (somente com --source).")
    parser.add_argument("--source-ci",action="store_true",help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if ((args.source and (args.full or args.diagnose_cerulean)) or
        ((args.source_work_dir or args.source_stage or args.source_ci) and not args.source)):
        parser.error("--source não pode ser combinado com ZIP completo ou diagnóstico")
    root = args.game_dir.expanduser().resolve()
    if (root / "Data/blue-sinnoh-shared-qa.txt").is_file():
        raise ValueError("A cópia de QA de Sinnoh não recebe atualizações do canal público.")
    info = read_installed(root)
    if args.source:
        if info["channel"] != "multiregion":
            raise ValueError("A atualização pela fonte é somente para o canal multirregional.")
        stamp=info.get("source_update") or {}
        stage=args.source_stage or ("k06" if stamp.get("stage")=="K06_APPROACH" else "k05")
        filename={"k05":"source_update.py","k06":"k06_source_candidate.py"}[stage]
        recipe = Path(__file__).resolve().with_name(filename)
        if not recipe.is_file():
            recipe = Path.home()/".cache"/"pokemon-blue-android"/stage/"scripts/android"/filename
        if not recipe.is_file():
            raise ValueError(f"A receita Kanto {stage.upper()} não está instalada. Use a revisão oficial publicada.")
        command = [sys.executable,str(recipe),"--game-dir",str(root),"--source-workflow"]
        if args.source_ci:
            if stage!="k06" or os.getenv("GITHUB_ACTIONS")!="true":
                raise ValueError("O teste da receita só pode rodar no ambiente de CI.")
            command.append("--ci")
        if args.source_work_dir:
            command.extend(("--work-dir",str(args.source_work_dir.resolve())))
        if args.update:
            command.append("--update")
        return subprocess.run(command,check=False).returncode
    if (root/".blue-k05-recovery.json").exists():
        print("Há uma atualização interrompida. Use --source --update; nenhum ZIP será baixado.")
        return 2 if args.update else 0
    if info.get("source_update") is not None:
        print("A instalação foi construída pela fonte. Use --source com uma receita compatível; nenhum ZIP será baixado.")
        return 2 if args.update else 0
    release, manifest = remote_update(info)
    verify_forward_revision(info["revision"], manifest["revision"])
    if args.diagnose_cerulean:
        try:
            mismatches = cerulean_integrity(root, info, manifest)
            print("Arquivos divergentes:", len(mismatches))
            return 3 if mismatches else 0
        finally:
            cerulean_logs(root)
    if info["revision"] == manifest["revision"] and not args.full:
        if info["channel"] == "multiregion":
            mismatches = cerulean_integrity(root, info, manifest)
            if mismatches:
                print("Revisao igual, mas arquivos divergentes. Execute --diagnose-cerulean.")
                return 3
        print("O jogo ja esta atualizado:", info["revision"])
        return 0
    print("Versao instalada:", info["revision"])
    print("Versao disponivel:", manifest["revision"])
    patch = None if args.full else compatible_patch(release, info, manifest)
    if patch:
        print("Atualizacao incremental:", patch["asset"],
              "(" + str(patch["size"]) + " bytes); sem backup.")
        if not args.update:
            print("Feche o JoiPlay e execute com --update para instalar.")
            return 0
        path = root / ".blue-android-downloads" / patch["asset"]
        try:
            download(asset_url(release, patch["asset"]), path,
                     patch["sha256"], patch["size"])
            changed, removed, _unused = apply_patch(root, info, manifest, path)
        finally:
            path.unlink(missing_ok=True)
            if path.parent.is_dir() and not any(path.parent.iterdir()):
                path.parent.rmdir()
        print("Atualizacao incremental concluida:", changed, "arquivo(s) modificados,",
              removed, "removido(s). Nenhum backup criado.")
        return 0
    if not args.full:
        print("Sem patch incremental para esta revisao. Nenhum ZIP completo sera baixado.")
        print("Aguarde uma release com patch para sua versao ou use --full --update")
        print("para baixar o ZIP completo MANUALMENTE (sem backup, apenas arquivos alterados).")
        return 0 if not args.update else 2
    full = manifest.get("full") or {}
    print("Modo manual --full: download integral de", full.get("asset", "indisponivel"))
    print("Somente os arquivos alterados serao substituidos; sem backup.")
    if not args.update:
        print("Execute com --full --update para confirmar.")
        return 0
    _backup, count = install_full_from_release(root, info, release, manifest)
    print("Atualizacao concluida:", count, "arquivo(s) modificados. Saves preservados.")
    print("Reabra o mesmo Game.exe no JoiPlay.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("ATUALIZACAO NAO CONCLUIDA:", error, file=sys.stderr)
        sys.exit(1)
