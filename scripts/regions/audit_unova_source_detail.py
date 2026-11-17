#!/usr/bin/env python3
"""Unova: inert RXDATA source audit (no extraction, Ruby execution, or installs).

Use only with the manually provided ZIP, privately staged in .blue-work.
A map-name match is a CANDIDATE, not proof of region, rights or gameplay.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import unicodedata
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from server.ruby_marshal import RubyObject, loads, text
from audit_unova_u02 import audit_zip, is_within_source, fail

MAX_RXDATA = 24 * 1024 * 1024
MAX_READ_TOTAL = 256 * 1024 * 1024
MAP_RX = re.compile(r"map0*([1-9][0-9]*)\.rxdata\Z", re.I)
STATIC_TRANSFER = 201
SCRIPT_CODES = {355, 655}


def normalized(raw: str) -> str:
    plain = unicodedata.normalize("NFKD", raw)
    plain = "".join(x for x in plain if not unicodedata.combining(x))
    return re.sub(r"[^a-z0-9]+", " ", plain.casefold()).strip()


def attrs(obj, cls: str) -> dict:
    if not isinstance(obj, RubyObject) or obj.name != cls:
        fail("esperado objeto " + cls)
    return obj.attrs


def parse(raw: bytes, name: str):
    if len(raw) > MAX_RXDATA:
        fail(name + " maior que limite RXDATA")
    try:
        return loads(raw)
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, RecursionError) as exc:
        fail("RXDATA corrompido/incompativel: " + name + " (" + exc.__class__.__name__ + ")")


def inspect(source: Path, catalog: dict) -> dict:
    if not isinstance(catalog, dict) or catalog.get("state") != "PLANNED_REFERENCE_ONLY" or catalog.get("may_install") is not False:
        fail("catalogo simbolico ausente/inseguro")
    areas = catalog.get("areas")
    if not isinstance(areas, list) or not areas:
        fail("catalogo de areas vazio")
    metadata = audit_zip(source)  # validates ZIP structure without extracting
    wrappers = metadata["project_wrapper"]
    prefix = (wrappers + "/" if wrappers else "") + "Data/"
    with zipfile.ZipFile(source) as archive:
        members = {info.filename.casefold(): info for info in archive.infolist() if not info.is_dir()}
        total = 0

        def read_member(name: str) -> bytes:
            nonlocal total
            info = members.get(name.casefold())
            if info is None:
                fail("arquivo fonte ausente: " + name)
            if info.file_size > MAX_RXDATA or total + info.file_size > MAX_READ_TOTAL:
                fail("limite de leitura RXDATA excedido")
            with archive.open(info) as handle:
                raw = handle.read(MAX_RXDATA + 1)
            if len(raw) != info.file_size or len(raw) > MAX_RXDATA:
                fail("RXDATA com tamanho divergente")
            total += len(raw)
            return raw

        infos_raw = read_member(prefix + "MapInfos.rxdata")
        infos = parse(infos_raw, "MapInfos.rxdata")
        if not isinstance(infos, dict) or len(infos) > 7500 or any(type(i) is not int or i < 1 for i in infos):
            fail("MapInfos nao e dicionario RMXP seguro")
        names = {}
        for mid, info in infos.items():
            name = text(attrs(info, "RPG::MapInfo").get("@name", b"")).strip()
            if len(name) > 200:
                fail("nome de mapa muito longo")
            names[mid] = name
        maps = []
        missing = sorted(set(infos) - set(metadata["all_regions_source_map_ids"]))
        orphan = sorted(set(metadata["all_regions_source_map_ids"]) - set(infos))
        for mid in metadata["all_regions_source_map_ids"]:
            candidates = [prefix + f"Map{mid:03d}.rxdata", prefix + f"Map{mid}.rxdata"]
            source_file = next((name for name in candidates if name.casefold() in members), None)
            if source_file is None:
                # Accept nonstandard zero padding but never infer a destination MapID.
                source_file = next((info.filename for info in members.values()
                    if info.filename.casefold().startswith(prefix.casefold())
                    and MAP_RX.fullmatch(info.filename.split("/")[-1])
                    and int(MAP_RX.fullmatch(info.filename.split("/")[-1]).group(1)) == mid), None)
            if not source_file:
                fail("MapID anunciado sem arquivo real")
            data = read_member(source_file)
            obj = attrs(parse(data, source_file), "RPG::Map")
            width, height = obj.get("@width"), obj.get("@height")
            if any(type(v) is not int or not 1 <= v <= 500 for v in (width, height)):
                fail("dimensoes invalidas Map " + str(mid))
            events = obj.get("@events", {})
            if not isinstance(events, dict) or len(events) > 5000:
                fail("eventos invalidos em Map " + str(mid))
            pages = static = dynamic = scripts = 0
            refs = set()
            for event in events.values():
                e = attrs(event, "RPG::Event")
                epages = e.get("@pages", [])
                if not isinstance(epages, list) or len(epages) > 100:
                    fail("paginas excessivas no Map " + str(mid))
                pages += len(epages)
                for page in epages:
                    page_attrs = attrs(page, "RPG::Event::Page")
                    cmds = page_attrs.get("@list", [])
                    if not isinstance(cmds, list) or len(cmds) > 30000:
                        fail("comandos excessivos no Map " + str(mid))
                    for command in cmds:
                        command_attrs = attrs(command, "RPG::EventCommand")
                        code = command_attrs.get("@code")
                        params = command_attrs.get("@parameters", [])
                        if code in SCRIPT_CODES:
                            scripts += 1
                        if code == STATIC_TRANSFER:
                            if (isinstance(params, list) and len(params) >= 2
                                    and params[0] == 0 and type(params[1]) is int and params[1] > 0):
                                refs.add(params[1])
                                static += 1
                            else:
                                dynamic += 1
            name = names.get(mid, "")
            norm = normalized(name)
            matches = [area["key"] for area in areas
                       if normalized(area["name"]) == norm and area.get("kind") != "route"]
            # "Route 1" alone cannot disambiguate multiple regions in a donor project.
            maps.append({
                "source_map_id": mid, "name": name,
                "width": width, "height": height,
                "event_count": len(events), "event_pages": pages,
                "static_transfer_commands": static,
                "dynamic_transfer_commands": dynamic,
                "static_transfer_target_ids": sorted(refs),
                "untrusted_script_commands_not_executed": scripts,
                "unova_name_candidates_for_manual_review": matches,
                "candidate_confirmed_as_unova": False,
                "source_sha256": hashlib.sha256(data).hexdigest(),
                "destination_map_id": None,
                "rights_verified": False, "compiled_in_game": False,
            })
    all_ids = set(metadata["all_regions_source_map_ids"])
    unresolved = sorted({ref for row in maps for ref in row["static_transfer_target_ids"] if ref not in all_ids})
    candidates_found = sorted({name for row in maps for name in row["unova_name_candidates_for_manual_review"]})
    return {
        "schema": 1, "region": "UNOVA", "phase": "U02_E05",
        "mode": "READ_ONLY_INERT_SOURCE_INSPECTION",
        "status": "SOURCE_RXDATA_INSPECTED_NOT_APPROVED",
        "source_zip_sha256": metadata["archive_sha256"],
        "source_mapinfos_sha256": hashlib.sha256(infos_raw).hexdigest(),
        "all_regions_source_map_count": len(maps),
        "candidate_unova_area_keys": candidates_found,
        "confirmed_unova_map_count": None,
        "missing_map_files": missing, "orphan_map_files": orphan,
        "unresolved_transfer_ids": unresolved,
        "total_untrusted_script_commands_not_executed": sum(m["untrusted_script_commands_not_executed"] for m in maps),
        "maps": maps, "rights_verified": False,
        "native_mapinfos_verified": False, "can_install": False,
        "game_or_saves_modified": False, "game_exe_tested": False,
        "android_tested": False,
        "blockers": [
            "Nomes de mapas sao candidatos; identificacao regional e revisao manual pendentes",
            "Direitos de assets/musicas/eventos por arquivo nao verificados",
            "Reservas MapID de Decades/Kanto/Johto/Hoenn/Sinnoh ainda sem auditoria local",
            "Mapas ainda nao convertidos nem testados em Game.exe/JoiPlay",
        ],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, default=ROOT)
    ap.add_argument("--source", type=Path)
    ap.add_argument("--catalog", type=Path, default=ROOT / "data/regions/unova-u03-areas.json")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)
    project = args.project.absolute()
    source = args.source or project / ".blue-work/unova/sources/Pokemon_World_V18.zip"
    try:
        if not is_within_source(project, source):
            fail("ZIP deve estar em .blue-work/unova/sources, sem symlinks")
        if args.catalog.is_symlink() or not args.catalog.is_file():
            fail("catalogo ausente ou symlink")
        if not source.is_file():
            fail("ZIP real nao fornecido")
        catalog = json.loads(args.catalog.read_text("utf-8"))
        report = inspect(source, catalog)
        if args.write:
            # Never reuse the U02 report or follow workspace symlinks.
            work = project / ".blue-work"
            local = work / "unova"
            dest = local / "audit"
            for folder in (project, work, local, dest):
                if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
                    fail("pasta de relatorio insegura")
            dest.mkdir(parents=True, exist_ok=True)
            target = dest / "u02-rxdata-detail.json"
            if target.is_symlink():
                fail("relatorio symlink")
            payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
            if target.exists():
                if target.read_text("utf-8") != payload:
                    fail("relatorio anterior difere; preservar evidencia anterior")
            else:
                with target.open("x", encoding="utf-8") as out:
                    out.write(payload)
        print(json.dumps({k: v for k, v in report.items() if k != "maps"}, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError, zipfile.BadZipFile) as exc:
        print("UNOVA_RXDATA_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
