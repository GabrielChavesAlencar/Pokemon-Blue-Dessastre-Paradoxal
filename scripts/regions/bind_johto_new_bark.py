"""Vincula IDs/hashes REAIS de cinco mapas New Bark, mas não inventa XY.

Após stage_johto + build_johto_interiors, confere toda a prévia com
verify_johto, preenche somente MapIDs e SHA-256 em uma CÓPIA do template de
eventos. Portas, NPCs, sprite, destino e spawn permanecem não verificados.
NÃO altera game/, nem ativa Johto nem cria prova de gameplay.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import tempfile
from pathlib import Path

from audit_johto import ROOT, checksum, read_map_data
from build_johto_events import read_json
from verify_johto import inspect
from server.ruby_marshal import RubyObject

DEFAULT_PREVIEW = ROOT / ".blue-work/johto-staging-interiors"
DEFAULT_SPEC = ROOT / "data/regions/johto-new-bark-events.json"
DEFAULT_OUTPUT = ROOT / ".blue-work/johto-new-bark-bound.json"
HASH = re.compile(r"[0-9a-f]{64}\Z")
REQUIRED = {
    "JOHTO_NEW_BARK_PLAYER_HOME_2F",
    "JOHTO_NEW_BARK_PLAYER_HOME_1F",
    "JOHTO_NEW_BARK_TOWN",
    "JOHTO_NEW_BARK_ELM_LAB",
    "JOHTO_ROUTE_29",
}


def bind(preview: Path, game: Path, template: dict, *, root: Path = ROOT) -> dict:
    root = root.resolve()
    allowed = (root / ".blue-work").resolve()
    preview = preview.absolute()
    game = game.absolute()
    if preview.is_symlink() or not preview.resolve().is_relative_to(allowed):
        raise ValueError("Preview de Johto deve estar em .blue-work/")
    verified = inspect(preview, game, root=root)
    if verified.get("status") != "STRUCTURAL_PREVIEW_VALIDATED_NOT_PLAYABLE":
        raise ValueError("Preview de geometria sem verificação")
    manifest_path = preview / "johto-stage.json"
    manifest = read_json(manifest_path)
    if (manifest.get("region"), manifest.get("status"),
            manifest.get("can_install"), manifest.get("not_playable")) != (
            "JOHTO", "GEOMETRY_PREVIEW_ONLY", False, True):
        raise ValueError("Manifesto da prévia não é somente de terreno")
    source_hash = manifest.get("source_archive_sha256")
    if not isinstance(source_hash, str) or not HASH.fullmatch(source_hash):
        raise ValueError("Fonte RMXP sem hash verificado")
    rows = manifest.get("maps")
    if not isinstance(rows, list):
        raise ValueError("Não há mapas no staging")
    symbols = {}
    used = set()
    for row in rows:
        symbol, mid = row.get("symbol"), row.get("destination_id")
        if (not isinstance(symbol, str) or symbol in symbols
                or type(mid) is not int or mid in used
                or not 600 <= mid <= 999 or row.get("events_imported") != 0):
            raise ValueError("MapIDs duplicados/incorretos no staging")
        symbols[symbol] = mid
        used.add(mid)
    if not REQUIRED.issubset(symbols):
        raise ValueError("Faltam interiores/cidade/Route 29 reais: " +
                         ", ".join(sorted(REQUIRED - set(symbols))))
    if (template.get("schema"), template.get("region"), template.get("status")) != (
            1, "JOHTO", "EVENT_COORDINATES_REQUIRE_REAL_AUDIT"):
        raise ValueError("O template de eventos não corresponde a New Bark")
    required_rows = template.get("maps")
    if (not isinstance(required_rows, list) or len(required_rows) != 5
            or {row.get("symbol") for row in required_rows} != REQUIRED):
        raise ValueError("Template com mapas inesperados ou ausentes")
    result = copy.deepcopy(template)
    todo = []
    for row in result["maps"]:
        symbol = row["symbol"]
        if row.get("map_id") is not None or row.get("map_sha256") is not None:
            raise ValueError("Somente vincular template ainda não preenchido")
        mid = symbols[symbol]
        file = preview / "Data" / f"Map{mid:03d}.rxdata"
        room = read_map_data(file)
        if not isinstance(room, RubyObject) or room.name != "RPG::Map":
            raise ValueError("Mapa não é uma sala RMXP válida")
        if room.attrs.get("@events") != {}:
            raise ValueError("Mapa já contém eventos, proibir dupla instalação")
        row["map_id"] = mid
        row["map_sha256"] = checksum(file)
        for event in row.get("events", []):
            key = event.get("key")
            if (event.get("x") is not None or event.get("y") is not None
                    or event.get("verified_position") is not False
                    or (event.get("kind") == "handler" and event.get("sprite") is not None)
                    or (event.get("kind") == "warp" and (
                        event.get("arrival_x") is not None or
                        event.get("arrival_y") is not None))):
                raise ValueError("Template contém coordenadas/sprites não auditados: " + str(key))
            todo.append({"event": key, "symbol": symbol,
                         "map_id": mid, "required": "x/y e colisões" +
                         (", sprite real" if event.get("kind") == "handler"
                          else ", tile passável no destino")})
    start = result.get("start")
    if (not isinstance(start, dict) or
            start.get("symbol") != "JOHTO_NEW_BARK_PLAYER_HOME_2F" or
            start.get("x") is not None or start.get("y") is not None or
            start.get("verified_position") is not False or
            start.get("passability_verified") is not False):
        raise ValueError("Spawn só pode ser definido após revisão do quarto")
    todo.append({"event": "PLAYER_SPAWN", "symbol": start["symbol"],
                 "map_id": symbols[start["symbol"]],
                 "required": "x/y + tile passável e início dentro da casa"})
    result["binding_status"] = "MAP_IDS_BOUND_EVENT_POSITIONS_PENDING"
    result["can_install"] = False
    result["not_playable"] = True
    result["source_archive_sha256"] = source_hash
    result["geometry_stage_sha256"] = checksum(manifest_path)
    result["todo_review"] = todo
    return result


def publish(output: Path, spec: dict, *, root: Path = ROOT) -> None:
    allowed = (root.resolve() / ".blue-work").resolve()
    output = output.absolute()
    if (output.is_symlink() or not output.resolve().is_relative_to(allowed)
            or output.resolve() == allowed or output.exists()):
        raise ValueError("Saída deve ser NOVA e isolada em .blue-work/")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".johto-bind-", dir=output.parent) as tmp:
        temp = Path(tmp) / "bound.json"
        temp.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        if output.exists() or output.is_symlink():
            raise ValueError("Saída já criada; impedir sobrescrita")
        temp.rename(output)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, default=ROOT / "game")
    parser.add_argument("--preview", type=Path, default=DEFAULT_PREVIEW)
    parser.add_argument("--template", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = bind(args.preview, args.game, read_json(args.template))
        publish(args.output, result)
    except (ValueError, OSError, KeyError, TypeError) as err:
        print("[JOHTO][BLOQUEADO] " + str(err), file=sys.stderr)
        return 2
    print("[JOHTO] Cinco mapas vinculados a MapIDs e SHA-256 auditados.")
    print(f"[JOHTO] Faltam {len(result['todo_review'])} posições/sprites para o piloto.")
    print("[JOHTO] NÃO está jogável. Arquivo:", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
