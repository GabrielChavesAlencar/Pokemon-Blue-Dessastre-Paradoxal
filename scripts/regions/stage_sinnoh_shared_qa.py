"""Install and optionally compile Sinnoh in a disposable Blue-Story copy."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import zlib

from prepare_sinnoh_shared import CANDIDATE, ROOT, shared
from install_sinnoh_experimental_windows import safe_path, scan_source
from install_sinnoh_qa_copy import jsonc
from scripts.android.package import compiled_region, REGION_START_PLUGIN, REGION_TRAVEL_PLUGIN
from scripts.launch_game import Marshal, RubyString, dump

QA_DIR = ".blue-work/sinnoh-shared-qa"
CACHE = "Data/PluginScripts.rxdata"
SCRIPTS = "Data/Scripts.rxdata"
NATIVE_RECEIPT = "Data/blue-sinnoh-shared-native-compile.txt"
START_RECEIPT = "Data/blue-sinnoh-shared-native-start.txt"


def engine_output(raw):
    return (raw or b"")[-4000:].decode("utf-8",errors="replace").replace("\0","")


def run_native_probe(game, patch, *, timeout):
    scripts = shared.safe_file(game,SCRIPTS)
    original = scripts.read_bytes()
    rows = Marshal(original).read()
    entry, = [row for row in rows if row[1] == b"Main"]
    source = zlib.decompress(entry[2]).decode("utf-8")
    entry[2] = RubyString(zlib.compress(patch(source).encode("utf-8")))
    shared.atomic(scripts,b"\x04\x08" + dump(rows))
    try:
        return subprocess.run([str(game/"Game.exe")],cwd=game,stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,timeout=timeout,check=False)
    except subprocess.TimeoutExpired as error:
        raise ValueError(f"Game.exe não concluiu o teste em {timeout}s.\n"+
                         engine_output(error.stdout)) from error
    finally:
        shared.atomic(scripts,original)


def compile_boot_script(source, token):
    needle = "    Compiler.main"
    if source.count(needle) != 1:
        raise ValueError("Ponto de entrada do compilador de Blue-Story desconhecido.")
    boot = "    PluginManager.runPlugins"
    if source.count(boot) != 1:
        raise ValueError("Ponto de entrada dos plugins de Blue-Story desconhecido.")
    source = source.replace(boot, '''    $DEBUG = true
    Object.send(:define_method,:pbPrintException) do |error|
      warn [error.class, error.message, *Array(error.backtrace)].join("\\n")
      exit! 1
    end
''' + boot)
    return source.replace(needle, f'''    begin
  {needle}
      GameData::Trainer.load
      GameData::Item.load
      raise "Sinnoh: missing compiled shared runtime or Barry teams" unless BlueSinnohSharedEvents.ready?
      Object.constants.grep(/\\ABlueSinnoh/).each do |name|
        handler = Object.const_get(name)
        handler.verify_compiled! if handler.respond_to?(:verify_compiled!)
      end
      File.binwrite("{NATIVE_RECEIPT}", "{token}")
    rescue StandardError, ScriptError => error
      warn [error.class, error.message, *Array(error.backtrace).first(12)].join("\\n")
      exit! 1
    end
    exit
''')


def compile_windows(game, token, map_ids):
    regional_data = [shared.MAP_INFOS,shared.TILESETS,shared.CONNECTIONS]
    regional_data.extend(f"Data/Map{mid:03d}.rxdata" for mid in map_ids)
    protected = {}
    for relative in regional_data:
        path = shared.safe_file(game,relative)
        protected[path] = path.read_bytes()
    try:
        result = run_native_probe(game,lambda source:compile_boot_script(source,token),timeout=360)
        receipt = shared.safe_file(game,NATIVE_RECEIPT)
        if result.returncode != 0 or not receipt.is_file() or receipt.read_text("ascii") != token:
            raise ValueError("O Game.exe não concluiu a compilação Sinnoh.\n" +
                             engine_output(result.stdout))
    finally:
        # Essentials may regenerate editor indexes and serialized map events.
        # Keep the verified authored Sinnoh events and the regional indexes.
        for path, content in protected.items():
            if not path.is_file() or path.read_bytes() != content:
                shared.atomic(path,content)
    cache = shared.safe_file(game,CACHE).read_bytes()
    for path in (shared.PLUGIN, REGION_START_PLUGIN, REGION_TRAVEL_PLUGIN):
        compiled_region(cache,Path(path).name,shared.safe_file(game,path).read_bytes())
    return shared.sha(cache)


def verify_native_start(game, manifest, token):
    expected = json.dumps([manifest[key] for key in ("start","arrival","agent")])
    def patch(source):
        source = source.replace("\r\n","\n")
        anchor = "    Game.set_up_system\n"
        if source.count(anchor) != 1:
            raise ValueError("Inicialização de Novo Jogo não reconhecida.")
        return source.replace(anchor,anchor+f'''
    begin
      start, arrival, agent = {expected}
      raise "Sinnoh ausente no Novo Jogo" unless BlueRegionStart.sinnoh_spawn == start &&
        BlueRegionStart.request_initial("SINNOH")
      Game.start_new
      regional = $PokemonGlobal.blue_regions
      raise "Região inicial incorreta" unless regional && regional["current"] == "SINNOH" && regional["initial"] == "SINNOH"
      raise "Quarto inicial incorreto" unless [$game_map.map_id,$game_player.x,$game_player.y] == start
      $map_factory = PokemonMapFactory.new(arrival[0])
      $game_player.moveto(arrival[1],arrival[2])
      2.times {{ BlueRegionTravel.attach_sinnoh_agent($game_map) }}
      agents = $game_map.events.values.select {{ |event| event.name == BlueRegionTravel::SINNOH_AGENT_NAME }}
      raise "Agente de Twinleaf ausente, deslocado ou duplicado" unless agents.length == 1 &&
        [$game_map.map_id,agents[0].x,agents[0].y] == agent
      File.binwrite("{START_RECEIPT}", "{token}")
    rescue StandardError, ScriptError => error
      warn [error.class, error.message, *Array(error.backtrace).first(12)].join("\\n")
      exit! 1
    end
    exit
''')
    receipt = shared.safe_file(game,START_RECEIPT)
    receipt.unlink(missing_ok=True)
    result = run_native_probe(game,patch,timeout=150)
    if result.returncode != 0 or not receipt.is_file() or receipt.read_text("ascii") != token:
        raise ValueError("O Game.exe não confirmou Novo Jogo e agente de Twinleaf.\n" +
                         engine_output(result.stdout))


def stage(project, *, base_game=None, compile_native=False):
    project = project.resolve()
    base = base_game.resolve() if base_game else project / "game"
    candidate = project / CANDIDATE
    target = project / QA_DIR
    for path in (target.parent,candidate,target):
        if path.is_symlink():
            raise ValueError("Caminho indireto reservado para QA de Sinnoh.")
    if target.exists():
        raise ValueError("Já existe uma cópia de QA. Preserve seus testes antes de preparar outra.")
    proof = json.loads(safe_path(candidate/"candidate.json").read_bytes())
    if proof.get("profile") != "BLUE_SINNOH_SHARED_CANDIDATE_V1" or proof.get("runtime_install_enabled") is not False:
        raise ValueError("O staging aceita somente um candidato de Sinnoh.")
    proof["profile"] = shared.QA_PROFILE
    shared.validate_manifest(proof,qa=True)
    for rel in (REGION_START_PLUGIN,REGION_TRAVEL_PLUGIN,
                "Plugins/ZZZZ Blue Story and Presentation/TitleKanto.rb"):
        expected = (project/"scripts/battle_polish"/Path(rel).name).read_text("utf-8")
        if shared.safe_file(base,rel).read_text("utf-8") != expected:
            raise ValueError("A base de QA precisa do script atualizado: " + rel)
    snapshot = scan_source(base)
    token = secrets.token_hex(12)
    with tempfile.TemporaryDirectory(prefix="sinnoh-shared-qa-",dir=target.parent) as tmp:
        root = Path(tmp) / "qa"
        game = root / "game"
        for rel, path in snapshot.items():
            dest = safe_path(game/rel)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,dest)
        config = jsonc(safe_path(game/"mkxp.json").read_text("utf-8-sig"))
        if any("save" in key.casefold() or "userdata" in key.casefold() for key in config):
            raise ValueError("A configuração base de saves impede isolar a cópia de QA.")
        config.update(dataPathApp="BlueStorySinnohSharedQA-"+token,
                      dataPathOrg="BlueStoryQA",windowTitle="Blue-Story Sinnoh QA")
        shared.atomic(game/"mkxp.json",(json.dumps(config,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
        manifest = root/"manifest-qa.json"
        proof_bytes = (json.dumps(proof,ensure_ascii=False,sort_keys=True)+"\n").encode("utf-8")
        shared.atomic(manifest,proof_bytes)
        shared.install_overlay(root,game,candidate/"world",manifest,qa=True)
        print("SINNOH_SHARED_WINDOWS_144_MAPS_INSTALLED_QA",flush=True)
        result = {"status":"STAGED_SHARED_QA", "maps":len(proof["map_ids"]),
                  "overlay_sha256":shared.sha(proof_bytes),
                  "base_mapinfos_sha256":proof["base"][shared.MAP_INFOS],
                  "commit_sha":os.environ.get("GITHUB_SHA"),
                  "windows_travel":False, "joiplay_travel":False}
        if compile_native:
            result["plugin_cache_sha256"] = compile_windows(game,result["overlay_sha256"],proof["map_ids"])
            result["compiler"] = "Windows Game.exe"
            verify_native_start(game,proof,result["overlay_sha256"])
            result.update(native_new_game=True,native_twinleaf_agent=True)
        shared.installed(game,qa=True)
        shared.atomic(root/"stage.json",(json.dumps(result,indent=2)+"\n").encode("utf-8"))
        root.rename(target)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--base-game",type=Path,help="Read-only base used by the candidate")
    parser.add_argument("--compile",action="store_true")
    args = parser.parse_args()
    print("SINNOH_SHARED_QA_STAGE",json.dumps(stage(args.project,base_game=args.base_game,
                                                   compile_native=args.compile)),flush=True)
