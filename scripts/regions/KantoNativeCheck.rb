# Runs inside the copied mkxp-z game, after the native compiler.
module KantoNativeCheck
  def self.require!(condition, message)
    raise message unless condition
  end

  def self.run
    SaveData.initialize_bootup_values
    Game.start_new
    require!($data_system.start_map_id == $game_map.map_id, "Pallet did not load")
    require!($game_map.events.size >= 4, "Pallet events missing")
    require!(!File.expand_path(SaveData::SAVE_DIR).include?("Pokemon Blue Dessastre Paradoxal"),
             "Pilot pointed at Decades save directory")

    current = $game_map.map_id
    destinations = $game_map.events.values.flat_map do |event|
      event.list.filter_map { |command| command.parameters[1] if command.code == 201 }
    end
    lab = destinations.find { |id| GameData::MapMetadata.get(id).real_name.include?("Oak") }
    require!(lab, "Oak's Lab transfer missing")
    $map_factory.setup(lab)
    $game_player.moveto(6, 12)
    require!($game_map.events.size >= 3, "Lab events missing")

    # Supply the choice and battle results so the compiler can run without a user.
    Object.send(:define_method, :pbMessage) { |*args| args[1].is_a?(Array) ? 0 : nil }
    battle_calls = []
    TrainerBattle.define_singleton_method(:start) do |type, name, version = 0|
      data = GameData::Trainer.get(type, name, version)
      battle_calls << [type, name, version]
      !!data
    end
    BlueKantoPilot.choose_starter
    require!($player.party.first&.species == :BULBASAUR, "Starter was not given")
    BlueKantoPilot.rival
    require!(battle_calls.last == [:BLUE_KANTO_RIVAL, "Blue", 11], "Wrong rival team")
    require!(BlueKantoPilot.rival_done?, "Rival result not recorded")
    connections = MapFactoryHelper.getMapConnections
    first_route = connections.compact.find { |edge| edge[0] == current }&.[](3)
    require!(first_route, "Route 1 connection missing")
    require!(GameData::Encounter.get(first_route).types[:LandDay].any? { |slot| slot[1] == :PIDGEY },
             "Route 1 wild table missing")
    brock = GameData::Trainer.get(:BLUE_KANTO_LEADER, "Brock")
    require!(brock.pokemon.map { |pokemon| pokemon[:species] } == [:GEODUDE, :ONIX], "Brock roster differs")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER, "Brock")
    require!(BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO") == ["BOULDER"],
             "Badge was not awarded exactly once")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER, "Brock")
    require!(battle_calls.count { |row| row[1] == "Brock" } == 1, "Brock battle repeated after victory")

    slot = "Kanto Native Verification"
    require!(Game.save(slot), "Pilot save failed")
    save_file = SaveData.get_full_path(slot)
    saved = SaveData.read_from_file(save_file)
    Game.load(saved)
    require!(BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO") == ["BOULDER"],
             "Pilot badge did not survive reload")
    require!($player.party.first&.species == :BULBASAUR, "Pilot team did not survive reload")
    require!($game_map.map_id == lab, "Pilot did not reload its map")
    File.write("Data/blue-kanto-proof.txt", "Pallet, Oak, rival, Route 1, Brock, save and load verified")
  end
end
