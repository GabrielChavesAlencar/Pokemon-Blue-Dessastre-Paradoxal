"""Create a PRIVATE support ZIP with only Johto room data, never user saves.

This does not modify game/ or any source binaries. User can share this ZIP
in a chat for investigating unexpected map hashes and stair event scripts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/regions"))
from server.ruby_marshal import RubyObject, loads, text
from johto_main_preview import PROOF, READY
from diagnose_johto_bedroom import inspect

DEFAULT_OUT = ROOT / ".blue-work" / "JOHTO_DIAGNOSTICO_MAPAS.zip"
SELECTED = ("Data/Map600.rxdata", "Data/Map674.rxdata", "Data/Map675.rxdata")


def event_summary(blob: bytes):
    room = loads(blob)
    if not isinstance(room, RubyObject) or room.name != "RPG::Map":
        return {"error": "not a Ruby RPG::Map"}
    info = {"width": room.attrs.get("@width"), "height": room.attrs.get("@height"),
            "tileset_id": room.attrs.get("@tileset_id"), "events": []}
    for event in room.attrs.get("@events", {}).values():
        row = {"id": event.attrs.get("@id"), "name": text(event.attrs.get("@name")),
               "x": event.attrs.get("@x"), "y": event.attrs.get("@y"), "pages": []}
        for page in event.attrs.get("@pages", []):
            commands = []
            for command in page.attrs.get("@list", [])[:70]:
                args = command.attrs.get("@parameters", [])
                code = command.attrs.get("@code")
                # Do not export full unrelated NPC script text.
                if code in (201, 355, 655):
                    safe_args = [str(v)[:120] if not isinstance(v, int) else v
                                 for v in args[:8]]
                    commands.append({"code": code, "parameters": safe_args})
            row["pages"].append({"trigger": page.attrs.get("@trigger"),
                                 "commands": commands})
        info["events"].append(row)
    return info


def bundle(project: Path, game: Path, output: Path):
    game = game.resolve()
    output = output.resolve()
    if not output.is_relative_to((project / ".blue-work").resolve()):
        raise ValueError("A saída deve ficar dentro de .blue-work")
    if not (game / "Game.exe").is_file():
        raise ValueError("Game.exe gerenciado não encontrado")
    diag = inspect(project, game)
    result = {"status": "Johto map bytes gathered without saves",
              "diagnostic": diag, "files": {}, "events": {}}
    raw_files = {}
    for rel in SELECTED:
        path = game / rel
        if path.is_symlink() or not path.is_file():
            result["files"][rel] = {"missing": True}
            continue
        blob = path.read_bytes()
        if len(blob) > 16_000_000:
            raise ValueError("Mapa excede tamanho máximo: " + rel)
        raw_files[rel] = blob
        result["files"][rel] = {"size": len(blob),
                                "sha256": hashlib.sha256(blob).hexdigest()}
        if rel.endswith(("674.rxdata", "675.rxdata")):
            try:
                result["events"][rel] = event_summary(blob)
            except (ValueError, IndexError, KeyError, TypeError) as error:
                result["events"][rel] = {"error": str(error)}
    proof = game / PROOF
    if proof.is_file() and not proof.is_symlink():
        try:
            original = json.loads(proof.read_text("utf-8"))
            result["proof"] = {k: original.get(k)
                               for k in ("schema", "region", "status",
                                         "source_bundle_sha256", "bedroom_layout",
                                         "bedroom_stairs_warp", "bedroom_stairs_return",
                                         "map_ids", "private_hgss")}
            result["proof"]["file_hashes"] = {
                rel: original.get("file_hashes", {}).get(rel) for rel in SELECTED
            }
        except (ValueError, OSError) as error:
            result["proof_error"] = str(error)
    marker = game / READY
    if marker.is_file() and not marker.is_symlink():
        result["ready_marker"] = marker.read_text("ascii", errors="replace").strip()[:160]
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() or output.is_symlink():
        raise ValueError("ZIP de diagnóstico já existe. Renomeie/remova o ZIP antigo antes.")
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for rel, blob in raw_files.items():
            archive.writestr(rel, blob)
        archive.writestr("DIAGNOSTICO_JOHTO.json",
                         json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        archive.writestr("LEIA-ME.txt",
                         "Sem saves, dados de conta ou arquivos pessoais.\n"
                         "Contém APENAS três mapas de Johto e seus eventos do jogo.\n"
                         "Compartilhe se desejar a auditoria; nunca copie este ZIP em game/.\n")
    return {"zip": str(output), "maps": sorted(raw_files),
            "contains_saves": False, "status": result["diagnostic"]["status"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, default=ROOT / "game")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    try:
        report = bundle(ROOT, args.game_dir, args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("[JOHTO] Erro ao preparar diagnóstico privado:", error, file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
