"""Prepare Johto's SOURCE map connections for an isolated game copy.

Each line uses the real source PBS format:
MapID,Edge,Offset,MapID,Edge,Offset
Never assigns old Kanto IDs, modifies game/PBS, certifies passability or
claims that missing Johto interiors / Route 29 to Cherrygrove exist.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

from audit_johto import ROOT, checksum
from verify_johto import inspect

GRAPH_PATH = ROOT / "data/regions/johto-v1-map-connections.json"
SOURCE_MANIFEST = ROOT / "data/regions/johto-source.json"
OUTPUT = ROOT / ".blue-work/johto-connections-preview.txt"
DIRECTIONS = {"North", "South", "East", "West"}
LINE = re.compile(r"\d+,(?:North|South|East|West),\d+,\d+,(?:North|South|East|West),\d+\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")


def compile_connections(graph: dict, source: dict, stage: dict) -> tuple[str, dict]:
    """Pure conversion; refuse incomplete or contaminated source provenance."""
    pinned = source.get("source", {}).get("archive_sha256")
    if (not isinstance(pinned, str) or not SHA256.fullmatch(pinned)
            or graph.get("source_archive_sha256") != pinned
            or stage.get("source_archive_sha256") != pinned):
        raise ValueError("Johto source/stage/connections SHA-256 mismatch")
    if (graph.get("schema"), graph.get("region"), graph.get("can_install")) != (
            1, "JOHTO", False):
        raise ValueError("Johto connections must be uninstalled source references")
    if (stage.get("schema"), stage.get("region"), stage.get("status"),
            stage.get("can_install"), stage.get("not_playable")) != (
            1, "JOHTO", "GEOMETRY_PREVIEW_ONLY", False, True):
        raise ValueError("Only a Johto geometry preview may generate connections")
    allowed = source.get("maps")
    if not isinstance(allowed, dict) or not allowed:
        raise ValueError("No audited Johto symbols")
    rows = stage.get("maps")
    if not isinstance(rows, list):
        raise ValueError("Missing verified preview maps")
    remap = {}
    used_destinations = set()
    for row in rows:
        sid, did, symbol = row.get("source_id"), row.get("destination_id"), row.get("symbol")
        if sid is None:  # author-built local interior, not a foreign source MapID
            continue
        if (type(sid) is not int or type(did) is not int or
                not 600 <= did <= 999 or
                symbol != allowed.get(str(sid)) or
                sid in remap or did in used_destinations or
                row.get("events_imported") != 0):
            raise ValueError("Untrusted/duplicate map row in Johto stage")
        remap[sid] = did
        used_destinations.add(did)
    edges = graph.get("connections")
    if not isinstance(edges, list) or not edges:
        raise ValueError("No map connections supplied")
    produced = []
    seen = set()
    for edge in edges:
        if not isinstance(edge, dict):
            raise ValueError("Invalid Johto edge")
        sid, tid = edge.get("from_id"), edge.get("to_id")
        side_a, side_b = edge.get("from_edge"), edge.get("to_edge")
        offset_a, offset_b = edge.get("from_offset"), edge.get("to_offset")
        if (type(sid) is not int or type(tid) is not int or
                sid == tid or sid not in remap or tid not in remap or
                side_a not in DIRECTIONS or side_b not in DIRECTIONS or
                type(offset_a) is not int or type(offset_b) is not int or
                offset_a < 0 or offset_b < 0):
            raise ValueError("Edge references absent/non-Johto map or has invalid position")
        # Corner cases in Essentials permit large offsets, which must not be
        # guessed as tile positions or independently clamped.
        if not ((side_a, side_b) in (("North", "South"), ("South", "North"),
                                         ("East", "West"), ("West", "East"))):
            raise ValueError("Map edges must face opposite sides")
        key = (sid, side_a, offset_a, tid, side_b, offset_b)
        reverse = (tid, side_b, offset_b, sid, side_a, offset_a)
        if key in seen or reverse in seen:
            raise ValueError("Duplicate/reversed Johto border connection")
        seen.add(key)
        output_line = f"{remap[sid]},{side_a},{offset_a},{remap[tid]},{side_b},{offset_b}"
        if not LINE.fullmatch(output_line):
            raise ValueError("Unsafe compiled connection format")
        produced.append(output_line)
    if not any({e.get("from_id"), e.get("to_id")} == {79, 104} for e in edges):
        raise ValueError("Johto pilot requires the real New Bark / Route 29 edge")
    result = {
        "schema": 1, "region": "JOHTO", "status": "COMPILED_CONNECTIONS_PREVIEW_ONLY",
        "source_archive_sha256": pinned, "source_count": len(edges),
        "compiled_count": len(produced), "can_install": False,
        "tested_in_game": False,
        "missing_required": ["JOHTO_ROUTE_29_TO_CHERRYGROVE",
                             "JOHTO_NEW_BARK_PLAYER_HOME_AND_LAB_WARPS"],
    }
    return ("\n".join(produced) + "\n", result)


def merge_pbs(native: bytes | None, additions: str) -> bytes:
    """For experimental copy ONLY. Original PBS lines retain byte contents."""
    if native is not None:
        if b"\0" in native or len(native) > 2_000_000:
            raise ValueError("Unsafe pre-existing map_connections.txt")
        if b"\r" in native and b"\r\n" not in native:
            raise ValueError("Unusual native PBS newline format")
        try:
            native.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise ValueError("Native connections must be UTF-8")
    else:
        native = b""
    prior = set()
    for line in native.decode("utf-8-sig").splitlines():
        trimmed = line.split("#", 1)[0].strip()
        if trimmed and LINE.fullmatch(trimmed.replace(" ", "")):
            prior.add(trimmed.replace(" ", ""))
    lines = [x.strip() for x in additions.splitlines() if x.strip()]
    if not lines or any(not LINE.fullmatch(x) for x in lines) or len(lines) != len(set(lines)):
        raise ValueError("Invalid generated Johto PBS lines")
    if prior.intersection(lines):
        raise ValueError("Johto connections already present in native PBS")
    separator = b"" if not native or native.endswith(b"\n") else b"\r\n" if b"\r\n" in native else b"\n"
    line_end = "\r\n" if b"\r\n" in native else "\n"
    appendix = ("# Blue Johto - experimental audited geometry only" + line_end +
                line_end.join(lines) + line_end).encode("utf-8")
    return native + separator + appendix


def build(preview: Path, game: Path, graph: dict, source: dict,
          *, root: Path = ROOT) -> tuple[str, dict]:
    # Check against the native base rather than believing a local JSON stage.
    proof = inspect(preview, game, root=root)
    if proof.get("status") != "STRUCTURAL_PREVIEW_VALIDATED_NOT_PLAYABLE":
        raise ValueError("Johto geometry preview did not pass native-integrity checks")
    stage = json.loads((preview / "johto-stage.json").read_text(encoding="utf-8"))
    return compile_connections(graph, source, stage)


def write_preview(output: Path, compiled: str, *, root: Path = ROOT) -> None:
    work = (root.resolve() / ".blue-work").resolve()
    dest = output.absolute()
    if (dest.is_symlink() or dest.exists() or dest.resolve() == work or
            not dest.resolve().is_relative_to(work)):
        raise ValueError("Only a NEW output under .blue-work/ is permitted")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".johto-edges-", dir=dest.parent) as temp:
        written = Path(temp) / "connections.txt"
        written.write_text(compiled, encoding="utf-8")
        if dest.exists() or dest.is_symlink():
            raise ValueError("Johto connections already exist")
        written.rename(dest)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--preview", type=Path, default=ROOT / ".blue-work/johto-staging")
    p.add_argument("--game", type=Path, default=ROOT / "game")
    p.add_argument("--graph", type=Path, default=GRAPH_PATH)
    p.add_argument("--source", type=Path, default=SOURCE_MANIFEST)
    p.add_argument("--output", type=Path, default=OUTPUT)
    args = p.parse_args(argv)
    try:
        source = json.loads(args.source.read_text(encoding="utf-8"))
        graph = json.loads(args.graph.read_text(encoding="utf-8"))
        result, stats = build(args.preview, args.game, graph, source)
        write_preview(args.output, result)
    except (OSError, ValueError, TypeError, KeyError) as e:
        print("[JOHTO][BLOQUEADO] " + str(e), file=sys.stderr)
        return 2
    print(f"[JOHTO] {stats['compiled_count']} conexoes remapeadas em preview ISOLADO.")
    print("[JOHTO] Ainda NAO jogavel: falta New Bark casa/lab, Route 29/Cherrygrove e testes reais.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
