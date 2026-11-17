#!/usr/bin/env python3
"""G07.2: audit a SYNTHETIC, documentation-only Unova incremental package.

Strictly read-only. Do not call a real installer, extractor, downloader,
Game.exe, JoiPlay, Android updater, PC storage or save APIs. Digests verify
integrity only, NOT signer authenticity, provenance rights or installation.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = "data/regions/unova-g07-incremental.schema.json"
CONTRACT_PATH = "data/regions/unova-g07-incremental-contract.json"
REGISTRY = "site/public/data/regions.json"
TRACKER = "site/public/data/unova-github-progress.json"
PREDECESSOR = "data/regions/unova-g05-travel-contract.json"
SOURCE_PATHS = (
    "scripts/windows/Bootstrap.cs", "scripts/install_game.py",
    "scripts/android/update_client.py", "scripts/regions/audit_unova_a12_ownership.py",
)
CHANNEL = "blue-story-unova-documentation"
REPO = "GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal"
PREFIX = "docs/unova-package-fixtures/"
SOURCE_MANIFEST = PREFIX + "origin-manifest.json"
RIGHTS = {
    "status": "FIXTURE_ONLY_NOT_DISTRIBUTABLE",
    "license_id": None,
    "evidence_path": None,
    "redistribution_approved": False,
}
MAX_BYTES = 65536
MAX_PACKAGE_BYTES = 524288
MAX_FILES = 16
HEX64 = re.compile(r"^[a-f0-9]{64}$")
HEX40 = re.compile(r"^[a-f0-9]{40}$")
VERSION = re.compile(r"^0\.0\.[1-9][0-9]*-planned$")
ID = re.compile(r"^UNOVA-G07\.2-FIXTURE-[a-z0-9-]{1,24}$")
PART = re.compile(r"^[a-z0-9][a-z0-9._-]{0,40}$")
PATH_KEYS = {"path", "kind", "sha256", "source_sha256", "size", "source_size", "rights"}
ROOT_KEYS = {
    "schema_version", "region", "campaign", "package_id", "package_version",
    "channel", "status", "mode", "source", "compatibility", "rights", "files",
    "native_payload_approved", "release_allowed", "game_exe_tested",
    "saves_modified", "package_sha256",
}
SOURCE_KEYS = {
    "repository", "origin_revision", "target_revision", "manifest_path",
    "manifest_sha256", "manifest_size",
}
CLIENT_KEYS = {
    "client", "protocol_version", "minimum_blue_story_version",
    "windows", "android", "joiplay", "installer_adapter_implemented",
}
ORIGIN_KEYS = {"region", "channel", "revision", "package_version", "fixture_only", "files"}
ORIGIN_FILE_KEYS = {"path", "sha256", "size"}
CONTRACT_KEYS = {
    "schema_version", "phase", "region", "status", "schema_path", "validator_path",
    "runtime_sources", "predecessor", "source_manifest_requirement",
    "package_authentication", "channel", "allowed_prefix", "allowed_suffixes",
    "maximum_files", "maximum_file_bytes", "maximum_package_bytes",
    "rights_status", "native_payload_approved", "release_allowed",
    "installer_implemented", "android_supported", "game_exe_tested",
    "saves_modified", "can_install", "notes",
}
CLI_STATUSES = {"phase": "G07.2", "can_install": False, "native_payload_approved": False,
                "release_allowed": False, "game_exe_tested": False,
                "saves_modified": False}

def deny(message: str) -> None:
    raise ValueError("UNOVA_G07_2_BLOCKED: " + str(message))

def strict(data: Any, keys: set[str], name: str) -> dict:
    if not isinstance(data, dict) or set(data) != keys:
        deny("unknown or missing fields in " + name)
    return data

def j(root: Path, name: str) -> dict:
    file = root / name
    if file.is_symlink() or not file.is_file() or file.stat().st_size > 100000:
        deny("source missing, symlink or too large: " + name)
    return json.loads(file.read_text(encoding="utf-8"))

def body(root: Path, name: str) -> str:
    file = root / name
    if file.is_symlink() or not file.is_file() or file.stat().st_size > 150000:
        deny("audited runtime source missing: " + name)
    return file.read_text(encoding="utf-8")

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")

def package_digest(pkg: dict) -> str:
    return digest(canonical({key: val for key, val in pkg.items()
                             if key != "package_sha256"}))

def path_ok(name: Any) -> bool:
    if not isinstance(name, str) or not name.startswith(PREFIX) or len(name) > 130:
        return False
    if any(char in name for char in ("\\", ":", "%", "\x00", "?", "#")):
        return False
    if not name.isascii() or name != name.lower() or ".." in name:
        return False
    suffix = Path(name).suffix
    if suffix not in (".txt", ".md", ".json"):
        return False
    parts = name[len(PREFIX):].split("/")
    return bool(parts) and all(PART.fullmatch(part) for part in parts)

def sha(value: Any, name: str) -> None:
    if type(value) is not str or not HEX64.fullmatch(value):
        deny("missing or malformed SHA-256: " + name)

def size(value: Any, name: str) -> None:
    if type(value) is not int or not 1 <= value <= MAX_BYTES:
        deny("invalid bounded file size: " + name)

def rights(value: Any) -> None:
    strict(value, set(RIGHTS), "rights")
    if value != RIGHTS or any(type(value[k]) is not type(RIGHTS[k]) for k in RIGHTS):
        deny("rights unverified, absent or falsely distributable")

def validate_catalog(root: Path = ROOT) -> dict:
    c = j(root, CONTRACT_PATH)
    strict(c, CONTRACT_KEYS, "G07.2 contract")
    required = {
        "schema_version": 1, "phase": "G07.2", "region": "UNOVA",
        "status": "PLANNED_INCREMENTAL_SCHEMA_ONLY", "schema_path": SCHEMA_PATH,
        "validator_path": "scripts/regions/audit_unova_g07_incremental_manifest.py",
        "runtime_sources": list(SOURCE_PATHS), "predecessor": PREDECESSOR,
        "source_manifest_requirement": "SHA256_AND_FULL_ORIGIN_REVISION",
        "package_authentication": "DIGEST_ONLY_NOT_SIGNED_OR_TRUSTED",
        "channel": CHANNEL, "allowed_prefix": PREFIX,
        "allowed_suffixes": [".txt", ".md", ".json"],
        "maximum_files": MAX_FILES, "maximum_file_bytes": MAX_BYTES,
        "maximum_package_bytes": MAX_PACKAGE_BYTES,
        "rights_status": RIGHTS["status"],
        "native_payload_approved": False, "release_allowed": False,
        "installer_implemented": False, "android_supported": False,
        "game_exe_tested": False, "saves_modified": False, "can_install": False,
    }
    for key, expect in required.items():
        if c.get(key) != expect or type(c.get(key)) is not type(expect):
            deny("contract source/policy drift: " + key)
    if not isinstance(c["notes"], list) or len(c["notes"]) < 6:
        deny("native limitations missing")
    schema = j(root, SCHEMA_PATH)
    if (schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
        or schema.get("type") != "object"
        or schema.get("additionalProperties") is not False
        or set(schema.get("required", [])) != ROOT_KEYS
        or set(schema.get("properties", {})) != ROOT_KEYS):
        deny("schema no longer strict draft 2020-12")
    for k, v in {
        "schema_version": 1, "region": "UNOVA", "campaign": "WHITE_BW",
        "channel": CHANNEL, "status": "PLANNED_OFFLINE_PACKAGE_SCHEMA_ONLY",
        "mode": "fixture_only", "native_payload_approved": False,
        "release_allowed": False, "game_exe_tested": False,
        "saves_modified": False,
    }.items():
        if schema["properties"].get(k, {}).get("const") != v:
            deny("schema falsely relaxed: " + k)
    props = schema["properties"]
    for name in ("source", "compatibility", "rights"):
        if props[name].get("additionalProperties") is not False:
            deny("schema lets unrecognized fields through: " + name)
    if (props["files"].get("maxItems") != MAX_FILES
        or props["files"].get("items", {}).get("additionalProperties") is not False
        or props["files"]["items"].get("properties", {}).get("kind", {}).get("const") != "documentation_fixture"):
        deny("schema file limits relaxed")
    reg = j(root, REGISTRY)
    board = j(root, TRACKER)
    previous = j(root, PREDECESSOR)
    if (reg.get("regions", {}).get("UNOVA", {}).get("status") != "planned"
        or previous.get("can_install") is not False
        or board.get("status") != "PLANNED_NOT_NATIVE_PLAYABLE"
        or board.get("native_technical_bar", {}).get("completed") != 0
        or board.get("native_playable_bar", {}).get("completed") != 0):
        deny("Unova was promoted without native proof")
    if not any(t.get("id") == "G07.2" and t.get("status") in ("pending", "done")
               for g in board.get("groups", []) for t in g.get("tasks", [])):
        deny("G07.2 tracker missing")
    native = {p: body(root, p) for p in SOURCE_PATHS}
    signatures = {
        SOURCE_PATHS[0]: ("static string Hash(string path)", "static void Download(string url,string target,string expected)",
                          "internal static string SafePath", "static bool Protected",
                          "Download(\"https://codeload.github.com/\"+Repo+\"/zip/\"+revision,zip,null)"),
        SOURCE_PATHS[1]: ("def install(project,game,hub_only=False", "scripts/regions/auto_integrate_johto.py"),
        SOURCE_PATHS[2]: ('CHANNELS = {', '"decades":', '"kanto":', '"multiregion":', "def safe_path(name):"),
        SOURCE_PATHS[3]: ("def audit_installer_sources(project):", "parsed, not imported or executed"),
    }
    for name, tokens in signatures.items():
        if any(token not in native[name] for token in tokens):
            deny("Blue-Story/Android/A12 source changed, re-audit required: " + name)
    return {**CLI_STATUSES, "status": "SOURCE_SCHEMA_CHECKED_FIXTURE_ONLY",
            "schema_draft": "2020-12", "physical_installation_proved": False,
            "allowed_directory": PREFIX, "max_files": MAX_FILES}

def decode_origin(raw: bytes, source: dict) -> dict:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        deny("origin manifest bytes absent or oversized")
    if source["manifest_size"] != len(raw) or digest(raw) != source["manifest_sha256"]:
        deny("origin manifest SHA-256/size mismatch")
    def pairs(rows):
        d = {}
        for k, v in rows:
            if k in d:
                deny("duplicate JSON key in origin manifest")
            d[k] = v
        return d
    try:
        decoded = json.loads(raw, object_pairs_hook=pairs,
                             parse_constant=lambda _: deny("unsafe JSON constant"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        deny("origin manifest malformed JSON: " + str(e)[:100])
    strict(decoded, ORIGIN_KEYS, "origin manifest")
    if canonical(decoded) != raw:
        deny("origin manifest not canonical JSON")
    if (decoded["region"] != "UNOVA" or decoded["channel"] != CHANNEL
        or decoded["fixture_only"] is not True
        or decoded["revision"] != source["origin_revision"]
        or decoded["package_version"] != "0.0.0"):
        deny("origin revision, channel or status mismatch")
    entries = decoded["files"]
    if not isinstance(entries, list) or not 0 < len(entries) <= MAX_FILES:
        deny("missing/oversized origin file inventory")
    seen = set()
    for item in entries:
        strict(item, ORIGIN_FILE_KEYS, "origin file")
        if not path_ok(item["path"]) or item["path"].casefold() in seen:
            deny("unsafe or duplicate origin path")
        seen.add(item["path"].casefold())
        sha(item["sha256"], "origin inventory")
        size(item["size"], "origin file")
    return decoded

def validate_package(package: dict, origin_manifest_bytes: bytes,
                     source_bytes: Mapping[str, bytes],
                     destination_bytes: Mapping[str, bytes]) -> dict:
    strict(package, ROOT_KEYS, "incremental package")
    expected = {
        "schema_version": 1, "region": "UNOVA", "campaign": "WHITE_BW",
        "channel": CHANNEL, "status": "PLANNED_OFFLINE_PACKAGE_SCHEMA_ONLY",
        "mode": "fixture_only", "native_payload_approved": False,
        "release_allowed": False, "game_exe_tested": False,
        "saves_modified": False,
    }
    for k, val in expected.items():
        if package.get(k) != val or type(package.get(k)) is not type(val):
            deny("native release claim or unsupported package identity: " + k)
    if not isinstance(package["package_id"], str) or not ID.fullmatch(package["package_id"]):
        deny("unexpected package identity")
    version = package["package_version"]
    if type(version) is not str or not VERSION.fullmatch(version):
        deny("incompatible version or downgrade")
    rights(package["rights"])
    source = strict(package["source"], SOURCE_KEYS, "source/provenance")
    if source["repository"] != REPO or source["manifest_path"] != SOURCE_MANIFEST:
        deny("foreign or unproven source manifest")
    for k in ("origin_revision", "target_revision"):
        if type(source[k]) is not str or not HEX40.fullmatch(source[k]):
            deny("source/target revision must be full Git SHA")
    if source["origin_revision"] == source["target_revision"]:
        deny("same revision is not an incremental update")
    sha(source["manifest_sha256"], "origin manifest")
    size(source["manifest_size"], "origin manifest")
    client = strict(package["compatibility"], CLIENT_KEYS, "compatibility")
    expected_client = {
        "client": "Blue-Story", "protocol_version": 1,
        "minimum_blue_story_version": "0.0.0", "windows": "schema_only",
        "android": "not_supported", "joiplay": "not_supported",
        "installer_adapter_implemented": False,
    }
    if client != expected_client or any(type(client[k]) is not type(v)
                                        for k, v in expected_client.items()):
        deny("Blue-Story/Windows/Android/JoiPlay compatibility not proven")
    files = package["files"]
    if not isinstance(files, list) or not 0 < len(files) <= MAX_FILES:
        deny("invalid number of fixture-only files")
    origin = decode_origin(origin_manifest_bytes, source)
    originals = {f["path"]: f for f in origin["files"]}
    if not isinstance(source_bytes, Mapping) or not isinstance(destination_bytes, Mapping):
        deny("synthetic source and destination bytes required")
    names = []
    total_size = len(origin_manifest_bytes)
    for f in files:
        strict(f, PATH_KEYS, "file metadata")
        name = f["path"]
        if not path_ok(name) or name == SOURCE_MANIFEST:
            deny("unsafe native, traversal, protected or source-manifest payload path")
        if f["kind"] != "documentation_fixture":
            deny("native map/asset/script payload prohibited")
        if name.casefold() in (x.casefold() for x in names):
            deny("duplicate or casefold-colliding file path")
        names.append(name)
        rights(f["rights"])
        sha(f["sha256"], "destination file")
        sha(f["source_sha256"], "origin file")
        size(f["size"], "destination file")
        size(f["source_size"], "source file")
        if name not in originals:
            deny("payload missing from source manifest inventory")
        if f["source_sha256"] != originals[name]["sha256"] or f["source_size"] != originals[name]["size"]:
            deny("source inventory hash/size mismatch")
        old, new = source_bytes.get(name), destination_bytes.get(name)
        if type(old) is not bytes or type(new) is not bytes:
            deny("missing in-memory origin or destination bytes")
        if len(old) != f["source_size"] or digest(old) != f["source_sha256"]:
            deny("actual synthetic source bytes fail SHA-256")
        if len(new) != f["size"] or digest(new) != f["sha256"]:
            deny("actual synthetic destination bytes fail SHA-256")
        total_size += len(old) + len(new)
        if digest(old) == digest(new):
            deny("unchanged bytes cannot be advertised as increment")
    if set(source_bytes) != set(names) or set(destination_bytes) != set(names) or set(originals) != set(names):
        deny("unlisted, missing, shadow or extra payload/source entry")
    if total_size > MAX_PACKAGE_BYTES:
        deny("package exceeds dry-run memory cap")
    sha(package["package_sha256"], "package identity")
    if package["package_sha256"] != package_digest(package):
        deny("package metadata SHA-256 mismatch (not a signature)")
    return {**CLI_STATUSES, "status": "SYNTHETIC_DOCS_UPDATE_VALIDATED_NOT_INSTALLABLE",
            "origin_revision": source["origin_revision"],
            "target_revision": source["target_revision"],
            "files_checked": len(files), "sha256_verified": True,
            "provenance_authenticated": False, "license_verified": False,
            "native_files_written": 0, "bytes_written": 0, "fixture_only": True}

def demo_package() -> tuple[dict, bytes, dict[str, bytes], dict[str, bytes]]:
    name = PREFIX + "g07-2-note.txt"
    old = b"old"
    new = b"abc"
    origin = {
        "region": "UNOVA", "channel": CHANNEL, "revision": "a" * 40,
        "package_version": "0.0.0", "fixture_only": True,
        "files": [{"path": name, "sha256": digest(old), "size": len(old)}],
    }
    source_manifest = canonical(origin)
    obj = {
        "schema_version": 1, "region": "UNOVA", "campaign": "WHITE_BW",
        "package_id": "UNOVA-G07.2-FIXTURE-alpha",
        "package_version": "0.0.1-planned", "channel": CHANNEL,
        "status": "PLANNED_OFFLINE_PACKAGE_SCHEMA_ONLY", "mode": "fixture_only",
        "source": {
            "repository": REPO, "origin_revision": "a" * 40,
            "target_revision": "b" * 40, "manifest_path": SOURCE_MANIFEST,
            "manifest_sha256": digest(source_manifest),
            "manifest_size": len(source_manifest),
        },
        "compatibility": {
            "client": "Blue-Story", "protocol_version": 1,
            "minimum_blue_story_version": "0.0.0",
            "windows": "schema_only", "android": "not_supported",
            "joiplay": "not_supported", "installer_adapter_implemented": False,
        },
        "rights": copy.deepcopy(RIGHTS),
        "files": [{
            "path": name, "kind": "documentation_fixture",
            "sha256": digest(new), "source_sha256": digest(old),
            "size": len(new), "source_size": len(old),
            "rights": copy.deepcopy(RIGHTS),
        }],
        "native_payload_approved": False, "release_allowed": False,
        "game_exe_tested": False, "saves_modified": False,
    }
    obj["package_sha256"] = package_digest(obj)
    return obj, source_manifest, {name: old}, {name: new}

def demo(root: Path = ROOT) -> dict:
    validate_catalog(root)
    obj, origin, old, new = demo_package()
    valid = validate_package(obj, origin, old, new)
    altered = copy.deepcopy(obj)
    altered["files"][0]["path"] = "../game/Data/Map518.rxdata"
    altered["package_sha256"] = package_digest(altered)
    blocked = False
    try:
        validate_package(altered, origin, old, new)
    except ValueError:
        blocked = True
    if not blocked:
        deny("unsafe native MapID path unexpectedly accepted")
    return {**valid, "unsafe_native_map_path_blocked": blocked,
            "blue_story_integrated": False, "android_supported": False}

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--simulate-demo", action="store_true")
    args = p.parse_args(argv)
    try:
        report = validate_catalog() if args.check else demo()
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, OSError, UnicodeError, TypeError, KeyError, IndexError, RecursionError) as err:
        print("UNOVA_G07_2_BLOCKED: " + str(err)[:280])
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
