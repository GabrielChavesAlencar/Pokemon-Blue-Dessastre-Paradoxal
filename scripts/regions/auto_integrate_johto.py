"""Install a strictly local/private Johto experimental main-game preview.

The OFFLINE 12 ZIP alone is NOT an executable release. Its pinned assets are
compiled into a guarded 100-map early-access integration by
johto_main_preview.py, with backups and no Kanto/Hoenn map overlaps.
Never produce the final 13-point VERIFIED_PLAYABLE release proof here.
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
    """Find private ZIPs, including names Windows browsers assign to duplicates.

    Never scan arbitrary files, hidden paths or symlinks; every candidate must
    still pass the pinned whole-archive SHA-256 before the installer uses it.
    """
    directories = [project / ".blue-work", project, Path.home() / "Downloads"]
    profile = os.environ.get("USERPROFILE")
    if profile:
        directories.append(Path(profile) / "Downloads")
    seen = set()
    for directory in directories:
        if directory.is_symlink() or not directory.is_dir():
            continue
        for name in ("johto-offline12-preview.zip", PRIVATE_BUNDLE_NAME):
            path = directory / name
            if path.is_file() and not path.is_symlink():
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    yield path
        # Browsers save duplicate ZIPs as "(1)", "(2)", etc. Previously
        # this made Blue-Story report "missing" even with the correct bytes.
        for path in sorted(directory.glob("Johto_Offline_Fase12_Auditoria_Integracao_Privado (*.zip")):
            suffix = path.name.removeprefix("Johto_Offline_Fase12_Auditoria_Integracao_Privado ")
            if (suffix.startswith("(") and suffix.endswith(").zip")
                    and suffix[1:-5].isdigit() and path.is_file()
                    and not path.is_symlink() and path.resolve() not in seen):
                seen.add(path.resolve())
                yield path


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
        "ready": value["status"] in {"already_integrated_verified",
                    "experimental_installed_not_native_tested"},
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
    # The experimental proof is deliberately distinct from the final,
    # 13-point VERIFIED_PLAYABLE release proof.
    preview_manifest = game / "Data/blue-johto-main-preview.json"
    preview_marker = game / "Data/blue-johto-preview-ready.txt"
    if preview_manifest.exists() or preview_marker.exists():
        try:
            import sys
            sys.path.insert(0, str(project))
            sys.path.insert(0, str(project / "scripts/regions"))
            import johto_main_preview
            report = johto_main_preview.preview_proof(game)
            if report:
                # A copied Boot.rb is NOT replaced by Blue-Story's source update.
                # The first Johto preview used Compiler.singleton_class.prepend,
                # causing SystemStackError during native Compiler.main.
                # Apply the audited runtime-only hotfix transactionally, preserving
                # all 100 maps, global MapInfos/PBS and every save.
                hotfix = johto_main_preview.refresh_installed_runtime(game, project)
                return record(project, {"status": "experimental_installed_not_native_tested",
                                        "reason": "100 mapas Johto preservados; plugin Ruby verificado/atualizado. Compilação e gameplay nativos ainda pendentes",
                                        "map_count": 100, "native_qa": False,
                                        "changed": hotfix["changed"],
                                        "runtime_hotfix": hotfix.get("runtime_hotfix"),
                                        "backup_folder": hotfix.get("backup_folder")})
        except (ImportError, OSError, ValueError, KeyError, TypeError) as exc:
            return record(project, {"status": "existing_install_needs_review",
                                    "reason": str(exc)})
        return record(project, {"status": "existing_install_needs_review",
                                "reason": "Johto prévia parcialmente instalada; não iniciar ou sobrescrever"})
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
    rejected_sources = []
    for source in candidate_bundles(project):
        try:
            bundle = inspect_offline_bundle(source)
            baseline = inspect_current_baseline(game, source)
        except (OSError, ValueError, KeyError, zipfile.BadZipFile,
                json.JSONDecodeError) as exc:
            # An outdated preview cached in .blue-work must NOT hide a
            # valid original ZIP downloaded later by the user.
            rejected_sources.append(f"{source.name}: {exc}")
            continue
        # The original private ZIP is NOT copied directly into game/. It is
        # validated, visually repaired and remapped into unused 600–699 IDs
        # by the separate transactional builder. Hoenn owns 700–999.
        try:
            import sys
            sys.path.insert(0, str(project))
            sys.path.insert(0, str(project / "scripts/regions"))
            import johto_main_preview
            result = johto_main_preview.install(game, source, project, apply=True)
            installed = johto_main_preview.preview_proof(game)
            if not installed:
                raise ValueError("Instalação Johto sem prova estática verificável")
        except (ImportError, OSError, ValueError, KeyError, TypeError,
                AttributeError, IndexError) as exc:
            return record(project, {"status": "experimental_install_blocked",
                                    "reason": str(exc), "bundle_path": str(source),
                                    "bundle": bundle, "current_game": baseline})
        return record(project, {"status": "experimental_installed_not_native_tested",
                                "reason": "Prévia local de 100 mapas integrada, com saves compartilhados; falta validar Game.exe/JoiPlay. Campanha ainda experimental.",
                                "changed": True, "map_count": result["maps"],
                                "native_qa": False, "bundle_path": str(source),
                                "bundle": bundle, "current_game": baseline})
    if rejected_sources:
        return record(project, {"status": "offline_bundle_invalid",
                                "reason": "Pacotes Johto encontrados, mas nenhum tem o SHA-256 original: " +
                                "; ".join(rejected_sources[:4])})
    return record(project, {"status": "awaiting_johto_installable_release",
                            "reason": "ZIP privado Johto OFFLINE 12 não encontrado. Salve Johto_Offline_Fase12_Auditoria_Integracao_Privado.zip na pasta Downloads e reabra Blue-Story.exe. Kanto/Hoenn e os saves foram preservados."})


if __name__ == "__main__":
    print(json.dumps(integrate(), ensure_ascii=False, indent=2))
