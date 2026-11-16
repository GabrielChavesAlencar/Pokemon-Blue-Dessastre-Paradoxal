"""Diagnose/repair the ACTUAL private Johto bedroom in the Blue-Story game.

Read-only by default; '--apply' invokes the existing verified and backed-up
Map674+Map675 installer. All failures leave native maps/saves unchanged.
Works with the portable Python unpacked by Blue-Story.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "regions"))
from server.ruby_marshal import RubyObject, loads, text
from build_johto_elm_lab_v1 import tile, table_values
from johto_main_preview import (PROOF, preview_proof,
                               scoped_bedroom_proof, refresh_installed_bedroom)

OUTPUT = ROOT / ".blue-work" / "johto-bedroom-diagnostic.json"


def sha_file(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(project: Path = ROOT, game: Path | None = None):
    project = Path(project).resolve()
    game = (Path(game) if game is not None else project / "game").resolve()
    report = {
        "schema": 1, "region": "JOHTO", "game_dir": str(game),
        "game_exe": str(game / "Game.exe"),
        "game_found": (game / "Game.exe").is_file(),
        "bedroom_map": str(game / "Data/Map674.rxdata"),
        "home_map": str(game / "Data/Map675.rxdata"),
        "status": "UNKNOWN", "safe_to_apply": False,
        "hgss_asset_manifest": (project / ".blue-work/johto-hgss-tiles/manifest.json").is_file(),
    }
    proof_file = game / PROOF
    if proof_file.is_file() and not proof_file.is_symlink():
        try:
            proof = json.loads(proof_file.read_text("utf-8"))
            report["manifest_bedroom_layout"] = proof.get("bedroom_layout", "")
            art = proof.get("private_hgss") or {}
            report["private_hgss_status"] = art.get("status", "no_private_art")
            report["private_hgss_maps"] = art.get("maps", [])
            hashes = proof.get("file_hashes") or {}
            report["two_map_hashes_match"] = all(
                (game / name).is_file() and sha_file(game / name) == hashes.get(name)
                for name in ("Data/Map674.rxdata", "Data/Map675.rxdata")
            )
        except (OSError, ValueError, TypeError, KeyError) as error:
            report["manifest_error"] = str(error)
    else:
        report["manifest_error"] = "Manifesto da prévia de Johto ausente"

    try:
        for mid in (674, 675):
            path = game / f"Data/Map{mid:03}.rxdata"
            if not path.is_file() or path.is_symlink():
                raise ValueError(f"Arquivo nativo Map{mid} ausente/ligado por symlink")
        bedroom = loads((game / "Data/Map674.rxdata").read_bytes())
        home = loads((game / "Data/Map675.rxdata").read_bytes())
        if any(not isinstance(x, RubyObject) or x.name != "RPG::Map" for x in (bedroom, home)):
            raise ValueError("Map674/675 não são mapas RPG Maker XP válidos")
        w,h = bedroom.attrs["@width"], bedroom.attrs["@height"]
        (_,_,depth), cells = table_values(bedroom.attrs["@data"].data, 3)
        report["map_size"] = [w,h,depth]
        if (w,h,depth) != (14,11,3):
            raise ValueError("Geometria do quarto difere do mapa auditado 14x11")
        stairs = [
            ev for ev in bedroom.attrs["@events"].values()
            if text(ev.attrs.get("@name")) == "JH_HOME2F_TO_1F"
        ]
        if len(stairs) != 1:
            raise ValueError(f"Escada do quarto: esperado um warp; encontrados {len(stairs)}")
        event = stairs[0]
        pos = [event.attrs["@x"], event.attrs["@y"]]
        report["actual_stairs_warp_xy"] = pos
        report["expected_stairs_warp_xy"] = [4,4]
        top_left = cells[2 + w * (3 + h * 2)]
        report["left_stair_tile"] = top_left
        report["left_stair_tile_expected"] = tile(238,1)
        downstairs = [
            ev for ev in home.attrs["@events"].values()
            if text(ev.attrs.get("@name")) == "JH_HOME1F_TO_2F"
        ]
        if len(downstairs) == 1:
            command = downstairs[0].attrs["@pages"][0].attrs["@list"][0]
            report["return_xy"] = command.attrs["@parameters"][2:4]
        report["bedroom_geometry_updated"] = (
            pos == [4,4] and top_left == tile(238,1)
            and report.get("return_xy") == [4,5]
        )
        report["status"] = ("LAYOUT_HGSS_APPLIED" if report["bedroom_geometry_updated"]
                            else "OLD_OR_DIFFERENT_BEDROOM")
    except (KeyError, IndexError, OSError, TypeError, ValueError) as error:
        report["status"] = "MAP_READ_ERROR"
        report["error"] = str(error)

    try:
        proof = preview_proof(game)
        report["preview_integrity"] = "OK" if proof else "NO_PRIVATE_PREVIEW"
        report["safe_to_apply"] = bool(proof) and report["status"] == "OLD_OR_DIFFERENT_BEDROOM"
    except (OSError, ValueError, KeyError, TypeError) as error:
        report["full_integrity_error"] = str(error)
        try:
            scoped = scoped_bedroom_proof(game)
            if scoped:
                report["preview_integrity"] = "SCOPED_OK_GLOBAL_FILES_CHANGED"
                report["safe_to_apply"] = report["status"] == "OLD_OR_DIFFERENT_BEDROOM"
            else:
                report["preview_integrity"] = "FAILED"
                report["preview_integrity_error"] = str(error)
        except (OSError, ValueError, KeyError, TypeError) as local_error:
            report["preview_integrity"] = "FAILED"
            report["preview_integrity_error"] = str(local_error)
    report["next_action"] = (
        "Mapa HGSS aplicado; ainda faltam PNGs privados para móveis HGSS originais"
        if report["status"] == "LAYOUT_HGSS_APPLIED" and not
           report.get("private_hgss_status") == "private_art_compiled"
        else "Executar --apply com o Game.exe fechado" if report["safe_to_apply"]
        else "Verificar game_dir, logs e manifesto; não sobrescrever mapas sem auditoria"
    )
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, default=ROOT/"game")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path, default=OUTPUT)
    a = parser.parse_args(argv)
    report = inspect(ROOT, a.game_dir)
    if a.apply:
        if report["safe_to_apply"]:
            try:
                result = refresh_installed_bedroom(
                    a.game_dir, ROOT, allow_global_drift=True)
                report = inspect(ROOT, a.game_dir)
                report["repair"] = result
            except (OSError, KeyError, TypeError, ValueError) as error:
                report["repair_error"] = str(error)
        else:
            report["repair_error"] = "Não é seguro aplicar: " + report["status"] + \
                " / " + report.get("preview_integrity", "unknown")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if a.report:
        target = a.report.resolve()
        if target.is_relative_to((ROOT/".blue-work").resolve()) and target.parent.is_dir():
            target.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", "utf-8")
    return 0 if report["status"] == "LAYOUT_HGSS_APPLIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
