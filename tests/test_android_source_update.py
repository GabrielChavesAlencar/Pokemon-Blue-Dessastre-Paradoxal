import contextlib
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.android.source_update import preflight, clone_verified_install, commit_local, atomic_file, manifest_row, installed_provenance, PRODUCT_REVISION, write_compiler_ini, compiler_config, local_delta, K05_RUNTIME, K05_COMPILED, work_holder, source_workflow, RECOVERY_FILE, recover_source_install
from unittest.mock import patch
from scripts.android.update_client import MARKER, read_installed, main as updater_main


class AndroidPinnedSourceUpdateTests(unittest.TestCase):
    def make(self,root):
        data=root/"Data"
        data.mkdir()
        content=b"synthetic native file"
        regions={"kanto":{str(i):mid for i,mid in enumerate(range(300,465),10)},
                 "hoenn":{str(i):mid for i,mid in enumerate(range(700,899),10)}}
        installed={"schema":1,"channel":"multiregion","revision":"a"*40,"files":{}}
        for region,ids in regions.items():
            (data/f"blue-{region}-install.json").write_text(json.dumps({"maps":ids}))
            for mid in ids.values():
                path=f"Data/Map{mid:03d}.rxdata"
                (root/path).write_bytes(content)
                installed["files"][path]={"sha256":hashlib.sha256(content).hexdigest()}
        (root/MARKER).write_text(json.dumps(installed))
        save=root/"saves"/"Game.rxdata"
        save.parent.mkdir()
        save.write_bytes(b"not a real save; do not inspect")
        return save

    def test_preflight_is_read_only_and_keeps_hoenn_and_save(self):
        with TemporaryDirectory() as work:
            root=Path(work)
            saved=self.make(root)
            before={p:p.read_bytes() for p in root.rglob("*") if p.is_file()}
            proof=preflight(root)
            self.assertEqual(proof["hoenn_maps"],199)
            self.assertEqual(proof["kanto_maps"],165)
            self.assertFalse(proof["updated"])
            self.assertFalse(proof["compile_verified"])
            self.assertEqual({p:p.read_bytes() for p in root.rglob("*") if p.is_file()},before)
            self.assertIn(saved,before)

    def test_reject_missing_modified_or_colliding_map_before_download(self):
        with TemporaryDirectory() as work:
            root=Path(work)
            self.make(root)
            hoenn=root/"Data/Map700.rxdata"
            before=hoenn.read_bytes()
            hoenn.write_bytes(b"owner edit")
            with self.assertRaisesRegex(ValueError,"Map700"):
                preflight(root)
            self.assertEqual(hoenn.read_bytes(),b"owner edit")
            hoenn.write_bytes(before)
            (root/"Data/Map609.rxdata").write_bytes(b"other region")
            with self.assertRaisesRegex(ValueError,"609"):
                preflight(root)

    def test_clone_only_verified_runtime_and_rolls_back_bad_copy(self):
        with TemporaryDirectory() as folder:
            parent=Path(folder).resolve()
            root=parent/"installed"
            root.mkdir()
            save=self.make(root)
            manifest=read_installed(root)
            stage=parent/"stage"
            for meta in manifest["files"].values():
                meta["size"]=len(b"synthetic native file")
            clone_verified_install(root,stage,manifest)
            self.assertTrue((stage/"Data/Map700.rxdata").is_file())
            self.assertFalse((stage/save.relative_to(root)).exists())
            self.assertEqual(save.read_bytes(),b"not a real save; do not inspect")
            bad=parent/"bad"
            (root/"Data/Game.rxdata").write_bytes(b"private")
            manifest["files"]["Data/Game.rxdata"]={"size":7,"sha256":hashlib.sha256(b"private").hexdigest()}
            with self.assertRaisesRegex(ValueError,"Caminho não permitido"):
                clone_verified_install(root,bad,manifest)
            self.assertFalse(bad.exists())
            self.assertEqual((root/"Data/Game.rxdata").read_bytes(),b"private")

    def test_apply_fault_rolls_back_and_leaves_revision_unchanged(self):
        with TemporaryDirectory() as folder:
            parent=Path(folder).resolve()
            root,stage=parent/"installed",parent/"stage"
            root.mkdir()
            save=self.make(root)
            names=["Data/Map609.rxdata","Data/Map610.rxdata"]
            (stage/"Data").mkdir(parents=True)
            (root/names[0]).write_bytes(b"old tile")
            for name in names:
                (stage/name).write_bytes(b"local new tile")
            changes={name:manifest_row(stage/name) for name in names}
            revision=(root/MARKER).read_bytes()
            def limited(path,data):
                if path==root/names[1]:
                    raise OSError("simulated I/O failure")
                return atomic_file(path,data)
            with patch("scripts.android.source_update.atomic_file",side_effect=limited):
                with self.assertRaisesRegex(OSError,"simulated"):
                    commit_local(root,stage,changes,b"new revision",parent/"recovery")
            self.assertEqual((root/MARKER).read_bytes(),revision)
            self.assertEqual((root/names[0]).read_bytes(),b"old tile")
            self.assertFalse((root/names[1]).exists())
            self.assertEqual(save.read_bytes(),b"not a real save; do not inspect")

    def test_product_identity_is_not_the_recipe_sha(self):
        baseline={"Data/Map609.rxdata":{"sha256":"a"*64,"size":100}}
        recipe="b"*40
        result=installed_provenance(baseline,recipe)
        self.assertEqual(result["product_revision"], PRODUCT_REVISION)
        self.assertEqual(result["recipe_revision"], recipe)
        self.assertNotEqual(result["product_revision"], result["recipe_revision"])
        changed={"Data/Map609.rxdata":{"sha256":"c"*64,"size":100}}
        self.assertNotEqual(result["inventory_sha256"],installed_provenance(changed,recipe)["inventory_sha256"])

    def test_normalizes_only_the_disposable_native_ini(self):
        with TemporaryDirectory() as root:
            parent=Path(root)
            game=parent/"input"
            stage=parent/"stage"
            game.mkdir()
            stage.mkdir()
            supplied=b"other original native bytes"
            (game/"Game.ini").write_bytes(supplied)
            write_compiler_ini(stage)
            ini=(stage/"Game.ini").read_bytes()
            self.assertIn(b"Scripts=Data\\Scripts.rxdata",ini)
            self.assertEqual(ini.decode("ascii").encode("ascii"),ini)
            self.assertEqual((game/"Game.ini").read_bytes(),supplied)

    def test_compiler_config_pins_the_relative_entry_point(self):
        original='{"gameFolder":"another-folder","execName":"Other","customScript":"other.rb","windowTitle":"original"}'
        data=json.loads(compiler_config(original,"Isolated compiler"))
        self.assertEqual(data["gameFolder"],".")
        self.assertEqual(data["execName"],"Game")
        self.assertEqual(data["customScript"],"")
        self.assertEqual(data["rgssVersion"],1)
        self.assertEqual(data["windowTitle"],"original")
        self.assertEqual(data["dataPathApp"],"Isolated compiler")

    def test_recompiled_unrelated_files_are_discarded_and_foreign_maps_refused(self):
        with TemporaryDirectory() as folder:
            parent=Path(folder).resolve()
            root,stage=parent/"installed",parent/"scratch"
            paths=K05_RUNTIME | K05_COMPILED | {"Data/Map700.rxdata","Data/Map609.rxdata",
                "PBS/pokemon_forms_Gen_9_Pack.txt","Data/Scripts.rxdata","Data/species.dat"}
            for base in (root,stage):
                for name in paths:
                    dst=base/name
                    dst.parent.mkdir(parents=True,exist_ok=True)
                    dst.write_bytes(b"before")
            names={"Data/Map609.rxdata","PBS/pokemon_forms_Gen_9_Pack.txt","Data/Scripts.rxdata",
                   "Data/species.dat","Data/items.dat"}
            for name in names:
                (stage/name).write_bytes(b"after")
            old={"files":{name:manifest_row(root/name) for name in paths}}
            kanto={"maps":{"94":609},"installed_sha256":{"Data\\Map609.rxdata":"a"*64}}
            changed=local_delta(root,stage,old,kanto)
            self.assertEqual(set(changed),{"Data/Map609.rxdata","Data/items.dat"})
            (stage/"Data/Map700.rxdata").write_bytes(b"foreign difference")
            with self.assertRaisesRegex(ValueError,"fora de Kanto"):
                local_delta(root,stage,old,kanto)

    def test_final_contract_failure_rolls_back_before_revision_is_written(self):
        with TemporaryDirectory() as folder:
            parent=Path(folder).resolve()
            root,stage=parent/"installed",parent/"scratch"
            root.mkdir()
            self.make(root)
            name="Data/Map609.rxdata"
            (stage/"Data").mkdir(parents=True)
            (stage/name).write_bytes(b"new file")
            before=(root/MARKER).read_bytes()
            def fail(target):
                self.assertEqual((target/MARKER).read_bytes(),before)
                raise ValueError("wrong compiled cache")
            with self.assertRaisesRegex(ValueError,"wrong compiled cache"):
                commit_local(root,stage,{name:manifest_row(stage/name)},b"new revision",parent/"backup",verify=fail)
            self.assertFalse((root/name).exists())
            self.assertEqual((root/MARKER).read_bytes(),before)

    def test_source_updater_dispatches_without_querying_binary_releases(self):
        with TemporaryDirectory() as folder:
            root=Path(folder).resolve()
            self.make(root)
            with patch("scripts.android.update_client.subprocess.run") as process, \
                    patch("scripts.android.update_client.remote_update") as remote:
                process.return_value.returncode=0
                rc=updater_main(["--source","--update","--game-dir",str(root)])
                self.assertEqual(rc,0)
                self.assertIn("--source-workflow",process.call_args.args[0])
                remote.assert_not_called()
            mark=read_installed(root)
            mark["source_update"]={"mode":"pinned-source-local"}
            (root/MARKER).write_text(json.dumps(mark))
            with patch("scripts.android.update_client.remote_update") as remote, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(updater_main(["--update","--game-dir",str(root)]),2)
                remote.assert_not_called()

    def test_source_staging_requires_a_separate_visible_directory(self):
        with TemporaryDirectory() as folder:
            root=Path(folder).resolve()/"installed"
            root.mkdir()
            self.make(root)
            with self.assertRaisesRegex(ValueError,"pasta separada"):
                work_holder(root,"a"*40,root/"danger")
            with self.assertRaisesRegex(ValueError,"pasta separada"):
                work_holder(root,"a"*40,root.parent)
            target=root.parent/"visible-copy"
            proof=source_workflow(root,target)
            self.assertFalse(target.exists())
            self.assertTrue(proof["no_binary_zip"])
            self.assertEqual(proof["target_revision"],PRODUCT_REVISION)

    def test_updater_resumes_only_after_compiler_proof(self):
        with TemporaryDirectory() as folder:
            parent=Path(folder).resolve()
            root,work=parent/"installed",parent/"work"
            root.mkdir()
            self.make(root)
            before=(root/MARKER).read_bytes()
            with patch("scripts.android.source_update.stage_local") as stage, \
                    patch("scripts.android.source_update.finish_local") as finish:
                stage.return_value={"status":"staged"}
                self.assertEqual(source_workflow(root,work,True),{"status":"staged"})
                stage.assert_called_once_with(root,work)
                finish.assert_not_called()
                holder=work/("a"*40)
                staged=holder/"game"
                (staged/"Data").mkdir(parents=True)
                receipt={"installed_root":str(root),"staged_game":str(staged)}
                (holder/"proof.json").write_text(json.dumps(receipt))
                self.assertEqual(source_workflow(root,work,True),receipt)
                finish.assert_not_called()
                (staged/"Data/blue-android-compiled.txt").write_text("simulated marker")
                finish.return_value={"status":"applied"}
                self.assertEqual(source_workflow(root,work,True),{"status":"applied"})
                finish.assert_called_once_with(root,PRODUCT_REVISION,True,work)
                self.assertEqual((root/MARKER).read_bytes(),before)

    def test_source_recovery_survives_process_exit_before_and_after_marker(self):
        child = r"""
import os,sys
from pathlib import Path
from scripts.android import source_update as s
root,stage,backup=map(Path,sys.argv[1:4])
pause=sys.argv[4]
saved=s.atomic_file
def interrupted(path,data):
    saved(path,data)
    if path.name==pause and root in path.parents:
        os._exit(91)
s.atomic_file=interrupted
row="Data/Map609.rxdata"
s.commit_local(root,stage,{row:s.manifest_row(stage/row)},b"completed",backup,baseline="a"*40)
"""
        for point,expected in (("Map609.rxdata","rolled_back"),("blue-update.json","committed")):
            with self.subTest(point=point),TemporaryDirectory() as folder:
                d=Path(folder).resolve()
                root,work=d/"live",d/"visible"
                root.mkdir()
                save=self.make(root)
                old=(root/MARKER).read_bytes()
                holder=work_holder(root,"a"*40,work)
                stage=holder/"game"
                (stage/"Data").mkdir(parents=True)
                (stage/"Data/Map609.rxdata").write_bytes(b"new Kanto")
                result=subprocess.run([sys.executable,"-c",child,str(root),str(stage),str(holder/"backup"),point])
                self.assertEqual(result.returncode,91)
                self.assertTrue((root/RECOVERY_FILE).is_file())
                with self.assertRaisesRegex(ValueError,"interrompida"):
                    recover_source_install(root,work,False)
                self.assertEqual(recover_source_install(root,work,True),expected)
                self.assertFalse((root/RECOVERY_FILE).exists())
                self.assertEqual((root/MARKER).read_bytes(),old if expected=="rolled_back" else b"completed")
                self.assertEqual((root/"Data/Map609.rxdata").exists(),expected=="committed")
                self.assertEqual(save.read_bytes(),b"not a real save; do not inspect")
