#!/usr/bin/env python3
"""SP04: validate planned Unova NPC roster, join optional PRIVATE SP03 sprites.

Read-only input. Only private .blue-work reports; never installs assets or
confirms that a filename match is the correct sprite, licensed or playable.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CATALOG=ROOT/"data/regions/unova-sp04-npcs.json"
AREAS=ROOT/"data/regions/unova-u03-areas.json"
TRAINERS=ROOT/"data/regions/unova-e06-e07-preparation.json"
REGIONS=ROOT/"site/public/data/regions.json"
SP03_DIR=Path(".blue-work/unova/audit/sprite-packs")
SP04_DIR=Path(".blue-work/unova/audit/npc-catalog")
SHA=re.compile(r"[0-9a-f]{64}\Z")
AUDIT_FILENAME=re.compile(r"sprites-[0-9a-f]{16}\.json\Z")
MAX_JSON=32*1024*1024
VALID_SCOPES={"WHITE_BW","BW_POSTGAME","BLACK_ONLY_VARIANT","CUSTOM_BLUE"}
VALID_PRIORITY={"P0","P1","P2"}
STATUS="PLANNED_REFERENCE_ONLY"
FIELDS={
    "key","display_name","role","story_scope","priority",
    "primary_area_key","planned_phase","additional_area_keys",
    "filename_alias_candidates","trainer_reference_key",
    "status","sprite_source_pack","sprite_source_path","sprite_sha256",
    "sprite_dimensions","sprite_grid_confirmed","author_verified",
    "license_evidence_url","redistribution_allowed","assigned_sprite_approved",
    "visual_qa_passed","game_exe_tested","android_tested",
    "npc_event_verified","installed",
}


def fail(message: str) -> None:
    raise ValueError("UNOVA_SP04_BLOQUEADO: "+message)


def norm(value: str) -> str:
    value=unicodedata.normalize("NFKD", value)
    value="".join(ch for ch in value if not unicodedata.combining(ch))
    value=re.sub(r"(?<=[a-z])(?=[A-Z])","_",value)
    return re.sub(r"[^a-z0-9]+","_",value.lower()).strip("_")


def read_json(path: Path, limit: int=MAX_JSON) -> dict:
    if path.is_symlink() or not path.is_file() or not 0<path.stat().st_size<=limit:
        fail("JSON ausente, inseguro ou grande demais: "+str(path))
    value=json.loads(path.read_text("utf-8-sig"))
    if not isinstance(value,dict):
        fail("JSON nao e objeto")
    return value


def validate_catalog(catalog: dict, areas: dict, trainers: dict, registry: dict) -> list[dict]:
    defaults={"schema":1,"region":"UNOVA","phase":"SP04",
              "reference_version":"WHITE_BW","status":"PLANNED_NPC_CATALOG_ONLY",
              "source_pack_not_downloaded":True,
              "source_sprites_verified":False,"rights_verified":False,
              "can_install":False,"game_exe_tested":False,"android_tested":False}
    if not isinstance(catalog,dict):
        fail("catalogo SP04 ausente")
    if set(catalog) != set(defaults)|{"notes","characters"}:
        fail("schema SP04 incorreto")
    for field,value in defaults.items():
        if type(catalog.get(field)) is not type(value) or catalog[field]!=value:
            fail("campo SP04 ativou fonte, licenca ou jogo indevidamente: "+field)
    if (not isinstance(catalog["notes"],list) or
        any(not isinstance(note,str) or len(note)<20 for note in catalog["notes"])):
        fail("notas SP04 insuficientes")
    if (areas.get("state")!="PLANNED_REFERENCE_ONLY" or
        areas.get("may_install") is not False or
        registry.get("regions",{}).get("UNOVA",{}).get("status")!="planned"):
        fail("catalogo de areas ou Unova deixou de ser planned")
    names={row.get("key"):row for row in areas.get("areas",[])
           if isinstance(row,dict)}
    if len(names)!=74 or len(areas.get("areas",[]))!=74:
        fail("areas U03 ausentes ou duplicadas")
    known_trainers={row.get("key") for row in trainers.get("trainer_references",[])
                    if isinstance(row,dict)}
    if len(known_trainers)!=19:
        fail("catalogo de treinadores historico alterado")
    rows=catalog.get("characters")
    if not isinstance(rows,list) or len(rows)!=73:
        fail("elenco SP04 deve listar 73 personagens/arquetipos planejados")
    seen=set()
    actual_trainers=set()
    leaders=set()
    for index,item in enumerate(rows):
        if not isinstance(item,dict) or set(item)!=FIELDS:
            fail("campos de NPC invalidos, indice "+str(index))
        key=item["key"]
        if (not isinstance(key,str) or not re.fullmatch(r"UNOVA_NPC_[A-Z0-9_]+",key)
            or key in seen):
            fail("identidade de NPC duplicada/invalida")
        seen.add(key)
        if (not isinstance(item["display_name"],str) or not item["display_name"] or
            len(item["display_name"])>120 or not isinstance(item["role"],str) or
            not re.fullmatch(r"[A-Z_]+",item["role"])):
            fail("nome/papel de NPC invalido")
        if (item["story_scope"] not in VALID_SCOPES or
            item["priority"] not in VALID_PRIORITY):
            fail("variacao/prioridade de NPC invalida")
        area=names.get(item["primary_area_key"])
        if area is None or item["planned_phase"]!=area.get("phase"):
            fail("area ou fase narrativa inexistente")
        other=item["additional_area_keys"]
        if (not isinstance(other,list) or len(other)!=len(set(other)) or
            any(k not in names or k==item["primary_area_key"] for k in other)):
            fail("areas complementares invalidas")
        aliases=item["filename_alias_candidates"]
        if (not isinstance(aliases,list) or not 1<=len(aliases)<=12 or
            any(not isinstance(a,str) or len(a)>100 or not norm(a) for a in aliases) or
            len({norm(a) for a in aliases})!=len(aliases)):
            fail("aliases duplicados/inseguros de NPC")
        ref=item["trainer_reference_key"]
        if ref is not None:
            if ref not in known_trainers or ref in actual_trainers:
                fail("referencia de treinador SP04 ausente/duplicada")
            if key!="UNOVA_NPC_"+ref.removeprefix("UNOVA_TRAINER_"):
                fail("referencia de treinador contradiz ID do NPC")
            actual_trainers.add(ref)
        if item["status"] != STATUS:
            fail("NPC falsamente instalado ou confirmado")
        for field in ("sprite_source_pack","sprite_source_path","sprite_sha256",
                      "sprite_dimensions","license_evidence_url"):
            if item[field] is not None:
                fail("asset licenciado/atribuido falsamente: "+field)
        for field in ("sprite_grid_confirmed","author_verified","redistribution_allowed",
                      "assigned_sprite_approved","visual_qa_passed","game_exe_tested",
                      "android_tested","npc_event_verified","installed"):
            if item[field] is not False:
                fail("NPC aprovado sem evidencia: "+field)
        if item["role"]=="GYM_LEADER":
            leaders.add(key)
    needed={"UNOVA_NPC_JUNIPER","UNOVA_NPC_CHEREN","UNOVA_NPC_BIANCA",
            "UNOVA_NPC_N","UNOVA_NPC_GHETSIS",
            "UNOVA_NPC_TEAM_PLASMA" if False else "UNOVA_NPC_PLASMA_GRUNT_MALE",
            "UNOVA_NPC_REGIONAL_TRAVEL_AGENT",
            "UNOVA_NPC_HILBERT","UNOVA_NPC_HILDA"}
    if not needed <= seen:
        fail("personagem principal ou NPC regional ausente")
    expected_leaders={"UNOVA_NPC_"+x for x in (
        "CHILI","CRESS","CILAN","LENORA","BURGH","ELESA",
        "CLAY","SKYLA","BRYCEN","IRIS")}
    if leaders != expected_leaders:
        fail("lideres de White incompletos ou Drayden como lider")
    if ("UNOVA_NPC_DRAYDEN" not in seen or
        next(r for r in rows if r["key"]=="UNOVA_NPC_DRAYDEN")["story_scope"]!="BLACK_ONLY_VARIANT"):
        fail("Drayden deve ser referencia opcional Black, nao lider White")
    if actual_trainers != known_trainers:
        fail("elenco novo nao preserva as 19 referencias existentes")
    return rows


def private_report(root: Path, name: Path) -> Path:
    root=Path(root).absolute()
    allowed=root/SP03_DIR
    target=Path(name).absolute()
    if (not target.is_relative_to(allowed) or target.parent!=allowed or
        not AUDIT_FILENAME.fullmatch(target.name)):
        fail("SP03 deve estar em .blue-work/unova/audit/sprite-packs, nome hash")
    for part in [root,root/".blue-work",root/".blue-work/unova",
                 root/".blue-work/unova/audit",allowed,target]:
        if part.is_symlink():
            fail("pasta ou relatorio de sprite via symlink")
    return target


def read_sp03(project: Path, path: Path) -> dict:
    report=read_json(private_report(project,path))
    expected={"schema":1,"region":"UNOVA","phase":"SPRITE_AUDIT_SP03",
              "mode":"PRIVATE_SPRITE_PACK_METADATA_INSPECTION_NO_EXTRACTION",
              "status":"SPRITES_AUDITED_NOT_LICENSED_OR_INSTALLED"}
    for key,value in expected.items():
        if report.get(key)!=value:
            fail("SP03 invalido, incompleto ou com imagens corrompidas: "+key)
    for flag in ("rights_verified","may_redistribute","game_exe_tested",
                 "android_tested","game_or_saves_modified","can_install"):
        if report.get(flag) is not False:
            fail("SP03 declara permissao ou teste nao provado: "+flag)
    digest=report.get("archive_sha256")
    if not isinstance(digest,str) or not SHA.fullmatch(digest):
        fail("SP03 sem SHA256 completo")
    if Path(path).name != "sprites-"+digest[:16]+".json":
        fail("nome do relatorio nao confere com hash")
    imgs=report.get("images")
    if (not isinstance(imgs,list) or report.get("supported_images")!=len(imgs) or
        len(imgs)<1 or len(imgs)>12000 or report.get("invalid_images")!=[]):
        fail("SP03 com imagens invalidas/contagem divergente")
    seen=set()
    for item in imgs:
        if not isinstance(item,dict) or not isinstance(item.get("path"),str):
            fail("linha SP03 malformada")
        name=item["path"].casefold()
        if name in seen or "\\" in name or name.startswith("/") or ".." in Path(name).parts:
            fail("arquivo SP03 duplicado ou inseguro")
        seen.add(name)
        if (not isinstance(item.get("sha256"),str) or
            not SHA.fullmatch(item["sha256"]) or item.get("rights_verified") is not False or
            item.get("installable") is not False or
            item.get("native_four_direction_layout_verified") is not False or
            item.get("native_animation_playback_verified") is not False):
            fail("imagem SP03 falsamente verificada")
        if (type(item.get("width")) is not int or type(item.get("height")) is not int or
            not 1<=item["width"]<=8192 or not 1<=item["height"]<=8192):
            fail("dimensoes SP03 invalidas")
        if (not isinstance(item.get("sheet_layout_candidates"),list) or
            not isinstance(item.get("character_name_candidates"),list) or
            not isinstance(item.get("warnings"),list)):
            fail("metadados SP03 malformados")
    return report


def merge(catalog: dict,areas: dict,trainers: dict,regions: dict,sp03: dict|None) -> dict:
    roster=validate_catalog(catalog,areas,trainers,regions)
    if sp03 is not None and sp03.get("status")!="SPRITES_AUDITED_NOT_LICENSED_OR_INSTALLED":
        fail("SP03 inseguro ou nao aprovado tecnicamente")
    images=sp03["images"] if sp03 is not None else []
    output=[]
    states=Counter()
    for npc in roster:
        canonical=npc["key"].removeprefix("UNOVA_NPC_")
        aliases={norm(s) for s in npc["filename_alias_candidates"]}
        candidates=[]
        for sprite in images:
            if sprite.get("sprite_kind_candidate") in ("BATTLE_SPRITE_CANDIDATE","ICON_CANDIDATE"):
                continue
            stem=norm(Path(sprite["path"]).stem)
            names=sprite["character_name_candidates"]
            via="IDENTITY_FILENAME_CANDIDATE" if canonical in names else (
                 "EXACT_FILENAME_ALIAS_CANDIDATE" if stem in aliases else None)
            if via is None:
                continue
            candidates.append({
                "source_path_candidate":sprite["path"],
                "source_sha256_candidate":sprite["sha256"],
                "candidate_match_reason":via,
                "width":sprite["width"],"height":sprite["height"],
                "format":sprite["format"],
                "animation_frames_declared":sprite["animation_frames_declared"],
                "sheet_layout_candidates":sprite["sheet_layout_candidates"],
                "warnings":sprite["warnings"],
                "reference_name_matches":sprite["decades_same_basename_matches"],
                "reviewed_as_correct_character":False,
                "rights_verified":False,"selected_for_installation":False,
            })
        candidates.sort(key=lambda c:(c["source_path_candidate"].casefold(),c["source_sha256_candidate"]))
        state=("NO_PACK_AUDIT" if sp03 is None else
               "NO_FILENAME_MATCH_UNVERIFIED" if not candidates else
               "MULTIPLE_CANDIDATES_MANUAL_REVIEW" if len(candidates)>1 else
               "SINGLE_CANDIDATE_MANUAL_REVIEW")
        states[state]+=1
        output.append({
            "npc_key":npc["key"],"display_name":npc["display_name"],
            "role":npc["role"],"story_scope":npc["story_scope"],
            "priority":npc["priority"],"primary_area_key":npc["primary_area_key"],
            "planned_phase":npc["planned_phase"],
            "trainer_reference_key":npc["trainer_reference_key"],
            "status":state,"candidate_count":len(candidates),
            "sprite_candidates":candidates,
            "author_verified":False,"license_verified":False,
            "sprite_selection_approved":False,"game_exe_tested":False,
            "android_tested":False,"npc_installed":False,
        })
    return {
        "schema":1,"region":"UNOVA","phase":"SP04",
        "mode":"SYMBOLIC_ROSTER_AND_PRIVATE_SPRITE_CANDIDATES_ONLY",
        "status":"NPC_CATALOG_AUDITED_NOT_INSTALLED_OR_LICENSED",
        "roster_entries":len(output),
        "source_sprite_report_sha256":sp03.get("archive_sha256") if sp03 else None,
        "source_sprites_audited":sp03 is not None,
        "candidate_npcs_count":sum(bool(x["candidate_count"]) for x in output),
        "candidate_files_total":sum(x["candidate_count"] for x in output),
        "status_counts":dict(sorted(states.items())),
        "npcs":output,
        "rights_verified":False,"can_install":False,
        "game_or_saves_modified":False,"game_exe_tested":False,"android_tested":False,
        "next_action":"Revisao humana de imagens, identidade, creditos, licencas e layout antes de selecionar um NPC piloto SP05.",
    }


def save(project: Path, report: dict) -> Path:
    project=Path(project).absolute()
    out=project/SP04_DIR
    for folder in [project,project/".blue-work",project/".blue-work/unova",
                   project/".blue-work/unova/audit",out]:
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            fail("saida privada via symlink/arquivo")
    out.mkdir(parents=True,exist_ok=True)
    digest=report["source_sprite_report_sha256"]
    filename="npc-sp04-"+(digest[:16] if digest else "planned-only")+".json"
    target=out/filename
    if target.is_symlink():
        fail("arquivo de saida e symlink")
    payload=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if target.exists():
        if target.read_text("utf-8")!=payload:
            fail("relatorio anterior divergente: preservar evidencia, nao substituir")
    else:
        with target.open("x",encoding="utf-8") as file:
            file.write(payload)
    return target


def main(argv=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--audit",type=Path,help="JSON de sprite SP03 dentro da pasta privada")
    parser.add_argument("--latest",action="store_true",help="usar o relatorio SP03 privado mais recente")
    parser.add_argument("--write",action="store_true")
    args=parser.parse_args(argv)
    try:
        if args.audit is not None and args.latest:
            fail("escolha --audit ou --latest")
        project=args.project.absolute()
        roster=read_json(project/"data/regions/unova-sp04-npcs.json")
        areas=read_json(project/"data/regions/unova-u03-areas.json")
        trainers=read_json(project/"data/regions/unova-e06-e07-preparation.json")
        regions=read_json(project/"site/public/data/regions.json")
        source=args.audit
        if args.latest:
            folder=project/SP03_DIR
            if folder.is_symlink():
                fail("pasta privada SP03 e symlink")
            if folder.is_dir():
                choices=sorted(
                    (p for p in folder.iterdir() if AUDIT_FILENAME.fullmatch(p.name)),
                    key=lambda p:(p.stat().st_mtime_ns,p.name),reverse=True)
                source=choices[0] if choices else None
        report_sp03=read_sp03(project,source) if source is not None else None
        result=merge(roster,areas,trainers,regions,report_sp03)
        if args.write:
            target=save(project,result)
            print("RELATORIO_PRIVADO_SP04: "+str(target),file=sys.stderr)
        print(json.dumps({k:v for k,v in result.items() if k!="npcs"},
                         indent=2,ensure_ascii=False))
        return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
