"""Regression: dedicated species moves editor (no assets from Decades required)."""
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"server"))
from main import (build_handler, pbs_path, read_text, sections_in,
                  section_lines, file_hash, save_section)
from moves_editor import (catalog, detail, save, replace_fields, MoveEditorError)


class MoveFixture(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        pbs=self.root/"PBS";pbs.mkdir()
        self.backups=self.root/"backups"
        self.original=("\ufeff# source\r\n#--------------------\r\n[ALPHAMON]\r\n"
          "Name = Alpha Mon\r\nTypes = WATER\r\n"
          "Moves = 1,TACKLE,10,BITE\r\n"
          "TutorMoves = PROTECT\r\nEggMoves = BITE\r\n"
          "BaseStats = 80,80,80,80,80,80\r\n"
          "#--------------------\r\n[BETAMON]\r\nName = Beta Mon\r\n"
          "Moves = 5,TACKLE\r\nTutorMoves = PROTECT\r\n")
        (pbs/"pokemon.txt").write_bytes(self.original.encode("utf-8"))
        (pbs/"pokemon_forms.txt").write_text(
          "[ALPHAMON,1]\nFormName = Mega Alpha\nBaseStats = 90,90,90,90,90,90\n",encoding="utf-8")
        (pbs/"pokemon_base_Gen_9_Pack.txt").write_text(
          "[GAMMAMON]\nName = Gamma Mon\nMoves = 1,TACKLE\n",encoding="utf-8")
        (pbs/"pokemon_metrics.txt").write_text("[ALPHAMON]\nFrontSprite = 0,0\n",encoding="utf-8")
        (pbs/"moves.txt").write_text(
          "[TACKLE]\nName = Tackle\n[BITE]\nName = Bite\n"
          "[PROTECT]\nName = Protect\n[FLAMETHROWER]\nName = Flamethrower\n",
          encoding="utf-8")
        (pbs/"moves_Gen_9_Pack.txt").write_text(
          "[CHILLINGWATER]\nName = Chilling Water\n",encoding="utf-8")
        self.functions=dict(pbs_path=pbs_path,read_text=read_text,
                            sections_in=sections_in,section_lines=section_lines,
                            file_hash=file_hash)

    def get(self,file,index):
        return detail(self.root,file,index,**self.functions)

    def save_record(self,previous,**updates):
        body={**{k:previous[k] for k in ("file","index","id","hash")},
              **previous["own"],"inherit":previous["inherited"],**updates}
        return save(self.root,self.backups,body,save_section=save_section,
                    **self.functions)


class MoveUnitTests(MoveFixture):
    def test_catalog_includes_all_species_and_form_and_extra_moves(self):
        result=catalog(self.root,read_text=read_text,sections_in=sections_in,
                       section_lines=section_lines)
        self.assertEqual(len(result["species"]),4)
        self.assertTrue(any(x["id"]=="ALPHAMON,1" and x["form"] for x in result["species"]))
        self.assertTrue(any(x["id"]=="GAMMAMON" for x in result["species"]))
        self.assertFalse(any(x["file"]=="pokemon_metrics.txt" for x in result["species"]))
        self.assertIn("CHILLINGWATER",{m["id"] for m in result["moves"]})

    def test_save_only_three_move_fields_preserving_bom_crlf_other_species(self):
        old=self.get("pokemon.txt",0)
        original_other=self.original.split("[BETAMON]")[1]
        response=self.save_record(old,level=[
            {"level":1,"move":"TACKLE"},{"level":12,"move":"FLAMETHROWER"}],
            tutor=["PROTECT","CHILLINGWATER"],egg=["BITE","TACKLE"])
        self.assertTrue(response["ok"])
        self.assertFalse(response["unchanged"])
        raw=(self.root/"PBS"/"pokemon.txt").read_bytes()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        text=raw.decode("utf-8")
        self.assertIn("Moves = 1,TACKLE,12,FLAMETHROWER\r\n",text)
        self.assertIn("TutorMoves = PROTECT,CHILLINGWATER\r\n",text)
        self.assertIn("EggMoves = BITE,TACKLE\r\n",text)
        self.assertIn("BaseStats = 80,80,80,80,80,80",text)
        self.assertIn("[BETAMON]"+original_other,text)
        self.assertEqual(len(list((self.backups/"pokemon.txt").glob("*.bak"))),1)

    def test_form_inheritance_and_override(self):
        initial=self.get("pokemon_forms.txt",0)
        self.assertTrue(initial["form"])
        self.assertEqual(set(initial["inherited"]),{"level","tutor","egg"})
        self.assertEqual(initial["effective"]["level"][1]["move"],"BITE")
        custom=self.save_record(initial,level=[{"level":7,"move":"FLAMETHROWER"}],
                                tutor=[],egg=[],inherit=["tutor","egg"])
        self.assertTrue(custom["ok"])
        form=self.get("pokemon_forms.txt",0)
        self.assertEqual(form["own"]["level"],[{"level":7,"move":"FLAMETHROWER"}])
        self.assertIn("tutor",form["inherited"])
        self.assertEqual(form["effective"]["tutor"],["PROTECT"])
        old_base=self.get("pokemon.txt",0)
        self.assertEqual(old_base["own"]["level"][1]["move"],"BITE")
        self.save_record(form,level=[],tutor=[],egg=[],inherit=["level","tutor","egg"])
        self.assertNotIn("Moves =", (self.root/"PBS"/"pokemon_forms.txt").read_text())

    def test_unknown_move_invalid_level_and_stale_hash(self):
        first=self.get("pokemon.txt",0)
        with self.assertRaisesRegex(MoveEditorError,"não encontrado"):
            self.save_record(first,level=[{"level":1,"move":"NOTAMOVE"}])
        with self.assertRaisesRegex(MoveEditorError,"Níveis"):
            self.save_record(first,level=[{"level":101,"move":"TACKLE"}])
        changed=self.save_record(first,tutor=["CHILLINGWATER"])
        self.assertTrue(changed["ok"])
        with self.assertRaises(MoveEditorError) as conflict:
            self.save_record(first,tutor=["PROTECT"])
        self.assertEqual(conflict.exception.status,409)

    def test_reject_other_pbs_path_and_inheritance_for_base(self):
        base=self.get("pokemon.txt",0)
        for path in ("../pokemon.txt","pokemon_metrics.txt","items.txt","pokemon.txt/../secrets"):
            with self.assertRaises(MoveEditorError):
                self.get(path,0)
        with self.assertRaisesRegex(MoveEditorError,"Somente formas"):
            self.save_record(base,level=[],inherit=["level"])

    def test_repeated_moves_lines_are_preserved_as_single_field_on_write(self):
        source=self.root/"PBS"/"pokemon.txt"
        raw=source.read_bytes().replace(b"Moves = 1,TACKLE,10,BITE\r\n",
            b"Moves = 1,TACKLE\r\nMoves = 10,BITE\r\n")
        source.write_bytes(raw)
        original=self.get("pokemon.txt",0)
        self.assertEqual(len(original["own"]["level"]),2)
        self.save_record(original,level=[{"level":1,"move":"TACKLE"},
                                         {"level":10,"move":"BITE"}],tutor=["BITE"])
        data=source.read_text("utf-8-sig")
        self.assertEqual(sum(1 for line in data.splitlines() if line.startswith("Moves =")),1)


class MoveAPITests(MoveFixture):
    def setUp(self):
        super().setUp()
        server=ThreadingHTTPServer(("127.0.0.1",0),build_handler(self.root,self.backups,0))
        server.RequestHandlerClass=build_handler(self.root,self.backups,server.server_port)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        self.origin="http://127.0.0.1:"+str(server.server_port)

    def request(self,path,data=None):
        headers={"X-Blue-Studio":"1"}
        if data is not None:
            headers["Content-Type"]="application/json"
            headers["Origin"]=self.origin
        req=Request(self.origin+path,data=json.dumps(data).encode() if data is not None else None,
                    method="POST" if data is not None else "GET",headers=headers)
        with urlopen(req) as response:
            return json.load(response)

    def test_api_catalog_entry_and_save(self):
        entries=self.request("/api/pokemon-moves/catalog")
        self.assertEqual(len(entries["species"]),4)
        original=self.request("/api/pokemon-moves/entry?file=pokemon.txt&index=0")
        self.assertEqual(original["own"]["level"][0]["move"],"TACKLE")
        result=self.request("/api/pokemon-moves/save",{
            "file":"pokemon.txt","index":0,"id":"ALPHAMON","hash":original["hash"],
            "level":[{"level":1,"move":"TACKLE"},{"level":20,"move":"BITE"}],
            "tutor":["PROTECT"],"egg":["CHILLINGWATER"],"inherit":[]})
        self.assertTrue(result["ok"])
        updated=self.request("/api/pokemon-moves/entry?file=pokemon.txt&index=0")
        self.assertEqual(updated["own"]["level"][1]["level"],20)
        self.assertEqual(updated["own"]["egg"],["CHILLINGWATER"])
        with self.assertRaises(HTTPError) as fail:
            self.request("/api/pokemon-moves/save",{
                "file":"pokemon.txt","index":0,"id":"ALPHAMON","hash":original["hash"],
                "level":[],"tutor":[],"egg":[],"inherit":[]})
        self.assertEqual(fail.exception.code,409)

    def test_reject_malicious_file_and_missing_move(self):
        with self.assertRaises(HTTPError) as fail:
            self.request("/api/pokemon-moves/entry?file=../items.txt&index=0")
        self.assertEqual(fail.exception.code,400)
        original=self.request("/api/pokemon-moves/entry?file=pokemon.txt&index=0")
        body={"file":"pokemon.txt","index":0,"id":"ALPHAMON","hash":original["hash"],
              "level":[{"level":1,"move":"DOESNOTEXIST"}],
              "tutor":[],"egg":[],"inherit":[]}
        with self.assertRaises(HTTPError) as fail:
            self.request("/api/pokemon-moves/save",body)
        self.assertEqual(fail.exception.code,400)


if __name__=="__main__":
    unittest.main()
