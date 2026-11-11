"""Regression tests for regional Eevee integration without a game ROM."""
import importlib.util
import json
import shutil
import struct
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FUTURE=ROOT/'scripts/dessastre_paradoxal/future_eevee.py'
spec=importlib.util.spec_from_file_location('regional_eevee',FUTURE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
MANIFEST=mod.load_manifest(ROOT)
MAPS=json.loads((ROOT/'data/eevee-regional-encounters.json').read_text('utf8'))
TRAINERS=json.loads((ROOT/'data/eevee-regional-trainers.json').read_text('utf8'))

class RegionalEeveeTests(unittest.TestCase):
    def test_all_forms_have_distinct_types_correct_bst_and_eight_evolutions(self):
        self.assertEqual(len(MANIFEST['forms']),9)
        stats={e['card']['base']:e['card']['stats'] for e in MANIFEST['forms']}
        self.assertEqual(sum(stats['EEVEE']),325)
        self.assertTrue(all(sum(v)==525 for k,v in stats.items() if k!='EEVEE'))
        self.assertEqual(len(MANIFEST['evolutions']),8)
        self.assertEqual(len({v['methodId'] for v in MANIFEST['evolutions'].values()}),8)
        allowed_moves=set(m for e in MANIFEST['forms'] for _,m in e['details']['moves'])
        allowed_moves.update(m for e in MANIFEST['forms'] for m in e['details']['tm']+e['details'].get('tutor',[])+e['details']['egg'])
        allowed_abilities=set(a for e in MANIFEST['forms'] for a in e['details']['abilities']+e['details']['hidden'])
        pbs,missing,missing_a=mod.build_forms(MANIFEST,allowed_moves,allowed_abilities)
        self.assertEqual(missing,[]);self.assertEqual(missing_a,[])
        self.assertEqual(pbs.count('FormName = Regional'),9)
        self.assertIn('[EEVEE,50]',pbs)
        self.assertIn('Evolutions = ',pbs)
        for evo in MANIFEST['evolutions'].values():self.assertIn(evo['methodId'],pbs)
        self.assertIn('Types = GHOST',pbs)
        self.assertIn('BaseStats = 50,45,45,60,60,65',pbs)

    def test_all_63_graphics_are_pngs_with_expected_dimensions(self):
        assets=mod.extract_sprites(ROOT,MANIFEST)
        self.assertEqual(len(assets),63)
        self.assertEqual(len(set(assets)),63)
        for path,content in assets.items():
            self.assertTrue(path.startswith('Graphics/Pokemon/'))
            self.assertEqual(content[:8],mod.SIGNATURE)
            width,height=struct.unpack_from('>II',content,16)
            size=48 if '/Footprints/' in path else 64 if '/Icons' in path else 128
            self.assertEqual((width,height),(size,size),path)

    def test_exact_chances_paradox_protection_all_versions_and_idempotence(self):
        self.assertEqual(len(MAPS['areas']),9)
        raw=''
        for a in MAPS['areas']:
            raw+=f"[{a['mapId']}]\n{a['method']},21\n    60,PIKACHU,5,8\n    35,RATTATA,6,9\n    5,CAVEFANG,8,10\n"
            raw+=f"[{a['mapId']},1]\n{a['method']},21\n    95,PIKACHU,8,11\n    5,CAVEFANG,8,11\n"
        changed=mod.regional_encounters(raw,MAPS,{'CAVEFANG'})
        self.assertEqual(mod.regional_encounters(changed,MAPS,{'CAVEFANG'}),changed)
        for a in MAPS['areas']:
            self.assertEqual(changed.count(','+a['species']+','),2)
            for section in (f"[{a['mapId']}]",f"[{a['mapId']},1]"):
                fragment=changed.split(section+'\n',1)[1].split('\n[',1)[0]
                lines=[x.strip().split(',') for x in fragment.splitlines() if x.startswith('    ')]
                self.assertEqual(sum(int(x[0]) for x in lines),100)
                self.assertEqual(int(next(x[0] for x in lines if x[1]==a['species'])),a['percent'])
                self.assertEqual(int(next(x[0] for x in lines if x[1]=='CAVEFANG')),5)
                self.assertIn('PIKACHU',{x[1] for x in lines})
                if section.endswith(',1]'):
                    self.assertNotIn('RATTATA',{x[1] for x in lines})
                else:
                    self.assertIn('RATTATA',{x[1] for x in lines})

    def test_trainers_get_one_regional_form_without_replacing_originals(self):
        raw=''
        for t in TRAINERS['trainers']:
            raw+=f"[{t['trainerType']},{t['name']}]\nPokemon = PIKACHU,20\nPokemon = BULBASAUR,23\nPokemon = CHARMANDER,24\n"
        new,added=mod.patch_trainers(raw,TRAINERS)
        self.assertEqual(added,9)
        self.assertEqual(new.count('    Form = 50'),9)
        self.assertEqual(new.count('Pokemon = CHARMANDER,24'),9)
        self.assertEqual(new.count('Pokemon = EEVEE,24'),1)
        self.assertEqual(mod.patch_trainers(new,TRAINERS),(new,0))

    def test_ruby_evolution_handlers_syntax(self):
        ruby=shutil.which('ruby')
        if not ruby:self.skipTest('Ruby not available')
        code=ROOT/'scripts/dessastre_paradoxal/FutureEevee.rb'
        result=subprocess.run([ruby,'-c',str(code)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

if __name__=='__main__':unittest.main()
