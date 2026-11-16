# Reproduces the SystemStackError seen in Boot.rb:774 without Game.exe.
# Johto must NEVER prepend Compiler.main: other plugins alias it after
# our plugin loads, forming an infinite alias/super cycle.
require "tmpdir"
require "fileutils"

module EventHandlers
  @events = {}
  def self.add(event, id, callback)
    @events[[event, id]] = callback
  end
  def self.enter_map
    @events.fetch([:on_enter_map, :blue_johto_main_compile_status]).call(nil)
  end
end

module Compiler
  @native_calls = 0
  def self.main
    @native_calls += 1
    :compiled
  end
  def self.native_calls
    @native_calls
  end
end

module BlueRegionStart
  def self.johto_preview_proof
    $johto_preview_installed ? { "status" => "EXPERIMENTAL_PRIVATE_UNVERIFIED" } : nil
  end
end

module GameData
  module Trainer
    def self.exists?(*_args)
      $johto_trainers_compiled
    end
  end
  module Encounter
    def self.exists?(*_args)
      $johto_encounters_compiled
    end
  end
end

def require_check(value, message)
  raise message unless value
end

$johto_preview_installed = false
$johto_trainers_compiled = false
$johto_encounters_compiled = false

load ARGV.fetch(0)
require_check(defined?(BlueJohtoMainCompile), "Johto runtime did not load")
require_check(!defined?(BlueJohtoMainCompile::CompilerHook),
              "Recursive Johto CompilerHook is still installed")
require_check(!Compiler.singleton_class.ancestors.include?(BlueJohtoMainCompile),
              "Johto plugin must not prepend Compiler.singleton_class")

# These are the three actual project patterns: aliases of Compiler.main
# created by Blue Battle Options, ZA Megas, and Blue Music.
[:blue_options_original_main, :blue_za_original_main, :blue_music_original_main].each do |original|
  Compiler.singleton_class.class_eval do
    alias_method original, :main
    define_method(:main) { send(original) }
  end
end
require_check(Compiler.main == :compiled, "Native compiler result changed")
require_check(Compiler.native_calls == 1, "Compiler.main called recursively")

Dir.mktmpdir("johto-native-compiler-") do |root|
  Dir.chdir(root) do
    FileUtils.mkdir_p("Data")
    EventHandlers.enter_map
    require_check(BlueJohtoMainCompile::STAMPS.keys.none? { |p| File.exist?(p) },
                  "Uninstalled Johto created fake compiled markers")
    $johto_preview_installed = true
    EventHandlers.enter_map
    require_check(BlueJohtoMainCompile::STAMPS.keys.none? { |p| File.exist?(p) },
                  "Johto issued readiness markers before PBS data was compiled")
    $johto_trainers_compiled = $johto_encounters_compiled = true
    EventHandlers.enter_map
    BlueJohtoMainCompile::STAMPS.each do |path, token|
      require_check(File.file?(path) && File.read(path).strip == token,
                    "Missing real compiled trainer/encounter token: #{path}")
    end
    EventHandlers.enter_map
    require_check(Compiler.native_calls == 1, "Map-enter check invoked Compiler.main")
    $johto_trainers_compiled = false
    EventHandlers.enter_map
    require_check(BlueJohtoMainCompile::STAMPS.keys.none? { |p| File.exist?(p) },
                  "Stale Johto markers were not invalidated")
  end
end
puts "Blue Johto compiler alias regression and map-ready checks OK"
