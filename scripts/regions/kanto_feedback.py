"""Collect opt-in, LOCAL, human-observed Kanto Windows/JoiPlay QA evidence.

Nothing is sent to GitHub or elsewhere. CI never counts a report as approved
gameplay, and no auto-generated report can mark a check as 'pass'.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from audit import ROOT


SECTIONS = {
    "inicio": (
        ("initial", "Nova partida abre Pallet DENTRO da casa e aceita os controles"),
        ("oak", "Oak oferece os 3 iniciais e Blue inicia batalha real"),
        ("old_route", "Viridian, Floresta e Pewter funcionam, incluindo Brock"),
        ("route3", "Rota 3: saída de Pewter, treinadores e caminho de volta"),
        ("moon", "Mt. Moon: andares, escadas, encontros e saídas"),
        ("cerulean", "Rota 4 e Cerulean: entradas, Pokémon Center e retorno"),
        ("misty", "Ginásio de Cerulean: treinador e batalha real com Misty"),
        ("cascade", "Cascade Badge dada uma vez, sem duplicação ou travamento"),
        ("save", "Salvar, sair, voltar e recuperar mapa, equipe, badges e itens"),
        ("safety", "Save e instalação original de Decades permaneceram intactos"),
    ),
    "ginasios": (
        ("surge", "Vermilion: S.S. Anne, puzzle, Lt. Surge e Thunder Badge"),
        ("erika", "Celadon: entrar/voltar e vencer Erika para receber Rainbow"),
        ("koga", "Fuchsia: seis treinadores e Soul Badge apenas após Koga"),
        ("sabrina", "Saffron: dojo, teletransportes, Sabrina após Silph e Marsh"),
        ("silph", "Silph Co. 1F-11F, Card Key, rival e Giovanni separados"),
        ("mansion", "Pokémon Mansion: quatro andares, estátuas e Secret Key"),
        ("blaine", "Cinnabar: seis quizzes, ginásio trancado sem chave, Volcano"),
        ("giovanni", "Viridian: ginásio trancado sem 7 badges; Earth sem duplicação"),
        ("trainers", "Treinadores por visão respeitam direção, paredes e derrota"),
        ("wild", "Encontros selvagens e captura reais com nível/peso do habitat"),
        ("fishing", "Pesca/Surf não inventam níveis; Route23 fica em revisão"),
        ("hms", "HMs Flash/Cut/Surf/Strength seguem insígnias locais e obstáculos"),
        ("collision", "Portas, escadas, NPCs e tilemaps não têm softlock"),
    ),
    "liga": (
        ("route22", "Route22 acessa o portão da Liga sem pular os guardas"),
        ("route23", "Route23 tem 8 bloqueios de insígnias locais em ordem"),
        ("victory", "Victory Road 1F-3F permite travessia real e volta"),
        ("strength", "Mecanismos de Strength não exigem atalhos artificiais"),
        ("elite", "Lorelei, Bruno, Agatha e Lance lutam em ordem sem bypass"),
        ("blue", "Campeão Blue usa o time correto conforme o inicial escolhido"),
        ("defeat", "Derrota reinicia a tentativa e permite recuperação sem softlock"),
        ("hall", "Hall of Fame registra Kanto uma vez e não repete recompensa"),
        ("leader_badges", "Cartão local mostra 8 badges; cartão global soma regiões"),
    ),
    "integracao": (
        ("installed", "Game.exe integrado oferece Kanto sem mudar origem Decades"),
        ("existing_save", "Save legado Decades continua abrindo sem corrupção"),
        ("return", "NPC na cidade inicial permite ida e volta com o MESMO save"),
        ("box", "Pokémon restritos vão à box; não retornam à party antes de 8 badges"),
        ("inventory", "Dinheiro, Bag, Pokédex, equipe e PC persistem após viagem"),
        ("region_unlock", "Liga Kanto habilita apenas Johto/Decades elegíveis"),
        ("site", "Site identifica mapas prévia, oito badges e times sem informação falsa"),
        ("restart", "Salvar, fechar/reabrir e testar todos os estados anteriores"),
    ),
    "android": (
        ("joiplay_boot", "JoiPlay abre o piloto em Android sem travar em escolha"),
        ("joiplay_input", "Controles, teclas e interação de NPCs no Android funcionam"),
        ("joiplay_maps", "Mapas/tiles/transições/colisões não se corrompem no Android"),
        ("joiplay_save", "Salvar/carregar e bater/curar/capturar no Android funciona"),
    ),
}
CHECKS = tuple(item for group in SECTIONS.values() for item in group)
STATUS = frozenset({"pass", "fail", "not_tested"})
PLATFORMS = frozenset({"windows", "joiplay"})


def report_summary(checks: dict[str, str]) -> dict:
    """Counts reported observations, NEVER an acceptance certification."""
    keys = {key for key, _ in CHECKS}
    unexpected = set(checks) - keys
    if unexpected:
        raise ValueError("Checklist contém IDs desconhecidos: " + ", ".join(sorted(unexpected)))
    invalid = {key: value for key, value in checks.items() if value not in STATUS}
    if invalid:
        raise ValueError("Checklist contém estados inválidos: " + repr(invalid))
    states = {key: checks.get(key, "not_tested") for key, _ in CHECKS}
    counts = {status: sum(value == status for value in states.values()) for status in STATUS}
    return {
        "total": len(CHECKS),
        "passed_reported": counts["pass"],
        "failed_reported": counts["fail"],
        "not_tested": counts["not_tested"],
        "manual_review_required": True,
        "ci_does_not_count_as_manual_qa": True,
        "accepted_integrally": False,
    }


def write_report(
    checks: dict[str, str], notes: str, folder: Path,
    *, platform: str = "windows", scope: str = "inicio",
) -> Path:
    workspace = (ROOT / ".blue-work").resolve()
    folder = folder.resolve()
    if folder != workspace and not folder.is_relative_to(workspace):
        raise ValueError("O relatório experimental deve ficar dentro de .blue-work")
    if platform not in PLATFORMS or scope not in (*SECTIONS, "all"):
        raise ValueError("Plataforma ou seção de relatório inválida")
    result = report_summary(checks)
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    recorded_at = datetime.now(timezone.utc).isoformat()
    report = folder / f"kanto-experimental-{stamp}.md"
    lines = [
        "# Kanto — sessão experimental " + ("Windows" if platform == "windows" else "JoiPlay"),
        f"Data UTC: {recorded_at}",
        f"Seção testada: {scope}",
        "Relatório LOCAL; não enviado automaticamente ao GitHub.",
        "Resultados autorrelatados não equivalem a aceite integral.",
        "Testes nativos da CI simulam batalhas e não substituem esta observação.",
        "",
        "## Checklist do jogador",
    ]
    for group, group_checks in SECTIONS.items():
        lines.extend(["", "### " + group.capitalize()])
        for key, label in group_checks:
            state = checks.get(key, "not_tested")
            mark = "x" if state == "pass" else " "
            suffix = (" — FALHOU" if state == "fail" else
                      " — NÃO TESTADO" if state == "not_tested" else
                      " — RELATADO COMO TESTADO")
            lines.append(f"- [{mark}] {label}{suffix}")
    lines.extend([
        "", "## Resumo de observações",
        f"- {result['passed_reported']}/{result['total']} relatados como passaram",
        f"- {result['failed_reported']} falharam",
        f"- {result['not_tested']} sem teste",
        "- **Aceite integral: NÃO ATESTADO**; validar evidência manual antes de atualizar a segunda barra",
        "", "## Problemas e observações", notes or "Nenhuma anotação.", "",
    ])
    report.write_text("\n".join(lines), encoding="utf-8")
    # Machine-readable *local* companion: explicit acceptance=false, no saves,
    # passwords or user identity. The manually entered notes remain local too.
    companion = {
        "schema": 2,
        "type": "manual_observation_unreviewed",
        "date_utc": recorded_at,
        "platform": platform,
        "scope": scope,
        "checks": {key: checks.get(key, "not_tested") for key, _ in CHECKS},
        "summary": result,
        "notes": notes,
    }
    report.with_suffix(".json").write_text(
        json.dumps(companion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".blue-work/kanto-gui-reports")
    parser.add_argument("--no-prompt", action="store_true", help="Gerar template pendente, sem declarar passe")
    parser.add_argument("--scope", choices=(*SECTIONS, "all", "select"), default="select")
    parser.add_argument("--platform", choices=tuple(sorted(PLATFORMS)), default="windows")
    args = parser.parse_args()
    answers = {}
    scope = "all" if args.no_prompt else args.scope
    notes = ""
    if not args.no_prompt and sys.stdin.isatty():
        print("\n=== RELATÓRIO MANUAL DE KANTO (não enviado) ===")
        if scope == "select":
            print("Seções: " + " | ".join(f"{i+1}: {name}" for i, name in enumerate(SECTIONS)) +
                  " | A: todas")
            raw = input("Qual seção você realmente testou? [1]: ").strip().lower()
            scope = ("all" if raw == "a" else
                     list(SECTIONS)[int(raw or "1")-1] if (raw or "1").isdigit()
                     and 1 <= int(raw or "1") <= len(SECTIONS) else "inicio")
        selected = CHECKS if scope == "all" else SECTIONS[scope]
        print("S = passou de verdade | F = falhou | N/Enter = não testei")
        for key, label in selected:
            while True:
                response = input(f"[{key}] {label} [S/F/N]: ").strip().lower()
                if response in ("", "n", "s", "f"):
                    answers[key] = {"s": "pass", "f": "fail", "n": "not_tested",
                                    "": "not_tested"}[response]
                    break
        notes = input("Mapa/NPC/ações para reproduzir o problema (opcional): ").strip()
    elif scope == "select":
        scope = "all"
    try:
        result = write_report(answers, notes, args.output,
                              scope=scope, platform=args.platform)
    except (OSError, ValueError) as error:
        print(f"[ERRO] {error}", file=sys.stderr)
        return 2
    summary = report_summary(answers)
    print(f"[RELATÓRIO LOCAL] {result}")
    print(f"[OBSERVAÇÕES] {summary['passed_reported']} passaram / "
          f"{summary['failed_reported']} falharam / {summary['not_tested']} pendentes")
    print("[IMPORTANTE] Nem um relatório 100% preenchido substitui revisão de evidências.")
    print("[INFO] Dados e saves não foram enviados ao GitHub.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
