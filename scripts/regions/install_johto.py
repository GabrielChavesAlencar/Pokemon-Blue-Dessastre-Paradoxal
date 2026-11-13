"""Phase 16 Johto final-install preflight: safe, read-only by default.

No map pack, licensed audio, verified trainer PBS or Game.exe-ready Johto
package exists yet. NEVER turn a geometry preview into a playable install.
--apply intentionally refuses until an audited, transactional installer with
real map/event/PC/Hall-of-Fame evidence has been implemented and reviewed.
"""
from __future__ import annotations

import argparse
import hashlib
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


def verify_pilot_package(root: Path, pilot: Path) -> list[str]:
    """Read-only integrity check; synthetic data can NEVER prove gameplay QA."""
    issues: list[str] = []
    manifest = pilot / "Data/blue-johto-install.json"
    marker = pilot / "Data/blue-johto-start.txt"
    if pilot.is_symlink() or (pilot / "Data").is_symlink():
        return ["Piloto Johto: links simbólicos para dados executáveis recusados"]
    if not manifest.is_file() or manifest.is_symlink():
        return ["Piloto isolado sem manifesto de Johto com gameplay e hashes verificados"]
    try:
        proof = read_json(manifest)
    except (OSError, ValueError, json.JSONDecodeError):
        return ["Piloto Johto: manifesto ilegível ou inválido"]
    checks = proof.get("checks")
    if (proof.get("schema") != 1 or proof.get("region") != "JOHTO" or
            proof.get("status") != "VERIFIED_PLAYABLE" or
            not isinstance(checks, dict) or set(checks) != set(RELEASE_PROOFS) or
            not all(checks.get(key) is True for key in RELEASE_PROOFS)):
        issues.append("Piloto Johto: 13 comprovantes de release incompletos")
    source = read_json(root / "data/regions/johto-source.json")
    claimed_hash = proof.get("source_archive_sha256")
    source_hash = source.get("source", {}).get("archive_sha256")
    if (not isinstance(source_hash, str) or
            not re.fullmatch(r"[a-f0-9]{64}", source_hash) or
            claimed_hash != source_hash):
        issues.append("Piloto Johto: fonte do release diverge do SHA-256 auditado")

    points: dict[str, list[int]] = {}
    for name in ("start", "travel_point", "npc_point"):
        point = proof.get(name)
        if (not isinstance(point, list) or len(point) != 4 or
                any(type(v) is not int for v in point) or
                not 600 <= point[0] <= 999 or min(point[1:3]) < 0 or
                point[3] not in (2, 4, 6, 8)):
            issues.append(f"Piloto Johto: {name} sem coordenadas seguras")
        else:
            points[name] = point
    if len(points) == 3:
        start, town, npc = (points[name] for name in
                            ("start", "travel_point", "npc_point"))
        if (start[0] == town[0] or town[0] != npc[0] or
                town[1:3] == npc[1:3] or
                abs(town[1] - npc[1]) + abs(town[2] - npc[2]) > 3):
            issues.append("Piloto Johto: casa, chegada e NPC não são pontos seguros distintos")
        expected_marker = f"BLUE_JOHTO_START_V1,JOHTO,{start[0]},{start[1]},{start[2]}"
        if (not marker.is_file() or marker.is_symlink() or
                marker.read_text(encoding="utf-8").strip() != expected_marker):
            issues.append("Piloto Johto: marcador de início não coincide com os hashes")
    file_hashes = proof.get("file_hashes")
    if not isinstance(file_hashes, dict):
        return issues + ["Piloto Johto: lista de hashes ausente"]
    required = {"Data/MapInfos.rxdata", "Data/Tilesets.rxdata"}
    required.update(f"Data/Map{pos[0]:03}.rxdata" for pos in points.values())
    if not required.issubset(file_hashes):
        issues.append("Piloto Johto: MapInfos, Tilesets ou MapIDs sem hash obrigatório")
    for name, recorded in file_hashes.items():
        if (not isinstance(name, str) or
                not re.fullmatch(r"Data/(?:MapInfos|Tilesets|Map[0-9]{3})\.rxdata", name)):
            issues.append("Piloto Johto: caminho de hash inválido")
            continue
        if name.startswith("Data/Map") and name != "Data/MapInfos.rxdata":
            map_id = int(name[8:11])
            if not 600 <= map_id <= 999:
                issues.append(f"Piloto Johto: MapID {map_id} pode sobrescrever outra região")
                continue
        if not isinstance(recorded, str) or not re.fullmatch(r"[a-f0-9]{64}", recorded):
            issues.append(f"Piloto Johto: hash malformado de {name}")
            continue
        file = pilot / name
        if not file.is_file() or file.is_symlink() or file.stat().st_size == 0:
            issues.append(f"Piloto Johto: {name} ausente, vazio ou symlink")
            continue
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        if digest != recorded:
            issues.append(f"Piloto Johto: {name} modificado desde a auditoria")
    return issues


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
    # Never trust boolean attestations without checking actual files/coords.
    blockers.extend(verify_pilot_package(root, pilot))
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
        "next_action": "Usar johto_qa.py em cópia isolada com a prévia OFFLINE 12 compatível; compilar PBS e auditar direitos. O instalador público requer os 13 gates de release.",
    }


def save_report(report: dict, target: Path, root: Path = ROOT) -> None:
    raw_work = root.resolve() / ".blue-work"
    # Resolving first would hide a malicious link from .blue-work to game/.
    if raw_work.is_symlink():
        raise ValueError("Workspace .blue-work symlink recusado")
    work = raw_work.resolve()
    destination = target.absolute()
    if (not destination.resolve().is_relative_to(work) or
            destination.exists() or destination.is_symlink() or
            destination.resolve() == work):
        raise ValueError("Relatório deve ser novo e estar dentro de .blue-work")
    parent = destination.parent
    while parent != raw_work and parent != parent.parent:
        if parent.is_symlink():
            raise ValueError("Diretório simbólico no relatório recusado")
        parent = parent.parent
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive create: protect against late-created files and replacements.
    with destination.open("x", encoding="utf-8") as output:
        output.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


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
        print(json.dumps(report, ensure_ascii=True, indent=2))
        if args.apply:
            # Even --report must not create files when --apply is denied.
            print("[JOHTO][BLOQUEADO] Aplicação transacional indisponível; nenhum jogo modificado.",
                  file=sys.stderr)
            return 2
        if args.report:
            save_report(report, args.report, args.root)
        return 2 if args.strict and report["blockers"] else 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print("[JOHTO][BLOQUEADO] " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
