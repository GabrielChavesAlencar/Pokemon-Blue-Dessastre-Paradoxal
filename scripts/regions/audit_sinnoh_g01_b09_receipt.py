#!/usr/bin/env python3
"""G01: validate sanitized B09 recovery metadata, NOT the physical game.

No binary execution, no saves, no source game scanning, and no native approval.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/regions/sinnoh-b09-native-qa.json"
STATUS = "PRIVATE_NATIVE_QA_CLONE_CREATED_NOT_RUNNABLE_YET"
STAGE_BASE = ".blue-work/sinnoh-b09-native-qa/native-"
STAGE_PATH = re.compile(r"\.blue-work/sinnoh-b09-native-qa/native-([0-9a-f]{16})\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
# The overlay replaces both original tables; these are not extra physical files.
OVERLAY_REPLACEMENTS = frozenset(("Data/MapInfos.rxdata", "Data/Tilesets.rxdata"))
RECEIPT_FIELDS = frozenset((
    "status", "relative_path", "files_reused", "files_copied",
    "files_repaired", "native_file_count", "sinnoh_overlay_files",
    "map_ids_clone_total", "saves_copied", "game_exe_executed",
    "safe_to_launch", "phase_b_approved", "r07_complete",
    "b08_maps_validated", "b08_pngs_validated",
    "b08_nonzero_terrain_cells", "future_reservations_verified",
    "native_game_tested", "joiplay_tested", "can_install_live_game",
))
DRY_RUN_FIELDS = frozenset((
    "status", "plan_sha256", "native_files_count", "overlay_files_count",
    "estimated_bytes", "expected_map_count", "excluded_private_files",
    "game_exe_will_be_copied_but_not_launched", "source_game_untouched",
    "phase_b_approved", "b08_maps_validated", "b08_pngs_validated",
    "b08_nonzero_terrain_cells", "future_reservations_verified",
    "native_game_tested", "joiplay_tested", "can_install_live_game",
    "r07_complete",
))
FALSE_RECEIPT = ("saves_copied", "game_exe_executed", "safe_to_launch",
                 "r07_complete", "future_reservations_verified",
                 "native_game_tested", "joiplay_tested", "can_install_live_game")
FALSE_DRY_RUN = ("future_reservations_verified", "native_game_tested",
                 "joiplay_tested", "can_install_live_game", "r07_complete")


def blocked(reason: str) -> None:
    raise ValueError("SINNOH_G01_BLOCKED: " + reason)


def require_int(value: object, label: str, *, positive: bool = False,
                maximum: int = 1_000_000) -> int:
    if type(value) is not int or value < (1 if positive else 0) or value > maximum:
        blocked("contador invalido: " + label)
    return value


def read_json(path: Path) -> dict:
    """Only tiny JSON objects; errors must not print paths or contents."""
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536:
            blocked("arquivo de entrada ausente, inseguro ou acima de 64 KiB")
        result = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        blocked("arquivo JSON de entrada ilegivel ou invalido")
    if type(result) is not dict:
        blocked("arquivo JSON nao e um objeto")
    return result


def check_contract(contract: dict) -> tuple[int, int, int, int]:
    if type(contract) is not dict or contract.get("region") != "SINNOH" or contract.get("stage") != "B09":
        blocked("contrato B09 invalido")
    original = require_int(contract.get("expected_installed_native_map_count"), "mapas originais", positive=True)
    maps = require_int(contract.get("expected_sinnoh_terrain_maps_in_clone"), "mapas Sinnoh", positive=True)
    total = require_int(contract.get("expected_qa_clone_map_count"), "mapas totais", positive=True)
    pngs = require_int(contract.get("expected_png_count"), "PNGs", positive=True)
    if (original, maps, total, pngs) != (648, 54, 702, 14) or total != original + maps:
        blocked("contagens contratuais nao correspondem ao projeto")
    if contract.get("can_install_live_game") is not False or contract.get("can_mark_native_playable") is not False:
        blocked("contrato permite instalacao ou jogo sem prova")
    if type(contract.get("phase_b_approved")) is not int or contract["phase_b_approved"] != 0:
        blocked("contrato contem aprovacao falsa")
    return maps, pngs, total, 484722


def audit_receipt(receipt: dict, contract: dict, dry_run: dict | None = None) -> dict:
    maps, pngs, total, terrain_cells = check_contract(contract)
    if type(receipt) is not dict or set(receipt) != RECEIPT_FIELDS:
        blocked("campos obrigatorios desconhecidos ou ausentes no recibo")
    if receipt["status"] != STATUS:
        blocked("status nao representa clone privado B09 criado")
    folder = receipt["relative_path"]
    if type(folder) is not str or not STAGE_PATH.fullmatch(folder):
        blocked("caminho do clone fora do workspace privado ou malformado")
    for field in FALSE_RECEIPT:
        if receipt[field] is not False:
            blocked("indicador indevido de seguranca ou teste: " + field)
    if type(receipt["phase_b_approved"]) is not int or receipt["phase_b_approved"] != 0:
        blocked("fase B aprovada sem teste nativo")
    for field, expected in (("map_ids_clone_total", total),
                            ("b08_maps_validated", maps),
                            ("b08_pngs_validated", pngs),
                            ("b08_nonzero_terrain_cells", terrain_cells)):
        if type(receipt[field]) is not int or receipt[field] != expected:
            blocked("contagem esperada divergiu: " + field)
    native = require_int(receipt["native_file_count"], "arquivos nativos", positive=True)
    overlay = require_int(receipt["sinnoh_overlay_files"], "arquivos overlay", positive=True)
    if native < 648 or overlay != maps + pngs + len(OVERLAY_REPLACEMENTS):
        blocked("numero de arquivos da origem/overlay incompativel")
    reused = require_int(receipt["files_reused"], "reaproveitados")
    copied = require_int(receipt["files_copied"], "copiados")
    repaired = require_int(receipt["files_repaired"], "reparados")
    logical = native + overlay
    processed = reused + copied + repaired
    if processed != logical - len(OVERLAY_REPLACEMENTS):
        blocked("diferenca entre contagens nao corresponde a substituicoes de tabelas")
    plan_bound = False
    if dry_run is not None:
        if type(dry_run) is not dict or set(dry_run) != DRY_RUN_FIELDS:
            blocked("dry-run faltando campos ou contendo campos inesperados")
        if dry_run["status"] != "B09_DRY_RUN_NO_FILES_WRITTEN":
            blocked("dry-run nao e uma simulacao B09")
        sha = dry_run["plan_sha256"]
        if type(sha) is not str or not SHA.fullmatch(sha) or not folder.endswith("native-" + sha[:16]):
            blocked("recibo B09 nao corresponde ao plano SHA-256")
        for field, expected in (
            ("native_files_count", native), ("overlay_files_count", overlay),
            ("expected_map_count", total), ("b08_maps_validated", maps),
            ("b08_pngs_validated", pngs), ("b08_nonzero_terrain_cells", terrain_cells),
        ):
            if type(dry_run[field]) is not int or dry_run[field] != expected:
                blocked("dry-run diverge do recibo: " + field)
        require_int(dry_run["estimated_bytes"], "estimated_bytes",
                    positive=True, maximum=12 * 1024 * 1024 * 1024)
        require_int(dry_run["excluded_private_files"], "excluded_private_files")
        for field in FALSE_DRY_RUN:
            if dry_run[field] is not False:
                blocked("dry-run contem indicador de aprovacao indevida: " + field)
        for field in ("game_exe_will_be_copied_but_not_launched", "source_game_untouched"):
            if dry_run[field] is not True:
                blocked("dry-run nao preserva politica B09: " + field)
        if type(dry_run["phase_b_approved"]) is not int or dry_run["phase_b_approved"] != 0:
            blocked("dry-run contem fase B indevidamente aprovada")
        plan_bound = True
    return {
        "schema": 1,
        "region": "SINNOH",
        "stage": "G01",
        "status": "B09_RECEIPT_METADATA_CONSISTENT_NOT_PLAYABLE",
        "receipt_fields_consistent": True,
        "linked_to_supplied_dry_run": plan_bound,
        "logical_plan_entries": logical,
        "accounted_unique_file_operations": processed,
        "expected_overlay_replacements": len(OVERLAY_REPLACEMENTS),
        "declared_clone_maps": total,
        "source_game_inspected": False,
        "private_clone_independently_audited": False,
        "receipt_authenticity_proven": False,
        "game_exe_tested": False,
        "joiplay_tested": False,
        "safe_to_launch": False,
        "can_install_live_game": False,
        "r07_complete": False,
        "phase_b_approved": 0,
        "phase_c_approved": 0,
        "phase_d_approved": 0,
        "limitations": [
            "Counts reconcile only against known overlay replacement policy; filenames not audited",
            "Receipt is not a digital signature or physical inspection of the clone",
            "B10 save isolation, B11 audit and native tests remain pending",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--dry-run", type=Path)
    args = parser.parse_args(argv)
    try:
        report = audit_receipt(read_json(args.receipt), read_json(CONTRACT),
                               read_json(args.dry_run) if args.dry_run else None)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError) as err:
        print(str(err) if str(err).startswith("SINNOH_G01_BLOCKED:")
              else "SINNOH_G01_BLOCKED: entrada invalida", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
