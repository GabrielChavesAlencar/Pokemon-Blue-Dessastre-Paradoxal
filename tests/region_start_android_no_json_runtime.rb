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
puts "PASS: JoiPlay New Game without JSON, 199 real-map gate, Decades/Kanto unchanged"
