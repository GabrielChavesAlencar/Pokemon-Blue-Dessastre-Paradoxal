"""Install a reviewed Sinnoh overlay into the managed Blue-Story world."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from audit_sinnoh_rxdata import read_marshal
from install_hoenn import atomic, safe_file, sha
from pbs import HEADER
from sinnoh_f10b7_field_audit import cell_shape, directional_component, directional_masks
from sinnoh_legacy_plugin_guard import assert_no_legacy_sinnoh_shared
from sinnoh_private_visual import parse_connections
from stage import serialize

RECEIPT = "Data/blue-sinnoh-shared.json"
START = "Data/blue-sinnoh-shared.txt"
PLUGIN = "Plugins/ZZZZZ Blue Sinnoh Shared/SinnohSharedEvents.rb"
META = "Plugins/ZZZZZ Blue Sinnoh Shared/meta.txt"
MAP_INFOS = "Data/MapInfos.rxdata"
TILESETS = "Data/Tilesets.rxdata"
CONNECTIONS = "Data/map_connections.dat"
PBS_CONNECTIONS = "PBS/map_connections.txt"
MAP_PBS = {"PBS/encounters.txt", "PBS/map_metadata.txt"}
MAP_FILE = re.compile(r"Data/Map([0-9]{3})\.rxdata")
SHARED_FILES = {MAP_INFOS, TILESETS, CONNECTIONS, PBS_CONNECTIONS}
INSTALL_FILES = {PLUGIN, META, *SHARED_FILES}
ASSET = re.compile(r"(?:Graphics/(?:Tilesets|Autotiles|Characters)/SN(?:QA|SH)_[A-Za-z0-9_]+\.png|"
                   r"Audio/(?:BGM|BGS|ME|SE)/SN(?:QA|SH)_[A-Za-z0-9_]+\.(?:ogg|wav)|"
                   r"PBS/[a-z_]+_sinnoh(?:_[a-z0-9_]+)?\.txt)")
ID_RANGE = range(442, 600)
# A clean 151-map Kanto installation can use IDs through 450. Its upgrades
# can instead append above Hoenn. Use the same Sinnoh slots on both bases.
SHARED_IDS = range(451, 595)
QA_PROFILE = "BLUE_SINNOH_SHARED_QA_V1"
QA_MARKER = "Data/blue-sinnoh-shared-qa.txt"


def validate_manifest(data, *, android=False, qa=False):
    if not isinstance(data, dict):
        raise ValueError("Manifesto compartilhado de Sinnoh inválido.")
    approvals = ("map_ids", "asset_rights", "connected_world", "windows_travel")
    if android:
        approvals += ("joiplay_travel", "android_distribution")
    status = data.get("approvals", {})
    profile_ok = (not android and data.get("profile") == QA_PROFILE and isinstance(status,dict) and
                  all(status.get(key) is False for key in (*approvals,"joiplay_travel","android_distribution"))) if qa else (
                  data.get("profile") == "BLUE_SINNOH_SHARED_V1" and isinstance(status,dict) and
                  all(status.get(key) is True for key in approvals))
    if data.get("schema") != 1 or not profile_ok:
        raise ValueError("Sinnoh precisa de um pacote compartilhado revisado para esta plataforma.")
    ids = data.get("map_ids", [])
    if (not isinstance(ids, list) or len(ids) != 144 or
            any(type(mid) is not int or mid not in ID_RANGE for mid in ids) or ids != sorted(set(ids))):
        raise ValueError("Reserva dos 144 MapIDs de Sinnoh inválida.")
    for key in ("start", "arrival", "agent"):
        point = data.get(key)
        if (not isinstance(point, list) or len(point) != 3 or
                any(type(v) is not int or v < 0 for v in point) or point[0] not in ids):
            raise ValueError(f"Posição física de Sinnoh inválida: {key}")
    symbols = data.get("map_symbols")
    if (qa or symbols is not None) and (not isinstance(symbols,dict) or
            not all(isinstance(key,str) and key.startswith("SINNOH_") and type(mid) is int
                    for key,mid in symbols.items()) or sorted(symbols.values()) != ids or
            symbols.get("SINNOH_PLAYER_BEDROOM") != data["start"][0] or
            symbols.get("SINNOH_TWINLEAF_TOWN") != data["arrival"][0]):
        raise ValueError("Reserva simbólica dos MapIDs de Sinnoh inválida.")
    spawn, npc = data["arrival"], data["agent"]
    if spawn[0] != npc[0] or not 1 <= abs(spawn[1]-npc[1])+abs(spawn[2]-npc[2]) <= 4:
        raise ValueError("O agente regional deve ficar junto à chegada de Sinnoh.")
    hashes = data.get("files", {})
    base = data.get("base", {})
    if not isinstance(hashes, dict) or not isinstance(base, dict):
        raise ValueError("Inventário compartilhado de Sinnoh inválido.")
    files = set(hashes)
    required = INSTALL_FILES | {f"Data/Map{mid:03d}.rxdata" for mid in ids}
    shared_files = SHARED_FILES | (MAP_PBS & files)
    if not required <= files or any(not ASSET.fullmatch(rel) for rel in files-required-MAP_PBS):
        raise ValueError("O pacote Sinnoh contém um arquivo fora do overlay regional.")
    if set(base) != shared_files or any(not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
            for digest in [*hashes.values(), *base.values()]):
        raise ValueError("Hashes do pacote Sinnoh incompletos.")
    return data


def marker(data):
    rows = [data[key] for key in ("start", "arrival", "agent")] + [data["map_ids"]]
    return ("BLUE_SINNOH_SHARED_V1\n" + "".join(",".join(map(str,row))+"\n" for row in rows)).encode("ascii")


def verify_files(data, read, *, android=False, installed=False, qa=False):
    validate_manifest(data, android=android, qa=qa)
    # Shared indexes can grow when another region is added. Semantic checks below
    # verify that the installed Sinnoh maps are still bound to those indexes.
    # The editable global indexes may grow. The candidate's Sinnoh rows must
    # still be semantically identical in both connection formats.
    skip = SHARED_FILES if installed else set()
    infos = read_marshal(read(MAP_INFOS), "SINNOH_SHARED_INFOS")
    tiles = read_marshal(read(TILESETS), "SINNOH_SHARED_TILESETS")
    if not isinstance(infos, dict) or not set(data["map_ids"]) <= set(infos):
        raise ValueError("MapInfos não inclui todos os mapas de Sinnoh.")
    # The original audited source identifies Twinleaf Town by name.
    # Reject manifests that put the travel agent on a route or later city.
    town = infos[data["arrival"][0]]
    if getattr(town, "name", None) != "RPG::MapInfo" or town.attrs.get("@name") != b"Twinleaf Town":
        raise ValueError("A chegada e o Agente Regional de Sinnoh devem ficar em Twinleaf Town.")
    points = {data[key][0] for key in ("start", "arrival", "agent")}
    worlds = {}
    for rel, digest in data["files"].items():
        if rel in skip:
            continue
        raw = read(rel)
        if sha(raw) != digest:
            raise ValueError(f"Arquivo Sinnoh incompleto ou alterado: {rel}")
        map_file = MAP_FILE.fullmatch(rel)
        if map_file:
            mid = int(map_file[1])
            world = read_marshal(raw, "SINNOH_SHARED_MAP")
            tile_id = world.attrs.get("@tileset_id") if getattr(world,"name",None) == "RPG::Map" else None
            if type(tile_id) is not int or not 0 < tile_id < len(tiles) or not tiles[tile_id]:
                raise ValueError(f"Mapa Sinnoh sem tileset válido: {mid}")
            if mid in points:
                worlds[mid] = world
    if installed and read(START).replace(b"\r\n",b"\n") != marker(data):
        raise ValueError("Marcador de viagem de Sinnoh não corresponde à instalação.")
    if data.get("connection_rows") is not None:
        ids = set(data["map_ids"])
        native = read_marshal(read(CONNECTIONS), "SINNOH_SHARED_NATIVE_CONNECTIONS")
        local_native = [[a,ad.decode("ascii"),ao,b,bd.decode("ascii"),bo]
                        for a,ad,ao,b,bd,bo in native if a in ids or b in ids]
        local_pbs = [list(row) for row in parse_connections(read(PBS_CONNECTIONS))
                     if row[0] in ids or row[3] in ids]
        if local_native != data["connection_rows"] or local_pbs != local_native:
            raise ValueError("As conexões instaladas de Sinnoh divergem do pacote.")
    for key in ("start", "arrival", "agent"):
        mid,x,y = data[key]
        world = worlds[mid]
        if (not cell_shape(world, tiles, (x,y)).get("ordinary_walkable") or any(
                (event.attrs["@x"],event.attrs["@y"]) == (x,y) for event in world.attrs["@events"].values())):
            raise ValueError(f"Posição de Sinnoh ocupada ou intransitável: {key}")
    world = worlds[data["arrival"][0]]
    arrival = tuple(data["arrival"][1:])
    agent = tuple(data["agent"][1:])
    masks = directional_masks(world, tiles)
    occupied = {(event.attrs["@x"],event.attrs["@y"]) for event in world.attrs["@events"].values()}
    reachable = directional_component(set(masks)-occupied-{agent}, arrival, masks)
    if not any(abs(x-agent[0])+abs(y-agent[1]) == 1 for x,y in reachable):
        raise ValueError("O agente de saída não é alcançável a partir da chegada de Sinnoh.")
    return data


def map_pbs_sections(raw, path):
    sections = {}
    current = None
    for line in raw.decode("utf-8-sig").splitlines():
        line = line.strip()
        if match := HEADER.fullmatch(line):
            key = match[1]
            if not re.fullmatch(r"\d+(?:,\d+)?",key):
                raise ValueError(f"Seção PBS inválida em {path}: {key}")
            current = tuple(map(int,key.split(",")))
            if len(current) == 1:
                current += (0,)
            if current in sections:
                raise ValueError(f"MapID/versão PBS duplicados em {path}: {key}")
            sections[current] = []
        elif current is not None and line and not line.startswith("#"):
            sections[current].append(line)
    return sections


def preserve_map_pbs(path, before, after, ids):
    old, new = map_pbs_sections(before,path), map_pbs_sections(after,path)
    if (any(mid in ids for mid,_ in old) or
            any(new.get(key) != lines for key,lines in old.items()) or
            any(key[0] not in ids for key in new.keys()-old.keys())):
        raise ValueError(f"Sinnoh alteraria seções PBS de outras regiões em {path}.")


def preserve_base(game, data, files):
    before = {rel:safe_file(game,rel).read_bytes() for rel in data["base"]}
    if {rel:sha(raw) for rel,raw in before.items()} != data["base"]:
        raise ValueError("Pacote Sinnoh preparado para outra revisão do mundo compartilhado.")
    ids = set(data["map_ids"])
    for rel in MAP_PBS & before.keys():
        preserve_map_pbs(rel,before[rel],files[rel],ids)
    old = read_marshal(before[MAP_INFOS], "SINNOH_SHARED_BASE_INFOS")
    new = read_marshal(files[MAP_INFOS], "SINNOH_SHARED_NEW_INFOS")
    if (set(new)-set(old) != ids or ids & set(old) or
            any(mid not in new or serialize(info)!=serialize(new[mid]) for mid,info in old.items())):
        raise ValueError("O overlay alteraria a reserva ou o índice de mapas de outra região.")
    old = read_marshal(before[TILESETS], "SINNOH_SHARED_BASE_TILESETS")
    new = read_marshal(files[TILESETS], "SINNOH_SHARED_NEW_TILESETS")
    if serialize(old) != serialize(new[:len(old)]):
        raise ValueError("O overlay alteraria tilesets existentes.")
    old = read_marshal(before[CONNECTIONS], "SINNOH_SHARED_BASE_CONNECTIONS")
    new = read_marshal(files[CONNECTIONS], "SINNOH_SHARED_NEW_CONNECTIONS")
    added = new[len(old):]
    if new[:len(old)] != old or not added or any(row[0] not in ids or row[3] not in ids for row in added):
        raise ValueError("As conexões de Sinnoh alterariam outra região.")
    pbs = files[PBS_CONNECTIONS]
    if (not pbs.startswith(before[PBS_CONNECTIONS]) or
            [[a,ad.encode("ascii"),ao,b,bd.encode("ascii"),bo] for a,ad,ao,b,bd,bo in
             parse_connections(pbs[len(before[PBS_CONNECTIONS]):])] != added):
        raise ValueError("PBS e conexões compiladas de Sinnoh divergem.")


def installed(game, *, android=False, qa=False):
    read = lambda rel: safe_file(game, rel).read_bytes()
    if (game / QA_MARKER).exists() != qa:
        raise ValueError("Instalação de QA de Sinnoh exige o verificador local de QA.")
    return verify_files(json.loads(read(RECEIPT)), read, android=android, installed=True, qa=qa)


def integrate(project, game):
    project, game = project.resolve(), game.resolve()
    if game != project / "game":
        return {"changed": False, "status": "fora da instalação gerenciada"}
    if any((game / rel).exists() or (game / rel).is_symlink() for rel in (RECEIPT, START)):
        installed(game)
        return {"changed": False, "status": "já integrado"}
    folder = project / ".blue-work/sinnoh-shared"
    manifest = folder / "manifest.json"
    if any(path.is_symlink() for path in (folder.parent,folder,manifest)) or not manifest.resolve().is_relative_to(project):
        raise ValueError("O pacote compartilhado de Sinnoh contém um caminho indireto.")
    if not manifest.exists():
        return {"changed": False, "status": "aguardando pacote compartilhado aprovado"}
    lock = safe_file(game, "Data/.blue-sinnoh-install.lock")
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        return install_overlay(project, game, folder, manifest)
    finally:
        os.close(fd)
        lock.unlink()


def install_overlay(project, game, folder, manifest, *, qa=False):
    if any((game / rel).exists() for rel in (RECEIPT, START)):
        installed(game,qa=qa)
        return {"changed": False, "status": "já integrado"}
    assert_no_legacy_sinnoh_shared(game)
    if (game / "sinnoh-experimental-qa.json").exists():
        raise ValueError("O perfil experimental de Sinnoh deve ficar em uma cópia separada.")
    data = validate_manifest(json.loads(manifest.read_bytes()), qa=qa)
    files = {rel:safe_file(folder, rel).read_bytes() for rel in data["files"]}
    verify_files(data, files.__getitem__, qa=qa)
    additions = {safe_file(game, rel) for rel in files if rel not in data["base"]}
    if any(path.exists() for path in additions):
        raise ValueError("Arquivos de Sinnoh já existem sem registro de instalação compartilhada.")
    preserve_base(game, data, files)
    request = "Data/blue-compile-request.txt"
    cache = "Data/PluginScripts.rxdata"
    changes = {**files, request:b"compile", RECEIPT:manifest.read_bytes(), START:marker(data)}
    if qa:
        changes[QA_MARKER] = b"STAGED_SHARED_QA\n"
    paths = {rel:safe_file(game,rel) for rel in (*changes, cache)}
    originals = {rel:path.read_bytes() if path.is_file() else None for rel,path in paths.items()}
    if any(sha(originals[rel]) != digest for rel,digest in data["base"].items()):
        raise ValueError("O jogo compartilhado mudou durante a preparação de Sinnoh.")
    backup = project / ".blue-backups" / datetime.now(timezone.utc).strftime("sinnoh-%Y%m%dT%H%M%S%fZ")
    for rel,raw in originals.items():
        if raw is not None:
            atomic(safe_file(backup,rel), raw)
    try:
        paths[cache].unlink(missing_ok=True)
        for rel,raw in changes.items():
            atomic(paths[rel],raw)
        installed(game,qa=qa)
    except BaseException:
        for rel,raw in reversed(list(originals.items())):
            if raw is None:
                paths[rel].unlink(missing_ok=True)
            else:
                atomic(paths[rel],raw)
        raise
    return {"changed": True, "status": "integrado"}
