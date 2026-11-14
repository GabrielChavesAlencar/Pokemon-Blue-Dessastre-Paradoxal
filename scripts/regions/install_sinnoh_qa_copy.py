#!/usr/bin/env python3
"""Build a PRIVATE Sinnoh native QA copy with independent save identifiers.

Requires an already assembled and hashed private Sinnoh overlay. Does NOT
approve gameplay, rights, release, actual compilation or Barry battle. Creates
no ready marker. The Game.exe must be launched only by a local tester after
reviewing the QA folder. Never touches the native game or its saves.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
import uuid
import zlib
from pathlib import Path, PurePosixPath

from johto_qa import index_base, safe_path, SOURCE_FILES, COPY_DIRS
from johto_qa import SYSTEM_CLASSES
from prepare_sinnoh_pilot_bundle import ROOT, digest, _safe_under
from server.ruby_marshal import RubyObject, loads
from stage import serialize
from pilot import SYSTEM_CLASSES as SYSTEM_CLASSES_NATIVE

# The same Essentials scripts-array roundtrip used by private Johto QA.
sys.path.insert(0, str(ROOT / "scripts/official_rules"))
from prepare_restore import Marshal, RubyString, dump

PROFILE = re.compile(r"[a-f0-9]{12}\Z")
SHA = re.compile(r"[a-f0-9]{64}\Z")
START_PLUGIN = "Plugins/ZZZZZ Blue Sinnoh QA Start/SinnohQAStart.rb"
START_META = "Plugins/ZZZZZ Blue Sinnoh QA Start/meta.txt"
QA_META = "Sinnoh qa.json"
COMPILE_REQUEST = "Data/blue-sinnoh-qa-compile-request.txt"
COMPILED = "Data/blue-sinnoh-qa-compiled.txt"
COMPILE_ERROR = "Data/blue-sinnoh-qa-compile-error.txt"
BARRY_READY = "Data/blue-sinnoh-rival-ready.txt"
MAX_FILES = 30000
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 4 * 1024 * 1024 * 1024


def fail(message: str):
    raise ValueError("[SINNOH QA INSTALL] " + message)


def load_overlay(folder: Path, *, project: Path) -> tuple[dict, dict[str, bytes]]:
    work = project / ".blue-work"
    folder = _safe_under(folder, work, "Overlay")
    report_file = folder / "sinnoh-qa-overlay-report.json"
    if report_file.is_symlink() or not report_file.is_file():
        fail("Relatório privado de Sinnoh ausente")
    report = json.loads(report_file.read_text(encoding="utf-8"))
    if (not isinstance(report, dict) or
            (report.get("schema"), report.get("region"), report.get("mode"),
             report.get("status"), report.get("runtime_playable"),
             report.get("can_merge_into_main_game"),
             report.get("ready_marker_created")) != (
                1, "SINNOH", "ISOLATED_QA_OVERLAY_DRY_RUN",
                "NOT_PLAYABLE_PBS_NOT_COMPILED", False, False, False)):
        fail("Overlay não é o pacote privado não jogável auditado")
    hashes = report.get("files_sha256")
    if not isinstance(hashes, dict) or not hashes or len(hashes) > MAX_FILES:
        fail("Overlay sem inventário SHA-256 completo")
    if (report.get("maps") != 9 or report.get("warps") != 16
            or report.get("author_events") != 24
            or report.get("barry_pbs_teams_statistically_verified") != 3
            or sorted(report.get("physical_starter_balls", [])) !=
                    ["CHIMCHAR", "PIPLUP", "TURTWIG"]):
        fail("Sinnoh sem os 9 mapas, 24 eventos ou 3 PBS originais")
    blobs: dict[str, bytes] = {}
    total = 0
    casenames = set()
    for rel, expected in hashes.items():
        if not isinstance(rel, str) or not isinstance(expected, str) or not SHA.fullmatch(expected):
            fail("Entrada de hash inválida")
        path = PurePosixPath(rel)
        if (path.is_absolute() or len(path.parts) < 2
                or ".." in path.parts or "\\" in rel or ":" in rel
                or rel.casefold() in casenames):
            fail("Nome de arquivo inseguro ou colisão no overlay")
        casenames.add(rel.casefold())
        if not (
            (rel.startswith("Data/Map") and re.fullmatch(r"Data/Map(?:0[0-9]{2}|[1-5][0-9]{2}|Infos)\.rxdata", rel))
            or rel == "Data/Tilesets.rxdata"
            or rel in ("PBS/trainer_types_sinnoh_barry.txt", "PBS/trainers_sinnoh_barry.txt")
            or re.fullmatch(r"Graphics/(?:Tilesets|Autotiles)/[A-Za-z0-9_ .()-]+\.png", rel)
            or rel in ("Plugins/ZZZZZ Blue Sinnoh Intro/meta.txt",
                       "Plugins/ZZZZZ Blue Sinnoh Intro/SinnohPilot.rb")
        ) or rel == "Data/Map000.rxdata":
            fail("Arquivo fora da whitelist de Sinnoh: " + rel)
        p = folder.joinpath(*path.parts)
        if p.is_symlink() or not p.is_file():
            fail("Arquivo faltando ou link em overlay: " + rel)
        if p.stat().st_size > MAX_FILE_BYTES:
            fail("Arquivo do overlay grande demais")
        blob = p.read_bytes()
        if digest(blob) != expected:
            fail("Overlay adulterado: " + rel)
        total += len(blob)
        if total > MAX_TOTAL_BYTES:
            fail("Overlay excede limite permitido")
        blobs[rel] = blob
    actual = set()
    for f in folder.rglob("*"):
        if f.is_symlink():
            fail("Overlay contém symlink")
        if f.is_file():
            actual.add(f.relative_to(folder).as_posix())
    if actual != set(blobs) | {"sinnoh-qa-overlay-report.json"}:
        fail("Overlay contém arquivos extras ou ausentes")
    expected = {
        "Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
        "PBS/trainers_sinnoh_barry.txt", "PBS/trainer_types_sinnoh_barry.txt",
        "Plugins/ZZZZZ Blue Sinnoh Intro/SinnohPilot.rb",
        "Plugins/ZZZZZ Blue Sinnoh Intro/meta.txt",
    }
    if not expected.issubset(blobs):
        fail("Overlay não inclui todos os arquivos obrigatórios")
    return report, blobs


def jsonc(content: str) -> dict:
    # mkxp accepts JSON comments and trailing commas. Preserve literal // inside URLs.
    stripped = re.sub(r'"(?:[^"\\]|\\.)*"|//[^\r\n]*',
                      lambda m: "" if m[0].startswith("//") else m[0], content)
    stripped = re.sub(r'"(?:[^"\\]|\\.)*"|,(?=\s*[}\]])',
                      lambda m: "" if m[0] == "," else m[0], stripped)
    result = json.loads(stripped)
    if not isinstance(result, dict):
        fail("mkxp.json precisa ser um objeto")
    return result


def unique_save_configs(base: Path, token: str) -> tuple[bytes, bytes, dict]:
    if not PROFILE.fullmatch(token):
        fail("Identificador de perfil precisa ter 12 hexadecimais")
    config_file = base / "mkxp.json"
    ini_file = base / "Game.ini"
    if any(x.is_symlink() or not x.is_file() for x in (config_file, ini_file)):
        fail("Game.ini/mkxp.json ausentes ou symlinks")
    original_config = jsonc(config_file.read_text("utf-8-sig"))
    if any("save" in key.casefold() or "userdata" in key.casefold()
           for key in original_config):
        fail("mkxp tem configuração de salvamento própria; isolamento não provado")
    title = "Sinnoh QA " + token
    app = "Sinnoh-QA-" + token
    org = "Dessastre-Sinnoh-QA-" + token
    if (app == original_config.get("dataPathApp") or
            org == original_config.get("dataPathOrg")):
        fail("Perfil QA coincide com o jogo principal")
    config = dict(original_config)
    config.update(windowTitle=title, dataPathApp=app, dataPathOrg=org)
    ini = ini_file.read_text("utf-8-sig")
    ini, count = re.subn(r"(?m)^Title=[^\r\n]*", "Title=" + title, ini)
    if count != 1:
        fail("Game.ini deve conter um Title válido único")
    if "Title=" + title in ini_file.read_text("utf-8-sig"):
        fail("Game.ini já usa o perfil QA")
    return (
        (json.dumps(config, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        ini.encode("utf-8"),
        {"title": title, "dataPathApp": app, "dataPathOrg": org},
    )


def compile_boot(blob: bytes) -> bytes:
    rows = Marshal(blob).read()
    matches = [row for row in rows if isinstance(row, list) and len(row) >= 3
               and row[1] == b"Main"]
    if len(matches) != 1:
        fail("Bootstrap nativo Main ausente ou duplicado")
    main = matches[0]
    source = zlib.decompress(main[2]).decode("utf-8")
    before, compiler = "    PluginManager.runPlugins", "    Compiler.main"
    if (source.count(before) != 1 or source.count(compiler) != 1 or
            source.index(before) >= source.index(compiler) or
            "blue_sinnoh_qa_compile" in source):
        fail("Bootstrap nativo não é um Main Essentials conhecido e limpo")
    hook = """    if File.file?("Sinnoh qa.json") && File.file?("Data/blue-sinnoh-qa-compile-request.txt")
      $blue_sinnoh_qa_compile = true
      $DEBUG = true
      %w[PluginScripts.rxdata trainers.dat].each do |name|
        path = "Data/#{name}"
        File.delete(path) if File.file?(path)
      end
      Object.send(:define_method, :pbPrintException) do |error|
        File.write("Data/blue-sinnoh-qa-compile-error.txt", error.full_message)
        exit! 1
      end
    end
"""
    verify = """    if $blue_sinnoh_qa_compile
      begin
        GameData::Trainer.load
        valid = (0..2).all? { |v| GameData::Trainer.exists?(:BLUE_SINNOH_RIVAL, "Barry", v) }
        raise "Sinnoh QA: tres equipes PBS Barry ausentes" unless valid
        File.write("Data/blue-sinnoh-qa-compiled.txt",
                   File.read("Data/blue-sinnoh-qa-compile-request.txt").strip)
        File.delete("Data/blue-sinnoh-qa-compile-request.txt")
      rescue StandardError => error
        pbPrintException(error)
      end
      exit
    end
"""
    source = source.replace(before, hook + before).replace(compiler, compiler + "\n" + verify)
    main[2] = RubyString(zlib.compress(source.encode("utf-8")))
    return b"\x04\x08" + dump(rows)


def prepare(base: Path, overlay_dir: Path, spec: dict, *,
            token: str, project: Path = ROOT) -> tuple[dict, dict[str, bytes], dict[str, str]]:
    project = Path(project).absolute()
    base = Path(base).absolute()
    if (project.is_symlink() or not project.is_dir() or base.is_symlink()
            or base != project / "game"
            or (project / ".blue-work").is_symlink()):
        fail("Usar somente a base game/ deste projeto; nunca outro piloto")
    native = index_base(base)
    overlay_report, overlay = load_overlay(overlay_dir, project=project)
    if (base / BARRY_READY).exists():
        fail("Marcador Barry já existe em game/ principal")
    expected_ids = set(overlay_report.get("geometry_all_map_ids", []))
    if (not expected_ids or any(type(x) is not int or not 1 <= x < 600
                                for x in expected_ids)):
        fail("IDs auditados do overlay inválidos")
    # Every staged map must be genuinely NEW to the base.
    overlay_maps = {int(m.group(1)) for name in overlay
                    if (m := re.fullmatch(r"Data/Map([0-9]{3})\.rxdata", name))}
    if overlay_maps != expected_ids:
        fail("Mapa de overlay não bate com o inventário de IDs")
    from prepare_sinnoh_pilot_bundle import native_map_ids
    if overlay_maps & native_map_ids(base):
        fail("Overlay tenta sobrescrever um MapID da base")
    whitelist_replace = {"Data/MapInfos.rxdata", "Data/Tilesets.rxdata"}
    fold = {p.casefold(): p for p in native}
    if len(fold) != len(native):
        fail("Nomes da base colidem ignorando maiúsculas")
    for rel in overlay:
        prior = fold.get(rel.casefold())
        if prior and (prior != rel or rel not in whitelist_replace):
            fail("Overlay sobrescreveria arquivo já existente: " + rel)
    if (not isinstance(spec, dict) or spec.get("region") != "SINNOH"):
        fail("Especificação local Sinnoh inválida")
    start = spec.get("start")
    if not isinstance(start, dict) or start.get("symbol") != "SINNOH_PLAYER_BEDROOM":
        fail("Spawn deve começar no quarto do jogador")
    if (start.get("verified_position") is not True or
            start.get("passability_verified") is not True):
        fail("Spawn sem verificação de passabilidade")
    start_point = [start.get("map_id"), start.get("x"), start.get("y")]
    if (any(type(v) is not int for v in start_point)
            or start_point[0] not in overlay_maps):
        fail("Spawn precisa ter MapID e coordenadas reais no overlay")
    start_map = loads(overlay[f"Data/Map{start_point[0]:03d}.rxdata"])
    if not isinstance(start_map, RubyObject) or start_map.name != "RPG::Map":
        fail("Mapa de spawn não contém RPG::Map")
    w, h = (start_map.attrs.get("@width"), start_map.attrs.get("@height"))
    if (not all(type(v) is int for v in (w, h))
            or not 0 <= start_point[1] < w
            or not 0 <= start_point[2] < h):
        fail("Spawn fora dos limites do mapa real")
    if start_map.attrs.get("@events") is None:
        fail("Mapa inicial não contém eventos auditados")
    existing = loads((base / "Data/System.rxdata").read_bytes())
    if not isinstance(existing, RubyObject) or existing.name != "RPG::System":
        fail("System.rxdata da base inválido")
    system = loads((base / "Data/System.rxdata").read_bytes())
    system.attrs.update(dict(zip(
        ("@start_map_id", "@start_x", "@start_y"), start_point)))
    script_blob = (base / "Data/Scripts.rxdata").read_bytes()
    new_script = compile_boot(script_blob)
    mkxp, game_ini, profile = unique_save_configs(base, token)
    output = dict(overlay)
    output["Data/System.rxdata"] = serialize(system, SYSTEM_CLASSES_NATIVE)
    output["Data/Scripts.rxdata"] = new_script
    output["mkxp.json"] = mkxp
    output["Game.ini"] = game_ini
    start_source = project / "scripts/regions/SinnohQAStart.rb"
    if start_source.is_symlink() or not start_source.is_file():
        fail("Ruby isolado de início Sinnoh QA ausente")
    output[START_PLUGIN] = start_source.read_bytes()
    output[START_META] = (
        b"Name = Blue Sinnoh QA Start\nVersion = 0.1\n"
        b"Essentials = 21.1\nRequires = Blue Sinnoh Intro\n"
        b"Scripts = SinnohQAStart.rb\n"
    )
    # Never embed a ready marker in output. Compile request triggers a one-shot
    # native compiler and the compiled proof is generated ONLY by the QA Game.exe.
    token_sha = digest(
        (token + overlay_report["files_sha256"]["Data/MapInfos.rxdata"] +
         overlay_report["files_sha256"]["PBS/trainers_sinnoh_barry.txt"]).encode("ascii"))
    output[COMPILE_REQUEST] = (token_sha + "\n").encode("ascii")
    protected = {
        "Data/MapInfos.rxdata", "Data/System.rxdata",
        f"Data/Map{start_point[0]:03d}.rxdata",
        "PBS/trainer_types_sinnoh_barry.txt", "PBS/trainers_sinnoh_barry.txt",
    }
    meta = {
        "schema": 1, "kind": "ISOLATED_SINNOH_QA", "region": "SINNOH",
        "profile": profile, "start": start_point,
        "compile_token": token_sha,
        "file_sha256": {p: digest(output[p]) for p in sorted(protected)},
        "geometry_total_maps": len(overlay_maps),
        "intro_maps": 9, "event_count": 24, "warps": 16,
        "starter_balls": ["CHIMCHAR", "PIPLUP", "TURTWIG"],
        "barry_versions": [0, 1, 2],
        "runtime_playable": False,
        "native_pbs_compiled": False,
        "marker_created": False,
        "source_rights_verified": False,
        "android_tested": False,
        "may_release": False,
        "note": "Private QA copy; first Game.exe run is compilation only. No Barry ready marker created.",
    }
    output[QA_META] = (json.dumps(meta, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if any(key in output for key in (COMPILED, COMPILE_ERROR, BARRY_READY)):
        fail("Overlay contém marcador que seria criado prematuramente")
    report = {
        "schema": 1, "region": "SINNOH",
        "mode": "ISOLATED_QA_INSTALL_PLAN",
        "copy_only": True, "native_compile_required": True,
        "can_run_first_compilation_only": True,
        "save_isolation": profile,
        "save_migration": False,
        "native_files": len(native),
        "overlay_files": len(output),
        "start": start_point,
        "compile_request_token_sha256": token_sha,
        "base_file_hashes": native,
        "overlay_file_hashes": {k: digest(v) for k, v in sorted(output.items())},
        "runtime_playable": False,
        "can_install_into_main_game": False,
        "source_rights_verified": False,
        "verified_native_battle": False,
        "ready_marker_created": False,
        "current_main_game_or_saves_modified": False,
    }
    return report, output, native


def install(project: Path, base: Path, output: Path, report: dict,
            overlay: dict[str, bytes], native: dict[str, str]) -> dict:
    project = Path(project).absolute()
    base = Path(base).absolute()
    dest = _safe_under(output, project / ".blue-work", "Instalação QA")
    if dest.exists() or dest.is_symlink():
        fail("Destino QA já existe; recusar sobrescrita de uma instalação ou saves")
    if dest in base.parents or base in dest.parents:
        fail("Instalação QA não pode usar a pasta do jogo principal")
    work = project / ".blue-work"
    work.mkdir(exist_ok=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".sinnoh-qa-pending-", dir=dest.parent))
    try:
        # Johto's baseline index explicitly excludes save files and backups.
        for name, expected in sorted(native.items()):
            src = base / name
            if src.is_symlink() or not src.is_file() or digest(src.read_bytes()) != expected:
                fail("Base mudou durante a cópia: " + name)
            to = temp / name
            to.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, to)
            if digest(to.read_bytes()) != expected:
                fail("Falha de cópia base: " + name)
        backup = temp / "_sinnoh_qa_originals"
        for name, content in sorted(overlay.items()):
            if name in native:
                target = backup / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(temp / name, target)
                if digest(target.read_bytes()) != native[name]:
                    fail("Backup de arquivo original falhou")
            to = temp / name
            to.parent.mkdir(parents=True, exist_ok=True)
            with to.open("wb") as fp:
                fp.write(content)
                fp.flush()
                os.fsync(fp.fileno())
            if digest(to.read_bytes()) != report["overlay_file_hashes"][name]:
                fail("Arquivo do QA alterado durante escrita: " + name)
        (temp / "sinnoh-qa-transaction.json").write_text(
            json.dumps({
                "schema": 1, "kind": "SINNOH_QA_PRIVATE_TRANSACTION",
                "base_sha256": digest(json.dumps(native, sort_keys=True).encode("ascii")),
                "file_sha256": report["overlay_file_hashes"],
                "save_isolation": report["save_isolation"],
                "runtime_playable": False,
            }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if dest.exists() or dest.is_symlink():
            fail("Destino QA criado em paralelo")
        temp.rename(dest)
    except BaseException:
        if temp.exists():
            shutil.rmtree(temp)
        raise
    return {**report, "created": True, "qa_directory": str(dest)}


def verify(qa: Path, *, project: Path = ROOT) -> dict:
    qa = _safe_under(qa, Path(project).absolute() / ".blue-work", "Instalação QA")
    proof_file = qa / QA_META
    trans_file = qa / "sinnoh-qa-transaction.json"
    if any(p.is_symlink() or not p.is_file() for p in (proof_file, trans_file)):
        fail("Provas do instalador QA ausentes")
    proof = json.loads(proof_file.read_text("utf-8"))
    trans = json.loads(trans_file.read_text("utf-8"))
    if (proof.get("kind") != "ISOLATED_SINNOH_QA" or proof.get("region") != "SINNOH"
            or trans.get("kind") != "SINNOH_QA_PRIVATE_TRANSACTION"):
        fail("Não é instalação criada pelo instalador de Sinnoh")
    profile = proof.get("profile")
    if not isinstance(profile, dict) or not all(
        isinstance(profile.get(k), str) and "Sinnoh" in profile[k]
        for k in ("dataPathApp", "dataPathOrg")
    ):
        fail("Perfil de save separado ausente")
    mkxp = jsonc((qa / "mkxp.json").read_text("utf-8"))
    if any(mkxp.get(k) != profile[k] for k in ("dataPathApp", "dataPathOrg")):
        fail("Configuração de saves foi alterada")
    ini = (qa / "Game.ini").read_text("utf-8-sig")
    if ini.count("Title=" + profile["title"]) != 1:
        fail("Game.ini não corresponde ao QA isolado")
    for rel, expected in proof["file_sha256"].items():
        file = qa / rel
        if file.is_symlink() or not file.is_file() or digest(file.read_bytes()) != expected:
            fail("Arquivo protegido no QA foi alterado: " + rel)
    if (qa / BARRY_READY).exists():
        fail("Marcador de Barry não pode ser criado antes da QA manual de gameplay")
    compiled = qa / COMPILED
    errors = qa / COMPILE_ERROR
    if errors.exists():
        fail("Compilação nativa anterior retornou erro; inspecione o log local")
    compiled_ok = (
        compiled.is_file() and not compiled.is_symlink()
        and compiled.read_text("ascii").strip() == proof["compile_token"]
    )
    if compiled.is_file() and not compiled_ok:
        fail("Prova de compilação nativa não corresponde ao QA")
    pending = (qa / COMPILE_REQUEST).exists()
    if compiled_ok and pending:
        fail("Compilação marcada como concluída mas pedido ainda está pendente")
    return {
        "region": "SINNOH", "mode": "QA_READ_ONLY_VERIFICATION",
        "save_profile_isolated_in_config": True,
        "compiled_marker_present": compiled_ok,
        "compile_request_pending": pending,
        "python_verified_trainer_battle": False,
        "starter_events_accepted_in_game": False,
        "gameplay_save_reload_verified": False,
        "android_verified": False,
        "barry_ready_marker_present": False,
        "ready_to_launch_for_manual_testing": compiled_ok,
        "playable_approved": False,
    }


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--game", type=Path, default=ROOT / "game")
    cli.add_argument("--overlay", type=Path, help="pasta privada de overlay")
    cli.add_argument("--spec", type=Path, help="JSON local auditado de Twinleaf")
    cli.add_argument("--output", type=Path, help="pasta NOVA .blue-work/sinnoh-qa-...")
    cli.add_argument("--install", action="store_true", help="criar cópia QA, nunca no game/")
    cli.add_argument("--verify", type=Path, help="apenas verificar instalação QA anterior")
    args = cli.parse_args()
    try:
        if args.verify is not None:
            result = verify(args.verify)
        else:
            if args.overlay is None or args.spec is None:
                fail("--overlay e --spec são obrigatórios para preparar a cópia")
            token = secrets.token_hex(6)
            report, files, native = prepare(
                args.game, args.overlay, json.loads(args.spec.read_text("utf-8")),
                token=token)
            if args.install:
                output = args.output or ROOT / ".blue-work" / ("game-sinnoh-qa-" + token)
                result = install(ROOT, args.game, output, report, files, native)
            else:
                result = {**report, "created": False,
                          "qa_directory": None}
    except (ValueError, OSError, KeyError, TypeError, UnicodeError, zlib.error) as exc:
        print("SINNOH_QA_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
