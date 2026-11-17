#!/usr/bin/env python3
"""S25 offline: valida ponte BlueMusic sem audio nem hooks nativos."""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/music"))
import audit_sinnoh_music_s24 as s24
MANIFEST=ROOT/"data/regions/sinnoh-music-s25.json"
BRIDGE=ROOT/"scripts/music/SinnohBlueMusicBridge.rb"
PRIORITY=["EXPLICIT_ENGINE","MANUAL_BLUE_MUSIC","VERIFIED_SINNOH","KEEP_NATIVE"]
POLICIES={
    "preserve_mute":True,"preserve_custom":True,"preserve_random":True,
    "no_cross_region":True,"no_global_hooks":True,"no_unlicensed_track":True,
    "restore_after_battle_by_engine":True
}
EXPECTED={
    "schema":1,"region":"SINNOH","stage":"S25",
    "status":"BRIDGE_OFFLINE_NOT_INSTALLED",
    "source_ch16":"data/regions/sinnoh-music-ch16.json",
    "source_s24":"data/regions/sinnoh-music-s24.json",
    "blue_music":"scripts/music/BlueMusic.rb",
    "bridge":"scripts/music/SinnohBlueMusicBridge.rb",
    "cue_count":46,"approved_tracks":[],"licensed_sources":[],
    "native_maps":[],"native_events":[],"compiled_bindings":[],
    "enabled":False,"installed":False,"autoplay":False,"audio_copied":False,
    "game_exe_tested":False,"joiplay_tested":False,"native_qa_approved":False,
    "priority":PRIORITY,"policies":POLICIES,
    "note":"Somente contrato de codigo; nenhum arquivo autorizado, mapa, evento ou hook compilado. Sem reproducao em Game.exe ou JoiPlay."
}
REQUIRED=(
    "module BlueSinnohMusicBridge","VERIFIED_NATIVE_SOURCES = {}.freeze",
    "def self.safe_manifest?(m)","def self.resolve(manifest,catalog,key,current_region:",
    "def self.native_ready?(manifest,key)","current_region=='SINNOH'",
    "blue_music.entry('map',map_id)","blue_music.entry('global',category)",
    "BlueSinnohMusicContracts.resolve(","DEFAULT"
)
BANNED=(
    "pbBGMPlay(","pbCueBGM(","pbMEPlay(","BlueMusic.install",
    "File.write(","File.open(","load_data(","EventHandlers.add(",
    "RPG::AudioFile.new(","def self.install","Object.prepend("
)

def fail(message):
    raise ValueError("SINNOH_S25_BLOCKED: "+message)

def audit(manifest,matrix,catalog,doc,blue,adapter,regions,bridge):
    proof=s24.audit(matrix,catalog,doc,blue,adapter,regions)
    if proof["scenario_count"]!=46 or proof["install_allowed"]:
        fail("fonte S24 invalida")
    if not isinstance(manifest,dict) or set(manifest)!=set(EXPECTED):
        fail("campos inesperados")
    for k,v in EXPECTED.items():
        if type(manifest[k]) is not type(v) or manifest[k]!=v:
            fail("fontes, direitos, hook ou QA ficticios: "+k)
    if not isinstance(bridge,str) or len(bridge)<700 or any(k not in bridge for k in REQUIRED):
        fail("API bridge incompleta")
    executable="\n".join(line for line in bridge.splitlines() if not line.lstrip().startswith("#"))
    if any(k in executable for k in BANNED):
        fail("bridge tentou tocar/instalar audio")
    if "SinnohBlueMusicBridge" in blue or "SinnohMusicContracts" in blue:
        fail("BlueMusic global adulterado")
    return {"region":"SINNOH","stage":"S25","status":EXPECTED["status"],
            "cues":46,"read_only":True,"music_installed":False,
            "tracks_verified":0,"native_bindings":0,"qa_native":False}

def run():
    return audit(
        json.loads(MANIFEST.read_text("utf-8")),
        json.loads(s24.FILES["matrix"].read_text("utf-8")),
        json.loads(s24.FILES["catalog"].read_text("utf-8")),
        s24.FILES["document"].read_text("utf-8"),
        s24.FILES["blue"].read_text("utf-8"),
        s24.FILES["adapter"].read_text("utf-8"),
        json.loads(s24.FILES["regions"].read_text("utf-8")),
        BRIDGE.read_text("utf-8")
    )

if __name__=="__main__":
    try:
        print(json.dumps(run(),ensure_ascii=False,indent=2))
        print("SINNOH_S25_BRIDGE_OK_OFFLINE")
    except (ValueError,OSError,TypeError,KeyError) as error:
        print(str(error),file=sys.stderr)
        sys.exit(2)
