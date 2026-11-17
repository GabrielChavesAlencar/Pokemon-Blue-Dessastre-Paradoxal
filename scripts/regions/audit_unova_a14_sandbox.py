#!/usr/bin/env python3
"""A14: prepare controlled Windows Sandbox runtime test from a verified A13 clone.

No Game.exe is launched on host. The .wsb file must be opened separately.
The host game's QA clone and launcher assets are mapped READ-ONLY; ONLY a new,
dedicated reports-only folder is writable from the sandbox. Even a successful
process exit does not certify save paths or Unova gameplay.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import audit_unova_a13_private_qa as a13
import audit_unova_a04_mapids as a04

REPORT=Path(".blue-work/unova/audit")
STATUS="A14_SANDBOX_CONFIG_PREPARED_RUNTIME_NOT_STARTED"
QA_NAME=re.compile(r"qa-unova-a13-[a-f0-9]{16}\Z")
HASH=re.compile(r"[0-9a-f]{64}\Z")
ROOT_NAME="PokemonBlueUnovaMapids"
SCRIPT_NAME="RUN_SANDBOX_QA.cmd"
CONFIG_NAME="ABRIR_A14_WINDOWS_SANDBOX.wsb"
RUNTIME_LOG="A14_SANDBOX_RUNTIME.txt"
MAX_METADATA=16*1024*1024
KEY_FILES=("Game.exe","Data/MapInfos.rxdata","Data/Map001.rxdata",
           "Data/Scripts.rxdata","Data/System.rxdata")

def blocked(reason):
    raise ValueError("UNOVA_A14_BLOCKED: "+str(reason))

def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()

def sha_file(p):
    return a13.hash_file(p)

def no_links(path):
    a13.no_symlink_ancestors(path)
    if path.exists() and a13.path_is_link(path):
        blocked("junction/symlink: "+str(path))

def read_evidence(qa:Path):
    file=qa/a13.INVENTORY_FILE
    if file.is_symlink() or not file.is_file() or file.stat().st_size>MAX_METADATA:
        blocked("A13 manifest missing or too large")
    try:
        evidence=json.loads(file.read_text("utf-8"))
    except (ValueError,UnicodeError) as exc:
        blocked("A13 manifest invalid: "+str(exc))
    if not isinstance(evidence,dict) or evidence.get("phase")!="A13" or (
        evidence.get("status")!=a13.STATUS or
        evidence.get("approved_for_gameplay") is not False or
        evidence.get("runtime_save_isolation_tested") is not False or
        evidence.get("game_exe_launched") is not False or
        evidence.get("native_game_modified") is not False or
        evidence.get("qa_clone_path")!=str(qa)):
        blocked("A13 evidence does not match inert private QA")
    listing=evidence.get("copied_files")
    if not isinstance(listing,list) or not listing or len(listing)>a13.MAX_FILES:
        blocked("A13 complete file listing absent")
    digest={}
    for entry in listing:
        if not isinstance(entry,dict) or not isinstance(entry.get("path"),str):
            blocked("bad A13 source file entry")
        if entry["path"] in KEY_FILES:
            digest[entry["path"]]=entry.get("sha256")
    if set(digest)!=set(KEY_FILES) or any(
            not isinstance(v,str) or not HASH.fullmatch(v) for v in digest.values()):
        blocked("core native file hashes missing")
    for name,expected in digest.items():
        p=qa/name
        if p.is_symlink() or not p.is_file() or sha_file(p)!=expected:
            blocked("QA core file changed: "+name)
    if digest["Data/MapInfos.rxdata"]!=evidence.get("source_mapinfos_sha256"):
        blocked("A04 and A13 MapInfos differ")
    if digest["Data/Map001.rxdata"]!=evidence.get("source_map001_sha256"):
        blocked("A04 and A13 Map001 differ")
    for forbidden in ("Saves","Save","Savedata","SaveData","AppData",".blue-work"):
        if (qa/forbidden).exists() or (qa/forbidden).is_symlink():
            blocked("QA includes private save directory: "+forbidden)
    for p in (qa/"Data",qa):
        for candidate in p.glob("File*.rxdata"):
            blocked("QA contains a potentially private save file: "+candidate.name)
    config=qa/"mkxp.json"
    ini=qa/"Game.ini"
    if any(x.is_symlink() or not x.is_file() for x in (config,ini)):
        blocked("QA save profile config missing or unsafe")
    source_profile=evidence.get("qa_profile")
    if not isinstance(source_profile,dict):
        blocked("QA profile missing")
    actual=a13.jsonc(config.read_text("utf-8-sig"))
    if a13.restricted_keys(actual):
        blocked("QA mkxp contains custom save path")
    fields={"windowTitle":"window_title","dataPathApp":"dataPathApp","dataPathOrg":"dataPathOrg"}
    for k,proof_key in fields.items():
        if actual.get(k)!=source_profile.get(proof_key):
            blocked("QA mkxp profile differs from A13 evidence: "+k)
    ini_text=ini.read_text("utf-8-sig")
    title=source_profile["window_title"]
    if ini_text.count("Title="+title)!=1:
        blocked("QA Game.ini title differs")
    if not (source_profile["dataPathApp"].startswith("BlueUnovaA13QA-")
            and source_profile["dataPathOrg"].startswith("DessastreUnovaA13QA-")):
        blocked("QA namespace is not an A13-specific namespace")
    return {"file_count":evidence.get("source_file_count"),
            "source_bytes":evidence.get("source_bytes"),
            "qa_profile":source_profile,
            "source_mapinfos_sha256":digest["Data/MapInfos.rxdata"],
            "source_map001_sha256":digest["Data/Map001.rxdata"],
            "core_files_verified":sorted(digest),
            "entire_qa_rehashed_now":False,
            "no_runtime_save_path_proven":True}

def sandbox_cmd():
    # Windows Sandbox is an independent OS environment; host game paths only
    # appear as read-only mappings. Exiting the game records a log, never approval.
    return (
        '@echo off\r\n'
        'setlocal EnableExtensions DisableDelayedExpansion\r\n'
        'title UNOVA A14 - TESTE SOMENTE NO WINDOWS SANDBOX\r\n'
        'set "QA_SRC=C:\\UNOVA_A14_RO"\r\n'
        'set "QA_DST=C:\\UNOVA_A14_TEST"\r\n'
        'set "RPT=C:\\UNOVA_A14_REPORTS"\r\n'
        'set "LOG=%RPT%\\A14_SANDBOX_RUNTIME.txt"\r\n'
        'echo A14_STATUS=SANDBOX_SESSION_STARTED_NOT_CERTIFIED>"%LOG%"\r\n'
        'echo A14_SANDBOX_HOST_MAPPINGS_READONLY_GAME_AND_TOOLS=CONFIGURED>>"%LOG%"\r\n'
        'echo A14_GAME_RUNTIME_SAVE_PATH_VERIFIED=NO>>"%LOG%"\r\n'
        'echo A14_HOST_GAME_OR_SAVES_MODIFIED=NOT_TESTED_DIRECTLY>>"%LOG%"\r\n'
        'echo A14_UNOVA_MAPS_INSTALLED=NO>>"%LOG%"\r\n'
        'echo A14_GAME_EXE_STARTED=NO>>"%LOG%"\r\n'
        'echo A14_START_DATE=%DATE% %TIME%>>"%LOG%"\r\n'
        'if not exist "%QA_SRC%\\Game.exe" goto :missing\r\n'
        'if not exist "%QA_SRC%\\unova-a13-copy-evidence.json" goto :missing\r\n'
        'if not exist "%RPT%" goto :noreport\r\n'
        'if not exist "%QA_DST%" mkdir "%QA_DST%"\r\n'
        'echo Copiando a QA para o disco TEMPORARIO do Sandbox...\r\n'
        'robocopy "%QA_SRC%" "%QA_DST%" /E /XJ /R:0 /W:0 /NFL /NDL > "%RPT%\\A14_SANDBOX_COPY.txt"\r\n'
        'if errorlevel 8 goto :copyfail\r\n'
        'if not exist "%QA_DST%\\Game.exe" goto :copyfail\r\n'
        'echo A14_SANDBOX_PRIVATE_COPY_CREATED=YES>>"%LOG%"\r\n'
        'echo.\r\n'
        'echo   O Game.exe sera executado SOMENTE nesta VM descartavel.\r\n'
        'echo   Nao carregue saves pessoais e nao use esta copia para jogar de verdade.\r\n'
        'echo   Para testar salvamento, use apenas um novo save descartavel.\r\n'
        'echo.\r\n'
        'choice /C NS /M "Deseja iniciar o Game.exe de teste? (N=nao, S=sim)"\r\n'
        'if errorlevel 2 goto :run\r\n'
        'echo A14_USER_DECLINED_LAUNCH=YES>>"%LOG%"\r\n'
        'goto :done\r\n'
        ':run\r\n'
        'echo A14_GAME_EXE_STARTED=ATTEMPTED>>"%LOG%"\r\n'
        'echo A14_GAME_START_DATE=%DATE% %TIME%>>"%LOG%"\r\n'
        'cd /d "%QA_DST%"\r\n'
        'start "" /wait "%QA_DST%\\Game.exe"\r\n'
        'set "EXITCODE=%ERRORLEVEL%"\r\n'
        'echo A14_GAME_PROCESS_EXIT_CODE=%EXITCODE%>>"%LOG%"\r\n'
        'echo A14_GAME_EXIT_DATE=%DATE% %TIME%>>"%LOG%"\r\n'
        'echo A14_GAMEPLAY_APPROVED=NO>>"%LOG%"\r\n'
        'echo A14_RUNTIME_SAVE_PATH_PROVED=NO>>"%LOG%"\r\n'
        'echo A14_SANDBOX_APPDATA_FILE_LIST_BEGIN>>"%LOG%"\r\n'
        'if exist "%APPDATA%" dir /S /B /A:-D "%APPDATA%" >>"%LOG%" 2>NUL\r\n'
        'if exist "%LOCALAPPDATA%" dir /S /B /A:-D "%LOCALAPPDATA%" >>"%LOG%" 2>NUL\r\n'
        'echo A14_SANDBOX_APPDATA_FILE_LIST_END>>"%LOG%"\r\n'
        'goto :done\r\n'
        ':missing\r\n'
        'echo A14_ERROR=SOURCE_MISSING>>"%LOG%"\r\n'
        'goto :done\r\n'
        ':noreport\r\n'
        'echo Pasta de relatorios nao compartilhada. Teste abortado.\r\n'
        'goto :done\r\n'
        ':copyfail\r\n'
        'echo A14_ERROR=PRIVATE_COPY_FAILED>>"%LOG%"\r\n'
        ':done\r\n'
        'echo A14_TEST_FINISHED_DATE=%DATE% %TIME%>>"%LOG%"\r\n'
        'echo.\r\n'
        'echo Relatorio: C:\\UNOVA_A14_REPORTS\\A14_SANDBOX_RUNTIME.txt\r\n'
        'echo Envie o relatorio, NAO envie os arquivos de save nem o jogo.\r\n'
        'echo Feche esta VM quando terminar; o jogo de teste sera descartado.\r\n'
        'pause\r\n'
        'exit /b 0\r\n'
    ).encode("utf-8")

def make_wsb(qa:Path,tool_dir:Path,reports:Path):
    root=ET.Element("Configuration")
    for name in ("VGpu","Networking","AudioInput","VideoInput",
                 "PrinterRedirection","ClipboardRedirection"):
        ET.SubElement(root,name).text="Disable"
    mappings=ET.SubElement(root,"MappedFolders")
    for folder,sandbox,readonly in (
         (qa,r"C:\UNOVA_A14_RO",True),
         (tool_dir,r"C:\UNOVA_A14_TOOLS",True),
         (reports,r"C:\UNOVA_A14_REPORTS",False)):
        m=ET.SubElement(mappings,"MappedFolder")
        ET.SubElement(m,"HostFolder").text=str(folder)
        ET.SubElement(m,"SandboxFolder").text=sandbox
        ET.SubElement(m,"ReadOnly").text="true" if readonly else "false"
    logon=ET.SubElement(root,"LogonCommand")
    ET.SubElement(logon,"Command").text=r"cmd.exe /c C:\UNOVA_A14_TOOLS\RUN_SANDBOX_QA.cmd"
    return (ET.tostring(root,encoding="unicode",xml_declaration=False)+"\n").encode("utf-8")

def ensure_file(path:Path,payload:bytes):
    no_links(path)
    if path.exists():
        if not path.is_file() or path.read_bytes()!=payload:
            blocked("existing A14 asset changed; no overwrite: "+str(path))
    else:
        with path.open("xb") as f:f.write(payload)

def prepare(qa_path:Path,a13_result:dict,localappdata:Path,progress=None):
    """One-click host preflight. Does NOT launch, even if Windows Sandbox exists."""
    qa=Path(qa_path).absolute()
    local=Path(localappdata).absolute()
    if not local.is_dir():
        blocked("LOCALAPPDATA invalid")
    no_links(local);no_links(qa)
    expected_parent=local/ROOT_NAME/"qa-copies"
    if (qa.parent!=expected_parent or not QA_NAME.fullmatch(qa.name)
        or not qa.is_dir()):
        blocked("QA A13 not in expected private path")
    if not isinstance(a13_result,dict) or a13_result.get("status") not in (
            a13.STATUS,"QA_BASELINE_EXISTING_VERIFIED_RUNTIME_UNVERIFIED"
            ) or a13_result.get("path")!=str(qa) or not a13_result.get("profile"):
        blocked("A13 not completed or report path inconsistent")
    if progress:progress("A14: verificando perfil A13 e hashes nativos essenciais...")
    evidence=read_evidence(qa)
    if evidence["qa_profile"]!=a13_result["profile"]:
        blocked("A13 result profile changed")
    identity=qa.name.split("-")[-1]
    base=local/ROOT_NAME/"sandbox-a14"/("qa-"+identity)
    tools=base/"tools"
    reports=base/"reports"
    no_links(base)
    for folder in (base,tools,reports):
        no_links(folder)
        if not folder.exists():folder.mkdir(parents=True,exist_ok=False)
        if not folder.is_dir():blocked("A14 folder invalid")
    script=sandbox_cmd()
    ensure_file(tools/SCRIPT_NAME,script)
    wsb=make_wsb(qa,tools,reports)
    file=base/CONFIG_NAME
    ensure_file(file,wsb)
    found=bool(shutil.which("WindowsSandbox.exe")) if os.name=="nt" else None
    if progress:progress("A14: arquivo .wsb preparado sem executar Game.exe.")
    return {"schema":1,"phase":"A14","region":"UNOVA","status":STATUS,
        "source_a13_qa_path":str(qa),"a13_files":evidence["file_count"],
        "a13_source_bytes":evidence["source_bytes"],
        "source_mapinfos_sha256":evidence["source_mapinfos_sha256"],
        "source_map001_sha256":evidence["source_map001_sha256"],
        "core_files_verified_now":evidence["core_files_verified"],
        "all_qa_files_reverified_now":False,
        "qa_save_namespace_config":evidence["qa_profile"],
        "qa_runtime_save_path_verified":False,
        "host_game_started":False,"sandbox_game_started":False,
        "wsb_configuration_path":str(file),
        "sandbox_script_path":str(tools/SCRIPT_NAME),
        "sandbox_reports_folder":str(reports),
        "runtime_log_expected":str(reports/RUNTIME_LOG),
        "sandbox_binary_found_in_path":found,
        "sandbox_feature_enabled_and_usable":"UNKNOWN_NOT_TESTED",
        "sandbox_host_mappings":[{"path":str(qa),"read_only":True},
                                 {"path":str(tools),"read_only":True},
                                 {"path":str(reports),"read_only":False}],
        "networking_disabled_in_config":True,
        "clipboard_disabled_in_config":True,
        "host_saves_not_read_or_modified_by_preflight":True,
        "source_qa_game_modified":False,
        "gameplay_approved":False,"unova_maps_installed":False,
        "can_reserve_mapids":False,"can_install":False,
        "bar_a_completed":0,"bar_a_total":8,
        "next_manual_step":"DOUBLE_CLICK_WSB_ONLY_IF_WINDOWS_SANDBOX_IS_SUPPORTED"}

def save(project:Path,report:dict):
    project=a04.safe_path(project)
    for folder in (project/".blue-work",project/".blue-work/unova",project/REPORT):
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            blocked("unsafe report location")
        folder.mkdir(exist_ok=True)
    data=(json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+"\n").encode("utf-8")
    dest=project/REPORT/("a14-sandbox-preflight-"+hash_bytes(data)[:16]+".json")
    ensure_file(dest,data)
    return dest
