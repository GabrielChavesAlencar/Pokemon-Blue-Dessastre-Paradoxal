"""Read-only mapping for exporting Kanto site facts from the isolated game."""
import json
from pathlib import Path


def prepared_plan(pilot: Path, manifest: dict) -> dict:
    source = pilot / "Kanto pilot.json"
    if not source.is_file():
        raise ValueError("Expected a source preview or a prepared isolated Kanto pilot")
    meta = json.loads(source.read_text(encoding="utf-8"))
    maps = {str(k): int(v) for k, v in meta["maps"].items()}
    if set(maps) != set(manifest["maps"]) or len(set(maps.values())) != len(maps):
        raise ValueError("Pilot map IDs do not match the pinned source catalog")
    rows = []
    for original, label in manifest["maps"].items():
        dest = maps[original]
        if dest < 1 or not (pilot / "Data" / f"Map{dest:03d}.rxdata").is_file():
            raise ValueError(f"Missing compiled source map {original} -> {dest}")
        rows.append({"source_id": int(original), "proposed_id": dest, "key": "KANTO_" + label})
    return {"package_sha256": manifest["sha256"], "region": manifest["region"], "maps": rows}
