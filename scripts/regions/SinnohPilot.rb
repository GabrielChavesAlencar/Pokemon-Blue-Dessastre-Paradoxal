# Authored Sinnoh introductory story for a FUTURE isolated test copy only.
# DO NOT load into main Decades, Kanto, Johto or Hoenn.
# No global hooks, map IDs, starter grants without a Poké Ball, or donor scripts.
# RPG Maker events must be compiled after REAL Twinleaf/Verity/Sandgem audits.
module BlueSinnohPilot
  STARTERS = [:TURTWIG, :CHIMCHAR, :PIPLUP].freeze
  RIVAL_CHOICES = {
    :TURTWIG => [:CHIMCHAR, 0],
    :CHIMCHAR => [:PIPLUP, 1],
    :PIPLUP => [:TURTWIG, 2]
  }.freeze
  RIVAL_READY = "Data/blue-sinnoh-rival-ready.txt".freeze
  RIVAL_PROOF = "BLUE_SINNOH_BARRY_V1_READY".freeze


  # Runs from a bedroom autorun after the native map and player exist.
  # The profile flag is separate from the six story checkpoints.
  PROFILE_LOG = "sinnoh-profile-error.txt".freeze

  # This report contains runtime diagnostics, not saves or typed player names.
  def self.profile_error(stage, error)
    if defined?(BlueSinnohExperimental) && File.file?("sinnoh-experimental-qa.json") &&
       File.basename(Dir.pwd) == "game-sinnoh-experimental-" + BlueSinnohExperimental::TOKEN
      File.open(PROFILE_LOG, "wb") do |file|
        file.write("SINNOH_PROFILE_STAGE=#{stage}\n")
        file.write("#{error.class}: #{error.message}\n")
        file.write(Array(error.backtrace).first(15).join("\n"))
      end
    end
  rescue StandardError
    # Do not let diagnostic I/O replace the original runtime failure.
  end

  def self.setup_profile
    stage = "regional_state"
    state = regional_state
    raise "Sinnoh QA: perfil regional ausente" unless state
    return true if state["sinnoh_profile_complete"] == true
    stage = "native_api"
    raise "Sinnoh QA: tela de personagem indisponivel" unless
      defined?($player) && $player && defined?($game_player) && $game_player &&
      defined?(pbChangePlayer) && defined?(pbTrainerName) &&
      defined?(pbEnterPlayerName) && defined?(Settings::MAX_PLAYER_NAME_SIZE)
    stage = "character_metadata"
    if defined?(GameData::PlayerMetadata)
      [9, 10].each do |id|
        raise "Sinnoh QA: cadastro Platinum ausente (#{id})" unless GameData::PlayerMetadata.try_get(id)
      end
    end
    stage = "intro_message"
    pbMessage(_INTL("Rowan: Bem-vindo ao mundo dos Pokemon! Esta e a regiao de Sinnoh."))
    stage = "character_choice"
    choice = pbMessage(_INTL("Qual sera seu personagem?"), ["Lucas", "Dawn"], 0)
    return false unless choice == 0 || choice == 1
    id = choice == 1 ? 10 : 9
    stage = "change_player"
    pbChangePlayer(id)
    raise "Sinnoh QA: cadastro Platinum nao carregado" unless
      $player.respond_to?(:character_ID) && $player.character_ID == id
    # Essentials sets the character ID before opening its native naming UI.
    # Do not force an additional refresh until both ID and outfit are set.
    stage = "name_entry"
    pbMessage(_INTL("Rowan: E como voce se chama?"))
    name = pbEnterPlayerName(_INTL("Seu nome?"), 1, Settings::MAX_PLAYER_NAME_SIZE)
    return false unless name.is_a?(String) && !name.strip.empty?
    stage = "name_commit"
    pbTrainerName(name)
    raise "Sinnoh QA: nome do jogador nao foi aplicado" unless
      $player.respond_to?(:name) && $player.name == name
    stage = "sprite_refresh"
    $game_player.refresh_charset if $game_player.respond_to?(:refresh_charset)
    $game_player.transparent = false if $game_player.respond_to?(:transparent=)
    stage = "final_message"
    pbMessage(_INTL("Rowan: {1}, sua aventura esta prestes a comecar!", $player.name))
    state["sinnoh_profile_complete"] = true
    true
  rescue StandardError => error
    profile_error(stage, error)
    begin
      pbMessage("Sinnoh QA: falha na etapa #{stage} (#{error.class}). Tente novamente ao sair do quarto. Diagnostico: sinnoh-profile-error.txt.")
    rescue StandardError
      # Preserve control of the map even when the message API is unavailable.
    end
    false
  end

  def self.lake_entry_allowed?
    flags = progress
    return false unless flags
    unless flags["mother_intro"] == true
      pbMessage(_INTL("Antes de ir ao lago, fale com sua mãe em Twinleaf Town."))
      return false
    end
    unless flags["barry_intro"] == true
      pbMessage(_INTL("Barry ainda está em casa. Encontre-o antes de ir ao lago."))
      return false
    end
    true
  end

  def self.choose_starter_scene(species)
    flags = progress
    return false unless flags
    if flags["starter_received"]
      hide_starter_balls
      return false
    end
    return choose_starter_from_ball(species) unless flags["rowan_briefcase_seen"]
    name = defined?(GameData::Species) ? GameData::Species.get(species).name : species.to_s
    return false unless pbConfirmMessage(_INTL("Deseja escolher {1} como seu parceiro?",name))
    return false unless choose_starter_from_ball(species)
    hide_starter_balls
    # The existing guarded native battle cannot mark success unless all
    # three compiled Barry teams are valid. The action NPC remains available.
    barry_rival
    true
  end

  # All state lives ONLY in the active Sinnoh region-scoped save record.
  # Never initialize/replace the BlueRegions global state for other regions.
  def self.regional_state
    return nil unless defined?($PokemonGlobal) && $PokemonGlobal
    return nil unless $PokemonGlobal.respond_to?(:blue_regions)
    record = $PokemonGlobal.blue_regions
    return nil unless record.is_a?(Hash) &&
                      record["version"] == 1 &&
                      record["current"] == "SINNOH"
    # CH07: private Sinnoh QA saves must not borrow another region's initial.
    return nil if record.key?("initial") && record["initial"] != "SINNOH"
    record
  end

  # Checkpoint reads must not create or repair flags, especially after a
  # failed event or when a loaded save is incomplete or forged.
  def self.valid_flags?(flags)
    return false unless flags.is_a?(Hash)
    checkpoints = %w[mother_intro barry_intro rowan_briefcase_seen
                     starter_received rival_fought pokedex_received]
    # Refuse arbitrary saved flags: only these six checkpoints plus the
    # paired physical starter species belong to this isolated story.
    return false unless flags.keys.all? { |key|
      key.is_a?(String) && (checkpoints.include?(key) || key == "starter")
    }
    checkpoints.each do |key|
      return false if flags.key?(key) && flags[key] != true && flags[key] != false
    end
    return false if flags["barry_intro"] == true && flags["mother_intro"] != true
    return false if flags["rowan_briefcase_seen"] == true && flags["barry_intro"] != true
    raw = flags["starter"]
    chosen = raw.is_a?(String) && STARTERS.map(&:to_s).include?(raw)
    granted = flags["starter_received"] == true
    return false if granted != !!chosen
    return false if granted && flags["rowan_briefcase_seen"] != true
    return false if flags.key?("starter") && !granted
    return false if flags["rival_fought"] == true && !granted
    return false if flags["pokedex_received"] == true && flags["rival_fought"] != true
    true
  end

  def self.progress
    state = regional_state
    return nil unless state
    existing = state["sinnoh_pilot"]
    return {} if existing.nil?
    valid_flags?(existing) ? existing : nil
  end

  # Only a completed action may create/update the isolated progress record.
  def self.commit_flag(key)
    state = regional_state
    flags = progress
    return false unless state && flags && key.is_a?(String)
    # Exactly one transition per verified event, never arbitrary direct writes.
    previous = {
      "mother_intro" => nil,
      "barry_intro" => "mother_intro",
      "rowan_briefcase_seen" => "barry_intro",
      "rival_fought" => "starter_received",
      "pokedex_received" => "rival_fought"
    }
    return false unless previous.key?(key) && flags[key] != true
    required = previous[key]
    return false if required && flags[required] != true
    return false if key == "rival_fought" && !@rival_battle_in_progress
    return false if key == "pokedex_received" && !@pokedex_grant_in_progress
    return false unless valid_flags?(flags.merge(key => true))
    state["sinnoh_pilot"] ||= {}
    state["sinnoh_pilot"][key] = true
    true
  end

  def self.starter
    flags = progress
    return nil unless flags
    current = flags["starter"]
    selected = current.is_a?(String) ? current.to_sym : nil
    STARTERS.include?(selected) ? selected : nil
  end

  def self.starter_name
    selected = starter
    return nil unless selected
    if defined?(GameData::Species)
      return GameData::Species.get(selected).name
    end
    selected.to_s.capitalize
  end

  def self.mother
    flags = progress
    return false unless flags
    if flags["mother_intro"]
      pbMessage(_INTL("Mãe: Boa viagem! Volte quando quiser descansar."))
      return false
    end
    pbMessage(_INTL("Mãe: Barry veio procurar você. Ele falou sobre uma pesquisa perto do lago."))
    commit_flag("mother_intro")
  end

  def self.barry_intro
    flags = progress
    return false unless flags
    unless flags["mother_intro"]
      pbMessage(_INTL("Barry: Sua mãe está esperando você em casa."))
      return false
    end
    if flags["barry_intro"]
      pbMessage(_INTL("Barry: Vamos descobrir o que o professor está investigando!"))
      return false
    end
    pbMessage(_INTL("Barry: Dizem que um pesquisador esteve perto do Lago Verity. Vamos conferir!"))
    commit_flag("barry_intro")
  end

  # In this Blue-authored pilot, Rowan authorizes the player to choose a
  # research partner from THREE physical ball events after Barry's introduction.
  def self.rowan_briefcase
    flags = progress
    return false unless flags
    unless flags["barry_intro"]
      pbMessage(_INTL("Rowan: Quero conversar com você e Barry juntos."))
      return false
    end
    if flags["rowan_briefcase_seen"]
      pbMessage(_INTL("Rowan: A maleta está aberta. Examine uma das três Poké Bolas."))
      return false
    end
    pbMessage(_INTL("Rowan: Preciso de ajuda para observar os Pokémon desta região."))
    pbMessage(_INTL("Rowan: Escolha um parceiro da maleta. Os três precisam de bons treinadores."))
    commit_flag("rowan_briefcase_seen")
  end

  # J05: grant EXACTLY one physical-ball starter in the isolated Sinnoh save.
  # Native pbAddPokemonSilent is not a transaction API. Therefore we require
  # an available party slot (no untracked PC storage writes), validate that
  # exactly one expected Pokemon was added, then atomically replace the
  # existing regional flag Hash. On a failed grant, compensate only the
  # identified appended party member, never modify foreign-region flags.
  def self.choose_starter_from_ball(species)
    flags = progress
    return false unless flags
    requested = species.is_a?(Symbol) ? species :
                (species.is_a?(String) && STARTERS.map(&:to_s).include?(species) ?
                 species.to_sym : nil)
    return false unless STARTERS.include?(requested)
    if flags["starter_received"] || flags.key?("starter")
      pbMessage(_INTL("Rowan: Você já escolheu um parceiro desta maleta."))
      return false
    end
    unless flags["rowan_briefcase_seen"]
      pbMessage(_INTL("Rowan: Aguarde minha explicação antes de escolher."))
      return false
    end
    return false unless defined?(pbAddPokemonSilent)
    return false if @starter_grant_in_progress
    scope = regional_state
    return false unless scope && scope["sinnoh_pilot"].equal?(flags) && !flags.frozen?
    return false unless defined?($player) && $player && $player.respond_to?(:party)
    player = $player
    party = player.party
    # A full party would send the starter to storage, where a failed grant
    # could not be rolled back without touching unrelated boxes/saves.
    return false unless party.is_a?(Array) && !party.frozen? && party.length < 6
    before = party.dup
    committed = false
    @starter_grant_in_progress = true
    begin
      accepted = pbAddPokemonSilent(requested, 5)
      added = party.length == before.length + 1 &&
              before.each_with_index.all? { |mon, i| party[i].equal?(mon) }
      return false unless accepted && added
      actual = party[-1]
      given_species = actual.is_a?(Array) ? actual[0] :
                      (actual.respond_to?(:species) ? actual.species : nil)
      given_level = actual.is_a?(Array) ? actual[1] :
                    (actual.respond_to?(:level) ? actual.level : nil)
      return false unless given_species.to_s == requested.to_s && given_level == 5
      return false unless $player.equal?(player) && regional_state.equal?(scope)
      return false unless scope["sinnoh_pilot"].equal?(flags) &&
                          valid_flags?(flags) &&
                          flags["rowan_briefcase_seen"] == true &&
                          !flags["starter_received"] && !flags.key?("starter")
      candidate = flags.merge("starter" => requested.to_s, "starter_received" => true)
      return false unless valid_flags?(candidate)
      flags.replace(candidate)
      committed = true
      pbMessage(_INTL("Rowan: Ótima escolha! Observe seu parceiro durante a viagem."))
      true
    rescue StandardError
      # A failed message display after the flag commit is not a new grant.
      committed
    ensure
      unless committed
        # Remove only our newly appended Pokemon, never rewrite a save or
        # remove party members if the engine reordered the team.
        if party.length == before.length + 1 &&
           before.each_with_index.all? { |mon, i| party[i].equal?(mon) }
          party.pop
        end
      end
      @starter_grant_in_progress = false
    end
  end

  # The professor never exposes a choice dialog or grants Pokémon.
  def self.choose_starter
    flags = progress
    return false unless flags
    pbMessage(_INTL("Rowan: Toque na Poké Bola do Pokémon que deseja acompanhar."))
    false
  end

  def self.rival_species
    selected = starter
    selected ? RIVAL_CHOICES.fetch(selected)[0] : nil
  end

  def self.rival_version
    selected = starter
    selected ? RIVAL_CHOICES.fetch(selected)[1] : nil
  end

  def self.rival_fought?
    flags = progress
    flags && flags["rival_fought"] == true
  end

  # CH08: a marker is not a compiled PBS team. A missing or mismatched
  # GameData trainer must never call TrainerBattle.start or advance the save.
  # Check only the selected version (0/1/2) in this isolated pilot.
  def self.compiled_rival_valid?
    version = rival_version
    expected = rival_species
    return false unless version.is_a?(Integer) && (0..2).cover?(version) && expected
    return false unless defined?(GameData::Trainer) &&
                        GameData::Trainer.respond_to?(:get)
    trainer = GameData::Trainer.get(:BLUE_SINNOH_RIVAL, "Barry", version)
    return false unless trainer && trainer.respond_to?(:pokemon)
    team = trainer.pokemon
    return false unless team.is_a?(Array) && team.length == 1
    pokemon = team.first
    species = pokemon.is_a?(Hash) ? (pokemon[:species] || pokemon["species"]) :
              (pokemon.respond_to?(:species) ? pokemon.species : nil)
    level = pokemon.is_a?(Hash) ? (pokemon[:level] || pokemon["level"]) :
            (pokemon.respond_to?(:level) ? pokemon.level : nil)
    species.to_s == expected.to_s && level.is_a?(Integer) && level == 5
  rescue StandardError
    false
  end

  # J05 release gate: ALL three compiled Barry seed teams must match the
  # authored starter-counter mapping. A single present trainer is not proof
  # that the other two starters can complete the tutorial.
  def self.all_rival_versions_valid?
    return false unless defined?(GameData::Trainer) &&
                        GameData::Trainer.respond_to?(:get)
    RIVAL_CHOICES.each_value do |expected, version|
      trainer = GameData::Trainer.get(:BLUE_SINNOH_RIVAL, "Barry", version)
      return false unless trainer && trainer.respond_to?(:pokemon)
      team = trainer.pokemon
      return false unless team.is_a?(Array) && team.length == 1
      pokemon = team.first
      species = pokemon.is_a?(Hash) ? (pokemon[:species] || pokemon["species"]) :
                (pokemon.respond_to?(:species) ? pokemon.species : nil)
      level = pokemon.is_a?(Hash) ? (pokemon[:level] || pokemon["level"]) :
              (pokemon.respond_to?(:level) ? pokemon.level : nil)
      return false unless species.to_s == expected.to_s && level.is_a?(Integer) && level == 5
    end
    true
  rescue StandardError
    false
  end

  def self.barry_rival
    flags = progress
    return false unless flags
    unless starter
      pbMessage(_INTL("Barry: Primeiro escolha seu parceiro na maleta!"))
      return false
    end
    if rival_fought?
      pbMessage(_INTL("Barry: Ainda vamos ter muitas batalhas pela frente!"))
      return false
    end
    # Until all three versions exist and are checked by the isolated build,
    # DO NOT attempt to start an arbitrary PBS trainer from the main game.
    ready_for_release = File.file?(RIVAL_READY) && !File.symlink?(RIVAL_READY) &&
                        File.read(RIVAL_READY).strip == RIVAL_PROOF
    # The private QA may TEST the battle before final gameplay acceptance.
    # Its native map/PBS probe + per-copy hash proof is mandatory, and this
    # does not create the release marker or change behavior in the main game.
    qa_test_only = defined?(BlueSinnohQAStart) &&
                   BlueSinnohQAStart.respond_to?(:barry_test_authorized?) &&
                   BlueSinnohQAStart.barry_test_authorized?
    # J12-E: the exploratory QA may WALK without compiled Barry, but never
    # battle without its real 3-team GameData compilation and private proof.
    # This only affects the J12-E experimental copy, not shared campaign QA.
    experimental_test = defined?(BlueSinnohExperimental) &&
                        defined?(BlueKantoTitle) &&
                        BlueKantoTitle.respond_to?(:sinnoh_experimental_maps_ready?) &&
                        BlueKantoTitle.sinnoh_experimental_maps_ready? &&
                        BlueKantoTitle.sinnoh_experimental_barry_compiled?
    if defined?(BlueSinnohExperimental)
      # The J12-E sandbox must NEVER inherit an older release/QA marker
      # for Barry from a copied game. Only this copy's compilation proof counts.
      ready_for_release = false
      qa_test_only = false
    end
    unless (ready_for_release || qa_test_only || experimental_test) && compiled_rival_valid? &&
           all_rival_versions_valid? && defined?(TrainerBattle) && TrainerBattle.respond_to?(:start)
      pbMessage(_INTL("Barry: Nossa primeira batalha estará disponível no piloto de Sinnoh."))
      return false
    end
    return false if @rival_battle_in_progress
    @rival_battle_in_progress = true
    scope = regional_state
    chosen = starter
    begin
      pbMessage(_INTL("Barry: Vamos descobrir como nossos parceiros se saem!"))
      setBattleRule("canLose")
      result = TrainerBattle.start(:BLUE_SINNOH_RIVAL, "Barry", rival_version)
      # false means a completed canLose defeat, nil means no confirmed battle.
      return false unless result == true || result == false
      return false unless scope && regional_state.equal?(scope) && starter == chosen
      $player.heal_party if defined?($player) && $player && $player.respond_to?(:heal_party)
      return false unless commit_flag("rival_fought")
      pbMessage(result ?
        _INTL("Barry: Você venceu! Vou melhorar minha estratégia.") :
        _INTL("Barry: Que batalha! Vamos continuar treinando."))
      true
    rescue StandardError
      # An engine/compiled trainer exception is NOT a completed battle.
      pbMessage(_INTL("Barry: Nossa batalha não pôde ser validada."))
      false
    ensure
      @rival_battle_in_progress = false
    end
  end

  def self.rowan_pokedex
    flags = progress
    return false unless flags
    unless flags["rival_fought"] == true && starter
      pbMessage(_INTL("Rowan: Primeiro conheça seu parceiro e complete o treino com Barry."))
      return false
    end
    if flags["pokedex_received"]
      pbMessage(_INTL("Rowan: Registre suas descobertas na Pokédex."))
      return false
    end
    # Only mark dex as delivered after the engine's actual player field exists.
    return false unless defined?($player) && $player &&
                        $player.respond_to?(:has_pokedex=)
    return false if @pokedex_grant_in_progress
    @pokedex_grant_in_progress = true
    begin
      # The existing region scoped save is the ONLY story record. Do not
      # persist dex_received if the native player setter fails or reads false.
      return false unless $player.respond_to?(:has_pokedex)
      scope = regional_state
      original = $player.has_pokedex
      saved_flags = flags.dup
      return false unless scope && scope["sinnoh_pilot"].equal?(flags)
      return false unless commit_flag("pokedex_received")
      begin
        $player.has_pokedex = true
        raise "Pokedex field was not set" unless $player.has_pokedex == true
      rescue StandardError
        # Revert only this event and only if the Sinnoh save identity remains.
        if regional_state.equal?(scope) && scope["sinnoh_pilot"].equal?(flags) &&
           !flags.frozen?
          flags.replace(saved_flags)
        end
        begin
          $player.has_pokedex = original
        rescue StandardError
          # Cannot repair an incompatible native setter; no false save proof.
        end
        return false
      end
      pbMessage(_INTL("Rowan: Sua Pokédex está pronta. Explore Sinnoh com cuidado."))
      true
    ensure
      @pokedex_grant_in_progress = false
    end
  end
  # Private pilot only. Self-switch B is persisted by Essentials, including
  # after leaving the lake and reopening a saved game.
  def self.hide_starter_balls
    flags = progress
    return false unless flags && flags["starter_received"] == true
    return false unless defined?($game_map) && $game_map && $game_map.respond_to?(:events) &&
      defined?($game_self_switches) && $game_self_switches
    $game_map.events.each do |id,event|
      next unless event.respond_to?(:name) && %w[SN_BALL_TURTWIG SN_BALL_CHIMCHAR SN_BALL_PIPLUP].include?(event.name)
      $game_self_switches[[$game_map.map_id,id,"B"]] = true
      event.refresh if event.respond_to?(:refresh)
      # Old saves can still hold pre-update event pages in their map factory.
      event.erase if event.respond_to?(:erase)
    end
    true
  end

  def self.route202_allowed?
    flags = progress
    state = regional_state
    !!(flags && state && flags["pokedex_received"] == true &&
       state["sinnoh_lab_supplies"] == true && $player &&
       $player.respond_to?(:has_pokedex) && $player.has_pokedex == true)
  end

  # Keep the existing dex transition contract intact. Supplies are tracked
  # separately for compatibility with older saves that already have the dex.
  def self.lab_reward
    flags = progress
    state = regional_state
    return false unless flags && state
    unless flags["rival_fought"] == true && starter
      pbMessage(_INTL("Rowan: Primeiro conheca seu parceiro e complete o treino com Barry."))
      return false
    end
    if route202_allowed?
      pbMessage(_INTL("Rowan: Registre suas descobertas na Pokedex. Boa viagem!"))
      return true
    end
    return false if @lab_reward_in_progress
    return false unless $player && $player.respond_to?(:has_pokedex) && $player.respond_to?(:has_pokedex=)
    return false unless defined?($bag) && $bag && $bag.respond_to?(:quantity) &&
      $bag.respond_to?(:add) && $bag.respond_to?(:remove) && $bag.respond_to?(:can_add?)
    before = $bag.quantity(:POKEBALL)
    original_dex = $player.has_pokedex
    saved_flags = flags.dup
    @lab_reward_in_progress = true
    committed = false
    begin
      unless state["sinnoh_lab_supplies"] == true
        unless $bag.can_add?(:POKEBALL,5)
          pbMessage(_INTL("Rowan: Libere espaco na mochila para cinco Poke Bolas."))
          return false
        end
        return false unless $bag.add(:POKEBALL,5) && $bag.quantity(:POKEBALL)==before+5
      end
      return false unless (flags["pokedex_received"] == true && $player.has_pokedex == true) || rowan_pokedex
      return false unless regional_state.equal?(state) && $player.has_pokedex == true &&
        progress && progress["pokedex_received"] == true
      state["sinnoh_lab_supplies"] = true
      committed = true
      pbMessage(_INTL("Rowan: Aqui estao cinco Poke Bolas! Agora voce pode seguir pela Rota 202."))
      true
    rescue StandardError
      committed
    ensure
      unless committed
        delta = $bag.quantity(:POKEBALL)-before
        $bag.remove(:POKEBALL,delta) if delta>0 && delta<=5
        if regional_state.equal?(state) && state["sinnoh_pilot"].equal?(flags) && !flags.frozen?
          flags.replace(saved_flags)
          $player.has_pokedex = original_dex
        end
      end
      @lab_reward_in_progress = false
    end
  end

end
