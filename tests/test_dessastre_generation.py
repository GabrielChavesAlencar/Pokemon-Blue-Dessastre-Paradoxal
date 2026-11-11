import importlib.util,json,re,shutil,tempfile,unittest
from pathlib import Path
from server.pokemon_studio import make_species_raw,parse_fields,generation_fields,PokemonValidationError
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('blue_dp_install',ROOT/'scripts/dessastre_paradoxal/install.py')
installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)
MANIFEST=json.loads((ROOT/'data/dessastre-paradoxal.json').read_text(encoding='utf8'))

class NamedGenerationTests(unittest.TestCase):
    def test_rare_spread_has_all_ready_paradoxes_once_and_excludes_drafts_and_megas(self):
        config=json.loads((ROOT/'data/fan-encounters.json').read_text('utf8'))
        placed=[id for area in config['areas'] for id in area['species']]
        expected={p['id'] for p in MANIFEST['entries'] if p['category'] in ('past_paradox','future_paradox') and not p['pending']}
        self.assertEqual(len(placed),44);self.assertEqual(len(placed),len(set(placed)))
        self.assertEqual(set(placed),expected);self.assertEqual(config['chancePerSpecies'],5)
        self.assertTrue(all(a['reason'] and a['mapId'] not in (156,157) for a in config['areas']))

    def test_rare_spread_migrates_grottos_and_versions_without_losing_original_slots(self):
        entries=[{'id':'CAVEFANG','category':'past_paradox','pending':False}, {'id':'IRONCRUSHER','category':'future_paradox','pending':False}, {'id':'DRAFT','category':'past_paradox','pending':True}]
        config={'version':2,'chancePerSpecies':5,'areas':[{'mapId':88,'method':'Land','species':['CAVEFANG','IRONCRUSHER']}]}
        original='[88]\nLand,21\n    60,PIKACHU,5,8\n    40,EEVEE,8\nWater,10\n    100,MAGIKARP,3\n[88,1]\nLand,21\n    100,VULPIX,5\n[156]\nLand,21\n    50,ZUBAT,65,70\n    50,CAVEFANG,65,70\n'
        result=installer.update_encounters(original,entries,config)
        self.assertIn('    54,PIKACHU,5,8\n    36,EEVEE,8\n    5,CAVEFANG,5,8\n    5,IRONCRUSHER,5,8',result)
        self.assertIn('[88,1]\nLand,21\n    90,VULPIX,5\n    5,CAVEFANG,5\n    5,IRONCRUSHER,5\n',result)
        self.assertIn('[156]\nLand,21\n    100,ZUBAT,65,70\n',result)
        self.assertIn('Water,10\n    100,MAGIKARP,3\n',result)
        self.assertEqual(installer.update_encounters(result,entries,config),result)
        config['areas'][0]['species']=['DRAFT']
        with self.assertRaisesRegex(ValueError,'nao liberado'):installer.update_encounters(original,entries,config)
    def test_extra_assets_are_exact_and_archive_corruption_is_rejected(self):
        import hashlib,wave,io
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root)
            assets=installer.extra_assets(root,game)
            manifest=json.loads((ROOT/'data/fan-assets.json').read_text())
            self.assertEqual(len(assets),60)
            for entry in manifest['files']:
                raw=assets[(game/entry['target']).resolve()]
                self.assertEqual(hashlib.sha256(raw).hexdigest(),entry['sha256'])
                if entry['path'].endswith('.wav'):
                    with wave.open(io.BytesIO(raw)) as sound:self.assertGreater(sound.getnframes(),0)
                else:self.assertEqual(raw[:8],b'\x89PNG\r\n\x1a\n')
            (root/'site/assets/fan-extras.tar.gz').write_bytes(b'corrupt')
            with self.assertRaises(ValueError):installer.extra_assets(root,game)

    def test_paradox_encounters_preserve_originals_levels_other_areas_and_are_idempotent(self):
        original='[1]\nLand,5\n    100,PIKACHU,2,3\n[156]\nLand,21\n    60,GREAT_TUSK,65,70\n    40,SCREAM_TAIL,65,70\nWater,10\n    100,MAGIKARP,5\n[157]\nLand,21\n    50,IRON_TREADS,65,70\n    50,IRON_BUNDLE,65,70\n'
        result=installer.update_encounters(original,MANIFEST['entries'])
        self.assertEqual(installer.update_encounters(result,MANIFEST['entries']),result)
        self.assertIn('[1]\nLand,5\n    100,PIKACHU,2,3\n',result)
        self.assertIn('Water,10\n    100,MAGIKARP,5\n',result)
        for key,category in [('156','past_paradox'),('157','future_paradox')]:
            section=next(s for s in installer.parse_sections(result) if s[0]==key)
            block=result[section[1]:section[2]].split('Land,21\n')[1].split('Water,')[0]
            rows=[line.strip().split(',') for line in block.splitlines() if line.strip()]
            self.assertEqual(sum(int(r[0]) for r in rows),100)
            expected={p['id'] for p in MANIFEST['entries'] if p['category']==category and not p['pending']}
            self.assertEqual({r[1] for r in rows if r[1] in expected},expected)
            self.assertEqual(sum(int(r[0]) for r in rows if r[1] in expected),50)
            self.assertTrue(all(r[2:]==['65','70'] for r in rows))
        self.assertNotIn(',PRIMALNOTIC,',result)

    def test_generation_name_serializes_to_engine_flag(self):
        raw=make_species_raw({'id':'BLUEAUTHOR','name':'Blue Author','stats':[80]*6,'description':'????','generation':'Dessastre Paradoxal'})
        fields=parse_fields(raw);self.assertEqual(fields['Generation'],'0');self.assertEqual(fields['Flags'],'DessastreParadoxal');self.assertEqual(fields['Pokedex'],'????')
        self.assertEqual(generation_fields('9'),('9',''))
        with self.assertRaises(PokemonValidationError):generation_fields('anything else')

    def test_manifest_preserves_all_records_and_marks_drafts(self):
        entries=MANIFEST['entries'];self.assertEqual(len(entries),71);self.assertEqual(len({p['id'] for p in entries}),71)
        drafts=[p for p in entries if p['pending']];self.assertEqual(len(drafts),7)
        self.assertTrue(all(p['stats']==[None]*6 for p in drafts))
        approved=json.loads((ROOT/'site/public/data/pokedex-approved.json').read_text(encoding='utf8'))['species']
        self.assertTrue(all(p['description']==approved.get(p['id'],{}).get('description','????') for p in entries))
        self.assertEqual(sum(bool(p.get('base')) for p in entries),12)
        cave=next(p for p in entries if p['id']=='CAVEFANG');self.assertEqual(cave['stats'],[85,130,65,155,50,85]);self.assertEqual(cave['learnset']['level'][0]['id'],'ABSORB')
        self.assertTrue(all(isinstance(m['level'],int) and 0<=m['level']<=100 for p in entries for m in p['learnset']['level']))

    def fixture(self,root):
        game=root/'game';(game/'PBS').mkdir(parents=True);(game/'Data').mkdir();(game/'Data/Scripts.rxdata').write_bytes(b'fixture');(game/'Data/Map001.rxdata').write_bytes(b'campaign map')
        (root/'data').mkdir();(root/'site/assets').mkdir(parents=True);(root/'scripts/dessastre_paradoxal').mkdir(parents=True)
        shutil.copy2(ROOT/'site/assets/fan-pokemon.tar.gz',root/'site/assets/fan-pokemon.tar.gz')
        shutil.copy2(ROOT/'site/assets/fan-extras.tar.gz',root/'site/assets/fan-extras.tar.gz')
        shutil.copy2(ROOT/'data/fan-assets.json',root/'data/fan-assets.json')
        mini={**MANIFEST,'entries':[p for p in MANIFEST['entries'] if p['id'] in ['CAVEFANG','HORSAND']]}
        (root/'data/dessastre-paradoxal.json').write_text(json.dumps(mini),encoding='utf8')
        for name in ['Generation.rb','RuntimeChecks.rb','meta.txt']:shutil.copy2(ROOT/'scripts/dessastre_paradoxal'/name,root/'scripts/dessastre_paradoxal'/name)
        moves={m['id'] for p in mini['entries'] for group in p['learnset'].values() for m in group}
        (game/'PBS/moves.txt').write_text('\n'.join('['+x+']' for x in sorted(moves)),encoding='utf8')
        (game/'PBS/abilities.txt').write_text('[PROTOSYNTHESIS]\n',encoding='utf8')
        (game/'PBS/pokemon.txt').write_text('[BULBASAUR]\nName = Bulbasaur\n',encoding='utf8')
        return game

    def test_install_does_not_compile_drafts_or_change_maps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root);before=(game/'PBS/pokemon.txt').read_bytes()
            result=installer.install(root,game,True);self.assertTrue(result['applied']);self.assertEqual(result['pending'],1)
            species=(game/'PBS/pokemon_dessastre_paradoxal.txt').read_text();self.assertIn('[CAVEFANG]',species);self.assertNotIn('[HORSAND]',species)
            # Engine front scale is 2x; back, shiny and graphics remain unchanged.
            metrics=(game/'PBS/pokemon_metrics_dessastre_paradoxal.txt').read_text()
            self.assertIn('[CAVEFANG]\nFrontSprite = 0,0,2\nBackSprite = 0,0,1\nShadowSprite = 0,0,2',metrics)
            self.assertNotIn('[HORSAND]',metrics)
            self.assertEqual(metrics.count('FrontSprite = 0,0,2'),1)
            self.assertEqual((game/'Data/Map001.rxdata').read_bytes(),b'campaign map');self.assertEqual((game/'PBS/pokemon.txt').read_bytes(),before)
            self.assertEqual(installer.install(root,game,True)['files'],0)

    def test_source_archive_hash_is_checked_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root);(root/'site/assets/fan-pokemon.tar.gz').write_bytes(b'broken')
            with self.assertRaises(ValueError):installer.install(root,game,True)
            self.assertFalse((game/'PBS/pokemon_dessastre_paradoxal.txt').exists())

    def test_site_export_preserves_edits_made_in_the_local_pbs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root)
            source=root/'scripts/export_site_data.py';shutil.copy2(ROOT/'scripts/export_site_data.py',source)
            export_spec=importlib.util.spec_from_file_location('blue_dp_export_fixture',source)
            exporter=importlib.util.module_from_spec(export_spec);export_spec.loader.exec_module(exporter)
            cave=next(p for p in MANIFEST['entries'] if p['id']=='CAVEFANG')
            (root/'data/dessastre-paradoxal.json').write_text(json.dumps({**MANIFEST,'entries':[cave]}),encoding='utf8')
            (game/'PBS/pokemon_dessastre_paradoxal.txt').write_text('[CAVEFANG]\nName = Cave Fang\nTypes = DARK\nBaseStats = 100,101,102,103,104,105\nAbilities = INNERFOCUS\nMoves = 1,TACKLE\nGeneration = 0\nFlags = DessastreParadoxal\nPokedex = ????\n',encoding='utf8')
            (game/'PBS/map_metadata.txt').write_text('');(game/'PBS/encounters.txt').write_text('')
            output=root/'export';exporter.export(game,output)
            catalog=json.loads((output/'catalog.json').read_text(encoding='utf8'));detail=json.loads((output/'details.json').read_text(encoding='utf8'))['species']['CAVEFANG']
            actual=next(p for p in catalog['species'] if p['id']=='CAVEFANG')
            self.assertEqual(actual['stats'],[100,101,102,103,104,105]);self.assertEqual(actual['types'],['DARK'])
            self.assertEqual(detail['abilities'],['INNERFOCUS']);self.assertEqual(detail['moves'],[[1,'TACKLE']])

    def test_existing_species_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root);(game/'PBS/pokemon.txt').write_text('[CAVEFANG]\nName = Existing author record\n')
            with self.assertRaisesRegex(ValueError,'ID ja usado'):installer.install(root,game,True)
            self.assertIn('Existing author record',(game/'PBS/pokemon.txt').read_text())

    def test_new_evolution_preserves_trade_empty_parameters_and_other_branches(self):
        text='[KADABRA]\nEvolutions = ALAKAZAM,Trade,,ALAKAZAM,Item,LINKINGCORD\n[OTHER]\nName = Same\n'
        link=['BLUEAUTHOR','Level','40'];updated=installer.append_evolution(text,'KADABRA',link)
        self.assertIn('ALAKAZAM,Trade,,ALAKAZAM,Item,LINKINGCORD,BLUEAUTHOR,Level,40',updated)
        self.assertEqual(installer.append_evolution(updated,'KADABRA',link),updated);self.assertIn('[OTHER]\nName = Same',updated)

if __name__=='__main__':unittest.main()
