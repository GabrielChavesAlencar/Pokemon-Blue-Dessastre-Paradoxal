#!/usr/bin/env python3
"""B00: receive externally uploaded RMXP source ZIP for read-only inspection.

The script NEVER unpacks a donor ZIP or writes game, save, audio, map or PBS files.
It reports only source-file *metadata*, not permission, Sinnoh ownership or QA.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from audit_sinnoh_source import audit as audit_source
from audit_sinnoh_source import _zip_parts

MANIFEST=ROOT/"data/regions/sinnoh-b00-source-intake.json"
REQUIRED_KEYS={"schema","region","workstream","step","status","source_candidates",
  "optional_art","mandatory_user_uploads","optional_uploads","intake_mode",
  "source_map_ids_verified","source_map_count_verified",
  "source_sinnoh_map_ids_identified","assets_usage_rights_individually_verified",
  "decades_occupied_map_ids_verified","planned_regions_reservations_verified",
  "source_pbs_or_native_events_installed","game_or_saves_modified",
  "game_exe_tested","joiplay_tested","technical_phase_approved",
  "phase_b_completed","phase_b_total","notes"}
MAX_CREDITS_BYTES=2_000_000
MAX_ZIP_ENTRIES=60000
MAX_ZIP_MEMBER_BYTES=1024**3
MAX_ZIP_TOTAL_BYTES=12*1024**3
CATEGORIES=("tilesets","autotiles","characters","pbs_text","rpg_project")

def blocked(message):
    raise ValueError("SINNOH_B00_BLOCKED: "+message)

def load_manifest(root=ROOT):
    p=Path(root)/"data/regions/sinnoh-b00-source-intake.json"
    if p.is_symlink() or not p.is_file():blocked("manifesto ausente/inseguro")
    d=json.loads(p.read_text("utf-8"))
    if type(d) is not dict or set(d)!=REQUIRED_KEYS:
        blocked("manifesto B00 incompleto/adulterado")
    if (d["schema"]!=1 or d["region"]!="SINNOH" or d["step"]!="B00"
        or d["workstream"]!="B" or d["status"]!="SOURCE_UPLOADED_AND_RXDATA_MAP_TREE_AUDITED_LOCALLY_NOT_INSTALLABLE"
        or d["phase_b_completed"]!=0 or d["phase_b_total"]!=13
        or any(d[key] is not False for key in (
          "assets_usage_rights_individually_verified",
          "decades_occupied_map_ids_verified","planned_regions_reservations_verified",
          "source_pbs_or_native_events_installed","game_or_saves_modified",
          "game_exe_tested","joiplay_tested","technical_phase_approved"
        ))):
        blocked("dados de origem ou aprovacoes nativas fabricados")
    receipt_path=Path(root)/"data/regions/sinnoh-b00-actual-source.json"
    if receipt_path.is_symlink() or not receipt_path.is_file():
        blocked("comprovante de fonte local ausente")
    receipt=json.loads(receipt_path.read_text("utf-8"))
    if (receipt.get("source_zip_sha256")!=d["source_candidates"][0]["donor_package_sha256"]
        or receipt.get("sinnoh_map_count")!=76
        or receipt.get("rights_per_asset_verified") is not False
        or receipt.get("phase_b_technically_approved")!=0):
        blocked("comprovante de fonte auditada adulterado")
    if (d["source_map_ids_verified"] is not True
        or d["source_map_count_verified"] is not True
        or d["source_sinnoh_map_ids_identified"] is not True):
        blocked("mapas reais recebidos precisam de marcador de auditoria")
    candidates=d.get("source_candidates")
    if not isinstance(candidates,list) or len(candidates)!=2:
        blocked("fontes desconhecidas")
    return d

def check_credits(credits):
    if credits is None:return None
    p=Path(credits).expanduser().absolute()
    if p.suffix.lower()!=".txt" or p.is_symlink() or not p.is_file():
        blocked("creditos devem ser arquivo .txt comum")
    if not 0<p.stat().st_size<=MAX_CREDITS_BYTES:
        blocked("creditos ausentes/vazios/grandes demais")
    # sha256 only. This is NOT legal clearance for each included asset.
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    return {"filename":p.name,"sha256":digest,
            "individual_asset_rights_verified":False}

def inspect_extra_zip(source):
    counts=Counter({k:0 for k in CATEGORIES})
    if source is None or Path(source).suffix.lower()!=".zip":
        return dict(counts)
    file=Path(source).expanduser().absolute()
    if file.is_symlink() or not file.is_file():blocked("ZIP da fonte ausente")
    total=0
    seen=set()
    with zipfile.ZipFile(file) as archive:
        members=archive.infolist()
        if len(members)>MAX_ZIP_ENTRIES:blocked("ZIP excede numero seguro de entradas")
        for m in members:
            bits=m.external_attr>>16
            import stat
            if stat.S_IFMT(bits)==stat.S_IFLNK or (m.flag_bits & 1):
                blocked("ZIP inclui link ou arquivo criptografado")
            parts=_zip_parts(m.filename)
            if m.is_dir():continue
            normalized="/".join(parts).casefold()
            if normalized in seen:blocked("ZIP inclui nomes duplicados")
            seen.add(normalized)
            total+=m.file_size
            if m.file_size>MAX_ZIP_MEMBER_BYTES or total>MAX_ZIP_TOTAL_BYTES:
                blocked("ZIP grande demais para preflight")
            lower=tuple(p.casefold() for p in parts)
            if len(lower)<2:continue
            ending=lower[-1]
            parent=lower[-2]
            if parent=="tilesets" and ending.endswith((".png",".bmp")):
                counts["tilesets"]+=1
            elif parent=="autotiles" and ending.endswith((".png",".bmp")):
                counts["autotiles"]+=1
            elif parent=="characters" and ending.endswith((".png",".bmp")):
                counts["characters"]+=1
            elif parent=="pbs" and ending.endswith(".txt"):
                counts["pbs_text"]+=1
            elif ending=="game.rxproj":
                counts["rpg_project"]+=1
    return dict(counts)

def inspect(source=None,credits=None,game_data=None,*,root=ROOT):
    source=Path(source).expanduser().absolute() if source is not None else None
    m=load_manifest(root)
    donor=audit_source(root=Path(root),source=source,game_data=game_data)
    credits_info=check_credits(credits)
    inventory=inspect_extra_zip(source)
    shape=donor["source"]
    if source is None:
        status="SOURCE_NOT_PROVIDED_IN_THIS_RUN"
    elif shape["empty_or_template_source"]:
        status="SOURCE_TOO_SMALL_OR_TEMPLATE_ONLY"
    elif credits_info is None:
        status="CREDITS_REQUIRED_FOR_REVIEW"
    else:
        status="CANDIDATE_FOR_DEEP_RXDATA_AUDIT_NOT_APPROVED"
    return {
        "schema":1,"region":"SINNOH","stage":"B00",
        "status":status,"source_provided":source is not None,
        "donor_map_count_all_regions":shape["map_count"] if shape else None,
        "donor_map_ids_all_regions":shape["source_map_ids"] if shape else None,
        "donor_zip_sha256":shape["sha256_zip"] if shape else None,
        "source_has_expected_rmxp_shape":bool(shape and shape["required_data_present"]),
        "additional_file_counts":inventory,"credits":credits_info,
        "native_game_data_available":donor["native"]["status"]=="LOCAL_READ_ONLY",
        "source_sinnoh_map_ids_identified":False,
        "rights_for_individual_assets_confirmed":False,
        "can_import_maps":False,"may_publish":False,
        "phase_b_completed":0,"phase_b_total":13,
        "game_or_saves_modified":False,
        "game_exe_tested":False,"joiplay_tested":False,
        "blockers":donor["blockers"]+
          (["Precisa de arquivo de créditos original"] if not credits_info else [])+
          ["Separar mapas Sinnoh dos demais mapas do ZIP usando auditoria profunda",
           "Verificar permissões de cada tileset, música, gráfico e NPC"]
    }

def main(argv=None):
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--source",type=Path,help="ZIP original do autor")
    cli.add_argument("--credits",type=Path,help="Credits.txt original")
    cli.add_argument("--game-data",type=Path,help="pasta game/Data privada, opcional")
    args=cli.parse_args(argv)
    try:
        print(json.dumps(inspect(args.source,args.credits,args.game_data),
                         indent=2,ensure_ascii=False))
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,
            zipfile.BadZipFile,zipfile.LargeZipFile) as e:
        print(str(e),file=sys.stderr);return 2
    return 0

if __name__=="__main__":raise SystemExit(main())
