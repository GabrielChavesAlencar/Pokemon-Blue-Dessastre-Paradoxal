# Eight real, form-restricted evolutionary methods for the regional Eevee.
# The normal Eevee and its official evolution methods are never modified.
module BlueFutureEevee
  FORM=50
  FORESTS=[82,110,140].freeze
  CAVES=[158,159,162,167,173].freeze
  SUMMITS=[171,173].freeze
  MAGNETIC=[119,129,187].freeze
  TOXIC_WATER=[121].freeze

  def self.regional?(pokemon)
    pokemon && pokemon.species==:EEVEE && pokemon.form_simple==FORM
  end

  def self.map?(ids)
    $game_map && ids.include?($game_map.map_id)
  end

  def self.weather?(kind)
    return false unless $game_screen
    weather=$game_screen.weather_type
    GameData::Weather.exists?(weather) && GameData::Weather.get(weather).category==kind
  end

  def self.knows?(pokemon,move)
    pokemon.moves.any? { |known| known.id==move }
  end

  def self.eligible?(pkmn,minimum)
    regional?(pkmn) && pkmn.level>=minimum
  end

  # Record successful player move attempts on the individual Pokemon, not a
  # global counter, and only if the move is used in a double/triple battle.
  # Evolution verifies that the uses happened at the level immediately before
  # leveling up; uses from previous levels cannot be carried forward.
  module HelpingHand
    def pbUseMove(*args)
      choice=args[0]
      move=choice.is_a?(Array) ? choice[2] : nil
      result=super
      pokemon=@pokemon
      if pokemon && BlueFutureEevee.regional?(pokemon) &&
         move && move.respond_to?(:id) && move.id==:HELPINGHAND &&
         !@lastMoveFailed && @battle && @battle.pbSideSize(0)>1 && !opposes?
        level=pokemon.instance_variable_get(:@blue_future_eevee_helping_level)
        count=(level==pokemon.level) ? pokemon.instance_variable_get(:@blue_future_eevee_helping_uses).to_i : 0
        pokemon.instance_variable_set(:@blue_future_eevee_helping_level,pokemon.level)
        pokemon.instance_variable_set(:@blue_future_eevee_helping_uses,[count+1,3].min)
      end
      result
    end
  end

  METHODS={
    :PoisonBondLevel=>proc { |pkmn,min|
      eligible?(pkmn,min) && pkmn.item==:POISONBARB &&
        pkmn.status==:POISON && map?(TOXIC_WATER)
    },
    :MagneticResonanceLevel=>proc { |pkmn,min|
      eligible?(pkmn,min) && pkmn.item==:METALCOAT && map?(MAGNETIC)
    },
    :SandstormMoveLevel=>proc { |pkmn,min|
      eligible?(pkmn,min) && knows?(pkmn,:MUDSLAP) && weather?(:Sandstorm)
    },
    :DragonDawnBondLevel=>proc { |pkmn,min|
      eligible?(pkmn,min) && pkmn.item==:DRAGONFANG && pkmn.happiness>=160 &&
        PBDayNight.isMorning?
    },
    :NightForestCocoonLevel=>proc { |pkmn,min|
      eligible?(pkmn,min) && pkmn.item==:SILVERPOWDER &&
        PBDayNight.isNight? && map?(FORESTS)
    },
    :CaveCurseStoneLevel=>proc { |pkmn,min|
      eligible?(pkmn,min) && pkmn.item==:HARDSTONE &&
        knows?(pkmn,:CURSE) && map?(CAVES)
    },
    :SummitSkyLevel=>proc { |pkmn,min|
      eligible?(pkmn,min) && pkmn.item==:SKYPLATE &&
        knows?(pkmn,:SWIFT) && map?(SUMMITS)
    },
    :HelpingHandBondLevel=>proc { |pkmn,min|
      eligible?(pkmn,min) && pkmn.happiness>=180 &&
        pkmn.instance_variable_get(:@blue_future_eevee_helping_uses).to_i>=3 &&
        pkmn.instance_variable_get(:@blue_future_eevee_helping_level)==pkmn.level-1
    }
  }.freeze

  def self.register_methods
    METHODS.each do |id,condition|
      next if GameData::Evolution.exists?(id)
      GameData::Evolution.register({
        :id=>id,
        :parameter=>Integer,
        :level_up_proc=>condition,
        :after_evolution_proc=>proc { |pokemon,species,parameter,new_species|
          next false unless species==new_species
          pokemon.instance_variable_set(:@blue_future_eevee_helping_uses,0)
          true
        }
      })
    end
  end

  def self.install
    return if @installed
    register_methods
    Battle::Battler.prepend(HelpingHand) unless Battle::Battler.ancestors.include?(HelpingHand)
    @installed=true
  end
end

BlueFutureEevee.register_methods
