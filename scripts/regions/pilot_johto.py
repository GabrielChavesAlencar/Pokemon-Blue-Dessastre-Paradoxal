"""Monta uma cópia experimental de New Bark sem tocar no jogo principal.

Pré-requisitos: stage_johto + verify_johto, eventos gerados em memória com
coordenadas reais e PBS do motor instalado. NÃO instala mapa, salva progresso,
ativa Johto na campanha principal ou emite VERIFIED_PLAYABLE.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

from audit_johto import ROOT, checksum, read_map_data
from build_johto_events import compile_events, read_json
from draft_johto_rival_pbs import build as build_rival_pbs
from compile_johto_connections import build as build_connections, merge_pbs
from pilot import copy_game, SYSTEM_CLASSES
from stage import serialize
from verify_johto import inspect
from server.ruby_marshal import RubyObject

OUTPUT = ROOT / ".blue-work/johto-pilot"
PREVIEW = ROOT / ".blue-work/johto-staging-v1"
SPEC = ROOT / "data/regions/johto-new-bark-events.json"
SAVE_APP = "Johto Piloto"
SAVE_ORG = "Dessastre Paradoxal Johto Testes"
PILOT_FILES = (
    "scripts/regions/JohtoPilot.rb",
    "scripts/regions/JohtoPilotStart.rb",
)


def checked_file(path: Path) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Arquivo obrigatório ausente ou symlink: {path}")
    return path


def allowed_workspace(root: Path, directory: Path, *, must_be_new=False) -> Path:
    work = (root / ".blue-work").resolve()
    if (work.is_symlink() or directory.is_symlink() or
            not directory.resolve().is_relative_to(work) or
            directory.resolve() == work or
            (must_be_new and directory.exists())):
        raise ValueError("Workspace inválido ou destino não é novo dentro de .blue-work/")
    return directory


def validate_events_and_spawn(spec: dict, map_ids: dict, preview: Path) -> list[int]:
    rows = spec.get("maps")
    if not isinstance(rows, list) or len(rows) < 5:
        raise ValueError("Os cinco mapas iniciais de New Bark precisam estar auditados")
    adjacency = {}
    for row in rows:
        key = row.get("symbol")
        if key not in map_ids:
            raise ValueError("Mapa simbólico ainda ausente: " + str(key))
        adjacency[key] = {event.get("destination") for event in row.get("events", [])
                          if event.get("kind") == "warp"}
    for origin, targets in adjacency.items():
        for target in targets:
            if target not in adjacency or origin not in adjacency[target]:
                raise ValueError("Warp sem retorno validado: " + origin + " -> " + str(target))
    start = spec.get("start")
    home = "JOHTO_NEW_BARK_PLAYER_HOME_2F"
    if (not isinstance(start, dict) or start.get("symbol") != home or
            start.get("verified_position") is not True or
            start.get("passability_verified") is not True or
            type(start.get("x")) is not int or type(start.get("y")) is not int):
        raise ValueError("Spawn real dentro do quarto ainda não foi verificado")
    mid = map_ids[home]
    current = read_map_data(preview / "Data" / f"Map{mid:03d}.rxdata")
    width, height = current.attrs.get("@width"), current.attrs.get("@height")
    x, y = start["x"], start["y"]
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError("Spawn fora do mapa do quarto")
    home_row = next(row for row in rows if row["symbol"] == home)
    if any((event["x"], event["y"]) == (x, y) for event in home_row["events"]):
        raise ValueError("Spawn em cima de NPC/porta")
    return [mid, x, y]


def inspect_game(game: Path, root: Path) -> None:
    if game.resolve() != (root / "game").resolve() or game.is_symlink():
        raise ValueError("Usar somente a instalação original root/game como fonte de leitura")
    needed = ("Game.exe", "Game.ini", "mkxp.json",
              "Data/System.rxdata", "Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
              "Plugins/ZZZZ Blue Story and Presentation/Regions.rb",
              "Graphics/Trainers/RIVAL1.png")
    for path in needed:
        checked_file(game / path)
    for dir_name in ("Audio", "Data", "Fonts", "Graphics", "PBS", "Plugins"):
        directory = game / dir_name
        if not directory.is_dir() or directory.is_symlink():
            raise ValueError("Pasta obrigatória ausente/symlink: " + dir_name)
    config = (game / "mkxp.json").read_text(encoding="utf-8-sig")
    if re.search(r'"dataPath(App|Org)"\s*:', config):
        raise ValueError("Não reutilizar perfil de save de uma instalação já personalizada")


def validate_sprites(spec: dict, game: Path, preview: Path) -> None:
    for row in spec["maps"]:
        for event in row["events"]:
            if event.get("kind") != "handler":
                continue
            name = event["sprite"]
            base, staged = (game / "Graphics/Characters" / (name + ".png"),
                            preview / "Graphics/Characters" / (name + ".png"))
            # Characters are never sourced automatically from untrusted scripts.
            image = base if base.is_file() else staged
            checked_file(image)
            with image.open("rb") as stream:
                if stream.read(8) != b"\x89PNG\r\n\x1a\n":
                    raise ValueError("Sprite não é PNG válido: " + str(image))


def replace_ini(text: str) -> str:
    if not re.search(r"(?m)^Title=", text):
        raise ValueError("Game.ini não tem Title=")
    return re.sub(r"(?m)^Title=.*$", "Title=" + SAVE_APP, text)


def isolate_saves(text: str) -> str:
    # The file shipped by the Blue base is an object (not JSON-with-comments).
    config = json.loads(text.lstrip("\ufeff"))
    if not isinstance(config, dict):
        raise ValueError("mkxp.json não contém objeto")
    if any(key in config for key in ("dataPathApp", "dataPathOrg")):
        raise ValueError("A base já tem perfil de save customizado")
    config["dataPathApp"], config["dataPathOrg"] = SAVE_APP, SAVE_ORG
    config["windowTitle"] = "Pokémon Blue - Johto experimental"
    return json.dumps(config, ensure_ascii=False, indent=2) + "\n"


def plan(preview: Path, game: Path, spec: dict, *, root: Path = ROOT) -> tuple[dict, dict, dict, dict]:
    inspect_game(game, root)
    allowed_workspace(root, preview)
    preview_validation = inspect(preview, game, root=root)
    if preview_validation.get("status") != "STRUCTURAL_PREVIEW_VALIDATED_NOT_PLAYABLE":
        raise ValueError("Prévia de mapas não passou na verificação estrutural")
    event_report, event_data = compile_events(preview, spec, work_root=root)
    map_ids = event_report["map_ids"]
    start = validate_events_and_spawn(spec, map_ids, preview)
    validate_sprites(spec, game, preview)
    pbs_report, pbs_files = build_rival_pbs(game)
    for path in PILOT_FILES:
        checked_file(root / path)
    if (pbs_report.get("can_install") is not False or
            pbs_report.get("battle_proven") is not False):
        raise ValueError("PBS do rival não são rascunho seguro")
    return (
        {"region": "JOHTO", "status": "PREPARED_FOR_ISOLATED_BUILD",
         "start": start, "map_ids": map_ids,
         "source_archive_sha256": event_report["source_archive_sha256"],
         "battle_proven": False, "gameplay_verified": False,
         "preview_validation": preview_validation},
        event_data, pbs_files, pbs_report
    )


BORDER_EVENTS = {
    "JH_TOWN_TO_ROUTE29": ("JOHTO_NEW_BARK_TOWN", "JOHTO_ROUTE_29"),
    "JH_ROUTE29_TO_NEW_BARK": ("JOHTO_ROUTE_29", "JOHTO_NEW_BARK_TOWN"),
}


def without_duplicate_border_warps(spec: dict, connections: str) -> dict:
    """Replace the real New Bark/Route29 border with PBS only in a PILOT.

    Keep the source event template untouched; reject if either explicit warp
    is missing/mutated. PBS must have both real source maps connected.
    """
    if not isinstance(spec, dict) or not isinstance(spec.get("maps"), list):
        raise ValueError("Mapa de eventos New Bark invalido")
    result = copy.deepcopy(spec)
    expected_keys = set(BORDER_EVENTS)
    removed = set()
    map_symbols = {row.get("symbol") for row in result["maps"]}
    if len(map_symbols) != len(result["maps"]):
        raise ValueError("Mapas duplicados na especificacao do piloto")
    for row in result["maps"]:
        original_events = row.get("events")
        if not isinstance(original_events, list):
            raise ValueError("Eventos de New Bark invalidos")
        filtered = []
        for event in original_events:
            name = event.get("key")
            if name in expected_keys:
                origin, destination = BORDER_EVENTS[name]
                if (name in removed or row.get("symbol") != origin
                        or event.get("kind") != "warp"
                        or event.get("destination") != destination):
                    raise ValueError("Warp de borda New Bark/Route29 foi alterado")
                removed.add(name)
                continue
            filtered.append(event)
        if not filtered:
            raise ValueError("Nao remover todos os eventos de um mapa de New Bark")
        row["events"] = filtered
    if removed != expected_keys:
        raise ValueError("Warps da borda New Bark/Route29 incompletos")
    lines = [line.split(",") for line in connections.splitlines() if line.strip()]
    if not all(len(line) == 6 for line in lines):
        raise ValueError("PBS de borda malformado")
    ids = {row["symbol"]: row.get("map_id") for row in result["maps"]}
    a, b = ids.get("JOHTO_NEW_BARK_TOWN"), ids.get("JOHTO_ROUTE_29")
    if (type(a) is not int or type(b) is not int or a == b or
            not any({int(line[0]), int(line[3])} == {a, b} for line in lines)):
        raise ValueError("PBS nao prova borda entre MapIDs de New Bark e Rota 29")
    return result


def assemble(preview: Path, game: Path, output: Path, spec: dict,
             *, root: Path = ROOT, with_connections: bool = False) -> dict:
    root = root.resolve()
    preview, game, output = preview.absolute(), game.absolute(), output.absolute()
    allowed_workspace(root, output, must_be_new=True)
    if output.resolve() == preview.resolve() or output.resolve().is_relative_to(preview.resolve()):
        raise ValueError("Destino dentro da prévia")
    connection_text, connection_report = None, None
    event_spec = spec
    if with_connections:
        graph = read_json(root / "data/regions/johto-v1-map-connections.json")
        source_manifest = read_json(root / "data/regions/johto-source.json")
        connection_text, connection_report = build_connections(
            preview, game, graph, source_manifest, root=root)
        # Do not install 2 explicit teleports on top of the real PBS border.
        event_spec = without_duplicate_border_warps(spec, connection_text)
    report, events, pbs, pbs_report = plan(preview, game, event_spec, root=root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=".johto-pilot-build-") as temp:
        target = Path(temp) / "game"
        target.mkdir()
        copy_game(game, target)
        # stage_johto contains no executable, script, foreign event or music.
        for folder in ("Data", "Graphics"):
            staged = preview / folder
            if staged.is_dir():
                shutil.copytree(staged, target / folder, dirs_exist_ok=True)
        for name, payload in {**events, **pbs}.items():
            destination = target / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
        if connection_text is not None:
            # IMPORTANT: merge only into the experimental copy, preserve every
            # installed Kanto/Decades PBS line and avoid overwriting game/.
            dest_pbs = target / "PBS/map_connections.txt"
            existing = dest_pbs.read_bytes() if dest_pbs.is_file() else None
            dest_pbs.parent.mkdir(parents=True, exist_ok=True)
            dest_pbs.write_bytes(merge_pbs(existing, connection_text))

        # Only experimental copy receives custom trainer graphic/runtime.
        shutil.copyfile(game / "Graphics/Trainers/RIVAL1.png",
                        target / "Graphics/Trainers/BLUE_JOHTO_RIVAL.png")
        plugin = target / "Plugins/ZZZZZ Blue Johto Pilot"
        plugin.mkdir(parents=True)
        # A single registered Ruby script guarantees load order; the source
        # files remain independently versioned in scripts/regions/.
        runtime = "\n".join((root / file).read_text(encoding="utf-8")
                            for file in PILOT_FILES)
        (plugin / "JohtoPilotBoot.rb").write_text(runtime + "\n", encoding="utf-8")
        (plugin / "meta.txt").write_text(
            "Name = Blue Johto Pilot\nVersion = 0.1\nEssentials = 21.1\n"
            "Requires = Blue Battle Presentation and Story\n"
            "Scripts = JohtoPilotBoot.rb\n", encoding="utf-8")

        system_file = target / "Data/System.rxdata"
        system = read_map_data(system_file)
        if not isinstance(system, RubyObject) or system.name != "RPG::System":
            raise ValueError("System.rxdata não é RPG::System")
        mid, x, y = report["start"]
        system.attrs.update({"@start_map_id": mid, "@start_x": x, "@start_y": y})
        system_file.write_bytes(serialize(system, SYSTEM_CLASSES))
        ini = target / "Game.ini"
        ini.write_text(replace_ini(ini.read_text(encoding="utf-8-sig")), encoding="utf-8")
        mkxp = target / "mkxp.json"
        mkxp.write_text(isolate_saves(mkxp.read_text(encoding="utf-8-sig")), encoding="utf-8")
        compiled = target / "Data/PluginScripts.rxdata"
        if compiled.exists():
            checked_file(compiled)
            compiled.unlink()
        (target / "Data/blue-compile-request.txt").write_text("compile", encoding="ascii")

        # A boot guard distinct from the 13-proof production release path.
        watched = ["Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
                   "Data/System.rxdata", f"Data/Map{mid:03d}.rxdata",
                   *sorted(pbs)]
        if connection_text is not None:
            watched.append("PBS/map_connections.txt")
        hashes = {name: checksum(target / name) for name in watched}
        proof = {"schema": 1, "region": "JOHTO",
                 "status": "EXPERIMENTAL_UNTESTED", "can_install": False,
                 "archive_sha256": report["source_archive_sha256"],
                 "start": report["start"], "file_hashes": hashes,
                 "battle_proven": False, "gameplay_verified": False,
                 "source_connections_compiled": (
                     connection_report["compiled_count"] if connection_report else 0),
                 "connections_tested_in_game": False}
        (target / "Data/blue-johto-pilot-proof.json").write_text(
            json.dumps(proof, indent=2) + "\n", encoding="utf-8")
        (target / "Johto pilot.json").write_text(
            json.dumps({"kind": "ISOLATED_JOHTO_TEST",
                        "archive_sha256": report["source_archive_sha256"],
                        "save_app": SAVE_APP, "save_org": SAVE_ORG}) + "\n",
            encoding="utf-8")
        # NO blue-johto-install.json, NO VERIFIED_PLAYABLE marker,
        # NO blue-johto-rival-ready.txt: test real battles before allowing rival.
        (target / "JOHTO_PILOTO_LEIA-ME.txt").write_text(
            "PILOTO EXPERIMENTAL NAO VALIDADO. Executar Game.exe nesta copia apenas.\n"
            "Comeca no quarto, se mapas/sprites/eventos foram auditados de verdade.\n"
            "Rival fica BLOQUEADO ate compilar e testar as 3 versoes PBS reais.\n"
            "Nunca copiar estes dados diretamente para a instalacao principal.\n",
            encoding="utf-8")
        if output.exists() or output.is_symlink():
            raise ValueError("Destino passou a existir durante montagem")
        target.rename(output)

    report["status"] = "EXPERIMENTAL_COPY_ASSEMBLED_UNTESTED"
    report["output"] = str(output)
    report["rival_versions"] = pbs_report["versions"]
    report["source_connections_compiled"] = (
        connection_report["compiled_count"] if connection_report else 0)
    return report


def main(argv=None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--preview", type=Path, default=PREVIEW)
    cli.add_argument("--game", type=Path, default=ROOT / "game")
    cli.add_argument("--spec", type=Path, default=SPEC)
    cli.add_argument("--output", type=Path, default=OUTPUT)
    cli.add_argument("--with-connections", action="store_true",
                     help="Adicionar as conexoes reais remapeadas somente no PBS da copia piloto")
    args = cli.parse_args(argv)
    try:
        report = assemble(args.preview, args.game, args.output, read_json(args.spec),
                          with_connections=args.with_connections)
    except (ValueError, OSError, TypeError, KeyError, json.JSONDecodeError) as error:
        print("[JOHTO][BLOQUEADO] " + str(error), file=sys.stderr)
        return 2
    print("[JOHTO] Cópia experimental montada:", report["output"])
    print("[JOHTO] NÃO é VERIFIED_PLAYABLE. Verificar na engine antes de liberar rival ou menu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
