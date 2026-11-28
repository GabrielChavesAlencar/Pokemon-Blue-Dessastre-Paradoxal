"""U02 synthetic ZIP metadata tests: never reads real donor assets."""
import contextlib
import io
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts' / 'regions'))
import audit_unova_u02 as u02


class SourceInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sources = self.root / '.blue-work/unova/sources'
        self.sources.mkdir(parents=True)
        self.zip = self.sources / 'Pokemon_World_V18.zip'

    def put_zip(self, members):
        with zipfile.ZipFile(self.zip, 'w') as z:
            for name, data in members:
                # Keep malformed path bytes intact even on Windows.
                entry = zipfile.ZipInfo(name)
                entry.filename = name
                z.writestr(entry, data)
        return self.zip

    def basic(self):
        return [
            ('World/Data/MapInfos.rxdata', b'x'),
            ('World/Data/Tilesets.rxdata', b'x'),
            ('World/Data/Map001.rxdata', b'not a real map'),
            ('World/Data/Map002.rxdata', b'not a real map'),
            ('World/Graphics/Characters/npc.png', b'png'),
            ('World/Audio/BGM/theme.ogg', b'audio'),
            ('World/PBS/trainers.txt', b'trainers'),
        ]

    def test_01_zip_inventory_does_not_claim_unova_maps_or_rights(self):
        self.put_zip(self.basic())
        result = u02.audit_zip(self.zip)
        self.assertEqual(result['all_regions_source_map_count'], 2)
        self.assertIsNone(result['unova_map_ids'])
        self.assertIsNone(result['unova_map_count'])
        self.assertFalse(result['map_names_from_mapinfos_verified'])
        self.assertFalse(result['rights_per_asset_verified'])
        self.assertFalse(result['can_install'])
        self.assertFalse(result['game_or_saves_modified'])
        self.assertEqual(result['assets_by_folder']['Graphics/Characters']['count'], 1)
        self.assertEqual(result['assets_by_folder']['Audio/BGM']['count'], 1)

    def test_02_no_source_blocks_without_inventing_map_count(self):
        result = u02.missing_source_report()
        self.assertEqual(result['status'], 'BLOCKED_SOURCE_NOT_PROVIDED')
        self.assertIsNone(result['all_regions_source_map_count'])
        self.assertFalse(result['can_install'])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = u02.main(['--project', str(self.root)])
        self.assertEqual(code, 2)

    def test_03_zip_traversal_and_absolute_paths_block(self):
        for name in ('../Map002.rxdata', '/absolute', 'foo\\bar', 'C:/windows', 'foo/./bar'):
            with self.subTest(name=name):
                self.put_zip(self.basic() + [(name, b'x')])
                with self.assertRaises(ValueError):
                    u02.audit_zip(self.zip)

    def test_04_duplicate_casefold_names_block(self):
        self.put_zip(self.basic() + [('world/data/MAP001.rxdata', b'x')])
        with self.assertRaisesRegex(ValueError, 'duplicada'):
            u02.audit_zip(self.zip)

    def test_05_duplicate_numeric_map_ids_block(self):
        self.put_zip(self.basic() + [('World/Data/Map1.rxdata', b'x')])
        with self.assertRaisesRegex(ValueError, 'MapID fonte duplicado'):
            u02.audit_zip(self.zip)

    def test_06_no_mapinfos_or_multiple_data_roots_block(self):
        self.put_zip([p for p in self.basic() if 'MapInfos' not in p[0]])
        with self.assertRaises(ValueError):
            u02.audit_zip(self.zip)
        self.put_zip(self.basic() + [('Other/Data/MapInfos.rxdata',b'x'),('Other/Data/Tilesets.rxdata',b'x')])
        with self.assertRaises(ValueError):
            u02.audit_zip(self.zip)

    def test_07_zip_symlink_member_blocks(self):
        with zipfile.ZipFile(self.zip, 'w') as z:
            for name, contents in self.basic():
                z.writestr(name,contents)
            info = zipfile.ZipInfo('World/evil')
            info.create_system = 3
            info.external_attr = ((stat.S_IFLNK | 0o777) << 16)
            z.writestr(info,'/game')
        with self.assertRaisesRegex(ValueError, 'simbolico'):
            u02.audit_zip(self.zip)

    def test_08_external_source_and_symlink_block(self):
        outside = self.root / 'outside.zip'
        outside.write_bytes(b'test')
        self.assertFalse(u02.is_within_source(self.root,outside))
        try:
            link = self.sources / 'link.zip'
            link.symlink_to(outside)
        except OSError:
            self.skipTest('symlinks unavailable')
        self.assertFalse(u02.is_within_source(self.root,link))

    def test_09_report_only_under_blue_work_and_no_fake_signoff(self):
        self.put_zip(self.basic())
        before = self.zip.read_bytes()
        report = u02.audit_zip(self.zip)
        dest = u02.write_report(self.root, report)
        self.assertTrue(dest.is_relative_to(self.root/'.blue-work/unova/audit'))
        self.assertEqual(before,self.zip.read_bytes())
        report['can_install']=True
        with self.assertRaises(ValueError):
            u02.write_report(self.root,report)

    def test_10_symlink_report_directory_blocks(self):
        self.put_zip(self.basic())
        dest = self.root/'.blue-work/unova/audit'
        outside=self.root/'elsewhere'
        outside.mkdir()
        try:
            dest.symlink_to(outside,target_is_directory=True)
        except OSError:
            self.skipTest('symlinks unavailable')
        with self.assertRaisesRegex(ValueError, 'insegura'):
            u02.write_report(self.root,u02.audit_zip(self.zip))

    def test_11_cli_with_zip_writes_report_and_does_not_install(self):
        self.put_zip(self.basic())
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            code=u02.main(['--project',str(self.root),'--write'])
        self.assertEqual(code,0)
        self.assertIn('"can_install": false',out.getvalue())
        self.assertFalse((self.root/'game').exists())

    def test_12_corrupt_zip_not_success(self):
        self.zip.write_bytes(b'corrupt')
        with self.assertRaises(zipfile.BadZipFile):
            u02.audit_zip(self.zip)


if __name__ == '__main__':
    unittest.main()
