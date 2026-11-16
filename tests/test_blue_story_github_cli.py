"""Regressões offline da CLI automática e do botão Publicar do Johto."""
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.windows import github_cli


class BlueStoryGithubCliTests(unittest.TestCase):
    def test_installation_reuses_portable_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            exe = project / "tools/gh/gh.exe"
            exe.parent.mkdir(parents=True)
            exe.write_bytes(b"already installed locally")
            with patch.object(github_cli, "_read") as download:
                self.assertEqual(github_cli.ensure_cli(project), str(exe))
                download.assert_not_called()

    def test_release_asset_hash_is_verified(self):
        asset = {"name": "gh_2.9.0_windows_amd64.zip", "digest": "sha256:" + "a" * 64}
        self.assertEqual(github_cli._expected_hash({"assets": []}, asset), "a" * 64)

    def test_checksums_file_fallback(self):
        asset = {"name": "gh_2.9.0_windows_amd64.zip"}
        release = {"assets": [{
            "name": "gh_2.9.0_checksums.txt",
            "browser_download_url": github_cli.RELEASE_DOWNLOAD + "v2.9.0/gh_2.9.0_checksums.txt"
        }]}
        with patch.object(github_cli, "_read", return_value=("b" * 64 + "  " + asset["name"] + "\n").encode()):
            self.assertEqual(github_cli._expected_hash(release, asset), "b" * 64)

    def test_missing_hash_rejected_before_installation(self):
        with self.assertRaisesRegex(RuntimeError, "SHA-256"):
            github_cli._expected_hash({"assets": []}, {"name": "gh_1_windows_amd64.zip"})

    @unittest.skipUnless(shutil.which("node"), "Node.js não disponível neste runner")
    def test_inline_editor_javascript_is_valid(self):
        html = (ROOT / "web/johto-map-editor.html").read_text("utf-8")
        script = html.split("<script>", 1)[1].split("</script>", 1)[0]
        result = subprocess.run(["node", "--check", "-"], input=script,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
