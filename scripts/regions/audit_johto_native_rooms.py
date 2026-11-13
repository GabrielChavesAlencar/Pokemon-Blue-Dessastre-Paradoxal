"""Inventário SOMENTE LEITURA de salas-base para os interiores de New Bark.

Analisa mapas RMXP do game/ local; não lê/executa comandos Ruby de scripts,
não elege salas automaticamente e não escreve no game/ ou no stage.
Exporta candidatos com ID, hash, tamanho, tileset e transferências estáticas
para orientar inspeção manual de quarto, casa e laboratório.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

from audit_johto import ROOT, checksum, map_files, read_map_data
from build_johto_interiors import confirm_tile_table
from verify_johto import inspect
from server.ruby_marshal import RubyObject, text

DEFAULT_OUTPUT = ROOT / ".blue-work/johto-native-room-candidates.json"
DEFAULT_PREVIEW = ROOT / ".blue-work/johto-staging"
KEYWORDS = {
    "JOHTO_NEW_BARK_PLAYER_HOME_2F": ("bedroom", "bed", "quarto", "room", "upstairs", "2f"),
    "JOHTO_NEW_BARK_PLAYER_HOME_1F": ("home", "house", "casa", "mother", "mae", "mom"),
    "JOHTO_NEW_BARK_ELM_LAB": ("lab", "laboratory", "laboratorio", "professor", "research"),
}


def normalized(value: object) -> str:
    label = text(value)
    label = unicodedata.normalize("NFKD", label)
    label = "".join(c for c in label if not unicodedata.combining(c))
    return label.casefold()


def static_transfers(world: RubyObject) -> list[dict]:
    """Only records numeric direct warps (event code 201); never evals scripts."""
    events = world.attrs.get("@events", {})
    if not isinstance(events, dict):
        return []
    transfers = []
    for event_id, event in events.items():
        if not isinstance(event, RubyObject) or event.name != "RPG::Event":
            continue
        pages = event.attrs.get("@pages", [])
        if not isinstance(pages, list):
            continue
        for pnum, page in enumerate(pages, start=1):
            if not isinstance(page, RubyObject):
                continue
            commands = page.attrs.get("@list", [])
            if not isinstance(commands, list):
                continue
            for op in commands:
                if not isinstance(op, RubyObject) or op.attrs.get("@code") != 201:
                    continue
                params = op.attrs.get("@parameters", [])
                if (not isinstance(params, list) or len(params) < 4
                        or type(params[0]) is not int or params[0] != 0
                        or not all(type(v) is int for v in params[1:4])):
                    continue
                dest, x, y = params[1:4]
                if dest > 0 and x >= 0 and y >= 0:
                    transfers.append({"event_id": event_id, "page": pnum,
                                      "destination_id": dest, "x": x, "y": y})
    return transfers[:200]


def report(game: Path, preview: Path, *, root: Path = ROOT) -> dict:
    root = root.resolve()
    game, preview = game.absolute(), preview.absolute()
    if game.is_symlink() or game.resolve() != (root / "game").resolve():
        raise ValueError("Only project/game may be audited for native rooms")
    proof = inspect(preview, game, root=root)
    if proof["status"] != "STRUCTURAL_PREVIEW_VALIDATED_NOT_PLAYABLE":
        raise ValueError("No verified Johto geometric preview")
    native = game / "Data"
    infos = read_map_data(native / "MapInfos.rxdata")
    tiles = read_map_data(native / "Tilesets.rxdata")
    if not isinstance(infos, dict) or not isinstance(tiles, list):
        raise ValueError("Native MapInfos/Tilesets are not RMXP compatible")
    rows = []
    skipped = 0
    for mid, filename in sorted(map_files(native).items()):
        info = infos.get(mid)
        if not isinstance(info, RubyObject) or info.name != "RPG::MapInfo":
            skipped += 1
            continue
        world = read_map_data(filename)
        if not isinstance(world, RubyObject) or world.name != "RPG::Map":
            skipped += 1
            continue
        try:
            confirm_tile_table(world)
        except ValueError:
            skipped += 1
            continue
        tid = world.attrs.get("@tileset_id")
        if (type(tid) is not int or not 0 < tid < len(tiles)
                or not isinstance(tiles[tid], RubyObject)):
            skipped += 1
            continue
        name = text(info.attrs.get("@name"))
        canonical = normalized(name)
        transfers = static_transfers(world)
        events = world.attrs.get("@events", {})
        scores = {symbol: sum(4 for key in keywords if key in canonical)
                  for symbol, keywords in KEYWORDS.items()}
        # Small rooms rank higher for bedrooms than extensive caves/overworld.
        width, height = world.attrs["@width"], world.attrs["@height"]
        if width <= 24 and height <= 24:
            scores["JOHTO_NEW_BARK_PLAYER_HOME_2F"] += 1
            scores["JOHTO_NEW_BARK_PLAYER_HOME_1F"] += 1
        if len(transfers) >= 1:
            for symbol in scores:
                scores[symbol] += 1
        rows.append({
            "native_map_id": mid, "native_map_sha256": checksum(filename),
            "name": name, "width": width, "height": height,
            "tileset_id": tid, "events": len(events) if isinstance(events, dict) else 0,
            "direct_transfers": transfers, "ranking_scores": scores,
            "status": "CANDIDATE_REQUIRES_VISUAL_INSPECTION",
            "template_reviewed": False,
        })
    suggestions = {
        symbol: [
            {"native_map_id": row["native_map_id"], "name": row["name"],
             "sha256": row["native_map_sha256"], "score": row["ranking_scores"][symbol]}
            for row in sorted(rows,
                              key=lambda x: (-x["ranking_scores"][symbol],
                                             x["native_map_id"]))[:12]
        ]
        for symbol in KEYWORDS
    }
    return {
        "schema": 1, "region": "JOHTO", "status": "READ_ONLY_ROOM_CANDIDATES",
        "can_install": False, "native_game_modified": False,
        "room_reviewed": False, "count": len(rows), "skipped": skipped,
        "suggestions_not_approved": suggestions, "rooms": rows,
        "next_action": ("Revisar visualmente 3 templates distintos no game, "
                        "conferir grafia/tileset/colisões e preencher IDs, "
                        "hashes e destino em data/regions/johto-interior-templates.json"),
    }


def write_report(output: Path, contents: dict, *, root: Path = ROOT) -> None:
    allowed = (root.resolve() / ".blue-work").resolve()
    output = output.absolute()
    if (output.is_symlink() or output.resolve() == allowed or
            not output.resolve().is_relative_to(allowed) or output.exists()):
        raise ValueError("Relatório deve ser arquivo NOVO em .blue-work/")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".johto-room-audit-", dir=output.parent) as directory:
        staging = Path(directory) / "report.json"
        staging.write_text(
            json.dumps(contents, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if output.exists() or output.is_symlink():
            raise ValueError("Relatório existente; impedir overwrite")
        staging.rename(output)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, default=ROOT / "game")
    p.add_argument("--preview", type=Path, default=DEFAULT_PREVIEW)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = p.parse_args(argv)
    try:
        result = report(args.game, args.preview)
        write_report(args.output, result)
    except (ValueError, OSError, TypeError, KeyError) as error:
        print("[JOHTO][BLOQUEADO] " + str(error), file=sys.stderr)
        return 2
    print(f"[JOHTO] {result['count']} salas nativas candidatas; revisão visual PENDENTE.")
    print("[JOHTO] Relatório:", args.output)
    print("[JOHTO] Nenhum mapa real de Johto foi aprovado ou instalado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
