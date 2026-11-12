"""Compile symbolic Kanto music rules against the *installed* pilot MapIDs.

F4 keeps F2/F3 regional music and compiles only six confirmed Kanto ME triggers
from the catalog of fourteen. No native/global audio or saves are overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path("Data/blue-kanto-music.txt")
MAGIC = "BLUE_KANTO_MUSIC_V1"
ME_ENABLED_PHASE4 = frozenset({"obtained_pokemon", "obtained_item", "healed",
                               "badge_awarded", "evolved", "caught"})
ME_NUMBERS = frozenset({1,9,14,22,23,29,31,42,43,44,49,51,54,58})
BATTLE_KEYS = frozenset({
    "wild", "trainer", "gym", "legendary", "champion",
    "wildVictory", "trainerVictory", "gymVictory",
})


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def load_mapping(game: Path) -> dict:
    """Use pilot metadata or the Kanto installation transaction, never FRLG IDs."""
    pilot = game / "Kanto pilot.json"
    installed = game / "Data/blue-kanto-install.json"
    if pilot.is_file():
        data = load_json(pilot)
    elif (game / "Data/blue-kanto-start.txt").is_file() and installed.is_file():
        data = load_json(installed)
        if data.get("schema") != 1:
            raise ValueError("Unsupported Kanto installation manifest")
    else:
        raise ValueError("Kanto pilot or installed Kanto manifest is required")
    if not isinstance(data.get("maps"), dict):
        raise ValueError("Missing compiled map mapping")
    return data["maps"]


def _track(catalog: dict, number: int, kind: str) -> str:
    if isinstance(number, bool) or not isinstance(number, int):
        raise ValueError("Track number must be an integer")
    item = catalog.get(number)
    if not item or item.get("kind") != kind:
        raise ValueError(f"Unknown Kanto {kind} track: {number}")
    name = item.get("filename")
    path = item.get("game_path")
    if (not isinstance(name, str) or not name or Path(name).name != name
            or any(ch in name for ch in "\t\r\n\\/:") or
            path != f"Audio/{kind}/Kanto/{name}" or
            not name.casefold().endswith(".mp3")):
        raise ValueError(f"Unsafe Kanto track: {number}")
    return f"Kanto/{name}"


def _rules(project: Path) -> tuple[dict, dict, dict]:
    rules_path = project / "data/kanto-music-rules.json"
    rules = load_json(rules_path)
    source = load_json(project / "data/regions/kanto-source.json")
    manifest = load_json(project / "data/kanto-music.json")
    if (rules.get("schema"), rules.get("region"),
        rules.get("default_enabled")) != (1, "KANTO", False) or rules.get("phase") not in (1, 2, 3, 4):
        raise ValueError("Invalid Kanto rules/version")
    if source.get("region") != "KANTO" or manifest.get("region") != "KANTO":
        raise ValueError("Not a Kanto source or soundtrack catalog")
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) != 64:
        raise ValueError("Kanto 64-track catalog missing")
    catalog = {item["number"]: item for item in files}
    if len(catalog) != len(files):
        raise ValueError("Duplicated Kanto soundtrack numbers")
    return rules, source, catalog


def compile_bytes(project: Path, game: Path, mapping: dict) -> tuple[bytes, dict]:
    """Pure compilation; checks all actual MapXXX.rxdata files, writes nothing."""
    rules, source, catalog = _rules(project)
    maps = source.get("maps")
    if not isinstance(maps, dict) or len(maps) != 142:
        raise ValueError("Kanto source map catalog changed unexpectedly")
    source_ids = set(maps)
    if set(map(str, mapping)) != source_ids:
        raise ValueError("Compiled MapIDs do not cover precisely Kanto source maps")
    actual = {}
    for source_id in source_ids:
        destination = mapping[source_id] if source_id in mapping else mapping[int(source_id)]
        if isinstance(destination, bool):
            raise ValueError("Invalid destination MapID")
        try:
            destination = int(destination)
        except (TypeError, ValueError) as error:
            raise ValueError("Invalid destination MapID") from error
        if destination < 1:
            raise ValueError("Invalid destination MapID")
        path = game / "Data" / f"Map{destination:03d}.rxdata"
        if not path.is_file() or not path.resolve().is_relative_to(game.resolve()):
            raise ValueError(f"Compiled Kanto map missing: {source_id} -> {destination}")
        actual[source_id] = destination
    if len(set(actual.values())) != len(actual):
        raise ValueError("Duplicate compiled MapID")
    preview = set(source.get("preview_only", []))
    if not preview.issubset({int(i) for i in maps}):
        raise ValueError("Invalid Kanto preview map IDs")
    symbols = {}
    for source_id, key in maps.items():
        if not isinstance(key, str) or not key or key in symbols:
            raise ValueError("Duplicate or invalid Kanto map symbol")
        symbols[key] = (int(source_id), actual[source_id])

    header = f"{MAGIC}\tKANTO\t" + hashlib.sha256(
        (project / "data/kanto-music-rules.json").read_bytes()).hexdigest()
    lines = [header]
    for key in sorted(symbols):
        origin, dest = symbols[key]
        lines.append(f"SCOPE\t{dest}\t{key}\t{int(origin in preview)}")

    report = {"region": "KANTO", "source_maps": len(actual),
              "preview_maps": len(preview), "real_map_ids": {
                  key: dest for key, (_, dest) in sorted(symbols.items())
              }, "staged_map_rules": 0, "staged_battles": 0,
              "staged_events": 0, "staged_scenes": 0,
              "staged_transport": 0, "active_transport_bindings": 0,
              "active_map_bindings": 0, "active_battle_bindings": 0,
              "default_global_pool_signatures": 0,
              "active_me_bindings": 0, "pending_me_events": [],
              "missing_audio": [], "preview_skipped": [],
              "native_playback_tested": False}
    seen = set()
    for row in rules.get("maps", []):
        key = row.get("map")
        if key not in symbols or key in seen:
            raise ValueError(f"Unknown or duplicated symbolic Kanto map: {key}")
        seen.add(key)
        track = _track(catalog, row.get("track"), "BGM")
        report["staged_map_rules"] += 1
        if not _enabled(row):
            continue
        origin, dest = symbols[key]
        if origin in preview:
            report["preview_skipped"].append(key)
            continue
        if not (game / "Audio/BGM" / track).is_file():
            report["missing_audio"].append(track)
            continue
        vol, pitch = _settings(row)
        lines.append(f"MAP\t{dest}\t{track}\t{vol}\t{pitch}")
        report["active_map_bindings"] += 1
    # Only unchanged Decades factory pools may yield to Kanto defaults.
    # Explicitly edited random lists, custom/mute or volume/pitch stay primary.
    if rules["phase"] >= 3:
        shared = load_json(project / "data/shared-music.json")["config"]["global"]
        for pool_key in ("wild", "trainer", "gym"):
            preset = shared.get(pool_key, {})
            if (preset.get("mode") != "random" or
                    not isinstance(preset.get("tracks"), list) or
                    not all(isinstance(name, str) for name in preset["tracks"])):
                raise ValueError("Invalid Decades baseline pool " + pool_key)
            payload = [str(preset.get("volume", 100)),
                       str(preset.get("pitch", 100)), *preset["tracks"]]
            signature = hashlib.sha256("\n".join(payload).encode("utf-8")).hexdigest()
            lines.append(f"BASEPOOL\t{pool_key}\t{signature}")
            report["default_global_pool_signatures"] += 1
    seen.clear()
    for row in rules.get("battles", []):
        key = row.get("category")
        if key not in BATTLE_KEYS or key in seen:
            raise ValueError(f"Invalid Kanto battle class: {key}")
        seen.add(key)
        track = _track(catalog, row.get("track"), "BGM")
        report["staged_battles"] += 1
        if not _enabled(row):
            continue
        if not (game / "Audio/BGM" / track).is_file():
            report["missing_audio"].append(track)
            continue
        vol, pitch = _settings(row)
        lines.append(f"BATTLE\t{key}\t{track}\t{vol}\t{pitch}")
        report["active_battle_bindings"] += 1

    seen.clear()
    transports = rules.get("transport", [])
    if not isinstance(transports, list):
        raise ValueError("Kanto transport rules must be a list")
    for row in transports:
        mode = row.get("mode")
        if mode not in ("bicycle", "surf") or mode in seen:
            raise ValueError(f"Invalid or duplicated Kanto transport mode: {mode}")
        seen.add(mode)
        track = _track(catalog, row.get("track"), "BGM")
        report["staged_transport"] += 1
        if not _enabled(row):
            continue
        if not (game / "Audio/BGM" / track).is_file():
            report["missing_audio"].append(track)
            continue
        vol, pitch = _settings(row)
        lines.append(f"TRANSPORT\t{mode}\t{track}\t{vol}\t{pitch}")
        report["active_transport_bindings"] += 1

    # All 14 ME are inventoried, but only events with audited native or
    # Kanto-specific completion callbacks may be enabled. Never bind by
    # guesswork, menu open, or an unfinished Pokémon Center/printer minigame.
    seen.clear()
    event_numbers=set()
    for row in rules.get("events", []):
        key = row.get("event")
        if (not isinstance(key, str) or not key or
                not key.replace("_", "").isalnum() or key in seen):
            raise ValueError("Invalid or duplicate Kanto ME event")
        seen.add(key)
        number = row.get("track")
        track = _track(catalog, number, "ME")
        if number in event_numbers:
            raise ValueError("Duplicate Kanto ME track")
        event_numbers.add(number)
        report["staged_events"] += 1
        if not _enabled(row):
            report["pending_me_events"].append(key)
            continue
        if rules["phase"] < 4 or key not in ME_ENABLED_PHASE4:
            raise ValueError(f"Unverified Kanto ME event cannot be enabled: {key}")
        if not (game / "Audio/ME" / track).is_file():
            report["missing_audio"].append("ME/" + track)
            continue
        vol, pitch = _settings(row)
        lines.append(f"ME\t{key}\t{track}\t{vol}\t{pitch}")
        report["active_me_bindings"] += 1
    if rules["phase"] >= 4:
        if event_numbers != ME_NUMBERS or len(seen) != 14:
            raise ValueError("Phase 4 requires the full 14-ME inventory")
        if {row["event"] for row in rules["events"] if row["enabled"]} != ME_ENABLED_PHASE4:
            raise ValueError("Only the six proven Phase 4 ME hooks may be active")

    seen.clear()
    for row in rules.get("scenes", []):
        key = row.get("scene")
        if (not isinstance(key, str) or not key or
                not key.replace("_", "").isalnum() or key in seen):
            raise ValueError("Invalid Kanto scene name")
        seen.add(key)
        _track(catalog, row.get("track"), "BGM")
        report["staged_scenes"] += 1
        if _enabled(row):
            raise ValueError("Scene playback requires a verified Phase 5 hook")
    report["lines"] = len(lines)
    return ("\n".join(lines) + "\n").encode("utf-8"), report


def _enabled(row: dict) -> bool:
    if not isinstance(row.get("enabled"), bool):
        raise ValueError("Explicit enabled boolean required for every music rule")
    return row["enabled"]


def _settings(row: dict) -> tuple[int, int]:
    volume, pitch = row.get("volume", 100), row.get("pitch", 100)
    if (type(volume) is not int or not 0 <= volume <= 100 or
            type(pitch) is not int or not 50 <= pitch <= 150):
        raise ValueError("Invalid regional volume/pitch")
    return volume, pitch


def phase3_track_numbers(project: Path) -> set[int]:
    """Eight BGM assets used exclusively by Kanto battle/victory hooks."""
    rules, _, catalog = _rules(project)
    numbers: set[int] = set()
    for row in rules.get("battles", []):
        _track(catalog, row["track"], "BGM")
        if _enabled(row):
            numbers.add(row["track"])
    return numbers


def phase4_track_numbers(project: Path) -> set[int]:
    """Only proven Kanto ME events, never unmatched menu/scene fanfares."""
    rules, _, catalog = _rules(project)
    numbers: set[int] = set()
    for row in rules.get("events", []):
        _track(catalog, row["track"], "ME")
        if _enabled(row):
            if row["event"] not in ME_ENABLED_PHASE4 or rules["phase"] < 4:
                raise ValueError("Unverified Kanto ME cannot be installed")
            numbers.add(row["track"])
    return numbers


def approved_audio_track_numbers(project: Path) -> set[int]:
    """All approved Kanto MP3s, both looping BGM and triggered ME."""
    return approved_track_numbers(project) | phase4_track_numbers(project)


def approved_track_numbers(project: Path) -> set[int]:
    """Minimal BGM payload for all approved Kanto phases."""
    return phase2_track_numbers(project) | phase3_track_numbers(project)


def phase2_track_numbers(project: Path) -> set[int]:
    """Audio assets required by enabled non-preview Kanto maps and vehicles."""
    rules, source, catalog = _rules(project)
    source_keys = {label: int(sid) for sid, label in source["maps"].items()}
    preview = set(source["preview_only"])
    numbers: set[int] = set()
    for row in rules.get("maps", []):
        key = row["map"]
        if key not in source_keys:
            raise ValueError("Unknown Kanto map in phase 2 assets")
        number = row["track"]
        _track(catalog, number, "BGM")
        if _enabled(row) and source_keys[key] not in preview:
            numbers.add(number)
    for row in rules.get("transport", []):
        _track(catalog, row["track"], "BGM")
        if _enabled(row):
            numbers.add(row["track"])
    return numbers


def plan_installed(project: Path, game: Path) -> dict[Path, bytes]:
    """Supplement the normal music installer only for an already-installed Kanto."""
    marker = game / "Data/blue-kanto-start.txt"
    installed = game / "Data/blue-kanto-install.json"
    if not marker.is_file() or not installed.is_file():
        return {}
    if not marker.read_text(encoding="ascii").startswith("BLUE_KANTO_START_V1,KANTO,"):
        raise ValueError("Unknown Kanto integration marker")
    # Do not break RUN.bat on an older Kanto install that has fewer maps;
    # the source/region installer must migrate that mapping first.
    mapped = load_json(installed).get("maps", {})
    pinned = load_json(project / "data/regions/kanto-source.json")["maps"]
    if not isinstance(mapped, dict) or set(mapped) != set(pinned):
        return {}
    content, _ = compile_bytes(project, game, load_mapping(game))
    return {game / OUTPUT: content}


def write_safely(project: Path, game: Path, content: bytes) -> str:
    """Explicit CLI apply: atomic update with an exact backup, no global writes."""
    home = (project / "game").resolve()
    work = (project / ".blue-work").resolve()
    target_dir = game.resolve()
    if target_dir != home and (target_dir == work or not target_dir.is_relative_to(work)):
        raise ValueError("Refusing to write outside game/ or .blue-work/ subfolders")
    dest = game / OUTPUT
    if not dest.parent.resolve().is_relative_to(target_dir):
        raise ValueError("Invalid Kanto music destination")
    if dest.is_file() and dest.read_bytes() == content:
        return "unchanged"
    if dest.exists() and not dest.is_file():
        raise ValueError("Kanto music destination is not a regular file")
    if dest.is_file():
        backup = project / ".blue-backups" / (
            "kanto-music-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        ) / OUTPUT
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes(dest.read_bytes())
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".blue-kanto-music-", dir=dest.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(content)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return "written"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, default=ROOT / ".blue-work/kanto-pilot")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    game = args.game.resolve()
    try:
        content, result = compile_bytes(ROOT, game, load_mapping(game))
        result["status"] = write_safely(ROOT, game, content) if args.apply else "dry_run"
        result["writes_global_config"] = False
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print("[KANTO MUSIC F1 ERROR] " + str(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
