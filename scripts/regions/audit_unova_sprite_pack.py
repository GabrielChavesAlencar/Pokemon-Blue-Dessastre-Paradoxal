#!/usr/bin/env python3
"""Audit Unova sprite-only ZIPs safely, with optional read-only Decades comparison.

Standard library only. Never extracts, copies, stages, installs, executes donor
code, writes in game/, or approves licensing. Image metadata and sheet layouts
are CANDIDATES only, not visually or natively confirmed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import struct
import sys
import unicodedata
import zipfile
import zlib
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
MAX_ZIP = 2 * 1024**3
MAX_MEMBERS = 30000
MAX_TOTAL_DECLARED = 6 * 1024**3
MAX_SPRITE_BYTES = 16 * 1024**2
MAX_PIXELS = 16_777_216
MAX_DIM = 8192
MAX_REFERENCE_FILES = 10000
SPRITE_EXT = {".png", ".gif", ".apng"}
OTHER_IMAGE_EXT = {".bmp", ".jpg", ".jpeg", ".webp", ".tga", ".ase", ".aseprite"}
EXPECTED = ("CHEREN", "BIANCA", "JUNIPER", "N", "GHETSIS", "TEAM_PLASMA",
            "HILBERT", "HILDA", "CILAN", "CHILI", "CRESS", "LENORA",
            "BURGH", "ELESA", "CLAY", "SKYLA", "BRYCEN", "IRIS",
            "SHAUNTAL", "GRIMSLEY", "CAITLIN", "MARSHAL", "ALDER")
CHUNK = 1024 * 1024
MAX_REPORT_IMAGES = 12000


def deny(message: str) -> None:
    raise ValueError("UNOVA_SPRITES_BLOQUEADO: " + message)


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_zip_parts(path: str) -> tuple[str, ...]:
    if not path or path.startswith("/") or "\\" in path or "\x00" in path:
        deny("caminho ZIP absoluto ou inseguro")
    parts = tuple(path.rstrip("/").split("/"))
    if any(not p or p in (".", "..") or ":" in p or any(ord(c) < 32 for c in p)
           for p in parts):
        deny("ZIP com travessia, caractere de controle ou caminho vazio")
    return parts


def inspect_png(blob: bytes) -> dict:
    if len(blob) < 45 or blob[:8] != b"\x89PNG\r\n\x1a\n":
        deny("PNG com assinatura ausente")
    offset = 8
    width = height = None
    color = None
    apng = 0
    palette_alpha = False
    found_idat = False
    ended = False
    while offset + 12 <= len(blob):
        size = struct.unpack_from(">I", blob, offset)[0]
        if size > MAX_SPRITE_BYTES or offset + 12 + size > len(blob):
            deny("PNG com chunk incompleto ou excessivo")
        kind = blob[offset + 4:offset + 8]
        payload = blob[offset + 8:offset + 8 + size]
        crc_expected = struct.unpack_from(">I", blob, offset + 8 + size)[0]
        crc_actual = zlib.crc32(kind + payload) & 0xffffffff
        if crc_actual != crc_expected:
            deny("PNG com chunk CRC invalido")
        if width is None:
            if kind != b"IHDR" or size != 13:
                deny("PNG sem IHDR como primeiro chunk")
            width, height, depth, color, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", payload)
            if (not 0 < width <= MAX_DIM or not 0 < height <= MAX_DIM or
                width * height > MAX_PIXELS or color not in (0, 2, 3, 4, 6) or
                depth not in (1, 2, 4, 8, 16) or compression != 0 or
                filtering != 0 or interlace not in (0, 1)):
                deny("metadados IHDR invalidos ou imagem excessiva")
        elif kind == b"IHDR":
            deny("PNG com IHDR duplicado")
        if kind == b"acTL":
            if size != 8 or apng:
                deny("APNG acTL invalido/duplicado")
            apng, _plays = struct.unpack(">II", payload)
            if not 1 <= apng <= 2000:
                deny("APNG com quadros excessivos")
        if kind == b"tRNS":
            palette_alpha = True
        if kind == b"IDAT":
            found_idat = True
        offset += 12 + size
        if kind == b"IEND":
            if size != 0 or offset != len(blob):
                deny("PNG com IEND invalido ou bytes extras")
            ended = True
            break
    if not ended or width is None or not found_idat:
        deny("PNG truncado/sem IDAT/IEND")
    return {
        "format": "APNG" if apng else "PNG",
        "width": width, "height": height,
        "animation_frames_declared": apng or 1,
        "animation_decoded": False,
        "transparency_possible": color in (4, 6) or palette_alpha,
    }


def _gif_subblocks(blob: bytes, offset: int) -> int:
    while True:
        if offset >= len(blob):
            deny("GIF com sub-bloco incompleto")
        count = blob[offset]
        offset += 1
        if count == 0:
            return offset
        if offset + count > len(blob):
            deny("GIF com dados de sub-bloco truncados")
        offset += count


def inspect_gif(blob: bytes) -> dict:
    if len(blob) < 14 or blob[:6] not in (b"GIF87a", b"GIF89a"):
        deny("GIF com cabecalho ausente")
    width, height = struct.unpack_from("<HH", blob, 6)
    if not (0 < width <= MAX_DIM and 0 < height <= MAX_DIM
            and width * height <= MAX_PIXELS):
        deny("GIF com dimensoes invalidas")
    flags = blob[10]
    offset = 13
    if flags & 0x80:
        offset += 3 * (2 ** ((flags & 7) + 1))
    if offset > len(blob):
        deny("GIF com paleta global truncada")
    frames = 0
    delays = []
    has_transparency = False
    pending_delay = 0
    closed = False
    while offset < len(blob):
        marker = blob[offset]
        offset += 1
        if marker == 0x3B:
            if offset != len(blob):
                deny("GIF contem bytes apos trailer")
            closed = True
            break
        if marker == 0x21:
            if offset >= len(blob):
                deny("GIF com extensao truncada")
            label = blob[offset]
            offset += 1
            if label == 0xF9:
                if offset + 6 > len(blob) or blob[offset] != 4 or blob[offset + 5] != 0:
                    deny("GIF com Graphics Control Extension invalida")
                has_transparency |= bool(blob[offset + 1] & 1)
                pending_delay = struct.unpack_from("<H", blob, offset + 2)[0] * 10
                offset += 6
            else:
                offset = _gif_subblocks(blob, offset)
            continue
        if marker == 0x2C:
            if offset + 9 > len(blob):
                deny("GIF com descritor de frame truncado")
            x, y, frame_w, frame_h = struct.unpack_from("<HHHH", blob, offset)
            if frame_w < 1 or frame_h < 1 or x + frame_w > width or y + frame_h > height:
                deny("GIF frame fora do canvas")
            local_flags = blob[offset + 8]
            offset += 9
            if local_flags & 0x80:
                offset += 3 * (2 ** ((local_flags & 7) + 1))
            if offset >= len(blob):
                deny("GIF com paleta local ou codigo LZW ausente")
            lzw = blob[offset]
            if lzw > 12:
                deny("GIF LZW fora do limite")
            offset = _gif_subblocks(blob, offset + 1)
            frames += 1
            if frames > 2000:
                deny("GIF com quadros demais")
            delays.append(pending_delay)
            pending_delay = 0
            continue
        deny("GIF com bloco desconhecido")
    if not closed or not frames:
        deny("GIF sem frames/trailer")
    return {
        "format": "GIF", "width": width, "height": height,
        "animation_frames_declared": frames,
        "animation_decoded": False,
        "delays_ms_declared": delays[:60],
        "transparency_possible": has_transparency,
    }


def image_info(blob: bytes, extension: str) -> dict:
    if extension in (".png", ".apng"):
        return inspect_png(blob)
    if extension == ".gif":
        return inspect_gif(blob)
    deny("extensao raster nao suportada")


def sheet_guesses(width: int, height: int, animated: bool) -> list[dict]:
    if animated:
        return []
    guesses = []
    for columns, rows, label in (
            (4, 4, "RMXP_4_COLUMNS_4_DIRECTIONS_CANDIDATE"),
            (3, 4, "THREE_FRAME_4_DIRECTIONS_CANDIDATE")):
        if width % columns or height % rows:
            continue
        cw, ch = width // columns, height // rows
        if not 8 <= cw <= 256 or not 8 <= ch <= 256:
            continue
        guesses.append({
            "layout_candidate": label,
            "columns": columns, "direction_rows": rows,
            "cell_width": cw, "cell_height": ch,
            "directions_assumed_not_proven": ["down", "left", "right", "up"],
        })
    return guesses


def tokens(name: str) -> set[str]:
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    # Underscore and camel-case are both common in RPG Maker sprite files.
    name = re.sub(r"(?<=[a-z])(?=[A-Z])", "_", name)
    return {x for x in re.findall(r"[a-z0-9]+", name.lower()) if x}


def identity_candidate(stem: str, relative_path: str) -> list[str]:
    words = tokens(stem)
    identifiers = []
    specials = {
        "CHEREN": ("cheren",), "BIANCA": ("bianca",),
        "JUNIPER": ("juniper",), "GHETSIS": ("ghetsis",),
        "TEAM_PLASMA": ("plasma",), "HILBERT": ("hilbert",),
        "HILDA": ("hilda",), "CILAN": ("cilan",),
        "CHILI": ("chili",), "CRESS": ("cress",),
        "LENORA": ("lenora",), "BURGH": ("burgh",),
        "ELESA": ("elesa",), "CLAY": ("clay",),
        "SKYLA": ("skyla",), "BRYCEN": ("brycen",),
        "IRIS": ("iris",), "SHAUNTAL": ("shauntal",),
        "GRIMSLEY": ("grimsley",), "CAITLIN": ("caitlin",),
        "MARSHAL": ("marshal",), "ALDER": ("alder",),
    }
    for name, aliases in specials.items():
        if any(alias in words for alias in aliases):
            identifiers.append(name)
    if stem.strip().lower() == "n" or re.fullmatch(r"n[_ -](?:bw|trainer|overworld|ow)", stem.lower()):
        identifiers.append("N")
    return sorted(set(identifiers))


def kind_candidate(path: str) -> str:
    s=path.casefold()
    if any(part in s for part in ("/characters/", "/overworld/", "/ow/", "/npc/", "/npcs/")):
        return "OVERWORLD_SHEET_CANDIDATE"
    if "battler" in s or "/pokemon/" in s:
        return "BATTLE_SPRITE_CANDIDATE"
    if "/icon" in s:
        return "ICON_CANDIDATE"
    return "UNCLASSIFIED_IMAGE"


def _read_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> bytes:
    if info.file_size > MAX_SPRITE_BYTES or info.file_size == 0:
        deny("imagem vazia ou grande demais: " + info.filename[:120])
    with archive.open(info) as stream:
        data = stream.read(MAX_SPRITE_BYTES + 1)
    if len(data) != info.file_size:
        deny("tamanho descompactado inesperado: " + info.filename[:120])
    return data


def reference_inventory(directory: Path | None) -> dict:
    if directory is None:
        return {
            "status": "NOT_PROVIDED", "files_scanned": 0,
            "same_name_comparisons_available": False,
            "typical_4x4_cell_height": None,
            "sprites": {},
        }
    root = directory.absolute()
    if not root.exists():
        deny("pasta de referencia Decades indicada nao encontrada")
    if root.is_symlink() or not root.is_dir():
        deny("diretorio Decades invalido ou link simbolico")
    found = defaultdict(list)
    count = 0
    heights = []
    for current, folders, files in os.walk(root, followlinks=False):
        current = Path(current)
        if current.is_symlink():
            deny("symlink em pasta de referencia")
        for folder in folders:
            if (current/folder).is_symlink():
                deny("symlink de pasta no Decades")
        for name in files:
            path = current/name
            if path.is_symlink():
                deny("symlink de sprite no Decades")
            if path.suffix.lower() not in SPRITE_EXT:
                continue
            count += 1
            if count > MAX_REFERENCE_FILES:
                deny("referencia Decades contem sprites demais")
            if not 0 < path.stat().st_size <= MAX_SPRITE_BYTES:
                continue
            try:
                data = path.read_bytes()
                meta = image_info(data, path.suffix.lower())
            except ValueError:
                # A broken native reference does not certify compatibility.
                continue
            basename = path.stem.casefold()
            guesses = sheet_guesses(meta["width"], meta["height"],meta["animation_frames_declared"] > 1)
            heights.extend(g["cell_height"] for g in guesses if g["columns"] == 4)
            found[basename].append({
                "width": meta["width"], "height": meta["height"],
                "format": meta["format"],
                "sha256": hashlib.sha256(data).hexdigest(),
                "sheet_guesses": guesses,
            })
    return {
        "status": "SCANNED_READ_ONLY",
        "files_scanned": count,
        "same_name_comparisons_available": True,
        "typical_4x4_cell_height": median(heights) if heights else None,
        "sprites": dict(found),
    }


def audit(source: Path, reference_dir: Path | None = None) -> dict:
    source = Path(source).absolute()
    if source.is_symlink() or not source.is_file() or source.suffix.lower() != ".zip":
        deny("ZIP de sprites ausente, symlink ou extensao invalida")
    if not 0 < source.stat().st_size <= MAX_ZIP:
        deny("tamanho de ZIP fora do limite")
    reference = reference_inventory(reference_dir)
    entries = []
    seen = set()
    declared = 0
    actual_images = []
    unsupported = []
    invalid = []
    digest_groups = defaultdict(list)
    stem_groups = defaultdict(list)
    character_paths = defaultdict(list)
    with zipfile.ZipFile(source) as z:
        members = z.infolist()
        if len(members) > MAX_MEMBERS:
            deny("ZIP com entradas demais")
        for item in members:
            parts = safe_zip_parts(item.filename)
            key = "/".join(parts).casefold()
            if key in seen:
                deny("ZIP contem duplicacao de caminho, inclusive caixa")
            seen.add(key)
            if stat.S_IFMT(item.external_attr >> 16) == stat.S_IFLNK:
                deny("ZIP contem link simbolico")
            if item.flag_bits & 1:
                deny("ZIP contem membro criptografado")
            declared += item.file_size
            if declared > MAX_TOTAL_DECLARED:
                deny("ZIP ultrapassou limite descompactado")
            if item.file_size > 1_000_000 and item.file_size/max(1,item.compress_size) > 1000:
                deny("ZIP com taxa suspeita de descompactacao")
            if item.is_dir():
                continue
            extension = Path(item.filename).suffix.casefold()
            if extension in OTHER_IMAGE_EXT:
                if len(unsupported) < 250:
                    unsupported.append(item.filename)
                continue
            if extension not in SPRITE_EXT:
                continue
            if len(actual_images) >= MAX_REPORT_IMAGES:
                deny("mais sprites que o limite suportado")
            try:
                blob = _read_member(z, item)
                meta = image_info(blob, extension)
            except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as exc:
                invalid.append({"path": item.filename, "error": str(exc)[:250]})
                continue
            hexsha=hashlib.sha256(blob).hexdigest()
            stem=Path(item.filename).stem
            guesses=sheet_guesses(meta["width"],meta["height"],meta["animation_frames_declared"] > 1)
            identities=identity_candidate(stem,item.filename)
            refs=reference["sprites"].get(stem.casefold(),[])
            dimension_mismatch=any(
                (r["width"],r["height"]) != (meta["width"],meta["height"])
                for r in refs)
            ratio=None
            if guesses and refs and refs[0]["sheet_guesses"]:
                baseline_h=refs[0]["sheet_guesses"][0]["cell_height"]
                if baseline_h:
                    ratio=round(guesses[0]["cell_height"]/baseline_h,3)
            warnings = []
            if not guesses and meta["animation_frames_declared"] == 1:
                warnings.append("NO_4_DIRECTION_LAYOUT_CANDIDATE")
            if len(guesses) > 1:
                warnings.append("LAYOUT_AMBIGUOUS_4X4_VS_3X4")
            if refs:
                warnings.append("EXISTING_DECADES_BASENAME_COLLISION_DO_NOT_OVERWRITE")
                if dimension_mismatch:
                    warnings.append("POTENTIAL_DIMENSION_MISMATCH")
                if ratio is not None and (ratio > 1.25 or ratio < 0.8):
                    warnings.append("POTENTIAL_FRAME_SCALE_MISMATCH")
            else:
                # Unmatched name is not proof of compatible sizing.
                typical=reference["typical_4x4_cell_height"]
                if guesses and typical:
                    factor=guesses[0]["cell_height"]/typical
                    if factor > 1.5 or factor < 0.67:
                        warnings.append("POTENTIAL_REFERENCE_SCALE_OUTLIER")
            row = {
                "path": item.filename, "basename": stem, "sha256": hexsha,
                "bytes":len(blob), **meta,
                "sprite_kind_candidate":kind_candidate("/"+item.filename),
                "character_name_candidates":identities,
                "sheet_layout_candidates":guesses,
                "native_four_direction_layout_verified":False,
                "native_animation_playback_verified":False,
                "decades_same_basename_matches":len(refs),
                "decades_matching_dimensions":bool(refs) and not dimension_mismatch,
                "decades_exact_binary_match":bool(refs) and any(r["sha256"]==hexsha for r in refs),
                "candidate_cell_height_ratio_to_first_decades_match":ratio,
                "warnings":warnings,
                "rights_verified":False,
                "installable":False,
            }
            actual_images.append(row)
            digest_groups[hexsha].append(item.filename)
            stem_groups[stem.casefold()].append(item.filename)
            for character in identities:
                character_paths[character].append(item.filename)
    if not actual_images and not invalid:
        deny("ZIP nao contem sprites PNG ou GIF analisaveis")
    if not actual_images and invalid:
        deny("nenhum sprite PNG/GIF valido no pacote")
    duplicates=[
        {"sha256":h,"paths":sorted(files)}
        for h,files in sorted(digest_groups.items())
        if len(files)>1
    ]
    stem_collisions=[
        {"basename_casefold":h, "paths":sorted(files)}
        for h,files in sorted(stem_groups.items())
        if len(files)>1
    ]
    return {
        "schema":1,"region":"UNOVA","phase":"SPRITE_AUDIT_SP03",
        "mode":"PRIVATE_SPRITE_PACK_METADATA_INSPECTION_NO_EXTRACTION",
        "status":"SPRITES_AUDITED_NOT_LICENSED_OR_INSTALLED" if not invalid
                 else "SPRITES_WITH_INVALID_FILES_NEED_REVIEW",
        "archive_basename":source.name,
        "archive_sha256":sha_file(source),
        "whole_archive_file_entries":len(members),
        "supported_images":len(actual_images),
        "formats_count":dict(sorted(Counter(x["format"] for x in actual_images).items())),
        "sprite_kinds_count":dict(sorted(Counter(x["sprite_kind_candidate"] for x in actual_images).items())),
        "potential_warnings_count":dict(sorted(Counter(
            warning for image in actual_images for warning in image["warnings"]).items())),
        "invalid_images":invalid,
        "unsupported_image_paths":unsupported,
        "duplicate_content_groups":duplicates,
        "same_basename_collisions":stem_collisions,
        "characters_by_filename_candidates":dict(sorted(character_paths.items())),
        "requested_characters_not_matched_by_filename":[x for x in EXPECTED if x not in character_paths],
        "reference_status":reference["status"],
        "reference_files_scanned":reference["files_scanned"],
        "reference_typical_4x4_cell_height":reference["typical_4x4_cell_height"],
        "images":actual_images,
        "rights_verified":False,
        "may_redistribute":False,
        "game_exe_tested":False,"android_tested":False,
        "game_or_saves_modified":False,
        "can_install":False,
        "notes":[
            "Nomes identificados por arquivo sao candidatos; N nao se identifica por letra no meio do nome.",
            "Grid 4x4/3x4 e somente hipotese; nao valida ordem de direcoes nem frames.",
            "Comparacao Decades so usa arquivos locais fornecidos; sem referencia a compatibilidade fica desconhecida.",
            "Dimensoes iguais nao comprovam estilo/pivo/escala renderizada; exige teste Game.exe/JoiPlay.",
            "Direitos e atribuicoes precisam ser aprovados por arquivo, nao por existencia no ZIP.",
        ]
    }


def save_report(project: Path, report: dict) -> Path:
    project=Path(project).absolute()
    if project.is_symlink() or not project.is_dir():
        deny("raiz de projeto invalida")
    folders=[project/".blue-work",project/".blue-work/unova",
             project/".blue-work/unova/audit",project/".blue-work/unova/audit/sprite-packs"]
    for folder in folders:
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            deny("pasta de relatorio symlink/arquivo")
    for folder in folders:
        folder.mkdir(exist_ok=True)
    target=folders[-1]/("sprites-"+report["archive_sha256"][:16]+".json")
    if target.is_symlink():
        deny("saida symlink")
    payload=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if target.exists():
        if target.read_text("utf-8") != payload:
            deny("relatorio previo divergente; nao sobrescrever")
    else:
        with target.open("x",encoding="utf-8") as fh:
            fh.write(payload)
    return target


def choose_gui():
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
        root=tk.Tk()
        root.withdraw()
        messagebox.showinfo("Unova — auditoria segura",
            "Selecione o ZIP de sprites do autor. Nenhuma imagem sera instalada ou extraida.")
        selected=filedialog.askopenfilename(parent=root,title="Escolher pack sprites de Unova",
                                            filetypes=[("ZIP de sprites","*.zip")])
        if not selected:
            root.destroy()
            return None
        reference=None
        if messagebox.askyesno("Comparar com Decades?",
               "Quer selecionar a pasta Graphics/Characters de sua instalacao do Decades?\n"
               "Os arquivos serao lidos somente para comparacao."):
            ref=filedialog.askdirectory(parent=root,title="Selecione Graphics/Characters do Decades")
            if ref:
                reference=Path(ref)
        root.destroy()
        return Path(selected),reference
    except (ImportError,RuntimeError,OSError) as exc:
        deny("seletor grafico indisponivel: "+str(exc))


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--zip",type=Path)
    parser.add_argument("--reference-dir",type=Path,
                        help="Graphics/Characters real do Decades, leitura apenas")
    parser.add_argument("--gui",action="store_true")
    parser.add_argument("--write",action="store_true")
    args=parser.parse_args(argv)
    try:
        zip_path=args.zip
        ref=args.reference_dir
        if args.gui:
            selection=choose_gui()
            if selection is None:
                print("UNOVA_SPRITES_CANCELADO: nenhum arquivo alterado")
                return 2
            zip_path, ref=selection
        if zip_path is None:
            deny("selecione o ZIP por --gui ou --zip")
        result=audit(zip_path,ref)
        target=save_report(args.project,result) if args.write or args.gui else None
        compact={k:v for k,v in result.items() if k!="images"}
        if target is not None:
            compact["private_report"]=str(target.relative_to(Path(args.project).absolute()))
        print(json.dumps(compact,indent=2,ensure_ascii=False))
        return 0 if not result["invalid_images"] else 2
    except (OSError,ValueError,TypeError,KeyError,zipfile.BadZipFile,zipfile.LargeZipFile,
            NotImplementedError) as exc:
        print("UNOVA_SPRITES_BLOQUEADO: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
