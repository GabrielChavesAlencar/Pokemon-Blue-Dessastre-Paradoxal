#!/usr/bin/env python3
"""Unova E04 — manually selected, private and inert ZIP/Credits intake.

Never downloads third-party assets, extracts content, executes donor files,
installs maps, edits existing game files, or claims license verification.
The user must select the archive provided at the author's original page.
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

from audit_unova_u02 import audit_zip, fail

ROOT = Path(__file__).resolve().parents[2]
REL = Path(".blue-work/unova/sources")
AUDIT_REL = Path(".blue-work/unova/audit")
ZIP_NAME = "Pokemon_World_V18.zip"
CREDITS_NAME = "Credits.txt"
SOURCE_POST = "https://www.reddit.com/r/PokemonRMXP/comments/wsiyyr/"
SOURCE_LINK = "https://www.mediafire.com/file/tq5w0in2xt2peb1/Pokemon_World_V18.zip/file"
CREDITS_LINK = "https://www.mediafire.com/file/gdtsjg5lbnstzo1/Credits.txt/file"
CHUNK = 1024 * 1024
MAX_CREDITS = 512_000


def validate_root(project: Path) -> tuple[Path, Path]:
    project = project.absolute()
    if not project.is_dir() or project.is_symlink():
        fail("raiz do projeto ausente ou symlink")
    source_dir = project / REL
    audit_dir = project / AUDIT_REL
    for location in (project / ".blue-work", project / ".blue-work/unova",
                     source_dir, audit_dir):
        if location.is_symlink() or (location.exists() and not location.is_dir()):
            fail("diretorio de trabalho inseguro")
    # Only create ignored workspace folders; never touch game/, saves or Data.
    source_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    return source_dir, audit_dir


def private_source(path: Path, kind: str, max_bytes: int) -> tuple[str, int]:
    path = path.absolute()
    if path.is_symlink() or not path.is_file():
        fail(kind + " ausente ou symlink")
    if path.stat().st_size <= 0 or path.stat().st_size > max_bytes:
        fail(kind + " com tamanho proibido")
    if kind == "ZIP" and path.suffix.casefold() != ".zip":
        fail("arquivo de fonte deve ser ZIP")
    if kind == "CREDITS" and path.suffix.casefold() != ".txt":
        fail("arquivo de creditos deve ser TXT")
    return path.name, path.stat().st_size


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(CHUNK)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def copy_once(source: Path, dest: Path, limit: int) -> str:
    source = source.absolute()
    if source == dest or source.resolve() == dest.resolve():
        # Idempotence for files already selected in the private workspace.
        return sha256(dest)
    if dest.is_symlink():
        fail("destino de auditoria e symlink")
    if dest.exists():
        if not dest.is_file() or source.stat().st_size != dest.stat().st_size:
            fail("fonte diferente ja existe; nenhuma substituicao automatica")
        if sha256(source) != sha256(dest):
            fail("SHA-256 divergente; nao substituir arquivo privado existente")
        return sha256(dest)

    temp = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=dest.parent,
                                         prefix=".unova-intake-", delete=False) as target:
            temp = Path(target.name)
            with source.open("rb") as original:
                copied = 0
                digest = hashlib.sha256()
                for chunk in iter(lambda: original.read(CHUNK), b""):
                    copied += len(chunk)
                    if copied > limit:
                        fail("arquivo alterado/excede limite durante copia")
                    target.write(chunk)
                    digest.update(chunk)
            target.flush()
            os.fsync(target.fileno())
        if source.stat().st_size != copied or sha256(source) != digest.hexdigest():
            fail("fonte mudou durante copia")
        if dest.exists():
            fail("outra aquisicao criou o destino; nao sobrescrever")
        # Private temp file is on same volume, atomically renamed.
        temp.rename(dest)
        return digest.hexdigest()
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


def intake(project: Path, zip_path: Path, credits_path: Path | None = None) -> dict:
    project = Path(project).absolute()
    zip_path = Path(zip_path).absolute()
    credits_path = Path(credits_path).absolute() if credits_path else None

    # All validation BEFORE copying prevents a malformed source being installed.
    private_source(zip_path, "ZIP", 4 * 1024**3)
    source_info = audit_zip(zip_path)
    credits_info = None
    if credits_path is not None:
        _, size = private_source(credits_path, "CREDITS", MAX_CREDITS)
        with credits_path.open("rb") as stream:
            first = stream.read(512)
        if b"\x00" in first:
            fail("Credits.txt parece arquivo binario")
        credits_info = {
            "selected_name": credits_path.name,
            "bytes": size,
            "sha256": sha256(credits_path),
        }

    source_dir, audit_dir = validate_root(project)
    zip_dest = source_dir / ZIP_NAME
    copy_sha = copy_once(zip_path, zip_dest, 4 * 1024**3)
    if copy_sha != source_info["archive_sha256"]:
        fail("hash ZIP copiado nao corresponde ao inspecionado")
    copied_meta = audit_zip(zip_dest)
    if copied_meta["archive_sha256"] != source_info["archive_sha256"]:
        fail("fonte ZIP privada passou a divergir")

    if credits_path is not None:
        target = source_dir / CREDITS_NAME
        copied_credits_sha = copy_once(credits_path, target, MAX_CREDITS)
        if copied_credits_sha != credits_info["sha256"]:
            fail("hash do Credits.txt mudou na copia")

    report = {
        "schema": 1,
        "region": "UNOVA",
        "phase": "E04",
        "mode": "LOCAL_USER_SELECTED_PRIVATE_INTAKE",
        "status": "ZIP_PRESENT_AND_METADATA_VALIDATED_ORIGIN_NOT_ATTESTED",
        "source_post": SOURCE_POST,
        "expected_source_page": SOURCE_LINK,
        "expected_credits_page": CREDITS_LINK,
        "selected_zip_basename": zip_path.name,
        "private_zip_path": str(REL / ZIP_NAME).replace("\\", "/"),
        "archive_sha256": copy_sha,
        "archive_bytes": copied_meta["archive_size_bytes"],
        "whole_donor_project_map_count": copied_meta["all_regions_source_map_count"],
        "unova_map_count": None,
        "credits_present": credits_info is not None,
        "credits_sha256": credits_info["sha256"] if credits_info else None,
        "source_origin_verified_by_author": False,
        "published_author_hash_matched": False,
        "license_verified": False,
        "credits_are_reuse_permission": False,
        "rights_per_asset_verified": False,
        "native_mapids_checked": False,
        "can_install": False,
        "game_or_saves_modified": False,
        "game_exe_tested": False,
        "android_tested": False,
        "next_actions": [
            "Conferir hash/proveniencia com o criador ou fonte oficial",
            "Inspecionar MapInfos e eventos com auditor inerte",
            "Cruzar mapas candidatos com roteiro Unova e revisar manualmente",
            "Validar licencas e autorizacoes individualmente",
        ],
    }
    output = audit_dir / "e04-intake.json"
    if output.is_symlink():
        fail("relatorio de entrada e symlink")
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if output.exists():
        if output.read_text("utf-8") != payload:
            fail("relatorio previo diferente; nao sobrescrever")
    else:
        with output.open("x", encoding="utf-8") as handle:
            handle.write(payload)
    return report


def pick_inputs():
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Unova E04 — fonte original",
            "Selecione o ZIP que voce baixou da publicacao do criador.\n"
            "A ferramenta nao baixa, executa nem instala esse fangame.\n"
            "Pagina original: " + SOURCE_POST)
        selected_zip = filedialog.askopenfilename(
            parent=root, title="Selecione Pokemon_World_V18.zip",
            filetypes=[("Arquivo ZIP", "*.zip")])
        if not selected_zip:
            root.destroy()
            return None
        selected_credits = None
        if messagebox.askyesno("Creditos (opcional)",
                "Voce possui o arquivo Credits.txt do autor para auditar?\n"
                "Sem ele, a verificacao de direitos ficara pendente."):
            selected_credits = filedialog.askopenfilename(
                parent=root, title="Selecione Credits.txt",
                filetypes=[("Arquivo TXT", "*.txt")])
        root.destroy()
        return Path(selected_zip), Path(selected_credits) if selected_credits else None
    except (ImportError, RuntimeError, OSError) as exc:
        fail("janela grafica indisponivel: " + str(exc))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, default=ROOT)
    ap.add_argument("--zip", type=Path)
    ap.add_argument("--credits", type=Path)
    ap.add_argument("--gui", action="store_true",
                    help="abrir seletor de arquivo do Windows (sem PowerShell)")
    args = ap.parse_args(argv)
    try:
        if args.gui:
            selection = pick_inputs()
            if selection is None:
                print("UNOVA_E04_CANCELADO: nenhuma copia ou instalacao realizada")
                return 2
            zip_path, credits = selection
        else:
            if args.zip is None:
                fail("use --gui para selecionar o ZIP, ou --zip <arquivo> na CLI")
            zip_path, credits = args.zip, args.credits
        report = intake(args.project, zip_path, credits)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print("UNOVA_E04_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
