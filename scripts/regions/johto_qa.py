"""Stage the offline-12 Johto bundle in a private, disposable Windows QA copy."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import struct
import sys
import uuid
import zlib
import zipfile
from pathlib import Path, PurePosixPath

from audit_johto import ROOT, checksum
from build_johto_events import EVENT_CLASSES, event_page, ruby
from build_johto_elm_lab_v1 import table_values
from build_johto_bedroom_v1 import tile
from compile_johto_connections import merge_pbs
from install_johto import save_report
from package_johto_offline12 import MAP_IDS, RIVAL_PBS, STAGE_PBS, RUNTIME, expected_events
from pilot import SYSTEM_CLASSES
from server.ruby_marshal import RubyObject, loads, text
from stage import serialize

sys.path.insert(0, str(ROOT / "scripts/official_rules"))
from prepare_restore import Marshal, RubyString, dump

TARGET = "game-johto-qa"
MARKER = "johto-qa-transaction.json"
SAVE_ORG = "Dessastre Paradoxal Johto QA"
DATA = {f"Data/Map{i:03}.rxdata" for i in MAP_IDS} | {
    "Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
}
PBS = {f"PBS/{name}" for name in (*RIVAL_PBS, *STAGE_PBS)}
ORIGINAL_BUNDLE_SHA256 = "74e727875803f70b3c0598b6b88fe5d79717df849ba1b888fae0583c09202a49"
ORIGINAL_BUNDLE_PREFIX = "Johto_Offline_Fase12/"
CONNECTIONS = "PBS/map_connections_johto_offline12.txt"
TRAINER_SPRITES = {
    "BLUE_JOHTO_RIVAL": "RIVAL1",
    "BLUE_JOHTO_FALKNER": "JOHTOIAN_HGSS_FALKNER",
    "BLUE_JOHTO_ELDER": "JOHTOIAN_HGSS_ELDER",
    "BLUE_JOHTO_SAGE": "JOHTOIAN_HGSS_SAGE",
}
GRAPHIC = re.compile(r"Graphics/(?:Tilesets|Autotiles|Characters)/[A-Za-z0-9_ ()-]{1,90}\.png")
PNG = b"\x89PNG\r\n\x1a\n"
MAP = re.compile(r"Map(\d+)\.rxdata", re.I)
SAVE = re.compile(r"(?:File [A-H]|Auto [1-3]|Game|Save[0-9]*)\.rxdata(?:\.bak)?", re.I)
PLUGIN = "Plugins/ZZZZZ Blue Johto QA"
STORY = "Plugins/ZZZZ Blue Story and Presentation"
COPY_DIRS = ("Audio", "Data", "Fonts", "Graphics", "PBS", "Plugins", "Scripts")
SOURCE_FILES = {"Game.exe", "Game.ini", "mkxp.json", "preload.rb", "soundfont.sf2", "Credits.txt"}
BASE_BLUE_DATA = {
    "blue-campaign-reference.dat", "blue-hub-presets.dat", "blue-pt-br.dat",
    "blue-kanto-install.json", "blue-kanto-music.txt", "blue-kanto-start.txt",
    "blue-music.json", "blue-music.rxdata", "blue-music-categories.rxdata",
    "blue-music-playlists.json", "blue-shared-music.sha256",
}


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(path: Path) -> Path:
    # Resolve only after checking every ancestor; Windows junctions aren't symlinks.
    path = path.absolute()
    if ".." in path.parts:
        raise ValueError("Não use '..' nos caminhos")
    for parent in (path, *path.parents):
        try:
            st = parent.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(st.st_mode) or getattr(st, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"Link ou junction recusado: {parent}")
    return path


def regular(path: Path) -> Path:
    safe_path(path)
    if not path.is_file():
        raise ValueError(f"Arquivo obrigatório ausente: {path}")
    return path


def archive_payload(bundle: Path, pinned: str) -> tuple[dict[str, bytes], dict, str]:
    bundle_hash = checksum(regular(bundle))
    original = bundle_hash == ORIGINAL_BUNDLE_SHA256
    prefix = ORIGINAL_BUNDLE_PREFIX if original else "stage/"
    audit_path = (prefix if original else "") + "johto-offline12-audit.json"
    files = {}
    with zipfile.ZipFile(bundle) as archive:
        members = archive.infolist()
        if len(members) > 350 or sum(x.file_size for x in members) > 96_000_000:
            raise ValueError("Pacote Johto excede o limite de tamanho")
        seen = set()
        for item in members:
            name = item.filename
            parts = PurePosixPath(name).parts
            if (not parts or PurePosixPath(name).as_posix() != name.rstrip("/")
                    or name.startswith("/") or "\\" in name or ":" in name
                    or any(x in (".", "..") for x in parts)
                    or name.casefold().rstrip("/") in seen
                    or item.file_size > 16_000_000
                    or stat.S_ISLNK(item.external_attr >> 16)):
                raise ValueError(f"Entrada ZIP insegura: {name}")
            seen.add(name.casefold().rstrip("/"))
            if item.is_dir():
                if name.rstrip("/") not in {
                    "stage", "stage/Data", "stage/Graphics", "stage/Graphics/Characters",
                    "stage/Graphics/Autotiles", "stage/Graphics/Tilesets", "stage/PBS",
                    "review_only", "review_only/Ruby",
                }:
                    raise ValueError(f"Pasta inesperada no ZIP: {name}")
                continue
            rel = name.removeprefix(prefix)
            if name.startswith(prefix) and (
                    rel in DATA | PBS | {CONNECTIONS, "johto-stage.json"} or GRAPHIC.fullmatch(rel)):
                files[rel] = archive.read(item)
            elif name == audit_path:
                files["johto-offline12-audit.json"] = archive.read(item)
            elif original and name.startswith(prefix) and (
                    re.fullmatch(r"johto-[a-z0-9_-]+\.json", rel)
                    or rel in {"LEIA-ME.txt", "LEIA_ME_FASE10.txt", "LEIA_ME_FASE11.txt",
                               "NAO_INSTALAR_NA_PASTA_GAME.txt"}):
                continue
            elif name in {"OFFLINE_ONLY_NOT_INSTALLABLE.txt", *(
                f"review_only/Ruby/{n}" for n in RUNTIME
            )} or re.fullmatch(r"stage/johto-[a-z0-9_-]+\.json", name):
                continue  # Review scripts and stage notes are never copied.
            else:
                raise ValueError(f"Arquivo inesperado no pacote: {name}")
    missing = DATA | PBS | {CONNECTIONS, "johto-stage.json", "johto-offline12-audit.json"}
    if not missing.issubset(files) or any(not blob for blob in files.values()):
        raise ValueError("Pacote OFFLINE 12 incompleto ou com arquivo vazio")
    stage = json.loads(files.pop("johto-stage.json"))
    audit = json.loads(files.pop("johto-offline12-audit.json"))
    if (stage.get("status") != "BLUE_OFFLINE12_PREVIEW_ONLY_NOT_INSTALLABLE"
            or stage.get("can_install") is not False or stage.get("not_playable") is not True
            or audit.get("stage" if original else "milestone") != "OFFLINE_12_OF_12"
            or audit.get("gameplay_playable") is not False or audit.get("can_install") is not False
            or not isinstance(pinned, str) or not re.fullmatch("[a-f0-9]{64}", pinned)
            or stage.get("source_archive_sha256") != pinned
            or not original and audit.get("source_archive_sha256") != pinned):
        raise ValueError("Pacote não corresponde à prévia OFFLINE 12 e à fonte Johto fixada")
    if original:
        # The original private export uses a separate layout. Its audited whole
        # archive digest is required before trusting the legacy file inventory.
        hashes = audit["included_file_hashes"]
        payload = DATA | PBS | {CONNECTIONS} | {name for name in files if GRAPHIC.fullmatch(name)}
        if not payload.issubset(hashes) or any(hash_bytes(files[name]) != hashes[name] for name in payload):
            raise ValueError("Arquivos do ZIP original divergem da auditoria")
        return files, stage, bundle_hash

    hashes = {f"Data/Map{i:03}.rxdata": audit["packaged_map_sha256"].get(str(i)) for i in MAP_IDS}
    hashes.update({f"PBS/{name}": sha for name, sha in audit["pbs"]["sha256"].items()})
    hashes.update({f"Data/{name}.rxdata": audit[key] for name, key in (
        ("MapInfos", "stage11_mapinfos_sha256"), ("Tilesets", "stage11_tilesets_sha256")
    )})
    if set(hashes) != DATA | PBS or any(hash_bytes(files[k]) != v for k, v in hashes.items()):
        raise ValueError("Mapas, metadados ou PBS divergem dos hashes da auditoria offline")
    return files, stage, bundle_hash


def index_base(base: Path) -> dict[str, str]:
    for name in ("Game.exe", "Game.ini", "mkxp.json", "Data/MapInfos.rxdata",
                 "Data/Tilesets.rxdata", "Data/System.rxdata", "Data/Scripts.rxdata",
                 f"{STORY}/RegionStart.rb", f"{STORY}/meta.txt"):
        regular(base / name)
    for name in ("Audio", "Data", "Fonts", "Graphics", "PBS", "Plugins"):
        if not safe_path(base / name).is_dir():
            raise ValueError(f"Pasta do jogo ausente: {name}")
    if any(safe_path(base / name).exists() for name in (
            "Kanto pilot.json", "Johto pilot.json", MARKER, PLUGIN,
            "Data/blue-johto-start.txt", "Data/blue-johto-install.json")):
        raise ValueError("Use uma base Decades, não outro piloto ou uma Johto instalada")
    files = {}
    seen = set()
    for current, dirs, names in os.walk(base):
        directory = Path(current)
        if directory == base:
            dirs[:] = [name for name in dirs if name in COPY_DIRS]
            names = [name for name in names if name in SOURCE_FILES or name.lower().endswith(".dll")]
        else:
            dirs[:] = [name for name in dirs if name.casefold() not in ("saves", "backups", "backup")]
        for name in sorted(dirs):
            safe_path(directory / name)
        for name in sorted(names):
            if (SAVE.fullmatch(name) or name.lower().endswith((".bak", ".log", ".tmp"))
                    or name.lower().startswith("blue-")
                    and not (directory == base / "Data" and name in BASE_BLUE_DATA)):
                continue
            file = directory / name
            if not file.is_file():
                raise ValueError(f"Entrada do jogo não é arquivo: {file}")
            st = file.lstat()
            if (stat.S_ISLNK(st.st_mode) or getattr(st, "st_file_attributes", 0) & 0x400):
                raise ValueError(f"Link no jogo: {file}")
            rel = file.relative_to(base).as_posix()
            key = rel.casefold()
            if key in seen:
                raise ValueError(f"Colisão por maiúsculas/minúsculas: {rel}")
            seen.add(key)
            files[rel] = checksum(file)
    return files


def validate_maps(files: dict, stage: dict, base: Path, root: Path) -> tuple[list[int], set]:
    rows = stage.get("maps", [])
    ids = {row["symbol"]: row["destination_id"] for row in rows}
    if (len(rows) != len(ids) or set(ids.values()) != MAP_IDS or len(ids) != 82
            or any(row.get("events_imported") != 0 for row in rows)):
        raise ValueError("MapIDs da prévia não correspondem a 600–681")
    native_infos = loads((base / "Data/MapInfos.rxdata").read_bytes())
    native_tiles = loads((base / "Data/Tilesets.rxdata").read_bytes())
    infos = loads(files["Data/MapInfos.rxdata"])
    tiles = loads(files["Data/Tilesets.rxdata"])
    if not (isinstance(infos, dict) and isinstance(native_infos, dict)
            and isinstance(tiles, list) and isinstance(native_tiles, list)):
        raise ValueError("MapInfos ou Tilesets inválidos")
    disk = {int(m[1]) for p in (base / "Data").iterdir() if (m := MAP.fullmatch(p.name))}
    if (set(native_infos) | disk) & MAP_IDS:
        raise ValueError("MapIDs Johto colidem com mapas ou registros da base")
    if (checksum(base / "Data/MapInfos.rxdata") != stage.get("native_mapinfos_sha256")
            or checksum(base / "Data/Tilesets.rxdata") != stage.get("native_tilesets_sha256")
            or set(infos) != set(native_infos) | MAP_IDS
            or any(infos[key] != val for key, val in native_infos.items())
            or tiles[:len(native_tiles)] != native_tiles):
        raise ValueError("Prévia construída sobre outra base: MapInfos/Tilesets de Decades/Kanto divergentes")

    actions, warps = expected_events(root)
    maps = {mid: loads(files[f"Data/Map{mid:03}.rxdata"]) for mid in MAP_IDS}
    references, seen = set(), set()
    for mid, obj in maps.items():
        if not isinstance(obj, RubyObject) or obj.name != "RPG::Map":
            raise ValueError(f"Map{mid}: objeto RMXP inválido")
        a = obj.attrs
        tid = a["@tileset_id"]
        if (type(tid) is not int or not 0 < tid < len(tiles)
                or a.get("@autoplay_bgm") or a.get("@autoplay_bgs")
                or any(isinstance(a.get(key), RubyObject) and a[key].attrs.get("@name")
                       for key in ("@bgm", "@bgs"))):
            raise ValueError(f"Map{mid}: tileset ou áudio inesperado")
        tile = tiles[tid].attrs
        for name, folder in (
            (tile["@tileset_name"], "Tilesets"),
            *((name, "Autotiles") for name in tile["@autotile_names"])
        ):
            if name:
                references.add(f"Graphics/{folder}/{text(name)}.png")
        for event in a["@events"].values():
            e = event.attrs
            name = text(e["@name"])
            if name in seen or name not in actions.keys() | warps.keys() or len(e["@pages"]) != 1:
                raise ValueError(f"Map{mid}: evento extra/repetido: {name}")
            seen.add(name)
            sym, xy, *detail = (actions if name in actions else warps)[name]
            x, y = xy
            if ids[sym] != mid or (e["@x"], e["@y"]) != xy or not (
                    0 <= x < a["@width"] and 0 <= y < a["@height"]):
                raise ValueError(f"Map{mid}: posição incorreta de {name}")
            page = e["@pages"][0]
            sprite = text(page.attrs["@graphic"].attrs["@character_name"])
            if sprite:
                references.add(f"Graphics/Characters/{sprite}.png")
            if name in actions:
                expected = event_page(script=detail[0], sprite=sprite)
            else:
                dest, (dx, dy), _ = detail
                target = maps[ids[dest]].attrs
                if not (0 <= dx < target["@width"] and 0 <= dy < target["@height"]):
                    raise ValueError(f"Map{mid}: destino de {name} fora dos limites")
                expected = event_page(warp=(ids[dest], dx, dy), touch=True)
            if any(page.attrs.get(k) != expected.attrs[k] for k in (
                    "@list", "@condition", "@move_type", "@move_route", "@trigger")):
                raise ValueError(f"Map{mid}: script, transferência ou condição fora do contrato: {name}")
    if seen != actions.keys() | warps.keys():
        raise ValueError("Eventos de Johto incompletos")
    for rel in references:
        if not GRAPHIC.fullmatch(rel):
            raise ValueError(f"Referência gráfica inválida: {rel}")
    spawn = json.loads((root / "data/regions/johto-stage07-warps.json").read_text("utf-8"))["spawn"]
    mid, x, y = ids[spawn["symbol"]], spawn["x"], spawn["y"]
    home = maps[mid].attrs
    if (not 0 <= x < home["@width"] or not 0 <= y < home["@height"]
            or any((ev.attrs["@x"], ev.attrs["@y"]) == (x, y) for ev in home["@events"].values())):
        raise ValueError("Ponto inicial inválido no quarto de New Bark")
    return [mid, x, y], references


def pbs_headers(blob: bytes, prefix: str, *, strict: bool = False) -> set:
    result = set()
    for line in blob.decode("utf-8-sig").splitlines():
        header = re.fullmatch(r"\s*\[([^\]]+)\]\s*(?:#.*)?", line)
        if not header:
            continue
        fields = [x.strip() for x in header[1].split(",")]
        if prefix == "trainers" and len(fields) in (2, 3):
            key = (fields[0].upper(), fields[1], int(fields[2]) if len(fields) == 3 else 0)
        elif prefix == "encounters" and fields[0].isdecimal():
            key = int(fields[0])
        else:
            key = header[1].strip().upper()
        if strict and key in result:
            raise ValueError(f"Seção PBS Johto duplicada: {key}")
        result.add(key)
    return result


def validate_pbs(base: Path, files: dict, native: dict) -> bytes:
    groups = {}
    for prefix in ("trainer_types", "trainers", "encounters"):
        pattern = re.compile(rf"PBS/{prefix}(?:_.*)?\.txt", re.I)
        old = set().union(*(pbs_headers((base / rel).read_bytes(), prefix)
                            for rel in native if pattern.fullmatch(rel)))
        added = set()
        for rel, blob in files.items():
            if pattern.fullmatch(rel):
                headers = pbs_headers(blob, prefix, strict=True)
                if headers & (old | added):
                    raise ValueError(f"Colisão PBS em {rel}: {headers & (old | added)}")
                added.update(headers)
        groups[prefix] = (old, added)
    old, new = groups["trainer_types"]
    trainers = groups["trainers"][1]
    if (new != TRAINER_SPRITES.keys() or len(trainers) != 21
            or any(not isinstance(k, tuple) or k[0] not in old | new for k in trainers)
            or groups["encounters"][1] != {625, 626, 627}):
        raise ValueError("Tipos, equipes ou encontros de Johto incompletos ou sem cadastro")
    paths = [rel for rel in native if re.fullmatch(r"PBS/map_connections(?:_.*)?\.txt", rel, re.I)]
    for rel in paths:
        for line in (base / rel).read_text("utf-8-sig").splitlines():
            bits = line.split("#", 1)[0].strip().split(",")
            if len(bits) == 6 and any(bits[i].strip().isdigit() and
                                     int(bits[i]) in MAP_IDS for i in (0, 3)):
                raise ValueError(f"Colisão de conexão nativa em {rel}: {line}")
    rows = [line.strip() for line in files.pop(CONNECTIONS).decode("utf-8-sig").splitlines()
            if line.strip()]
    edges = set()
    for row in rows:
        a, ad, ax, b, bd, bx = row.split(",")
        if (int(a) not in MAP_IDS or int(b) not in MAP_IDS or int(a) == int(b)
                or (a, ad, ax, b, bd, bx) in edges or (b, bd, bx, a, ad, ax) in edges):
            raise ValueError(f"Conexão inválida ou duplicada: {row}")
        edges.add((a, ad, ax, b, bd, bx))
    if len(edges) != 44 or not {"600,West,13,625,East,0", "601,East,12,625,West,0",
                                "602,East,6,627,West,0"}.issubset(rows):
        raise ValueError("Conexões New Bark–Violet incompletas")
    path = "PBS/map_connections.txt"
    return merge_pbs((base / path).read_bytes() if path in native else None, "\n".join(rows))


def json_bytes(data) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def native_compile_boot(blob: bytes) -> bytes:
    rows = Marshal(blob).read()
    matches = [row for row in rows if row[1] == b"Main"]
    if len(matches) != 1:
        raise ValueError("Bootstrap nativo Main ausente ou duplicado")
    row = matches[0]
    source = zlib.decompress(row[2]).decode("utf-8")
    before, compiler = "    PluginManager.runPlugins", "    Compiler.main"
    if source.count(before) != 1 or source.count(compiler) != 1 or source.index(before) > source.index(compiler):
        raise ValueError("Bootstrap nativo não corresponde ao Essentials esperado")
    hook = """    if File.file?('Johto pilot.json') && File.file?('Data/blue-johto-qa-compile-request.txt')
      $blue_johto_qa_compile = true
      $DEBUG = true
      %w[PluginScripts.rxdata trainers.dat].each do |name|
        path = "Data/#{name}"
        File.delete(path) if File.file?(path)
      end
      Object.send(:define_method, :pbPrintException) do |error|
        File.write('Data/blue-johto-qa-compile-error.txt', error.full_message)
        exit! 1
      end
    end
"""
    verify = """    if $blue_johto_qa_compile
      begin
        GameData::Trainer.load
        GameData::Encounter.load
        silver = (0..2).all? { |v| GameData::Trainer.exists?(:BLUE_JOHTO_RIVAL, "Rival", v) }
        raise 'Johto QA: Silver PBS ausente' unless silver
        falkner = (0..1).all? { |v| GameData::Trainer.exists?(:BLUE_JOHTO_FALKNER, "Falkner", v) }
        raise 'Johto QA: Falkner PBS ausente' unless falkner
        raise 'Johto QA: rotas sem encontros' unless (625..627).all? { |id| GameData::Encounter.exists?(id, 0) }
        routes = [[:YOUNGSTER, "Johto Mikey"], [:YOUNGSTER, "Johto Joey"],
                  [:BUGCATCHER, "Johto Don"], [:BUGCATCHER, "Johto Wade"],
                  [:YOUNGSTER, "Johto Ian"]]
        tower = [[:BLUE_JOHTO_SAGE, "Nico"], [:BLUE_JOHTO_SAGE, "Troy"], [:BLUE_JOHTO_ELDER, "Li"]]
        unless (routes + tower).all? { |type, name| (0..1).all? { |v| GameData::Trainer.exists?(type, name, v) } }
          raise 'Johto QA: equipes de rota ou Torre Sprout ausentes'
        end
        # These markers activate trainer battles only inside this compiled QA copy.
        if File.file?("Johto pilot.json") && File.file?("Data/blue-johto-qa-start.txt")
          File.write("Data/blue-johto-rival-ready.txt", "BLUE_JOHTO_RIVAL_V1_READY")
          File.write("Data/blue-johto-routes-ready.txt", "BLUE_JOHTO_ROUTES10_TESTED_READY")
          File.write("Data/blue-johto-violet-ready.txt", "BLUE_JOHTO_VIOLET_V1_READY")
        end
        File.write('Data/blue-johto-qa-compiled.txt', File.read('Data/blue-johto-qa-compile-request.txt'))
        File.delete('Data/blue-johto-qa-compile-request.txt')
      rescue StandardError => error
        pbPrintException(error)
      end
      exit
    end
"""
    source = source.replace(before, hook + before).replace(compiler, compiler + "\n" + verify)
    row[2] = RubyString(zlib.compress(source.encode("utf-8")))
    return b"\x04\x08" + dump(rows)


def repair_new_bark(town, bedroom, home, lab):
    # Retain the existing room footprints and warps while using a continuous
    # wood wall face in place of the repeated corner tile.
    for room in (bedroom, home):
        data = room.attrs["@data"]
        (w, h, _), original = table_values(data.data, 3)
        cells = list(original)
        for x in range(1, w - 1):
            cells[x + w * (1 + h)] = tile(191, 4)
            cells[x + w * (h - 1)] = tile(192, 4)
        data.data = data.data[:20] + struct.pack(f"<{len(cells)}H", *cells)
    events = town.attrs["@events"]
    events = {id: event for id, event in events.items() if event.attrs["@name"] != b"JH_ROUTE29_GUARD"}
    town.attrs["@events"] = events
    for event_id in (1, 2):
        events[event_id].attrs["@pages"][0].attrs["@graphic"].attrs["@character_name"] = b"doors2"
    # The Route 29 connection uses the west edge at y=26–28.
    for y in range(26, 29):
        event_id = max(events) + 1
        events[event_id] = ruby("RPG::Event", id=event_id, name=b"JH_ROUTE29_GUARD", x=0, y=y,
                                pages=[event_page(script="BlueJohtoPilot.guard_route", touch=True)])
    events = {id: event for id, event in bedroom.attrs["@events"].items()
              if event.attrs["@name"] != b"JH_NEW_GAME_PROFILE"}
    bedroom.attrs["@events"] = events
    event_id = max(events) + 1
    page = event_page(script="BlueJohtoPilot.choose_profile", touch=True)
    page.attrs["@trigger"] = 3
    page.attrs["@list"].insert(1, ruby("RPG::EventCommand", code=123, indent=0, parameters=[b"A", 0]))
    done = event_page(script="nil", touch=True)
    done.attrs["@trigger"] = 0
    done.attrs["@condition"].attrs["@self_switch_valid"] = True
    events[event_id] = ruby("RPG::Event", id=event_id, name=b"JH_NEW_GAME_PROFILE", x=6, y=7,
                            pages=[page, done])
    for event in lab.attrs["@events"].values():
        if text(event.attrs["@name"]).startswith("JH_STARTER_"):
            event.attrs["@y"] = 6
            event.attrs["@pages"][0].attrs["@always_on_top"] = True


def plan(base: Path, bundle: Path, root: Path, report: dict) -> tuple[dict, dict]:
    pinned = json.loads((root / "data/regions/johto-source.json").read_text("utf-8"))["source"]["archive_sha256"]
    native = index_base(base)
    report["base_files"] = len(native)
    report["base_tree_sha256"] = hash_bytes(json_bytes(dict(sorted(native.items()))))
    report["base_data"] = {name: native[f"Data/{name}.rxdata"] for name in ("MapInfos", "Tilesets", "System", "Scripts")}
    files, stage, bundle_hash = archive_payload(bundle, pinned)
    start, references = validate_maps(files, stage, base, root)
    files["PBS/map_connections.txt"] = validate_pbs(base, files, native)
    only_changes = {"Data/MapInfos.rxdata", "Data/Tilesets.rxdata", "PBS/map_connections.txt"}
    native_names = {name.casefold(): name for name in native}
    for rel in list(files):
        old = native_names.get(rel.casefold())
        if GRAPHIC.fullmatch(rel):
            if rel not in references:
                del files[rel]
                continue
            if not files[rel].startswith(PNG):
                raise ValueError(f"Gráfico da prévia inválido: {rel}")
            if old and native[old] == hash_bytes(files[rel]) and old == rel:
                del files[rel]
                continue
        if old and (old != rel or rel not in only_changes):
            raise ValueError(f"Colisão de arquivo entre a base e a prévia: {rel}")
    for rel in references - files.keys():
        if rel not in native or not regular(base / rel).read_bytes().startswith(PNG):
            raise ValueError(f"Gráfico de mapa/evento ausente: {rel}")
    for trainer, sprite in TRAINER_SPRITES.items():
        rel = f"Graphics/Trainers/{trainer}.png"
        source = f"Graphics/Trainers/{sprite}.png"
        if rel.casefold() in native_names or source not in native:
            raise ValueError(f"Colisão ou sprite de batalha nativo ausente: {source}")
        files[rel] = regular(base / source).read_bytes()
        if not files[rel].startswith(PNG):
            raise ValueError(f"Sprite de batalha inválido: {source}")

    # Apply authored QA repairs only after validation of the pinned bundle.
    repair_count = 0
    if "Graphics/Characters/doors2.png" in native:
        paths = [f"Data/Map{mid:03}.rxdata" for mid in (600, start[0], 675, 676)]
        maps = [loads(files[path]) for path in paths]
        repair_new_bark(*maps)
        repair_count = 4
        files.update({path: serialize(data, EVENT_CLASSES) for path, data in zip(paths, maps)})
    for rel, source in ((f"{STORY}/Economy.rb", "scripts/battle_polish/Economy.rb"),
                        ("Plugins/ZZZZ Blue Music/BlueMusic.rb", "scripts/music/BlueMusic.rb")):
        if rel in native:
            files[rel] = regular(root / source).read_bytes()

    app = f"Johto QA {uuid.uuid4().hex[:12]}"
    config_text = (base / "mkxp.json").read_text("utf-8-sig")
    # mkxp accepts JSON comments and trailing commas. Match string literals
    # first so URLs and punctuation inside strings are preserved.
    config_text = re.sub(r'"(?:[^"\\]|\\.)*"|//[^\r\n]*',
                         lambda match: "" if match[0].startswith("//") else match[0], config_text)
    config_text = re.sub(r'"(?:[^"\\]|\\.)*"|,(?=\s*[}\]])',
                         lambda match: "" if match[0] == "," else match[0], config_text)
    config = json.loads(config_text)
    config.update(dataPathApp=app, dataPathOrg=SAVE_ORG, windowTitle="Pokémon Blue — Johto QA")
    files["mkxp.json"] = json_bytes(config)
    ini, count = re.subn(r"(?m)^Title=[^\r\n]*", f"Title={app}", (base / "Game.ini").read_text("utf-8-sig"))
    if count != 1:
        raise ValueError("Game.ini da base precisa de um único Title=")
    files["Game.ini"] = ini.encode("utf-8")
    system = loads((base / "Data/System.rxdata").read_bytes())
    if not isinstance(system, RubyObject) or system.name != "RPG::System":
        raise ValueError("System.rxdata nativo inválido")
    system.attrs.update(dict(zip(("@start_map_id", "@start_x", "@start_y"), start)))
    files["Data/System.rxdata"] = serialize(system, SYSTEM_CLASSES)
    files["Data/Scripts.rxdata"] = native_compile_boot((base / "Data/Scripts.rxdata").read_bytes())
    files["Data/blue-johto-qa-compile-request.txt"] = (bundle_hash + "\n").encode("ascii")
    start_crc = zlib.crc32(files[f"Data/Map{start[0]:03}.rxdata"])
    files["Data/blue-johto-qa-start.txt"] = (
        "BLUE_JOHTO_QA_START_V2," + ",".join(map(str, [*start, start_crc])) + "\n"
    ).encode("ascii")
    runtime = (*RUNTIME, "JohtoPilotStart.rb")
    files[f"{PLUGIN}/Boot.rb"] = b"\n".join(regular(root / "scripts/regions" / name).read_bytes()
                                             for name in runtime)
    files[f"{PLUGIN}/meta.txt"] = (
        b"Name = Blue Johto QA\nVersion = 0.1\nEssentials = 21.1\n"
        b"Requires = Blue Battle Presentation and Story\nScripts = Boot.rb\n"
    )
    files["Johto pilot.json"] = json_bytes({
        "kind": "ISOLATED_JOHTO_TEST", "archive_sha256": pinned, "save_app": app, "save_org": SAVE_ORG,
    })
    files["Data/blue-johto-pilot-proof.json"] = json_bytes({
        "schema": 1, "region": "JOHTO", "status": "EXPERIMENTAL_UNTESTED",
        "can_install": False, "archive_sha256": pinned, "start": start,
        "file_hashes": {name: hash_bytes(files[name]) for name in sorted(DATA | PBS | {"Data/System.rxdata"})},
    })
    report.update(status="QA_COPY_PLANNED", bundle_sha256=bundle_hash, maps=82,
                  events=32 + repair_count, connections=44, trainer_teams=21, start=start)
    return native, files


def publish_copy(work: Path, base: Path, native: dict, overlay: dict, report: dict) -> None:
    target = work / TARGET
    if target.exists() or target.is_symlink():
        raise ValueError(f"Já existe {TARGET}; use --rollback para arquivá-lo antes de montar outro")
    work.mkdir(parents=True, exist_ok=True)
    transaction = uuid.uuid4().hex
    tmp = work / f".johto-qa-pending-{transaction}"
    tmp.mkdir()
    backup = tmp / "_johto_backup"
    backup.mkdir()
    try:
        for name, expected in native.items():
            path = tmp / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(regular(base / name), path)
            if checksum(path) != expected:
                raise ValueError(f"A base mudou durante a cópia: {name}")
        before = {}
        for name, blob in overlay.items():
            path = tmp / name
            if name in native:
                old = backup / name
                old.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, old)
                if checksum(old) != native[name]:
                    raise ValueError(f"Falha ao verificar backup de {name}")
                before[name] = native[name]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)
            if checksum(path) != hash_bytes(blob):
                raise ValueError(f"Falha ao verificar escrita de {name}")
        after = {name: hash_bytes(blob) for name, blob in overlay.items()}
        (tmp / MARKER).write_bytes(json_bytes({
            "schema": 1, "kind": "BLUE_JOHTO_QA_TRANSACTION", "id": transaction,
            "bundle_sha256": report["bundle_sha256"], "native_files": native,
            "backups": before, "overlay_sha256": after, "native_pbs_compiled": False,
        }))
        # Same-filesystem publication under the QA lock; never expose a partial copy.
        if target.exists() or target.is_symlink():
            raise ValueError("Destino do piloto criado durante a transação")
        tmp.rename(target)
    except BaseException:
        shutil.rmtree(tmp)
        raise
    report.update(status="QA_COPY_STAGED_UNTESTED", target=str(target), backups=len(before))


def rollback(work: Path) -> Path:
    target = work / TARGET
    marker = json.loads(regular(target / MARKER).read_text("utf-8"))
    transaction = marker.get("id", "")
    if (marker.get("kind") != "BLUE_JOHTO_QA_TRANSACTION" or marker.get("schema") != 1
            or not re.fullmatch("[a-f0-9]{32}", transaction)):
        raise ValueError("Cópia não foi criada pelo instalador de QA")
    retired = work / f"johto-qa-archived-{transaction}"
    if retired.exists() or retired.is_symlink():
        raise ValueError("Já existe um arquivo de reversão para esta cópia")
    # Preserve the entire QA copy, including any local findings, rather than deleting files.
    target.rename(retired)
    return retired


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, default=ROOT / "game")
    parser.add_argument("--bundle", type=Path, default=ROOT / ".blue-work/johto-offline12-preview.zip")
    parser.add_argument("--report", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Valida sem criar cópia (padrão)")
    mode.add_argument("--stage-qa", action="store_true")
    mode.add_argument("--rollback", action="store_true")
    args = parser.parse_args(argv)
    report = {"region": "JOHTO", "status": "BLOCKED", "native_pbs_compiled": False,
              "gameplay_verified": False, "ready_markers_created": False, "base_modified": False}
    try:
        work = safe_path(ROOT / ".blue-work")
        if args.stage_qa or args.rollback:
            work.mkdir(parents=True, exist_ok=True)
            lock = work / ".johto-qa.lock"
            with lock.open("x"):
                pass
            try:
                if args.rollback:
                    report.update(status="QA_COPY_ARCHIVED", archived=str(rollback(work)))
                else:
                    base = safe_path(args.game)
                    if base == work or work.is_relative_to(base) or base.is_relative_to(work / TARGET):
                        raise ValueError("A base não pode conter o workspace nem ser o destino de QA")
                    if (work / TARGET).exists() or (work / TARGET).is_symlink():
                        raise ValueError(f"Já existe {TARGET}; use --rollback antes de montar outro")
                    native, overlay = plan(base, args.bundle, ROOT, report)
                    publish_copy(work, base, native, overlay, report)
            finally:
                lock.unlink()
        else:
            plan(safe_path(args.game), args.bundle, ROOT, report)
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError,
            zlib.error, zipfile.BadZipFile) as exc:
        report.update(status="BLOCKED", reason=str(exc))
    print(json.dumps(report, ensure_ascii=True, indent=2))
    if args.report:
        try:
            save_report(report, safe_path(args.report), ROOT)
        except (OSError, ValueError) as exc:
            print(f"Relatório não gravado: {exc}", file=sys.stderr)
            return 2
    return 2 if report["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
