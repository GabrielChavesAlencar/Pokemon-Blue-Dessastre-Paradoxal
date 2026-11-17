#!/usr/bin/env python3
"""One-click Unova MapID check: find installed Decades, run A04 then A05.

No questions, no directory selection, no Ruby execution, no maps written.
A04 and A05 remain observations only; neither approves MapID allocation.
The summary text is always in .blue-work/unova/audit, and can open in Notepad.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Mapping

import audit_unova_a04_mapids as a04
import audit_unova_a05_candidates as a05

ROOT = Path(__file__).resolve().parents[2]
SUMMARY = Path(".blue-work/unova/audit/LEIA_AQUI_UNOVA_MAPIDS.txt")
MIN_NATIVE_MAPS = 20
MAX_CANDIDATE_DIR_ENTRIES = 30_000


def deny(message: str) -> None:
    raise ValueError("UNOVA_AUTO_BLOQUEADO: " + message)


def candidate_locations(
    project: Path, environ: Mapping[str, str] | None = None
) -> list[tuple[str, Path]]:
    """Fixed trusted roots, never recursive searching of Downloads/whole disks."""
    env = dict(os.environ if environ is None else environ)
    project = Path(project).absolute()
    explicit = env.get("BLUE_DECADES_GAME_DIR", "").strip().strip('"')
    if explicit:
        # If an override exists, do not silently audit another installation.
        return [("BLUE_DECADES_GAME_DIR", Path(explicit).expanduser().absolute())]
    local = env.get("LOCALAPPDATA", "").strip()
    profile = env.get("USERPROFILE", "").strip()
    roaming = env.get("APPDATA", "").strip()
    locations = []
    if local:
        locations.extend([
            ("INSTALACAO_PADRAO", Path(local)/"PokemonBlueDessastreParadoxal"/"game"),
            ("INSTALACAO_PADRAO_SEM_GAME", Path(local)/"PokemonBlueDessastreParadoxal"),
            ("APP_LOCAL_BLUE_STORY", Path(local)/"Blue-Story"/"game"),
        ])
    if profile:
        locations.append((
            "USERPROFILE_PADRAO", Path(profile)/"AppData"/"Local"/
            "PokemonBlueDessastreParadoxal"/"game"))
    if roaming:
        locations.append((
            "APPDATA_BLUE", Path(roaming)/"PokemonBlueDessastreParadoxal"/"game"))
    locations.extend([
        ("REPOSITORIO_GAME", project/"game"),
        ("REPOSITORIO_GAME_DATA", project/"game"/"Data"),
        ("REPOSITORIO_PAI_GAME", project.parent/"game"),
        ("REPOSITORIO_PAI_BLUE",project.parent/"PokemonBlueDessastreParadoxal"/"game"),
    ])
    dedup: dict[str, tuple[str, Path]] = {}
    for label, path in locations:
        absolute = path.absolute()
        key = os.path.normcase(str(absolute)).casefold()
        if key not in dedup:
            dedup[key] = (label, absolute)
    return list(dedup.values())


def examine_game(path: Path) -> tuple[Path | None, str]:
    """Conservative identity check without parsing or changing data."""
    candidate = Path(path).absolute()
    if not candidate.exists():
        return None, "não encontrado"
    try:
        if candidate.is_symlink():
            return None, "caminho é um link simbólico"
        data = a04.directory_root(candidate)
        game_dir = data.parent
        if not (game_dir/"Game.exe").is_file():
            return None, "Game.exe não encontrado junto à pasta Data"
        mapinfos = data/"MapInfos.rxdata"
        if not mapinfos.is_file() or mapinfos.is_symlink():
            return None, "MapInfos.rxdata ausente ou inseguro"
        count = 0
        total = 0
        for item in data.iterdir():
            total += 1
            if total > MAX_CANDIDATE_DIR_ENTRIES:
                return None, "pasta Data com entradas demais"
            if item.is_symlink():
                return None, "pasta Data contém link simbólico"
            if item.is_file() and a04._map_id(item.name) is not None:
                count += 1
                if count >= MIN_NATIVE_MAPS:
                    break
        if count < MIN_NATIVE_MAPS:
            return None, f"somente {count} arquivos de mapas detectados"
        # a04.scan_dir verifies every file, file size and MapInfos later.
        return game_dir, "Game.exe, MapInfos e mapa(s) detectados"
    except (ValueError, OSError, PermissionError) as exc:
        return None, "não foi possível inspecionar: " + str(exc)[:170]


def discover(
    project: Path, environ: Mapping[str, str] | None = None
) -> tuple[Path | None, list[dict], str | None]:
    candidates = candidate_locations(project, environ)
    checked: list[dict] = []
    found: dict[str, tuple[str, Path]] = {}
    for label, path in candidates:
        selected, comment = examine_game(path)
        checked.append({"label": label,"path": str(path),"result": comment,
                        "eligible": selected is not None})
        if selected is not None:
            key = os.path.normcase(str(selected.absolute())).casefold()
            found.setdefault(key, (label, selected))
    if not found:
        return None, checked, "Nenhuma instalacao com Game.exe, MapInfos e mapas foi encontrada nos locais conhecidos."
    if len(candidates)==1 and candidates[0][0]=="BLUE_DECADES_GAME_DIR":
        return next(iter(found.values()))[1],checked,None
    preferred = next(
        ((label, path) for label, path in found.values()
         if label in ("INSTALACAO_PADRAO","INSTALACAO_PADRAO_SEM_GAME",
                      "USERPROFILE_PADRAO")),None
    )
    if preferred is not None:
        # When the known installed path is valid, prefer it over stale repo copies.
        return preferred[1],checked,None
    if len(found)!=1:
        return None, checked, (
            "Foram encontradas varias instalacoes alternativas. "
            "Para evitar escolher a errada, use BLUE_DECADES_GAME_DIR "
            "com a pasta game correta."
        )
    return next(iter(found.values()))[1],checked,None


def pretty(result: dict) -> str:
    checked = result.get("candidates_checked", [])
    lines = [
        "UNOVA — AUDITORIA AUTOMATICA DE MAPIDS",
        "="*56,
        "Resultado: "+result["status"],
        "Instalacao encontrada: "+str(result.get("game_dir") or "(nenhuma)"),
        "",
    ]
    if result.get("error"):
        lines += ["BLOQUEIO: "+result["error"],""]
    a04_result=result.get("a04_result")
    a05_result=result.get("a05_result")
    if a04_result:
        lines.extend([
            "A04 — inventario da instalacao atual",
            "  Ocupados/declarados observados: "+
                str(a04_result["observed_or_declared_occupied_count"]),
            "  MapInfos SHA-256: "+
                str(a04_result["sources"]["DECADES"]["mapinfos_sha256"]),
            "  Sobreposicoes: "+str(a04_result["overlap_count"]),
            "  Relatorio completo: "+str(result["a04_report_path"]),
            "",
        ])
    if a05_result:
        lines.extend([
            "A05 — comparacao com B01/B04/B05",
            "  Historico B01: 648 ocupados",
            "  Sinnoh (retencao administrativa): 442-517 (76)",
            "  Unova bloco candidato prioritario: 518-599 (82)",
            "  Outros candidatos historicos: 92",
            "  Colisoes novas com candidatos: "+
                str(len(a05_result["a04_observed_candidate_collisions"] or [])),
            "  IDs em conflito (amostra): "+
                ", ".join(str(x) for x in
                          (a05_result["a04_observed_candidate_collisions"] or [])[:40]),
            "  Bloco 518-599 ainda desocupado nos dados observados? "+
                ("Sim" if a05_result["a04_preferred_block_observed_vacant"] else "Nao"),
            "  MapInfos atual igual ao historico? "+
                ("Sim" if a05_result["a04_snapshot_baseline_hash_matches_b05"] else "Nao"),
            "  Status: "+a05_result["status"],
            "  Relatorio completo: "+str(result["a05_report_path"]),
            "",
        ])
    lines.extend([
        "IMPORTANTE:",
        "  Esta ferramenta NAO altera Game.exe, MapInfos, mapas, scripts ou saves.",
        "  NENHUM MapID de Unova foi reservado nem certificado como livre.",
        "  A Barra A continua 0/8 ate validar reservas e instalacao real.",
        "",
        "Se precisar me enviar um arquivo, envie o relatorio A05 acima",
        "ou o A04 quando o diagnostico indicar divergencias.",
        "",
        "Pastas pesquisadas:",
    ])
    for item in checked:
        lines.append(f" - {item['label']}: {item['path']} — {item['result']}")
    return "\n".join(lines) + "\n"


def store_summary(project: Path, report: dict) -> Path:
    project = a04.safe_path(project)
    dest = project/SUMMARY
    parents=[project/".blue-work",project/".blue-work/unova",
             project/".blue-work/unova/audit"]
    for folder in parents:
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            deny("pasta privada de relatorios invalida")
        folder.mkdir(exist_ok=True)
    if dest.is_symlink():
        deny("arquivo de resumo e link simbolico")
    # Summary is a human-readable latest pointer. Original immutable
    # content-addressed A04/A05 JSON reports remain untouched.
    with dest.open("w",encoding="utf-8-sig",newline="\r\n") as file:
        file.write(pretty(report))
    return dest


def execute(project: Path, environ: Mapping[str,str] | None = None) -> dict:
    project = a04.safe_path(project)
    selected, checked, reason = discover(project,environ)
    result: dict = {
        "status":"BLOCKED_NO_AUTOMATIC_GAME_FOUND",
        "game_dir":str(selected) if selected else None,
        "candidates_checked":checked,
        "error":reason,
        "a04_result":None,"a05_result":None,
        "a04_report_path":None,"a05_report_path":None,
        "no_game_files_modified":True,
        "can_reserve_mapids":False,"can_install":False,
    }
    if selected is None:
        return result
    try:
        baseline = a04.scan_source(selected,"DECADES",base=True)
        a04_result = a04.analyze(baseline,{})
        a04_path = a04.write_private(project,a04_result)
        result["a04_report_path"]=str(a04_path)
        result["a04_result"]=a04_result
        # This links the exact A04 content-addressed report to the A05 output.
        a05_result = a05.audit(project,a04_path)
        a05_path = a05.save(project,a05_result)
        result.update({
            "status":"AUTO_A04_A05_DONE_NOT_NATIVE_APPROVED",
            "error":None,
            "a05_result":a05_result,
            "a05_report_path":str(a05_path),
        })
    except (ValueError,OSError,KeyError,TypeError) as exc:
        result["status"]="AUTO_A04_OR_A05_BLOCKED"
        result["error"]=str(exc)
    return result


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--open-summary",action="store_true",
                        help="abrir o resumo gerado no Notepad no Windows")
    args=parser.parse_args(argv)
    try:
        result=execute(args.project)
        summary=store_summary(args.project,result)
        print("UNOVA_AUTO_STATUS="+result["status"])
        print("UNOVA_AUTO_RESUMO="+str(summary))
        print("UNOVA_A04="+str(result.get("a04_report_path") or "NAO_GERADO"))
        print("UNOVA_A05="+str(result.get("a05_report_path") or "NAO_GERADO"))
        if result.get("error"):
            print("UNOVA_AUTO_ERRO="+result["error"])
        if args.open_summary and os.name=="nt":
            try:
                subprocess.Popen(["notepad.exe",str(summary)],
                                 close_fds=True)
            except OSError as exc:
                print("Nao foi possivel abrir Notepad: "+str(exc),file=sys.stderr)
        return 0 if result["status"]=="AUTO_A04_A05_DONE_NOT_NATIVE_APPROVED" else 2
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print("UNOVA_AUTO_BLOQUEADO: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
