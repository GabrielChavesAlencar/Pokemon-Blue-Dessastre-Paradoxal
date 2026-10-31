import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from main import (sections_in, extract_fields, read_text, file_hash, save_section, pbs_path, EditorError, build_handler)


class PBSUnitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "PBS").mkdir()
        self.backups = self.root / "backups"
        self.path = self.root / "PBS" / "pokemon.txt"
        self.source = ('\ufeff# Header\r\n#-------------------------------\r\n[ABYSS]\r\n'
                       'Name = Abyss\r\nMoves = 1,TACKLE\r\nMoves = 4,BITE\r\n'
                       '#-------------------------------\r\n[SEAWORM]\r\n'
                       'Name = Sea Worm\r\nBaseStats = 1,2,3,4,5,6\r\n')
        self.path.write_bytes(self.source.encode('utf-8'))

    def test_parse_and_fields(self):
        raw, txt = read_text(self.path)
        ss = sections_in(txt)
        self.assertEqual([x['id'] for x in ss], ['ABYSS', 'SEAWORM'])
        fields = extract_fields(txt)
        self.assertEqual(sum(x['key']=='Moves' for x in fields), 2)
        self.assertEqual(ss[0]['label'], 'Abyss')

    def test_save_preserves_other_records_bom_and_backups(self):
        b = self.path.read_bytes()
        result = save_section(self.root, 'pokemon.txt', 0, file_hash(b), '[ABYSS]\nName = New Abyss\nMoves = 1,TACKLE\nMoves = 4,BITE\n', self.backups)
        after = self.path.read_bytes()
        self.assertTrue(after.startswith(b'\xef\xbb\xbf'))
        self.assertIn(b'Name = New Abyss', after)
        self.assertIn(b'Name = Sea Worm', after)
        self.assertEqual(result['index'], 0)
        self.assertEqual(len(list((self.backups / 'pokemon.txt').glob('*.bak'))), 1)

    def test_create_duplicate_and_concurrency(self):
        b = self.path.read_bytes()
        result = save_section(self.root, 'pokemon.txt', -1, file_hash(b), '[NEWMON]\nName = New\n', self.backups)
        self.assertEqual(result['count'], 3)
        with self.assertRaises(EditorError):
            save_section(self.root, 'pokemon.txt', -1, file_hash(b), '[DIFFERENT]\nName = X\n', self.backups)
        with self.assertRaises(EditorError):
            save_section(self.root, 'pokemon.txt', -1, result['hash'], '[NEWMON]\nName = X\n', self.backups)

    def test_block_traversal_and_multiple_sections(self):
        for path in ('../secrets.txt','/tmp/evil.txt','..\\foo.txt','nonexistent.txt'):
            with self.assertRaises(EditorError):
                pbs_path(self.root, path)
        with self.assertRaises(EditorError):
            save_section(self.root,'pokemon.txt',0,file_hash(self.path.read_bytes()),'[A]\n[X]\n',self.backups)


class APITest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'PBS').mkdir()
        (self.root / 'PBS' / 'moves.txt').write_text('[TACKLE]\nName = Tackle\nPower = 40\n', encoding='utf-8')
        self.srv = ThreadingHTTPServer(('127.0.0.1', 0), build_handler(self.root, self.root / 'backups', 0))
        self.srv.RequestHandlerClass = build_handler(self.root, self.root / 'backups', self.srv.server_port)
        self.thread = threading.Thread(target=self.srv.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.origin = f'http://127.0.0.1:{self.srv.server_port}'

    def api(self, path, method='GET', obj=None, token=True):
        headers = {'Content-Type':'application/json'} if obj is not None else {}
        if token:headers['X-Blue-Studio']='1'
        if obj is not None:headers['Origin']=self.origin
        req = Request(self.origin+path, data=json.dumps(obj).encode() if obj is not None else None, method=method, headers=headers)
        with urlopen(req) as r:return json.load(r)

    def test_http_roundtrip(self):
        files=self.api('/api/files')
        self.assertEqual(files['files'][0]['name'],'moves.txt')
        ls=self.api('/api/sections?file=moves.txt')
        self.assertEqual(ls['sections'][0]['id'],'TACKLE')
        section=self.api('/api/section?file=moves.txt&index=0')
        self.assertIn('Power = 40',section['raw'])
        updated=self.api('/api/save','POST',{'file':'moves.txt','index':0,'hash':ls['hash'],'raw':section['raw'].replace('40','45')})
        self.assertTrue(updated['ok'])
        self.assertIn('Power = 45',self.api('/api/section?file=moves.txt&index=0')['raw'])
        self.assertEqual(len(self.api('/api/backups?file=moves.txt')['backups']),1)
        backups=self.api('/api/backups?file=moves.txt')['backups']
        restored=self.api('/api/restore','POST',{'file':'moves.txt','hash':updated['hash'],'backup':backups[0]['name']})
        self.assertTrue(restored['ok'])
        self.assertIn('Power = 40',self.api('/api/section?file=moves.txt&index=0')['raw'])


    def test_new_frontend_files_served(self):
        for target, mime in (('/navigation.js','javascript'),('/studio-shell.css','css')):
            req = Request(self.origin + target)
            with urlopen(req) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(mime, response.headers.get('Content-Type',''))
                self.assertGreater(len(response.read()), 500)

    def test_post_requires_token(self):
        with self.assertRaises(HTTPError) as ctx:
            self.api('/api/launch','POST',{},token=False)
        self.assertEqual(ctx.exception.code,403)

if __name__=='__main__':unittest.main()
