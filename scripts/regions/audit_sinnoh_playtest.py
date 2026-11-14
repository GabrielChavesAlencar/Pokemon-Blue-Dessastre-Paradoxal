#!/usr/bin/env python3
"""Plan/check manual native Sinnoh QA with evidence tied to an isolated build.

This tool NEVER launches Game.exe, plays a battle, reads user saves, modifies the
main game or unlocks Barry. Gameplay observations must come from a real Windows
(or separately identified Android) session with locally held screenshots/logs.
It verifies reported observations, not that the tester actually performed them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

from install_sinnoh_qa_copy import QA_META, ROOT, verify as verify_copy

SHA = re.compile(r"[a-f0-9]{64}\Z")
SNAPSHOT = re.compile(r"qa-evidence/[A-Za-z0-9_.-]+\.(?:png|jpg|jpeg|txt|log)\Z")
MODES = ("normal", "master")
STARS = ("TURTWIG", "CHIMCHAR", "PIPLUP")
RIVALS = ("CHIMCHAR", "PIPLUP", "TURTWIG")
REGIONS = ("DECADES", "KANTO", "JOHTO", "HOENN")
MAX_EVIDENCE_SIZE = 20 * 1024 * 1024


def fail(msg: str):
    raise ValueError("[SINNOH NATIVE QA] " + msg)


def checked_qa(qa: Path, project: Path) -> tuple[Path, dict]:
    qa = Path(qa).absolute()
    project = Path(project).absolute()
    work = project / ".blue-work"
    if (qa == work or not qa.is_relative_to(work) or
            not qa.resolve().is_relative_to(work.resolve()) or
            any(p.is_symlink() for p in (qa, *qa.parents))):
        fail("Somente perfil QA real dentro de .blue-work (sem symlinks)")
    outcome = verify_copy(qa, project=project)
    if (not outcome.get("engine_structural_report_consistent") or
            not outcome.get("compiled_marker_present") or
            outcome.get("barry_ready_marker_present") is not False):
        fail("Falta compilação/sondagem estrutural da cópia QA, ou Barry liberado prematuramente")
    meta = json.loads((qa / QA_META).read_text("utf-8"))
    if meta.get("region") != "SINNOH" or meta.get("runtime_playable") is not False:
        fail("Metadados do piloto não são versão QA bloqueada")
    return qa, meta


def expected_cases(meta: dict) -> list[dict]:
    contract = meta.get("event_contract")
    if not isinstance(contract, list) or len(contract) != 9:
        fail("Sem inventário completo de eventos Twinleaf")
    cases: list[dict] = []
    for i, starter in enumerate(STARS):
        cases.append({
            "id": "ball-" + starter, "kind": "starter",
            "starter": starter, "must_reject_second_ball": True,
        })
        for mode in MODES:
            for outcome in ("win", "loss"):
                cases.append({
                    "id": f"barry-{starter}-{mode}-{outcome}",
                    "kind": "barry",
                    "starter": starter, "opponent": RIVALS[i], "version": i,
                    "mode": mode, "outcome": outcome,
                    "percent": 70 if mode == "normal" else 90,
                    "master_min_party": 4 if mode == "master" else 1,
                })
        cases.append({
            "id": "save-reload-" + starter, "kind": "save_reload",
            "starter": starter, "must_keep_party_and_dex": True,
        })
    for m in contract:
        if not isinstance(m, dict) or type(m.get("id")) is not int:
            fail("ID de mapa ausente/ilegal no contrato")
        for event in m.get("events", []):
            if not isinstance(event, dict) or not isinstance(event.get("key"), str):
                fail("Evento sem nome no contrato")
            if event.get("kind") == "warp":
                destination = next((d["id"] for d in contract
                                    if d["symbol"] == event["destination"]), None)
                if type(destination) is not int:
                    fail("Warp sem destino no contrato QA")
                cases.append({
                    "id": "warp-" + event["key"], "kind": "warp",
                    "source_map_id": m["id"], "destination_map_id": destination,
                    "arrival_x": event["arrival_x"], "arrival_y": event["arrival_y"],
                })
            elif event.get("kind") == "handler":
                cases.append({
                    "id": "npc-" + event["key"], "kind": "npc",
                    "handler": event["handler"], "map_id": m["id"],
                })
    for region in REGIONS:
        cases.append({"id": "regression-" + region, "kind": "regression",
                      "region": region})
    cases.append({"id": "android-joi-play", "kind": "android",
                  "platform": "Android/JoiPlay", "must_use_independent_profile": True})
    if (len(cases) != 3 + 12 + 3 + 16 + 5 + 4 + 1 or
            len({row["id"] for row in cases}) != len(cases)):
        fail("Inventário QA mudou: necessário revisar número de testes")
    return cases


def new_plan(qa: Path, *, project: Path = ROOT) -> dict:
    _, meta = checked_qa(qa, project)
    return {
        "schema": 1,
        "region": "SINNOH",
        "mode": "LOCAL_HUMAN_NATIVE_QA_PLAN",
        "compile_token": meta["compile_token"],
        "save_profile": meta["profile"],
        "origin": "REAL_QA_OBSERVATIONS_REQUIRED",
        "status": "UNTESTED",
        "may_approve_gameplay": False,
        "may_create_barry_ready_marker": False,
        "cases": [{**case, "observation": None, "evidence": None}
                  for case in expected_cases(meta)],
        "warning": "Observations and screenshots must be obtained from actual Game.exe/JoiPlay runs. This JSON does not prove a real session occurred.",
    }


def write_new_plan(qa: Path, *, project: Path = ROOT) -> Path:
    plan = new_plan(qa, project=project)
    destination = Path(qa).absolute() / "sinnoh-native-playtest.json"
    if destination.exists() or destination.is_symlink():
        fail("Plano já existe; não sobrescrever evidências anteriores")
    with destination.open("x", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return destination


def verify_evidence(qa: Path, item: dict) -> bool:
    if item is None:
        return False
    if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
        fail("Evidência deve ter somente path e sha256")
    path, expected = item["path"], item["sha256"]
    if not isinstance(path, str) or not SNAPSHOT.fullmatch(path):
        fail("Evidência deve ficar em qa-evidence/ e ter extensão permitida")
    if not isinstance(expected, str) or not SHA.fullmatch(expected):
        fail("SHA256 da evidência inválido")
    file = qa / PurePosixPath(path)
    if (file.is_symlink() or not file.is_file() or
            any(p.is_symlink() for p in file.parents)
            or not file.resolve().is_relative_to(qa.resolve())
            or file.stat().st_size > MAX_EVIDENCE_SIZE):
        fail("Evidência ausente, insegura ou grande demais")
    if hashlib.sha256(file.read_bytes()).hexdigest() != expected:
        fail("Captura/log foi alterado depois de registrar o SHA256")
    return True


def validate_observation(case: dict, observed: dict) -> None:
    kind = case["kind"]
    if not isinstance(observed, dict):
        fail("Observação de caso precisa ser JSON objeto")
    if observed.get("platform") not in ("windows", "android"):
        fail("Plataforma da observação é obrigatória")
    if kind != "android" and observed["platform"] != "windows":
        fail("Sessões Windows do Game.exe não podem ser aprovadas com prova Android")
    if kind == "android" and observed["platform"] != "android":
        fail("Android/JoiPlay requer prova própria, não prova Windows")
    if observed.get("pass") is not True:
        fail("Não marcar caso como concluído sem pass:true")
    if kind == "starter":
        if (observed.get("species") != case["starter"] or
                observed.get("second_ball_denied") is not True):
            fail("Poké Bola errada ou duplicação de inicial não testada")
    elif kind == "barry":
        if (observed.get("species") != case["opponent"] or
                observed.get("version") != case["version"] or
                observed.get("outcome") != case["outcome"]):
            fail("Resultado ou contra-inicial de Barry divergente")
        highest = observed.get("highest_party_level")
        enemy = observed.get("enemy_level")
        maximum = observed.get("growth_rate_max_level")
        size = observed.get("enemy_party_size")
        if (any(type(n) is not int for n in (highest, enemy, maximum, size))
                or not 1 <= highest <= maximum
                or not 1 <= maximum <= 1000
                or not 1 <= size <= 6):
            fail("Níveis reais, máximo de crescimento e tamanho do time inválidos")
        expected = min(max(highest * case["percent"] // 100, 1), maximum)
        if enemy != expected:
            fail(f"Nível de Barry não segue {case['percent']}% Blue: esperado {expected}, observado {enemy}")
        if size < case["master_min_party"]:
            fail("Equipe de Barry menor que a configuração esperada para o modo")
        if case["mode"] == "normal" and size != 1:
            fail("Normal não deve ganhar reforços Master de forma silenciosa")
    elif kind == "warp":
        if (observed.get("destination_map_id") != case["destination_map_id"]
                or observed.get("arrival_x") != case["arrival_x"]
                or observed.get("arrival_y") != case["arrival_y"]):
            fail("Warp não chegou nas coordenadas nativas previstas")
    elif kind == "npc":
        if observed.get("handler") != case["handler"]:
            fail("NPC não executou o handler esperado")
    elif kind == "save_reload":
        if (observed.get("starter_before") != case["starter"]
                or observed.get("starter_after") != case["starter"]
                or observed.get("same_profile_after_reload") is not True
                or observed.get("same_party_after_reload") is not True
                or observed.get("pokedex_kept_after_reload") is not True):
            fail("Save/load falhou ou perfil mudou")
    elif kind == "regression":
        if observed.get("region") != case["region"] or observed.get("save_untouched") is not True:
            fail("Regressão de região/saves não verificada")
    elif kind == "android":
        if (observed.get("joi_play_session") is not True or
                observed.get("independent_save_profile") is not True or
                observed.get("starter_and_warp_tested") is not True):
            fail("JoiPlay/Android não validado")
    else:
        fail("Tipo de caso não reconhecido")


def audit(qa: Path, *, project: Path = ROOT) -> dict:
    qa, meta = checked_qa(qa, project)
    file = qa / "sinnoh-native-playtest.json"
    if file.is_symlink() or not file.is_file():
        fail("Plano de playtest não encontrado; use --create apenas após --verify")
    data = json.loads(file.read_text("utf-8"))
    if (data.get("schema"), data.get("region"), data.get("mode"),
            data.get("compile_token"), data.get("may_approve_gameplay"),
            data.get("may_create_barry_ready_marker")) != (
                1, "SINNOH", "LOCAL_HUMAN_NATIVE_QA_PLAN",
                meta["compile_token"], False, False):
        fail("Playtest desconectado da compilação correta")
    if data.get("save_profile") != meta["profile"]:
        fail("Perfil da captura difere do perfil de save QA")
    cases = data.get("cases")
    expected = expected_cases(meta)
    if not isinstance(cases, list) or len(cases) != len(expected):
        fail("Quantidade de casos não corresponde ao roteiro real de QA")
    done = 0
    by_kind: dict[str, dict[str, int]] = {}
    for a, b in zip(cases, expected):
        if not isinstance(a, dict) or {
            key: a.get(key) for key in b
        } != b:
            fail("Caso de teste foi alterado/reordenado")
        kind = b["kind"]
        row = by_kind.setdefault(kind, {"complete": 0, "total": 0})
        row["total"] += 1
        if a.get("observation") is None and a.get("evidence") is None:
            continue
        if a.get("observation") is None or a.get("evidence") is None:
            fail("Observação sem captura ou captura sem observação")
        verify_evidence(qa, a["evidence"])
        validate_observation(b, a["observation"])
        done += 1
        row["complete"] += 1
    return {
        "schema": 1, "region": "SINNOH",
        "mode": "MANUAL_QA_EVIDENCE_INTEGRITY_AUDIT",
        "status": "INCOMPLETE" if done < len(expected) else "MANUAL_EVIDENCE_RECORDED_NEEDS_HUMAN_REVIEW",
        "completed": done, "total": len(expected),
        "by_kind": by_kind,
        "native_game_executed_independently_proven": False,
        "screenshot_or_log_hashes_consistent": True,
        "source_asset_rights_verified": False,
        "main_game_or_saves_modified": False,
        "automatically_approved_gameplay": False,
        "may_create_barry_ready_marker": False,
        "report_only": True,
    }


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--qa", type=Path, required=True)
    group = cli.add_mutually_exclusive_group(required=True)
    group.add_argument("--create", action="store_true",
                       help="Create a local, unfilled checklist in QA copy; never overwrite")
    group.add_argument("--audit", action="store_true",
                       help="Read-only validation of typed observations & screenshot hashes")
    args = cli.parse_args()
    try:
        if args.create:
            path = write_new_plan(args.qa)
            print(json.dumps({"created": True, "location": str(path),
                              "gameplay_approved": False}, ensure_ascii=False))
        else:
            print(json.dumps(audit(args.qa), ensure_ascii=False, indent=2))
    except (ValueError, OSError, TypeError, KeyError, UnicodeError) as exc:
        print("SINNOH_PLAYTEST_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
