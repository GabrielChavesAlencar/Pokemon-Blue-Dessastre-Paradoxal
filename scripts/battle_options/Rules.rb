# Own per-battle rules. Never repurpose the original game's numbered switches.
class PokemonSystem
  attr_accessor :blue_battle_mechanics, :blue_sprite_quality
end

module BlueBattleOptions
  MAPS = [22,33,42,43,48].freeze
  LABELS = {'tera'=>'Terastal','dynamax'=>'Dynamax','mega'=>'Mega Evolucao','zmove'=>'Z-Moves'}.freeze
  METHODS = {'mega'=>['MegaEvolve?','MegaEvolution','MegaEvolution?','MegaEvolve'],
             'dynamax'=>['Dynamax?','Dynamax','Dynamax?','Dynamax'],
             'tera'=>['Terastallize?','Terastallize','Terastallize?','Terastallize'],
             'zmove'=>['ZMove?','ZMove','ZMove?','ZMove']}.freeze
  def self.defaults; LABELS.keys.to_h { |key| [key,true] }; end
  def self.battle_area?(map_id=nil)
    MAPS.include?(map_id || ($game_map && $game_map.map_id))
  end
  def self.rules(scope=:mode)
    if scope==:lab
      @lab_rules ||= defaults
    elsif scope==:campaign
      $PokemonGlobal.blue_campaign_mechanics ||= defaults
    elsif $PokemonSystem
      $PokemonSystem.blue_battle_mechanics ||= defaults
    else
      defaults
    end
  end
  def self.snapshot(scope=:mode)
    defaults.merge(rules(scope).select { |k,v| LABELS.key?(k) && [true,false].include?(v) })
  end
  def self.allowed?(battle,key)
    settings=battle.instance_variable_get(:@blue_mechanics)
    !settings || settings[key]!=false
  end
  def self.prepare_lab_party(party,settings)
    party.each do |pkmn|
      pkmn.makeUnmega if settings['mega']==false && pkmn.mega?
    end
  end
  module BattleRules
    def initialize(*args)
      @blue_mechanics=BlueBattleOptions.snapshot if BlueBattleOptions.battle_area?
      super
    end
  end
  METHODS.each do |key,names|
    can,register,registered,activate=names
    BattleRules.define_method('pbCan'+can) do |*args|
      BlueBattleOptions.allowed?(self,key) && super(*args)
    end
    BattleRules.define_method('pbRegister'+register) do |*args|
      return false unless BlueBattleOptions.allowed?(self,key)
      super(*args)
    end
    BattleRules.define_method('pbRegistered'+registered) do |*args|
      BlueBattleOptions.allowed?(self,key) && super(*args)
    end
    BattleRules.define_method('pbToggleRegistered'+register) do |*args|
      return false unless BlueBattleOptions.allowed?(self,key)
      super(*args)
    end
    # Also gate scripted activations, which can skip the eligibility method.
    next if key=='zmove' # Z-Moves are registered moves, not a pbZMove transform.
    BattleRules.define_method('pb'+activate) do |*args|
      return unless BlueBattleOptions.allowed?(self,key)
      super(*args)
    end
  end
  def self.install
    return if @installed
    Battle.prepend(BattleRules)
    Game_Map.prepend(MapEvents)
    DeluxeBitmapWrapper.prepend(BlueSpriteQuality::Wrapper)
    install_menus
    install_mechanic_selector
    @installed=true
  end
end

module Compiler
  class << self
    alias blue_options_original_main main
    def main
      blue_options_original_main
      BlueBattleOptions.install
    end
  end
end
