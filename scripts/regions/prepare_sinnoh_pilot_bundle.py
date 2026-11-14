#!/usr/bin/env python3
"""Assemble a PRIVATE, NOT-PLAYABLE Sinnoh QA overlay from verified stages.

Combines audited geometry, ORIGINAL Blue Twinleaf event overlay and Barry PBS
draft, plus original BlueSinnohPilot plugin. No installation into game/,
no save modification, no Game.exe/Scripts/System.rxdata copy, no ready marker,
no donor event script execution or public asset upload.

Requires actual reviewed map positions and hashes in a LOCAL event spec.
The committed template intentionally cannot pass this builder.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath

from build_sinnoh_twinleaf_events import MAPS, compile_events, read_json
from build_sinnoh_barry_pbs import PBS_TRAINERS, PBS_TYPE, READY_MARKER
from verify_sinnoh_barry_pbs import inspect as inspect_barry
from server.ruby_marshal import RubyObject, loads
from stage import serialize
from sinnoh_staging_transaction import stage_root

ROOT = Path(__file__).resolve().parents[2]
SHA = re.compile(r"[a-f0-9]{64}\Z")
MAP = re.compile(r"Data/Map([1-9][0-9]{2})\.rxdata\Z")
GRAPHIC = re.compile(r"Graphics/(?:Tilesets|Autotiles)/[A-Za-z0-9_. ()-]+\.png\Z")
PLUGIN_FILE = "Plugins/ZZZZZ Blue Sinnoh Intro/SinnohPilot.rb"
PLUGIN_META = "Plugins/ZZZZZ Blue Sinnoh Intro/meta.txt"
MAX_BYTES = 512 * 1024 * 1024


def fail(message: str) -> None:
    raise ValueError("[SINNOH BUNDLE] " + message)


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _safe_under(path: Path, base: Path, label: str) -> Path:
    path = Path(path).absolute()
    base = Path(base).absolute()
    if path == base or not path.is_relative_to(base):
        fail(f"{label} deve estar dentro de {base}")
    if not path.resolve().is_relative_to(base.resolve()) or any(
        parent.is_symlink() for parent in (path, *path.parents)
    ):
        fail(f"{label} contém link simbólico ou escapa do diretório")
    return path


def load_stage(project: Path, folder: Path, *, geometry: bool) -> dict[str, bytes]:
    base = stage_root(project)
    folder = _safe_under(folder, base, "Stage")
    manifest_path = folder / "stage-manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        fail("Manifesto transacional do stage ausente")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (not isinstance(manifest, dict)
            or (manifest.get("schema"), manifest.get("region"),
                manifest.get("mode"), manifest.get("may_install_into_game"),
                manifest.get("writes_to_main_game")) !=
               (1, "SINNOH", "LOCAL_STAGE_ONLY", False, False)):
        fail("Stage Sinnoh não é prévia local sem autorização de instalação")
    label, sha, rows = (manifest.get("label"), manifest.get("plan_sha256"),
                         manifest.get("files"))
    if (not isinstance(label, str) or not isinstance(sha, str)
            or not SHA.fullmatch(sha) or folder.name != f"{label}-{sha[:16]}"
            or not isinstance(rows, list) or not rows or len(rows) > 5000):
        fail("Identificação/quantidade de arquivos do stage inválida")
    plan = {"label": label, "files": rows}
    actual_signature = digest(json.dumps(plan, ensure_ascii=True, sort_keys=True,
                        separators=(",", ":")).encode("ascii"))
    if actual_signature != sha:
        fail("Assinatura SHA-256 da transação alterada")
    records = {}
    total = 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "bytes", "sha256"}:
            fail("Registro do stage inválido")
        rel, count, expected = row["path"], row["bytes"], row["sha256"]
        if (not isinstance(rel, str) or not isinstance(count, int)
                or count < 1 or not isinstance(expected, str) or not SHA.fullmatch(expected)
                or rel in records):
            fail("Arquivo duplicado ou hash inválido no stage")
        p = PurePosixPath(rel)
        if p.is_absolute() or ".." in p.parts or not (
            (geometry and (rel in ("Data/MapInfos.rxdata", "Data/Tilesets.rxdata")
                           or MAP.fullmatch(rel) or GRAPHIC.fullmatch(rel)))
            or (not geometry and MAP.fullmatch(rel))
        ):
            fail("Stage contém arquivo fora do escopo de geometria/eventos")
        target = folder.joinpath(*p.parts)
        if target.is_symlink() or not target.is_file():
            fail("Arquivo do stage ausente ou link simbólico")
        raw = target.read_bytes()
        if len(raw) != count or digest(raw) != expected:
            fail("Conteúdo de stage adulterado: " + rel)
        total += len(raw)
        if total > MAX_BYTES:
            fail("Stage ultrapassa limite de tamanho")
        records[rel] = raw
    actual_paths = set()
    for item in folder.rglob("*"):
        if item.is_symlink():
            fail("Stage possui link simbólico oculto")
        if item.is_file():
            actual_paths.add(item.relative_to(folder).as_posix())
    if actual_paths != set(records) | {"stage-manifest.json"}:
        fail("Stage contém arquivo extra ou não declarado")
    if geometry and not {"Data/MapInfos.rxdata", "Data/Tilesets.rxdata"} <= records.keys():
        fail("Stage de geometria sem MapInfos/Tilesets")
    return records


def native_map_ids(game: Path) -> set[int]:
    game = Path(game).absolute()
    data = game / "Data"
    if game.is_symlink() or data.is_symlink() or not data.is_dir():
        fail("game/Data local deve ser diretório normal e somente leitura")
    p = data / "MapInfos.rxdata"
    if p.is_symlink() or not p.is_file():
        fail("MapInfos nativo obrigatório")
    infos = loads(p.read_bytes())
    if (not isinstance(infos, dict) or any(
        type(key) is not int or key <= 0 or not isinstance(value, RubyObject)
        for key, value in infos.items()
    )):
        fail("MapInfos nativo inválido")
    occupied = set(infos)
    for f in data.iterdir():
        if f.is_symlink():
            fail("game/Data contém link simbólico")
        if match := re.fullmatch(r"Map([0-9]+)\.rxdata", f.name):
            occupied.add(int(match[1]))
    # Indices reserved in currently installed PBS can also block even when
    # a corresponding Data/MapNNN.rxdata has not yet been compiled.
    pbs = game / "PBS"
    if pbs.is_dir() and not pbs.is_symlink():
        for file in pbs.glob("*.txt"):
            if file.is_symlink():
                fail("PBS de referência contém link simbólico")
            if file.name.startswith(("encounters", "map_metadata")):
                for line in file.read_text("utf-8-sig").splitlines():
                    if match := re.match(r"^\s*\[\s*(\d+)\s*(?:,|\])", line):
                        occupied.add(int(match[1]))
            if file.name.startswith("map_connections"):
                for line in file.read_text("utf-8-sig").splitlines():
                    parts = line.split("#", 1)[0].split(",")
                    if len(parts) == 6:
                        for index in (0, 3):
                            if parts[index].strip().isdecimal():
                                occupied.add(int(parts[index].strip()))
    return occupied


def build(
    geometry_stage: Path, story_stage: Path, spec: dict, barry_draft: Path,
    game: Path, *, project: Path = ROOT,
) -> tuple[dict, dict[str, bytes]]:
    """Validate everything again, yielding only a NOT-PLAYABLE private overlay."""
    project = Path(project).absolute()
    game = Path(game).absolute()
    if (project.is_symlink() or not project.is_dir()
            or game.is_symlink() or not game.is_dir()
            or not game.resolve().is_relative_to(project.resolve())
            or game.resolve().is_relative_to((project / ".blue-work").resolve())):
        fail("Raiz do projeto ou jogo de referência inválidos")
    if geometry_stage.absolute() == story_stage.absolute():
        fail("Geometria e história exigem stages independentes")
    geom = load_stage(project, geometry_stage, geometry=True)
    story = load_stage(project, story_stage, geometry=False)
    if len(spec.get("maps", [])) != len(MAPS):
        fail("A história exige todos os nove mapas de Sinnoh")
    ids = [row.get("map_id") for row in spec["maps"]]
    if (any(type(mid) is not int or not 1 <= mid < 600 for mid in ids)
            or len(set(ids)) != len(MAPS)):
        fail("MapIDs de Sinnoh devem ser reais, únicos e menores que 600")
    proposed = {f"Data/Map{mid:03d}.rxdata" for mid in ids}
    geometry_maps = {path for path in geom if MAP.fullmatch(path)}
    if set(story) != proposed or not proposed.issubset(geometry_maps):
        fail("Stage autoral não corresponde exatamente aos nove mapas verificados")
    occupied = native_map_ids(game)
    if occupied & set(ids):
        fail("MapID Sinnoh já pertence ao game/Data/PBS instalado")
    # Verify native MapInfos data was not rewritten in the geometry preview.
    game_infos_path = game / "Data/MapInfos.rxdata"
    existing = loads(game_infos_path.read_bytes())
    merged = loads(geom["Data/MapInfos.rxdata"])
    if not isinstance(merged, dict) or set(existing) | set(ids) != set(merged):
        fail("MapInfos da geometria não preserva exatamente os mapas originais")
    for native_id, info in existing.items():
        if serialize(info) != serialize(merged[native_id]):
            fail("MapInfos original foi alterado na prévia")
    game_tiles_path = game / "Data/Tilesets.rxdata"
    if game_tiles_path.is_symlink() or not game_tiles_path.is_file():
        fail("Tilesets nativo ausente")
    original_tiles = loads(game_tiles_path.read_bytes())
    merged_tiles = loads(geom["Data/Tilesets.rxdata"])
    if (not isinstance(original_tiles, list) or not isinstance(merged_tiles, list)
            or len(original_tiles) > len(merged_tiles)
            or any(serialize(a) != serialize(b) for a, b in zip(original_tiles, merged_tiles))):
        fail("Tilesets do Blue foram alterados na prévia")
    # Recompile directly from the original stage and *local* verified spec.
    # This ensures the map contents in the story stage are EXACTLY what our
    # whitelisted original event compiler produces, not donor scripts.
    expected_report, rebuilt = compile_events(geometry_stage, spec, project=project)
    if set(rebuilt) != set(story) or any(rebuilt[name] != story[name] for name in rebuilt):
        fail("Stage de eventos diferente do compilador autoral auditado")
    source_script = project / "scripts/regions/SinnohPilot.rb"
    if source_script.is_symlink() or not source_script.is_file():
        fail("BlueSinnohPilot original não encontrado")
    plugin = source_script.read_bytes()
    if not (b"module BlueSinnohPilot" in plugin
            and b"choose_starter_from_ball" in plugin
            and b"RIVAL_READY" in plugin):
        fail("Plugin original incompleto")
    if (game / READY_MARKER).exists():
        fail("Marcador Barry já existe na instalação principal")
    draft = inspect_barry(barry_draft, game, root=project)
    outputs = {**geom, **story}
    for rel, expected in draft["files_sha256"].items():
        candidate = Path(barry_draft).absolute() / rel
        if candidate.is_symlink() or not candidate.is_file():
            fail("PBS do Barry ausente no draft")
        raw = candidate.read_bytes()
        if digest(raw) != expected:
            fail("PBS do Barry adulterado depois da auditoria")
        if rel in outputs:
            fail("Colisão entre recursos da geometria e PBS")
        outputs[rel] = raw
    outputs[PLUGIN_FILE] = plugin
    outputs[PLUGIN_META] = (
        b"Name = Blue Sinnoh Intro\nVersion = 0.1\n"
        b"Essentials = 21.1\nRequires = Blue Battle Presentation and Story\n"
        b"Scripts = SinnohPilot.rb\n"
    )
    if any(name.startswith(("Data/System", "Data/Scripts", "Data/blue-sinnoh-rival-ready"))
           or "SinnohPreview.rb" in name for name in outputs):
        fail("Overlay contém script legado, System, Scripts ou marcador indevido")
    report = {
        "schema": 1, "region": "SINNOH",
        "mode": "ISOLATED_QA_OVERLAY_DRY_RUN",
        "status": "NOT_PLAYABLE_PBS_NOT_COMPILED",
        "maps": len(ids), "map_ids": sorted(ids),
        "author_events": sum(expected_report["event_counts"].values()),
        "warps": expected_report["warp_count"],
        "physical_starter_balls": expected_report["starter_balls"],
        "barry_pbs_teams_statistically_verified": draft["teams_verified"],
        "game_data_physically_audited": True,
        "future_johto_hoenn_kanto_reservations_verified": False,
        "donor_script_events_copied": 0,
        "native_pbs_compiled": False,
        "native_game_or_saves_modified": False,
        "legacy_plugin_loaded": False,
        "runtime_playable": False,
        "ready_marker_created": False,
        "can_merge_into_main_game": False,
        "rights_and_redistribution_approved": False,
        "warning": "Only a local private integration overlay; no Game.exe, save profiles, compiled PBS, verified future reservations, or Windows/Android acceptance.",
        "files_sha256": {p: digest(v) for p, v in sorted(outputs.items())},
    }
    return report, outputs


def publish(project: Path, destination: Path, report: dict, outputs: dict[str, bytes]) -> dict:
    """Publish only to a NEW directory under .blue-work; no overwrite."""
    project = Path(project).absolute()
    work = project / ".blue-work"
    output = _safe_under(destination, work, "Pacote privado")
    if not work.is_dir() or work.is_symlink() or output.exists() or output.is_symlink():
        fail("Workspace indisponível ou destino já existe")
    if not outputs or set(outputs) != set(report["files_sha256"]):
        fail("Relatório não corresponde aos arquivos de preparação")
    total = sum(len(raw) for raw in outputs.values())
    if total > MAX_BYTES:
        fail("Pacote excede limite de tamanho")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".sinnoh-assembly-", dir=output.parent))
    try:
        for rel, contents in sorted(outputs.items()):
            p = PurePosixPath(rel)
            if p.is_absolute() or ".." in p.parts or not isinstance(contents, bytes):
                fail("Arquivo de saída inválido")
            file = temp.joinpath(*p.parts)
            file.parent.mkdir(parents=True, exist_ok=True)
            with file.open("xb") as fp:
                fp.write(contents)
                fp.flush()
                os.fsync(fp.fileno())
            if digest(file.read_bytes()) != report["files_sha256"][rel]:
                fail("Hash do pacote mudou durante montagem")
        (temp / "sinnoh-qa-overlay-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if output.exists():
            fail("Destino foi criado durante o preparo")
        temp.rename(output)
    except BaseException:
        if temp.exists():
            shutil.rmtree(temp)
        raise
    return {**report, "private_output": str(output), "created": True}


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--geometry-stage", required=True, type=Path)
    cli.add_argument("--story-stage", required=True, type=Path)
    cli.add_argument("--spec", required=True, type=Path)
    cli.add_argument("--barry-draft", required=True, type=Path)
    cli.add_argument("--game", required=True, type=Path)
    cli.add_argument("--output", type=Path, default=ROOT / ".blue-work/sinnoh-qa-overlay")
    cli.add_argument("--publish", action="store_true",
                     help="Opt-in: create a new, local-only overlay under .blue-work")
    args = cli.parse_args()
    try:
        spec = read_json(args.spec)
        report, outputs = build(
            args.geometry_stage, args.story_stage, spec, args.barry_draft,
            args.game,
        )
        if args.publish:
            report = publish(ROOT, args.output, report, outputs)
        else:
            report = {**report, "created": False, "private_output": None}
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        print("SINNOH_BUNDLE_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
