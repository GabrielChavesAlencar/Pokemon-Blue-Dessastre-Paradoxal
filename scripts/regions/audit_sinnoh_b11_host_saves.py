#!/usr/bin/env python3
"""B11: READ-ONLY before/after host save fingerprint + VM-only Sinnoh QA witness.

The B11 Windows Sandbox config mounts ONLY a validated B09 clone and B11
helper scripts read-only. Never run Game.exe on host or copy real saves.
Reports disclose counts, not host file paths, names or save bytes.
No claim of ALL possible save locations, gameplay success or native approval.
"""
from __future__ import annotations
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import platform
import re
import secrets
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import uuid

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import prepare_sinnoh_b10_save_isolation as b10
import build_sinnoh_b09_native_qa as b09
from audit_sinnoh_b06_technical_candidate import load
CONTRACT=ROOT/"data/regions/sinnoh-b11-host-save-audit.json"
WORK_SUBDIR=".blue-work/sinnoh-b11-save-audit"
SHA=re.compile(r"[0-9a-f]{64}\Z")
SESSION=re.compile(r"[0-9a-f]{32}\Z")
MAX_FILES=40000
MAX_FILE_BYTES=4*1024*1024*1024
MAX_TOTAL_BYTES=12*1024*1024*1024
GUEST_SCRIPT="B11_DIAGNOSTICAR_DENTRO_DA_SANDBOX.cmd"
GUEST_PREP="B10_PREPARAR_NO_WINDOWS_SANDBOX.cmd"
WSB="B11_ISOLAMENTO_E_DIAGNOSTICO.wsb"

def blocked(text):
    raise ValueError("SINNOH_B11_BLOCKED: "+text)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def file_sha(p):
    dig=hashlib.sha256()
    with Path(p).open("rb") as f:
        for piece in iter(lambda:f.read(1024*1024),b""):
            dig.update(piece)
    return dig.hexdigest()

def link(p):
    return b09.is_link(p)

def check_contract(c,c10,c09):
    expected={
      "schema":1,"region":"SINNOH","stage":"B11",
      "status":"HOST_SAVE_WATCH_AND_GUEST_DIAGNOSTICS_READY_NOT_EXECUTED",
      "b10_stage":c10["stage"],"b10_status":c10["status"],
      "b10_clone_subdir":c09["clone_workspace_subdir"],
      "sandbox_subdir":WORK_SUBDIR,
      "expected_clone_maps":702,"sinnoh_map_range":[442,495],
      "readonly_clone_mapping":True,"readonly_tools_mapping":True,
      "sandbox_networking_disabled":True,
      "sandbox_clipboard_disabled":True,
      "no_autostart_Game_exe":True,
      "host_saves_never_copied":True,
      "host_fingerprint_scopes_explicit_or_named_application_paths_only":True,
      "host_save_root_names_never_in_shared_report":True,
      "coverage_known_incomplete_until_save_code_audited":True,
      "sandbox_runtime_save_path_verified":False,
      "host_saves_unchanged_after_native_test_confirmed":False,
      "game_exe_tested":False,
      "rendering_50000_70000_tilesets_verified":False,
      "r07_complete":False,"r08_complete":False,"r09_complete":False,
      "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
    }
    if type(c) is not dict or c!=expected:
        blocked("contrato B11 divergente ou progresso indevido")

def workspace(project=ROOT):
    project=Path(project).absolute()
    base=project/".blue-work"
    dest=base/"sinnoh-b11-save-audit"
    if link(base) or link(dest) or not dest.resolve().is_relative_to(project.resolve()):
        blocked("diretorio privado B11 inseguro")
    return dest

def default_scopes(env=None):
    env=dict(os.environ if env is None else env)
    result=[]
    for key in ("APPDATA","LOCALAPPDATA"):
        root=env.get(key)
        if root:result.append(Path(root)/"PokemonBlueDessastreParadoxal")
    user=env.get("USERPROFILE")
    if user:
        result.append(Path(user)/"Saved Games"/"PokemonBlueDessastreParadoxal")
        result.append(Path(user)/"Documents"/"PokemonBlueDessastreParadoxal")
    return result

def checked_roots(roots):
    output=[]
    seen=set()
    for root in roots:
        p=Path(root).expanduser().absolute()
        if any(link(parent) for parent in (p,*p.parents)) or not p.is_dir():
            blocked("pasta monitorada ausente, symlink ou junction (inclusive ancestral)")
        resolved=p.resolve()
        key=str(resolved).casefold()
        if key in seen:continue
        seen.add(key)
        output.append(resolved)
    if not output:
        blocked("nenhuma pasta de saves monitoravel; informe --watch-dir")
    for i,p in enumerate(output):
        for other in output[i+1:]:
            if p.is_relative_to(other) or other.is_relative_to(p):
                blocked("pastas monitoradas sobrepostas")
    return output

def fingerprint(roots,key):
    """HMAC names; SHA256 of bytes, including additions, deletions and changes."""
    if not isinstance(key,bytes) or len(key)<24:
        blocked("segredo de identificacao da sessao invalido")
    result={}
    bytes_scanned=0
    for slot,root in enumerate(checked_roots(roots)):
        def walk_error(exc):
            # Do not leak private directory names in user-visible diagnostics.
            blocked("erro de leitura durante a varredura de saves; escopo incompleto")
        for dirpath,dirs,files in os.walk(
                root,topdown=True,followlinks=False,onerror=walk_error):
            here=Path(dirpath)
            for d in dirs:
                if link(here/d):
                    blocked("junction/symlink encontrado em pasta monitorada")
            for name in files:
                p=here/name
                if link(p) or not p.is_file():
                    blocked("arquivo pessoal nao regular/junction")
                before=p.stat()
                size=before.st_size
                if size>MAX_FILE_BYTES:blocked("arquivo muito grande para auditoria")
                bytes_scanned+=size
                if bytes_scanned>MAX_TOTAL_BYTES or len(result)>=MAX_FILES:
                    blocked("escopo excede limite B11; reduza pastas monitoradas")
                relative=p.relative_to(root).as_posix()
                label=f"{slot}:{relative}".encode("utf-8","surrogatepass")
                identifier=hmac.new(key,label,hashlib.sha256).hexdigest()
                if identifier in result:
                    blocked("colisao inesperada de caminho HMAC")
                digest=file_sha(p)
                after=p.stat()
                signature=lambda st:(st.st_size,st.st_mtime_ns,st.st_ctime_ns,
                                      getattr(st,"st_ino",None))
                if signature(before)!=signature(after) or link(p):
                    blocked("arquivo mudou durante a auditoria; tente um novo snapshot")
                result[identifier]={"sha256":digest,"bytes":size}
    return result,bytes_scanned

def compare(before,after):
    old=set(before);new=set(after)
    added=new-old
    deleted=old-new
    changed={n for n in old&new if before[n]!=after[n]}
    return {"files_added":len(added),"files_removed":len(deleted),
            "files_changed":len(changed),"watch_unchanged":not (added or deleted or changed)}

def b10_session(project,clone_sha):
    folder=b10.session_root(project)/f"session-{clone_sha[:16]}"
    if link(folder) or not folder.is_dir():
        blocked("sessao B10 nao encontrada: primeiro execute B10")
    meta=folder/"B10_SESSAO.json"
    wsb=folder/"B10_ISOLAMENTO.wsb"
    guest=folder/"tools"/GUEST_PREP
    for p in (meta,wsb,guest):
        if link(p) or not p.is_file():
            blocked("arquivos B10 incompletos ou inseguros")
    doc=json.loads(meta.read_text("utf-8"))
    required={
       "stage":"B10","status":"WSB_CONFIG_PREPARED_NOT_LAUNCHED",
       "source_clone_sha256":clone_sha,
       "native_map_ids":648,"sinnoh_terrain_map_ids":54,
       "expected_total_maps":702,
       "all_cloned_files_sha_verified":True,
       "sandbox_feature_enabled_on_host":True,
       "sandbox_session_started":False,"game_exe_started":False,
       "save_write_isolation_runtime_verified":False,
       "host_save_directories_mapped":False,
       "mapped_folders_read_only":True,
       "internet_networking_enabled":False,
       "clipboard_enabled":False,
       "rights_verified":False,"r07_complete":False,
       "r08_complete":False,"r09_complete":False,"phase_b_approved":0,
    }
    if any(doc.get(k)!=v for k,v in required.items()):
        blocked("sessao B10 nao corresponde a copia atual")
    clone=b09.clone_root(project)/f"native-{clone_sha[:16]}"
    expected=b10.xml_wsb(str(clone),str(folder/"tools"))
    if wsb.read_text("utf-8")!=expected:
        blocked("config WSB B10 foi alterada")
    if guest.read_text("utf-8").replace("\r\n","\n").strip()!=b10.GUEST_CMD.strip():
        blocked("script de guest B10 foi alterado")
    return folder

GUEST_DIAG=r"""@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Sinnoh B11 - Diagnostico SOMENTE dentro da VM
echo.
echo B11: SOMENTE dentro da WINDOWS SANDBOX apos preparar a copia B10.
rem Protecao adicional contra uso acidental no host; NAO autentica a VM.
if /I not "%USERNAME%"=="WDAGUtilityAccount" goto :outside
if /I not "%USERPROFILE%"=="C:\Users\WDAGUtilityAccount" goto :outside
if not exist "C:\SinnohB10Tools\B11_DIAGNOSTICAR_DENTRO_DA_SANDBOX.cmd" goto :outside
if not exist "C:\SinnohB10Game\Game.exe" goto :failed
if not exist "C:\SinnohB10Game\Data\Map442.rxdata" goto :failed
if not exist "C:\SinnohB10Game\Data\Map495.rxdata" goto :failed
echo [OK] Game.exe e MapIDs extremos da copia privada localizados.
echo [ATENCAO] Isso nao prova que sprites ou tilesets foram renderizados.
echo.
echo Verificando quantidade de arquivos de save visiveis SOMENTE na VM:
powershell.exe -NoProfile -NonInteractive -Command "$bases=@($env:APPDATA,$env:LOCALAPPDATA,(Join-Path $env:USERPROFILE 'Documents'),(Join-Path $env:USERPROFILE 'Saved Games'),'C:\SinnohB10Game');$count=0;foreach($b in $bases){if(Test-Path -LiteralPath $b){$count+=@(Get-ChildItem -LiteralPath $b -File -Recurse -ErrorAction SilentlyContinue | Where-Object {$_.Name -match '^(Save|Game).*([.]rxdata|[.]sav|[.]dat)$'}).Count}};Write-Host ('B11_VM_CANDIDATE_SAVE_FILES=' + $count)"
echo.
echo Observe no Game.exe DENTRO DA VM: abertura, mapa Twinleaf 442,
echo geometria, textura, tilesets 256x50000/256x70000, erros e salvamento.
echo Se abrir, fechar a Sandbox apaga os dados internos nao compartilhados.
echo Guarde apenas observacoes pessoais; nao exporte saves.
pause
exit /b 0
:outside
echo [B11 BLOQUEADO] O contexto nao corresponde ao convidado Windows Sandbox.
echo Nao execute Game.exe nem copie saves no Windows principal.
pause
exit /b 3
:failed
echo [B11 BLOQUEADO] O clone nao foi preparado em C:\SinnohB10Game.
echo Execute primeiro C:\SinnohB10Tools\B10_PREPARAR_NO_WINDOWS_SANDBOX.cmd
pause
exit /b 2
"""

def prepare_before(project,clone_sha,roots,*,scope_selection_mode="explicit",
                   default_scopes_not_monitored=None):
    """Create a private baseline and WSB config; return only sanitized JSON."""
    if scope_selection_mode not in ("explicit","default"):
        blocked("modo de selecao de diretorios invalido")
    if scope_selection_mode=="default":
        if (type(default_scopes_not_monitored) is not int
                or not 0<=default_scopes_not_monitored<=4):
            blocked("cobertura dos diretorios padrao desconhecida")
    elif default_scopes_not_monitored is not None:
        blocked("diretorios ausentes nao podem ser inferidos do modo explicito")
    b10_session(project,clone_sha)
    roots=checked_roots(roots)
    key=secrets.token_bytes(32)
    entries,total=fingerprint(roots,key)
    base=workspace(project)
    if link(base):blocked("workspace privado inseguro")
    base.mkdir(parents=True,exist_ok=True)
    identity=uuid.uuid4().hex
    target=base/f"watch-{identity}"
    tmp=Path(tempfile.mkdtemp(prefix=".b11-",dir=base))
    try:
        tools=tmp/"tools"
        tools.mkdir()
        (tools/GUEST_PREP).write_text(b10.GUEST_CMD,encoding="utf-8",newline="\r\n")
        (tools/GUEST_SCRIPT).write_text(GUEST_DIAG,encoding="utf-8",newline="\r\n")
        clone=b09.clone_root(project)/f"native-{clone_sha[:16]}"
        wsb=b10.xml_wsb(str(clone),str(target/"tools"))
        b10.check_wsb_policy(wsb,str(clone),str(target/"tools"))
        (tmp/WSB).write_text(wsb,encoding="utf-8")
        internal={
          "schema":1,"region":"SINNOH","stage":"B11",
          "id":identity,"clone_sha":clone_sha,"roots":[str(p) for p in roots],
          "hmac_key":key.hex(),"baseline":entries,
          "baseline_digest":hmac.new(key,json.dumps(entries,sort_keys=True).encode(),
                                     hashlib.sha256).hexdigest(),
          "baseline_bytes":total,"baseline_files":len(entries),
          "scope_selection_mode":scope_selection_mode,
          "default_scopes_not_monitored":default_scopes_not_monitored,
        }
        (tmp/"private-baseline.json").write_text(
            json.dumps(internal,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
        if target.exists():blocked("sessao B11 duplicada")
        tmp.rename(target)
    except BaseException:
        if tmp.exists():shutil.rmtree(tmp)
        raise
    return {
      "stage":"B11","status":"HOST_SAVE_SNAPSHOT_BEFORE_RECORDED_SANDBOX_NOT_RUN",
      "watch_id":identity,"clone_sha256":clone_sha,
      "monitored_directories_count":len(roots),
      "scope_selection_mode":scope_selection_mode,
      "default_scopes_not_monitored":default_scopes_not_monitored,
      "monitored_files_before":len(entries),"bytes_hashed_before":total,
      "config_relative_path":(target/WSB).relative_to(project).as_posix(),
      "paths_names_and_saves_in_report":False,
      "windows_sandbox_started":False,"Game_exe_started":False,
      "host_saves_runtime_isolation_confirmed":False,
      "coverage_is_partial":True,"r07_complete":False,"phase_b_approved":0,
    }

def validate_private_baseline(doc,identity):
    """Validate a PRIVATE snapshot; never include its contents in output."""
    required={
        "schema","region","stage","id","clone_sha","roots","hmac_key",
        "baseline","baseline_digest","baseline_bytes","baseline_files",
        "scope_selection_mode","default_scopes_not_monitored",
    }
    if type(doc) is not dict or set(doc)!=required:
        blocked("estrutura do baseline privado invalida")
    if (doc["schema"]!=1 or doc["region"]!="SINNOH" or doc["stage"]!="B11"
            or doc["id"]!=identity or type(doc["clone_sha"]) is not str
            or not SHA.fullmatch(doc["clone_sha"])):
        blocked("identidade do baseline privado incorreta")
    if (type(doc["hmac_key"]) is not str or
            not re.fullmatch(r"[0-9a-f]{64}",doc["hmac_key"])):
        blocked("chave de sessao privada invalida")
    key=bytes.fromhex(doc["hmac_key"])
    if (type(doc["roots"]) is not list or not 1<=len(doc["roots"])<=32
            or any(type(p) is not str or not p or
                   not Path(p).is_absolute() for p in doc["roots"])):
        blocked("escopos privados invalidos")
    mode=doc["scope_selection_mode"]
    missing=doc["default_scopes_not_monitored"]
    if mode not in ("explicit","default"):
        blocked("origem dos escopos invalida")
    if ((mode=="explicit" and missing is not None)
            or (mode=="default" and
                (type(missing) is not int or not 0<=missing<=4))):
        blocked("declaracao de cobertura invalida")
    baseline=doc["baseline"]
    if type(baseline) is not dict or len(baseline)>MAX_FILES:
        blocked("inventario privado de hashes invalido")
    total=0
    for identifier,row in baseline.items():
        if (type(identifier) is not str or not SHA.fullmatch(identifier)
                or type(row) is not dict or set(row)!={"sha256","bytes"}
                or type(row["sha256"]) is not str or not SHA.fullmatch(row["sha256"])
                or type(row["bytes"]) is not int or
                not 0<=row["bytes"]<=MAX_FILE_BYTES):
            blocked("registro privado de save invalido")
        total+=row["bytes"]
        if total>MAX_TOTAL_BYTES:
            blocked("baseline privado excede limite de bytes")
    if (type(doc["baseline_files"]) is not int
            or doc["baseline_files"]!=len(baseline)
            or type(doc["baseline_bytes"]) is not int
            or doc["baseline_bytes"]!=total):
        blocked("contagens de baseline privado adulteradas")
    expected=hmac.new(key,json.dumps(baseline,sort_keys=True).encode(),
                      hashlib.sha256).hexdigest()
    if (type(doc["baseline_digest"]) is not str
            or not hmac.compare_digest(doc["baseline_digest"],expected)):
        blocked("baseline privado alterado desde o snapshot")
    # The HMAC key lives in this local file too: corruption check, NOT proof
    # against intentional editing by someone who can modify the snapshot.
    return key


def inspect_after(project,identity,observation):
    if type(identity) is not str or not SESSION.fullmatch(identity):
        blocked("identificador B11 invalido")
    target=workspace(project)/f"watch-{identity}"
    if link(target) or not target.is_dir():
        blocked("baseline privado B11 nao encontrado")
    path=target/"private-baseline.json"
    if link(path) or not path.is_file() or path.stat().st_size>30_000_000:
        blocked("baseline privado ausente ou adulterado")
    doc=json.loads(path.read_text("utf-8"))
    key=validate_private_baseline(doc,identity)
    roots=[Path(p) for p in doc["roots"]]
    after,total=fingerprint(roots,key)
    changes=compare(doc["baseline"],after)
    supported={"not_run","launch_failed","launched","rendered_map","save_inside_vm"}
    if observation not in supported:blocked("observacao da VM invalida")
    return {
      "stage":"B11",
      "status":("HOST_WATCHED_FILES_CHANGED_REVIEW_REQUIRED" if not changes["watch_unchanged"]
                else "HOST_WATCHED_FILES_UNCHANGED_LIMITED_EVIDENCE"),
      "watch_id":identity,
      "monitored_directories_count":len(roots),
      "scope_selection_mode":doc["scope_selection_mode"],
      "default_scopes_not_monitored":doc["default_scopes_not_monitored"],
      "coverage_is_partial":True,
      "monitored_files_before":doc["baseline_files"],
      "monitored_files_after":len(after),
      "bytes_hashed_after":total,
      **changes,
      "guest_observation_self_reported":observation,
      "guest_vm_execution_independently_verified":False,
      "complete_host_save_coverage_verified":False,
      "true_runtime_save_path_in_source_verified":False,
      "host_saves_globally_isolated_proven":False,
      "assets_rights_verified":False,
      "R07_R08_R09_approved":False,
      "gameplay_approved":False,
      "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
      "paths_names_and_saves_in_report":False,
      "next_action":"Upload only this JSON summary, never private-baseline.json or save files.",
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group()
    group.add_argument("--before",action="store_true")
    group.add_argument("--after")
    p.add_argument("--clone-sha")
    p.add_argument("--latest",action="store_true")
    p.add_argument("--native-inventory",type=Path)
    p.add_argument("--watch-dir",action="append",type=Path)
    p.add_argument("--observation",default="not_run",
                   choices=("not_run","launch_failed","launched","rendered_map","save_inside_vm"))
    args=p.parse_args(argv)
    try:
        if args.before:
            if not args.native_inventory or bool(args.latest)==bool(args.clone_sha):
                blocked("--before precisa de --native-inventory e --latest OU --clone-sha")
            if platform.system()!="Windows":
                blocked("B11 exige Windows com sandbox real para executar o snapshot")
            clone,sha_val=b10.find_clone(ROOT,args.clone_sha,args.latest)
            evidence=b10.run(project=ROOT,clone_sha=sha_val,
                native_inventory=args.native_inventory,prepare=False)
            if evidence.get("sandbox_supported") is not True or evidence.get("clone_total_map_ids")!=702:
                blocked("B10 ou 702 MapIDs nao validados")
            if args.watch_dir:
                roots=args.watch_dir
                mode="explicit"
                missing=None
            else:
                candidates=default_scopes()
                roots=[x for x in candidates if x.is_dir() or link(x)]
                mode="default"
                missing=len(candidates)-len(roots)
            result=prepare_before(ROOT,sha_val,roots,
                scope_selection_mode=mode,
                default_scopes_not_monitored=missing)
        elif args.after:
            if args.before or args.latest or args.clone_sha or args.native_inventory or args.watch_dir:
                blocked("--after nao pode modificar o escopo do snapshot")
            result=inspect_after(ROOT,args.after,args.observation)
        else:
            if (any((args.latest,args.clone_sha,args.native_inventory,args.watch_dir))
                or args.observation!="not_run"):
                blocked("informe --before ou --after")
            c=load(CONTRACT);c10=load(b10.CONTRACT);c09=load(b09.CONTRACT)
            check_contract(c,c10,c09)
            result={"stage":"B11","status":"B11_CODE_READY_NO_WINDOWS_EVIDENCE",
                    "requires_b10_session":True,
                    "runtime_save_coverage_proven":False,
                    "native_game_tested":False,
                    "phase_b_approved":0}
        print(json.dumps(result,indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,OverflowError) as ex:
        # Never print raw OS exceptions containing filenames, root names,
        # full paths, HMAC keys, or details from a private save.
        message=str(ex)
        print(message if message.startswith("SINNOH_B11_BLOCKED:")
              else "SINNOH_B11_BLOCKED: erro na auditoria privada; consulte apenas o estado local",
              file=sys.stderr)
        return 2
if __name__=="__main__":
    raise SystemExit(main())
