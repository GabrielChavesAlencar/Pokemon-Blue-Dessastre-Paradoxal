"""Build the installed-file inventory inside each Android full ZIP."""
import hashlib
import json
from pathlib import Path
from scripts.android.update_client import safe_path


def installed_manifest(channel, revision, files):
    if channel not in ("decades", "kanto"):
        raise ValueError("Unknown Android update channel.")
    assets = {}
    immutable = {}
    for name, source in sorted(files.items()):
        if isinstance(source, Path):
            digest = hashlib.sha256()
            size = 0
            with source.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    size += len(chunk)
                    digest.update(chunk)
            entry = {"sha256": digest.hexdigest(), "size": size}
            (assets if safe_path(name) else immutable)[name] = entry
        else:
            data = bytes(source)
            entry = {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
            (assets if safe_path(name) else immutable)[name] = entry
    return json.dumps({
        "schema": 1, "channel": channel, "revision": revision, "files": assets, "immutable": immutable,
    }, sort_keys=True, separators=(",", ":")).encode("utf8")


def verify_manifest(archive, base, channel, revision):
    info = json.loads(archive.read(base + "Data/blue-update.json"))
    if info.get("channel") != channel or info.get("revision") != revision or info.get("schema") != 1:
        raise ValueError("Android update channel/revision does not match the game ZIP.")
    if not isinstance(info.get("files"), dict):
        raise ValueError("Android inventory missing.")
    actual = {name[len(base):] for name in archive.namelist()
              if name.startswith(base) and safe_path(name[len(base):])}
    if actual != set(info["files"]):
        raise ValueError("Android installed inventory differs from full ZIP.")
    return info
