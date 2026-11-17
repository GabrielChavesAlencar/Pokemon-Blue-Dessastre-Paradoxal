"""Repackage the audited combined Android release with the Kanto JoiPlay hotfix.

Never invent/rebuild regional maps from unavailable upstream downloads.
Only change the audited Blue-owned regional plugin sources/caches, updater,
and release metadata. Maps and saves remain untouched. The existing ZIP is
verified against its recorded original SHA and all file hashes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.android.package import verify_archive, fingerprint, REGION_START_PLUGIN
from scripts.android.publish_updates import from_archive
from server.ruby_marshal import loads

PREFIX = "Pokemon-Blue-Android/"
BASE_REV = "125155eaf256fcc3e5bfa9880585e9d07ce22618"
REGION = "Plugins/ZZZZ Blue Story and Presentation/RegionStart.rb"
KANTO = "Plugins/ZZZZZ Blue Kanto Pilot/KantoPilot.rb"
MOBILE = "Plugins/ZZZZ Blue Battle Lab/Mobile.rb"
KANTO_MANIFEST = "Data/blue-kanto-install.json"
CACHE = "Data/PluginScripts.rxdata"
UPDATER = "ATUALIZAR-ANDROID.py"
README = "LEIA-ME-ANDROID.txt"
MOBILE_INFO = "Data/blue-mobile-build.txt"
MARKER = "Data/blue-update.json"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def replace_compiled_region(cache, source):
    """Use the actual Ruby Marshal serializer for opaque plugin metadata.

    The production PluginScripts.rxdata contains Hash objects that the
    project's deliberately limited Python Marshal writer cannot serialize.
    Ruby is available on the GitHub Linux runner and preserves all Marshal
    types, object references, hash defaults and string encoding flags.
    """
    ruby = r'''
require "zlib"
data = Marshal.load(STDIN.binmode.read)
wanted = File.binread(ARGV.fetch(0))
matched = 0
data.each do |plugin|
  plugin.fetch(2).each do |entry|
    next unless entry[0].to_s == "RegionStart.rb"
    previous = Zlib::Inflate.inflate(entry[1])
    abort "Unknown compiled RegionStart.rb" unless previous.include?("module BlueRegionStart")
    entry[1] = Zlib::Deflate.deflate(wanted)
    matched += 1
  end
end
abort "Expected exactly one compiled RegionStart.rb, got #{matched}" unless matched == 1
STDOUT.binmode.write(Marshal.dump(data))
'''
    result = subprocess.run(
        ["ruby", "-e", ruby, str(ROOT / "scripts/battle_polish/RegionStart.rb")],
        input=cache, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False, timeout=120,
    )
    if result.returncode:
        raise ValueError("Ruby could not patch the real plugin cache: " +
                         result.stderr.decode("utf8", "replace")[:1200])
    matches = [
        zlib.decompress(row[1])
        for plugin in loads(result.stdout) for row in plugin[2]
        if row[0] == b"RegionStart.rb"
    ]
    if matches != [source]:
        raise ValueError("Compiled Kanto fix absent after Ruby Marshal rewrite.")
    return result.stdout



def replace_compiled_kanto(cache, source):
    """Replace only the KantoPilot entry inside the actual Ruby Marshal cache."""
    ruby = r'''
require "zlib"
data = Marshal.load(STDIN.binmode.read)
wanted = File.binread(ARGV.fetch(0))
matched = 0
data.each do |plugin|
  plugin.fetch(2).each do |entry|
    next unless entry[0].to_s == "KantoPilot.rb"
    previous = Zlib::Inflate.inflate(entry[1])
    abort "Unrecognized KantoPilot plugin" unless previous.include?("module BlueKantoPilot")
    entry[1] = Zlib::Deflate.deflate(wanted)
    matched += 1
  end
end
abort "Expected exactly one KantoPilot.rb, got #{matched}" unless matched == 1
STDOUT.binmode.write(Marshal.dump(data))
'''
    patched = subprocess.run(
        ["ruby", "-e", ruby, str(ROOT / "scripts/regions/KantoPilot.rb")],
        input=cache, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False, timeout=120,
    )
    if patched.returncode:
        raise ValueError("Cannot update compiled KantoPilot: " +
                         patched.stderr.decode("utf8", "replace")[:1200])
    matches = [
        zlib.decompress(row[1])
        for plugin in loads(patched.stdout) for row in plugin[2]
        if row[0] == b"KantoPilot.rb"
    ]
    if matches != [source]:
        raise ValueError("Compiled Kanto fossil fix missing after Ruby Marshal rewrite.")
    return patched.stdout


def replace_compiled_mobile(cache, source):
    """Replace only the Mobile entry inside the actual Ruby Marshal cache."""
    ruby = r'''
require "zlib"
data = Marshal.load(STDIN.binmode.read)
wanted = File.binread(ARGV.fetch(0))
matched = 0
data.each do |plugin|
  plugin.fetch(2).each do |entry|
    next unless entry[0].to_s == "Mobile.rb"
    previous = Zlib::Inflate.inflate(entry[1])
    abort "Unrecognized BlueMobile plugin" unless previous.include?("module BlueMobile")
    entry[1] = Zlib::Deflate.deflate(wanted)
    matched += 1
  end
end
abort "Expected exactly one Mobile.rb, got #{matched}" unless matched == 1
STDOUT.binmode.write(Marshal.dump(data))
'''
    patched = subprocess.run(
        ["ruby", "-e", ruby, str(ROOT / "scripts/battle_lab/Mobile.rb")],
        input=cache, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False, timeout=120,
    )
    if patched.returncode:
        raise ValueError("Cannot update compiled Mobile: " +
                         patched.stderr.decode("utf8", "replace")[:1200])
    matches = [
        zlib.decompress(row[1])
        for plugin in loads(patched.stdout) for row in plugin[2]
        if row[0] == b"Mobile.rb"
    ]
    if matches != [source]:
        raise ValueError("Compiled Android version UI missing after Ruby Marshal rewrite.")
    return patched.stdout


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
    kanto = (ROOT / "scripts/regions/KantoPilot.rb").read_bytes()
    mobile = (ROOT / "scripts/battle_lab/Mobile.rb").read_bytes()
    if b"def self.show_version" not in mobile:
        raise ValueError("Game version display missing from Mobile.rb")
    if (b"def self.choose_moon_fossil" not in kanto or
            b"def self.revive_cinnabar_fossil" not in kanto):
        raise ValueError("Verified Kanto fossil fix missing from main.")
    before = source.read(PREFIX + REGION)
    if before == source_code and source.read(PREFIX + KANTO) == kanto:
        raise ValueError("Baseline already contains both regional fixes.")
    patched_region = replace_compiled_region(source.read(PREFIX + CACHE), source_code)
    patched_both = replace_compiled_kanto(patched_region, kanto)
    patched_all = replace_compiled_mobile(patched_both, mobile)
    proof = json.loads(source.read(PREFIX + KANTO_MANIFEST))
    hashes = proof.get("installed_sha256")
    if not isinstance(hashes, dict):
        raise ValueError("Original Kanto install proof has no checksum table.")
    # The importer records map/PBS hashes, not the separately installed plugin.
    # It is normal for legacy archives to lack KANTO in this checksum table.
    windows_key = KANTO.replace("/", "\\")
    recorded = hashes.get(windows_key, hashes.get(KANTO))
    if recorded is not None and not re.fullmatch(r"[0-9a-f]{64}", str(recorded)):
        raise ValueError("Invalid historical Kanto plugin checksum.")
    # The source manifest was written by Python on Windows; its keys use
    # backslashes, while ZIP members use forward slashes. Preserve BOTH.
    # Old combined releases may have compiled the game after sync_runtime
    # updated KantoPilot, leaving an older installer checksum in this proof.
    # Validate the actual distributed runtime against its compiled cache;
    # the outer update manifest separately pins every archived file hash.
    from scripts.android.package import compiled_region
    compiled_region(source.read(PREFIX + CACHE), "KantoPilot.rb",
                    source.read(PREFIX + KANTO))
    hashes[KANTO] = digest(kanto)
    if windows_key in hashes:
        hashes[windows_key] = digest(kanto)
    result = {
        REGION: source_code,
        KANTO: kanto,
        MOBILE: mobile,
        KANTO_MANIFEST: (json.dumps(proof, indent=2) + "\n").encode("utf-8"),
        CACHE: patched_all,
        UPDATER: updater,
    }
    instructions = source.read(PREFIX + README)
    old_revision_line = ("Revision: " + BASE_REV + "\n").encode()
    if instructions.count(old_revision_line) != 1:
        raise ValueError("Original ZIP README revision does not match baseline.")
    result[README] = instructions.replace(
        old_revision_line, ("Revision: " + revision + "\n").encode()
    ) + (b"\nKanto Android: 142 mapas confirmados, RegionStart.rb corrigido "
         b"no cache do JoiPlay. Fosseis: escolha exclusiva no Mt. Moon "
         b"apos derrotar Miguel, inclusive em saves antigos; restauracao no "
         b"laboratorio de Cinnabar pelo menu local.\nAtualizador Android: "
         b"protecao contra downgrade e escolha correta da release.\n")

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
    # The timestamp describes this package build, NOT an imagined time when
    # the player installed it. The updater records the latter separately.
    build_utc = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    if re.search(rb"(?m)^Build-UTC: [^\n]+$", boot):
        boot = re.sub(rb"(?m)^Build-UTC: [^\n]+$", b"Build-UTC: " + build_utc.encode(), boot)
    else:
        boot += b"Build-UTC: " + build_utc.encode() + b"\n"
    result[MOBILE_INFO] = boot
    return result


def regenerate_installed_manifest(original, changed, revision):
    data = copy.deepcopy(original)
    data["revision"] = revision
    for name, payload in changed.items():
        if name == UPDATER:
            # The 2026 fast updater is patchable. Migrate this one verified
            # file out of legacy immutable; keep Game.exe/save config pinned.
            if (name not in data["files"] and
                    name not in data.get("immutable", {})):
                raise ValueError("Missing original Android updater in source ZIP.")
            data.setdefault("immutable", {}).pop(name, None)
            data["files"][name] = {"sha256": digest(payload), "size": len(payload)}
            continue
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
        compiled_region(
            source.read(PREFIX + CACHE),
            "KantoPilot.rb",
            source.read(PREFIX + KANTO),
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
