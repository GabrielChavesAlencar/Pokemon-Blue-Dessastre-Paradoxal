"""Install and optionally compile Sinnoh in a disposable Blue-Story copy."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import zlib

from prepare_sinnoh_shared import CANDIDATE, ROOT, shared
from install_sinnoh_experimental_windows import scan_source
from install_sinnoh_qa_copy import jsonc
from scripts.android.package import compiled_region, REGION_START_PLUGIN, REGION_TRAVEL_PLUGIN
from scripts.launch_game import Marshal, RubyString, dump

QA_DIR = ".blue-work/sinnoh-shared-qa"
CACHE = "Data/PluginScripts.rxdata"
SCRIPTS = "Data/Scripts.rxdata"
NATIVE_RECEIPT = "Data/blue-sinnoh-shared-native-compile.txt"


def compile_windows(game, token):
    scripts = shared.safe_file(game,SCRIPTS)
    original = scripts.read_bytes()
    rows = Marshal(original).read()
    entry, = [row for row in rows if row[1] == b"Main"]
    source = zlib.decompress(entry[2]).decode("utf-8")
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
    source = source.replace(needle, needle + f'''
    GameData::Trainer.load
    GameData::Item.load
    raise "Sinnoh: missing compiled shared runtime or Barry teams" unless BlueSinnohSharedEvents.ready?
    Object.constants.grep(/\\ABlueSinnoh/).each do |name|
      handler = Object.const_get(name)
      handler.verify_compiled! if handler.respond_to?(:verify_compiled!)
    end
    File.binwrite("{NATIVE_RECEIPT}", "{token}")
    exit
''')
    entry[2] = RubyString(zlib.compress(source.encode("utf-8")))
    tiles = shared.safe_file(game,shared.TILESETS)
    protected_tiles = tiles.read_bytes()
    shared.atomic(scripts,b"\x04\x08" + dump(rows))
    try:
        result = subprocess.run([str(game/"Game.exe")],cwd=game,
                                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=360,check=False)
        receipt = shared.safe_file(game,NATIVE_RECEIPT)
        if result.returncode != 0 or not receipt.is_file() or receipt.read_text("ascii") != token:
            raise ValueError("O Game.exe não concluiu a compilação Sinnoh.\n" +
                             result.stdout[-4000:].decode("utf-8",errors="replace"))
    finally:
        shared.atomic(scripts,original)
        # Essentials may serialize a fresh editor tileset index during compile.
        # The imported map IDs use the previously verified append-only index.
        shared.atomic(tiles,protected_tiles)
    cache = shared.safe_file(game,CACHE).read_bytes()
    for path in (shared.PLUGIN, REGION_START_PLUGIN, REGION_TRAVEL_PLUGIN):
        compiled_region(cache,Path(path).name,shared.safe_file(game,path).read_bytes())
    return shared.sha(cache)


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
    proof = json.loads(shared.safe_file(candidate,"candidate.json").read_bytes())
    if proof.get("profile") != "BLUE_SINNOH_SHARED_CANDIDATE_V1" or proof.get("runtime_install_enabled") is not False:
        raise ValueError("O staging aceita somente um candidato de Sinnoh.")
    proof["profile"] = shared.QA_PROFILE
    shared.validate_manifest(proof,qa=True)
    snapshot = scan_source(base)
    token = secrets.token_hex(12)
    with tempfile.TemporaryDirectory(prefix="sinnoh-shared-qa-",dir=target.parent) as tmp:
        root = Path(tmp) / "qa"
        game = root / "game"
        for rel, path in snapshot.items():
            dest = shared.safe_file(game,rel)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,dest)
        config = jsonc(shared.safe_file(game,"mkxp.json").read_text("utf-8-sig"))
        if any("save" in key.casefold() or "userdata" in key.casefold() for key in config):
            raise ValueError("A configuração base de saves impede isolar a cópia de QA.")
        config.update(dataPathApp="BlueStorySinnohSharedQA-"+token,
                      dataPathOrg="BlueStoryQA",windowTitle="Blue-Story Sinnoh QA")
        shared.atomic(game/"mkxp.json",(json.dumps(config,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
        manifest = root/"manifest-qa.json"
        proof_bytes = (json.dumps(proof,ensure_ascii=False,sort_keys=True)+"\n").encode("utf-8")
        shared.atomic(manifest,proof_bytes)
        shared.install_overlay(root,game,candidate/"world",manifest,qa=True)
        result = {"status":"STAGED_SHARED_QA", "maps":len(proof["map_ids"]),
                  "overlay_sha256":shared.sha(proof_bytes), "windows_travel":False, "joiplay_travel":False}
        if compile_native:
            result["plugin_cache_sha256"] = compile_windows(game,result["overlay_sha256"])
            result["compiler"] = "Windows Game.exe"
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
