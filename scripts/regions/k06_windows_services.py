"""Add Celadon's store and interiors to the official Windows installation."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from audit import KANTO, ROOT, inventory, json_file, load, text
from audit_k06_celadon_services import summarize
from build_k06_celadon_services import CANDIDATES, STORE, stage_services
from ensure_source import prepare
from install_kanto import recorded_hashes, verify_installed
from k06_approach_migration import INSTALL, checked_file, require_hashes, verify_native_graph
from scripts.android import source_update as journal
from scripts.android.update_client import safe_path

STAGE = "K06_CELADON_SERVICES"
FLAG = Path("data/regions/k06-services-release.json")
COMPILE = "Data/blue-compile-request.txt"
READY = "Data/blue-kanto-ready.txt"
RUNTIME = "Plugins/ZZZZZ Blue Kanto Pilot/KantoPilot.rb"
REGION = "Plugins/ZZZZ Blue Story and Presentation/RegionStart.rb"
RECEIPT = "Data/blue-kanto-k06-services.json"
EXPECTED_FLAG = {"schema":1,"stage":STAGE,"source_maps":list(CANDIDATES)}
REGISTRY = {"Data/MapInfos.rxdata","Data/Tilesets.rxdata"}
OWNED = {"PBS/map_metadata_kanto.txt","PBS/items_kanto.txt",RUNTIME}
BACKUP_K06 = "k06-approach"
BACKUP_SERVICES = "k06-services"


def activation_enabled(project):
    flag = project/FLAG
    if flag.is_symlink():
        raise ValueError("O catálogo de Celadon precisa ser um arquivo do projeto.")
    if not flag.exists():
        return False
    if json_file(flag) != EXPECTED_FLAG:
        raise ValueError("Catálogo de Celadon não corresponde aos quatro interiores verificados.")
    return True


def map_scope(base):
    if set(base) != json_file(KANTO)["maps"].keys() or len(set(base.values())) != 178:
        raise ValueError("O registro instalado deve preservar os 178 MapIDs publicados.")
    old = {f"Data/Map{base[str(sid)]:03}.rxdata" for sid in (114,*STORE)}
    new = {f"Data/Map{mid:03}.rxdata" for mid in CANDIDATES.values()}
    return old,new


def asset_paths(game, staged):
    paths = set()
    for folder,prefix in (("Tilesets","FRLG_Preview_"),("Autotiles","FRLG_Preview_"),
                          ("Characters","FRLG_Pilot_")):
        for asset in (staged/"Graphics"/folder).glob(prefix+"*.png"):
            rel = asset.relative_to(staged).as_posix()
            prior = journal.checked_row(game/rel)
            after = journal.checked_row(asset)
            if prior is None:
                paths.add(rel)
            elif after != prior:
                raise ValueError("O novo lote sobrescreveria um gráfico existente.")
    return paths


def registry_binding(game, extras, parent):
    """Bind new interiors to their native registry, not transient Marshal bytes.

    Essentials can rewrite the shared Tilesets container at regular boot.
    The updater appends to the exact prior container and proves that existing
    rows were preserved; later boots must preserve these four actual bindings.
    """
    infos, paths = inventory(game)
    tiles = load(checked_file(game,"Data/Tilesets.rxdata"))
    binding = {}
    for sid, mid in extras.items():
        info = infos[mid].attrs
        tile_id = load(paths[mid]).attrs["@tileset_id"]
        if not 0 < tile_id < len(tiles) or tiles[tile_id] is None or info["@parent_id"] != parent:
            raise ValueError("Registro nativo de tileset ou mapa de Celadon inválido.")
        tile = tiles[tile_id].attrs
        binding[sid] = {"map_id":mid,"title":text(info["@name"]),
                        "tile_id":tile_id,"sheet":text(tile["@tileset_name"]),
                        "autotiles":[text(raw) for raw in tile["@autotile_names"]]}
    return binding


def verify_services(game, proof=None):
    game = game.resolve()
    proof = proof or json_file(checked_file(game,INSTALL))
    mapping = proof.get("maps", {})
    extras = {str(sid):mid for sid,mid in CANDIDATES.items()}
    if (proof.get("schema") != 1 or proof.get("source") != "Essentials FRLG 21.1"
            or proof.get("content_stage") != STAGE
            or any(mapping.get(sid)!=mid for sid,mid in extras.items())):
        raise ValueError("Recibo final de instalação de Celadon inválido.")
    base = {sid:mid for sid,mid in mapping.items() if sid not in extras}
    map_scope(base)
    if len(set(mapping.values())) != 182:
        raise ValueError("Colisão de MapIDs no catálogo de Celadon.")
    details = json_file(checked_file(game,RECEIPT))
    if details.get("base_maps") != base or details.get("new_maps") != extras:
        raise ValueError("O recibo de Celadon não preserva o registro anterior.")
    infos,files = inventory(game)
    if not set(mapping.values()) <= (infos.keys()&files.keys()):
        raise ValueError("Mapas de Celadon ausentes no registro.")
    if registry_binding(game, extras, base["114"]) != details.get("native_registry"):
        raise ValueError("O motor mudou vínculos nativos dos quatro interiores de Celadon.")
    verify_native_graph(game,mapping={int(k):v for k,v in base.items()})
    if (checked_file(game,READY).read_text("ascii").strip()!=f"BLUE_KANTO_READY_V1,182,{base['7']}"
            or b"BlueKantoCeladonServices" not in checked_file(game,RUNTIME).read_bytes()):
        raise ValueError("Marcador nativo de Celadon não confere.")
    hashes = recorded_hashes(proof)
    expected = set(details["verified_paths"])
    owned_maps,added_maps = map_scope(base)
    if not (OWNED | owned_maps | added_maps | {REGION,READY}) <= expected or any(
            not safe_path(name) or name not in hashes for name in expected):
        raise ValueError("Escopo de verificação final inválido.")
    require_hashes(game, expected-REGISTRY, hashes)
    return {"maps":182,"stage":STAGE,"kanto_start":[base["7"],25,7]}


def recover(game, backup_home):
    if not (game/journal.RECOVERY_FILE).exists():
        return
    with journal.update_lock(game):
        data = journal.recovery_plan(game,record_marker=INSTALL)
        if data is not None:
            lane = data.get("baseline")
            if lane not in {"windows-k05", "windows-k06-approach"}:
                raise ValueError("Recibo de recuperação não pertence ao instalador de Kanto.")
            backup = BACKUP_K06 if lane=="windows-k05" else BACKUP_SERVICES
            journal.recover_under_lock(game,backup_home/backup,data,record_marker=INSTALL)


def install(game):
    game = game.resolve()
    if os.name!="nt" or game!=(ROOT/"game").resolve() or not activation_enabled(ROOT):
        raise ValueError("Instalação de Celadon não habilitada nesta pasta gerenciada.")
    backup_home = ROOT/".blue-backups"
    backup_home.mkdir(exist_ok=True)
    recover(game,backup_home)
    before = checked_file(game,INSTALL).read_bytes()
    proof = json.loads(before)
    if proof.get("content_stage")==STAGE:
        verify_services(game,proof)
        print("KANTO_K06_WINDOWS_CELADON_CURRENT_OK",flush=True)
        return False
    if proof.get("content_stage")!="K06_APPROACH" or verify_installed(game)["maps"]!=178:
        raise ValueError("Instale a passagem de Celadon antes da loja.")
    old_maps,new_maps = map_scope(proof["maps"])
    old_hash = recorded_hashes(proof)
    require_hashes(game, old_maps|OWNED, old_hash)
    prior_registry = {rel:journal.checked_row(game/rel) for rel in REGISTRY}
    if None in prior_registry.values():
        raise ValueError("Registro nativo principal ausente.")
    source = prepare()
    with tempfile.TemporaryDirectory(prefix="k06-services-",dir=ROOT/".blue-work") as work:
        stage = Path(work).resolve()/"game"
        witness = stage_services(source,game,stage,summarize(source,json_file(KANTO)),windows_product=True)
        (stage/REGION).write_bytes((ROOT/"scripts/battle_polish/RegionStart.rb").read_bytes())
        paths = old_maps|new_maps|OWNED|REGISTRY|asset_paths(game,stage)|{REGION,READY}
        details = {"schema":1,"stage":STAGE,"base_maps":proof["maps"],
                   "new_maps":{str(k):v for k,v in CANDIDATES.items()},"verified_paths":sorted(paths),
                   "unchanged_old_map_count":witness["unrelated_maps_byte_identical"]}
        details["native_registry"] = registry_binding(stage, details["new_maps"], proof["maps"]["114"])
        (stage/RECEIPT).write_text(json.dumps(details,sort_keys=True)+"\n",encoding="utf8")
        (stage/COMPILE).write_bytes(b"compile")
        if any(not safe_path(name) for name in paths):
            raise ValueError("Caminho fora do inventário de Celadon.")
        stamp = json_file(stage/INSTALL)
        stamp["content_stage"] = STAGE
        new_rows = {name:journal.manifest_row(checked_file(stage,name)) for name in paths}
        updated_hashes = {**old_hash, **{name:row["sha256"] for name,row in new_rows.items()}}
        stamp["installed_sha256"] = updated_hashes
        changes,bases = {},{}
        for rel in sorted(paths|{COMPILE,RECEIPT}):
            row = new_rows.get(rel) or journal.manifest_row(checked_file(stage,rel))
            old = journal.checked_row(game/rel)
            if rel in old_maps|OWNED and (old is None or old["sha256"] != old_hash[rel]):
                raise ValueError("O registro anterior mudou durante a montagem.")
            if rel in REGISTRY and old!=prior_registry[rel]:
                raise ValueError("O registro nativo mudou durante a montagem.")
            if rel in new_maps|{RECEIPT} and old is not None:
                raise ValueError("Celadon não sobrescreve mapas ou recibos desconhecidos.")
            if row!=old:
                changes[rel],bases[rel] = row,old
        journal.commit_local(game,stage,changes,json.dumps(stamp,sort_keys=True).encode("utf8"),
            backup_home/BACKUP_SERVICES,verify=lambda path:verify_services(path,stamp),
            before_marker=before,baseline="windows-k06-approach",record_marker=INSTALL,before_files=bases)
    print("KANTO_K06_WINDOWS_CELADON_OVERLAY_OK",flush=True)
    return True


if __name__=="__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",required=True,type=Path)
    p.add_argument("--verify",action="store_true")
    a = p.parse_args()
    if a.verify:
        print(json.dumps(verify_services(a.game)))
    else:
        install(a.game)
