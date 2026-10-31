"""Restoration writes are transactional and reject stale inputs."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts' / 'official_rules'))
import apply_restore
import restore

def sha(data):
    return hashlib.sha256(data).hexdigest()

class OfficialRulesSafetyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.game = self.root / 'game'
        self.work = self.root / 'cache'
        self.stage = self.work / 'staged'
        (self.game / 'Data').mkdir(parents=True)
        (self.game / 'Data' / 'Map001.rxdata').write_bytes(b'original-map')
        self.original = {'PBS/pokemon.txt': b'old-species', 'PBS/moves.txt': b'old-moves'}
        plan = []
        for relative, before in self.original.items():
            target = self.game / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(before)
            source = self.stage / relative
            source.parent.mkdir(parents=True, exist_ok=True)
            after = b'new-' + before
            source.write_bytes(after)
            plan.append({'path':relative, 'before':sha(before), 'after':sha(after)})
        (self.work / 'plan.json').write_text(json.dumps({'files':plan}), encoding='utf-8')
        (self.work / 'static-validation.json').write_text('{"result":"PASS"}', encoding='utf-8')
        context = patch.multiple(apply_restore, ROOT=self.work, GAME=self.game, STAGE=self.stage)
        context.start()
        self.addCleanup(context.stop)

    def test_success_preserves_map_and_backs_up_originals(self):
        apply_restore.main(['--apply'])
        manifest = json.loads((self.work / 'applied.json').read_text(encoding='utf-8'))
        backup = Path(manifest['backup'])
        for relative, before in self.original.items():
            self.assertEqual((backup / relative).read_bytes(), before)
            self.assertEqual((self.game / relative).read_bytes(), b'new-' + before)
        self.assertEqual((self.game / 'Data' / 'Map001.rxdata').read_bytes(), b'original-map')

    def test_stale_input_is_rejected_before_any_backup_or_write(self):
        (self.game / 'PBS' / 'moves.txt').write_bytes(b'edit-from-another-tool')
        with self.assertRaises(AssertionError):
            apply_restore.main(['--apply'])
        self.assertEqual((self.game / 'PBS' / 'pokemon.txt').read_bytes(), b'old-species')
        self.assertFalse((self.root / '.blue-backups').exists())

    def test_write_failure_rolls_back_previously_written_files(self):
        real_atomic = apply_restore.atomic
        failed = False
        def fail_second(path, data):
            nonlocal failed
            if path == self.game / 'PBS' / 'moves.txt' and not failed:
                failed = True
                raise OSError('Simulated disk failure')
            return real_atomic(path, data)
        with patch.object(apply_restore, 'atomic', side_effect=fail_second):
            with self.assertRaisesRegex(OSError, 'Simulated disk failure'):
                apply_restore.main(['--apply'])
        for relative, before in self.original.items():
            self.assertEqual((self.game / relative).read_bytes(), before)

    def test_untrusted_reference_hash_is_rejected_without_downloading(self):
        archive = self.root / 'invalid.zip'
        archive.write_bytes(b'untrusted-archive')
        with patch.object(restore, 'download') as download:
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                restore.references(self.work / 'references', archive, self.root / 'invalid.rar')
            download.assert_not_called()
