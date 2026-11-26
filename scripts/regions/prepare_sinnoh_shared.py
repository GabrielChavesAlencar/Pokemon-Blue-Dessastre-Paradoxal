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
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts/regions")]

import sinnoh_shared as shared
from audit_sinnoh_rxdata import read_marshal
from sinnoh_f10b7_field_audit import cell_shape, directional_component, directional_masks, step_allowed
from stage import serialize

CANDIDATE = ".blue-work/sinnoh-shared-candidate"


def shared_handlers(project, handlers):
    region = project / "scripts/regions"
    code = [region.joinpath("SinnohSharedEvents.rb").read_bytes(),
            region.joinpath("SinnohPilot.rb").read_bytes()]
    for part in handlers:
        # Port the generated regional tables and their handlers together.
        # Do not load the private bootstrap, save token or teleport tools.
        part = re.sub(rb"defined\?\(BlueSinnohExperimental\)\s*&&\s*BlueSinnohExperimental\.private_copy\?|BlueSinnohExperimental\.private_copy\?",
                      b"BlueSinnohSharedEvents.active?", part)
        part = re.sub(rb"defined\?\(BlueKantoTitle\)\s*&&\s*BlueKantoTitle\.sinnoh_experimental_barry_compiled\?",
                      b"BlueSinnohSharedEvents.ready?", part)
        part = re.sub(rb"!defined\?\(BlueKantoTitle\)\s*\|\|\s*!BlueKantoTitle\.sinnoh_experimental_barry_compiled\?",
                      b"!BlueSinnohSharedEvents.ready?", part)
        part = part.replace(b"def self.install!\n    return unless BlueSinnohSharedEvents.active?\n",
                            b"def self.install!\n")
        part = part.replace(b"return unless BlueSinnohSharedEvents.active? && defined?(TilemapRenderer)",
                            b"return unless defined?(TilemapRenderer)")
        if b"BlueSinnohExperimental" in part or b"BlueSinnohQAStart" in part or b"sinnoh_experimental_barry_compiled?" in part:
            module = re.search(rb"(?m)^module (\w+)",part)
            raise ValueError("Private QA gate in shared Sinnoh handler " +
                             (module[1].decode("ascii") if module else "without a module"))
        code.append(part)
    code.append(b"BlueSinnohSharedEvents.bind!\n")
    return {shared.PLUGIN:b"\n".join(code),
            shared.META:b"Name = Blue Sinnoh Shared\nVersion = 0.1\nEssentials = 21.1\nRequires = Blue Battle Presentation and Story\nScripts = SinnohSharedEvents.rb\n"}


def choose_town_points(world, tiles, anchor):
    """Choose adjacent, unoccupied cells on the actual initial-town component."""
    occupied = {(e.attrs["@x"], e.attrs["@y"]): e.attrs.get("@name")
                for e in world.attrs["@events"].values()}
    masks = directional_masks(world, tiles)
    dry = {p for p in masks if cell_shape(world, tiles, p).get("ordinary_walkable")}
    if anchor not in dry:
        raise ValueError("Twinleaf entry witness is not on dry ground")
    dry.difference_update(occupied)
    if anchor not in dry:
        if occupied[anchor] not in (b"SN_TOWN_TO_ROUTE201", "SN_TOWN_TO_ROUTE201"):
            raise ValueError("Unexpected event on the Twinleaf entry witness")
        x, y = anchor
        neighbours = [(x+dx,y+dy) for dx,dy in ((0,1),(-1,0),(1,0),(0,-1))
                      if (x+dx,y+dy) in dry and step_allowed(masks[anchor], masks[x+dx,y+dy], (dx,dy))]
        if not neighbours:
            raise ValueError("No clear dry step from the Twinleaf portal")
        anchor = max(neighbours, key=lambda point: len(directional_component(dry, point, masks)))
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
    runtime = outputs.get(shared.PLUGIN,b"")
    handlers = {}
    parts = re.split(rb"(?m)^module (BlueSinnoh\w+)\s*$",runtime)
    for module, code in zip(parts[1::2],parts[2::2]):
        handlers.setdefault(module,set()).update(re.findall(rb"(?m)^  def self\.(\w+[?!]?)",code))
    missing = set()
    for mid in ids:
        world = read_marshal(files[f"Data/Map{mid:03d}.rxdata"], "SHARED_CANDIDATE_MAP")
        tid = world.attrs.get("@tileset_id")
        if type(tid) is not int or not 0 < tid < len(tiles) or not tiles[tid]:
            raise ValueError(f"Invalid tileset for map {mid}")
        for event in world.attrs["@events"].values():
            for page in event.attrs.get("@pages", []):
                for command in page.attrs.get("@list", []):
                    if command.attrs.get("@code") not in (111,355,655):
                        continue
                    for raw in command.attrs.get("@parameters", []):
                        if not isinstance(raw,bytes):
                            continue
                        for module,method in re.findall(rb"\b(BlueSinnoh\w+)\.(\w+[?!]?)",raw):
                            if method == b"respond_to?" and module in handlers:
                                continue
                            if method not in handlers.get(module,()):
                                missing.add(f"{mid}:{module.decode()}.{method.decode()}")
    if missing:
        raise ValueError("Eventos Sinnoh sem handler no pacote: " + ", ".join(sorted(missing)[:12]))
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
    proof = {"map_ids":ids, "map_symbols":dict(sorted(mapping.items())), "base":base, "start":start,
             "arrival":[town_id,*arrival], "agent":[town_id,*agent]}
    shared.preserve_base(game, proof, files)
    # Copy only namespaced regional resources and reviewed regional additions.
    for p, raw in outputs.items():
        if shared.ASSET.fullmatch(p) or p in (shared.PLUGIN, shared.META):
            if (game / p).exists() or (game / p).is_symlink():
                raise ValueError("Regional asset collision: "+p)
            files[p] = raw
    review = {}
    for p in sorted(shared.MAP_PBS & outputs.keys()):
        old = shared.safe_file(game,p).read_bytes()
        shared.preserve_map_pbs(p,old,outputs[p],set(ids))
        files[p] = outputs[p]
        base[p] = shared.sha(old)
    proof["connection_rows"] = [list(row) for row in shared.parse_connections(
        files[shared.PBS_CONNECTIONS][len(shared.safe_file(game,shared.PBS_CONNECTIONS).read_bytes()):])]
    unhandled = sorted(p for p in outputs if p not in files and p not in review)
    proof.update(schema=1, profile="BLUE_SINNOH_SHARED_CANDIDATE_V1",
                 campaign=report.get("campaign",{}),
                 files={p:shared.sha(raw) for p,raw in files.items()},
                 review_files={p:shared.sha(raw) for p,raw in review.items()},
                 excluded_outputs=unhandled,
                 approvals={k:False for k in ("map_ids","asset_rights","connected_world",
                                                "windows_travel","joiplay_travel","android_distribution")},
                 runtime_install_enabled=False, native_verified=False,
                 blockers=["native compiler and full Windows and JoiPlay travel receipts",
                           "asset distribution approval"])
    return files, review, proof


def prepare(project, game):
    project, game = project.resolve(), game.resolve()
    shared.assert_no_legacy_sinnoh_shared(game)
    folder = project / CANDIDATE
    if folder.exists() or folder.is_symlink() or folder.parent.is_symlink():
        raise ValueError("Candidate exists; preserve it or move it before preparing another")
    from sinnoh_source_download import ensure_sources
    from install_sinnoh_experimental_windows import build_files
    ensure_sources(project)
    outputs, report = build_files(game, project, shared_runtime=True)
    actual = set(report["mapids"].values())
    reserved = set(shared.SHARED_IDS)
    if actual != reserved:
        raise ValueError("Reserva de Sinnoh incompleta. Ausentes: " + str(sorted(reserved-actual)) +
                         ". Extras: " + str(sorted(actual-reserved)) +
                         ". Campanha: " + json.dumps(report["campaign"],ensure_ascii=False))
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
    parser.add_argument("--base-game", type=Path, help="Existing shared game to read without changes")
    args = parser.parse_args()
    result = prepare(args.project,args.base_game or args.project/"game")
    print("SINNOH_SHARED_WORLD_CANDIDATE", json.dumps({
        "map_count":len(result["map_ids"]), "start":result["start"],
        "arrival":result["arrival"], "agent":result["agent"],
        "connection_count":len(result["connection_rows"]),
        "runtime_install_enabled":result["runtime_install_enabled"],
    }),flush=True)
