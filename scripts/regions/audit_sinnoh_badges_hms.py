#!/usr/bin/env python3
"""CH11: audit authored Sinnoh badges/HMs against the existing Blue registry.

Read-only. Does not create items, award badges, modify saves, or certify maps.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/regions/sinnoh-badges-hms-contract.json"
REGISTRY = ROOT / "site/public/data/regions.json"
REGIONS_RUNTIME = ROOT / "scripts/battle_polish/Regions.rb"
POLICY_RUNTIME = ROOT / "scripts/battle_polish/RegionalPolicy.rb"
EXPECTED = (
    ("COAL", "ROCK_SMASH", "HM06"),
    ("FOREST", "CUT", "HM01"),
    ("COBBLE", "FLY", "HM02"),
    ("RELIC", "DEFOG", "HM05"),
    ("FEN", "SURF", "HM03"),
    ("MINE", "STRENGTH", "HM04"),
    ("ICICLE", "ROCK_CLIMB", "HM08"),
    ("BEACON", "WATERFALL", "HM07"),
)


def fail(msg: str):
    raise ValueError("[SINNOH CH11] " + msg)


def read_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        fail("JSON ausente ou symlink: " + str(path))
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        fail("JSON deve ser objeto")
    return value


def read_runtime(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        fail("Runtime Ruby ausente ou symlink: " + str(path))
    return path.read_text(encoding="utf-8")


def audit(contract: dict, registry: dict, runtime: str, policy: str) -> dict:
    required = {
        "schema", "region", "status", "reference_game", "source_of_truth",
        "approved_for_install", "gameplay_verified", "native_gym_events_verified",
        "hm_pickup_events_installed", "requires_confirmed_local_pickup",
        "hm_item_is_not_equivalent_to_local_pickup",
        "no_cross_region_key_item_or_hm_transfer",
        "native_decades_badges_unchanged", "native_map_ids_assigned",
        "rules", "notes",
    }
    if set(contract) != required:
        fail("Campos do contrato ausentes ou desconhecidos")
    if (type(contract["schema"]) is not int or contract["schema"] != 1
            or contract["region"] != "SINNOH"
            or contract["status"] != "PLANNED_CONTRACT_NOT_INSTALLED"
            or contract["reference_game"] != "Pokémon Platinum"
            or contract["source_of_truth"] != "site/public/data/regions.json"):
        fail("Identidade, escopo ou status planejado do contrato alterado")
    false_flags = (
        "approved_for_install", "gameplay_verified", "native_gym_events_verified",
        "hm_pickup_events_installed", "native_map_ids_assigned",
    )
    true_flags = (
        "requires_confirmed_local_pickup",
        "hm_item_is_not_equivalent_to_local_pickup",
        "no_cross_region_key_item_or_hm_transfer",
        "native_decades_badges_unchanged",
    )
    if any(contract[k] is not False for k in false_flags) or any(
        contract[k] is not True for k in true_flags
    ):
        fail("Contrato falsamente jogável ou sem isolamento regional")
    if (not isinstance(contract["notes"], str) or
            len(contract["notes"]) < 40):
        fail("Aviso de limitações incompleto")
    entries = contract["rules"]
    if not isinstance(entries, list) or len(entries) != 8:
        fail("Contrato deve conter exatamente oito insígnias e oito HMs")
    pairs = []
    for row in entries:
        if (not isinstance(row, dict) or
                set(row) != {"badge", "field_move", "hm_item",
                             "verified_gym_event", "verified_hm_pickup_event"}):
            fail("Campos obrigatórios de badge/HM ausentes")
        if (row["verified_gym_event"] is not False or
                row["verified_hm_pickup_event"] is not False):
            fail("Eventos de ginásio ou item declarados jogáveis indevidamente")
        if any(not isinstance(row[k], str) for k in
               ("badge", "field_move", "hm_item")):
            fail("Badge, HM e item precisam ser nomes de texto")
        pairs.append((row["badge"], row["field_move"], row["hm_item"]))
    if tuple(pairs) != EXPECTED:
        fail("Insígnias, itens HM, permissões ou ordem Platinum incompatíveis")
    if (not isinstance(registry, dict) or
            not isinstance(registry.get("regions"), dict) or
            "SINNOH" not in registry["regions"]):
        fail("Catálogo de regiões ausente")
    region = registry["regions"]["SINNOH"]
    if (not isinstance(region, dict) or region.get("status") != "planned"
            or region.get("milestones") != [row[0] for row in EXPECTED]):
        fail("Oito insígnias Sinnoh divergentes do catálogo público")
    field = region.get("field")
    if not isinstance(field, dict) or set(field) != {
        row[1] for row in EXPECTED
    }:
        fail("Tabela de campo/HMs Sinnoh diverge do catálogo público")
    for badge, move, _item in EXPECTED:
        rule = field.get(move)
        if (not isinstance(rule, dict) or
                rule != {"badge": "SINNOH:" + badge, "tool": True}):
            fail("HM liberado por insígnia de outra região ou regra irregular")
    for other in ("KANTO", "JOHTO", "HOENN"):
        if other not in registry["regions"]:
            fail("Região existente ausente: " + other)
    start = runtime.find("SINNOH_HM_ITEMS = {")
    if start < 0:
        fail("Constante local de HMs não implementada em Regions.rb")
    stop = runtime.find("}.freeze", start)
    if stop < 0:
        fail("Constante HM sem fechamento")
    declarations = re.findall(
        r'"([A-Z_]+)"\s*=>\s*:(HM[0-9]{2})', runtime[start:stop]
    )
    if (len(declarations) != 8 or
            set(declarations) != {(m, i) for _, m, i in EXPECTED}):
        fail("Runtime Ruby de HM não coincide com oito contratos Platinum")
    for guard in (
        "def self.valid_sinnoh_badges?", "def self.sinnoh_local_hms",
        "def self.record_sinnoh_hm", 'state["current"] == "SINNOH"',
        "pickup_confirmed == true",
        'state["region_local_hms"]["SINNOH"] << action',
        "if region == \"SINNOH\"", "sinnoh_local_hms(state).include?(action)",
    ):
        if guard not in runtime:
            fail("Guarda Ruby de insígnias/HM local ausente: " + guard)
    for guard in ("local_proof = current[\"current\"] == \"SINNOH\"",
                  "BlueRegions.field_access(current, current[\"current\"], action, local_proof)"):
        if guard not in policy:
            fail("Política de campo Ruby não exige HM de Sinnoh local: " + guard)
    return {
        "schema": 1, "region": "SINNOH",
        "mode": "READ_ONLY_DECLARATIVE_CONTRACT",
        "badges": 8, "hm_moves": 8,
        "ruby_runtime_mapping_matches_registry": True,
        "cross_region_hm_ownership_allowed": False,
        "native_gym_events_verified": False,
        "hm_pickup_events_installed": False,
        "can_install": False, "gameplay_verified": False,
    }


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--contract", type=Path, default=CONTRACT)
    cli.add_argument("--registry", type=Path, default=REGISTRY)
    cli.add_argument("--regions-runtime", type=Path, default=REGIONS_RUNTIME)
    cli.add_argument("--policy-runtime", type=Path, default=POLICY_RUNTIME)
    args = cli.parse_args()
    try:
        result = audit(read_json(args.contract), read_json(args.registry),
                       read_runtime(args.regions_runtime),
                       read_runtime(args.policy_runtime))
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        print("SINNOH_CH11_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
