"""Record real manual findings after an experimental Kanto play session.

This script writes a LOCAL report in .blue-work only. It does not fabricate a
pass from automated tests or upload personal files/saves to GitHub.
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
from audit import ROOT

CHECKS = (
    ("initial", "Nova partida abre Pallet e permite andar com os controles"),
    ("oak", "Oak oferece os 3 iniciais e Blue inicia batalha real"),
    ("old_route", "Viridian, Floresta e Pewter funcionam, incluindo Brock"),
    ("route3", "Rota 3: saída de Pewter, treinadores e caminho de volta"),
    ("moon", "Mt. Moon: andares, escadas, encontros e saídas"),
    ("cerulean", "Rota 4 e Cerulean: entradas, Pokémon Center e retorno"),
    ("misty", "Ginásio de Cerulean: treinador e batalha real com Misty"),
    ("cascade", "Cascade Badge dada uma vez, sem duplicação ou travamento"),
    ("save", "Salvar, sair, voltar e recuperar mapa, equipe, badges e itens"),
    ("safety", "Save e instalação original de Decades permaneceram intactos"),
)


def write_report(checks: dict[str, str], notes: str, folder: Path) -> Path:
    workspace = (ROOT / ".blue-work").resolve()
    folder = folder.resolve()
    if folder != workspace and not folder.is_relative_to(workspace):
        raise ValueError("O relatório experimental deve ficar dentro de .blue-work")
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    report = folder / f"kanto-experimental-{stamp}.md"
    lines = ["# Kanto — sessão experimental Windows",
             f"Data UTC: {datetime.now(timezone.utc).isoformat()}",
             "Relatório local não enviado ao GitHub.",
             "A CI não substitui a observação de jogabilidade.", "",
             "## Checklist do jogador"]
    for key, text in CHECKS:
        state = checks.get(key, "not_tested")
        checked = "x" if state == "pass" else " "
        suffix = " — FALHOU" if state == "fail" else (" — NÃO TESTADO" if state == "not_tested" else "")
        lines.append(f"- [{checked}] {text}{suffix}")
    lines.extend(["", "## Problemas e observações", notes or "Nenhuma anotação.", ""])
    report.write_text("\n".join(lines), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".blue-work/kanto-gui-reports")
    parser.add_argument("--no-prompt", action="store_true", help="Só gerar template pendente, para testes")
    args = parser.parse_args()
    answers = {}
    if not args.no_prompt and sys.stdin.isatty():
        print("\n=== RELATÓRIO DE JOGABILIDADE KANTO ===")
        print("Marque apenas o que você realmente verificou. S=passou, F=falhou, N=não testei.")
        for key, label in CHECKS:
            while True:
                answer = input(f"[{key}] {label} [S/F/N]: ").strip().lower()
                if answer in ("", "n", "s", "f"):
                    answers[key] = {"s":"pass", "f":"fail", "n":"not_tested", "":"not_tested"}[answer]
                    break
        notes = input("Descreva bug, mapa, NPC e erro (opcional): ").strip()
    else:
        notes = ""
    try:
        result = write_report(answers, notes, args.output)
    except (OSError, ValueError) as e:
        print(f"[ERRO] {e}", file=sys.stderr)
        return 2
    print(f"[RELATÓRIO] {result}")
    print("[INFO] Os resultados não foram enviados ao GitHub.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
