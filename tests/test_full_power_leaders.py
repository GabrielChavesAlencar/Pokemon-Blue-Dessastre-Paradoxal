import importlib.util,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('blue_full_power',ROOT/'scripts/battle_polish/leaders.py')
leaders=importlib.util.module_from_spec(spec);spec.loader.exec_module(leaders)
DATA=leaders.manifest(ROOT)

def fixture(newline='\n'):
    chunks=['# untouched intro\n[YOUNGSTER,Other trainer]\nPokemon = PIKACHU,9\n\tItem = ORANBERRY\n']
    for row in DATA['replacements']:
        for label in ['1v1 Full Power','2v2 Basic Power','2v2 Full Power','3v3 Full Power']:
            chunks.append(f"# section\n[YOUNGSTER,{row['leader']} ({label})]\nItems = MEGARING\nPokemon = {row['from']},50\n\tForm = 0\n\tMoves = TACKLE,GROWL\n\tItem = ORANBERRY\n\tEV = 0,0,0,0,0,0\n\tIV = 31,0,31,31,0,31\nPokemon = EEVEE,49\n\tMoves = QUICKATTACK\n# keep this comment\n")
            if row['leader']=='Cethin':chunks.append('Pokemon = ARBOK,48\n\tItem = AIRBALLOON\n\tMoves = GLARE\n')
    return ''.join(chunks).replace('\n',newline)

def sections(text):
    matches=list(leaders.HEADER.finditer(text))
    return {m[1]:text[m.start():(matches[i+1].start() if i+1<len(matches) else len(text))] for i,m in enumerate(matches)}

class FullPowerTests(unittest.TestCase):
    def test_only_exact_double_full_power_variants_change_and_other_slots_are_preserved(self):
        before=fixture();after=leaders.transform(before,DATA);a,b=sections(before),sections(after)
        self.assertEqual(set(a),set(b))
        for key in a:
            if '(2v2 Full Power)' not in key:self.assertEqual(a[key],b[key],key)
            else:
                self.assertIn('Pokemon = EEVEE,49\n\tMoves = QUICKATTACK\n# keep this comment\n',b[key])
                self.assertIn('Items = MEGARING',b[key])
        self.assertEqual(len([k for k in a if a[k]!=b[k]]),18)
    def test_every_requested_set_and_mega_stone_is_written(self):
        after=sections(leaders.transform(fixture(),DATA))
        for row in DATA['replacements']:
            s=after['YOUNGSTER,'+row['leader']+' (2v2 Full Power)']
            self.assertIn('Pokemon = '+row['species']+',50',s)
            self.assertIn('Moves = '+','.join(row['moves']),s)
            self.assertIn('Nature = '+row['nature'],s)
            self.assertIn('Item = '+row['item'],s)
        self.assertIn('Pokemon = ARBOK,48\n\tItem = DPARBOKITE',after['YOUNGSTER,Cethin (2v2 Full Power)'])
    def test_pbs_speed_is_fourth_and_special_attack_is_fifth(self):
        after=sections(leaders.transform(fixture(),DATA))
        self.assertIn('EV = 200,0,0,52,252,0',after['YOUNGSTER,Reva (2v2 Full Power)'])
        self.assertIn('EV = 252,0,152,0,100,0',after['YOUNGSTER,Atlas (2v2 Full Power)'])
        self.assertIn('EV = 252,152,0,0,0,100',after['YOUNGSTER,Cethin (2v2 Full Power)'])
    def test_reapplying_is_idempotent_in_both_line_endings(self):
        for newline in ['\n','\r\n']:
            first=leaders.transform(fixture(newline),DATA)
            self.assertEqual(first,leaders.transform(first,DATA))
            if newline=='\r\n':self.assertNotIn('\n',first.replace('\r\n',''))
    def test_missing_or_ambiguous_slots_refuse_to_overwrite(self):
        raw=fixture()
        with self.assertRaises(ValueError):leaders.transform(raw.replace('SUNFLORA,50','BULBASAUR,50'),DATA)
        duplicate=raw.replace('Pokemon = EEVEE,49','Pokemon = SUNFLORA,49',1)
        # Target only the double Full Power Marigold section for a real ambiguity.
        duplicate=raw.replace('Pokemon = SUNFLORA,50\n','Pokemon = SUNFLORA,50\nPokemon = ARCHGUTOR,50\n')
        with self.assertRaises(ValueError):leaders.transform(duplicate,DATA)
if __name__=='__main__':unittest.main()
