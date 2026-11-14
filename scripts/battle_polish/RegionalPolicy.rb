# Regional restrictions for the MAIN campaign. Legacy Decades/arena saves
# keep the native PC, badges and hidden move rules.
module BlueRegionalPolicy
  FIELD_MOVES = {
    :CUT=>"CUT", :FLASH=>"FLASH", :FLY=>"FLY", :STRENGTH=>"STRENGTH",
    :SURF=>"SURF", :ROCKSMASH=>"ROCK_SMASH", :WATERFALL=>"WATERFALL",
    :DIVE=>"DIVE", :ROCKCLIMB=>"ROCK_CLIMB", :DEFOG=>"DEFOG"
  }.freeze

  # HM identity follows the Kanto/FRLG story. Alternate IDs cover
  # Essentials bases that name the item by its move rather than by number.
  KANTO_HM_ITEMS = {
    :CUT=>[:HM01, :HMCUT],
    :FLY=>[:HM02, :HMFLY],
    :SURF=>[:HM03, :HMSURF],
    :STRENGTH=>[:HM04, :HMSTRENGTH],
    :FLASH=>[:HM05, :HMFLASH],
    :ROCKSMASH=>[:HM06, :HMROCKSMASH],
    :WATERFALL=>[:HM07, :HMWATERFALL]
  }.freeze

  def self.state
    # The separately built "Testar Kanto" has no blue-kanto-install.json:
    # its Kanto pilot.json is the installation marker instead. Never allow
    # that missing main-game marker to silently fall back to native HMs.
    pilot = File.file?("Kanto pilot.json")
    installed = defined?(BlueRegionTravel) && BlueRegionTravel.installed?
    return nil unless $PokemonGlobal && (pilot || (installed && BlueRegions.active?))
    stored = $PokemonGlobal.blue_regions
    return nil unless stored.is_a?(Hash) && stored["version"] == 1
    return nil unless BlueRegions.known?(stored["current"])
    return nil if pilot && stored["current"] != "KANTO"
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

  # The regional badge/event is checked FIRST. For the isolated Kanto
  # pilot, the tool is the actual HM item in the Bag, AND an able party
  # member whose species can learn the move. No move slot is required.
  def self.hm_owned?(move)
    ids = KANTO_HM_ITEMS[move.to_s.upcase.to_sym]
    return false unless ids && $bag && defined?(GameData::Item)
    ids.any? { |item| GameData::Item.exists?(item) && $bag.has?(item) }
  end

  def self.eligible_pokemon?(pkmn, move)
    return false unless pkmn && $player && $player.party.any? { |member| member.equal?(pkmn) }
    return false if pkmn.egg? || pkmn.fainted?
    pkmn.respond_to?(:compatible_with_move?) && pkmn.compatible_with_move?(move.to_s.upcase.to_sym)
  end

  def self.compatible_pokemon(move)
    return nil unless $player
    $player.party.find { |pkmn| eligible_pokemon?(pkmn, move) }
  end

  def self.field_result(move, selected = nil)
    current = state
    return :native unless current && current["current"] != "DECADES"
    move_id = move.to_s.upcase.to_sym
    action = FIELD_MOVES[move_id]
    return :native unless action
    # Do not change native/tool behavior of other regional pilots here.
    return BlueRegions.field_access(current, current["current"], action, true) if current["current"] != "KANTO"
    prerequisite = BlueRegions.field_access(current, "KANTO", action, false)
    return prerequisite unless prerequisite == :tool
    return :hm unless hm_owned?(move_id)
    return :pokemon unless selected ? eligible_pokemon?(selected, move_id) : !!compatible_pokemon(move_id)
    :allowed
  end

  def self.field_allowed?(move, showmsg = true, selected = nil)
    outcome = field_result(move, selected)
    return true if outcome == :native || outcome == :allowed
    if showmsg
      region = state["current"]
      label = BlueRegions.info(region)["name"]
      explanation = case outcome
      when :badge then _INTL("A insígnia necessária ainda não foi obtida em {1}.", label)
      when :event then _INTL("Conclua primeiro a missão de campo de {1}.", label)
      when :hm then _INTL("Você precisa obter o HM de {1} e mantê-lo na Bolsa.", move.to_s.upcase)
      when :pokemon then _INTL("Você precisa de um Pokémon da equipe capaz de aprender {1}.", move.to_s.upcase)
      when :tool then _INTL("Falta a ferramenta ou habilidade para usar este movimento.")
      else _INTL("Este movimento de campo não está disponível em {1}.", label)
      end
      pbMessage(explanation)
    end
    false
  end

  # The native Essentials field script still searches for a Pokémon that
  # knows the move. Only while processing an already-authorized Kanto HM
  # interaction, let it find the compatible party member instead.
  def self.kanto_field_context?(move)
    @field_move == move.to_s.upcase.to_sym && field_result(move) == :allowed &&
      state && state["current"] == "KANTO"
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
      return false unless BlueRegionalPolicy.field_allowed?(move, showmsg, pkmn)
      BlueRegionalPolicy.with_field(move) { super }
    end
    def triggerUseMove(move, pkmn)
      return false unless BlueRegionalPolicy.field_allowed?(move, true, pkmn)
      BlueRegionalPolicy.with_field(move) { super }
    end
  end

  module PartyHMSelection
    def get_pokemon_with_move(move)
      if BlueRegionalPolicy.kanto_field_context?(move)
        candidate = BlueRegionalPolicy.compatible_pokemon(move)
        return candidate if candidate
      end
      super
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

  # Direct field-effect entry points must not bypass the permission
  # check (for example a map event calling pbStartSurfing or a boulder event).
  module DirectFieldEffects
    def pbStartSurfing(*args, &block)
      return false unless BlueRegionalPolicy.field_allowed?(:SURF)
      BlueRegionalPolicy.with_field(:SURF) { super }
    end

    def pbPushThisBoulder(*args, &block)
      return false unless BlueRegionalPolicy.field_allowed?(:STRENGTH)
      BlueRegionalPolicy.with_field(:STRENGTH) { super }
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
    Object.prepend(DirectFieldEffects)
    Trainer.prepend(PartyHMSelection)
    Object.prepend(GiftGuard)
    PokemonStorage.prepend(StorageGuard)
    Battle::CatchAndStoreMixin.prepend(CaughtPokemon)
    EventHandlers.add(:on_enter_map, :blue_region_auto_deposit,
                      proc { |*args| BlueRegionalPolicy.auto_deposit })
    @installed = true
  end
end
