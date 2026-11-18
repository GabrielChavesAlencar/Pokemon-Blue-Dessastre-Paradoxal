# Regression for the actual JoiPlay New Game error:
# [Blue Battle Presentation and Story] RegionStart.rb:66 NameError
# uninitialized constant BlueRegionStart::JSON.
# Must work without Ruby's optional JSON/Digest gems and never fake Hoenn.
require "tmpdir"
require "fileutils"

# Simulate the minimal Ruby runtime in the Android RPG Maker plugin.
module Kernel
  alias_method :blue_native_require, :require
  def require(feature)
    if feature == "json" || feature == "digest"
      raise LoadError, "#{feature} unavailable in JoiPlay"
    end
    blue_native_require(feature)
  end
end
Object.send(:remove_const, :JSON) if Object.const_defined?(:JSON, false)
Object.send(:remove_const, :Digest) if Object.const_defined?(:Digest, false)

def pbRgssExists?(name); File.file?(name); end
def check(ok, msg); raise "JOIPLAY_NEW_GAME: #{msg}" unless ok; end

load File.expand_path(ARGV.fetch(0))
check(!defined?(::JSON), "fixture unexpectedly has JSON constant")

Dir.mktmpdir("blue-joiplay-no-json") do |directory|
  Dir.chdir(directory) do
    FileUtils.mkdir_p("Data")
    FileUtils.mkdir_p("PBS")
    FileUtils.mkdir_p("Plugins/ZZZZZ Blue Hoenn Pilot")

    # The full 199-map verified installation has an independent compact
    # registry and readied markers written by install_hoenn.py.
    maps = {}
    199.times { |i| maps[(i + 1).to_s] = 700 + i }
    home = [maps["8"], 25, 6, 2]
    town = [maps["7"], 10, 10, 2]
    File.write("Data/blue-hoenn-install.json",
               '{"schema":1,"region":"HOENN","source_commit":"' +
               BlueRegionStart::HOENN_REVISION +
               '","status":"INTEGRATED_FILES_READY_FOR_NATIVE_QA","maps":{' +
               maps.map { |key,value| %("#{key}":#{value}) }.join(",") +
               '},"start":[' + home.join(",") +
               '],"town":[' + town.join(",") + ']}')
    File.write("Data/blue-hoenn-pilot.txt",
               "BLUE_HOENN_PILOT_V1\n#{home[0]},25,6\n" +
               maps.map { |source,dest| "#{source},#{dest}\n" }.join)
    File.write("Data/blue-hoenn-ready.txt",
               "BLUE_HOENN_READY_V1,199,#{home[0]},#{town.join(',')}\n")
    File.write("Data/blue-hoenn-start.txt",
               "BLUE_HOENN_START_V1,HOENN,#{home[0]},25,6\n")
    %w[Data/MapInfos.rxdata Data/Tilesets.rxdata
       PBS/trainers_hoenn_pilot.txt PBS/trainer_types_hoenn_pilot.txt
       PBS/encounters_hoenn_pilot.txt PBS/map_metadata_hoenn_pilot.txt].each do |file|
      File.write(file, "compiled fixture")
    end
    File.write("Plugins/ZZZZZ Blue Hoenn Pilot/HoennPilot.rb", "fixture")
    maps.values.each { |id| File.write(sprintf("Data/Map%03d.rxdata", id), "map") }

    check(BlueRegionStart.hoenn_manifest["maps"].size == 199,
          "Hoenn manifest not decoded from compact proof without JSON")
    check(BlueRegionStart.hoenn_integrated?,
          "installed Hoenn incorrectly blocked without JSON")
    check(BlueRegionStart.request_initial("HOENN"),
          "New Game Hoenn raised NameError or failed")
    check(BlueRegionStart.choose_initial == "HOENN",
          "Hoenn selection was replaced with Decades")
    check(BlueRegionStart.hoenn_spawn == home[0, 3],
          "wrong starting position")
    check(BlueRegionStart.hoenn_town_point == town,
          "wrong Littleroot arrival point")
    # Regression: the SAME combined Android ZIP has all 142 Kanto maps.
    # JoiPlay sometimes provides an unusable JSON constant rather than no
    # JSON constant at all. Kanto must work in both cases, just as Hoenn does.
    FileUtils.mkdir_p("Plugins/ZZZZZ Blue Kanto Pilot")
    kanto_maps = {}
    # Match the 142 legacy namespace without the three later-added FRLG
    # source IDs (53, 54, 55). Their new destination slots append at 442-444.
    legacy_source_ids = (1..145).to_a - [53, 54, 55]
    legacy_source_ids.each_with_index { |id, i| kanto_maps[id.to_s] = 300 + i }
    kanto_home = [kanto_maps["7"], 25, 7]
    File.write("Data/blue-kanto-install.json",
               '{"schema":1,"maps":{' +
               kanto_maps.map { |key,value| %("#{key}":#{value}) }.join(",") +
               '},"source":"Essentials FRLG 21.1"}')
    File.write("Data/blue-kanto-start.txt",
               "BLUE_KANTO_START_V1,KANTO,#{kanto_home.join(',')}\n")
    File.write("Data/blue-kanto-ready.txt",
               "BLUE_KANTO_READY_V1,142,#{kanto_home[0]}\n")
    %w[Data/MapInfos.rxdata Data/Tilesets.rxdata
       PBS/encounters_kanto.txt PBS/trainers_kanto.txt
       PBS/trainer_types_kanto.txt PBS/map_metadata_kanto.txt
       PBS/map_connections_kanto.txt Data/blue-kanto-locale.dat
       Data/blue-kanto-npc-dialogues.dat
       Data/blue-kanto-pewter-route3-gate.txt
       Data/blue-kanto-pewter-mom-sprite.txt
       Data/blue-kanto-viridian-route2-line.txt
       Data/blue-kanto-silph-floors.txt].each { |file| File.write(file, "fixture") }
    File.write("Plugins/ZZZZZ Blue Kanto Pilot/KantoPilot.rb", "fixture")
    kanto_maps.values.each { |id|
      File.write(sprintf("Data/Map%03d.rxdata", id), "kanto")
    }
    check(BlueRegionStart.kanto_integrated?,
          "Kanto incorrectly marked 'instalacao necessaria' without JSON")
    check(BlueRegionStart.request_initial("KANTO"),
          "New Game Kanto could not be selected without JSON")
    check(BlueRegionStart.choose_initial == "KANTO",
          "Kanto starting selection was replaced by Decades")
    # Reproduces Android plugin providing ::JSON without .parse.
    Object.const_set(:JSON, Module.new)
    check(BlueRegionStart.kanto_integrated?,
          "Kanto blocked by incomplete JoiPlay JSON constant")
    ::JSON.define_singleton_method(:parse) { |_raw| nil }
    check(BlueRegionStart.kanto_integrated?,
          "Kanto blocked when JoiPlay JSON returns nil")
    ::JSON.define_singleton_method(:parse) { |_raw| raise NoMethodError, "broken JSON" }
    check(BlueRegionStart.kanto_integrated?,
          "Kanto blocked when JoiPlay JSON parser raises")
    Object.send(:remove_const, :JSON)
    # The fallback is NOT a bypass: all physical 142 maps and the proof
    # must exist. Hoenn stays independent and available.
    missing = sprintf("Data/Map%03d.rxdata", kanto_maps["42"])
    File.delete(missing)
    check(!BlueRegionStart.kanto_integrated?,
          "Incomplete Kanto incorrectly unlocked with only 141 maps")
    File.write(missing, "kanto")
    File.write("Data/blue-kanto-ready.txt", "BLUE_KANTO_READY_V1,142,999\n")
    check(!BlueRegionStart.kanto_integrated?,
          "Kanto unlocked with invalid ready gate")
    File.write("Data/blue-kanto-ready.txt",
               "BLUE_KANTO_READY_V1,142,#{kanto_home[0]}\n")
    check(BlueRegionStart.kanto_integrated? && BlueRegionStart.hoenn_integrated?,
          "Kanto proof repair affected Hoenn")
    check(BlueRegionStart.request_initial("HOENN"),
          "Hoenn unavailable after Kanto JSON fallback")

    # The new 145-map Android installation must be accepted WITHOUT JSON,
    # but only when all three source maps and the correct ready gate exist.
    kanto_maps.merge!({"53"=>442,"54"=>443,"55"=>444})
    File.write("Data/blue-kanto-install.json",
               '{"schema":1,"maps":{' +
               kanto_maps.map { |key,value| %("#{key}":#{value}) }.join(",") +
               '},"source":"Essentials FRLG 21.1"}')
    File.write("Data/blue-kanto-ready.txt",
               "BLUE_KANTO_READY_V1,145,#{kanto_home[0]}\n")
    check(!BlueRegionStart.kanto_integrated?,
          "145-map manifest accepted before new route files were installed")
    [442,443,444].each { |id| File.write(sprintf("Data/Map%03d.rxdata", id), "kanto") }
    check(BlueRegionStart.kanto_integrated?,
          "JoiPlay rejected verified 145-map Cerulean/Bill installation")
    check(BlueRegionStart.request_initial("KANTO"),
          "New Game Kanto rejected valid 145-map installation")
    File.delete("Data/Map443.rxdata")
    check(!BlueRegionStart.kanto_integrated?,
          "Kanto accepted missing physical Route 25 MapID")
    File.write("Data/Map443.rxdata", "kanto")
    File.write("Data/blue-kanto-ready.txt",
               "BLUE_KANTO_READY_V1,142,#{kanto_home[0]}\n")
    check(!BlueRegionStart.kanto_integrated?,
          "Kanto accepted 145-map manifest with old 142-map ready marker")
    File.write("Data/blue-kanto-ready.txt",
               "BLUE_KANTO_READY_V1,145,#{kanto_home[0]}\n")
    check(BlueRegionStart.kanto_integrated? && BlueRegionStart.hoenn_integrated?,
          "145-map new Kanto impacted Hoenn or failed its own proof")

    check(BlueRegionStart.request_initial("DECADES"),
          "Decades new game blocked by missing JSON")
    check(BlueRegionStart.choose_initial == "DECADES",
          "Decades initial selection was lost")

    # Johto is currently unverified and must remain unavailable, but its
    # optional JSON/Digest parsing must never crash the common title menu.
    File.write("Data/blue-johto-install.json", "{}")
    check(BlueRegionStart.johto_install_proof.nil?,
          "Johto silently unlocked without JSON/Digest")

    # No region may be entered from a fabricated marker.
    File.delete(sprintf("Data/Map%03d.rxdata", maps["42"]))
    check(!BlueRegionStart.hoenn_integrated?,
          "Hoenn unlocked with a missing original map")
    check(!BlueRegionStart.request_initial("HOENN"),
          "New Game accepted incomplete 199-map installation")
  end
end
puts "PASS: JoiPlay New Game without JSON, 142 legacy/145 new Kanto +199 Hoenn, no false ready"
