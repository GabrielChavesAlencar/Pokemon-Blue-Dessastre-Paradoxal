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
