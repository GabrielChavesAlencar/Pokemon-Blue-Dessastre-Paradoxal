require "tmpdir"
require "fileutils"

require_relative "../scripts/regions/SinnohSharedEvents"
require_relative "../scripts/regions/SinnohPilot"

Dir.mktmpdir do |root|
  Dir.chdir(root) do
    FileUtils.mkdir_p("Data")
    File.write(BlueSinnohSharedEvents::RECEIPT, "{}")
    ids = (445..588).to_a
    File.write(BlueSinnohSharedEvents::POINTS, "BLUE_SINNOH_SHARED_V1\n445,1,1\n446,1,1\n446,2,1\n#{ids.join(',')}\n")
    BlueSinnohPilot.define_singleton_method(:all_rival_versions_valid?) { true }
    state = { "version" => 1, "initial" => "KANTO", "current" => "SINNOH" }
    $PokemonGlobal = Struct.new(:blue_regions).new(state)
    $game_map = Struct.new(:map_id).new(446)
    BlueSinnohSharedEvents.enter_map
    raise "Regional visit rejected" unless BlueSinnohPilot.regional_state.equal?(state)
    raise "Shared visit changed the profile" unless BlueSinnohPilot.setup_profile && state["initial"] == "KANTO"
    raise "Missing checkpoint" unless BlueSinnohPilot.commit_flag("mother_intro")
    $game_map.map_id = 300
    raise "Sinnoh runtime leaked outside its maps" if BlueSinnohPilot.regional_state
    $game_map.map_id = 446
    state["current"] = "HOENN"
    raise "Sinnoh runtime leaked outside the active region" if BlueSinnohPilot.regional_state
    state["current"] = "SINNOH"
    raise "Sinnoh checkpoint failed to persist" unless BlueSinnohPilot.progress["mother_intro"]
  end
end
puts "SINNOH_SHARED_VISITOR_SCOPE_OK"
