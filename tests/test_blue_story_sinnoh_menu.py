"""Blue-Story native menu for opt-in Sinnoh J12-E QA copy, no manual BAT.

These tests use temporary synthetic folders and never access Game.exe or saves.
"""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.windows import launch_sinnoh_pilot as ui

ROOT=Path(__file__).resolve().parents[1]

class BlueStorySinnohMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.csharp=(ROOT/"scripts/windows/Bootstrap.cs").read_text("utf-8")
        cls.pipeline=(ROOT/".github/workflows/blue-story-windows.yml").read_text("utf-8")
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="blue-story-sinnoh-menu-synthetic-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/"scripts").mkdir()
        (self.root/"scripts/install_game.py").write_text("# dummy","utf-8")
        (self.root/"game").mkdir()
        (self.root/"game/Game.exe").write_bytes(b"synthetic fake executable")
        self.receipt=self.root/".blue-work"/ui.RECEIPT_NAME
    def fake_install(self,base,files,report,project):
        dest=project/".blue-work/game-sinnoh-experimental-abc123abc123"
        dest.mkdir(parents=True)
        (dest/"INICIAR_SINNOH_EXPERIMENTAL.bat").write_text("rem Synthetic")
        (dest/"sinnoh-experimental-qa.json").write_text("{}")
        return dest
    def simulate(self):
        with patch.object(ui.installer,"build_files",return_value=(
            {"Data/Map442.rxdata":b"synthetic source"},
            {"main_game_modified":False,"r09_native_qa_executed":0}
        )) as prep,patch.object(ui.installer,"install_copy",side_effect=self.fake_install) as copy:
            return ui.prepare(self.root,self.root/"game",self.receipt),prep,copy
    def test_01_built_in_menu_shows_named_sinnoh_button(self):
        self.assertIn('Text="Testar piloto Sinnoh"',self.csharp)
        self.assertIn('Text="Jogar campanha"',self.csharp)
    def test_02_requires_explicit_menu_choice_not_auto_install(self):
        self.assertIn('sinnoh.Click+=delegate { selection.TrySetResult("sinnoh"); };',self.csharp)
        self.assertIn('if(chosen=="sinnoh") {',self.csharp)
        self.assertIn('string chosen=await selection.Task;',self.csharp)
        # A source-only update opens the menu, even with incomplete Kanto.
        self.assertGreater(self.csharp.index('string chosen=await selection.Task;'),
                           self.csharp.index('else await Task.Run((Action)PrepareSourceOnly);'))
        # Full regional install is ONLY called after choosing the campaign.
        self.assertLess(self.csharp.index('string chosen=await selection.Task;'),
                        self.csharp.index('title.Text="Verificando a instalacao da campanha..."'))
    def test_03_sinnoh_option_precedes_johto_missing_prompt(self):
        self.assertLess(self.csharp.index('if(chosen=="sinnoh")'),
                        self.csharp.index('if(!Hub && !JohtoReady()'))
    def test_04_not_shown_in_battle_hub(self):
        self.assertIn('if(!Hub) {\n                                title.Text="Escolha como deseja jogar";',self.csharp)
        self.assertIn('if(Hub)throw new Exception("Sinnoh experimental',self.csharp)
    def test_05_uses_bundled_portable_python_not_system_python(self):
        self.assertIn('string python=Runtime("python","python.exe");',self.csharp)
        self.assertIn('"scripts/windows/launch_sinnoh_pilot.py"',self.csharp)
    def test_06_launches_only_qa_copy_launcher(self):
        self.assertIn('scripts/windows/sinnoh_qa_supervisor.py',self.csharp)
        self.assertNotIn('Process.Start(new ProcessStartInfo(Path.Combine(game,"Game.exe"))',self.csharp[:self.csharp.index('if(chosen=="sinnoh")')])
    def test_07_python_receipt_has_no_native_approval(self):
        info,prep,copy=self.simulate()
        self.assertFalse(info["main_game_modified"])
        self.assertEqual(info["native_qa_cases_approved"],0)
        self.assertFalse(info["R07_approved"])
        self.assertFalse(info["R08_approved"])
        self.assertFalse(info["R09_approved"])
        self.assertFalse(info["playable_verified"])
        prep.assert_called_once()
        copy.assert_called_once()
    def test_08_receipt_writes_only_to_managed_work_directory(self):
        info,_,_=self.simulate()
        self.assertEqual(json.loads(self.receipt.read_text("utf-8")),info)
        self.assertTrue(Path(info["qa_directory"]).is_relative_to(self.root/".blue-work"))
    def test_09_synthetic_game_source_unchanged(self):
        previous=(self.root/"game/Game.exe").read_bytes()
        self.simulate()
        self.assertEqual((self.root/"game/Game.exe").read_bytes(),previous)
    def test_10_reject_unmanaged_game_path(self):
        foreign=self.root/"another-game"
        foreign.mkdir()
        with self.assertRaisesRegex(ValueError,"BLUE_STORY_ONLY_MANAGED_READONLY_GAME"):
            ui.prepare(self.root,foreign,self.receipt)
    def test_11_reject_existing_stale_receipt(self):
        self.receipt.parent.mkdir();self.receipt.write_text("{}")
        with self.assertRaisesRegex(ValueError,"RECEIPT_NOT_NEW"):
            ui.prepare(self.root,self.root/"game",self.receipt)
    def test_12_reject_receipt_outside_workdir(self):
        with self.assertRaisesRegex(ValueError,"RECEIPT_NOT_NEW"):
            ui.prepare(self.root,self.root/"game",self.root/"other.json")
    def test_13_reject_invalid_project_root(self):
        (self.root/"scripts/install_game.py").unlink()
        with self.assertRaisesRegex(ValueError,"PROJECT_ROOT_INVALID"):
            ui.prepare(self.root,self.root/"game",self.receipt)
    def test_14_reject_native_qa_falsely_approved(self):
        with patch.object(ui.installer,"build_files",return_value=({},{
            "main_game_modified":False,"r09_native_qa_executed":44
        })):
            with self.assertRaisesRegex(ValueError,"NATIVE_QA_MUST_REMAIN_UNVERIFIED"):
                ui.prepare(self.root,self.root/"game",self.receipt)
        self.assertFalse(self.receipt.exists())
    def test_15_reject_main_game_modified(self):
        with patch.object(ui.installer,"build_files",return_value=({},{
            "main_game_modified":True,"r09_native_qa_executed":0
        })):
            with self.assertRaisesRegex(ValueError,"SOURCE_GAME_MUTATION_CLAIM"):
                ui.prepare(self.root,self.root/"game",self.receipt)
    def test_16_reject_unsafe_copy_name_or_location(self):
        with patch.object(ui.installer,"build_files",return_value=({},{
            "main_game_modified":False,"r09_native_qa_executed":0
        })),patch.object(ui.installer,"install_copy",return_value=self.root/"game"):
            with self.assertRaisesRegex(ValueError,"INCOMPLETE_OR_UNSAFE_QA_COPY"):
                ui.prepare(self.root,self.root/"game",self.receipt)
    def test_17_no_auto_copy_when_source_preflight_fails(self):
        with patch.object(ui.installer,"build_files",side_effect=ValueError("Local MapInfos absent")),\
             patch.object(ui.installer,"install_copy") as install:
            with self.assertRaisesRegex(ValueError,"MapInfos"):
                ui.prepare(self.root,self.root/"game",self.receipt)
            install.assert_not_called()
    def test_18_one_click_supervisor_waits_and_closes(self):
        self.assertIn('scripts/windows/sinnoh_qa_supervisor.py',self.csharp)
        self.assertIn('"--project-root",Root,"--qa-dir",qa',self.csharp)
        self.assertIn('await Task.Run(delegate {',self.csharp)
        self.assertIn('form.Close();return;',self.csharp)
        self.assertNotIn('experimental.WaitForExit()',self.csharp)
    def test_19_release_is_not_published_on_pr(self):
        self.assertIn("pull_request:",self.pipeline)
        self.assertIn("if: github.event_name != 'pull_request'",self.pipeline)
    def test_20_menu_retains_regular_game_option(self):
        self.assertIn('campaign.Click+=delegate { selection.TrySetResult("campaign"); };',self.csharp)
        self.assertIn('if(!Hub && !JohtoReady())',self.csharp)
        self.assertIn('string game=Path.Combine(Root,"game");var process=Process.Start',self.csharp)
    def test_21_reparse_points_rejected_by_exe(self):
        self.assertIn('FileAttributes.ReparsePoint',self.csharp)
    def test_22_experimental_copy_not_implicitly_downloaded(self):
        self.assertNotIn('install_sinnoh_experimental_windows.py","--install"',self.csharp)
        self.assertIn('"--project-root",Root,"--game-dir",game',self.csharp)

    def test_23_kanto_142_of_145_cannot_block_sinnoh_menu(self):
        # Previous behavior performed install_game.py before the menu; the
        # protected Kanto 142/145 state raised ValueError and blocked Sinnoh.
        before=self.csharp.index('else await Task.Run((Action)PrepareSourceOnly);')
        menu=self.csharp.index('string chosen=await selection.Task;')
        sinnoh=self.csharp.index('if(chosen=="sinnoh") {')
        main=self.csharp.index('title.Text="Verificando a instalacao da campanha..."')
        self.assertLess(before,menu)
        self.assertLess(menu,sinnoh)
        self.assertLess(sinnoh,main)
    def test_24_source_only_branch_never_runs_kanto_installer(self):
        source=self.csharp.index('if(sourceOnly) {')
        back=self.csharp.index('StageEmbeddedJohto();',source)
        install=self.csharp.index('var install=new List<string>{"scripts/install_game.py","--apply"};')
        self.assertLess(source,back)
        self.assertLess(back,install)
        self.assertIn('return;',self.csharp[source:back])
        self.assertIn('static void PrepareSourceOnly() { Prepare(true); }',self.csharp)
    def test_25_main_campaign_still_runs_all_regional_install_checks(self):
        main=self.csharp.index('title.Text="Verificando a instalacao da campanha..."')
        self.assertIn('await Task.Run((Action)Prepare);',self.csharp[main:main+600])
        self.assertIn('static void Prepare() { Prepare(false); }',self.csharp)
        self.assertIn('Run(python,install.ToArray(),pathExtra);',self.csharp)
    def test_26_blue_battle_hub_still_uses_full_prepare(self):
        self.assertIn('if(Hub)await Task.Run((Action)Prepare);',self.csharp)
    def test_27_kanto_verification_error_is_not_suppressed_for_campaign(self):
        self.assertIn('if(!Hub && !experimentalSelected)',self.csharp)
        self.assertIn('Kanto NAO instalado: ',self.csharp)
        self.assertIn('Em caso de mapa incompleto, a campanha sera bloqueada',self.csharp)
    def test_28_sinnoh_qa_launch_still_requires_proof_and_saves_isolation(self):
        self.assertIn('PrepareSinnohTestCopy',self.csharp)
        self.assertIn('INICIAR_SINNOH_EXPERIMENTAL.bat',self.csharp)
        self.assertIn('SINNOH_PRIVATE_EXPERIMENTAL_COPY_NOT_APPROVED',self.csharp)
        self.assertIn('main_game_modified',self.csharp)
        self.assertIn('native_qa_cases_approved',self.csharp)

    def test_29_show_actual_python_code2_failure_in_dialog(self):
        self.assertIn('var tail=new Queue<string>();',self.csharp)
        self.assertIn('if(process.ExitCode!=0) {',self.csharp)
        self.assertIn('Motivo: ',self.csharp)
        self.assertIn('while(tail.Count>5)tail.Dequeue();',self.csharp)

    def test_31_no_external_bat_is_needed_for_restarting_sinnoh_qa(self):
        self.assertNotIn('Process.Start(new ProcessStartInfo(bat)',self.csharp)
        self.assertIn('Run(python,new[]{"scripts/windows/sinnoh_qa_supervisor.py"',self.csharp)

    def test_30_repair_must_not_bypass_native_kanto_gate(self):
        self.assertIn('if(!Hub && !experimentalSelected)',self.csharp)
        self.assertIn('if(sourceOnly) {',self.csharp)
        self.assertIn('Run(python,install.ToArray(),pathExtra);',self.csharp)

if __name__=="__main__":unittest.main()
