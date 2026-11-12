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
    File.write("Data/blue-kanto-integrated-proof.txt",
               "Kanto initial selection and one-save reload verified; Decades native map unchanged")
    stage("completed")
  end
end
