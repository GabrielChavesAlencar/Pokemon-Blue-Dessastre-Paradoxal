# Keep the current region usable even when an older save has no visited-map flags.
# Does not mark destinations visited or grant Fly access to unknown locations.
module BlueRegionMapSafety
  # Bindings store English action IDs; translating an ID before lookup loses it.
  CONTROL_ACTIONS={2=>'Down',4=>'Left',6=>'Right',8=>'Up',11=>'Menu',12=>'Cancel',13=>'Action',
    14=>'Scroll Up',15=>'Scroll Down',16=>'Ready Menu',17=>'AUX1',18=>'AUX2'}.freeze
  def convertButtonToString(button)
    Array(button).map do |code|
      action=CONTROL_ACTIONS[code]
      next 'Ctrl' unless action
      controls=$PokemonSystem.respond_to?(:game_controls) ? $PokemonSystem.game_controls : []
      binding=Array(controls).find { |c| c.control_action==action }
      binding ? makeButtonNameShorter(binding.key_name) : _INTL(action)
    end.join('/')
  end
  def getPlayerPosition
    @playerPos=BlueHabitatMap.position($game_map.map_id) unless @playerPos
    @mapMetadata ||= GameData::MapMetadata.new(id:$game_map.map_id)
    super
  end
  def getAvailableRegions
    result=super
    current=BlueHabitatMap.position($game_map.map_id)
    region=current ? current[0] : @region
    if region && GameData::TownMap.exists?(region) && !@avRegions.any? { |name,id| id==region }
      @avRegions << [GameData::TownMap.get(region).name,region]
    end
    @avRegions
  end
end
