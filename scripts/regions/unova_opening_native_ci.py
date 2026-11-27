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
from unova_opening_stage import ROOT, MAP_INFOS, TILESETS, write_overlay, OUTPUT
from unova_original_opening import checksum

WORK = ROOT / ".blue-work/unova/ci"
GAME = WORK / "game"
PROBE = "Data/unova-opening-native-check.rb"
INPUT = "Data/unova-opening-native-input.json"
RESULT = "Data/unova-opening-native-result.json"
COMPILED = "Data/unova-opening-base-compiled.txt"
ERROR = "Data/unova-opening-native-error.txt"


def only_ci():
    if os.name != "nt" or os.environ.get("GITHUB_ACTIONS") != "true":
        raise ValueError("A execução nativa exige um runner Windows do GitHub Actions.")
    no_symlink_ancestors(GAME)


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
        return source.replace(compiler, compiler + f'''
    GameData::Species.load
    File.binwrite("{COMPILED}", "UNOVA_QA_BASE_COMPILED")
    exit
''')
    return source.replace(compiler, "").replace(ready, ready + f'''
    begin
      require "json"
      load "{PROBE}"
      config = JSON.parse(File.binread("{INPUT}"))
      report = UnovaOpeningNativeCheck.run(config)
      File.binwrite("{RESULT}", JSON.generate(report))
    rescue StandardError, ScriptError => error
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
    previous_outputs = (INPUT, RESULT, COMPILED, ERROR)
    if not (GAME / "Game.exe").is_file() or any((GAME / name).exists() for name in previous_outputs):
        raise ValueError("A cópia descartável precisa ser uma instalação nova de CI.")
    isolate_profile()
    compiled = run_native_probe(GAME, lambda source: patch_main(source, compile_only=True), timeout=360)
    marker = GAME / COMPILED
    if compiled.returncode != 0 or not marker.is_file() or marker.read_bytes() != b"UNOVA_QA_BASE_COMPILED":
        raise ValueError(f"Compilação da base QA falhou (saída {compiled.returncode}).\n"
                         + diagnostic(compiled))
    config = write_overlay(ROOT, GAME, android_manifest)
    expected_base = {MAP_INFOS: config["baselines"]["windows_mapinfos_sha256"],
                     TILESETS: config["base_tilesets_sha256"]}
    payload = {}
    for name, digest in config["files_sha256"].items():
        path = GAME / name
        raw = (ROOT / OUTPUT / name).read_bytes()
        if (checksum(raw) != digest or
                (name in expected_base and checksum(path.read_bytes()) != expected_base[name]) or
                (name not in expected_base and (path.exists() or path.is_symlink()))):
            raise ValueError("O conteúdo do overlay ou da base mudou antes da aplicação.")
        payload[path] = raw
    for path, raw in payload.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    (GAME / PROBE).write_bytes((ROOT / "scripts/regions/UnovaOpeningNativeCheck.rb").read_bytes())
    (GAME / INPUT).write_text(json.dumps(config), encoding="utf-8")
    result = run_native_probe(GAME, lambda source: patch_main(source, compile_only=False), timeout=240)
    if result.returncode != 0 or not (GAME / RESULT).is_file():
        raise ValueError(f"Game.exe não confirmou o corredor QA (saída {result.returncode}).\n"
                         + diagnostic(result))
    proof = json.loads((GAME / RESULT).read_bytes())
    if (proof["windows_game_exe"] is not True or len(proof["doors"]) != len(config["doors"])
            or proof["visited_map_ids"] != sorted(config["map_ids"].values())):
        raise ValueError("Resultado nativo incompleto.")
    proof["revision"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    proof["map_ids"] = config["map_ids"]
    proof["overlay_files_sha256"] = config["files_sha256"]
    proof["android_reference"] = config["baselines"]["android"]
    (WORK / "windows-native-receipt.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print(f"Game.exe verificou {len(proof['doors'])} portas e save/reload.")


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
