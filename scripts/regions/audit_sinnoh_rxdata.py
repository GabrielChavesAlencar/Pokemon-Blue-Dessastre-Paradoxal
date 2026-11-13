#!/usr/bin/env python3
"""Deep, INERT Sinnoh RXDATA map audit for a local ZIP or RMXP directory.

It never extracts the archive, executes third-party Ruby, changes maps/saves,
or allocates destination IDs. Accepts missing references as findings, not as
working maps. Only use sources whose ownership/rights can be established.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

from audit_johto import ROOT
from audit_sinnoh_source import inspect_zip, inspect_directory, inspect_native, validate_registry
from server.ruby_marshal import RubyObject, loads, text

MAX_RMXP_BYTES = 32_000_000
GRAPHIC_NAME = re.compile(r"[\w .()\-]{1,180}\Z", re.UNICODE)
MAP_FILENAME = re.compile(r"Map0*(\d+)\.rxdata\Z", re.I)


def attrs(value) -> dict:
    return value.attrs if isinstance(value, RubyObject) else {}


def read_marshal(raw: bytes, name: str):
    if len(raw) > MAX_RMXP_BYTES:
        raise ValueError(f"{name}: RXDATA maior que o limite seguro")
    try:
        return loads(raw)
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        raise ValueError(f"{name}: Ruby Marshal inválido") from exc


class Source:
    """Single verified Data root; no extraction, symlink following or writes."""

    def __init__(self, source: Path):
        self.path = source.expanduser().absolute()
        if self.path.is_symlink():
            raise ValueError("Fonte em link simbólico bloqueada")
        self.zip = self.path.suffix.lower() == ".zip"
        self.metadata = inspect_zip(self.path) if self.zip else inspect_directory(self.path)
        base = self.metadata["project_root_inside_source"]
        self.base = base + "/" if base not in ("", ".") else ""
        self.archive = None
        self.member_names = {}
        if self.zip:
            self.archive = zipfile.ZipFile(self.path)
            for info in self.archive.infolist():
                if info.is_dir():
                    continue
                if info.filename.casefold() in self.member_names:
                    raise ValueError("Membros ZIP duplicados por nome")
                self.member_names[info.filename.casefold()] = info
        else:
            self.root = self.path / base

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self.archive:
            self.archive.close()

    def exists(self, rel: str) -> bool:
        if self.zip:
            return (self.base + rel).casefold() in self.member_names
        path = self.root / rel
        return path.is_file() and not path.is_symlink()

    def read(self, rel: str) -> bytes:
        if self.zip:
            info = self.member_names.get((self.base + rel).casefold())
            if not info:
                raise ValueError("Arquivo da fonte ausente: " + rel)
            if info.file_size > MAX_RMXP_BYTES:
                raise ValueError("RXDATA muito grande: " + rel)
            assert self.archive is not None
            with self.archive.open(info) as stream:
                raw = stream.read(MAX_RMXP_BYTES + 1)
        else:
            path = self.root / rel
            if path.is_symlink() or not path.is_file():
                raise ValueError("Arquivo da fonte ausente ou link: " + rel)
            if path.stat().st_size > MAX_RMXP_BYTES:
                raise ValueError("RXDATA muito grande: " + rel)
            raw = path.read_bytes()
        if len(raw) > MAX_RMXP_BYTES:
            raise ValueError("RXDATA ultrapassou limite de leitura: " + rel)
        return raw

    def map_paths(self):
        """Look up filenames by numeric ID, including unpadded Map1.rxdata."""
        available = {}
        if self.zip:
            names = [name[len(self.base):] for name in self.member_names
                     if name.startswith(self.base.casefold())]
        else:
            data = self.root / "Data"
            names = ["Data/" + p.name for p in data.iterdir() if p.is_file()]
        for name in names:
            if not name.casefold().startswith("data/"):
                continue
            leaf = name[5:]
            found = MAP_FILENAME.fullmatch(leaf)
            if not found:
                continue
            mid = int(found.group(1))
            if mid in available:
                raise ValueError(f"MapID duplicado: {mid}")
            available[mid] = name
        return available


def graphic_reference(source: Source, folder: str, value) -> str | None:
    name = text(value).strip()
    if not name:
        return None
    # Do not resolve untrusted paths outside the project.
    if not GRAPHIC_NAME.fullmatch(name) or name in (".", ".."):
        return f"INVALID:{folder}/{name[:80]}"
    return f"Graphics/{folder}/{name}.png"


def audit_rxdata(source: Path, game_data: Path | None = None) -> dict:
    with Source(source) as donor:
        infos_raw = donor.read("Data/MapInfos.rxdata")
        tiles_raw = donor.read("Data/Tilesets.rxdata")
        infos = read_marshal(infos_raw, "MapInfos.rxdata")
        tilesets = read_marshal(tiles_raw, "Tilesets.rxdata")
        if not isinstance(infos, dict) or not all(type(mid) is int and mid > 0 for mid in infos):
            raise ValueError("MapInfos deve ser dicionário indexado por MapIDs inteiros")
        if not isinstance(tilesets, (list, dict)):
            raise ValueError("Tilesets deve ser lista/dicionário RMXP")
        if len(infos) > 5000 or len(tilesets) > 5000:
            raise ValueError("MapInfos/Tilesets excedem limite da auditoria")
        map_paths = donor.map_paths()
        if set(donor.metadata["source_map_ids"]) != set(map_paths):
            raise ValueError("Arquivos reais não correspondem ao inventário superficial")
        if not map_paths:
            raise ValueError("Fonte não contém mapas")
        tile_lookup = (
            {key: obj for key, obj in enumerate(tilesets)}
            if isinstance(tilesets, list) else tilesets
        )
        source_maps = set(map_paths)
        refs = set()
        dynamic_transfers = 0
        scripts = 0
        map_rows = []
        missing_graphics = set()
        invalid_graphics = set()
        graphic_refs = set()
        for mid, rel in sorted(map_paths.items()):
            raw = donor.read(rel)
            map_obj = read_marshal(raw, rel)
            if not isinstance(map_obj, RubyObject) or map_obj.name != "RPG::Map":
                raise ValueError(f"{rel}: esperado RPG::Map")
            data = attrs(map_obj)
            width, height, tile_id = (data.get("@width"), data.get("@height"),
                                      data.get("@tileset_id"))
            if any(type(n) is not int for n in (width, height, tile_id)):
                raise ValueError(f"{rel}: dimensões ou tileset inválidos")
            if not (0 < width <= 500 and 0 < height <= 500 and tile_id > 0):
                raise ValueError(f"{rel}: dimensões ou tileset fora do limite")
            tile = tile_lookup.get(tile_id)
            if not isinstance(tile, RubyObject) or tile.name != "RPG::Tileset":
                raise ValueError(f"{rel}: tileset {tile_id} inexistente")
            tile_attrs = attrs(tile)
            associated = [graphic_reference(donor, "Tilesets", tile_attrs.get("@tileset_name"))]
            auto = tile_attrs.get("@autotile_names", [])
            if not isinstance(auto, list):
                raise ValueError(f"{rel}: autotiles inválidos")
            associated += [graphic_reference(donor, "Autotiles", name) for name in auto]
            for graphic in associated:
                if not graphic:
                    continue
                graphic_refs.add(graphic)
                if graphic.startswith("INVALID:"):
                    invalid_graphics.add(graphic)
                elif not donor.exists(graphic):
                    missing_graphics.add(graphic)
            events = data.get("@events", {})
            if not isinstance(events, dict):
                raise ValueError(f"{rel}: eventos devem ser um dicionário")
            event_count = len(events)
            pages = 0
            transfers = set()
            for event in events.values():
                if not isinstance(event, RubyObject):
                    raise ValueError(f"{rel}: evento RMXP inválido")
                for page in attrs(event).get("@pages", []):
                    pages += 1
                    for command in attrs(page).get("@list", []):
                        code = attrs(command).get("@code")
                        args = attrs(command).get("@parameters", [])
                        if code in (355, 655):
                            scripts += 1
                        if code == 201:
                            if (isinstance(args, list) and len(args) > 1
                                    and args[0] == 0 and type(args[1]) is int):
                                transfers.add(args[1])
                            else:
                                dynamic_transfers += 1
            refs.update(transfers)
            info = infos.get(mid)
            map_rows.append({
                "source_id": mid, "name": text(attrs(info).get("@name", b"")).strip(),
                "width": width, "height": height,
                "tileset_id": tile_id, "events": event_count, "event_pages": pages,
                "transfer_targets": sorted(transfers),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "source_file": rel,
            })
        native = inspect_native(game_data) if game_data is not None else {
            "status": "NOT_CHECKED", "occupied_ids": None}
        native_ids = native.get("occupied_ids")
        result = {
            "schema": 1, "region": "SINNOH",
            "mode": "READ_ONLY_INERT_RMXP", "source": str(donor.path),
            "source_mode": donor.metadata["mode"], "source_zip_sha256":
                donor.metadata["sha256_zip"],
            "source_map_count": len(map_rows),
            "mapinfos_sha256": hashlib.sha256(infos_raw).hexdigest(),
            "tilesets_sha256": hashlib.sha256(tiles_raw).hexdigest(),
            "source_map_ids": sorted(source_maps),
            "missing_map_files": sorted(set(infos) - source_maps),
            "orphan_map_files": sorted(source_maps - set(infos)),
            "unresolved_static_transfer_ids": sorted(refs - source_maps),
            "dynamic_transfer_commands": dynamic_transfers,
            "untrusted_script_commands_not_executed": scripts,
            "graphics_referenced": len(graphic_refs),
            "missing_graphics": sorted(missing_graphics),
            "invalid_graphic_names": sorted(invalid_graphics),
            "native": native,
            "unmapped_id_collisions": (
                sorted(source_maps & set(native_ids)) if native_ids is not None else None
            ),
            "maps": map_rows,
            "rights_verified": False,
            "import_allowed": False, "pilot_verified": False,
            "warning": (
                "No asset/script execution or extraction. Static transfers omit "
                "common events/conditional scripts, so no readiness claim. "
                "No MapIDs allocated, rights not cleared, game unchanged."
            )
        }
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="ZIP ou diretório RMXP Sinnoh legítimo")
    parser.add_argument("--game-data", type=Path,
                        help="Instalação local game/Data para detectar IDs ocupados")
    args = parser.parse_args()
    try:
        report = audit_rxdata(args.source, args.game_data)
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print("SINNOH_RXDATA_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
