"""Monta primeiro piloto New Bark apenas se TODAS as coordenadas foram auditadas.

Só escreve em .blue-work/johto-pilot. Nunca muda game/, Kanto, Decades ou saves.
O resultado é experimental; nenhum marcador de fase jogável é criado.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from audit_johto import ROOT
from inspect_johto_pilot_readiness import assess, inspect_native, read_spec
from pilot_johto import assemble


def run(*, root: Path = ROOT) -> dict:
    root = root.resolve()
    preview = root / ".blue-work/johto-staging-interiors"
    events = root / ".blue-work/johto-new-bark-bound.json"
    connections = root / ".blue-work/johto-connections-preview.txt"
    output = root / ".blue-work/johto-pilot"
    game = root / "game"
    if output.exists() or output.is_symlink():
        raise ValueError("PILOTO existente preservado. Nao sobrescrever saves/testes")
    stage, rooms, sprites = inspect_native(preview, game, root=root)
    bound = read_spec(events)
    if not connections.is_file() or connections.is_symlink():
        raise ValueError("PBS compilado de Johto ausente; prepare a geometria primeiro")
    review = assess(stage, bound, rooms, sprites, with_connections=True,
                    connections=connections.read_text(encoding="utf-8"))
    if not review["ready_for_isolated_assembly"]:
        codes = sorted({x["problem"] for x in review["outstanding"]})
        raise ValueError("Portas/NPCs/spawn ainda pendentes: " + ", ".join(codes))
    # O montador repete auditoria SHA, IDs, eventos, sprites e PBS e mantém
    # o jogo nativo intacto. Não aceitar 'ready' como prova de gameplay.
    result = assemble(preview, game, output, bound, root=root, with_connections=True)
    if result.get("status") != "EXPERIMENTAL_COPY_ASSEMBLED_UNTESTED":
        raise ValueError("Montador retornou status inesperado")
    return {"status": result["status"], "output": str(output),
            "spawn": result["start"], "reviewed_events": review["events_ready"],
            "gameplay_playable": False, "gameplay_tested": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        result = run(root=args.root)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("[JOHTO][BLOQUEADO]", exc, file=sys.stderr)
        print("[JOHTO] Nenhum arquivo do game/ original foi alterado.", file=sys.stderr)
        return 2
    print("[JOHTO] Copia experimental criada:", result["output"])
    print("[JOHTO] Iniciar Game.exe desta copia para QA real, sem afetar saves originais.")
    print("[JOHTO] Fases jogaveis 0/13 e testadas 0/13 ate prova real.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
