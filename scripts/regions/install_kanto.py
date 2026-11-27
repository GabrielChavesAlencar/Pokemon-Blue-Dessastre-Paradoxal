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
from audit import ROOT, KANTO, json_file, inventory, allocate_kanto_ids, load
from export_kanto import LOCATION_NAMES
from server.ruby_marshal import RubyObject, text
from cerulean_doors import verify_cerulean_doors
from pilot import (OUTPUT, SOURCE, PILOT_META, TYPES, build, pilot_is_current,
                   revised_path, EVENT_CLASSES, write_map)
from verify_pilot import inspect

PBS_NAMES = ("encounters_kanto.txt", "trainers_kanto.txt", "trainer_types_kanto.txt",
             "map_metadata_kanto.txt", "map_connections_kanto.txt", "items_kanto.txt")
DATA_NAMES = ("MapInfos.rxdata", "Tilesets.rxdata")
PLUGIN = Path("Plugins/ZZZZZ Blue Kanto Pilot")
MARKER = Path("Data/blue-kanto-start.txt")
READY_GATE = Path("Data/blue-kanto-ready.txt")


def ready_gate_bytes(mapping):
    return f"BLUE_KANTO_READY_V1,{len(mapping)},{mapping[7]}\n".encode("ascii")

PORTRAITS = tuple(f"BLUE_KANTO_{kind}.png" for kind in TYPES)
# Runtime-only files referenced by the authored Kanto plugin/events. The
# experimental teleport list and independent save profile are NOT integrated.
KANTO_RUNTIME_DATA = (
    "blue-kanto-npc-dialogues.dat",
    "blue-kanto-pewter-route3-gate.txt",
    "blue-kanto-pewter-mom-sprite.txt",
    "blue-kanto-viridian-route2-line.txt",
    "blue-kanto-silph-floors.txt",
)
KANTO_LOCALE = Path("Data/blue-kanto-locale.dat")


def trainer_portraits(pilot, *, candidate=False):
    """Every trainer type copied by pilot.install_pbs must follow maps."""
    folder = pilot / "Graphics" / "Trainers"
    result = {}
    for name in (*PORTRAITS, "BLUE_KANTO_GAMBLER.png") if candidate else PORTRAITS:
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


def recorded_hashes(proof):
    return {k.replace(chr(92), "/"): v for k, v in proof["installed_sha256"].items()}


def recorded_digest(value):
    return isinstance(value, str) and len(value) == 64 and all(
        c in "0123456789abcdef" for c in value.lower())


def legacy_map_identity(game, pilot, relative):
    """A changed map must still be the same FRLG location, not another region.

    Both maps are parsed as data, never executed. A missing file can be restored
    at a proven registry slot; a changed map must retain its dimensions and
    imported tileset identity. Old bytes are backed up by apply_install.
    """
    target = game / relative
    if not target.exists():
        return
    old, new = load(target), load(pilot / relative)
    if any(not isinstance(obj, RubyObject) or obj.name != "RPG::Map"
           for obj in (old, new)):
        raise ValueError("Invalid Kanto map structure: " + str(relative))
    if any(old.attrs.get(k) != new.attrs.get(k) for k in ("@width", "@height")):
        raise ValueError("Kanto map dimensions changed: " + str(relative))
    def tile_identity(root, obj):
        tiles = load(root / "Data/Tilesets.rxdata")
        idx = obj.attrs.get("@tileset_id")
        if type(idx) is not int or not 0 < idx < len(tiles):
            raise ValueError("Invalid Kanto tileset: " + str(relative))
        tile = tiles[idx]
        if not isinstance(tile, RubyObject) or tile.name != "RPG::Tileset":
            raise ValueError("Invalid Kanto tileset: " + str(relative))
        graphic = text(tile.attrs["@tileset_name"])
        if not graphic.startswith("FRLG_Preview_"):
            raise ValueError("Foreign tileset in Kanto slot: " + str(relative))
        return graphic
    if tile_identity(game, old) != tile_identity(pilot, new):
        raise ValueError("Kanto tileset identity changed: " + str(relative))


def check_migration_target(game, pilot, relative, source, proof):
    target = game / relative
    recorded = recorded_hashes(proof).get(relative.as_posix())
    if target.exists() and (digest(target) == digest(source) or recorded == digest(target)):
        return
    old_maps = {Path("Data") / f"Map{mid:03d}.rxdata" for mid in proof["maps"].values()}
    if relative in old_maps and recorded_digest(recorded):
        legacy_map_identity(game, pilot, relative)
        return
    if not target.exists():
        return
    # These are generated regional resources only, not user art or saves.
    generated = {Path("PBS") / name for name in PBS_NAMES}
    generated.update(Path("Data") / name for name in KANTO_RUNTIME_DATA)
    generated.update((KANTO_LOCALE, Path("Data/blue-kanto-music.txt"),
                      PLUGIN / "KantoPilot.rb", PLUGIN / "meta.txt"))
    if relative in generated and recorded_digest(recorded):
        return
    raise ValueError("Arquivo existente alterado ou sem prova Kanto: " + str(relative))


def install_catalogue(game, candidate=False):
    catalog = json_file(KANTO)
    if candidate:
        from k03e_contract import candidate_manifest, require_migration_game
        require_migration_game(ROOT, game)
        return candidate_manifest(catalog)
    return catalog


def manifest(pilot, game, migration=None, *, candidate=False):
    catalog = install_catalogue(game, candidate)
    if not pilot_is_current(pilot):
        raise ValueError("Piloto antigo ou ausente; reconstrua a copia.")
    proof = inspect(pilot, candidate=True) if candidate else inspect(pilot)
    expected_count = len(catalog["maps"])
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
    if migration is not None:
        old = {int(k): v for k, v in migration["maps"].items()}
        infos, occupied_files = inventory(game)
        wanted = {int(k) for k in catalog["maps"]}
        if mapping != allocate_kanto_ids(wanted, infos.keys() | occupied_files.keys(), old):
            raise ValueError("Migration changed existing MapIDs or new allocation")
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
    for name in KANTO_RUNTIME_DATA:
        relative = Path("Data") / name
        files[relative] = pilot / relative
    # Keep Kanto's reviewed NPC/plate locale as an isolated overlay. The
    # regular Blue plugin installer merges it without overwriting existing
    # Decades translations on every future ABRIR_JOGO.bat run.
    files[KANTO_LOCALE] = pilot / "Data/blue-pt-br.dat"
    # Import approved Kanto BGM and ME only. Already-identical user MP3s are
    # untouched; conflicting files abort before any map is installed.
    from scripts.music.compile_kanto_music import approved_audio_track_numbers
    selected = approved_audio_track_numbers(ROOT)
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
    files.update(trainer_portraits(pilot, candidate=True) if 79 in mapping else trainer_portraits(pilot))
    for relative, source in files.items():
        if not source.is_file():
            raise ValueError("Arquivo de origem ausente: " + str(relative))
        if relative.parts[:2] != ("Data", "MapInfos.rxdata") and relative.parts[:2] != ("Data", "Tilesets.rxdata"):
            target = game / relative
            if target.is_symlink() or not target.resolve().is_relative_to(game.resolve()):
                raise ValueError("Destino inseguro: " + str(relative))
            if target.exists():
                if migration is None:
                    raise ValueError("Destino ocupado, recusado: " + str(relative))
                if not target.is_file():
                    raise ValueError("Destino nao e arquivo: " + str(relative))
                check_migration_target(game, pilot, relative, source, migration)
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


def apply_install(game, pilot, commit=False, migration=None, *, candidate=False):
    if candidate:
        install_catalogue(game, True)
        if migration is None:
            raise ValueError("K03-E candidate requires an owned predecessor")
    if (game / MARKER).exists() and migration is None:
        raise ValueError("Kanto ja instalado: recusar IDs duplicados.")
    if migration is None:
        files, mapping, original_hashes = manifest(pilot, game)
    else:
        current_proof = legacy_proof(game, candidate=True) if candidate else legacy_proof(game)
        if current_proof != migration:
            raise ValueError("Kanto manifest changed during migration")
        files, mapping, original_hashes = (manifest(pilot, game, migration=migration, candidate=True)
                                           if candidate else manifest(pilot, game, migration=migration))
    plan = {"status": "dry_run", "maps": len(mapping), "files": len(files),
            "start": [mapping[7], 25, 7], "map_ids": mapping}
    if not commit:
        return plan

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = ROOT / ".blue-backups" / ("kanto-" + stamp)
    backup.mkdir(parents=True, exist_ok=False)
    extra = [Path("Data/blue-kanto-install.json"), READY_GATE, MARKER,
             Path("Data/blue-compile-request.txt"), Path("Data/PluginScripts.rxdata")]
    originals = {}
    for relative in list(files) + extra:
        target = game / relative
        if migration is not None and (target.is_symlink() or
                not target.resolve().is_relative_to(game.resolve()) or
                (target.exists() and not target.is_file())):
            raise ValueError("Unsafe migration target: " + str(relative))
        originals[relative] = target.read_bytes() if target.is_file() else None
        if originals[relative] is not None:
            atomic(backup / relative, originals[relative])
    if migration is not None:
        for name in DATA_NAMES:
            if digest(game / "Data" / name) != original_hashes[name]:
                raise ValueError("Shared map registry changed during migration")
        for relative in list(files) + extra:
            target = game / relative
            current = target.read_bytes() if target.is_file() else None
            if current != originals[relative]:
                raise ValueError("Installation changed during migration: " + str(relative))
            if (relative in files and relative.as_posix() not in
                    {"Data/MapInfos.rxdata", "Data/Tilesets.rxdata"}):
                check_migration_target(game, pilot, relative, files[relative], migration)
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
        # The Ruby engine may not have the JSON standard-library gem. This
        # small marker is written only AFTER every installed file and hash
        # passes; the original source + map manifest are still preserved.
        atomic(game / READY_GATE, ready_gate_bytes(mapping))
        # The marker is deliberately committed LAST. No menu until ready.
        start = "BLUE_KANTO_START_V1,KANTO,%d,25,7\n" % mapping[7]
        atomic(game / MARKER, start.encode("ascii"))
        if migration is not None:
            # Keep the final installed verification inside the rollback boundary.
            verify_installed(game, candidate=True) if candidate else verify_installed(game)
            plan["recovered_legacy_maps"] = [
                str(rel) for rel in files if rel.as_posix() in {
                    f"Data/Map{mid:03d}.rxdata" for mid in migration["maps"].values()
                } and (originals[rel] is None or
                       hashlib.sha256(originals[rel]).hexdigest() !=
                       recorded_hashes(migration).get(rel.as_posix()))
            ]
    except BaseException:
        for relative, old in reversed(list(originals.items())):
            target = game / relative
            if old is None:
                target.unlink(missing_ok=True)
            else:
                atomic(target, old)
        raise
    plan["status"] = "migrated" if migration is not None else "installed"
    plan["backup"] = str(backup)
    return plan


def known_legacy_catalog(wanted, previous):
    """Accept only published predecessor sets; never an arbitrary map count."""
    north = {"53", "54", "55"}
    interiors = {"43", "44", "45", "46", "47", "48"}
    if len(wanted) == 145 and north <= wanted and not interiors.intersection(wanted):
        return previous == wanted - north
    if len(wanted) == 151 and north | interiors <= wanted:
        return previous in (wanted - interiors, wanted - interiors - north)
    if len(wanted) == 152 and north | interiors | {"58"} <= wanted:
        published = wanted - {"58"}
        return previous in (published, published - interiors, published - interiors - north)
    diglett = {"23", "79", "81", "82"}
    if len(wanted) == 160 and diglett <= wanted:
        baseline = wanted - diglett
        return previous == baseline or known_legacy_catalog(baseline, previous)
    vermilion = {"68", "69", "70", "71"}
    if len(wanted) == 156 and north | interiors | {"58"} | vermilion <= wanted:
        baseline = wanted - vermilion
        return previous == baseline or known_legacy_catalog(baseline, previous)
    return False


def broken_current_cerulean(game, mapping):
    """Allow a same-catalogue rebuild only for a demonstrably broken city.

    The usual legacy_proof checks still validate ownership, map names and
    hashes; apply_install retains its backup/rollback and stable allocation.
    """
    if (not isinstance(mapping, dict) or
            any(type(v) is not int or not 0 < v < 1000 for v in mapping.values()) or
            not all(k in mapping for k in ("39", "43", "44", "45", "46", "47", "48"))):
        return False
    city = game / "Data" / f"Map{mapping['39']:03}.rxdata"
    if not city.is_file() or city.is_symlink():
        return False
    try:
        verify_cerulean_doors(city.read_bytes(), mapping)
    except (ValueError, OSError):
        return True
    return False


def verify_ss_anne_rival(game, mapping):
    """Check the actual installed source lanes and all three compiled-input PBS profiles."""
    if "75" not in mapping:
        return
    obj = load(game / "Data" / f"Map{mapping['75']:03}.rxdata")
    events = obj.attrs.get("@events", {})
    for event_id, x in ((22,31),(26,32),(27,33)):
        event = events.get(event_id)
        if (not isinstance(event, RubyObject) or
            (event.attrs.get("@x"), event.attrs.get("@y")) != (x,20) or
            not any(page.attrs.get("@trigger") == 1 and any(
                op.attrs.get("@code") == 355 and
                text(op.attrs["@parameters"][0]) == "BlueKantoPilot.ss_anne_rival"
                for op in page.attrs.get("@list", []))
                for page in event.attrs.get("@pages", []))):
            raise ValueError(f"S.S. Anne rival gate: missing source lane {event_id}")
    trainers = (game / "PBS/trainers_kanto.txt").read_text(encoding="utf-8-sig")
    headers = {line.strip() for line in trainers.splitlines()}
    if not all(f"[BLUE_KANTO_RIVAL,Blue,{v}]" in headers for v in (41,42,43)):
        raise ValueError("S.S. Anne rival gate: missing trainer profiles")


def outdated_current_ss_anne(game, mapping):
    if not isinstance(mapping, dict) or type(mapping.get("75")) is not int:
        return False
    city = game / "Data" / f"Map{mapping['75']:03}.rxdata"
    if not city.is_file() or city.is_symlink():
        return False
    try:
        verify_ss_anne_rival(game, mapping)
    except ValueError as error:
        return str(error).startswith("S.S. Anne rival gate:")
    return False


def legacy_proof(game, *, candidate=False):
    """Verify an exact published predecessor before transactional migration."""
    path = game / "Data/blue-kanto-install.json"
    marker = game / MARKER
    if any(p.is_symlink() or not p.is_file() for p in (path, marker)):
        raise ValueError("Missing legacy Kanto proof")
    proof = json_file(path)
    mapping = proof.get("maps")
    catalog = install_catalogue(game, candidate)
    wanted = {str(k) for k in catalog["maps"]}
    if (proof.get("schema") != 1 or proof.get("source") != "Essentials FRLG 21.1" or
            not isinstance(mapping, dict) or
            not (known_legacy_catalog(wanted, set(mapping)) or
                 (set(mapping) == wanted and (broken_current_cerulean(game, mapping) or
                                              outdated_current_ss_anne(game, mapping)))) or
            any(type(v) is not int or not 0 < v < 1000 for v in mapping.values()) or
            len(set(mapping.values())) != len(mapping) or
            marker.read_text(encoding="ascii").strip() !=
            f"BLUE_KANTO_START_V1,KANTO,{mapping.get('7')},25,7"):
        raise ValueError("Unknown legacy Kanto mapping; refusing migration")
    hashes = proof.get("installed_sha256")
    if not isinstance(hashes, dict):
        raise ValueError("Missing legacy Kanto checksums")
    hashes = recorded_hashes(proof)
    infos, files = inventory(game)
    source_names = catalog["maps"]
    for source_id, map_id in mapping.items():
        rel = f"Data/Map{map_id:03d}.rxdata"
        target = game / rel
        info = infos.get(map_id)
        if (not recorded_digest(hashes.get(rel)) or not isinstance(info, RubyObject) or
                info.name != "RPG::MapInfo" or target.is_symlink() or
                not target.resolve().is_relative_to(game.resolve()) or
                (target.exists() and not target.is_file())):
            raise ValueError("Legacy Kanto map ownership not proven: " + rel)
        if map_id not in files or hashes[rel] != digest(files[map_id]):
            expected_name = LOCATION_NAMES[source_names[source_id]]
            if text(info.attrs.get("@name", b"")) != expected_name:
                raise ValueError("Legacy Kanto map registry name differs: " + rel)
            print("[KANTO MIGRATION] " + ("missing" if map_id not in files else "checksum drift") +
                  ": " + rel + "; source reconstruction and backup required.", flush=True)
    gate = game / READY_GATE
    if gate.is_symlink() or (gate.exists() and gate.read_bytes() !=
            ready_gate_bytes({int(k): v for k, v in mapping.items()})):
        raise ValueError("Legacy Kanto ready marker conflicts with mapping")
    return proof


def preserve_k03e_predecessor(game, pilot, proof):
    """Stage an additive 156->160 upgrade without replacing existing events.

    The real native compiler expands raw transfers into fade/sound sequences.
    Do not substitute freshly generated raw maps for the compiled predecessor.
    Only copy an owned map after its geometry, identity, event IDs and stable
    allocation are checked. The new Route 2 door is separately source-audited.
    This function writes to the prepared pilot only, never the installed game.
    """
    from k03e_contract import MAPS, WARPS
    old = {int(k): v for k, v in proof["maps"].items()}
    new = {int(k): v for k, v in json_file(pilot / PILOT_META)["maps"].items()}
    if (len(old) != 156 or len(new) != 160 or
            set(new) - set(old) != set(MAPS) or
            any(new.get(sid) != mid for sid, mid in old.items())):
        raise ValueError("K03-E predecessor mapping differs")
    hashes = recorded_hashes(proof)
    preserved = {}
    route = None
    # Validate the entire predecessor before changing the staged payload.
    for sid, mid in old.items():
        path = Path("Data") / f"Map{mid:03d}.rxdata"
        prior, rebuilt = game / path, pilot / path
        if (not recorded_digest(hashes.get(path.as_posix())) or
                any(p.is_symlink() or not p.is_file() for p in (prior, rebuilt)) or
                not prior.resolve().is_relative_to(game.resolve()) or
                not rebuilt.resolve().is_relative_to(pilot.resolve())):
            raise ValueError("K03-E missing owned predecessor: " + str(path))
        legacy_map_identity(game, pilot, path)
        old_obj, new_obj = load(prior), load(rebuilt)
        if any(old_obj.attrs[k] != new_obj.attrs[k] for k in ("@width", "@height", "@data")):
            raise ValueError(f"K03-E predecessor geometry differs {sid}")
        previous, staged = old_obj.attrs["@events"], new_obj.attrs["@events"]
        if sid == 18:
            if 1 in previous or set(staged) != set(previous) | {1}:
                raise ValueError("K03-E Route2 event IDs differ")
            door = staged[1]
            page = door.attrs["@pages"][0].attrs
            dest, x, y, direction = WARPS[(18, 1)]
            transfers = [op.attrs["@parameters"][:5] for op in page["@list"]
                         if op.attrs["@code"] == 201]
            if (door.attrs["@id"] != 1 or page["@trigger"] != 1 or
                    transfers != [[0, new[dest], x, y, direction]]):
                raise ValueError("K03-E Route2 audited door differs")
            route = (path, old_obj, door)
        else:
            if set(previous) != set(staged):
                raise ValueError(f"K03-E predecessor event IDs differ {sid}")
            preserved[path] = digest(prior)
    if len(preserved) != 155 or route is None:
        raise ValueError("K03-E incomplete predecessor preservation")
    for path, checksum in preserved.items():
        raw = (game / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != checksum:
            raise ValueError("K03-E predecessor changed during preparation: " + str(path))
        atomic(pilot / path, raw)
    path, obj, door = route
    obj.attrs["@events"][1] = door
    write_map(pilot / path, obj, EVENT_CLASSES)
    if load(pilot / path) != obj or any(digest(pilot / p) != h for p, h in preserved.items()):
        raise ValueError("K03-E staged preservation verification failed")
    return preserved, path, obj.attrs


def migrate_existing(game, source, pilot, commit=False):
    proof = legacy_proof(game)
    mapping = {int(k): v for k, v in proof["maps"].items()}
    pilot = revised_path(pilot) if pilot.exists() else pilot
    build(source, game, pilot, existing=mapping)
    if len(mapping) == 156 and len(json_file(pilot / PILOT_META)["maps"]) == 160:
        preserve_k03e_predecessor(game, pilot, proof)
    return apply_install(game, pilot, commit, migration=proof)


def verify_installed(game, *, candidate=False):
    """Read-only check for the CURRENT integrated Kanto, not a gameplay test."""
    marker = game / MARKER
    proof_file = game / "Data/blue-kanto-install.json"
    if not marker.is_file() or not proof_file.is_file():
        raise ValueError("Kanto not installed in the main Decades game.")
    proof = json.loads(proof_file.read_text(encoding="utf-8"))
    mapping = proof.get("maps")
    catalog = install_catalogue(game, candidate)
    expected = len(catalog["maps"])
    if proof.get("schema") != 1 or proof.get("source") != "Essentials FRLG 21.1":
        raise ValueError("Unknown or incomplete Kanto main installation.")
    if not isinstance(mapping, dict) or len(mapping) != expected:
        raise ValueError(f"Older Kanto installation: {len(mapping) if isinstance(mapping,dict) else 0}/{expected} maps. Do not overwrite saves or merge IDs automatically.")
    if (candidate or "79" in catalog["maps"]) and set(mapping) != set(catalog["maps"]):
        raise ValueError("Invalid K03-E source map set")
    if len(set(mapping.values())) != expected:
        raise ValueError("Duplicated Kanto map IDs.")
    start = marker.read_text(encoding="ascii").strip()
    if start != f"BLUE_KANTO_START_V1,KANTO,{mapping['7']},25,7":
        raise ValueError("Kanto start marker does not match its installed mapping.")
    files = [game / "Data/MapInfos.rxdata", game / "Data/Tilesets.rxdata",
             game / "Data/blue-kanto-music.txt", game / KANTO_LOCALE,
             game / PLUGIN / "KantoPilot.rb"]
    files.extend(game / "Data" / name for name in KANTO_RUNTIME_DATA)
    files.extend(game / "PBS" / name for name in PBS_NAMES)
    files.extend(game / "Data" / f"Map{map_id:03}.rxdata"
                 for map_id in mapping.values())
    missing = [str(p.relative_to(game)) for p in files if not p.is_file()]
    if missing:
        raise ValueError(f"Kanto main installation missing {len(missing)} files; first: {missing[:5]}")
    if "43" in mapping:
        verify_cerulean_doors((game / "Data" / f"Map{mapping['39']:03}.rxdata").read_bytes(), mapping)
    verify_ss_anne_rival(game, mapping)
    return {"status": "integrated_files_ready_for_native_QA",
            "maps": expected, "kanto_start": [mapping["7"],25,7],
            "decades_save_modified": False, "game_exe_tested": False}



def sync_runtime(game, commit=False):
    """Refresh only the author's Kanto plugin after a verified integration.

    MapIDs, PBS, NPC events, System.rxdata and saves are NEVER rewritten.
    A manually edited plugin or an unknown installation manifest blocks the
    update instead of being replaced silently.
    """
    verified = verify_installed(game)
    # The native engine may not include Ruby's JSON gem. Add the plain-text
    # gate for older *verified* Kanto installs; never overwrite a foreign or
    # divergent marker. This operation does not touch maps or saves.
    ready_path = game / READY_GATE
    ready_text = (f"BLUE_KANTO_READY_V1,{verified['maps']},"
                  f"{verified['kanto_start'][0]}\n").encode("ascii")
    if ready_path.is_symlink():
        raise ValueError("Kanto ready gate is a symlink.")
    if ready_path.exists():
        if ready_path.read_bytes() != ready_text:
            raise ValueError("Kanto ready gate conflicts with installed map proof.")
    elif commit:
        atomic(ready_path, ready_text)
    rel = PLUGIN / "KantoPilot.rb"
    target = game / rel
    source = ROOT / "scripts/regions/KantoPilot.rb"
    proof_path = game / "Data/blue-kanto-install.json"
    old_proof_bytes = proof_path.read_bytes()
    proof = json.loads(old_proof_bytes.decode("utf-8"))
    recorded = proof.get("installed_sha256", {}).get(str(rel))
    if not isinstance(recorded, str) or len(recorded) != 64:
        raise ValueError("Kanto runtime has no original checksum; refusing automatic update.")
    current = digest(target)
    if current != recorded:
        raise ValueError("Kanto runtime was edited locally; refusing overwrite.")
    wanted = digest(source)
    if wanted == current:
        return {"status": "runtime_current", "changed": False}
    if not commit:
        return {"status": "runtime_update_preview", "changed": False}

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = ROOT / ".blue-backups" / ("kanto-runtime-" + stamp)
    backup.mkdir(parents=True, exist_ok=False)
    prior = target.read_bytes()
    compiled = game / "Data/PluginScripts.rxdata"
    trigger = game / "Data/blue-compile-request.txt"
    compiled_before = compiled.read_bytes() if compiled.is_file() else None
    trigger_before = trigger.read_bytes() if trigger.is_file() else None
    atomic(backup / rel, prior)
    atomic(backup / "Data/blue-kanto-install.json", old_proof_bytes)
    if compiled_before is not None:
        atomic(backup / "Data/PluginScripts.rxdata", compiled_before)
    if trigger_before is not None:
        atomic(backup / "Data/blue-compile-request.txt", trigger_before)
    try:
        atomic(target, source.read_bytes())
        if digest(target) != wanted:
            raise IOError("Failed verifying new Kanto runtime")
        proof["installed_sha256"][str(rel)] = wanted
        atomic(proof_path, (json.dumps(proof, indent=2) + "\n").encode("utf-8"))
        compiled.unlink(missing_ok=True)
        atomic(trigger, b"compile")
    except BaseException:
        atomic(target, prior)
        atomic(proof_path, old_proof_bytes)
        if compiled_before is None:
            compiled.unlink(missing_ok=True)
        else:
            atomic(compiled, compiled_before)
        if trigger_before is None:
            trigger.unlink(missing_ok=True)
        else:
            atomic(trigger, trigger_before)
        raise
    return {"status": "runtime_updated", "changed": True,
            "backup": str(backup)}



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--migrate-existing", action="store_true",
                        help="Migrate only a verified published Kanto catalog without reassigning IDs")
    parser.add_argument("--verify-installed", action="store_true",
                        help="Check main Kanto mapping/resources without changing files")
    parser.add_argument("--sync-runtime", action="store_true",
                        help="Safely update the installed Kanto plugin without overwriting maps or saves")
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
    if args.migrate_existing:
        print(json.dumps(migrate_existing(game, args.source.resolve(), pilot, args.apply),
                         ensure_ascii=False, indent=2))
        return
    if args.verify_installed:
        print(json.dumps(verify_installed(game), ensure_ascii=False, indent=2))
        return
    if args.sync_runtime:
        print(json.dumps(sync_runtime(game, args.apply), ensure_ascii=False, indent=2))
        return
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
