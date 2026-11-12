"""Audit the Kanto audio ZIP and optionally publish it as a GitHub Release asset.

The repository deliberately does not distribute third-party game soundtracks
as tracked files. This command requires an *explicit* rights confirmation and
a local, authenticated GitHub CLI session before publishing a release.
Nothing is uploaded without --publish AND --confirm-rights.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

DEFAULT_TAG = "kanto-audio-user-supplied-2026-11-12"
DEFAULT_REPO = "GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal"
EXPECTED_ZIP_SHA256 = "60af6717ee93bc1381b2c38103c6ec5ddf162650bd80cc45432ef0d7f3dd5284"
MAX_ARCHIVE_BYTES = 250 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 300 * 1024 * 1024
MAX_TRACK_BYTES = 15 * 1024 * 1024
TRACK_NAME = re.compile(r"1-(?:0[1-9]|[1-5][0-9]|60|7[0-3])\.\s+.+\.mp3$", re.I)


def inspect_archive(source: Path) -> dict:
    if not source.is_file():
        raise ValueError(f"Arquivo ZIP nao encontrado: {source}")
    if source.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("Arquivo ZIP excede o limite local de verificacao")
    tracks = []
    names = set()
    total = 0
    with zipfile.ZipFile(source) as archive:
        entries = archive.infolist()
        for info in entries:
            raw = info.filename.replace("\\", "/")
            name = PurePosixPath(raw)
            if (name.is_absolute() or
                any(piece in ("", "..", ".") for piece in name.parts) or
                re.match(r"^[A-Za-z]:", raw) or "\x00" in raw):
                raise ValueError("Entrada ZIP com caminho inseguro: " + raw)
            if info.is_dir():
                continue
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Links simbolicos no ZIP nao sao aceitos")
            if len(name.parts) != 2 or name.parts[0] != "pkm msc kanto":
                raise ValueError("A raiz do album nao confere: " + raw)
            if not TRACK_NAME.fullmatch(name.name):
                raise ValueError("Faixa inesperada ou tipo de arquivo nao MP3: " + raw)
            if info.file_size < 1000 or info.file_size > MAX_TRACK_BYTES:
                raise ValueError("Faixa com tamanho invalido: " + raw)
            key = name.name.casefold()
            if key in names:
                raise ValueError("Faixa duplicada: " + raw)
            names.add(key)
            total += info.file_size
            if total > MAX_UNCOMPRESSED_BYTES:
                raise ValueError("ZIP possivelmente inflado, acima do limite")
            with archive.open(info) as file:
                prefix = file.read(3)
            if prefix != b"ID3" and not (prefix[0] == 0xff and prefix[1] & 0xe0 == 0xe0):
                raise ValueError("A entrada nao tem cabecalho de MP3: " + raw)
            tracks.append({"filename": name.name, "bytes": info.file_size})
    if len(tracks) != 64:
        raise ValueError(f"Esperadas 64 musicas MP3; encontradas {len(tracks)}")
    tracks.sort(key=lambda row: row["filename"])
    digest = hashlib.sha256()
    with source.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != EXPECTED_ZIP_SHA256:
        raise ValueError("O ZIP nao corresponde ao pacote de Kanto enviado neste chat (SHA-256)")
    return {
        "archive_name": source.name,
        "archive_sha256": digest.hexdigest(),
        "archive_bytes": source.stat().st_size,
        "uncompressed_audio_bytes": total,
        "tracks_count": len(tracks),
        "tracks": tracks,
        "audited_not_uploaded": True,
    }


def publish_release(source: Path, *, repo: str, tag: str) -> None:
    binary = shutil.which("gh")
    if not binary:
        raise RuntimeError("GitHub CLI (gh) nao encontrado. Instale e rode gh auth login")
    checked = subprocess.run(
        [binary, "auth", "status"], capture_output=True, text=True
    )
    if checked.returncode != 0:
        raise RuntimeError("GitHub CLI nao autenticado: execute gh auth login")
    exists = subprocess.run(
        [binary, "release", "view", tag, "--repo", repo],
        capture_output=True, text=True
    )
    if exists.returncode == 0:
        raise RuntimeError(
            f"Ja existe a release {tag}; nao vou substituir nenhum audio automaticamente"
        )
    notes = (
        "Arquivo fornecido pelo usuario, com 64 MP3s para uso em Kanto. "
        "Esta publicacao e de responsabilidade de quem confirmou ter direitos "
        "de distribuicao. Audio nao foi adicionado ao historico Git."
    )
    subprocess.run(
        [binary, "release", "create", tag, str(source), "--repo", repo,
         "--title", "Kanto — pacote de 64 musicas", "--notes", notes],
        check=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True,
                        help='Caminho local para "pkm msc kanto.zip"')
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--tag", default=DEFAULT_TAG)
    parser.add_argument("--publish", action="store_true",
                        help="Enviar o ZIP como asset em uma GitHub Release")
    parser.add_argument("--confirm-rights", action="store_true",
                        help="Declaro ter permissao de distribuir publicamente estes audios")
    parser.add_argument("--manifest", type=Path, default=None,
                        help="Salvar relatorio JSON local de faixas/tamanhos/hashes")
    args = parser.parse_args(argv)
    try:
        metadata = inspect_archive(args.archive)
        if args.manifest:
            args.manifest.parent.mkdir(parents=True, exist_ok=True)
            args.manifest.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print(
            f"[AUDITORIA] {metadata['tracks_count']} MP3 / "
            f"{metadata['uncompressed_audio_bytes']} bytes / "
            f"SHA256 ZIP {metadata['archive_sha256']}"
        )
        if not args.publish:
            print("[PREVIA] Nenhum audio enviado ao GitHub; use --publish apos conferir os direitos.")
            return 0
        if not args.confirm_rights:
            raise ValueError(
                "GitHub publico: confirme a autorizacao de redistribuicao "
                "com --confirm-rights antes do envio"
            )
        publish_release(args.archive.resolve(), repo=args.repo, tag=args.tag)
        print(f"[PUBLICADO] Release {args.tag} em {args.repo}")
        return 0
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError,
            subprocess.CalledProcessError) as error:
        print(f"[ERRO] {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
