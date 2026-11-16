"""Install an auto-updated Johto Map Studio folder beside Blue-Story.exe.

The official GitHub main source is first synced by Bootstrap.cs into the
managed project. This installer mirrors only PUBLIC editor source assets, not
game/Maps, ZIPs, saves, GitHub tokens, or installed private HGSS PNGs.

Launchers in the mirrored folder intentionally invoke the canonical managed
project's .bat; one installation, one set of maps/backups and one edit history.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path

FOLDER = "Johto-Map-Studio"
MARKER = ".blue-johto-studio.json"
SOURCES = {
    "editor/johto_map_editor.py": "scripts/regions/johto_map_editor.py",
    "editor/johto_map_patches.py": "scripts/regions/johto_map_patches.py",
    "editor/johto-map-editor.html": "web/johto-map-editor.html",
    "docs/JOHTO_MAP_STUDIO.md": "docs/JOHTO_MAP_STUDIO.md",
}
ENTRYPOINTS = {
    "EDITAR_MAPAS_JOHTO.bat": "EDITAR_MAPAS_JOHTO.bat",
    "CONECTAR_GITHUB_EDITOR_JOHTO.bat": "CONECTAR_GITHUB_EDITOR_JOHTO.bat",
}
MAX_ASSET = 2_000_000


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _checked_source(project: Path, name: str) -> bytes:
    src = project / name
    if src.is_symlink() or not src.is_file() or src.stat().st_size > MAX_ASSET:
        raise ValueError("Arquivo do editor não encontrado na main: " + name)
    return src.read_bytes()


def _batch(project: Path, script: str) -> bytes:
    root = str(project.resolve())
    if '"' in root or '\n' in root or '\r' in root or '%' in root:
        raise ValueError("Caminho do projeto não pode ser incorporado no atalho BAT")
    return (
        "@echo off\r\n"
        "setlocal EnableExtensions DisableDelayedExpansion\r\n"
        f'pushd "{root}"\r\n'
        "if errorlevel 1 (echo [ERRO] Pasta do jogo nao encontrada. & pause & exit /b 1)\r\n"
        f'if not exist "{script}" (echo [ERRO] Editor nao foi baixado da main. & pause & exit /b 1)\r\n'
        f'call "{script}"\r\n'
        "set \"RC=%ERRORLEVEL%\"\r\n"
        "popd\r\n"
        "exit /b %RC%\r\n"
    ).encode("utf-8")


def _files(project: Path) -> dict[str, bytes]:
    files = {name: _checked_source(project, source) for name, source in SOURCES.items()}
    for name, canonical in ENTRYPOINTS.items():
        # Explicit check before emitting a shortcut pointing into the project.
        _checked_source(project, canonical)
        files[name] = _batch(project, canonical)
    files["LEIA-ME.txt"] = (
        "JOHTO MAP STUDIO - Blue: Dessastre Paradoxal\r\n"
        "\r\n"
        "Este editor foi baixado automaticamente pela main do GitHub.\r\n"
        "Execute EDITAR_MAPAS_JOHTO.bat para abrir o editor no navegador.\r\n"
        "Use CONECTAR_GITHUB_EDITOR_JOHTO.bat para autenticar a sua conta GitHub.\r\n"
        "\r\n"
        f"O jogo, mapas, backups e patches sao mantidos SOMENTE em:\r\n{project}\r\n"
        "Os arquivos na subpasta editor/ sao copia de referencia do codigo,\r\n"
        "atualizados pelo Blue-Story. Nao edite manualmente essas copias.\r\n"
        "O editor funciona offline para desenhar, mas publicar exige GitHub.\r\n"
        "Feche Game.exe antes de salvar as edicoes do mapa.\r\n"
        "Se Johto nao estiver instalada, instale a regiao pelo Blue-Story primeiro.\r\n"
    ).encode("utf-8")
    return files


def install(project: Path, executable_dir: Path | None = None) -> dict:
    project = Path(project).resolve()
    if not (project / "scripts/install_game.py").is_file():
        raise ValueError("Pasta do projeto Blue-Story não encontrada")
    files = _files(project)
    locations = [project / FOLDER]
    if executable_dir is not None:
        adjacent = Path(executable_dir).resolve() / FOLDER
        if adjacent != locations[0]:
            locations.append(adjacent)

    result = {"schema": 1, "editor": FOLDER, "installed": [], "warnings": []}
    for dest in locations:
        try:
            if dest.is_symlink():
                raise ValueError("Pasta do editor é symlink; não sobrescrever")
            if dest.exists() and not dest.is_dir():
                raise ValueError("Já existe um arquivo com o nome do editor")
            manifest = dest / MARKER
            if dest.is_dir() and not manifest.is_file() and any(dest.iterdir()):
                raise ValueError("Pasta preexistente sem assinatura Blue; nada foi sobrescrito")
            if manifest.is_symlink():
                raise ValueError("Manifesto do editor é symlink")
            old = {}
            if manifest.is_file():
                old = json.loads(manifest.read_text("utf-8"))
                if old.get("schema") != 1 or old.get("owner") != "BLUE_STORY_JOHTO_MAP_STUDIO":
                    raise ValueError("Assinatura do editor não corresponde à instalação Blue")
            dest.mkdir(parents=True, exist_ok=True)
            old_hashes = old.get("files", {})
            previous = {}
            backups = {}
            written = []
            temps = []
            try:
                for relative, body in files.items():
                    target = dest / relative
                    if target.is_symlink() or target.parent.is_symlink():
                        raise ValueError("Arquivo de destino symlink: " + relative)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    prior = target.read_bytes() if target.is_file() else None
                    if prior == body:
                        continue
                    previous[target] = prior
                    if prior is not None:
                        # Unexpected local changes must never disappear silently.
                        if digest(prior) != old_hashes.get(relative):
                            backups[relative] = prior
                    staged = target.with_name(target.name + ".johto-new")
                    if staged.exists() or staged.is_symlink():
                        raise ValueError("Arquivo temporário do editor já existe")
                    staged.write_bytes(body)
                    temps.append(staged)
                for target, prior in previous.items():
                    staged = target.with_name(target.name + ".johto-new")
                    os.replace(staged, target)
                    written.append(target)
                # A manifest is the final write, so partial installs never
                # claim full synchronization when a source copy failed.
                marker = {
                    "schema": 1, "owner": "BLUE_STORY_JOHTO_MAP_STUDIO",
                    "project": str(project),
                    "files": {name: digest(body) for name, body in files.items()},
                }
                tmp_manifest = manifest.with_name(MARKER + ".tmp")
                if tmp_manifest.exists() or tmp_manifest.is_symlink():
                    raise ValueError("Manifesto temporário do editor já existe")
                tmp_manifest.write_text(json.dumps(marker, ensure_ascii=False, indent=2) + "\n", "utf-8")
                temps.append(tmp_manifest)
                os.replace(tmp_manifest, manifest)
                if backups:
                    backup_folder = project / ".blue-backups" / ("johto-editor-shortcut-" + uuid.uuid4().hex)
                    for relative, body in backups.items():
                        backup_path = backup_folder / relative
                        backup_path.parent.mkdir(parents=True, exist_ok=True)
                        backup_path.write_bytes(body)
                result["installed"].append(str(dest))
            except BaseException:
                for target in reversed(written):
                    prior = previous[target]
                    if prior is None:
                        target.unlink(missing_ok=True)
                    else:
                        target.write_bytes(prior)
                raise
            finally:
                for staged in temps:
                    staged.unlink(missing_ok=True)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            result["warnings"].append({"directory": str(dest), "reason": str(error)})
            # If even the managed folder failed, the install cannot provide
            # a working entrypoint; the optional adjacent folder is best effort.
            if dest == locations[0]:
                raise
    result["ready"] = len(result["installed"]) > 0
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--launcher-dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(install(args.project_root, args.launcher_dir),
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
