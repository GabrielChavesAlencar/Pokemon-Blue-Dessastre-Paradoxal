"""K00-A: exercise the actual published Android 74 -> 75 delta.
CI-only; no user device, JoiPlay execution, or historical personal saves.
The old full ZIP and both manifests are pinned, and the target delta is
verified against its published manifest before exercising the packaged updater.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.android import update_client as client
from scripts.android.publish_updates import from_archive
from scripts.android.package import compiled_region

OLD = "0bb75cf4971abe943c962e6bb8efb49945d0ecfa"
NEW = "ae5f3a1a869b5e808bf51848ef5e63db076e860d"
CHANNEL = "multiregion"
NAME, MANIFEST = client.CHANNELS[CHANNEL]
PATCH = NAME.removesuffix(".zip") + ".patch.zip"
OLD_TAG = "android-multiregion-74-0bb75cf"
NEW_TAG = "android-multiregion-75-ae5f3a1"
PINS = {
    (OLD_TAG, NAME): (1401408945, "cb612df21593f538d80720fd98eb9cc6d5882312b5f0bda03db4217a48c1784e"),
    (OLD_TAG, MANIFEST): (3746100, "8e7bae0ffcd9d6e1d0be56809ee72b4f9604364fcd46da00e7f309143137598c"),
    (NEW_TAG, MANIFEST): (3746108, "039d4925b52eed9cedf49d4cc591bfa56ef11ac1cf3d4e25b90f1504e338a931"),
    (NEW_TAG, PATCH): (1696931, "170c402895417abcf9d0b3f700fe581fc0ec5de38b94c0a8e566319b187dac31"),
}
REPORT = ROOT / ".blue-work/k00-android-release-proof.json"


def check(value, message):
    if not value:
        raise AssertionError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def packaged_client(game):
    spec = importlib.util.spec_from_file_location("k00_packaged_updater", game / "ATUALIZAR-ANDROID.py")
    module = importlib.util.module_from_spec(spec)
    # Don't create __pycache__ in the tested installation.
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    return module


def download_pinned(folder):
    for (tag, name), (size, digest) in PINS.items():
        path = folder / tag / name
        path.parent.mkdir(parents=True, exist_ok=True)
        # gh authenticates to the repository if private. The pinned digest,
        # not the transport or filename alone, is the integrity authority.
        subprocess.run(["gh", "release", "download", tag, "--repo", client.REPO,
                        "--pattern", name, "--dir", str(path.parent)], check=True)
        check(path.stat().st_size == size and client.sha256_file(path) == digest,
              "Published asset integrity mismatch: " + str(path))


def snapshot(game, names):
    return {name: (client.sha256_file(game / name), (game / name).stat().st_mtime_ns)
            for name in names if (game / name).is_file()}


def verify_files(game, manifest):
    records = {**manifest.get("immutable", {}), **manifest["files"]}
    for name, meta in records.items():
        target = client._local_target(game, name)
        check(target.is_file() and target.stat().st_size == meta["size"] and
              client.sha256_file(target) == meta["sha256"], "File verification failed: " + name)
    return len(records)


def interrupt_worker(game, manifest_path, delta):
    updater = packaged_client(game)
    original = updater._replace_from_zip

    def stop_after_first(*args):
        original(*args)
        # Real process termination after an atomic file replacement, before
        # revision marker commit. No Python exception cleanup or fake state.
        os._exit(77)

    updater._replace_from_zip = stop_after_first
    updater.apply_patch(game, updater.read_installed(game), read_json(manifest_path), delta)
    raise AssertionError("Interruption did not occur")


def run(work):
    downloads = work / "downloads"
    download_pinned(downloads)
    full = downloads / OLD_TAG / NAME
    old_remote = read_json(downloads / OLD_TAG / MANIFEST)
    new_manifest_path = downloads / NEW_TAG / MANIFEST
    new = read_json(new_manifest_path)
    delta = downloads / NEW_TAG / PATCH
    installed, prefix = from_archive(full, CHANNEL)
    check(installed["revision"] == old_remote["revision"] == OLD and new["revision"] == NEW,
          "Wrong published revision")
    check(installed["files"] == old_remote["files"] and
          installed.get("immutable", {}) == old_remote.get("immutable", {}), "Baseline manifest mismatch")
    check(new["channel"] == CHANNEL, "Wrong target channel")
    check(new["full"]["sha256"] == "3aa040ac5f6eab34b49a58351b6ee947b17f812464dfcfba974c70241efe750e"
          and new["full"]["size"] == 1401411010, "Target full archive metadata differs")
    # Use a release descriptor with the exact verified asset, not the latest
    # release (which will change). No real network fallback during apply.
    release = {"target_commitish": NEW, "assets": [{
        "name": PATCH, "state": "uploaded",
        "browser_download_url": "https://github.com/" + client.REPO +
                                "/releases/download/" + NEW_TAG + "/" + PATCH}]}
    selected = client.compatible_patch(release, installed, new)
    check(selected and selected["asset"] == PATCH and
          (selected["size"], selected["sha256"]) == PINS[(NEW_TAG, PATCH)], "Wrong delta selected")
    with ZipFile(delta) as archive:
        delta_meta = json.loads(archive.read("patch.json"))
        changed, removed = client._verify_paths(client._old_patch_files(installed, new["files"]),
                                                new["files"], delta_meta)
        check(len(changed) > 1, "Need multiple real replacements for interruption")
        check(delta_meta["from_revision"] == OLD and delta_meta["to_revision"] == NEW,
              "Wrong delta ancestry")
    game = work / "game"
    game.mkdir()
    # Extract only verified, inventoried game files. No extractall, no saves,
    # no path outside this disposable directory.
    with ZipFile(full) as archive:
        for name in sorted(set(installed["files"]) | set(installed.get("immutable", {})) | {client.MARKER}):
            target = client._local_target(game, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(prefix + name) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
    old_count = verify_files(game, installed)
    mapping_path = "Data/blue-kanto-install.json"
    old_maps = read_json(game / mapping_path)["maps"]
    check(len(old_maps) == 145, "Baseline map registry is not 145")
    saves = {
        "Game.rxdata": b"K00 synthetic root save",
        "Data/File A.rxdata": b"K00 synthetic slot A",
        "SaveData/Auto 1.rxdata": b"K00 synthetic auto save",
        "saves/K00.sav": b"K00 synthetic save directory",
        "user-notes.txt": b"K00 untracked file",
    }
    for name, data in saves.items():
        target = client._local_target(game, name)
        check(not target.exists(), "Save sentinel collides with published file")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    updater = packaged_client(game)
    names = set(installed["files"]) | set(installed.get("immutable", {})) | set(saves) | {client.MARKER}
    before = snapshot(game, names)
    marker_before = (game / client.MARKER).read_bytes()
    # Verify transport corruption is rejected before installation, including
    # cleanup of .part. Local file URI avoids a fabricated external failure.
    truncated = work / "truncated.zip"
    truncated.write_bytes(delta.read_bytes()[:-1])
    refused = work / "refused.zip"
    try:
        updater.download(truncated.as_uri(), refused, selected["sha256"], selected["size"])
    except ValueError as error:
        check("checksum/size mismatch" in str(error), str(error))
    else:
        raise AssertionError("Truncated real patch was accepted")
    check(not refused.exists() and not refused.with_suffix(".zip.part").exists(), "Partial download leaked")
    # Corrupt one actual payload while keeping the patch metadata untouched.
    corrupt = work / "corrupt.zip"
    victim = next(name for name in sorted(changed) if changed[name]["size"] > 0)
    with ZipFile(delta) as source, ZipFile(corrupt, "w") as target:
        for name in source.namelist():
            data = source.read(name)
            if name == "files/" + victim:
                data = bytes([data[0] ^ 1]) + data[1:]
            target.writestr(name, data)
    try:
        updater.apply_patch(game, updater.read_installed(game), new, corrupt)
    except ValueError as error:
        check("checksum mismatch" in str(error), str(error))
    else:
        raise AssertionError("Corrupt patch was accepted")
    check(snapshot(game, names) == before and not any((game / name).exists()
          for name in changed if name not in installed["files"]), "Corrupt patch changed installation")
    # Process dies after the first actual replacement.
    child = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--interrupt",
                            str(game), str(new_manifest_path), str(delta)])
    check(child.returncode == 77, "Expected abrupt interruption, got " + str(child.returncode))
    check((game / client.MARKER).read_bytes() == marker_before, "Revision committed before completion")
    first = sorted(changed)[0]
    check(client.sha256_file(game / first) == changed[first]["sha256"], "First replacement absent")
    first_mtime = (game / first).stat().st_mtime_ns
    check(snapshot(game, saves) == {k: before[k] for k in saves}, "Interruption changed saves")
    # Resume using the actual packaged updater and exact published patch.
    updated, deleted, backup = updater.apply_patch(game, updater.read_installed(game), new, delta)
    check(updated == len(changed) - 1 and deleted == len(removed) and backup is None,
          "Resume did not skip completed file")
    check((game / first).stat().st_mtime_ns == first_mtime, "Already updated file was rewritten")
    final_marker = updater.read_installed(game)
    check(final_marker["revision"] == NEW and final_marker["channel"] == CHANNEL
          and final_marker.get("update_mode") == "patch", "Wrong committed revision")
    check(final_marker["files"] == new["files"] and final_marker["immutable"] == new["immutable"],
          "Committed file table differs")
    final_count = verify_files(game, new)
    check(all(not (game / name).exists() for name in removed), "Removed file remains")
    stable = (set(installed["files"]) & set(new["files"])) - set(changed)
    stable |= (set(installed.get("immutable", {})) & set(new.get("immutable", {}))) - set(changed)
    stable |= set(saves)
    check(snapshot(game, stable) == {k: before[k] for k in stable},
          "Unchanged files, protected config, or saves were rewritten")
    check(read_json(game / mapping_path)["maps"] == old_maps, "Kanto MapIDs changed")
    check(all((game / f"Data/Map{mid:03d}.rxdata").is_file() for mid in old_maps.values()),
          "Missing Kanto map")
    cache = (game / "Data/PluginScripts.rxdata").read_bytes()
    runtime = (game / "Plugins/ZZZZZ Blue Kanto Pilot/KantoPilot.rb").read_bytes()
    journey = (game / "Plugins/ZZZZ Blue Story and Presentation/Journey.rb").read_bytes()
    check(b"def self.cerulean_rival_crossing?" in runtime, "Gary fix absent")
    compiled_region(cache, "KantoPilot.rb", runtime)
    compiled_region(cache, "Journey.rb", journey)
    # Re-run the command on the same pinned release; no downloads/writes.
    final_names = set(new["files"]) | set(new["immutable"]) | set(saves) | {client.MARKER}
    final = snapshot(game, final_names)
    with patch.object(updater, "remote_update", return_value=(release, new)), \
         patch.object(updater, "verify_forward_revision"), \
         patch.object(updater, "download", side_effect=AssertionError("Unexpected download")):
        check(updater.main(["--game-dir", str(game), "--update"]) == 0, "Idempotent CLI failed")
    check(snapshot(game, final_names) == final, "Idempotent invocation rewrote files")
    check(not (game / ".blue-android-update-backups").exists() and
          not (game / ".blue-android-downloads").exists(), "Unexpected backup/download directory")
    return {"status": "PASS", "fixture": "published_android_74_to_75", "physical_joiplay": False,
            "from_revision": OLD, "to_revision": NEW, "patch_bytes": selected["size"],
            "patch_sha256": selected["sha256"], "old_files_verified": old_count,
            "final_files_verified": final_count, "changed": len(changed), "removed": len(removed),
            "resumed_writes": updated, "unchanged_files_preserved": len(stable),
            "save_sentinels_preserved": len(saves), "truncated_download_rejected": True,
            "corrupt_payload_rejected": True, "abrupt_process_exit": 77, "marker_last": True,
            "already_updated_file_not_rewritten": True, "idempotent": True, "no_backup": True,
            "kanto_map_ids_preserved": len(old_maps), "compiled_cerulean_gary": True,
            "compiled_journey": True}


if __name__ == "__main__":
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Run only in isolated GitHub Actions")
    if len(sys.argv) == 5 and sys.argv[1] == "--interrupt":
        interrupt_worker(*(Path(p) for p in sys.argv[2:]))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="k00-android-published-") as folder:
            result = run(Path(folder))
    except Exception as error:
        REPORT.write_text(json.dumps({"status": "FAIL", "error": str(error)}, indent=2), encoding="utf-8")
        raise
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("KANTO_K00_ANDROID_RELEASE_REPORT:" + json.dumps(result, sort_keys=True))
    print("KANTO_K00_REAL_ANDROID_DELTA_RESUME_OK")
