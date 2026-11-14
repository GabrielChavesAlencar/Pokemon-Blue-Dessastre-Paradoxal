#!/usr/bin/env python3
"""Read-only audit: legacy Sinnoh standalone pilot vs shared regional plan.

Do NOT build, install, remap, delete or migrate files. An isolated pilot
with a different save profile is NOT automatically safe to merge into Blue's
multi-region Game.exe. No physical Sinnoh map or native compatibility proven.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JOHTO_RANGE = (600, 999)
START_SYMBOL = "SINNOH_PLAYER_BEDROOM"
LEGACY_PY = "scripts/regions/pilot_sinnoh.py"
LEGACY_RB = "scripts/regions/SinnohPreview.rb"
NEW_RB = "scripts/regions/SinnohPilot.rb"
PLAN_JSON = "data/regions/sinnoh-twinleaf-events.json"


def reject(message: str):
    raise ValueError("[SINNOH LEGACY] " + message)


def source_assignments(source: str) -> dict[str, ast.AST]:
    tree = ast.parse(source)
    assignments = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id not in assignments:
                    assignments[target.id] = node.value
    return assignments


def literal_range(node: ast.AST) -> list[int]:
    if (not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name)
            or node.func.id != "range" or node.keywords or len(node.args) != 2):
        reject("MapIDs do piloto legado não usam range explícito")
    lo, hi = (ast.literal_eval(arg) for arg in node.args)
    if type(lo) is not int or type(hi) is not int or hi <= lo or hi - lo > 200:
        reject("Faixa de IDs do piloto legado inválida")
    return list(range(lo, hi))


def inspect_legacy_python(code: str) -> dict:
    assignments = source_assignments(code)
    try:
        names = ast.literal_eval(assignments["NAMES"])
        zipped = assignments["IDS"]
        if (not isinstance(names, dict) or not names or len(names) > 200
                or not isinstance(zipped, ast.Call)
                or not isinstance(zipped.func, ast.Name) or zipped.func.id != "dict"
                or len(zipped.args) != 1 or
                not isinstance(zipped.args[0], ast.Call)
                or not isinstance(zipped.args[0].func, ast.Name)
                or zipped.args[0].func.id != "zip"
                or len(zipped.args[0].args) != 2
                or not isinstance(zipped.args[0].args[0], ast.Name)
                or zipped.args[0].args[0].id != "NAMES"):
            reject("MapIDs legados não podem ser extraídos de forma segura")
        destinations = literal_range(zipped.args[0].args[1])
        if len(destinations) != len(names):
            reject("Contagem de mapas do piloto não corresponde a IDs")
        start = tuple(ast.literal_eval(assignments["START"]))
        if len(start) != 3 or start[0] not in names:
            reject("Start legado não corresponde ao mapa-fonte")
        source_sha = ast.literal_eval(assignments["SOURCE_SHA256"])
    except (KeyError, TypeError, ValueError, SyntaxError) as exc:
        reject("Não foi possível auditar configuração legada: " + str(exc))
    if (not isinstance(source_sha, str) or
            not re.fullmatch(r"[a-f0-9]{64}", source_sha)):
        reject("Hash fixo legado ausente")
    if not all(token in code for token in (
            "copy_game(", "install_copy(", "dataPathApp", "dataPathOrg",
            "build_overlay(", "SinnohPreview.rb")):
        reject("Isolamento de launcher legado não pode ser inferido")
    return {
        "source_map_ids": sorted(names),
        "legacy_map_ids": destinations,
        "source_to_destination": {
            str(source_id): destination
            for source_id, destination in zip(names, destinations)
        },
        "legacy_source_sha256": source_sha,
        "legacy_start_source_map_id": start[0],
        "legacy_start_candidate_map_id": destinations[list(names).index(start[0])],
        "legacy_start_xy": list(start[1:]),
        "standalone_code_path_present": True,
        "standalone_runtime_verified": False,
    }


def examine(legacy_code: str, legacy_ruby: str, new_ruby: str, spec: dict,
            *, reserved_from: int = 600, reserved_through: int = 999) -> dict:
    if (type(reserved_from) is not int or type(reserved_through) is not int
            or reserved_from > reserved_through):
        reject("Reserva Johto inválida")
    legacy = inspect_legacy_python(legacy_code)
    if not re.search(r'START\s*=\s*\[\s*\d+\s*,', legacy_ruby):
        reject("Plugin legado não tem spawn verificável")
    if "BlueSinnohPreview.rowan" not in legacy_code:
        reject("Piloto legado não invoca o Rowan por diálogo esperado")
    if not all(x in legacy_ruby for x in (
            "pbMessage(", "names + [", "pbAddPokemonSilent(", "module BlueSinnohPreview")):
        reject("Piloto Ruby legado não corresponde à escolha por diálogo")
    if not all(x in new_ruby for x in (
            "module BlueSinnohPilot", "choose_starter_from_ball", "RIVAL_READY",
            "def self.barry_rival", "def self.rowan_pokedex")):
        reject("Novo roteiro com três Poké Bolas não encontrado")
    if (not isinstance(spec, dict) or
            (spec.get("schema"), spec.get("region"),
             spec.get("approved_for_install"), spec.get("gameplay_verified")) !=
            (1, "SINNOH", False, False)):
        reject("Template do novo piloto indevidamente marcada como instalada")
    maps = spec.get("maps")
    if (not isinstance(maps, list) or len(maps) < 9
            or any(not isinstance(m, dict) or m.get("map_id") is not None
                   for m in maps)):
        reject("Template Sinnoh possui IDs supostamente reais não auditados")
    if (not isinstance(spec.get("start"), dict) or
            spec["start"].get("symbol") != START_SYMBOL or
            spec["start"].get("map_id") is not None):
        reject("Spawn inicial deve ficar simbólico até auditoria")
    reserved = sorted(set(legacy["legacy_map_ids"]) &
                      set(range(reserved_from, reserved_through + 1)))
    return {
        "schema": 1, "region": "SINNOH",
        "mode": "READ_ONLY_LEGACY_RECONCILIATION",
        "status": "LEGACY_STANDALONE_ONLY_MERGE_BLOCKED",
        "legacy": legacy,
        "johto_protected_range": [reserved_from, reserved_through],
        "legacy_ids_overlapping_johto": reserved,
        "legacy_starter_selection": "ROWAN_DIALOG",
        "new_story_starter_selection": "THREE_PHYSICAL_BALL_EVENTS",
        "new_story_planned_maps": len(maps),
        "new_map_ids_allocated": False,
        "legacy_source_rights_verified": False,
        "can_merge_into_shared_campaign": False,
        "safe_to_install": False,
        "runtime_qa_completed": False,
        "migration_completed": False,
        "next_actions": [
            "Conservar piloto legado somente como experimento independente, sem importar seus MapIDs",
            "Auditar fonte legítima dos nove mapas e todas as reservas de Johto/Hoenn/Decades",
            "Atribuir IDs reais fora de 600..999 somente com plano hash-pinned e baseline local",
            "Converter eventos para BlueSinnohPilot; remover escolha antiga por diálogo somente na cópia experimental",
            "Validar PBS Barry, spawn na casa e saves separados no Game.exe/JoiPlay",
        ],
    }


def audit_repo(root: Path = ROOT) -> dict:
    root = root.resolve()
    paths = [root / p for p in (LEGACY_PY, LEGACY_RB, NEW_RB, PLAN_JSON)]
    if any(path.is_symlink() or not path.is_file() for path in paths):
        reject("Arquivos-base ausentes ou symlink")
    a, b, c = (path.read_text("utf-8-sig") for path in paths[:3])
    spec = json.loads(paths[3].read_text("utf-8-sig"))
    result = examine(a, b, c, spec)
    result["input_sha256"] = {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in zip((LEGACY_PY, LEGACY_RB, NEW_RB, PLAN_JSON), paths)
    }
    return result


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--root", type=Path, default=ROOT)
    cli.add_argument("--output", type=Path,
                     help="Opcional: somente um novo JSON em .blue-work, sem overwrite")
    args = cli.parse_args()
    try:
        report = audit_repo(args.root)
        if args.output is not None:
            from audit_johto import write_report
            write_report(args.output, report)
    except (OSError, ValueError, KeyError, TypeError, SyntaxError) as exc:
        print("SINNOH_LEGACY_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
