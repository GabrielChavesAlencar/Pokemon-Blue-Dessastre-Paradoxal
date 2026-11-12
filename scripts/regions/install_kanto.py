"""Optional, transactional installation of the isolated Kanto pilot into game/.

Dry run is the default. Do not copy game executables, System.rxdata, INI,
mkxp config or saves. Assets from the authorized FRLG kit stay local.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from audit import ROOT, KANTO, json_file
from pilot import OUTPUT, SOURCE, PILOT_META, TYPES, build, pilot_is_current, revised_path
from verify_pilot import inspect

PBS_NAMES = ("encounters_kanto.txt", "trainers_kanto.txt", "trainer_types_kanto.txt",
             "map_metadata_kanto.txt", "map_connections_kanto.txt")
DATA_NAMES = ("MapInfos.rxdata", "Tilesets.rxdata")
PLUGIN = Path("Plugins/ZZZZZ Blue Kanto Pilot")
MARKER = Path("Data/blue-kanto-start.txt")
PORTRAITS = tuple(f"BLUE_KANTO_{kind}.png" for kind in TYPES)


def trainer_portraits(pilot):
    """Every trainer type copied by pilot.install_pbs must follow maps."""
    folder = pilot / "Graphics" / "Trainers"
    result = {}
    for name in PORTRAITS:
        source = folder / name
        if not source.is_file() or not source.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError(f"Missing or invalid Kanto trainer portrait: {name}")
        result[Path("Graphics") / "Trainers" / name] = source
    return result



def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".blue-kanto-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def manifest(pilot, game):
    if not pilot_is_current(pilot):
        raise ValueError("Piloto antigo ou ausente; reconstrua a copia.")
    proof = inspect(pilot)
    expected_count = len(json_file(KANTO)["maps"])
    if proof["maps"] != expected_count:
        raise ValueError(f"A auditoria nao confirmou {expected_count} mapas.")
    info = json.loads((pilot / PILOT_META).read_text(encoding="utf-8"))
    expected = info.get("base_data_sha256", {})
    if set(expected) != set(DATA_NAMES):
        raise ValueError("Hashes da instalacao original ausentes.")
    for name in DATA_NAMES:
        if digest(game / "Data" / name) != expected[name]:
            raise ValueError("Base alterada depois de preparar o piloto: " + name)
    mapping = {int(k): int(v) for k, v in info["maps"].items()}
    files = {Path("Data") / name: pilot / "Data" / name for name in DATA_NAMES}
    for dest in mapping.values():
        file = Path("Data") / ("Map%03d.rxdata" % dest)
        files[file] = pilot / file
    for name in PBS_NAMES:
        file = Path("PBS") / name
        files[file] = pilot / file
    # Generated-only regional audio manifest: MapIDs come from the pilot.
    music_file = Path("Data/blue-kanto-music.txt")
    files[music_file] = pilot / music_file
    # Import only approved regional BGM tracks. Already-identical user MP3s are
    # untouched; conflicting files abort before any map is installed.
    from scripts.music.compile_kanto_music import approved_track_numbers
    selected = approved_track_numbers(ROOT)
    catalog = json_file(ROOT / "data/kanto-music.json")
    for item in catalog["files"]:
        if item["number"] not in selected:
            continue
        relative = Path(item["game_path"])
        source_audio = pilot / relative
        if (source_audio.is_symlink() or not source_audio.is_file() or
                not source_audio.resolve().is_relative_to(pilot.resolve())):
            raise ValueError("Musica de Kanto nao preparada: " + str(relative))
        if digest(source_audio) != digest(ROOT / item["repo_path"]):
            raise ValueError("Musica de Kanto divergente: " + str(relative))
        destination_audio = game / relative
        if not destination_audio.resolve().is_relative_to(game.resolve()):
            raise ValueError("Destino de audio inseguro: " + str(relative))
        if destination_audio.exists():
            if not destination_audio.is_file() or digest(destination_audio) != digest(source_audio):
                raise ValueError("Audio existente diferente, recusar sobrescrita: " + str(relative))
            continue
        files[relative] = source_audio
    for path in (pilot / PLUGIN).rglob("*"):
        if path.is_file():
            files[PLUGIN / path.relative_to(pilot / PLUGIN)] = path
    for name in ("Tilesets", "Autotiles", "Characters"):
        folder = pilot / "Graphics" / name
        for path in folder.glob("*.png"):
            if path.name.startswith(("FRLG_Pilot_", "FRLG_Preview_")):
                files[Path("Graphics") / name / path.name] = path
    # Previously omitted: the trainer portraits referenced by the
    # BLUE_KANTO_* PBS types. Import only these explicit names, never all art.
    files.update(trainer_portraits(pilot))
    for relative, source in files.items():
        if not source.is_file():
            raise ValueError("Arquivo de origem ausente: " + str(relative))
        if relative.parts[:2] != ("Data", "MapInfos.rxdata") and relative.parts[:2] != ("Data", "Tilesets.rxdata"):
            if (game / relative).exists():
                raise ValueError("Destino ocupado, recusado: " + str(relative))
    if not any(k.parts[:2] == ("Graphics", "Tilesets") for k in files):
        raise ValueError("Tilesets da origem nao encontrados.")
    return files, mapping, expected


def repair_portraits(game, commit=False):
    """Only add missing Kanto trainer images to an existing install.

    Copies from original trainer type images already on the user's computer.
    Never rebuilds/imports maps, and never overwrites an unknown image.
    """
    if not (game / MARKER).is_file():
        raise ValueError("Kanto must already be installed before portrait repair")
    manifest_path = game / "Data/blue-kanto-install.json"
    if not manifest_path.is_file():
        raise ValueError("Kanto installation manifest missing; refusing repair")
    old_bytes = manifest_path.read_bytes()
    info = json.loads(old_bytes.decode("utf-8"))
    if info.get("schema") != 1:
        raise ValueError("Unknown Kanto install manifest version")

    pending = {}
    for kind, base in TYPES.items():
        relative = Path("Graphics/Trainers") / f"BLUE_KANTO_{kind}.png"
        target = game / relative
        source = game / "Graphics/Trainers" / f"{base}.png"
        if not source.is_file() or not source.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError(f"Original trainer portrait not found: {base}.png")
        if target.exists():
            if digest(target) != digest(source):
                raise ValueError(f"Existing portrait differs; refusing to overwrite: {relative}")
        else:
            pending[relative] = source
    plan = {"status": "repair_preview", "missing_portraits": [str(k) for k in pending],
            "total_expected": len(PORTRAITS)}
    if not commit or not pending:
        if not pending:
            plan["status"] = "already_correct"
        return plan

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = ROOT / ".blue-backups" / ("kanto-portraits-" + stamp)
    backup.mkdir(parents=True, exist_ok=False)
    atomic(backup / "Data/blue-kanto-install.json", old_bytes)
    written = []
    try:
        for relative, source in pending.items():
            target = game / relative
            # Recheck just before writing; refuse a concurrent external edit.
            if target.exists():
                raise ValueError(f"Portrait appeared during repair: {relative}")
            atomic(target, source.read_bytes())
            written.append(target)
            if digest(target) != digest(source):
                raise IOError(f"Portrait checksum mismatch: {relative}")
        checksums = info.setdefault("installed_sha256", {})
        for kind in TYPES:
            relative = Path("Graphics/Trainers") / f"BLUE_KANTO_{kind}.png"
            checksums[str(relative)] = digest(game / relative)
        atomic(manifest_path, (json.dumps(info, indent=2) + "\n").encode("utf-8"))
    except BaseException:
        for target in reversed(written):
            target.unlink(missing_ok=True)
        atomic(manifest_path, old_bytes)
        raise
    plan.update(status="repaired", backup=str(backup))
    return plan


def apply_install(game, pilot, commit=False):
    if (game / MARKER).exists():
        raise ValueError("Kanto ja instalado: recusar IDs duplicados.")
    files, mapping, original_hashes = manifest(pilot, game)
    plan = {"status": "dry_run", "maps": len(mapping), "files": len(files),
            "start": [mapping[7], 25, 7], "map_ids": mapping}
    if not commit:
        return plan

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = ROOT / ".blue-backups" / ("kanto-" + stamp)
    backup.mkdir(parents=True, exist_ok=False)
    extra = [Path("Data/blue-kanto-install.json"), MARKER,
             Path("Data/blue-compile-request.txt"), Path("Data/PluginScripts.rxdata")]
    originals = {}
    for relative in list(files) + extra:
        target = game / relative
        originals[relative] = target.read_bytes() if target.is_file() else None
        if originals[relative] is not None:
            atomic(backup / relative, originals[relative])
    info = {"schema": 1, "maps": mapping, "base_data_sha256": original_hashes,
            "installed_sha256": {str(k): digest(v) for k, v in files.items()},
            "source": "Essentials FRLG 21.1"}
    try:
        for relative, source in files.items():
            atomic(game / relative, source.read_bytes())
            if digest(game / relative) != info["installed_sha256"][str(relative)]:
                raise IOError("Checksum incorreto: " + str(relative))
        (game / "Data/PluginScripts.rxdata").unlink(missing_ok=True)
        atomic(game / "Data/blue-compile-request.txt", b"compile")
        atomic(game / "Data/blue-kanto-install.json",
               (json.dumps(info, indent=2) + "\n").encode("utf-8"))
        # The marker is deliberately committed LAST. No menu until ready.
        start = "BLUE_KANTO_START_V1,KANTO,%d,25,7\n" % mapping[7]
        atomic(game / MARKER, start.encode("ascii"))
    except BaseException:
        for relative, old in reversed(list(originals.items())):
            target = game / relative
            if old is None:
                target.unlink(missing_ok=True)
            else:
                atomic(target, old)
        raise
    plan["status"] = "installed"
    plan["backup"] = str(backup)
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--repair-portraits", action="store_true",
                        help="Only repair missing Kanto trainer images in an already installed game")
    parser.add_argument("--game", type=Path, default=ROOT / "game")
    parser.add_argument("--pilot", type=Path, default=OUTPUT)
    parser.add_argument("--source", type=Path, default=SOURCE)
    args = parser.parse_args()
    game, pilot = args.game.resolve(), args.pilot.resolve()
    work = (ROOT / ".blue-work").resolve()
    if not (game == (ROOT / "game").resolve() or game.is_relative_to(work)):
        parser.error("Destino fora de game/ e .blue-work")
    if not pilot.is_relative_to(work):
        parser.error("Piloto fora de .blue-work")
    if args.repair_portraits:
        print(json.dumps(repair_portraits(game, args.apply), indent=2))
        return
    if (game / MARKER).exists():
        print("Kanto ja instalado. Para corrigir retratos, use --repair-portraits.")
        return
    fresh = False
    try:
        meta = json.loads((pilot / PILOT_META).read_text(encoding="utf-8"))
        fresh = pilot_is_current(pilot) and all(
            meta["base_data_sha256"][n] == digest(game / "Data" / n)
            for n in DATA_NAMES)
    except (OSError, ValueError, KeyError, TypeError):
        fresh = False
    if not fresh:
        pilot = revised_path(pilot) if pilot.exists() else pilot
        build(args.source.resolve(), game, pilot)
    print(json.dumps(apply_install(game, pilot, args.apply), indent=2))


if __name__ == "__main__":
    main()
