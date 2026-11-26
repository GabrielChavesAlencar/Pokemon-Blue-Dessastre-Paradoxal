"""CI-only migration exercise using real RXDATA, not a historical player save.

Derive a controlled 142-map registry from the verified current 145-map
installation. This is a reconstruction, NOT an archival 142-map game or
physical playtest. Never write to the original game or publish its data.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

import install_kanto as installer
from audit import ROOT, load, inventory
from stage import serialize
from pilot import EVENT_CLASSES

NEW = {"53", "54", "55"}
REPORT = ROOT / ".blue-work/k00-migration-proof.json"
WORK = ROOT / ".blue-work/k00-migration-ci"


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def snapshot(game, paths):
    return {str(p): installer.digest(game / p) if (game / p).is_file() else None
            for p in paths}


def run():
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.name != "nt":
        raise RuntimeError("This destructive fixture is restricted to Windows GitHub Actions")
    original = ROOT / "game"
    installer.verify_installed(original)
    check(not WORK.exists(), "K00 fixture directory already exists")
    WORK.mkdir(parents=True)
    game = WORK / "game"
    pilot = WORK / "rebuilt-pilot"
    # Only CI's freshly installed game is copied. No user device or save.
    shutil.copytree(original, game)
    proof_path = Path("Data/blue-kanto-install.json")
    proof = json.loads((game / proof_path).read_text("utf-8"))
    current = dict(proof["maps"])
    check(len(current) == 145 and NEW <= current.keys(), "Unexpected current registry")
    old = {key: value for key, value in current.items() if key not in NEW}
    infos, native_maps = inventory(game)
    foreign = {mid: path for mid, path in native_maps.items()
               if mid not in current.values()}
    protected = [Path("Data/System.rxdata"), Path("Game.exe"), Path("Game.ini"),
                 Path("mkxp.json")] + [p.relative_to(game) for p in foreign.values()]
    original_protected = snapshot(original, protected)
    # Explicitly synthetic save sentinel; never load into the engine.
    sentinel = Path("saves/K00-CI-SENTINEL.rxdata")
    (game / sentinel).parent.mkdir(parents=True, exist_ok=True)
    (game / sentinel).write_bytes(b"K00 synthetic save preservation sentinel")
    protected.append(sentinel)
    protected_before = snapshot(game, protected)
    # Remove only the three added map slots from this disposable copy.
    hashes = installer.recorded_hashes(proof)
    for key in NEW:
        mid = current[key]
        relative = Path(f"Data/Map{mid:03d}.rxdata")
        (game / relative).unlink()
        del infos[mid]
        hashes.pop(relative.as_posix(), None)
    installer.atomic(game / "Data/MapInfos.rxdata", serialize(infos))
    proof["maps"] = old
    proof["installed_sha256"] = hashes
    installer.atomic(game / proof_path, (json.dumps(proof, indent=2) + "\n").encode())
    installer.atomic(game / installer.READY_GATE,
                     installer.ready_gate_bytes({int(k): v for k, v in old.items()}))
    # Use Map300 if it really belongs to the old registry, else the actual
    # allocated Pallet slot. Never treat a foreign Map300 as Kanto.
    drift_id = 300 if 300 in old.values() else old["5"]
    drift_rel = Path(f"Data/Map{drift_id:03d}.rxdata")
    map_data = load(game / drift_rel)
    map_data.attrs["@autoplay_bgm"] = not map_data.attrs["@autoplay_bgm"]
    installer.atomic(game / drift_rel, serialize(map_data, EVENT_CLASSES))
    drift_hash = installer.digest(game / drift_rel)
    check(drift_hash != hashes[drift_rel.as_posix()], "Fixture did not produce map drift")
    # Missing second map has a proven registry slot and checksum.
    missing_id = next(mid for mid in old.values() if mid != drift_id)
    missing_rel = Path(f"Data/Map{missing_id:03d}.rxdata")
    (game / missing_rel).unlink()
    legacy = installer.legacy_proof(game)
    check(legacy["maps"] == old, "Legacy ownership failed")
    # Build exactly once against this copied registry using production code.
    installer.build(installer.SOURCE, game, pilot,
                    existing={int(k): v for k, v in old.items()})
    files, mapping, _ = installer.manifest(pilot, game, migration=legacy)
    check(len(mapping) == 145 and all(mapping[int(k)] == v for k, v in old.items()),
          "142 existing MapIDs changed")
    check(not (set(mapping.values()) & set(foreign)), "Foreign map ID collision")
    check(len(set(mapping.values()) - set(old.values())) == 3, "Expected exactly 3 new IDs")
    touched = list(files) + [proof_path, installer.READY_GATE, installer.MARKER,
                             Path("Data/blue-compile-request.txt"),
                             Path("Data/PluginScripts.rxdata")]
    before = snapshot(game, touched + protected)
    # Demonstrate that a real foreign tileset on the drifted map is refused.
    tiles = load(game / "Data/Tilesets.rxdata")
    foreign_tile = next(i for i, tile in enumerate(tiles) if i > 0 and tile is not None
                        and not installer.text(tile.attrs["@tileset_name"]).startswith("FRLG_Preview_"))
    prior = (game / drift_rel).read_bytes()
    map_data.attrs["@tileset_id"] = foreign_tile
    installer.atomic(game / drift_rel, serialize(map_data, EVENT_CLASSES))
    try:
        try:
            installer.apply_install(game, pilot, True, migration=legacy)
        except ValueError as error:
            check("Foreign tileset" in str(error), "Wrong foreign-map rejection: " + str(error))
        else:
            raise AssertionError("Foreign map was accepted")
    finally:
        installer.atomic(game / drift_rel, prior)
    check(snapshot(game, touched + protected) == before, "Foreign rejection mutated fixture")
    # Inject failure only at final verification; real file writes and rollback
    # execute unchanged. Never count this injection as real gameplay.
    with patch.object(installer, "verify_installed",
                      side_effect=ValueError("K00 injected final verification failure")):
        try:
            installer.apply_install(game, pilot, True, migration=legacy)
        except ValueError as error:
            check(str(error) == "K00 injected final verification failure", str(error))
        else:
            raise AssertionError("Injected failure did not abort")
    check(snapshot(game, touched + protected) == before, "Rollback hash mismatch")
    result = installer.apply_install(game, pilot, True, migration=legacy)
    check(result["status"] == "migrated", "Migration not committed")
    recovered = {p.replace(chr(92), "/") for p in result["recovered_legacy_maps"]}
    check({drift_rel.as_posix(), missing_rel.as_posix()} <= recovered, "Recovery not reported")
    check(installer.verify_installed(game)["maps"] == 145, "Final verification failed")
    check(snapshot(game, protected) == protected_before, "Protected files changed")
    final = snapshot(game, touched + protected)
    check(installer.sync_runtime(game, True)["status"] == "runtime_current",
          "Second runtime sync was not idempotent")
    try:
        installer.apply_install(game, pilot, True)
    except ValueError as error:
        check("Kanto ja instalado" in str(error), str(error))
    else:
        raise AssertionError("Duplicate installation accepted")
    check(snapshot(game, touched + protected) == final, "Second install changed files")
    check(snapshot(original, protected[:-1]) == original_protected, "Original game changed")
    return {"status": "PASS", "fixture": "reconstructed_142_from_real_145_rxdata",
            "historical_install": False, "physical_gameplay": False,
            "revision": os.environ.get("GITHUB_SHA"),
            "old_maps": len(old), "new_maps": len(mapping), "preserved_map_ids": len(old),
            "drift_map": drift_id, "missing_map": missing_id,
            "foreign_maps_preserved": len(foreign), "synthetic_save_preserved": True,
            "foreign_rejected": True, "rollback_hashes_equal": True,
            "idempotent": True, "original_game_preserved": True,
            "recovered_maps": sorted(recovered)}


if __name__ == "__main__":
    try:
        report = run()
    except Exception as error:
        REPORT.write_text(json.dumps({"status": "FAIL", "error": str(error)}, indent=2), encoding="utf-8")
        raise
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("KANTO_K00_MIGRATION_REPORT:" + json.dumps(report, sort_keys=True))
    print("KANTO_K00_REAL_RXDATA_MIGRATION_FIXTURE_OK")
