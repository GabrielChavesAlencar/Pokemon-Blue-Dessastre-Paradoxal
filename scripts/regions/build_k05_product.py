"""Assemble a product-shaped 178-map candidate without touching the live catalog."""
from __future__ import annotations

import json
import os
from tempfile import TemporaryDirectory

from audit import KANTO, ROOT, inventory, json_file, load
from build_k05_city import digest, extend_terrain, isolate
from k04_corridor import publication_catalog
from k05_contract import LAVENDER_BOUNDARY, MAPS, NAMES, SLOTS
from k05_promotion import install
from pilot import PILOT_META, write_map

PRODUCT_APP="Kanto K05 Product CI"
PRODUCT_NAME="kanto-k05-product"


def append_candidate(catalog):
    if publication_catalog(catalog["maps"])!=165 or set(catalog["preview_only"]) & MAPS.keys():
        raise ValueError("K05 released predecessor is not the exact K04 scope")
    return {**catalog,"maps":{**catalog["maps"],**{str(i):role for i,role in MAPS.items()}}}


def compose(source,baseline,output,catalog):
    """Write new maps and metadata in a separate target and preserve old bytes."""
    old_catalog={**catalog,"maps":{key:role for key,role in catalog["maps"].items()
                                  if int(key) not in MAPS}}
    if append_candidate(old_catalog)!=catalog:
        raise ValueError("K05 product candidate roles differ")
    old_meta=json_file(baseline/PILOT_META)
    current={int(k):v for k,v in old_meta["maps"].items()}
    if set(current)!=set(map(int,old_catalog["maps"])) or output.exists() or baseline==output:
        raise ValueError("K05 product requires a fresh output and an exact 165-map staging base")
    _,paths=inventory(baseline)
    hashes={p.relative_to(baseline):digest(p) for p in paths.values()}
    mapping={**current,**SLOTS}
    with TemporaryDirectory(prefix=".k05-product-",dir=output.parent) as td:
        from pathlib import Path
        target,delta=extend_terrain(source,baseline,Path(td),old_catalog,MAPS,SLOTS)
        if delta!=SLOTS or set(delta.values()) & paths.keys():
            raise ValueError("K05 product map allocation collision")
        infos=target/"Data/MapInfos.rxdata"
        table=load(infos)
        with (target/"PBS/map_metadata_kanto.txt").open("a",encoding="utf8") as pbs:
            for sid,mid in delta.items():
                name=NAMES[MAPS[sid]]
                table[mid].attrs["@name"]=name.encode("utf8")
                pbs.write(f"\n[{mid:03d}]\nName = {name}\n")
                if sid==93:
                    pbs.write("Outdoor = true\nShowArea = true\n")
        write_map(infos,table)
        s0,d0,o0,s1,d1,o1=LAVENDER_BOUNDARY
        seam=[mapping[s0],d0,o0,mapping[s1],d1,o1]
        with (target/"PBS/map_connections_kanto.txt").open("a",encoding="ascii") as pbs:
            pbs.write("\n"+",".join(map(str,seam))+"\n")
        install(source,target,mapping,{"connections":[seam]},catalog)
        if any(digest(baseline/p)!=h or digest(target/p)!=h for p,h in hashes.items()):
            raise ValueError("K05 product modified a K04 or non-Kanto map")
        old_meta["maps"]=mapping
        if publication_catalog(json_file(KANTO)["maps"])==178:
            from scripts.music.compile_kanto_music import compile_bytes
            music,_=compile_bytes(ROOT,target,mapping)
            (target/"Data/blue-kanto-music.txt").write_bytes(music)
        (target/PILOT_META).write_text(json.dumps(old_meta),encoding="utf8")
        (target/"Data/blue-compile-request.txt").write_text("compile",encoding="ascii")
        (target/"Data/PluginScripts.rxdata").unlink(missing_ok=True)
        target.rename(output)
    return {"maps":len(mapping),"old_maps_byte_identical":len(hashes),
            "lavender_map_ids":SLOTS,"single_seam":seam,"published":False,
            "manual_playthrough":False}


def run():
    if os.getenv("GITHUB_ACTIONS")!="true":
        raise ValueError("K05 product smoke test must remain in Actions")
    work=ROOT/".blue-work"
    output=work/PRODUCT_NAME
    report=compose(work/"frlg-source/Essentials FRLG",work/"kanto-k05-baseline",output,
                   append_candidate(json_file(KANTO)))
    isolate(output,json_file(output/PILOT_META),profile=PRODUCT_APP,fixture="k05_product_fixture_only")
    (work/"kanto-k05-product-proof.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    print("KANTO_K05_PRODUCT_COMPOSED_OK:"+json.dumps(report),flush=True)


if __name__=="__main__":
    run()
