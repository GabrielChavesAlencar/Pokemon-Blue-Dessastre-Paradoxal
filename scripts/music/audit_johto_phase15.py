"""Read-only Johto phase15 audit. No music installation or false-playability claims."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KINDS = {"BGM", "ME"}
RULE_GROUPS = ("maps", "battles", "me", "scenes")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def audit(root: Path = ROOT) -> dict:
    manifest = load(root / "data/johto-music.json")
    rules = load(root / "data/johto-music-rules.json")
    source = load(root / "data/regions/johto-source.json")
    preview = load(root / "site/public/data/johto-preview.json")
    registry = load(root / "site/public/data/regions.json")
    for name, row in (("manifest", manifest), ("rules", rules),
                      ("source", source), ("preview", preview)):
        if row.get("region") != "JOHTO" or row.get("schema") != 1:
            raise ValueError(f"Invalid Johto {name}")
    if manifest.get("phase") != "15/16" or rules.get("phase") != "15/16":
        raise ValueError("Phase 15 catalog mismatch")
    if manifest.get("status") != "PLANNED_CUES_NOT_INSTALLED":
        raise ValueError("Unsafe Johto audio status")
    if manifest.get("license_verified") is not False or manifest.get("distribution_approved") is not False:
        raise ValueError("Johto audio rights cannot be presumed")
    if manifest.get("recordings") != [] or manifest.get("verified_tracks") != 0:
        raise ValueError("Unverified Johto audio was declared available")
    if source.get("import_enabled") is not False or source.get("mapping_verified") is not False or source.get("maps") != {}:
        raise ValueError("Johto source must remain uninstalled")
    if rules.get("default_enabled") is not False or rules.get("status") != "PREVIEW_ONLY_NO_ACTIVE_AUDIO":
        raise ValueError("Johto audio cannot be enabled by default")
    guards = rules.get("guardrails", {})
    required = (
        "require_real_compiled_mapids", "require_source_sha256",
        "require_rights_clearance", "require_compiled_event_hooks",
        "deny_kanto_decades_maps"
    )
    if guards.get("requires_current_region") != "JOHTO" or not all(guards.get(k) is True for k in required):
        raise ValueError("Johto music could affect Kanto/Decades")
    if guards.get("on_missing_audio") != "KEEP_EXISTING_BGM" or (
        guards.get("on_me_finish") != "RESTORE_PREVIOUS_BGM"
    ):
        raise ValueError("Unsafe audio fallback")
    for kind in KINDS:
        expected = f"Audio/{kind}/Johto"
        if manifest.get("asset_roots", {}).get(kind) != expected or rules.get("asset_roots", {}).get(kind) != expected:
            raise ValueError("Wrong Johto audio destination")
    if preview.get("status") != "preview_only_not_playable" or preview.get("region") != "JOHTO":
        raise ValueError("Site exposes Johto as playable")
    if any(preview.get(k) != 0 for k in ("maps_installed", "trainers_compiled",
                                         "teams_verified", "encounters_verified", "audio_files_installed")):
        raise ValueError("False Johto gameplay status")
    if registry.get("regions", {}).get("JOHTO", {}).get("status") != "planned":
        raise ValueError("Johto marked playable without maps")
    cues = manifest.get("cues", [])
    ids = [cue.get("id") for cue in cues]
    if not cues or len(ids) != len(set(ids)) or any(not isinstance(k, str) or not k for k in ids):
        raise ValueError("Invalid Johto cue index")
    lookup = {cue["id"]: cue for cue in cues}
    for cue in cues:
        if cue.get("kind") not in KINDS or cue.get("status") != "MISSING_SOURCE":
            raise ValueError("Johto cue was improperly certified")
        if any(cue.get(k) is not None for k in ("source_file", "repo_path", "game_path", "sha256", "license")):
            raise ValueError("Unverified Johto audio file referenced")
        if cue.get("loop_verified") is not False:
            raise ValueError("Unverified Johto audio loop")
    for kind in RULE_GROUPS:
        items = rules.get(kind)
        if not isinstance(items, list) or not items:
            raise ValueError(f"Missing Johto {kind} rules")
        values = [item.get("area" if kind == "maps" else "category" if kind == "battles" else "event") for item in items]
        if len(values) != len(set(values)):
            raise ValueError(f"Duplicate Johto {kind} rule")
        for rule in items:
            if rule.get("enabled") is not False or rule.get("pending_reason") != "NO_LICENSED_AUDIO_OR_VERIFIED_EVENT_AND_MAP":
                raise ValueError("Unverified Johto audio was enabled")
            cue = lookup.get(rule.get("cue"))
            if not cue:
                raise ValueError("Unknown Johto audio cue")
            if cue["kind"] != ("ME" if kind == "me" else "BGM"):
                raise ValueError("Wrong music kind for scene")
    if preview.get("music") != {"status": "NO_LICENSED_AUDIO", "cues": len(cues), "rules_enabled": 0}:
        raise ValueError("Johto portal/audio catalogs disagree")
    return {
        "region": "JOHTO", "phase": "15/16", "status": "PASS_SAFE_PREVIEW",
        "cues": len(cues),
        "bgm": sum(1 for x in cues if x["kind"] == "BGM"),
        "me": sum(1 for x in cues if x["kind"] == "ME"),
        "rules": {k: len(rules[k]) for k in RULE_GROUPS},
        "playable_maps": 0, "compiled_trainers": 0,
        "licensed_audio": 0, "enabled_music_rules": 0
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(audit(args.project), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
