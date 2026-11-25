"""Read-only local item PBS diagnostic. Never grants or compiles items."""
import hashlib
import re
from pbs import read_blocks

EXPECTED={2:"POTION",3:"TM24",4:"ELECTIRIZER",5:"MAXELIXER"}
def audit(base,candidates):
    result={"status":"BLOCKED","catalog_provenance":"LOCAL_PBS_READ_ONLY",
            "items":[],"items_granted":0,"native_verified":False,"saves_accessed":False}
    pbs=base/"PBS"
    blocks={}
    error=None
    if pbs.is_symlink() or not pbs.is_dir() or not (pbs/"items.txt").is_file():
        error="missing_or_unsafe_local_pbs"
    else:
        try:
            for path in sorted(pbs.glob("items*.txt")):
                if path.is_symlink() or not path.is_file():raise ValueError("unsafe_item_file")
                raw=path.read_bytes()
                for key,lines in read_blocks(path).items():
                    if key.upper() in EXPECTED.values():
                        blocks.setdefault(key.upper(),[]).append((key,lines,path.name,hashlib.sha256(raw).hexdigest()))
        except (OSError,UnicodeError,ValueError):
            error="invalid_or_duplicate_local_pbs"
    for eid,symbol in EXPECTED.items():
        matches=[x for x in candidates if x.get("event_id")==eid]
        literals=matches[0].get("literal_candidates",[]) if len(matches)==1 else []
        source_ok=(len(literals)==1 and literals[0].get("symbol")==symbol
                   and literals[0].get("quantity")==1 and literals[0].get("legacy_numeric_id") is None)
        local=blocks.get(symbol,[])
        row={"event_id":eid,"symbol":symbol,"quantity":1,"source_literal_valid":source_ok,
             "local_catalog_valid":False,"grant_enabled":False}
        if not source_ok:row["reason"]="source_identity_mismatch"
        elif error:row["reason"]=error
        elif len(local)!=1:row["reason"]="local_item_missing" if not local else "local_item_ambiguous"
        else:
            key,lines,name,digest=local[0]
            attrs={}
            duplicate=False
            for line in lines:
                k,sep,v=line.partition("=")
                if not sep:continue
                k=k.strip()
                if k in attrs:duplicate=True
                attrs[k]=v.split("#",1)[0].strip()
            pocket=attrs.get("Pocket","")
            valid=(key==symbol and not duplicate and bool(attrs.get("Name")) and
                   pocket.isascii() and pocket.isdigit() and int(pocket)>0)
            if symbol=="TM24":
                valid=valid and attrs.get("Move")=="THUNDERBOLT"
            row.update(local_catalog_valid=valid,pbs_file=name,pbs_sha256=digest,
                       reason="compiled_item_and_acquisition_review_pending" if valid else "local_item_definition_invalid")
        result["items"].append(row)
    result["local_catalog_valid_count"]=sum(x["local_catalog_valid"] for x in result["items"])
    if result["local_catalog_valid_count"]==4:result["status"]="LOCAL_PBS_IDENTITIES_VALIDATED_NO_GRANTS"
    return result
