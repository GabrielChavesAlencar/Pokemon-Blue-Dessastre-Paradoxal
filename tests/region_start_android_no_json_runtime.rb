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

region_start = File.expand_path(ARGV.fetch(0))
load region_start
load File.join(File.dirname(region_start), "TitleKanto.rb")
check(!defined?(::JSON), "fixture unexpectedly has JSON constant")

Dir.mktmpdir("blue-joiplay-no-json") do |directory|
  Dir.chdir(directory) do
    FileUtils.mkdir_p("Data")
    FileUtils.mkdir_p("PBS")
    FileUtils.mkdir_p("Plugins/ZZZZZ Blue Hoenn Pilot")

    # Sinnoh shares the same game only after the real runtime and all maps
    # are present. The title must not interpret a private QA copy as shared.
    check(!BlueRegionStart.request_initial("SINNOH"), "missing Sinnoh unlocked")
    Object.const_set(:BlueSinnohSharedEvents, Module.new)
    BlueSinnohSharedEvents.define_singleton_method(:ready?) { true }
    ids = (442..585).to_a
    File.write("Data/blue-sinnoh-shared.json", "{}")
    File.write("Data/blue-sinnoh-shared.txt", "BLUE_SINNOH_SHARED_V1\n442,3,6\n443,2,3\n443,2,4\n#{ids.join(',')}\n")
    ids.each { |id| File.write(sprintf("Data/Map%03d.rxdata",id), "map") }
    check(BlueRegionStart.request_initial("SINNOH"), "Sinnoh blocked without JSON")
    check(BlueRegionStart.choose_initial == "SINNOH", "Sinnoh fallback chose Decades")
    check(BlueRegionStart.sinnoh_shared_points == [[442,3,6],[443,2,3,2],[443,2,4]], "wrong Sinnoh travel points")
    File.delete("Data/Map585.rxdata")
    check(!BlueRegionStart.sinnoh_spawn, "Sinnoh stayed open with a missing map")
    File.write("Data/Map585.rxdata", "map")
    File.write("sinnoh-experimental-qa.json", "{}")
    check(!BlueRegionStart.sinnoh_spawn, "isolated QA authorized shared Sinnoh")
    File.delete("sinnoh-experimental-qa.json")

    # The full 199-map verified installation has an independent compact
    # registry and readied markers written by install_hoenn.py.
    maps = BlueRegionStart::HOENN_LEGACY_SOURCES.each_with_index.to_h { |source, index| [source, 700 + index] }
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
    # Exercise the same installed files after the V2 migration, including
    # SHA-256 in the bundled parser path with neither optional gem present.
    compact_file = BlueRegionStart::HOENN_PILOT_METADATA
    File.write(compact_file, File.read(compact_file).sub("BLUE_HOENN_PILOT_V1", "BLUE_HOENN_PILOT_V2"))
    [BlueRegionStart::HOENN_READY, BlueRegionStart::HOENN_START].each do |name|
      File.write(name, File.read(name).sub("_V1,", "_V2,"))
    end
    manifest_file = BlueRegionStart::HOENN_INSTALL
    manifest_v2 = File.read(manifest_file).sub('"schema":1', '"schema":2,"catalog_revision":1')
    legacy_blob = maps.map { |source, dest| %("#{source}":#{dest}) }.join(",")
    compact_hash = BlueSinnohQA.sha256_file(compact_file)
    manifest_v2 = manifest_v2.sub(/\}\z/,
      ',"legacy_maps":{' + legacy_blob + '},"installed_sha256":{"' + compact_file + '":"' + compact_hash + '"}}')
    File.write(manifest_file, manifest_v2)
    check(BlueRegionStart.hoenn_integrated? && BlueRegionStart.hoenn_spawn == home[0,3],
          "V2 did not unlock with bundled parser and SHA-256")
    File.write(manifest_file, manifest_v2.sub('{', '{"schema":1,'))
    check(!BlueRegionStart.hoenn_integrated?, "V2 accepted duplicate JSON fields")
    File.write(manifest_file, manifest_v2.sub(compact_hash, "0"*64))
    check(!BlueRegionStart.hoenn_integrated?, "V2 accepted invalid compact SHA-256")
    File.write(manifest_file, manifest_v2)
    # Regression: the SAME combined Android ZIP has all 142 Kanto maps.
    # JoiPlay sometimes provides an unusable JSON constant rather than no
    # JSON constant at all. Kanto must work in both cases, just as Hoenn does.
    FileUtils.mkdir_p("Plugins/ZZZZZ Blue Kanto Pilot")
    kanto_maps = {}
    142.times { |i| kanto_maps[(i + 1).to_s] = 300 + i }
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

    # Upgrade the same synthetic legacy registry to an independent 156-map
    # installation. The additional four destinations skip Sinnoh reservations.
    # Every existing legacy file remains in place.
    expanded = kanto_maps.reject { |source,_| (68..71).include?(source.to_i) }
    # Synthetic source keys only; the real source identity and 152->156
    # ownership migration are tested separately in the Windows native CI.
    (143..156).each { |source| expanded[source.to_s] = 600 + source - 143 }
    (68..71).each { |source| expanded[source.to_s] = 596 + source - 68 }
    check(expanded.size == 156,"bad expanded fixture")
    write_kanto_registry = proc do |registry,count|
      File.write("Data/blue-kanto-install.json",
                 '{"schema":1,"maps":{' +
                 registry.map { |key,value| %("#{key}":#{value}) }.join(",") +
                 '},"source":"Essentials FRLG 21.1"}')
      File.write("Data/blue-kanto-ready.txt",
                 "BLUE_KANTO_READY_V1,#{count},#{kanto_home[0]}\n")
    end
    expanded.values.each { |id| File.write(sprintf("Data/Map%03d.rxdata",id), "kanto") }
    write_kanto_registry.call(expanded,156)
    check(BlueRegionStart.kanto_integrated?, "156-map Kanto rejected without JSON")
    check(BlueRegionStart.kanto_compact_maps(kanto_home) == expanded, "156-map registry changed")
    check(BlueRegionStart.request_initial("KANTO") &&
          BlueRegionStart.choose_initial == "KANTO", "156-map Kanto start blocked")
    missing_new = sprintf("Data/Map%03d.rxdata",expanded["71"])
    File.delete(missing_new)
    check(!BlueRegionStart.kanto_integrated?, "156-map gate accepted missing fisherman house")
    File.write(missing_new,"kanto")
    wrong_source = expanded.dup
    wrong_source["999"] = wrong_source.delete("68")
    write_kanto_registry.call(wrong_source,156)
    check(!BlueRegionStart.kanto_integrated?, "156-map gate accepted missing Fan Club source")
    reserved = expanded.merge("68"=>455)
    write_kanto_registry.call(reserved,156)
    check(!BlueRegionStart.kanto_integrated?, "156-map gate accepted reserved Sinnoh ID")
    write_kanto_registry.call(expanded,152)
    check(!BlueRegionStart.kanto_integrated?, "156-map gate accepted stale marker count")
    write_kanto_registry.call(expanded,156)
    check(BlueRegionStart.kanto_integrated? && BlueRegionStart.hoenn_integrated?,
          "156-map gate repair affected Hoenn")
    Object.const_set(:JSON, Module.new)
    ::JSON.define_singleton_method(:parse) { |_raw| raise NoMethodError, "broken JSON" }
    check(BlueRegionStart.kanto_integrated?, "156-map gate rejected broken JoiPlay JSON")
    Object.send(:remove_const, :JSON)
    puts "KANTO_K03B_156_READY_GATE_NO_JSON_OK"

    # Construct an independent synthetic legacy/append registry without reusing
    # the provisional source keys or destinations from the older mock above.
    k04 = {"86"=>604, "87"=>605, "88"=>606, "90"=>607, "91"=>608}
    before_rock = expanded.reject { |source, dest| k04.key?(source) || k04.value?(dest) }
    ["23","79","81","82"].each_with_index { |source,index| before_rock[source] = 600 + index unless before_rock.key?(source) }
    (800..920).each do |id|
      break if before_rock.size == 160
      before_rock[id.to_s] = id
    end
    check(before_rock.size == 160 && before_rock.values.uniq.size == 160,"bad K04 predecessor fixture")
    k04_maps = before_rock.merge(k04)
    k04_maps.values.each { |id| File.write(sprintf("Data/Map%03d.rxdata",id), "kanto") }
    write_kanto_registry.call(k04_maps,165)
    check(BlueRegionStart.kanto_integrated?, "165-map K04 rejected without JSON")
    write_kanto_registry.call(k04_maps.merge("90"=>k04_maps["91"],"91"=>k04_maps["90"]),165)
    check(!BlueRegionStart.kanto_integrated?, "165-map ready gate accepted swapped Rock Tunnel floors")
    write_kanto_registry.call(k04_maps,160)
    check(!BlueRegionStart.kanto_integrated?, "165-map ready gate accepted stale predecessor count")
    write_kanto_registry.call(k04_maps,165)
    check(BlueRegionStart.kanto_integrated? && BlueRegionStart.hoenn_integrated?, "K04 gate affected Hoenn")
    puts "KANTO_K04_165_READY_GATE_NO_JSON_OK"

    lavender = ((93..98).to_a + (100..106).to_a).each_with_index.to_h { |sid, index| [sid.to_s,609+index] }
    before_lavender = k04_maps.reject { |source,dst| lavender.key?(source) || lavender.value?(dst) }
    (921..998).each do |id|
      break if before_lavender.size==165
      before_lavender[id.to_s]=id
    end
    check(before_lavender.size==165,"bad K05 predecessor fixture")
    k05_maps=before_lavender.merge(lavender)
    k05_maps.values.each { |id| File.write(sprintf("Data/Map%03d.rxdata",id),"kanto") }
    write_kanto_registry.call(k05_maps,178)
    check(BlueRegionStart.kanto_compact_maps(kanto_home)==k05_maps && BlueRegionStart.kanto_integrated?,
          "178-map K05 rejected without JSON")
    write_kanto_registry.call(k05_maps.merge("104"=>620,"105"=>619),178)
    check(!BlueRegionStart.kanto_integrated?,"K05 gate accepted swapped Tower floors")
    write_kanto_registry.call(k05_maps.merge("90"=>608,"91"=>607),178)
    check(!BlueRegionStart.kanto_integrated?,"K05 gate accepted swapped K04 floors")
    write_kanto_registry.call(k05_maps,178)
    File.delete("Data/Map621.rxdata")
    check(!BlueRegionStart.kanto_integrated?,"K05 gate ignored missing summit map")
    File.write("Data/Map621.rxdata","kanto")
    check(BlueRegionStart.kanto_integrated? && BlueRegionStart.hoenn_integrated?,
          "K05 readiness checks affected Hoenn")
    puts "KANTO_K05_178_READY_GATE_NO_JSON_OK"


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
puts "PASS: JoiPlay New Game without JSON, 142 Kanto/199 Hoenn maps, both regions selectable"
