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
PRIVATE_BUNDLE_NAME = "Johto_Offline_Fase12_Auditoria_Integracao_Privado.zip"


def candidate_bundles(project: Path):
    """Search only known, local user-owned package locations; never publish assets."""
    names = ("johto-offline12-preview.zip", PRIVATE_BUNDLE_NAME)
    directories = [project / ".blue-work", project, Path.home() / "Downloads"]
    profile = os.environ.get("USERPROFILE")
    if profile:
        directories.append(Path(profile) / "Downloads")
    for folder in directories:
        for name in names:
            candidate = folder / name
            if candidate.is_file() and not candidate.is_symlink():
                yield candidate


def inspect_current_baseline(game: Path, archive_path: Path) -> dict:
    """Explain whether the historical offline preview fits the CURRENT game.

    Hoenn may have changed MapInfos, Tilesets and allocated MapIDs since the
    private offline package was built. These are blockers, never an excuse to
    overwrite the current base or downgrade another installed region.
    """
    data = game / "Data"
    result = {"baseline_compatible": False, "rebase_required": True,
              "map_id_conflicts": [], "reason": ""}
    if not (data / "MapInfos.rxdata").is_file() or not (data / "Tilesets.rxdata").is_file():
        result["reason"] = "MapInfos/Tilesets atuais ausentes"
        return result
    with zipfile.ZipFile(archive_path) as archive:
        stage = json.loads(archive.read(OFFLINE_PREFIX + "johto-stage.json"))
    expected = (stage.get("native_mapinfos_sha256"),
                stage.get("native_tilesets_sha256"))
    actual = (checksum(data / "MapInfos.rxdata"),
              checksum(data / "Tilesets.rxdata"))
    collisions = [i for i in range(600, 682)
                  if (data / f"Map{i:03}.rxdata").exists()]
    result["map_id_conflicts"] = collisions
    result["baseline_compatible"] = expected == actual and not collisions
    result["rebase_required"] = expected != actual or bool(collisions)
    result["reason"] = ("Instalação atual difere da base OFFLINE 12: integrar com merge "
                        "de MapInfos/Tilesets e MapIDs livres, preservando Kanto/Hoenn."
                        if result["rebase_required"] else
                        "Prévia usa esta base, mas ainda exige scripts/PBS, direitos e QA nativa.")
    return result



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
    for source in candidate_bundles(project):
        try:
            bundle = inspect_offline_bundle(source)
            baseline = inspect_current_baseline(game, source)
        except (OSError, ValueError, KeyError, zipfile.BadZipFile,
                json.JSONDecodeError) as exc:
            return record(project, {"status": "offline_bundle_invalid", "reason": str(exc),
                                    "bundle_path": str(source)})
        return record(project, {"status": "offline_preview_not_installable",
                                "reason": baseline["reason"] +
                                " Johto continua bloqueada até conclusão de todos os testes.",
                                "bundle_path": str(source), "bundle": bundle,
                                "current_game": baseline})
    return record(project, {"status": "awaiting_johto_installable_release",
                            "reason": "Nenhum pacote Johto instalado e verificado. O Blue-Story procurou na pasta do projeto, .blue-work e Downloads. Johto não será habilitada sem instalador transacional e testes reais."})


if __name__ == "__main__":
    print(json.dumps(integrate(), ensure_ascii=False, indent=2))
