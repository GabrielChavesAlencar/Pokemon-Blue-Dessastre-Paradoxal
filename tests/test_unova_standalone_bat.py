"""RUN_UNOVA_MAPIDS.bat must work alone from Downloads, without repository files."""
from __future__ import annotations

import ast
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
BAT=ROOT/"RUN_UNOVA_MAPIDS.bat"
NEEDED=(
 "scripts/regions/unova_auto_mapids.py",
 "scripts/regions/audit_unova_a04_mapids.py",
 "scripts/regions/audit_unova_a05_candidates.py",
 "scripts/regions/audit_sinnoh_b05_mapid_planning.py",
 "server/ruby_marshal.py",
 "data/regions/unova-a05-mapid-candidates.json",
 "data/regions/sinnoh-b05-mapid-planning.json",
 "data/regions/sinnoh-b01-actual-native.json",
 "data/regions/sinnoh-b03-installer-evidence.json",
 "data/regions/unova-u03-areas.json",
)


def unpack():
    bat=BAT.read_text(encoding="utf-8-sig")
    marker="::BEGIN_UNOVA_PAYLOAD"
    if bat.count(marker)!=1:
        raise ValueError("embedded bundle marker missing/duplicated")
    prefix,source=bat.split(marker,1)
    source=source.lstrip("\r\n")
    tree=ast.parse(source)
    decl=next(node for node in tree.body
              if isinstance(node,ast.Assign) and
              any(isinstance(target,ast.Name) and target.id=="BUNDLE_B64"
                  for target in node.targets))
    payload=ast.literal_eval(decl.value)
    b64="".join(payload)
    data=base64.b64decode(b64,validate=True)
    return prefix,source,json.loads(data.decode("utf-8"))


class StandaloneBatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prefix,cls.python_code,cls.files=unpack()

    def test_01_batch_launches_own_file_not_external_scripts(self):
        self.assertIn('"%~f0"',self.prefix)
        self.assertNotIn("%PYRUN% scripts\\regions\\unova_auto_mapids.py",self.prefix)
        self.assertIn("python",self.prefix.casefold())
        self.assertIn("exit /b",self.prefix)

    def test_02_contains_all_ten_dependency_files(self):
        self.assertEqual(set(self.files),set(NEEDED))

    def test_03_embedded_files_same_as_repository(self):
        for name,source in self.files.items():
            with self.subTest(name=name):
                self.assertEqual(source,(ROOT/name).read_text("utf-8"))

    def test_04_embedded_python_compiles_and_cache_is_stable(self):
        compile(self.python_code,str(BAT),"exec")
        for name,source in self.files.items():
            if name.endswith(".py"):
                compile(source,name,"exec")

    def test_05_bat_has_no_powershell_commands_or_downloads(self):
        self.assertNotIn("powershell.exe",self.prefix.casefold())
        self.assertNotIn("powershell -",self.prefix.casefold())
        self.assertNotIn("curl ",self.prefix.casefold())
        self.assertNotIn("bitsadmin",self.prefix.casefold())
        self.assertNotIn("git clone",self.prefix.casefold())

    def test_06_bat_writes_no_game_saves_or_maps(self):
        self.assertIn("data/regions/sinnoh-b05-mapid-planning.json",self.files)
        self.assertNotIn("game/Data",self.prefix)
        self.assertIn("read_only",self.files["scripts/regions/audit_unova_a04_mapids.py"].casefold()
                      .replace("-","_").replace(" ","_"))

    def test_07_python_payload_from_downloads_without_repo(self):
        # Run the actual embedded Python tail, not the existing repo's scripts.
        from server.ruby_marshal import RubyObject
        from stage import serialize
        with tempfile.TemporaryDirectory(prefix="portable-unova-") as root:
            temp=Path(root)
            downloads=temp/"Downloads"
            downloads.mkdir()
            standalone_bat=downloads/"RUN_UNOVA_MAPIDS.bat"
            shutil.copyfile(BAT,standalone_bat)
            appdata=temp/"AppData/Local"
            game=appdata/"PokemonBlueDessastreParadoxal/game"
            data=game/"Data"
            data.mkdir(parents=True)
            (game/"Game.exe").write_bytes(b"synthetic test exe")
            infos={}
            for mid in range(100,124):
                infos[mid]=RubyObject("RPG::MapInfo",
                        {"@name":f"Map {mid}".encode("utf-8")})
                (data/f"Map{mid:03d}.rxdata").write_bytes(f"fake{mid}".encode())
            (data/"MapInfos.rxdata").write_bytes(serialize(infos))
            before=(data/"MapInfos.rxdata").read_bytes()
            # BAT's -c loader reads BAT content and runs embedded tail.
            loader=("import pathlib,sys;"
                    "p=pathlib.Path(sys.argv[1]);"
                    "s=p.read_text(encoding='utf-8-sig');"
                    "m='::'+'BEGIN_UNOVA_PAYLOAD';"
                    "a,b,c=s.partition(m);"
                    "assert b;"
                    "exec(compile(c.lstrip('\\r\\n'),str(p),'exec'),"
                    "{'__name__':'__main__','__file__':str(p)})")
            env=dict(os.environ,LOCALAPPDATA=str(appdata),
                     USERPROFILE=str(temp/"profile"),
                     APPDATA=str(temp/"roaming"))
            result=subprocess.run(
                [sys.executable,"-c",loader,str(standalone_bat)],
                cwd=downloads,env=env,capture_output=True,text=True,timeout=35)
            self.assertEqual(result.returncode,0, result.stderr+"\n"+result.stdout)
            self.assertIn("AUTO_A04_A05_DONE_NOT_NATIVE_APPROVED",result.stdout)
            self.assertEqual((data/"MapInfos.rxdata").read_bytes(),before)
            self.assertFalse((game/".blue-work").exists())
            cache=appdata/"PokemonBlueUnovaMapids"
            reports=list(cache.glob("bundle-*/.blue-work/unova/audit/LEIA_AQUI_UNOVA_MAPIDS.txt"))
            self.assertEqual(len(reports),1)
            summary=reports[0].read_text("utf-8-sig")
            self.assertIn("B04 V2",summary)
            self.assertIn("A05",summary)
            self.assertIn("NENHUM MapID",summary)
            self.assertTrue(list(cache.glob("bundle-*/.blue-work/unova/audit/a04-mapids-*.json")))
            self.assertTrue(list(cache.glob("bundle-*/.blue-work/unova/audit/a05-candidates-*.json")))


if __name__=="__main__":
    unittest.main()
