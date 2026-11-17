#!/usr/bin/env python3
"""SP05 — isolated, NON-INSTALLABLE Cheren visual QA fixture.

A private staging area, NEVER game/Data, Graphics/Characters, Blue-Story or
saves. Rights documents are fingerprinted, NOT authenticated by this tool.
No sprite can be staged without actual ZIP/SP03/SP04, 4x4 PNG, local rights
evidence and a real Decades sprite to compare visible pixel sizes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import zlib
import zipfile
from pathlib import Path
from statistics import median
from urllib.parse import urlparse

import audit_unova_sprite_pack as sprite
import audit_unova_sp04_npcs as npc

ROOT = Path(__file__).resolve().parents[2]
POLICY = Path("data/regions/unova-sp05-cheren-pilot.json")
QA = Path(".blue-work/unova/qa/sp05-cheren")
MAX_IMAGE = 8 * 1024 * 1024
MAX_RIGHTS_DOC = 128 * 1024
SHA = re.compile(r"[0-9a-f]{64}\Z")
DEST = "Graphics/Characters/UNOVA_NPC_CHEREN.png"
FIELDS_FALSE = (
    "source_sprite_selected", "source_rights_verified", "visual_review_complete",
    "game_exe_tested", "android_tested", "map_id_verified",
    "changes_existing_game", "can_install",
)


def fail(message: str) -> None:
    raise ValueError("UNOVA_SP05_BLOQUEADO: " + message)


def file_bytes(path: Path, maximum: int = MAX_IMAGE) -> bytes:
    path = Path(path).absolute()
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        fail("arquivo ausente, symlink, vazio ou maior que limite: " + str(path))
    return path.read_bytes()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_policy(project: Path) -> dict:
    root = Path(project).absolute()
    policy = npc.read_json(root / POLICY, limit=100_000)
    expected = {
        "schema": 1, "region": "UNOVA", "phase": "SP05",
        "status": "PLANNED_PRIVATE_QA_ONLY",
        "npc_key": "UNOVA_NPC_CHEREN",
        "story_scope": "WHITE_BW",
        "planned_area_key": "UNOVA_NUVEMA_TOWN",
        "destination_relative": DEST,
    }
    for key, value in expected.items():
        if policy.get(key) != value:
            fail("manifesto SP05 foi alterado: " + key)
    for key in FIELDS_FALSE:
        if policy.get(key) is not False:
            fail("manifesto SP05 aprovou algo sem QA: " + key)
    image = policy.get("image_requirements", {})
    if (image.get("format") != "PNG_RGBA8_NONINTERLACED"
        or image.get("columns") != 4
        or image.get("frames_per_direction") != 4
        or image.get("direction_rows") != ["down","left","right","up"]
        or image.get("require_all_16_visible") is not True):
        fail("exigencia de grade/direcao alterada")
    rights = policy.get("rights_policy", {})
    if (rights.get("local_evidence_file_required_for_staging") is not True or
        rights.get("rights_document_authenticity_not_auto_verified") is not True or
        rights.get("redistribution_permission_not_inferred") is not True or
        rights.get("public_distribution_allowed") is not False):
        fail("politica de direitos alterada")
    scale = policy.get("scale_policy", {})
    if (scale.get("baseline_required") is not True or
        scale.get("visual_signoff_required") is not True or
        scale.get("min_visible_height_ratio") != 0.8 or
        scale.get("max_visible_height_ratio") != 1.2 or
        scale.get("min_visible_width_ratio") != 0.8 or
        scale.get("max_visible_width_ratio") != 1.25):
        fail("limites ou revisao de escala alterados")
    return policy


def plan(project: Path) -> dict:
    policy = load_policy(project)
    # Revalidate the currently planned roster & regional status before any QA.
    catalog = npc.read_json(Path(project)/"data/regions/unova-sp04-npcs.json")
    areas = npc.read_json(Path(project)/"data/regions/unova-u03-areas.json")
    trainers = npc.read_json(Path(project)/"data/regions/unova-e06-e07-preparation.json")
    regions = npc.read_json(Path(project)/"site/public/data/regions.json")
    chars = npc.validate_catalog(catalog, areas, trainers, regions)
    found = [r for r in chars if r["key"] == "UNOVA_NPC_CHEREN"]
    if len(found) != 1 or found[0]["primary_area_key"] != policy["planned_area_key"]:
        fail("Cheren SP04 ausente ou referencia de area divergente")
    return {
        "schema": 1,"region": "UNOVA","phase": "SP05",
        "mode": "PRIVATE_QA_FIXTURE_PLAN_ONLY",
        "status": "BLOCKED_MISSING_AUTHOR_SOURCE_AND_NATIVE_QA",
        "npc_key": "UNOVA_NPC_CHEREN",
        "reserved_character_filename": "UNOVA_NPC_CHEREN.png",
        "reserved_relative_path": DEST,
        "reference_area_key": "UNOVA_NUVEMA_TOWN",
        "source_zip_obtained": False,
        "sprite_selected": False,
        "rights_evidence_authenticated": False,
        "four_direction_order_visually_confirmed": False,
        "scale_visually_approved": False,
        "game_exe_tested": False, "android_tested": False,
        "game_or_saves_modified": False, "can_install": False,
        "blockers": [
            "ZIP de sprite do autor e relatórios SP03/SP04 correspondentes não fornecidos",
            "Comprovante escrito de uso/local QA e autoria não verificados",
            "Sprite de referência real do Decades não fornecido para medir escala",
            "Ordem de direções e animações ainda requerem inspeção visual",
            "Game.exe e JoiPlay ainda não foram testados",
            "Eventos/mapas e licença de redistribuição não estão aprovados",
        ],
    }


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    distances = (abs(p-a),abs(p-b),abs(p-c))
    return (a,b,c)[distances.index(min(distances))]


def rgba_pixels(blob: bytes) -> tuple[int,int,bytes]:
    meta = sprite.inspect_png(blob)
    if meta["format"] != "PNG" or meta["animation_frames_declared"] != 1:
        fail("piloto exige PNG estático; não GIF/APNG")
    if len(blob) > MAX_IMAGE:
        fail("sprite acima do limite")
    size = struct.unpack_from(">I",blob,8)[0]
    ihdr=blob[16:16+size]
    w,h,depth,color,compression,filtering,interlace=struct.unpack(">IIBBBBB",ihdr)
    if (depth,color,compression,filtering,interlace)!=(8,6,0,0,0):
        fail("piloto exige RGBA8 sem interlace (não converter fonte automaticamente)")
    if (w%4 or h%4 or w<64 or h<64 or w>1024 or h>1024):
        fail("grade precisa ser exatamente 4x4 com celulas razoaveis")
    cursor=8
    compressed=[]
    found_idat=False
    while cursor+12<=len(blob):
        count=struct.unpack_from(">I",blob,cursor)[0]
        name=blob[cursor+4:cursor+8]
        data=blob[cursor+8:cursor+8+count]
        if name==b"IDAT":
            compressed.append(data)
            found_idat=True
        cursor+=count+12
        if name==b"IEND":
            break
    if not found_idat:
        fail("PNG sem IDAT")
    stride=w*4
    expected=(stride+1)*h
    if expected>5*1024*1024:
        fail("imagem RGBA decodificada excessiva")
    decoder=zlib.decompressobj()
    raw=decoder.decompress(b"".join(compressed),expected+1)
    raw+=decoder.flush()
    if (len(raw)!=expected or not decoder.eof or decoder.unused_data or
            decoder.unconsumed_tail):
        fail("dados PNG incompletos, comprimidos excessivos ou adicionais")
    previous=bytearray(stride)
    result=bytearray(stride*h)
    for row in range(h):
        marker=raw[row*(stride+1)]
        if marker not in range(5):
            fail("filtro PNG inválido")
        current=bytearray(raw[row*(stride+1)+1:(row+1)*(stride+1)])
        for x in range(stride):
            a=current[x-4] if x>=4 else 0
            b=previous[x]
            c=previous[x-4] if x>=4 else 0
            if marker==1:
                current[x]=(current[x]+a)&255
            elif marker==2:
                current[x]=(current[x]+b)&255
            elif marker==3:
                current[x]=(current[x]+((a+b)//2))&255
            elif marker==4:
                current[x]=(current[x]+paeth(a,b,c))&255
        result[row*stride:(row+1)*stride]=current
        previous=current
    return w,h,bytes(result)


def measure_sheet(blob: bytes) -> dict:
    w,h,pixels=rgba_pixels(blob)
    cw,ch=w//4,h//4
    frames=[]
    row_stats=[]
    for direction, label in enumerate(("down","left","right","up")):
        for frame in range(4):
            xs=[]
            ys=[]
            for yy in range(ch):
                y=direction*ch+yy
                for xx in range(cw):
                    x=frame*cw+xx
                    alpha=pixels[(y*w+x)*4+3]
                    if alpha>0:
                        xs.append(xx)
                        ys.append(yy)
            if not xs:
                fail("quadro invisível: "+label+"/"+str(frame))
            frame_data={
                "direction_row_assumed":label, "column":frame,
                "occupied_width":max(xs)-min(xs)+1,
                "occupied_height":max(ys)-min(ys)+1,
                "foot_y_in_cell":max(ys),
                "opaque_or_semtransparent_pixel_count":len(xs),
            }
            frames.append(frame_data)
        row_frames=frames[-4:]
        row_stats.append({
            "direction_row_assumed":label,
            "visible_height_median":median(f["occupied_height"] for f in row_frames),
            "foot_y_median":median(f["foot_y_in_cell"] for f in row_frames),
        })
    return {
        "sheet_width":w,"sheet_height":h,"columns":4,"direction_rows":4,
        "cell_width":cw,"cell_height":ch,
        "frame_count":16,
        "frame_metrics":frames,
        "direction_row_metrics":row_stats,
        "visible_height_median":median(f["occupied_height"] for f in frames),
        "visible_width_median":median(f["occupied_width"] for f in frames),
        "direction_order_verified":False,
        "animation_in_game_verified":False,
        "visual_identity_verified":False,
    }


def verify_sp04(project: Path, sp03_path: Path, sp04_path: Path,
                source_zip_hash: str, member: str, image_hash: str) -> tuple[dict,dict]:
    sp03=npc.read_sp03(project,sp03_path)
    if sp03["archive_sha256"]!=source_zip_hash:
        fail("hash ZIP original diverge do relatorio SP03")
    expected_sp04_path=project/npc.SP04_DIR/("npc-sp04-"+source_zip_hash[:16]+".json")
    sp04_path=Path(sp04_path).absolute()
    if sp04_path!=expected_sp04_path:
        fail("SP04 fora da pasta privada ou hash diferente")
    for part in (project/".blue-work",project/".blue-work/unova",
                 project/".blue-work/unova/audit",project/npc.SP04_DIR,sp04_path):
        if part.is_symlink():
            fail("SP04 via symlink")
    sp04=npc.read_json(sp04_path)
    catalog=npc.read_json(project/"data/regions/unova-sp04-npcs.json")
    areas=npc.read_json(project/"data/regions/unova-u03-areas.json")
    trainers=npc.read_json(project/"data/regions/unova-e06-e07-preparation.json")
    regions=npc.read_json(project/"site/public/data/regions.json")
    expected=npc.merge(catalog,areas,trainers,regions,sp03)
    if sp04!=expected:
        fail("SP04 local alterado; refazer a partir do auditor original")
    cheren=[r for r in sp04["npcs"] if r["npc_key"]=="UNOVA_NPC_CHEREN"]
    if len(cheren)!=1:
        fail("Cheren ausente do SP04")
    matching=[row for row in cheren[0]["sprite_candidates"]
              if row["source_path_candidate"]==member and
              row["source_sha256_candidate"]==image_hash]
    if len(matching)!=1:
        fail("imagem escolhida não aparece como candidata única para Cheren")
    return sp03, matching[0]


def private_stage_dir(project: Path, image_hash: str) -> Path:
    project=project.absolute()
    dest=project/QA/image_hash[:16]
    names=(project,project/".blue-work",project/".blue-work/unova",
           project/".blue-work/unova/qa",project/QA,dest)
    for name in names:
        if name.is_symlink() or (name.exists() and not name.is_dir()):
            fail("pasta de QA é symlink, arquivo ou não permitida")
    for name in names[1:]:
        name.mkdir(exist_ok=True)
    return dest


def write_immutable(path: Path, data: bytes) -> None:
    if path.is_symlink():
        fail("alvo QA é symlink")
    if path.exists():
        if not path.is_file() or path.read_bytes()!=data:
            fail("alvo já existe com outro conteúdo; nunca sobrescrever QA")
    else:
        with path.open("xb") as stream:
            stream.write(data)


def stage(args) -> dict:
    project=Path(args.project).absolute()
    plan(project)
    required=("zip","member","sp03","sp04","reference_sprite","rights_evidence","rights_holder","source_url")
    for key in required:
        if getattr(args,key,None) in (None,""):
            fail("staging privado exige --"+key.replace("_","-"))
    zip_path=Path(args.zip).absolute()
    if zip_path.is_symlink() or not zip_path.is_file() or zip_path.suffix.lower()!=".zip":
        fail("ZIP fonte ausente/inseguro")
    if not str(args.member).lower().endswith(".png"):
        fail("piloto exige um arquivo PNG")
    sprite.safe_zip_parts(args.member)
    src_report=sprite.audit(zip_path)
    if src_report["status"]!="SPRITES_AUDITED_NOT_LICENSED_OR_INSTALLED":
        fail("ZIP inclui imagens inválidas ou foi reprovado no SP03")
    archive_hash=src_report["archive_sha256"]
    rows=[x for x in src_report["images"] if x["path"]==args.member]
    if len(rows)!=1:
        fail("sprite não encontrado ou não único no ZIP")
    with zipfile.ZipFile(zip_path) as z:
        info=z.getinfo(args.member)
        if not 0<info.file_size<=MAX_IMAGE:
            fail("PNG maior que limite")
        with z.open(info) as f:
            sprite_bytes=f.read(MAX_IMAGE+1)
        if len(sprite_bytes)!=info.file_size:
            fail("tamanho da entrada ZIP inesperado")
    image_hash=digest(sprite_bytes)
    if rows[0]["sha256"]!=image_hash:
        fail("imagem não confere com auditoria SP03")
    sp03, candidate=verify_sp04(project,Path(args.sp03),Path(args.sp04),
                                archive_hash,args.member,image_hash)
    reference_path=Path(args.reference_sprite).absolute()
    if reference_path.suffix.lower()!=".png":
        fail("referência Decades para QA deve ser PNG")
    reference_bytes=file_bytes(reference_path)
    rights_path=Path(args.rights_evidence).absolute()
    rights_bytes=file_bytes(rights_path,MAX_RIGHTS_DOC)
    if len(rights_bytes)<20 or b"\x00" in rights_bytes[:256]:
        fail("evidência de direitos ausente, binária ou insuficiente")
    holder=str(args.rights_holder).strip()
    if not 2<=len(holder)<=150:
        fail("autor/representante não informado")
    url=urlparse(str(args.source_url))
    if url.scheme!="https" or not url.netloc or url.username or url.password:
        fail("URL de proveniência deve ser HTTPS sem credenciais")
    own=measure_sheet(sprite_bytes)
    reference=measure_sheet(reference_bytes)
    ratio_h=own["visible_height_median"]/reference["visible_height_median"]
    ratio_w=own["visible_width_median"]/reference["visible_width_median"]
    if not 0.8<=ratio_h<=1.2:
        fail("altura visível incompatível com Decades (proporção "+format(ratio_h,".3f")+")")
    if not 0.8<=ratio_w<=1.25:
        fail("largura visível incompatível com Decades (proporção "+format(ratio_w,".3f")+")")
    output={
        "schema":1,"region":"UNOVA","phase":"SP05",
        "mode":"PRIVATE_SPRITE_QA_ONLY_NOT_GAME_INSTALLATION",
        "status":"LOCAL_QA_ASSET_STAGED_PENDING_MANUAL_SIGNOFF",
        "npc_key":"UNOVA_NPC_CHEREN","planned_area_key":"UNOVA_NUVEMA_TOWN",
        "original_zip_sha256":archive_hash,
        "selected_zip_member":args.member,"selected_image_sha256":image_hash,
        "sp03_zip_hash_matched":True,"sp04_candidate_hash_matched":True,
        "staged_relative_path":DEST,
        "sprite_metrics":own,
        "reference_sprite_sha256":digest(reference_bytes),
        "reference_metrics":{k:v for k,v in reference.items() if k!="frame_metrics"},
        "visible_height_ratio":round(ratio_h,3),
        "visible_width_ratio":round(ratio_w,3),
        "rights_holder_declared":holder,"source_url_declared":str(args.source_url),
        "rights_evidence_sha256":digest(rights_bytes),
        "rights_evidence_present_not_authenticated":True,
        "rights_verified":False,"redistribution_approved":False,
        "directions_visually_verified":False,
        "animation_in_game_verified":False,
        "native_scale_verified":False,
        "map_id_assigned":False,"npc_event_installed":False,
        "game_exe_tested":False,"android_tested":False,
        "game_or_saves_modified":False,"can_install":False,
        "next_action":"Inspecionar 4x4 com pessoa responsável, confirmar licença/identidade, depois testar em cópia Game.exe/JoiPlay; nunca copiar diretamente ao Decades principal.",
    }
    qa=private_stage_dir(project,image_hash)
    image=qa/DEST
    folder=image.parent
    for part in (qa/"Graphics",folder):
        if part.is_symlink() or (part.exists() and not part.is_dir()):
            fail("pasta de sprite em QA insegura")
        part.mkdir(exist_ok=True)
    manifest=qa/"sp05-cheren-qa.json"
    if manifest.is_symlink():
        fail("manifesto QA symlink")
    payload=json.dumps(output,ensure_ascii=False,indent=2).encode("utf-8")+b"\n"
    if manifest.exists() and manifest.read_bytes()!=payload:
        fail("manifesto prévio divergente: não substituir")
    if image.exists() and image.read_bytes()!=sprite_bytes:
        fail("sprite QA anterior divergente: não substituir")
    write_immutable(image,sprite_bytes)
    write_immutable(manifest,payload)
    output["private_qa_directory"]=str(qa.relative_to(project)).replace("\\","/")
    return output



def choose_gui(project: Path):
    """Windows file pickers; the ordinary CLI remains available for tests."""
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, simpledialog
        root=tk.Tk()
        root.withdraw()
        messagebox.showinfo("Cheren SP05 - apenas QA privado",
            "Selecione um ZIP de sprites já auditado no SP03 e um relatório SP04.\n"
            "São necessários uma referência do Decades e documento de permissão.\n"
            "Nenhum arquivo será instalado no Game.exe nem no Blue-Story.",
            parent=root)
        zip_path=filedialog.askopenfilename(parent=root,title="ZIP original com sprite de Cheren",
                   filetypes=[("ZIP de sprites","*.zip")])
        if not zip_path:
            root.destroy()
            return None
        sp03_path=filedialog.askopenfilename(parent=root,title="Relatório privado SP03: sprites-....json",
                  initialdir=str(project/npc.SP03_DIR),
                  filetypes=[("Relatório JSON","*.json")])
        if not sp03_path:
            root.destroy()
            return None
        sp04_path=filedialog.askopenfilename(parent=root,title="Relatório privado SP04: npc-sp04-....json",
                  initialdir=str(project/npc.SP04_DIR),
                  filetypes=[("Relatório JSON","*.json")])
        if not sp04_path:
            root.destroy()
            return None
        sp04_report=npc.read_json(Path(sp04_path))
        cheren=[row for row in sp04_report.get("npcs",[])
                if isinstance(row,dict) and row.get("npc_key")=="UNOVA_NPC_CHEREN"]
        candidates=cheren[0].get("sprite_candidates",[]) if len(cheren)==1 else []
        if not candidates:
            messagebox.showerror("Cheren sem candidatos",
                "SP04 ainda não encontrou um sprite candidato para Cheren neste pack.",
                parent=root)
            root.destroy()
            return None
        menu="\n".join(str(i+1)+" - "+x["source_path_candidate"]
                        for i,x in enumerate(candidates[:30]))
        selection=simpledialog.askinteger("Selecionar Cheren",
                "Escolha um candidato (requer verificação visual posterior):\n"+menu,
                minvalue=1,maxvalue=min(len(candidates),30),parent=root)
        if selection is None:
            root.destroy()
            return None
        member=candidates[selection-1]["source_path_candidate"]
        baseline=filedialog.askopenfilename(parent=root,
                title="Sprite PNG de referência: Decades/Graphics/Characters",
                filetypes=[("PNG de personagem","*.png")])
        if not baseline:
            root.destroy()
            return None
        proof=filedialog.askopenfilename(parent=root,
                title="Documento local de permissão/autoria (não verificado automaticamente)",
                filetypes=[("Comprovante TXT ou PDF","*.txt *.pdf"),("Todos os arquivos","*.*")])
        if not proof:
            root.destroy()
            return None
        holder=simpledialog.askstring("Autor dos recursos",
                "Informe o nome do autor indicado no comprovante:",parent=root)
        if not holder:
            root.destroy()
            return None
        url=simpledialog.askstring("URL de origem",
                "Informe URL HTTPS da publicação original do autor:",
                initialvalue="https://eeveeexpo.com/resources/25/",parent=root)
        root.destroy()
        if not url:
            return None
        return {
            "zip":Path(zip_path),"sp03":Path(sp03_path),
            "sp04":Path(sp04_path),"member":member,
            "reference_sprite":Path(baseline),"rights_evidence":Path(proof),
            "rights_holder":holder,"source_url":url,
        }
    except (ImportError,RuntimeError,OSError) as exc:
        fail("seletor grafico indisponível: "+str(exc))



def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--stage",action="store_true",
                        help="staging somente em .blue-work/unova/qa, nunca no jogo")
    parser.add_argument("--gui",action="store_true",
                        help="selecionar por janelas do Windows todos os insumos de QA")
    parser.add_argument("--zip",type=Path)
    parser.add_argument("--member",type=str)
    parser.add_argument("--sp03",type=Path)
    parser.add_argument("--sp04",type=Path)
    parser.add_argument("--reference-sprite",type=Path)
    parser.add_argument("--rights-evidence",type=Path)
    parser.add_argument("--rights-holder",type=str)
    parser.add_argument("--source-url",type=str)
    args=parser.parse_args(argv)
    try:
        if args.gui:
            if args.stage:
                fail("use apenas --gui para a seleção interativa")
            options=choose_gui(Path(args.project).absolute())
            if options is None:
                print("UNOVA_SP05_CANCELADO: nenhum arquivo do jogo alterado")
                return 2
            for name,value in options.items():
                setattr(args,name,value)
            args.stage=True
        result=stage(args) if args.stage else plan(args.project)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (ValueError,OSError,TypeError,KeyError,zipfile.BadZipFile,
            zipfile.LargeZipFile,NotImplementedError,zlib.error) as exc:
        print("UNOVA_SP05_BLOQUEADO: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
