"""E04 external-source probe: no network, fake rights or unsafe redirects in tests."""
from __future__ import annotations
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import unova_e04_remote_probe as probe


class RemoteProbeSafetyTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="unova-e04-remote-")
        self.addCleanup(temp.cleanup)
        self.project = Path(temp.name)

    def info(self,name,size=340):
        return {"filename":name,"size":str(size),"quickkey":"tq5w0in2xt2peb1"}

    def test_01_only_mediafire_https_allowed(self):
        for url in (
            "https://mediafire.com/file/key/test",
            "https://www.mediafire.com/file/key/test",
            "https://download100.mediafire.com/test.zip",
        ):
            self.assertTrue(probe.is_mediafire_url(url),url)

    def test_02_block_nonmediafire_and_embedded_domains(self):
        for url in (
            "http://www.mediafire.com/file/key",
            "https://evil.example/test",
            "https://mediafire.com.evil.example/test",
            "https://evilmediafire.com/test",
            "https://user:pass@www.mediafire.com/file/key",
            "file:///etc/passwd",
            "https://localhost/",
        ):
            self.assertFalse(probe.is_mediafire_url(url),url)

    def test_03_reject_redirect_off_provider(self):
        h=probe.SafeRedirect()
        with self.assertRaises(probe.SourceBlocked):
            h.redirect_request(None,None,302,"",{},"https://evil.example/test")

    def test_04_provider_info_size_must_be_numeric(self):
        with self.assertRaises(probe.SourceBlocked):
            probe.safe_meta({"filename":"Pokemon_World_V18.zip","size":"x"},"key")

    def test_05_api_quickkey_must_be_pinned(self):
        with self.assertRaises(probe.SourceBlocked):
            probe.get_api_file_info("unexpected_key")

    def test_06_json_metadata_is_not_rights_or_origin(self):
        values=[
            {"zip":{"filename":"Pokemon_World_V18.zip","size":"340"},
             "credits":{"filename":"Credits.txt","size":"30"}},
        ]
        with patch.object(probe,"get_api_file_info",side_effect=[
            values[0]["zip"],values[0]["credits"],
        ]):
            out=probe.probe(self.project,download=False)
        self.assertEqual(out["status"],"PROVIDER_METADATA_ONLY_NOT_SOURCE_AUDIT")
        self.assertFalse(out["zip_downloaded"])
        self.assertFalse(out["e04_complete"])
        self.assertIsNone(out["whole_donor_project_map_count"])
        self.assertFalse(out["may_redistribute"])
        self.assertFalse(out["may_install"])
        self.assertFalse(out["source_identity_verified_with_author"])

    def test_07_wrong_provider_filename_blocks_download(self):
        with patch.object(probe,"get_api_file_info",side_effect=[
            {"filename":"Malware.exe","size":"2"},
            {"filename":"Credits.txt","size":"2"},
        ]),patch.object(probe,"get_direct_link",side_effect=AssertionError("should not call")):
            out=probe.probe(self.project,download=False)
        self.assertIn("zip: NOME_ARQUIVO_DIVERGENTE",out["errors"])
        self.assertFalse(out["zip_downloaded"])

    def test_08_if_network_fails_report_remains_blocked(self):
        with patch.object(probe,"get_api_file_info",
                          side_effect=probe.SourceBlocked("API_BLOQUEADA")):
            out=probe.probe(self.project,download=True)
        self.assertEqual(out["status"],"BLOCKED_SOURCE_NOT_OBTAINED")
        self.assertTrue(out["errors"])
        self.assertFalse(out["zip_downloaded"])
        self.assertFalse(out["e04_complete"])
        self.assertFalse((self.project/"game").exists())

    def test_09_download_limit_check_before_network(self):
        with self.assertRaises(probe.SourceBlocked):
            probe.download_private(self.project,
                "https://download100.mediafire.com/some.zip",
                "Pokemon_World_V18.zip", probe.MAX_SOURCE+1,probe.MAX_SOURCE)

    def test_10_redirect_cannot_be_attacker_domain(self):
        with self.assertRaises(probe.SourceBlocked):
            probe.download_private(self.project,
                "https://download100.mediafire.com.evil.example/some.zip",
                "Pokemon_World_V18.zip", 1,2)

    def test_11_download_url_must_be_mediafire_download_host(self):
        with self.assertRaises(probe.SourceBlocked):
            probe.download_private(self.project,
                "https://www.mediafire.com/file/123/file.zip",
                "Pokemon_World_V18.zip", 1,2)

    def test_12_safe_workspace_rejects_symlink(self):
        outside=self.project/"outside"
        outside.mkdir()
        try:
            (self.project/".blue-work").symlink_to(outside,target_is_directory=True)
        except OSError:
            self.skipTest("symlink unsupported")
        with self.assertRaises(probe.SourceBlocked):
            probe.verify_workspace(self.project)
        self.assertFalse((outside/"unova").exists())

    def test_13_page_extract_accepts_only_mediafire_download_url(self):
        page=b'<a aria-label="Download file" href="https://download234.mediafire.com/abc/def.zip" id="downloadButton">Download</a>'
        with patch.object(probe,"request_bounded",return_value=page):
            actual=probe.get_direct_link("tq5w0in2xt2peb1","Pokemon_World_V18.zip",{})
        self.assertEqual(actual,"https://download234.mediafire.com/abc/def.zip")

    def test_14_page_extract_rejects_other_host(self):
        page=b'<a href="https://evil.example/steal.zip" id="downloadButton">Download</a>'
        with patch.object(probe,"request_bounded",return_value=page):
            with self.assertRaises(probe.SourceBlocked):
                probe.get_direct_link("tq5w0in2xt2peb1","Pokemon_World_V18.zip",{})

    def test_15_source_complete_flag_never_true_even_when_fake_download(self):
        metadata={"filename":"Pokemon_World_V18.zip","size":"340"}
        meta_credits={"filename":"Credits.txt","size":"30"}
        fake={"bytes":340,"sha256":"f"*64,"private_path":".blue-work/unova/sources/Pokemon_World_V18.zip",
              "path":self.project/"fake.zip"}
        with patch.object(probe,"get_api_file_info",side_effect=[metadata,meta_credits]), \
             patch.object(probe,"get_direct_link",return_value="https://download100.mediafire.com/file"), \
             patch.object(probe,"download_private",return_value=fake), \
             patch.object(probe,"audit_zip",return_value={"all_regions_source_map_count":5}):
            out=probe.probe(self.project,download=True)
        self.assertTrue(out["zip_downloaded"])
        self.assertEqual(out["whole_donor_project_map_count"],5)
        self.assertIsNone(out["unova_map_count"])
        self.assertFalse(out["e04_complete"])
        self.assertFalse(out["copyright_rights_verified"])
        self.assertFalse(out["may_install"])

    def test_16_api_payload_malformed_fail_closed(self):
        with patch.object(probe,"request_bounded",return_value=b'{"response":{"result":"Error","message":"File deleted"}}'):
            with self.assertRaises(probe.SourceBlocked):
                probe.get_api_file_info("tq5w0in2xt2peb1")

    def test_17_api_reply_success_parses_provider_info(self):
        response={"response":{"result":"Success","file_info":{
            "quickkey":"tq5w0in2xt2peb1","filename":"Pokemon_World_V18.zip",
            "size":"340"}}}
        with patch.object(probe,"request_bounded",return_value=json.dumps(response).encode()):
            x=probe.get_api_file_info("tq5w0in2xt2peb1")
        self.assertEqual(x["filename"],"Pokemon_World_V18.zip")


if __name__=="__main__":
    unittest.main()
