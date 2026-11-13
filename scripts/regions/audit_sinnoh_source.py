#!/usr/bin/env python3
"""Read-only Sinnoh source and native-game preflight; never installs donor files.

Checks ZIP or extracted RMXP project shape, map IDs, dependencies, the regional
registry and collisions with the local Decades installation. No Ruby code from
a donor is run, no ZIP content is extracted, and no saves/assets are changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP_RE = re.compile(r"Map([0-9]{1,5})\.rxdata$", re.I)
REQUIRED = {"MapInfos.rxdata", "Tilesets.rxdata"}
EXPECTED_BADGES = (
    "COAL", "FOREST", "COBBLE", "RELIC",
    "FEN", "MINE", "ICICLE", "BEACON",
)
EXPECTED_FIELD = {
    "ROCK_SMASH": "COAL", "CUT": "FOREST", "FLY": "COBBLE",
    "DEFOG": "RELIC", "SURF": "FEN", "STRENGTH": "MINE",
    "ROCK_CLIMB": "ICICLE", "WATERFALL": "BEACON",
}
MAX_MEMBERS = 60000
MAX_BYTES = 12 * 1024**3
MAX_ITEM = 1024**3


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for data in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(data)
    return digest.hexdigest()


def map_id(name: str) -> int | None:
    match = MAP_RE.fullmatch(name)
    return int(match.group(1)) if match and int(match.group(1)) > 0 else None


def validate_registry(root: Path) -> dict:
    file = root / "site/public/data/regions.json"
    registry = json.loads(file.read_text("utf-8-sig"))
    region = registry["regions"]["SINNOH"]
    if region.get("status") != "planned":
        raise ValueError("Sinnoh deve continuar planned antes do piloto comprovado")
    if tuple(region["milestones"]) != EXPECTED_BADGES:
        raise ValueError("Insígnias de Sinnoh divergentes da ordem Platinum")
    fields = region["field"]
    if set(fields) != set(EXPECTED_FIELD):
        raise ValueError("Ações de campo de Sinnoh divergentes de Platinum")
    for action, badge in EXPECTED_FIELD.items():
        rule = fields[action]
        if rule.get("badge") != "SINNOH:" + badge or rule.get("tool") is not True:
            raise ValueError(f"Sinnoh {action}: regra de insígnia local inválida")
    circuit = registry["circuit"]
    if circuit.index("SINNOH") == 0 or circuit.index("SINNOH") == len(circuit) - 1:
        raise ValueError("Sinnoh fora de posição segura no circuito")
    idx = circuit.index("SINNOH")
    neighbors = [circuit[idx - 1], circuit[idx + 1]]
    if neighbors != ["HOENN", "UNOVA"]:
        raise ValueError("Sinnoh deve liberar Hoenn e Unova")
    return {"status": region["status"], "badges": list(EXPECTED_BADGES),
            "field_rules_valid": True, "league_unlocks": neighbors}


def _zip_parts(raw: str) -> tuple[str, ...]:
    if not raw or "\x00" in raw or "\\" in raw or raw.startswith("/"):
        raise ValueError(f"Nome inseguro de entrada ZIP: {raw!r}")
    parts = raw.rstrip("/").split("/")
    if any(not part or part in (".", "..") or ":" in part for part in parts):
        raise ValueError(f"Caminho inseguro de entrada ZIP: {raw!r}")
    return tuple(parts)


def inspect_zip(source: Path) -> dict:
    if source.is_symlink() or not source.is_file():
        raise ValueError("A fonte ZIP não pode ser link simbólico ou inexistente")
    groups: dict[str, dict] = {}
    with zipfile.ZipFile(source) as archive:
        members = archive.infolist()
        if len(members) > MAX_MEMBERS:
            raise ValueError("ZIP com entradas demais")
        size = 0
        seen: set[str] = set()
        for member in members:
            parts = _zip_parts(member.filename)
            if stat.S_IFMT(member.external_attr >> 16) == stat.S_IFLNK:
                raise ValueError("ZIP contém link simbólico")
            if member.flag_bits & 1:
                raise ValueError("ZIP contém membro criptografado")
            if member.file_size > MAX_ITEM:
                raise ValueError("ZIP contém arquivo excessivamente grande")
            size += member.file_size
            if size > MAX_BYTES:
                raise ValueError("ZIP excede limite de tamanho descompactado")
            if member.is_dir() or len(parts) < 2 or parts[-2] != "Data":
                continue
            name = parts[-1]
            if name not in REQUIRED and map_id(name) is None:
                continue
            base = "/".join(parts[:-2])
            key = (base + "/Data/" + name).casefold()
            if key in seen:
                raise ValueError(f"Entrada duplicada na fonte: {key}")
            seen.add(key)
            group = groups.setdefault(base, {"files": set(), "maps": set()})
            group["files"].add(name)
            number = map_id(name)
            if number is not None:
                if number in group["maps"]:
                    raise ValueError("IDs duplicados em mapas Sinnoh")
                group["maps"].add(number)
    return _summarize(groups, checksum(source), "ZIP_METADATA_ONLY")


def inspect_directory(source: Path) -> dict:
    if source.is_symlink() or not source.is_dir():
        raise ValueError("Pasta de origem não existe ou é link simbólico")
    candidates = []
    # Examine project root and up to two parent wrapper levels; never follow links.
    queue = [(source, 0)]
    while queue:
        folder, depth = queue.pop(0)
        data = folder / "Data"
        if data.is_dir() and not data.is_symlink():
            candidates.append(data)
        if depth < 2:
            for entry in folder.iterdir():
                if entry.is_dir() and not entry.is_symlink() and entry.name != "Data":
                    queue.append((entry, depth + 1))
    groups: dict[str, dict] = {}
    for data in candidates:
        names: set[str] = set()
        maps: set[int] = set()
        for file in data.iterdir():
            if file.is_symlink():
                raise ValueError("Link simbólico em pasta Data: " + str(file))
            if not file.is_file():
                continue
            if file.name in REQUIRED or map_id(file.name) is not None:
                if file.stat().st_size > MAX_ITEM:
                    raise ValueError("RXDATA acima do limite: " + file.name)
                if file.name.casefold() in {n.casefold() for n in names}:
                    raise ValueError("Arquivos de dados duplicados por caixa")
                names.add(file.name)
                number = map_id(file.name)
                if number is not None:
                    if number in maps:
                        raise ValueError("MapID duplicado no diretório de origem")
                    maps.add(number)
        groups[str(data.relative_to(source).parent)] = {"files": names, "maps": maps}
    return _summarize(groups, None, "LOCAL_DIRECTORY_METADATA_ONLY")


def _summarize(groups: dict, archive_hash: str | None, mode: str) -> dict:
    valid = [(name, values) for name, values in groups.items()
             if REQUIRED.issubset(values["files"])]
    if len(valid) != 1:
        raise ValueError(f"Esperado exatamente um Data/ com MapInfos e Tilesets; encontrados: {len(valid)}")
    base, values = valid[0]
    maps = sorted(values["maps"])
    return {
        "mode": mode, "project_root_inside_source": base,
        "sha256_zip": archive_hash, "map_count": len(maps),
        "source_map_ids": maps, "required_data_present": True,
        "empty_or_template_source": len(maps) <= 2,
        "source_maps_imported": False, "permission_confirmed": False,
    }


def inspect_native(game_data: Path) -> dict:
    if not game_data.exists():
        return {"status": "ABSENT", "source": str(game_data), "occupied_ids": None}
    if game_data.is_symlink() or not game_data.is_dir():
        raise ValueError("Diretório game/Data inválido ou link simbólico")
    ids: set[int] = set()
    for file in game_data.iterdir():
        if file.is_symlink():
            raise ValueError("Link simbólico no game/Data")
        number = map_id(file.name)
        if number is not None:
            ids.add(number)
    info_file = game_data / "MapInfos.rxdata"
    if info_file.is_file():
        from audit_johto import read_map_data
        infos = read_map_data(info_file)
        if not isinstance(infos, dict):
            raise ValueError("MapInfos de Decades não é um dicionário RMXP")
        ids.update(key for key in infos if isinstance(key, int) and key > 0)
    return {"status": "LOCAL_READ_ONLY", "occupied_count": len(ids),
            "highest_occupied": max(ids) if ids else None,
            "occupied_ids": sorted(ids)}


def audit(root: Path = ROOT, source: Path | None = None,
          game_data: Path | None = None) -> dict:
    registry = validate_registry(root)
    title = (root / "scripts/battle_polish/TitleKanto.rb").read_text("utf-8")
    if not all(token in title for token in (
        'SINNOH_LABEL = "Testar Sinnoh"',
        'SINNOH_LAUNCHER = "SINNOH_JOGAR_EXPERIMENTAL.bat"',
        'pilot_sinnoh.py', 'Sinnoh pilot.json', 'ordered << :blue_test_sinnoh',
    )):
        raise ValueError("O menu Testar Sinnoh não está conectado ao carregador seguro")
    if source:
        source = source.expanduser().absolute()
        if source == root.absolute() or source == (root / "game").absolute() or (
                (root / "game").absolute() in source.parents):
            raise ValueError("Não usar a instalação game/ como fonte de Sinnoh")
        candidate = inspect_zip(source) if source.suffix.lower() == ".zip" else inspect_directory(source)
    else:
        candidate = None
    native = inspect_native(game_data or (root / "game/Data"))
    overlaps = (sorted(set(candidate["source_map_ids"]) & set(native["occupied_ids"]))
                if candidate and native["occupied_ids"] is not None else None)
    blockers = []
    if candidate is None:
        blockers.append("Fonte real de Sinnoh não fornecida")
    else:
        if candidate["empty_or_template_source"]:
            blockers.append("Fonte contém apenas até dois mapas; não comprova Sinnoh jogável")
        blockers.extend([
            "Autorização de uso/redistribuição por asset não verificada",
            "Interiores, eventos e gráficos ainda não auditados no runtime",
        ])
    if native["status"] == "ABSENT":
        blockers.append("Instalação game/Data local indisponível; IDs de Decades e regiões não auditados")
    blockers.extend([
        "Reserva/remapeamento de IDs não realizado",
        "Execução Windows e JoiPlay/Android ainda não comprovada",
    ])
    return {
        "schema": 1, "region": "SINNOH", "mode": "READ_ONLY",
        "registry": registry, "title_option": "WIRED_NO_REAL_PILOT",
        "source": candidate, "native": native, "unmapped_id_collisions": overlaps,
        "rights_verified": False, "map_installation_verified": False,
        "native_gameplay_verified": False, "phase_00_fully_approved": False,
        "technical_phases_approved": 0, "playable_phases_approved": 0,
        "blockers": blockers,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="ZIP legítimo ou pasta de projeto RMXP")
    parser.add_argument("--game-data", type=Path, help="Cópia local da pasta game/Data, opcional")
    args = parser.parse_args(argv)
    try:
        report = audit(source=args.source, game_data=args.game_data)
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, ImportError) as exc:
        print("SINNOH_PREFLIGHT_BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
