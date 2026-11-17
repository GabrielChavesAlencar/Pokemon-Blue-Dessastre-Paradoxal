#!/usr/bin/env python3
"""Guard planned Unova E06 permissions and E07 music/trainer catalogs.

No downloads, audio file operations, source-script execution, or game changes.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/regions/unova-e06-e07-preparation.json"
AREAS = ROOT / "data/regions/unova-u03-areas.json"
REGISTRY = ROOT / "site/public/data/regions.json"
RIGHTS = set("map_geometry tilesets autotiles character_sprites npc_events trainer_sprites battle_sprites dialogues scripts_plugins audio_bgm audio_me audio_se trainer_data encounter_data".split())
EXPECTED_LEADERS = set("CHILI CRESS CILAN LENORA BURGH ELESA CLAY SKYLA BRYCEN IRIS".split())
EXPECTED_ELITE = set("SHAUNTAL GRIMSLEY CAITLIN MARSHAL".split())
EXPECTED_BATTLES = set("WILD TRAINER CHEREN BIANCA GYM TEAM_PLASMA N GHETSIS ELITE_FOUR ALDER LEGENDARY RESHIRAM_ZEKROM KYUREM".split())
EXPECTED_ME = set("BADGE ITEM EVOLUTION HALL_OF_FAME".split())
KEY = re.compile(r"UNOVA_[A-Z0-9_]{3,80}\Z")


def fail(message):
    raise ValueError("UNOVA_E06_E07_BLOQUEADO: " + message)


def validate(data, areas, region):
    if not isinstance(data, dict) or set(data) != {
        "schema","region","phase","status","reference_version",
        "source_assets_imported","audio_bytes_added","rights_verified",
        "can_install","game_exe_tested","android_tested","note",
        "rights_matrix","music_cues","trainer_references"
    }:
        fail("schema de fonte incompleto ou campos extras")
    expected = {
        "schema":1, "region":"UNOVA", "phase":"E06_E07",
        "status":"PLANNED_CATALOG_ONLY", "reference_version":"WHITE_BW",
        "source_assets_imported":False, "audio_bytes_added":0,
        "rights_verified":False, "can_install":False,
        "game_exe_tested":False, "android_tested":False
    }
    for key,value in expected.items():
        if type(data.get(key)) is not type(value) or data.get(key) != value:
            fail("campo de aprovação falso: " + key)
    if not isinstance(data["note"],str) or len(data["note"]) < 80:
        fail("aviso de planejamento insuficiente")
    if not isinstance(region,dict) or region.get("status") != "planned":
        fail("registro Unova não pode estar jogável")

    if not isinstance(areas,dict) or areas.get("state") != "PLANNED_REFERENCE_ONLY":
        fail("catálogo de áreas deve permanecer planned")
    area_list = areas.get("areas",[])
    area_keys = {x.get("key") for x in area_list if isinstance(x,dict)}
    if len(area_keys) != len(area_list) or len(area_keys) != 74:
        fail("catálogo de 74 áreas divergente")

    rights = data["rights_matrix"]
    if not isinstance(rights,list) or len(rights) != len(RIGHTS):
        fail("matriz de direitos incompleta")
    named = set()
    for row in rights:
        if not isinstance(row,dict) or set(row) != {
            "asset_group","source_file","rights_owner","permission_evidence_url",
            "license","redistribution_allowed","status"
        }:
            fail("registro de direitos malformado")
        group = row["asset_group"]
        if group in named or group not in RIGHTS:
            fail("grupo de direitos repetido/desconhecido")
        named.add(group)
        if any(row[k] is not None for k in ("source_file","rights_owner","permission_evidence_url","license")):
            fail("fonte/licença falsamente declarada")
        if row["redistribution_allowed"] is not False or row["status"] != "UNVERIFIED":
            fail("redistribuição não verificada")
    if named != RIGHTS:
        fail("grupos de direitos ausentes")

    cues=data["music_cues"]
    if not isinstance(cues,list) or len(cues) < 60:
        fail("chaves musicais incompletas")
    seen=set()
    battles=set()
    mes=set()
    targets=set()
    for cue in cues:
        if not isinstance(cue,dict) or set(cue) != {
            "key","scope","kind","target_area_key","priority","source_track",
            "licensed_audio_sha256","physical_map_id","enabled","fallback",
            "rights_verified","compiled_binding_verified"
        }:
            fail("cue malformada")
        k=cue["key"]
        if not isinstance(k,str) or not KEY.fullmatch(k) or k in seen:
            fail("cue duplicada/inválida")
        seen.add(k)
        scope=cue["scope"]
        if scope=="map":
            if (not k.startswith("UNOVA_MAP_") or cue["kind"]!="BGM"
                or cue["priority"]!=40 or cue["target_area_key"] not in area_keys):
                fail("escopo map inválido ou área inexistente")
            targets.add(cue["target_area_key"])
        elif scope=="battle":
            if (not k.startswith("UNOVA_BATTLE_") or cue["kind"]!="BGM"
                or cue["priority"]!=20 or cue["target_area_key"] is not None):
                fail("escopo de batalha inválido")
            battles.add(k[len("UNOVA_BATTLE_"):])
        elif scope=="me":
            if (not k.startswith("UNOVA_ME_") or cue["kind"]!="ME"
                or cue["priority"]!=15 or cue["target_area_key"] is not None):
                fail("escopo ME inválido")
            mes.add(k[len("UNOVA_ME_"):])
        else:
            fail("scope musical não reconhecido")
        if (cue["source_track"] is not None or cue["licensed_audio_sha256"] is not None
            or cue["physical_map_id"] is not None or cue["enabled"] is not False
            or cue["rights_verified"] is not False
            or cue["compiled_binding_verified"] is not False):
            fail("áudio, direitos ou MapID falsamente aprovados")
        expected_fallback = ("ENGINE_RESUMES_PREVIOUS_BGM" if scope=="me"
                             else "PRESERVE_CURRENT_BLUE_MUSIC_OR_NATIVE")
        if cue["fallback"] != expected_fallback:
            fail("fallback não conservador")
    if battles != EXPECTED_BATTLES or mes != EXPECTED_ME or not targets:
        fail("cue essencial ausente")
    if "UNOVA_NUVEMA_TOWN" not in targets or "UNOVA_NS_CASTLE" not in targets:
        fail("músicas de áreas críticas ausentes")

    trainers=data["trainer_references"]
    if not isinstance(trainers,list) or len(trainers) < 19:
        fail("elenco de treinadores incompleto")
    actor_ids=set()
    roles={}
    for row in trainers:
        if not isinstance(row,dict) or set(row)!={
            "key","area_key","role","source_trainer_id","pbs_trainer_id",
            "level_reference","team","verified","installed"
        }:
            fail("treinador inválido")
        key=row["key"]
        if not isinstance(key,str) or not key.startswith("UNOVA_TRAINER_") or key in actor_ids:
            fail("treinador duplicado")
        actor_ids.add(key)
        roles[key.removeprefix("UNOVA_TRAINER_")]=row["role"]
        if row["area_key"] not in area_keys or row["role"] not in ("leader","elite","champion_postgame","rival","boss"):
            fail("área/papel de treinador inválidos")
        if (row["source_trainer_id"] is not None or row["pbs_trainer_id"] is not None
            or row["level_reference"] is not None or row["team"] != []
            or row["verified"] is not False or row["installed"] is not False):
            fail("time, PBS ou nível inventado")
    if not EXPECTED_LEADERS <= {a for a,role in roles.items() if role=="leader"}:
        fail("líder White ausente")
    if not EXPECTED_ELITE <= {a for a,role in roles.items() if role=="elite"}:
        fail("Elite Four incompleta")
    if not {"N","GHETSIS","ALDER","CHEREN","BIANCA"} <= set(roles):
        fail("personagem de história ausente")
    return {
        "region":"UNOVA","phase":"E06_E07","status":"PLANNED_CATALOG_VALIDATED",
        "rights_groups_unverified":len(rights),"music_cues":len(cues),
        "trainer_references":len(trainers),"area_music_targets":len(targets),
        "rights_cleared":False,"music_installed":False,"teams_verified":False,
        "game_or_saves_modified":False,"can_install":False
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data",type=Path,default=DATA)
    parser.add_argument("--areas",type=Path,default=AREAS)
    parser.add_argument("--registry",type=Path,default=REGISTRY)
    args=parser.parse_args(argv)
    try:
        for file in (args.data,args.areas,args.registry):
            if file.is_symlink() or not file.is_file() or file.stat().st_size>3_000_000:
                fail("arquivo inexistente, symlink ou muito grande")
        data=json.loads(args.data.read_text("utf-8-sig"))
        areas=json.loads(args.areas.read_text("utf-8-sig"))
        registry=json.loads(args.registry.read_text("utf-8-sig"))
        result=validate(data,areas,registry["regions"]["UNOVA"])
        print(json.dumps(result,indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
