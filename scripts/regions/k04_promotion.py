"""Compose the proven K04 conversions into a prepared 165-map pilot."""
from audit import inventory, load
from audit_cerulean_interiors import inspect_events
from audit_k04_rock_tunnel import summarize
from build_k04_geometry import inject_warps
from k04_corridor import MAPS, connections, published_destinations, verify_source
from k04_gameplay import (install_actors, install_aide_and_runtime,
                          install_pbs_payload, trainer_profiles)
from kanto_overworld import source_obstacle
from pilot import EVENT_CLASSES, write_map


def install(source, target, tmp, mapping, plan):
    """Allow exactly five new K04 maps plus one original Route 2 event."""
    slots = {int(i): v for i, v in published_destinations().items()}
    if len(mapping) != 165 or any(mapping.get(sid) != dest for sid, dest in slots.items()):
        raise ValueError("K04 build requires the full catalog and reserved map IDs")
    _, by_id = inventory(source)
    report = summarize(source, inspect_events(source, tuple(MAPS)),
                       {str(sid): mapping[sid] for sid in MAPS})
    verify_source(report)
    specs = trainer_profiles(report)
    if any(row not in plan["connections"] for row in connections(mapping)):
        raise ValueError("K04 build lacks an original corridor connection")
    donors = {sid: load(by_id[sid]) for sid in MAPS}
    report["cut_anchors"] = {
        str(sid): [{"event": eid, "xy": [ev.attrs["@x"],ev.attrs["@y"]]}
                   for eid, ev in donors[sid].attrs["@events"].items()
                   if source_obstacle(ev) == "cut"]
        for sid in (86, 87)}
    count = 0
    for sid, dest in slots.items():
        path = target / "Data" / f"Map{dest:03d}.rxdata"
        donor, native = donors[sid], load(path)
        if any(native.attrs[k] != donor.attrs[k] for k in ("@data","@width","@height")):
            raise ValueError(f"K04 geometry differs from original source: {sid}")
        inject_warps(donor, native, sid, mapping)
        actors, _, _ = install_actors(source, target, donor, native, sid, report)
        count += len(actors)
        write_map(path, native, EVENT_CLASSES)
    if count != 30 or len(specs) != 29:
        raise ValueError("K04 trainer event/profile count changed")
    install_pbs_payload(source, target, tmp, specs, slots, encounters_staged=True)
    install_aide_and_runtime(source, target, by_id, mapping)
