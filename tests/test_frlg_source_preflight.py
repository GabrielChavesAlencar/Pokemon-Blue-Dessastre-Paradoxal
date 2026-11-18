"""Offline synthetic negative tests only; no game, network or archives."""
import importlib.util,io,json,os,socket,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("frlg_source_preflight",ROOT/"tools/frlg_source_preflight.py")
f=importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)

class SourceOnlyTests(unittest.TestCase):
    def test_manifest_pin(self):
        self.assertEqual(f.validate_manifest(),f.PIN)
    def changed_manifest(self,key,value):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"pin.json"
            obj=json.loads(f.MANIFEST.read_text())
            obj[key]=value
            p.write_text(json.dumps(obj))
            with self.assertRaises(f.SourceRejected): f.validate_manifest(p)
    def test_changed_sha(self): self.changed_manifest("sha256","0"*64)
    def test_changed_source(self): self.changed_manifest("source","https://example.org/")
    def test_changed_author(self): self.changed_manifest("author","fake")
    def test_missing_rights_guard(self): self.changed_manifest("policy","free redistribution")
    def test_html_quota(self):
        with self.assertRaises(f.SourceRejected): f.verify_stream(io.BytesIO(b"<html>Too many users</html>"))
    def test_zip(self):
        with self.assertRaises(f.SourceRejected): f.verify_stream(io.BytesIO(b"PK\x03\x04zip"))
    def test_forged_rar(self):
        with self.assertRaises(f.SourceRejected): f.verify_stream(io.BytesIO(f.RAR5+b"not original"))
    def test_truncated_archive(self):
        with self.assertRaises(f.SourceRejected): f.verify_stream(io.BytesIO(b""))
    def test_size_limit(self):
        with self.assertRaises(f.SourceRejected): f.verify_stream(io.BytesIO(f.RAR5+b"hello"),limit=5)
    def test_invalid_pin(self):
        with self.assertRaises(f.SourceRejected): f.verify_stream(io.BytesIO(f.RAR5),expected="fake")
    def test_missing_file(self):
        with self.assertRaises(f.SourceRejected): f.verify_file("/not/an/existing/file.rar")
    def test_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"target"
            p.write_bytes(f.RAR5)
            l=Path(d)/"link"
            l.symlink_to(p)
            with self.assertRaises(f.SourceRejected): f.verify_file(l)
    def test_missing_secret(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(f.SourceRejected): f.verify_secret_url()
    def test_http(self):
        with self.assertRaises(f.SourceRejected): f.require_https("http://example.org/a")
    def test_url_credentials(self):
        with self.assertRaises(f.SourceRejected): f.require_https("https://u:p@example.org/a")
    def test_private_hosts(self):
        for u in ("https://localhost/x","https://127.0.0.1/x","https://169.254.169.254/x","https://[::1]/x"):
            with self.subTest(u=u):
                with self.assertRaises(f.SourceRejected): f.require_https(u)
    def test_host_not_allowlisted(self):
        with self.assertRaises(f.SourceRejected):
            f.require_https("https://mirror.example.org/file.rar","cdn.example.org")
    def test_host_allowlisted(self):
        f.require_https("https://cdn.example.org/file.rar?token=secret","cdn.example.org")
    def test_missing_host_secret(self):
        with patch.dict(os.environ,{"FRLG_SOURCE_URL":"https://example.org/file.rar"},clear=True):
            with self.assertRaises(f.SourceRejected): f.verify_secret_url()
    def test_private_dns_rejected(self):
        private=[(socket.AF_INET,socket.SOCK_STREAM,6,"",("127.0.0.1",443))]
        with patch.object(f.socket,"getaddrinfo",return_value=private):
            with self.assertRaises(f.SourceRejected): f.require_public_dns("example.org")
    def test_public_dns_pass(self):
        public=[(socket.AF_INET,socket.SOCK_STREAM,6,"",("8.8.8.8",443))]
        with patch.object(f.socket,"getaddrinfo",return_value=public):
            f.require_public_dns("example.org")
    def test_redirect_downgrade(self):
        request=f.urllib.request.Request("https://example.org/a")
        with self.assertRaises(f.SourceRejected):
            f.NoRedirects().redirect_request(request,None,302,"redirect",{},"http://example.org/a")
    def test_redirect_even_if_https_is_rejected(self):
        request=f.urllib.request.Request("https://cdn.example.org/start")
        with self.assertRaises(f.SourceRejected):
            f.NoRedirects().redirect_request(request,None,302,"redirect",{},"https://cdn.example.org/redirect")
    def test_config_cli(self):
        self.assertEqual(f.main(["--check-config"]),0)
    def test_missing_source_cli(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertEqual(f.main(["--from-secret-env"]),1)

if __name__=="__main__": unittest.main()
