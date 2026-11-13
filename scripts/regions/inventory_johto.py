"""Inventário estrutural de eventos RMXP de Johto: APENAS LEITURA.

Nunca executa scripts de eventos do pacote externo, não extrai diálogos,
não escreve em game/, não inventa MapIDs nem certifica jogabilidade.
Usar depois de audit_johto.py com o mesmo pacote de origem.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

from audit_johto import (
    ROOT, DEFAULT_SOURCE, DEFAULT_REPORT, attributes, checksum,
    map_files, project_data, read_map_data, write_report,
)
from server.ruby_marshal import RubyObject, text

DEFAULT_AREAS = ROOT / "data/regions/johto-area-scope.json"
DEFAULT_OUTPUT = ROOT / ".blue-work/johto-content-inventory.json"

# Somente códigos RMXP, nunca texto dos comandos ou script de terceiros.
CODES = {
    101: "message", 401: "message",
    102: "choice", 103: "number_input",
    111: "conditional", 121: "switch", 122: "variable",
    123: "self_switch", 125: "gold", 126: "item_change",
    127: "weapon_change", 128: "armor_change",
    201: "transfer", 202: "vehicle", 203: "location",
    205: "move_route", 301: "native_battle",
    302: "shop", 303: "name_entry",
    355: "untrusted_script", 655: "untrusted_script",
}
TRIGGERS = {0: "action", 1: "player_touch", 2: "event_touch",
            3: "autorun", 4: "parallel"}


def normalize(value: str) -> str:
    raw = unicodedata.normalize("NFKD", value.casefold())
    return re.sub(r"[^a-z0-9]+", " ", "".join(
        c for c in raw if not unicodedata.combining(c))).strip()


def area_scope(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if data.get("schema") != 1 or data.get("region") != "JOHTO":
        raise ValueError("Escopo geográfico de Johto inválido")
    rows = data.get("areas")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Escopo de áreas vazio ou inválido")
    keys = set()
    for row in rows:
        key = row.get("key")
        aliases = row.get("aliases")
        if (not isinstance(key, str) or not re.fullmatch(r"JOHTO_[A-Z0-9_]+", key)
                or key in keys or not isinstance(aliases, list) or not aliases
                or not all(isinstance(a, str) and normalize(a) for a in aliases)
                or type(row.get("required")) is not bool):
            raise ValueError("Área duplicada ou inválida: " + str(key))
        keys.add(key)
    return rows


def static_warp(parameters) -> dict | None:
    """Apenas transferências com mapa/XY constantes; variável é dinâmica."""
    if not isinstance(parameters, list) or not parameters:
        return None
    if parameters[0] != 0:
        return {"mode": "dynamic"}
    if (len(parameters) < 4 or
            any(type(v) is not int for v in parameters[1:4])):
        return {"mode": "invalid"}
    return {"mode": "static", "map_id": parameters[1],
            "x": parameters[2], "y": parameters[3]}


def event_summary(event_id: int, event: RubyObject, width: int,
                  height: int, known_maps: dict[int, dict]) -> tuple[dict, list[str]]:
    if not isinstance(event, RubyObject) or event.name != "RPG::Event":
        raise ValueError("Evento de origem não é RPG::Event")
    f = attributes(event)
    x, y = f.get("@x"), f.get("@y")
    warnings = []
    if (type(x) is not int or type(y) is not int or
            not 0 <= x < width or not 0 <= y < height):
        warnings.append("EVENT_POSITION_INVALID")
    pages = f.get("@pages", [])
    if not isinstance(pages, list):
        raise ValueError("Páginas de evento inválidas")
    result_pages = []
    for index, page in enumerate(pages, start=1):
        if not isinstance(page, RubyObject) or page.name != "RPG::Event::Page":
            raise ValueError("Página de evento RMXP inválida")
        p = attributes(page)
        commands = p.get("@list", [])
        if not isinstance(commands, list):
            raise ValueError("Lista de comandos de evento inválida")
        counts = {}
        warps = []
        for cmd in commands:
            if not isinstance(cmd, RubyObject) or cmd.name != "RPG::EventCommand":
                raise ValueError("Comando RMXP inválido")
            c = attributes(cmd)
            code = c.get("@code")
            if type(code) is not int:
                raise ValueError("Código RMXP inválido")
            kind = CODES.get(code, "other")
            counts[kind] = counts.get(kind, 0) + 1
            if code == 201:
                target = static_warp(c.get("@parameters"))
                if target is None:
                    warnings.append("TRANSFER_MISSING_PARAMETERS")
                    continue
                warps.append(target)
                if target["mode"] == "invalid":
                    warnings.append("TRANSFER_INVALID")
                elif target["mode"] == "static":
                    dest = known_maps.get(target["map_id"])
                    if dest is None:
                        warnings.append("TRANSFER_TARGET_MISSING")
                    elif not (0 <= target["x"] < dest["width"]
                              and 0 <= target["y"] < dest["height"]):
                        warnings.append("TRANSFER_TARGET_OUT_OF_BOUNDS")
        trigger = p.get("@trigger")
        if trigger not in TRIGGERS:
            warnings.append("UNKNOWN_EVENT_TRIGGER")
        result_pages.append({
            "page": index, "trigger": TRIGGERS.get(trigger, "unknown"),
            "command_counts": dict(sorted(counts.items())),
            "static_or_dynamic_warps": warps,
            "requires_manual_reconstruction": bool(
                counts.get("untrusted_script")
                or counts.get("native_battle")
                or counts.get("item_change")
                or counts.get("shop")),
        })
    return ({
        "source_event_id": event_id,
        "name": text(f.get("@name", b"")).strip()[:180],
        "x": x, "y": y, "pages": result_pages,
        "status": "SOURCE_STRUCTURE_ONLY_NOT_INSTALLED",
    }, sorted(set(warnings)))


def create_inventory(source: Path, audit: dict, areas: list[dict]) -> dict:
    """Compara hashes reais antes de ler eventos, sem escrever no jogo."""
    if (audit.get("schema"), audit.get("region"), audit.get("mode"),
            audit.get("can_install")) != (1, "JOHTO", "READ_ONLY_NO_INSTALL", False):
        raise ValueError("Exige auditoria anterior read-only de Johto")
    if source.is_symlink():
        raise ValueError("Fonte ligada por symlink")
    data = project_data(source)
    if (checksum(data / "MapInfos.rxdata") != audit.get("mapinfos_sha256")
            or checksum(data / "Tilesets.rxdata") != audit.get("tilesets_sha256")):
        raise ValueError("MapInfos/Tilesets alterados após auditoria")
    entries = audit.get("maps")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Auditoria sem mapas")
    known = {}
    for row in entries:
        idx = row.get("source_id")
        if type(idx) is not int or idx in known:
            raise ValueError("IDs de origem inconsistentes")
        known[idx] = row
    actual = map_files(data)
    if set(actual) != set(known):
        raise ValueError("Lista de mapas diferente da auditoria")
    maps = []
    totals = {key: 0 for key in (
        "maps", "events", "event_pages", "messages", "choices",
        "native_battle_commands", "item_change_commands",
        "untrusted_script_commands", "transfer_commands")}
    for source_id, file in sorted(actual.items()):
        row = known[source_id]
        if checksum(file) != row.get("sha256"):
            raise ValueError("Mapa alterado após auditoria: " + file.name)
        original = read_map_data(file)
        if not isinstance(original, RubyObject) or original.name != "RPG::Map":
            raise ValueError("Objeto de mapa RMXP inválido")
        fields = attributes(original)
        if (fields.get("@width"), fields.get("@height"), fields.get("@tileset_id")) != (
                row.get("width"), row.get("height"), row.get("tileset_id")):
            raise ValueError("Geometria/tileset divergente da auditoria")
        raw_events = fields.get("@events", {})
        if not isinstance(raw_events, dict):
            raise ValueError("Eventos RMXP inválidos")
        listed, warnings = [], []
        for event_id, event in sorted(raw_events.items()):
            if type(event_id) is not int or event_id < 1:
                raise ValueError("ID de evento de origem inválido")
            summary, notes = event_summary(
                event_id, event, row["width"], row["height"], known)
            listed.append(summary)
            warnings.extend(notes)
            for page in summary["pages"]:
                totals["event_pages"] += 1
                counts = page["command_counts"]
                totals["messages"] += counts.get("message", 0)
                totals["choices"] += counts.get("choice", 0)
                totals["native_battle_commands"] += counts.get("native_battle", 0)
                totals["item_change_commands"] += counts.get("item_change", 0)
                totals["untrusted_script_commands"] += counts.get("untrusted_script", 0)
                totals["transfer_commands"] += counts.get("transfer", 0)
        totals["maps"] += 1
        totals["events"] += len(listed)
        maps.append({
            "source_id": source_id, "name": row["name"],
            "sha256": row["sha256"], "width": row["width"],
            "height": row["height"], "tileset_id": row["tileset_id"],
            "source_events": listed,
            "warnings": sorted(set(warnings)),
            "status": "SOURCE_GEOMETRY_AND_EVENT_INDEX_ONLY",
        })
    # Integridade cruzada com auditor anterior: sem reescrever os dados.
    if (totals["untrusted_script_commands"] !=
            audit.get("untrusted_script_commands")
            or totals["maps"] != audit.get("map_count")):
        raise ValueError("Inventário não coincide com auditoria de origem")
    scope = []
    for area in areas:
        aliases = [normalize(alias) for alias in area["aliases"]]
        matches = [m["source_id"] for m in maps
                   if any(alias in normalize(m["name"]) for alias in aliases)]
        scope.append({
            "key": area["key"], "required": area["required"],
            "candidate_source_ids": matches,
            "inventory_verified": False,
            "npcs_verified": False, "items_verified": False,
            "events_verified": False, "warps_verified": False,
            "audio_verified": False, "gameplay_verified": False,
            "status": "NEEDS_MANUAL_HGSS_RECONSTRUCTION",
        })
    return {
        "schema": 1, "region": "JOHTO",
        "mode": "READ_ONLY_NO_INSTALL", "can_install": False,
        "status": "SOURCE_INVENTORY_NOT_PLAYABLE",
        "source_hash_verified": audit.get("archive_hash_pinned_and_verified") is True,
        "source_archive_sha256": audit.get("source_archive_sha256"),
        "totals": totals, "areas": scope, "maps": maps,
        "notes": [
            "Map Pack structure is not the complete HGSS event/item/NPC inventory.",
            "Event command parameters and untrusted scripts were never executed.",
            "No NPC, item, battle, map or soundtrack has been installed in game/.",
            "Matches by map name are only candidates; manual mapping required.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    cli.add_argument("--audit", type=Path, default=DEFAULT_REPORT)
    cli.add_argument("--areas", type=Path, default=DEFAULT_AREAS)
    cli.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = cli.parse_args(argv)
    try:
        audit = json.loads(args.audit.read_text(encoding="utf-8-sig"))
        inventory = create_inventory(args.source, audit, area_scope(args.areas))
        write_report(args.output, inventory)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print("[JOHTO][BLOQUEADO] " + str(exc), file=sys.stderr)
        return 2
    totals = inventory["totals"]
    print("[JOHTO] Inventário inert: %s mapas, %s eventos, %s páginas." %
          (totals["maps"], totals["events"], totals["event_pages"]))
    print("[JOHTO] Nenhum NPC/item foi implantado; gameplay BLOQUEADO.")
    print("[JOHTO] Relatório:", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
