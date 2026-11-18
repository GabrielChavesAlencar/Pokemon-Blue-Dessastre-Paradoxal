"""Kanto FRLG download provenance: offline pinned-digest regression.

Uses only tracked JSON and YAML source. No network, copyrighted assets, maps,
native installer, Game.exe, JoiPlay or saves. Does not approve another archive.
"""
from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"data/regions/kanto-source.json"
WORKFLOW=ROOT/".github/workflows/kanto-pilot-check.yml"
PINNED="48883c8217bcd9e7fa1b9446bddaa9db5f9715a7ba73ac02785b6660769e2683"
FILE_ID="1dsqD8lEJCz-lioEruRqQycWJLCUVxVtI"

class FRLGSourcePinningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.workflow=WORKFLOW.read_text(encoding="utf-8")

    def test_pinned_manifest_not_rewritten(self):
        self.assertEqual(self.manifest["region"],"KANTO")
        self.assertEqual(self.manifest["sha256"],PINNED)
        self.assertRegex(PINN,r"^[0-9a-f]{64}$")

    def test_source_attributed_and_not_redistributed(self):
        self.assertEqual(self.manifest["source"],"https://eeveeexpo.com/resources/1797/")
        self.assertEqual(self.manifest["author"],"TheTinfoilTemplar")
        self.assertIn("do not redistribute the archive",self.manifest["policy"])

    def test_fallback_uses_same_original_file_id_only(self):
        matches=re.findall(r"https://(?:drive\.usercontent\.google\.com|drive\.google\.com)/[^\s',]+",self.workflow)
        self.assertEqual(len(matches),3)
        for url in matches:
            self.assertIn(FILE_ID,url)
            self.assertIn("confirm=t",url)
        self.assertEqual(self.workflow.count(FILE_ID),3)

    def test_checksum_guard_runs_before_archival_read(self):
        code=self.workflow
        self.assertIn("$expected=[string]$manifest.sha256",code)
        self.assertIn("$hash=(Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()",code)
        self.assertIn("if($hash -ceq $expected){$verified=$true;break}",code)
        self.assertIn("if(-not $verified){",code)
        self.assertIn("throw 'FRLG archive hash differs from pinned manifest; no pilot can be built'",code)
        self.assertLess(code.index("if(-not $verified){"),code.index("$entries=@(tar -tf $archive"))
        self.assertLess(code.index("$entries=@(tar -tf $archive"),code.index("tar -xf $archive"))

    def test_failed_source_is_deleted_not_extracted(self):
        code=self.workflow
        self.assertIn("Remove-Item -LiteralPath $archive -Force -ErrorAction SilentlyContinue",code)
        self.assertIn("try { Invoke-WebRequest",code)
        self.assertIn("catch { Write-Warning",code)
        self.assertNotIn("continue-on-error: true\n        shell: powershell\n        run: |\n          $ProgressPreference",code[:1800])

    def test_fake_archive_cannot_have_pinned_sha(self):
        forged=b"<html>Google Drive download confirmation</html>"
        self.assertNotEqual(hashlib.sha256(forged).hexdigest(),PINNED)
        self.assertNotEqual(hashlib.sha256(b"tampered FRLG archive").hexdigest(),PINNED)

if __name__=="__main__":unittest.main()
