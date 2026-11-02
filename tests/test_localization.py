import importlib.util,json,sys,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/localization'))
from catalog import controls,validate,extract
spec=importlib.util.spec_from_file_location('blue_locale_install',ROOT/'scripts/localization/install.py')
installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)
from server.ruby_marshal import loads,text,dumps_simple
class LocalizationTests(unittest.TestCase):
    def test_quest_display_fields_and_abilities_are_collected_without_executing_ruby(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);data=root/'game/Data';data.mkdir(parents=True)
            messages=[{} for _ in range(31)]
            messages[5]={'Flamethrower':'Flamethrower'};messages[10]={'Blaze':'Blaze'}
            for name in ['messages_core.dat','messages_game.dat','CommonEvents.rxdata']:(data/name).write_bytes(b'inert test data')
            quest=root/'game/Plugins/MQS/004_Quest_Data.rb';quest.parent.mkdir(parents=True)
            quest.write_text(':ID => "QuestInternalId",\n:Name => "A new quest",\n:Stage1 => "Find the clue.",\n:Condition => "SecretFlag",\nraise "Never execute Ruby"\n',encoding='utf8')
            with patch('catalog.loads',side_effect=[messages,messages,[None]]):result=extract(root)
            self.assertIn('Blaze',result['strings']);self.assertIn('A new quest',result['strings'])
            self.assertIn('Find the clue.',result['strings'])
            for protected in ['Flamethrower','QuestInternalId','SecretFlag','Never execute Ruby']:self.assertNotIn(protected,result['strings'])
    def test_gender_colour_prefix_does_not_consume_portuguese_word(self):
        validate(r'\bOK. Please return. \mI am here.',r'\bPode voltar. \mEu estou aqui.')
        self.assertEqual(controls(r'\bPode voltar.'),controls(r'\bHello.'))
    def test_formatting_and_variables_are_required_unchanged(self):
        source=r'\bHello, \PN!\nYou have {1:d} points, #{currency}. <b>Go!</b>'
        target=r'\bOlá, \PN!\nVocê tem {1:d} pontos, #{currency}. <b>Vá!</b>'
        validate(source,target)
        for broken in [target.replace(r'\PN','Ash'),target.replace('{1:d}','{1}'),target.replace('#{currency}','dinheiro'),target.replace('</b>',''),target.replace(r'\n','')]:
            with self.subTest(broken=broken),self.assertRaises(ValueError):validate(source,broken)
    def test_locale_compiles_to_native_pairs_without_mutating_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir();game=root/'game';game.mkdir()
            original=game/'Save.rxdata';original.write_bytes(b'existing save')
            rows={'Hello':'Olá','Welcome, {1}!':'Bem-vindo, {1}!'}
            (root/'data/pt-br.json').write_text(json.dumps({'version':1,'language':'pt-BR','translations':rows}),encoding='utf8')
            plan=installer.plan(root,game)
            self.assertEqual(list(plan),[game/'Data/blue-pt-br.dat'])
            decoded={text(k):text(v) for k,v in loads(next(iter(plan.values())))}
            self.assertEqual(decoded,rows);self.assertEqual(original.read_bytes(),b'existing save')
            self.assertFalse((game/'Data').exists())
    def test_invalid_locale_fails_before_writing(self):
        for data in [{'version':1,'language':'es','translations':{}},{'version':1,'language':'pt-BR','translations':{'Hi':''}},{'version':0,'language':'pt-BR','translations':{}},{'version':1,'language':'pt-BR','translations':{'Hi, {1}!':'Olá!'}}]:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);(root/'data').mkdir();(root/'data/pt-br.json').write_text(json.dumps(data),encoding='utf8')
                with self.assertRaises(ValueError):installer.plan(root,root/'game')
                self.assertFalse((root/'game').exists())
    def test_published_catalog_covers_story_and_preserves_controls(self):
        path=ROOT/'data/pt-br.json'
        if not path.is_file():self.skipTest('Author-time translation is still building')
        data=json.loads(path.read_text(encoding='utf8'));self.assertEqual(data['coverage']['missing'],0)
        self.assertGreaterEqual(data['coverage']['mapStrings'],1900)
        self.assertGreaterEqual(len(data['translations']),14000)
        for source,target in data['translations'].items():
            self.assertEqual(controls(source),controls(target),source)
            self.assertNotIn('\ufffd',target)
if __name__=='__main__':unittest.main()
