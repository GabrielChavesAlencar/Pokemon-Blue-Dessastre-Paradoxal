#!/usr/bin/env python3
"""Validate Sinnoh ChatGPT progress without modifying game files or ledgers."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATES = ("done", "partial", "pending")
NUM_TASKS = 20
LEDGER = "data/regions/sinnoh-progress.json"
PANEL = "docs/SINNOH_PROGRESSO.md"
MAP = "docs/SINNOH_MAPEAMENTO_EXECUCAO_CHAT_MAIN_2026-11-16.md"


def section(markdown: str, heading: str) -> str | None:
    match = re.search(
        r"(?ms)^## " + re.escape(heading) + r"[ \t]*\n(.*?)(?=^## |\Z)",
        markdown,
    )
    return match.group(1) if match else None


def markdown_bar(body: str, label: str, expected: tuple[int, int, int],
                 errors: list[str], exact_cells: bool = False) -> None:
    match = re.search(
        r"(?m)^([█░]+)\s+(\d+)/(\d+)\s+\((\d+)%\)\s*$", body
    )
    if not match:
        errors.append(label + ": barra ausente ou ilegível")
        return
    cells, *numbers = match.groups()
    actual = tuple(int(x) for x in numbers)
    if actual != expected:
        errors.append(f"{label}: barra {actual}, esperado {expected}")
    if exact_cells:
        filled = expected[0] * NUM_TASKS // expected[1]
        correct = "█" * filled + "░" * (NUM_TASKS - filled)
        if cells != correct:
            errors.append(label + ": preenchimento gráfico incompatível")


def norm(value: str) -> str:
    return value.replace("*", "").replace(chr(96), "").strip()


def validate(root: Path = ROOT) -> list[str]:
    """Return human-readable contract failures; does not write files."""
    errors: list[str] = []
    try:
        record = json.loads((root / LEDGER).read_text(encoding="utf-8"))
        panel = (root / PANEL).read_text(encoding="utf-8")
        mapping = (root / MAP).read_text(encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"arquivos de progresso indisponíveis/inválidos: {exc}"]

    work = record.get("chat_direct_workstream")
    if not isinstance(work, dict):
        return ["chat_direct_workstream ausente ou inválido"]
    tasks = work.get("tasks")
    if not isinstance(tasks, list):
        return ["chat_direct_workstream.tasks não é lista"]
    expected_ids = [f"CH{i:02d}" for i in range(1, NUM_TASKS + 1)]
    ids = [row.get("id") if isinstance(row, dict) else None for row in tasks]
    if ids != expected_ids:
        errors.append("IDs CH01–CH20 devem ser únicos, completos e ordenados")
    counts = {state: 0 for state in STATES}
    for i, item in enumerate(tasks):
        if not isinstance(item, dict):
            errors.append(f"tarefa {i + 1}: não é objeto")
            continue
        task_id = item.get("id", f"índice {i}")
        status = item.get("status")
        if status not in STATES:
            errors.append(f"{task_id}: status desconhecido: {status}")
            continue
        counts[status] += 1
        if item.get("priority") not in ("P0", "P1", "P2", "P3", "P4"):
            errors.append(f"{task_id}: prioridade inválida")
        for field in ("title", "acceptance"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{task_id}: campo {field} vazio")
        if status == "done":
            evidence = item.get("evidence_path")
            if not isinstance(evidence, str) or not evidence.strip():
                errors.append(f"{task_id}: concluído sem evidência")
            else:
                source = (root / evidence).resolve()
                if not source.is_relative_to(root.resolve()) or not source.is_file():
                    errors.append(f"{task_id}: evidência ausente ou fora do repositório")

    done, partial, pending = (counts[s] for s in STATES)
    percent = 100 * done // NUM_TASKS
    expected = (done, NUM_TASKS, percent)
    if len(tasks) != NUM_TASKS or sum(counts.values()) != NUM_TASKS:
        errors.append("total real de tarefas diferente de 20")
    for key, value in {
        "total": NUM_TASKS, "done": done, "partial": partial,
        "pending": pending, "percent_complete": percent,
    }.items():
        if type(work.get(key)) is not int or work[key] != value:
            errors.append(f"chat_direct_workstream.{key}: esperado {value}")
    if work.get("not_gameplay_progress") is not True:
        errors.append("Barra E não pode representar progresso jogável")
    if work.get("technical_and_gameplay_gates_unchanged") is not True:
        errors.append("Contrato de preservação dos gates ausente")
    for key, location in (("documentation", MAP), ("progress_panel", PANEL)):
        if work.get(key) != location:
            errors.append(f"chat_direct_workstream.{key}: caminho inválido")

    panel_e = section(panel, "Barra E — novas entregas diretas pelo ChatGPT na main")
    mapping_e = section(mapping, "2. Nova Barra E — trabalho que pode ser concluído pelo chat")
    if panel_e is None:
        errors.append("painel: seção Barra E ausente")
    else:
        markdown_bar(panel_e, "painel Barra E", expected, errors, exact_cells=True)
        for key, value in (("Concluídas", done), ("Parciais", partial), ("Pendentes", pending)):
            got = re.search(r"(?m)^-\s+\*\*" + re.escape(key) + r":\*\*\s+(\d+)", panel_e)
            if not got or int(got.group(1)) != value:
                errors.append(f"painel Barra E: contador {key} incorreto")

    if mapping_e is None:
        errors.append("mapeamento: seção 2/Barra E ausente")
    else:
        markdown_bar(mapping_e, "mapeamento Barra E", expected, errors, exact_cells=True)
        for state, value, name in (
            ("done", done, "concluídas?"), ("partial", partial, "parciais"),
            ("pending", pending, "pendentes?"),
        ):
            got = re.search(r"\*\*(\d+)\s+" + name + r"\*\*", mapping_e)
            if not got or int(got.group(1)) != value:
                errors.append(f"mapeamento: contador {state} incorreto")
        rows = []
        for line in mapping_e.splitlines():
            if re.match(r"^\|\s*P[0-4]\s*\|", line):
                columns = [x.strip() for x in line.split("|")[1:-1]]
                if len(columns) != 4:
                    errors.append("mapeamento: linha da tabela inválida")
                else:
                    rows.append(columns)
        if len(rows) != NUM_TASKS:
            errors.append(f"mapeamento: esperado 20 linhas CH, encontradas {len(rows)}")
        else:
            for item, columns in zip(tasks, rows):
                if not isinstance(item, dict):
                    continue
                priority, marked_id, title, acceptance = columns
                found = re.findall(r"\bCH\d{2}\b", marked_id)
                if found != [item.get("id")] or priority != item.get("priority"):
                    errors.append(f"mapeamento: ID/prioridade incompatíveis com {item.get('id')}")
                if norm(title) != norm(str(item.get("title", ""))):
                    errors.append(f"mapeamento: título incompatível com {item.get('id')}")
                if norm(acceptance) != norm(str(item.get("acceptance", ""))):
                    errors.append(f"mapeamento: aceite incompatível com {item.get('id')}")
                icon = {"done": "✅", "partial": "🟡", "pending": ""}.get(
                    item.get("status"), ""
                )
                if (bool("✅" in marked_id) != (icon == "✅") or
                        bool("🟡" in marked_id) != (icon == "🟡")):
                    errors.append(f"mapeamento: marcador incorreto para {item.get('id')}")

    development = record.get("development", {})
    phases = record.get("phase_gates", {})
    if not isinstance(development, dict) or not isinstance(phases, dict):
        errors.append("barras A–D sem configuração")
    else:
        old_total = development.get("total")
        old_done = development.get("done")
        if (type(old_total) is not int or type(old_done) is not int or
                old_total <= 0 or not 0 <= old_done <= old_total):
            errors.append("Barra A: valores inválidos")
        else:
            old_pct = 100 * old_done // old_total
            if development.get("percent_complete") != old_pct:
                errors.append("Barra A: percentual do JSON inválido")
            block = section(panel, "Barra A — desenvolvimento aqui no GitHub")
            if block is None:
                errors.append("Barra A ausente do painel")
            else:
                markdown_bar(block, "Barra A", (old_done, old_total, old_pct), errors)
        phase_total = phases.get("total")
        if type(phase_total) is not int or phase_total <= 0:
            errors.append("Barras B/C/D: total inválido")
        else:
            for heading, field in (
                ("Barra B — fases tecnicamente aprovadas", "technically_approved"),
                ("Barra C — fases jogáveis no Game.exe", "playable_in_game_executable"),
                ("Barra D — aceitação completa Windows / Android", "fully_tested_native"),
            ):
                num = phases.get(field)
                block = section(panel, heading)
                if type(num) is not int or not 0 <= num <= phase_total or block is None:
                    errors.append(f"{heading}: configuração ausente/inválida")
                else:
                    markdown_bar(block, heading, (num, phase_total,
                                                  100 * num // phase_total), errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="raiz de um checkout do projeto (somente leitura)")
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        print("SINNOH_CHAT_PROGRESS_FAIL")
        for error in errors:
            print("- " + error)
        return 1
    obj = json.loads((args.root / LEDGER).read_text("utf-8"))
    work = obj["chat_direct_workstream"]
    print(f"SINNOH_CHAT_PROGRESS_OK {work['done']}/{work['total']} "
          f"({work['percent_complete']}%), partial={work['partial']}, "
          f"pending={work['pending']}; jogo não avaliado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
