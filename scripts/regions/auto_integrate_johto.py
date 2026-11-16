"""Safely check Johto readiness after the Kanto/Hoenn main-game installers.

The OFFLINE 12 ZIP is a private QA preview, NOT a playable overlay. This
module never copies its maps or creates the release-proof/start markers.
Actual integration requires a separate transactional installer with native QA.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL_BUNDLE_SHA256 = "74e727875803f70b3c0598b6b88fe5d79717df849ba1b888fae0583c09202a49"
OFFLINE_PREFIX = "Johto_Offline_Fase12/"
OFFLINE_MAPS = frozenset(f"{OFFLINE_PREFIX}Data/Map{i:03}.rxdata" for i in range(600, 682))
BUNDLE_PATHS = (
    ".blue-work/johto-offline12-preview.zip",
    ".blue-work/Johto_Offline_Fase12_Auditoria_Integracao_Privado.zip",
    "Johto_Offline_Fase12_Auditoria_Integracao_Privado.zip",
)
STATUS = Path(".blue-work/johto-main-install-status.json")


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_offline_bundle(path: Path) -> dict:
    """Identify the audited original without extracting untrusted ZIP entries."""
    if not path.is_file() or path.is_symlink():
        raise ValueError("Pacote Johto ausente ou é um link simbólico")
    digest = checksum(path)
    if digest != ORIGINAL_BUNDLE_SHA256:
        raise ValueError("O ZIP encontrado não corresponde à auditoria OFFLINE 12 original")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or not OFFLINE_MAPS.issubset(names):
            raise ValueError("O pacote Johto não contém os 82 MapIDs auditados")
        if not {OFFLINE_PREFIX + "Data/MapInfos.rxdata",
                OFFLINE_PREFIX + "Data/Tilesets.rxdata",
                OFFLINE_PREFIX + "johto-offline12-audit.json"}.issubset(names):
            raise ValueError("Pacote de Johto sem metadados da auditoria")
        if archive.testzip() is not None:
            raise ValueError("CRC inválido no ZIP de Johto")
    return {"sha256": digest, "map_count": 82, "kind": "OFFLINE_12_PREVIEW_NOT_INSTALLABLE"}


def inspect_installed(project: Path, game: Path) -> list[str]:
    """Check a *previously installed* verified Johto build, never certify QA."""
    if not (game / "Data/blue-johto-install.json").is_file():
        return ["Manifesto de verificação Johto ausente"]
    installer = project / "scripts/regions/install_johto.py"
    if not installer.is_file():
        return ["Verificador de Johto ausente no projeto"]
    spec = importlib.util.spec_from_file_location("blue_johto_release_verifier", installer)
    if spec is None or spec.loader is None:
        return ["Falha ao carregar verificador Johto"]
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    errors = module.verify_pilot_package(project, game)
    for relative in (
        "Plugins/ZZZZZ Blue Johto Pilot/JohtoPilot.rb",
        "PBS/trainers_johto.txt",
        "PBS/trainer_types_johto.txt",
        "Data/PluginScripts.rxdata",
    ):
        file = game / relative
        if not file.is_file() or file.is_symlink() or file.stat().st_size == 0:
            errors.append("Arquivo Johto ausente na instalação principal: " + relative)
    if (game / "Johto pilot.json").exists():
        errors.append("Perfil isolado de Johto não pode habilitar o Decades principal")
    return errors


def record(project: Path, value: dict) -> dict:
    status = project / STATUS
    if status.parent.is_symlink() or status.is_symlink():
        raise ValueError("Relatório Johto não pode usar link simbólico")
    status.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": 1,
        "region": "JOHTO",
        "ready": value["status"] == "already_integrated_verified",
        "changed": False,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        **value,
    }
    temporary = status.with_name(status.name + ".tmp")
    try:
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, status)
    finally:
        temporary.unlink(missing_ok=True)
    return payload


def integrate(project: Path = ROOT, game: Path | None = None) -> dict:
    project = Path(project).resolve()
    game = Path(game or project / "game").resolve()
    if game != (project / "game").resolve():
        return record(project, {"status": "foreign_game_skipped", "reason": "Só a instalação game/ gerenciada é aceita"})
    if not (game / "Game.exe").is_file():
        return record(project, {"status": "no_game_skipped", "reason": "Decades ainda não está instalado"})
    proof = game / "Data/blue-johto-install.json"
    marker = game / "Data/blue-johto-start.txt"
    if proof.exists() or marker.exists():
        try:
            errors = inspect_installed(project, game)
        except (ValueError, KeyError, OSError, TypeError) as exc:
            errors = [str(exc)]
        if errors:
            return record(project, {"status": "existing_install_needs_review",
                                    "reason": "; ".join(errors[:5])})
        return record(project, {"status": "already_integrated_verified",
                                "reason": "Prova e conteúdo Johto instalados previamente e revalidados"})
    for candidate in BUNDLE_PATHS:
        source = project / candidate
        if not source.exists():
            continue
        try:
            bundle = inspect_offline_bundle(source)
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            return record(project, {"status": "offline_bundle_invalid", "reason": str(exc),
                                    "bundle_path": candidate})
        return record(project, {"status": "offline_preview_not_installable",
                                "reason": "82 mapas e PBS de preparação: falta conciliar mapas/tilesets após Kanto/Hoenn, instalador transacional, direitos e testes nativos Windows/JoiPlay",
                                "bundle_path": candidate, "bundle": bundle})
    return record(project, {"status": "awaiting_johto_installable_release",
                            "reason": "Nenhum pacote Johto instalado e verificado. A versão OFFLINE 12 não pode habilitar a região no jogo principal."})


if __name__ == "__main__":
    print(json.dumps(integrate(), ensure_ascii=False, indent=2))
