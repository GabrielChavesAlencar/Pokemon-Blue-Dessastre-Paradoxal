"""Blue Studio: local-only PBS editor for Pokémon Essentials/Decades.
Standard library only. No assets of any third-party fangame are distributed here.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import struct
import zlib
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
import webbrowser
from pokemon_studio import (PokemonValidationError, create_species, make_species_raw,
                            validate_pokemon, species_catalog, pbs_catalog)

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
DEFAULT_GAME = ROOT / "game"
BACKUPS = ROOT / ".blue-backups"
MAX_POST = 8_000_000
SECTION_RE = re.compile(r"^\s*\[([^\]\r\n]+)\][ \t]*(?:#.*)?$", re.MULTILINE)
FIELD_RE = re.compile(r"^([\t ]*)([A-Za-z][A-Za-z0-9_]*)[\t ]*=[\t ]*(.*)$")
EDIT_LOCK = threading.Lock()


class EditorError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def pbs_path(game_root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or name in (".", "..") or Path(name).name != name or not name.lower().endswith(".txt") or "\\" in name or "/" in name:
        raise EditorError("Nome de arquivo PBS inválido.")
    root = (game_root / "PBS").resolve()
    target = (root / name).resolve()
    if target.parent != root or not target.is_file():
        raise EditorError("Arquivo PBS não encontrado.", 404)
    return target


def file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_text(path: Path) -> tuple[bytes, str]:
    raw = path.read_bytes()
    try:
        return raw, raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Pokémon Essentials PBS data is generally UTF-8; refuse destructive transcoding.
        raise EditorError("Arquivo não está em UTF-8; não será regravado automaticamente.", 422)


def sections_in(text: str) -> list[dict]:
    lines = text.splitlines(keepends=True)
    found = []
    for i, line in enumerate(lines):
        m = SECTION_RE.fullmatch(line.rstrip("\r\n"))
        if m:
            found.append({"id": m.group(1).strip(), "start": i, "index": len(found)})
    for i, sec in enumerate(found):
        sec["end"] = found[i + 1]["start"] if i + 1 < len(found) else len(lines)
        chunk = lines[sec["start"]:sec["end"]]
        name = ""
        for line in chunk[1:]:
            match = FIELD_RE.match(line.strip("\r\n"))
            if match and match.group(2).lower() in ("name", "formname"):
                name = match.group(3).strip()[:100]
                break
        sec["label"] = name
    return found


def section_lines(text: str, sec: dict) -> str:
    return "".join(text.splitlines(keepends=True)[sec["start"]:sec["end"]])


def extract_fields(chunk: str) -> list[dict]:
    fields = []
    for lineno, line in enumerate(chunk.splitlines()):
        m = FIELD_RE.match(line)
        if m:
            fields.append({"line": lineno, "key": m.group(2), "value": m.group(3), "indent": m.group(1)})
    return fields


def validate_section(content: str) -> str:
    if not isinstance(content, str) or not content or len(content.encode("utf-8")) > 200_000:
        raise EditorError("Seção vazia ou maior que 200 KB.")
    if "\x00" in content:
        raise EditorError("Conteúdo binário inválido.")
    lines = content.splitlines()
    if not lines:
        raise EditorError("Seção vazia.")
    match = SECTION_RE.fullmatch(lines[0])
    if not match:
        raise EditorError("A primeira linha precisa ser [IDENTIFICADOR].")
    if any(SECTION_RE.fullmatch(line) for line in lines[1:]):
        raise EditorError("Edite uma seção de cada vez (foi detectado outro cabeçalho).")
    return match.group(1).strip()


def save_section(game_root: Path, name: str, index: int, expected_hash: str, content: str, backup_root: Path = BACKUPS) -> dict:
    if not isinstance(index, int):
        raise EditorError("Índice de seção inválido.")
    new_id = validate_section(content)
    path = pbs_path(game_root, name)
    with EDIT_LOCK:
        raw, source = read_text(path)
        if file_hash(raw) != expected_hash:
            raise EditorError("Arquivo modificado desde a leitura. Recarregue antes de salvar para evitar perda de dados.", 409)
        sections = sections_in(source)
        if any(s["id"].casefold() == new_id.casefold() and s["index"] != index for s in sections):
            raise EditorError("Já existe uma seção com este identificador neste arquivo.", 409)
        newline = "\r\n" if source.count("\r\n") > source.count("\n") / 2 else "\n"
        new_content = content.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n") + "\n"
        if newline == "\r\n":
            new_content = new_content.replace("\n", newline)
        if index == -1:
            new_source = source.rstrip("\r\n") + newline + "#-------------------------------" + newline + new_content
        else:
            if index < 0 or index >= len(sections):
                raise EditorError("Seção não encontrada.", 404)
            lines = source.splitlines(keepends=True)
            sec = sections[index]
            # Keep nearby separators from the original file if user deleted them.
            new_source = "".join(lines[:sec["start"]]) + new_content + "".join(lines[sec["end"]:])
        # Preserve UTF-8 BOM if present.
        new_bytes = (b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b"") + new_source.encode("utf-8")
        backup_file(backup_root, name, raw)
        atomic_write(path, new_bytes)
        updated = sections_in(new_source)
        selected = next((s["index"] for s in updated if s["id"].casefold() == new_id.casefold()), None)
        return {"ok": True, "hash": file_hash(new_bytes), "index": selected, "id": new_id, "count": len(updated)}


def atomic_write(target: Path, data: bytes) -> None:
    fd, temp = tempfile.mkstemp(prefix=".blue-", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, target)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def backup_file(backup_root: Path, name: str, data: bytes) -> None:
    folder = backup_root / name
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = folder / f"{stamp}-{file_hash(data)[:10]}.bak"
    atomic_write(target, data)
    for old in sorted(folder.glob("*.bak"))[:-20]:
        old.unlink()


# Pokémon Essentials / Animated Pokémon System stores sprites in PNG, including
# multi-frame horizontal strips; GIFs may also contain animated frames.
SPRITE_FOLDERS = {
    "front": "Front", "back": "Back",
    "front-shiny": "Front shiny", "back-shiny": "Back shiny",
}
SPRITE_EXTENSIONS = ("png", "gif")
MAX_SPRITE_BYTES = 5_000_000


def sprite_location(game_root: Path, species: str, kind: str) -> Path:
    if (not isinstance(species, str)
            or not re.fullmatch(r"[A-Za-z0-9_]{1,80}", species)
            or not isinstance(kind, str) or kind not in SPRITE_FOLDERS):
        raise EditorError("Espécie ou variante de sprite inválida.")
    # Restrict to exactly the allowed Pokémon graphics subdirectory.
    return game_root / "Graphics" / "Pokemon" / SPRITE_FOLDERS[kind]


def sprite_files(game_root: Path, species: str, kind: str) -> list[Path]:
    parent = sprite_location(game_root, species, kind)
    if parent.is_symlink():
        raise EditorError("Diretório de sprites não pode ser um link simbólico.")
    found = []
    for ext in SPRITE_EXTENSIONS:
        file = parent / (species + "." + ext)
        if file.is_symlink():
            raise EditorError("Sprite não pode ser um link simbólico.")
        if file.is_file():
            found.append(file)
    return found


def sprite_dimensions(data: bytes, extension: str) -> tuple[int, int, str]:
    if extension == "png":
        if (len(data) < 45 or not data.startswith(b"\x89PNG\r\n\x1a\n")
                or data[12:16] != b"IHDR"
                or int.from_bytes(data[8:12], "big") != 13
                or not data.endswith(b"IEND\xaeB\x60\x82")):
            raise EditorError("PNG inválido ou incompleto.")
        crc = zlib.crc32(data[12:29]) & 0xFFFFFFFF
        if crc != int.from_bytes(data[29:33], "big"):
            raise EditorError("Cabeçalho PNG corrompido (CRC).")
        width, height = struct.unpack(">II", data[16:24])
        kind = "PNG em faixa" if width > height * 2 else "PNG estático"
    elif extension == "gif":
        if (len(data) < 24 or data[:6] not in (b"GIF87a", b"GIF89a")
                or data[-1] != 0x3B):
            raise EditorError("GIF inválido ou incompleto.")
        width, height = struct.unpack("<HH", data[6:10])
        kind = "GIF"
    else:
        raise EditorError("Use PNG estático, PNG em faixa ou GIF.")
    if not 1 <= width <= 4096 or not 1 <= height <= 4096:
        raise EditorError("Dimensões do sprite fora do intervalo permitido (1–4096 px).")
    return width, height, kind


def sprite_metadata(game_root: Path, species: str, kind: str) -> dict:
    found = sprite_files(game_root, species, kind)
    file = found[0] if found else None
    result = {"species": species, "kind": kind, "exists": bool(file),
              "conflict": len(found) > 1, "file": None}
    if file:
        raw = file.read_bytes()
        width, height, mode = sprite_dimensions(raw, file.suffix[1:].lower())
        result["file"] = {"name": file.name, "format": file.suffix[1:].lower(),
                          "mode": mode, "width": width, "height": height,
                          "size": len(raw), "hash": file_hash(raw)}
    return result


def save_sprite(game_root: Path, backup_root: Path, species: str, kind: str,
                name: str, content: str, mode: str, expected_hash: str) -> dict:
    parent = sprite_location(game_root, species, kind)
    if not isinstance(name, str) or name.rsplit(".", 1)[-1].lower() not in SPRITE_EXTENSIONS:
        raise EditorError("Escolha um arquivo PNG ou GIF.")
    if mode not in ("static", "animated"):
        raise EditorError("Selecione imagem estática ou animada.")
    extension = name.rsplit(".", 1)[-1].lower()
    if not isinstance(content, str) or len(content) > MAX_SPRITE_BYTES * 2:
        raise EditorError("Imagem muito grande.")
    try:
        data = base64.b64decode(content, validate=True)
    except (binascii.Error, ValueError) as error:
        raise EditorError("Base64 da imagem inválido.") from error
    if len(data) < 24 or len(data) > MAX_SPRITE_BYTES:
        raise EditorError("Imagem vazia ou maior que 5 MB.")
    width, height, detected = sprite_dimensions(data, extension)
    if mode == "static" and (extension != "png" or detected != "PNG estático"):
        raise EditorError("Para sprite estático use PNG de quadro único (não uma faixa animada).")
    if mode == "animated" and extension == "png" and detected != "PNG em faixa":
        raise EditorError("Para PNG animado, use uma faixa horizontal com mais de 2 quadros.")
    if mode == "animated" and extension == "gif" and not data.startswith((b"GIF87a", b"GIF89a")):
        raise EditorError("GIF inválido.")
    with EDIT_LOCK:
        old_files = sprite_files(game_root, species, kind)
        current = old_files[0] if old_files else None
        old_hash = file_hash(current.read_bytes()) if current else ""
        if not isinstance(expected_hash, str) or expected_hash != old_hash:
            raise EditorError("Sprite alterado desde a visualização. Atualize a página.", 409)
        parent.mkdir(parents=True, exist_ok=True)
        destination = parent / (species + "." + extension)
        # Save the original assets before replacing/removing either extension.
        for existing in old_files:
            backup_file(backup_root, f"sprites/{SPRITE_FOLDERS[kind]}/{existing.name}",
                        existing.read_bytes())
        atomic_write(destination, data)
        # Avoid .gif and .png versions silently competing in pbResolveBitmap.
        for existing in old_files:
            if existing != destination:
                existing.unlink()
    return sprite_metadata(game_root, species, kind)


def metric_target(root: Path, species: str) -> tuple[str,str]:
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{1,63}", species or ""):
        raise EditorError("Identificador do Pokémon inválido.")
    match = re.fullmatch(r"([A-Z][A-Z0-9_]+)_(\d+)", species)
    if match and int(match.group(2)) > 0:
        return "pokemon_metrics_forms.txt", match.group(1) + "," + str(int(match.group(2)))
    return "pokemon_metrics.txt", species


def pokemon_metrics(root: Path, species: str) -> dict:
    filename, key = metric_target(root, species)
    file = pbs_path(root, filename)
    raw, content = read_text(file)
    found = next((s for s in sections_in(content) if s["id"] == key), None)
    block = section_lines(content, found) if found else ""
    values = {f["key"]: f["value"] for f in extract_fields(block)}
    def pair(field, default="0,0"):
        try:
            parts = [int(x.strip()) for x in values.get(field,default).split(",")]
            if len(parts) < 2:
                raise ValueError()
            return parts
        except ValueError:
            return [0,0]
    return {"species":species,"header":key,"file":filename,"exists":bool(found),
            "hash":file_hash(raw),"front":pair("FrontSprite"),"back":pair("BackSprite"),
            "speed":pair("AnimationSpeed"),"index":found["index"] if found else -1}


def save_pokemon_metrics(root: Path, backups: Path, obj: dict) -> dict:
    species = obj.get("species", "")
    data = pokemon_metrics(root, species)
    values = {}
    for name in ("front", "back"):
        parts=obj.get(name)
        if not isinstance(parts,list) or len(parts)!=3 or any(type(n)!=int for n in parts):
            raise EditorError(name+" exige [X,Y,escala].")
        if any(abs(n)>250 for n in parts[:2]) or not 1 <= parts[2] <= 8:
            raise EditorError("Posição permitida: -250 a 250; escala: 1 a 8.")
        values[name]=parts
    speed=obj.get("speed")
    if not isinstance(speed,list) or len(speed)!=2 or any(type(n)!=int or not 0<=n<=4 for n in speed):
        raise EditorError("Velocidade exige dois valores de 0 a 4.")
    if obj.get("expectedHash") != data["hash"]:
        raise EditorError("Métricas alteradas desde a leitura; atualize a página.",409)
    # No .rxdata or runtime manipulation here: this writes the native PBS schema.
    lines=["["+data["header"]+"]",
           "FrontSprite = "+",".join(map(str,values["front"])),
           "BackSprite = "+",".join(map(str,values["back"])),
           "AnimationSpeed = "+",".join(map(str,speed))]
    old = section_lines(read_text(pbs_path(root, data["file"]))[1],
                        sections_in(read_text(pbs_path(root,data["file"]))[1])[data["index"]]) if data["exists"] else ""
    extra=[line for line in old.splitlines()[1:] if not
           re.match(r"^\s*(?:FrontSprite|BackSprite|AnimationSpeed)\s*=",line)]
    lines.extend(line for line in extra if line and not line.startswith("#-----------------"))
    result=save_section(root,data["file"],data["index"],data["hash"],
                        "\n".join(lines)+"\n",backups)
    return {"ok":True,**pokemon_metrics(root,species),"saved":result["ok"]}


def build_handler(game_root: Path, backup_root: Path, port: int):
    class Handler(BaseHTTPRequestHandler):
        server_version = "BlueStudio/0.1"

        def send_json(self, code: int, obj):
            payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def params(self):
            return parse_qs(urlsplit(self.path).query)

        def param(self, key: str, default=None):
            return self.params().get(key, [default])[0]

        def error(self, exception):
            if isinstance(exception, EditorError):
                self.send_json(exception.status, {"error": str(exception)})
            else:
                print("Blue Studio error:", repr(exception), file=sys.stderr)
                self.send_json(500, {"error": "Erro interno. Consulte o terminal do servidor."})

        def do_GET(self):
            try:
                p = urlsplit(self.path).path
                if p == "/api/status":
                    files = list((game_root / "PBS").glob("*.txt")) if (game_root / "PBS").is_dir() else []
                    self.send_json(200, {"gameReady": (game_root / "Game.exe").is_file(), "pbsReady": bool(files), "gameDir": str(game_root), "pbsFiles": len(files), "origin": "HazyCrazy/Pokemon-Decades", "version": "0.1.0"})
                elif p == "/api/files":
                    files = [{"name": f.name, "size": f.stat().st_size} for f in (game_root / "PBS").glob("*.txt") if f.is_file()] if (game_root / "PBS").is_dir() else []
                    self.send_json(200, {"files": sorted(files, key=lambda f: f["name"].casefold())})
                elif p == "/api/file":
                    name = self.param("file", "")
                    raw, content = read_text(pbs_path(game_root, name))
                    self.send_json(200, {"file": name, "hash": file_hash(raw), "raw": content, "count": len(sections_in(content))})
                elif p == "/api/sections":
                    name = self.param("file", "")
                    raw, content = read_text(pbs_path(game_root, name))
                    s = sections_in(content)
                    self.send_json(200, {"file": name, "hash": file_hash(raw), "sections": [{"index": x["index"], "id": x["id"], "label": x["label"]} for x in s]})
                elif p == "/api/section":
                    name = self.param("file", "")
                    raw, content = read_text(pbs_path(game_root, name))
                    ix = int(self.param("index", "-1"))
                    s = sections_in(content)
                    if ix < 0 or ix >= len(s):
                        raise EditorError("Seção não encontrada.", 404)
                    chunk = section_lines(content, s[ix])
                    self.send_json(200, {"file": name, "hash": file_hash(raw), "index": ix, "id": s[ix]["id"], "raw": chunk, "fields": extract_fields(chunk)})
                elif p == "/api/backups":
                    name = self.param("file", "")
                    pbs_path(game_root, name)
                    b = backup_root / name
                    files = [{"name": f.name, "size": f.stat().st_size} for f in sorted(b.glob("*.bak"), reverse=True)[:20]] if b.is_dir() else []
                    self.send_json(200, {"backups": files})
                elif p == "/api/pokemon/catalog":
                    self.send_json(200, {
                        "types": sorted(pbs_catalog(game_root, "types")),
                        "abilities": sorted(pbs_catalog(game_root, "abilities")),
                        "moves": sorted(pbs_catalog(game_root, "moves")),
                        "speciesCount": len(species_catalog(game_root))
                    })
                elif p == "/api/pokemon/metrics":
                    self.send_json(200, pokemon_metrics(game_root, self.param("species", "")))
                elif p == "/api/sprite-info":
                    species = self.param("species", "")
                    kind = self.param("kind", "front")
                    self.send_json(200, sprite_metadata(game_root, species, kind))
                elif p == "/api/sprite":
                    species = self.param("species", "")
                    kind = self.param("kind", "front")
                    found = sprite_files(game_root, species, kind)
                    if not found:
                        raise EditorError("Sprite não encontrado.", 404)
                    target = found[0]
                    if target.stat().st_size > MAX_SPRITE_BYTES:
                        raise EditorError("Sprite ultrapassa 5 MB.", 413)
                    raw = target.read_bytes()
                    extension = target.suffix[1:].lower()
                    sprite_dimensions(raw, extension)
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png" if extension == "png" else "image/gif")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.send_header("Content-Length", str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)
                elif p == "/" or p in ("/index.html", "/app.js", "/sprites.js", "/navigation.js", "/style.css", "/studio-shell.css"):
                    requested = "index.html" if p == "/" else p.lstrip("/")
                    data = (WEB / requested).read_bytes()
                    content_type = mimetypes.guess_type(requested)[0] or "application/octet-stream"
                    self.send_response(200)
                    self.send_header("Content-Type", content_type + ("; charset=utf-8" if content_type.startswith("text/") or content_type.endswith("javascript") else ""))
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    self.send_json(404, {"error": "Rota não encontrada."})
            except (ValueError, OSError) as ex:
                self.error(EditorError(str(ex), 400))
            except Exception as ex:
                self.error(ex)

        def do_POST(self):
            try:
                origin = self.headers.get("Origin", "")
                expected = (f"http://127.0.0.1:{port}", f"http://localhost:{port}")
                if (origin and origin not in expected) or self.headers.get("X-Blue-Studio", "") != "1":
                    raise EditorError("Requisição não autorizada (somente editor local).", 403)
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > MAX_POST or "application/json" not in self.headers.get("Content-Type", ""):
                    raise EditorError("JSON inválido ou maior que 8 MB.", 413)
                obj = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(obj, dict):
                    raise EditorError("Corpo inválido.")
                p = urlsplit(self.path).path
                if p == "/api/save":
                    result = save_section(game_root, obj.get("file", ""), obj.get("index"), obj.get("hash", ""), obj.get("raw", ""), backup_root)
                    self.send_json(200, result)
                elif p == "/api/file":
                    name, expected, content = obj.get("file", ""), obj.get("hash", ""), obj.get("raw", "")
                    if not isinstance(content, str) or len(content.encode("utf-8")) > 6_000_000 or "\x00" in content:
                        raise EditorError("Conteúdo inválido ou maior que 6 MB.")
                    path = pbs_path(game_root, name)
                    with EDIT_LOCK:
                        old = path.read_bytes()
                        if file_hash(old) != expected:
                            raise EditorError("Arquivo alterado. Recarregue antes de salvar.", 409)
                        data = (b"\xef\xbb\xbf" if old.startswith(b"\xef\xbb\xbf") else b"") + content.encode("utf-8")
                        backup_file(backup_root, name, old)
                        atomic_write(path, data)
                    self.send_json(200, {"ok": True, "hash": file_hash(data)})
                elif p == "/api/restore":
                    name, filename, expected = obj.get("file", ""), obj.get("backup", ""), obj.get("hash", "")
                    path = pbs_path(game_root, name)
                    if not isinstance(filename, str) or not re.fullmatch(r"\d{8}T\d{12}Z-[0-9a-f]{10}\.bak", filename):
                        raise EditorError("Backup inválido.")
                    source = (backup_root / name / filename).resolve()
                    if source.parent != (backup_root / name).resolve() or not source.is_file():
                        raise EditorError("Backup não encontrado.", 404)
                    with EDIT_LOCK:
                        raw = path.read_bytes()
                        if file_hash(raw) != expected:
                            raise EditorError("Arquivo modificado. Recarregue antes de restaurar.", 409)
                        data = source.read_bytes()
                        backup_file(backup_root, name, raw)
                        atomic_write(path, data)
                    self.send_json(200, {"ok": True, "hash": file_hash(data)})
                elif p == "/api/pokemon/new":
                    try:
                        response = create_species(game_root, backup_root, obj,lock=EDIT_LOCK,
                            backup_file=backup_file,atomic_write=atomic_write,
                            read_text=read_text,file_hash=file_hash)
                    except PokemonValidationError as exc:
                        raise EditorError(str(exc)) from exc
                    self.send_json(200,response)
                elif p == "/api/pokemon/validate":
                    try:
                        response = validate_pokemon(game_root,obj.get("raw",""))
                    except PokemonValidationError as exc:
                        raise EditorError(str(exc)) from exc
                    self.send_json(200,response)
                elif p == "/api/pokemon/metrics":
                    self.send_json(200,save_pokemon_metrics(game_root,backup_root,obj))
                elif p == "/api/pokemon/compile":
                    if os.name != "nt":
                        raise EditorError("Compilação do Essentials exige Windows com o jogo local.",400)
                    shortcut=game_root/"Game.exe - Debug Mode.lnk"
                    exe=game_root/"Game.exe"
                    if shortcut.is_file():
                        os.startfile(str(shortcut))
                        self.send_json(200,{"ok":True,"launched":True,
                            "message":"Atalho Debug Mode aberto. Em Debug > Files > Compile data, compile os PBS. Verifique a confirmação no console."})
                    elif exe.is_file():
                        subprocess.Popen([str(exe)],cwd=str(game_root),close_fds=True)
                        self.send_json(200,{"ok":True,"launched":True,
                            "message":"Game.exe aberto sem garantia de Debug. Para compilar, inicie pelo RPG Maker XP em Debug, segure Ctrl durante o início ou use Debug > Files > Compile data."})
                    else:
                        raise EditorError("Game.exe não encontrado.",404)
                elif p == "/api/sprite-upload":
                    result = save_sprite(
                        game_root, backup_root, obj.get("species", ""),
                        obj.get("kind", ""), obj.get("filename", ""),
                        obj.get("data", ""), obj.get("mode", ""),
                        obj.get("expectedHash", ""))
                    self.send_json(200, result)
                elif p == "/api/launch":
                    exe = game_root / "Game.exe"
                    if not exe.is_file():
                        raise EditorError("Game.exe não está instalado. Use BAIXAR_BASE_DECADES.bat.", 404)
                    if os.name != "nt":
                        raise EditorError("A execução direta de Game.exe está habilitada somente no Windows.", 400)
                    subprocess.Popen([str(exe)], cwd=str(game_root), close_fds=True)
                    self.send_json(200, {"ok": True, "message": "Jogo iniciado."})
                else:
                    raise EditorError("Rota não encontrada.", 404)
            except (ValueError, json.JSONDecodeError) as ex:
                self.error(EditorError("Dados inválidos: " + str(ex)))
            except Exception as ex:
                self.error(ex)

        def log_message(self, fmt, *args):
            if not urlsplit(self.path).path.startswith("/api/sprite"):
                print("[Blue Studio]", fmt % args)
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-dir", default=os.environ.get("BLUE_GAME_DIR", str(DEFAULT_GAME)))
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    root = Path(args.game_dir).expanduser().resolve()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), build_handler(root, BACKUPS, args.port))
    url = f"http://127.0.0.1:{args.port}"
    print("\n=== Blue Studio | Pokémon Blue Dessastre Paradoxal ===")
    print("Editor:", url)
    print("Jogo local:", root)
    print("Pressione Ctrl+C para encerrar.\n")
    if not args.no_browser:
        threading.Timer(0.35, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Servidor encerrado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
