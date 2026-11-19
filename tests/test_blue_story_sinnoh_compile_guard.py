"""Real Ruby execution of the generated QA compiler boundary, without Game.exe."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zlib

from scripts.regions.install_sinnoh_experimental_windows import patch_bootstrap
from scripts.official_rules.prepare_restore import Marshal, RubyString, dump

TOKEN = "012345abcdef"
IDS = list(range(442, 451))
MAIN = b"def boot\n    PluginManager.runPlugins\n    Compiler.main\nend\nboot\n"
RAW = b"\x04\x08" + dump([[1, RubyString(b"Main"), RubyString(zlib.compress(MAIN))]])
HARNESS = r'''
module PluginManager
  def self.runPlugins; end
end
module Compiler
  def self.main
    (442..450).each { |id| File.binwrite("Data/Map%03d.rxdata" % id, "compiler door rewrite") }
    File.binwrite("Data/MapInfos.rxdata", "compiler index rewrite")
    File.binwrite("Data/Tilesets.rxdata", "compiler tile rewrite")
    File.binwrite("Data/Map441.rxdata", "unrelated compiler output")
    File.binwrite("Data/trainers.dat", "Barry PBS output")
    raise "synthetic compiler failure" if ENV["GUARD_CASE"] == "failure"
  end
end
module GameData
  module Trainer
    def self.load; end
    def self.exists?(*args); true; end
  end
end
protected_paths = (442..450).map { |id| "Data/Map%03d.rxdata" % id } +
                  ["Data/MapInfos.rxdata", "Data/Tilesets.rxdata"]
Dir.chdir(ARGV[1]) do
  begin
    eval(File.read(ARGV[0]), TOPLEVEL_BINDING, "GeneratedMain")
  rescue SystemExit => error
    raise "unexpected exit" unless error.status == 0
  rescue RuntimeError => error
    raise unless ENV["GUARD_CASE"] == "failure" && error.message == "synthetic compiler failure"
  end
  active = ["normal", "failure"].include?(ENV["GUARD_CASE"])
  protected_paths.each do |path|
    expected = active ? "original:" + path : "compiler " +
      (path.include?("MapInfos") ? "index" : path.include?("Tilesets") ? "tile" : "door") + " rewrite"
    raise "protected bytes changed: #{path}" unless File.binread(path) == expected
  end
  raise "lost trainer compilation" unless File.binread("Data/trainers.dat") == "Barry PBS output"
  raise "affected unrelated map" unless File.binread("Data/Map441.rxdata") == "unrelated compiler output"
  compiled = File.file?("Data/sinnoh-experimental-compiled.txt")
  raise "incorrect compiler proof" unless compiled == (ENV["GUARD_CASE"] == "normal")
end
puts "PASS: scoped Sinnoh compiler snapshot, trainer output and unrelated maps"
'''


class SinnohCompileGuardTests(unittest.TestCase):
    def test_rejects_invalid_or_duplicate_protected_map_ids(self):
        for ids in ([442] * 9, [1, *range(443, 451)], [True, *range(443, 451)]):
            with self.subTest(ids=ids), self.assertRaisesRegex(ValueError, "COMPILE_MAP_IDS"):
                patch_bootstrap(RAW, TOKEN, ids)

    @unittest.skipUnless(shutil.which("ruby"), "Ruby unavailable locally; exercised in CI")
    def test_compiler_rewrites_cannot_change_pinned_maps_or_fake_success(self):
        for case in ("normal", "failure", "no-request", "wrong-folder"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                qa = root / ("game-sinnoh-experimental-" +
                             ("ffffffffffff" if case == "wrong-folder" else TOKEN))
                (qa / "Data").mkdir(parents=True)
                paths = [f"Data/Map{mid:03}.rxdata" for mid in IDS]
                paths += ["Data/MapInfos.rxdata", "Data/Tilesets.rxdata"]
                for path in paths:
                    (qa / path).write_text("original:" + path, encoding="utf8")
                (qa / "sinnoh-experimental-qa.json").write_text("{}")
                if case != "no-request":
                    (qa / "Data/sinnoh-experimental-compile-request.txt").write_text("proof")
                rows = Marshal(patch_bootstrap(RAW, TOKEN, IDS)).read()
                main = root / "GeneratedMain.rb"
                main.write_bytes(zlib.decompress(rows[0][2]))
                harness = root / "harness.rb"
                harness.write_text(HARNESS, encoding="utf8")
                run = subprocess.run([shutil.which("ruby"), str(harness), str(main), str(qa)],
                                     env={**os.environ, "GUARD_CASE": case},
                                     capture_output=True, text=True, timeout=30)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
