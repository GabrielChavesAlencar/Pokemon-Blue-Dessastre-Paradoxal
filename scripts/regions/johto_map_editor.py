"""Local visual Johto tile editor (http://127.0.0.1:8771/).

Saves real RPG Maker XP Map600–699 files with backups. Publishes only a JSON
tile-delta to the repository's main branch with the user's existing GitHub CLI
authentication. Never publishes games, third-party tilesets, personal saves,
or local event script content. Never opens a remote listener.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/regions"))

from server.ruby_marshal import RubyObject, loads, text
from build_johto_elm_lab_v1 import table_values
from johto_opening import set_tiles
from stage import serialize
import johto_qa
import johto_map_patches as patches

REPO = "GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal"
UI = ROOT / "web/johto-map-editor.html"
MAX_REQUEST = 1_500_000
MAX_MAP_BYTES = 20_000_000
LOCK = threading.RLock()


class EditorError(Exception):
    def __init__(self, message: str, code: int = 400):
        super().__init__(message)
        self.code = code


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _file(path):
    if path.is_symlink() or not path.is_file():
        raise EditorError("Arquivo esperado não encontrado na instalação: " + path.name, 404)
    return path


def _game_map(game: Path, mid: int):
    mid = patches.map_id(mid)
    target = game / "Data" / f"Map{mid:03}.rxdata"
    _file(target)
    if target.stat().st_size > MAX_MAP_BYTES:
        raise EditorError("Mapa Johto maior que o limite de segurança")
    raw = target.read_bytes()
    obj = loads(raw)
    if not isinstance(obj, RubyObject) or obj.name != "RPG::Map":
        raise EditorError("Arquivo não é um mapa RPG Maker XP")
    return target, raw, obj


def _tilesets(game: Path):
    path = _file(game / "Data/Tilesets.rxdata")
    if path.stat().st_size > 20_000_000:
        raise EditorError("Tilesets.rxdata maior que o limite")
    sets = loads(path.read_bytes())
    if not isinstance(sets, list):
        raise EditorError("Lista de tilesets RMXP inválida")
    return sets


def catalog(game: Path):
    path = game / "Data/MapInfos.rxdata"
    infos = loads(path.read_bytes()) if path.is_file() and not path.is_symlink() else {}
    if not isinstance(infos, dict):
        infos = {}
    result = []
    for mid in range(600, 700):
        target = game / "Data" / f"Map{mid:03}.rxdata"
        if target.is_file() and not target.is_symlink():
            entry = infos.get(mid)
            name = text(entry.attrs.get("@name")) if isinstance(entry, RubyObject) else ""
            result.append({"id": mid, "name": name or f"Map{mid:03}"})
    return result


def details(project: Path, game: Path, mid: int):
    _, raw, obj = _game_map(game, mid)
    tilesets = _tilesets(game)
    name, width, height, cells, flags = patches.inspect_map(obj, tilesets, mid)
    events = []
    for key, event in sorted(obj.attrs["@events"].items()):
        if not isinstance(event, RubyObject):
            continue
        warp = None
        for page in event.attrs.get("@pages", []):
            for command in page.attrs.get("@list", []):
                if command.attrs.get("@code") == 201:
                    args = command.attrs.get("@parameters", [])
                    if len(args) >= 4 and args[0] == 0:
                        warp = {"map": args[1], "x": args[2], "y": args[3]}
                    break
            if warp:
                break
        events.append({"id": event.attrs.get("@id", key),
                       "name": text(event.attrs.get("@name"))[:100],
                       "x": event.attrs["@x"], "y": event.attrs["@y"],
                       "pages": len(event.attrs.get("@pages", [])), "warp": warp})
    patch_path = patches.patch_path(project, mid)
    patch = patches.read_patch(project, mid)
    return {"id": mid, "width": width, "height": height, "depth": 3,
            "cells": cells, "tileset": name, "flags": list(flags),
            "events": events, "map_hash": sha(raw),
            "patch_hash": sha(patch_path.read_bytes()) if patch else None,
            "saved_edits": len(patch["edits"]) if patch else 0,
            "source_path": str(game / "Data" / f"Map{mid:03}.rxdata")}


def _running_game():
    if os.name != "nt":
        return False
    try:
        process = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Game.exe", "/FO", "CSV", "/NH"],
                                 capture_output=True, text=True, timeout=8)
        return process.returncode == 0 and '"Game.exe"' in process.stdout
    except (OSError, subprocess.TimeoutExpired):
        return False


def _atomic_changes(blobs: dict[Path, bytes], backups: Path):
    """All files backed up; restore originals if any filesystem swap fails."""
    backups.mkdir(parents=True, exist_ok=False)
    originals = {}
    pending = []
    changed = []
    try:
        for path, raw in blobs.items():
            if path.is_symlink() or path.parent.is_symlink():
                raise EditorError("Não sobrescrever arquivo ou pasta symlink")
            path.parent.mkdir(parents=True, exist_ok=True)
            original = path.read_bytes() if path.is_file() else None
            originals[path] = original
            if original is not None:
                backup = backups / path.name
                # All files have distinct names: Map674.rxdata, Map674.json,
                # blue-johto-main-preview.json.
                backup.write_bytes(original)
            temp = path.with_name(path.name + ".johto-editor-tmp")
            if temp.exists() or temp.is_symlink():
                raise EditorError("Arquivo temporário do editor já existe")
            temp.write_bytes(raw)
            pending.append(temp)
        for path, raw in blobs.items():
            temp = path.with_name(path.name + ".johto-editor-tmp")
            if sha(temp.read_bytes()) != sha(raw):
                raise EditorError("Checksum divergente antes de salvar")
            os.replace(temp, path)
            changed.append(path)
    except BaseException:
        for path in reversed(changed):
            original = originals[path]
            if original is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(original)
        raise
    finally:
        for path in pending:
            path.unlink(missing_ok=True)


def save_changes(project: Path, game: Path, payload: dict):
    mid = patches.map_id(payload.get("map_id"))
    if _running_game():
        raise EditorError("Feche o Game.exe antes de salvar. O jogo pode carregar o mapa antigo.", 409)
    operations = payload.get("changes")
    if not isinstance(operations, list) or len(operations) > patches.MAX_EDITS:
        raise EditorError("Lista de desenhos inválida ou grande demais")
    with LOCK:
        map_path, old_bytes, obj = _game_map(game, mid)
        if payload.get("map_hash") != sha(old_bytes):
            raise EditorError("Mapa alterado desde a abertura. Recarregue antes de salvar.", 409)
        sets = _tilesets(game)
        name, width, height, cells, flags = patches.inspect_map(obj, sets, mid)
        patch_path = patches.patch_path(project, mid)
        existing = patches.read_patch(project, mid)
        prior = sha(patch_path.read_bytes()) if existing else None
        if prior != payload.get("patch_hash"):
            raise EditorError("Patch mudou desde a abertura. Recarregue antes de salvar.", 409)
        merged = {(e["x"], e["y"], e["z"]): dict(e)
                  for e in existing["edits"]} if existing else {}
        if existing and existing["tileset"] != name:
            raise EditorError("Tileset mudou; não juntar patches de versões diferentes.", 409)
        for item in operations:
            if not isinstance(item, dict) or set(item) != {"x","y","z","from","to"} or any(type(v) is not int for v in item.values()):
                raise EditorError("Cada alteração deve conter x,y,z,from,to inteiros")
            x,y,z,old,new = (item[k] for k in ("x","y","z","from","to"))
            if not 0 <= x < width or not 0 <= y < height or not 0 <= z < 3:
                raise EditorError("Coordenadas fora do mapa")
            index = x + width * (y + height * z)
            if old != cells[index]:
                raise EditorError("Tile atual diverge do editor; atualize a página.",409)
            if new == old:
                continue
            previous = merged.get((x,y,z))
            original = previous["before"] if previous else old
            if new == original:
                merged.pop((x,y,z), None)
            else:
                merged[(x,y,z)] = {"x":x,"y":y,"z":z,
                                   "before":original,"after":new}
        # Apply the delta to the full in-memory map BEFORE any filesystem writes.
        new_patch = {"schema":patches.SCHEMA, "map_id":mid, "tileset":name,
                     "edits":sorted(merged.values(),key=lambda r:(r["z"],r["y"],r["x"]))}
        patches.validate_patch_format(new_patch, mid)
        if not operations:
            raise EditorError("Nada para salvar")
        # Current installed map may already include earlier changes; apply
        # only the submitted differences, but enforce collision and events.
        delta = {"schema":1,"map_id":mid,"tileset":name,"edits":[
            {"x":a["x"],"y":a["y"],"z":a["z"],
             "before":a["from"],"after":a["to"]}
            for a in operations if a["from"] != a["to"]]}
        updated = patches.apply_patch(obj, sets, mid, delta)
        if not updated:
            raise EditorError("Nenhuma alteração nova")
        native = serialize(obj, johto_qa.EVENT_CLASSES)
        # Refuse any accidental changes to non-tile attributes/event scripts.
        verified = loads(native)
        if verified.attrs["@events"] != loads(old_bytes).attrs["@events"]:
            raise EditorError("Validação falhou: eventos nativos foram alterados")
        blobs = {map_path: native, patch_path: patches.encode_patch(new_patch)}
        proof = game / "Data/blue-johto-main-preview.json"
        if proof.is_file() and not proof.is_symlink():
            data = json.loads(proof.read_text("utf-8"))
            if data.get("region") != "JOHTO" or not isinstance(data.get("file_hashes"),dict):
                raise EditorError("Manifesto de Johto inesperado; não alterar")
            data["file_hashes"][f"Data/Map{mid:03}.rxdata"] = sha(native)
            data.setdefault("editor_map_patches",{})[str(mid)] = sha(blobs[patch_path])
            blobs[proof] = (json.dumps(data,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
        backup = project / ".blue-backups" / ("johto-editor-" + uuid.uuid4().hex)
        _atomic_changes(blobs,backup)
        return {"saved":True,"map_id":mid,"count":updated,
                "patch":str(patch_path.relative_to(project)),
                "map_hash":sha(native),"patch_hash":sha(blobs[patch_path]),
                "backup":str(backup),
                "note":"Mapa local atualizado; publicar na main é uma ação separada"}


def gh_binary(project: Path):
    for path in (shutil.which("gh"), project / "tools/gh/gh.exe",
                 project / ".blue-tools/gh/gh.exe"):
        if path and Path(path).is_file():
            return str(path)
    raise EditorError("GitHub CLI (gh) não encontrado. Instale e execute 'gh auth login' uma vez.", 409)


def _gh(project, args, body=None, allow_404=False):
    gh = gh_binary(project)
    try:
        result = subprocess.run([gh,"api",*args],input=body,capture_output=True,
                                text=True,timeout=30,check=False)
    except (OSError,subprocess.TimeoutExpired) as error:
        raise EditorError("Falha ao consultar GitHub: " + type(error).__name__, 502) from error
    if result.returncode != 0:
        if allow_404 and ("HTTP 404" in result.stderr or "Not Found" in result.stderr):
            return None
        raise EditorError("Falha no GitHub. Confira 'gh auth status', acesso de escrita ao repositório e conexão.", 502)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise EditorError("Resposta inesperada da API do GitHub", 502) from error


def remote(project: Path, mid: int):
    mid = patches.map_id(mid)
    relative = f"data/regions/johto-map-edits/Map{mid:03}.json"
    remote = _gh(project, [f"repos/{REPO}/contents/{relative}?ref=main"],allow_404=True)
    local = patches.patch_path(project, mid)
    local_bytes = local.read_bytes() if local.is_file() and not local.is_symlink() else None
    if remote is None:
        return {"exists":False,"sha":None,"in_sync":local_bytes is None}
    if not isinstance(remote,dict) or remote.get("type") != "file":
        raise EditorError("Caminho remoto não é um arquivo comum")
    blob = base64.b64decode(remote.get("content",""),validate=False)
    return {"exists":True,"sha":remote["sha"],"in_sync":blob == local_bytes}


class Session:
    def __init__(self, project:Path, game:Path):
        self.project,self.game=project,game
        self.token=secrets.token_hex(24)
        self.publish_baseline={}


def publish(session: Session, mid:int, expected_sha, expected_patch_hash):
    mid=patches.map_id(mid)
    local=patches.patch_path(session.project,mid)
    with LOCK:
        if not local.is_file() or local.is_symlink():
            raise EditorError("Salve alterações no editor antes de publicar",409)
        raw=local.read_bytes()
        if sha(raw)!=expected_patch_hash:
            raise EditorError("O patch mudou desde o último salvamento",409)
        patches.read_patch(session.project,mid)
        baseline=session.publish_baseline.get(mid)
        if baseline is None or not baseline["in_sync"]:
            raise EditorError("Clique em 'Verificar GitHub' com a versão local sincronizada antes de editar/publicar",409)
        current=remote(session.project,mid)
        if current["sha"]!=expected_sha or current["sha"]!=baseline["sha"]:
            raise EditorError("Outro commit atualizou este mapa na main. Atualize o projeto e compare as edições.",409)
        body={"message":f"feat(johto-map): editar Map{mid:03} pelo editor visual",
              "content":base64.b64encode(raw).decode("ascii"),"branch":"main"}
        if current["sha"]:
            body["sha"]=current["sha"]
        output=_gh(session.project,["--method","PUT",
                       f"repos/{REPO}/contents/data/regions/johto-map-edits/Map{mid:03}.json",
                       "--input","-"],body=json.dumps(body))
        if not isinstance(output,dict) or "commit" not in output:
            raise EditorError("GitHub não confirmou o commit de Johto",502)
        next_sha=output.get("content",{}).get("sha")
        session.publish_baseline[mid]={"sha":next_sha,"in_sync":True}
        return {"published":True,"map_id":mid,
                "branch":"main","url":output["commit"].get("html_url",""),
                "file":f"data/regions/johto-map-edits/Map{mid:03}.json",
                "sha":next_sha}


def make_handler(session: Session):
    class Handler(BaseHTTPRequestHandler):
        server_version="JohtoMapEditor/1.0"

        def log_message(self, format, *args):
            sys.stderr.write("[JOHTO EDITOR] "+format%args+"\n")

        def json_response(self,status,data):
            raw=json.dumps(data,ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Content-Length",str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def binary(self,body,typ):
            self.send_response(200)
            self.send_header("Content-Type",typ)
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Cache-Control","no-store")
            self.send_header("Content-Length",str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def query_id(self):
            try:
                return patches.map_id(int(parse_qs(urlsplit(self.path).query)["id"][0]))
            except (ValueError,KeyError,IndexError,TypeError) as exc:
                raise EditorError("Selecione um mapa Johto válido") from exc

        def do_GET(self):
            try:
                path=urlsplit(self.path).path
                if path in ("/","/index.html"):
                    self.binary(_file(UI).read_bytes(),"text/html; charset=utf-8")
                elif path=="/api/maps":
                    self.json_response(200,{"maps":catalog(session.game)})
                elif path=="/api/map":
                    self.json_response(200,details(session.project,session.game,self.query_id()))
                elif path=="/api/tileset":
                    mid=self.query_id()
                    _,_,obj=_game_map(session.game,mid)
                    sets=_tilesets(session.game)
                    name,_,_,_,_=patches.inspect_map(obj,sets,mid)
                    if not re.fullmatch(r"[A-Za-z0-9_ ().-]{1,120}",name):
                        raise EditorError("Nome gráfico de tileset inválido")
                    folder=(session.game/"Graphics/Tilesets").resolve()
                    png=(folder/(name+".png")).resolve()
                    if png.parent!=folder:
                        raise EditorError("Arquivo gráfico fora da instalação")
                    raw=_file(png).read_bytes()
                    if len(raw)>32_000_000 or not raw.startswith(b"\x89PNG\r\n\x1a\n"):
                        raise EditorError("PNG de tileset inválido")
                    self.binary(raw,"image/png")
                elif path=="/api/remote":
                    mid=self.query_id()
                    status=remote(session.project,mid)
                    session.publish_baseline[mid]=status
                    self.json_response(200,status)
                else:
                    self.json_response(404,{"error":"Rota não encontrada"})
            except (EditorError,patches.PatchError,ValueError,OSError,KeyError) as err:
                self.json_response(getattr(err,"code",400),{"error":str(err)})

        def do_POST(self):
            try:
                parsed=urlsplit(self.path).path
                origin=self.headers.get("Origin","")
                expected=f"http://127.0.0.1:{self.server.server_port}"
                if origin!=expected:
                    raise EditorError("Origem não autorizada para editar arquivos locais",403)
                if self.headers.get("X-Johto-Editor-Token") != session.token:
                    raise EditorError("Token local de edição inválido",403)
                count=int(self.headers.get("Content-Length","0"))
                if not 0<count<=MAX_REQUEST:
                    raise EditorError("Requisição de edição excede limite",413)
                body=json.loads(self.rfile.read(count))
                if not isinstance(body,dict):
                    raise EditorError("JSON de edição inválido")
                if parsed=="/api/save":
                    result=save_changes(session.project,session.game,body)
                    self.json_response(200,result)
                elif parsed=="/api/publish":
                    result=publish(session,body.get("map_id"),
                                   body.get("remote_sha"),body.get("patch_hash"))
                    self.json_response(200,result)
                else:
                    self.json_response(404,{"error":"Rota não encontrada"})
            except (EditorError,patches.PatchError,ValueError,OSError,KeyError,json.JSONDecodeError) as err:
                self.json_response(getattr(err,"code",400),{"error":str(err)})

    # Insert the random session-only anti-CSRF secret as a response header on
    # HTML, never on a network-accessible server. Script loads it from a meta.
    old_binary=Handler.binary
    def serve_binary(self,body,typ):
        if typ.startswith("text/html"):
            body=body.replace(b"__JOHTO_CSRF__",session.token.encode("ascii"))
        return old_binary(self,body,typ)
    Handler.binary=serve_binary
    return Handler


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir",type=Path,default=ROOT/"game")
    parser.add_argument("--port",type=int,default=8771)
    parser.add_argument("--no-browser",action="store_true")
    args=parser.parse_args(argv)
    if not 1024<=args.port<=65535:
        parser.error("Porta inválida")
    game=args.game_dir.resolve()
    if not game.is_dir() or not (game/"Game.exe").is_file():
        parser.error("Instale o Game.exe pelo Blue-Story antes de editar mapas")
    server=ThreadingHTTPServer(("127.0.0.1",args.port),
                               make_handler(Session(ROOT,game)))
    url=f"http://127.0.0.1:{args.port}/"
    print("Editor visual Johto:",url,flush=True)
    print("Publicar na main exige GitHub CLI com 'gh auth login'.",flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__=="__main__":
    raise SystemExit(main())
