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
    ("sinnoh-badges-hms-audit", [PY, "scripts/regions/audit_sinnoh_badges_hms.py"]),
    ("sinnoh-story-audit", [PY, "scripts/regions/audit_sinnoh_story_ch14.py"]),
    ("sinnoh-teams-audit", [PY, "scripts/regions/audit_sinnoh_teams_ch15.py"]),
    ("sinnoh-music-audit", [PY, "scripts/music/audit_sinnoh_music_ch16.py"]),
]

RUBY_RUNTIME = [
    ("sinnoh-pilot", ["tests/sinnoh_pilot_runtime.rb", "scripts/regions/SinnohPilot.rb"]),
    ("sinnoh-pilot-ch07", ["tests/sinnoh_pilot_ch07_runtime.rb", "scripts/regions/SinnohPilot.rb"]),
    ("sinnoh-barry-ch08", ["tests/sinnoh_barry_ch08_runtime.rb", "scripts/battle_polish/Campaign.rb", "scripts/regions/SinnohPilot.rb"]),
    ("sinnoh-barry-native-probe", ["tests/sinnoh_barry_native_probe_runtime.rb", "scripts/regions/SinnohBarryNativeProbe.rb"]),
    ("sinnoh-qa-start", ["tests/sinnoh_qa_start_runtime.rb", "scripts/regions/SinnohQAStart.rb"]),
    ("sinnoh-engine-fixture", ["tests/sinnoh_qa_engine_probe_runtime.rb", "scripts/regions/SinnohQAProbe.rb", "data/regions/sinnoh-twinleaf-events.json"]),
    ("sinnoh-badges-hms", ["tests/sinnoh_badge_hm_ch11_runtime.rb", "tests/regions_data_fixture.rb", "scripts/battle_polish/Regions.rb", "scripts/battle_polish/RegionTravel.rb", "scripts/battle_polish/RegionalPolicy.rb", "data/regions/sinnoh-badges-hms-contract.json"]),
    ("sinnoh-evolution", ["tests/sinnoh_evolution_ch12_runtime.rb", "tests/regions_data_fixture.rb", "scripts/battle_polish/Regions.rb", "scripts/battle_polish/EvolutionScaling.rb", "scripts/battle_polish/Story.rb", "scripts/battle_polish/Campaign.rb", "data/regions/sinnoh-trainer-evolution-contract.json"]),
    ("sinnoh-story", ["tests/sinnoh_story_ch14_runtime.rb", "tests/regions_data_fixture.rb", "scripts/battle_polish/Regions.rb", "scripts/battle_polish/RegionTravel.rb", "scripts/regions/SinnohStoryContracts.rb", "data/regions/sinnoh-story-ch14-contract.json"]),
    ("sinnoh-music", ["tests/sinnoh_music_ch16_runtime.rb", "scripts/music/BlueMusic.rb", "scripts/music/SinnohMusicContracts.rb", "data/regions/sinnoh-music-ch16.json"]),
]
RUBY_SYNTAX = [
    "scripts/regions/SinnohPilot.rb",
    "scripts/regions/SinnohQAStart.rb",
    "scripts/regions/SinnohQAProbe.rb",
    "scripts/regions/SinnohBarryNativeProbe.rb",
    "scripts/regions/SinnohStoryContracts.rb",
    "scripts/music/SinnohMusicContracts.rb",
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
