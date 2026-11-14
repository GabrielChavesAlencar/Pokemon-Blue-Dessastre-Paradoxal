#!/usr/bin/env python3
"""Read-only audit of the LEGACY Sinnoh pilot against the multi-region plan.

The old 800..805 IDs may be valid in a fully separate copy. They are NOT
approved for importing into the multi-region world, where 600..999 is the
provisional Johto reservation. Never remap saves automatically.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JOHTO_RANGE = range(600, 1000)
LEGACY_PLUGIN = "BlueSinnohPreview"
NEW_PLUGIN = "BlueSinnohPilot"
TITLE_OPTION = "Testar Sinnoh"


def fail(reason: str) -> None:
    raise ValueError("[SINNOH PILOT COMPAT] " + reason)


def _pilot_identifiers(source: str) -> tuple[list[int], list[int]]:
    tree = ast.parse(source)
    declared_names = None
    declared_ids = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        target = node.targets[0].id
        if target == "NAMES":
            if not isinstance(node.value, ast.Dict):
                fail("NAMES do piloto legado deixou de ser dicionário literal")
            keys = [ast.literal_eval(v) for v in node.value.keys]
            if not keys or any(type(x) is not int or x <= 0 for x in keys):
                fail("MapIDs da origem doadora inválidos")
            if len(keys) != len(set(keys)):
                fail("MapIDs da fonte duplicados")
            declared_names = keys
        elif target == "IDS":
            expr = node.value
            # Only the audited old form: dict(zip(NAMES, range(a, b)))
            if (not isinstance(expr, ast.Call) or not isinstance(expr.func, ast.Name)
                    or expr.func.id != "dict" or len(expr.args) != 1):
                fail("Forma do remapeamento legado mudou; revisão humana necessária")
            z = expr.args[0]
            if (not isinstance(z, ast.Call) or not isinstance(z.func, ast.Name)
                    or z.func.id != "zip" or len(z.args) != 2
                    or not isinstance(z.args[0], ast.Name) or z.args[0].id != "NAMES"):
                fail("MapIDs do piloto legado não podem ser inferidos seguramente")
            seq = z.args[1]
            if (not isinstance(seq, ast.Call) or not isinstance(seq.func, ast.Name)
                    or seq.func.id != "range"):
                fail("IDS não usa range literal verificável")
            args = [ast.literal_eval(a) for a in seq.args]
            if len(args) != 2 or any(type(n) is not int for n in args):
                fail("Intervalo de MapIDs ilegível")
            declared_ids = list(range(*args))
    if not declared_names or not declared_ids or len(declared_names) != len(declared_ids):
        fail("Remapeamento legado incompleto, não assumir MapIDs")
    return declared_names, declared_ids


def audit_compat(
    legacy_py: str, legacy_rb: str, title_rb: str, new_rb: str,
    *, installed_ids: list[int] | None = None
) -> dict:
    sources, ids = _pilot_identifiers(legacy_py)
    if (LEGACY_PLUGIN + ".rowan" not in legacy_py
            or "SinnohPreview.rb" not in legacy_py
            or "BlueSinnohPreview" not in legacy_rb
            or "pbMessage(" not in legacy_rb
            or "STARTERS" not in legacy_rb):
        fail("Piloto antigo perdeu sua forma de inicial por diálogo ou seu plugin")
    if (NEW_PLUGIN not in new_rb
            or "choose_starter_from_ball" not in new_rb
            or "RIVAL_READY" not in new_rb):
        fail("Novo piloto de três bolas/Barry está incompleto")
    if TITLE_OPTION not in title_rb:
        fail("Opção Testar Sinnoh ausente do menu principal")
    occupied = set()
    if installed_ids is not None:
        if (not isinstance(installed_ids, list)
                or any(type(x) is not int or x <= 0 for x in installed_ids)
                or len(installed_ids) != len(set(installed_ids))):
            fail("IDs instalados devem vir de auditoria real, sem duplicações")
        occupied = set(installed_ids)
    overlap = sorted(set(ids) & set(JOHTO_RANGE))
    live = sorted(set(ids) & occupied)
    return {
        "schema": 1, "region": "SINNOH",
        "mode": "STATIC_READ_ONLY_RECONCILIATION",
        "legacy_source_ids": sources,
        "legacy_destination_ids": ids,
        "johto_reserved_range": [600, 999],
        "overlap_johto_reserved": overlap,
        "overlap_physical_installed": live if installed_ids is not None else None,
        "legacy_story_module": LEGACY_PLUGIN,
        "new_story_module": NEW_PLUGIN,
        "legacy_start_choice": "ROWAN_DIALOG",
        "new_start_choice": "THREE_PHYSICAL_BALLS",
        "isolated_legacy_pilot_possible_in_principle": True,
        "isolated_legacy_pilot_tested": False,
        "multi_region_merge_safe": False,
        "no_map_ids_allocated": True,
        "no_saves_migrated": True,
        "no_files_written": True,
        "must_resolve": [
            "Não inserir mapas 800–805 do piloto antigo na instalação multi-regiões",
            "Manter perfis e saves do piloto legado separados dos novos",
            "Auditar origem, licença, coordenadas, links e IDs de todos os mapas reais",
            "Recriar os eventos da introdução com BlueSinnohPilot e três Poké Bolas, não ativar ambos os plugins",
            "Verificar primeiro o plano de MapIDs do game/Data e as reservas de Hoenn e Johto",
            "Testar a migração de saves apenas com plano dedicado e cópia, nunca sobrescrever",
        ],
    }


def scan_project(root: Path = ROOT, *, installed_ids: list[int] | None = None) -> dict:
    root = root.resolve()
    paths = [
        root / "scripts/regions/pilot_sinnoh.py",
        root / "scripts/regions/SinnohPreview.rb",
        root / "scripts/battle_polish/TitleKanto.rb",
        root / "scripts/regions/SinnohPilot.rb",
    ]
    if any(p.is_symlink() or not p.is_file() for p in paths):
        fail("Fonte legada e nova devem ser arquivos regulares presentes")
    return audit_compat(
        *(p.read_text(encoding="utf-8") for p in paths),
        installed_ids=installed_ids
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--installed-ids-report", type=Path,
                        help="JSON do auditor local RXDATA (nunca supor IDs sem dados)")
    args = parser.parse_args()
    try:
        physical = None
        if args.installed_ids_report:
            report = json.loads(args.installed_ids_report.read_text("utf-8"))
            if (not isinstance(report, dict) or report.get("region") != "SINNOH"
                    or report.get("mode") != "READ_ONLY_INERT_RMXP"
                    or report.get("native", {}).get("status") != "LOCAL_READ_ONLY"):
                fail("Relatório físico não é uma auditoria RXDATA nativa verificada")
            physical = report["native"]["occupied_ids"]
        result = scan_project(args.root, installed_ids=physical)
    except (OSError, ValueError, TypeError, SyntaxError, KeyError) as exc:
        print("SINNOH_COMPAT_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
