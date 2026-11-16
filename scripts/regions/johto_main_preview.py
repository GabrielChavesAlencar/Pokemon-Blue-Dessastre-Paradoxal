"""Local PRIVATE Johto preview installer for the shared Decades game.

Unlike a final 13-gate Johto release, this is a visibly experimental
New Bark/Violet build. Only user-owned, pinned OFFLINE12 bytes are accepted;
licensed graphics/audio are NOT shipped from GitHub. Kanto, Hoenn, saves,
game launcher settings and existing maps are never overwritten.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/regions"))

import johto_qa
import johto_hgss_assets as hgss
import johto_map_patches as map_patches
import johto_visual as visual
from johto_opening import repair_opening
from sinnoh_map_id_guard import assert_johto_shared_overlay_map_ids
from server.ruby_marshal import RubyObject, loads, text
from stage import serialize

PINNED_SHA = johto_qa.ORIGINAL_BUNDLE_SHA256
STAGED_IDS = frozenset(range(600, 682))
PREVIEW_IDS = frozenset(range(600, 700))  # 700+ belongs to Hoenn!
PROOF = "Data/blue-johto-main-preview.json"
READY = "Data/blue-johto-preview-ready.txt"
PLUGIN = "Plugins/ZZZZZ Blue Johto Main"
STATUS = "EXPERIMENTAL_PRIVATE_UNVERIFIED"
START = (674, 6, 7)
TOWN = (600, 10, 26, 2)
NPC = (600, 10, 25, 2)
RUNTIME = ("JohtoPilot.rb", "JohtoRouteTrainers.rb", "JohtoViolet.rb", "JohtoMainCompile.rb")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def raw_json(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def local_target(game: Path, name: str) -> Path:
    if not name or "\\" in name or name.startswith("/") or ".." in Path(name).parts:
        raise ValueError("Caminho interno inválido: " + name)
    path = game / name
    johto_qa.safe_path(path)
    if not path.resolve().is_relative_to(game.resolve()):
        raise ValueError("Destino de Johto fora de game/")
    return path


def assert_spawn_not_blocked(map_obj) -> None:
    """Allow only the audited invisible autorun at the player's start tile."""
    overlapping = [event for event in map_obj.attrs["@events"].values()
                   if (event.attrs["@x"], event.attrs["@y"]) == START[1:]]
    expected = [
        e for e in overlapping
        if text(e.attrs["@name"]) == "JH_NEW_GAME_PROFILE"
        and e.attrs["@pages"]
        and e.attrs["@pages"][0].attrs.get("@trigger") == 3
        and not e.attrs["@pages"][0].attrs["@graphic"].attrs.get("@character_name")
    ]
    if len(overlapping) != len(expected) or len(expected) > 1:
        raise ValueError("Spawn do jogador bloqueado por NPC/obstáculo inesperado")


def preview_proof(game: Path) -> dict | None:
    manifest = game / PROOF
    if not manifest.is_file() or manifest.is_symlink():
        return None
    data = json.loads(manifest.read_text("utf-8"))
    if (data.get("schema") != 1 or data.get("region") != "JOHTO"
            or data.get("status") != STATUS or data.get("source_bundle_sha256") != PINNED_SHA
            or data.get("map_ids") != sorted(PREVIEW_IDS)
            or data.get("start") != list(START) or data.get("town") != list(TOWN)
            or data.get("npc") != list(NPC)):
        raise ValueError("Instalação experimental de Johto possui manifesto inválido")
    marker = game / READY
    expected = ("BLUE_JOHTO_PRIVATE_PREVIEW_V1,100," +
                ",".join(map(str, (*START, *TOWN[:3], *NPC[:3]))))
    if not marker.is_file() or marker.is_symlink() or marker.read_text("ascii").strip() != expected:
        raise ValueError("Marcador de Johto experimental ausente ou incompatível")
    hashes = data.get("file_hashes")
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("Johto experimental não possui inventário de arquivos")
    if not all(f"Data/Map{i:03}.rxdata" in hashes for i in PREVIEW_IDS):
        raise ValueError("Mapas de Johto não estão no inventário da instalação")
    for name, recorded in hashes.items():
        file = local_target(game, name)
        if not re.fullmatch("[a-f0-9]{64}", str(recorded)) or not file.is_file() or file.is_symlink():
            raise ValueError("Arquivo da instalação Johto ausente: " + name)
        if johto_qa.checksum(file) != recorded:
            raise ValueError("Arquivo de Johto alterado após instalação: " + name)
    for path in ("PBS/map_connections.txt", f"{PLUGIN}/Boot.rb",
                 "PBS/map_metadata_johto_main.txt", "Data/MapInfos.rxdata",
                 "Data/Tilesets.rxdata"):
        if not (game / path).is_file():
            raise ValueError("Dependência de Johto ausente: " + path)
    return data


def refresh_installed_runtime(game: Path, root: Path = ROOT) -> dict:
    """Repair an already installed preview's Ruby plugin, never its maps/saves.

    The original Boot.rb prepended Compiler.main; other Blue plugins alias
    Compiler.main and create a recursive super/alias cycle on startup. A source
    update alone cannot repair the copied game/Plugins script. This performs
    a hash-verified, backed-up, two-file plugin+manifest update in place.
    """
    game, root = Path(game).resolve(), Path(root).resolve()
    installed = preview_proof(game)
    if installed is None:
        return {"changed": False, "reason": "Johto não instalada"}
    plugin_name = f"{PLUGIN}/Boot.rb"
    manifest_name = PROOF
    old = local_target(game, plugin_name)
    manifest = local_target(game, manifest_name)
    if not old.is_file() or old.is_symlink() or manifest.is_symlink():
        raise ValueError("Plugin/manifesto Johto existente não é arquivo regular")
    expected_old_hash = installed["file_hashes"].get(plugin_name)
    if sha(old.read_bytes()) != expected_old_hash:
        raise ValueError("Plugin Johto modificado manualmente; hotfix automático recusado")

    source_files = [root / "scripts/regions" / name for name in RUNTIME]
    for path in source_files:
        johto_qa.regular(path)
    replacement = b"\n".join(path.read_bytes() for path in source_files)
    if (b"Compiler.singleton_class.prepend(" in replacement or
            b"module CompilerHook" in replacement):
        raise ValueError("Novo plugin Johto ainda contém o hook recursivo de Compiler.main")
    if replacement == old.read_bytes():
        return {"changed": False, "reason": "Plugin Ruby Johto já atualizado"}

    changed_manifest = copy.deepcopy(installed)
    changed_manifest["file_hashes"][plugin_name] = sha(replacement)
    changed_manifest["runtime_hotfix"] = "johto-compiler-no-prepend-v2"
    updated_json = raw_json(changed_manifest)
    backups = root / ".blue-backups" / ("johto-boot-hotfix-" + uuid.uuid4().hex)
    backups.mkdir(parents=True)
    for relative in (plugin_name, manifest_name):
        target = local_target(game, relative)
        backup = backups / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
    written = []
    try:
        for target, contents in ((old, replacement), (manifest, updated_json)):
            pending = target.with_name(target.name + ".blue-hotfix-tmp")
            if pending.exists() or pending.is_symlink():
                raise ValueError("Arquivo temporário de correção Johto já existe")
            try:
                pending.write_bytes(contents)
                if sha(pending.read_bytes()) != sha(contents):
                    raise ValueError("Falha ao verificar gravação do hotfix Johto")
                os.replace(pending, target)
                written.append(target)
            finally:
                pending.unlink(missing_ok=True)
        preview_proof(game)
        return {"changed": True, "reason": "Plugin Johto corrigido sem tocar mapas ou saves",
                "backup_folder": str(backups), "runtime_hotfix": "compiler-no-prepend-v2"}
    except BaseException:
        for target in reversed(written):
            relative = target.relative_to(game)
            shutil.copy2(backups / relative, target)
        raise




# Exact SHA-256 bytes of the USER-SUPPLIED 16-Nov Johto diagnostic package.
# The in-game writer added door sounds/fades and other New Bark events after
# installation. This pair can be MIGRATED once; it is not an unrestricted
# bypass for changed maps or a claim that all of Johto passed native QA.
AUDITED_LIVE_BEDROOM_SHA = {
    "Data/Map674.rxdata": "8d837d343087eec13927e601ff3d506c1cb3bbaae696c90211b91111814e12b7",
    "Data/Map675.rxdata": "71fa3e6c22a87f6dd2f4ddab0538f9f33586e5cc979a9891b24f9d259e9469c3",
}


def scoped_bedroom_proof(game: Path, *, accept_audited_live_maps: bool = False,
                         allow_changed_map_bytes: bool = False) -> dict | None:
    """Validate only the two original Johto maps for explicit manual repair.

    Other plug-ins/regions can legitimately change shared PBS or MapInfos after
    Johto installation. This is deliberately NOT a Johto release or ready proof.
    It must never make the global preview pass when shared artifacts drift.
    """
    game = Path(game).resolve()
    manifest = local_target(game, PROOF)
    if not manifest.is_file() or manifest.is_symlink():
        return None
    data = json.loads(manifest.read_text("utf-8"))
    if (data.get("schema") != 1 or data.get("region") != "JOHTO"
            or data.get("status") != STATUS
            or data.get("source_bundle_sha256") != PINNED_SHA
            or data.get("map_ids") != sorted(PREVIEW_IDS)
            or data.get("start") != list(START)
            or data.get("town") != list(TOWN) or data.get("npc") != list(NPC)):
        raise ValueError("Johto: manifesto incompatível para reparo isolado")
    marker = local_target(game, READY)
    expected = "BLUE_JOHTO_PRIVATE_PREVIEW_V1,100," + ",".join(
        map(str, (*START, *TOWN[:3], *NPC[:3])))
    if (not marker.is_file() or marker.is_symlink()
            or marker.read_text("ascii").strip() != expected):
        raise ValueError("Johto: marcador de instalação privada não corresponde ao pacote original")
    hashes = data.get("file_hashes")
    if not isinstance(hashes, dict):
        raise ValueError("Johto: hashes ausentes")
    for name in ("Data/Map674.rxdata", "Data/Map675.rxdata"):
        path = local_target(game, name)
        value = hashes.get(name)
        if (not isinstance(value, str) or not re.fullmatch("[a-f0-9]{64}", value)
                or not path.is_file() or path.is_symlink()):
            raise ValueError("Johto: mapa alterado ou sem hash auditado: " + name)
        observed = sha(path.read_bytes())
        if not allow_changed_map_bytes and observed != value and not (
                accept_audited_live_maps and observed == AUDITED_LIVE_BEDROOM_SHA[name]
                and data.get("bedroom_layout") in (None, "")):
            raise ValueError("Johto: mapa alterado ou sem hash auditado: " + name)
    # The global tileset may have been enlarged by Kanto/Hoenn. Accept ONLY
    # the authentic Johto slot and tables the map already references.
    tilesets = loads(local_target(game, "Data/Tilesets.rxdata").read_bytes())
    room = loads(local_target(game, "Data/Map674.rxdata").read_bytes())
    home = loads(local_target(game, "Data/Map675.rxdata").read_bytes())
    tid = room.attrs.get("@tileset_id") if isinstance(room, RubyObject) else None
    if (not isinstance(home, RubyObject) or home.name != "RPG::Map"
            or not isinstance(tilesets, list) or type(tid) is not int
            or tid <= 0 or tid >= len(tilesets)
            or not isinstance(tilesets[tid], RubyObject)):
        raise ValueError("Johto: tileset de New Bark não confere com a prévia original")
    name = text(tilesets[tid].attrs.get("@tileset_name"))
    private_hgss = (data.get("private_hgss") or {}).get("status") == "private_art_compiled"
    if (name != "BLUE_JOHTO_OPENING_INSIDE" and not (
            private_hgss and re.fullmatch(r"BLUE_JOHTO_HGSS_PRIVATE_[0-9]+", name))):
        raise ValueError("Johto: tileset de New Bark não confere com a prévia original")
    return data




def runtime_semantic_preview(game: Path) -> dict | None:
    """Recognize a compiled/modified Johto preview without promising native QA.

    Game.exe/region installers can update maps, PBS and shared MapInfos after
    original installation; comparing every byte to a time-frozen install proof
    is NOT an installation test. We retain the pinned original ZIP signature,
    require unchanged-or-audited New Bark anchors, parse all 100 genuine RMXP
    maps, validate their IDs and tileset references, and mark drift explicitly.
    """
    game = Path(game).resolve()
    # Room edits made by the visual editor and by Game.exe can be perfectly
    # valid RXDATA even when they no longer equal the frozen OFFLINE12 SHA.
    # Check provenance + all 100 native maps, not the two old bedroom bytes.
    # This intentionally does NOT authorize rewriting Map674/Map675.
    original = scoped_bedroom_proof(
        game, accept_audited_live_maps=True, allow_changed_map_bytes=True)
    if original is None:
        return None
    info_path = local_target(game, "Data/MapInfos.rxdata")
    tiles_path = local_target(game, "Data/Tilesets.rxdata")
    if (info_path.is_symlink() or tiles_path.is_symlink()
            or not info_path.is_file() or not tiles_path.is_file()):
        raise ValueError("Johto: registradores globais de mapas/tilesets ausentes")
    infos, tiles = loads(info_path.read_bytes()), loads(tiles_path.read_bytes())
    if not isinstance(infos, dict) or not PREVIEW_IDS.issubset(infos.keys()):
        raise ValueError("Johto: a tabela MapInfos não contém os 100 mapas")
    if not isinstance(tiles, list):
        raise ValueError("Johto: Tilesets.rxdata inválido")
    hashes = original["file_hashes"]
    changed = []
    for mid in sorted(PREVIEW_IDS):
        relative = f"Data/Map{mid:03d}.rxdata"
        path = local_target(game, relative)
        if not path.is_file() or path.is_symlink() or path.stat().st_size > 16_000_000:
            raise ValueError("Johto: mapa ausente ou arquivo inesperado: " + relative)
        contents = path.read_bytes()
        if sha(contents) != hashes.get(relative):
            changed.append(mid)
        m = loads(contents)
        if not isinstance(m, RubyObject) or m.name != "RPG::Map":
            raise ValueError("Johto: mapa não é RPG::Map: " + relative)
        a = m.attrs
        tid = a.get("@tileset_id")
        if (type(a.get("@width")) is not int or type(a.get("@height")) is not int
                or not 3 <= a["@width"] <= 300 or not 3 <= a["@height"] <= 300
                or not isinstance(a.get("@events"), dict) or type(tid) is not int
                or tid <= 0 or tid >= len(tiles)
                or not isinstance(tiles[tid], RubyObject)):
            raise ValueError("Johto: formato/dimensões de mapa inválidos: " + relative)
        table = a.get("@data")
        if (not table or getattr(table, "name", None) != "Table"):
            raise ValueError("Johto: terreno nativo ausente: " + relative)
        shape, _ = visual.table_values(table.data, 3)
        if shape != (a["@width"], a["@height"], 3):
            raise ValueError("Johto: terreno incompatível: " + relative)
        names = set()
        for event in a["@events"].values():
            if not isinstance(event, RubyObject) or event.name != "RPG::Event":
                raise ValueError("Johto: evento inválido: " + relative)
            ex,ey=event.attrs.get("@x"),event.attrs.get("@y")
            if (type(ex) is not int or type(ey) is not int
                    or not 0 <= ex < a["@width"] or not 0 <= ey < a["@height"]):
                raise ValueError("Johto: evento fora do mapa: " + relative)
            names.add(text(event.attrs.get("@name")))
        if mid == 674 and not {"JH_HOME2F_TO_1F", "JH_NEW_GAME_PROFILE"}.issubset(names):
            raise ValueError("Johto: escada ou inicialização do quarto ausente em Map674")
        if mid == 675 and "JH_HOME1F_TO_2F" not in names:
            raise ValueError("Johto: retorno do primeiro andar ausente em Map675")
    plugin = local_target(game, f"{PLUGIN}/Boot.rb")
    metadata = local_target(game, "PBS/map_metadata_johto_main.txt")
    if (not plugin.is_file() or plugin.is_symlink()
            or not metadata.is_file() or metadata.is_symlink()):
        raise ValueError("Johto: plugin ou metadados regionais ausentes")
    if b"Compiler.singleton_class.prepend(" in plugin.read_bytes():
        raise ValueError("Johto: versão antiga do compilador recursivo; atualizar Boot.rb")
    return {"status": "EXPERIMENTAL_INSTALLED_RUNTIME_MODIFIED_NOT_NATIVE_TESTED",
            "map_count": len(PREVIEW_IDS), "changed_map_ids": changed,
            "native_qa": False, "operational_map_structure": True}



def refresh_installed_bedroom(game: Path, root: Path = ROOT, *, allow_global_drift: bool = False) -> dict:
    """Apply the HGSS-inspired 2F layout to a previously installed Johto preview.

    Reusing Blue-Story must also update the real Map674/Map675 RXDATA, not just
    the Python authoring code. Only hash-verified Johto files are edited; no
    Kanto/Hoenn/Decades maps, world registry, compiled scripts or saves change.
    """
    game, root = Path(game).resolve(), Path(root).resolve()
    global_drift = False
    try:
        installed = preview_proof(game)
    except (OSError, ValueError, KeyError, TypeError):
        if not allow_global_drift:
            raise
        installed = scoped_bedroom_proof(game, accept_audited_live_maps=True)
        global_drift = True
    if installed is None:
        return {"changed": False, "reason": "Johto não instalada"}
    if installed.get("bedroom_layout") == visual.HGSS_BEDROOM_LAYOUT:
        # Do not trust a flag alone: check the actual warp on Map674, because
        # the game may still display its old staircase after a partial update.
        actual = loads(local_target(game, "Data/Map674.rxdata").read_bytes())
        stairs = [e for e in actual.attrs["@events"].values()
                  if text(e.attrs.get("@name")) == "JH_HOME2F_TO_1F"]
        if len(stairs) != 1 or (stairs[0].attrs["@x"], stairs[0].attrs["@y"]) != visual.HGSS_STAIRS_WARP:
            raise ValueError("Manifesto diz HGSS, mas Map674 ainda contém escada antiga")
        return {"changed": False, "reason": "Quarto HGSS de Johto já atualizado",
                "global_integrity_drift": global_drift}

    paths = ("Data/Map674.rxdata", "Data/Map675.rxdata")
    maps = [loads(local_target(game, name).read_bytes()) for name in paths]
    if any(not isinstance(obj, RubyObject) or obj.name != "RPG::Map" for obj in maps):
        raise ValueError("Quarto/casa de Johto não são mapas RMXP válidos")
    tilesets = loads(local_target(game, "Data/Tilesets.rxdata").read_bytes())
    tid = maps[0].attrs.get("@tileset_id")
    if (not isinstance(tilesets, list) or type(tid) is not int or tid <= 0
            or tid >= len(tilesets) or not isinstance(tilesets[tid], RubyObject)
            or text(tilesets[tid].attrs.get("@tileset_name")) != "BLUE_JOHTO_OPENING_INSIDE"):
        raise ValueError("Tileset do quarto não é o atlas Johto auditado")
    _, passages = visual.table_values(tilesets[tid].attrs["@passages"].data, 1)
    # Four imported decoration tiles + two nine-tile rugs, padded to 24
    # entries by extend_tileset(); do not duplicate the atlas in game/.
    first = len(passages) - 24
    if first < 384 or len(passages) - first != 24:
        raise ValueError("Tileset Johto sem as decorações originais")
    visual.style_bedroom_hgss(maps[0], maps[1], first)
    modified = {name: serialize(obj, johto_qa.EVENT_CLASSES)
                for name, obj in zip(paths, maps)}
    proof = copy.deepcopy(installed)
    proof["bedroom_layout"] = visual.HGSS_BEDROOM_LAYOUT
    proof["bedroom_stairs_warp"] = list(visual.HGSS_STAIRS_WARP)
    proof["bedroom_stairs_return"] = list(visual.HGSS_STAIRS_RETURN)
    for name, contents in modified.items():
        proof["file_hashes"][name] = sha(contents)
    modified[PROOF] = raw_json(proof)

    backups = root / ".blue-backups" / ("johto-bedroom-hgss-" + uuid.uuid4().hex)
    backups.mkdir(parents=True)
    for name in (*paths, PROOF):
        source = local_target(game, name)
        if not source.is_file() or source.is_symlink():
            raise ValueError("Arquivo Johto inesperado: " + name)
        target = backups / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    written = []
    try:
        for name in (*paths, PROOF):
            target = local_target(game, name)
            pending = target.with_name(target.name + ".blue-hgss-tmp")
            if pending.exists() or pending.is_symlink():
                raise ValueError("Atualização do quarto Johto encontrou temporário antigo")
            try:
                pending.write_bytes(modified[name])
                if sha(pending.read_bytes()) != sha(modified[name]):
                    raise ValueError("Falha de checksum no quarto Johto")
                os.replace(pending, target)
                written.append(name)
            finally:
                pending.unlink(missing_ok=True)
        # Recheck exactly the same security scope that was authorized.
        # Global readiness stays false when unrelated shared files have drifted.
        if global_drift:
            scoped_bedroom_proof(game)
        else:
            preview_proof(game)
        return {"changed": True, "bedroom_layout": visual.HGSS_BEDROOM_LAYOUT,
                "global_integrity_drift": global_drift,
                "reason": "Map674 e retorno da escada em Map675 atualizados",
                "backup_folder": str(backups)}
    except BaseException:
        for name in reversed(written):
            shutil.copy2(backups / name, local_target(game, name))
        raise



def refresh_installed_private_hgss(game: Path, root: Path = ROOT) -> dict:
    """Update local artist-provided HGSS graphics in ALL mapped Johto interiors.

    Only runs if the user has provided a valid private tile manifest and PNGs;
    never downloads/distributes artwork and never modifies saves or other
    regions. The installer records exact hashes and supports full rollback.
    """
    game, root = Path(game).resolve(), Path(root).resolve()
    manifest, sources = hgss.private_sources(root)
    if manifest is None:
        return {"changed": False, "reason": "Tilesets de autores não fornecidos"}
    installed = preview_proof(game)
    if installed is None:
        return {"changed": False, "reason": "Johto experimental ainda não instalada"}
    digest = sha((root / hgss.MANIFEST).read_bytes())
    old = installed.get("private_hgss") or {}
    if old.get("manifest_sha256") == digest and old.get("status") == "private_art_compiled":
        if old.get("source_digests") != {s: t[5] for s, t in sources.items()}:
            raise ValueError("Manifesto/arquivos HGSS privados divergentes")
        return {"changed": False, "reason": "Todos interiores HGSS já preparados"}
    if old.get("status") == "private_art_compiled":
        raise ValueError("Troca de pacote HGSS já instalado exige uma migração auditada; não empilhar tilesets")

    names = [f"Data/Map{mid:03}.rxdata" for mid in sorted(hgss.INTERIORS)]
    maps = {mid: loads(local_target(game, f"Data/Map{mid:03}.rxdata").read_bytes())
            for mid in sorted(hgss.INTERIORS)}
    if any(not isinstance(obj, RubyObject) or obj.name != "RPG::Map" for obj in maps.values()):
        raise ValueError("Mapas de interiores Johto inválidos")
    sets = loads(local_target(game, "Data/Tilesets.rxdata").read_bytes())
    if not isinstance(sets, list):
        raise ValueError("Tilesets da instalação Johto inválidos")
    extra = {}
    def read_graphic(category, name):
        key = f"Graphics/{category}/{name}.png"
        return extra[key] if key in extra else johto_qa.regular(local_target(game, key)).read_bytes()
    art = hgss.compile_private_art(maps, sets, extra, read_graphic, root)
    if art.get("status") != "private_art_compiled":
        raise ValueError("Manifesto HGSS não produziu os tiles esperados")
    # Validate every generated tile reference, named graphic and flag table
    # before touching the existing installation.
    visual.audit_tilesets(maps, sets, read_graphic)
    replacement = {f"Data/Map{mid:03}.rxdata": serialize(maps[mid], johto_qa.EVENT_CLASSES)
                   for mid in art["maps"]}
    replacement["Data/Tilesets.rxdata"] = serialize(sets)
    replacement.update(extra)

    new_proof = copy.deepcopy(installed)
    new_proof["private_hgss"] = art
    for name, blob in replacement.items():
        new_proof["file_hashes"][name] = sha(blob)
    replacement[PROOF] = raw_json(new_proof)

    backup_files = {name for name in replacement if name != PROOF
                    and local_target(game, name).exists()}
    backup_files.add(PROOF)
    backups = root / ".blue-backups" / ("johto-private-hgss-" + uuid.uuid4().hex)
    backups.mkdir(parents=True)
    for name in sorted(backup_files):
        src = local_target(game, name)
        if not src.is_file() or src.is_symlink():
            raise ValueError("Backup HGSS encontrou arquivo inesperado: " + name)
        target = backups / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)

    # The proof is last so interrupted upgrades never pass preview_proof().
    updated = []
    try:
        order = [name for name in replacement if name != PROOF] + [PROOF]
        for name in order:
            destination = local_target(game, name)
            if name.startswith("Graphics/") and destination.exists():
                raise ValueError("Atlas HGSS privado já existente: " + name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            pending = destination.with_name(destination.name + ".hgss-tmp")
            if pending.exists() or pending.is_symlink():
                raise ValueError("Atualização HGSS encontrou arquivo temporário")
            try:
                pending.write_bytes(replacement[name])
                if sha(pending.read_bytes()) != sha(replacement[name]):
                    raise ValueError("Falha de integridade HGSS: " + name)
                os.replace(pending, destination)
                updated.append(name)
            finally:
                pending.unlink(missing_ok=True)
        preview_proof(game)
        return {"changed": True, "maps": art["maps"], "credits": art["credits"],
                "backup_folder": str(backups), "reason": "Interiores HGSS atualizados"}
    except BaseException:
        for name in reversed(updated):
            destination = local_target(game, name)
            if name in backup_files:
                shutil.copy2(backups / name, destination)
            else:
                destination.unlink(missing_ok=True)
        raise


def build_overlay(game: Path, bundle: Path, root: Path = ROOT) -> tuple[dict[str, bytes], dict]:
    """Plan and validate in memory; no writes to game/ until every check passes."""
    if game.is_symlink() or not (game / "Game.exe").is_file():
        raise ValueError("Game.exe principal não encontrado")
    if any((game / f"{name} pilot.json").exists() for name in ("Kanto", "Johto", "Hoenn", "Sinnoh")):
        raise ValueError("Não é permitido integrar Johto numa cópia de piloto")
    if (game / PROOF).exists() or (game / READY).exists():
        raise ValueError("Instalação Johto já presente; revalidar antes de modificar")
    files, stage, bundle_hash = johto_qa.archive_payload(bundle, json.loads(
        (root / "data/regions/johto-source.json").read_text("utf-8"))["source"]["archive_sha256"])
    if bundle_hash != PINNED_SHA:
        raise ValueError("Prévia privada Johto não corresponde ao pacote original auditado")
    rows = stage.get("maps", [])
    if len(rows) != 82 or {r.get("destination_id") for r in rows} != STAGED_IDS:
        raise ValueError("Prévia Johto não contém exatamente os 82 mapas de origem")
    current_infos = loads((game / "Data/MapInfos.rxdata").read_bytes())
    current_tiles = loads((game / "Data/Tilesets.rxdata").read_bytes())
    stage_infos = loads(files.pop("Data/MapInfos.rxdata"))
    stage_tiles = loads(files.pop("Data/Tilesets.rxdata"))
    if not (isinstance(current_infos, dict) and isinstance(stage_infos, dict)
            and isinstance(current_tiles, list) and isinstance(stage_tiles, list)):
        raise ValueError("MapInfos/Tilesets não são dados nativos RMXP válidos")
    # Hoenn uses IDs 700–999. All supplementary Johto house interiors in this
    # first shared preview are deliberately restricted to 682–699.
    conflicts = [i for i in PREVIEW_IDS
                 if i in current_infos or (game / f"Data/Map{i:03}.rxdata").exists()]
    if conflicts:
        raise ValueError("MapIDs já usados por outra região: " + str(conflicts[:12]))
    if not STAGED_IDS.issubset(stage_infos):
        raise ValueError("MapInfos do pacote não incluem Johto")

    maps = {i: loads(files.pop(f"Data/Map{i:03}.rxdata")) for i in sorted(STAGED_IDS)}
    for mid, map_obj in maps.items():
        if not isinstance(map_obj, RubyObject) or map_obj.name != "RPG::Map":
            raise ValueError(f"Map{mid} inválido")
    # PBS is merged into the current Kanto+Hoenn file, never replaced by the
    # historical base embedded in the offline package.
    native_pbs = {p.relative_to(game).as_posix(): "" for p in (game / "PBS").glob("*.txt")}
    files["PBS/map_connections.txt"] = johto_qa.validate_pbs(game, files, native_pbs)

    def graphic(folder: str, name: str) -> bytes:
        relative = f"Graphics/{folder}/{name}.png"
        if relative in files:
            return files[relative]
        return johto_qa.regular(game / relative).read_bytes()

    sprites = {p.stem for p in (game / "Graphics/Characters").glob("*.png")}
    sprites.update(Path(k).stem for k in files if k.startswith("Graphics/Characters/"))
    johto_qa.repair_new_bark(*(maps[i] for i in (600, START[0], 675, 676)))
    repair_opening(maps, sprites)
    # Install the private QA-authored rooms and visual fixes, but never the
    # interiors 700–708 that would overwrite Hoenn in the shared build.
    old_rooms, old_names = visual.REGIONAL_INTERIORS, visual.NEW_MAPS
    try:
        visual.REGIONAL_INTERIORS = {k: v for k, v in old_rooms.items() if k < 700}
        visual.NEW_MAPS = {k: v for k, v in old_names.items() if k < 700}
        visual.repair_visual_layout(maps, stage_infos, stage_tiles, files, graphic)
        # Optional artist-provided HGSS indoor PNGs are imported from the
        # user's PRIVATE .blue-work folder, never committed to the repository.
        hgss_report = hgss.compile_private_art(maps, stage_tiles, files, graphic, root)
        # Manual Johto maps override authored defaults AFTER visual repair.
        editor_patches = map_patches.apply_project_patches(maps, stage_tiles, root)
        files["PBS/map_metadata_johto_main.txt"] = visual.johto_metadata(maps, stage_infos)
        files["PBS/map_connections.txt"] = visual.revise_connections(files["PBS/map_connections.txt"])
        count, tile_count = visual.audit_tilesets(maps, stage_tiles, graphic)
    finally:
        visual.REGIONAL_INTERIORS, visual.NEW_MAPS = old_rooms, old_names
    if set(maps) != PREVIEW_IDS or count != 100:
        raise ValueError("Construção Johto deve produzir os 100 mapas 600–699")
    if not (0 <= START[1] < maps[START[0]].attrs["@width"]
            and 0 <= START[2] < maps[START[0]].attrs["@height"]):
        raise ValueError("Spawn New Bark fora do quarto")
    # The offline-12 authoring pass intentionally places a transparent,
    # autorun profile initializer on the EXACT New Bark bedroom start tile.
    # Reject real blockers, but do not reject that one named, non-graphic
    # initializer or Johto can never be installed from its original ZIP.
    assert_spawn_not_blocked(maps[START[0]])

    # Copy each source Johto tileset to a NEW native index, leaving all
    # Decades/Kanto/Hoenn tileset ids and metadata exactly as they were.
    ids = sorted({m.attrs["@tileset_id"] for m in maps.values()})
    new_tiles = copy.deepcopy(current_tiles)
    remap = {}
    for old_id in ids:
        if type(old_id) is not int or old_id <= 0 or old_id >= len(stage_tiles):
            raise ValueError(f"Tileset Johto inválido: {old_id}")
        new_id = len(new_tiles)
        clone = copy.deepcopy(stage_tiles[old_id])
        if not isinstance(clone, RubyObject) or clone.name != "RPG::Tileset":
            raise ValueError("Tileset Johto corrompido")
        clone.attrs["@id"] = new_id
        remap[old_id] = new_id
        new_tiles.append(clone)
    for mid, obj in maps.items():
        obj.attrs["@tileset_id"] = remap[obj.attrs["@tileset_id"]]
        files[f"Data/Map{mid:03}.rxdata"] = serialize(obj, johto_qa.EVENT_CLASSES)
    new_infos = current_infos.copy()
    for mid in sorted(maps):
        new_infos[mid] = stage_infos[mid]
    files["Data/MapInfos.rxdata"] = serialize(new_infos)
    files["Data/Tilesets.rxdata"] = serialize(new_tiles)

    # All map graphics must exist with the exact expected name. Never replace
    # a different Kanto/Hoenn PNG under the same filename.
    for rel in list(files):
        if rel.startswith("Graphics/"):
            path = game / rel
            if path.exists():
                if path.is_symlink() or johto_qa.checksum(path) != sha(files[rel]):
                    raise ValueError(f"Gráfico já usado por outra região: {rel}")
                del files[rel]
            elif not files[rel].startswith(johto_qa.PNG):
                raise ValueError(f"PNG Johto inválido: {rel}")
    for trainer, original in johto_qa.TRAINER_SPRITES.items():
        target = f"Graphics/Trainers/{trainer}.png"
        if (game / target).exists():
            raise ValueError("Sprite do treinador Johto já existe: " + trainer)
        source = game / f"Graphics/Trainers/{original}.png"
        files[target] = johto_qa.regular(source).read_bytes()
    for source in RUNTIME:
        if not (root / "scripts/regions" / source).is_file():
            raise ValueError("Script Ruby Johto ausente: " + source)
    files[f"{PLUGIN}/Boot.rb"] = b"\n".join(
        (root / "scripts/regions" / source).read_bytes() for source in RUNTIME)
    files[f"{PLUGIN}/meta.txt"] = (
        b"Name = Blue Johto Main Preview\nVersion = 0.1\nEssentials = 21.1\n"
        b"Requires = Blue Battle Presentation and Story\nScripts = Boot.rb\n")

    # Optional licensed HGSS audio is NOT in this ZIP. Disable per-map
    # auto playback when the track is not already in the player's game.
    for mid in maps:
        obj = maps[mid]
        track = text(obj.attrs["@bgm"].attrs["@name"]) if obj.attrs.get("@bgm") else ""
        if obj.attrs.get("@autoplay_bgm") and track and not (
                game / ("Audio/BGM/" + track + ".ogg")).is_file():
            obj.attrs["@autoplay_bgm"] = False
            files[f"Data/Map{mid:03}.rxdata"] = serialize(obj, johto_qa.EVENT_CLASSES)

    # Recheck all explicitly referenced graphics after visual repairs.
    referenced = set()
    for old_id in ids:
        tileset = stage_tiles[old_id].attrs
        if tileset["@tileset_name"]:
            referenced.add("Graphics/Tilesets/" + text(tileset["@tileset_name"]) + ".png")
        for name in tileset["@autotile_names"]:
            if name:
                referenced.add("Graphics/Autotiles/" + text(name) + ".png")
    for map_obj in maps.values():
        for event in map_obj.attrs["@events"].values():
            for page in event.attrs["@pages"]:
                name = text(page.attrs["@graphic"].attrs["@character_name"])
                if name:
                    referenced.add("Graphics/Characters/" + name + ".png")
    for name in referenced:
        if name not in files and not (game / name).is_file():
            raise ValueError("Sprite/tileset Johto ausente: " + name)

    report = {
        "schema": 1, "region": "JOHTO", "status": STATUS,
        "source_bundle_sha256": PINNED_SHA,
        "source_release_approved": False, "native_gameplay_verified": False,
        "android_verified": False, "fully_playable": False,
        "map_ids": sorted(PREVIEW_IDS), "start": list(START),
        "town": list(TOWN), "npc": list(NPC),
        "tilesets_added": tile_count, "pbs_compilation_pending": True,
        "bedroom_layout": visual.HGSS_BEDROOM_LAYOUT,
        "bedroom_stairs_warp": list(visual.HGSS_STAIRS_WARP),
        "bedroom_stairs_return": list(visual.HGSS_STAIRS_RETURN),
        "private_hgss": hgss_report,
        "editor_map_patches": {str(mid): map_patches.digest(
            map_patches.patch_path(root, mid).read_bytes()) for mid in editor_patches},
        "file_hashes": {name: sha(blob) for name, blob in files.items()},
    }
    files[PROOF] = raw_json(report)
    files[READY] = ("BLUE_JOHTO_PRIVATE_PREVIEW_V1,100," +
                    ",".join(map(str, (*START, *TOWN[:3], *NPC[:3]))) + "\n").encode("ascii")
    return files, report


def install(game: Path, bundle: Path, root: Path = ROOT, *, apply: bool = False) -> dict:
    game, root = Path(game).resolve(), Path(root).resolve()
    package = Path(bundle).resolve()
    files, report = build_overlay(game, package, root)
    # CH03: reject foreign Map*.rxdata at the shared installer write boundary,
    # even when the overlay producer is replaced or a report is tampered with.
    # Existing Hoenn 800–805 files are not touched or flagged as Sinnoh.
    assert_johto_shared_overlay_map_ids(files, allowed_ids=PREVIEW_IDS)
    if not apply:
        return {"status": "PLAN_VALIDATED_NOT_INSTALLED", "ready": False,
                "maps": len(PREVIEW_IDS), "files": len(files)}
    backups = root / ".blue-backups" / ("johto-preview-" + uuid.uuid4().hex)
    backups.mkdir(parents=True)
    previous: dict[str, Path | None] = {}
    written: list[str] = []
    try:
        # Never overwrite other region's map or plugin. Only these two native
        # registries plus map_connections are intentionally modified in place.
        replaceable = {"Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
                       "PBS/map_connections.txt"}
        for name in files:
            target = local_target(game, name)
            if target.exists():
                if name not in replaceable:
                    raise ValueError("Destino Johto existente, não sobrescrever: " + name)
                backup = backups / name
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
                previous[name] = backup
            else:
                previous[name] = None
        ordered = [n for n in files if n not in (PROOF, READY)] + [PROOF, READY]
        for name in ordered:
            target = local_target(game, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_name(target.name + ".blue-johto-tmp")
            if tmp.exists() or tmp.is_symlink():
                raise ValueError("Arquivo temporário Johto já existe: " + str(tmp))
            try:
                tmp.write_bytes(files[name])
                if sha(tmp.read_bytes()) != sha(files[name]):
                    raise ValueError("Escrita corrompida: " + name)
                os.replace(tmp, target)
                written.append(name)
            finally:
                tmp.unlink(missing_ok=True)
        report["backup_folder"] = str(backups)
        # The marker is written LAST. No auto-unlock if an earlier write fails.
        return {"status": "EXPERIMENTAL_INSTALLED_NOT_NATIVE_TESTED",
                "ready": False, "changed": True, "maps": 100,
                "backup_folder": str(backups)}
    except BaseException:
        for name in reversed(written):
            target = local_target(game, name)
            original = previous.get(name)
            if original is None:
                target.unlink(missing_ok=True)
            else:
                shutil.copy2(original, target)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, default=ROOT / "game")
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--verify-installed", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = ({"status": "EXPERIMENTAL_VERIFIED_STATIC",
                   "ready": False, "proof": preview_proof(args.game)}
                  if args.verify_installed else
                  install(args.game, args.bundle, ROOT, apply=args.apply))
        print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError) as err:
        print("[JOHTO PREVIEW] BLOQUEADO: " + str(err), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
