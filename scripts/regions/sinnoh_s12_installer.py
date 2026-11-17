#!/usr/bin/env python3
"""S12: safe one-step installer for a PRIVATE Sinnoh Windows QA copy.

No ROM/maps/assets download. The caller MUST supply a previously audited,
hash-pinned private overlay and the matching local event specification.
Default is dry-run; --install is explicit. Never modifies game/, shared saves,
GitHub, other regions, or user AppData. It does NOT approve native gameplay.
"""
from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path

from install_sinnoh_qa_copy import ROOT, prepare, install, verify
from prepare_sinnoh_pilot_bundle import _safe_under
from audit_sinnoh_s08_resources import private_overlay_audit

PRIVATE_SPEC = "sinnoh-qa-spec.json"
OVERLAY_REPORT = "sinnoh-qa-overlay-report.json"
QA_PREFIX = "game-sinnoh-qa-"


def blocked(message: str) -> None:
    raise ValueError("SINNOH_S12_BLOQUEADO: " + message)


def private_project(project: Path) -> tuple[Path, Path]:
    root = Path(project).absolute()
    work = root / ".blue-work"
    if root.is_symlink() or not root.is_dir() or work.is_symlink():
        blocked("projeto nao existe ou contem link simbolico")
    if not work.is_dir():
        blocked("pasta .blue-work ausente; obtenha fonte de mapas autorizada antes")
    return root, work


def select_auto(project: Path = ROOT) -> tuple[Path, Path]:
    """Select a single audited overlay + spec, never guess donor maps."""
    root, work = private_project(project)
    spec = work / PRIVATE_SPEC
    if spec.is_symlink() or not spec.is_file():
        blocked("especificacao privada .blue-work/" + PRIVATE_SPEC + " ausente")
    found = []
    for item in work.iterdir():
        report = item / OVERLAY_REPORT
        if report.exists() or report.is_symlink():
            if item.is_symlink() or not item.is_dir() or report.is_symlink():
                blocked("overlay privado com link simbolico ou formato invalido")
            found.append(item)
    if len(found) != 1:
        blocked("exige exatamente um overlay previamente auditado; encontrados " +
                str(len(found)))
    return found[0], spec


def existing_qa(project: Path) -> list[Path]:
    _, work = private_project(project)
    found = []
    for item in work.iterdir():
        if not item.name.startswith(QA_PREFIX):
            continue
        if item.is_symlink() or not item.is_dir():
            blocked("copia QA existente insegura; nenhuma substituicao permitida")
        found.append(item)
    return sorted(found)


def execute(project: Path = ROOT, *, overlay: Path, spec: Path,
            do_install: bool = False, token: str | None = None) -> dict:
    """Atomic installation via the existing QA installer; no fallback to game/."""
    root, work = private_project(project)
    overlay = _safe_under(overlay, work, "Overlay privado")
    spec = _safe_under(spec, work, "Especificacao privada")
    if spec.is_symlink() or not spec.is_file() or spec.suffix.lower() != ".json":
        blocked("especificacao JSON local ausente ou insegura")
    if overlay.is_symlink() or not overlay.is_dir():
        blocked("overlay privado ausente ou inseguro")
    if (overlay == spec.parent or spec.is_relative_to(overlay)):
        blocked("especificacao deve ser externa ao overlay imutavel")
    if do_install and existing_qa(root):
        blocked("ja existe copia Sinnoh QA; nao sobrescrever saves nem criar outra que S10 nao identifica")
    source = json.loads(spec.read_text(encoding="utf-8"))
    if not isinstance(source, dict) or source.get("region") != "SINNOH":
        blocked("especificacao nao pertence a Sinnoh")
    profile = secrets.token_hex(6) if token is None else token
    report, blobs, native = prepare(root / "game", overlay, source,
                                    token=profile, project=root)
    integrity = private_overlay_audit(root, overlay, spec, token=profile)
    if (integrity["status"] != "STATIC_INTEGRITY_VERIFIED_NOT_NATIVE_GAMEPLAY"
            or integrity["missing_graphics"] or
            not integrity["plugin_dependencies_verified"] or
            integrity["native_qa_approved"] or integrity["native_gameplay_verified"]):
        blocked("S08: integridade dos recursos de Sinnoh nao comprovada")
    if (report.get("mode") != "ISOLATED_QA_INSTALL_PLAN"
            or report.get("runtime_playable") is not False
            or report.get("current_main_game_or_saves_modified") is not False
            or report.get("save_migration") is not False
            or report.get("ready_marker_created") is not False):
        blocked("plano de instalacao afirma estado jogavel ou altera saves")
    result = {
        "region": "SINNOH",
        "status": "DRY_RUN_VALIDATED_NOT_INSTALLED",
        "scope": "PRIVATE_QA_ONLY",
        "created": False,
        "qa_directory": None,
        "game_exe_executed": False,
        "joiplay_executed": False,
        "save_migration": False,
        "main_game_or_user_saves_modified": False,
        "native_gameplay_verified": False,
        "native_qa_approved": False,
        "source_rights_and_native_testing_pending": True,
        "overlay_files": len(blobs),
        "native_files": len(native),
        "resource_integrity_verified": True,
        "resource_integrity_mode": "STATIC_OFFLINE_ONLY",
        "referenced_graphics_count": integrity["referenced_graphics_count"],
        "profile": report["save_isolation"],
    }
    if not do_install:
        return result
    dest = work / (QA_PREFIX + profile)
    installed = install(root, root / "game", dest, report, blobs, native)
    checked = verify(dest, project=root)
    if (not installed.get("created")
            or not checked["save_namespace_verified"]
            or not checked["no_foreign_save_in_qa"]
            or checked["compiled_marker_present"]
            or not checked["compile_request_pending"]
            or checked["ready_to_launch_for_manual_testing"]
            or checked["playable_approved"]):
        blocked("copia QA criada, mas verificacao final falhou; inspecione antes de iniciar")
    return {
        **result,
        "status": "PRIVATE_QA_INSTALLED_NATIVE_COMPILATION_PENDING",
        "created": True,
        "qa_directory": str(dest),
        "verified_file_hashes": True,
        "save_namespace_verified": True,
        "compile_request_pending": True,
    }


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--project", type=Path, default=ROOT)
    cli.add_argument("--auto", action="store_true",
                     help="overlay unico com relatorio e .blue-work/sinnoh-qa-spec.json")
    cli.add_argument("--overlay", type=Path)
    cli.add_argument("--spec", type=Path)
    cli.add_argument("--install", action="store_true",
                     help="opt-in: criar NOVA copia QA privada nao jogavel")
    args = cli.parse_args(argv)
    try:
        if args.auto:
            if args.overlay is not None or args.spec is not None:
                blocked("--auto nao aceita caminhos alternativos")
            overlay, spec = select_auto(args.project)
        else:
            if args.overlay is None or args.spec is None:
                blocked("forneca --overlay e --spec ou use --auto")
            overlay, spec = args.overlay, args.spec
        result = execute(args.project, overlay=overlay, spec=spec,
                         do_install=args.install)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
