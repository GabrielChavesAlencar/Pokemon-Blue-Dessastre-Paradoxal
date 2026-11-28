"""Disposable Android Celadon compilation check from the exact public source build.

No game assets, patch archives, save data, or generated caches are published.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts/regions")]

from audit import KANTO, inventory, json_file
from audit_k06_celadon_services import summarize
from build_k06_celadon_services import CANDIDATES, STAGE_LOCAL, STORE, check_approach_stamp, stage_services
from ensure_source import RELATIVE_ARCHIVE, RELATIVE_SOURCE
from k06_approach_migration import APPROACH, INSTALL, READY, checked_file, verify_native_graph
from qa_k04_migration import save_namespace_valid
from scripts.android import source_update as source
from scripts.android.package import (
    HOENN_PLUGIN, KANTO_PLUGIN, REGION_START_PLUGIN, compiled_region, fingerprint, request_compile,
)
from scripts.android.update_client import MARKER, read_installed

PRODUCT = "791f8c8af9ecfba4e97a14c5535ca5957a9702e6"
RECIPE = "8e35c46091f17a5c93e11d7d9b8d6cc8698c179d"
WORK = ROOT / ".blue-work/k06-android-ci"
GAME = WORK / "Pokemon-Blue-Android"
RECIPE_ROOT = WORK / "k06-public-recipe"
CANDIDATE = WORK / "celadon-services"
SAVE = "K06-SAVE-SYNTHETIC.rxsave"
PROFILE = "Kanto K06 Celadon Android CI"
RECEIPT = WORK / "celadon-services-proof.json"


def verify_predecessor(game):
    game = game.resolve(strict=True)
    if (game/source.RECOVERY_FILE).exists() or (game/source.RECOVERY_FILE).is_symlink():
        raise ValueError("Resolve the interrupted Android update first")
    old = read_installed(game)
    proof = old.get("source_update")
    if not isinstance(proof,dict):
        raise ValueError("The verified Android source provenance is absent")
    expected = source.installed_provenance(old["files"], RECIPE)["inventory_sha256"]
    previous = proof.get("previous_inventory_sha256")
    if (old["channel"], old["revision"], proof.get("mode"), proof.get("product_revision"),
        proof.get("recipe_revision"), proof.get("stage"), proof.get("inventory_sha256")) != (
            "multiregion", PRODUCT, "pinned-source-local", PRODUCT, RECIPE, "K06_APPROACH", expected
        ) or not isinstance(previous,str) or not re.fullmatch(r"[a-f0-9]{64}",previous):
        raise ValueError("Celadon requires the exact, verified source-built K06 approach")
    regions, _ = source.protected_map_inventory(game, old)
    registered = json_file(checked_file(game, INSTALL))
    check_approach_stamp(registered, android_base=old)
    approach = json_file(checked_file(game, READY))
    if ((approach.get("status"), approach.get("population"), approach.get("source_ids")) != (
            "K06_APPROACH_CANDIDATE", 178, list(APPROACH))
            or len(regions["kanto"]) != 178 or len(regions["hoenn"]) != 199):
        raise ValueError("Celadon predecessor has an invalid shared regional registry")
    for rel in ("Data/MapInfos.rxdata", "Data/Tilesets.rxdata", INSTALL, READY):
        if source.checked_row(game/rel) != old["files"].get(rel):
            raise ValueError(f"Android predecessor registry hash mismatch: {rel}")
    verify_native_graph(game, compiled=True)
    return old


def pinned_source():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RECIPE_ROOT, text=True).strip()
    if head != RECIPE or source.digest(RECIPE_ROOT/RELATIVE_ARCHIVE) != json_file(KANTO)["sha256"]:
        raise ValueError("The exact public K06 approach source or recipe was not authenticated")
    return RECIPE_ROOT/RELATIVE_SOURCE


def require_ci():
    if (os.name != "nt" or os.getenv("GITHUB_ACTIONS") != "true" or not GAME.is_dir()
            or GAME.resolve() != WORK.resolve()/GAME.name or WORK.resolve() != WORK):
        raise ValueError("Celadon candidate is limited to a disposable Android installation in Windows CI")


def stage():
    require_ci()
    installed = verify_predecessor(GAME)
    original = pinned_source()
    sentinel = source.digest(checked_file(GAME,SAVE))
    marker_hash = source.digest(checked_file(GAME,MARKER))
    report = stage_services(original,GAME,CANDIDATE,summarize(original,json_file(KANTO)),android_base=installed)
    cfg = CANDIDATE/"mkxp.json"
    cfg.write_text(source.compiler_config(cfg.read_text("utf-8-sig"), PROFILE),encoding="utf8")
    if not save_namespace_valid(CANDIDATE,PROFILE) or (CANDIDATE/SAVE).exists():
        raise ValueError("The scoped compiler accidentally inherited a player save namespace")
    source.write_compiler_ini(CANDIDATE)
    (CANDIDATE/REGION_START_PLUGIN).write_bytes((ROOT/"scripts/battle_polish/RegionStart.rb").read_bytes())
    request_compile(CANDIDATE)
    if (source.digest(checked_file(GAME,SAVE)) != sentinel or source.digest(checked_file(GAME,MARKER)) != marker_hash):
        raise ValueError("Read-only candidate staging changed its verified predecessor")
    report.update(before_update_sha256=marker_hash, sentinel_sha256=sentinel, recipe=RECIPE)
    RECEIPT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    print("KANTO_K06_CELADON_ANDROID_SOURCE_STAGED_OK",flush=True)


def verify_clone(game, staged, report, old):
    candidate = json_file(checked_file(staged,INSTALL))
    previous = json_file(checked_file(game,INSTALL))["maps"]
    expected = {**previous, **{str(sid):mid for sid,mid in CANDIDATES.items()}}
    if (candidate.get("content_stage") != STAGE_LOCAL or candidate["maps"] != expected
            or not save_namespace_valid(staged,PROFILE)):
        raise ValueError("Scoped Android candidate has wrong registry or save profile")
    if source.digest(checked_file(game,MARKER)) != report["before_update_sha256"]:
        raise ValueError("Real predecessor was modified during the Android candidate")
    ready = checked_file(staged,"Data/blue-android-compiled.txt").read_text("ascii")
    if ready != fingerprint(staged):
        raise ValueError("Android native compiler did not attest the new plugin files")
    for rel in (KANTO_PLUGIN, HOENN_PLUGIN, REGION_START_PLUGIN):
        compiled_region(checked_file(staged,"Data/PluginScripts.rxdata").read_bytes(),
                        Path(rel).name, checked_file(staged,rel).read_bytes())
    for rel in ("Data/items.dat","Data/map_metadata.dat"):
        if source.checked_row(staged/rel) in (None, old["files"].get(rel)):
            raise ValueError(f"Android compiler failed to commit updated data: {rel}")
    before_infos,before_maps = inventory(game)
    after_infos,after_maps = inventory(staged)
    allowed = set(CANDIDATES.values())
    if ((set(after_infos)-set(before_infos)) != allowed or (set(after_maps)-set(before_maps)) != allowed
            or any(info != after_infos.get(mid) for mid,info in before_infos.items())):
        raise ValueError("Android registry changed outside four new authorized interiors")
    changed = {expected[str(sid)] for sid in (114,*STORE)}
    unchanged = 0
    for mid,path in before_maps.items():
        if mid in changed:
            continue
        name = path.relative_to(game).as_posix()
        row = old["files"].get(name)
        if row is None or source.checked_row(after_maps[mid]) != row or source.checked_row(path) != row:
            raise ValueError(f"Android unrelated map changed: {mid}")
        unchanged += 1
    if source.checked_row(staged/"Data/map_connections.dat") != old["files"].get("Data/map_connections.dat"):
        raise ValueError("Celadon store introduced a new outdoor route")
    return unchanged


def verify():
    require_ci()
    report = json_file(RECEIPT)
    unchanged = verify_clone(GAME,CANDIDATE,report,verify_predecessor(GAME))
    if (CANDIDATE/SAVE).exists() or source.digest(checked_file(GAME,SAVE)) != report["sentinel_sha256"]:
        raise ValueError("Disposable save witness changed")
    print("KANTO_K06_CELADON_ANDROID_COMPILED_CANDIDATE_OK:"+json.dumps(
        {"new_maps": CANDIDATES,"unchanged_old_kanto_ids":178,"unchanged_other_maps":unchanged,
         "unchanged_hoenn":199,"source_baseline":PRODUCT,"source_recipe":RECIPE,
         "physical_android":False,"applied_to_predecessor":False,"published":False}),flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("step",choices=("stage","verify"))
    globals()[p.parse_args().step]()
