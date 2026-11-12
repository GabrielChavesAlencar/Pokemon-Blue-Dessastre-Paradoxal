# Runs only in the disposable Windows CI installation of the main Blue game.
# No trainer battles are mocked; these checks cover NEW GAME setup and saves.
module KantoIntegratedCheck
  def self.require!(condition, message)
    raise message unless condition
  end

  def self.run
    SaveData.initialize_bootup_values
    spawn = BlueRegionStart.kanto_spawn
    require!(spawn && spawn.length == 3, "Integrated Kanto marker/map missing")
    original = [$data_system.start_map_id, $data_system.start_x, $data_system.start_y]

    BlueRegionStart.define_singleton_method(:choose_initial) { "KANTO" }
    Game.start_new
    require!($game_map.map_id == spawn[0], "Kanto initial map did not load")
    require!([$game_player.x, $game_player.y] == spawn[1,2], "Kanto spawn is wrong")
    require!($PokemonGlobal.blue_regions["initial"] == "KANTO", "Kanto initial region not saved")
    require!($PokemonGlobal.blue_regions["current"] == "KANTO", "Kanto current region not saved")
    require!($PokemonGlobal.blue_story_mode == :story, "Story mode was not selected")
    require!($PokemonGlobal.blue_traditional_starters == true, "Regional starter mode not enabled")
    require!($PokemonGlobal.blue_campaign_departure == false, "Kanto would lose Oak's items on departure")
    require!([$data_system.start_map_id, $data_system.start_x, $data_system.start_y] == original,
             "Native Decades System.rxdata start coordinates were changed")

    slot = "Kanto Integration CI"
    require!(Game.save(slot), "Kanto integrated save failed")
    saved = SaveData.read_from_file(SaveData.get_full_path(slot))

    BlueRegionStart.define_singleton_method(:choose_initial) { "DECADES" }
    Game.start_new
    require!($game_map.map_id == original[0], "Decades no longer starts at its native map")
    require!($PokemonGlobal.blue_regions["initial"] == "DECADES", "Decades initial flag not preserved")
    require!(!$PokemonGlobal.blue_campaign_started, "Decades intro was bypassed")
    require!([$data_system.start_map_id, $data_system.start_x, $data_system.start_y] == original,
             "Native System start was not restored")

    # A saved Kanto game reloads as Kanto, without choosing a region again.
    Game.load(saved)
    require!($game_map.map_id == spawn[0], "Kanto save did not restore its map")
    require!($PokemonGlobal.blue_regions["initial"] == "KANTO", "Kanto save lost its origin")
    require!($PokemonGlobal.blue_regions["current"] == "KANTO", "Kanto current region did not survive save")
    File.write("Data/blue-kanto-integrated-proof.txt",
               "Kanto initial selection, Decades native start, one-save reload verified")
  end
end
