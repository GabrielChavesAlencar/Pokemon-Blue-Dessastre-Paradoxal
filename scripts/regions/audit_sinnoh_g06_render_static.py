#!/usr/bin/env python3
"""G06: static Sinnoh rendering/PNG audit; synthetic bytes only on GitHub.

The native PNGs, donor graphics and Game.exe are NOT in this repository.
A metadata-only report must never claim that the 14 real images were inspected.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
PNG = b"\x89PNG\r\n\x1a\n"
MAX_PNG_BYTES = 32_000_000
MAX_WIDTH = 16384
MAX_HEIGHT = 100000
MAX_PIXELS = 40_000_000
MAX_DECODED = 128 * 1024 * 1024
MAX_CHUNKS = 1024
COLOUR_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
VALID_DEPTHS = {0: (1, 2, 4, 8, 16), 2: (8, 16),
                3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}
ADAM7 = ((0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8),
         (2, 0, 4, 4), (0, 2, 2, 4), (1, 0, 2, 2),
         (0, 1, 1, 2))


def blocked(reason: str) -> None:
    raise ValueError("SINNOH_G06_BLOCKED: " + reason)


def load_public(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
        blocked("manifesto publico ausente, inseguro ou excessivamente grande")
    result = json.loads(path.read_text(encoding="utf-8"))
    if type(result) is not dict:
        blocked("manifesto publico deve ser objeto")
    return result


def risk(width: int, height: int) -> dict:
    if (type(width) is not int or type(height) is not int or
            width <= 0 or height <= 0 or width * height > MAX_PIXELS):
        blocked("dimensoes nao podem ser avaliadas")
    return {
        "width": width, "height": height,
        "pixels": width * height,
        "estimated_rgba8_mib": round(width * height * 4 / 1048576, 2),
        "height_exceeds_conservative_16384_side_check": height > 16384,
        "gpu_runtime_compatibility_confirmed": False,
        "needs_native_render_test": True,
    }


def _passes(width: int, height: int, channels: int, depth: int,
            interlace: int) -> list[tuple[int, int]]:
    grids = ADAM7 if interlace else ((0, 0, 1, 1),)
    result = []
    for startx, starty, stepx, stepy in grids:
        pw = max(0, (width - startx + stepx - 1) // stepx)
        ph = max(0, (height - starty + stepy - 1) // stepy)
        if pw and ph:
            scan_bytes = (pw * channels * depth + 7) // 8
            result.append((scan_bytes + 1, ph))
    return result


def inspect_png(raw: bytes) -> dict:
    """Validate PNG chunks, CRC, raster zlib stream and per-row filter bytes.

    No graphics are decoded to pixels or executed. Memory is bounded by a
    64-KiB inflate chunk, even for 70,000-pixel-high PNGs.
    """
    if type(raw) is not bytes or len(raw) > MAX_PNG_BYTES or not raw.startswith(PNG):
        blocked("PNG invalido, ausente ou acima do limite de tamanho")
    pos = len(PNG)
    ihdr = None
    plte_count = None
    has_idat = False
    after_idat = False
    saw_iend = False
    chunks = 0
    compressed = []
    while pos < len(raw):
        chunks += 1
        if chunks > MAX_CHUNKS or len(raw) - pos < 12:
            blocked("PNG com muitos chunks ou cabecalho truncado")
        n = struct.unpack_from(">I", raw, pos)[0]
        tag = raw[pos + 4:pos + 8]
        end = pos + 8 + n
        if n > MAX_PNG_BYTES or end + 4 > len(raw):
            blocked("chunk PNG truncado ou excessivamente grande")
        if len(tag) != 4 or any(not (65 <= c <= 90 or 97 <= c <= 122)
                                for c in tag) or not 65 <= tag[2] <= 90:
            blocked("tipo PNG nao canonico ou reserved bit invalido")
        content = raw[pos + 8:end]
        actual_crc = struct.unpack_from(">I", raw, end)[0]
        if zlib.crc32(tag + content) & 0xFFFFFFFF != actual_crc:
            blocked("CRC do PNG divergente")
        if chunks == 1 and (tag != b"IHDR" or n != 13):
            blocked("PNG precisa iniciar com IHDR")
        if tag == b"IHDR":
            if ihdr is not None or chunks != 1 or n != 13:
                blocked("IHDR duplicado, invalido ou fora de ordem")
            width, height, depth, colour, compression, filt, interlace = (
                struct.unpack(">IIBBBBB", content))
            if (not 1 <= width <= MAX_WIDTH or
                    not 1 <= height <= MAX_HEIGHT or
                    width * height > MAX_PIXELS or
                    depth not in VALID_DEPTHS.get(colour, ()) or
                    compression != 0 or filt != 0 or interlace not in (0, 1)):
                blocked("dimensoes, profundidade, cores ou compressao PNG invalidas")
            ihdr = (width, height, depth, colour, interlace)
        elif tag == b"PLTE":
            if ihdr is None or plte_count is not None or has_idat:
                blocked("paleta ausente de ordem ou duplicada")
            if ihdr[3] in (0, 4) or n == 0 or n % 3 != 0 or n > 768:
                blocked("paleta PNG invalida para tipo de cor")
            plte_count = n // 3
            if ihdr[3] == 3 and plte_count > 1 << ihdr[2]:
                blocked("paleta indexada excede profundidade de cor")
        elif tag == b"IDAT":
            if ihdr is None or after_idat:
                blocked("IDAT ausente de ordem ou fragmentado por outro chunk")
            has_idat = True
            compressed.append(content)
        elif tag == b"IEND":
            if n != 0 or not has_idat or end + 4 != len(raw):
                blocked("IEND invalido ou bytes apos o fim do PNG")
            saw_iend = True
            break
        elif tag[0] & 32 == 0:
            blocked("chunk critico PNG desconhecido")
        if has_idat and tag != b"IDAT":
            after_idat = True
        pos = end + 4
    if ihdr is None or not has_idat or not saw_iend:
        blocked("PNG incompleto sem IHDR/IDAT/IEND")
    width, height, depth, colour, interlace = ihdr
    if colour == 3 and plte_count is None:
        blocked("PNG indexado sem PLTE")
    pass_rows = _passes(width, height, COLOUR_CHANNELS[colour], depth, interlace)
    wanted = sum(row * count for row, count in pass_rows)
    if wanted > MAX_DECODED:
        blocked("scanlines PNG ultrapassam memoria de auditoria")
    decoder = zlib.decompressobj()
    pass_index = row_index = offset_in_row = total = 0

    def feed(decoded: bytes) -> None:
        nonlocal pass_index, row_index, offset_in_row, total
        index = 0
        total += len(decoded)
        if total > wanted:
            blocked("zlib PNG expandiu mais bytes que as dimensoes permitem")
        while index < len(decoded):
            if pass_index == len(pass_rows):
                blocked("scanlines excedentes")
            size, count = pass_rows[pass_index]
            if offset_in_row == 0 and decoded[index] not in (0, 1, 2, 3, 4):
                blocked("filtro de scanline PNG invalido")
            take = min(size - offset_in_row, len(decoded) - index)
            offset_in_row += take
            index += take
            if offset_in_row == size:
                offset_in_row = 0
                row_index += 1
                if row_index == count:
                    pass_index += 1
                    row_index = 0

    for data in compressed:
        for start in range(0, len(data), 65536):
            pending = data[start:start + 65536]
            while pending:
                try:
                    decoded = decoder.decompress(pending, 65536)
                except zlib.error:
                    blocked("zlib do PNG corrompido")
                feed(decoded)
                if decoder.unused_data:
                    blocked("dados comprimidos extras apos o fim do PNG")
                previous_len = len(pending)
                pending = decoder.unconsumed_tail
                if not decoded and pending and len(pending) >= previous_len:
                    blocked("zlib PNG nao avanca")
    if not decoder.eof or total != wanted or pass_index != len(pass_rows):
        blocked("raster PNG incompleto ou quantidade de scanlines incorreta")
    return {
        "width": width, "height": height, "bit_depth": depth,
        "colour_type": colour, "interlaced": bool(interlace),
        "crc_and_zlib_valid": True,
        "decoded_scanline_bytes": total,
        "chunk_count": chunks,
        "high_texture_side_risk": height > 16384 or width > 16384,
        "game_exe_rendered": False,
    }


def audit_metadata(b01: dict, b06: dict, b07: dict, b08: dict) -> dict:
    if (b01.get("stage") != "B01" or b06.get("stage") != "B06" or
            b07.get("stage") != "B07" or b08.get("stage") != "B08"):
        blocked("encadeamento dos manifestos B01/B06/B07/B08 invalido")
    if (type(b01.get("native_tileset_count")) is not int or
            b01["native_tileset_count"] != 70 or
            b01.get("native_physical_map_count") != 648):
        blocked("baseline B01 de tilesets alterado")
    if (b01.get("donor_tilesets") !=
            {"1": "OutsideWorld2.7", "31": "SinnohCompleteTileset"} or
            b06.get("source_tileset_references") != [1, 31] or
            b07.get("required_source_tilesets") != [1, 31] or
            b08.get("source_tilesets_to_new_indices") != [1, 31]):
        blocked("proveniencia dos dois tilesets doadores mudou")
    if (b07.get("native_tileset_strategy") != "APPEND_TO_SNAPSHOT_COPY_ONLY" or
            b01.get("tilesets_sha256") != b07.get("native_tilesets_sha256") or
            b01.get("tilesets_sha256") != b08.get("native_tilesets_sha256") or
            b01.get("mapinfos_sha256") != b08.get("native_mapinfos_sha256") or
            b07.get("source_zip_sha256") != b08.get("b07_source_sha256")):
        blocked("hashes da base ou politica de anexacao divergentes")
    if (b07.get("candidate_terrain_destinations") != list(range(442, 496)) or
            b07.get("excluded_empty_destinations") != list(range(496, 518)) or
            b08.get("expected_staged_terrain_ids") != list(range(442, 496)) or
            b08.get("excluded_empty_ids") != list(range(496, 518)) or
            b08.get("expected_staged_maps") != 54 or
            b08.get("expected_pngs") != 14 or
            b08.get("expected_nonzero_terrain_cells") != 484722):
        blocked("contagens de geometrias e PNGs nao conferem")
    for name, doc, keys in (
        ("B07", b07, ("rights_per_asset_verified", "redistribution_approved",
                      "r07_complete", "r08_complete", "r09_complete",
                      "can_install_into_game", "native_game_exe_tested",
                      "joiplay_tested")),
        ("B08", b08, ("rights_per_asset_verified", "has_live_stage_evidence",
                      "r07_complete", "r08_complete", "r09_complete",
                      "can_install", "can_mark_gameplay"))):
        if any(doc.get(key) is not False for key in keys):
            blocked("manifesto " + name + " afirma aprovacao sem evidencia")
    if (b08.get("must_verify_png_chunks_references_and_native_tileset_append")
            is not True or
            b08.get("overlay_is_a_non_runnable_private_copy") is not True):
        blocked("B08 deixou de exigir PNGs verificados no stage privado")
    # B01 counts actual records but does NOT expose an independently checked
    # serialized list index 0. Thus 71/72 is a conditional expectation only.
    return {
        "schema": 1, "region": "SINNOH", "stage": "G06",
        "status": "STATIC_RENDER_METADATA_RECONCILED_PNG_BYTES_NOT_AVAILABLE",
        "baseline_native_tileset_record_count": 70,
        "source_tileset_ids": [1, 31],
        "source_tileset_names": [b01["donor_tilesets"]["1"], b01["donor_tilesets"]["31"]],
        "expected_private_tileset_indices_if_zero_slot_present": [71, 72],
        "private_tileset_indices_verified_against_native_serialized_table": False,
        "expected_geometry_map_count": 54,
        "expected_private_png_count": 14,
        "real_png_bytes_inspected_on_github": 0,
        "real_png_crc_zlib_verified_on_github": False,
        "real_png_references_checked_against_bytes_on_github": False,
        "b08_local_byte_level_audit_required": True,
        "tall_png_dimensions_are_reported_not_publicly_reverified": True,
        "tall_png_render_risks": [
            {"source_tileset_name": "OutsideWorld2.7", **risk(256, 50000)},
            {"source_tileset_name": "SinnohCompleteTileset", **risk(256, 70000)},
        ],
        "rendering_in_Game_exe_verified": False,
        "android_joiplay_verified": False,
        "rights_per_asset_verified": False,
        "r07_complete": False, "r08_complete": False, "r09_complete": False,
        "can_install_live_game": False, "phase_b_approved": 0,
        "phase_c_approved": 0, "phase_d_approved": 0,
        "next_gate": "B08 local must validate 14 real PNG files and tileset table; B10/B11 native isolated render tests pending",
    }


def run(root: Path = ROOT) -> dict:
    root = Path(root)
    return audit_metadata(*[load_public(root / ("data/regions/" + name))
                            for name in ("sinnoh-b01-actual-native.json",
                                         "sinnoh-b06-technical-candidate.json",
                                         "sinnoh-b07-private-stage.json",
                                         "sinnoh-b08-private-qa.json")])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        print(json.dumps(run(), indent=2, ensure_ascii=False))
        return 0
    except (OSError, UnicodeError, ValueError, TypeError, KeyError):
        print("SINNOH_G06_BLOCKED: metadados de renderizacao ausentes ou invalidos",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
