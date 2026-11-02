import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('blue_profile_export',ROOT/'scripts/export_story_teams.py')
export=importlib.util.module_from_spec(spec);spec.loader.exec_module(export)
from server.ruby_marshal import dumps_simple,integer

def dumps(value):
    # Inert fixture writer; production only reads the native engine export.
    if isinstance(value,dict):
        return b'\x04\x08'+b'{'+integer(len(value))+b''.join(dumps(k)[2:]+dumps(v)[2:] for k,v in value.items())
    if isinstance(value,list):return b'\x04\x08'+b'['+integer(len(value))+b''.join(dumps(v)[2:] for v in value)
    return dumps_simple(value)

class CampaignProfiles(unittest.TestCase):
    def fixture(self,root,source=b'current PBS'):
        game=root/'game';(game/'Data').mkdir(parents=True)
        masters={f'Leader {i}':[{'id':id,'origin':'blue-engine','team':[{'species':'PIKACHU'}]*6}
            for id in ['beginner','intermediate','advanced','master']] for i in range(18)}
        data={'version':1,'sourceCRC':zlib.crc32(source),'rulesCRC':export.campaign_rules_crc(),'masters':masters}
        (game/'Data/blue-campaign-reference.dat').write_bytes(dumps(data))
        return game,{'masters':[{'name':name} for name in masters]}
    def test_imports_only_matching_native_profiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            game,roster=self.fixture(Path(tmp))
            self.assertTrue(export.campaign_profiles(game,roster,b'current PBS'))
            self.assertEqual(len(roster['masters']),18)
            self.assertTrue(all(len(t['campaignVariants'])==4 for t in roster['masters']))
    def test_source_change_does_not_publish_stale_teams(self):
        with tempfile.TemporaryDirectory() as tmp:
            game,roster=self.fixture(Path(tmp));export.campaign_profiles(game,roster,b'current PBS')
            self.assertTrue(export.campaign_profiles(game,roster,b'changed PBS'))
            self.assertTrue(all('campaignVariants' not in t for t in roster['masters']))
    def test_incomplete_native_profiles_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            game,roster=self.fixture(Path(tmp))
            data={'version':1,'sourceCRC':zlib.crc32(b'current PBS'),'rulesCRC':export.campaign_rules_crc(),'masters':{}}
            (game/'Data/blue-campaign-reference.dat').write_bytes(dumps(data))
            with self.assertRaises(ValueError):export.campaign_profiles(game,roster,b'current PBS')
    def test_rule_changes_invalidate_previous_profiles(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            game,roster=self.fixture(Path(tmp));export.campaign_profiles(game,roster,b'current PBS')
            with patch.object(export,'campaign_rules_crc',return_value=0):
                self.assertTrue(export.campaign_profiles(game,roster,b'current PBS'))
            self.assertTrue(all('campaignVariants' not in t for t in roster['masters']))

if __name__=='__main__':unittest.main()
