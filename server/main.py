"""Blue Studio: local-only PBS editor for Pokémon Essentials/Decades.
Standard library only. No assets of any third-party fangame are distributed here.
"""
from __future__ import annotations

import argparse
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
                elif p == "/api/sprite":
                    # Whitelist a small fixed set of graphics paths; never trust arbitrary URLs/paths.
                    species = self.param("species", "")
                    kind = self.param("kind", "front")
                    if not re.fullmatch(r"[A-Za-z0-9_\-]+(?:_\d+)?", species or "") or kind not in ("front", "back", "front-shiny", "back-shiny", "icon"):
                        raise EditorError("Imagem inválida.")
                    sub = {"front": "Front", "back": "Back", "front-shiny": "Front shiny", "back-shiny": "Back shiny", "icon": "Icons"}[kind]
                    target = (game_root / "Graphics" / "Pokemon" / sub / (species + ".png")).resolve()
                    parent = (game_root / "Graphics" / "Pokemon" / sub).resolve()
                    if target.parent != parent or not target.is_file() or target.stat().st_size > 2_000_000:
                        raise EditorError("Sprite não encontrado.", 404)
                    data = target.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.end_headers()
                    self.wfile.write(data)
                elif p == "/" or p in ("/index.html", "/app.js", "/style.css"):
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
