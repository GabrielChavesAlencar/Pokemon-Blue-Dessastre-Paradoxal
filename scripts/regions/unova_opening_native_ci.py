"""Run the native opening-corridor check on a fresh GitHub Windows runner."""

import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

from audit_unova_a13_private_qa import no_symlink_ancestors
from install_sinnoh_qa_copy import jsonc
from stage_sinnoh_shared_qa import run_native_probe, engine_output
from unova_opening_stage import ENCOUNTERS_PBS, MAP_INFOS, OUTPUT, ROOT, STORY, TILESETS, encounters_pbs, write_overlay
from unova_original_opening import checksum
from server.ruby_marshal import loads
from stage import serialize

WORK = ROOT / ".blue-work/unova/ci"
GAME = WORK / "game"
PROBE = "Data/unova-opening-native-check.rb"
INPUT = "Data/unova-opening-native-input.dat"
RESULT = "Data/unova-opening-native-result.dat"
ERROR = "Data/unova-opening-native-error.txt"


def only_ci():
    if os.name != "nt" or os.environ.get("GITHUB_ACTIONS") != "true":
        raise ValueError("A execução nativa exige um runner Windows do GitHub Actions.")
    no_symlink_ancestors(GAME)


def convert_strings(value, conversion, source_type):
    if isinstance(value, source_type):
        return conversion(value)
    if isinstance(value, (list, tuple)):
        return [convert_strings(child, conversion, source_type) for child in value]
    if isinstance(value, dict):
        return {convert_strings(key, conversion, source_type): convert_strings(child, conversion, source_type)
                for key, child in value.items()}
    return value


def patch_main(source, *, compile_only):
    source = source.replace("\r\n", "\n")
    plugins = "    PluginManager.runPlugins\n"
    compiler = "    Compiler.main\n"
    ready = "    Game.set_up_system\n"
    if any(source.count(text) != 1 for text in (plugins, compiler, ready)):
        raise ValueError("Pontos de entrada da engine não reconhecidos.")
    source = source.replace(plugins, f'''    Object.send(:define_method, :pbPrintException) do |error|
      report = [error.class, error.message, *Array(error.backtrace).first(16)].join("\\n")
      File.binwrite("{ERROR}", report)
      warn report
      exit! 1
    end
''' + plugins)
    if compile_only:
        return source.replace(compiler, compiler + "    exit\n")
    return source.replace(compiler, "").replace(ready, ready + f'''
    begin
      load "{STORY}"
      load "{PROBE}"
      config = Marshal.load(File.binread("{INPUT}"))
      report = UnovaOpeningNativeCheck.run(config)
      File.binwrite("{RESULT}", Marshal.dump(report))
    rescue Exception => error
      pbPrintException(error)
    end
    exit
''')


def isolate_profile():
    path = GAME / "mkxp.json"
    config = jsonc(path.read_text(encoding="utf-8-sig"))
    if any("save" in key.casefold() or "userdata" in key.casefold() for key in config):
        raise ValueError("A base tem caminho de saves configurado fora do perfil QA.")
    config.update(dataPathApp="BlueUnovaOpeningQA-" + secrets.token_hex(12), dataPathOrg="BlueStoryQA")
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")


def run(android_manifest):
    only_ci()
    previous_outputs = (INPUT, RESULT, ERROR)
    if not (GAME / "Game.exe").is_file() or any((GAME / name).exists() for name in previous_outputs):
        raise ValueError("A cópia descartável precisa ser uma instalação nova de CI.")
    isolate_profile()
    encounters = GAME / ENCOUNTERS_PBS
    with encounters.open("xb") as stream:
        stream.write(encounters_pbs())
    compiled = run_native_probe(GAME, lambda source: patch_main(source, compile_only=True), timeout=360)
    if (compiled.returncode != 0 or b"Successfully compiled all game data" not in compiled.stdout
            or not (GAME / "Data/species.dat").is_file()):
        raise ValueError(f"Compilação da base QA falhou (saída {compiled.returncode}).\n"
                         + diagnostic(compiled))
    print("A engine compilou a base QA. Preparando a execução do corredor.", flush=True)
    config = write_overlay(ROOT, GAME, android_manifest)
    expected_base = {MAP_INFOS: config["baselines"]["windows_mapinfos_sha256"],
                     TILESETS: config["base_tilesets_sha256"]}
    payload = {}
    for name, digest in config["files_sha256"].items():
        path = GAME / name
        raw = (ROOT / OUTPUT / name).read_bytes()
        if checksum(raw) != digest:
            raise ValueError("O conteúdo do overlay mudou antes da aplicação.")
        if name == ENCOUNTERS_PBS:
            if path.read_bytes() != raw:
                raise ValueError("O PBS compilado diverge do overlay.")
            continue
        if ((name in expected_base and checksum(path.read_bytes()) != expected_base[name]) or
                (name not in expected_base and (path.exists() or path.is_symlink()))):
            raise ValueError("O conteúdo do overlay ou da base mudou antes da aplicação.")
        payload[path] = raw
    for path, raw in payload.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    (GAME / PROBE).write_bytes((ROOT / "scripts/regions/UnovaOpeningNativeCheck.rb").read_bytes())
    scenario = {key: config[key] for key in ("spawn", "map_ids", "doors", "journey", "fieldwork", "encounters")}
    (GAME / INPUT).write_bytes(serialize(convert_strings(scenario, str.encode, str)))
    result = run_native_probe(GAME, lambda source: patch_main(source, compile_only=False), timeout=240)
    if result.returncode != 0 or not (GAME / RESULT).is_file():
        raise ValueError(f"Game.exe não confirmou o corredor QA (saída {result.returncode}).\n"
                         + diagnostic(result))
    proof = convert_strings(loads((GAME / RESULT).read_bytes()), bytes.decode, bytes)
    if (proof["windows_game_exe"] is not True or len(proof["doors"]) != len(config["doors"])
            or proof["visited_map_ids"] != sorted(config["map_ids"].values())
            or proof["fieldwork"]["reported"] is not True or not proof["wild_encounter"]["selected"]):
        raise ValueError("Resultado nativo incompleto.")
    proof["revision"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    proof["map_ids"] = config["map_ids"]
    proof["overlay_files_sha256"] = config["files_sha256"]
    proof["android_reference"] = config["baselines"]["android"]
    (WORK / "windows-native-receipt.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print(f"Game.exe verificou {len(proof['doors'])} portas, missão, encontro e save/reload.")


def diagnostic(result):
    error = GAME / ERROR
    if error.is_file():
        return error.read_text(encoding="utf-8", errors="replace")
    return engine_output(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--android-manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        run(args.android_manifest)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
