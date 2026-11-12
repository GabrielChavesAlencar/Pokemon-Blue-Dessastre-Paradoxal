"""Read-only source audit of Saffron, Sabrina and Silph Co. (FRLG 1.1)."""
from __future__ import annotations
import re
from collections import Counter
from audit import ROOT, load
from server.ruby_marshal import text

SOURCE = ROOT / ".blue-work/frlg-source/Essentials FRLG"
MAPS = (57, 62, 107, 108, 111, 112, 168, 169, 170, 171, 172,
        178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189)
FOCUS = re.compile(r"(?i)trainer|battle|rocket|leader|sabrina|giovanni|rival|"
                   r"card.?key|silph|warp|teleport|elevator|lift|pbmessage|mart|heal|"
                   r"door|switch|self.?switch|fossil|lapras")
def safe(value):
    s = text(value) if isinstance(value, bytes) else str(value)
    return s.replace("|", "/").replace("\n", " ").replace("\r", " ").strip()[:200]
def main():
    all_warps=[]
    for mid in MAPS:
        m = load(SOURCE / "Data" / f"Map{mid:03}.rxdata").attrs
        events=m["@events"]
        print(f"SAFF_CORE_MAP:{mid}|{m['@width']}x{m['@height']}|events={len(events)}")
        for eid,ev in sorted(events.items()):
            attrs=ev.attrs
            name=safe(attrs["@name"])
            warps=[]
            codes=Counter()
            scripts=[]
            for page in attrs["@pages"]:
                for cmd in page.attrs["@list"]:
                    op=cmd.attrs
                    codes[op["@code"]]+=1
                    args=op["@parameters"]
                    if op["@code"]==201 and len(args)>=6 and args[0]==0:
                        warps.append(tuple(int(x) for x in args[1:6]))
                    if op["@code"] in (355,655) and args:
                        scripts.append(safe(args[0]))
            page=attrs["@pages"][0].attrs
            graphic=safe(page["@graphic"].attrs["@character_name"])
            for target,*_ in warps:
                all_warps.append((mid,int(eid),target))
            if (mid in (168,169,170,171,172,178,188,189) or
                    warps or FOCUS.search(name) or any(FOCUS.search(s) for s in scripts)):
                warp_text=";".join(",".join(map(str,w)) for w in sorted(set(warps))[:14])
                script_text=";".join(s for s in scripts if FOCUS.search(s))[:240]
                print(f"SAFF_CORE_EVENT:{mid}|{eid}|{name}|xy={attrs['@x']},{attrs['@y']}|"
                      f"trigger={page['@trigger']}|graphic={graphic}|"
                      f"warps={warp_text}|scripts={script_text}|pages={len(attrs['@pages'])}|"
                      f"opcodes={','.join(str(x) for x in sorted(codes) if x in (111,121,122,123,125,201,355,655))}")
    headers=Counter()
    for line in (SOURCE/"PBS/trainers.txt").read_text(encoding="utf-8-sig").splitlines():
        raw=line.strip()
        if raw.startswith("[") and raw.endswith("]"):
            k=raw[1:-1]
            if re.search(r"(?i)sabrina|giovanni|rocket|psychic|dojo|juggler|channeler|"
                         r"blackbelt|scientist|rival",k):
                headers[k]+=1
    for name,n in sorted(headers.items()):
        print(f"SAFF_CORE_PBS:{name}|occurrences={n}")
    print(f"SAFF_CORE_WARPS:{len(all_warps)}|distinct={len(set(all_warps))}")
if __name__=="__main__":
    main()
