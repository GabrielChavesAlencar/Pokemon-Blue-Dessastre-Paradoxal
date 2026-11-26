"""Additive authorial catalogue for the private Sinnoh copy only."""
import hashlib
from pbs import catalogue,read_blocks
import sinnoh_f11a_gym as gym
import sinnoh_f12b5_authored_quest as mars
import sinnoh_f12c3_jupiter_candidate as jupiter
import sinnoh_f12d_integrated as integrated

TYPES="PBS/trainer_types_sinnoh_story.txt"
ITEMS="PBS/items_sinnoh_workskey.txt"
WORKS_KEY=b"[WORKSKEY]\nName = Works Key\nNamePlural = Works Keys\nPocket = 8\nPrice = 0\nFlags = KeyItem\nDescription = A key to the Valley Windworks.\n"

def prepare(base,blobs):
    pbs=base/"PBS"
    if pbs.is_symlink() or not pbs.is_dir():
        raise ValueError("SINNOH_REGIONAL_CATALOGUE_UNSAFE")
    for prefix in ("trainer_types","items"):
        files=list(pbs.glob(prefix+"*.txt"))
        if not files or any(p.is_symlink() or not p.is_file() for p in files):
            raise ValueError("SINNOH_REGIONAL_CATALOGUE_MISSING_OR_UNSAFE")
    for path in (TYPES,ITEMS):
        if path in blobs or (base/path).exists() or (base/path).is_symlink():
            raise ValueError("SINNOH_REGIONAL_CATALOGUE_PATH_COLLISION")
    types=catalogue(base,"trainer_types");items=catalogue(base,"items")
    folded={x.casefold() for x in types}
    generated=[];unresolved=[];used={}
    def ensure(label,aliases,ident,name,gender,money):
        candidates=[x for x in aliases if x in types]
        if len(candidates)==1:
            used[label]=candidates[0];return
        if candidates or any(x.casefold() in folded for x in aliases):
            unresolved.append(label);return
        block="[%s]\nName = %s\nGender = %s\nBaseMoney = %d\n"%(ident,name,gender,money)
        generated.append((ident,block));types.add(ident);folded.add(ident.casefold());used[label]=ident
    for leader in gym.LEADER_ORDER:
        aliases=gym.GYM_SPECS[leader][3]
        ensure(leader,aliases,aliases[-1],"Gym Leader",
               "Female" if leader in ("Gardenia","Fantina","Maylene","Candice") else "Male",100)
    ensure("Galactic grunt",mars.GRUNTS,"GALACTIC_GRUNT","Team Galactic","Male",32)
    commanders=[("Mars",mars.COMMANDERS,"COMMANDER_MARS","Female"),
                ("Jupiter",jupiter.JUPITER,"COMMANDER_JUPITER","Female"),
                ("Saturn",integrated.LAKES["VALOR"][2],"COMMANDER_SATURN","Male")]
    if all(not any(a.casefold() in folded for a in aliases) for _,aliases,_,_ in commanders):
        ensure("Galactic admin",("GALACTIC_ADMIN",),"GALACTIC_ADMIN","Galactic Commander","Male",100)
    for label,aliases,ident,gender in commanders:
        ensure(label,aliases,ident,"Galactic Commander",gender,100)
    delta={}
    if generated:delta[TYPES]=("\n".join(b for _,b in generated)).encode("ascii")
    item_matches=[x for x in mars.KEYS if x in items]
    item_counts=sum(1 for p in pbs.glob("items*.txt") for k in read_blocks(p) if k.casefold() in {x.casefold() for x in mars.KEYS})
    if not item_matches and item_counts==0:
        delta[ITEMS]=WORKS_KEY
    elif len(item_matches)!=1 or item_counts!=1:
        unresolved.append("Works Key")
    catalogue(base,"trainer_types",delta);catalogue(base,"items",delta)
    return delta,{"status":"PRIVATE_REGIONAL_CATALOGUE_PREPARED",
        "generated_trainer_types":[ident for ident,_ in generated],
        "resolved_types":used,"unresolved":unresolved,
        "works_key_prepared":ITEMS in delta,"source_catalogues_modified":False,
        "compiled_catalog_verified":False,
        "sha256":{k:hashlib.sha256(v).hexdigest() for k,v in delta.items()}}
