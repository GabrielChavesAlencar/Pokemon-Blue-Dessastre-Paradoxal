"""Read-only Johto RMXP source audit. Never installs or executes third-party events.

Only serialized RPG Maker map DATA is inspected, using the existing inert
server.ruby_marshal reader. Output is confined to .blue-work/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from server.ruby_marshal import RubyObject, loads, text

DEFAULT_MANIFEST = ROOT / "data/regions/johto-source.json"
DEFAULT_SOURCE = ROOT / ".blue-work/johto-source"
DEFAULT_REPORT = ROOT / ".blue-work/johto-audit.json"
MAP_RE = re.compile(r"Map([0-9]+)\.rxdata", re.I)
MAX_RMXP_BYTES = 32_000_000
REQUIRED_NAMES = ("New Bark", "Cherrygrove", "Violet", "Azalea",
                  "Goldenrod", "Ecruteak", "Olivine", "Cianwood",
                  "Mahogany", "Blackthorn")


def checksum(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def read_map_data(path: Path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Invalid or linked source file: " + str(path))
    if path.stat().st_size > MAX_RMXP_BYTES:
        raise ValueError("Source RMXP file exceeds reader limit: " + path.name)
    return loads(path.read_bytes())


def project_data(source: Path) -> Path:
    source = source.resolve()
    if source == (ROOT / "game").resolve() or source == ROOT.resolve():
        raise ValueError("Johto source cannot be game/ or the project root")
    if not source.is_dir() or source.is_symlink():
        raise FileNotFoundError("Extract the Johto map pack under .blue-work/johto-source first")
    candidates = [source / "Data"]
    candidates.extend(p / "Data" for p in source.iterdir() if p.is_dir() and not p.is_symlink())
    valid = [data for data in candidates
             if data.is_dir() and not data.is_symlink()
             and (data / "MapInfos.rxdata").is_file()
             and (data / "Tilesets.rxdata").is_file()]
    if len(valid) != 1:
        raise ValueError("Expected one RMXP Data directory with MapInfos and Tilesets, found %d" % len(valid))
    return valid[0]


def map_files(data: Path) -> dict[int, Path]:
    maps = {}
    for file in data.iterdir():
        found = MAP_RE.fullmatch(file.name)
        if not found:
            continue
        map_id = int(found.group(1))
        if map_id <= 0 or map_id in maps or file.is_symlink():
            raise ValueError("Duplicate/unsafe source map ID: " + str(map_id))
        maps[map_id] = file
    if not maps:
        raise ValueError("No RMXP MapNNN.rxdata files in source")
    return maps


def attributes(item) -> dict:
    return item.attrs if isinstance(item, RubyObject) else {}


def source_map_audit(data: Path) -> dict:
    infos = read_map_data(data / "MapInfos.rxdata")
    tilesets = read_map_data(data / "Tilesets.rxdata")
    if not isinstance(infos, dict) or not isinstance(tilesets, (list, dict)):
        raise ValueError("Unexpected MapInfos or Tilesets RMXP data")
    files = map_files(data)
    tile_ids = (set(range(len(tilesets))) if isinstance(tilesets, list)
                else set(tilesets))
    maps = []
    transfer_ids = set()
    unsafe_script_commands = 0
    all_tilesets = set()
    for source_id, file in sorted(files.items()):
        obj = read_map_data(file)
        props = attributes(obj)
        if not isinstance(obj, RubyObject) or obj.name != "RPG::Map":
            raise ValueError("Expected RPG::Map in " + file.name)
        width, height, tileset_id = (props.get("@width"), props.get("@height"),
                                     props.get("@tileset_id"))
        events = props.get("@events", {})
        if not all(isinstance(v, int) and v > 0 for v in (width, height)):
            raise ValueError("Invalid map dimensions: " + file.name)
        if not isinstance(tileset_id, int) or tileset_id <= 0:
            raise ValueError("Invalid map tileset: " + file.name)
        if not isinstance(events, dict):
            raise ValueError("Invalid map events dictionary: " + file.name)
        all_tilesets.add(tileset_id)
        pages = 0
        scripts = 0
        transfers = set()
        for event in events.values():
            for page in attributes(event).get("@pages", []):
                pages += 1
                for command in attributes(page).get("@list", []):
                    fields = attributes(command)
                    code = fields.get("@code")
                    parameters = fields.get("@parameters", [])
                    if code in (355, 655):  # Script/continuation: never run.
                        scripts += 1
                    if (code == 201 and isinstance(parameters, list)
                            and len(parameters) > 1 and parameters[0] == 0
                            and isinstance(parameters[1], int)):
                        transfers.add(parameters[1])
        transfer_ids.update(transfers)
        entry = attributes(infos.get(source_id))
        maps.append({
            "source_id": source_id,
            "name": text(entry.get("@name", b"")).strip() or "(unnamed)",
            "width": width, "height": height,
            "tileset_id": tileset_id,
            "events": len(events), "event_pages": pages,
            "untrusted_script_commands": scripts,
            "transfer_targets": sorted(transfers),
            "sha256": checksum(file)
        })
        unsafe_script_commands += scripts
    names = [entry["name"].casefold() for entry in maps]
    return {
        "map_count": len(maps),
        "tilesets_referenced": sorted(all_tilesets),
        "missing_tileset_ids": sorted(all_tilesets - tile_ids),
        "orphan_map_files": sorted(set(files) - set(infos)),
        "missing_map_files": sorted(set(infos) - set(files)),
        "unresolved_transfer_ids": sorted(transfer_ids - set(files)),
        "named_area_candidates": {
            name: [row["source_id"] for row in maps if name.casefold() in row["name"].casefold()]
            for name in REQUIRED_NAMES
        },
        "untrusted_script_commands": unsafe_script_commands,
        "mapinfos_sha256": checksum(data / "MapInfos.rxdata"),
        "tilesets_sha256": checksum(data / "Tilesets.rxdata"),
        "maps": maps
    }


def game_snapshot(game: Path) -> dict:
    """Optional read-only baseline. All Game.exe/saves/data remain untouched."""
    if not game.exists():
        return {"present": False, "existing_ids": [], "protected_hashes": {}}
    data = game / "Data"
    if not data.is_dir():
        raise ValueError("Game directory lacks Data/: " + str(game))
    files = map_files(data)
    registered = set()
    mapinfos = data / "MapInfos.rxdata"
    if mapinfos.is_file():
        infos = read_map_data(mapinfos)
        if not isinstance(infos, dict) or not all(type(n) is int and n > 0 for n in infos):
            raise ValueError("Invalid native MapInfos; refusing map ID collision assumptions")
        registered = set(infos)
    protected = {}
    for filename in ("MapInfos.rxdata", "Tilesets.rxdata", "Scripts.rxdata",
                     "System.rxdata", "blue-kanto-install.json", "blue-kanto-music.txt"):
        path = data / filename
        if path.is_file():
            protected["Data/" + filename] = checksum(path)
    return {"present": True, "existing_ids": sorted(files),
            "registered_ids": sorted(registered),
            "protected_hashes": protected}


def audit(source: Path, manifest_path: Path = DEFAULT_MANIFEST,
          game: Path | None = None, archive: Path | None = None) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if (manifest.get("schema"), manifest.get("region"), manifest.get("import_enabled")) != (1, "JOHTO", False):
        raise ValueError("Johto audit requires schema 1 and import disabled")
    data = project_data(source)
    result = source_map_audit(data)
    snapshot = game_snapshot(game) if game is not None else {
        "present": False, "existing_ids": [], "protected_hashes": {}
    }
    actual_archive_sha = checksum(archive) if archive is not None else None
    expected_archive_sha = manifest["source"].get("archive_sha256")
    archive_verified = bool(expected_archive_sha and actual_archive_sha == expected_archive_sha)
    result.update({
        "schema": 1, "region": "JOHTO",
        "mode": "READ_ONLY_NO_INSTALL",
        "source_pack": manifest["source"]["name"],
        "source_archive_sha256": actual_archive_sha,
        "archive_hash_pinned_and_verified": archive_verified,
        "source_rights_still_require_review": True,
        "game": snapshot,
        "map_id_overlap_before_remapping": sorted(set(snapshot["existing_ids"])
                                                  & {r["source_id"] for r in result["maps"]}),
        "can_install": False,
        "warnings": ["Third-party Ruby event scripts were counted, never executed",
                     "Do not copy MapInfos.rxdata, Tilesets.rxdata or source IDs into game/",
                     "Source map pack is not a completed Johto campaign",
                     "Audio and asset rights must be verified separately",
                     "Create stable symbolic IDs and map remaps before staging"]
    })
    if expected_archive_sha and archive is not None and not archive_verified:
        raise ValueError("Johto source archive SHA-256 does not match pinned manifest")
    return result


def write_report(output: Path, report: dict) -> None:
    output = output.absolute()
    work = (ROOT / ".blue-work").resolve()
    if output.is_symlink() or not output.resolve().is_relative_to(work) or output.resolve() == work:
        raise ValueError("Audit report must stay inside .blue-work/")
    if output.parent.is_symlink():
        raise ValueError("Audit report directory cannot be a symlink")
    encoded = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if output.exists():
        if output.read_bytes() != encoded:
            raise FileExistsError("Audit report exists with different contents; choose another --output")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(encoded)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Johto RMXP source audit; NEVER imports game assets")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--game", type=Path, default=None)
    parser.add_argument("--archive", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    try:
        report = audit(args.source, args.manifest, args.game, args.archive)
        write_report(args.output, report)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("[JOHTO][BLOQUEADO] " + str(error), file=sys.stderr)
        return 2
    print("[JOHTO] Auditados %d mapas (somente leitura); %d scripts de evento não executados."
          % (report["map_count"], report["untrusted_script_commands"]))
    print("[JOHTO] Instalacao BLOQUEADA ate remapeamento, licencas e teste isolado.")
    print("[JOHTO] Relatorio:", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
