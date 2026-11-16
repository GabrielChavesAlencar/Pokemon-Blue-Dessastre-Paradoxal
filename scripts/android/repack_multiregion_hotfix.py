"""Repackage the audited combined Android release with the Kanto JoiPlay hotfix.

Never invent/rebuild regional maps from unavailable upstream downloads.
Only change source/cache of RegionStart, updater, and release metadata. The
existing ZIP is verified against its recorded original SHA and all file hashes.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.android.package import verify_archive, fingerprint, REGION_START_PLUGIN
from scripts.android.publish_updates import from_archive
from scripts.official_rules.prepare_restore import Marshal, RubyString, dump
from server.ruby_marshal import loads

PREFIX = "Pokemon-Blue-Android/"
BASE_REV = "125155eaf256fcc3e5bfa9880585e9d07ce22618"
REGION = "Plugins/ZZZZ Blue Story and Presentation/RegionStart.rb"
CACHE = "Data/PluginScripts.rxdata"
UPDATER = "ATUALIZAR-ANDROID.py"
README = "LEIA-ME-ANDROID.txt"
MOBILE_INFO = "Data/blue-mobile-build.txt"
MARKER = "Data/blue-update.json"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def replace_compiled_region(cache, source):
    plugins = Marshal(cache).read()
    matched = 0
    for plugin in plugins:
        if not isinstance(plugin, list) or len(plugin) != 3:
            raise ValueError("Unrecognized plugin cache structure.")
        for row in plugin[2]:
            if bytes(row[0]) != b"RegionStart.rb":
                continue
            old = zlib.decompress(row[1])
            if b"module BlueRegionStart" not in old:
                raise ValueError("Unexpected RegionStart.rb in compiled cache.")
            if matched:
                raise ValueError("Duplicate compiled RegionStart.rb.")
            updated = RubyString(zlib.compress(source))
            if hasattr(row[1], "ivars"):
                updated.ivars = row[1].ivars
            row[1] = updated
            matched += 1
    if matched != 1:
        raise ValueError("Missing compiled RegionStart.rb.")
    result = b"\x04\x08" + dump(plugins)
    matches = [
        zlib.decompress(row[1])
        for plugin in loads(result) for row in plugin[2]
        if row[0] == b"RegionStart.rb"
    ]
    if matches != [source]:
        raise ValueError("Failed to reserialize compiled RegionStart.rb.")
    return result


def regional_proof(source):
    kanto = json.loads(source.read(PREFIX + "Data/blue-kanto-install.json"))
    hoenn = json.loads(source.read(PREFIX + "Data/blue-hoenn-install.json"))
    km, hm = kanto["maps"], hoenn["maps"]
    if not (kanto["schema"] == 1 and kanto["source"] == "Essentials FRLG 21.1"
            and len(km) == 142 and len(set(km.values())) == 142
            and len(hm) == 199 and len(set(hm.values())) == 199):
        raise ValueError("Original ZIP lacks the real 142 Kanto/199 Hoenn maps.")
    start = "BLUE_KANTO_START_V1,KANTO,{},25,7".format(km["7"])
    ready = "BLUE_KANTO_READY_V1,142,{}".format(km["7"])
    if (source.read(PREFIX + "Data/blue-kanto-start.txt").decode().strip() != start
            or source.read(PREFIX + "Data/blue-kanto-ready.txt").decode().strip() != ready):
        raise ValueError("Original Kanto installation markers are inconsistent.")
    for map_id in list(km.values()) + list(hm.values()):
        name = PREFIX + "Data/Map{:03d}.rxdata".format(map_id)
        if source.getinfo(name).file_size == 0:
            raise ValueError("Regional map is empty: " + name)
    return len(km), len(hm)


def plugin_fingerprint(source, substitutions):
    checksum = hashlib.sha256()
    names = sorted(
        name[len(PREFIX):] for name in source.namelist()
        if name.startswith(PREFIX + "Plugins/") and
        Path(name).suffix.lower() in (".rb", ".txt")
    )
    for name in names:
        data = substitutions.get(name)
        if data is None:
            data = source.read(PREFIX + name)
        checksum.update(name.encode())
        checksum.update(data.replace(b"\r\n", b"\n"))
    return checksum.hexdigest()


def modified_files(source, revision):
    source_code = (ROOT / "scripts/battle_polish/RegionStart.rb").read_bytes()
    updater = (ROOT / "scripts/android/update_client.py").read_bytes()
    if (b"def self.kanto_compact_maps" not in source_code or
            b"!kanto_compact_maps(spawn).nil?" not in source_code or
            b"def verify_forward_revision" not in updater):
        raise ValueError("Kanto/Android-updater bug fixes missing from main.")
    before = source.read(PREFIX + REGION)
    if before == source_code:
        raise ValueError("Hotfix baseline already contains this code.")
    result = {
        REGION: source_code,
        CACHE: replace_compiled_region(source.read(PREFIX + CACHE), source_code),
        UPDATER: updater,
    }
    instructions = source.read(PREFIX + README)
    old_revision_line = ("Revision: " + BASE_REV + "\n").encode()
    if instructions.count(old_revision_line) != 1:
        raise ValueError("Original ZIP README revision does not match baseline.")
    result[README] = instructions.replace(
        old_revision_line, ("Revision: " + revision + "\n").encode()
    ) + (b"\nKanto Android: 142 mapas confirmados e RegionStart.rb corrigido "
         b"no cache do JoiPlay.\nAtualizador Android: protecao contra "
         b"downgrade e escolha correta da release.\n")

    boot = source.read(PREFIX + MOBILE_INFO)
    before_revision = ("Revision: " + BASE_REV + "\n").encode()
    if boot.count(before_revision) != 1:
        raise ValueError("Original mobile build metadata is inconsistent.")
    boot = boot.replace(before_revision, ("Revision: " + revision + "\n").encode())
    previous_fingerprint = re.search(rb"(?m)^Plugins-SHA256: [0-9a-f]{64}$", boot)
    if previous_fingerprint:
        new_fingerprint = plugin_fingerprint(source, result)
        boot = boot.replace(
            previous_fingerprint.group(),
            b"Plugins-SHA256: " + new_fingerprint.encode()
        )
    result[MOBILE_INFO] = boot
    return result


def regenerate_installed_manifest(original, changed, revision):
    data = copy.deepcopy(original)
    data["revision"] = revision
    for name, payload in changed.items():
        table = "files" if name in data["files"] else "immutable"
        if name not in data.get(table, {}):
            raise ValueError("Expected file not in original installed manifest: " + name)
        data[table][name] = {"sha256": digest(payload), "size": len(payload)}
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf8")


def rebuild(source_path, output_path, revision):
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("GitHub commit revision must be SHA-40.")
    if revision == BASE_REV:
        raise ValueError("New release must have a different revision.")
    original, folder = from_archive(source_path, "multiregion")
    if folder != PREFIX or original["revision"] != BASE_REV:
        raise ValueError("Refusing to repack an unknown original Android release.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source_path, "r") as source:
        proof = regional_proof(source)
        changed = modified_files(source, revision)
        changed[MARKER] = regenerate_installed_manifest(original, changed, revision)
        seen = set()
        with zipfile.ZipFile(output_path, "w", allowZip64=True) as dest:
            for info in source.infolist():
                relative = info.filename[len(PREFIX):]
                if relative in seen:
                    raise ValueError("Duplicate path in source ZIP.")
                seen.add(relative)
                item = copy.copy(info)
                payload = changed.get(relative)
                if payload is not None:
                    dest.writestr(item, payload)
                else:
                    with source.open(info, "r") as reader, dest.open(item, "w", force_zip64=True) as writer:
                        for block in iter(lambda: reader.read(1024 * 1024), b""):
                            writer.write(block)
    # Existing verified maps, events, music, and profiles were copied verbatim.
    # Verify all output SHA-256 entries plus the compiled plugin before release.
    from_archive(output_path, "multiregion")
    verify_archive(output_path, revision, channel="multiregion")
    with zipfile.ZipFile(output_path) as source:
        regional_proof(source)
        from scripts.android.package import compiled_region
        compiled_region(
            source.read(PREFIX + CACHE),
            "RegionStart.rb",
            source.read(PREFIX + REGION),
        )
    return {"revision": revision, "maps_kanto": proof[0], "maps_hoenn": proof[1],
            "sha256": digest_file(output_path), "bytes": output_path.stat().st_size}


def digest_file(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--revision", required=True)
    a = ap.parse_args()
    result = rebuild(a.source, a.output, a.revision)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
