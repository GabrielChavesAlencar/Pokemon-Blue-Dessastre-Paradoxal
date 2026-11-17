#!/usr/bin/env python3
"""S24: catalogo musical por cenario, somente leitura; nenhum audio e instalado."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/music"))
import audit_sinnoh_music_ch16 as ch16

FILES = {
    "matrix": ROOT / "data/regions/sinnoh-music-s24.json",
    "catalog": ROOT / "data/regions/sinnoh-music-ch16.json",
    "document": ROOT / "docs/SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md",
    "blue": ROOT / "scripts/music/BlueMusic.rb",
    "adapter": ROOT / "scripts/music/SinnohMusicContracts.rb",
    "regions": ROOT / "site/public/data/regions.json",
}
GUARDS = {
  "city": "VERIFIED_MAP_ID_AND_REGION",
  "route": "VERIFIED_MAP_ID_AND_REGION",
  "cave": "VERIFIED_MAP_ID_AND_REGION",
  "post_game": "VERIFIED_MAP_ID_AND_REGION",
  "scene": "VERIFIED_SCENE_AND_EVENT_OWNER",
  "battle": "VERIFIED_BATTLE_AND_REGION",
  "transport": "VERIFIED_SURF_EVENT_AND_REGION",
  "me": "COMMITTED_EVENT_RESULT_AND_REGION"
}
META = {
    "schema": 1, "region": "SINNOH", "stage": "S24",
    "status": "COMPLETE_SCENARIO_INDEX_NOT_PLAYABLE",
    "source_catalog": "data/regions/sinnoh-music-ch16.json",
    "source_document": "docs/SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md",
    "blue_music_runtime": "scripts/music/BlueMusic.rb",
    "cues_expected": 46, "native_binding_count": 0,
    "verified_recordings": 0, "licensed_recordings": 0, "byte_assets_added": 0,
    "active_in_bluemusic": False, "autoplay_enabled": False,
    "install_allowed": False, "game_exe_tested": False, "joiplay_tested": False,
    "native_qa_approved": False,
    "credits_requirement": "AUTHOR_SOURCE_LICENSE_AND_REDISTRIBUTION_CONSENT_REQUIRED",
    "rule": "Catalogação simbólica completa; não autoriza cópia, distribuição ou reprodução de áudio de terceiros.",
}
NULL_FIELDS = (
    "file", "sha256", "composer_or_arranger", "rights_holder",
    "license", "source_url", "redistribution_consent", "attribution",
    "physical_map_id", "physical_event_id"
)

def fail(msg):
    raise ValueError("SINNOH_S24_BLOCKED: " + msg)

def expected_scenarios(source):
    rows = []
    for cue in source["cues"]:
        rows.append({
            "cue": cue["key"],
            "historical_source_key": cue["source_key"],
            "context": cue["key"].removeprefix("SINNOH_").replace("_", " ").title(),
            "scope": cue["scope"], "kind": cue["kind"],
            "time_window": cue["time_window"], "priority": cue["priority"],
            "trigger_guard": GUARDS[cue["scope"]], "fallback": cue["fallback"],
            **{k: None for k in NULL_FIELDS},
            "compiled_hook": False, "enabled": False, "audit_only": True,
        })
    return rows

def audit(matrix, source, document, blue, adapter, registry):
    proof = ch16.audit(source, document, blue, adapter, registry)
    if (len(source["cues"]) != 46 or
            len({c["key"] for c in source["cues"]}) != 46):
        fail("catalogo CH16 nao tem 46 cues unicos")
    if not isinstance(matrix, dict) or set(matrix) != set(META) | {"scenarios"}:
        fail("campos da matriz faltantes/desconhecidos")
    for key, target in META.items():
        if type(matrix[key]) is not type(target) or matrix[key] != target:
            fail("direitos/instalacao/native QA falsificados: " + key)
    wanted = expected_scenarios(source)
    actual = matrix["scenarios"]
    if not isinstance(actual, list) or len(actual) != len(wanted):
        fail("cenarios ausentes ou adicionais")
    for row, exp in zip(actual, wanted):
        if (not isinstance(row, dict) or set(row) != set(exp) or
                any(type(row[k]) is not type(v) or row[k] != v
                    for k, v in exp.items())):
            fail("cue/associacao/licenca/gancho falsificado: " + exp["cue"])
    groups = dict(Counter(row["scope"] for row in actual))
    if groups != proof["by_scope"]:
        fail("grupos nao coincidem com CH16")
    return {
        "region": "SINNOH", "stage": "S24",
        "status": META["status"], "scenario_count": len(actual),
        "by_scope": groups,
        "bgm_count": sum(x["kind"] == "BGM" for x in actual),
        "me_count": sum(x["kind"] == "ME" for x in actual),
        "historical_source_keys": len({x["historical_source_key"] for x in actual}),
        "licensed_audio": 0, "native_bindings": 0,
        "install_allowed": False, "native_qa_approved": False,
    }

def run():
    return audit(
        ch16.json_file(FILES["matrix"]), ch16.json_file(FILES["catalog"]),
        ch16.read(FILES["document"]), ch16.read(FILES["blue"]),
        ch16.read(FILES["adapter"]), ch16.json_file(FILES["regions"])
    )

def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        result = run()
    except (ValueError, OSError, TypeError, KeyError) as e:
        print(str(e), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("SINNOH_S24_CATALOG_OK_OFFLINE_ONLY")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
