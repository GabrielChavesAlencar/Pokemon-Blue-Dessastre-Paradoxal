"""Prepare the additive K04 upgrade without writing the installed game."""
from pathlib import Path

from audit import json_file, load, text
from k04_corridor import published_destinations
from k04_flash import EVENT_ID, SOURCE_ID, XY
from pilot import EVENT_CLASSES, PILOT_META, write_map


def prepare(game, pilot, proof):
    """Retain all old map bytes except Map21's source-audited Flash aide.

    The caller runs the existing installer ownership and rollback checks;
    this preparation can only change the isolated pilot.
    """
    from install_kanto import atomic, digest, legacy_map_identity, recorded_digest, recorded_hashes

    old = proof["maps"]
    new = json_file(pilot / PILOT_META)["maps"]
    slots = published_destinations()
    if (len(old) != 160 or len(new) != 165 or not {"23","79","81","82"} <= old.keys()
            or new.keys() - old.keys() != slots.keys()
            or any(new.get(k) != v for k, v in {**old, **slots}.items())):
        raise ValueError("K04 predecessor mapping differs")
    paths = {}
    hashes = recorded_hashes(proof)
    gate = None
    for sid, dest in old.items():
        rel = Path("Data") / f"Map{dest:03d}.rxdata"
        expected_sha = hashes.get(rel.as_posix())
        prior, rebuilt = game / rel, pilot / rel
        if not recorded_digest(expected_sha) or any(
                path.is_symlink() or not path.is_file() or
                not path.resolve().is_relative_to(root.resolve())
                for path,root in ((prior,game),(rebuilt,pilot))):
            raise ValueError(f"K04 missing owned predecessor: {rel}")
        legacy_map_identity(game, pilot, rel)
        previous, staged = load(prior), load(rebuilt)
        if any(previous.attrs[k] != staged.attrs[k] for k in ("@width", "@height", "@data")):
            raise ValueError(f"K04 predecessor geometry differs: {sid}")
        events, replacement = previous.attrs["@events"], staged.attrs["@events"]
        if sid != str(SOURCE_ID):
            if events.keys() != replacement.keys():
                raise ValueError(f"K04 predecessor event IDs differ: {sid}")
            paths[rel] = digest(prior)
        else:
            if replacement.keys() - {EVENT_ID} != events.keys() - {EVENT_ID}:
                raise ValueError("K04 changes more than the one Flash aide")
            install_verified_aide(previous, replacement[EVENT_ID])
            gate = (rel, previous, digest(prior))
    if len(paths) != 159 or gate is None:
        raise ValueError("K04 predecessor is incomplete")
    for rel, expected in paths.items():
        raw = (game / rel).read_bytes()
        from hashlib import sha256
        if sha256(raw).hexdigest() != expected:
            raise ValueError(f"K04 installed map changed during preparation: {rel}")
        atomic(pilot / rel, raw)
    rel, previous, expected = gate
    if digest(game / rel) != expected:
        raise ValueError("K04 installed Flash gatehouse changed during preparation")
    write_map(pilot / rel, previous, EVENT_CLASSES)
    if load(pilot / rel) != previous or any(digest(pilot / p) != h for p,h in paths.items()):
        raise ValueError("K04 migrated map preservation failed")
    return paths, rel


def install_verified_aide(previous, aide):
    """Refuse to replace an active event or modify any other old event."""
    events = previous.attrs["@events"]
    old = events.get(EVENT_ID)
    if old is not None:
        if tuple(old.attrs[k] for k in ("@x","@y")) != XY or any(
            op.attrs["@code"] not in (0,101,401,355) or
            (op.attrs["@code"] == 355 and not text(op.attrs["@parameters"][0]).startswith(
                "BlueKantoPilot.npc_dialogue(21, 2,"))
            for page in old.attrs["@pages"] for op in page.attrs["@list"]):
            raise ValueError("K04 will not replace an active Route 2 event")
    page, = aide.attrs["@pages"]
    ops = page.attrs["@list"]
    if (tuple(aide.attrs[k] for k in ("@x","@y")) != XY or aide.attrs["@id"] != EVENT_ID
            or page.attrs["@trigger"] != 0 or [op.attrs["@code"] for op in ops] != [355,0]
            or ops[0].attrs["@parameters"] != [b"BlueKantoPilot.route2_flash"]):
        raise ValueError("K04 required the audited native Flash aide")
    events[EVENT_ID] = aide
