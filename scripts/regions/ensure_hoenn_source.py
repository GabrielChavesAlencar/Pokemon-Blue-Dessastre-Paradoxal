"""Download only the pinned Hoenn source files needed by the shared campaign.

This is run by Blue-Story.exe through auto_integrate_hoenn.py, NOT by Game.exe.
Every file is tied to a SHA-1 Git blob in the fixed public Git tree and is
cached under ignored .blue-work/. No repository ZIP, imported donor script or
donor executable is downloaded or executed; no assets are redistributed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from hoenn_qa_phase1 import (
    PINNED_TREE, check_source, check_tree, load_tree,
    PINNED_MAPINFOS_SHA256, PINNED_TILESETS_SHA256,
)
from pilot_hoenn import BGM, PNG, ROOT, SOURCE_MAPS, Source, UPSTREAM
from hoenn_audio import RECOVERY, bgm_source
from server.ruby_marshal import RubyObject, loads, text

PUBLIC_REPO = "SocomSeal/The-PMon-World-Project"
SOURCE_DIR = "The Pokémon World Project - Hoenn"
RAW_BASE = (
    f"https://raw.githubusercontent.com/{PUBLIC_REPO}/{UPSTREAM}/"
    f"{quote(SOURCE_DIR, safe='')}/"
)
INVENTORY = ROOT / ".blue-work/hoenn-tree-pinned.json"
STAGE = ROOT / ".blue-work/hoenn-source" / hashlib.sha256(
    PINNED_TREE.encode("ascii")).hexdigest()[:16]
MAX_BLOB_BYTES = 100 * 1024 * 1024
MAX_TOTAL_BYTES = 750 * 1024 * 1024
RETRIES = 3
CREDIT_TRACK = "Audio/BGM/ORAS Misc - Hall of Fame (The Hall of Fame).ogg"
BOSS_SPRITES = (
    "Graphics/Trainers/RSE_LEADER_Juan.png",
    "Graphics/Trainers/RSE_AQUALEADER_Archie.png",
    "Graphics/Trainers/RSE_CHAMPION_Wallace.png",
)


def safe_stage(root: Path) -> None:
    """Reject symlinks and unexpected paths before writing cached donor bytes."""
    root = root.resolve(strict=False)
    if not root.is_relative_to(ROOT.resolve()) or root == ROOT.resolve():
        raise ValueError("Cache de Hoenn fora da pasta de trabalho.")
    current = ROOT
    for part in root.relative_to(ROOT.resolve()).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Link simbólico no cache de Hoenn: {current}")


def sha_git(blob: bytes) -> str:
    return hashlib.sha1(f"blob {len(blob)}\0".encode("ascii") + blob).hexdigest()


def existing_verified(path: Path, expected: str, size: int) -> bool:
    if not path.is_file() or path.is_symlink() or path.stat().st_size != size:
        return False
    digest = hashlib.sha1(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise ValueError(f"Cache Hoenn alterado, não será sobrescrito: {path}")
    return True


class PinnedDownloader:
    def __init__(self, inventory: Path, stage: Path, *, opener=urlopen):
        self.inventory = Path(inventory)
        self.stage = Path(stage)
        self.opener = opener
        safe_stage(self.stage)
        tree = load_tree(self.inventory)
        check_tree(tree)
        self.blobs = {row["path"]: row for row in tree["tree"] if row.get("type") == "blob"}
        self.written = 0
        self.reused = 0
        self.bytes_downloaded = 0

    def _download(self, rel: str, dest: Path, expected: str, size: int) -> None:
        url = RAW_BASE + quote(rel, safe="/")
        error = None
        for attempt in range(RETRIES):
            temporary = None
            try:
                request = Request(url, headers={
                    "User-Agent": "Pokemon-Blue-Hoenn-Verified-Installer/1.0",
                    "Accept": "application/octet-stream",
                })
                dest.parent.mkdir(parents=True, exist_ok=True)
                fd, tmp = tempfile.mkstemp(prefix=".blue-hoenn-", dir=dest.parent)
                temporary = Path(tmp)
                digest = hashlib.sha1(f"blob {size}\0".encode("ascii"))
                read_bytes = 0
                with os.fdopen(fd, "wb") as out, self.opener(request, timeout=90) as response:
                    while True:
                        chunk = response.read(256 * 1024)
                        if not chunk:
                            break
                        read_bytes += len(chunk)
                        if read_bytes > size:
                            raise ValueError(f"Download excedeu o inventário: {rel}")
                        digest.update(chunk)
                        out.write(chunk)
                    out.flush()
                    os.fsync(out.fileno())
                if read_bytes != size or digest.hexdigest() != expected:
                    raise ValueError(f"Arquivo não corresponde à revisão fixa de Hoenn: {rel}")
                if dest.exists():
                    # Never replace a different user-edited or donor file.
                    if existing_verified(dest, expected, size):
                        temporary.unlink()
                        self.reused += 1
                        return
                    raise ValueError(f"Arquivo existente não pode ser substituído: {rel}")
                os.replace(temporary, dest)
                self.written += 1
                self.bytes_downloaded += read_bytes
                return
            except (HTTPError, URLError, OSError, TimeoutError) as exc:
                error = exc
                if attempt + 1 >= RETRIES:
                    break
                time.sleep(1 + attempt)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        raise RuntimeError(f"Download de Hoenn indisponível ({rel}): {error}")

    def file(self, rel: str, *, required: bool = True) -> Path | None:
        row = self.blobs.get(rel)
        if row is None:
            if required:
                raise ValueError(f"Arquivo Hoenn não existe na revisão fixa: {rel}")
            return None
        size = row.get("size")
        expected = row.get("sha")
        if (not isinstance(size, int) or not (0 < size <= MAX_BLOB_BYTES) or
                not isinstance(expected, str) or not re.fullmatch(r"[a-f0-9]{40}", expected)):
            raise ValueError(f"Arquivo Hoenn inválido no inventário: {rel}")
        if not re.fullmatch(r"(?:Data|PBS|Audio|Graphics)/[^\x00-\x1f]+", rel) or (
            "\\" in rel or ".." in Path(rel).parts or Path(rel).is_absolute()
        ):
            raise ValueError(f"Caminho Hoenn inválido: {rel}")
        target = self.stage / rel
        safe_stage(target.parent)
        if target.is_symlink():
            raise ValueError(f"Link simbólico não permitido: {rel}")
        if existing_verified(target, expected, size):
            self.reused += 1
        else:
            if self.bytes_downloaded + size > MAX_TOTAL_BYTES:
                raise ValueError("Fonte Hoenn ultrapassa limite de download de 750 MiB.")
            self._download(rel, target, expected, size)
        return target

    def collect(self) -> dict:
        # First obtain the minimum source to discover tileset dependencies.
        files = [
            "Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
            "PBS/map_connections.txt", "PBS/encounters.txt",
            *(f"Data/Map{mid:03}.rxdata" for mid in SOURCE_MAPS),
        ]
        for index, rel in enumerate(files, 1):
            self.file(rel)
            if index % 50 == 0:
                print(f"[HOENN AUTO] Mapas/arquivos originais: {index}/{len(files)}", flush=True)

        tiles_raw = (self.stage / "Data/Tilesets.rxdata").read_bytes()
        if hashlib.sha256(tiles_raw).hexdigest() != PINNED_TILESETS_SHA256:
            raise ValueError("Tilesets Hoenn não correspondem à origem auditada.")
        infos_raw = (self.stage / "Data/MapInfos.rxdata").read_bytes()
        if hashlib.sha256(infos_raw).hexdigest() != PINNED_MAPINFOS_SHA256:
            raise ValueError("MapInfos Hoenn não correspondem à origem auditada.")
        tiles = loads(tiles_raw)
        if not isinstance(tiles, list):
            raise ValueError("Tilesets Hoenn não puderam ser decodificados.")
        used = set()
        for mid in SOURCE_MAPS:
            world = loads((self.stage / f"Data/Map{mid:03}.rxdata").read_bytes())
            if not isinstance(world, RubyObject) or world.name != "RPG::Map":
                raise ValueError(f"Mapa de origem inválido: {mid}")
            used.add(world.attrs["@tileset_id"])
        images = set()
        for tid in sorted(used):
            if not isinstance(tid, int) or tid <= 0 or tid >= len(tiles):
                raise ValueError(f"ID de tileset Hoenn inválido: {tid}")
            tile = tiles[tid]
            if not isinstance(tile, RubyObject):
                raise ValueError(f"Tileset Hoenn corrompido: {tid}")
            pairs = [("Tilesets", text(tile.attrs["@tileset_name"]))]
            pairs.extend(("Autotiles", text(v)) for v in tile.attrs["@autotile_names"] if v)
            for directory, name in pairs:
                if not name:
                    continue
                if not re.fullmatch(r"[A-Za-z0-9_ ()-]+", name):
                    raise ValueError(f"Nome de gráfico Hoenn inesperado: {name}")
                images.add(f"Graphics/{directory}/{name}.png")
        tracks = {bgm_source(name) for name in BGM.values()} | {RECOVERY, CREDIT_TRACK}
        art = [name for name in BOSS_SPRITES if name in self.blobs]
        total = len(images) + len(tracks) + len(art)
        print(f"[HOENN AUTO] Baixando recursos visuais/sonoros auditados: {total}",flush=True)
        for index, rel in enumerate([*sorted(images), *sorted(tracks), *art], 1):
            dest = self.file(rel)
            if rel.endswith(".png") and not dest.read_bytes().startswith(PNG):
                raise ValueError(f"Imagem Hoenn inválida: {rel}")
            if rel.endswith(".ogg") and not dest.read_bytes().startswith(b"OggS"):
                raise ValueError(f"Áudio Hoenn inválido: {rel}")
            if index % 20 == 0 or index == total:
                print(f"[HOENN AUTO] Recursos auditados: {index}/{total}",flush=True)

        # Check the exact same contract required by the previous local ZIP.
        source = Source(self.stage, self.inventory)
        result = check_source(source)
        if result["real_map_rxdata_hashes_verified"] != 199:
            raise ValueError("Nem todos os 199 mapas Hoenn foram verificados.")
        return {
            "status": "PINNED_HOENN_SOURCE_READY",
            "source_commit": UPSTREAM,
            "tree_sha": PINNED_TREE,
            "maps": 199,
            "files_downloaded": self.written,
            "files_reused": self.reused,
            "bytes_downloaded": self.bytes_downloaded,
            "graphics": len(images),
            "audio": len(tracks),
            "redistribution_approved": False,
            "stage": str(self.stage),
        }


def bootstrap(*, inventory: Path = INVENTORY, stage: Path = STAGE) -> dict:
    return PinnedDownloader(inventory, stage).collect()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=INVENTORY)
    parser.add_argument("--stage", type=Path, default=STAGE)
    args = parser.parse_args()
    try:
        result = bootstrap(inventory=args.inventory, stage=args.stage)
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
        return 0
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as exc:
        print("[HOENN AUTO] Fonte não instalada:", exc, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
