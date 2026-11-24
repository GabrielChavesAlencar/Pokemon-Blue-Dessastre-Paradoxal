#!/usr/bin/env python3
"""Blue-Story native Sinnoh QA supervisor: launch, verify, recover, restart once.

No shell or fallback to the main Game.exe. Only operates inside an exact
private QA directory created under the managed project's .blue-work folder.
The first native compiler may rewrite Tilesets.rxdata; restore only the
original SHA-pinned bytes saved by the installer. Never rebaseline hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "regions"))
import install_sinnoh_experimental_windows as installer

ENABLED = "Data/sinnoh-experimental-auto-restart-enabled.txt"
REQUEST = "Data/sinnoh-experimental-auto-restart-request.txt"
PRISTINE = "Data/sinnoh-experimental-tilesets-pristine.bin"
TILESETS = "Data/Tilesets.rxdata"
COMPILE_REQUEST = "Data/sinnoh-experimental-compile-request.txt"
MAX_TILE_BYTES = 256 * 1024 * 1024
HASH_PATTERN = re.compile(r"[a-f0-9]{64}$")


def block(reason: str):
    raise ValueError("SINNOH_QA_SUPERVISOR_BLOCKED:" + reason)


def secure_file(path: Path):
    installer.safe_path(path)
    if not path.is_file():
        block("MISSING_OR_UNSAFE_FILE:" + path.name)
    return path


def digest(path: Path) -> str:
    secure_file(path)
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(32768)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def load_qa(project: Path, qa: Path) -> dict:
    project = installer.safe_path(Path(project).absolute())
    qa = installer.safe_path(Path(qa).absolute())
    work = installer.safe_path(project / ".blue-work")
    if (not project.is_dir() or qa.parent != work or
            not re.fullmatch(r"game-sinnoh-experimental-[a-f0-9]{12}", qa.name) or
            not qa.is_dir()):
        block("NOT_EXACT_PRIVATE_QA_DIRECTORY")
    data = json.loads(secure_file(qa / "sinnoh-experimental-qa.json").read_text("utf-8"))
    token = qa.name.rsplit("-", 1)[-1]
    if (not isinstance(data, dict) or data.get("schema") != 1 or
        data.get("mode") != installer.MODE or data.get("region") != "SINNOH" or
        data.get("profile_token") != token or
        data.get("main_game_modified") is not False or
        data.get("personal_saves_copied") is not False or
        data.get("r09_native_qa_executed") != 0 or
        data.get("runtime_playable_verified") is not False):
        block("INVALID_QA_MANIFEST_OR_PROVENANCE")
    save_token = data.get("save_profile_token", token)
    if not isinstance(save_token, str) or not re.fullmatch(r"[a-f0-9]{12}", save_token):
        block("INVALID_SAVE_PROFILE_TOKEN")
    profile = data.get("save_profile")
    if (not isinstance(profile, dict) or
            profile.get("title") != "Sinnoh QA " + save_token or
            profile.get("dataPathApp") != "Sinnoh-QA-" + save_token or
            profile.get("dataPathOrg") != "Dessastre-Sinnoh-QA-" + save_token):
        block("INVALID_PRIVATE_SAVE_NAMESPACE")
    config = json.loads(secure_file(qa / "mkxp.json").read_text("utf-8-sig"))
    if (not isinstance(config, dict) or
        any("save" in str(k).casefold() or "userdata" in str(k).casefold()
            for k in config) or
        any(config.get(key) != value for key, value in (
            ("windowTitle", profile["title"]),
            ("dataPathApp", profile["dataPathApp"]),
            ("dataPathOrg", profile["dataPathOrg"])))):
        block("GAME_EXE_SAVE_NAMESPACE_MISMATCH")
    title = "Title=" + profile["title"]
    if secure_file(qa / "Game.ini").read_text("utf-8-sig").splitlines().count(title) != 1:
        block("GAME_INI_TITLE_MISMATCH")
    maps = data.get("mapids")
    story=data.get("private_lake_story",{})
    count=10 if isinstance(story,dict) and story.get("portal_pairs")==2 else 9
    cities={"SINNOH_"+k for k in ("JUBILIFE_CITY","OREBURGH_CITY","FLOAROMA_TOWN","ETERNA_CITY","HEARTHOME_CITY","SOLACEON_TOWN","VEILSTONE_CITY","PASTORIA_CITY","CELESTIC_TOWN","CANALAVE_CITY","SNOWPOINT_CITY","SUNYSHORE_CITY")}
    city_report=data.get("city_expansion",{})
    if city_report:
        if (count!=10 or not isinstance(maps,dict) or not isinstance(city_report,dict) or set(city_report)!=cities or
                any(k not in maps or not isinstance(city_report[k],dict) or city_report[k].get("target_id")!=maps[k] for k in cities)):
            block("INVALID_F04_CITY_MANIFEST")
        count=22
    routes=data.get("route_expansion",{})
    route_keys={"SINNOH_ROUTE_%d"%n for n in range(203,231)}|{"SINNOH_ROUTE_%d_SEGMENT_2"%n for n in (205,210,212,224,225,228)}
    if routes:
        if (count!=22 or not isinstance(routes,dict) or set(routes)!=route_keys or
                any(k not in maps or not isinstance(routes[k],dict) or routes[k].get("target_id")!=maps[k] for k in route_keys)):
            block("INVALID_F05_ROUTE_MANIFEST")
        count=56
    interiors=data.get("interior_expansion",{})
    interior_keys={"SINNOH_F07_INTERIOR_%03d"%mid for mid in (32,43,48,81,86,87,88,97,107,115,120,124,125,129,130,131,132,133,134,135,136,137,138,143,148,149,158,167,168,169,170,171,172,187,188,220)}
    extra=data.get("f08c_expansion",{})
    extra_keys={"SINNOH_RESORT_AREA","SINNOH_CYCLING_ROAD","SINNOH_SURVIVAL_AREA","SINNOH_FIGHT_AREA"}
    natural=data.get("natural_expansion",{})
    natural_keys=set(["SINNOH_OREBURGH_MINE","SINNOH_OREBURGH_GATE","SINNOH_MT_CORONET_WEST_APPROACH","SINNOH_SOLACEON_RUINS","SINNOH_ETERNA_FOREST","SINNOH_ETERNA_FOREST_SOURCE_093","SINNOH_FLOAROMA_MEADOW","SINNOH_MT_CORONET_SOURCE_117","SINNOH_MT_CORONET_INTERIOR_ROUTES","SINNOH_RAVAGED_PATH","SINNOH_STARK_MOUNTAIN","SINNOH_STARK_MOUNTAIN_SOURCE_153","SINNOH_ACUITY_LAKEFRONT","SINNOH_LAKE_ACUITY","SINNOH_ACUITY_CAVERN","SINNOH_SNOWPOINT_TEMPLE","SINNOH_MT_CORONET_SOURCE_174","SINNOH_MT_CORONET_SOURCE_182","SINNOH_MT_CORONET_SOURCE_183","SINNOH_MT_CORONET_SOURCE_184","SINNOH_WAYWARD_CAVE","SINNOH_WAYWARD_CAVE_SOURCE_190","SINNOH_VERITY_CAVERN","SINNOH_MANIAC_TUNNEL","SINNOH_SPRING_PATH","SINNOH_SENDOFF_SPRING","SINNOH_TURNBACK_CAVE","SINNOH_TURNBACK_CAVE_SOURCE_211","SINNOH_TURNBACK_CAVE_SOURCE_212","SINNOH_TURNBACK_CAVE_SOURCE_213","SINNOH_VALOR_LAKEFRONT","SINNOH_LAKE_VALOR","SINNOH_LAKE_VALOR_SOURCE_216","SINNOH_VALOR_CAVERN","SINNOH_GREAT_MARSH"])
    if natural:
        if (count!=56 or not isinstance(natural,dict) or set(natural)!=natural_keys or
                any(k not in maps or not isinstance(natural[k],dict) or natural[k].get("target_id")!=maps[k] for k in natural_keys) or
                any(type(n) is not int or not 442<=n<=517 for k,n in maps.items() if k not in natural_keys and not (interiors and k in interior_keys) and not (extra and k in extra_keys))):
            block("INVALID_F06_NATURAL_MANIFEST")
        count=91
    if interiors:
        if (count!=91 or not isinstance(interiors,dict) or set(interiors)!=interior_keys or
                any(k not in maps or not isinstance(interiors[k],dict) or interiors[k].get("target_id")!=maps[k] or
                    interiors[k].get("source_tileset_id")!=25 or interiors[k].get("outdoor") is not False
                    for k in interior_keys)):
            block("INVALID_F07_INTERIOR_MANIFEST")
        count=127
    if extra:
        if (count!=127 or not isinstance(extra,dict) or set(extra)!=extra_keys or
            any(k not in maps or not isinstance(extra[k],dict) or extra[k].get("target_id")!=maps[k]
                or extra[k].get("source_tileset_id")!=24 or extra[k].get("outdoor") is not True for k in extra_keys)):
            block("INVALID_F08C_MANIFEST")
        count=131
    if (not isinstance(maps, dict) or len(maps) != count or
            (count>=10 and "SINNOH_VERITY_LAKEFRONT" not in maps) or
            len(set(maps.values())) != count or
            not all(type(n) is int and 442 <= n <= (599 if count>=91 else 517) for n in maps.values())):
        block("INVALID_NINE_QA_MAPIDS")
    start = data.get("start")
    if (not isinstance(start, list) or len(start) != 3 or
        start[0] != maps.get("SINNOH_PLAYER_BEDROOM") or
        not all(type(n) is int and n >= 0 for n in start)):
        block("INVALID_SINNOH_QA_START")
    secure_file(qa / "Game.exe")
    return data


def restore_exact(qa: Path, expected: str, hashes: dict):
    pristine = qa / PRISTINE
    tiles = qa / TILESETS
    if hashes.get(PRISTINE) != expected or digest(pristine) != expected:
        block("TILESETS_PRISTINE_HASH_MISMATCH")
    secure_file(tiles)
    if pristine.stat().st_size > MAX_TILE_BYTES:
        block("TILESETS_PRISTINE_TOO_LARGE")
    fd, name = tempfile.mkstemp(prefix=".sinnoh-tilesets-verified-", dir=qa / "Data")
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as dest, pristine.open("rb") as source:
            while True:
                chunk = source.read(32768)
                if not chunk:
                    break
                dest.write(chunk)
        if digest(temporary) != expected:
            block("TILESETS_SNAPSHOT_CHANGED_DURING_COPY")
        # Source and destination are already verified regular files.
        os.replace(temporary, tiles)
        if digest(tiles) != expected:
            block("TILESETS_RESTORE_FAILED")
    finally:
        if temporary.exists():
            temporary.unlink()


def audit_maps(qa: Path, data: dict, *, allow_tile_recovery: bool):
    hashes = data.get("file_sha256")
    if not isinstance(hashes, dict):
        block("MISSING_SHA256_MANIFEST")
    files = ["Data/MapInfos.rxdata", TILESETS] + [
        "Data/Map%03d.rxdata" % n for n in data["mapids"].values()
    ]
    if data.get("visual_revision") == "SINNOH_ORIGINAL_PIXEL_ART_V2":
        files += [
            "Graphics/Tilesets/SN_J11C_Original_Interior.png",
            "Graphics/Tilesets/SN_J11C_Original_Exterior.png",
            "Graphics/Autotiles/SNQA_WaterV2.png",
            "Graphics/Autotiles/SNQA_PathV2.png",
            "Graphics/Autotiles/SNQA_GrassV2.png",
            "Graphics/Characters/SNQA_MOTHER.png",
            "Graphics/Characters/SNQA_BARRY.png",
            "Graphics/Characters/SNQA_ROWAN.png",
            "Graphics/Characters/SNQA_BALL.png",
        ]
    private=data.get("private_visual_import",{})
    if isinstance(private,dict) and private.get("maps"):
        files += ["Graphics/Tilesets/SNQA_Private_Outdoors.png","Graphics/Tilesets/SNQA_Private_Indoors.png"]
        files += ["Graphics/Autotiles/SNQA_Private_Auto_%d.png"%i for i in range(1,8)]
    cities=data.get("city_expansion",{})
    if cities:
        source_ids={row["source_id"] for row in cities.values()}
        if source_ids!={22,77,84,90,96,106,109,123,160,205,219,225}:block("INVALID_F04_SOURCE_IDS")
        files += ["Graphics/Tilesets/SNQA_F04_%03d.png"%mid for mid in sorted(source_ids)]
    routes=data.get("route_expansion",{})
    if routes:
        source_ids={row["source_id"] for row in routes.values()}
        if source_ids!={42,79,80,91,94,104,105,108,110,116,122,126,140,141,142,146,150,151,155,156,157,164,165,198,199,200,206,218,222,223,224,226,233,234}:block("INVALID_F05_SOURCE_IDS")
        files += ["Graphics/Tilesets/SNQA_F05_%03d.png"%mid for mid in sorted(source_ids)]
    natural=data.get("natural_expansion",{})
    if natural:
        source_ids={row["source_id"] for row in natural.values()}
        if source_ids!={33,76,82,89,92,93,98,117,121,145,152,153,159,161,162,173,174,182,183,184,189,190,197,207,208,209,210,211,212,213,214,215,216,217,221}:block("INVALID_F06_SOURCE_IDS")
        files += ["Graphics/Tilesets/SNQA_F06_%03d.png"%mid for mid in sorted(source_ids)]
    interiors=data.get("interior_expansion",{})
    if interiors:
        source_ids={row["source_id"] for row in interiors.values()}
        if source_ids!={32,43,48,81,86,87,88,97,107,115,120,124,125,129,130,131,132,133,134,135,136,137,138,143,148,149,158,167,168,169,170,171,172,187,188,220}:block("INVALID_F07_SOURCE_IDS")
        files += ["Graphics/Tilesets/SNQA_F07_%03d.png"%mid for mid in sorted(source_ids)]
    extra=data.get("f08c_expansion",{})
    if extra:
        source_ids={row["source_id"] for row in extra.values()}
        if source_ids!={139,147,163,166}:block("INVALID_F08C_SOURCE_IDS")
        files += ["Graphics/Tilesets/SNQA_F08C_%03d.png"%mid for mid in sorted(source_ids)]
    continuity=data.get("private_continuity",{})
    if continuity:
        if not isinstance(continuity,dict) or len(continuity.get("connections",[]))!=(6 if data.get("private_lake_story") else 3):
            block("INVALID_PRIVATE_CONTINUITY")
        audio=continuity.get("audio_files")
        expected_audio=["Audio/BGM/SNQA_"+name+".ogg" for name in ("Twinleaf","Twinleaf_n","Route201","Route201_n","Lake","Sandgem","Sandgem_n")]
        if not isinstance(audio,list) or sorted(audio)!=sorted(expected_audio):
            block("INVALID_PRIVATE_AUDIO_MANIFEST")
        files += ["Data/map_connections.dat","PBS/map_connections.txt","PBS/map_metadata.txt"]+expected_audio
    if (not isinstance(hashes.get(PRISTINE), str) or
        hashes.get(PRISTINE) != hashes.get(TILESETS)):
        block("PRISTINE_NOT_PINNED_TO_ORIGINAL_HASH")
    if digest(qa / PRISTINE) != hashes[PRISTINE]:
        block("PRISTINE_FILE_TAMPERED")
    for rel in files:
        expected = hashes.get(rel)
        if not isinstance(expected, str) or not HASH_PATTERN.fullmatch(expected):
            block("INVALID_SHA256:" + rel)
        current = digest(qa / rel)
        if current != expected:
            if rel != TILESETS or not allow_tile_recovery:
                block("MAP_OR_INDEX_SHA256_MISMATCH:" + rel)
            restore_exact(qa, expected, hashes)
    return True


def supervise(project: Path, qa: Path, runner=None) -> int:
    project = installer.safe_path(Path(project).absolute())
    qa = installer.safe_path(Path(qa).absolute())
    data = load_qa(project, qa)
    token = data["profile_token"]
    enabled = qa / ENABLED
    request = qa / REQUEST
    pending = qa / COMPILE_REQUEST
    # Reject links and stale control markers before starting any executable.
    if enabled.exists() or enabled.is_symlink() or request.exists() or request.is_symlink():
        block("UNEXPECTED_SUPERVISOR_MARKER")
    if pending.exists() or pending.is_symlink():
        secure_file(pending)
    game = qa / "Game.exe"
    if runner is None:
        def runner(executable, cwd):
            return subprocess.call([str(executable)], cwd=str(cwd), shell=False)
    audit_maps(qa, data, allow_tile_recovery=True)
    with enabled.open("x", encoding="ascii") as stream:
        stream.write(token + "\n")
    try:
        if pending.is_file():
            print("SINNOH_QA: compilacao inicial apenas na copia privada", flush=True)
            code = runner(game, qa)
            if code != 0:
                block("NATIVE_COMPILER_EXIT_CODE:" + str(code))
            if pending.exists() or pending.is_symlink():
                block("NATIVE_COMPILER_REQUEST_STILL_PENDING")
            # Compiler may regenerate RXDATA even after the installer's SHA.
            audit_maps(qa, data, allow_tile_recovery=True)
        for attempt in range(2):
            audit_maps(qa, data, allow_tile_recovery=True)
            print("SINNOH_QA: abrindo mesma copia isolada (tentativa %d/2)" %
                  (attempt + 1), flush=True)
            code = runner(game, qa)
            if request.exists() or request.is_symlink():
                secure_file(request)
                proof = token + "\n" + data["file_sha256"][TILESETS] + "\n"
                if request.read_text("ascii") != proof or code != 0:
                    block("UNVERIFIED_RESTART_REQUEST")
                audit_maps(qa, data, allow_tile_recovery=False)
                request.unlink()
                if attempt:
                    block("ONE_RESTART_LIMIT_REACHED")
                print("SINNOH_QA: restauracao confirmada; reinicio automatico", flush=True)
                continue
            if code != 0:
                block("GAME_EXE_EXIT_CODE:" + str(code))
            return 0
        block("ONE_RESTART_LIMIT_REACHED")
    finally:
        # Remove only markers created for this supervised session.
        if enabled.is_file() and not enabled.is_symlink():
            enabled.unlink()
        if request.is_file() and not request.is_symlink():
            request.unlink()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--qa-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        return supervise(args.project_root, args.qa_dir)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as error:
        print(str(error), file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
