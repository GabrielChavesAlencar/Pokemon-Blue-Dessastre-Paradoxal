"""Stable, narrow K05 publication contract. No gameplay or I/O here."""
from __future__ import annotations

CITY = {
    93:"LAVENDER_TOWN", 94:"LAVENDER_CENTER", 95:"LAVENDER_MART",
    96:"LAVENDER_HOUSE", 97:"LAVENDER_NAME_RATER", 98:"LAVENDER_FUJI_HOUSE",
}
TOWER = {sid:f"POKEMON_TOWER_{sid-99}F" for sid in range(100,107)}
MAPS = {**CITY, **TOWER}
NAMES = dict(zip(CITY.values(),("Lavender Town","Lavender Pokémon Center","Lavender Poké Mart",
    "Lavender House","Name Rater's House","Mr. Fuji's House")))
NAMES.update({role:f"Pokémon Tower - {sid-99}F" for sid,role in TOWER.items()})
SLOTS = {sid:mid for sid,mid in zip(MAPS,range(609,622))}
K05_COUNT = 178
LAVENDER_BOUNDARY=(93,"North",0,87,"South",0)


def published_destinations():
    return {str(sid):mid for sid,mid in SLOTS.items()}


def predecessor_sets(wanted):
    """Only the exact released 156-, 160- and 165-map subsets may skip to K05."""
    try:
        from scripts.regions.k03e_contract import MAPS as DIGLETT
        from scripts.regions.k04_corridor import MAPS as ROCK
    except ModuleNotFoundError:
        from k03e_contract import MAPS as DIGLETT
        from k04_corridor import MAPS as ROCK
    wanted=set(wanted)
    groups=[{str(i) for i in group} for group in (MAPS,ROCK,DIGLETT)]
    if len(wanted)!=K05_COUNT or not set.union(*groups)<=wanted:
        return {}
    result={}
    for group in groups:
        wanted=wanted-group
        result[len(wanted)]=wanted
    return result


def scoped_connection(a,side_a,off_a,b,side_b,off_b):
    """Decide just the K05-specific road; preserve every previous route."""
    return not {a,b} & MAPS.keys() or (a,side_a,int(off_a),b,side_b,int(off_b))==LAVENDER_BOUNDARY


def baseline_manifest(active):
    """Private 165 source scope used while assembling the active 178 product."""
    expected={str(i):key for i,key in MAPS.items()}
    if len(active["maps"])!=K05_COUNT or any(active["maps"].get(i)!=key for i,key in expected.items()):
        raise ValueError("K05 release catalog is not active or an audited source ID changed")
    return {**active,"maps":{i:key for i,key in active["maps"].items() if i not in expected}}
