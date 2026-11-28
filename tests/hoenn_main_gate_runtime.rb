# Offline runtime release gate for the legacy and versioned Hoenn catalogs.
require "tmpdir"
require "json"
require "digest"
require "fileutils"

def pbRgssExists?(name); File.file?(name); end
def check(condition,label)
  raise "HOENN_MAIN_GATE: #{label}" unless condition
end
load File.expand_path(ARGV.fetch(0))
catalog = JSON.parse(File.read(File.expand_path("../data/regions/hoenn-map-catalog.json", __dir__)))
check(BlueRegionStart::HOENN_CATALOGS.fetch(1) == catalog.fetch("revisions").fetch("1").map(&:to_s).sort,
      "Ruby legacy keys differ from the versioned project catalog")
module EventHandlers
  def self.add(*); end
end
load File.expand_path("../scripts/regions/HoennPilot.rb", __dir__)

Dir.mktmpdir("hoenn-main-title") do |tmp|
  Dir.chdir(tmp) do
    FileUtils.mkdir_p("Data")
    FileUtils.mkdir_p("PBS")
    FileUtils.mkdir_p("Plugins/ZZZZZ Blue Hoenn Pilot")
    ids = BlueRegionStart::HOENN_LEGACY_SOURCES.each_with_index.to_h { |source, index| [source, 700 + index] }
    start = [ids["8"],25,6,2]
    town = [ids["7"],5,10,2]
    check(!BlueRegionStart.request_initial("HOENN"),
          "Hoenn without files was allowed")
    File.write("Data/blue-hoenn-start.txt",
               "BLUE_HOENN_START_V1,HOENN,#{start[0]},25,6\n")
    File.write("Data/blue-hoenn-ready.txt",
               "BLUE_HOENN_READY_V1,199,#{start[0]},#{town.join(',')}\n")
    check(!BlueRegionStart.request_initial("HOENN"),
          "start and ready markers alone unlocked Hoenn")
    ["Data/MapInfos.rxdata","Data/Tilesets.rxdata",
     "PBS/trainers_hoenn_pilot.txt","PBS/trainer_types_hoenn_pilot.txt",
     "PBS/encounters_hoenn_pilot.txt","PBS/map_metadata_hoenn_pilot.txt",
     "Plugins/ZZZZZ Blue Hoenn Pilot/HoennPilot.rb"].each do |file|
      File.write(file,"synthetic structure")
    end
    ids.values.each do |id|
      File.write(sprintf("Data/Map%03d.rxdata",id),"verified map")
    end
    File.write("Data/blue-hoenn-pilot.txt",
               "BLUE_HOENN_PILOT_V1\n#{start[0]},25,6\n" +
               ids.map { |source, dest| "#{source},#{dest}\n" }.join)
    proof = {"schema"=>1,"region"=>"HOENN","source_commit"=>BlueRegionStart::HOENN_REVISION,
             "status"=>"INTEGRATED_FILES_READY_FOR_NATIVE_QA",
             "maps"=>ids.dup,"start"=>start,"town"=>town}
    File.write("Data/blue-hoenn-install.json",JSON.generate(proof))
    compact = BlueRegionStart.hoenn_compact_manifest
    check(compact && compact["town"] == town && compact["maps"].length == 199,
          "Hoenn without Ruby json gem could not read audited compact marker")
    check(BlueRegionStart.hoenn_integrated?,
          "audited Hoenn files could not enable main title")
    check(BlueRegionStart.request_initial("HOENN"),
          "integrated Hoenn not selectable")
    check(BlueRegionStart.choose_initial=="HOENN",
          "Hoenn start replaced with Decades")
    check(BlueRegionStart.hoenn_spawn==start[0,3],
          "Hoenn start map/position was not selected")
    check(BlueRegionStart.hoenn_town_point==town,
          "Littleroot arrival was replaced by bedroom")
    File.write("Hoenn pilot.json","{}")
    check(!BlueRegionStart.hoenn_integrated?,
          "isolated Hoenn pilot masqueraded as main integration")
    File.delete("Hoenn pilot.json")
    File.write("Data/blue-hoenn-start.txt",
               "BLUE_HOENN_START_V1,HOENN,999,25,6\n")
    check(!BlueRegionStart.request_initial("HOENN"),
          "incorrect start map ID was accepted")
    File.write("Data/blue-hoenn-start.txt",
               "BLUE_HOENN_START_V1,HOENN,#{start[0]},25,6\n")
    proof["status"]="STATIC_QA_ONLY"
    File.write("Data/blue-hoenn-install.json",JSON.generate(proof))
    check(!BlueRegionStart.hoenn_integrated?,
          "raw static-only QA claimed main game readiness")
    proof["status"]="INTEGRATED_FILES_READY_FOR_NATIVE_QA"
    proof["maps"]["8"] = 999
    File.write("Data/blue-hoenn-install.json",JSON.generate(proof))
    check(!BlueRegionStart.hoenn_integrated?,
          "modified mapping unlocked unverified bedroom")

    legacy_mapping = ids.dup
    proof.merge!("schema"=>2, "catalog_revision"=>1, "maps"=>ids.dup, "legacy_maps"=>legacy_mapping)
    write_v2 = proc do |value, compact_map = value["maps"]|
      raw = "BLUE_HOENN_PILOT_V2\n#{start[0]},25,6\n" +
        compact_map.map { |source, dest| "#{source},#{dest}\n" }.join
      File.binwrite(BlueRegionStart::HOENN_PILOT_METADATA, raw)
      actual = value.merge("installed_sha256"=>{BlueRegionStart::HOENN_PILOT_METADATA=>Digest::SHA256.hexdigest(raw)})
      File.write(BlueRegionStart::HOENN_INSTALL, JSON.generate(actual))
      File.write(BlueRegionStart::HOENN_START, "BLUE_HOENN_START_V2,HOENN,#{start[0]},25,6\n")
      File.write(BlueRegionStart::HOENN_READY, "BLUE_HOENN_READY_V2,#{value['maps'].size},#{start[0]},#{town.join(',')}\n")
    end
    write_v2.call(proof)
    check(BlueRegionStart.hoenn_integrated? && BlueRegionStart.hoenn_spawn == start[0,3] &&
          BlueRegionStart.hoenn_town_point == town, "V2 did not preserve V1 start and arrival")
    File.write(BlueRegionStart::HOENN_JOURNAL, "{}")
    check(!BlueRegionStart.hoenn_integrated?, "V2 accepted an interrupted install")
    File.delete(BlueRegionStart::HOENN_JOURNAL)
    check(BlueHoennPilot.metadata == [start[0,3], legacy_mapping.transform_keys(&:to_i)],
          "Hoenn gameplay did not read the V2 map mapping")

    File.open(BlueRegionStart::HOENN_PILOT_METADATA, "ab") { |f| f.write("\n") }
    check(!BlueRegionStart.hoenn_integrated?, "V2 accepted a changed compact file")
    mismatched = legacy_mapping.merge("11"=>legacy_mapping["12"], "12"=>legacy_mapping["11"])
    write_v2.call(proof, mismatched)
    check(!BlueRegionStart.hoenn_integrated?, "V2 accepted compact mapping different from its manifest")
    write_v2.call(proof.merge("maps"=>mismatched))
    check(!BlueRegionStart.hoenn_integrated?, "V2 remapped the older save catalog")
    wrong = legacy_mapping.dup
    wrong["999"] = wrong.delete("11")
    write_v2.call(proof.merge("maps"=>wrong, "legacy_maps"=>wrong))
    check(!BlueRegionStart.hoenn_integrated?, "V2 accepted the right count with unapproved maps")
    write_v2.call(proof.merge("catalog_revision"=>2))
    check(!BlueRegionStart.hoenn_integrated?, "V2 unknown catalog revision unlocked")

    original_catalogs = BlueRegionStart::HOENN_CATALOGS
    BlueRegionStart.send(:remove_const, :HOENN_CATALOGS)
    BlueRegionStart.const_set(:HOENN_CATALOGS, original_catalogs.merge(2=> (legacy_mapping.keys + ["999"]).sort))
    begin
      expanded = legacy_mapping.merge("999"=>950)
      File.write("Data/Map950.rxdata", "synthetic catalog expansion")
      write_v2.call(proof.merge("catalog_revision"=>2, "maps"=>expanded))
      check(BlueRegionStart.hoenn_integrated?, "V2 still hard-coded to 199 despite approved expansion")
      File.delete("Data/Map950.rxdata")
      check(!BlueRegionStart.hoenn_integrated?, "V2 accepted approved but missing expansion map")
    ensure
      BlueRegionStart.send(:remove_const, :HOENN_CATALOGS)
      BlueRegionStart.const_set(:HOENN_CATALOGS, original_catalogs)
    end
  end
end
puts "PASS: Hoenn title gated by installed 199-map manifest; Decades/Kanto unaffected"
