#!/usr/bin/env python3
"""CH20 — auditoria ESTATICA do pacote Android/JoiPlay e roteiro Sinnoh de 44 casos.

Por padrao nao escreve nada; com --output salva apenas em .blue-work.
Nao instala arquivos, extrai ZIP, executa Ruby/Game.exe/JoiPlay, toca em saves,
nem converte evidencias sintéticas em aprovacao de gameplay.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile

try:
    from scripts.regions.audit_sinnoh_twinleaf_events import audit as audit_event_schema
except ModuleNotFoundError:
    # Executar diretamente: python scripts/regions/audit_sinnoh_android_ch20.py
    from audit_sinnoh_twinleaf_events import audit as audit_event_schema

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = "data/regions/sinnoh-twinleaf-events.json"
SCHEMA = "data/regions/sinnoh-twinleaf-events.schema.json"
LEDGER = "data/regions/sinnoh-progress.json"
MAX_FILES = 60000
MAX_UNCOMPRESSED = 12 * 1024**3
MAX_FILE_SIZE = 1024**3
EXPECTED_COUNTS = {
    "starter": 3, "barry": 12, "save_reload": 3,
    "warp": 16, "npc": 5, "regression": 4, "android": 1,
}
STARTERS = ("TURTWIG", "CHIMCHAR", "PIPLUP")
RIVALS = ("CHIMCHAR", "PIPLUP", "TURTWIG")
REGIONS = ("DECADES", "KANTO", "JOHTO", "HOENN")
REQUIRED_FOR_STRUCTURAL_REVIEW = (
    "Data/MapInfos.rxdata", "Data/System.rxdata", "Data/Scripts.rxdata",
)
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def blocked(message: str):
    raise ValueError("[SINNOH CH20] " + message)


def safe_document(root: Path, name: str) -> dict:
    file = root / name
    if file.is_symlink() or not file.is_file():
        blocked("Fonte do checklist ausente ou symlink: " + name)
    obj = json.loads(file.read_text("utf-8"))
    if not isinstance(obj, dict) or obj.get("region") != "SINNOH":
        blocked("Documento Sinnoh invalido: " + name)
    return obj


def checklist(root: Path = ROOT) -> list[dict]:
    """IDs identicos aos produzidos pelo auditor nativo; sem MapIDs inventados."""
    doc = safe_document(root, TEMPLATE)
    ledger = safe_document(root, LEDGER)
    schema_file = root / SCHEMA
    if schema_file.is_symlink() or not schema_file.is_file():
        blocked("Schema de Twinleaf ausente ou symlink")
    # Reusar o auditor CH06 (24 eventos, topologia, sprites, flags e posicoes)
    # em vez de confiar apenas em contagens ou IDs de eventos.
    try:
        audit_event_schema(doc, json.loads(schema_file.read_text("utf-8")))
    except (ValueError, KeyError, TypeError) as error:
        blocked("Contrato Twinleaf CH06 invalido: " + str(error))
    work = ledger.get("native_playtest_workstream")
    if (not isinstance(work, dict) or work.get("android_joi_play_tested") is not False
            or work.get("native_qa_approved") is not False
            or work.get("manual_evidence_accepted") is not False):
        blocked("Ledger de QA nativo alterado; revisar antes de gerar roteiro")
    if (doc.get("gameplay_verified") is not False
            or doc.get("approved_for_install") is not False):
        blocked("Plano de eventos promove Sinnoh indevidamente a jogavel")
    maps = doc.get("maps")
    if not isinstance(maps, list) or len(maps) != 9:
        blocked("Contrato Twinleaf deve conter nove mapas simbolicos")
    cases = []
    for i, starter in enumerate(STARTERS):
        cases.append({"id": "ball-" + starter, "kind": "starter"})
        for mode in ("normal", "master"):
            for result in ("win", "loss"):
                cases.append({
                    "id": f"barry-{starter}-{mode}-{result}", "kind": "barry",
                    "expected_rival": RIVALS[i], "mode": mode, "outcome": result,
                    "expected_scaling_percent": 70 if mode == "normal" else 90,
                })
        cases.append({"id": "save-reload-" + starter, "kind": "save_reload"})
    symbols = {row.get("symbol") for row in maps if isinstance(row, dict)}
    if len(symbols) != 9 or None in symbols:
        blocked("Simbolos de mapa duplicados/invalidos")
    for row in maps:
        if (not isinstance(row, dict) or row.get("map_id") is not None
                or not isinstance(row.get("events"), list)):
            blocked("MapID concreto/informacao de eventos inesperada no template")
        for event in row["events"]:
            if not isinstance(event, dict):
                blocked("Evento nao e objeto")
            key, kind = event.get("key"), event.get("kind")
            if not isinstance(key, str) or not re.fullmatch(r"SN_[A-Z0-9_]+", key):
                blocked("Chave de evento invalida")
            if kind == "warp":
                if (event.get("destination") not in symbols or
                        any(event.get(k) is not None for k in ("x", "y", "arrival_x", "arrival_y"))):
                    blocked("Warp com destino invalido ou coordenadas ficticias")
                cases.append({
                    "id": "warp-" + key, "kind": "warp",
                    "from_symbol": row["symbol"], "to_symbol": event["destination"],
                })
            elif kind == "handler":
                if not isinstance(event.get("handler"), str) or not event["handler"]:
                    blocked("NPC sem handler")
                cases.append({"id": "npc-" + key, "kind": "npc",
                              "handler": event["handler"], "map_symbol": row["symbol"]})
            elif kind == "starter_ball":
                if event.get("species") not in STARTERS:
                    blocked("Pokebola de starter desconhecido")
            else:
                blocked("Tipo inesperado de evento no contrato: " + str(kind))
    for region in REGIONS:
        cases.append({"id": "regression-" + region, "kind": "regression", "region": region})
    cases.append({"id": "android-joi-play", "kind": "android",
                  "platform": "Android/JoiPlay", "independent_save_required": True})
    counts = Counter(item["kind"] for item in cases)
    if dict(counts) != EXPECTED_COUNTS or len({item["id"] for item in cases}) != 44:
        blocked("Inventario de 44 casos mudou ou tem duplicatas")
    return [{**row, "native_status": "pending", "evidence": None} for row in cases]


def zip_parts(name: str) -> tuple[str, ...]:
    if (not isinstance(name, str) or not name or "\x00" in name
            or "\\" in name or name.startswith("/")):
        blocked("Caminho ZIP inseguro")
    parts = name.rstrip("/").split("/")
    if any(not p or p in (".", "..") or ":" in p for p in parts):
        blocked("Caminho ZIP inseguro")
    return tuple(parts)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for piece in iter(lambda: file.read(1024 * 1024), b""):
            h.update(piece)
    return h.hexdigest()


def inspect_package(package: Path | None) -> dict:
    """Sem descompactar nem executar; metadados ZIP NAO comprovam runtime."""
    if package is None:
        return {"status": "NOT_PROVIDED", "sha256": None,
                "structural_checks": None, "blockers": ["Pacote Android/JoiPlay nao fornecido"]}
    if package.is_symlink() or not package.is_file() or package.suffix.lower() != ".zip":
        blocked("Pacote deve ser um ZIP local regular (sem symlink)")
    files: set[str] = set()
    prefixes: dict[str, set[str]] = {}
    total = 0
    with zipfile.ZipFile(package) as archive:
        members = archive.infolist()
        if len(members) > MAX_FILES:
            blocked("ZIP contem entradas demais")
        for member in members:
            parts = zip_parts(member.filename)
            if stat.S_IFMT(member.external_attr >> 16) == stat.S_IFLNK:
                blocked("ZIP contem symlink")
            if member.flag_bits & 1:
                blocked("ZIP criptografado nao auditavel")
            total += member.file_size
            if member.file_size > MAX_FILE_SIZE or total > MAX_UNCOMPRESSED:
                blocked("ZIP acima do limite de seguranca")
            if member.is_dir():
                continue
            normalized = "/".join(parts).casefold()
            if normalized in files:
                blocked("Entradas ZIP duplicadas (inclusive diferenca de caixa)")
            files.add(normalized)
            for i in range(len(parts)):
                relative = "/".join(parts[i:]).casefold()
                if relative in {x.casefold() for x in REQUIRED_FOR_STRUCTURAL_REVIEW}:
                    prefix = "/".join(parts[:i])
                    prefixes.setdefault(prefix, set()).add(relative)
    required = {x.casefold() for x in REQUIRED_FOR_STRUCTURAL_REVIEW}
    roots = [name for name, present in prefixes.items() if required.issubset(present)]
    if len(roots) != 1:
        return {"status": "BLOCKED", "sha256": sha256(package),
                "archive_members": len(files), "structural_checks": "INCOMPLETE",
                "blockers": ["ZIP precisa conter exatamente uma raiz Data/ com MapInfos, System e Scripts"]}
    prefix = roots[0]
    actual = ((prefix + "/") if prefix else "").casefold()
    conflicts = sorted(int(m.group(1)) for name in files
                       if (m := re.fullmatch(re.escape(actual) + r"data/map(800|80[1-5])\.rxdata", name)))
    return {
        "status": "STRUCTURE_PRESENT_UNVERIFIED",
        "sha256": sha256(package),
        "archive_members": len(files),
        "source_root": prefix or ".",
        "structural_checks": "METADATA_ONLY",
        "legacy_map_id_800_805_files": conflicts,
        "blockers": [
            "Nenhum script/plugin Ruby foi executado no JoiPlay",
            "Licenca, grafico, fontes, save e assets Android nao foram comprovados",
            "MapIDs 800-805 exigem identificacao de regiao antes de qualquer merge"
        ] if conflicts else [
            "Nenhum script/plugin Ruby foi executado no JoiPlay",
            "Licenca, grafico, fontes, save e assets Android nao foram comprovados",
        ],
    }


def audit(root: Path = ROOT, package: Path | None = None) -> dict:
    cases = checklist(root)
    pkg = inspect_package(package)
    # O hash canonico e independente da ordem de chaves e da plataforma.
    # Aponta para o plano, NAO para capturas nem gameplay executado.
    manifest = json.dumps(cases, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":")).encode("utf-8")
    source_sha = {
        "twinleaf_template": sha256(root / TEMPLATE),
        "twinleaf_schema": sha256(root / SCHEMA),
        "qa_ledger": sha256(root / LEDGER),
    }
    return {
        "schema": 1, "chapter": "CH20", "region": "SINNOH",
        "mode": "STATIC_JOIPLAY_PREFLIGHT_NOT_NATIVE_QA",
        "package": pkg,
        "checklist_total": 44,
        "by_kind": EXPECTED_COUNTS.copy(),
        "checklist_sha256": hashlib.sha256(manifest).hexdigest(),
        "input_sha256": source_sha,
        "completed_native_cases": 0,
        "cases": cases,
        "static_checklist_valid": True,
        "status": "PENDING_NATIVE_ANDROID_AND_WINDOWS_TESTS",
        "game_exe_tested": False, "joiplay_tested": False,
        "native_gameplay_verified": False, "manual_evidence_accepted": False,
        "ready_marker_created": False, "main_game_or_saves_modified": False,
        "notes": [
            "Casos vem do contrato de Twinleaf e das regras de audit_sinnoh_playtest.py",
            "IDs/simbolos nao sao mapas ou coordenadas fisicamente instalados",
            "Para evidencias nativas usar audit_sinnoh_playtest.py sobre copia QA compilada",
        ],
    }


def safe_output(root: Path, requested: Path) -> Path:
    root = root.absolute()
    work = root / ".blue-work"
    target = requested if requested.is_absolute() else root / requested
    target = target.absolute()
    if (target == work or not target.is_relative_to(work)
            or (work.is_symlink() or any(parent.is_symlink() for parent in
                                       (target, *target.parents) if parent.exists()))
            or (work.exists() and not target.resolve().is_relative_to(work.resolve()))):
        blocked("Relatorios somente dentro de .blue-work, sem symlinks")
    if target.exists() or target.is_symlink():
        blocked("Nao sobrescrever relatorio CH20 existente")
    return target


def write_report(root: Path, report: dict, output: Path) -> None:
    target = safe_output(root, output)
    target.parent.mkdir(parents=True, exist_ok=True)
    # x (exclusive) evita perder um relatorio anterior.
    with target.open("x", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--package", type=Path, help="ZIP da instalacao para inspecionar sem extrair")
    cli.add_argument("--output", type=Path, help="JSON novo somente em .blue-work")
    args = cli.parse_args(argv)
    try:
        result = audit(package=args.package)
        if args.output:
            write_report(ROOT, result, args.output)
        print(json.dumps({k: v for k, v in result.items() if k != "cases"},
                         ensure_ascii=False, indent=2))
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError,
            zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        print("SINNOH_CH20_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
