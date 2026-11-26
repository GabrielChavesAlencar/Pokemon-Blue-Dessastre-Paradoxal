"""Verify exact published Android 128 recovery deltas on disposable real ZIPs.
No gameplay claims, no personal saves, no game files in uploaded artifacts.
"""
from __future__ import annotations
import argparse
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
from qa_k00_android_release import check, read_json, packaged_client, snapshot, verify_files
from scripts.android import update_client as client
from scripts.android.publish_updates import from_archive
from scripts.android.package import compiled_region
from scripts.android.verify_kanto_cerulean import KANTO_ATLAS, KANTO_RUNTIME, JOURNEY
from scripts.regions.kanto_wall_atlas import render_wall_atlas

CHANNEL = "multiregion"
NAME, MANIFEST = client.CHANNELS[CHANNEL]
NEW_TAG = "android-multiregion-128-4decb88"
NEW = "4decb88dc70b393c164bc501ca029bec113b4e3c"
NEW_MANIFEST_PIN = (3747448, "afacd165cc8088bb9858762c47b9eb1e27412cacb1b2be2cd606443fa2bae658")
NEW_FULL_PIN = (1401446257, "01f7f9caaa9cc136461d50a8a163887427c7b6be3a7cde99e85e5bfa28c089f6")
ATLAS_SHA = "93fa174122b15f45b4985986a0d059d552496f833cf80e4ed185db1da9df3f7c"
BASELINES = {
    "hotfix31": {
        "tag": "android-multiregion-hotfix-31-e7200ef",
        "revision": "e7200ef8003c2d84eb1c6931b403c9faaa0d15b6", "maps": 142,
        "zip": (1401941400, "71de98691f915a7847b6feac91c81970f3c874d2cf57538630d2d0ae112dcc6f"),
        "manifest": (3744977, "9e7cc215b28af442b49e61f93bfc0931ed7842bc144128c62dea3bfdd3372437"),
        "patch": NAME.removesuffix(".zip") + ".patch.zip",
        "patch_pin": (4094730, "22725b5b868b6d243872d4d5b7c15fb568808ec7dfd298f87bc9672816795d2c"),
    },
    "build82": {
        "tag": "android-multiregion-82-e23ff33",
        "revision": "e23ff33a67ed6cea6ca652f0d2150ae5d1de206d", "maps": 145,
        "zip": (1401412233, "2ba794ddc39994294d6cd3924996ef24c4374108c35d5a329b0a1061be84b31f"),
        "manifest": (3746108, "90a4bfbfcfc2b2b0e8755b0d4e05bbe50491fc8f7c6ed0018171fc4acaa75149"),
        "patch": NAME.removesuffix(".zip") + ".from-e23ff33a67ed.patch.zip",
        "patch_pin": (3988600, "054807eeb0d77ce0ca158415d295ca2e972e34e0d6ae220d015c032e66b03489"),
    },
}

def gh_json(endpoint):
    return json.loads(subprocess.check_output(["gh", "api", endpoint], text=True))

def fetch_pinned(folder, tag, name, pin):
    path = folder / tag / name
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["gh", "release", "download", tag, "--repo", client.REPO,
                    "--pattern", name, "--dir", str(path.parent)], check=True)
    check((path.stat().st_size, client.sha256_file(path)) == pin,
          "Published asset differs from pinned size/hash: " + name)
    return path

def asset_pin(release, name, pin):
    rows = [a for a in release["assets"] if a["name"] == name]
    check(len(rows) == 1 and rows[0]["state"] == "uploaded" and
          (rows[0]["size"], rows[0]["digest"]) == (pin[0], "sha256:" + pin[1]),
          "GitHub asset receipt mismatch: " + name)

def run(work, baseline):
    base = BASELINES[baseline]
    old_tag, old_rev = base["tag"], base["revision"]
    release = gh_json("repos/" + client.REPO + "/releases/tags/" + NEW_TAG)
    old_release = gh_json("repos/" + client.REPO + "/releases/tags/" + old_tag)
    check(release["target_commitish"] == NEW and old_release["target_commitish"] == old_rev,
          "Wrong published target revision")
    for name, pin in ((NAME, NEW_FULL_PIN), (MANIFEST, NEW_MANIFEST_PIN),
                      (base["patch"], base["patch_pin"])):
        asset_pin(release, name, pin)
    asset_pin(old_release, NAME, base["zip"])
    asset_pin(old_release, MANIFEST, base["manifest"])
    withdrawn = gh_json("repos/" + client.REPO + "/releases/tags/" + BASELINES["hotfix31"]["tag"])
    check("RETIRADO DE USO" in withdrawn["name"] and NEW_TAG in withdrawn["body"],
          "Bad release was not marked withdrawn")
    # Check the actual published release descriptors with the new selector.
    with patch.object(client, "get_json", return_value=[withdrawn, release]):
        check(client.release_for(CHANNEL)["tag_name"] == NEW_TAG, "Withdrawn release offered")
    ancestry = gh_json("repos/" + client.REPO + "/compare/" + old_rev + "..." + NEW)
    check(ancestry.get("status") == "ahead", "Target revision is not a descendant")
    full = fetch_pinned(work, old_tag, NAME, base["zip"])
    old_remote = read_json(fetch_pinned(work, old_tag, MANIFEST, base["manifest"]))
    new_path = fetch_pinned(work, NEW_TAG, MANIFEST, NEW_MANIFEST_PIN)
    new = read_json(new_path)
    delta = fetch_pinned(work, NEW_TAG, base["patch"], base["patch_pin"])
    installed, prefix = from_archive(full, CHANNEL)
    check(installed["revision"] == old_remote["revision"] == old_rev and
          new["revision"] == NEW and new["channel"] == CHANNEL, "Manifest revision/channel mismatch")
    check(installed["files"] == old_remote["files"] and
          installed.get("immutable", {}) == old_remote.get("immutable", {}), "Baseline manifest mismatch")
    check((new["full"]["size"], new["full"]["sha256"]) == NEW_FULL_PIN, "Target ZIP metadata mismatch")
    check(len(new["patches"]) == 9 and len({p["from_revision"] for p in new["patches"]}) == 9,
          "Unexpected patch inventory")
    for row in new["patches"]:
        asset_pin(release, row["asset"], (row["size"], row["sha256"]))
    selected = client.compatible_patch(release, installed, new)
    check(selected and selected["asset"] == base["patch"] and
          (selected["size"], selected["sha256"]) == base["patch_pin"], "Wrong selected patch")
    game = work / "game"
    game.mkdir()
    with ZipFile(full) as archive:
        for name in sorted(set(installed["files"]) | set(installed.get("immutable", {})) | {client.MARKER}):
            target = client._local_target(game, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(prefix + name) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
    old_count = verify_files(game, installed)
    mapping_path = "Data/blue-kanto-install.json"
    old_maps = read_json(game / mapping_path)["maps"]
    check(len(old_maps) == base["maps"], "Baseline map count differs")
    saves = {"Game.rxdata": b"K02C root save", "Data/File A.rxdata": b"K02C slot A",
             "SaveData/Auto 1.rxdata": b"K02C autosave", "saves/K02C.sav": b"K02C save folder",
             "user-notes.txt": b"K02C untracked user file"}
    for name, data in saves.items():
        path = client._local_target(game, name)
        check(not path.exists(), "Sentinel collides: " + name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    with ZipFile(delta) as archive:
        meta = json.loads(archive.read("patch.json"))
        changed, removed = client._verify_paths(client._old_patch_files(installed, new["files"]),
                                                new["files"], meta)
        check(meta["from_revision"] == old_rev and meta["to_revision"] == NEW, "Wrong patch ancestry")
    stable = ((set(installed["files"]) & set(new["files"])) |
              (set(installed.get("immutable", {})) & set(new.get("immutable", {})))) - set(changed)
    stable |= set(saves)
    before = snapshot(game, stable)
    updater = packaged_client(game)
    check(updater.compatible_patch(release, installed, new)["asset"] == base["patch"],
          "Old installed updater did not select recovery delta")
    updated, deleted, backup = updater.apply_patch(game, updater.read_installed(game), new, delta)
    check((updated, deleted, backup) == (len(changed), len(removed), None), "Unexpected patch writes")
    marker = updater.read_installed(game)
    check(marker["revision"] == NEW and marker["channel"] == CHANNEL and marker["update_mode"] == "patch"
          and marker["files"] == new["files"] and marker["immutable"] == new["immutable"], "Wrong committed marker")
    final_count = verify_files(game, new)
    check(snapshot(game, stable) == before, "Unchanged data/saves rewritten")
    check(all(not (game / name).exists() for name in removed), "Removed file remains")
    maps = read_json(game / mapping_path)["maps"]
    check(len(maps) == 151 and len(set(maps.values())) == 151 and
          all(maps.get(source) == mid for source, mid in old_maps.items()), "MapID regression")
    check(all((game / f"Data/Map{mid:03d}.rxdata").stat().st_size >= 128 for mid in maps.values()),
          "Native map missing")
    music_count = sum(line.startswith("MAP\t") for line in
                      (game / "Data/blue-kanto-music.txt").read_text("utf8").splitlines())
    check(music_count == 83, "Kanto music count differs")
    atlas = game / KANTO_ATLAS
    check(atlas.read_bytes() == render_wall_atlas() and client.sha256_file(atlas) == ATLAS_SHA,
          "Authored atlas differs")
    cache = (game / "Data/PluginScripts.rxdata").read_bytes()
    runtime = (game / KANTO_RUNTIME).read_bytes()
    journey = (game / JOURNEY).read_bytes()
    check(b"def self.cerulean_rival_crossing?" in runtime, "Gary missing")
    compiled_region(cache, "KantoPilot.rb", runtime)
    compiled_region(cache, "Journey.rb", journey)
    # Reload the updated packaged client; no download or rewrite on same revision.
    new_updater = packaged_client(game)
    final_names = set(new["files"]) | set(new["immutable"]) | set(saves) | {client.MARKER}
    final = snapshot(game, final_names)
    with patch.object(new_updater, "remote_update", return_value=(release, new)), \
         patch.object(new_updater, "verify_forward_revision"), \
         patch.object(new_updater, "download", side_effect=AssertionError("Unexpected download")):
        check(new_updater.main(["--game-dir", str(game), "--update"]) == 0, "Idempotent CLI failed")
    check(snapshot(game, final_names) == final, "Idempotent invocation rewrote files")
    check(not (game / ".blue-android-update-backups").exists() and
          not (game / ".blue-android-downloads").exists(), "Unexpected backup/download directory")
    return {"status": "PASS", "baseline": baseline, "from_revision": old_rev, "to_revision": NEW,
            "old_tag": old_tag, "new_tag": NEW_TAG, "old_maps": len(old_maps), "kanto_maps": len(maps),
            "map_ids_preserved": len(old_maps), "music_maps": music_count, "atlas_sha256": ATLAS_SHA,
            "old_files_verified": old_count, "final_files_verified": final_count, "changed": updated,
            "removed": deleted, "unchanged_files_preserved": len(stable), "save_sentinels_preserved": len(saves),
            "patch_bytes": selected["size"], "patch_sha256": selected["sha256"], "published_assets_verified": True,
            "no_backup": True, "idempotent": True, "compiled_gary": True, "compiled_journey": True,
            "physical_joiplay": False}

if __name__ == "__main__":
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Run only in isolated GitHub Actions")
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", choices=BASELINES)
    args = parser.parse_args()
    report = ROOT / ".blue-work" / ("k02c-recovery-" + args.baseline + ".json")
    report.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="k02c-recovery-") as folder:
            result = run(Path(folder), args.baseline)
    except Exception as error:
        report.write_text(json.dumps({"status": "FAIL", "baseline": args.baseline, "error": str(error)}, indent=2), encoding="utf8")
        raise
    report.write_text(json.dumps(result, indent=2), encoding="utf8")
    print("KANTO_K02C_PUBLISHED_RECOVERY_REPORT:" + json.dumps(result, sort_keys=True))
    print("KANTO_K02C_PUBLISHED_RECOVERY_" + args.baseline.upper() + "_OK")
