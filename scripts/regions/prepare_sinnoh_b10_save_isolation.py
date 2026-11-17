#!/usr/bin/env python3
"""B10: make a Windows Sandbox config for a verified B09 QA clone.

Fail closed on unsupported Windows, missing B07/B08/B09 evidence, altered
files, or unsafe paths. Maps TWO readonly folders only: immutable QA game and
a guest-only preparation CMD. No automatic Game.exe launch, no host save access.
This does NOT prove runtime behaviour, rights, native gameplay, or Windows VM
execution until separately observed by the user.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import build_sinnoh_b09_native_qa as b09
from audit_sinnoh_b06_technical_candidate import B00,B01,B04,B05,B06,load,verify_native_zip
from audit_sinnoh_b01_inventory import unpack as unpack_native
from build_sinnoh_b07_private_stage import CONTRACT as B07, MAPNAME
from audit_sinnoh_b08_private_qa import CONTRACT as B08
from sinnoh_staging_transaction import ALLOWED
CONTRACT=ROOT/"data/regions/sinnoh-b10-save-isolation.json"
B09=b09.CONTRACT
WSB_PARENT=".blue-work/sinnoh-b10-sandbox"
SHA=re.compile(r"[a-f0-9]{64}\Z")
SAVED_NAMES=("B10_ISOLAMENTO.wsb","B10_PREPARAR_NO_WINDOWS_SANDBOX.cmd","B10_SESSAO.json")
GUEST_SOURCE=r"C:\SinnohB10Source"
GUEST_TOOLS=r"C:\SinnohB10Tools"
GUEST_DEST=r"C:\SinnohB10Game"
MAX_RECEIPT_BYTES=20_000_000
MAX_HASH_BYTES=14*1024*1024*1024

def blocked(reason):
    raise ValueError("SINNOH_B10_BLOCKED: "+reason)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def is_link(p):
    return b09.is_link(p)

def check_contract(c,b09c,b08,b07,b06,b00,b01,b04,b05):
    terrain=b09.check_contract(b09c,b08,b07,b06,b00,b01,b04,b05)
    expected={
      "schema":1,"region":"SINNOH","stage":"B10",
      "status":"WINDOWS_SANDBOX_SAVE_ISOLATION_PREPARED_NO_NATIVE_EXECUTION",
      "b09_clone_status":b09c["status"],
      "b09_clone_workspace":b09c["clone_workspace_subdir"],
      "native_b01_inventory_sha256":b09c["native_inventory_sha256"],
      "native_mapinfos_sha256":b01["mapinfos_sha256"],
      "native_tilesets_sha256":b01["tilesets_sha256"],
      "expected_original_maps":648,
      "expected_sinnoh_maps":len(terrain),
      "expected_clone_maps":702,
      "supported_isolation":"WINDOWS_SANDBOX_HYPERV_VM_ONLY",
      "supported_windows_editions":["Professional","Enterprise","Education"],
      "sandbox_feature":"Containers-DisposableClientVM",
      "sandbox_config_subdir":WSB_PARENT,
      "mapped_clone_read_only":True,
      "mapped_tools_read_only":True,
      "network_disabled":True,
      "clipboard_disabled":True,
      "vGPU_disabled":True,
      "printer_redirection_disabled":True,
      "audio_video_input_disabled":True,
      "no_logon_command":True,
      "game_exe_started_automatically":False,
      "sandbox_edition_and_feature_checked_at_runtime":True,
      "unsupported_windows_must_block":True,
      "guest_game_copy_required_before_any_run":True,
      "host_data_and_saves_never_mapped":True,
      "may_start_original_game":False,
      "host_saves_runtime_isolation_tested":False,
      "guest_game_tested":False,
      "asset_rights_verified":False,
      "future_regional_reservations_verified":False,
      "real_b09_user_report_received":False,
      "r07_complete":False,"r08_complete":False,"r09_complete":False,
      "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0
    }
    if type(c) is not dict or c!=expected:
        blocked("contrato de isolamento B10 alterado ou afirmacao de teste falsa")
    return terrain

def find_clone(project,plan_sha=None,latest=False):
    if bool(plan_sha)==bool(latest):
        blocked("escolha --latest ou --clone-sha")
    root=b09.clone_root(project)
    if latest:
        if not root.is_dir():blocked("copia B09 nao encontrada")
        items=[p for p in root.iterdir() if p.is_dir()
            and re.fullmatch(r"native-[a-f0-9]{16}",p.name)]
        if len(items)!=1:blocked("exatamente uma copia B09 exigida; escolha --clone-sha")
        folder=items[0]
        manifest=folder/"B09_PRIVATE_QA_MANIFEST.json"
        if is_link(manifest) or not manifest.is_file():
            blocked("manifesto da copia B09 ausente")
        obj=json.loads(manifest.read_text("utf-8"))
        plan_sha=obj.get("plan_sha256")
    if type(plan_sha) is not str or not SHA.fullmatch(plan_sha):
        blocked("SHA de clone B09 invalido")
    folder=root/f"native-{plan_sha[:16]}"
    if is_link(folder) or not folder.is_dir() or not folder.resolve().is_relative_to(root.resolve()):
        blocked("copia B09 privada ausente ou link")
    return folder,plan_sha

def safe_rel(name):
    if type(name) is not str or not name or len(name)>512:
        blocked("nome de arquivo B09 invalido")
    if name.startswith(("\\","/")) or "\\" in name or ":" in name or "\x00" in name:
        blocked("caminho Windows inseguro no B09")
    p=PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or "." in p.parts or len(p.parts)>16:
        blocked("caminho de clone com traversal")
    if any(x.endswith((".", " ")) or not x for x in p.parts):
        blocked("componente Windows ambiguo")
    if any(re.fullmatch(r"(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?",x)
           for x in p.parts):
        blocked("nome reservado Windows")
    return p

def audit_clone(project,folder,plan_sha,c,b09c,b01,b05):
    """Recalculate EVERY copied file and the B09 plan, reject saves/extra files."""
    manifest=folder/"B09_PRIVATE_QA_MANIFEST.json"
    if is_link(manifest) or not manifest.is_file() or manifest.stat().st_size>MAX_RECEIPT_BYTES:
        blocked("manifesto B09 ausente ou grande")
    doc=json.loads(manifest.read_text("utf-8"))
    strict={
        "schema":1,"region":"SINNOH","stage":"B09",
        "mode":"PRIVATE_NATIVE_QA_CLONE_UNTESTED",
        "plan_sha256":plan_sha,
        "game_exe_in_clone":True,"game_exe_launched":False,
        "saves_copied":False,"save_isolation_verified":False,
        "DO_NOT_LAUNCH":True,
        "rights_verified":False,"r07_complete":False,
        "r08_complete":False,"r09_complete":False,
        "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
        "source_game_untouched":True
    }
    if type(doc) is not dict or set(doc)!=set(strict)|{
        "stage_sha256","files","native_files_copied","overlay_files_copied"
    } or any(doc.get(k)!=v for k,v in strict.items()):
        blocked("manifesto B09 nao prova copiagem privada intacta")
    stage_sha=doc.get("stage_sha256")
    if type(stage_sha) is not str or not SHA.fullmatch(stage_sha):
        blocked("stage B07/B08 nao identificado")
    rows=doc.get("files")
    if type(rows) is not list or not rows or len(rows)>b09.MAX_FILES+100:
        blocked("lista B09 invalida")
    expected_native=b09c["expected_installed_native_map_count"]
    expected_sinnoh=b09c["expected_sinnoh_terrain_maps_in_clone"]
    source_ids=set()
    stage_ids=set()
    native_count=0
    overlay_count=0
    seen=set()
    final={}
    total=0
    for row in rows:
        if type(row) is not dict or set(row)!={"path","bytes","sha256","origin"}:
            blocked("registro B09 invalido")
        rel=row["path"]
        safe_rel(rel)
        origin=row["origin"]
        if origin not in ("NATIVE","OVERLAY"):
            blocked("origem inesperada no B09")
        if (type(row["bytes"]) is not int or not 0<=row["bytes"]<=b09.MAX_SINGLE
            or type(row["sha256"]) is not str or not SHA.fullmatch(row["sha256"])):
            blocked("hash/tamanho de B09 invalido")
        folded=(rel.casefold(),origin)
        if folded in seen:blocked("arquivo B09 duplicado")
        seen.add(folded)
        if origin=="NATIVE":
            if b09.should_skip(Path(rel)):blocked("save/pasta pessoal no B09")
            native_count+=1
            m=MAPNAME.fullmatch(Path(rel).name) if len(PurePosixPath(rel).parts)==2 and rel.startswith("Data/") else None
            if m:source_ids.add(int(m.group(1)))
        else:
            if not ALLOWED.fullmatch(rel):
                blocked("overlay B08 fora da allowlist")
            overlay_count+=1
            m=re.fullmatch(r"Data/Map([0-9]{3})\.rxdata",rel)
            if m:stage_ids.add(int(m.group(1)))
        final[rel]=row
        total+=row["bytes"]
        if total>MAX_HASH_BYTES:blocked("copia ultrapassa limite")
    if rows!=sorted(rows,key=lambda x:(x["path"],x["origin"])):
        blocked("ordem do B09 adulterada")
    signed=sha(json.dumps({"stage_sha256":stage_sha,"files":rows},
        sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii"))
    if signed!=plan_sha:blocked("assinatura SHA do plano B09 alterada")
    if (native_count!=doc["native_files_copied"]
        or overlay_count!=doc["overlay_files_copied"]):
        blocked("contagem dos arquivos B09 incoerente")
    from audit_sinnoh_b05_mapid_planning import expand
    occupied=expand(b05["occupied"]["ranges"],limit=999)
    if (source_ids!=occupied or len(source_ids)!=expected_native
        or stage_ids!=set(c["candidate_installed_sinnoh_ids"])
        or len(stage_ids)!=expected_sinnoh
        or stage_ids&source_ids):
        blocked("MapIDs B09/Sinnoh colidem com B01 ou Unova")
    for key,baseline in (("Data/MapInfos.rxdata",b01["mapinfos_sha256"]),
                         ("Data/Tilesets.rxdata",b01["tilesets_sha256"])):
        if not any(x["path"]==key and x["origin"]=="NATIVE"
                   and x["sha256"]==baseline for x in rows):
            blocked("B09 nao preserva baseline nativo: "+key)
        if not any(x["path"]==key and x["origin"]=="OVERLAY" for x in rows):
            blocked("B09 nao adicionou MapInfos/Tilesets Sinnoh")
    if not any(x["path"]=="Game.exe" and x["origin"]=="NATIVE" for x in rows):
        blocked("B09 sem Game.exe do usuário")
    actual=set()
    for p in folder.rglob("*"):
        if is_link(p):blocked("clone contem symlink/junction")
        if p.is_file():
            relative=p.relative_to(folder).as_posix()
            safe_rel(relative)
            actual.add(relative)
    expected=set(final)|{
        "B09_PRIVATE_QA_MANIFEST.json","NAO_EXECUTAR_ANTES_DE_ISOLAR_SAVES.txt"
    }
    if actual!=expected:blocked("clone tem arquivos desconhecidos ou saves")
    note=folder/"NAO_EXECUTAR_ANTES_DE_ISOLAR_SAVES.txt"
    if not note.is_file() or "QA PRIVADO B09" not in note.read_text("utf-8"):
        blocked("aviso B09 de nao executar ausente")
    for name,row in final.items():
        path=folder/name
        if (is_link(path) or not path.is_file()
            or path.stat().st_size!=row["bytes"]
            or b09.file_sha(path)!=row["sha256"]):
            blocked("arquivo B09 adulterado: "+name)
    if any(b09.SENSITIVE_FILE.fullmatch(PurePosixPath(name).name) for name in final):
        blocked("possivel save presente em clone B09")
    return {"B09_full_hashes_verified":len(final),
            "native_map_ids_confirmed":len(source_ids),
            "sinnoh_map_ids_confirmed":len(stage_ids),
            "clone_total_map_ids":len(source_ids|stage_ids),
            "source_stage_sha256":stage_sha,
            "clone_sha256":plan_sha}

def probe_windows_sandbox():
    if platform.system()!="Windows":
        return {"supported":False,"reason":"NOT_WINDOWS",
                "edition":"UNKNOWN","feature_enabled":False}
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
            edition=str(winreg.QueryValueEx(key,"EditionID")[0])
    except (OSError,ImportError):
        return {"supported":False,"reason":"WINDOWS_EDITION_UNKNOWN",
                "edition":"UNKNOWN","feature_enabled":False}
    if not edition.casefold().startswith(("professional","enterprise","education")):
        return {"supported":False,"reason":"WINDOWS_EDITION_UNSUPPORTED",
                "edition":"UNSUPPORTED","feature_enabled":False}
    try:
        proc=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive",
            "-Command","(Get-WindowsOptionalFeature -Online -FeatureName 'Containers-DisposableClientVM' -ErrorAction Stop).State.ToString()"],
            capture_output=True,text=True,timeout=30)
    except (OSError,subprocess.TimeoutExpired):
        return {"supported":False,"reason":"SANDBOX_FEATURE_QUERY_FAILED",
                "edition":"SUPPORTED","feature_enabled":False}
    if proc.returncode!=0 or not any(x.strip().casefold()=="enabled"
                                     for x in proc.stdout.splitlines()):
        return {"supported":False,"reason":"SANDBOX_FEATURE_NOT_ENABLED",
                "edition":"SUPPORTED","feature_enabled":False}
    return {"supported":True,"reason":"SUPPORTED_AND_FEATURE_ENABLED",
            "edition":"SUPPORTED","feature_enabled":True}

def xml_wsb(clone_path,tools_path):
    root=ET.Element("Configuration")
    def element(tag,val):
        ET.SubElement(root,tag).text=val
    element("vGPU","Disable")
    element("Networking","Disable")
    element("AudioInput","Disable")
    element("VideoInput","Disable")
    element("ProtectedClient","Enable")
    element("PrinterRedirection","Disable")
    element("ClipboardRedirection","Disable")
    mapped=ET.SubElement(root,"MappedFolders")
    for host,guest in ((clone_path,GUEST_SOURCE),(tools_path,GUEST_TOOLS)):
        node=ET.SubElement(mapped,"MappedFolder")
        ET.SubElement(node,"HostFolder").text=str(host)
        ET.SubElement(node,"SandboxFolder").text=guest
        ET.SubElement(node,"ReadOnly").text="true"
    # No LogonCommand. User chooses if/when to run Game.exe inside guest.
    return '<?xml version="1.0" encoding="utf-8"?>\n'+ET.tostring(
        root,encoding="unicode")+"\n"

GUEST_CMD=r"""@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Sinnoh B10 - Preparar jogo APENAS dentro da Windows Sandbox
echo.
echo [B10] Este script so deve ser executado DENTRO da Windows Sandbox.
echo A origem mapeada e SOMENTE LEITURA; o destino fica dentro da VM.
if not exist "C:\SinnohB10Source\B09_PRIVATE_QA_MANIFEST.json" goto :failed
if not exist "C:\SinnohB10Source\Game.exe" goto :failed
if exist "C:\SinnohB10Game" (
  echo [BLOQUEADO] Ja existe C:\SinnohB10Game. Nao sobrescrever.
  goto :failed
)
echo.
echo Copiando o jogo privado para C:\SinnohB10Game (gravavel somente na VM)...
robocopy "C:\SinnohB10Source" "C:\SinnohB10Game" /E /R:0 /W:0 /NFL /NDL /NJH /NJS /NP
if errorlevel 8 goto :failed
if not exist "C:\SinnohB10Game\Game.exe" goto :failed
if not exist "C:\SinnohB10Game\Data\Map442.rxdata" goto :failed
if not exist "C:\SinnohB10Game\Data\Map495.rxdata" goto :failed
echo.
echo [OK] Copia PRIVADA pronta dentro da Windows Sandbox.
echo Este teste NAO modifica arquivos da instalacao original.
echo CONFIRME que esta na janela da Windows Sandbox antes de iniciar.
echo Se desejar um teste MANUAL, abra C:\SinnohB10Game\Game.exe
echo NAO abra Game.exe em C:\SinnohB10Source nem no Windows principal.
echo Ao fechar a Sandbox, os saves e arquivos criados aqui serao descartados.
echo.
pause
exit /b 0
:failed
echo [B10 BLOQUEADA] Diretórios ausentes, pasta previa existente ou copia falhou.
echo Nenhum jogo foi executado por este script.
pause
exit /b 2
"""

def session_root(project):
    project=Path(project).absolute()
    work=b09.clone_root(project).parent
    dest=work/"sinnoh-b10-sandbox"
    if is_link(dest) or not dest.resolve().is_relative_to(project.resolve()):
        blocked("B10 nao pode criar pasta fora do workspace privado")
    return dest

def prepare_session(project,clone_folder,plan_sha,proof,host):
    if host.get("supported") is not True or host.get("feature_enabled") is not True:
        blocked("Windows Sandbox (Pro/Enterprise/Education e recurso habilitado) obrigatoria")
    root=session_root(project)
    if not root.parent.exists():blocked("workspace original nao encontrado")
    target=root/f"session-{plan_sha[:16]}"
    if target.exists() or is_link(target):
        blocked("sessao B10 existente: nao sobrescrever")
    root.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix=".sinnoh-b10-",dir=root))
    try:
        tools=temp/"tools"
        tools.mkdir()
        guest=tools/"B10_PREPARAR_NO_WINDOWS_SANDBOX.cmd"
        guest.write_text(GUEST_CMD,encoding="utf-8",newline="\r\n")
        wsb=xml_wsb(str(clone_folder),str(target/"tools"))
        config=temp/"B10_ISOLAMENTO.wsb"
        config.write_text(wsb,encoding="utf-8")
        proof_host={
           "schema":1,"region":"SINNOH","stage":"B10",
           "status":"WSB_CONFIG_PREPARED_NOT_LAUNCHED",
           "source_clone_sha256":plan_sha,
           "source_stage_sha256":proof["source_stage_sha256"],
           "native_map_ids":proof["native_map_ids_confirmed"],
           "sinnoh_terrain_map_ids":proof["sinnoh_map_ids_confirmed"],
           "expected_total_maps":proof["clone_total_map_ids"],
           "all_cloned_files_sha_verified":True,
           "sandbox_feature_enabled_on_host":True,
           "sandbox_session_started":False,
           "game_exe_started":False,"save_write_isolation_runtime_verified":False,
           "host_save_directories_mapped":False,
           "mapped_folders_read_only":True,
           "internet_networking_enabled":False,
           "clipboard_enabled":False,
           "guest_game_copy_completed":False,
           "rights_verified":False,
           "r07_complete":False,"r08_complete":False,"r09_complete":False,
           "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
           "note":"Host config verified but WSB guest and Game.exe not executed by B10 tool."
        }
        receipt=temp/"B10_SESSAO.json"
        receipt.write_text(json.dumps(proof_host,indent=2,ensure_ascii=False)+"\n",
                           encoding="utf-8")
        if target.exists() or is_link(target):blocked("sessao B10 apareceu em paralelo")
        temp.rename(target)
    except BaseException:
        if temp.exists():shutil.rmtree(temp)
        raise
    return {
      **proof_host,
      "config_relative_path":(target/"B10_ISOLAMENTO.wsb").relative_to(project).as_posix(),
      "guest_instructions":"Dentro da Sandbox, execute C:\\SinnohB10Tools\\B10_PREPARAR_NO_WINDOWS_SANDBOX.cmd manualmente. Depois, se desejar, abra C:\\SinnohB10Game\\Game.exe apenas dentro da VM.",
      "can_start_game_on_host":False
    }

def run(*,project=ROOT,clone_sha=None,latest=False,native_inventory,
        prepare=False,host_probe=probe_windows_sandbox):
    project=Path(project).absolute()
    c,b09c,b08,b07,b06,b00,b01,b04,b05=(
       load(project/p) for p in (
         "data/regions/sinnoh-b10-save-isolation.json",
         "data/regions/sinnoh-b09-native-qa.json",
         "data/regions/sinnoh-b08-private-qa.json",
         "data/regions/sinnoh-b07-private-stage.json",
         "data/regions/sinnoh-b06-technical-candidate.json",
         "data/regions/sinnoh-b00-actual-source.json",
         "data/regions/sinnoh-b01-actual-native.json",
         "data/regions/sinnoh-b04-v2-validated.json",
         "data/regions/sinnoh-b05-mapid-planning.json"))
    terrain=check_contract(c,b09c,b08,b07,b06,b00,b01,b04,b05)
    clone,plan_sha=find_clone(project,clone_sha,latest)
    native_zip=Path(native_inventory)
    verify_native_zip(native_zip,b06,b05)
    inv,raw=unpack_native(native_zip)
    proof=audit_clone(project,clone,plan_sha,c,b09c,b01,b05)
    b08_files,b08_audit=b09.check_qa_overlay(
        project,proof["source_stage_sha256"],
        native_raw=raw,
        expected_ids=[x["candidate_destination_map_id"] for x in terrain])
    for rel,data in b08_files.items():
        item=clone/rel
        if not item.is_file() or b09.file_sha(item)!=sha(data):
            blocked("clone B09 difere do overlay B08: "+rel)
    if b08_audit["maps_validated"]!=54 or b08_audit["pngs_verified"]!=14:
        blocked("B08 nao validou os 54 mapas e 14 PNGs")
    host=host_probe()
    if prepare:
        out=prepare_session(project,clone,plan_sha,proof,host)
    else:
        out={**proof,
            "status":"B10_DRY_RUN_NO_FILES_WRITTEN",
            "sandbox_supported":host["supported"],
            "sandbox_support_reason":host["reason"],
            "game_exe_started":False,
            "host_saves_mapped":False,"safe_to_launch_on_host":False,
            "phase_b_approved":0}
    return out

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--clone-sha")
    p.add_argument("--latest",action="store_true")
    p.add_argument("--native-inventory",type=Path)
    p.add_argument("--prepare",action="store_true",help="Write .wsb ONLY in .blue-work, never launch")
    p.add_argument("--probe",action="store_true",help="Check Windows edition and Sandbox feature only")
    args=p.parse_args(argv)
    try:
        if args.probe:
            if args.latest or args.clone_sha or args.native_inventory or args.prepare:
                blocked("--probe nao combina com outros comandos")
            result=probe_windows_sandbox()
        elif not any((args.clone_sha,args.latest,args.native_inventory,args.prepare)):
            c=load(CONTRACT)
            b09c=load(B09);b08=load(B08);b07=load(B07)
            b06=load(ROOT/"data/regions/sinnoh-b06-technical-candidate.json")
            b00=load(B00);b01=load(B01);b04=load(B04);b05=load(B05)
            check_contract(c,b09c,b08,b07,b06,b00,b01,b04,b05)
            result={"status":"B10_READY_AWAITING_B09_CLONE_AND_WINDOWS_SANDBOX",
                    "host_save_isolation_proven":False,
                    "game_exe_tested":False,"phase_b_approved":0}
        else:
            if not args.native_inventory:
                blocked("--native-inventory B01 obrigatorio")
            result=run(clone_sha=args.clone_sha,latest=args.latest,
                native_inventory=args.native_inventory,prepare=args.prepare)
        print(json.dumps(result,indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,IndexError,UnicodeError,
            ImportError,OverflowError) as ex:
        print(str(ex),file=sys.stderr)
        return 2

if __name__=="__main__":raise SystemExit(main())
