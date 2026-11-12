"""Install *already versioned* Kanto music in an isolated or local Blue game.

The source catalog stays under assets/music/kanto/{BGM,ME}; the RPG Maker
runtime reads game/Audio/{BGM,ME}/Kanto. No map or battle preferences are
altered. The default operation only audits; --apply copies with conflicts
rejected and changes rolled back if an unexpected error occurs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data/kanto-music.json"
CATEGORIES = frozenset({"BGM", "ME"})
EXPECTED_FILES = 64
EXPECTED_BYTES = 135_768_381


def git_blob_sha(path: Path) -> str:
    digest = hashlib.sha1()
    size = path.stat().st_size
    digest.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_target_game(game: Path) -> Path:
    game = game.resolve()
    home = (ROOT / "game").resolve()
    work = (ROOT / ".blue-work").resolve()
    if game != home and not (game != work and game.is_relative_to(work)):
        raise ValueError("Destinos permitidos: game/ ou subpasta de .blue-work/ exclusivamente")
    if not (game / "Game.exe").is_file() or not (game / "Audio").is_dir():
        raise ValueError("Instalacao do jogo incompleta: Game.exe e Audio/ obrigatorios")
    return game


def audit(manifest_path: Path = MANIFEST, base: Path = ROOT) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = manifest.get("files", [])
    if manifest.get("schema") != 1 or manifest.get("region") != "KANTO":
        raise ValueError("Manifesto de Kanto invalido")
    if len(items) != EXPECTED_FILES:
        raise ValueError(f"Esperadas {EXPECTED_FILES} musicas, encontradas {len(items)}")
    counts = {"BGM": 0, "ME": 0}
    paths = set()
    numbers = set()
    total = 0
    for item in items:
        number = item["number"]
        kind = item["kind"]
        name = item["filename"]
        if kind not in CATEGORIES:
            raise ValueError("Categoria invalida no catalogo")
        if (
            Path(name).name != name
            or ".." in name
            or "/" in name
            or "\\" in name
            or not name.lower().endswith(".mp3")
        ):
            raise ValueError("Nome inseguro: " + str(name))
        source_rel = f"assets/music/kanto/{kind}/{name}"
        destination_rel = f"Audio/{kind}/Kanto/{name}"
        if item["repo_path"] != source_rel or item["game_path"] != destination_rel:
            raise ValueError("Destinos divergentes do esquema de pastas")
        if number in numbers or source_rel in paths:
            raise ValueError("Musica duplicada")
        numbers.add(number)
        paths.add(source_rel)
        source = base / source_rel
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Arquivo MP3 ausente ou link simbolico: {source_rel}")
        size = source.stat().st_size
        if size != item["bytes"] or git_blob_sha(source) != item["git_blob_sha"]:
            raise ValueError("Arquivo MP3 alterado ou corrompido: " + source_rel)
        counts[kind] += 1
        total += size
    expected_numbers = set(range(1, 61)) | {70, 71, 72, 73}
    if numbers != expected_numbers or counts != {"BGM": 50, "ME": 14}:
        raise ValueError("O catalogo nao preserva as 64 faixas e categorias previstas")
    if total != EXPECTED_BYTES or manifest.get("total_bytes") != total:
        raise ValueError("Tamanho total de audio nao confere com o pacote")
    return {"files": len(items), "BGM": counts["BGM"], "ME": counts["ME"],
            "bytes": total, "manifest": manifest, "base": base}


def install(game: Path, *, apply: bool = False,
            manifest_path: Path = MANIFEST, base: Path = ROOT) -> dict:
    info = audit(manifest_path, base)
    game = safe_target_game(game)
    plan = []
    for track in info["manifest"]["files"]:
        source = base / track["repo_path"]
        destination = game / track["game_path"]
        if not destination.resolve().is_relative_to(game):
            raise ValueError("Destino atraves de symlink fora do jogo: " + str(destination))
        if destination.exists():
            if not destination.is_file() or git_blob_sha(destination) != track["git_blob_sha"]:
                raise ValueError("Conflito: nao sobrescrever audio ja existente: " +
                                 track["game_path"])
            plan.append((source, destination, False))
        else:
            plan.append((source, destination, True))
    pending = [row for row in plan if row[2]]
    if not apply:
        return {"status": "preview", "total": len(plan),
                "new": len(pending), "unchanged": len(plan)-len(pending),
                "writes": False}
    staged = []
    installed = []
    try:
        for source, destination, _ in pending:
            destination.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(prefix=".kanto-import-", dir=destination.parent)
            os.close(fd)
            temporary = Path(name)
            staged.append(temporary)
            shutil.copyfile(source, temporary)
            staged_sha = git_blob_sha(temporary)
            if staged_sha != git_blob_sha(source):
                raise OSError("Falha de integridade ao copiar " + source.name)
        for (_, destination, _), temp in zip(pending, staged):
            if destination.exists():
                raise FileExistsError("Destino mudou durante a instalacao: " + str(destination))
            # Use an exclusive new-file create rather than overwrite existing
            # audio in a race with another editor or import process.
            with destination.open("xb") as out, temp.open("rb") as file:
                shutil.copyfileobj(file, out, length=1024*1024)
            installed.append(destination)
            if git_blob_sha(destination) != git_blob_sha(temp):
                raise OSError("Falha ao conferir musica instalada: " + str(destination))
    except BaseException:
        for destination in reversed(installed):
            destination.unlink(missing_ok=True)
        raise
    finally:
        for temporary in staged:
            temporary.unlink(missing_ok=True)
    return {"status": "installed", "total": len(plan),
            "new": len(installed), "unchanged": len(plan)-len(installed),
            "writes": bool(installed)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true",
                        help="Somente conferir os 64 MP3, sem exigir Game.exe")
    parser.add_argument("--game", type=Path, default=ROOT / "game",
                        help="game/ local ou piloto isolado em .blue-work/")
    parser.add_argument("--apply", action="store_true",
                        help="Copiar sem sobrescrever Audio/BGM e Audio/ME")
    args = parser.parse_args()
    try:
        if args.audit and args.apply:
            parser.error("--audit e --apply nao podem ser combinados")
        result = (audit() if args.audit else install(args.game, apply=args.apply))
        if args.audit:
            result = {k:v for k,v in result.items() if k not in ("manifest","base")}
            result["status"]="audited_only"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print("[KANTO MUSIC ERROR]", error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
