"""F6 integration matrix, audio codec checks, honest native/manual statuses."""
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.music import audit_kanto_phase6 as phase6
from scripts.music import compile_kanto_music as compiler

ROOT = Path(__file__).resolve().parents[1]


class KantoPhaseSixAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "data/kanto-music.json").read_text("utf-8"))

    def test_complete_catalog_matrix_never_claims_audible_or_loop_acceptance(self):
        rows=phase6.classify_catalog(ROOT,self.manifest)
        self.assertEqual(len(rows),64)
        self.assertEqual(sum(x["status"]=="VINCULADA" for x in rows),38)
        self.assertEqual(sum(x["status"]=="PENDENTE_EVENTO" for x in rows),20)
        self.assertEqual(sum(x["status"]=="MAPA_AUSENTE" for x in rows),6)
        self.assertEqual({x["number"] for x in rows if x["status"]=="MAPA_AUSENTE"},
                         set(phase6.ABSENT_KANTO_AREAS))
        self.assertEqual(sum(x["kind"]=="ME" and x["status"]=="VINCULADA" for x in rows),6)
        self.assertEqual(sum(x["kind"]=="BGM" and x["status"]=="VINCULADA" for x in rows),32)
        self.assertEqual({x["number"] for x in rows if x["status"]=="VINCULADA"},
                         compiler.approved_audio_track_numbers(ROOT))
        self.assertTrue(all(x["engine_playback"]=="BLOQUEADA_AMBIENTE" for x in rows))
        self.assertTrue(all(x["codec_probe"]=="BLOQUEADA_AMBIENTE" for x in rows))
        self.assertEqual({x["number"] for x in rows},
                         set(range(1,61))|{70,71,72,73})
        self.assertEqual(len({x["filename"] for x in rows}),64)
        self.assertTrue(all(x["git_blob_sha"] and x["bindings"] is not None for x in rows))

    def test_unknown_cinematics_and_ME_cannot_be_pretended_active(self):
        rows={r["number"]:r for r in phase6.classify_catalog(ROOT,self.manifest)}
        for n in (1,2,4,5,16,20,22,24,26,33,42,43,44,46,49,51,58,60,71,73):
            self.assertEqual(rows[n]["status"],"PENDENTE_EVENTO")
        self.assertEqual(rows[72]["status"],"VINCULADA")
        self.assertEqual(rows[70]["status"],"VINCULADA")
        self.assertEqual(rows[29]["status"],"VINCULADA")
        self.assertEqual(rows[31]["status"],"VINCULADA")

    @staticmethod
    def result(code=0,stdout="",stderr=""):
        return SimpleNamespace(returncode=code,stdout=stdout,stderr=stderr)

    def test_full_decoder_probe_reports_actual_codec_channels_and_duration(self):
        def fake_run(cmd,**kwargs):
            if cmd[0]=="fake-ffprobe":
                return self.result(stdout=json.dumps({
                    "streams":[{"codec_type":"audio","codec_name":"mp3",
                                "channels":2,"sample_rate":"44100"}],
                    "format":{"duration":"83.751"}}))
            if cmd[0]=="fake-ffmpeg":
                return self.result()
            raise AssertionError("unexpected command "+repr(cmd))
        with patch.object(phase6.subprocess,"run",side_effect=fake_run) as run:
            result=phase6.probe_audio(Path("synthetic.mp3"),
                                      ffprobe="fake-ffprobe",ffmpeg="fake-ffmpeg")
        self.assertEqual(result["decode"],"PASS_FULL_MP3_DECODE")
        self.assertEqual(result["sample_rate_hz"],44100)
        self.assertEqual(result["channels"],2)
        self.assertEqual(result["duration_seconds"],83.751)
        commands=[call.args[0] for call in run.call_args_list]
        self.assertEqual(len(commands),2)
        self.assertIn("-xerror",commands[1])
        self.assertEqual(commands[1][-2:],["null","-"])
        self.assertNotIn("-t",commands[1])  # full, not a short sample

    def test_decoder_rejects_non_mp3_or_invalid_audio_stream(self):
        for fake in ({"streams":[{"codec_type":"audio","codec_name":"aac",
                                  "channels":2,"sample_rate":"44100"}],
                      "format":{"duration":"20.0"}},
                     {"streams":[],"format":{"duration":"20.0"}},
                     {"streams":[{"codec_type":"audio","codec_name":"mp3",
                                  "channels":0,"sample_rate":"0"}],
                      "format":{"duration":"20.0"}}):
            with patch.object(phase6.subprocess,"run",
                              return_value=self.result(stdout=json.dumps(fake))):
                with self.assertRaises(ValueError):
                    phase6.probe_audio(Path("wrong.mp3"),
                                       ffprobe="fake-ffprobe",ffmpeg="fake-ffmpeg")

    def test_decoder_rejects_actual_ffmpeg_decode_error(self):
        probe=self.result(stdout=json.dumps({
            "streams":[{"codec_type":"audio","codec_name":"mp3",
                        "channels":2,"sample_rate":"44100"}],
            "format":{"duration":"99.6"}}))
        decode=self.result(code=1,stderr="Invalid data found")
        with patch.object(phase6.subprocess,"run",side_effect=[probe,decode]):
            with self.assertRaisesRegex(ValueError,"full MP3 decode failed"):
                phase6.probe_audio(Path("bad.mp3"),
                                   ffprobe="fake-ffprobe",ffmpeg="fake-ffmpeg")

    def test_no_decoder_never_marks_64_files_as_playback_tested(self):
        catalog={"bytes":135768381,"BGM":50,"ME":14,"manifest":self.manifest}
        with patch.object(phase6.install_kanto_music,"audit",return_value=catalog), \
             patch.object(phase6.shutil,"which",return_value=None):
            data=phase6.audit(ROOT,decoder="auto")
            self.assertEqual(data["status"],"BLOCKED_ENV")
            self.assertEqual(data["codec_full_decode_pass"],0)
            self.assertEqual(data["approved_tracks"],38)
            self.assertEqual(data["audible_windows_acceptance"],"BLOCKED_ENV")
            self.assertFalse(data["native_engine_scope_checked"])
            self.assertFalse(data["saves_were_modified"])
            with self.assertRaisesRegex(RuntimeError,"BLOCKED_ENV"):
                phase6.audit(ROOT,decoder="required")

    def test_required_decoder_explicitly_marks_failed_track(self):
        catalog={"bytes":135768381,"BGM":50,"ME":14,"manifest":self.manifest}
        def fail_track(path,**kwargs):
            if "1-03." in str(path):
                raise ValueError("corrupt MP3")
            return {"decode":"PASS_FULL_MP3_DECODE","channels":2,
                    "sample_rate_hz":44100,"duration_seconds":91.2}
        with patch.object(phase6.install_kanto_music,"audit",return_value=catalog), \
             patch.object(phase6.shutil,"which",return_value="/tmp/ffmpeg-fake"), \
             patch.object(phase6,"probe_audio",side_effect=fail_track):
            data=phase6.audit(ROOT,decoder="required")
        self.assertEqual(data["status"],"FAIL")
        self.assertEqual(data["codec_full_decode_pass"],63)
        self.assertEqual(data["codec_failures"],[3])
        self.assertEqual(next(row for row in data["tracks"] if row["number"]==3)
                         ["codec_probe"],"FAILED_CODEC_OR_DECODE")


if __name__ == "__main__":
    unittest.main()
