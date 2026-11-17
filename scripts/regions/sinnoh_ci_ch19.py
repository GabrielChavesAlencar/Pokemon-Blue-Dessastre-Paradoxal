#!/usr/bin/env python3
"""CH19: regressao exclusivamente offline de Sinnoh, sem Game.exe/JoiPlay.

O resultado e FAIL-CLOSED: uma falha/timeout/runner ausente nao vira sucesso.
Kanto e Johto pertencem a jobs distintos e nunca sao usados para aprovar Sinnoh.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable

PYTHON_CHECKS = [
    ("sinnoh-python-unit", [PY, "-m", "unittest", "discover", "-s", "tests", "-p", "test_sinnoh_*.py", "-v"]),
    ("sinnoh-progress-consistency", [PY, "scripts/regions/validate_sinnoh_chat_progress.py"]),
    ("sinnoh-source-audit", [PY, "scripts/regions/audit_sinnoh_source.py"]),
    ("sinnoh-b00-file-intake", [PY, "scripts/regions/audit_sinnoh_b00_intake.py"]),
    ("sinnoh-b01-inventory-syntax", [PY, "-m", "py_compile", "scripts/regions/audit_sinnoh_b01_inventory.py"]),
    ("sinnoh-b02-regional-reservations", [PY, "scripts/regions/audit_sinnoh_b02_reservations.py"]),
    ("sinnoh-b03-installer-tilesets-preflight", [PY, "scripts/regions/audit_sinnoh_b03_installer_evidence.py"]),
    ("sinnoh-b04-local-provenance-preflight", [PY, "scripts/regions/audit_sinnoh_b04_provenance.py"]),
    ("sinnoh-b05-multiregion-mapid-planning", [PY, "scripts/regions/audit_sinnoh_b05_mapid_planning.py"]),
    ("sinnoh-b06-real-technical-candidate", [PY, "scripts/regions/audit_sinnoh_b06_technical_candidate.py"]),
    ("sinnoh-b07-private-geometry-preflight", [PY, "scripts/regions/build_sinnoh_b07_private_stage.py"]),
    ("sinnoh-b08-private-qa-preflight", [PY, "scripts/regions/audit_sinnoh_b08_private_qa.py"]),
    ("sinnoh-s07-remap-reconciliation-syntax", [PY, "-m", "py_compile", "scripts/regions/sinnoh_s07_reconcile.py"]),
    ("sinnoh-badges-hms-audit", [PY, "scripts/regions/audit_sinnoh_badges_hms.py"]),
    ("sinnoh-s15-gyms-audit", [PY, "scripts/regions/audit_sinnoh_s15_gyms.py"]),
    ("sinnoh-s16-local-hms", [PY, "scripts/regions/audit_sinnoh_s16_hms.py"]),
    ("sinnoh-s13-intro-audit", [PY, "scripts/regions/audit_sinnoh_s13_intro.py"]),
    ("sinnoh-s14-starters-audit", [PY, "scripts/regions/audit_sinnoh_s14_starters.py"]),
    ("sinnoh-s31-acceptance-report", [PY, "scripts/regions/audit_sinnoh_s31_acceptance.py"]),
    ("sinnoh-story-audit", [PY, "scripts/regions/audit_sinnoh_story_ch14.py"]),
    ("sinnoh-teams-audit", [PY, "scripts/regions/audit_sinnoh_teams_ch15.py"]),
    ("sinnoh-s17-balance-contract", [PY, "scripts/regions/audit_sinnoh_s17_balance.py"]),
    ("sinnoh-s18-wild-contract", [PY, "scripts/regions/audit_sinnoh_s18_wild.py"]),
    ("sinnoh-s19-galactic-contract", [PY, "scripts/regions/audit_sinnoh_s19_galactic.py"]),
    ("sinnoh-s20-distortion-contract", [PY, "scripts/regions/audit_sinnoh_s20_distortion.py"]),
    ("sinnoh-s21-league-contract", [PY, "scripts/regions/audit_sinnoh_s21_league.py"]),
    ("sinnoh-s22-travel-contract", [PY, "scripts/regions/audit_sinnoh_s22_travel.py"]),
    ("sinnoh-s23-postgame-contract", [PY, "scripts/regions/audit_sinnoh_s23_postgame.py"]),
    ("sinnoh-music-audit", [PY, "scripts/music/audit_sinnoh_music_ch16.py"]),
    ("sinnoh-s24-music-catalog", [PY, "scripts/music/audit_sinnoh_music_s24.py"]),
    ("sinnoh-s25-bridge-audit", [PY, "scripts/music/audit_sinnoh_music_s25.py"]),
]

RUBY_RUNTIME = [
    ("sinnoh-pilot", ["tests/sinnoh_pilot_runtime.rb", "scripts/regions/SinnohPilot.rb"]),
    ("sinnoh-pilot-ch07", ["tests/sinnoh_pilot_ch07_runtime.rb", "scripts/regions/SinnohPilot.rb"]),
    ("sinnoh-s13-intro", ["tests/sinnoh_s13_intro_runtime.rb", "scripts/regions/SinnohPilot.rb", "scripts/regions/SinnohIntroContracts.rb", "data/regions/sinnoh-intro-s13.json"]),
    ("sinnoh-s14-starters", ["tests/sinnoh_s14_starter_runtime.rb", "scripts/regions/SinnohPilot.rb", "scripts/regions/SinnohStarterContracts.rb", "data/regions/sinnoh-starters-s14.json"]),
    ("sinnoh-barry-ch08", ["tests/sinnoh_barry_ch08_runtime.rb", "scripts/battle_polish/Campaign.rb", "scripts/regions/SinnohPilot.rb"]),
    ("sinnoh-barry-native-probe", ["tests/sinnoh_barry_native_probe_runtime.rb", "scripts/regions/SinnohBarryNativeProbe.rb"]),
    ("sinnoh-qa-start", ["tests/sinnoh_qa_start_runtime.rb", "scripts/regions/SinnohQAStart.rb"]),
    ("sinnoh-engine-fixture", ["tests/sinnoh_qa_engine_probe_runtime.rb", "scripts/regions/SinnohQAProbe.rb", "data/regions/sinnoh-twinleaf-events.json"]),
    ("sinnoh-badges-hms", ["tests/sinnoh_badge_hm_ch11_runtime.rb", "tests/regions_data_fixture.rb", "scripts/battle_polish/Regions.rb", "scripts/battle_polish/RegionTravel.rb", "scripts/battle_polish/RegionalPolicy.rb", "data/regions/sinnoh-badges-hms-contract.json"]),
    ("sinnoh-s15-gyms", ["tests/sinnoh_s15_gyms_runtime.rb", "tests/regions_data_fixture.rb", "scripts/battle_polish/Regions.rb", "scripts/regions/SinnohGymContracts.rb", "data/regions/sinnoh-gyms-s15.json"]),
    ("sinnoh-s16-hms", ["tests/sinnoh_s16_hms_runtime.rb", "tests/regions_data_fixture.rb", "scripts/battle_polish/Regions.rb", "scripts/regions/SinnohHMContracts.rb", "data/regions/sinnoh-hms-s16.json"]),
    ("sinnoh-evolution", ["tests/sinnoh_evolution_ch12_runtime.rb", "tests/regions_data_fixture.rb", "scripts/battle_polish/Regions.rb", "scripts/battle_polish/EvolutionScaling.rb", "scripts/battle_polish/Story.rb", "scripts/battle_polish/Campaign.rb", "data/regions/sinnoh-trainer-evolution-contract.json"]),
    ("sinnoh-s17-trainers", ["tests/sinnoh_s17_trainer_balance_runtime.rb", "tests/sinnoh_evolution_ch12_runtime.rb", "tests/regions_data_fixture.rb", "scripts/battle_polish/Regions.rb", "scripts/battle_polish/EvolutionScaling.rb", "scripts/battle_polish/Story.rb", "scripts/battle_polish/Campaign.rb", "data/regions/sinnoh-trainer-evolution-contract.json"]),
    ("sinnoh-s18-wild", ["tests/sinnoh_s18_wild_runtime.rb", "tests/sinnoh_evolution_ch12_runtime.rb", "tests/regions_data_fixture.rb", "scripts/battle_polish/Regions.rb", "scripts/battle_polish/EvolutionScaling.rb", "scripts/battle_polish/Story.rb", "scripts/battle_polish/Campaign.rb", "data/regions/sinnoh-trainer-evolution-contract.json"]),
    ("sinnoh-story", ["tests/sinnoh_story_ch14_runtime.rb", "tests/regions_data_fixture.rb", "scripts/battle_polish/Regions.rb", "scripts/battle_polish/RegionTravel.rb", "scripts/regions/SinnohStoryContracts.rb", "data/regions/sinnoh-story-ch14-contract.json"]),
    ("sinnoh-s19-galactic", ["tests/sinnoh_s19_galactic_runtime.rb", "tests/regions_data_fixture.rb", "scripts/battle_polish/Regions.rb", "scripts/regions/SinnohStoryContracts.rb", "scripts/regions/SinnohGalacticContracts.rb", "data/regions/sinnoh-galactic-s19.json"]),
    ("sinnoh-s20-distortion", ["tests/sinnoh_s20_distortion_runtime.rb", "tests/regions_data_fixture.rb", "scripts/battle_polish/Regions.rb", "scripts/regions/SinnohStoryContracts.rb", "scripts/regions/SinnohDistortionContracts.rb", "data/regions/sinnoh-distortion-s20.json"]),
    ("sinnoh-s21-league", ["tests/sinnoh_s21_league_runtime.rb", "tests/regions_data_fixture.rb", "scripts/battle_polish/Regions.rb", "scripts/regions/SinnohStoryContracts.rb", "scripts/regions/SinnohLeagueContracts.rb", "data/regions/sinnoh-league-s21.json"]),
    ("sinnoh-s22-travel", ["tests/sinnoh_s22_travel_runtime.rb", "tests/regions_data_fixture.rb", "scripts/battle_polish/Regions.rb", "scripts/battle_polish/RegionTravel.rb", "scripts/regions/SinnohStoryContracts.rb", "scripts/regions/SinnohTravelContracts.rb", "data/regions/sinnoh-travel-s22.json"]),
    ("sinnoh-s23-postgame", ["tests/sinnoh_s23_postgame_runtime.rb", "tests/regions_data_fixture.rb", "scripts/battle_polish/Regions.rb", "scripts/regions/SinnohStoryContracts.rb", "scripts/regions/SinnohPostgameContracts.rb", "data/regions/sinnoh-postgame-s23.json"]),
    ("sinnoh-music", ["tests/sinnoh_music_ch16_runtime.rb", "scripts/music/BlueMusic.rb", "scripts/music/SinnohMusicContracts.rb", "data/regions/sinnoh-music-ch16.json"]),
    ("sinnoh-music-s26", ["tests/sinnoh_s26_music_regression.rb", "scripts/music/BlueMusic.rb", "scripts/music/SinnohMusicContracts.rb", "data/regions/sinnoh-music-ch16.json"]),
    ("sinnoh-s25-bridge", ["tests/sinnoh_s25_music_runtime.rb", "scripts/music/BlueMusic.rb", "scripts/music/SinnohMusicContracts.rb", "scripts/music/SinnohBlueMusicBridge.rb", "data/regions/sinnoh-music-ch16.json", "data/regions/sinnoh-music-s25.json"]),
]
RUBY_SYNTAX = [
    "scripts/regions/SinnohPilot.rb",
    "scripts/regions/SinnohIntroContracts.rb",
    "scripts/regions/SinnohStarterContracts.rb",
    "scripts/regions/SinnohQAStart.rb",
    "scripts/regions/SinnohQAProbe.rb",
    "scripts/regions/SinnohBarryNativeProbe.rb",
    "scripts/regions/SinnohStoryContracts.rb",
    "scripts/regions/SinnohGymContracts.rb",
    "scripts/regions/SinnohHMContracts.rb",
    "scripts/regions/SinnohGalacticContracts.rb",
    "scripts/regions/SinnohDistortionContracts.rb",
    "scripts/regions/SinnohLeagueContracts.rb",
    "scripts/regions/SinnohTravelContracts.rb",
    "scripts/regions/SinnohPostgameContracts.rb",
    "scripts/music/SinnohMusicContracts.rb",
    "scripts/music/SinnohBlueMusicBridge.rb",
    "scripts/battle_polish/Regions.rb",
    "scripts/battle_polish/RegionTravel.rb",
    "scripts/battle_polish/RegionalPolicy.rb",
    "scripts/battle_polish/Campaign.rb",
    "scripts/battle_polish/Story.rb",
    "scripts/battle_polish/EvolutionScaling.rb",
]
RUBY_CHECKS = [
    *[(f"ruby-syntax-{Path(name).stem}", ["ruby", "-c", name]) for name in RUBY_SYNTAX],
    *[(label, ["ruby", *args]) for label, args in RUBY_RUNTIME],
]

# Diferentes tipos de evidencias nao podem ser promovidos a certificacao nativa.
EVIDENCE_LEVEL = "offline_synthetic"
NATIVE_FIELDS = {
    "game_exe_executed": False,
    "joiplay_executed": False,
    "native_qa_approved": False,
    "native_maps_verified": False,
    "gameplay_certified": False,
}


def run_check(label: str, command: list[str], cwd: Path, timeout: int = 240) -> dict:
    """Roda uma verificacao, sempre devolvendo um status verificavel."""
    if not label or not command:
        raise ValueError("CH19 exige nome e comando")
    result = {"id": label, "command": command, "status": "blocked", "returncode": None, "tail": ""}
    executable = command[0]
    if not (Path(executable).is_file() or shutil.which(executable)):
        result["tail"] = f"Runner ausente: {executable}"
        return result
    try:
        process = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                                 timeout=timeout, errors="replace", check=False)
    except subprocess.TimeoutExpired as exc:
        result.update(status="failed", tail=f"Tempo excedido ({timeout}s): {str(exc)[:200]}")
        return result
    except (OSError, ValueError) as exc:
        result["tail"] = f"Nao foi possivel executar: {exc}"
        return result
    result["returncode"] = process.returncode
    result["status"] = "passed" if process.returncode == 0 else "failed"
    output = ((process.stdout or "") + "\n" + (process.stderr or "")).strip()
    result["tail"] = output[-2500:]
    return result


def summarize(suite: str, results: list[dict]) -> dict:
    if suite not in ("python", "ruby"):
        raise ValueError("suite nao pertence a Sinnoh")
    if not results:
        raise ValueError("suite vazia nunca e aprovada")
    statuses = [r["status"] for r in results]
    if any(s not in ("passed", "failed", "blocked") for s in statuses):
        raise ValueError("status nao reconhecido")
    # Nao confiar em 'passed' quando o processo retornou erro. Os relatórios
    # tambem precisam expor a causa, para que CI nao mascare falhas regionais.
    for row in results:
        status, code = row["status"], row.get("returncode")
        if status == "passed" and (type(code) is not int or code != 0):
            raise ValueError("CH19 resultado 'passed' sem exit code 0")
        if status == "blocked" and code is not None:
            raise ValueError("CH19 runner 'blocked' com exit code incompatível")
    state = "passed" if all(s == "passed" for s in statuses) else (
        "failed" if "failed" in statuses else "blocked"
    )
    return {
        "chapter": "CH19",
        "region": "sinnoh",
        "suite": suite,
        "scope": "sinnoh_only",
        "evidence_level": EVIDENCE_LEVEL,
        "status": state,
        "counts": {s: statuses.count(s) for s in ("passed", "failed", "blocked")},
        "external_subsystems": {"kanto": "not_run", "johto": "not_run", "hoenn": "not_run"},
        **NATIVE_FIELDS,
        "checks": results,
    }


def save_report(report: dict, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    suite = report["suite"]
    target = output / f"sinnoh-ch19-{suite}.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"# CH19 Sinnoh — {suite}",
        "",
        f"**Resultado offline:** {report['status']} — {report['counts']}",
        "",
        "**Escopo:** somente Sinnoh; Kanto/Johto/Hoenn não executados neste job.",
        "**QA nativo:** não executado; este relatório não certifica Game.exe/JoiPlay.",
        "",
        "| Verificação | Resultado | Exit code |",
        "|---|---|---|",
    ]
    for check in report["checks"]:
        lines.append(f"| {check['id']} | {check['status']} | {check['returncode']} |")
    (output / f"sinnoh-ch19-{suite}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", required=True, choices=("python", "ruby"))
    parser.add_argument("--output", default=".blue-work/sinnoh-ch19")
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args(argv)
    if args.timeout < 1:
        parser.error("--timeout deve ser positivo")
    checks = PYTHON_CHECKS if args.suite == "python" else RUBY_CHECKS
    results = []
    for label, command in checks:
        r = run_check(label, command, ROOT, args.timeout)
        results.append(r)
        print(f"CH19 {args.suite}: {label} = {r['status']} ({r['returncode']})", flush=True)
        if r["status"] != "passed":
            print(r["tail"], file=sys.stderr, flush=True)
    report = summarize(args.suite, results)
    report["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["git_sha"] = os.environ.get("GITHUB_SHA", "local-unverified")
    save_report(report, Path(args.output))
    print(f"CH19_SCOPE=sinnoh_only CH19_STATUS={report['status']} NATIVE_QA=false")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
