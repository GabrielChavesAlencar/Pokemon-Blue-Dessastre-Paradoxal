"""Safely unpack an ORIGINAL Johto RMXP map pack into ignored .blue-work/.

This never fetches third-party media, extracts scripts, executes code or touches
game/. It supports ZIP only; RAR packages must be unpacked manually, and their
contents audited with audit_johto.py before anything is staged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from audit_johto import ROOT

FILE_RE = re.compile(
    r"(?:Data/(?:Map[0-9]{1,4}|MapInfos|Tilesets)\.rxdata"
    r"|Graphics/(?:Tilesets|Autotiles)/[^/]{1,130}\.png)$",
    flags=re.I,
)
MAX_FILES = 5000
MAX_TOTAL = 1_000_000_000
MAX_ENTRY = 32_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for block in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized_name(info: zipfile.ZipInfo) -> str:
    name = info.filename.replace("\\", "/")
    parts = PurePosixPath(name).parts
    if (not parts or name.startswith("/") or
            ":" in parts[0] or
            any(part in (".", "..", "") for part in parts) or
            "\x00" in name or "\\" in name):
        raise ValueError("Unsafe path inside Johto archive")
    kind = (info.external_attr >> 16) & 0o170000
    if kind == stat.S_IFLNK:
        raise ValueError("Symlinks are not permitted in Johto archive")
    if info.flag_bits & 0x1:
        raise ValueError("Encrypted ZIP members are not permitted")
    return "/".join(parts).rstrip("/")


def selected_members(package: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    info = package.infolist()
    if len(info) > MAX_FILES:
        raise ValueError("Excessive member count in Johto archive")
    candidates = {}
    names = set()
    for member in info:
        name = normalized_name(member)
        if not name or member.is_dir():
            continue
        key = name.casefold()
        if key in names:
            raise ValueError("Duplicate archive path, including case-only collision: " + name)
        names.add(key)
        if member.file_size > MAX_ENTRY:
            raise ValueError("Unsafe oversized Johto archive member: " + name)
        parts = name.split("/")
        for i in range(len(parts)):
            suffix = "/".join(parts[i:])
            if not FILE_RE.fullmatch(suffix):
                continue
            # Determine one consistent project root before extracting.
            prefix = "/".join(parts[:i])
            candidates.setdefault(prefix, {})[suffix] = member
            break
    roots = [prefix for prefix, entries in candidates.items()
             if ("Data/MapInfos.rxdata" in entries and "Data/Tilesets.rxdata" in entries
                 and any(re.fullmatch(r"Data/Map[0-9]{1,4}\.rxdata", item)
                         for item in entries))]
    if len(roots) != 1:
        raise ValueError("Archive must contain ONE RMXP project with MapInfos, Tilesets and maps")
    chosen = candidates[roots[0]]
    if sum(x.file_size for x in chosen.values()) > MAX_TOTAL:
        raise ValueError("Johto map contents exceed archive extraction limit")
    return chosen


def prepare(archive: Path, output: Path, *, root: Path = ROOT) -> dict:
    root = root.resolve()
    work = root / ".blue-work"
    if work.is_symlink():
        raise ValueError("Refusing symlinked .blue-work root")
    work = work.resolve()
    archive = archive.resolve()
    output = output.absolute()
    if (not archive.is_relative_to(work) or
            not output.resolve().is_relative_to(work) or output.resolve() == work or
            output.exists() or output.is_symlink() or
            archive.is_relative_to(output.resolve())):
        raise ValueError("Johto source and NEW output must both be inside .blue-work/")
    if archive.suffix.lower() != ".zip":
        raise ValueError("Only ZIP supported: extract RAR locally and audit that folder")
    if not archive.is_file() or archive.is_symlink():
        raise FileNotFoundError("Local Johto archive not found")
    digest = sha256(archive)
    with zipfile.ZipFile(archive, "r") as package:
        members = selected_members(package)
        totals = {"files": 0, "maps": 0, "total_bytes": 0}
        hashes = {}
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".johto-source-", dir=output.parent) as folder:
            staged = Path(folder) / "project"
            for name, info in sorted(members.items()):
                destination = staged.joinpath(*name.split("/"))
                destination.parent.mkdir(parents=True, exist_ok=True)
                with package.open(info) as input_file:
                    # Checked uncompressed member size before extraction.
                    raw = input_file.read(MAX_ENTRY + 1)
                    if len(raw) != info.file_size or len(raw) > MAX_ENTRY:
                        raise ValueError("Corrupt or excessive ZIP member: " + name)
                if name.lower().endswith(".png"):
                    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
                        raise ValueError("Invalid Johto PNG: " + name)
                elif not raw.startswith(b"\x04\x08"):
                    raise ValueError("Invalid Johto RMXP data: " + name)
                destination.write_bytes(raw)
                hashes[name] = hashlib.sha256(raw).hexdigest()
                totals["files"] += 1
                totals["maps"] += int(bool(re.fullmatch(r"Data/Map[0-9]{1,4}\.rxdata", name)))
                totals["total_bytes"] += len(raw)
            report = {"schema": 1, "region": "JOHTO",
                      "status": "EXTRACTED_UNVERIFIED_DO_NOT_INSTALL",
                      "source_archive_sha256": digest,
                      "content": totals, "file_hashes": hashes,
                      "rights_verified": False, "maps_audited": False,
                      "game_files_changed": 0,
                      "note": "Only map data and PNG assets extracted; no rights or map IDs approved"}
            (staged / "johto-source-extraction.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
            if output.exists() or output.is_symlink():
                raise ValueError("Output already exists; refusing source overwrite")
            staged.rename(output)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / ".blue-work/johto-source/project")
    args = parser.parse_args(argv)
    try:
        result = prepare(args.archive, args.output)
    except (OSError, zipfile.BadZipFile, ValueError, RuntimeError) as error:
        print("[JOHTO][BLOQUEADO] " + str(error), file=sys.stderr)
        return 2
    print("[JOHTO] %d arquivos, %d mapas RMXP extraídos em área isolada." %
          (result["content"]["files"], result["content"]["maps"]))
    print("[JOHTO] SHA-256 do pacote:", result["source_archive_sha256"])
    print("[JOHTO] Ainda exige revisão de fontes, mapeamento, direitos e jogo real.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
