"""Build a PERSONAL Blue-Story.exe with the user's pinned private Johto ZIP.

This tool is deliberately never run by the PUBLIC release CI and never adds the
private map pack to GitHub. It appends a verified ZIP as a PE overlay, which
Bootstrap.cs stages before install_game.py runs. The receiver needs only the
resulting EXE, not a separate Johto ZIP. Source and destination cannot alias.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import struct
import zipfile
from pathlib import Path

PINNED_SHA256 = "74e727875803f70b3c0598b6b88fe5d79717df849ba1b888fae0583c09202a49"
MAGIC = b"BLUEJH12"
MAX_SOURCE_BYTES = 32_000_000
ORIGINAL_MAPS = {
    f"Johto_Offline_Fase12/Data/Map{mid:03}.rxdata" for mid in range(600, 682)
}


def checksum(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def read_embedded(executable: bytes) -> bytes | None:
    if len(executable) < 16 or executable[-16:-8] != MAGIC:
        return None
    (count,) = struct.unpack("<q", executable[-8:])
    if count <= 0 or count > MAX_SOURCE_BYTES or len(executable) < 16 + count:
        raise ValueError("O sufixo do Blue-Story contém tamanho Johto inválido")
    return executable[-16-count:-16]


def package(launcher: Path, original_zip: Path, destination: Path) -> dict:
    launcher = launcher.resolve()
    original_zip = original_zip.resolve()
    destination = destination.resolve()
    if destination in (launcher, original_zip):
        raise ValueError("Nunca sobrescrever o EXE de origem ou o ZIP privado")
    if not launcher.is_file() or not original_zip.is_file() or launcher.is_symlink() or original_zip.is_symlink():
        raise ValueError("Arquivos de entrada ausentes ou symlinks")
    exe = launcher.read_bytes()
    if not exe.startswith(b"MZ"):
        raise ValueError("Este não é um executável Windows PE")
    if read_embedded(exe) is not None:
        raise ValueError("O executável já tem um pacote Johto embutido")
    private = original_zip.read_bytes()
    if not 0 < len(private) <= MAX_SOURCE_BYTES or checksum(private) != PINNED_SHA256:
        raise ValueError("ZIP de Johto não corresponde ao hash privado OFFLINE12 auditado")
    with zipfile.ZipFile(original_zip) as z:
        if not ORIGINAL_MAPS.issubset(set(z.namelist())) or z.testzip() is not None:
            raise ValueError("ZIP privado OFFLINE12 não contém os 82 mapas auditados")
    content = exe + private + MAGIC + struct.pack("<q", len(private))
    if checksum(read_embedded(content)) != PINNED_SHA256:
        raise ValueError("Falha ao confirmar o payload Johto embutido")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        raise ValueError("Arquivo de saída já existe; não sobrescrever outro EXE")
    temp = destination.with_name(destination.name + ".tmp")
    if temp.exists() or temp.is_symlink():
        raise ValueError("Temporário antigo de saída encontrado")
    try:
        with temp.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(destination)
    finally:
        temp.unlink(missing_ok=True)
    return {"file": str(destination), "bytes": len(content),
            "johto_bytes": len(private), "johto_sha256": PINNED_SHA256,
            "exe_sha256": checksum(content),
            "note": "PRIVATE BUNDLE - not for public GitHub release"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--launcher", type=Path, required=True)
    parser.add_argument("--johto-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(package(args.launcher, args.johto_zip, args.output))


if __name__ == "__main__":
    main()
