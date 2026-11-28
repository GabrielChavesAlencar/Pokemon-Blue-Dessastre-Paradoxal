# Blue-authored replacement for the Route 2 Pokédex aide.
module BlueKantoPilot
  def self.route2_flash
    return false unless kanto_current? && $game_map && $game_map.map_id == kanto_map_id(21) && $player && $bag
    flags = (progress["pilot_items"] ||= [])
    key = "KANTO_021_FLASH_AIDE"
    # Accept an HM already obtained in an older save, either in Bag or PC.
    ids = [:HM05,:HMFLASH].select { |id| GameData::Item.exists?(id) }
    return false if ids.empty?
    pc = $PokemonGlobal.respond_to?(:pcItemStorage) ? $PokemonGlobal.pcItemStorage : nil
    owned = ids.any? { |id| $bag.has?(id) } ||
      (pc && pc.respond_to?(:items) && pc.items.any? { |item| item.is_a?(Array) && ids.include?(item[0]) && item[1].to_i > 0 })
    if flags.include?(key) || owned
      pbMessage(t("The Boulder Badge lets you use Flash outside battle in Kanto.",
        "A Insígnia da Rocha permite usar Flash fora da batalha em Kanto."))
      return true
    end
    if $player.pokedex.owned_count(0) < 10
      pbMessage(t("Register 10 different Pokémon as caught in the Kanto Pokédex, then come back for Flash.",
        "Registre 10 espécies diferentes como capturadas na Pokédex de Kanto e volte para receber Flash."))
      return false
    end
    return false unless pbReceiveItem(ids.first)
    flags << key
    true
  end
end
