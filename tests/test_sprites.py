"""Sprites PNG/GIF: formato, segurança, backups e HTTP sem o jogo real."""
import base64
import json
import struct
import tempfile
import threading
import unittest
import zlib
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from main import (EditorError, build_handler, file_hash, save_sprite,
                  sprite_dimensions, sprite_metadata)


def make_png(w=1, h=1):
    def chunk(typ, body):
        return (struct.pack(">I", len(body)) + typ + body +
                struct.pack(">I", zlib.crc32(typ + body) & 0xffffffff))
    row = b"\x00" + b"\xff\x00\x00\xff" * w
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(row * h)) +
            chunk(b"IEND", b""))


GIF = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==")


class SpriteTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root = Path(self.dir.name)
        self.backups = self.root / ".backups"

    def save(self, data, filename="image.png", mode="static", expected="",
             species="TESTMON", kind="front"):
        return save_sprite(self.root, self.backups, species, kind, filename,
                           base64.b64encode(data).decode("ascii"), mode, expected)

    def test_png_static_and_four_variants(self):
        for variant in ("front", "back", "front-shiny", "back-shiny"):
            result = self.save(make_png(), kind=variant)
            self.assertEqual(result["file"]["mode"], "PNG estático")
            self.assertEqual(result["file"]["width"], 1)
            self.assertTrue((self.root / "Graphics" / "Pokemon" /
                             {"front":"Front","back":"Back","front-shiny":"Front shiny",
                              "back-shiny":"Back shiny"}[variant] / "TESTMON.png").is_file())
        self.assertEqual(sprite_dimensions(make_png(3,1), "png")[2], "PNG em faixa")

    def test_animated_strip_requires_mode_and_static_works(self):
        with self.assertRaises(EditorError):
            self.save(make_png(3,1))
        result = self.save(make_png(3,1),mode="animated")
        self.assertEqual(result["file"]["mode"], "PNG em faixa")
        self.assertEqual(result["file"]["width"], 3)

    def test_gif_replaces_png_and_creates_backup(self):
        result = self.save(make_png(),species="CHARIZARD_1")
        new = self.save(GIF,filename="animated.gif",mode="animated",
                        expected=result["file"]["hash"],species="CHARIZARD_1")
        self.assertEqual(new["file"]["format"],"gif")
        base=self.root/"Graphics"/"Pokemon"/"Front"
        self.assertTrue((base/"CHARIZARD_1.gif").exists())
        self.assertFalse((base/"CHARIZARD_1.png").exists())
        backups=list((self.backups/"sprites"/"Front"/"CHARIZARD_1.png").glob("*.bak"))
        self.assertEqual(len(backups),1)
        self.assertEqual(backups[0].read_bytes(),make_png())

    def test_conflict_does_not_overwrite_and_blocks_traversal(self):
        original=self.save(make_png())
        with self.assertRaises(EditorError) as ctx:
            self.save(make_png(2,2),expected="stale")
        self.assertEqual(ctx.exception.status,409)
        self.assertEqual(sprite_metadata(self.root,"TESTMON","front")["file"]["hash"],
                         original["file"]["hash"])
        for species in ("../TESTMON", "A/B", "..", "TESTMON.gif", "ß"):
            with self.assertRaises(EditorError):
                self.save(make_png(),species=species)
        with self.assertRaises(EditorError):
            self.save(make_png(),kind="anydir")
        with self.assertRaises(EditorError):
            self.save(b"not an image")
        with self.assertRaises(EditorError):
            self.save(GIF,filename="fake.png")
        with self.assertRaises(EditorError):
            self.save(GIF,filename="valid.gif",mode="static")

    def test_reject_corrupted_png_and_bad_gif(self):
        bad=bytearray(make_png())
        bad[29] ^= 0x40
        with self.assertRaises(EditorError):
            sprite_dimensions(bytes(bad),"png")
        with self.assertRaises(EditorError):
            sprite_dimensions(GIF[:-1],"gif")

    def test_symlinks_denied(self):
        outside=self.root/"outside.png"
        outside.write_bytes(make_png())
        folder=self.root/"Graphics"/"Pokemon"/"Front"
        folder.mkdir(parents=True)
        try:
            (folder/"TESTMON.png").symlink_to(outside)
        except OSError as error:
            if getattr(error, "winerror", None) == 1314:
                self.skipTest("Windows account cannot create symbolic links")
            raise
        with self.assertRaises(EditorError):
            sprite_metadata(self.root,"TESTMON","front")


class SpriteHTTPTest(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.server=ThreadingHTTPServer(("127.0.0.1",0),build_handler(self.root,self.root/"backups",0))
        self.server.RequestHandlerClass=build_handler(self.root,self.root/"backups",self.server.server_port)
        thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.origin="http://127.0.0.1:"+str(self.server.server_port)

    def test_png_get_info_upload_and_gif_content_type(self):
        url=self.origin+"/api/sprite-info?species=TESTMON&kind=front"
        with urlopen(url) as resp:
            self.assertFalse(json.load(resp)["exists"])
        data=make_png()
        body=json.dumps({"species":"TESTMON","kind":"front","filename":"static.png",
            "data":base64.b64encode(data).decode(),"mode":"static","expectedHash":""}).encode()
        with urlopen(Request(self.origin+"/api/sprite-upload",data=body,method="POST",
              headers={"Origin":self.origin,"X-Blue-Studio":"1",
                       "Content-Type":"application/json"})) as resp:
            self.assertEqual(json.load(resp)["file"]["format"],"png")
        with urlopen(self.origin+"/api/sprite?species=TESTMON&kind=front") as resp:
            self.assertEqual(resp.headers["Content-Type"],"image/png")
            self.assertEqual(resp.read(),data)
        with urlopen(self.origin+"/sprites.js") as resp:
            self.assertEqual(resp.status,200)
            self.assertIn("javascript",resp.headers.get("Content-Type",""))
        with self.assertRaises(HTTPError) as err:
            urlopen(self.origin+"/api/sprite?species=../nope&kind=front")
        self.assertEqual(err.exception.code,400)


if __name__ == "__main__":
    unittest.main()
