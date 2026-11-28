"""K05-specific integrity checks shared by the local and CI JoiPlay packager."""
from __future__ import annotations

import json
from scripts.regions.k05_contract import published_destinations


CELADON = {"125":276,"126":277,"127":278,"128":279}


def verify_registry(read, *, allow_celadon=False):
    kanto=json.loads(read("Data/blue-kanto-install.json"))
    maps=kanto.get("maps",{})
    expected=published_destinations()
    if not isinstance(maps,dict):
        raise ValueError("Invalid Android Kanto registry")
    if len(maps)<178 and not any(k in maps for k in expected):
        return False  # Historic version, keep its own existing verification.
    celadon = kanto.get("content_stage")=="K06_CELADON_SERVICES"
    if celadon and not allow_celadon:
        raise ValueError("Celadon is not part of the historical binary package.")
    if celadon:
        expected = {**expected,**CELADON}
    count = 182 if celadon else 178
    if len(maps)!=count or any(maps.get(k)!=v for k,v in expected.items()):
        raise ValueError("Android Lavender files do not use the thirteen published MapIDs")
    if len(set(maps.values()))!=count or any(type(i) is not int or not 0<i<1000 for i in maps.values()):
        raise ValueError("Android K05 contains invalid or duplicate destinations")
    ready=read("Data/blue-kanto-ready.txt").decode("ascii").strip()
    if ready!=f"BLUE_KANTO_READY_V1,{count},{maps.get('7')}":
        raise ValueError("Android Lavender compact ready registry disagrees")
    for map_id in expected.values():
        name=f"Data/Map{map_id:03d}.rxdata"
        if not read(name).startswith(b"\x04\x08"):
            raise ValueError(f"Android Lavender map is absent or not RGSS Marshal: {name}")
    return True
