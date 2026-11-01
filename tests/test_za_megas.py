import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
za=module('za_install','scripts/za_megas/install.py')
paste=module('paste_worker','scripts/battle_lab/pokepaste.py')
class MegaCatalogueTests(unittest.TestCase):
    def test_catalogue_has_all_stones_and_variants(self):
        entries=json.loads((ROOT/'data/za-megas.json').read_text(encoding='utf8'))['entries']
        self.assertEqual(len(entries),48)
        self.assertEqual(len({e['stone'] for e in entries}),45)
        self.assertEqual(sum(len(e['forms']) for e in entries),50)
        self.assertTrue(all(len(e['stats'])==6 and min(e['stats'].values())>0 for e in entries))
    def test_patch_corrects_stat_order_and_preserves_unrelated_fields_and_pending_abilities(self):
        entries=[dict(species='RAICHU',forms=[3],types=['ELECTRIC'],stats=dict(zip(za.ORDER,[60,100,55,130,160,80])),stone='RAICHUNITEY',ability='NOGUARD'),dict(species='ZYGARDE',forms=[4],types=['DRAGON','GROUND'],stats=dict(zip(za.ORDER,[216,70,91,100,216,85])),stone='ZYGARDITE',ability=None)]
        source='[RAICHU,3]\nBaseStats = 1,2,3,4,5,6\nMegaStone = MEGAITEY\nMoves = 1,THUNDERSHOCK\n[ZYGARDE,4]\nUnmegaForm = 2\nAbilities = POWERCONSTRUCT\n[RAICHU,1]\nTypes = ELECTRIC,PSYCHIC\n'
        result=za.apply_catalog(source,entries)
        self.assertIn('BaseStats = 60,100,55,130,160,80',result)
        self.assertIn('Moves = 1,THUNDERSHOCK',result)
        self.assertIn('Abilities = POWERCONSTRUCT',result)
        self.assertIn('Flags = BlueZAProvisionalAbility',result)
        self.assertTrue(result.endswith('[RAICHU,1]\nTypes = ELECTRIC,PSYCHIC\n'))
        self.assertEqual(za.apply_catalog(result,entries),result)
    def test_patch_rejects_incomplete_base_before_writing(self):
        with self.assertRaisesRegex(ValueError,'incompleta'):
            za.apply_catalog('[PIKACHU]\n',[dict(species='RAICHU',forms=[3])])
class PasteURLTests(unittest.TestCase):
    def test_both_user_links_and_raw_query_links_normalize_to_original_host(self):
        for url,id in [('https://pokepast-es.translate.goog/0aa2fa5b1738e3c7?_x_tr_sl=en&_x_tr_tl=pt&_x_tr_hl=pt&_x_tr_pto=tc','0aa2fa5b1738e3c7'),('https://pokepast.es/8206474502b1a3be','8206474502b1a3be'),('https://pokepast.es/8206474502b1a3be/raw?foo=1','8206474502b1a3be')]:
            self.assertEqual(paste.normalize(url),'https://pokepast.es/'+id+'/raw')
    def test_unknown_hosts_schemes_userinfo_paths_and_fragments_rejected(self):
        for url in ['http://pokepast.es/8206474502b1a3be','https://pokepast.es.evil.test/8206474502b1a3be','https://evil.test/8206474502b1a3be','https://pokepast.es@evil.test/8206474502b1a3be','https://pokepast-es.translate.goog/../../secret','https://pokepast.es/8206474502b1a3be#evil']:
            with self.assertRaises(ValueError):paste.normalize(url)
