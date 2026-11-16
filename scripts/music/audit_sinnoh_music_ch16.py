#!/usr/bin/env python3
"""CH16 read-only Sinnoh music cue audit. Never loads or installs audio."""
from __future__ import annotations
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = {
 "catalog": ROOT/"data/regions/sinnoh-music-ch16.json",
 "reference": ROOT/"docs/SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md",
 "blue": ROOT/"scripts/music/BlueMusic.rb",
 "adapter": ROOT/"scripts/music/SinnohMusicContracts.rb",
 "regions": ROOT/"site/public/data/regions.json",
}
GROUPS = {
 "city": "TWINLEAF_DAY TWINLEAF_NIGHT SANDGEM ROWAN_LAB JUBILIFE OREBURGH FLOAROMA ETERNA_CITY HEARTHOME VEILSTONE PASTORIA CANALAVE SNOWPOINT SUNYSHORE".split(),
 "route": "ROUTE_201_DAY ROUTE_201_NIGHT ROUTE_203 ROUTE_206 ROUTE_209 ROUTE_216".split(),
 "cave": "LAKE OREBURGH_MINE ETERNA_FOREST IRON_ISLAND MT_CORONET VICTORY_ROAD GALACTIC_HQ".split(),
 "scene": "SPEAR_PILLAR DISTORTION_WORLD CYNTHIA_INTRO HALL_OF_FAME_BGM".split(),
 "battle": "WILD TRAINER RIVAL GYM GALACTIC GALACTIC_COMMANDER CYRUS GIRATINA ELITE_FOUR CHAMPION".split(),
 "transport": ["SURF"], "post_game": ["FRONTIER"],
 "me": "BADGE_ME ITEM_ME HALL_OF_FAME_ME".split(),
}
PRIORITY={"scene":10,"me":15,"battle":20,"transport":30,"city":40,"route":40,"cave":40,"post_game":40}
POLICY=["EXPLICIT_ENGINE_EVENT","FORCED_VERIFIED_SCENE","CONFIGURED_BLUE_MUSIC",
        "VERIFIED_BATTLE","VERIFIED_TRANSPORT","VERIFIED_MAP","PRESERVE_NATIVE"]
KEEP="KEEP_EXISTING_BLUE_MUSIC_OR_NATIVE_AUDIO"
FALLBACK={
 "missing_file":KEEP,"invalid_hash":KEEP,"missing_license":KEEP,
 "unverified_native_scope":KEEP,"cross_region":"KEEP_ORIGINAL_REGION_AUDIO",
 "after_battle":"ENGINE_RESTORES_EXISTING_MAP_BGM",
 "after_me":"ENGINE_RESUMES_PREVIOUS_BGM",
 "after_scene_same_map":"RESTORE_PREVIOUS_IF_STILL_OWNED",
 "after_scene_map_changed":"DO_NOT_RESTORE_PREVIOUS",
 "on_load":"RESELECT_NATIVE_OR_EXISTING_BLUE_MUSIC",
 "no_repeat_same_track":True,"no_force_silence":True,
}
FADE={"fade_seconds":None,"fade_engine_default_until_licensed_proof":True,
      "loop_points":None,"loop_validation_required":True,
      "on_failed_audio":"NO_FADE_NO_REPLAY_NO_OVERRIDE","on_duplicate_cue":"NO_REPLAY"}
GUARDS={"only_current_region":"SINNOH","map_id_must_be_verified":True,
 "events_must_be_verified":True,"explicit_player_choices_first":True,
 "no_cross_region_changes":True,"do_not_modify_BlueMusic_rb":True,
 "no_autoplay_or_hook_install":True}
TOP={
 "schema":1,"region":"SINNOH","phase":"CH16",
 "status":"SYMBOLIC_CUES_PLANNED_NOT_INSTALLED",
 "source":"docs/SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md",
 "blue_music_runtime":"scripts/music/BlueMusic.rb",
 "contract_runtime":"scripts/music/SinnohMusicContracts.rb",
 "native_game_installed":False,"active_audio_overrides":False,
 "compiled_event_hooks_verified":False,"copyright_clearance_verified":False,
 "redistribution_approved":False,"gameplay_verified":False,"can_install":False,
 "recordings":[],"verified_tracks":0,"byte_assets_added":0,"default_enabled":False,
 "rights_policy":"NO_OFFICIAL_AUDIO_WITHOUT_RIGHTS",
 "priority_policy":POLICY,"fallback_policy":FALLBACK,
 "fade_loop_policy":FADE,"scope_guards":GUARDS,
}

def fail(message):
    raise ValueError("SINNOH_CH16_BLOQUEADO: "+message)

def read(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size>10_000_000:
        fail("Fonte ausente, symlink ou acima do limite: "+str(path))
    return path.read_text(encoding="utf-8-sig")

def json_file(path):
    x=json.loads(read(path))
    if not isinstance(x,dict):
        fail("JSON não é objeto")
    return x

def documented(markdown):
    start=markdown.find("### 4.1. Catálogo funcional proposto")
    end=markdown.find("### 4.2. Regras de prioridade musical",start)
    if start<0 or end<=start:
        fail("Tabela de Sinnoh ausente")
    out=[]
    for line in markdown[start:end].splitlines():
        if not line.startswith("| ") or "SINNOH_" not in line: continue
        keys=re.findall(r"\x60(SINNOH_[A-Z0-9_]+)\x60",line.split("|")[1])
        if not keys: fail("Linha musical inválida")
        out.extend(keys)
    return out

def expected():
    rows=[]
    for scope, names in GROUPS.items():
        for name in names:
            key="SINNOH_"+name
            rows.append({
                "key":key,"source_key":"SINNOH_HALL_OF_FAME" if name in
                    ("HALL_OF_FAME_BGM","HALL_OF_FAME_ME") else key,
                "scope":scope,"kind":"ME" if scope=="me" else "BGM",
                "time_window":"day" if name.endswith("_DAY") else
                    "night" if name.endswith("_NIGHT") else None,
                "priority":PRIORITY[scope],"track_path":None,
                "track_sha256":None,"loop_start_ms":None,"loop_end_ms":None,
                "fade_seconds":None,"volume":None,"pitch":None,
                "physical_map_id":None,"physical_event_id":None,
                "source_verified":False,"license_verified":False,
                "native_hook_verified":False,"compiled_binding_verified":False,
                "enabled":False,
                "pending_reason":"NO_LICENSED_AUDIO_OR_VERIFIED_NATIVE_BINDING",
                "fallback":KEEP,"audit_only":True,
            })
    return rows

def audit(cat, doc, blue, adapter, registry):
    if not isinstance(cat,dict) or set(cat)!=set(TOP)|{"cues","notes"}:
        fail("Campos do manifesto ausentes/desconhecidos")
    for key, value in TOP.items():
        if type(cat[key]) is not type(value) or cat[key]!=value:
            fail("Direitos/escopo/prioridade/fallback adulterado: "+key)
    if not isinstance(cat["notes"],str) or len(cat["notes"])<200:
        fail("Aviso de restrições insuficiente")
    wanted=expected()
    if not isinstance(cat["cues"],list) or len(cat["cues"])!=len(wanted):
        fail("Quantidade de cues incorreta")
    for item, target in zip(cat["cues"],wanted):
        if (not isinstance(item,dict) or set(item)!=set(target)
                or any(type(item[k]) is not type(v) or item[k]!=v
                       for k,v in target.items())):
            fail("Cue, MapID, áudio, direitos ou loop inventado: "+target["key"])
    original=documented(doc)
    if Counter(original)!=Counter(set(x["source_key"] for x in wanted)):
        fail("Chaves do MD e catálogo não coincidem")
    if registry.get("regions",{}).get("SINNOH",{}).get("status")!="planned":
        fail("Sinnoh não permanece planned")
    guards=(
        "def self.valid_track?(name)",
        "File.file?('Audio/BGM/'+name)",
        "def self.entry(scope,key)","def self.audio_for(scope,key)",
        "def self.battle_audio(key,kanto_allowed=true)",
        "return nil if $PokemonGlobal && $PokemonGlobal.nextBattleBGM",
        "def self.apply_map(game_map)",
        "map.autoplay_bgm=original[0];map.bgm=original[1].clone",
        "def self.current_bgm","def self.with_kanto_scene(name)",
        "def self.kanto_vehicle_audio","def self.kanto_me_audio(event)",
    )
    for word in guards:
        if word not in blue: fail("BlueMusic perdeu proteção: "+word)
    if "SinnohMusicContracts" in blue or "sinnoh-music-ch16" in blue:
        fail("CH16 não pode instalar código no BlueMusic compartilhado")
    required=(
        "module BlueSinnohMusicContracts","def self.safe_catalog?(catalog)",
        "def self.cue(catalog, key)","def self.resolve(catalog,key,current_region:",
        "current_region=='SINNOH'","explicit_engine_audio==true",
        "blue_music.entry('map',map_id)","blue_music.entry('global',blue_global_key)",
        "def self.transition(from:,to:,",
        "return :no_replay if same_track==true",
        "return :keep_new_region_audio if region_changed==true",
        "def self.fade_loop(catalog,key)",
    )
    for word in required:
        if word not in adapter: fail("Proteção Ruby ausente: "+word)
    code="\n".join(x for x in adapter.splitlines()
                   if not x.lstrip().startswith("#"))
    for banned in ("pbBGMPlay(","pbCueBGM(","pbMEPlay(","BlueMusic.install",
                   "File.write(","load_data(","File.open(","def self.install"):
        if banned in code: fail("Ruby de planejamento tenta reproduzir/instalar áudio")
    return {"region":"SINNOH","status":TOP["status"],"cue_count":len(wanted),
      "by_scope":dict(Counter(x["scope"] for x in wanted)),
      "bgm_cues":sum(x["kind"]=="BGM" for x in wanted),
      "me_cues":sum(x["kind"]=="ME" for x in wanted),
      "document_keys_matched":len(set(original)),
      "native_bindings_verified":0,"recordings_included":0,
      "playback_hook_installed":False,"copyright_cleared":False,
      "can_install":False,"gameplay_verified":False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key,path in FILES.items():
        parser.add_argument("--"+key,type=Path,default=path)
    args=parser.parse_args()
    try:
        output=audit(json_file(args.catalog),read(args.reference),
                     read(args.blue),read(args.adapter),json_file(args.regions))
    except (ValueError,OSError,KeyError,TypeError) as e:
        print(str(e),file=sys.stderr)
        return 2
    print(json.dumps(output,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
