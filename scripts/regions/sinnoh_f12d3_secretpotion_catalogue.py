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
