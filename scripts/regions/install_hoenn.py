"""Install or migrate the audited Hoenn catalog in the main Decades game.

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
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from audit import ROOT
from hoenn_catalog import (
    CATALOG_REVISION, LEGACY_SOURCE_IDS, approved_source_ids, marker_bytes, validate_manifest, verify_markers,
)
from hoenn_qa_phase1 import check_source, check_tree
from pilot_hoenn import (
    Source, UPSTREAM, SOURCE_MAPS, START, build_overlay,
)
from prepare_hoenn_source import inspect_zip
from hoenn_stage10 import LEGACY_VOID_SURF_BORDERS, RESTORED_SURF_BORDERS
from install_kanto import verify_installed as verify_kanto
from server.ruby_marshal import loads

MAIN = (ROOT / "game").resolve()
MANIFEST = Path("Data/blue-hoenn-install.json")
START_MARKER = Path("Data/blue-hoenn-start.txt")
READY_MARKER = Path("Data/blue-hoenn-ready.txt")
CONNECTIONS = "PBS/map_connections.txt"
COMPILE_REQUEST = "Data/blue-compile-request.txt"
PLUGIN_CACHE = "Data/PluginScripts.rxdata"
COMPACT = "Data/blue-hoenn-pilot.txt"
JOURNAL = "Data/.blue-hoenn-install-journal.json"
LOCK = "Data/.blue-hoenn-install.lock"
SURF_LAYOUT = 2
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
MIGRATION_BACKUP = re.compile(r"hoenn-v2-\d{8}T\d{12}Z")
MIGRATION_FILES = frozenset({
    CONNECTIONS, COMPILE_REQUEST, PLUGIN_CACHE, PLUGIN, COMPACT,
    MANIFEST.as_posix(), START_MARKER.as_posix(), READY_MARKER.as_posix(),
})


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


def verify_installed(game: Path, *, allow_pending: bool = False) -> dict:
    """Read-only after installation; never infer verification from a marker."""
    if not allow_pending and safe_file(game, JOURNAL).exists():
        raise ValueError("A migração de Hoenn precisa ser retomada pelo instalador.")
    proof_file = safe_file(game, MANIFEST.as_posix())
    if not proof_file.is_file():
        raise ValueError("Hoenn ainda não está integrada.")
    data = json.loads(proof_file.read_bytes())
    maps = validate_manifest(data)
    verify_markers(lambda name: safe_file(game, name).read_bytes(), data)
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
    if data["schema"] == 2:
        infos = loads(safe_file(game, "Data/MapInfos.rxdata").read_bytes())
        if not isinstance(infos, dict) or not set(maps.values()) <= infos.keys():
            raise ValueError("MapInfos não contém todos os MapIDs aprovados de Hoenn.")
    return {"status": "integrated_files_ready_for_native_QA", "maps": len(maps),
            "start": data["start"], "town": data["town"], "schema": data["schema"],
            "shared_save": True, "game_exe_tested_here": False}



def reconcile_surf_connections(raw: bytes, mapping: dict[int, int]) -> bytes:
    """Recognize either complete Hoenn layout, preserving every unrelated row."""
    from hoenn_qa_phase2 import ALL_BORDERS

    def row(border):
        a, side_a, offset_a, b, side_b, offset_b = border
        return ",".join(map(str, (mapping[a], side_a, offset_a,
                                  mapping[b], side_b, offset_b)))

    current = Counter(map(row, ALL_BORDERS))
    restored = [row(border) for border in RESTORED_SURF_BORDERS]
    obsolete = {row(border) for border in LEGACY_VOID_SURF_BORDERS}
    legacy = current - Counter(restored) + Counter(obsolete)
    owned = set(mapping.values())
    lines = raw.splitlines(keepends=True)
    observed = Counter()
    kept = []
    for index, line in enumerate(lines):
        encoding = "utf-8-sig" if index == 0 else "utf-8"
        cells = [cell.strip() for cell in line.decode(encoding).split("#", 1)[0].split(",")]
        body = ",".join(cells)
        if len(cells) == 6 and any(cell.isdecimal() and int(cell) in owned
                                   for cell in (cells[0], cells[3])):
            observed[body] += 1
        if body not in obsolete:
            kept.append(line)
    if observed == current:
        return raw
    if observed != legacy:
        raise ValueError("As conexões de Hoenn têm uma edição, duplicata ou migração parcial desconhecida.")
    newline = b"\r\n" if b"\r\n" in raw else b"\n"
    prefix = b"".join(kept)
    if prefix and not prefix.endswith(b"\n"):
        prefix += newline
    return prefix + newline.join(line.encode("ascii") for line in restored) + newline


@contextmanager
def installation_lock(game: Path):
    # The OS releases the lock if the process exits during a journaled write.
    with safe_file(game, LOCK).open("a+b") as handle:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def optional_bytes(path: Path) -> bytes | None:
    return path.read_bytes() if path.exists() else None


def optional_sha(blob: bytes | None) -> str | None:
    return sha(blob) if blob is not None else None


def migration_backup(name: str) -> Path:
    root = ROOT / ".blue-backups"
    if not isinstance(name, str) or not MIGRATION_BACKUP.fullmatch(name) or root.is_symlink():
        raise ValueError("Pasta de backup da migração de Hoenn inválida.")
    result = root / name
    if result.is_symlink():
        raise ValueError("Pasta de backup indireta da migração de Hoenn.")
    return result


def recover_migration(game: Path) -> bool:
    journal = safe_file(game, JOURNAL)
    if not journal.exists():
        return False
    transaction = json.loads(journal.read_bytes())
    files = transaction.get("files") if isinstance(transaction, dict) else None
    if not isinstance(files, dict) or set(files) != MIGRATION_FILES or transaction.get("schema") != 1:
        raise ValueError("Registro de recuperação de Hoenn inválido.")
    backup = migration_backup(transaction.get("backup"))
    restore = {}
    for rel, hashes in files.items():
        if (not isinstance(hashes, list) or len(hashes) != 2 or
                any(h is not None and (not isinstance(h, str) or not HEX.fullmatch(h)) for h in hashes)):
            raise ValueError("Hashes inválidos no registro de recuperação de Hoenn.")
        before, after = hashes
        path = safe_file(game, rel)
        current = optional_sha(optional_bytes(path))
        if current not in (before, after):
            raise ValueError(f"Arquivo mudou após a interrupção da migração de Hoenn: {rel}")
        if current != before:
            raw = safe_file(backup, rel).read_bytes() if before is not None else None
            if optional_sha(raw) != before:
                raise ValueError(f"Backup de Hoenn não corresponde ao registro: {rel}")
            restore[path] = raw
    for path, raw in reversed(list(restore.items())):
        if raw is None:
            path.unlink(missing_ok=True)
        else:
            atomic(path, raw)
    journal.unlink()
    return True


def commit_migration(game: Path, previous: dict, changes: dict) -> tuple[dict, Path]:
    paths = {rel: safe_file(game, rel) for rel in changes}
    backup = migration_backup(datetime.now(timezone.utc).strftime("hoenn-v2-%Y%m%dT%H%M%S%fZ"))
    backup.mkdir(parents=True, exist_ok=False)
    for rel, raw in previous.items():
        if raw is not None:
            atomic(safe_file(backup, rel), raw)
    if any(optional_bytes(path) != previous[rel] for rel, path in paths.items()):
        raise ValueError("A instalação mudou durante a preparação da migração de Hoenn.")
    hashes = {rel: [optional_sha(previous[rel]), optional_sha(raw)] for rel, raw in changes.items()}
    journal = safe_file(game, JOURNAL)
    atomic(journal, json.dumps({"schema": 1, "backup": backup.name, "files": hashes}).encode("utf-8"))
    try:
        for rel, raw in changes.items():
            path = paths[rel]
            if optional_bytes(path) != previous[rel]:
                raise ValueError(f"Arquivo mudou durante a migração de Hoenn: {rel}")
            if raw is None:
                path.unlink(missing_ok=True)
            elif raw != previous[rel]:
                atomic(path, raw)
        result = verify_installed(game, allow_pending=True)
    except BaseException:
        recover_migration(game)
        raise
    journal.unlink()
    return result, backup


def migrate_existing(game: Path, commit: bool) -> dict:
    """Upgrade the receipt and runtime in place, without importing legacy maps again."""
    from hoenn_qa_phase2 import inspect_connections
    from pilot_hoenn import allocate_hoenn_map_ids

    result = verify_installed(game)
    previous = {rel: optional_bytes(safe_file(game, rel)) for rel in MIGRATION_FILES}
    proof = json.loads(previous[MANIFEST.as_posix()])
    mapping = validate_manifest(proof)
    if set(mapping) != approved_source_ids(CATALOG_REVISION):
        raise ValueError("A revisão atual do catálogo requer um lote aditivo de mapas auditados.")
    ownership = allocate_hoenn_map_ids(game, mapping, previous=mapping)
    if ownership != mapping:
        raise ValueError("A migração de Hoenn não preservou os MapIDs registrados.")

    raw = previous[CONNECTIONS]
    if raw is None:
        raise ValueError("PBS de conexões de Hoenn ausente.")
    patched = reconcile_surf_connections(raw, mapping)
    layout = proof.get("surf_connection_layout")
    if layout not in (None, SURF_LAYOUT) or (layout == SURF_LAYOUT and patched != raw):
        raise ValueError("O manifesto de Hoenn declara conexões que não estão instaladas.")
    plugin = Path(__file__).with_name("HoennPilot.rb").read_bytes()
    if (proof["schema"] == 2 and proof["catalog_revision"] == CATALOG_REVISION and
            layout == SURF_LAYOUT and previous[PLUGIN] == plugin):
        return {**result, "catalog_migration_pending": False, "catalog_changed": False}
    maps = {source: loads(safe_file(game, f"Data/Map{dest:03}.rxdata").read_bytes())
            for source, dest in mapping.items()}
    inspect_connections(patched.decode("utf-8-sig"), mapping, maps)
    if not commit:
        return {**result, "catalog_migration_pending": True, "catalog_changed": False}

    proof.update(schema=2, catalog_revision=CATALOG_REVISION,
                 legacy_maps=dict(proof.get("legacy_maps", proof["maps"])),
                 surf_connection_layout=SURF_LAYOUT)
    markers = marker_bytes(proof)
    for name, raw in ((PLUGIN, plugin), (COMPACT, markers[COMPACT]), (CONNECTIONS, patched)):
        proof["installed_sha256"][name] = sha(raw)
    # New runtime and compile request precede the menu markers. The journal
    # keeps readers unavailable until final verification and clean commit.
    changes = {
        PLUGIN_CACHE: None, COMPILE_REQUEST: b"compile", CONNECTIONS: patched,
        PLUGIN: plugin, COMPACT: markers[COMPACT],
        MANIFEST.as_posix(): (json.dumps(proof, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        READY_MARKER.as_posix(): markers[READY_MARKER.as_posix()],
        START_MARKER.as_posix(): markers[START_MARKER.as_posix()],
    }
    result, backup = commit_migration(game, previous, changes)
    return {**result, "catalog_migration_pending": False, "catalog_changed": True, "backup": str(backup)}


def vetted_town(report: dict, overlay: dict[str, bytes]) -> list[int]:
    """Use the builder's passability-verified stop for source Littleroot 7."""
    raw = overlay["Data/blue-hoenn-test-stops.txt"].decode("utf-8").splitlines()
    if len(raw) != len(report["maps"]) + 1 or raw[0] != "BLUE_HOENN_TEST_STOPS_V1":
        raise ValueError("Paradas de QA não foram auditadas para o catálogo de Hoenn.")
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
            or set(report.get("maps", {})) != approved_source_ids(CATALOG_REVISION)
            or len(set(report["maps"].values())) != len(report["maps"])):
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
        "schema": 2, "region": "HOENN",
        "catalog_revision": CATALOG_REVISION,
        "legacy_maps": {str(k): v for k, v in report["maps"].items() if k in LEGACY_SOURCE_IDS},
        "status": "INTEGRATED_FILES_READY_FOR_NATIVE_QA",
        "source_commit": UPSTREAM,
        "maps": {str(k): v for k, v in report["maps"].items()},
        "surf_connection_layout": SURF_LAYOUT,
        "start": start, "town": town,
        "installed_sha256": {rel: sha(blob) for rel, blob in files.items()},
        "native_qa_approved": False,
        "source_rights_redistribution_approved": False,
        "pilot_debug_tools_installed": False,
        "base_before_sha256": original,
    }
    files[COMPACT] = marker_bytes(proof)[COMPACT]
    proof["installed_sha256"][COMPACT] = sha(files[COMPACT])
    return files, proof



def validated_local_source(archive: Path, inventory: Path) -> tuple[Source, str]:
    """Reuse pinned Hoenn data already staged by TESTAR_HOENN.bat.

    A private archive isn't necessary for a second import if the original
    staged files AND their SHA-pinned inventory still exist. This never
    trusts an isolated Game.exe, save, or Hoenn pilot.json for source data.
    """
    from hoenn_qa_phase1 import load_tree
    archive = Path(archive)
    if archive.is_symlink():
        raise ValueError("ZIP de Hoenn por link simbólico recusado.")
    staged = ROOT / ".blue-work" / "hoenn-source"
    if not archive.is_file() and not staged.is_dir():
        raise ValueError(
            "Fonte Hoenn ausente: coloque 'The Pokémon World Project - Hoenn.zip' "
            "na mesma pasta de TESTAR_HOENN.bat ou execute TESTAR_HOENN.bat para "
            "preparar a fonte. Nenhum mapa ou save foi alterado."
        )
    # Even with only the local staged data, obtain the pinned PUBLIC Git
    # inventory when absent; never infer hashes from a forged local manifest.
    check_tree(load_tree(inventory, offline=False))
    if archive.is_file():
        extracted = inspect_zip(archive, extract=True, include_audio=True)
        source = Source(ROOT / extracted["local_stage"], inventory)
        check_source(source)
        return source, "audited_private_zip"

    staged = ROOT / ".blue-work" / "hoenn-source"
    if staged.is_symlink():
        raise ValueError("Pasta da fonte Hoenn por link simbólico recusada.")
    if staged.is_dir():
        candidates = sorted(
            p for p in staged.iterdir()
            if p.is_dir() and not p.is_symlink() and re.fullmatch(r"[a-f0-9]{16}", p.name)
        )
        problems = []
        for directory in candidates:
            try:
                source = Source(directory, inventory)
                check_source(source)
                return source, "audited_staged_source"
            except (OSError, ValueError, KeyError, TypeError) as error:
                problems.append(f"{directory.name}: {error}")
        if problems:
            raise ValueError("Fonte Hoenn local não passou na conferência de hashes: " +
                             " | ".join(problems[:2]))
    raise ValueError(
        "Fonte Hoenn ausente: coloque 'The Pokémon World Project - Hoenn.zip' "
        "na mesma pasta de TESTAR_HOENN.bat ou prepare a fonte com TESTAR_HOENN.bat. "
        "Não é possível liberar viagem sem os 199 mapas reais."
    )


def apply(game: Path, archive: Path, inventory: Path, commit: bool = False) -> dict:
    game = game.resolve()
    if game != MAIN or not (game / "Game.exe").is_file():
        raise ValueError("Instalação de Hoenn permitida somente no game/ principal.")
    if commit:
        with installation_lock(game):
            recover_migration(game)
            return apply_catalog(game, archive, inventory, commit=True)
    return apply_catalog(game, archive, inventory, commit=False)


def apply_catalog(game: Path, archive: Path, inventory: Path, commit: bool) -> dict:
    verify_kanto(game)
    status = detect_existing(game)
    if status == "installed":
        return migrate_existing(game, commit)
    if status == "partial":
        raise ValueError("Hoenn parcial/antiga detectada. Revisão manual obrigatória; IDs não serão migrados.")
    source, origin = validated_local_source(archive, inventory)
    files, proof = prepare_overlay(game, source)
    result = {"status": "dry_run", "maps": len(proof["maps"]), "files": len(files),
              "start": proof["start"], "town": proof["town"],
              "shared_save": True, "native_qa_approved": False,
              "source_kind": origin}
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
        markers = marker_bytes(proof)
        atomic(game / READY_MARKER, markers[READY_MARKER.as_posix()])
        # LAST write is the actual shared title/menu marker.
        atomic(game / START_MARKER, markers[START_MARKER.as_posix()])
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
