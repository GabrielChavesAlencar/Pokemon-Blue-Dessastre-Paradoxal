#!/usr/bin/env python3
"""Unova A04 — read-only inventory of map IDs across private RMXP snapshots.

--base-data is the real installed Decades game/Data (or its parent game dir).
--overlay REGION=PATH provides an optional region-tagged private Data dir/ZIP.
Tags are USER-DECLARED, NOT verified region ownership or installer provenance.
Never executes Ruby, extracts ZIPs, edits MapInfos, allocates MapIDs or game saves.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from server.ruby_marshal import RubyObject, loads, text

REPORT_DIR = Path(".blue-work/unova/audit")
MAP_NAME = re.compile(r"map0*([1-9][0-9]*)\.rxdata\Z", re.I)
REGIONS = ("KANTO", "JOHTO", "HOENN", "SINNOH")
MAX_MAP_ID = 99999
MAX_MAPS = 7500
MAX_FILE_BYTES = 24 * 1024 * 1024
MAX_TOTAL_READ = 1024 * 1024 * 1024
MAX_ZIP_BYTES = 4 * 1024**3
MAX_ZIP_MEMBERS = 60000
MAX_ZIP_UNPACKED = 12 * 1024**3


def block(message: str) -> None:
    raise ValueError("UNOVA_A04_BLOQUEADO: " + message)


def safe_path(source: Path, *, file: bool = False) -> Path:
    """Refuse symlinks in any ancestor; explicit inputs only, no traversal."""
    target = Path(source).expanduser().absolute()
    for part in (target, *target.parents):
        if part.is_symlink():
            block("symlink no caminho da fonte")
    if file and not target.is_file():
        block("arquivo de fonte ausente")
    if not file and not target.is_dir():
        block("diretorio de fonte ausente")
    return target


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for part in iter(lambda: inp.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def valid_parts(value: str) -> tuple[str, ...]:
    if not value or value.startswith("/") or "\\" in value or "\x00" in value:
        block("ZIP com caminho absoluto/backslash")
    parts = tuple(value.rstrip("/").split("/"))
    if any(not p or p in (".", "..") or ":" in p
           or any(ord(ch) < 32 for ch in p) for p in parts):
        block("ZIP com travessia ou componente inseguro")
    return parts


def parse_infos(blob: bytes) -> dict[int, str]:
    if not 0 < len(blob) <= MAX_FILE_BYTES:
        block("MapInfos.rxdata vazio ou grande")
    try:
        root = loads(blob)
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, RecursionError) as exc:
        block("MapInfos.rxdata Ruby Marshal invalido: " + type(exc).__name__)
    if not isinstance(root, dict) or not 0 < len(root) <= MAX_MAPS:
        block("MapInfos nao e dicionario RMXP de mapas")
    output = {}
    for mid, obj in root.items():
        if type(mid) is not int or not 0 < mid <= MAX_MAP_ID:
            block("MapID inválido no MapInfos")
        if not isinstance(obj, RubyObject) or obj.name != "RPG::MapInfo":
            block("MapInfos contem objeto nao RPG::MapInfo")
        name = text(obj.attrs.get("@name", b"")).strip()
        if not name or len(name) > 200 or any(ord(ch) < 32 for ch in name):
            block("nome vazio ou invalido de mapa")
        output[mid] = name
    return output


def _map_id(basename: str) -> int | None:
    match = MAP_NAME.fullmatch(basename)
    if not match:
        return None
    mid = int(match.group(1))
    if not 0 < mid <= MAX_MAP_ID:
        block("MapID excedeu limite")
    return mid


def directory_root(path: Path) -> Path:
    path = safe_path(path)
    root = path / "Data"
    if root.exists():
        return safe_path(root)
    if path.name.casefold() == "data":
        return path
    block("selecione a pasta game, Data ou uma pasta overlay com subpasta Data")


def scan_dir(path: Path, label: str, *, base: bool = False) -> dict:
    root = directory_root(path)
    entries = {}
    keys = set()
    for file in root.iterdir():
        key = file.name.casefold()
        if key in keys:
            block("arquivos diferem apenas em caixa: " + file.name)
        keys.add(key)
        if file.is_symlink():
            block("Data contem link simbolico: " + file.name)
        if file.is_dir():
            continue
        if not file.is_file():
            block("Data contem entrada desconhecida")
        mid = _map_id(file.name)
        if mid is not None:
            if mid in entries:
                block("MapID repetido em um mesmo Data: " + str(mid))
            entries[mid] = file
    if not entries or len(entries) > MAX_MAPS:
        block("Data sem MapNNN.rxdata ou mapas demais")
    infos_path = next((p for p in root.iterdir()
                       if p.name.casefold() == "mapinfos.rxdata"), None)
    if base and infos_path is None:
        block("Data do Decades principal sem MapInfos.rxdata")
    infos = {}
    infos_hash = None
    if infos_path:
        if not infos_path.is_file() or infos_path.is_symlink():
            block("MapInfos nao e arquivo regular")
        blob = _bounded_file(infos_path)
        infos = parse_infos(blob)
        infos_hash = hashlib.sha256(blob).hexdigest()
    maps = []
    total = 0
    for mid, file in sorted(entries.items()):
        size = file.stat().st_size
        if not 0 < size <= MAX_FILE_BYTES:
            block("MapNNN.rxdata vazio/grande")
        total += size
        if total > MAX_TOTAL_READ:
            block("dados de mapas excedem limite de leitura")
        maps.append({"id": mid, "source_filename": file.name,
                     "bytes": size, "sha256": sha256_file(file),
                     "mapinfo_name": infos.get(mid)})
    return assemble(label, maps, infos, infos_hash, "DIRECTORY",
                    "Data", None)


def _bounded_file(file: Path) -> bytes:
    size = file.stat().st_size
    if not 0 < size <= MAX_FILE_BYTES:
        block("arquivo RXDATA acima do limite")
    blob = file.read_bytes()
    if len(blob) != size:
        block("arquivo RXDATA mudou durante a leitura")
    return blob


def scan_zip(source: Path, label: str, *, base: bool = False) -> dict:
    source = safe_path(source, file=True)
    if source.suffix.casefold() != ".zip" or not 0 < source.stat().st_size <= MAX_ZIP_BYTES:
        block("fonte deve ser ZIP seguro de tamanho permitido")
    with zipfile.ZipFile(source) as z:
        entries = z.infolist()
        if len(entries) > MAX_ZIP_MEMBERS:
            block("ZIP possui entradas demais")
        seen = set()
        roots = defaultdict(dict)
        total = 0
        for entry in entries:
            parts = valid_parts(entry.filename)
            path_key = "/".join(parts).casefold()
            if path_key in seen:
                block("ZIP contem caminho duplicado, inclusive caixa")
            seen.add(path_key)
            if stat.S_IFMT(entry.external_attr >> 16) == stat.S_IFLNK:
                block("ZIP contem symlink")
            if entry.flag_bits & 1:
                block("ZIP contem membro criptografado")
            total += entry.file_size
            if total > MAX_ZIP_UNPACKED:
                block("ZIP ultrapassa limite de tamanho descompactado")
            if (entry.file_size > 1024 * 1024 and
                entry.file_size / max(1, entry.compress_size) > 1000):
                block("ZIP suspeito de bomba de descompactacao")
            if entry.is_dir():
                continue
            if len(parts) < 2 or parts[-2].casefold() != "data":
                continue
            basename = parts[-1]
            mid = _map_id(basename)
            if basename.casefold() != "mapinfos.rxdata" and mid is None:
                continue
            wrapper = tuple(part.casefold() for part in parts[:-2])
            if len(wrapper) > 4:
                block("Data do ZIP em caminho profundo demais")
            group = roots[wrapper]
            key = "MapInfos" if basename.casefold() == "mapinfos.rxdata" else mid
            if key in group:
                block("MapID duplicado dentro do ZIP: " + str(key))
            group[key] = entry
        valid = [(key, value) for key, value in roots.items()
                 if any(type(k) is int for k in value)]
        if len(valid) != 1:
            block("esperado um unico Data com mapas dentro do ZIP")
        wrapper, members = valid[0]
        if base and "MapInfos" not in members:
            block("ZIP base Decades sem MapInfos.rxdata")
        infos, infos_hash = {}, None
        total_read = 0

        def read(info: zipfile.ZipInfo) -> bytes:
            nonlocal total_read
            if not 0 < info.file_size <= MAX_FILE_BYTES:
                block("membro RXDATA vazio/grande")
            if total_read + info.file_size > MAX_TOTAL_READ:
                block("limite de leitura RXDATA excedido")
            with z.open(info) as stream:
                blob = stream.read(MAX_FILE_BYTES + 1)
            if len(blob) != info.file_size:
                block("ZIP muda tamanho dos arquivos")
            total_read += len(blob)
            return blob

        if "MapInfos" in members:
            content = read(members["MapInfos"])
            infos = parse_infos(content)
            infos_hash = hashlib.sha256(content).hexdigest()
        maps = []
        for mid, item in sorted(((k,v) for k,v in members.items() if type(k) is int)):
            payload = read(item)
            maps.append({"id": mid, "source_filename": item.filename.split("/")[-1],
                         "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
                         "mapinfo_name": infos.get(mid)})
    return assemble(label, maps, infos, infos_hash, "ZIP",
                    "/".join(wrapper) + ("/Data" if wrapper else "Data"),
                    sha256_file(source))


def assemble(label: str, maps: list[dict], infos: dict[int,str],
             infos_hash: str|None, source_kind: str, data_root: str,
             archive_sha: str|None) -> dict:
    files = {m["id"] for m in maps}
    declared = set(infos)
    return {
        "label": label, "input_label_is_user_declared_not_proven": True,
        "source_kind": source_kind, "data_root_label": data_root,
        "archive_sha256": archive_sha,
        "mapinfos_present": infos_hash is not None,
        "mapinfos_sha256": infos_hash,
        "file_count": len(maps),
        "mapinfos_declared_count": len(infos) if infos_hash else None,
        "missing_map_file_ids": sorted(declared - files),
        "orphan_map_file_ids": sorted(files - declared) if infos_hash else None,
        "map_ids_occupied_or_declared": sorted(files|declared),
        "maps": maps,
        "map_payloads_parsed": False,
        "region_identity_verified": False,
        "native_game_exe_tested": False,
    }


def scan_source(path: Path, label: str, *, base: bool = False) -> dict:
    path = Path(path).expanduser().absolute()
    return scan_zip(path,label,base=base) if path.suffix.casefold()==".zip" else scan_dir(path,label,base=base)


def analyze(base: dict, overlays: dict[str,dict]) -> dict:
    if base.get("label")!="DECADES" or base.get("mapinfos_present") is not True:
        block("baseline Decades com MapInfos real e obrigatorio")
    if not base.get("maps"):
        block("Decades sem mapas")
    if any(k not in REGIONS for k in overlays):
        block("rótulo regional desconhecido")
    sources = {"DECADES":base,**{k:overlays[k] for k in REGIONS if k in overlays}}
    occupied = {}
    for label, entry in sources.items():
        for mid in entry["map_ids_occupied_or_declared"]:
            occupied.setdefault(mid, []).append(label)
    files = defaultdict(list)
    for label,entry in sources.items():
        for row in entry["maps"]:
            files[row["id"]].append((label,row["sha256"]))
    overlaps = []
    for mid, labels in sorted(occupied.items()):
        if len(labels) < 2:
            continue
        same_files = files.get(mid,[])
        hashes = {hashval for _,hashval in same_files}
        status = ("SAME_MAP_BYTES_MULTIPLE_SNAPSHOTS_REVIEW" if
                  len(same_files)==len(labels) and len(hashes)==1 else
                  "DIFFERENT_OR_UNBACKED_MAPID_OVERLAP_REVIEW")
        overlaps.append({"map_id":mid,"declared_by":sorted(labels),
                         "file_hash_count":len(hashes),
                         "classification":status,
                         "safe_to_allocate":False})
    missing = [x for x in REGIONS if x not in overlays]
    blockers = [
        "Region labels assigned by operator are not proof of ownership",
        "MapInfos and files show occupancy only, not free/reservable MapIDs",
        "Map event transfers, dynamic scripts and installer state are not yet checked",
        "Neither MapIDs nor Unova maps are assigned or installed",
    ]
    if missing:
        blockers.append("Missing region overlay snapshots: "+", ".join(missing))
    if overlaps:
        blockers.append("Overlapping MapIDs require manual attribution and remap review")
    if any(s["missing_map_file_ids"] for s in sources.values()):
        blockers.append("One or more MapInfos entries lack map files")
    if any(s["orphan_map_file_ids"] for s in sources.values()
           if s["orphan_map_file_ids"] is not None):
        blockers.append("One or more map files are missing from their MapInfos")
    result = {
        "schema":1,"region":"UNOVA","phase":"A04",
        "mode":"READ_ONLY_NATIVE_MAPID_OCCUPANCY_AUDIT",
        "status":("OVERLAPPING_MAPIDS_REQUIRE_REVIEW" if overlaps else
                  "PARTIAL_SNAPSHOTS_NO_FREE_MAPID_CERTIFICATION" if missing else
                  "SNAPSHOTS_SCANNED_OWNERSHIP_UNVERIFIED"),
        "base_decades_scanned":True,
        "region_overlay_snapshots_present":sorted(overlays),
        "region_overlay_snapshots_missing":missing,
        "sources":sources,
        "observed_or_declared_occupied_map_ids":sorted(occupied),
        "observed_or_declared_occupied_count":len(occupied),
        "overlaps":overlaps,
        "overlap_count":len(overlaps),
        "possible_unbacked_mapinfos_count":sum(len(s["missing_map_file_ids"])
                                               for s in sources.values()),
        "region_ownership_verified":False,
        "all_installed_overlays_proven_complete":False,
        "available_map_ids_certified":None,
        "unova_destination_mapids_allocated":False,
        "can_reserve_mapids":False,
        "can_install":False,
        "game_or_saves_modified":False,
        "game_exe_tested":False,"android_tested":False,
        "bar_a_completed":0,"bar_a_total":8,
        "blockers":blockers,
    }
    return result


def missing_base() -> dict:
    return {
        "schema":1,"region":"UNOVA","phase":"A04",
        "mode":"READ_ONLY_NATIVE_MAPID_OCCUPANCY_AUDIT",
        "status":"BLOCKED_NATIVE_DECADES_MAPINFOS_NOT_PROVIDED",
        "base_decades_scanned":False,
        "region_overlay_snapshots_missing":list(REGIONS),
        "observed_or_declared_occupied_map_ids":None,
        "available_map_ids_certified":None,
        "unova_destination_mapids_allocated":False,
        "can_reserve_mapids":False,
        "can_install":False,
        "game_or_saves_modified":False,
        "game_exe_tested":False,"android_tested":False,
        "bar_a_completed":0,"bar_a_total":8,
        "blockers":["Selecione a pasta real game/Data do Decades que contenha MapInfos.rxdata"],
    }


def write_private(project: Path, report: dict) -> Path:
    project=safe_path(project)
    folders=(project/".blue-work",project/".blue-work/unova",project/REPORT_DIR)
    for folder in folders:
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            block("pasta de relatorio insegura")
        folder.mkdir(exist_ok=True)
    # An immutable content-addressed report; different sources keep separate evidence.
    payload=json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True).encode("utf-8")+b"\n"
    fingerprint=hashlib.sha256(payload).hexdigest()[:16]
    output=project/REPORT_DIR/("a04-mapids-"+fingerprint+".json")
    if output.is_symlink():
        block("saida de relatorio por symlink")
    if output.exists():
        if output.read_bytes()!=payload:
            block("relatorio divergente, nao sobrescrever")
    else:
        with output.open("xb") as stream:
            stream.write(payload)
    return output


def overlay_args(values: list[str]) -> dict[str,Path]:
    found={}
    for arg in values:
        if "=" not in arg:
            block("--overlay deve ser REGIAO=PASTA_OU_ZIP")
        label,raw=arg.split("=",1)
        label=label.strip().upper()
        if label not in REGIONS or not raw.strip() or label in found:
            block("overlay regional invalido ou duplicado")
        found[label]=Path(raw.strip())
    return found


def choose_gui():
    """Optional Windows UI; never reads a directory without user selection."""
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("A04: auditoria segura",
            "Escolha a pasta Data ou game de sua instalação real do Decades.\n"
            "Os arquivos serão lidos somente para identificar ocupação.\n"
            "Nenhum MapID será alocado para Unova.", parent=root)
        base = filedialog.askdirectory(
            parent=root,title="Escolha game/Data ou game (Decades instalado)")
        if not base:
            root.destroy()
            return None
        overlays = []
        if messagebox.askyesno("Comparar outras regiões?",
            "Você possui snapshots separados de Kanto, Johto, Hoenn e Sinnoh "
            "para comparar? É opcional e não prova a propriedade dos mapas.",
            parent=root):
            for label in REGIONS:
                if not messagebox.askyesno(label+" (opcional)",
                        "Deseja incluir uma fonte separada para "+label+"?",
                        parent=root):
                    continue
                byzip = messagebox.askyesno("Formato de "+label,
                    "A fonte de "+label+" está num ZIP?\n"
                    "Sim = escolher ZIP. Não = escolher pasta Data/game.",
                    parent=root)
                if byzip:
                    source = filedialog.askopenfilename(
                        parent=root,title="ZIP do snapshot "+label,
                        filetypes=[("ZIP de mapas","*.zip")])
                else:
                    source = filedialog.askdirectory(
                        parent=root,title="Data/game do snapshot "+label)
                if not source:
                    root.destroy()
                    return None
                overlays.append(label+"="+source)
        root.destroy()
        return Path(base),overlays
    except (OSError,ImportError,RuntimeError) as exc:
        block("seletor gráfico indisponível: "+str(exc))


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--gui",action="store_true",
                        help="selecionar pasta real e overlays por janelas Windows")
    parser.add_argument("--base-data",type=Path,
                        help="pasta Data OU game do Decades instalado, leitura apenas")
    parser.add_argument("--overlay",action="append",default=[],metavar="REGION=PATH",
                        help="KANTO/JOHTO/HOENN/SINNOH = pasta Data/game ou ZIP do overlay")
    parser.add_argument("--write",action="store_true")
    args=parser.parse_args(argv)
    try:
        if args.gui:
            if args.base_data or args.overlay:
                block("--gui nao pode ser combinado com --base-data/--overlay")
            selection=choose_gui()
            if selection is None:
                print("UNOVA_A04_CANCELADO: nenhuma fonte alterada")
                return 2
            args.base_data,args.overlay=selection
        if not args.base_data:
            report=missing_base()
            if args.write:
                write_private(args.project,report)
            print(json.dumps(report,ensure_ascii=False,indent=2))
            return 2
        overlays=overlay_args(args.overlay)
        base=scan_source(args.base_data,"DECADES",base=True)
        scans={}
        for label in REGIONS:
            if label in overlays:
                scans[label]=scan_source(overlays[label],label)
        report=analyze(base,scans)
        if args.write:
            output=write_private(args.project,report)
            print("RELATORIO_A04_PRIVADO: "+str(output),file=sys.stderr)
        summary={k:v for k,v in report.items() if k not in
                 ("sources","observed_or_declared_occupied_map_ids")}
        summary["observed_or_declared_occupied_count"]=report["observed_or_declared_occupied_count"]
        print(json.dumps(summary,ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError,zipfile.BadZipFile,
            zipfile.LargeZipFile,NotImplementedError) as exc:
        print("UNOVA_A04_BLOQUEADO: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
