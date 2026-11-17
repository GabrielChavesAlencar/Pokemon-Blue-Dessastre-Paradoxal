#!/usr/bin/env python3
"""R07: read-only evidence preflight for future Kanto/Johto/Hoenn MapID reservations.

This DOES NOT complete S07/R07. It cannot infer future allocations from
game/Data or grant ownership/asset licences. No maps, saves, scripts or
RPG Maker data are written. Optional report stays in .blue-work only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from audit_sinnoh_source import inspect_native

ROOT = Path(__file__).resolve().parents[2]
REGIONS = ("KANTO", "JOHTO", "HOENN")
HEX = re.compile(r"[a-f0-9]{64}\Z")
DECIMAL = re.compile(r"[1-9][0-9]*\Z")


def blocked(message: str) -> None:
    raise ValueError("SINNOH_R07_BLOQUEADO: " + message)


def root_paths(project: Path) -> tuple[Path, Path, Path]:
    project = Path(project).absolute()
    work = project / ".blue-work"
    game_data = project / "game" / "Data"
    if (not project.is_dir() or project.is_symlink()
            or work.is_symlink() or (project / "game").is_symlink()
            or game_data.is_symlink()):
        blocked("projeto ou caminho de jogo invalido/symlink")
    if (work.exists() and not work.is_dir()) or (
            game_data.exists() and not game_data.is_dir()):
        blocked("workspace ou game/Data nao sao diretorios validos")
    return project, work, game_data


def read_reservation(file: Path, region: str, baseline_sha: str) -> dict:
    if file.is_symlink() or not file.is_file():
        blocked("manifesto de reservas ausente: " + region)
    if file.stat().st_size > 250_000:
        blocked("manifesto de reservas grande demais: " + region)
    data = json.loads(file.read_text("utf-8-sig"))
    keys = {
        "schema", "region", "kind", "baseline_mapinfos_sha256",
        "future_reserved_map_ids", "ownership_evidence",
        "reviewed_locally", "read_only",
    }
    if (type(data) is not dict or set(data) != keys
            or data.get("schema") != 1 or data.get("region") != region
            or data.get("kind") != "LOCAL_FUTURE_MAP_ID_RESERVATIONS"
            or data.get("baseline_mapinfos_sha256") != baseline_sha
            or data.get("read_only") is not True):
        blocked("manifesto de reservas incompativel com baseline: " + region)
    raw = data["future_reserved_map_ids"]
    if (type(raw) is not list or len(raw) > 5000
            or any(type(i) is not int or not 1 <= i <= 999
                   for i in raw) or len(raw) != len(set(raw))):
        blocked("MapIDs futuros invalidos/duplicados: " + region)
    if data["reviewed_locally"] is not True:
        blocked("reservas futuras sem revisao local: " + region)
    evidence = data["ownership_evidence"]
    if (not isinstance(evidence, str) or not evidence.strip()
            or len(evidence) > 320 or any(x in evidence for x in ("..", "\\", "<", ">"))):
        blocked("evidencia humana de reserva ausente/insegura: " + region)
    return {"region": region, "count": len(raw), "ids": sorted(raw),
            "evidence_recorded": True, "local_review_asserted": True,
            "native_acceptance_confirmed": False}


def read_candidate_plan(plan: dict | None) -> list[int] | None:
    if plan is None:
        return None
    if (type(plan) is not dict or plan.get("schema") != 1
            or plan.get("region") != "SINNOH"
            or plan.get("mode") != "REMAP_CANDIDATE_ONLY"
            or plan.get("can_install") is not False
            or plan.get("may_stage_real_map_data") is not False):
        blocked("plano precisa ser candidato inerte de Sinnoh")
    mapping = plan.get("mapping")
    if (not isinstance(mapping, dict) or not mapping
            or len(mapping) > 5000):
        blocked("candidato sem remapeamento auditavel")
    values = []
    for source, destination in mapping.items():
        if (not isinstance(source, str) or not DECIMAL.fullmatch(source)
                or type(destination) is not int
                or not 1 <= destination <= 599):
            blocked("MapID proposto fora de 1..599 ou origem insegura")
        values.append(destination)
    if len(set(values)) != len(values):
        blocked("destinos Sinnoh duplicados")
    return sorted(values)


def audit(project: Path = ROOT, *, plan: dict | None = None) -> dict:
    project, work, game_data = root_paths(project)
    reasons: list[str] = []
    native = inspect_native(game_data)
    occupied = native.get("occupied_ids")
    if native.get("status") != "LOCAL_READ_ONLY" or occupied is None:
        reasons.append("game/Data local nao fornecido: MapIDs nativos desconhecidos")
    info_file = game_data / "MapInfos.rxdata"
    info_sha = None
    if info_file.is_symlink():
        blocked("MapInfos.rxdata nao pode ser symlink")
    if info_file.is_file():
        if info_file.stat().st_size > 32_000_000:
            blocked("MapInfos.rxdata acima do limite")
        info_sha = hashlib.sha256(info_file.read_bytes()).hexdigest()
    else:
        reasons.append("MapInfos.rxdata real ausente para vincular as reservas")
    future: dict[str, dict] = {}
    reserved_all: dict[int, str] = {}
    for region in REGIONS:
        file = work / "sinnoh-reservations" / (region.lower() + ".json")
        if file.parent.is_symlink() or file.is_symlink():
            blocked("link simbolico em reservas regionais: " + region)
        if info_sha is None or not file.is_file():
            reasons.append("reserva futura de " + region + " nao comprovada")
            continue
        record = read_reservation(file, region, info_sha)
        future[region] = record
        for mid in record["ids"]:
            if mid in reserved_all and reserved_all[mid] != region:
                reasons.append("reserva compartilhada em conflito: " + str(mid))
            reserved_all[mid] = region
    candidates = read_candidate_plan(plan)
    collisions = []
    if candidates is None:
        reasons.append("plano Sinnoh com MapIDs reais e hashes ainda ausente")
    else:
        existing = set(occupied or [])
        for mid in candidates:
            if mid in existing:
                collisions.append({"id": mid, "reason": "OCCUPIED_IN_NATIVE_BASE"})
            if mid in reserved_all:
                collisions.append({"id": mid, "reason": "FUTURE_RESERVED_" + reserved_all[mid]})
        if collisions:
            reasons.append("candidato Sinnoh colide com IDs instalados ou reservados")
    if len(future) != len(REGIONS):
        reasons.append("R07 exige cadastro futuro de TODAS as tres regioes")
    ready = not reasons
    return {
        "schema": 1, "region": "SINNOH", "task": "S07",
        "substep": "R07", "mode": "LOCAL_RESERVATIONS_DIAGNOSTIC_ONLY",
        "status": ("CANDIDATE_READY_FOR_MANUAL_REVIEW_NOT_APPROVED"
                   if ready else "BLOCKED_MISSING_NATIVE_RESERVATION_EVIDENCE"),
        "native_snapshot_present": native.get("status") == "LOCAL_READ_ONLY",
        "native_occupied_count": len(occupied) if occupied is not None else None,
        "native_mapinfos_sha256": info_sha,
        "future_regional_reservations": future,
        "future_regions_with_evidence": len(future),
        "future_regions_required": list(REGIONS),
        "sinnoh_candidate_destination_ids": candidates,
        "collisions": collisions,
        "blockers": reasons,
        "candidate_safety_reviewable": ready,
        "r07_complete": False,
        "r08_real_maps_imported": False,
        "r09_game_exe_joiplay_tested": False,
        "rights_verified": False,
        "may_apply_to_main_game": False,
        "game_or_saves_modified": False,
        "native_gameplay_verified": False,
        "note": "Snapshot e declaracoes nao provam direitos, reservas futuras exaustivas ou QA nativo. R07 fica parcial ate aceite real."
    }


def write_report(project: Path, report: dict) -> Path:
    project, work, _ = root_paths(project)
    if report.get("region") != "SINNOH" or report.get("r07_complete") is not False:
        blocked("relatorio adulterado ou falsamente aprovado")
    diagnostics = work / "sinnoh-diagnostics"
    if diagnostics.is_symlink():
        blocked("destino de diagnostico por symlink")
    diagnostics.mkdir(parents=True, exist_ok=True)
    output = diagnostics / "r07-reservations.json"
    if output.is_symlink():
        blocked("arquivo de diagnostico por symlink")
    raw = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=diagnostics,
                                         prefix=".r07-", suffix=".json",
                                         delete=False) as handle:
            tmp = Path(handle.name)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        tmp.replace(output)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    return output


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--project", type=Path, default=ROOT)
    cli.add_argument("--plan", type=Path,
                     help="JSON do plano Sinnoh candidato, nao da autorizacao de instalar")
    cli.add_argument("--write", action="store_true",
                     help="salva apenas .blue-work/sinnoh-diagnostics/r07-reservations.json")
    args = cli.parse_args(argv)
    try:
        plan = None
        if args.plan:
            plan_file = args.plan.absolute()
            root = args.project.absolute()
            if (plan_file.is_symlink() or not plan_file.is_file()
                    or (root / ".blue-work").is_symlink()
                    or not plan_file.is_relative_to(root / ".blue-work")
                    or not plan_file.resolve().is_relative_to((root / ".blue-work").resolve())
                    or plan_file.stat().st_size > 1_000_000):
                blocked("plano deve estar dentro de .blue-work, sem symlink")
            plan = json.loads(plan_file.read_text("utf-8"))
        result = audit(args.project, plan=plan)
        if args.write:
            output = write_report(args.project, result)
            result["report_path"] = str(output)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["candidate_safety_reviewable"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
