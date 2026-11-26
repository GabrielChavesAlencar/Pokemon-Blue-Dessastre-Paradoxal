#!/usr/bin/env python3
"""Prepare the real 144-map world layer against the existing shared game.

This is a local, non-distributable candidate, not the isolated pilot installer.
No save, executable, System.rxdata, Scripts.rxdata or QA plugin is copied.
The candidate is deliberately NOT the approved sinnoh-shared/manifest.json.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts/regions")]

import sinnoh_shared as shared
from audit_sinnoh_rxdata import read_marshal
from sinnoh_f10b7_field_audit import cell_shape, directional_component, directional_masks
from stage import serialize

CANDIDATE = ".blue-work/sinnoh-shared-candidate"
PBS_REVIEW = {"PBS/encounters.txt", "PBS/map_metadata.txt"}


def choose_town_points(world, tiles, anchor):
    """Choose adjacent, unoccupied cells on the actual initial-town component."""
    occupied = {(e.attrs["@x"], e.attrs["@y"]) for e in world.attrs["@events"].values()}
    masks = directional_masks(world, tiles)
    dry = {p for p in masks if cell_shape(world, tiles, p).get("ordinary_walkable")}
    dry -= occupied
    if anchor not in dry:
        raise ValueError("Twinleaf entry witness is not a free dry cell")
    reachable = directional_component(dry, anchor, masks)
    for arrival in sorted(reachable, key=lambda p: (abs(p[0]-anchor[0])+abs(p[1]-anchor[1]), p)):
        for agent in sorted(reachable):
            if abs(agent[0]-arrival[0])+abs(agent[1]-arrival[1]) != 1:
                continue
            remaining = directional_component(dry-{agent}, arrival, masks)
            if anchor in remaining:
                return arrival, agent
    raise ValueError("No accessible Twinleaf travel agent placement")


def prepare_world(game, outputs, report):
    """Return the regional data and explicit runtime blockers without installing it."""
    mapping = report["mapids"]
    ids = sorted(mapping.values())
    if len(ids) != 144 or len(set(ids)) != 144 or not set(ids) <= set(shared.ID_RANGE):
        raise ValueError("Expected 144 distinct reserved Sinnoh maps")
    if report.get("maps_prepared") != 144 or not report.get("private_visual_import", {}).get("maps"):
        raise ValueError("Real source geometry is required")
    expected_maps = {f"Data/Map{mid:03d}.rxdata" for mid in ids}
    if {p for p in outputs if shared.MAP_FILE.fullmatch(p)} != expected_maps:
        raise ValueError("Generated map inventory does not match reservation")
    if any((game / p).exists() or (game / p).is_symlink() for p in expected_maps):
        raise ValueError("Sinnoh candidate overlaps existing maps")
    files = {p:outputs[p] for p in shared.SHARED_FILES | expected_maps}
    infos = read_marshal(files[shared.MAP_INFOS], "SHARED_CANDIDATE_INFOS")
    tiles = read_marshal(files[shared.TILESETS], "SHARED_CANDIDATE_TILESETS")
    town_id = mapping["SINNOH_TWINLEAF_TOWN"]
    source = report["private_visual_import"]["maps"].get("SINNOH_TWINLEAF_TOWN", {})
    if source.get("source_id") != 194 or source.get("target_id") != town_id:
        raise ValueError("Twinleaf donor identity mismatch")
    # J11C originally named the nine maps with QA labels. Promote only the
    # proven Twinleaf name; do not rename the existing shared MapInfos entries.
    infos[town_id].attrs["@name"] = b"Twinleaf Town"
    files[shared.MAP_INFOS] = serialize(infos)
    for mid in ids:
        world = read_marshal(files[f"Data/Map{mid:03d}.rxdata"], "SHARED_CANDIDATE_MAP")
        tid = world.attrs.get("@tileset_id")
        if type(tid) is not int or not 0 < tid < len(tiles) or not tiles[tid]:
            raise ValueError(f"Invalid tileset for map {mid}")
    town = read_marshal(files[f"Data/Map{town_id:03d}.rxdata"], "SHARED_CANDIDATE_TOWN")
    # Use the donor-verified grassless component seed, not an invented map ID.
    from sinnoh_private_visual import SEEDS
    arrival, agent = choose_town_points(town, tiles, tuple(SEEDS["SINNOH_TWINLEAF_TOWN"]))
    start = report["start"]
    start_world = read_marshal(files[f"Data/Map{start[0]:03d}.rxdata"], "SHARED_CANDIDATE_START")
    if start[0] != mapping["SINNOH_PLAYER_BEDROOM"] or not cell_shape(start_world, tiles, tuple(start[1:])).get("ordinary_walkable"):
        raise ValueError("Invalid shared New Game start")
    if any((e.attrs["@x"],e.attrs["@y"]) == tuple(start[1:]) for e in start_world.attrs["@events"].values()):
        raise ValueError("Shared New Game start overlaps an event")
    base = {p:shared.sha(shared.safe_file(game,p).read_bytes()) for p in shared.SHARED_FILES}
    proof = {"map_ids":ids, "base":base, "start":start,
             "arrival":[town_id,*arrival], "agent":[town_id,*agent]}
    shared.preserve_base(game, proof, files)
    # Copy only namespaced regional resources; shared PBS additions remain
    # separate review inputs until the compiler and foreign sections are checked.
    for p, raw in outputs.items():
        if shared.ASSET.fullmatch(p):
            if (game / p).exists() or (game / p).is_symlink():
                raise ValueError("Regional asset collision: "+p)
            files[p] = raw
    review = {p:outputs[p] for p in PBS_REVIEW if p in outputs}
    unhandled = sorted(p for p in outputs if p not in files and p not in review)
    proof.update(schema=1, profile="BLUE_SINNOH_SHARED_CANDIDATE_V1",
                 files={p:shared.sha(raw) for p,raw in files.items()},
                 review_files={p:shared.sha(raw) for p,raw in review.items()},
                 excluded_outputs=unhandled,
                 approvals={k:False for k in ("map_ids","asset_rights","connected_world",
                                                "windows_travel","joiplay_travel","android_distribution")},
                 runtime_install_enabled=False, native_verified=False,
                 blockers=["shared event runtime and PBS merge/compilation",
                           "full Windows and JoiPlay travel receipts",
                           "asset distribution approval"])
    return files, review, proof


def prepare(project, game):
    project, game = project.resolve(), game.resolve()
    if game != project / "game":
        raise ValueError("Use the managed shared game/ as read-only base")
    shared.assert_no_legacy_sinnoh_shared(game)
    folder = project / CANDIDATE
    if folder.exists() or folder.is_symlink() or folder.parent.is_symlink():
        raise ValueError("Candidate exists; preserve it or move it before preparing another")
    from sinnoh_source_download import ensure_sources
    from install_sinnoh_experimental_windows import build_files
    ensure_sources(project)
    outputs, report = build_files(game, project)
    files, review, proof = prepare_world(game, outputs, report)
    folder.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sinnoh-shared-", dir=folder.parent) as tmp:
        staged = Path(tmp) / "candidate"
        for prefix, payload in (("world",files),("review",review)):
            for rel, raw in payload.items():
                shared.atomic(shared.safe_file(staged/prefix,rel),raw)
        shared.atomic(staged/"candidate.json",(json.dumps(proof,indent=2,ensure_ascii=False)+"\n").encode("utf-8"))
        staged.rename(folder)
    return proof


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT)
    args = parser.parse_args()
    result = prepare(args.project,args.project/"game")
    print("SINNOH_SHARED_WORLD_CANDIDATE", json.dumps(result,ensure_ascii=False))
