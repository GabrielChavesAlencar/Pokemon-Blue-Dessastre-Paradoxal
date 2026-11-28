"""Seed a clean Git recipe cache from a verified archive in the same Windows CI job.

Only the unchanged, pinned RAR is copied. No network calls, extracted content,
game files, Actions caches or artifacts are involved.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "regions"))
from audit import KANTO, json_file
from ensure_source import RELATIVE_ARCHIVE, RELATIVE_SOURCE, sha256


def direct_directory(path: Path) -> Path:
    path = path.absolute()
    if path.resolve(strict=True) != path or not path.is_dir():
        raise ValueError(f"Expected a direct CI directory: {path}")
    return path


def refuse_existing(path: Path) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise ValueError(f"Refusing to overwrite an existing CI cache path: {path}")


def seed_archive(workspace: Path, source: Path, target: Path, expected: str) -> Path:
    """The CLI accepts only the repository's pinned digest and Windows CI roots."""
    workspace = direct_directory(workspace)
    source = direct_directory(source)
    target = direct_directory(target)
    if (source == target or not source.is_relative_to(workspace) or
            not target.is_relative_to(workspace)):
        raise ValueError("Source and target must be different paths within the same CI workspace")
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("Invalid pinned FRLG digest")
    donor = source / RELATIVE_ARCHIVE
    if donor.resolve(strict=True) != donor or not donor.is_file() or sha256(donor) != expected:
        raise ValueError("The local FRLG archive does not match the pinned SHA-256")
    out = target / RELATIVE_ARCHIVE
    if out.resolve() != out:
        raise ValueError("The destination FRLG cache is indirect")
    for path in (target / RELATIVE_SOURCE, out, out.with_suffix(".rar.part")):
        refuse_existing(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent, prefix=".frlg-ci-copy-") as cache:
        staged = Path(cache) / out.name
        with donor.open("rb") as data, staged.open("xb") as copy:
            shutil.copyfileobj(data, copy, length=1024 * 1024)
        if sha256(staged) != expected:
            raise ValueError("The staged FRLG copy does not match the pinned SHA-256")
        # Only link our verified temporary file; this publishes atomically
        # without ever replacing an existing destination or linking the donor.
        os.link(staged, out)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    if os.name != "nt" or os.getenv("GITHUB_ACTIONS") != "true" or not os.getenv("GITHUB_WORKSPACE"):
        parser.error("This helper is limited to the disposable Windows GitHub Actions checkout.")
    try:
        seed_archive(Path(os.environ["GITHUB_WORKSPACE"]), args.source, args.target,
                     json_file(KANTO)["sha256"])
    except (OSError, ValueError) as error:
        parser.exit(1, f"Private FRLG cache rejected: {error}\n")
    print("KANTO_K06_FRLG_REUSED_LOCAL_ARCHIVE_OK")


if __name__ == "__main__":
    main()
