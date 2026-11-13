#!/usr/bin/env python3
"""Plan an explicit, collision-checked Sinnoh map remap without installing maps.

Requires inert RXDATA audit + real local game/Data snapshot. No automatic
allocation, no four-digit destination IDs, no overwrite, no event-script
execution, and NO serialized donor assets. A plan is NEVER install approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from audit_johto import ROOT, write_report

SHA = re.compile(r"[0-9a-f]{64}\Z")
ID = re.compile(r"[1-9][0-9]*\Z")
SYMBOL = re.compile(r"SINNOH_[A-Z0-9_]{3,80}\Z")
JOHTO_MIN, JOHTO_MAX = 600, 999
MAX_RMXP_MAPS = 5000


def fail(message: str):
    raise ValueError("[SINNOH REMAP] " + message)


def read_object(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        fail("Arquivo JSON precisa ser um objeto")
    return obj


def ids(values, label: str) -> set[int]:
    if not isinstance(values, list) or any(type(v) is not int or v <= 0 for v in values):
        fail(f"{label}: deve ser lista de IDs inteiros positivos")
    if len(values) != len(set(values)):
        fail(f"{label}: contém IDs duplicados")
    return set(values)


def valid_hash(raw, label: str) -> str:
    if not isinstance(raw, str) or not SHA.fullmatch(raw):
        fail(f"{label}: SHA-256 inválido/ausente")
    return raw


def keys_to_ids(obj, label: str) -> dict[int, object]:
    if not isinstance(obj, dict):
        fail(f"{label}: deve ser objeto")
    result = {}
    for key, value in obj.items():
        if not isinstance(key, str) or not ID.fullmatch(key):
            fail(f"{label}: ID de origem deve ser decimal positivo sem zero inicial")
        mid = int(key)
        if mid in result:
            fail(f"{label}: ID de origem repetido")
        result[mid] = value
    return result


def make_plan(audit: dict, request: dict, *, prior: dict | None = None,
              reserved: dict | None = None) -> dict:
    if (audit.get("schema"), audit.get("region"), audit.get("mode"),
            audit.get("import_allowed")) != (1, "SINNOH", "READ_ONLY_INERT_RMXP", False):
        fail("Auditoria RXDATA local real e não instalável é obrigatória")
    if (request.get("schema"), request.get("region")) != (1, "SINNOH"):
        fail("Requisição pertence a outra região ou tem schema incompatível")
    native = audit.get("native", {})
    if not isinstance(native, dict) or native.get("status") != "LOCAL_READ_ONLY":
        fail("É obrigatório auditar game/Data local e MapInfos antes do remapeamento")
    occupied = ids(native.get("occupied_ids"), "MapIDs ocupados no game/Data")
    existing_johto = set(range(JOHTO_MIN, JOHTO_MAX + 1))

    source = ids(audit.get("source_map_ids"), "MapIDs reais de origem")
    if not source or len(source) > MAX_RMXP_MAPS:
        fail("Origem vazia ou grande demais")
    rows = audit.get("maps")
    if not isinstance(rows, list) or len(rows) != len(source):
        fail("Inventário RXDATA incompleto")
    audited = {}
    for row in rows:
        if not isinstance(row, dict) or type(row.get("source_id")) is not int:
            fail("Linha RXDATA inválida")
        mid = row["source_id"]
        if mid in audited or mid not in source:
            fail("MapID duplicado ou ausente no inventário RXDATA")
        valid_hash(row.get("sha256"), f"Map{mid} doador")
        if not isinstance(row.get("name"), str):
            fail("Nome RMXP do mapa ausente")
        transfers = row.get("transfer_targets")
        if (not isinstance(transfers, list)
                or any(type(t) is not int or t <= 0 for t in transfers)):
            fail("Transferências inválidas; auditar antes de remapear")
        if len(set(transfers)) != len(transfers):
            fail("Transferências estáticas duplicadas no relatório")
        audited[mid] = row

    for field in ("missing_map_files", "orphan_map_files",
                  "unresolved_static_transfer_ids", "missing_graphics",
                  "invalid_graphic_names"):
        if audit.get(field) is None:
            fail(f"Auditoria incompleta: {field}")
        if audit[field]:
            fail(f"Fonte RXDATA apresenta problemas pendentes: {field}")

    original_infos = valid_hash(audit.get("mapinfos_sha256"), "MapInfos auditado")
    original_tiles = valid_hash(audit.get("tilesets_sha256"), "Tilesets auditado")
    if request.get("source_mapinfos_sha256") != original_infos:
        fail("MapInfos alterado ou sem hash fixo")
    if request.get("source_tilesets_sha256") != original_tiles:
        fail("Tilesets alterado ou sem hash fixo")
    donor_zip = audit.get("source_zip_sha256")
    if donor_zip is not None:
        valid_hash(donor_zip, "ZIP auditado")
        if request.get("source_zip_sha256") != donor_zip:
            fail("ZIP original não bate com hash do relatório")
    elif request.get("source_zip_sha256") not in (None, ""):
        fail("Requisição inclui ZIP inexistente na auditoria")
    requested_hashes = keys_to_ids(request.get("source_map_hashes"), "Hashes de mapas")
    mapping = keys_to_ids(request.get("mapping"), "Remapeamento")
    symbols = keys_to_ids(request.get("symbols"), "Símbolos")
    if set(mapping) != source or set(symbols) != source or set(requested_hashes) != source:
        fail("Todos os mapas reais devem ter IDs, símbolos e hashes; sem exclusão implícita")
    for mid in sorted(source):
        if requested_hashes[mid] != audited[mid]["sha256"]:
            fail(f"Map{mid}: hash diverge da fonte auditada")
    destinations = {}
    seen_symbols = set()
    for src in sorted(source):
        dst, symbol = mapping[src], symbols[src]
        if type(dst) is not int or not 1 <= dst < JOHTO_MIN:
            fail(f"Map{src}: destino fora do limite conservador 1..599; IDs >=1000 não testados")
        if dst in occupied:
            fail(f"Map{src}: destino {dst} já ocupado pelo jogo principal")
        if dst in existing_johto:
            fail(f"Map{src}: ID protegido de Johto")
        if dst in destinations:
            fail(f"Map{src}: destino {dst} duplicado")
        if not isinstance(symbol, str) or not SYMBOL.fullmatch(symbol) or symbol in seen_symbols:
            fail("Símbolo de mapa Sinnoh inválido/duplicado")
        destinations[dst] = src
        seen_symbols.add(symbol)

    # The supplied other-region reservation file is a REVIEW input, not proof
    # that every uninstalled Hoenn/Kanto/Johto reservation is known.
    protected = set()
    if reserved is not None:
        if (not isinstance(reserved, dict) or reserved.get("schema") != 1
                or reserved.get("region") != "SINNOH"):
            fail("Manifesto de reservas pertence a outra região")
        protected = ids(reserved.get("protected_ids"), "Reservas explícitas de outras regiões")
        if set(destinations) & protected:
            fail("Destino interfere em reserva declarada por outra região")
    else:
        # Never pretend that physical absence means no reserved ownership.
        pass

    # Existing plans are append-only. Freeze both numbers and symbols; never
    # repoint an existing source map even if the new donor release is reordered.
    if prior is not None:
        if (not isinstance(prior, dict) or prior.get("schema") != 1
                or prior.get("region") != "SINNOH"
                or prior.get("mode") != "REMAP_CANDIDATE_ONLY"):
            fail("Plano anterior inválido ou de outra região")
        old_map = keys_to_ids(prior.get("mapping"), "Remapeamento anterior")
        old_symbols = keys_to_ids(prior.get("symbols"), "Símbolos anteriores")
        old_hashes = keys_to_ids(prior.get("source_map_hashes"), "Hashes anteriores")
        if set(old_symbols) != set(old_map) or set(old_hashes) != set(old_map):
            fail("Plano anterior incompleto")
        for src, dst in old_map.items():
            if src not in mapping or dst != mapping[src]:
                fail("Remapeamento anterior deve ser preservado (saves)")
            if old_symbols[src] != symbols[src] or old_hashes[src] != requested_hashes[src]:
                fail("Símbolo/hash anterior modificado; auditar migração de saves")

    # Plans include a purely declarative rewrite list. No source .rxdata
    # bytes, shared MapInfos, event commands or PBS are ever rewritten.
    transfers = []
    for src in sorted(source):
        for target in sorted(audited[src]["transfer_targets"]):
            if target not in source:
                fail(f"Map{src}: transferência para Map{target} ainda não auditada")
            transfers.append({
                "from_source_id": src, "to_source_id": target,
                "from_candidate_id": mapping[src],
                "to_candidate_id": mapping[target],
                "mode": "STATIC_REFERENCE_PROPOSAL",
            })
    rows_out = [
        {"source_id": src, "source_name": audited[src]["name"],
         "symbol": symbols[src], "candidate_destination_id": mapping[src],
         "source_map_sha256": requested_hashes[src]}
        for src in sorted(source)
    ]
    result = {
        "schema": 1, "region": "SINNOH", "mode": "REMAP_CANDIDATE_ONLY",
        "status": "PENDING_NATIVE_AND_RIGHTS_REVIEW",
        "source_zip_sha256": donor_zip,
        "source_mapinfos_sha256": original_infos,
        "source_tilesets_sha256": original_tiles,
        "source_map_hashes": {str(src): requested_hashes[src] for src in sorted(source)},
        "symbols": {str(src): symbols[src] for src in sorted(source)},
        "mapping": {str(src): mapping[src] for src in sorted(source)},
        "maps": rows_out,
        "proposed_static_transfer_rewrites": transfers,
        "protected_johto_range": [JOHTO_MIN, JOHTO_MAX],
        "native_existing_map_ids": sorted(occupied),
        "other_region_reservations_listed": sorted(protected),
        "other_region_reservations_fully_verified": False,
        "dynamic_transfer_commands_for_manual_review":
            audit.get("dynamic_transfer_commands", 0),
        "untrusted_script_commands_not_executed":
            audit.get("untrusted_script_commands_not_executed", 0),
        "can_install": False,
        "may_stage_real_map_data": False,
        "four_digit_destination_ids_permitted": False,
        "game_or_saves_modified": False,
        "blocking_reasons": [
            "Não é conversor de mapas nem instalador: falta transformar/verificar RXDATA no piloto",
            "Reservas futuras de Hoenn/Johto/Kanto não comprovadas pelo game/Data",
            "Direitos por asset e dependências de áudio/PBS/eventos não aprovados",
            "Eventos dinâmicos/scripts de origem exigem auditoria sem execução",
            "MapIDs de 4 dígitos e integração Game.exe/JoiPlay ainda sem testes nativos",
        ],
    }
    payload = json.dumps(result, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":")).encode("ascii")
    result["plan_sha256"] = hashlib.sha256(payload).hexdigest()
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True, type=Path,
                        help="JSON do audit_sinnoh_rxdata.py com game/Data presente")
    parser.add_argument("--request", required=True, type=Path,
                        help="JSON preenchido APENAS com hashes/IDs REAIS auditados")
    parser.add_argument("--previous", type=Path,
                        help="Plano anterior: congela os IDs para compatibilidade de saves")
    parser.add_argument("--reserved", type=Path,
                        help="JSON com protected_ids de outras regiões")
    parser.add_argument("--output", type=Path,
                        default=ROOT / ".blue-work/sinnoh-remap-preview.json",
                        help="Apenas saída nova em .blue-work, sem sobrescrever backups")
    args = parser.parse_args(argv)
    try:
        report = read_object(args.audit)
        request = read_object(args.request)
        prior = read_object(args.previous) if args.previous else None
        reservations = read_object(args.reserved) if args.reserved else None
        result = make_plan(report, request, prior=prior, reserved=reservations)
        write_report(args.output, result)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print("SINNOH_REMAP_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({
        "mode": result["mode"], "map_count": len(result["maps"]),
        "static_rewrites": len(result["proposed_static_transfer_rewrites"]),
        "can_install": False, "plan_sha256": result["plan_sha256"],
        "report": str(args.output),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
