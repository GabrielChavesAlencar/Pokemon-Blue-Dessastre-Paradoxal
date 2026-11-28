"""Offline contract tests for SAFE Hoenn -> main Decades integration.

No donor archive, native Game.exe or user save is read or written.
"""
import hashlib
import io
import json
import sys
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import install_hoenn as hoenn
import auto_integrate_hoenn as auto
import ensure_hoenn_source as downloader
from hoenn_catalog import LEGACY_SOURCE_IDS, marker_bytes, validate_manifest
from hoenn_qa_phase2 import ALL_BORDERS
from hoenn_stage10 import LEGACY_VOID_SURF_BORDERS, RESTORED_SURF_BORDERS

class HoennMainIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="hoenn-main-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / "game"
        (self.game / "Data").mkdir(parents=True)
        (self.game / "PBS").mkdir()
        (self.game / "Data/MapInfos.rxdata").write_bytes(b"native mapinfos")
        (self.game / "Data/Tilesets.rxdata").write_bytes(b"native tilesets")
        (self.game / "PBS/map_connections.txt").write_bytes(b"native map connections")
        self.maps = {str(mid): 700 + n for n, mid in enumerate(hoenn.SOURCE_MAPS)}
        self.start = [self.maps["8"], 25, 6, 2]
        self.town = [self.maps["7"], 5, 10, 2]

    def test_isolated_hoenn_plugin_must_not_override_main_new_game(self):
        ruby = (ROOT / "scripts/regions/HoennPilot.rb").read_text(encoding="utf-8")
        start = ruby.split("  module Start", 1)[1].split(
            "  BlueRegionStart.singleton_class.prepend(Start)", 1)[0]
        self.assertIn('File.file?("Hoenn pilot.json")', start)
        self.assertIn("return super unless @new_game", start)
        self.assertIn("BlueHoennPilot::MARKER", start)

    def test_contract_excludes_pilot_boot_and_save_settings(self):
        required = {"Data/System.rxdata", "Data/Scripts.rxdata",
                    "Game.ini", "mkxp.json", "Hoenn pilot.json"}
        self.assertTrue(required.issubset(hoenn.FORBIDDEN))
        self.assertNotIn("Data/MapInfos.rxdata", hoenn.FORBIDDEN)
        self.assertTrue(hoenn.ALLOWED_REPLACE.issubset({
            "Data/MapInfos.rxdata", "Data/Tilesets.rxdata", "PBS/map_connections.txt"}))
        self.assertIn("c59233b", hoenn.UPSTREAM)
        self.assertEqual(len(hoenn.SOURCE_MAPS), 199)

    def test_littleroot_point_must_be_source_verified(self):
        rows = ["BLUE_HOENN_TEST_STOPS_V1"]
        for source, new in self.maps.items():
            rows.append(f"{source}|{new}|5|10|2|Hoenn Map {source}")
        raw = ("\n".join(rows)+"\n").encode("utf8")
        report = {"maps": {int(k): v for k,v in self.maps.items()}}
        self.assertEqual(hoenn.vetted_town(report, {"Data/blue-hoenn-test-stops.txt":raw}),
                         self.town)
        bogus = raw.replace(f"7|{self.maps['7']}|".encode(),
                            f"7|{self.maps['7']+1}|".encode())
        with self.assertRaises(ValueError):
            hoenn.vetted_town(report, {"Data/blue-hoenn-test-stops.txt":bogus})

    def install_proof_fixture(self):
        for rel in hoenn.REQUIRED:
            path = self.game / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"verified fixture")
        for mid in self.maps.values():
            (self.game / f"Data/Map{mid:03}.rxdata").write_bytes(b"authored fixture")
        hashes = {
            rel: hoenn.sha((self.game / rel).read_bytes()) for rel in (
                hoenn.PLUGIN,"Data/blue-hoenn-pilot.txt",
                "PBS/trainers_hoenn_pilot.txt", "PBS/encounters_hoenn_pilot.txt")
        }
        proof = {
            "schema":1,"region":"HOENN",
            "source_commit":hoenn.UPSTREAM,
            "status":"INTEGRATED_FILES_READY_FOR_NATIVE_QA",
            "maps":self.maps,"start":self.start,"town":self.town,
            "installed_sha256":hashes
        }
        for path, raw in marker_bytes(proof).items():
            (self.game / path).write_bytes(raw)
        hashes[hoenn.COMPACT] = hoenn.sha((self.game / hoenn.COMPACT).read_bytes())
        (self.game / hoenn.MANIFEST).write_text(json.dumps(proof))
        return proof

    def test_forged_release_or_modified_pbs_is_rejected(self):
        proof = self.install_proof_fixture()
        status=hoenn.verify_installed(self.game)
        self.assertEqual(status["maps"],199)
        self.assertFalse(status["game_exe_tested_here"])
        (self.game / "PBS/trainers_hoenn_pilot.txt").write_bytes(b"modified")
        with self.assertRaisesRegex(ValueError,"modificada"):
            hoenn.verify_installed(self.game)
        (self.game / "PBS/trainers_hoenn_pilot.txt").write_bytes(b"verified fixture")
        proof["source_commit"]="0"*40
        (self.game / hoenn.MANIFEST).write_text(json.dumps(proof))
        with self.assertRaisesRegex(ValueError,"inválido"):
            hoenn.verify_installed(self.game)

    def legacy_surf_fixture(self):
        self.install_proof_fixture()
        mapping = {int(source): dest for source, dest in self.maps.items()}
        def row(border):
            a, side_a, offset_a, b, side_b, offset_b = border
            return f"{mapping[a]},{side_a},{offset_a},{mapping[b]},{side_b},{offset_b}\r\n".encode("ascii")
        foreign = b"\xef\xbb\xbf# Kanto fixture\r\n001,East,0,002,West,0\r\n\r\n"
        common = b"".join(row(border) for border in ALL_BORDERS if border not in RESTORED_SURF_BORDERS)
        legacy = foreign + common + b"".join(map(row, LEGACY_VOID_SURF_BORDERS))
        current = foreign + common + b"".join(map(row, RESTORED_SURF_BORDERS))
        (self.game / hoenn.CONNECTIONS).write_bytes(legacy)
        return mapping, legacy, current

    def test_surf_repair_rejects_an_unknown_partial_layout(self):
        mapping, legacy, current = self.legacy_surf_fixture()
        connections = self.game / hoenn.CONNECTIONS
        changed = legacy + current.splitlines(keepends=True)[-1]
        connections.write_bytes(changed)
        with self.assertRaisesRegex(ValueError, "migração parcial"):
            hoenn.reconcile_surf_connections(changed, mapping)
        self.assertEqual(connections.read_bytes(), changed)
        self.assertFalse((self.game / hoenn.COMPILE_REQUEST).exists())

    def test_current_surf_layout_rejects_duplicate_rows_with_padded_map_ids(self):
        mapping, _, current = self.legacy_surf_fixture()
        duplicate = b"0" + current.splitlines(keepends=True)[-1]
        with self.assertRaisesRegex(ValueError, "duplicata"):
            hoenn.reconcile_surf_connections(current + duplicate, mapping)

    def test_v2_upgrade_preserves_maps_and_save_and_is_idempotent(self):
        mapping, legacy, current = self.legacy_surf_fixture()
        self.assertEqual(set(mapping), LEGACY_SOURCE_IDS)
        self.assertEqual(LEGACY_SOURCE_IDS, set(hoenn.SOURCE_MAPS))
        manifest = self.game / hoenn.MANIFEST
        save = self.game / "Data/File A.rxdata"
        save.write_bytes(b"save on a legacy destination")
        known_maps = list((self.game / "Data").glob("Map*.rxdata"))
        old_files = {path: path.read_bytes() for path in known_maps}
        old_proof = manifest.read_bytes()
        cache = self.game / hoenn.PLUGIN_CACHE
        cache.write_bytes(b"plugin scripts from V1")

        index = b"mapinfos migration fixture"
        (self.game / "Data/MapInfos.rxdata").write_bytes(index)
        old_files[self.game / "Data/MapInfos.rxdata"] = index

        def native_fixture(blob):
            return dict.fromkeys(mapping.values()) if blob == index else object()

        with patch.object(hoenn, "ROOT", self.root), \
             patch.object(hoenn, "CATALOG_REVISION", 1), \
             patch.object(hoenn, "loads", side_effect=native_fixture), \
             patch.object(hoenn, "allocate_hoenn_map_ids", return_value=mapping), \
             patch("hoenn_qa_phase2.inspect_connections"):
            dry = hoenn.migrate_existing(self.game, False)
            self.assertTrue(dry["catalog_migration_pending"])
            self.assertEqual(manifest.read_bytes(), old_proof)
            self.assertEqual((self.game / hoenn.CONNECTIONS).read_bytes(), legacy)
            result = hoenn.migrate_existing(self.game, True)
            repeated = hoenn.migrate_existing(self.game, True)
        proof = json.loads(manifest.read_bytes())
        self.assertEqual(validate_manifest(proof), mapping)
        self.assertEqual(proof["legacy_maps"], self.maps)
        self.assertEqual(proof["schema"], 2)
        self.assertTrue(result["catalog_changed"])
        self.assertFalse(repeated["catalog_changed"])
        self.assertEqual((self.game / hoenn.CONNECTIONS).read_bytes(), current)
        self.assertEqual((self.game / hoenn.COMPILE_REQUEST).read_bytes(), b"compile")
        self.assertFalse(cache.exists())
        self.assertFalse((self.game / hoenn.JOURNAL).exists())
        self.assertEqual(save.read_bytes(), b"save on a legacy destination")
        self.assertEqual({path: path.read_bytes() for path in known_maps}, old_files)
        self.assertEqual((Path(result["backup"]) / hoenn.MANIFEST).read_bytes(), old_proof)

    def test_v2_installation_resume_recovers_incomplete_known_writes(self):
        self.install_proof_fixture()
        old = {rel: hoenn.optional_bytes(self.game / rel) for rel in hoenn.MIGRATION_FILES}
        changes = dict(old)
        changes[hoenn.PLUGIN] = b"changed plugin"
        changes[hoenn.COMPACT] = b"changed compact"
        fail = self.game / hoenn.COMPACT
        atomic = hoenn.atomic

        def interrupt(path, blob):
            if path == fail:
                raise OSError("simulated interruption")
            atomic(path, blob)

        with patch.object(hoenn, "ROOT", self.root):
            with patch.object(hoenn, "recover_migration", return_value=False), \
                 patch.object(hoenn, "atomic", side_effect=interrupt):
                changes = dict(sorted(changes.items(), key=lambda entry: entry[0] != hoenn.PLUGIN))
                with self.assertRaisesRegex(OSError, "interruption"):
                    hoenn.commit_migration(self.game, old, changes)
            self.assertTrue((self.game / hoenn.JOURNAL).exists())
            self.assertEqual((self.game / hoenn.PLUGIN).read_bytes(), b"changed plugin")
            with self.assertRaisesRegex(ValueError, "retomada"):
                hoenn.verify_installed(self.game)
            self.assertTrue(hoenn.recover_migration(self.game))
            self.assertFalse(hoenn.recover_migration(self.game))
        self.assertEqual({rel: hoenn.optional_bytes(self.game / rel) for rel in old}, old)

    def test_oldale_transaction_rolls_back_city_and_new_map_together(self):
        self.install_proof_fixture()
        city = hoenn.map_path(self.maps["12"])
        houses_id = 899
        houses = hoenn.map_path(houses_id)
        names = hoenn.MIGRATION_FILES | {hoenn.MAP_INFOS, hoenn.MAP_METADATA, city, houses}
        previous = {name: hoenn.optional_bytes(self.game / name) for name in names}
        changes = {
            **previous,
            city: b"city with new doors",
            houses: b"house interior",
            hoenn.MAP_INFOS: b"index with house interior",
        }
        with patch.object(hoenn, "ROOT", self.root), \
             patch.object(hoenn, "verify_installed", side_effect=ValueError("interrupted verification")):
            with self.assertRaisesRegex(ValueError, "interrupted verification"):
                hoenn.commit_migration(self.game, previous, changes, oldale_houses=houses_id)
        self.assertEqual({name: hoenn.optional_bytes(self.game / name) for name in names}, previous)
        self.assertFalse((self.game / hoenn.JOURNAL).exists())

    def test_oldale_audit_checks_both_return_destinations(self):
        mapping = {12: 704, 15: 899}
        worlds = {mid: hoenn.ruby("RPG::Map", events={}) for mid in mapping.values()}
        for mid, name, xy, (target, x, y, direction) in hoenn.oldale_doors(mapping):
            page = hoenn.event_page(warp=(target, x, y), touch=True)
            page.attrs["@list"][0].attrs["@parameters"][4] = direction
            hoenn.append_event(worlds[mid], name, *xy, page)

        def read(relative):
            mid = int(Path(relative).stem.removeprefix("Map"))
            return hoenn.serialize(worlds[mid], hoenn.EVENT_CLASSES)

        hoenn.verify_oldale_doors(read, mapping)
        east_exit = worlds[899].attrs["@events"][2].attrs["@pages"][0]
        east_exit.attrs["@list"][0].attrs["@parameters"][2:4] = [5, 8]
        with self.assertRaisesRegex(ValueError, "Destino"):
            hoenn.verify_oldale_doors(read, mapping)

    def test_catalog_rejects_a_swapped_legacy_destination_and_unknown_revision(self):
        proof = self.install_proof_fixture()
        proof.update(schema=2, catalog_revision=1, legacy_maps=dict(self.maps))
        self.assertEqual(len(validate_manifest(proof)), len(LEGACY_SOURCE_IDS))
        proof["maps"]["11"], proof["maps"]["12"] = proof["maps"]["12"], proof["maps"]["11"]
        with self.assertRaisesRegex(ValueError, "remapeou"):
            validate_manifest(proof)
        proof["catalog_revision"] = 1000
        with self.assertRaisesRegex(ValueError, "desconhecida"):
            validate_manifest(proof)

    def test_reuses_original_pinned_stage_without_private_zip(self):
        directory = self.root / ".blue-work/hoenn-source/0123456789abcdef"
        directory.mkdir(parents=True)
        with patch.object(hoenn, "ROOT", self.root), \
             patch("hoenn_qa_phase1.load_tree", return_value={}) as inventory, \
             patch.object(hoenn, "check_tree") as tree, \
             patch.object(hoenn, "Source") as source_cls, \
             patch.object(hoenn, "check_source") as audit:
            source, origin = hoenn.validated_local_source(
                self.root / "missing-private.zip", self.root / ".blue-work/pinned-tree.json"
            )
        self.assertEqual(origin, "audited_staged_source")
        self.assertIs(source, source_cls.return_value)
        self.assertEqual(source_cls.call_args.args[0], directory)
        inventory.assert_called_once()
        tree.assert_called_once()
        audit.assert_called_once_with(source)

    def test_staged_source_never_bypasses_hash_audit(self):
        directory = self.root / ".blue-work/hoenn-source/0123456789abcdef"
        directory.mkdir(parents=True)
        with patch.object(hoenn, "ROOT", self.root), \
             patch("hoenn_qa_phase1.load_tree", return_value={}), \
             patch.object(hoenn, "check_tree"), \
             patch.object(hoenn, "check_source", side_effect=ValueError("wrong donor hash")):
            with self.assertRaisesRegex(ValueError, "hashes"):
                hoenn.validated_local_source(
                    self.root / "missing-private.zip", self.root / ".blue-work/pinned-tree.json"
                )

    def test_partial_hoenn_is_never_automatically_reallocated(self):
        self.assertEqual(hoenn.detect_existing(self.game),"absent")
        (self.game / "PBS/trainers_hoenn_pilot.txt").write_text("partial")
        self.assertEqual(hoenn.detect_existing(self.game),"partial")
        with patch.object(hoenn,"MAIN",self.game), patch.object(hoenn,"verify_kanto"):
            (self.game / "Game.exe").write_bytes(b"fixture")
            with self.assertRaisesRegex(ValueError, "Revisão manual"):
                hoenn.apply(self.game,self.root/"missing.zip",self.root/"missing.json",commit=True)

    def test_hoenn_overlay_rejects_collision_and_never_installs_boot_files(self):
        generated={f"Data/Map{mid:03}.rxdata":b"authored map" for mid in self.maps.values()}
        generated.update({
            "Data/MapInfos.rxdata":b"with Hoenn mapinfos",
            "Data/Tilesets.rxdata":b"with Hoenn tilesets",
            "PBS/map_connections.txt":b"native + Hoenn connections",
            "Data/System.rxdata":b"FORBIDDEN",
            "Data/Scripts.rxdata":b"FORBIDDEN",
            "Game.ini":b"FORBIDDEN",
            "mkxp.json":b"FORBIDDEN",
            "Hoenn pilot.json":b"FORBIDDEN",
            "Data/blue-hoenn-compile-request.txt":b"pilot only",
            "Data/blue-hoenn-test-stops.txt":(
                "BLUE_HOENN_TEST_STOPS_V1\n" +
                "".join(f"{src}|{mid}|5|10|2|Hoenn Map\n" for src,mid in self.maps.items())
            ).encode(),
        })
        report={"region":"HOENN","source_commit":hoenn.UPSTREAM,
                "maps":{int(k):v for k,v in self.maps.items()},"qa12":{"status":"STATIC"}}
        with patch.object(hoenn, "CATALOG_REVISION", 1), \
             patch.object(hoenn, "build_overlay", return_value=(generated, report)):
            files, proof=hoenn.prepare_overlay(self.game,None)
        self.assertEqual(len(proof["maps"]),199)
        self.assertEqual(proof["town"],self.town)
        self.assertFalse(hoenn.FORBIDDEN & set(files))
        self.assertIn("Data/MapInfos.rxdata",files)
        (self.game / f"Data/Map{self.maps['7']:03}.rxdata").write_bytes(b"foreign-map")
        with patch.object(hoenn, "CATALOG_REVISION", 1), \
             patch.object(hoenn, "build_overlay", return_value=(generated, report)):
            with self.assertRaisesRegex(ValueError,"sobrescrito"):
                hoenn.prepare_overlay(self.game,None)


class HoennAutoInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="hoenn-auto-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.game=self.root/"game"
        self.game.mkdir()
        (self.game/"Game.exe").write_bytes(b"fixture")
        (self.game/"Data").mkdir()
        self.patches=[
            patch.object(auto,"ROOT",self.root),
            patch.object(auto,"ZIP",self.root/"The Pokémon World Project - Hoenn.zip"),
            patch.object(auto,"STATUS",self.root/".blue-work/status.json"),
            patch.object(auto,"LOG",self.root/".blue-work/log.txt"),
            patch.object(auto,"SOURCE_CACHE",self.root/".blue-work/hoenn-source")
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def test_no_zip_bootstraps_pinned_public_source_automatically(self):
        calls = []
        with patch.object(auto, "invoke", side_effect=lambda *args: calls.append(args)):
            result = auto.integrate(self.root, self.game)
        self.assertEqual([args[-1] for args in calls],
                         ["--bootstrap-source", "--apply", "--verify-installed"])
        self.assertEqual(result["status"], "integrated")
        self.assertEqual(result["source"], "pinned_public_git")
        self.assertEqual((self.game / auto.GAME_STATUS).read_text().strip(), "integrated")

    def test_cache_is_reverified_by_bootstrap_before_import(self):
        auto.SOURCE_CACHE.mkdir(parents=True)
        calls = []
        with patch.object(auto, "invoke", side_effect=lambda *args: calls.append(args)):
            result = auto.integrate(self.root, self.game)
        self.assertEqual(result["status"], "integrated")
        self.assertEqual([call[-1] for call in calls],
                         ["--bootstrap-source", "--apply", "--verify-installed"])
        self.assertEqual((self.game / auto.GAME_STATUS).read_text().strip(), "integrated")

    def test_failed_public_download_blocks_travel_without_attempting_import(self):
        calls = []
        def invoke(*args):
            calls.append(args[-1])
            raise RuntimeError("Git source temporarily unavailable")
        with patch.object(auto, "invoke", side_effect=invoke):
            result = auto.integrate(self.root, self.game)
        self.assertEqual(calls, ["--bootstrap-source"])
        self.assertEqual(result["status"], "integration_blocked")
        self.assertFalse(result["ready"])
        self.assertFalse(result["changed"])
        self.assertIn("Git source", result["reason"])
        self.assertEqual((self.game / auto.GAME_STATUS).read_text().strip(),
                         "integration_blocked")

    def test_source_available_only_marks_ready_after_apply_and_verify(self):
        auto.ZIP.write_bytes(b"private fixture (never uploaded)")
        calls=[]
        with patch.object(auto,"invoke",side_effect=lambda *args:calls.append(args)):
            result=auto.integrate(self.root,self.game)
        self.assertEqual(result["status"],"integrated")
        self.assertEqual([call[-1] for call in calls],["--apply","--verify-installed"])
        self.assertTrue(result["changed"])

    def test_existing_surf_repair_requests_recompile_only_once(self):
        proof = self.game / auto.PROOF
        proof.write_bytes(b"old proof")
        with patch.object(auto, "invoke", side_effect=lambda *_: proof.write_bytes(b"revised proof")) as invoke:
            first = auto.integrate(self.root, self.game)
            second = auto.integrate(self.root, self.game)
        self.assertEqual([call.args[-1] for call in invoke.call_args_list], ["--apply", "--apply"])
        self.assertEqual(first["status"], "already_integrated")
        self.assertTrue(first["changed"])
        self.assertFalse(second["changed"])

    def test_existing_invalid_install_is_not_automatically_overwritten(self):
        (self.game / auto.PROOF).parent.mkdir(exist_ok=True)
        (self.game / auto.PROOF).write_text("{}")
        with patch.object(auto,"invoke",side_effect=RuntimeError("bad proof")):
            result=auto.integrate(self.root,self.game)
        self.assertEqual(result["status"],"existing_install_needs_review")
        self.assertFalse(result["ready"])



class HoennVerifiedPublicDownloaderTests(unittest.TestCase):
    """No real network in CI. Verify pinned raw Git blobs against bytes."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="hoenn-source-hash-")
        self.addCleanup(self.tmp.cleanup)
        self.stage = Path(self.tmp.name) / "staged"
        self.stage.mkdir()
        # The fake stage is inside a temporary fixture, not the actual
        # repository. Keep the production path boundary in place.
        root_patch = patch.object(downloader, "ROOT", Path(self.tmp.name))
        root_patch.start()
        self.addCleanup(root_patch.stop)
        self.body = b"Audited donor data; never run this as code."
        self.rel = "PBS/encounters.txt"
        self.digest = hashlib.sha1(
            f"blob {len(self.body)}\0".encode("ascii") + self.body
        ).hexdigest()
        self.download = object.__new__(downloader.PinnedDownloader)
        self.download.stage = self.stage
        self.download.blobs = {self.rel: {
            "path": self.rel, "sha": self.digest,
            "size": len(self.body), "type": "blob",
        }}
        self.download.opener = lambda *args, **kwargs: io.BytesIO(self.body)
        self.download.written = 0
        self.download.reused = 0
        self.download.bytes_downloaded = 0

    def test_obstacle_sprites_are_discovered_from_pinned_map_events(self):
        # The exact image named in the real Hoenn installer failure must be
        # discovered even when it is not part of the map's tileset graphics.
        def source_event(name, graphic, *, conditional=False, pages=1):
            condition = SimpleNamespace(attrs={"@switch1_valid": conditional})
            page = SimpleNamespace(attrs={
                "@graphic": SimpleNamespace(attrs={"@character_name": graphic.encode()}),
                "@condition": condition,
            })
            return SimpleNamespace(attrs={
                "@name": name.encode(), "@pages": [page] * pages,
            })
        world = SimpleNamespace(attrs={"@events": {
            1: source_event("Strength Boulder", "OBJ_RSE_Strength Boulder"),
            2: source_event("RockSmash Rock", "OBJ_RSE_RockSmash Rock"),
            3: source_event("NPC", "NPC_ORAS_Birch"),
            4: source_event("Strength Boulder", "Ignored conditional", conditional=True),
            5: source_event("Pushable Rock", "Ignored multipage", pages=2),
            6: source_event("Strength Rock", "../unsafe"),
        }})
        self.assertEqual(downloader.obstacle_character_paths(world), {
            "Graphics/Characters/OBJ_RSE_Strength Boulder.png",
            "Graphics/Characters/OBJ_RSE_RockSmash Rock.png",
        })
        self.assertNotIn("Graphics/Characters/OBJ_RSE_Strength Boulder.png",
                         downloader.BOSS_SPRITES)
        # The inventory must provide a pinned SHA for anything selected.
        self.assertTrue(all(item.startswith("Graphics/Characters/") for item in
                            downloader.obstacle_character_paths(world)))

    def test_public_installer_uses_local_pinned_metadata(self):
        from hoenn_qa_phase1 import check_tree, load_tree

        tree = load_tree(downloader.INVENTORY, offline=True)
        self.assertEqual(tree["scope"], "verified_shared_install_assets")
        self.assertEqual(check_tree(tree)["source_maps"], len(downloader.SOURCE_MAPS))
        self.assertTrue(all(row["path"].split("/")[0] in ("Data", "PBS", "Audio", "Graphics")
                            and row["size"] > 0 for row in tree["tree"]))

    def test_fixed_revision_and_upstream_raw_url(self):
        self.assertEqual(downloader.UPSTREAM, hoenn.UPSTREAM)
        self.assertEqual(downloader.PINNED_TREE,
                         "c3876ecea7545eb3a91b9c8748d7e2b13f07805d")
        self.assertIn("The%20Pok%C3%A9mon%20World%20Project%20-%20Hoenn/",
                      downloader.RAW_BASE)
        self.assertIn(downloader.UPSTREAM, downloader.RAW_BASE)
        self.assertNotIn("refs/heads/main", downloader.RAW_BASE)

    def test_download_hash_verification_and_idempotent_cached_reuse(self):
        result = self.download.file(self.rel)
        self.assertEqual(result.read_bytes(), self.body)
        self.assertEqual(self.download.written, 1)
        self.assertEqual(self.download.bytes_downloaded, len(self.body))
        with patch.object(self.download, "opener",
                          side_effect=AssertionError("unexpected second download")):
            self.assertEqual(self.download.file(self.rel).read_bytes(), self.body)
        self.assertEqual(self.download.reused, 1)

    def test_corrupt_remote_blob_is_rejected_and_no_cache_is_committed(self):
        self.download.opener = lambda *args, **kwargs: io.BytesIO(b"x"*len(self.body))
        with self.assertRaisesRegex(ValueError, "não corresponde"):
            self.download.file(self.rel)
        self.assertFalse((self.stage / self.rel).exists())

    def test_corrupt_cached_blob_is_never_overwritten_or_trusted(self):
        (self.stage / "PBS").mkdir()
        target = self.stage / self.rel
        target.write_bytes(b"x"*len(self.body))
        with self.assertRaisesRegex(ValueError, "Cache Hoenn alterado"):
            self.download.file(self.rel)
        self.assertEqual(target.read_bytes(), b"x"*len(self.body))

    def test_path_traversal_and_missing_inventory_blob_fail_closed(self):
        for bad in ("../PBS/encounters.txt", "Data/../PBS/encounters.txt"):
            self.download.blobs[bad] = self.download.blobs[self.rel].copy()
            with self.assertRaisesRegex(ValueError, "Caminho"):
                self.download.file(bad)
        with self.assertRaisesRegex(ValueError, "não existe"):
            self.download.file("Data/Map999.rxdata")

    def test_public_downloader_does_not_write_to_game_or_saves(self):
        code = (ROOT / "scripts/regions/ensure_hoenn_source.py").read_text("utf-8")
        self.assertNotIn("os.startfile", code)
        self.assertNotIn("Process.spawn", code)
        self.assertNotIn('COPY_DIRS', code)
        self.assertEqual(self.download.file(self.rel).parent,
                         self.stage / "PBS")

if __name__=="__main__":
    unittest.main()
