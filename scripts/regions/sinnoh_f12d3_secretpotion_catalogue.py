"""Local SecretPotion PBS validation, read-only and fail-closed."""
import hashlib
from pbs import read_blocks

ITEM="SECRETPOTION"

def audit(base):
    result={"status":"BLOCKED","symbol":ITEM,"local_catalog_valid":False,
            "compiled_catalog_verified":False,"items_granted":0}
    try:
        pbs=base/"PBS"
        if pbs.is_symlink() or not pbs.is_dir() or not (pbs/"items.txt").is_file():
            return {**result,"reason":"missing_or_unsafe_local_pbs"}
        matches=[]
        for path in sorted(pbs.glob("items*.txt")):
            if path.is_symlink() or not path.is_file():
                raise ValueError("unsafe_item_file")
            for key,lines in read_blocks(path).items():
                if key.upper()==ITEM:matches.append((path,key,lines))
        if len(matches)!=1:
            return {**result,"reason":"local_item_missing_or_ambiguous","matches":len(matches)}
        path,key,lines=matches[0]
        attrs={}
        for line in lines:
            name,sep,value=line.partition("=")
            if not sep:continue
            name=name.strip()
            if name in attrs:raise ValueError("duplicate_attribute")
            attrs[name]=value.split("#",1)[0].strip()
        flags={x.strip() for x in attrs.get("Flags","").split(",")}
        pocket=attrs.get("Pocket","")
        if key!=ITEM or not attrs.get("Name") or "KeyItem" not in flags or not pocket.isascii() or not pocket.isdigit() or int(pocket)<=0:
            return {**result,"reason":"local_item_definition_invalid"}
        return {**result,"status":"LOCAL_PBS_IDENTITY_VALIDATED","local_catalog_valid":True,
            "pbs_file":path.name,"pbs_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "reason":"compiled_catalog_and_geometry_pending"}
    except (OSError,UnicodeError,ValueError,TypeError):
        return {**result,"reason":"invalid_or_duplicate_local_pbs"}

# Project-authored definition for the missing item, local private QA only.
# Standard Essentials v21.1 key-item metadata (Pocket 8, Price 0).
FRAGMENT="PBS/items_sinnoh_f12d.txt"
DEFINITION=b"[SECRETPOTION]\nName = SecretPotion\nNamePlural = SecretPotions\nPocket = 8\nPrice = 0\nFlags = KeyItem\nDescription = A special medicine for the Psyduck on Route 210.\n"

def prepare_missing(base,blobs):
    report=audit(base)
    if report.get("local_catalog_valid"):
        return {},report
    if report.get("reason")!="local_item_missing_or_ambiguous" or report.get("matches")!=0:
        return {},report
    if (base/FRAGMENT).exists() or FRAGMENT in blobs:
        return {},{**report,"reason":"candidate_path_collision"}
    import re
    for path,raw in blobs.items():
        if path.startswith("PBS/items") and path.endswith(".txt"):
            if re.search(rb"(?im)^\s*\[SECRETPOTION\]\s*(?:#.*)?$",raw):
                return {},{**report,"reason":"generated_item_collision"}
    return {FRAGMENT:DEFINITION},{**report,"status":"AUTHORIAL_PRIVATE_ITEM_PREPARED",
        "authored_candidate":True,"candidate_sha256":hashlib.sha256(DEFINITION).hexdigest(),
        "reason":"compiled_key_item_identity_pending"}
