"""Phase 16 Johto final-install preflight: safe, read-only by default.

No map pack, licensed audio, verified trainer PBS or Game.exe-ready Johto
package exists yet. NEVER turn a geometry preview into a playable install.
--apply intentionally refuses until an audited, transactional installer with
real map/event/PC/Hall-of-Fame evidence has been implemented and reviewed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE_PROOFS = (
    "source_rights", "maps_and_warps", "sprites_and_tilesets",
    "story_events", "trainers_pbs", "battles_and_encounters",
    "native_save_reload", "hms_and_badges", "region_travel_and_box",
    "audio_rights_and_playback", "kanto_decades_regression",
    "windows_gameplay", "joiplay_gameplay",
)
PHASES = {
    1: "Auditoria de origem",
    2: "Inventário de mapas",
    3: "Prévia isolada de geometria",
    4: "Novo jogo em New Bark",
    5: "Violet, Falkner",
    6: "Azalea, Bugsy",
    7: "Goldenrod, Whitney",
    8: "Ecruteak, Morty",
    9: "Olivine, Cianwood, Chuck",
    10: "Ampharos, Jasmine",
    11: "Mahogany, Pryce",
    12: "Ice Path, Clair",
    13: "Elite Four, Lance",
    14: "Lendários e pós-jogo",
    15: "Músicas, treinadores, portal",
    16: "Integração, viagem e aceite",
}


def read_json(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return result


def audit(root: Path = ROOT) -> dict:
    root = root.resolve()
    blockers: list[str] = []
    source_path = root / "data/regions/johto-source.json"
    if not source_path.is_file():
        source = {}
        blockers.append("Fonte Johto: data/regions/johto-source.json ausente")
    else:
        source = read_json(source_path)
    archive_hash = source.get("source", {}).get("archive_sha256")
    if not isinstance(archive_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", archive_hash):
        blockers.append("Map Pack Johto original: SHA-256 da fonte não fixado")
    if source.get("mapping_verified") is not True or not source.get("maps"):
        blockers.append("MapIDs e warps reais de Johto não auditados")
    if source.get("source", {}).get("distribution_approved") is not True:
        blockers.append("Direitos de uso e distribuição dos tilesets/arte pendentes")
    if source.get("import_enabled") is not True:
        blockers.append("Importação Johto permanece bloqueada")
    phase_rows = []
    for number, name in PHASES.items():
        record = root / f"data/regions/johto-phase{number:02}.json"
        data = read_json(record) if record.is_file() else None
        integrated = bool(
            isinstance(data, dict) and data.get("region") == "JOHTO" and
            data.get("integrated") is True and
            data.get("validation") and
            all(value is True for value in data["validation"].values())
        )
        if number in range(5, 15) and not integrated:
            blockers.append(f"Etapa {number:02}: mapas/PBS/eventos/aceite real não integrados")
        phase_rows.append({
            "phase": f"{number:02}/16", "name": name,
            "manifest": record.relative_to(root).as_posix() if record.is_file() else None,
            "integrated_and_verified": integrated,
            "real_gameplay_accepted": False,
        })
    music_path = root / "data/johto-music.json"
    music = read_json(music_path) if music_path.is_file() else {}
    if music.get("license_verified") is not True or music.get("distribution_approved") is not True:
        blockers.append("Músicas de Johto sem licença de distribuição comprovada")
    if not music.get("recordings") or not music.get("verified_tracks"):
        blockers.append("Arquivos BGM/ME reais de Johto ainda ausentes")
    preview_path = root / "site/public/data/johto-preview.json"
    preview = read_json(preview_path) if preview_path.is_file() else {}
    if preview.get("maps_installed", 0) == 0:
        blockers.append("Portal Johto exibe apenas mapas simbólicos (zero instalados)")
    if preview.get("trainers_compiled", 0) == 0:
        blockers.append("PBS de Johto não compilados")
    game = root / "game"
    if not game.is_dir() or not (game / "Data/MapInfos.rxdata").is_file():
        blockers.append("Instalação local game/Data/MapInfos.rxdata indisponível para comparar hashes")
    pilot = root / ".blue-work/johto-pilot"
    verified_manifest = pilot / "Data/blue-johto-install.json"
    # Never use a staged geometry-only report or an unrelated Kanto manifest.
    if not verified_manifest.is_file():
        blockers.append("Piloto isolado sem manifesto de Johto com gameplay e hashes verificados")
    else:
        proof = read_json(verified_manifest)
        checks = proof.get("checks")
        if (proof.get("status") != "VERIFIED_PLAYABLE" or
                proof.get("schema") != 1 or proof.get("region") != "JOHTO" or
                not isinstance(checks, dict) or
                not all(checks.get(key) is True for key in RELEASE_PROOFS)):
            blockers.append("Manifesto de piloto não satisfaz provas mínimas da liberação")
    return {
        "schema": 1,
        "region": "JOHTO",
        "phase": "16/16",
        "status": "BLOCKED_AWAITING_ASSETS" if blockers else "REVIEW_REQUIRED_NOT_AUTO_INSTALLABLE",
        "dry_run": True,
        "apply_supported": False,
        "game_files_modified": 0,
        "technical_full_acceptance": 0,
        "gameplay_full_acceptance": 0,
        "phases": phase_rows,
        "blockers": blockers,
        "source_archive_sha256": archive_hash,
        "next_action": "Auditar Map Pack/RMXP e direitos, compilar eventos/PBS/áudio, testar em piloto, comprovar os 13 gates e só então construir instalador transacional com backups e rollback.",
    }


def save_report(report: dict, target: Path, root: Path = ROOT) -> None:
    work = (root.resolve() / ".blue-work").resolve()
    if work.is_symlink():
        raise ValueError("Workspace .blue-work symlink recusado")
    destination = target.absolute()
    if (not destination.resolve().is_relative_to(work) or
            destination.exists() or destination.is_symlink() or
            destination.resolve() == work):
        raise ValueError("Relatório deve ser novo e estar dentro de .blue-work")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--report", type=Path,
                        help="Salva JSON NOVO somente dentro de .blue-work")
    parser.add_argument("--strict", action="store_true",
                        help="Retorna código 2 enquanto houver bloqueios")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true",
                        help="Não disponível sem instalador transacional auditado")
    args = parser.parse_args(argv)
    try:
        report = audit(args.root)
        if args.report:
            save_report(report, args.report, args.root)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if args.apply:
            print("[JOHTO][BLOQUEADO] Aplicação transacional indisponível; nenhum jogo modificado.",
                  file=sys.stderr)
            return 2
        return 2 if args.strict and report["blockers"] else 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print("[JOHTO][BLOQUEADO] " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
