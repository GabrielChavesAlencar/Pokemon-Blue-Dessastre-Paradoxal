"""Integration checks for the shared installer and Android release guard."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts/regions")]

import sinnoh_shared as shared
import prepare_sinnoh_shared as candidate
from stage_sinnoh_shared_qa import QA_DIR, stage as stage_qa
from scripts.android.package import REGION_START_PLUGIN, REGION_TRAVEL_PLUGIN
from scripts.android.update_client import _preserve_shared_sinnoh
from server.ruby_marshal import RubyData, RubyObject
from stage import serialize


class SinnohSharedInstallerTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.project = Path(tmp.name).resolve()
        self.game = self.project / "game"
        self.overlay = self.project / ".blue-work/sinnoh-shared"

        def table(data):
            raw = struct.pack("<5I", 1, len(data), 1, 1, len(data))
            return RubyData("Table", raw + struct.pack(f"<{len(data)}H", *data))

        tileset = RubyObject("RPG::Tileset", {"@passages": table([0, 0]), "@terrain_tags": table([0, 0])})
        map_data = RubyData("Table",struct.pack("<5I",3,4,4,3,48)+struct.pack("<48H",*([1]*16+[0]*32)))
        world = RubyObject("RPG::Map", {"@width":4,"@height":4,"@tileset_id":2,"@events":{},"@data":map_data})
        self.base = {shared.MAP_INFOS:serialize({1:b"Decades"}),shared.TILESETS:serialize([None,tileset]),
                     shared.CONNECTIONS:serialize([]),shared.PBS_CONNECTIONS:b"# Existing regions\n",
                     "PBS/encounters.txt":b"[001]\nLand,20\n100,PIDGEY,4\n"}
        self.files = {shared.MAP_INFOS:serialize({1:b"Decades", **dict.fromkeys(range(442,586), b"Example"), 443:RubyObject("RPG::MapInfo", {"@name": b"Twinleaf Town"})}),
                      shared.TILESETS:serialize([None,tileset,tileset]),
                      shared.CONNECTIONS:serialize([[442,b"E",0,443,b"W",0]]),
                      shared.PBS_CONNECTIONS:self.base[shared.PBS_CONNECTIONS]+b"442,E,0,443,W,0\n",
                      shared.PLUGIN:b"module BlueSinnohSharedEvents; end\n",
                      shared.META:b"Scripts = SinnohSharedEvents.rb\n"}
        self.files.update({f"Data/Map{n:03d}.rxdata":serialize(world) for n in range(442,586)})
        self.approvals={"map_ids":True,"asset_rights":True,"connected_world":True,"windows_travel":True}
        for rel, raw in self.base.items():
            self.put(self.game / rel, raw)
        self.put(self.game / 'Data/Map001.rxdata', b'original Decades map')
        self.put(self.game / 'Data/PluginScripts.rxdata', b'previous plugin cache')
        self.put(self.game / 'mkxp.json', b'shared save settings')
        self.put(self.game / 'Saves/Game.rxdata', b'existing save')

    def put(self, path, raw):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def test_shared_reservation_is_disjoint_from_clean_kanto_and_migration(self):
        from audit import allocate_kanto_ids
        wanted = {int(mid) for mid in json.loads(
            (ROOT/"data/regions/kanto-source.json").read_text("utf-8"))["maps"]}
        clean_ids = allocate_kanto_ids(wanted, {1, 299})
        previous = {src:dst for src,dst in clean_ids.items() if src not in range(43,49)}
        migrated_ids = allocate_kanto_ids(wanted, set(previous.values()) | {1, 299, 898}, previous)
        pinned = json.loads((ROOT/candidate.MAP_RESERVATION).read_text("utf-8"))
        self.assertEqual(sorted(pinned.values()),list(shared.SHARED_IDS))
        self.assertFalse(set(pinned.values()) & set(clean_ids.values()))
        self.assertFalse(set(pinned.values()) & set(migrated_ids.values()))

    def test_author_download_tries_canonical_and_short_urls_for_html_response(self):
        import sinnoh_source_download as source
        from urllib.error import HTTPError
        from urllib.response import addinfourl
        from io import BytesIO
        canonical, short = source.PAGES["maps"]
        target = "https://mega.nz/file/" + source.MEGA_ID
        page = addinfourl(BytesIO(b"<html/>"),{},canonical,200)
        redirect = HTTPError(short,301,"Moved",{"Location":target},BytesIO())
        with patch.object(source,"build_opener") as opener:
            request = opener.return_value.open
            request.side_effect = [page,redirect]
            self.assertEqual(source.source_redirect("maps"),target)
            self.assertEqual([call.args[0].full_url for call in request.call_args_list],[canonical,short])
        with patch.object(source,"redirect_location",return_value=None):
            with self.assertRaisesRegex(TimeoutError,"DOWNLOAD_SOURCE_DID_NOT_REDIRECT"):
                source.source_redirect("maps")

    def prepare(self):
        for rel, raw in self.files.items():
            self.put(self.overlay / rel,raw)
        proof = {"schema":1,"profile":"BLUE_SINNOH_SHARED_V1","map_ids":list(range(442,586)),
                 "approvals":self.approvals,"start":[442,1,1],"arrival":[443,1,1],"agent":[443,2,1],
                 "base":{p:shared.sha(raw) for p,raw in self.base.items() if p in self.files},
                 "files":{p:shared.sha(raw) for p,raw in self.files.items()}}
        self.put(self.overlay / 'manifest.json', json.dumps(proof).encode())
        return proof

    def test_shared_overlay_is_installed_once_and_can_be_verified_for_android(self):
        self.assertFalse(shared.integrate(self.project,self.game)['changed'])
        self.approvals.update(joiplay_travel=True,android_distribution=True)
        self.prepare()
        self.assertTrue(shared.integrate(self.project,self.game)['changed'])
        self.assertFalse(shared.integrate(self.project,self.game)['changed'])
        self.assertEqual(shared.installed(self.game,android=True)['arrival'],[443,1,1])
        self.assertEqual((self.game / 'Data/Map001.rxdata').read_bytes(),b'original Decades map')
        self.assertEqual((self.game / 'mkxp.json').read_bytes(),b'shared save settings')
        self.assertEqual((self.game / 'Saves/Game.rxdata').read_bytes(),b'existing save')

    def test_verified_local_sources_enable_sinnoh_in_the_managed_game(self):
        proof = self.prepare()
        (self.overlay/"manifest.json").unlink()
        proof.update(profile="BLUE_SINNOH_SHARED_CANDIDATE_V1",
                     map_symbols={"SINNOH_PLAYER_BEDROOM":442,"SINNOH_TWINLEAF_TOWN":443,
                                  **{f"SINNOH_MAP_{mid}":mid for mid in range(444,586)}})
        proof["approvals"] = dict.fromkeys((*self.approvals,"joiplay_travel","android_distribution"),False)

        def prepare_main(project,game,*,candidate_dir):
            self.assertEqual((project,game),(self.project,self.game))
            for rel, raw in self.files.items():
                self.put(candidate_dir/"world"/rel,raw)
            return proof

        with patch.object(shared,"SHARED_IDS",range(442,586)), \
             patch("sinnoh_private_visual.discover",return_value={"maps":True,"overworlds":True}), \
             patch.object(candidate,"prepare",side_effect=prepare_main) as generator:
            self.assertTrue(shared.integrate(self.project,self.game)["changed"])
            self.assertFalse(shared.integrate(self.project,self.game)["changed"])
            self.assertEqual(shared.installed(self.game,local=True)["start"],[442,1,1])
            with self.assertRaises(ValueError):
                shared.installed(self.game,android=True,local=True)
            generator.assert_called_once()
        self.assertTrue((self.game/shared.LOCAL_MARKER).is_file())
        self.assertFalse((self.game/shared.QA_MARKER).exists())
        self.assertEqual((self.game/"Saves/Game.rxdata").read_bytes(),b"existing save")

    def test_installer_recovers_after_process_dies_during_marker_publication(self):
        self.prepare()
        crash = """
import os
from pathlib import Path
import sys
import sinnoh_shared as shared

project = Path(sys.argv[1])
write = shared.atomic
def stop_after_receipt(path, raw):
    write(path, raw)
    if path == project / "game" / shared.RECEIPT:
        os._exit(57)
shared.atomic = stop_after_receipt
shared.integrate(project, project / "game")
"""
        env_path = str(ROOT / "scripts/regions")
        result = subprocess.run(
            [sys.executable,"-c","import sys; sys.path[:0] = sys.argv[2:4]\n" + crash,
             str(self.project),env_path,str(ROOT)], cwd=ROOT, capture_output=True, timeout=30)
        self.assertEqual(result.returncode,57,result.stderr.decode())
        self.assertTrue((self.game / shared.INSTALL_JOURNAL).is_file())
        self.assertTrue((self.game / shared.RECEIPT).is_file())
        self.assertFalse((self.game / shared.START).exists())
        self.assertTrue(shared.recover(self.project,self.game))
        self.assertFalse((self.game / shared.RECEIPT).exists())
        self.assertFalse((self.game / "Data/Map442.rxdata").exists())
        self.assertEqual((self.game / shared.PLUGIN_CACHE).read_bytes(),b"previous plugin cache")
        for rel, raw in self.base.items():
            self.assertEqual((self.game / rel).read_bytes(),raw)
        self.assertEqual((self.game / "Saves/Game.rxdata").read_bytes(),b"existing save")
        self.assertTrue(shared.integrate(self.project,self.game)["changed"])
        self.assertFalse((self.game / shared.INSTALL_JOURNAL).exists())

    def test_shared_candidate_uses_144_maps_without_pilot_or_approval(self):
        outputs = dict(self.files)
        outputs["Game.ini"] = b"isolated title"
        outputs["Data/Scripts.rxdata"] = b"isolated scripts"
        outputs["PBS/encounters.txt"] = self.base["PBS/encounters.txt"] + b"[442]\nLand,20\n100,STARLY,4\n"
        report = {"maps_prepared":144,
                  "mapids":{"SINNOH_TWINLEAF_TOWN":443,"SINNOH_PLAYER_BEDROOM":442,
                            **{f"MAP_{mid}":mid for mid in range(444,586)}},
                  "start":[442,1,1],"private_visual_import":{"maps":{
                      "SINNOH_TWINLEAF_TOWN":{"source_id":194,"target_id":443}}}}
        from sinnoh_private_visual import SEEDS
        with patch.dict(SEEDS, {"SINNOH_TWINLEAF_TOWN":(1,1)}):
            world, review, proof = candidate.prepare_world(self.game,outputs,report)
        self.assertEqual(len(proof["map_ids"]),144)
        self.assertEqual(proof["arrival"][0],443)
        self.assertEqual(proof["agent"][0],443)
        self.assertNotIn("Game.ini",world)
        self.assertNotIn("Data/Scripts.rxdata",world)
        self.assertIn(shared.PLUGIN,world)
        self.assertIn("PBS/encounters.txt",world)
        self.assertFalse(any(proof["approvals"].values()))
        self.assertFalse(proof["runtime_install_enabled"])
        self.assertFalse((self.game / "Data/Map442.rxdata").exists())
        self.assertEqual((self.game / "Saves/Game.rxdata").read_bytes(),b"existing save")
        with self.assertRaises(ValueError):
            shared.validate_manifest(proof)
        proof["profile"] = shared.QA_PROFILE
        proof["map_symbols"] = {("SINNOH_" + key if key.startswith("MAP_") else key):mid
                                for key,mid in proof["map_symbols"].items()}
        shared.validate_manifest(proof,qa=True)
        with self.assertRaises(ValueError):
            shared.validate_manifest(proof,android=True)

    def test_occupied_twinleaf_portal_keeps_its_event(self):
        world = shared.read_marshal(self.files["Data/Map443.rxdata"],"TEST_TWINLEAF")
        portal = RubyObject("RPG::Event",{"@name":b"SN_TOWN_TO_ROUTE201","@x":1,"@y":1})
        world.attrs["@events"][1] = portal
        tiles = shared.read_marshal(self.files[shared.TILESETS],"TEST_TILESETS")
        arrival, agent = candidate.choose_town_points(world,tiles,(1,1))
        self.assertNotIn((1,1),(arrival,agent))
        self.assertIs(world.attrs["@events"][1],portal)

    def test_shared_windworks_checks_shared_catalog_instead_of_private_barry_probe(self):
        template = (ROOT/"scripts/regions/SinnohF12B5.rb").read_bytes()
        payload = candidate.shared_handlers(ROOT,[template])[shared.PLUGIN]
        windworks = payload.split(b"module BlueSinnohF12B5",1)[1]
        self.assertIn(b"return false if @busy || !BlueSinnohSharedEvents.ready?",windworks)
        self.assertNotIn(b"BlueSinnohExperimental",windworks)

    def test_map_pbs_preserves_other_regions_and_rejects_duplicate_ids(self):
        rel = "PBS/encounters.txt"
        original = self.base[rel]
        with self.assertRaisesRegex(ValueError,"outras regiões"):
            shared.preserve_map_pbs(rel,original,original.replace(b"PIDGEY",b"STARLY"),{442})
        with self.assertRaisesRegex(ValueError,"duplicados"):
            shared.preserve_map_pbs(rel,original,original+b"[1,0]\n",{442})

    def test_staging_copies_the_windows_root_and_uses_a_qa_save_namespace(self):
        proof = self.prepare()
        proof.update(profile="BLUE_SINNOH_SHARED_CANDIDATE_V1",runtime_install_enabled=False,
                     map_symbols={"SINNOH_PLAYER_BEDROOM":442,"SINNOH_TWINLEAF_TOWN":443,
                                  **{f"SINNOH_MAP_{mid}":mid for mid in range(444,586)}})
        proof["approvals"] = dict.fromkeys((*self.approvals,"joiplay_travel","android_distribution"),False)
        folder = self.project / candidate.CANDIDATE
        self.put(folder/"candidate.json",json.dumps(proof).encode())
        for rel, data in self.files.items():
            self.put(folder/"world"/rel,data)
        for rel in ("Game.exe","Game.ini","Data/Scripts.rxdata","Data/System.rxdata"):
            self.put(self.game/rel,b"staged fixture")
        self.put(self.game/"mkxp.json",b'{"dataPathApp":"BlueStory"}')
        for rel in (REGION_START_PLUGIN,REGION_TRAVEL_PLUGIN,
                    "Plugins/ZZZZ Blue Story and Presentation/TitleKanto.rb"):
            self.put(self.game/rel,b"# regional source\n")
            self.put(self.project/"scripts/battle_polish"/Path(rel).name,b"# regional source\n")
        staged = stage_qa(self.project)
        qa = self.project / QA_DIR / "game"
        self.assertEqual(staged["maps"],144)
        self.assertEqual(shared.installed(qa,qa=True)["profile"],shared.QA_PROFILE)
        self.assertTrue(json.loads((qa/"mkxp.json").read_bytes())["dataPathApp"].startswith("BlueStorySinnohSharedQA-"))
        self.assertEqual((self.game/"mkxp.json").read_bytes(),b'{"dataPathApp":"BlueStory"}')
        self.assertFalse((qa/"Saves/Game.rxdata").exists())

    def test_story_preserves_each_foreign_connection_index_as_installed(self):
        local = [442,b"E",0,443,b"W",0]
        native = [[1,b"N",0,2,b"S",1],local]
        pbs = b"1,N,0,2,S,2\n442,E,0,443,W,0\n"
        original = {shared.CONNECTIONS:serialize(native),shared.PBS_CONNECTIONS:pbs}
        ids = {442,443,444}
        scope = candidate.story_connection_scope(original,ids)
        added = [443,b"S",0,444,b"N",0]
        expanded = {shared.CONNECTIONS:serialize([local,added]),
                    shared.PBS_CONNECTIONS:scope[shared.PBS_CONNECTIONS]+b"443,S,0,444,N,0\n"}
        merged = candidate.restore_foreign_connections(original,scope,expanded,ids)
        self.assertEqual(shared.read_marshal(merged[shared.CONNECTIONS],"TEST_SCOPE"),native+[added])
        self.assertEqual(merged[shared.PBS_CONNECTIONS],pbs+b"443,S,0,444,N,0\n")

    def test_agent_cannot_be_placed_in_a_later_town(self):
        infos = shared.read_marshal(self.files[shared.MAP_INFOS], "TEST_INFOS")
        infos[443].attrs["@name"] = b"Sandgem Town"
        self.files[shared.MAP_INFOS] = serialize(infos)
        self.prepare()
        with self.assertRaisesRegex(ValueError, 'Twinleaf Town'):
            shared.integrate(self.project,self.game)
        self.assertFalse((self.game / shared.START).exists())
        self.assertEqual((self.game / 'Saves/Game.rxdata').read_bytes(),b'existing save')

    def test_mismatched_base_or_pilot_config_cannot_be_installed(self):
        self.prepare()
        self.put(self.game / 'Data/Map442.rxdata',b'unrelated map')
        with self.assertRaisesRegex(ValueError, 'já existem'):
            shared.integrate(self.project,self.game)
        self.assertEqual((self.game / 'Data/Map442.rxdata').read_bytes(),b'unrelated map')
        self.files['mkxp.json']=b'pilot settings'
        self.prepare()
        with self.assertRaisesRegex(ValueError, 'fora do overlay'):
            shared.integrate(self.project,self.game)
        self.assertFalse((self.game / shared.START).exists())

    def test_windows_approval_does_not_make_sinnoh_distributable_on_android(self):
        proof = self.prepare()
        shared.validate_manifest(proof)
        with self.assertRaisesRegex(ValueError,'esta plataforma'):
            shared.validate_manifest(proof,android=True)
        old = {shared.START:{},shared.RECEIPT:{},'Data/Map443.rxdata':{}}
        with self.assertRaisesRegex(ValueError,'removeria Sinnoh'):
            _preserve_shared_sinnoh(old,{shared.START:{},shared.RECEIPT:{}})

    def test_failed_install_restores_world_indexes_and_previous_cache(self):
        self.prepare()
        atomic = shared.atomic
        def fail_at_gate(path, data):
            if path == self.game / shared.START:
                raise OSError('write interrupted')
            atomic(path, data)
        with patch.object(shared,'atomic',side_effect=fail_at_gate):
            with self.assertRaisesRegex(OSError, 'write interrupted'):
                shared.integrate(self.project,self.game)
        for rel,raw in self.base.items():
            self.assertEqual((self.game / rel).read_bytes(),raw)
        self.assertEqual((self.game / 'Data/PluginScripts.rxdata').read_bytes(),b'previous plugin cache')
        self.assertFalse((self.game / shared.RECEIPT).exists())
        self.assertFalse((self.game / 'Data/Map442.rxdata').exists())


if __name__ == '__main__':
    unittest.main()
