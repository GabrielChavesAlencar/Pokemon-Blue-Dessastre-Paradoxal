"""Merge the locally audited 199-map Hoenn preview into the MAIN Decades game.

Unlike pilot_hoenn.stage, this NEVER copies a game, overwrites System/Scripts,
changes mkxp/save paths, or runs donor event scripts. Dry-run is the default.
The local author's ZIP + pinned Git tree are required for the first import.
No donor assets are committed to Git or redistributed by this utility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from audit import ROOT
from hoenn_qa_phase1 import check_source, check_tree
from pilot_hoenn import (
    Source, UPSTREAM, SOURCE_MAPS, START, build_overlay,
)
from prepare_hoenn_source import inspect_zip
from install_kanto import verify_installed as verify_kanto

MAIN = (ROOT / "game").resolve()
MANIFEST = Path("Data/blue-hoenn-install.json")
START_MARKER = Path("Data/blue-hoenn-start.txt")
READY_MARKER = Path("Data/blue-hoenn-ready.txt")
PLUGIN = "Plugins/ZZZZZ Blue Hoenn Pilot/HoennPilot.rb"
REQUIRED = (
    "Data/MapInfos.rxdata", "Data/Tilesets.rxdata", PLUGIN,
    "PBS/trainers_hoenn_pilot.txt", "PBS/trainer_types_hoenn_pilot.txt",
    "PBS/encounters_hoenn_pilot.txt", "PBS/map_metadata_hoenn_pilot.txt",
    "Data/blue-hoenn-pilot.txt",
)
ALLOWED_REPLACE = frozenset({
    "Data/MapInfos.rxdata", "Data/Tilesets.rxdata", "PBS/map_connections.txt",
})
FORBIDDEN = frozenset({
    "Data/System.rxdata", "Data/Scripts.rxdata", "Game.ini", "mkxp.json",
    "Hoenn pilot.json", "Data/blue-hoenn-test-stops.txt",
    "Data/blue-hoenn-compile-request.txt",
})
HEX = re.compile(r"^[a-f0-9]{64}$")


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def safe_file(game: Path, relative: str) -> Path:
    path = Path(relative)
    if (path.is_absolute() or ".." in path.parts or not path.parts or
            path.parts[0] not in {"Data", "PBS", "Graphics", "Audio", "Plugins"}):
        raise ValueError(f"Arquivo fora do escopo Hoenn: {relative}")
    target = game / path
    if target.is_symlink() or any(parent.is_symlink() for parent in
                                  list(target.parents)[:-1] if parent != game.parent):
        raise ValueError(f"Symlink recusado: {relative}")
    if not target.resolve().is_relative_to(game):
        raise ValueError(f"Arquivo fora da pasta do jogo: {relative}")
    return target


def atomic(path: Path, contents: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".blue-hoenn-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def detect_existing(game: Path) -> str:
    present = (game / MANIFEST).exists() or (game / START_MARKER).exists()
    partial = (game / "Data/blue-hoenn-pilot.txt").exists() or \
              (game / "PBS/trainers_hoenn_pilot.txt").exists() or \
              (game / PLUGIN).exists()
    return "installed" if present else "partial" if partial else "absent"


def verify_installed(game: Path) -> dict:
    """Read-only after installation; never infer verification from a marker."""
    proof_file = game / MANIFEST
    if not proof_file.is_file() or proof_file.is_symlink():
        raise ValueError("Hoenn ainda não está integrada.")
    data = json.loads(proof_file.read_text(encoding="utf-8"))
    maps = data.get("maps")
    if (data.get("schema") != 1 or data.get("region") != "HOENN" or
            data.get("source_commit") != UPSTREAM or
            data.get("status") != "INTEGRATED_FILES_READY_FOR_NATIVE_QA" or
            not isinstance(maps, dict) or
            set(maps) != {str(mid) for mid in SOURCE_MAPS} or
            len(set(maps.values())) != 199 or
            any(type(mid) is not int or not 700 <= mid <= 999 for mid in maps.values())):
        raise ValueError("Manifesto Hoenn inválido ou mapas remapeados.")
    start, town = data.get("start"), data.get("town")
    if (start != [maps[str(START[0])], START[1], START[2], 2] or
            not isinstance(town, list) or len(town) != 4 or
            town[0] != maps["7"] or
            not all(type(n) is int for n in town) or
            any(n < 0 for n in town[1:3]) or town[3] not in (2,4,6,8)):
        raise ValueError("Pontos iniciais de Hoenn inválidos.")
    marker = (game / START_MARKER)
    gate = (game / READY_MARKER)
    if (not marker.is_file() or marker.is_symlink() or
            marker.read_text("ascii").strip() !=
            f"BLUE_HOENN_START_V1,HOENN,{start[0]},{start[1]},{start[2]}" or
            not gate.is_file() or gate.is_symlink() or
            gate.read_text("ascii").strip() !=
            f"BLUE_HOENN_READY_V1,199,{start[0]},{town[0]},{town[1]},{town[2]},{town[3]}"):
        raise ValueError("Marcadores finais não correspondem ao manifesto.")
    entries = data.get("installed_sha256")
    if not isinstance(entries, dict) or not entries:
        raise ValueError("Manifesto sem hashes dos arquivos Hoenn.")
    for rel in [*REQUIRED, *(f"Data/Map{mid:03}.rxdata" for mid in maps.values())]:
        path = safe_file(game, rel)
        if not path.is_file() or not path.stat().st_size:
            raise ValueError(f"Arquivo de Hoenn ausente: {rel}")
    for rel in (PLUGIN, "Data/blue-hoenn-pilot.txt", "PBS/trainers_hoenn_pilot.txt",
                "PBS/encounters_hoenn_pilot.txt"):
        path = safe_file(game, rel)
        if not HEX.fullmatch(entries.get(rel, "")) or sha(path.read_bytes()) != entries[rel]:
            raise ValueError(f"Hoenn modificada ou não auditada: {rel}")
    return {"status": "integrated_files_ready_for_native_QA",
            "maps": 199, "start": start, "town": town,
            "shared_save": True, "game_exe_tested_here": False}


def vetted_town(report: dict, overlay: dict[str, bytes]) -> list[int]:
    """Use the builder's passability-verified stop for source Littleroot 7."""
    raw = overlay["Data/blue-hoenn-test-stops.txt"].decode("utf-8").splitlines()
    if len(raw) != 200 or raw[0] != "BLUE_HOENN_TEST_STOPS_V1":
        raise ValueError("Paradas de QA não foram auditadas para os 199 mapas.")
    line = next((line for line in raw[1:] if line.startswith("7|")), None)
    if not line:
        raise ValueError("Nenhum ponto seguro de chegada em Littleroot.")
    parts = line.split("|", 5)
    if len(parts) != 6:
        raise ValueError("Parada de Littleroot inválida.")
    src, dest, x, y, direction = map(int, parts[:5])
    if (src != 7 or dest != report["maps"][7] or x < 0 or y < 0 or
            direction not in (2,4,6,8)):
        raise ValueError("Ponto de Littleroot não coincide com o mapa auditado.")
    return [dest, x, y, direction]


def prepare_overlay(game: Path, source: Source) -> tuple[dict[str, bytes], dict]:
    """Compile fresh against the CURRENT Kanto+Decades MapInfos and free IDs."""
    original = {rel: sha((game / rel).read_bytes()) for rel in
                ("Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
                 "PBS/map_connections.txt")}
    overlay, report = build_overlay(game, source)
    if (report.get("source_commit") != UPSTREAM or report.get("region") != "HOENN"
            or set(report.get("maps", {})) != set(SOURCE_MAPS)
            or len(set(report["maps"].values())) != 199):
        raise ValueError("Auditoria do gerador de Hoenn incompleta.")
    if not isinstance(report.get("qa12"), dict):
        raise ValueError("Auditoria integrada QA12 não foi gerada.")
    town = vetted_town(report, overlay)
    start = [report["maps"][START[0]], START[1], START[2], 2]
    # Remove ONLY pilot-only output: never change launch settings/save folders.
    files = {rel: blob for rel, blob in overlay.items() if rel not in FORBIDDEN}
    if any(not isinstance(blob, bytes) for blob in files.values()):
        raise ValueError("Arquivo Hoenn sem conteúdo binário estável.")
    if "Data/System.rxdata" in files or "Data/Scripts.rxdata" in files:
        raise ValueError("O jogo principal não pode receber o boot do piloto.")
    expected_map_files = {f"Data/Map{mid:03}.rxdata" for mid in report["maps"].values()}
    generated = {rel for rel in files if re.fullmatch(r"Data/Map\d{3}\.rxdata", rel)}
    if generated != expected_map_files:
        raise ValueError("RXDATA de Hoenn ausentes ou fora do inventário.")
    for rel, blob in files.items():
        dest = safe_file(game, rel)
        if dest.exists() and rel not in ALLOWED_REPLACE and dest.read_bytes() != blob:
            raise ValueError(f"Arquivo existente de outra região não será sobrescrito: {rel}")
    proof = {
        "schema": 1, "region": "HOENN",
        "status": "INTEGRATED_FILES_READY_FOR_NATIVE_QA",
        "source_commit": UPSTREAM,
        "maps": {str(k): v for k, v in report["maps"].items()},
        "start": start, "town": town,
        "installed_sha256": {rel: sha(blob) for rel, blob in files.items()},
        "native_qa_approved": False,
        "source_rights_redistribution_approved": False,
        "pilot_debug_tools_installed": False,
        "base_before_sha256": original,
    }
    return files, proof


def apply(game: Path, archive: Path, inventory: Path, commit: bool = False) -> dict:
    game = game.resolve()
    if game != MAIN or not (game / "Game.exe").is_file():
        raise ValueError("Instalação de Hoenn permitida somente no game/ principal.")
    verify_kanto(game)
    status = detect_existing(game)
    if status == "installed":
        return verify_installed(game)
    if status == "partial":
        raise ValueError("Hoenn parcial/antiga detectada. Revisão manual obrigatória; IDs não serão migrados.")
    from hoenn_qa_phase1 import load_tree
    check_tree(load_tree(inventory, offline=not archive.is_file()))
    if not archive.is_file() or archive.is_symlink():
        raise ValueError("ZIP original de Hoenn ausente. O jogo principal foi preservado.")
    extracted = inspect_zip(archive, extract=True, include_audio=True)
    source = Source(ROOT / extracted["local_stage"], inventory)
    check_source(source)  # Git blob SHA + source assets/tilesets/audio.
    files, proof = prepare_overlay(game, source)
    result = {"status": "dry_run", "maps": 199, "files": len(files),
              "start": proof["start"], "town": proof["town"],
              "shared_save": True, "native_qa_approved": False}
    if not commit:
        return result
    # No donor run scripts or binary assets ever leave the local machine.
    for rel, digest in proof["base_before_sha256"].items():
        if sha(safe_file(game, rel).read_bytes()) != digest:
            raise ValueError(f"Base Kanto/Decades mudou durante a auditoria: {rel}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = ROOT / ".blue-backups" / ("hoenn-" + stamp)
    backup.mkdir(parents=True, exist_ok=False)
    extras = [str(MANIFEST), str(READY_MARKER), str(START_MARKER),
              "Data/blue-compile-request.txt", "Data/PluginScripts.rxdata"]
    originals = {}
    for rel in [*files, *extras]:
        path = safe_file(game, rel)
        originals[rel] = path.read_bytes() if path.is_file() else None
        if originals[rel] is not None:
            atomic(backup / rel, originals[rel])
    try:
        for rel, blob in files.items():
            atomic(safe_file(game, rel), blob)
            if sha(safe_file(game, rel).read_bytes()) != proof["installed_sha256"][rel]:
                raise IOError(f"Falha no hash após importar {rel}")
        # Native compiler merges regional PBS on next shared Game.exe launch.
        (game / "Data/PluginScripts.rxdata").unlink(missing_ok=True)
        atomic(game / "Data/blue-compile-request.txt", b"compile")
        atomic(game / MANIFEST, (json.dumps(proof, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        atomic(game / READY_MARKER,
               f"BLUE_HOENN_READY_V1,199,{proof['start'][0]},{proof['town'][0]}\n".encode("ascii"))
        # LAST write is the actual title/menu gate.
        atomic(game / START_MARKER,
               f"BLUE_HOENN_START_V1,HOENN,{proof['start'][0]},25,6\n".encode("ascii"))
        result.update(verify_installed(game))
    except BaseException:
        for rel, blob in reversed(list(originals.items())):
            path = safe_file(game, rel)
            if blob is None:
                path.unlink(missing_ok=True)
            else:
                atomic(path, blob)
        raise
    result["backup"] = str(backup)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, default=MAIN)
    parser.add_argument("--archive", type=Path,
                        default=ROOT / "The Pokémon World Project - Hoenn.zip")
    parser.add_argument("--inventory", type=Path,
                        default=ROOT / ".blue-work/hoenn-tree-pinned.json")
    parser.add_argument("--apply", action="store_true",
                        help="Permitir integração transacional; padrão somente simular")
    parser.add_argument("--verify-installed", action="store_true",
                        help="Verificar instalação existente sem usar o ZIP")
    args = parser.parse_args()
    try:
        result = (verify_installed(args.game.resolve()) if args.verify_installed else
                  apply(args.game, args.archive, args.inventory, args.apply))
    except (ValueError, KeyError, TypeError, IOError, OSError) as error:
        parser.exit(2, "HOENN BLOQUEADA: " + str(error) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
