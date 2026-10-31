"""No replacement of existing Pokémon: native PBS registry, references, and sprite metrics."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"server"))
from main import build_handler, backup_file, atomic_write, read_text, file_hash, EDIT_LOCK
from pokemon_studio import create_species,validate_pokemon,species_catalog,PokemonValidationError


class NewSpeciesTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.pbs=self.root/"PBS"
        self.pbs.mkdir()
        self.backups=self.root/"backups"
        (self.pbs/"pokemon.txt").write_text("[OLDMON]\nName = Oldmon\nTypes = WATER\nBaseStats = 70,70,70,70,70,70\nAbilities = SWIFTSWIM\nMoves = 1,TACKLE\n",encoding="utf-8")
        (self.pbs/"pokemon_base_Gen_9_Pack.txt").write_text("[HIDDENBASE]\nName = Hidden Base\n",encoding="utf-8")
        (self.pbs/"pokemon_forms.txt").write_text("[OLDMON,1]\nFormName = Alt\n",encoding="utf-8")
        (self.pbs/"pokemon_metrics.txt").write_text("[OLDMON]\nFrontSprite = 1,2\nBackSprite = 3,4\n",encoding="utf-8")
        (self.pbs/"pokemon_metrics_forms.txt").write_text("[OLDMON,1]\nFrontSprite = 2,2\n",encoding="utf-8")
        (self.pbs/"types.txt").write_text("[WATER]\nName = Water\n[DRAGON]\nName = Dragon\n",encoding="utf-8")
        (self.pbs/"abilities.txt").write_text("[SWIFTSWIM]\nName = Swift Swim\n",encoding="utf-8")
        (self.pbs/"moves.txt").write_text("[TACKLE]\nName = Tackle\n[BITE]\nName = Bite\n",encoding="utf-8")
        self.payload={"id":"CAVEFANG","name":"Cave Fang","type1":"WATER","type2":"DRAGON",
                      "stats":[60,70,80,90,100,110],"abilities":"SWIFTSWIM","moves":"1,TACKLE,10,BITE"}

    def create(self, body):
        return create_species(self.root,self.backups,body,lock=EDIT_LOCK,
                              backup_file=backup_file,atomic_write=atomic_write,
                              read_text=read_text,file_hash=file_hash)

    def test_create_two_new_species_no_replacement(self):
        before=(self.pbs/"pokemon.txt").read_bytes()
        m_before=(self.pbs/"pokemon_metrics.txt").read_bytes()
        one=self.create(self.payload)
        self.assertTrue(one["noReplacement"])
        self.assertEqual(one["totalStats"],510)
        two=self.create({**self.payload,"id":"ABYSSMON","name":"Abyss Mon"})
        self.assertTrue(two["created"])
        after=(self.pbs/"pokemon.txt").read_bytes()
        self.assertTrue(after.startswith(before))
        self.assertEqual(after.count(b"[OLDMON]"),1)
        self.assertEqual(after.count(b"[CAVEFANG]"),1)
        self.assertEqual(after.count(b"[ABYSSMON]"),1)
        self.assertTrue((self.pbs/"pokemon_metrics.txt").read_bytes().startswith(m_before))
        self.assertEqual(len(list((self.backups/"pokemon.txt").glob("*.bak"))),2)
        self.assertIn("OLDMON",species_catalog(self.root))
        self.assertIn("ABYSSMON",species_catalog(self.root))

    def test_duplicate_ids_across_extra_pbs(self):
        for name in ("OLDMON","HIDDENBASE"):
            with self.assertRaises(PokemonValidationError):
                self.create({**self.payload,"id":name})
        self.create(self.payload)
        with self.assertRaises(PokemonValidationError):
            self.create(self.payload)

    def test_unknown_ability_move_type_evolution(self):
        for change in ({"abilities":"INVALID"}, {"moves":"5,INVALID"},
                       {"type2":"NOTATYPE"}, {"evolutions":"MISSING,Level,20"}):
            with self.subTest(change=change),self.assertRaises(PokemonValidationError):
                self.create({**self.payload,**change})
        self.assertEqual((self.pbs/"pokemon.txt").read_text().count("[CAVEFANG]"),0)

    def test_bad_stats_and_injection(self):
        for change in ({"stats":[0,70,80,90,100,110]},
                       {"id":"A/B"}, {"name":"Name\n[INJECTED]"}):
            with self.subTest(change=change),self.assertRaises(PokemonValidationError):
                self.create({**self.payload,**change})


class SpeciesAPITest(NewSpeciesTests):
    def setUp(self):
        super().setUp()
        server=ThreadingHTTPServer(("127.0.0.1",0),build_handler(self.root,self.backups,0))
        server.RequestHandlerClass=build_handler(self.root,self.backups,server.server_port)
        t=threading.Thread(target=server.serve_forever,daemon=True)
        t.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.origin="http://127.0.0.1:"+str(server.server_port)

    def post(self,path,obj):
        data=json.dumps(obj).encode("utf-8")
        request=Request(self.origin+path,data=data,method="POST",headers={
            "Content-Type":"application/json","X-Blue-Studio":"1","Origin":self.origin})
        with urlopen(request) as resp:
            return json.load(resp)

    def get(self,path):
        with urlopen(self.origin+path) as resp:
            return json.load(resp)

    def test_create_and_update_metrics_http(self):
        result=self.post("/api/pokemon/new",self.payload)
        self.assertEqual(result["id"],"CAVEFANG")
        meta=self.get("/api/pokemon/metrics?species=CAVEFANG")
        self.assertTrue(meta["exists"])
        self.assertEqual(meta["front"],[0,0])
        changed=self.post("/api/pokemon/metrics",{
            "species":"CAVEFANG","front":[10,-4,2],"back":[-8,7,3],
            "speed":[0,0],"expectedHash":meta["hash"]})
        self.assertTrue(changed["saved"])
        self.assertEqual(changed["front"],[10,-4,2])
        text=(self.pbs/"pokemon_metrics.txt").read_text()
        self.assertIn("FrontSprite = 10,-4,2",text)
        self.assertIn("BackSprite = -8,7,3",text)
        with self.assertRaises(HTTPError) as conflict:
            self.post("/api/pokemon/metrics",{
                "species":"CAVEFANG","front":[0,0,2],"back":[0,0,3],
                "speed":[0,0],"expectedHash":meta["hash"]})
        self.assertEqual(conflict.exception.code,409)

    def test_form_metrics_does_not_overwrite_base(self):
        before=(self.pbs/"pokemon_metrics.txt").read_bytes()
        data=self.get("/api/pokemon/metrics?species=OLDMON_1")
        self.assertEqual(data["file"],"pokemon_metrics_forms.txt")
        updated=self.post("/api/pokemon/metrics",{
            "species":"OLDMON_1","front":[1,-3,2],"back":[2,4,3],
            "speed":[0,0],"expectedHash":data["hash"]})
        self.assertEqual(updated["header"],"OLDMON,1")
        self.assertEqual(before,(self.pbs/"pokemon_metrics.txt").read_bytes())

    def test_catalog_and_duplicate_http(self):
        self.assertIn("SWIFTSWIM",self.get("/api/pokemon/catalog")["abilities"])
        self.post("/api/pokemon/new",self.payload)
        with self.assertRaises(HTTPError) as dup:
            self.post("/api/pokemon/new",self.payload)
        self.assertEqual(dup.exception.code,400)
        self.assertTrue(self.get("/api/pokemon/catalog")["speciesCount"] >= 3)

if __name__=="__main__":
    unittest.main()
