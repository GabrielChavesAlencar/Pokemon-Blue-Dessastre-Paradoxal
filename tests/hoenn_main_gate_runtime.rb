# Offline runtime release gate: only a verified local 199-map Hoenn
# manifest can turn the main Decades title option into shared gameplay.
require "tmpdir"
require "json"
require "fileutils"

def pbRgssExists?(name); File.file?(name); end
def check(condition,label)
  raise "HOENN_MAIN_GATE: #{label}" unless condition
end
load File.expand_path(ARGV.fetch(0))

Dir.mktmpdir("hoenn-main-title") do |tmp|
  Dir.chdir(tmp) do
    FileUtils.mkdir_p("Data")
    FileUtils.mkdir_p("PBS")
    FileUtils.mkdir_p("Plugins/ZZZZZ Blue Hoenn Pilot")
    ids = {}
    199.times { |n| ids[(n+1).to_s] = 700+n }
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
             "maps"=>ids,"start"=>start,"town"=>town}
    File.write("Data/blue-hoenn-install.json",JSON.generate(proof))
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
  end
end
puts "PASS: Hoenn title gated by installed 199-map manifest; Decades/Kanto unaffected"
