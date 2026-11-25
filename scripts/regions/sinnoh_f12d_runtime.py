"""Conditional F12D activation for an already verified 144-map private copy."""
import json
import re
import sinnoh_f12d_pastoria_preview as preview
import sinnoh_f12b5_authored_quest as mars
import sinnoh_f10b_trainers as trainers
import sinnoh_f10c_npcs as npc

PBS="PBS/trainers_sinnoh_f12d.txt"
SPRITE="Graphics/Characters/SNQA_F12D_GRUNT.png"

def build(blobs,mapping,components,types,species,existing,root):
    def blocked(reason,report=None):
        return blobs,{"status":"F12D_RUNTIME_BLOCKED","reason":reason,
            "geometry":report,"runtime_install_enabled":False,"native_verified":False,
            "new_events":0,"new_portals":0,"new_maps":0,"items_granted":0},b""
    if set(mapping)!=preview.baseline.ALL:return blocked("requires_144_baseline")
    delta,report=preview.preview(blobs,mapping,components,root)
    if not delta or report.get("status")!="F12D2_EVENT_PREVIEW":return blocked("geometry_unproved",report)
    grunt=mars.choose(types,mars.GRUNTS)
    if not grunt or "CROAGUNK" not in species:return blocked("local_catalog_missing_or_ambiguous",report)
    identity=(grunt,"Grunt",14001)
    if identity in existing or PBS in blobs or SPRITE in blobs:return blocked("trainer_or_asset_collision",report)
    for path,raw in blobs.items():
        if path.startswith("PBS/trainers") and path.endswith(".txt"):
            for line in raw.decode("utf-8-sig").splitlines():
                m=re.fullmatch(r"\s*\[([^\]]+)\]\s*",line)
                if not m:continue
                v=[x.strip() for x in m[1].split(",")]
                if len(v) in (2,3) and (len(v)==2 or v[2].isdigit()):
                    if (v[0],v[1],int(v[2]) if len(v)==3 else 0)==identity:
                        return blocked("generated_trainer_collision",report)
    loc={p["id"]:[p["map_id"],*p["position"]] for p in report["placements"]}
    if tuple(loc)!=preview.ORDER:return blocked("unexpected_placement_order",report)
    spec=[*identity,loc["VALOR_BATTLE"][0],[list(t) for t in preview.TEAM]]
    literal="{"+",".join(json.dumps(k)+"=>"+json.dumps(v) for k,v in loc.items())+"}"
    template=(root/"scripts/regions/SinnohF12D.rb").read_text("utf-8")
    for key,value in (("__F12D_LOCATIONS__",literal),("__F12D_SPEC__",json.dumps(spec))):
        if template.count(key)!=1:raise ValueError("F12D_TEMPLATE")
        template=template.replace(key,value)
    out={**blobs,**delta,PBS:("\n[%s,%s,%d]\nLoseText = Voce venceu!\nPokemon = CROAGUNK,31\n"%identity).encode("ascii"),
         SPRITE:npc.authored_sheet("galactic_grunt")}
    return out,{**report,"status":"F12D_RUNTIME_PREPARED","runtime_install_enabled":True,
         "new_events":3,"compiled_catalog_verified":False,"native_verified":False},template.encode("utf-8")

def append(blobs,mapping,components,base,root):
    if set(mapping)!=preview.baseline.ALL:
        return blobs,{"status":"F12D_RUNTIME_BLOCKED","reason":"requires_144_baseline",
            "runtime_install_enabled":False,"native_verified":False},b""
    try:
        existing=set()
        for p in (base/"PBS").glob("trainers*.txt"):
            if p.is_symlink() or not p.is_file():raise ValueError("F12D_UNSAFE_PBS")
            for header in trainers.read_blocks(p):
                v=[x.strip() for x in header.split(",")]
                if len(v) in (2,3) and (len(v)==2 or v[2].isdigit()):
                    existing.add((v[0],v[1],int(v[2]) if len(v)==3 else 0))
        return build(blobs,mapping,components,trainers.catalogue(base,"trainer_types"),
            trainers.catalogue(base,"pokemon"),existing,root)
    except (OSError,ValueError,TypeError,KeyError,UnicodeError) as exc:
        return blobs,{"status":"F12D_RUNTIME_BLOCKED","reason":"preflight_failed:"+type(exc).__name__,
            "runtime_install_enabled":False,"native_verified":False},b""
