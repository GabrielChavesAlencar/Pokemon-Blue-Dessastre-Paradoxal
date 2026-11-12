# Regional restrictions for the MAIN campaign. Legacy Decades/arena saves
# keep the native PC, badges and hidden move rules.
module BlueRegionalPolicy
  FIELD_MOVES = {
    :CUT=>"CUT", :FLASH=>"FLASH", :FLY=>"FLY", :STRENGTH=>"STRENGTH",
    :SURF=>"SURF", :ROCKSMASH=>"ROCK_SMASH", :WATERFALL=>"WATERFALL",
    :DIVE=>"DIVE", :ROCKCLIMB=>"ROCK_CLIMB", :DEFOG=>"DEFOG"
  }.freeze

  def self.state
    return nil unless defined?(BlueRegionTravel) && BlueRegionTravel.installed?
    return nil unless $PokemonGlobal && BlueRegions.active?
    stored = $PokemonGlobal.blue_regions
    return nil unless stored.is_a?(Hash) && stored["version"] == 1
    return nil unless BlueRegions.known?(stored["current"])
    # A save that stayed in Decades should never be retroactively locked.
    if stored["current"] == "DECADES"
      history = stored["travel_history"]
      return nil unless history.is_a?(Array) && !history.empty?
    end
    BlueRegions.snapshot
  end

  def self.restricted?(pkmn)
    return false unless state
    BlueRegionTravel.restricted?(pkmn)
  end

  def self.field_result(move)
    current = state
    return :native unless current && current["current"] != "DECADES"
    action = FIELD_MOVES[move.to_s.upcase.to_sym]
    return :native unless action
    BlueRegions.field_access(current, current["current"], action, true)
  end

  def self.field_allowed?(move, showmsg = true)
    outcome = field_result(move)
    return true if outcome == :native || outcome == :allowed
    if showmsg
      region = state["current"]
      label = BlueRegions.info(region)["name"]
      explanation = case outcome
      when :badge then _INTL("A insígnia necessária ainda não foi obtida em {1}.", label)
      when :event then _INTL("Conclua primeiro a missão de campo de {1}.", label)
      when :tool then _INTL("Falta a ferramenta ou habilidade para usar este movimento.")
      else _INTL("Este movimento de campo não está disponível em {1}.", label)
      end
      pbMessage(explanation)
    end
    false
  end

  def self.with_field(move)
    old = @field_move
    @field_move = move.to_s.upcase.to_sym
    yield
  ensure
    @field_move = old
  end

  def self.local_field_override?
    return false unless @field_move
    outcome = field_result(@field_move)
    outcome == :allowed
  end

  def self.store_special(pkmn, see_form = true, showmsg = false)
    return false unless $PokemonStorage && $player && !($PokemonStorage.full?)
    # All conditions are checked BEFORE registering ownership or altering PC.
    pkmn.record_first_moves
    box = $PokemonStorage.pbStoreCaught(pkmn)
    return false unless box.is_a?(Integer) && box >= 0
    $player.pokedex.set_seen(pkmn.species)
    $player.pokedex.set_owned(pkmn.species)
    $player.pokedex.register(pkmn) if see_form
    if showmsg
      pbMessage(_INTL("{1} foi enviado ao PC até completar as oito conquistas locais.", pkmn.name))
    end
    true
  end

  def self.auto_deposit
    current = state
    return false unless current && $player && $PokemonStorage
    forbidden = $player.party.select { |pkmn| restricted?(pkmn) }
    return true if forbidden.empty?
    survivors = $player.party.reject { |pkmn| forbidden.any? { |s| s.equal?(pkmn) } }
    return false unless survivors.any? { |pkmn| !pkmn.egg? && !pkmn.fainted? }
    slots = BlueRegionTravel.free_storage_slots(forbidden.length)
    return false unless slots.length == forbidden.length
    original_party = $player.party.dup
    original_slots = slots.map { |box,slot| [box,slot,$PokemonStorage[box,slot]] }
    begin
      forbidden.each_with_index do |pkmn,i|
        box, slot = slots[i]
        raise "Box position occupied" unless $PokemonStorage[box,slot].nil?
        $PokemonStorage[box,slot] = pkmn
        idx = $player.party.index { |item| item.equal?(pkmn) }
        raise "Missing Pokémon in party" unless idx
        $player.party.delete_at(idx)
      end
      true
    rescue StandardError
      original_slots.each { |box,slot,previous| $PokemonStorage[box,slot] = previous }
      $player.party.replace(original_party)
      false
    end
  end

  # v21.1: both party-screen HM commands and map interactions call these.
  module HiddenMoves
    def triggerCanUseMove(move, pkmn, showmsg)
      return false unless BlueRegionalPolicy.field_allowed?(move, showmsg)
      BlueRegionalPolicy.with_field(move) { super }
    end
    def triggerUseMove(move, pkmn)
      return false unless BlueRegionalPolicy.field_allowed?(move)
      BlueRegionalPolicy.with_field(move) { super }
    end
  end

  module BadgeRequirement
    def pbCheckHiddenMoveBadge(badge = -1, showmsg = true)
      return true if BlueRegionalPolicy.local_field_override?
      super
    end
  end

  module FieldInteractions
    [:pbCut, :pbFlash, :pbSurf, :pbFly, :pbStrength, :pbRockSmash,
     :pbWaterfall, :pbDive, :pbRockClimb, :pbDefog].each do |method|
      define_method(method) do |*args, &block|
        move = method.to_s.sub(/^pb/, "").upcase.to_sym
        return false unless BlueRegionalPolicy.field_allowed?(move)
        BlueRegionalPolicy.with_field(move) { super(*args, &block) }
      end
    end
  end

  module StorageGuard
    def pbCopy(boxDst, indexDst, boxSrc, indexSrc)
      return false if boxDst == -1 &&
                      BlueRegionalPolicy.restricted?(self[boxSrc, indexSrc])
      super
    end
    def pbMoveCaughtToParty(pkmn)
      return false if BlueRegionalPolicy.restricted?(pkmn)
      super
    end
    def []=(box, slot, pkmn)
      return false if box == -1 && BlueRegionalPolicy.restricted?(pkmn)
      super
    end
  end

  module GiftGuard
    def pbAddPokemonSilent(pkmn, level = 1, see_form = true)
      return super unless pkmn && BlueRegionalPolicy.state
      pokemon = pkmn.is_a?(Pokemon) ? pkmn : Pokemon.new(pkmn, level)
      return super unless BlueRegionalPolicy.restricted?(pokemon)
      BlueRegionalPolicy.store_special(pokemon, see_form)
    end
    def pbAddPokemon(pkmn, level = 1, see_form = true)
      return super unless pkmn && BlueRegionalPolicy.state
      pokemon = pkmn.is_a?(Pokemon) ? pkmn : Pokemon.new(pkmn, level)
      return super unless BlueRegionalPolicy.restricted?(pokemon)
      BlueRegionalPolicy.store_special(pokemon, see_form, true)
    end
    def pbAddToParty(pkmn, level = 1, see_form = true)
      return super unless pkmn && BlueRegionalPolicy.state
      pokemon = pkmn.is_a?(Pokemon) ? pkmn : Pokemon.new(pkmn, level)
      return super unless BlueRegionalPolicy.restricted?(pokemon)
      BlueRegionalPolicy.store_special(pokemon, see_form, true)
    end
    def pbAddToPartySilent(pkmn, level = nil, see_form = true)
      return super unless pkmn && BlueRegionalPolicy.state
      pokemon = pkmn.is_a?(Pokemon) ? pkmn : Pokemon.new(pkmn, level || 1)
      return super unless BlueRegionalPolicy.restricted?(pokemon)
      BlueRegionalPolicy.store_special(pokemon, see_form)
    end
  end

  module CaughtPokemon
    def pbStorePokemon(pkmn)
      if BlueRegionalPolicy.restricted?(pkmn) && !$PokemonStorage.full?
        pkmn.record_first_moves
        box = $PokemonStorage.pbStoreCaught(pkmn)
        if box && box >= 0
          pbDisplayPaused(_INTL("{1} foi enviado à Box {2}; exige oito conquistas locais.", pkmn.name, box + 1))
          return
        end
      end
      # When every box is full, never silently delete a caught Pokémon.
      # The existing capture flow is retained until the player frees space.
      super
    end
  end

  def self.install
    return if @installed
    HiddenMoveHandlers.singleton_class.prepend(HiddenMoves)
    Object.prepend(BadgeRequirement)
    Object.prepend(FieldInteractions)
    Object.prepend(GiftGuard)
    PokemonStorage.prepend(StorageGuard)
    Battle::CatchAndStoreMixin.prepend(CaughtPokemon)
    EventHandlers.add(:on_enter_map, :blue_region_auto_deposit,
                      proc { |*args| BlueRegionalPolicy.auto_deposit })
    @installed = true
  end
end
