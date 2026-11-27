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
  # Gary's imported Oak Lab charset is the visual reference. Measure actual
  # non-transparent pixels rather than the padded height of the spritesheet.
  PILOT_OVERWORLD_SCALE = File.file?("Kanto pilot.json")
  INTEGRATED_KANTO = !PILOT_OVERWORLD_SCALE && File.file?("Data/blue-kanto-install.json")

  # User capture (build 1606): NPC 80px, player 62px, feet aligned.
  # The target is the actual NPC height, not 1.29 multiplied a second time
  # after normalization. This also works at different screen zoom levels.
  def self.overworld_frame_bounds(bitmap, x, y, width, height)
    return nil unless bitmap && width.to_i > 0 && height.to_i > 0 &&
      x >= 0 && y >= 0 && x+width <= bitmap.width && y+height <= bitmap.height
    top = nil
    bottom = nil
    height.times do |row|
      next unless width.times.any? { |column| bitmap.get_pixel(x+column,y+row).alpha > 0 }
      top ||= row
      bottom = row
    end
    top ? [top,bottom] : nil
  end

  # Measure all frames for the NPC reference. The player itself uses the
  # active source rectangle: real Red frames vary from 46 to 50 opaque pixels.
  def self.overworld_visible_height(bitmap, frame_width, frame_height)
    return nil unless bitmap && frame_width.to_i > 0 && frame_height.to_i > 0
    return nil unless bitmap.respond_to?(:get_pixel) &&
      bitmap.width == frame_width * 4 && bitmap.height == frame_height * 4
    tallest = 0
    4.times do |row|
      4.times do |column|
        bounds = overworld_frame_bounds(bitmap,column*frame_width,row*frame_height,
          frame_width,frame_height)
        tallest = [tallest, bounds[1]-bounds[0]+1].max if bounds
      end
    end
    tallest > 0 ? tallest : nil
  end

  def self.gary_overworld_height
    name = cerulean_rival_graphic
    return nil unless name && respond_to?(:cerulean_rival_graphic)
    @gary_overworld_heights ||= {}
    return @gary_overworld_heights[name] if @gary_overworld_heights.key?(name)
    path = pbResolveBitmap("Graphics/Characters/#{name}")
    return nil unless path
    reference = Bitmap.new(path)
    height = overworld_visible_height(reference, reference.width / 4, reference.height / 4)
    @gary_overworld_heights[name] = height if height
    height
  rescue StandardError
    nil
  ensure
    reference.dispose if reference && !reference.disposed?
  end

  def self.player_overworld_zoom(visible_height, reference_height = gary_overworld_height)
    return 1.0 unless visible_height.is_a?(Numeric) && visible_height > 0 &&
      reference_height.is_a?(Numeric) && reference_height > 0
    reference_height.to_f / visible_height
  end

  # Shared runtime is active ONLY while the current regional save is in Kanto.
  # Never apply Kanto-specific field rules to Decades maps or other regions.
  def self.kanto_current?
    # Standalone pilot has no Decades maps. Keep its native Cut sprite
    # handling available while the pilot marker exists (including map load).
    return true if PILOT_OVERWORLD_SCALE && File.file?("Kanto pilot.json")
    return false unless INTEGRATED_KANTO
    state = $PokemonGlobal && $PokemonGlobal.respond_to?(:blue_regions) &&
            $PokemonGlobal.blue_regions
    state.is_a?(Hash) && state["current"] == "KANTO"
  end
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

  # Removes only old source font/color overrides from imported FRLG NPC text.
  # Do not alter the underlying localization catalog, other regions, or signs'
  # window skins; this runs only when the isolated Kanto NPC bridge is called.
  def self.cut_tree_obstacle?(event)
    kanto_current? && event && event.respond_to?(:name) &&
      event.name.to_s.match?(/cut[ _-]*tree|cuttable[ _-]*tree/i)
  end

  # Correct the pilot's map-name announcement without changing map IDs,
  # the FRLG source atlas or the official names in the English-language PBS.
  # The generated Kanto pilot.json maps source FRLG Map010 to the stable Blue ID.
  def self.viridian_map_id
    return nil unless PILOT_OVERWORLD_SCALE || INTEGRATED_KANTO
    @viridian_map_id ||= begin
      path = PILOT_OVERWORLD_SCALE ? "Kanto pilot.json" : "Data/blue-kanto-install.json"
      match = File.read(path).match(/"10"\s*:\s*(\d+)/)
      match ? match[1].to_i : nil
    end
  rescue IOError, SystemCallError
    nil
  end

  # Resolve the immutable source MapID through the installed Kanto mapping.
  # No numeric assumptions about the allocated Decades map range.
  def self.kanto_map_id(source_id)
    return nil unless PILOT_OVERWORLD_SCALE || INTEGRATED_KANTO
    path = PILOT_OVERWORLD_SCALE ? "Kanto pilot.json" : "Data/blue-kanto-install.json"
    return nil unless File.file?(path)
    found = File.read(path).match(/"#{source_id}"\s*:\s*(\d+)/)
    found ? found[1].to_i : nil
  rescue IOError, SystemCallError
    nil
  end

  def self.viridian_display_name_for_map(map_id)
    return nil unless kanto_current? && viridian_map_id == map_id
    defined?(BlueLocale) && BlueLocale.enabled? ? "Cidade de Viridian" : "Viridian City"
  end

  def self.standard_npc_text(message)
    message.gsub(/\\(?:fn|fs|font|c)\[[^\]]*\]/i, "").gsub(/\\[br]/i, "")
  end

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
    # Blue/Decades uses readable white dialogue text by default. FRLG\b and
    # FRLG\r force blue/red letters with pale outlines on the dark textbox.
    # Keep sign skins (\\w[signskin]), pauses, newlines and substitutions.
    pbMessage(standard_npc_text(translated))
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

  # Route 5 Day Care: one slot, using the native Essentials transactions.
  def self.daycare_active?
    kanto_current? && $game_map && $game_map.map_id == kanto_map_id(58) &&
      defined?(DayCare) && $PokemonGlobal.respond_to?(:day_care)
  end

  def self.daycare_deposit(index)
    return false unless daycare_active? && index.is_a?(Integer) &&
      index >= 0 && index < $player.party.length
    care = $PokemonGlobal.day_care
    return false unless care && care.count == 0
    pokemon = $player.party[index]
    return false if !pokemon || pokemon.egg? || pokemon.cannot_store
    return false unless $player.party.each_with_index.any? { |p,i|
      i != index && !p.egg? && !p.fainted? }
    DayCare.deposit(index)
    true
  end

  def self.daycare_withdraw
    return false unless daycare_active?
    care = $PokemonGlobal.day_care
    index = care.slots.index { |slot| slot.filled? }
    return false unless index && !$player.party_full?
    cost = care[index].cost
    return false unless cost.is_a?(Integer) && cost >= 0 && $player.money >= cost
    DayCare.withdraw(index)
    $player.money -= cost
    true
  end

  def self.daycare_menu
    return false unless daycare_active?
    care = $PokemonGlobal.day_care
    if care.count == 0
      commands = $player.party.map { |p| t("{1} Lv.{2}", "{1} Nv.{2}",p.name,p.level) }
      commands << t("Cancel","Cancelar")
      choice = pbMessage(t("Day Care: Which Pokémon should I look after?",
        "Creche: De qual Pokémon devo cuidar?"),commands,commands.length)
      return false unless choice.is_a?(Integer) && choice >= 0 && choice < commands.length-1
      unless daycare_deposit(choice)
        pbMessage(t("Keep at least one Pokémon able to battle. Eggs cannot be deposited here.",
          "Mantenha pelo menos um Pokémon capaz de batalhar. Ovos não podem ficar aqui."))
        return false
      end
      pbMessage(t("I'll take good care of your Pokémon. Come back later!",
        "Vou cuidar bem do seu Pokémon. Volte mais tarde!"))
      return true
    end
    slot = care.slots.find { |entry| entry.filled? }
    return false unless slot
    return false unless pbConfirmMessage(t(
      "{1} gained {2} level(s). Take it back for $ {3}?",
      "{1} ganhou {2} nível(is). Quer retirá-lo por $ {3}?",
      slot.pokemon.name,slot.level_gain,slot.cost))
    unless daycare_withdraw
      pbMessage(t("You need room in your party and enough money.",
        "Você precisa de espaço na equipe e dinheiro suficiente."))
      return false
    end
    pbMessage(t("Take good care of your Pokémon!", "Cuide bem do seu Pokémon!"))
    true
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
  # the active Kanto campaign. Old Boulder+ saves lacking the parcel flag can
  # still collect and deliver it; do not permanently lock their Mart.
  def self.parcel_pickup_pending?
    starter && !progress["pilot_oak_parcel_received"] &&
      !progress["pilot_oak_parcel_delivered"]
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
    # Kanto's first Viridian visit gives Oak's parcel, but never sells
    # items until Oak has actually received it. The dialogue alone must
    # not fall through to pbPokemonMart (including on older saved games).
    if parcel_pickup_pending?
      # Recovery for existing saves where the shop's autorun was skipped.
      receive_oak_parcel
      return false
    end
    unless progress["pilot_oak_parcel_delivered"] == true
      pbMessage(BlueKantoPilot.t(
        "Clerk: Please deliver the package to Professor Oak in Pallet before shopping.",
        "Funcionário: Primeiro entregue o pacote ao professor Oak, em Pallet, para liberar as compras."
      ))
      return false
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

  # The old gate was on y=0, far beyond Viridian's sleeping old man.
  # The pilot builder now records the five-tile walkway line marked in the
  # screenshot, relative to source Map010's northern house doorway.
  def self.viridian_route2_line
    return nil unless kanto_current?
    @viridian_route2_line ||= begin
      path = "Data/blue-kanto-viridian-route2-line.txt"
      if File.file?(path)
        parts = File.read(path).strip.split("|")
        values = parts.length == 4 ? parts.map { |value| Integer(value, 10) } : []
        values if values.length == 4 && values[0] > 0 && values[1] > 0 &&
                  values[2] >= 0 && values[3] > values[2]
      end
    end
  rescue IOError, SystemCallError, ArgumentError
    nil
  end

  # Old Kanto saves can retain the original north-edge RPG::Event objects
  # after the build replaces Map010. Erase ONLY those obsolete event markers.
  # Don't touch story NPCs, maps from other regions or any quest flags.
  def self.clear_legacy_viridian_route2_gates
    line = viridian_route2_line
    return unless line && $game_map && $game_map.map_id == line[0]
    $game_map.events.each_value do |event|
      next unless event.name == "Kanto Viridian Route 2 Parcel Gate"
      next if event.instance_variable_get(:@erased)
      event.erase
    end
  end

  def self.route2_exit_blocked?(player, direction)
    return false unless player && $game_map
    line = viridian_route2_line
    return false unless line && $game_map.map_id == line[0]
    clear_legacy_viridian_route2_gates
    return false unless direction == 8 && !forest_unlocked?
    _map, row, first, last = line
    player.y == row + 1 && player.x >= first && player.x < last
  end

  # Exact, source-grounded Pewter east boundary compiled by pilot.py.
  # Only the first Kanto Boulder Badge may open Route 3; crystals earned in
  # other regions do not unlock it. No second foreign-story switch is needed.
  # Match the exact verified east border of Pewter (Map025) towards
  # Route 3 (Map032). Same coordinates as the existing Brock gate.
  def self.pewter_route3_crossing?(player, direction)
    return false unless player && $game_map && direction == 6
    gate = "Data/blue-kanto-pewter-route3-gate.txt"
    return false unless File.file?(gate)
    @pewter_route3_edge ||= begin
      pieces = File.read(gate).strip.split("|")
      pieces.length == 4 ? pieces.map { |value| Integer(value, 10) } : []
    end
    map_id, width, first, last = @pewter_route3_edge
    return false unless map_id && width && first && last
    $game_map.map_id == map_id && player.x >= width - 1 &&
      player.y >= first && player.y < last
  rescue IOError, SystemCallError, ArgumentError
    false
  end

  def self.pewter_route3_blocked?(player, direction)
    pewter_route3_crossing?(player, direction) &&
      !BlueRegions.local_achievements(progress, "KANTO").include?("BOULDER")
  end

  # Running Shoes are a native Player ability, not an HM or Bag item.
  # Mom hands them over on the FIRST successful journey through the
  # Brock-unlocked Pewter -> Route 3 passage; not at the gym or in Decades.
  def self.mom_running_shoes_at_route3
    return false unless kanto_current?
    return false unless $player && $PokemonSystem && progress["current"] == "KANTO"
    return false unless BlueRegions.local_achievements(progress, "KANTO").include?("BOULDER")
    return false if progress["pilot_mom_running_shoes"] == true
    return false unless $player.respond_to?(:has_running_shoes=) &&
                        $PokemonSystem.respond_to?(:runstyle=)
    # Display the actual Pallet mother in front of the player for this
    # scene only. The authored Pewter event is otherwise fully invisible
    # and passable; no event refresh/prepend is needed (save-safe).
    mother_event = nil
    if $game_map && $game_map.respond_to?(:events) &&
       File.file?("Data/blue-kanto-pewter-mom-sprite.txt")
      mother_event = $game_map.events.values.find { |ev|
        ev.name == "Kanto Running Shoes Mom"
      }
      sprite = File.read("Data/blue-kanto-pewter-mom-sprite.txt").strip
      if mother_event && sprite.start_with?("FRLG_Pilot_") &&
         mother_event.respond_to?(:character_name=)
        mother_event.moveto([$game_player.x - 1, 0].max, $game_player.y) if
          $game_player && mother_event.respond_to?(:moveto)
        mother_event.direction = 6 if mother_event.respond_to?(:direction=)
        mother_event.character_name = sprite
      end
    end
    begin
      pbMessage(t("Mom: {1}! I caught up with you at the Route 3 exit. Congratulations on beating Brock!",
                  "Mãe: {1}! Alcancei você na saída para a Rota 3. Parabéns por vencer o Brock!", $player.name))
      pbMessage(t("Mom: I brought you these Running Shoes. Now you can run on your journey!",
                  "Mãe: Trouxe estes Tênis de Corrida para você. Agora pode correr durante sua jornada!"))
      $player.has_running_shoes = true
      $PokemonSystem.runstyle = 1  # Native Essentials default: run without holding a key.
      progress["pilot_mom_running_shoes"] = true  # Stored on the Kanto regional save.
      BlueMusic.kanto_me_play("obtained_item") if defined?(BlueMusic)
      pbMessage(t("You received the Running Shoes! You'll run automatically from now on.",
                  "Você recebeu os Tênis de Corrida! A partir de agora, correrá automaticamente."))
      true
    ensure
      # The mother is a one-shot scene, not a permanent passage obstruction.
      mother_event.character_name = "" if mother_event &&
                                       mother_event.respond_to?(:character_name=)
    end
  end

  def self.pewter_route3_warning
    if BlueRegions.local_achievements(progress, "KANTO").include?("BOULDER")
      pbMessage(t("Pewter Guard: You have the Boulder Badge. Route 3 is open!", "Guarda de Pewter: você tem a Boulder Badge. A Rota 3 está liberada!"))
    else
      pbMessage(t("Pewter Guard: Defeat Brock and earn the Boulder Badge before heading to Route 3.",
                  "Guarda de Pewter: derrote Brock e conquiste a Boulder Badge antes de seguir para a Rota 3."))
    end
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

  # Compiled Kanto trainer PBS can be absent/stale in an existing Decades
  # installation even when the integrated maps are already present. Recover
  # ONLY the three author-verified Oak Lab rival variants, directly from the
  # installed PBS; never invent a team or modify Decades trainer profiles.
  # The native Essentials compiler remains the canonical permanent source.
  def self.ensure_lab_rival_trainer(version)
    type = :BLUE_KANTO_RIVAL
    return false unless [11, 12, 13].include?(version)
    return false unless defined?(GameData::Trainer) &&
                        defined?(GameData::TrainerType)
    return true if GameData::Trainer.exists?(type, "Blue", version)
    return false unless GameData::TrainerType.exists?(type)
    path = "PBS/trainers_kanto.txt"
    return false unless File.file?(path)
    target = "[BLUE_KANTO_RIVAL,Blue,#{version}]"
    selected = nil
    File.foreach(path, encoding: "UTF-8") do |line|
      stripped = line.strip
      if stripped.start_with?("[") && stripped.end_with?("]")
        if stripped == target
          return false if selected
          selected = []
        elsif selected
          break
        end
      elsif selected && !stripped.empty? && !stripped.start_with?("#")
        selected << stripped
      end
    end
    return false if !selected || selected.empty?
    pokemon = []
    lose_text = nil
    selected.each do |line|
      field, separator, raw = line.partition("=")
      return false if separator.empty?
      field = field.strip
      values = raw.split(",").map(&:strip)
      case field
      when "Pokemon"
        return false unless values.length == 2 && values[1].match?(/\A\d+\z/)
        level = values[1].to_i
        return false unless (1..100).cover?(level) &&
                            GameData::Species.exists?(values[0].to_sym)
        pokemon << {species: values[0].to_sym, level: level}
      when "Moves"
        return false if pokemon.empty? || values.empty? || values.any? { |id| id.empty? || !GameData::Move.exists?(id.to_sym) }
        pokemon[-1][:moves] = values.map(&:to_sym)
      when "Item"
        return false if pokemon.empty? || values.length != 1 ||
                        !GameData::Item.exists?(values[0].to_sym)
        pokemon[-1][:item] = values[0].to_sym
      when "LoseText"
        lose_text = raw.strip
      else
        return false  # No extra unreviewed PBS trainer properties.
      end
    end
    return false unless (1..6).cover?(pokemon.length)
    GameData::Trainer.register(
      id: [type, "Blue", version], trainer_type: type, real_name: "Blue",
      version: version, pokemon: pokemon, real_lose_text: lose_text
    )
    # Recompile from the normal, complete PBS set at the NEXT launcher start.
    begin
      File.write("Data/blue-compile-request.txt", "compile")
    rescue IOError, SystemCallError
    end
    GameData::Trainer.exists?(type, "Blue", version)
  rescue StandardError => error
    log_rival_failure(error, version, "prepare")
    false
  end

  def self.log_rival_failure(error, version, phase)
    # Essentials normally collapses an event exception into EventScriptError.
    # Keep the real cause/backtrace available without touching the save.
    begin
      details = [
        "KANTO_OAK_LAB_RIVAL",
        "phase=#{phase} version=#{version}",
        "#{error.class}: #{error.message}",
        *Array(error.backtrace).first(18),
        ""
      ].join("\n")
      File.open("Data/blue-kanto-rival-error.log", "a") { |log| log.write(details) }
    rescue StandardError
      # Logging is optional and must not cause another EventScriptError.
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
    version = RIVAL_VERSIONS.fetch(starter)
    announced = false
    begin
      BlueMusic.with_kanto_scene("rival_appears") do
        pbMessage(BlueKantoPilot.t("Gary: Hey, {1}! Before you go, let's test our Pokémon!", "Gary: Ei, {1}! Antes de ir, vamos testar nossos Pokémon!", $player.name))
        announced = true
      end
    rescue StandardError => error
      # A missing/corrupt optional Kanto rival BGM must NOT prevent Gary's
      # first mandatory battle. Keep the original exception for diagnosis.
      log_rival_failure(error, version, "intro_audio")
      unless announced
        pbMessage(BlueKantoPilot.t("Gary: Let's test our Pokémon!", "Gary: Vamos testar nossos Pokémon!"))
      end
    end
    unless ensure_lab_rival_trainer(version)
      pbMessage(BlueKantoPilot.t(
        "Gary: My battle team wasn't loaded. Reopen Blue-Story.exe to repair Kanto's battle data. Your progress is safe.",
        "Gary: Meu time não foi carregado. Abra novamente o Blue-Story.exe para reparar os dados da batalha de Kanto. Seu progresso está seguro."
      ))
      return false
    end
    begin
      setBattleRule("cannotLose")
      result = TrainerBattle.start(:BLUE_KANTO_RIVAL, "Blue", version)
    rescue StandardError => error
      log_rival_failure(error, version, "battle")
      $game_temp.clear_battle_rules if $game_temp && $game_temp.respond_to?(:clear_battle_rules)
      # Generic error messages concealed the REAL native failure and caused
      # repeated blind downloads. Show the exception type and first message
      # line in-game so a screenshot alone can diagnose the root cause.
      detail = "#{error.class}: #{error.message.to_s.lines.first.to_s.strip}"
      detail = detail.gsub(/[[:cntrl:]]/, " ")[0, 175]
      pbMessage(BlueKantoPilot.t(
        "Gary: The battle could not start ({1}). Your save is preserved. Send the error and Data/blue-kanto-rival-error.log.",
        "Gary: A batalha não iniciou ({1}). Seu save está preservado. Envie o erro e Data/blue-kanto-rival-error.log.",
        detail
      ))
      return false
    end
    # Native Essentials blacks out and transfers to the last healing center
    # when defeated. Never mark the tutorial rival as finished on a loss.
    return false unless result
    $player.heal_party  # Preserve the original tutorial victory recovery only.
    progress["pilot_rival"] = true
    pbMessage(BlueKantoPilot.t("Gary: You won. I'll train for our rematch!", "Gary: Você venceu. Vou treinar para a revanche!"))
    true
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
    setBattleRule("cannotLose")
    won = BlueStory.with_regional_full_power {
      TrainerBattle.start(type, name, FULL_POWER_OFFSET)
    }
    if won
      victories = (progress["pilot_full_power_gym_wins"] ||= [])
      victories << name unless victories.include?(name)
      pbMessage(BlueKantoPilot.t("You won {1}'s Full Power rematch!", "Você venceu a revanche Full Power de {1}!", name))
    end
    true
  end

  # Keep the original exception, map and event identity when a native
  # Kanto TrainerBattle raises an EventScriptError in JoiPlay. Never grant a
  # victory, change a self-switch or touch save data on a failed battle.
  def self.log_trainer_failure(error, type, name, event_key, version, phase)
    begin
      map_id = $game_map && $game_map.respond_to?(:map_id) ? $game_map.map_id : "unknown"
      details = [
        "KANTO_TRAINER_ERROR",
        "phase=#{phase} map=#{map_id} event=#{event_key} type=#{type} name=#{name.inspect} version=#{version}",
        "#{error.class}: #{error.message}",
        *Array(error.backtrace).first(20),
        ""
      ].join("\n")
      File.open("Data/blue-kanto-trainer-error.log", "a") { |file| file.write(details) }
    rescue StandardError
      # Read-only diagnostics must never generate another event exception.
    end
  end

  # Route-independent shim for the two source-grounded Cerulean Gym trainers.
  # Their optional alert/introduction cannot block the essential battle on
  # JoiPlay. This is used by newly compiled Map042 events, not by other maps.
  def self.cerulean_gym_trainer(type, name, event_key, event_id)
    begin
      pbTrainerIntro(type) if respond_to?(:pbTrainerIntro, true)
      event = $game_map && $game_map.respond_to?(:events) ? $game_map.events[event_id] : nil
      pbNoticePlayer(event) if event && respond_to?(:pbNoticePlayer, true)
    rescue StandardError => error
      log_trainer_failure(error, type, name, event_key, 0, "intro")
    end
    result = battle(type, name, event_key)
    begin
      sync_trainer_event(event_key, name, event_id)
    rescue StandardError => error
      log_trainer_failure(error, type, name, event_key, 0, "self_switch")
    end
    begin
      pbTrainerEnd if respond_to?(:pbTrainerEnd, true)
    rescue StandardError => error
      log_trainer_failure(error, type, name, event_key, 0, "outro")
    end
    # The legacy battle callback returns nil for ordinary trainer victories;
    # its persistent, map/event-scoped victory key is the authoritative result.
    progress.fetch("pilot_wins", []).include?(event_key)
  end

  CERULEAN_RIVAL_KEY = "KANTO_CERULEAN_RIVAL".freeze
  CERULEAN_RIVAL_LANES = [22, 23, 24].freeze
  CERULEAN_RIVAL_ROW = 6
  CERULEAN_RIVAL_ACTOR = 32

  def self.cerulean_rival_map?(map_id)
    return false unless kanto_current?
    id = (@cerulean_rival_map_id ||= kanto_map_id(39))
    id && map_id == id
  end

  def self.cerulean_rival_pending?
    RIVAL_VERSIONS.key?(starter) &&
      !progress["pilot_cerulean_rival"] &&
      !progress.fetch("pilot_wins", []).include?(CERULEAN_RIVAL_KEY)
  end

  # The old import emitted three transparent Event Touch markers. A player
  # could pass their line without any visible Gary or a native event start.
  # Use the already-audited Map039 line in the player movement path as well.
  # This repairs old RXDATA and loaded saves without rewriting any map.
  def self.cerulean_rival_crossing?(player, direction)
    return false unless player && $game_map &&
      cerulean_rival_map?($game_map.map_id) && cerulean_rival_pending?
    return false if player.respond_to?(:move_route_forcing) && player.move_route_forcing
    dx = {4=>-1, 6=>1}.fetch(direction, 0)
    dy = {2=>1, 8=>-1}.fetch(direction, 0)
    return false if dx == 0 && dy == 0
    # Also recover a save made on the trigger row before this patch.
    (player.y + dy == CERULEAN_RIVAL_ROW &&
      CERULEAN_RIVAL_LANES.include?(player.x + dx)) ||
      (player.y == CERULEAN_RIVAL_ROW &&
        CERULEAN_RIVAL_LANES.include?(player.x))
  end

  # Reuse Gary's actual, already-imported Oak Lab charset. Do not invent a
  # donor sprite filename or introduce a second character/foreign switch.
  # Native RXDATA lookup is read-only, and the source ID is remapped.
  def self.cerulean_rival_graphic
    return @cerulean_rival_graphic if @cerulean_rival_graphic
    lab_id = kanto_map_id(6)
    return nil unless lab_id
    lab = load_data(sprintf("Data/Map%03d.rxdata", lab_id))
    actor = lab.events[14]
    return nil unless actor
    name = actor.pages.map { |page| page.graphic.character_name }.find do |value|
      value.is_a?(String) && !value.empty?
    end
    @cerulean_rival_graphic = name if name
  rescue StandardError
    nil
  end

  # FRLG Map039 has three northbound touch tiles, not one event on Route24.
  # The separate key prevents Oak Lab's first Gary battle from suppressing
  # this encounter, and persists across all three entrance lanes.
  def self.cerulean_rival
    return false unless kanto_current? && RIVAL_VERSIONS.key?(starter)
    key = CERULEAN_RIVAL_KEY
    # A persisted exact win is proof even if an older scene stopped before
    # setting its completion flag. A generic legacy "Blue" win is not.
    progress["pilot_cerulean_rival"] = true if progress.fetch("pilot_wins", []).include?(key)
    unless progress["pilot_cerulean_rival"]
      version = RIVAL_VERSIONS.fetch(starter) + 20
      pbMessage(t("Gary: Hey! Let's see the Pokémon you've caught since Pallet!",
                  "Gary: Ei! Quero ver os Pokémon que você capturou desde Pallet!"))
      return false unless battle(:BLUE_KANTO_RIVAL, "Blue", key, version)
      return false unless progress.fetch("pilot_wins", []).include?(key)
      progress["pilot_cerulean_rival"] = true
      pbMessage(t("Gary: I'm going to see Bill! See you around!",
                  "Gary: Vou visitar o Bill! Até mais!"))
    end
    [15, 32, 34].each do |event_id|
      next unless $game_map && $game_map.events[event_id]
      index = [$game_map.map_id, event_id, "A"]
      $game_self_switches[index] = true
    end
    $game_map.need_refresh = true if $game_map
    true
  end

  def self.bill_request
    return unless kanto_current?
    if progress["pilot_bill_helped"]
      pbMessage(t("Bill: Thanks for helping with the teleporter!",
                  "Bill: Obrigado por me ajudar com o teletransportador!"))
      return
    end
    pbMessage(t("Bill: I had a Pokémon experiment go wrong. Please help me!",
                "Bill: Meu experimento Pokémon deu errado. Pode me ajudar?"))
    if !defined?(pbConfirmMessage) || pbConfirmMessage(t(
      "Will you operate the Cell Separator on my PC?",
      "Você pode operar o separador de células no meu PC?"))
      progress["pilot_bill_agreed"] = true
      pbMessage(t("Bill: Please use the PC to restore me.",
                  "Bill: Use o computador para me restaurar."))
    end
  end

  def self.bill_computer
    return false unless kanto_current?
    if progress["pilot_bill_helped"]
      pbMessage(t("Bill's Cell Separator is ready.", "O separador de células do Bill está pronto."))
      return true
    end
    unless progress["pilot_bill_agreed"]
      pbMessage(t("The Cell Separator is locked. Talk to Bill first.",
                  "O separador de células está bloqueado. Converse com Bill primeiro."))
      return false
    end
    # No foreign switches 87 or event scripts are executed.
    progress["pilot_bill_helped"] = true
    sync_cerulean_quest_pages(kanto_map_id(39))
    map_id = $game_map.map_id
    [3, 4, 8].each do |event_id|
      next unless $game_map.events[event_id]
      $game_self_switches[[map_id, event_id, "A"]] = true
    end
    $game_map.need_refresh = true
    pbMessage(t("The Cell Separator worked! Bill is back to normal.",
                "O separador funcionou! Bill voltou à forma normal."))
    true
  end

  # Namespaced native Key Item avoids collisions with another region's PBS.
  # Keep recognizing the older unnamespaced ID if a legacy game provided it.
  BILL_TICKET_IDS = [:BLUE_KANTO_SSTICKET, :SSTICKET].freeze

  def self.bill_ticket_item
    return nil unless defined?(GameData::Item)
    BILL_TICKET_IDS.find { |id| GameData::Item.exists?(id) }
  end

  def self.bill_ticket_in_bag?
    return false unless defined?(GameData::Item) && $bag
    BILL_TICKET_IDS.any? { |id| GameData::Item.exists?(id) && $bag.has?(id) }
  end

  def self.bill_ticket_owned?
    return true if bill_ticket_in_bag?
    # A legacy native ticket may already be stored in Kanto's item PC.
    # Never duplicate it. Regional travel stores and restores that PC.
    pc = $PokemonGlobal.respond_to?(:pcItemStorage) ? $PokemonGlobal.pcItemStorage : nil
    pc && pc.respond_to?(:items) && pc.items.any? { |entry|
      entry.is_a?(Array) && BILL_TICKET_IDS.include?(entry[0]) && entry[1].to_i > 0
    }
  end

  def self.bill_reward
    return false unless kanto_current?
    unless progress["pilot_bill_helped"]
      pbMessage(t("Talk to Bill and operate the PC first.",
                  "Converse com Bill e opere o computador primeiro."))
      return false
    end
    already_permitted = progress["pilot_bill_ticket"] || progress["pilot_ss_ticket"]
    if progress["pilot_bill_ticket_item_granted"] || bill_ticket_owned?
      progress["pilot_bill_ticket_item_granted"] = true
      progress["pilot_bill_ticket"] = true
      progress["pilot_ss_ticket"] = true
      pbMessage(t("Bill: Have fun aboard the S.S. Anne!",
                  "Bill: Divirta-se a bordo do S.S. Anne!"))
      return true
    end
    item = bill_ticket_item
    unless item
      # Compatibility with an old runtime/data pair. The delivery gate
      # requires the native item for all newly published Kanto packages.
      progress["pilot_bill_ticket"] = true
      progress["pilot_ss_ticket"] = true
      pbMessage(t("Bill: Your digital S.S. Anne boarding pass is ready!",
                  "Bill: Sua passagem digital para o S.S. Anne está pronta!"))
      return true
    end
    unless $bag.add(item, 1)
      pbMessage(t("Your Bag is full. Come back to receive Bill's S.S. Ticket.",
                  "Sua Bolsa está cheia. Volte para receber o S.S. Ticket do Bill."))
      # A previously issued permit stays valid, even if the physical
      # upgrade has to be retried after making space.
      return !!already_permitted
    end
    progress["pilot_bill_ticket_item_granted"] = true
    progress["pilot_bill_ticket"] = true
    progress["pilot_ss_ticket"] = true
    BlueMusic.kanto_me_play("obtained_item") if defined?(BlueMusic)
    pbMessage(t("Bill: Thanks for helping! Take this S.S. Ticket for Vermilion.",
                "Bill: Obrigado pela ajuda! Leve este S.S. Ticket para Vermilion."))
    true
  end

  # Source Map053 Event006: reward precedes the sixth battle. Recording the
  # item independently prevents defeat/retry from duplicating Nuggets.
  # K02-C: keep donor switch 87/88 out of the shared save. Bill's
  # verified local quest unlocks the original front and rear doors.
  CERULEAN_ROCKET_KEY = "KANTO_039_026".freeze
  def self.cerulean_house_open?
    kanto_current? && !!progress["pilot_bill_helped"]
  end

  def self.cerulean_house_entry?
    return true if cerulean_house_open?
    pbMessage(t("The police are investigating. Help Bill first.",
                "A polícia está investigando. Ajude Bill primeiro.")) if kanto_current?
    false
  end

  def self.cerulean_police
    return unless kanto_current?
    pbMessage(t("Team Rocket robbed this house. We are investigating.",
                "A Equipe Rocket roubou esta casa. Estamos investigando."))
  end

  def self.cerulean_house_owner
    return unless kanto_current?
    if progress["pilot_cerulean_dig_awarded"]
      pbMessage(t("I decided to teach Diglett Dig without a TM.",
                  "Decidi ensinar Dig ao Diglett sem uma TM."))
    else
      pbMessage(t("Team Rocket stole my Dig TM!", "A Equipe Rocket roubou minha TM Dig!"))
    end
  end

  # K02-C optional source events. Use local progress, never donor variables 1/2.
  def self.cerulean_trade_eligible?(pkmn)
    pkmn && pkmn.species == :POLIWHIRL && !pkmn.egg? &&
      !pkmn.shadowPokemon? && !pkmn.cannot_trade
  end

  def self.cerulean_trade_selected(index)
    return false unless kanto_current? && $game_map &&
      $game_map.map_id == kanto_map_id(46) && $player &&
      !progress["pilot_cerulean_jynx_trade"]
    return false unless index.is_a?(Integer) && index.between?(0,$player.party.length-1)
    offered = $player.party[index]
    return false unless cerulean_trade_eligible?(offered) && GameData::Species.exists?(:JYNX)
    received = Pokemon.new(:JYNX, offered.level)
    received.ability_index = 0
    received.nature = :MILD
    {HP:18, ATTACK:17, DEFENSE:18, SPECIAL_ATTACK:22, SPECIAL_DEFENSE:25, SPEED:21}.each do |stat,iv|
      received.iv[stat] = iv
    end
    received.calc_stats
    pbStartTrade(index, received, "Zynx", "Dontae", 0)
    return false unless $player.party[index].equal?(received)
    progress["pilot_cerulean_jynx_trade"] = true
    true
  end

  def self.cerulean_jynx_trade
    return false unless kanto_current? && $game_map && $game_map.map_id == kanto_map_id(46)
    if progress["pilot_cerulean_jynx_trade"]
      pbMessage(t("Has the Jynx I traded you grown stronger?", "A Jynx que troquei com você ficou mais forte?"))
      return false
    end
    return false unless pbConfirmMessage(t("Trade your Poliwhirl for my Jynx?",
                                            "Trocar seu Poliwhirl pela minha Jynx?"))
    index = -1
    pbFadeOutIn do
      scene = PokemonParty_Scene.new
      screen = PokemonPartyScreen.new(scene, $player.party)
      index = screen.pbChooseTradablePokemon(proc { |pkmn| cerulean_trade_eligible?(pkmn) })
    end
    return false unless cerulean_trade_selected(index)
    pbMessage(t("Thanks!", "Obrigado!"))
    true
  end

  def self.cerulean_badge_guide
    return false unless kanto_current? && $game_map && $game_map.map_id == kanto_map_id(44)
    badges = LEAGUE_REQUIRED_BADGES
    names = badges.map { |badge| badge.capitalize + " Badge" }
    pbMessage(t("Each local Badge earns one Emerald. Field moves require the local HM, Badge and a compatible Pokémon.",
                "Cada insígnia local concede uma esmeralda. HMs exigem o item, a insígnia local e um Pokémon compatível."))
    loop do
      index = pbMessage(t("Which Badge should I describe?", "Qual insígnia deseja consultar?"),
                        names + [t("Back", "Voltar")], names.length)
      break unless index.is_a?(Integer) && index.between?(0,names.length-1)
      obtained = BlueRegions.local_achievements(progress, "KANTO").include?(badges[index])
      pbMessage(t("{1}: {2}", "{1}: {2}", names[index],
                  obtained ? t("Earned in Kanto.", "Conquistada em Kanto.") :
                             t("Not yet earned in Kanto.", "Ainda não conquistada em Kanto.")))
    end
    true
  end

  KANTO_WALL_MAP = "Plugins/ZZZZZ Blue Kanto Pilot/KantoWallMap.png".freeze
  def self.cerulean_wall_map
    return false unless kanto_current? && $game_map &&
      [kanto_map_id(46),kanto_map_id(47)].include?($game_map.map_id)
    return false unless File.file?(KANTO_WALL_MAP)
    # Read-only atlas: native Decades map UI defaults to Beatha. No global
    # town-map registration, Fly destination or player movement is changed.
    pbFadeOutIn do
      viewport = Viewport.new(0,0,Graphics.width,Graphics.height)
      viewport.z = 99999
      sprite = Sprite.new(viewport)
      bitmap = Bitmap.new(KANTO_WALL_MAP)
      sprite.bitmap = bitmap
      zoom = [Graphics.width.to_f / bitmap.width, Graphics.height.to_f / bitmap.height].min
      sprite.zoom_x = sprite.zoom_y = zoom
      sprite.x = ((Graphics.width-bitmap.width*zoom)/2).round
      sprite.y = ((Graphics.height-bitmap.height*zoom)/2).round
      loop do
        Graphics.update
        Input.update
        break if Input.trigger?(Input::BACK) || Input.trigger?(Input::USE)
      end
    ensure
      sprite.dispose if sprite && !sprite.disposed?
      bitmap.dispose if bitmap && !bitmap.disposed?
      viewport.dispose if viewport && !viewport.disposed?
    end
    true
  end

  def self.cerulean_bike_exchange
    return false unless kanto_current? && $game_map &&
      $game_map.map_id == kanto_map_id(43) && $bag && defined?(GameData::Item)
    return false unless GameData::Item.exists?(:BIKEVOUCHER) &&
      GameData::Item.exists?(:BICYCLE)
    if progress["pilot_cerulean_bike_exchanged"] || $bag.has?(:BICYCLE)
      pbMessage(t("Enjoy your Bicycle!", "Aproveite sua bicicleta!"))
      return true
    end
    unless $bag.has?(:BIKEVOUCHER)
      pbMessage(t("Bring a Bike Voucher from the Pokémon Fan Club in Vermilion.",
                  "Traga um vale-bicicleta do Fã-Clube Pokémon de Vermilion."))
      return false
    end
    return false if $bag.respond_to?(:can_add?) && !$bag.can_add?(:BICYCLE, 1)
    return false unless $bag.remove(:BIKEVOUCHER, 1)
    unless $bag.add(:BICYCLE, 1)
      raise "Bike Voucher rollback failed" unless $bag.add(:BIKEVOUCHER, 1)
      return false
    end
    progress["pilot_cerulean_bike_exchanged"] = true
    pbMessage(t("You received a Bicycle!", "Você recebeu uma bicicleta!"))
    true
  end

  # All three original Rocket events use the same stable win and reward
  # keys. A full bag leaves a retriable reward, without replaying a battle.
  def self.cerulean_rocket
    return false unless cerulean_house_open? && $game_map &&
      $game_map.map_id == kanto_map_id(39)
    return true if progress["pilot_cerulean_dig_awarded"]
    return false unless $bag && defined?(GameData::Item) && GameData::Item.exists?(:TM28)
    return false unless GameData::Item.get(:TM28).move == :DIG
    return false unless progress.fetch("pilot_wins", []).include?(CERULEAN_ROCKET_KEY) ||
      battle(:BLUE_KANTO_ROCKET, "Grunt", CERULEAN_ROCKET_KEY, 6)
    unless $bag.add(:TM28, 1)
      pbMessage(t("Make room in your Bag for TM28.", "Libere espaço na Bolsa para a TM28."))
      return false
    end
    progress["pilot_cerulean_dig_awarded"] = true
    [26,37,38].each do |id|
      $game_self_switches[[$game_map.map_id,id,"A"]] = true
    end
    $game_map.need_refresh = true
    pbMessage(t("You recovered TM28!", "Você recuperou a TM28!"))
    true
  end

  def self.nugget_bridge_rocket
    return false unless kanto_current?
    (1..5).each do |eid|
      unless progress.fetch("pilot_wins", []).include?("KANTO_053_%03d" % eid)
        pbMessage(t("Defeat all five Nugget Bridge trainers first!",
                    "Derrote primeiro os cinco treinadores da Nugget Bridge!"))
        return false
      end
    end
    unless progress["pilot_nugget_bridge_awarded"]
      unless defined?(GameData::Item) && GameData::Item.exists?(:NUGGET) && $bag.add(:NUGGET, 1)
        pbMessage(t("You need room in your Bag to accept the Nugget.",
                    "Você precisa de espaço na Bolsa para receber a Nugget."))
        return false
      end
      progress["pilot_nugget_bridge_awarded"] = true
      pbMessage(t("You received a Nugget!", "Você recebeu uma Nugget!"))
    end
    key = "KANTO_053_006"
    return false unless battle(:BLUE_KANTO_ROCKET, "Grunt", key, 5)
    sync_trainer_event(key, "Grunt", 6)
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
    if wins.include?(key) || (key != CERULEAN_RIVAL_KEY && key != CERULEAN_ROCKET_KEY &&
        type != :BLUE_KANTO_LEADER_GIOVANNI && wins.include?(name))
      # Older saves may have Miguel defeated but still use his first page.
      # Both paths must offer the missing one-time prize.
      if key == "KANTO_038_019" && !progress["pilot_mt_moon_fossil"]
        choose_moon_fossil unless moon_fossil_props?
        return
      end
      return if full_power_gym(name, type)
      pbMessage(BlueKantoPilot.t("{1}: Good luck on your journey!", "{1}: Boa sorte na sua jornada!", name))
      return
    end
    if type == :BLUE_KANTO_RIVAL_SILPH && name == "Blue"
      BlueMusic.with_kanto_scene("rival_appears") do
        pbMessage(BlueKantoPilot.t("Blue: Let's see how much stronger you've grown since Pallet!", "Blue: Vamos ver como você ficou mais forte desde Pallet!"))
      end
    end
    # canLose suppresses Essentials' blackout and respawn. Kanto story
    # battles must use the engine's last Pokémon Center checkpoint.
    begin
      if defined?(GameData::Trainer) && GameData::Trainer.respond_to?(:exists?) &&
         !GameData::Trainer.exists?(type, name, version)
        raise "Compiled Kanto trainer is missing: #{type}/#{name}/#{version}"
      end
      setBattleRule("cannotLose")
      won = TrainerBattle.start(type, name, version)
    rescue StandardError => error
      log_trainer_failure(error, type, name, key, version, "battle")
      $game_temp.clear_battle_rules if $game_temp && $game_temp.respond_to?(:clear_battle_rules)
      detail = "#{error.class}: #{error.message.to_s.lines.first.to_s.strip}"
      detail = detail.gsub(/[[:cntrl:]]/, " ")[0, 175]
      pbMessage(BlueKantoPilot.t(
        "The Kanto trainer battle failed ({1}). No victory was recorded. See Data/blue-kanto-trainer-error.log.",
        "A batalha do treinador de Kanto falhou ({1}). Nenhuma vitória foi registrada. Veja Data/blue-kanto-trainer-error.log.",
        detail
      ))
      return false
    end
    return false unless won
    wins << key
    if key == "KANTO_038_019"
      pbMessage(t("Super Nerd Miguel: Fine! Pick only one of the two fossils.",
                  "Super Nerd Miguel: Tudo bem! Escolha apenas um dos dois fósseis."))
      # Old installations have no fossil objects in the RXDATA. Offer the same
      # one-time choice immediately rather than require a new game/map rewrite.
      choose_moon_fossil unless moon_fossil_props?
    end
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
    true
  end

  # Return a real victory to guarded story callbacks as well as persistent keys.
  # Defeat or a native exception exits before this line.
  # (A battle can already have awarded a leader badge above.)
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
    if name == "Miguel" && type == :BLUE_KANTO_SUPERNERD &&
       $game_map && $game_map.map_id == kanto_map_id(38)
      choose_moon_fossil unless progress["pilot_mt_moon_fossil"]
      return if progress["pilot_mt_moon_fossil"]
    end
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

  # Route25's real Bill quest now controls new tickets. Existing players
  # with an already issued regional pass keep it; no save flag is revoked.
  def self.ticketmaster
    return false unless kanto_current?
    unless BlueRegions.local_achievements(progress, "KANTO").include?("CASCADE")
      pbMessage(t("Harbor clerk: Earn the Cascade Badge in Cerulean first.",
                  "Porto: conquiste primeiro a Cascade Badge em Cerulean."))
      return false
    end
    if progress["pilot_ss_ticket"] || bill_ticket_in_bag?
      # Existing digital permits are upgraded on a return to Bill or at
      # the clerk, without ever invalidating a previously issued pass.
      bill_reward if progress["pilot_bill_helped"] && !progress["pilot_bill_ticket_item_granted"]
      progress["pilot_ss_ticket"] = true
      pbMessage(t("Harbor clerk: You're cleared to board the S.S. Anne!",
                  "Porto: sua passagem para o S.S. Anne está liberada!"))
      return true
    end
    unless progress["pilot_bill_helped"]
      pbMessage(t("Harbor clerk: Talk to Bill on Route 25 and help him first.",
                  "Porto: visite Bill na Rota 25 e ajude-o primeiro."))
      return false
    end
    # The original ticket was not redeemed yet; a full Bag can be retried.
    bill_reward
  end

  def self.harbor_gate(map_id, x, y)
    return false unless kanto_current?
    unless progress["pilot_ss_ticket"] || bill_ticket_in_bag?
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


  # Mt. Moon: one fossil, only AFTER the original Map038/Event019 battle.
  # Works for fresh RXDATA props and old installed maps (Miguel fallback).
  MOON_FOSSILS = {
    HELIXFOSSIL: :OMANYTE, DOMEFOSSIL: :KABUTO
  }.freeze
  CINNABAR_FOSSILS = MOON_FOSSILS.merge(OLDAMBER: :AERODACTYL).freeze

  def self.moon_fossil_props?
    $game_map && ["Kanto Helix Fossil", "Kanto Dome Fossil"].all? { |name|
      $game_map.events.values.any? { |ev| ev.name == name }
    }
  end

  def self.hide_moon_fossil_props
    return unless $game_map
    $game_map.events.each do |event_id, ev|
      next unless ["Kanto Helix Fossil", "Kanto Dome Fossil"].include?(ev.name)
      $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
    end
    $game_map.need_refresh = true
  end

  def self.choose_moon_fossil(requested = nil)
    return false unless kanto_current? && $game_map &&
                        $game_map.map_id == kanto_map_id(38)
    unless progress.fetch("pilot_wins", []).any? { |win|
      ["KANTO_038_019", "Miguel"].include?(win)
    }
      pbMessage(t("Defeat the researcher guarding the fossils first.",
                  "Derrote primeiro o pesquisador que guarda os fósseis."))
      return false
    end
    if progress["pilot_mt_moon_fossil"]
      hide_moon_fossil_props
      pbMessage(t("You already chose your Mt. Moon fossil. The other one must stay.",
                  "Você já escolheu seu fóssil do Mt. Moon. O outro deve ficar."))
      return false
    end
    if requested && !MOON_FOSSILS.key?(requested)
      return false
    end
    choice = requested
    unless choice
      names = [
        t("Helix Fossil (Omanyte)", "Fóssil Helix (Omanyte)"),
        t("Dome Fossil (Kabuto)", "Fóssil Dome (Kabuto)"),
        t("Cancel", "Cancelar")
      ]
      index = pbMessage(t("Choose only one fossil:", "Escolha apenas um fóssil:"),
                        names, -1)
      return false unless [0, 1].include?(index)
      choice = MOON_FOSSILS.keys[index]
    end
    label = GameData::Item.exists?(choice) ? GameData::Item.get(choice).name : choice.to_s
    return false unless pbConfirmMessage(t("Take the {1}? You cannot take the other.",
                                            "Pegar {1}? Não será possível pegar o outro.",
                                            label))
    unless GameData::Item.exists?(choice) &&
           (!$bag.respond_to?(:can_add?) || $bag.can_add?(choice, 1)) &&
           $bag.add(choice, 1)
      pbMessage(t("Make room in your Bag before taking a fossil.",
                  "Libere espaço na Bolsa antes de pegar um fóssil."))
      return false
    end
    progress["pilot_mt_moon_fossil"] = choice.to_s
    hide_moon_fossil_props
    BlueMusic.kanto_me_play("obtained_item")
    pbMessage(t("You received {1}! A scientist in Cinnabar can revive it.",
                "Você recebeu {1}! Um cientista em Cinnabar pode revivê-lo.", label))
    true
  end

  # The fossil laboratory is Kanto Map203 (not the Mansion or Gym).
  # Keep this command available in the laboratory pause menu on older saves
  # whose imported maps contain only the original safe interior doors.
  def self.in_cinnabar_lab?
    kanto_current? && $game_map && $game_map.map_id == kanto_map_id(203)
  end

  def self.revive_cinnabar_fossil
    return false unless in_cinnabar_lab?
    available = CINNABAR_FOSSILS.keys.select { |item|
      GameData::Item.exists?(item) && $bag && $bag.has?(item)
    }
    if available.empty?
      pbMessage(t("Cinnabar Lab: Bring a Helix Fossil, Dome Fossil or Old Amber.",
                  "Laboratório de Cinnabar: traga um Fóssil Helix, Fóssil Dome ou Âmbar Velho."))
      return false
    end
    labels = available.map { |item| GameData::Item.get(item).name }
    index = pbMessage(t("Which fossil should we revive?", "Qual fóssil deseja reviver?"),
                      labels + [t("Cancel", "Cancelar")], -1)
    return false unless index.is_a?(Integer) && index >= 0 && index < available.length
    item = available[index]
    species = CINNABAR_FOSSILS.fetch(item)
    unless GameData::Species.exists?(species)
      pbMessage(t("This fossil Pokémon is not registered in this game.",
                  "Este Pokémon fóssil ainda não está cadastrado no jogo."))
      return false
    end
    if $player.party.length >= 6
      pbMessage(t("Leave one free slot in your party before reviving a fossil.",
                  "Deixe uma vaga livre na equipe antes de reviver o fóssil."))
      return false
    end
    pokemon_name = GameData::Species.get(species).name
    return false unless pbConfirmMessage(t("Revive {1} into {2}?",
                                            "Reviver {1} em {2}?",
                                            GameData::Item.get(item).name, pokemon_name))
    return false unless $bag.remove(item, 1)
    begin
      unless pbAddPokemonSilent(species, 5)
        $bag.add(item, 1)
        pbMessage(t("Revival failed. Your fossil was returned.",
                    "A restauração falhou. Seu fóssil foi devolvido."))
        return false
      end
    rescue StandardError
      $bag.add(item, 1)
      raise
    end
    BlueMusic.kanto_me_play("obtained_pokemon")
    pbMessage(t("Cinnabar Lab restored {1}!", "O laboratório de Cinnabar restaurou {1}!",
                pokemon_name))
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

  SPIN_DIRECTIONS = [2, 4, 8, 6].freeze
  SPIN_TILES = {919 => 4, 927 => 6, 935 => 8, 943 => 2}.freeze
  SPIN_STOP_TILE = 951

  def self.viridian_spin(direction)
    return unless SPIN_DIRECTIONS.include?(direction)
    player = $game_player
    map = $game_map
    visited = {}
    loop do
      state = [player.x, player.y, direction]
      break if visited[state] || !player.can_move_in_direction?(direction, true)
      visited[state] = true
      player.move_generic(direction, false)
      break if [player.x, player.y] == state.first(2)
      # The interpreter owns input until the tile finishes the forced step.
      turns = SPIN_DIRECTIONS.rotate(SPIN_DIRECTIONS.index(direction))
      turns.each do |facing|
        player.turn_generic(facing, true)
        pbWait(0.035)
      end
      pbWait(0.02) while player.moving?
      break if $game_map != map
      tiles = [2, 1, 0].map { |layer| map.data[player.x, player.y, layer] }
      break if tiles.include?(SPIN_STOP_TILE)
      direction = tiles.filter_map { |tile| SPIN_TILES[tile] }.first || direction
    end
  end

  def self.league_badge_check(required, guard_id, barrier_id)
    unless required.between?(1, LEAGUE_REQUIRED_BADGES.length)
      return false
    end
    needed = LEAGUE_REQUIRED_BADGES.first(required)
    earned = BlueRegions.local_achievements(progress, "KANTO")
    missing = needed.reject { |badge| earned.include?(badge) }
    if missing.any?
      # Older pilots could leave a save standing on the blocking event after
      # coming back from Route 23. Move that exact position one step south.
      gate = $game_map.events[barrier_id]
      if required == 1 && barrier_id == 5 && gate &&
         [$game_player.x, $game_player.y] == [gate.x, gate.y]
        $game_player.moveto(gate.x, gate.y + 1)
        $game_player.turn_down
      end
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
    # This simplified puzzle is still an HM field action: no bypass via
    # a Ruby map event when the player lacks HM04 or an eligible Pokemon.
    return false unless BlueRegionalPolicy.field_allowed?(:STRENGTH)
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
    setBattleRule("cannotLose")
    setBattleRule("double")
    won = TrainerBattle.start(:BLUE_KANTO_COOLCOUPLE, "Ray & Tyra")
    return false unless won
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
    setBattleRule("cannotLose")
    full_power = progress["pilot_league_full_power"] == true
    version += FULL_POWER_OFFSET if full_power
    won = full_power ? BlueStory.with_regional_full_power {
      TrainerBattle.start(type, name, version)
    } : TrainerBattle.start(type, name, version)
    unless won
      # The engine has already blacked out at the last healing checkpoint.
      # Reset ONLY the current League attempt, never badges or story rewards.
      progress["pilot_league_full_power"] = false
      progress["pilot_league_active"] = false
      progress["pilot_league_wins"] = []
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

  def self.safari_guide
    pbMessage(t("The Safari Game costs $500. Explore four areas with 30 Safari Balls and a limit on steps.",
                "O jogo do Safari custa $500. Explore quatro áreas com 30 Safari Balls e um limite de passos."))
  end

  def self.safari_admission(destination)
    safari = pbSafariState
    charged = false
    if safari.inProgress?
      if safari.decision != 0
        safari.pbEnd
        pbMessage(t("Thanks for visiting the Safari Zone!", "Obrigado por visitar a Zona Safari!"))
        return
      end
    else
      return unless pbConfirmMessage(t("Enter the Safari Zone for $500?", "Entrar na Zona Safari por $500?"))
      if $player.money < 500
        pbMessage(t("You need $500 to enter.", "Você precisa de $500 para entrar."))
        return
      end
      if pbBoxesFull?
        pbMessage(t("Your Pokémon storage is full.", "O armazenamento de Pokémon está cheio."))
        return
      end
      $player.money -= 500
      charged = true
      safari.pbStart(30)
    end
    pbFadeOutIn { BlueRegionTravel.move_to([destination, 26, 31, 8]) }
  rescue StandardError
    if charged && $game_map.map_id != destination
      $player.money += 500
      safari.pbEnd
    end
    raise
  end

  def self.safari_teeth(event_id)
    return unless pbInSafari?
    unless progress["pilot_safari_teeth"]
      progress["pilot_safari_teeth"] = true
      pbMessage(t("You found the Safari Warden's Gold Teeth!",
                  "Você encontrou os Dentes de Ouro do Warden da Zona Safari!"))
    end
    $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
    $game_map.events[event_id].refresh
  end

  def self.safari_warden
    if progress["pilot_safari_strength"]
      pbMessage(t("Warden: Strength can move boulders outside battle.", "Warden: Strength move pedras pesadas fora de batalha."))
    elsif progress["pilot_safari_teeth"]
      pbMessage(t("Warden: You found my teeth! Please take this HM.", "Warden: Você encontrou meus dentes! Aceite este HM."))
      progress["pilot_safari_strength"] = true if pbReceiveItem(:HM04)
    else
      pbMessage(t("The Warden is missing his Gold Teeth. Look in the Safari Zone.",
                  "O Warden perdeu os Dentes de Ouro. Procure na Zona Safari."))
    end
  end

  def self.safari_reward
    if progress["pilot_safari_surf"]
      pbMessage(t("You already found the Surf prize.", "Você já resgatou o prêmio de Surf."))
      return
    end
    return unless pbReceiveItem(:HM03)
    progress["pilot_safari_surf"] = true
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

# Sprite_Character ja posiciona o pivot nos pes e atualiza o frame andando.
# Igualamos a altura visível ao Gary, sem alterar NPCs, imagens ou colisoes.
# Prevent a CutTree's alternate direction/pattern rows from rendering as
# a stump while it is merely being interacted with. Do NOT prepend Game_Event
# refresh/lock/update: that conflicts with Decades event refresh alias chains
# and raised SystemStackError at KantoPilot.rb:1272 when loading a saved map.
# Only the visible src_rect is normalized; game state is never modified.
module BlueKantoPilot::PlayerOverworldScale
  def update
    # Undo only our previous multiplier before the native update. Native
    # camera/animation zoom may change and must not be multiplied repeatedly.
    if instance_variable_defined?(:@blue_kanto_original_zoom)
      self.zoom_x, self.zoom_y = @blue_kanto_original_zoom
      remove_instance_variable(:@blue_kanto_original_zoom)
    end
    super
    if BlueKantoPilot.kanto_current? && @character &&
       BlueKantoPilot.cut_tree_obstacle?(@character) &&
       !@character.instance_variable_get(:@erased) &&
       !@character.instance_variable_get(:@blue_kanto_cut_animating) &&
       @tile_id == 0 && @cw && @ch && @cw > 0 && @ch > 0
      page = @character.instance_variable_get(:@page)
      graphic = page && page.graphic
      if graphic && graphic.direction && graphic.pattern
        self.src_rect.set(graphic.pattern * @cw,
                          ((graphic.direction - 2) / 2) * @ch, @cw, @ch)
      end
    end
    # The pilot marker alone excluded the shared Windows/Android builds.
    # The existing regional predicate also checks the integrated install
    # and current save region; NPCs, other regions and collision stay intact.
    if @character && @character.equal?($game_player) && BlueKantoPilot.kanto_current?
      sheet = respond_to?(:bitmap) ? bitmap : nil
      if sheet && @cw && @ch && @character.respond_to?(:character_name) &&
         respond_to?(:src_rect) && src_rect
        rect = src_rect
        key = [@character.character_name, sheet.object_id, sheet.width, sheet.height]
        if @blue_kanto_visible_key != key
          @blue_kanto_frame_bounds = {}
          @blue_kanto_visible_key = key
        end
        frame = [rect.x,rect.y,rect.width,rect.height]
        unless @blue_kanto_frame_bounds.key?(frame)
          @blue_kanto_frame_bounds[frame] = BlueKantoPilot.overworld_frame_bounds(sheet,*frame)
        end
        bounds = @blue_kanto_frame_bounds[frame]
        visible = bounds && bounds[1]-bounds[0]+1
        factor = BlueKantoPilot.player_overworld_zoom(visible)
        @blue_kanto_original_zoom = [zoom_x, zoom_y]
        self.zoom_x = zoom_x * factor
        self.zoom_y = zoom_y * factor
      end
    end
  end
end
Sprite_Character.prepend(BlueKantoPilot::PlayerOverworldScale) if defined?(Sprite_Character)

# Native Cut is the only path allowed to expose animation frames.
# No Game_Event methods are overridden; the native method handles the
# entire move route, erase and save state as before.
module BlueKantoPilot::CutTreeSmashAnimation
  def pbSmashEvent(event)
    return super unless BlueKantoPilot.cut_tree_obstacle?(event)
    event.instance_variable_set(:@blue_kanto_cut_animating, true)
    begin
      super
    ensure
      event.instance_variable_set(:@blue_kanto_cut_animating, false)
    end
  end
end
Object.prepend(BlueKantoPilot::CutTreeSmashAnimation)

# MapMetadata#name is used by the native location banner and map UI. Some
# localized saves show just "Cidade"; the pilot's source Map010 must retain
# its proper place name. Never change the actual map ID, real_name, or Decades.
module BlueKantoPilot::ViridianMapLabel
  def name
    local_name = BlueKantoPilot.viridian_display_name_for_map(@id)
    local_name || super
  end
end
GameData::MapMetadata.prepend(BlueKantoPilot::ViridianMapLabel) if defined?(GameData::MapMetadata)

# The Kanto-only markers ensure this global movement hook is inert on
# Decades, Johto, Hoenn and Sinnoh, even when those maps share a level cap.
# The center of the three existing source-grounded lane markers renders
# Gary until his Cerulean battle is won. Native event/page state is retained;
# even an old false-positive self-switch cannot conceal this pending actor.
module BlueKantoPilot::CeruleanRivalActor
  def character_name
    if @id == BlueKantoPilot::CERULEAN_RIVAL_ACTOR
      map_id = @map_id || (@map && @map.respond_to?(:map_id) && @map.map_id)
      if BlueKantoPilot.cerulean_rival_map?(map_id)
        return "" unless BlueKantoPilot.cerulean_rival_pending?
        return BlueKantoPilot.cerulean_rival_graphic || super
      end
    end
    super
  end
end
Game_Event.prepend(BlueKantoPilot::CeruleanRivalActor) if defined?(Game_Event)

# Synchronize self-switches at map boundaries, never by prepending
# Game_Event#refresh. Event Indicators aliases that method; aliasing a
# prepended refresh calls super back into the alias and overflows the stack.
module BlueKantoPilot
  def self.sync_cerulean_quest_pages(map_id)
    return false unless $game_self_switches && $PokemonGlobal &&
      kanto_current? && kanto_map_id(43) && map_id == kanto_map_id(39)
    desired = {13=>cerulean_house_open?,25=>cerulean_house_open?}
    [26,37,38].each { |id| desired[id] = !!progress["pilot_cerulean_dig_awarded"] }
    changed = false
    desired.each do |id, value|
      key = [map_id,id,"A"]
      next if !!$game_self_switches[key] == value
      $game_self_switches[key] = value
      changed = true
    end
    changed
  end

  # A save or an already-cached neighbouring map may retain the pre-K02-C
  # Game_Event table even after the installer added the six interiors.
  # Refreshing its old pages cannot create the missing doors. Only reload a
  # proven current Cerulean RXDATA, before sprites are created. Never touch
  # save files, MapIDs, player coordinates, quest flags or unrelated maps.
  CERULEAN_INTERIOR_DOORS = {3=>44,7=>43,8=>46,9=>48,10=>44,11=>45,12=>47,27=>48}.freeze

  def self.cerulean_door_transfer?(commands, destination)
    destination && Array(commands).any? { |op| op.code == 201 &&
      op.parameters[0] == 0 && op.parameters[1] == destination }
  end

  def self.reload_stale_cerulean_doors(map)
    return false unless map && kanto_current? && map.map_id == kanto_map_id(39)
    destinations = CERULEAN_INTERIOR_DOORS.transform_values { |source| kanto_map_id(source) }
    return false unless destinations.values.all? && destinations.values.uniq.length == 6
    stale = destinations.keys.select do |id|
      event = map.events[id]
      !event || event.trigger != 1 || !cerulean_door_transfer?(event.list,destinations[id])
    end
    return false if stale.empty?
    path = format("Data/Map%03d.rxdata",map.map_id)
    return false unless File.file?(path)
    authored = load_data(path)
    # The on-disk map must already contain ALL eight verified transfers.
    # An incomplete installation cannot be fixed by inventing a warp.
    return false unless authored.respond_to?(:events) &&
      destinations.all? { |id,destination| authored.events[id] &&
        authored.events[id].pages.any? { |page| page.trigger == 1 &&
          cerulean_door_transfer?(page.list,destination) } } &&
      destinations.values.all? { |id| File.file?(format("Data/Map%03d.rxdata",id)) }
    display = [map.display_x,map.display_y] if map.respond_to?(:display_x) && map.respond_to?(:display_y)
    map.setup(map.map_id)
    if display && map.respond_to?(:display_x=) && map.respond_to?(:display_y=)
      map.display_x,map.display_y = display
    end
    puts "KANTO_CERULEAN_STALE_DOORS_RELOADED:#{stale.inspect}"
    true
  end

  # A save may restore an existing map without calling setup again.
  # Refresh through the engine's existing chain only after flags change.
  def self.sync_loaded_cerulean_map(map)
    return unless map
    reloaded = reload_stale_cerulean_doors(map)
    changed = sync_cerulean_quest_pages(map.map_id)
    return unless reloaded || changed
    map.need_refresh = true
    map.events.each_value { |event| event.refresh }
  end
end

module BlueKantoPilot::CeruleanQuestMapSetup
  def setup(map_id, *args)
    BlueKantoPilot.sync_cerulean_quest_pages(map_id)
    super
  end
end
Game_Map.prepend(BlueKantoPilot::CeruleanQuestMapSetup) if defined?(Game_Map)

module BlueKantoPilot::CeruleanQuestMapLoad
  def createSpritesets(*args)
    if $map_factory && $map_factory.respond_to?(:maps)
      $map_factory.maps.each { |map| BlueKantoPilot.sync_loaded_cerulean_map(map) }
    else
      BlueKantoPilot.sync_loaded_cerulean_map($game_map)
    end
    super
  end
end
Scene_Map.prepend(BlueKantoPilot::CeruleanQuestMapLoad) if defined?(Scene_Map)

module BlueKantoPilot::Route2ExitGuard
  def move_generic(dir, turn_enabled = true)
    if BlueKantoPilot.cerulean_rival_crossing?(self, dir)
      turn_generic(dir, true) if turn_enabled
      # Do not continue the old movement after a battle/blackout. Victory
      # clears the encounter; the next ordinary movement proceeds normally.
      BlueKantoPilot.cerulean_rival
      return
    end
    if BlueKantoPilot.pewter_route3_blocked?(self, dir)
      turn_generic(dir, true) if turn_enabled
      key = $game_map.map_id
      if @blue_pewter_last_warning != key
        @blue_pewter_last_warning = key
        guard = $game_map.events[21]
        if guard
          guard.turn_toward_player
          pbExclaim(guard)
        end
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
    # Give Running Shoes before the east-edge map connection changes maps.
    # A blocked exit above returns early, so the gift requires Boulder.
    if BlueKantoPilot.pewter_route3_crossing?(self, dir)
      BlueKantoPilot.mom_running_shoes_at_route3
    end
    super
  end
end
Game_Player.prepend(BlueKantoPilot::Route2ExitGuard)

# The imported door tile can be unwalkable from its original doorstep even
# though another adjacent square passes a collision probe. Use the native
# event's starting flag on deliberate contact with the verified doorway.
# No new warp or teleport is constructed: the original event interpreter,
# including Bill's conditional and the authored destination, remains in charge.
module BlueKantoPilot
  CERULEAN_DOOR_STEPS = {
    3=>[[10,8],2], 7=>[[13,29],8], 8=>[[15,18],8],
    9=>[[30,12],8], 10=>[[10,12],8], 11=>[[17,12],8],
    12=>[[23,29],8], 27=>[[31,8],2]
  }.freeze

  def self.cerulean_door_contact(player, direction)
    return nil unless $game_map && kanto_current? &&
      $game_map.map_id == kanto_map_id(39)
    return nil unless $game_map.respond_to?(:events)
    return nil if $game_temp && $game_temp.respond_to?(:in_battle) && $game_temp.in_battle
    return nil if defined?(pbMapInterpreterRunning?) && pbMapInterpreterRunning?
    delta = {2=>[0,1],4=>[-1,0],6=>[1,0],8=>[0,-1]}[direction]
    return nil unless delta
    from = [player.x,player.y]
    target = [from[0]+delta[0],from[1]+delta[1]]
    CERULEAN_INTERIOR_DOORS.each do |id,source|
      event = $game_map.events[id]
      next unless event.is_a?(Game_Event) && event.respond_to?(:trigger) &&
        event.respond_to?(:list) && event.respond_to?(:x) && event.respond_to?(:y) &&
        event.respond_to?(:start) && event.respond_to?(:starting) &&
        event.trigger == 1 && cerulean_door_transfer?(event.list,kanto_map_id(source))
      next unless [event.x,event.y] == target ||
        (id == 7 && target == [14,28])
      canonical = CERULEAN_DOOR_STEPS[id] == [from,direction] ||
        (id == 7 && from == [14,29] && direction == 8)
      return [event,from,target,canonical]
    end
    nil
  end
end

module BlueKantoPilot::CeruleanDoorContact
  def move_generic(dir, turn_enabled = true)
    contact = turn_enabled && BlueKantoPilot.cerulean_door_contact(self,dir)
    # Canonical doorstep interaction is an event, not walking into a wall.
    # Dispatch before generic movement (which can reject the step, jump or
    # defer the event until the end of its animation).
    if contact && contact[3]
      event = contact[0]
      turn_generic(dir,true)
      event.start unless event.starting
      return
    end
    city = $game_map if contact
    result = super
    if contact && $game_map.equal?(city)
      event,from,target,canonical = contact
      # A native step onto the tile or a bump from the exact original
      # doorstep can start the same player-touch event. Never open walls
      # from arbitrary blocked neighbours, or bypass a running interpreter.
      if ([x,y] == target || (canonical && [x,y] == from && direction == dir)) &&
          !(defined?(pbMapInterpreterRunning?) && pbMapInterpreterRunning?)
        event.start unless event.starting
      end
    end
    result
  end
end
Game_Player.prepend(BlueKantoPilot::CeruleanDoorContact)

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

# A map-local action also serves verified, existing Kanto installations whose
# compiled Map203 was intentionally never rewritten by --sync-runtime.
MenuHandlers.add(:pause_menu, :blue_kanto_fossil_lab, {
  "name"=>BlueKantoPilot.t("Revive Fossil (Cinnabar Lab)", "Reviver fóssil (Lab. Cinnabar)"),
  "order"=>72,
  "condition"=>proc { |_menu| BlueKantoPilot.in_cinnabar_lab? },
  "effect"=>proc do |menu|
    menu.pbHideMenu
    BlueKantoPilot.revive_cinnabar_fossil
    menu.pbShowMenu
    false
  end
})

# Region-specific serialized native storage. The ordinary Essentials DayCare
# instance is never replaced; the native walking handler uses this getter.
if defined?(PokemonGlobalMetadata) && defined?(DayCare)
  module BlueKantoDayCareMetadata
    def day_care
      return super unless BlueKantoPilot.kanto_current?
      if !@blue_kanto_day_care
        @blue_kanto_day_care = DayCare.new
        @blue_kanto_day_care.gain_exp = true
        @blue_kanto_day_care.share_egg_moves = false
      end
      @blue_kanto_day_care
    end
  end
  PokemonGlobalMetadata.prepend(BlueKantoDayCareMetadata)
end
