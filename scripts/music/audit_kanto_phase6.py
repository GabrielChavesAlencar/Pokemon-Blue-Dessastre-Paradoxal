"""F6 soundtrack integrity + codec audit; never modifies music or game saves.

Catalog blobs and SHA are checked by install_kanto_music.audit(). If ffprobe and
ffmpeg are available, this additionally checks *actual MP3 decoding* (not the
ability to hear it from mkxp-z or seamless in-game loops). The report is explicit
about the distinction, on a per-track basis.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

try:
    from scripts.music import compile_kanto_music as compile_music
    from scripts.music import install_kanto_music
except ModuleNotFoundError:
    import compile_kanto_music as compile_music
    import install_kanto_music

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / ".blue-work/kanto-music-phase6-audio.json"
# These source areas are absent, not merely unfinished events, from the
# 142-map imported Kanto source currently registered. A new source map
# requires revisiting the policy rather than silently changing its status.
ABSENT_KANTO_AREAS = {
    38: "LAVENDER", 39: "POKEMON_TOWER", 41: "ROCKET_GAME_CORNER",
    45: "ROCKET_HIDEOUT", 57: "NET_CENTER",
    59: "SEVII",
}


def enabled_numbers(root: Path) -> set[int]:
    return compile_music.approved_audio_track_numbers(root)


def classify_catalog(root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rules = compile_music.load_json(root / "data/kanto-music-rules.json")
    source = compile_music.load_json(root / "data/regions/kanto-source.json")
    symbols = list(source["maps"].values())
    for n, marker in ABSENT_KANTO_AREAS.items():
        if any(marker in symbol for symbol in symbols):
            raise ValueError(f"Kanto missing-map status outdated for soundtrack {n}")
    active = enabled_numbers(root)
    by_number: dict[int, list[str]] = {}
    for field, key in (("maps", "map"), ("transport", "mode"), ("battles", "category"),
                       ("events", "event"), ("scenes", "scene")):
        for entry in rules[field]:
            by_number.setdefault(entry["track"], []).append(
                field + ":" + str(entry[key]) + (":enabled" if entry["enabled"] else ":pending")
            )
    rows = []
    for item in sorted(manifest["files"], key=lambda e: e["number"]):
        n = item["number"]
        rows.append({
            "number": n, "kind": item["kind"], "filename": item["filename"],
            "bytes": item["bytes"], "git_blob_sha": item["git_blob_sha"],
            "status": ("VINCULADA" if n in active else
                       "MAPA_AUSENTE" if n in ABSENT_KANTO_AREAS else "PENDENTE_EVENTO"),
            "reason": ("associated with audited Kanto runtime rule" if n in active else
                       "destination is absent from imported 142 Kanto maps"
                       if n in ABSENT_KANTO_AREAS else
                       "event or music segment requires implementation/audit"),
            "bindings": by_number.get(n, []),
            "engine_playback": "BLOQUEADA_AMBIENTE",
            "codec_probe": "BLOQUEADA_AMBIENTE",
            "decoder_sample_rate_hz": None,
            "decoder_channels": None,
            "decoder_duration_seconds": None,
        })
    assert len(rows) == 64
    assert {row["number"] for row in rows if row["status"] == "VINCULADA"} == active
    return rows


def probe_audio(path: Path, *, timeout: int = 45, ffprobe: str = "ffprobe",
                ffmpeg: str = "ffmpeg") -> dict[str, Any]:
    """Prove MP3 codec/duration and decode the entire file into a null output."""
    info = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,codec_name,sample_rate,channels",
         "-of", "json", str(path)],
        capture_output=True, text=True, timeout=timeout, check=False,
    )
    if info.returncode != 0:
        raise ValueError("ffprobe failed: " + info.stderr.strip()[-300:])
    try:
        data = json.loads(info.stdout)
        streams = [s for s in data.get("streams", [])
                   if s.get("codec_type") == "audio"]
        if len(streams) != 1:
            raise ValueError("expected one audio stream")
        stream = streams[0]
        codec = stream["codec_name"]
        channels = int(stream["channels"])
        sample_rate = int(stream["sample_rate"])
        duration = float(data["format"]["duration"])
        if codec != "mp3" or not (1 <= channels <= 2) or not (
                8000 <= sample_rate <= 96000) or not (0.1 <= duration <= 3600):
            raise ValueError("invalid MPEG codec/channel/sample-rate/duration")
    except (KeyError, TypeError, OverflowError) as ex:
        raise ValueError("invalid ffprobe audio stream metadata") from ex
    # -xerror aborts on a corrupt MP3 decode, instead of silently dropping
    # damaged frames. The full file, not just a header/small sample, is read.
    decode = subprocess.run(
        [ffmpeg, "-nostdin", "-hide_banner", "-v", "error", "-xerror",
         "-i", str(path), "-map", "0:a:0", "-f", "null", "-"],
        capture_output=True, text=True, timeout=timeout, check=False,
    )
    if decode.returncode != 0:
        raise ValueError("full MP3 decode failed: " + decode.stderr.strip()[-300:])
    return {"codec": codec, "channels": channels,
            "sample_rate_hz": sample_rate, "duration_seconds": round(duration, 3),
            "decode": "PASS_FULL_MP3_DECODE"}


def audit(root: Path = ROOT, *, decoder: str = "auto",
          ffprobe: str | None = None, ffmpeg: str | None = None) -> dict[str, Any]:
    if decoder not in ("off", "auto", "required"):
        raise ValueError("decoder must be off, auto or required")
    catalog = install_kanto_music.audit(root / "data/kanto-music.json", root)
    rows = classify_catalog(root, catalog["manifest"])
    probe_bin = ffprobe or shutil.which("ffprobe")
    decode_bin = ffmpeg or shutil.which("ffmpeg")
    has_decoder = bool(probe_bin and decode_bin)
    if decoder == "required" and not has_decoder:
        raise RuntimeError("BLOCKED_ENV: ffprobe + ffmpeg required for F6 decoder CI")
    failures = []
    if has_decoder and decoder != "off":
        for row in rows:
            path = root / ("assets/music/kanto/" + row["kind"] + "/" + row["filename"])
            try:
                result = probe_audio(path, ffprobe=probe_bin, ffmpeg=decode_bin)
                row["codec_probe"] = result["decode"]
                row["decoder_sample_rate_hz"] = result["sample_rate_hz"]
                row["decoder_channels"] = result["channels"]
                row["decoder_duration_seconds"] = result["duration_seconds"]
            except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
                row["codec_probe"] = "FAILED_CODEC_OR_DECODE"
                row["decoder_error"] = str(exc)[:350]
                failures.append(row["number"])
    status = "PASS" if not failures and (has_decoder or decoder == "off") else (
        "BLOCKED_ENV" if not has_decoder else "FAIL")
    report = {
        "schema": 1, "phase": 6, "status": status,
        "source_files_sha_pass": 64,
        "source_total_bytes": catalog["bytes"],
        "catalog_bgm": catalog["BGM"], "catalog_me": catalog["ME"],
        "approved_tracks": sum(row["status"] == "VINCULADA" for row in rows),
        "approved_bgm": sum(x["kind"] == "BGM" and x["status"] == "VINCULADA" for x in rows),
        "approved_me": sum(x["kind"] == "ME" and x["status"] == "VINCULADA" for x in rows),
        "pending_tracks": sum(row["status"] != "VINCULADA" for row in rows),
        "pending_events": sum(row["status"] == "PENDENTE_EVENTO" for row in rows),
        "missing_map_tracks": sum(row["status"] == "MAPA_AUSENTE" for row in rows),
        "codec_full_decode_pass": sum(x["codec_probe"] == "PASS_FULL_MP3_DECODE" for x in rows),
        "codec_failures": failures,
        "decoder_mode": decoder, "decoder_available": has_decoder,
        "native_engine_scope_checked": False,
        "audible_windows_acceptance": "BLOCKED_ENV",
        "loop_fade_listening_acceptance": "BLOCKED_ENV",
        "saves_were_modified": False, "decades_music_preferences_modified": False,
        "tracks": rows,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decoder", choices=("off", "auto", "required"),
                        default="auto")
    parser.add_argument("--output", type=Path, default=REPORT)
    args = parser.parse_args()
    output = args.output.resolve()
    # CI reports may only live under the ignored .blue-work directory.
    work = (ROOT / ".blue-work").resolve()
    if output == work or not output.is_relative_to(work):
        parser.error("phase 6 report must be under .blue-work")
    try:
        result = audit(decoder=args.decoder)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n",
                          encoding="utf-8")
        print(json.dumps({k: v for k, v in result.items() if k != "tracks"},
                         indent=2, ensure_ascii=False))
        for row in result["tracks"]:
            print(f"TRACK_{row['number']:02d}\t{row['kind']}\t{row['status']}\t"
                  f"{row['codec_probe']}\t{row['decoder_duration_seconds']}\t"
                  f"{row['filename']}")
        print("TRACK_MATRIX=" + str(output))
        return 0 if result["status"] != "FAIL" and (
            args.decoder != "required" or result["status"] == "PASS") else 2
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as error:
        print("KANTO_MUSIC_F6_ERROR=" + str(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
