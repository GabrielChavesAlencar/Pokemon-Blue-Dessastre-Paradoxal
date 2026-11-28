# Blue-authored elevator. State is stored in one namespaced save field and only
# accessible while on a configured store floor or within the cabin.
class PokemonGlobalMetadata
  attr_accessor :blue_kanto_celadon_floor
end

module BlueKantoCeladonServices
  FLOORS = (117..121).freeze
  CABIN = 123

  def self.at?(source)
    $game_map && $PokemonGlobal && BlueKantoPilot.kanto_current? &&
      $game_map.map_id == BlueKantoPilot.kanto_map_id(source)
  end

  def self.enter_cabin(source)
    return false unless FLOORS.cover?(source) && at?(source)
    $PokemonGlobal.blue_kanto_celadon_floor = source
    true
  end

  def self.select_floor
    return false unless at?(CABIN)
    options = FLOORS.map { |floor| BlueKantoPilot.t("{1}F","{1}º andar",floor-116) }
    options << BlueKantoPilot.t("Cancel","Cancelar")
    selection = pbMessage(BlueKantoPilot.t("Which floor?","Qual andar?"), options, options.length)
    return false unless selection.is_a?(Integer) && selection.between?(0,FLOORS.size-1)
    $PokemonGlobal.blue_kanto_celadon_floor = FLOORS.begin+selection
    true
  end

  def self.take_exit?(source)
    return false unless FLOORS.cover?(source) && at?(CABIN)
    floor = $PokemonGlobal.blue_kanto_celadon_floor
    return false unless source == (floor.is_a?(Integer) && FLOORS.cover?(floor) ? floor : FLOORS.begin)
    $PokemonGlobal.blue_kanto_celadon_floor = nil
    true
  end
end
