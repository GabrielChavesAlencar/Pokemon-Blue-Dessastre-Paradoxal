"""Additive K05 migration preparation, contained in a disposable staged pilot."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from audit import json_file, load
from k03e_contract import WARPS
from k04_corridor import published_destinations as rock_slots
from k04_migration import install_verified_aide
from k04_flash import SOURCE_ID as FLASH_MAP, EVENT_ID as FLASH_EVENT
from k05_contract import published_destinations, predecessor_sets
from pilot import EVENT_CLASSES, PILOT_META, write_map


def predecessor_edits(old,new):
    if (predecessor_sets(new).get(len(old))!=set(old) or
        any(new.get(sid)!=dest for sid,dest in {**old,**rock_slots(),**published_destinations()}.items())):
        raise ValueError("K05 predecessor map IDs or scope differ from the exact published append")
    return {156:{18,FLASH_MAP},160:{FLASH_MAP},165:set()}[len(old)]


def merge_route2(previous,staged,mapping):
    old,new = previous.attrs["@events"],staged.attrs["@events"]
    st = new.get(1)
    if 1 in old or st is None or new.keys() != old.keys() | {1}:
        raise ValueError("K05 cannot change anything except the source-anchored Diglett door")
    dest,x,y,face=WARPS[(18,1)]
    page,=st.attrs["@pages"]
    if (st.attrs["@id"]!=1 or
            page.attrs["@trigger"]!=1 or
            [op.attrs["@parameters"][:5] for op in page.attrs["@list"]
             if op.attrs["@code"]==201] != [[0,mapping[str(dest)],x,y,face]]):
        raise ValueError("K05 reserved Route 2 Diglett door is not the staged source door")
    old[1]=st


def prepare(game,pilot,proof):
    """Only stage the one/two audited native event edits and byte-copy old maps.

    The existing single installer transaction still owns all writes to the
    user's install, including exact rollback of marker, PBS, and compiled data.
    """
    from install_kanto import atomic, digest, legacy_map_identity, recorded_digest, recorded_hashes
    old=proof["maps"]
    new=json_file(pilot/PILOT_META)["maps"]
    allowed=predecessor_edits(old,new)
    hashes=recorded_hashes(proof)
    changes,keep={},{}
    for sid,mid in old.items():
        rel=Path("Data")/f"Map{mid:03}.rxdata"
        prior,rebuilt=game/rel,pilot/rel
        if (not recorded_digest(hashes.get(rel.as_posix())) or any(p.is_symlink() or
                not p.is_file() or not p.resolve().is_relative_to(base.resolve())
                for p,base in ((prior,game),(rebuilt,pilot)))):
            raise ValueError(f"K05 predecessor map ownership missing: {sid}/{mid}")
        legacy_map_identity(game,pilot,rel)
        prior_sha=digest(prior)
        previous,staged=load(prior),load(rebuilt)
        if any(previous.attrs[k]!=staged.attrs[k] for k in ("@width","@height","@data")):
            raise ValueError(f"K05 predecessor geometry differs: {sid}")
        if int(sid) not in allowed:
            if previous.attrs["@events"].keys()!=staged.attrs["@events"].keys():
                raise ValueError(f"K05 predecessor changed existing event IDs: {sid}")
            keep[rel]=prior_sha
        else:
            if int(sid)==18:
                merge_route2(previous,staged,new)
            elif int(sid)==FLASH_MAP:
                a,b=previous.attrs["@events"],staged.attrs["@events"]
                if FLASH_EVENT not in b or a.keys()-{FLASH_EVENT}!=b.keys()-{FLASH_EVENT}:
                    raise ValueError("K05 Route 2 gatehouse changes an event other than the Flash aide")
                install_verified_aide(previous,b[FLASH_EVENT])
            changes[rel]=(previous,prior_sha)
    if len(changes)!=len(allowed) or len(keep)+len(changes)!=len(old):
        raise ValueError("K05 did not account for every prior map")
    for rel,h in keep.items():
        raw=(game/rel).read_bytes()
        if sha256(raw).hexdigest()!=h:
            raise ValueError(f"K05 predecessor changed during staging: {rel}")
        atomic(pilot/rel,raw)
    for rel,(prepared,prior_sha) in changes.items():
        if digest(game/rel)!=prior_sha:
            raise ValueError(f"K05 predecessor changed during staging: {rel}")
        write_map(pilot/rel,prepared,EVENT_CLASSES)
        if load(pilot/rel)!=prepared:
            raise ValueError(f"K05 predecessor staged map failed Marshal roundtrip: {rel}")
    if any(digest(pilot/p)!=h for p,h in keep.items()):
        raise ValueError("K05 did not preserve every unchanged predecessor map byte-for-byte")
    return keep,set(changes)
