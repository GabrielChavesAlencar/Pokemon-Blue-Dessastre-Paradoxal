# CI-only native proof. The original Decades intro waits for input and must
# remain a MANUAL check, not a second headless Game.start_new call.
module KantoIntegratedCheck
  def self.require!(condition, message)
    raise message unless condition
  end

  def self.stage(label)
    File.write("Data/blue-kanto-integrated-stage.txt", label)
  end

  def self.run
    stage("bootup")
    SaveData.initialize_bootup_values
    spawn = BlueRegionStart.kanto_spawn
    require!(spawn && spawn.length == 3, "Integrated Kanto marker/map missing")
    original = [$data_system.start_map_id, $data_system.start_x, $data_system.start_y]

    # Select Kanto without opening a graphical choice menu in headless CI.
    # Real visual choice and Decades introduction remain manual acceptance tests.
    BlueRegionStart.define_singleton_method(:choose_initial) { "KANTO" }
    stage("before_kanto_new_game")
    Game.start_new
    stage("after_kanto_new_game")
    require!($game_map.map_id == spawn[0], "Kanto initial map did not load")
    require!([$game_player.x, $game_player.y] == spawn[1,2], "Kanto spawn is wrong")
    require!($PokemonGlobal.blue_regions["initial"] == "KANTO", "Kanto initial region not saved")
    require!($PokemonGlobal.blue_regions["current"] == "KANTO", "Kanto current region not saved")
    require!($PokemonGlobal.blue_story_mode == :story, "Story mode was not selected")
    require!($PokemonGlobal.blue_traditional_starters == true, "Regional starter mode not enabled")
    require!($PokemonGlobal.blue_campaign_departure == false, "Kanto would lose Oak's items on departure")
    require!([$data_system.start_map_id, $data_system.start_x, $data_system.start_y] == original,
             "Native Decades System.rxdata start coordinates were changed")

    stage("before_travel_validation")
    # This is a discardable CI session. Simulate Kanto's future League here,
    # because only Pallet-Pewter exists today; real gameplay NEVER grants it.
    state = $PokemonGlobal.blue_regions
    state["leagues"] << "KANTO"
    state["decades_return"] = [original[0], original[1], original[2], 2]
    pokemon = Pokemon.new(:BULBASAUR, 5)
    $player.party << pokemon
    original_money = $player.money
    original_bag = Marshal.dump($bag)
    original_pc = Marshal.dump($PokemonStorage)
    original_dex = Marshal.dump($player.pokedex)
    stage("travel_kanto_to_decades")
    require!(BlueRegionTravel.travel("DECADES", true), "Kanto->Decades travel did not complete")
    require!($game_map.map_id == original[0], "Decades return map differs from original")
    require!($PokemonGlobal.blue_regions["current"] == "DECADES", "Travel state was not committed")
    require!($PokemonGlobal.blue_regions["initial"] == "KANTO", "Travel changed the initial region")
    require!($player.party.first.equal?(pokemon), "Travel replaced the party Pokémon")

    # Emulate the already-audited Decades ending only in the throwaway CI
    # session so we can verify a two-way route without playing the full story.
    league = BlueRegionData::REGISTRY["decades"]["league"]
    $player.badges[league["badge"]] = true
    $game_switches[league["switch"]] = true
    stage("travel_decades_to_kanto")
    require!(BlueRegionTravel.travel("KANTO", true), "Decades->Kanto travel did not complete")
    require!($game_map.map_id == spawn[0], "Kanto return map differs from original")
    require!($PokemonGlobal.blue_regions["current"] == "KANTO", "Return state was not committed")
    require!($PokemonGlobal.blue_regions["initial"] == "KANTO", "Return changed the starting region")
    require!($PokemonGlobal.blue_regions["travel_history"].length == 2, "Two-way history missing")
    require!($player.party.first.equal?(pokemon), "Return replaced the Pokémon")
    require!($player.money == original_money, "Travel altered player money")
    require!(Marshal.dump($bag) == original_bag, "Travel altered the bag")
    require!(Marshal.dump($PokemonStorage) == original_pc, "Travel altered the PC")
    require!(Marshal.dump($player.pokedex) == original_dex, "Travel altered Pokédex")

    stage("before_kanto_save")
    slot = "Kanto Integration CI"
    require!(Game.save(slot), "Kanto integrated save failed")
    saved = SaveData.read_from_file(SaveData.get_full_path(slot))
    stage("before_kanto_reload")
    SaveData.mark_values_as_unloaded
    Game.load(saved)
    stage("after_kanto_reload")
    require!($game_map.map_id == spawn[0], "Kanto save did not restore its map")
    require!($PokemonGlobal.blue_regions["initial"] == "KANTO", "Kanto save lost its origin")
    require!($PokemonGlobal.blue_regions["current"] == "KANTO", "Kanto current region did not survive save")
    require!($PokemonGlobal.blue_regions["travel_history"].length == 2, "Travel history lost on save/reload")
    require!($player.party.first.species == :BULBASAUR, "Team changed after save/reload")
    File.write("Data/blue-kanto-integrated-proof.txt",
               "Two-way Kanto/Decades transfer, PC/bag/dex/money, same-save reload OK; simulated League only in CI")
    stage("completed")
  end
end
