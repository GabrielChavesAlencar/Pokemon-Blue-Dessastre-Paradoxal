#!/usr/bin/env python3
"""S30: auditar a cobertura da suite offline de Sinnoh SEM executar o jogo.

O manifesto apenas confirma fontes e contratos do repositorio. O resultado
dos jobs Python, Ruby, portal e Android pertence ao GitHub Actions e nao pode
ser substituido por este relatorio. Nenhum MapID e reservado ou importado.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts.regions import sinnoh_ci_ch19 as ci

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = {
    "python": (
        "scripts/regions/sinnoh_ci_ch19.py",
        "scripts/regions/validate_sinnoh_chat_progress.py",
        "tests/test_sinnoh_ci_ch19.py",
        "tests/test_sinnoh_progress.py",
        "tests/test_sinnoh_graph.py",
        "tests/test_sinnoh_android_ch20.py",
        "tests/test_sinnoh_playtest_audit.py",
        "tests/test_sinnoh_s30_suite.py",
    ),
    "ruby": (
        "tests/sinnoh_pilot_runtime.rb",
        "tests/sinnoh_barry_ch08_runtime.rb",
        "tests/sinnoh_story_ch14_runtime.rb",
        "tests/sinnoh_music_ch16_runtime.rb",
        "scripts/battle_polish/Campaign.rb",
    ),
    "portal": (
        "site/package.json",
        "site/scripts/sinnoh-guide.mjs",
        "site/src/assets/sinnoh-guide.js",
        "site/tests/sinnoh-guide.test.mjs",
        "site/tests/sinnoh-search.test.mjs",
        "site/tests/sinnoh-s27-development.test.mjs",
        "site/tests/sinnoh-s29-dynamic-levels.test.mjs",
    ),
    "contracts": (
        "data/regions/sinnoh-progress.json",
        "data/regions/sinnoh-source.json",
        "data/regions/sinnoh-twinleaf-events.json",
        "site/public/data/regions.json",
        ".github/workflows/sinnoh-ch19.yml",
        ".github/workflows/sinnoh-ch20.yml",
        ".github/workflows/sinnoh-s30.yml",
    ),
}

NATIVE_FIELDS = (
    "technically_approved", "playable_in_game_executable", "fully_tested_native",
)


def fail(message: str) -> None:
    raise ValueError("SINNOH_S30_BLOCKED: " + message)


def collect(root: Path = ROOT) -> dict:
    """Fail closed for missing tests, altered scopes or fabricated QA evidence."""
    root = root.resolve()
    hashed = {}
    for group, paths in REQUIRED.items():
        hashed[group] = {}
        for rel in paths:
            file = root / rel
            if (file.is_symlink() or not file.is_file()
                    or not file.resolve().is_relative_to(root)):
                fail("arquivo obrigatorio ausente/inseguro: " + rel)
            hashed[group][rel] = hashlib.sha256(file.read_bytes()).hexdigest()

    progress = json.loads((root / "data/regions/sinnoh-progress.json").read_text("utf-8"))
    if progress.get("region") != "SINNOH":
        fail("regiao adulterada")
    tasks = progress.get("tasks", [])
    if ([row.get("id") for row in tasks] != [f"S{i:02}" for i in range(1, 33)]
            or any(row.get("status") not in ("done", "partial", "pending")
                   for row in tasks)):
        fail("tarefas S01-S32 inconsistentes")
    counts = {s: sum(t["status"] == s for t in tasks)
              for s in ("done", "partial", "pending")}
    dev = progress.get("development", {})
    if (dev.get("total") != 32 or
            any(dev.get(s) != n for s, n in counts.items()) or
            dev.get("percent_complete") != 100 * counts["done"] // 32):
        fail("contadores da Barra A inconsistentes")
    status_by_id = {row["id"]: row["status"] for row in tasks}
    if status_by_id["S30"] != "done":
        fail("S30 deve ter evidencia auditada antes de ser concluida")
    if status_by_id["S31"] != "done":
        if any(progress.get("phase_gates", {}).get(s) != 0 for s in NATIVE_FIELDS):
            fail("aprovacao nativa sem aceite S31")
    if progress.get("chat_direct_workstream", {}).get("done") != 20:
        fail("Barra E inesperada")
    if (progress.get("native_playtest_workstream", {}).get("native_qa_approved") is True
            and status_by_id["S31"] != "done"):
        fail("playtest nativo promovido sem aceite")
    region = json.loads((root / "site/public/data/regions.json").read_text("utf-8"))
    if region.get("regions", {}).get("SINNOH", {}).get("status") != "planned":
        fail("Sinnoh erroneamente anunciada como jogavel")
    source = json.loads((root / "data/regions/sinnoh-source.json").read_text("utf-8"))
    if source.get("import_control", {}).get("imports_enabled") is not False:
        fail("importacao de mapas ativada indevidamente")
    if ("test_sinnoh_*.py" not in " ".join(ci.PYTHON_CHECKS[0][1])
            or "test_*.py" in " ".join(ci.PYTHON_CHECKS[0][1])
            or not any(name == "sinnoh-progress-consistency"
                       for name, _ in ci.PYTHON_CHECKS)):
        fail("descoberta Python de Sinnoh insegura")
    if (not any(name == "sinnoh-story" for name, _ in ci.RUBY_CHECKS)
            or not any(name == "sinnoh-music" for name, _ in ci.RUBY_CHECKS)
            or any("Game.exe" in " ".join(command) or "JoiPlay" in " ".join(command)
                   for _, command in ci.RUBY_CHECKS)):
        fail("comandos Ruby nao isolados")
    workflow = (root / ".github/workflows/sinnoh-s30.yml").read_text("utf-8")
    for signature in ("S30 / Manifesto", "S30 / Python", "S30 / Ruby",
                      "S30 / Portal", "S30 / Android estatico",
                      "npm run build", "npm test", "sinnoh_ci_ch19.py",
                      "audit_sinnoh_android_ch20.py"):
        if signature not in workflow:
            fail("workflow S30 sem gate obrigatorio: " + signature)

    return {
        "schema": 1,
        "region": "SINNOH",
        "task": "S30",
        "status": "ready_for_ci_not_native_verified",
        "scope": "offline_contracts_only",
        "groups": {name: {"files": len(items), "sha256": items}
                   for name, items in hashed.items()},
        "python_checks_declared": len(ci.PYTHON_CHECKS),
        "ruby_checks_declared": len(ci.RUBY_CHECKS),
        "development_counts": counts,
        "native_game_exe_tested": False,
        "joiplay_tested": False,
        "native_qa_approved": False,
        "ci_jobs_verified_by_manifest": False,
        "note": "Somente CI externo valida jobs; este manifesto NAO aprova gameplay.",
    }


def summary(report: dict) -> str:
    if (report.get("task") != "S30" or
            report.get("status") != "ready_for_ci_not_native_verified" or
            any(report.get(field) is not False for field in (
                "native_game_exe_tested", "joiplay_tested",
                "native_qa_approved", "ci_jobs_verified_by_manifest"))):
        fail("relatorio adulterado ou certificado falsamente")
    lines = [
        "# Sinnoh S30 - suite automatizada offline",
        "",
        "**Status:** manifesto pronto para CI; sem certificacao jogavel.",
        "**Testes no Game.exe/JoiPlay:** nao executados.",
        "",
        "| Grupo | Arquivos auditados |",
        "|---|---:|",
    ]
    for key, group in report["groups"].items():
        lines.append(f"| {key} | {group['files']} |")
    lines += ["", "**Criterio para concluir S30:** jobs Python, Ruby, Portal e Android",
              "estatico aprovados em GitHub Actions e PR integrado.",
              "**Barras nativas:** NAO alteradas.", ""]
    return "\n".join(lines)


def write_report(report: dict, path: Path, root: Path = ROOT) -> None:
    root = root.resolve()
    destination = path if path.is_absolute() else root / path
    destination = destination.absolute()
    allowed = (root / ".blue-work/sinnoh-s30").resolve()
    if (destination.is_symlink() or not destination.parent.resolve().is_relative_to(allowed)
            or not destination.name.endswith(".json") or destination.exists()
            or destination.with_suffix(".md").exists()
            or destination.with_suffix(".md").is_symlink()):
        fail("saida fora da pasta privada, symlink ou sobrescrita")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    destination.with_suffix(".md").write_text(summary(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=".blue-work/sinnoh-s30/manifest.json")
    args = parser.parse_args()
    try:
        report = collect()
        write_report(report, Path(args.output))
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(str(exc))
        return 1
    print("SINNOH_S30_MANIFEST_OK_OFFLINE_ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
