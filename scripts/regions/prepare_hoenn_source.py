#!/usr/bin/env python3
"""Select the map resources from a LOCAL Hoenn World Project ZIP.

Read-only by default. --extract writes into ignored .blue-work/hoenn-source/
only. This script NEVER installs assets into game/, pushes donor assets to Git,
loads RXDATA through Ruby Marshal, or executes any donor project code.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
SOURCE_NAME = "The Pokémon World Project - Hoenn"
STAGING_ROOT = ROOT / ".blue-work" / "hoenn-source"
DATA_NAMES = {"MapInfos.rxdata", "Tilesets.rxdata", "CommonEvents.rxdata",
              "Animations.rxdata"}
IMAGE_EXTS = {".png", ".gif", ".bmp", ".jpg", ".jpeg", ".webp"}
AUDIO_EXTS = {".ogg", ".mp3", ".wav", ".mid", ".midi", ".flac"}
PBS_EXTS = {".txt", ".json", ".csv"}
MAX_FILES = 60000
MAX_UNCOMPRESSED = 12 * 1024**3
MAX_INDIVIDUAL = 1024**3


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_hoenn_path(raw_name: str) -> PurePosixPath | None:
    """Locate Hoenn inside ZIP with optional parent directory, no path escape."""
    if (not isinstance(raw_name, str) or not raw_name or
            "\x00" in raw_name or "\\" in raw_name or raw_name.startswith("/")):
        raise ValueError(f"Unsafe ZIP member name: {raw_name!r}")
    path = PurePosixPath(raw_name)
    parts = path.parts
    if any(part in ("..", ".") or ":" in part for part in parts):
        raise ValueError(f"Unsafe ZIP member path: {raw_name!r}")
    if SOURCE_NAME in parts:
        parts = parts[parts.index(SOURCE_NAME) + 1:]
    elif len(parts) >= 1 and parts[0] in {"Data", "Graphics", "PBS", "Audio"}:
        pass  # A ZIP containing exactly the Hoenn project root.
    else:
        return None
    if not parts:
        return None
    return PurePosixPath(*parts)


def category(path: PurePosixPath, include_audio: bool = False) -> str | None:
    parts = path.parts
    if len(parts) < 2:
        return None
    if parts[0] == "Data" and len(parts) == 2:
        if re.fullmatch(r"Map[0-9]{1,5}\.rxdata", parts[1], re.IGNORECASE):
            return "maps"
        if parts[1] in DATA_NAMES:
            return "map_dependencies"
    if parts[0] == "Graphics" and path.suffix.lower() in IMAGE_EXTS:
        return "graphics"
    if parts[0] == "PBS" and path.suffix.lower() in PBS_EXTS:
        return "pbs_reference"
    if (include_audio and parts[0] == "Audio" and
            path.suffix.lower() in AUDIO_EXTS):
        return "audio_reference"
    return None


def is_symlink(info: zipfile.ZipInfo) -> bool:
    return stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK


def select_members(archive: zipfile.ZipFile,
                   include_audio: bool = False) -> list[dict]:
    """Fail closed for unsafe paths/collisions before touching the disk."""
    members = archive.infolist()
    if len(members) > MAX_FILES:
        raise ValueError(f"ZIP has too many members: {len(members)}")
    selected: list[dict] = []
    seen: set[str] = set()
    cumulative = 0
    for info in members:
        if is_symlink(info):
            raise ValueError(f"Refusing ZIP symbolic link: {info.filename}")
        path = relative_hoenn_path(info.filename)
        if not path or info.is_dir():
            continue
        kind = category(path, include_audio)
        if not kind:
            continue
        if info.flag_bits & 1:
            raise ValueError(f"Encrypted ZIP member: {info.filename}")
        if info.file_size > MAX_INDIVIDUAL:
            raise ValueError(f"Oversized resource: {info.filename}")
        cumulative += info.file_size
        if cumulative > MAX_UNCOMPRESSED:
            raise ValueError("ZIP exceeds permitted uncompressed resource size")
        key = str(path).casefold()
        if key in seen:
            raise ValueError(f"Duplicate Hoenn destination path: {path}")
        seen.add(key)
        selected.append({"path": path.as_posix(), "source": info.filename,
                         "kind": kind, "size": info.file_size,
                         "crc32": f"{info.CRC:08x}", "zip_info": info})
    if not any(row["path"] == "Data/MapInfos.rxdata" for row in selected):
        raise ValueError("Hoenn MapInfos.rxdata missing from ZIP")
    if not any(row["path"] == "Data/Tilesets.rxdata" for row in selected):
        raise ValueError("Hoenn Tilesets.rxdata missing from ZIP")
    if not any(row["kind"] == "maps" for row in selected):
        raise ValueError("No Hoenn Data/MapNNN.rxdata found")
    return sorted(selected, key=lambda row: row["path"])


def safe_stage(root: Path, digest: str) -> Path:
    """Staging is always a child of the repo's Git-ignored .blue-work."""
    stage_root = root / ".blue-work" / "hoenn-source"
    stage = stage_root / digest[:16]
    for element in (root / ".blue-work", stage_root, stage):
        if element.is_symlink():
            raise ValueError(f"Refusing symlink staging directory: {element}")
    if not stage.resolve().is_relative_to(root.resolve()):
        raise ValueError("Staging directory escapes the project root")
    return stage


def extract_selected(archive: zipfile.ZipFile, rows: list[dict],
                     stage: Path) -> tuple[int, int]:
    """Idempotent copy, never overwrite an existing different local file."""
    stage.mkdir(parents=True, exist_ok=True)
    written = 0
    reused = 0
    for row in rows:
        rel = PurePosixPath(row["path"])
        target = stage.joinpath(*rel.parts)
        parent = target.parent
        cursor = stage
        for part in rel.parts[:-1]:
            cursor /= part
            if cursor.is_symlink():
                raise ValueError(f"Unsafe symlink directory: {cursor}")
        if target.is_symlink():
            raise ValueError(f"Unsafe symlink target: {target}")
        parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            # Re-read source to ensure ZIP and existing file match exactly.
            h = hashlib.sha256()
            with archive.open(row["zip_info"]) as src:
                for chunk in iter(lambda: src.read(1024 * 1024), b""):
                    h.update(chunk)
            if sha256_file(target) != h.hexdigest():
                raise ValueError(f"Different file already exists: {target}")
            row["sha256"] = h.hexdigest()
            row["copy_status"] = "already_identical"
            reused += 1
            continue
        h = hashlib.sha256()
        try:
            with archive.open(row["zip_info"]) as src, target.open("xb") as dst:
                for chunk in iter(lambda: src.read(1024 * 1024), b""):
                    dst.write(chunk)
                    h.update(chunk)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        row["sha256"] = h.hexdigest()
        row["copy_status"] = "written"
        written += 1
    return written, reused


def inspect_zip(archive_path: Path, *, include_audio: bool = False,
                extract: bool = False, root: Path = ROOT) -> dict:
    if not archive_path.is_file():
        raise FileNotFoundError(f"Hoenn ZIP not found: {archive_path}")
    digest = sha256_file(archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        rows = select_members(archive, include_audio=include_audio)
        stage = safe_stage(root, digest)
        written = reused = 0
        if extract:
            written, reused = extract_selected(archive, rows, stage)
        kinds = dict(collections.Counter(row["kind"] for row in rows))
        serial_rows = [{key: value for key, value in row.items()
                        if key != "zip_info"} for row in rows]
        result = {
            "schema": 1,
            "region": "HOENN",
            "source_name": SOURCE_NAME,
            "archive_sha256": digest,
            "license_status": "UNVERIFIED_FOR_PUBLIC_REDISTRIBUTION",
            "public_git_upload_allowed": False,
            "mode": "LOCAL_STAGING" if extract else "READ_ONLY_AUDIT",
            "local_stage": str(stage.relative_to(root)),
            "source_maps": kinds.get("maps", 0),
            "categories": kinds,
            "selected_bytes": sum(row["size"] for row in rows),
            "written": written,
            "reused": reused,
            "files": serial_rows,
            "warning": (
                "Reference files only: do not copy MapInfos/Tilesets/CommonEvents/"
                "PBS/Audio directly into game/. Use separate ID remapping, "
                "per-asset rights checks and a verified transactional installer."
            ),
        }
        if extract:
            out = stage / "inventory.json"
            # Inventory is tool-created metadata, not a donor asset.
            tmp = stage / "inventory.json.tmp"
            if tmp.is_symlink() or out.is_symlink():
                raise ValueError("Unsafe inventory path (symlink)")
            with tmp.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
            tmp.replace(out)
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True,
                        help="ZIP containing The Pokémon World Project - Hoenn")
    parser.add_argument("--extract", action="store_true",
                        help="Prepare files ONLY in .blue-work/hoenn-source/")
    parser.add_argument("--with-audio", action="store_true",
                        help="Also stage third-party Audio as local REFERENCE ONLY")
    args = parser.parse_args(argv)
    try:
        result = inspect_zip(args.archive, include_audio=args.with_audio,
                             extract=args.extract)
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as error:
        print(f"HOENN_SOURCE_BLOCKED: {error}", file=sys.stderr)
        return 2
    print(f"Mode: {result['mode']}")
    print(f"Archive SHA-256: {result['archive_sha256']}")
    print(f"Hoenn map files: {result['source_maps']}")
    print(f"Selected categories: {result['categories']}")
    print(f"Staging location: {result['local_stage']}")
    print(f"Written: {result['written']}; already identical: {result['reused']}")
    print("IMPORTANT: no imported maps or rights approved for public GitHub.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
