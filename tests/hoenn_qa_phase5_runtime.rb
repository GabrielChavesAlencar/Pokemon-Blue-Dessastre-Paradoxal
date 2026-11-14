# Hoenn QA 05: integrated regression on top of the Stage10 synthetic Ruby fixture.
# NO donor ROM or Game.exe is loaded in this test.
load File.expand_path("hoenn_stage10_runtime.rb", __dir__)

def q5assert(condition,name)
  raise "[HOENN_QA5] #{name}" unless condition
end

# Fresh synthetic player/save; avoid carrying over Stage10 victory flags.
$PokemonGlobal.blue_regions = {
  "version"=>1,"initial"=>"HOENN","current"=>"HOENN",
  "achievements"=>{"HOENN"=>%w[STONE KNUCKLE DYNAMO HEAT BALANCE FEATHER MIND],
                    "KANTO"=>%w[RAIN]},
  "hoenn_pilot"=>{}
}
$game_map.map_id=866  # source 266 — submerged entrance to Seafloor Cavern.
flags=BlueHoennPilot.state
q5assert(!BlueHoennPilot.seafloor_story_ready?,"unearned Seafloor entrance")
q5assert(!BlueHoennPilot.stage10_transfer(266,227,7,8),
         "entered Seafloor without story milestones")
q5assert($game_map.map_id==866,"blocked entrance changed map")

# Missing any one gate must block entrance without touching unrelated flags.
required = BlueHoennPilot::QA5_SEAFLOOR_STORY_KEYS
q5assert(required==%w[groudon_awakened slateport_submarine_stolen
                       submarine_escaped space_center_saved hm_dive_received],
         "prerequisite ordering missing")
required.each {|key| flags[key]=true}
required.each do |key|
  flags[key]=false
  q5assert(!BlueHoennPilot.seafloor_story_ready?,"missing #{key} accepted")
  q5assert(!BlueHoennPilot.stage10_transfer(266,227,7,8),
           "entered Seafloor without #{key}")
  flags[key]=true
end
q5assert(BlueHoennPilot.seafloor_story_ready?,"full sequence not ready")
q5assert(BlueHoennPilot.stage10_transfer(266,227,7,8),"cannot enter after story")
q5assert($game_map.map_id==827,"wrong first Seafloor room")

# A player with a legacy partial save must always be able to return to sea,
# and a self-contained interior staircase must not become a one-way trap.
flags["space_center_saved"]=false
q5assert(BlueHoennPilot.stage10_transfer(227,228,8,8),
         "internal stairs blocked by save reconciliation")
q5assert($game_map.map_id==828,"wrong internal stairs target")
q5assert(BlueHoennPilot.stage10_transfer(228,227,7,8),
         "internal reverse stairs blocked")
q5assert(BlueHoennPilot.stage10_transfer(227,266,9,9),
         "Seafloor exit blocked for partial save")
q5assert($game_map.map_id==866,"exit changed to wrong submerged map")
flags["space_center_saved"]=true

# Archie must be interacted with IN the inner sanctum; losing does not set
# any boss/legendary flags, and a second win must not grant duplicate credit.
q5assert(!BlueHoennPilot.seafloor_archie,"Archie battle outside sanctum")
$game_map.map_id=836  # donor Map236 remapped in synthetic fixture
TrainerBattle.result=false
q5assert(!BlueHoennPilot.seafloor_archie,"Archie loss counted as win")
q5assert(!flags["seafloor_archie_defeated"],"Archie flag set on defeat")
q5assert(!BlueHoennPilot.seafloor_awakening,"Kyogre awakened before Archie")
TrainerBattle.result=true
q5assert(BlueHoennPilot.seafloor_archie,"Archie victory not registered")
q5assert(flags["seafloor_archie_defeated"],"Archie flag missing")
count=TrainerBattle.calls.count([:BLUE_HOENN_ARCHIE,"Archie",1026])
q5assert(BlueHoennPilot.seafloor_archie,"completed Archie stage not idempotent")
q5assert(TrainerBattle.calls.count([:BLUE_HOENN_ARCHIE,"Archie",1026])==count,
         "Archie battle repeated after victory")
$game_map.map_id=828
q5assert(!BlueHoennPilot.seafloor_awakening,"Kyogre woke in wrong room")
$game_map.map_id=836
q5assert(BlueHoennPilot.seafloor_awakening,"Kyogre scene did not resolve")
q5assert(!BlueHoennPilot.seafloor_awakening,"Kyogre scene repeated")

# Submarine departure is independently gated by BOTH the theft and Matt win.
flags.delete("submarine_escaped")
flags.delete("slateport_submarine_stolen")
flags["aqua_matt_defeated"]=true
q5assert(!BlueHoennPilot.submarine_escape,"submarine escaped before theft")
q5assert(!flags["submarine_escaped"],"submarine flag on blocked escape")
flags["slateport_submarine_stolen"]=true
q5assert(BlueHoennPilot.submarine_escape,"submarine escape after Matt")
q5assert(!BlueHoennPilot.submarine_escape,"submarine repeat scene")

# Persist flags without escalating regional achievements, then switch region.
$PokemonGlobal.blue_regions=Marshal.load(Marshal.dump($PokemonGlobal.blue_regions))
q5assert(BlueHoennPilot.state["kyogre_awakened"],"Kyogre flag lost on reload")
q5assert(BlueHoennPilot.state["seafloor_archie_defeated"],"Archie flag lost on reload")
$PokemonGlobal.blue_regions["current"]="KANTO"
before=Marshal.dump($PokemonGlobal.blue_regions)
q5assert(!BlueHoennPilot.seafloor_story_ready?,"Seafloor accessed in Kanto")
q5assert(!BlueHoennPilot.seafloor_archie,"Archie event leaked to Kanto")
q5assert(!BlueHoennPilot.seafloor_awakening,"Kyogre event leaked to Kanto")
q5assert(!BlueHoennPilot.submarine_escape,"submarine leaked to Kanto")
q5assert(before==Marshal.dump($PokemonGlobal.blue_regions),
         "Kanto state mutated by Hoenn")

puts "HOENN_QA5_STORY_RUNTIME_OK"
