#!/usr/bin/env python3
"""S16: audit HM local claim wiring without installing an engine callback."""
from __future__ import annotations
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_badges_hms as ch11
import audit_sinnoh_s15_gyms as s15

FILES={
  "s16":ROOT/"data/regions/sinnoh-hms-s16.json",
  "ch11":ROOT/"data/regions/sinnoh-badges-hms-contract.json",
  "s15":ROOT/"data/regions/sinnoh-gyms-s15.json",
  "teams":ROOT/"data/regions/sinnoh-trainer-teams-ch15.json",
  "registry":ROOT/"site/public/data/regions.json",
  "campaign":ROOT/"scripts/battle_polish/Campaign.rb",
  "regions":ROOT/"scripts/battle_polish/Regions.rb",
  "policy":ROOT/"scripts/battle_polish/RegionalPolicy.rb",
  "travel":ROOT/"scripts/battle_polish/RegionTravel.rb",
  "gyms_adapter":ROOT/"scripts/regions/SinnohGymContracts.rb",
  "adapter":ROOT/"scripts/regions/SinnohHMContracts.rb",
}
POLICY={
  "sinnoh_region_required": True,
  "local_badge_required": True,
  "local_hm_pickup_receipt_required": True,
  "bag_item_alone_insufficient": True,
  "foreign_region_items_never_count": True,
  "do_not_modify_decades_badges": True,
  "do_not_copy_key_items_between_regions": True,
  "no_rewards_without_engine_commit": True,
  "no_duplicate_pickup_receipt": True,
  "fail_closed_missing_native_callback": True,
  "preserve_native_field_move_handlers": True,
  "no_game_or_save_write": True
};
TOP={
  "schema": 1,
  "region": "SINNOH",
  "stage": "S16",
  "status": "LOCAL_HM_GATE_CONTRACT_NOT_INSTALLED",
  "sources": {
    "hm_ch11": "data/regions/sinnoh-badges-hms-contract.json",
    "gyms_s15": "data/regions/sinnoh-gyms-s15.json",
    "regional_runtime": "scripts/battle_polish/Regions.rb",
    "field_policy": "scripts/battle_polish/RegionalPolicy.rb",
    "region_travel": "scripts/battle_polish/RegionTravel.rb",
    "native_adapter": "scripts/regions/SinnohHMContracts.rb"
  },
  "hm_count": 8,
  "verified_native_sources": {},
  "native_pickups_installed": 0,
  "native_receipts_verified": 0,
  "approved_for_install": False,
  "can_grant_hm": False,
  "can_change_native_saves": False,
  "game_exe_tested": False,
  "joiplay_tested": False,
  "native_qa_approved": False,
  "policy": {
    "sinnoh_region_required": True,
    "local_badge_required": True,
    "local_hm_pickup_receipt_required": True,
    "bag_item_alone_insufficient": True,
    "foreign_region_items_never_count": True,
    "do_not_modify_decades_badges": True,
    "do_not_copy_key_items_between_regions": True,
    "no_rewards_without_engine_commit": True,
    "no_duplicate_pickup_receipt": True,
    "fail_closed_missing_native_callback": True,
    "preserve_native_field_move_handlers": True,
    "no_game_or_save_write": True
  },
  "notes": "Somente interface de gate para comprovantes de coleta local. Nenhum evento nativo, MapID, callback compilado, item, chave ou HM foi adicionado. O Blues Regions original permanece proprietario das insignias e comprovantes; S16 nao autoriza escrita em saves nem alteracoes de outros sistemas regionais."
};
NIL_FIELDS=("physical_map_id","physical_event_id","verified_source_id","source_hash_sha256")
FALSE_FIELDS=("handler_compiled","pickup_event_verified","local_receipt_verified","game_exe_tested","joiplay_tested","enabled")
REQUIRED=(
  "module BlueSinnohHMContracts",
  "VERIFIED_NATIVE_SOURCES = {}.freeze",
  "def self.preview(state, action, bag)",
  "def self.record_from_native(state, action, bag, outcome, source_id: nil)",
  "outcome==:engine_pickup_committed",
  "VERIFIED_NATIVE_SOURCES[action]==source_id",
  "BlueRegions.field_access(state,'SINNOH',action,true)",
  "BlueRegions.record_sinnoh_hm(state,action,HM_BADGES[action][1],bag,true)",
  "state['current']=='SINNOH'",
)
FORBIDDEN=("EventHandlers.add(","pbReceiveItem(","pbMessage(","File.write(","File.open(","Game_Map.prepend(","Object.prepend(","def self.install","BlueRegions.award(","GameData::Item.register(")

def fail(msg): raise ValueError("SINNOH_S16_BLOCKED: "+msg)
def audit(spec,original,gyms,teams,registry,campaign,regions,field_policy,travel,gyms_adapter,adapter):
    ch11.audit(original,registry,regions,field_policy)
    s15.audit(gyms,teams,original,registry,campaign,regions,gyms_adapter)
    if not isinstance(spec,dict) or set(spec)!=(set(TOP)|{"hms"}):
        fail("campos de manifesto ausentes/inventados")
    for k,v in TOP.items():
        if type(spec[k]) is not type(v) or spec[k]!=v: fail("status/instalacao/prova adulterado: "+k)
    hms=spec["hms"]
    if not isinstance(hms,list) or len(hms)!=8: fail("oito HMs obrigatorios")
    by_badge={g["badge"]:g for g in gyms["gyms"]}
    for i,(row,source) in enumerate(zip(hms,original["rules"])):
        if not isinstance(row,dict): fail("registro HM nao e objeto")
        expected={
          "action":source["field_move"],"hm_item":source["hm_item"],
          "badge":source["badge"],"leader":by_badge[source["badge"]]["name"],
          **{key:None for key in NIL_FIELDS},
          **{key:False for key in FALSE_FIELDS},
          "status":"REQUIRES_NATIVE_LOCAL_PICKUP",
        }
        if set(row)!=set(expected) or any(type(row[k]) is not type(v) or row[k]!=v for k,v in expected.items()):
            fail("HM, origem, insignia ou evento inventado: "+str(i))
    if (any(k not in adapter for k in REQUIRED) or
        any(k not in adapter for k in ("'ROCK_SMASH'=>['COAL', :HM06]","'DEFOG'=>['RELIC', :HM05]","'ROCK_CLIMB'=>['ICICLE', :HM08]"))):
        fail("adapter nao protege par HM/insignia")
    executable="\n".join(line for line in adapter.splitlines() if not line.lstrip().startswith("#"))
    if any(k in executable for k in FORBIDDEN): fail("adapter tenta alterar jogo ou saves")
    # CH11 and RegionTravel retain ownership of items, regional claim receipts and storage.
    for required in (
      "def self.record_sinnoh_hm(state, action, item, bag, pickup_confirmed = false)",
      "pickup_confirmed == true",
      "state[\"region_local_hms\"][\"SINNOH\"] << action",
      "def self.field_access(state, region, action, tool_ready = false)",
      "sinnoh_local_hms(state).include?(action)",
    ):
        if required not in regions: fail("guarda regional alterada: "+required)
    for required in (
      'local_proof = current["current"] == "SINNOH"',
      "BlueRegions.field_access(current, current[\"current\"], action, local_proof)",
      "return hm_owned?(move_id) ? :allowed : :hm",
    ):
        if required not in field_policy: fail("regra de campo alterada")
    for required in ("def self.stage_local_bag(state, destination)","Sem espaço para os itens-chave/HMs da região de destino"):
        if required not in travel: fail("separacao de inventario removida")
    return {"region":"SINNOH","stage":"S16","hm_contracts":8,"native_pickups_installed":0,
            "native_bindings":0,"game_exe_tested":False,"joiplay_tested":False,
            "can_install":False,"code_only":True}
def run():
    read=lambda k:FILES[k].read_text("utf-8")
    return audit(*[json.loads(read(k)) for k in ("s16","ch11","s15","teams","registry")],
                 *[read(k) for k in ("campaign","regions","policy","travel","gyms_adapter","adapter")])
if __name__=="__main__":
    try:
        print(json.dumps(run(),ensure_ascii=False,indent=2))
        print("SINNOH_S16_LOCAL_HM_CONTRACT_OK_OFFLINE")
    except (KeyError,TypeError,ValueError,OSError) as exc:
        print(str(exc),file=sys.stderr);sys.exit(2)
