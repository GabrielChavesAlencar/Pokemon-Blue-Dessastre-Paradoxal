"""Read-only Pallet residence audit from the pinned Essentials FRLG source.

No scripts from the source project are evaluated. Coordinates and paired
transfers are printed so house entry and Kanto new-game spawn are testable.
"""
from __future__ import annotations
from audit import ROOT,load
from server.ruby_marshal import text
SOURCE=ROOT/".blue-work/frlg-source/Essentials FRLG"
MAPS=(5,6,7,8)
def safe(value):
    value=text(value) if isinstance(value,bytes) else str(value)
    return value.replace("|","/").replace("\r"," ").replace("\n"," ")[:120]
def main():
    # Native Decades starting area: read-only diagnostic for the regional agent.
    native=ROOT/"game/Data"
    if (native/"System.rxdata").is_file():
        dec_sys=load(native/"System.rxdata").attrs
        dec_infos=load(native/"MapInfos.rxdata")
        print(f"DECADES_AUDIT_START:{dec_sys['@start_map_id']}|{dec_sys['@start_x']}|{dec_sys['@start_y']}")
        if dec_sys["@start_map_id"] in dec_infos:
            entry=dec_infos[dec_sys["@start_map_id"]].attrs
            print(f"DECADES_AUDIT_START_NAME:{safe(entry['@name'])}")
        for mid, info in sorted(dec_infos.items()):
            name=safe(info.attrs["@name"])
            if mid<=35 or any(x in name.lower() for x in ("town","city","village","vila","cidade")):
                print(f"DECADES_AUDIT_PLACE:{mid}|{name}|parent={info.attrs.get('@parent_id')}")
    for map_id in (1, 76, 77):
        path = native/f"Map{map_id:03}.rxdata"
        if not path.is_file():
            continue
        map_ = load(path).attrs
        print(f"DECADES_START_MAP:{map_id}|{map_['@width']}x{map_['@height']}|events={len(map_['@events'])}")
        for eid, ev in sorted(map_["@events"].items()):
            a = ev.attrs
            warps = []
            for page in a["@pages"]:
                for c in page.attrs["@list"]:
                    op = c.attrs
                    if op["@code"] == 201 and len(op["@parameters"]) >= 4:
                        warps.append(tuple(op["@parameters"][:4]))
            page=a["@pages"][0].attrs
            if warps or map_id==77 and (eid<=28 or "center" in safe(a["@name"]).lower()):
                print(f"DECADES_START_EVENT:{map_id}|{eid}|{safe(a['@name'])}|"
                      f"xy={a['@x']},{a['@y']}|graphic={safe(page['@graphic'].attrs['@character_name'])}|"
                      f"warp={';'.join(str(w) for w in warps)}")
    system=load(SOURCE/"Data/System.rxdata").attrs
    print(f"PALLET_SOURCE_START:{system['@start_map_id']}|{system['@start_x']}|{system['@start_y']}")
    for original in MAPS:
        map_=load(SOURCE/"Data"/f"Map{original:03}.rxdata").attrs
        print(f"PALLET_AUDIT_MAP:{original}|{map_['@width']}|{map_['@height']}|events={len(map_['@events'])}")
        for eid,event in sorted(map_["@events"].items()):
            attrs=event.attrs;warps=[]
            for page in attrs["@pages"]:
                for cmd in page.attrs["@list"]:
                    row=cmd.attrs
                    if row["@code"]==201 and len(row["@parameters"])>=6 and row["@parameters"][0]==0:
                        warps.append(tuple(int(v) for v in row["@parameters"][1:6]))
            page=attrs["@pages"][0].attrs
            graphic=safe(page["@graphic"].attrs["@character_name"])
            print(f"PALLET_AUDIT_EVENT:{original}|{eid}|{safe(attrs['@name'])}|xy={attrs['@x']},{attrs['@y']}|"
                  f"trigger={page['@trigger']}|graphic={graphic}|"
                  f"warps={';'.join(','.join(map(str,w)) for w in sorted(set(warps)))}")
if __name__=="__main__":
    main()
