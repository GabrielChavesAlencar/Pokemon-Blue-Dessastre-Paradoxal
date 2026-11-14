# Local Kanto pilot events. Loaded only by the separately prepared test game.
module BlueKantoPilot
  STARTERS = [:BULBASAUR, :CHARMANDER, :SQUIRTLE].freeze
  RIVAL_VERSIONS = {BULBASAUR: 11, CHARMANDER: 12, SQUIRTLE: 13}.freeze
  VIRIDIAN_MART_STOCK = [:POKEBALL, :POTION, :ANTIDOTE, :PARALYZEHEAL].freeze
  VIRIDIAN_REQUIRED_BADGES = %w[BOULDER CASCADE THUNDER RAINBOW SOUL MARSH VOLCANO].freeze
  LEAGUE_REQUIRED_BADGES = (VIRIDIAN_REQUIRED_BADGES + ["EARTH"]).freeze
  LEAGUE_ORDER = %w[LORELEI BRUNO AGATHA LANCE CHAMPION].freeze
  LEAGUE_CHAMPION_VERSIONS = {BULBASAUR: 1, CHARMANDER: 2, SQUIRTLE: 3}.freeze
  FULL_POWER_OFFSET = 100
  GYM_FULL_POWER = {
    "Brock" => :BLUE_KANTO_LEADER, "Misty" => :BLUE_KANTO_LEADER_MISTY,
    "Lt. Surge" => :BLUE_KANTO_LEADER_SURGE, "Erika" => :BLUE_KANTO_LEADER_ERIKA,
    "Koga" => :BLUE_KANTO_LEADER_KOGA, "Sabrina" => :BLUE_KANTO_LEADER_SABRINA,
    "Blaine" => :BLUE_KANTO_LEADER_BLAINE, "Giovanni" => :BLUE_KANTO_LEADER_GIOVANNI
  }.freeze

  # Passive FRLG dialogue is stored as original text in the isolated pilot.
  # RPG Maker 101/401 rendering does not reliably traverse _INTL, so resolve
  # the selected Blue language explicitly at the moment the NPC is spoken to.
  NPC_DIALOGUE_FILE = "Data/blue-kanto-npc-dialogues.dat".freeze

  def self.npc_dialogue(source_map, source_event, index)
    @npc_dialogues ||= begin
      raise "Kanto NPC dialogue table not installed" unless File.file?(NPC_DIALOGUE_FILE)
      load_data(NPC_DIALOGUE_FILE).each_with_object({}) do |entry, rows|
        original_map, original_event, lines = entry
        rows[[original_map, original_event]] = lines
      end
    end
    lines = @npc_dialogues[[source_map, source_event]]
    message = lines && lines[index]
    raise "Missing Kanto NPC dialogue #{source_map}/#{source_event}/#{index}" unless message.is_a?(String)
    translated = defined?(BlueLocale) ? BlueLocale.translate(message) : message
    pbMessage(translated)
  end

  def self.t(english, portuguese, *args)
    value = defined?(BlueLocale) && BlueLocale.enabled? ? portuguese : english
    # These paired lines already have their locale selected. The general
    # catalogue must not replace an authored line or any dynamic value.
    return _INTL(value, *args) unless defined?(BlueLocale)
    BlueLocale.with_raw { _INTL(value, *args) }
  end

  def self.progress
    $PokemonGlobal.blue_regions ||= BlueRegions.new_state("KANTO")
  end

  def self.choose_profile
    return unless progress["pilot_profile_pending"]
    pbCharacterSelect
    $game_player.transparent = false
    $game_player.refresh_charset
    progress.delete("pilot_profile_pending")
  end

  def self.met_mom?
    progress["pilot_met_mom"] || starter
  end

  def self.meet_mom
    pbMessage(BlueKantoPilot.t("Mom: {1}, Professor Oak was looking for you. Stop by the lab before leaving Pallet.", "Mãe: {1}, o professor Oak estava procurando por você. Passe no laboratório antes de sair de Pallet.", $player.name))
    progress["pilot_met_mom"] = true
  end

  def self.oak_warning
    pbMessage(BlueKantoPilot.t("Oak: Hey! Wait a second!", "Oak: Ei! Espere um pouco!"))
  end

  def self.show_approaching_oak(visible)
    key = [$game_map.map_id, 12, "A"]
    $game_self_switches[key] = visible
    $game_map.events[12].refresh
  end

  def self.oak_invitation
    pbMessage(BlueKantoPilot.t("Oak: It's dangerous to enter tall grass without a Pokémon. Come with me to the lab!", "Oak: É perigoso entrar na grama alta sem um Pokémon. Venha comigo ao laboratório!"))
  end

  def self.starter
    progress["pilot_starter"]&.to_sym
  end

  def self.choose_starter
    if starter
      if progress["pilot_oak_parcel_received"] && !progress["pilot_oak_parcel_delivered"]
        # The parcel is a Kanto-only quest flag, never a foreign Decades item.
        # Award the five Poké Balls atomically before committing the delivery,
        # so full-bag retries cannot duplicate the Pokédex or the reward.
        BlueMusic.with_kanto_scene("oak_talk") do
          pbMessage(BlueKantoPilot.t("Oak: You brought my package from Viridian! Thank you!", "Oak: Você trouxe meu pacote de Viridian! Muito obrigado!"))
          if $bag.add(:POKEBALL, 5)
            $player.has_pokedex = true if $player.respond_to?(:has_pokedex=)
            progress["pilot_oak_parcel_delivered"] = true
            BlueMusic.kanto_me_play("obtained_item")
            pbMessage(BlueKantoPilot.t("Oak: Here's your Pokédex and five Poké Balls. Now you can explore Viridian Forest!", "Oak: Aqui estão sua Pokédex e 5 Poké Bolas. Agora você pode explorar a Viridian Forest!"))
          else
            pbMessage(BlueKantoPilot.t("Oak: Make room in your Bag for the five Poké Balls. I'll keep the package until you return.", "Oak: Abra espaço na Bolsa para receber as 5 Poké Bolas. O pacote fica comigo até você voltar."))
          end
        end
      else
        pbMessage(BlueKantoPilot.t("Oak: Take good care of your {1}.", "Oak: Cuide bem do seu {1}.", GameData::Species.get(starter).name))
      end
      return
    end
    pbMessage(BlueKantoPilot.t("Oak: Choose one of the three Poké Balls on the table.", "Oak: Escolha uma das três Poké Bolas sobre a mesa."))
  end

  def self.choose_starter_ball(species)
    return if starter || !STARTERS.include?(species)
    name = GameData::Species.get(species).name
    return unless pbConfirmMessage(BlueKantoPilot.t("Choose {1} as your partner?", "Escolher {1} como seu parceiro?", name))
    return unless pbAddPokemonSilent(species, 5)
    progress["pilot_starter"] = species.to_s
    [18, 19, 20].each do |id|
      $game_self_switches[[$game_map.map_id, id, "A"]] = true
      $game_map.events[id]&.refresh
    end
    BlueMusic.kanto_me_play("obtained_pokemon")
    $bag.add(:POTION, 2)
    pbSetPokemonCenter
    pbMessage(BlueKantoPilot.t("Oak: {1} chose you! Visit Viridian and return to the lab when you find my package.", "Oak: {1} escolheu você! Visite Viridian e volte ao laboratório quando encontrar meu pacote.", name))
  end

  # A safe, local story step for the first Pallet -> Viridian -> Pallet
  # loop. The source item need not exist in Decades; state is saved only in
  # the active Kanto campaign. Existing Boulder+ saves skip the new quest.
  def self.parcel_pickup_pending?
    starter && !progress["pilot_oak_parcel_received"] &&
      !progress["pilot_oak_parcel_delivered"] &&
      !BlueRegions.local_achievements(progress, "KANTO").include?("BOULDER")
  end

  def self.prepare_viridian_mart_visit(mart_map_id, intro_event_id)
    return unless parcel_pickup_pending?
    # Old saves may have an A self-switch even though the automatic scene
    # was never actually completed. Reset only this Kanto Mart scene.
    key = [mart_map_id, intro_event_id, "A"]
    $game_self_switches[key] = false if $game_self_switches[key]
  end

  # The entrance autorun calls this and then waits (event command 210)
  # before the clerk hands out Oak's Parcel. Navigate around real shelves
  # and events, never through walls, and stop beside the actual shopkeeper.
  def self.walk_to_viridian_clerk(clerk_event_id)
    clerk = $game_map.events[clerk_event_id]
    return false unless clerk && $game_player
    start = [$game_player.x, $game_player.y]
    directions = [[2, 0, 1, 1], [4, -1, 0, 2],
                  [6, 1, 0, 3], [8, 0, -1, 4]]
    queue = [start]
    previous = {start => nil}
    destination = nil
    checked = 0
    until queue.empty? || checked >= 1024
      pos = queue.shift
      checked += 1
      if (pos[0] - clerk.x).abs + (pos[1] - clerk.y).abs == 1
        destination = pos
        break
      end
      directions.each do |direction, dx, dy, step|
        nx, ny = pos[0] + dx, pos[1] + dy
        neighbor = [nx, ny]
        next if nx < 0 || ny < 0 || nx >= $game_map.width || ny >= $game_map.height
        next if previous.key?(neighbor)
        next unless $game_player.passable?(pos[0], pos[1], direction)
        previous[neighbor] = [pos, step]
        queue << neighbor
      end
    end
    unless destination
      pbMessage(BlueKantoPilot.t("Clerk: You can talk to me from here. The counter is busy.", "Funcionário: Pode falar comigo daqui mesmo; o balcão está ocupado."))
      return false
    end
    steps = []
    cursor = destination
    while cursor != start
      parent, step = previous.fetch(cursor)
      steps.unshift(step)
      cursor = parent
    end
    face = if clerk.x > destination[0]
             18
           elsif clerk.x < destination[0]
             17
           elsif clerk.y > destination[1]
             16
           else
             19
           end
    route = RPG::MoveRoute.new
    route.repeat = false
    route.skippable = true
    route.list = (steps + [face, 0]).map { |code| RPG::MoveCommand.new(code) }
    $game_player.force_move_route(route)
    true
  end

  def self.viridian_parcel_call
    return unless parcel_pickup_pending?
    pbMessage(BlueKantoPilot.t("Clerk: Hey, you! Could you come over to the counter for a moment?", "Funcionário: Ei, você! Pode vir até o balcão um instante?"))
  end

  def self.receive_oak_parcel
    return false unless parcel_pickup_pending?
    # An isolated Kanto save flag avoids adding a foreign FRLG item ID.
    progress["pilot_oak_parcel_received"] = true
    BlueMusic.kanto_me_play("obtained_item")
    pbMessage(BlueKantoPilot.t("Clerk: Professor Oak ordered this package. Take it to his lab in Pallet!", "Funcionário: O professor Oak encomendou este pacote. Leve-o ao laboratório em Pallet!"))
    true
  end

  def self.viridian_mart
    if parcel_pickup_pending?
      # Recovery for already-installed saves; normal entry uses the autorun.
      # FireRed does not offer shopping during the first parcel handoff.
      receive_oak_parcel
      return
    elsif progress["pilot_oak_parcel_received"] && !progress["pilot_oak_parcel_delivered"]
      pbMessage(BlueKantoPilot.t("Clerk: Don't forget to deliver the package to Professor Oak in Pallet.", "Funcionário: Não esqueça de entregar o pacote ao professor Oak, em Pallet."))
    end
    pbPokemonMart(VIRIDIAN_MART_STOCK.dup)
  end

  def self.forest_unlocked?
    progress["pilot_oak_parcel_delivered"] == true ||
      # Existing Kanto saves with a badge must not be stranded by this patch.
      BlueRegions.local_achievements(progress, "KANTO").include?("BOULDER")
  end

  def self.route2_gate_warning
    pbMessage(BlueKantoPilot.t("The northern path to Route 2 is blocked. Deliver the Poké Mart package to Professor Oak in Pallet first!", "O caminho norte para a Rota 2 está bloqueado. Primeiro entregue a encomenda do Poké Mart ao Professor Oak em Pallet!"))
  end

  # A connected outdoor map changes before a normal transfer event runs.
  # The event markers created on Viridian's actual north edge define where
  # the route exists. Guard the LAST movement into Route 2 itself, even if an
  # invisible Player Touch event does not block the preceding tile.
  def self.route2_exit_blocked?(player, direction)
    return false unless player && direction == 8 && player.y == 0 && $game_map
    return false unless $game_map.events.values.any? { |event|
      event.name == "Kanto Viridian Route 2 Parcel Gate" &&
        event.y == 0 && event.x == player.x
    }
    !forest_unlocked?
  end

  # Exact, source-grounded Pewter east boundary compiled by pilot.py.
  # Only the first Kanto Boulder Badge may open Route 3; crystals earned in
  # other regions do not unlock it. No second foreign-story switch is needed.
  def self.pewter_route3_blocked?(player, direction)
    return false unless player && $game_map && direction == 6
    gate = "Data/blue-kanto-pewter-route3-gate.txt"
    return false unless File.file?(gate)
    @pewter_route3_edge ||= begin
      pieces = File.read(gate).strip.split("|")
      pieces.length == 4 ? pieces.map { |value| Integer(value, 10) } : []
    end
    map_id, width, first, last = @pewter_route3_edge
    return false unless map_id && width && first && last
    return false unless $game_map.map_id == map_id && player.x >= width - 1
    return false unless player.y >= first && player.y < last
    !BlueRegions.local_achievements(progress, "KANTO").include?("BOULDER")
  end

  def self.pewter_route3_warning
    pbMessage(BlueKantoPilot.t("The eastern exit from Pewter to Route 3 is blocked. Defeat Brock and earn the Boulder Badge first!", "A saída leste de Pewter para a Rota 3 está bloqueada. Derrote Brock e conquiste a Boulder Badge primeiro!"))
  end

  def self.rival_done?
    progress["pilot_rival"] == true
  end

  def self.rival_pending?
    starter && !rival_done? && $player.able_pokemon_count > 0
  end

  def self.lab_escort_pending?
    !starter && !progress["pilot_oak_lab_seen"] && ($game_player.x == 6 && $game_player.y == 12)
  end

  def self.position_lab_oak
    $game_map.events[15].moveto(6, 11)
  end

  def self.finish_lab_escort
    progress["pilot_oak_lab_seen"] = true
  end

  def self.rival_hint
    if rival_done?
      pbMessage(BlueKantoPilot.t("Gary: Keep training. We'll have our rematch later!", "Gary: Continue treinando. Nossa revanche fica para depois!"))
    else
      pbMessage(BlueKantoPilot.t("Gary: I want to see which Pokémon you pick.", "Gary: Quero ver qual Pokémon você vai escolher."))
    end
  end

  def self.rival
    if !starter
      pbMessage(BlueKantoPilot.t("Gary: Pick your Pokémon first.", "Gary: Escolha o seu Pokémon primeiro."))
      return
    end
    if rival_done?
      pbMessage(BlueKantoPilot.t("Gary: Keep training. We'll have our rematch later!", "Gary: Continue treinando. Nossa revanche fica para depois!"))
      return
    end
    return unless rival_pending?
    BlueMusic.with_kanto_scene("rival_appears") do
      pbMessage(BlueKantoPilot.t("Gary: Hey, {1}! Before you go, let's test our Pokémon!", "Gary: Ei, {1}! Antes de ir, vamos testar nossos Pokémon!", $player.name))
    end
    setBattleRule("canLose")
    result = TrainerBattle.start(:BLUE_KANTO_RIVAL, "Blue", RIVAL_VERSIONS.fetch(starter))
    $player.heal_party
    progress["pilot_rival"] = true
    if result
      pbMessage(BlueKantoPilot.t("Gary: You won. I'll train for our rematch!", "Gary: Você venceu. Vou treinar para a revanche!"))
    else
      pbMessage(BlueKantoPilot.t("Gary: That one was mine. Go train on Route 1.", "Gary: Essa foi minha. Vá treinar na Rota 1."))
    end
  end

  # The gate uses local Kanto badges, not the global crystal total. A
  # completed Decades/Johto region cannot prematurely unlock Giovanni.
  def self.viridian_access?
    earned = BlueRegions.local_achievements(progress, "KANTO")
    VIRIDIAN_REQUIRED_BADGES.all? { |badge| earned.include?(badge) } &&
      progress["pilot_silph_rescued"] == true
  end

  def self.viridian_gym_gate(map_id, x, y)
    unless viridian_access?
      missing = VIRIDIAN_REQUIRED_BADGES.reject do |badge|
        BlueRegions.local_achievements(progress, "KANTO").include?(badge)
      end
      if missing.any?
        pbMessage(BlueKantoPilot.t("Viridian Gym is closed. Earn the first seven Kanto badges ({1} left).", "O Ginásio de Viridian está fechado. Conquiste as sete primeiras insígnias de Kanto (faltam {1}).", missing.length))
      else
        pbMessage(BlueKantoPilot.t("The Gym will open once Silph Co. is free.", "O Ginásio só abre após a libertação da Silph Co."))
      end
      return false
    end
    pbFadeOutIn { BlueRegionTravel.move_to([map_id, x, y, 2]) }
    true
  end

  def self.viridian_gym_guide
    if !viridian_access?
      pbMessage(BlueKantoPilot.t("Guide: Giovanni will return once you've earned seven badges and freed Silph Co.", "Guia: Giovanni retorna ao ginásio somente após as sete insígnias e a libertação da Silph Co."))
    elsif BlueRegions.local_achievements(progress, "KANTO").include?("EARTH")
      pbMessage(BlueKantoPilot.t("Guide: The Earth Badge is yours! Head to the Pokémon League when the road opens.", "Guia: A Earth Badge é sua! Siga para a Liga Pokémon quando o caminho estiver disponível."))
    else
      pbMessage(BlueKantoPilot.t("Guide: Giovanni specializes in Ground-type Pokémon. Beat him to earn the Earth Badge!", "Guia: Giovanni é especialista em Pokémon do tipo Terra. Vença para receber a Earth Badge!"))
    end
  end

  def self.full_power_unlocked?
    state = BlueRegions.snapshot
    state && state.fetch("leagues", []).include?("KANTO") &&
      BlueRegions.profile(state, true) == :world_champion_rematch
  end

  def self.full_power_gym(name, trainer_type = nil)
    type = GYM_FULL_POWER[name]
    return false unless type && trainer_type == type && full_power_unlocked?
    return false unless pbConfirmMessage(BlueKantoPilot.t("{1}: Want to face my official Full Power team?", "{1}: Enfrentar meu time oficial Full Power?", name))
    setBattleRule("canLose")
    won = BlueStory.with_regional_full_power {
      TrainerBattle.start(type, name, FULL_POWER_OFFSET)
    }
    if won
      victories = (progress["pilot_full_power_gym_wins"] ||= [])
      victories << name unless victories.include?(name)
      pbMessage(BlueKantoPilot.t("You won {1}'s Full Power rematch!", "Você venceu a revanche Full Power de {1}!", name))
    else
      $player.heal_party
    end
    true
  end

  def self.battle(type, name, event_key = nil, version = 0)
    return unless starter
    if type == :BLUE_KANTO_LEADER_SABRINA && !progress["pilot_silph_rescued"]
      pbMessage(BlueKantoPilot.t("Sabrina is waiting for Silph Co. to be freed. Defeat Giovanni first.", "Sabrina está aguardando a libertação da Silph Co. Derrote Giovanni primeiro."))
      return
    end
    if type == :BLUE_KANTO_LEADER_GIOVANNI && !viridian_access?
      pbMessage(BlueKantoPilot.t("Giovanni won't accept your challenge yet. Earn the first seven badges and free Silph Co.", "Giovanni ainda não aceita seu desafio. Conquiste as sete primeiras insígnias e liberte a Silph Co."))
      return
    end
    if type == :BLUE_KANTO_LEADER_BLAINE && !progress["pilot_cinnabar_secret_key"]
      pbMessage(BlueKantoPilot.t("Blaine: Find the Secret Key in Pokémon Mansion before challenging me!", "Blaine: Encontre a Secret Key na Pokémon Mansion antes do desafio!"))
      return
    end
    if type == :BLUE_KANTO_LEADER_SURGE && !progress["pilot_surge_unlocked"]
      pbMessage(BlueKantoPilot.t("Lt. Surge is behind the electric locks. Solve the trash can puzzle first.", "Lt. Surge aguarda atrás das trancas elétricas. Resolva o enigma das lixeiras primeiro."))
      return
    end
    wins = (progress["pilot_wins"] ||= [])
    # New events persist stable region/map/event keys. Accept old name-only
    # entries from pilot saves built before this fix without replaying battles.
    key = event_key || "#{type}:#{name}"
    # Both Silph Co. and Viridian have a boss named Giovanni. A legacy
    # Silph name-only victory must never mark the *gym* Giovanni as beaten.
    if wins.include?(key) || (type != :BLUE_KANTO_LEADER_GIOVANNI && wins.include?(name))
      return if full_power_gym(name, type)
      pbMessage(BlueKantoPilot.t("{1}: Good luck on your journey!", "{1}: Boa sorte na sua jornada!", name))
      return
    end
    if type == :BLUE_KANTO_RIVAL_SILPH && name == "Blue"
      BlueMusic.with_kanto_scene("rival_appears") do
        pbMessage(BlueKantoPilot.t("Blue: Let's see how much stronger you've grown since Pallet!", "Blue: Vamos ver como você ficou mais forte desde Pallet!"))
      end
    end
    setBattleRule("canLose")
    won = TrainerBattle.start(type, name, version)
    unless won
      $player.heal_party
      return
    end
    wins << key
    if type == :BLUE_KANTO_LEADER && BlueRegions.award(progress, "KANTO", "BOULDER")
      BlueMusic.kanto_me_play("badge_awarded")
      pbMessage(BlueKantoPilot.t("Brock: The Boulder Badge is yours. The road to Cerulean is open!", "Brock: A Boulder Badge é sua. O caminho para Cerulean está aberto!"))
    elsif type == :BLUE_KANTO_LEADER_MISTY && BlueRegions.award(progress, "KANTO", "CASCADE")
      BlueMusic.kanto_me_play("badge_awarded")
      pbMessage(BlueKantoPilot.t("Misty: You earned the Cascade Badge! Head south to Vermilion!", "Misty: Você conquistou a Cascade Badge! Siga ao sul para Vermilion!"))
    elsif type == :BLUE_KANTO_LEADER_SURGE && BlueRegions.award(progress, "KANTO", "THUNDER")
      BlueMusic.kanto_me_play("badge_awarded")
      pbMessage(BlueKantoPilot.t("Lt. Surge: The Thunder Badge is yours! You can now use Fly in Kanto.", "Lt. Surge: A Thunder Badge é sua! Agora você pode usar Fly em Kanto."))
    elsif type == :BLUE_KANTO_LEADER_ERIKA && BlueRegions.award(progress, "KANTO", "RAINBOW")
      BlueMusic.kanto_me_play("badge_awarded")
      pbMessage(BlueKantoPilot.t("Erika: You earned the Rainbow Badge!", "Erika: Você conquistou a Rainbow Badge!"))
    elsif type == :BLUE_KANTO_LEADER_KOGA && BlueRegions.award(progress, "KANTO", "SOUL")
      BlueMusic.kanto_me_play("badge_awarded")
      pbMessage(BlueKantoPilot.t("Koga: The Soul Badge is yours now!", "Koga: A Soul Badge agora é sua!"))
    elsif type == :BLUE_KANTO_ROCKETBOSS && name == "Giovanni"
      progress["pilot_silph_rescued"] = true
      pbMessage(BlueKantoPilot.t("Giovanni was defeated! Silph Co. is free.", "Giovanni foi derrotado! A Silph Co. está livre."))
    elsif type == :BLUE_KANTO_LEADER_SABRINA && BlueRegions.award(progress, "KANTO", "MARSH")
      BlueMusic.kanto_me_play("badge_awarded")
      pbMessage(BlueKantoPilot.t("Sabrina: You earned the Marsh Badge!", "Sabrina: Você conquistou a Marsh Badge!"))
    elsif type == :BLUE_KANTO_LEADER_BLAINE && BlueRegions.award(progress, "KANTO", "VOLCANO")
      BlueMusic.kanto_me_play("badge_awarded")
      pbMessage(BlueKantoPilot.t("Blaine: The Volcano Badge is yours!", "Blaine: A Volcano Badge é sua!"))
    elsif type == :BLUE_KANTO_LEADER_GIOVANNI && BlueRegions.award(progress, "KANTO", "EARTH")
      BlueMusic.kanto_me_play("badge_awarded")
      pbMessage(BlueKantoPilot.t("Giovanni: You earned the Earth Badge! The League challenge lies ahead.", "Giovanni: Você conquistou a Earth Badge! O desafio da Liga está adiante."))


    end
  end

  # MAN-02: keep the native line-of-sight trainer on Event Touch until a
  # real victory. This is invoked only by the trainer's own local event page.
  # The page's second state is a self-switch A; old name-only saves still work.
  def self.sync_trainer_event(key, name, event_id)
    won = progress.fetch("pilot_wins", [])
    return false unless won.include?(key) || won.include?(name)
    return false if !$game_map || !$game_map.events[event_id]
    index = [$game_map.map_id, event_id, "A"]
    unless $game_self_switches[index]
      $game_self_switches[index] = true
      $game_map.need_refresh = true
    end
    true
  end

  def self.trainer_repeat(name, type = nil)
    return if full_power_gym(name, type)
    pbMessage(BlueKantoPilot.t("{1}: Good luck on your journey!", "{1}: Boa sorte na sua jornada!", name))
  end

  SURGE_CANS = ([4, 10] + (22..34).to_a).freeze
  SURGE_LOCKS = ([8] + (11..19).to_a).freeze

  # The original gym used source-project global switches. The pilot uses only
  # its own Kanto state and gym-event self switches, so Decades remains safe.
  def self.surge_pairs
    cans = SURGE_CANS.filter_map do |id|
      event = $game_map.events[id]
      [id, event.x, event.y] if event
    end
    return [] if cans.length < 2
    horizontal_or_vertical = cans.combination(2).filter_map do |a, b|
      next unless a[1] == b[1] || a[2] == b[2]
      [[a[0], b[0]], (a[1]-b[1]).abs + (a[2]-b[2]).abs]
    end
    return [] if horizontal_or_vertical.empty?
    closest = horizontal_or_vertical.map(&:last).min
    horizontal_or_vertical.select { |_pair, distance| distance == closest }.map(&:first)
  end

  def self.surge_can(event_id)
    if progress["pilot_surge_unlocked"]
      pbMessage(BlueKantoPilot.t("Both electric locks have already been disabled.", "As duas trancas elétricas já foram desativadas."))
      return
    end
    possible = surge_pairs
    if possible.empty?
      pbMessage(BlueKantoPilot.t("The mechanism isn't ready in this copy of the Gym.", "O mecanismo não está pronto nesta cópia do ginásio."))
      return
    end
    progress["pilot_surge_solution"] ||= possible.sample
    target = progress["pilot_surge_solution"]
    if !progress["pilot_surge_first"]
      if event_id == target[0]
        progress["pilot_surge_first"] = true
        pbMessage(BlueKantoPilot.t("You found the first key! Check a trash can nearby.", "Você encontrou a primeira chave! Procure outra lixeira próxima."))
      else
        pbMessage(BlueKantoPilot.t("There's no key in this trash can.", "Não há chave nesta lixeira."))
      end
    elsif event_id == target[1]
      progress["pilot_surge_unlocked"] = true
      progress["pilot_surge_first"] = false
      SURGE_LOCKS.each do |id|
        $game_self_switches[[$game_map.map_id, id, "A"]] = true
      end
      $game_map.need_refresh = true
      pbMessage(BlueKantoPilot.t("Both locks are disabled! You can now reach Lt. Surge.", "As duas trancas foram desativadas! Lt. Surge está acessível."))
    else
      progress["pilot_surge_first"] = false
      progress.delete("pilot_surge_solution")
      pbMessage(BlueKantoPilot.t("Wrong key! The trash can switches have reset.", "Chave errada! O sistema reiniciou a sequência de lixeiras."))
    end
  end

  def self.surge_gate
    pbMessage(BlueKantoPilot.t("The electric lock is active. Find two keys in the trash cans.", "A trava elétrica está ativa. Encontre duas chaves nas lixeiras."))
  end

  # TEMPORARY phase 08 story bridge: Bill's canonical S.S. Ticket event is
  # outside the installed route until the Cerulean north passage is audited.
  # Only players with Cascade may claim a ticket; never award it more than once.
  def self.ticketmaster
    if !BlueRegions.local_achievements(progress, "KANTO").include?("CASCADE")
      pbMessage(BlueKantoPilot.t("Harbor clerk: Earn the Cascade Badge in Cerulean first.", "Porto: Primeiro conquiste a Cascade Badge em Cerulean."))
      return
    end
    if progress["pilot_ss_ticket"] || (GameData::Item.exists?(:SSTICKET) && $bag.has?(:SSTICKET))
      progress["pilot_ss_ticket"] = true
      pbMessage(BlueKantoPilot.t("Harbor clerk: You're cleared to board the S.S. Anne!", "Porto: Sua passagem para o S.S. Anne está liberada!"))
    elsif !GameData::Item.exists?(:SSTICKET)
      # Decades does not guarantee the FRLG ticket item exists. Use a local
      # save-state permit without changing native item PBS or other saves.
      progress["pilot_ss_ticket"] = true
      pbMessage(BlueKantoPilot.t("Experimental access: Your digital pass for the S.S. Anne is active.", "Acesso experimental: a passagem digital para o S.S. Anne está liberada."))
    elsif $bag.add(:SSTICKET, 1)
      progress["pilot_ss_ticket"] = true
      BlueMusic.kanto_me_play("obtained_item")
      pbMessage(BlueKantoPilot.t("Experimental access: You received the S.S. Ticket. Bill's event will be adapted later.", "Acesso experimental: recebeu o S.S. Ticket. O evento de Bill será adaptado depois."))
    else
      pbMessage(BlueKantoPilot.t("Make room in your Bag to receive the S.S. Ticket.", "Você precisa liberar espaço na Bolsa para receber o S.S. Ticket."))
    end
  end

  def self.harbor_gate(map_id, x, y)
    unless progress["pilot_ss_ticket"] || (GameData::Item.exists?(:SSTICKET) && $bag.has?(:SSTICKET))
      pbMessage(BlueKantoPilot.t("You need the S.S. Ticket to enter the harbor. Speak to the clerk.", "O acesso ao porto exige o S.S. Ticket. Fale com o atendente."))
      return
    end
    pbFadeOutIn { BlueRegionTravel.move_to([map_id, x, y, 2]) }
  end

  # The captain's original scripts are not executed in Blue. Give the audited
  # Cut HM once, using the item ID actually available in the installed game.
  def self.captain
    events = (progress["field_events"]["KANTO"] ||= [])
    if events.include?("SS_ANNE_CAPTAIN")
      pbMessage(BlueKantoPilot.t("Captain: Use Cut to clear paths where you have permission.", "Capitão: Use Cut para abrir caminhos onde tiver permissão."))
      return
    end
    item = [:HM01, :HMCUT].find { |candidate| GameData::Item.exists?(candidate) }
    unless item
      pbMessage(BlueKantoPilot.t("HM Cut hasn't been added to this version of Blue yet.", "O HM Cut ainda não está cadastrado nesta versão do Blue."))
      return
    end
    unless $bag.add(item, 1)
      pbMessage(BlueKantoPilot.t("Captain: Make room in your Bag for HM Cut.", "Capitão: Libere espaço na Bolsa para receber o HM Cut."))
      return
    end
    events << "SS_ANNE_CAPTAIN"
    BlueMusic.kanto_me_play("obtained_item")
    pbMessage(BlueKantoPilot.t("The captain gave you HM Cut! The Cascade Badge lets you use it in Kanto.", "O Capitão entregou o HM Cut! A Cascade Badge permite usá-lo em Kanto."))
  end

  # Ground items preserve FRLG EventID and quantity, but all ownership and
  # persistence are Kanto-local. Only success hides the object; existing
  # field item flags migrate without granting a second copy.
  def self.pickup(item, key, event_id = nil, quantity = 1)
    collected = (progress["pilot_items"] ||= [])
    if collected.include?(key)
      if event_id && $game_map && $game_map.events[event_id]
        $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
        $game_map.events[event_id].refresh
      end
      return true
    end
    unless GameData::Item.exists?(item)
      pbMessage(BlueKantoPilot.t("This item isn't registered in Blue.", "O item não está cadastrado no Blue."))
      return false
    end
    unless quantity.between?(1, 99) && (!$bag.respond_to?(:can_add?) || $bag.can_add?(item, quantity))
      pbMessage(BlueKantoPilot.t("Your Bag is full. Make room to pick up this item.", "Sua Bolsa está cheia. Libere espaço para recolher o item."))
      return false
    end
    unless $bag.add(item, quantity)
      pbMessage(BlueKantoPilot.t("Your Bag is full. Make room to pick up this item.", "Sua Bolsa está cheia. Libere espaço para recolher o item."))
      return false
    end
    collected << key
    if event_id && $game_map && $game_map.events[event_id]
      $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
      $game_map.events[event_id].refresh
    end
    BlueMusic.kanto_me_play("obtained_item")
    label = GameData::Item.get(item).name
    pbMessage(BlueKantoPilot.t("Found {1}{2}!", "Encontrou {1}{2}!", quantity == 1 ? "" : "#{quantity}x ", label))
    true
  end


  # Silph Card Key: persist locally, never import a foreign item into Decades.
  def self.silph_card_key
    if progress["pilot_silph_card_key"]
      pbMessage(BlueKantoPilot.t("You already found the Silph Co. Card Key.", "Você já encontrou a Card Key da Silph Co."))
      return
    end
    progress["pilot_silph_card_key"] = true
    $game_self_switches[[$game_map.map_id, 9, "A"]] = true
    $game_map.need_refresh = true
    pbMessage(BlueKantoPilot.t("You found the Card Key! You can now open the Silph Co. doors.", "Encontrou a Card Key! Agora pode abrir as portas da Silph Co."))
  end

  # Adjacent source map event tiles form a single original locked door.
  def self.silph_door(event_ids)
    unless progress["pilot_silph_card_key"]
      pbMessage(BlueKantoPilot.t("A security lock. Find the Card Key on the fifth floor.", "Uma trava de segurança. Encontre a Card Key no 5º andar."))
      return
    end
    event_ids.each do |eid|
      next unless $game_map.events[eid]
      $game_self_switches[[$game_map.map_id, eid, "A"]] = true
    end
    $game_map.need_refresh = true
    pbMessage(BlueKantoPilot.t("The Card Key opened the door!", "A Card Key abriu a porta!"))
  end

  def self.silph_rival
    return unless starter
    versions = { BULBASAUR: 51, CHARMANDER: 52, SQUIRTLE: 53 }
    key = "KANTO_184_043"
    battle(:BLUE_KANTO_RIVAL_SILPH, "Blue", key, versions.fetch(starter))
  end

  def self.silph_president
    unless progress["pilot_silph_rescued"]
      pbMessage(BlueKantoPilot.t("President: Giovanni still controls the top floor!", "Presidente: Giovanni ainda controla o último andar!"))
      return
    end
    if progress["pilot_silph_master_ball"]
      pbMessage(BlueKantoPilot.t("President: Thank you for freeing Silph Co.!", "Presidente: Obrigado por libertar a Silph Co.!"))
      return
    end
    unless GameData::Item.exists?(:MASTERBALL)
      pbMessage(BlueKantoPilot.t("The Master Ball hasn't been added to this version of Blue yet.", "A Master Ball ainda não está cadastrada nesta versão do Blue."))
      return
    end
    unless $bag.add(:MASTERBALL, 1)
      pbMessage(BlueKantoPilot.t("President: Make room in your Bag for the Master Ball.", "Presidente: Abra espaço na Bolsa para receber a Master Ball."))
      return
    end
    progress["pilot_silph_master_ball"] = true
    BlueMusic.kanto_me_play("obtained_item")
    pbMessage(BlueKantoPilot.t("You received the Master Ball for freeing Silph Co.!", "Recebeu a Master Ball pela libertação da Silph Co.!"))
  end

  def self.dojo_prize(species, event_id)
    unless progress.fetch("pilot_wins", []).include?("KANTO_172_012")
      pbMessage(BlueKantoPilot.t("Defeat Master Koichi before choosing a Pokémon.", "Vença primeiro o mestre Koichi para escolher um Pokémon."))
      return
    end
    if progress["pilot_dojo_prize"]
      pbMessage(BlueKantoPilot.t("You've already chosen a Pokémon at the Fighting Dojo.", "Você já escolheu seu Pokémon no Fighting Dojo."))
      return
    end
    if $player.party.length >= 6
      pbMessage(BlueKantoPilot.t("Your party is full. Leave a space for the dojo Pokémon.", "Sua equipe está cheia. Deixe uma vaga para o Pokémon do dojo."))
      return
    end
    return unless GameData::Species.exists?(species)
    return unless pbConfirmMessage(BlueKantoPilot.t("Choose {1} as your one-time dojo prize?", "Escolher {1} como prêmio único do dojo?", GameData::Species.get(species).name))
    return unless pbAddPokemonSilent(species, 25)
    progress["pilot_dojo_prize"] = species.to_s
    BlueMusic.kanto_me_play("obtained_pokemon")
    [1, 2].each { |eid| $game_self_switches[[$game_map.map_id, eid, "A"]] = true }
    $game_map.need_refresh = true
    pbMessage(BlueKantoPilot.t("You received your Fighting Dojo prize!", "Prêmio do Fighting Dojo recebido!"))
  end

  def self.silph_elevator
    filename = "Data/blue-kanto-silph-floors.txt"
    unless experimental? && File.file?(filename)
      pbMessage(BlueKantoPilot.t("The elevator controls are available inside the pilot.", "Os controles do elevador não estão disponíveis fora do piloto."))
      return
    end
    floors = File.readlines(filename, encoding: "UTF-8").filter_map do |raw|
      parts = raw.strip.split("|")
      next unless parts.length == 5
      coords = parts.map { |part| Integer(part, 10) rescue nil }
      next unless coords.all? { |value| value.is_a?(Integer) }
      floor, map_id, x, y, direction = coords
      next unless floor.between?(1, 11) && map_id > 0 && x >= 0 && y >= 0
      next unless [2, 4, 6, 8].include?(direction)
      next unless pbRgssExists?(sprintf("Data/Map%03d.rxdata", map_id))
      [floor, [map_id, x, y, direction]]
    end
    return if floors.empty?
    choice = pbMessage(BlueKantoPilot.t("Silph Co. — choose a floor", "Silph Co. — escolher andar"),
                       floors.map { |row| BlueKantoPilot.t("Floor {1}F", "Andar {1}F", row[0]) } + [BlueKantoPilot.t("Back", "Voltar")], -1)
    return unless choice && choice.between?(0, floors.length - 1)
    pbFadeOutIn { BlueRegionTravel.move_to(floors[choice][1]) }
  end

  # Phase 12 uses only Kanto-local progress. The FRLG source contains
  # foreign switches, quiz scripts and rewards; none are executed by Blue.
  CINNABAR_QUIZZES = [
    [["Does Caterpie evolve into Metapod?", "Caterpie evolui para Metapod?"], true],
    [["Are there nine official Kanto badges?", "Existem nove insígnias oficiais de Kanto?"], false],
    [["Does Poliwag have three stages of evolution after its initial form?", "Poliwag possui três evoluções consecutivas?"], false],
    [["Are Electric-type moves super effective against Ground-type Pokémon?", "Golpes elétricos são supereficazes contra Pokémon Terrestres?"], false],
    [["Can two Pokémon of the same species and level have different stats?", "Dois Pokémon da mesma espécie e nível podem ter atributos diferentes?"], true],
    [["Does TM28 contain the move Tombstony?", "O TM28 contém o golpe Tombstony?"], false]
  ].freeze
  CINNABAR_GYM_DOORS = {
    1 => [20,21,22,23], 2 => [1,25,26,27],
    3 => [2,18,19,29], 4 => [13,31,32],
    5 => [34,35,36,37], 6 => [39,40,41,42]
  }.freeze

  def self.cinnabar_gym_gate(map_id, x, y)
    unless progress["pilot_cinnabar_secret_key"]
      pbMessage(BlueKantoPilot.t("Cinnabar Gym is locked. The Secret Key is in Pokémon Mansion.", "O ginásio de Cinnabar está trancado. A Secret Key está na Pokémon Mansion."))
      return
    end
    pbFadeOutIn { BlueRegionTravel.move_to([map_id, x, y, 2]) }
  end

  def self.cinnabar_unlock(group)
    return false unless CINNABAR_GYM_DOORS.key?(group)
    unlocked = (progress["pilot_cinnabar_doors"] ||= [])
    unlocked << group unless unlocked.include?(group)
    CINNABAR_GYM_DOORS[group].each do |event_id|
      next unless $game_map.events[event_id]
      $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
    end
    $game_map.need_refresh = true
    true
  end

  def self.cinnabar_quiz(group)
    return unless group.between?(1, CINNABAR_QUIZZES.length)
    if progress.fetch("pilot_cinnabar_doors", []).include?(group)
      pbMessage(BlueKantoPilot.t("This Gym room is already unlocked.", "Essa sala do ginásio já está liberada."))
      return
    end
    question, answer = CINNABAR_QUIZZES[group - 1]
    choice = pbMessage(BlueKantoPilot.t(*question), [BlueKantoPilot.t("Yes", "Sim"), BlueKantoPilot.t("No", "Não"), BlueKantoPilot.t("Back", "Voltar")], -1)
    return unless choice == 0 || choice == 1
    if (choice == 0) == answer
      cinnabar_unlock(group)
      pbMessage(BlueKantoPilot.t("Correct! The door opened.", "Resposta correta! A porta se abriu."))
    else
      pbMessage(BlueKantoPilot.t("Incorrect. You can try again or battle the trainer in this room.", "Resposta incorreta. Você pode tentar de novo ou enfrentar o treinador da sala."))
    end
  end

  def self.cinnabar_trainer(type, name, key, group)
    battle(type, name, key)
    cinnabar_unlock(group) if progress.fetch("pilot_wins", []).include?(key)
  end

  def self.cinnabar_door(group)
    if progress.fetch("pilot_cinnabar_doors", []).include?(group)
      cinnabar_unlock(group)
    else
      pbMessage(BlueKantoPilot.t("The door is locked. Answer the quiz or defeat the trainer in this room.", "A porta está trancada. Responda ao quiz ou vença o treinador da sala."))
    end
  end

  # Mansion's multiple doors are attached to a locally persisted floor
  # switch. Only the matching current map is affected, never native Decades.
  def self.mansion_switch(source_map, door_ids)
    used = (progress["pilot_mansion_switches"] ||= [])
    used << source_map unless used.include?(source_map)
    door_ids.each do |event_id|
      next unless $game_map.events[event_id]
      $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
    end
    $game_map.need_refresh = true
    pbMessage(BlueKantoPilot.t("A passage opened in Pokémon Mansion!", "Uma passagem da Pokémon Mansion foi aberta!"))
  end

  def self.mansion_door(source_map, door_ids)
    if progress.fetch("pilot_mansion_switches", []).include?(source_map)
      door_ids.each do |event_id|
        next unless $game_map.events[event_id]
        $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
      end
      $game_map.need_refresh = true
    else
      pbMessage(BlueKantoPilot.t("A nearby statue controls this passage.", "Esta passagem depende de uma estátua próxima."))
    end
  end

  def self.mansion_secret_key
    if progress["pilot_cinnabar_secret_key"]
      pbMessage(BlueKantoPilot.t("You already found the Secret Key in Pokémon Mansion.", "Você já encontrou a Secret Key da Pokémon Mansion."))
      return
    end
    progress["pilot_cinnabar_secret_key"] = true
    $game_self_switches[[$game_map.map_id, 8, "A"]] = true
    $game_map.need_refresh = true
    pbMessage(BlueKantoPilot.t("You found the Secret Key! Cinnabar Gym is unlocked.", "Você encontrou a Secret Key! O ginásio de Cinnabar foi destrancado."))
  end

  # Phase 14: use ONLY Kanto-local badges for the league checks. The
  # global Decades crystal total still controls levels, not story access.
  def self.league_badges?
    earned = BlueRegions.local_achievements(progress, "KANTO")
    LEAGUE_REQUIRED_BADGES.all? { |badge| earned.include?(badge) }
  end

  def self.league_badge_check(required, guard_id, barrier_id)
    unless required.between?(1, LEAGUE_REQUIRED_BADGES.length)
      return false
    end
    needed = LEAGUE_REQUIRED_BADGES.first(required)
    earned = BlueRegions.local_achievements(progress, "KANTO")
    missing = needed.reject { |badge| earned.include?(badge) }
    if missing.any?
      pbMessage(BlueKantoPilot.t("Guard: You need Kanto's {1} badge to proceed.", "Guarda: Você precisa da insígnia {1} de Kanto para seguir.", missing.first))
      return false
    end
    [guard_id, barrier_id].each do |event_id|
      next unless $game_map.events[event_id]
      $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
    end
    $game_map.need_refresh = true
    pbMessage(BlueKantoPilot.t("Guard: Your badges check out. You may pass!", "Guarda: Insígnias verificadas. Pode passar!"))
    true
  end

  def self.league_route_gate(map_id, x, y, required = 8)
    required = 8 unless required.between?(1, 8)
    earned = BlueRegions.local_achievements(progress, "KANTO")
    missing = LEAGUE_REQUIRED_BADGES.first(required).reject { |badge| earned.include?(badge) }
    if missing.any?
      pbMessage(BlueKantoPilot.t("The road to the League is blocked. You're missing Kanto's {1} badge.", "O acesso à Liga está bloqueado. Falta a insígnia {1} de Kanto.", missing.first))
      return false
    end
    pbFadeOutIn { BlueRegionTravel.move_to([map_id, x, y, 2]) }
    true
  end

  # Adapted passage for Victory Road's Strength mechanisms, keeping source
  # event sprites and simplifying the boulder position puzzle in the pilot.
  # The native Strength HM acquisition and exact tile puzzle require manual QA.
  def self.victory_strength(barrier_ids)
    unless BlueRegions.local_achievements(progress, "KANTO").include?("RAINBOW")
      pbMessage(BlueKantoPilot.t("The Victory Road mechanism requires Kanto's Rainbow Badge.", "O mecanismo da Victory Road requer a Rainbow Badge de Kanto."))
      return false
    end
    barrier_ids.each do |event_id|
      next unless $game_map.events[event_id]
      $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
    end
    $game_map.need_refresh = true
    pbMessage(BlueKantoPilot.t("The Victory Road boulder mechanism is active (experimental mode).", "O mecanismo de pedras da Victory Road foi ativado (modo experimental)."))
    true
  end

  def self.victory_couple
    key = "KANTO_213_PAIR"
    wins = (progress["pilot_wins"] ||= [])
    if wins.include?(key)
      pbMessage(BlueKantoPilot.t("Ray and Tyra: We've already battled. Good luck in the League!", "Ray e Tyra: Já batalhamos. Boa sorte na Liga!"))
      return true
    end
    return false unless starter
    setBattleRule("canLose")
    setBattleRule("double")
    won = TrainerBattle.start(:BLUE_KANTO_COOLCOUPLE, "Ray & Tyra")
    unless won
      $player.heal_party
      return false
    end
    wins << key
    [15, 16].each do |event_id|
      ekey = sprintf("KANTO_213_%03d", event_id)
      wins << ekey unless wins.include?(ekey)
      $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
    end
    $game_map.need_refresh = true
    true
  end

  def self.league_active?
    progress["pilot_league_active"] == true && league_badges? &&
      (!progress.fetch("leagues", []).include?("KANTO") ||
       progress["pilot_league_full_power"] == true)
  end

  def self.league_begin(map_id, x, y)
    unless league_badges?
      pbMessage(BlueKantoPilot.t("The League requires all eight Kanto badges, including the Earth Badge.", "A Liga exige as oito insígnias de Kanto, inclusive a Earth Badge."))
      return false
    end
    completed = progress.fetch("leagues", []).include?("KANTO")
    if completed && !full_power_unlocked?
      pbMessage(BlueKantoPilot.t("The official Full Power teams unlock after you finish every League in the regional circuit.", "Os times oficiais Full Power só ficam disponíveis após concluir todas as Ligas do circuito regional."))
      return false
    end
    if completed && !pbConfirmMessage(BlueKantoPilot.t("Challenge the Elite Four and Champion with their official Full Power teams?", "Desafiar a Elite Four e o Campeão com os times oficiais Full Power?"))
      return false
    end
    progress["pilot_league_full_power"] = completed
    progress["pilot_league_active"] = true
    progress["pilot_league_wins"] = []
    pbFadeOutIn { BlueRegionTravel.move_to([map_id, x, y, 2]) }
    true
  end

  def self.league_battle(stage, type, name, lobby_map)
    return false unless LEAGUE_ORDER.include?(stage)
    unless league_active? && starter
      pbMessage(BlueKantoPilot.t("Earn all eight badges and enter through the League's door to begin the challenge.", "Conquiste as oito insígnias e entre pela porta da Liga para iniciar o desafio."))
      return false
    end
    wins = (progress["pilot_league_wins"] ||= [])
    index = LEAGUE_ORDER.index(stage)
    if wins.include?(stage)
      pbMessage(BlueKantoPilot.t("{1}: You've already defeated me on this run.", "{1}: Já fui derrotado nesta tentativa.", name))
      return true
    end
    unless wins.length == index && LEAGUE_ORDER[0,index] == wins
      pbMessage(BlueKantoPilot.t("You must defeat the Elite Four in order.", "Você precisa superar a Elite Four na ordem correta."))
      return false
    end
    version = (stage == "CHAMPION") ? LEAGUE_CHAMPION_VERSIONS.fetch(starter) : 0
    if stage == "CHAMPION" && type == :BLUE_KANTO_CHAMPION_BLUE && name == "Blue"
      BlueMusic.with_kanto_scene("rival_appears") do
        pbMessage(BlueKantoPilot.t("Blue: You beat the Elite Four! Our final battle starts now.", "Blue: Você venceu a Elite! Nossa batalha final começa agora."))
      end
    end
    setBattleRule("canLose")
    full_power = progress["pilot_league_full_power"] == true
    version += FULL_POWER_OFFSET if full_power
    won = full_power ? BlueStory.with_regional_full_power {
      TrainerBattle.start(type, name, version)
    } : TrainerBattle.start(type, name, version)
    unless won
      $player.heal_party
      progress["pilot_league_full_power"] = false
      progress["pilot_league_active"] = false
      progress["pilot_league_wins"] = []
      pbMessage(BlueKantoPilot.t("You lost this League run. Return to the lobby and try again.", "Você perdeu esta tentativa da Liga. Volte ao saguão para tentar novamente."))
      pbFadeOutIn { BlueRegionTravel.move_to([lobby_map, 11, 16, 2]) }
      return false
    end
    wins << stage
    pbMessage(BlueKantoPilot.t("You beat {1}! League progress: {2}/5.", "Vitória contra {1}! Progresso da Liga: {2}/5.", name, wins.length))
    true
  end

  def self.league_advance(stage, map_id, x, y)
    wins = progress.fetch("pilot_league_wins", [])
    if !league_active? || !wins.include?(stage)
      pbMessage(BlueKantoPilot.t("The passage opens once you defeat the opponent in this room.", "A passagem só abre depois de vencer o adversário desta sala."))
      return false
    end
    pbFadeOutIn { BlueRegionTravel.move_to([map_id, x, y, 2]) }
    true
  end

  def self.league_finalize(pallet_map)
    unless league_active? && progress.fetch("pilot_league_wins", []) == LEAGUE_ORDER
      pbMessage(BlueKantoPilot.t("Hall of Fame locked: You still need to defeat the Elite Four or Champion.", "Hall of Fame bloqueado: faltam vitórias na Elite Four ou no Campeão."))
      return false
    end
    if progress["pilot_league_full_power"] == true
      progress["pilot_league_full_power"] = false
      progress["pilot_league_active"] = false
      progress["pilot_full_power_league_complete"] = true
      pbMessage(BlueKantoPilot.t("You completed the Full Power League! No badges were awarded again.", "Liga Full Power concluída! Nenhuma insígnia foi concedida novamente."))
      pbFadeOutIn { BlueRegionTravel.move_to([pallet_map, 18, 8, 2]) }
      return true
    end
    return false unless BlueRegions.complete_league(progress, "KANTO")
    progress["pilot_league_active"] = false
    progress["pilot_hall_of_fame"] = true
    BlueMusic.with_kanto_scene("hall_of_fame") do
      pbMessage(BlueKantoPilot.t("Hall of Fame: Kanto complete! Decades and Johto are open in the regional circuit.", "Hall of Fame: Kanto concluída! Decades e Johto foram liberadas no circuito regional."))
    end
    pbFadeOutIn { BlueRegionTravel.move_to([pallet_map, 18, 8, 2]) }
    true
  end

  # The regional transport NPC already exists in starter-town Pallet. The
  # Lobby's guide is an additional after-League point and uses the same
  # single-save travel service (only destinations with maps can be visited).
  def self.league_champion_npc
    pbMessage(BlueKantoPilot.t("Blue: Beating the Elite Four was just the start! Let's see if you can beat the Champion.", "Blue: Vencer a Elite foi só o começo! Quero ver se você supera o Campeão."))
  end

  def self.league_oak
    if progress.fetch("leagues", []).include?("KANTO")
      pbMessage(BlueKantoPilot.t("Oak: Your name has been entered in the Kanto Hall of Fame!", "Oak: Seu nome entrou para o Hall of Fame de Kanto!"))
    else
      pbMessage(BlueKantoPilot.t("Oak: Defeat Blue first and complete your journey in the Hall of Fame.", "Oak: Primeiro derrote Blue e conclua a jornada no Hall of Fame."))
    end
  end

  def self.league_guide
    if progress.fetch("leagues", []).include?("KANTO")
      pbMessage(BlueKantoPilot.t("League guide: Congratulations, Champion! Speak to the regional agent here or in Pallet.", "Guia da Liga: Parabéns, Campeão! Consulte o agente regional aqui ou em Pallet."))
      BlueRegionTravel.agent(true)
    else
      pbMessage(BlueKantoPilot.t("League guide: Defeat Lorelei, Bruno, Agatha, Lance and Blue in order.", "Guia da Liga: Vença Lorelei, Bruno, Agatha, Lance e Blue em sequência."))
    end
  end

  # Travel shortcuts exist only in the standalone pilot, NEVER in the
  # main Blue campaign. Stops are generated from source-defined warp entries.
  def self.experimental?
    File.file?("Kanto pilot.json") &&
      File.file?("Data/blue-kanto-experimental-stops.txt") &&
      $PokemonGlobal && $PokemonGlobal.blue_regions.is_a?(Hash) &&
      $PokemonGlobal.blue_regions["current"] == "KANTO"
  end

  def self.experimental_stops
    return [] unless experimental?
    File.readlines("Data/blue-kanto-experimental-stops.txt", encoding: "UTF-8").filter_map do |raw|
      parts = raw.strip.split("|")
      next unless parts.length == 6
      map, x, y, dir = parts[2,4].map { |part| Integer(part, 10) rescue nil }
      next unless [map,x,y,dir].all? { |item| item.is_a?(Integer) }
      next unless map > 0 && x >= 0 && y >= 0 && [2,4,6,8].include?(dir)
      next unless pbRgssExists?(sprintf("Data/Map%03d.rxdata", map))
      [parts[1], [map,x,y,dir]]
    end
  end

  def self.experimental_menu
    return unless experimental?
    unless $player.party.any? { |pkmn| !pkmn.egg? }
      pbMessage(BlueKantoPilot.t("Choose a Pokémon with Oak before using the test warps.", "Escolha um Pokémon com Oak antes de usar os teletransportes de teste."))
      return
    end
    unless $scene && $scene.respond_to?(:transfer_player) && $game_temp && !$game_temp.in_battle
      pbMessage(BlueKantoPilot.t("Test travel is unavailable during battles.", "O transporte de teste não está disponível durante batalhas."))
      return
    end
    stops = experimental_stops
    if stops.empty?
      pbMessage(BlueKantoPilot.t("No experimental destination is available.", "Nenhum destino experimental foi preparado."))
      return
    end
    choice = pbMessage(BlueKantoPilot.t("Experimental test: Travel without finishing the previous story.", "Teste experimental: viajar sem concluir a história anterior."),
                       stops.map(&:first) + [BlueKantoPilot.t("Cancel", "Cancelar")], -1)
    return if !choice || choice < 0 || choice >= stops.length
    label, point = stops[choice]
    return unless pbConfirmMessage(BlueKantoPilot.t("Travel to {1}? This option is available only in the test pilot.", "Ir para {1}? Esta opção existe apenas no piloto de testes.", label))
    begin
      pbFadeOutIn { BlueRegionTravel.move_to(point) }
      pbMessage(BlueKantoPilot.t("Arrived at {1}. Keep playing and save under Kanto Piloto.", "Chegou a {1}. Continue jogando e salve no perfil Kanto Piloto.",label))
    rescue StandardError => e
      pbMessage(BlueKantoPilot.t("Failed to travel to test destination: {1}", "Falha no destino experimental: {1}",e.message))
    end
  end

  # The source Safari Gate is mapped for navigation, but the isolated
  # pilot must NOT start a fake Safari session: native catch rules, step
  # limits, Safari Balls and exit restoration have not been audited.
  # Both the gate's counter and its guide use this non-transactional message.
  def self.safari_preview
    pbMessage(BlueKantoPilot.t(
      "Safari Zone: The entrance for catching Pokémon is in development. No ticket, money or Safari Ball will be used in this version.",
      "Safari Zone: a entrada para captura está em preparação. Nenhum ingresso, dinheiro ou Safari Ball será consumido nesta versão."
    ))
  end

  # Local Pallet residents; never run the foreign FRLG quest scripts.
  def self.mom
    if $player && $player.party.any? { |pkmn| !pkmn.egg? }
      $player.heal_party
      BlueMusic.kanto_me_play("healed")
      pbMessage(BlueKantoPilot.t("Mom: Rest for a while before continuing your Kanto adventure.", "Mãe: Descanse um pouco antes de continuar sua aventura por Kanto."))
    else
      pbMessage(BlueKantoPilot.t("Mom: Your room is upstairs. Visit Oak at his lab afterward.", "Mãe: Seu quarto fica no andar de cima. Depois visite Oak no laboratório."))
    end
  end

  def self.daisy
    pbMessage(BlueKantoPilot.t("Daisy: Welcome to Gary's house! Oak's lab is south of Pallet.", "Daisy: Bem-vindo à casa do Gary! O laboratório de Oak fica ao sul de Pallet."))
  end

  def self.heal
    $player.heal_party
    pbSetPokemonCenter
    BlueMusic.kanto_me_play("healed")
    pbMessage(BlueKantoPilot.t("Your party is rested.", "Sua equipe está descansada."))
  end
end

# The Kanto-only markers ensure this global movement hook is inert on
# Decades, Johto, Hoenn and Sinnoh, even when those maps share a level cap.
module BlueKantoPilot::Route2ExitGuard
  def move_generic(dir, turn_enabled = true)
    if BlueKantoPilot.pewter_route3_blocked?(self, dir)
      turn_generic(dir, true) if turn_enabled
      key = [$game_map.map_id, x, y, :pewter_route3]
      if @blue_pewter_last_warning != key
        @blue_pewter_last_warning = key
        BlueKantoPilot.pewter_route3_warning
      end
      return
    end
    @blue_pewter_last_warning = nil
    if BlueKantoPilot.route2_exit_blocked?(self, dir)
      turn_generic(dir, true) if turn_enabled
      warning_key = [$game_map.map_id, x, y]
      if @blue_route2_last_warning != warning_key
        @blue_route2_last_warning = warning_key
        BlueKantoPilot.route2_gate_warning
      end
      return
    end
    @blue_route2_last_warning = nil
    super
  end
end
Game_Player.prepend(BlueKantoPilot::Route2ExitGuard)

# This menu is visible ONLY in the isolated pilot with its local stop manifest.
MenuHandlers.add(:pause_menu, :blue_kanto_experimental, {
  "name"=>BlueKantoPilot.t("Kanto Test Mode (experimental)", "Testes Kanto (experimental)"),
  "order"=>71,
  "condition"=>proc { |_menu| BlueKantoPilot.experimental? },
  "effect"=>proc do |menu|
    menu.pbHideMenu
    BlueKantoPilot.experimental_menu
    menu.pbShowMenu
    false
  end
})
