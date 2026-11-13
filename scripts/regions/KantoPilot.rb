# Local Kanto pilot events. Loaded only by the separately prepared test game.
module BlueKantoPilot
  STARTERS = [:BULBASAUR, :CHARMANDER, :SQUIRTLE].freeze
  RIVAL_VERSIONS = {BULBASAUR: 11, CHARMANDER: 12, SQUIRTLE: 13}.freeze
  VIRIDIAN_MART_STOCK = [:POKEBALL, :POTION, :ANTIDOTE, :PARALYZEHEAL].freeze
  VIRIDIAN_REQUIRED_BADGES = %w[BOULDER CASCADE THUNDER RAINBOW SOUL MARSH VOLCANO].freeze
  LEAGUE_REQUIRED_BADGES = (VIRIDIAN_REQUIRED_BADGES + ["EARTH"]).freeze
  LEAGUE_ORDER = %w[LORELEI BRUNO AGATHA LANCE CHAMPION].freeze
  LEAGUE_CHAMPION_VERSIONS = {BULBASAUR: 1, CHARMANDER: 2, SQUIRTLE: 3}.freeze

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
    pbMessage(_INTL("Mãe: {1}, o professor Oak estava procurando por você. Passe no laboratório antes de sair de Pallet.", $player.name))
    progress["pilot_met_mom"] = true
  end

  def self.oak_warning
    pbMessage(_INTL("Oak: Ei! Espere um pouco!"))
  end

  def self.show_approaching_oak(visible)
    key = [$game_map.map_id, 12, "A"]
    $game_self_switches[key] = visible
    $game_map.events[12].refresh
  end

  def self.oak_invitation
    pbMessage(_INTL("Oak: É perigoso entrar na grama alta sem um Pokémon. Venha comigo ao laboratório!"))
  end

  def self.starter
    progress["pilot_starter"]&.to_sym
  end

  def self.prepare_lab_escort(lab_map, scene_event)
    return if starter
    # Region-local save flag and map-local self switch; no Decades/Johto flags.
    progress["pilot_lab_escort_pending"] = true
    $game_self_switches[[lab_map, scene_event, "A"]] = true
  end

  def self.lab_escort_started
    progress["pilot_lab_escort_pending"] = true
  end

  def self.oak_lab_briefing
    return if starter
    progress["pilot_lab_escort_pending"] = false
    progress["pilot_oak_lab_briefed"] = true
    BlueMusic.with_kanto_scene("oak_talk") do
      pbMessage(_INTL("Oak: Chegamos! Gary está esperando. Temos três Poké Bolas na mesa."))
      pbMessage(_INTL("Oak: Vá até uma delas e escolha o Pokémon que vai acompanhar você!"))
    end
  end

  def self.talk_to_oak
    if !starter
      if progress["pilot_oak_lab_briefed"]
        pbMessage(_INTL("Oak: Escolha seu inicial em uma das três Poké Bolas da mesa."))
      else
        pbMessage(_INTL("Oak: As três Poké Bolas na mesa contêm Bulbasaur, Charmander e Squirtle."))
      end
      return
    end
    choose_starter
  end

  def self.gary_talk
    if !starter
      pbMessage(_INTL("Gary: Você ainda não escolheu seu Pokémon? Vá até a mesa!"))
    elsif !rival_done?
      progress["pilot_gary_warned"] = true
      pbMessage(_INTL("Gary: Você já escolheu? Também tenho um Pokémon. Vamos ver quem é melhor!"))
    else
      pbMessage(_INTL("Gary: Vou treinar mais para nossa próxima batalha."))
    end
  end

  def self.pick_starter(species, event_id)
    if starter
      pbMessage(_INTL("Você já escolheu seu Pokémon inicial."))
      return
    end
    return unless STARTERS.include?(species)
    name = GameData::Species.get(species).name
    return unless pbConfirmMessage(_INTL("Escolher {1} desta Poké Bola?", name))
    choose_starter(species)
    return unless starter == species
    # Only the chosen tabletop object disappears, without global switches.
    $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
    $game_map.events[event_id]&.refresh
    gary_talk
  end

  def self.choose_starter(species = nil)
    if starter
      if progress["pilot_oak_parcel_received"] && !progress["pilot_oak_parcel_delivered"]
        # Record the parcel's delivery in the region-specific save instead of
        # creating an unknown FRLG quest item in the Decades item catalogue.
        progress["pilot_oak_parcel_delivered"] = true
        $player.has_pokedex = true if $player.respond_to?(:has_pokedex=)
        BlueMusic.with_kanto_scene("oak_talk") do
          pbMessage(_INTL("Oak: O pacote chegou de Viridian! Sua Pokédex está pronta. Obrigado!"))
        end
      else
        pbMessage(_INTL("Oak: Cuide bem do seu {1}.", GameData::Species.get(starter).name))
      end
      return
    end
    # The Oak dialogue is NOT a starter selection menu. A species can only
    # be supplied by an audited tabletop Poké Ball callback.
    unless STARTERS.include?(species)
      pbMessage(_INTL("Oak: Escolha um Pokémon tocando uma das três Poké Bolas da mesa."))
      return
    end
    return unless pbAddPokemonSilent(species, 5)
    progress["pilot_starter"] = species.to_s
    BlueMusic.kanto_me_play("obtained_pokemon")
    $bag.add(:POKEBALL, 5)
    $bag.add(:POTION, 2)
    pbSetPokemonCenter
    pbMessage(_INTL("Oak: {1} escolheu você! Leve estas Poké Bolas com você.", GameData::Species.get(species).name))
  end

  # A safe, local story step for the first Pallet -> Viridian -> Pallet
  # loop. The source item need not exist in Decades; state is saved only in
  # the active Kanto campaign. Existing Boulder+ saves skip the new quest.
  def self.viridian_mart
    completed = progress["pilot_oak_parcel_delivered"]
    advanced = BlueRegions.local_achievements(progress, "KANTO").include?("BOULDER")
    if starter && !completed && !progress["pilot_oak_parcel_received"] && !advanced
      progress["pilot_oak_parcel_received"] = true
      pbMessage(_INTL("Funcionário: Oak pediu que você leve este pacote até seu laboratório em Pallet."))
    elsif progress["pilot_oak_parcel_received"] && !completed
      pbMessage(_INTL("Funcionário: O pacote é para o professor Oak, em Pallet."))
    end
    pbPokemonMart(VIRIDIAN_MART_STOCK)
  end

  def self.rival_done?
    progress["pilot_rival"] == true
  end

  def self.rival_pending?
    starter && !rival_done? && $player.able_pokemon_count > 0
  end

  def self.rival
    if !starter
      pbMessage(_INTL("Gary: Escolha o seu Pokémon primeiro."))
      return
    end
    if rival_done?
      pbMessage(_INTL("Gary: Continue treinando. Nossa revanche fica para depois!"))
      return
    end
    return unless rival_pending?
    BlueMusic.with_kanto_scene("rival_appears") do
      pbMessage(_INTL("Gary: Ei, {1}! Antes de ir, vamos testar nossos Pokémon!", $player.name))
    end
    setBattleRule("canLose")
    result = TrainerBattle.start(:BLUE_KANTO_RIVAL, "Blue", RIVAL_VERSIONS.fetch(starter))
    $player.heal_party
    progress["pilot_rival"] = true
    if result
      pbMessage(_INTL("Gary: Você venceu. Vou treinar para a revanche!"))
    else
      pbMessage(_INTL("Gary: Essa foi minha. Vá treinar na Rota 1."))
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
        pbMessage(_INTL("O Ginásio de Viridian está fechado. Conquiste as sete primeiras insígnias de Kanto (faltam {1}).", missing.length))
      else
        pbMessage(_INTL("O Ginásio só abre após a libertação da Silph Co."))
      end
      return false
    end
    pbFadeOutIn { BlueRegionTravel.move_to([map_id, x, y, 2]) }
    true
  end

  def self.viridian_gym_guide
    if !viridian_access?
      pbMessage(_INTL("Guia: Giovanni retorna ao ginásio somente após as sete insígnias e a libertação da Silph Co."))
    elsif BlueRegions.local_achievements(progress, "KANTO").include?("EARTH")
      pbMessage(_INTL("Guia: A Earth Badge é sua! Siga para a Liga Pokémon quando o caminho estiver disponível."))
    else
      pbMessage(_INTL("Guia: Giovanni é especialista em Pokémon do tipo Terra. Vença para receber a Earth Badge!"))
    end
  end

  def self.battle(type, name, event_key = nil, version = 0)
    return unless starter
    if type == :BLUE_KANTO_LEADER_SABRINA && !progress["pilot_silph_rescued"]
      pbMessage(_INTL("Sabrina está aguardando a libertação da Silph Co. Derrote Giovanni primeiro."))
      return
    end
    if type == :BLUE_KANTO_LEADER_GIOVANNI && !viridian_access?
      pbMessage(_INTL("Giovanni ainda não aceita seu desafio. Conquiste as sete primeiras insígnias e liberte a Silph Co."))
      return
    end
    if type == :BLUE_KANTO_LEADER_BLAINE && !progress["pilot_cinnabar_secret_key"]
      pbMessage(_INTL("Blaine: Encontre a Secret Key na Pokémon Mansion antes do desafio!"))
      return
    end
    if type == :BLUE_KANTO_LEADER_SURGE && !progress["pilot_surge_unlocked"]
      pbMessage(_INTL("Lt. Surge aguarda atrás das trancas elétricas. Resolva o enigma das lixeiras primeiro."))
      return
    end
    wins = (progress["pilot_wins"] ||= [])
    # New events persist stable region/map/event keys. Accept old name-only
    # entries from pilot saves built before this fix without replaying battles.
    key = event_key || "#{type}:#{name}"
    # Both Silph Co. and Viridian have a boss named Giovanni. A legacy
    # Silph name-only victory must never mark the *gym* Giovanni as beaten.
    if wins.include?(key) || (type != :BLUE_KANTO_LEADER_GIOVANNI && wins.include?(name))
      pbMessage(_INTL("{1}: Boa sorte na sua jornada!", name))
      return
    end
    if type == :BLUE_KANTO_RIVAL_SILPH && name == "Blue"
      BlueMusic.with_kanto_scene("rival_appears") do
        pbMessage(_INTL("Blue: Vamos ver como você ficou mais forte desde Pallet!"))
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
      pbMessage(_INTL("Brock: A Boulder Badge é sua. O caminho para Cerulean está aberto!"))
    elsif type == :BLUE_KANTO_LEADER_MISTY && BlueRegions.award(progress, "KANTO", "CASCADE")
      BlueMusic.kanto_me_play("badge_awarded")
      pbMessage(_INTL("Misty: Você conquistou a Cascade Badge! Siga ao sul para Vermilion!"))
    elsif type == :BLUE_KANTO_LEADER_SURGE && BlueRegions.award(progress, "KANTO", "THUNDER")
      BlueMusic.kanto_me_play("badge_awarded")
      pbMessage(_INTL("Lt. Surge: A Thunder Badge é sua! Agora você pode usar Fly em Kanto."))
    elsif type == :BLUE_KANTO_LEADER_ERIKA && BlueRegions.award(progress, "KANTO", "RAINBOW")
      BlueMusic.kanto_me_play("badge_awarded")
      pbMessage(_INTL("Erika: Você conquistou a Rainbow Badge!"))
    elsif type == :BLUE_KANTO_LEADER_KOGA && BlueRegions.award(progress, "KANTO", "SOUL")
      BlueMusic.kanto_me_play("badge_awarded")
      pbMessage(_INTL("Koga: A Soul Badge agora é sua!"))
    elsif type == :BLUE_KANTO_ROCKETBOSS && name == "Giovanni"
      progress["pilot_silph_rescued"] = true
      pbMessage(_INTL("Giovanni foi derrotado! A Silph Co. está livre."))
    elsif type == :BLUE_KANTO_LEADER_SABRINA && BlueRegions.award(progress, "KANTO", "MARSH")
      BlueMusic.kanto_me_play("badge_awarded")
      pbMessage(_INTL("Sabrina: Você conquistou a Marsh Badge!"))
    elsif type == :BLUE_KANTO_LEADER_BLAINE && BlueRegions.award(progress, "KANTO", "VOLCANO")
      BlueMusic.kanto_me_play("badge_awarded")
      pbMessage(_INTL("Blaine: A Volcano Badge é sua!"))
    elsif type == :BLUE_KANTO_LEADER_GIOVANNI && BlueRegions.award(progress, "KANTO", "EARTH")
      BlueMusic.kanto_me_play("badge_awarded")
      pbMessage(_INTL("Giovanni: Você conquistou a Earth Badge! O desafio da Liga está adiante."))


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

  def self.trainer_repeat(name)
    pbMessage(_INTL("{1}: Boa sorte na sua jornada!", name))
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
      pbMessage(_INTL("As duas trancas elétricas já foram desativadas."))
      return
    end
    possible = surge_pairs
    if possible.empty?
      pbMessage(_INTL("O mecanismo não está pronto nesta cópia do ginásio."))
      return
    end
    progress["pilot_surge_solution"] ||= possible.sample
    target = progress["pilot_surge_solution"]
    if !progress["pilot_surge_first"]
      if event_id == target[0]
        progress["pilot_surge_first"] = true
        pbMessage(_INTL("Você encontrou a primeira chave! Procure outra lixeira próxima."))
      else
        pbMessage(_INTL("Não há chave nesta lixeira."))
      end
    elsif event_id == target[1]
      progress["pilot_surge_unlocked"] = true
      progress["pilot_surge_first"] = false
      SURGE_LOCKS.each do |id|
        $game_self_switches[[$game_map.map_id, id, "A"]] = true
      end
      $game_map.need_refresh = true
      pbMessage(_INTL("As duas trancas foram desativadas! Lt. Surge está acessível."))
    else
      progress["pilot_surge_first"] = false
      progress.delete("pilot_surge_solution")
      pbMessage(_INTL("Chave errada! O sistema reiniciou a sequência de lixeiras."))
    end
  end

  def self.surge_gate
    pbMessage(_INTL("A trava elétrica está ativa. Encontre duas chaves nas lixeiras."))
  end

  # TEMPORARY phase 08 story bridge: Bill's canonical S.S. Ticket event is
  # outside the installed route until the Cerulean north passage is audited.
  # Only players with Cascade may claim a ticket; never award it more than once.
  def self.ticketmaster
    if !BlueRegions.local_achievements(progress, "KANTO").include?("CASCADE")
      pbMessage(_INTL("Porto: Primeiro conquiste a Cascade Badge em Cerulean."))
      return
    end
    if progress["pilot_ss_ticket"] || (GameData::Item.exists?(:SSTICKET) && $bag.has?(:SSTICKET))
      progress["pilot_ss_ticket"] = true
      pbMessage(_INTL("Porto: Sua passagem para o S.S. Anne está liberada!"))
    elsif !GameData::Item.exists?(:SSTICKET)
      # Decades does not guarantee the FRLG ticket item exists. Use a local
      # save-state permit without changing native item PBS or other saves.
      progress["pilot_ss_ticket"] = true
      pbMessage(_INTL("Acesso experimental: a passagem digital para o S.S. Anne está liberada."))
    elsif $bag.add(:SSTICKET, 1)
      progress["pilot_ss_ticket"] = true
      BlueMusic.kanto_me_play("obtained_item")
      pbMessage(_INTL("Acesso experimental: recebeu o S.S. Ticket. O evento de Bill será adaptado depois."))
    else
      pbMessage(_INTL("Você precisa liberar espaço na Bolsa para receber o S.S. Ticket."))
    end
  end

  def self.harbor_gate(map_id, x, y)
    unless progress["pilot_ss_ticket"] || (GameData::Item.exists?(:SSTICKET) && $bag.has?(:SSTICKET))
      pbMessage(_INTL("O acesso ao porto exige o S.S. Ticket. Fale com o atendente."))
      return
    end
    pbFadeOutIn { BlueRegionTravel.move_to([map_id, x, y, 2]) }
  end

  # The captain's original scripts are not executed in Blue. Give the audited
  # Cut HM once, using the item ID actually available in the installed game.
  def self.captain
    events = (progress["field_events"]["KANTO"] ||= [])
    if events.include?("SS_ANNE_CAPTAIN")
      pbMessage(_INTL("Capitão: Use Cut para abrir caminhos onde tiver permissão."))
      return
    end
    item = [:HM01, :HMCUT].find { |candidate| GameData::Item.exists?(candidate) }
    unless item
      pbMessage(_INTL("O HM Cut ainda não está cadastrado nesta versão do Blue."))
      return
    end
    unless $bag.add(item, 1)
      pbMessage(_INTL("Capitão: Libere espaço na Bolsa para receber o HM Cut."))
      return
    end
    events << "SS_ANNE_CAPTAIN"
    BlueMusic.kanto_me_play("obtained_item")
    pbMessage(_INTL("O Capitão entregou o HM Cut! A Cascade Badge permite usá-lo em Kanto."))
  end

  def self.pickup(item, key)
    collected = (progress["pilot_items"] ||= [])
    if collected.include?(key)
      pbMessage(_INTL("Você já recolheu este item."))
      return
    end
    if $bag.add(item, 1)
      collected << key
      BlueMusic.kanto_me_play("obtained_item")
      pbMessage(_INTL("Encontrou {1}!", GameData::Item.get(item).name))
    else
      pbMessage(_INTL("Sua Bolsa está cheia. Libere espaço para recolher o item."))
    end
  end


  # Silph Card Key: persist locally, never import a foreign item into Decades.
  def self.silph_card_key
    if progress["pilot_silph_card_key"]
      pbMessage(_INTL("Você já encontrou a Card Key da Silph Co."))
      return
    end
    progress["pilot_silph_card_key"] = true
    $game_self_switches[[$game_map.map_id, 9, "A"]] = true
    $game_map.need_refresh = true
    pbMessage(_INTL("Encontrou a Card Key! Agora pode abrir as portas da Silph Co."))
  end

  # Adjacent source map event tiles form a single original locked door.
  def self.silph_door(event_ids)
    unless progress["pilot_silph_card_key"]
      pbMessage(_INTL("Uma trava de segurança. Encontre a Card Key no 5º andar."))
      return
    end
    event_ids.each do |eid|
      next unless $game_map.events[eid]
      $game_self_switches[[$game_map.map_id, eid, "A"]] = true
    end
    $game_map.need_refresh = true
    pbMessage(_INTL("A Card Key abriu a porta!"))
  end

  def self.silph_rival
    return unless starter
    versions = { BULBASAUR: 51, CHARMANDER: 52, SQUIRTLE: 53 }
    key = "KANTO_184_043"
    battle(:BLUE_KANTO_RIVAL_SILPH, "Blue", key, versions.fetch(starter))
  end

  def self.silph_president
    unless progress["pilot_silph_rescued"]
      pbMessage(_INTL("Presidente: Giovanni ainda controla o último andar!"))
      return
    end
    if progress["pilot_silph_master_ball"]
      pbMessage(_INTL("Presidente: Obrigado por libertar a Silph Co.!"))
      return
    end
    unless GameData::Item.exists?(:MASTERBALL)
      pbMessage(_INTL("A Master Ball ainda não está cadastrada nesta versão do Blue."))
      return
    end
    unless $bag.add(:MASTERBALL, 1)
      pbMessage(_INTL("Presidente: Abra espaço na Bolsa para receber a Master Ball."))
      return
    end
    progress["pilot_silph_master_ball"] = true
    BlueMusic.kanto_me_play("obtained_item")
    pbMessage(_INTL("Recebeu a Master Ball pela libertação da Silph Co.!"))
  end

  def self.dojo_prize(species, event_id)
    unless progress.fetch("pilot_wins", []).include?("KANTO_172_012")
      pbMessage(_INTL("Vença primeiro o mestre Koichi para escolher um Pokémon."))
      return
    end
    if progress["pilot_dojo_prize"]
      pbMessage(_INTL("Você já escolheu seu Pokémon no Fighting Dojo."))
      return
    end
    if $player.party.length >= 6
      pbMessage(_INTL("Sua equipe está cheia. Deixe uma vaga para o Pokémon do dojo."))
      return
    end
    return unless GameData::Species.exists?(species)
    return unless pbConfirmMessage(_INTL("Escolher {1} como prêmio único do dojo?", GameData::Species.get(species).name))
    return unless pbAddPokemonSilent(species, 25)
    progress["pilot_dojo_prize"] = species.to_s
    BlueMusic.kanto_me_play("obtained_pokemon")
    [1, 2].each { |eid| $game_self_switches[[$game_map.map_id, eid, "A"]] = true }
    $game_map.need_refresh = true
    pbMessage(_INTL("Prêmio do Fighting Dojo recebido!"))
  end

  def self.silph_elevator
    filename = "Data/blue-kanto-silph-floors.txt"
    unless experimental? && File.file?(filename)
      pbMessage(_INTL("Os controles do elevador não estão disponíveis fora do piloto."))
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
    choice = pbMessage(_INTL("Silph Co. — escolher andar"),
                       floors.map { |row| _INTL("Andar {1}F", row[0]) } + [_INTL("Voltar")], -1)
    return unless choice && choice.between?(0, floors.length - 1)
    pbFadeOutIn { BlueRegionTravel.move_to(floors[choice][1]) }
  end

  # Phase 12 uses only Kanto-local progress. The FRLG source contains
  # foreign switches, quiz scripts and rewards; none are executed by Blue.
  CINNABAR_QUIZZES = [
    [_INTL("Caterpie evolui para Metapod?"), true],
    [_INTL("Existem nove insígnias oficiais de Kanto?"), false],
    [_INTL("Poliwag possui três evoluções consecutivas?"), false],
    [_INTL("Golpes elétricos são supereficazes contra Pokémon Terrestres?"), false],
    [_INTL("Dois Pokémon da mesma espécie e nível podem ter atributos diferentes?"), true],
    [_INTL("O TM28 contém o golpe Tombstony?"), false]
  ].freeze
  CINNABAR_GYM_DOORS = {
    1 => [20,21,22,23], 2 => [1,25,26,27],
    3 => [2,18,19,29], 4 => [13,31,32],
    5 => [34,35,36,37], 6 => [39,40,41,42]
  }.freeze

  def self.cinnabar_gym_gate(map_id, x, y)
    unless progress["pilot_cinnabar_secret_key"]
      pbMessage(_INTL("O ginásio de Cinnabar está trancado. A Secret Key está na Pokémon Mansion."))
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
      pbMessage(_INTL("Essa sala do ginásio já está liberada."))
      return
    end
    question, answer = CINNABAR_QUIZZES[group - 1]
    choice = pbMessage(question, [_INTL("Sim"), _INTL("Não"), _INTL("Voltar")], -1)
    return unless choice == 0 || choice == 1
    if (choice == 0) == answer
      cinnabar_unlock(group)
      pbMessage(_INTL("Resposta correta! A porta se abriu."))
    else
      pbMessage(_INTL("Resposta incorreta. Você pode tentar de novo ou enfrentar o treinador da sala."))
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
      pbMessage(_INTL("A porta está trancada. Responda ao quiz ou vença o treinador da sala."))
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
    pbMessage(_INTL("Uma passagem da Pokémon Mansion foi aberta!"))
  end

  def self.mansion_door(source_map, door_ids)
    if progress.fetch("pilot_mansion_switches", []).include?(source_map)
      door_ids.each do |event_id|
        next unless $game_map.events[event_id]
        $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
      end
      $game_map.need_refresh = true
    else
      pbMessage(_INTL("Esta passagem depende de uma estátua próxima."))
    end
  end

  def self.mansion_secret_key
    if progress["pilot_cinnabar_secret_key"]
      pbMessage(_INTL("Você já encontrou a Secret Key da Pokémon Mansion."))
      return
    end
    progress["pilot_cinnabar_secret_key"] = true
    $game_self_switches[[$game_map.map_id, 8, "A"]] = true
    $game_map.need_refresh = true
    pbMessage(_INTL("Você encontrou a Secret Key! O ginásio de Cinnabar foi destrancado."))
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
      pbMessage(_INTL("Guarda: Você precisa da insígnia {1} de Kanto para seguir.", missing.first))
      return false
    end
    [guard_id, barrier_id].each do |event_id|
      next unless $game_map.events[event_id]
      $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
    end
    $game_map.need_refresh = true
    pbMessage(_INTL("Guarda: Insígnias verificadas. Pode passar!"))
    true
  end

  def self.league_route_gate(map_id, x, y, required = 8)
    required = 8 unless required.between?(1, 8)
    earned = BlueRegions.local_achievements(progress, "KANTO")
    missing = LEAGUE_REQUIRED_BADGES.first(required).reject { |badge| earned.include?(badge) }
    if missing.any?
      pbMessage(_INTL("O acesso à Liga está bloqueado. Falta a insígnia {1} de Kanto.", missing.first))
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
      pbMessage(_INTL("O mecanismo da Victory Road requer a Rainbow Badge de Kanto."))
      return false
    end
    barrier_ids.each do |event_id|
      next unless $game_map.events[event_id]
      $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
    end
    $game_map.need_refresh = true
    pbMessage(_INTL("O mecanismo de pedras da Victory Road foi ativado (modo experimental)."))
    true
  end

  def self.victory_couple
    key = "KANTO_213_PAIR"
    wins = (progress["pilot_wins"] ||= [])
    if wins.include?(key)
      pbMessage(_INTL("Ray e Tyra: Já batalhamos. Boa sorte na Liga!"))
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
      !progress.fetch("leagues", []).include?("KANTO")
  end

  def self.league_begin(map_id, x, y)
    unless league_badges?
      pbMessage(_INTL("A Liga exige as oito insígnias de Kanto, inclusive a Earth Badge."))
      return false
    end
    if progress.fetch("leagues", []).include?("KANTO")
      pbMessage(_INTL("Seu título de Campeão de Kanto já está registrado. Revanches completas virão depois."))
      return false
    end
    progress["pilot_league_active"] = true
    progress["pilot_league_wins"] = []
    pbFadeOutIn { BlueRegionTravel.move_to([map_id, x, y, 2]) }
    true
  end

  def self.league_battle(stage, type, name, lobby_map)
    return false unless LEAGUE_ORDER.include?(stage)
    unless league_active? && starter
      pbMessage(_INTL("Conquiste as oito insígnias e entre pela porta da Liga para iniciar o desafio."))
      return false
    end
    wins = (progress["pilot_league_wins"] ||= [])
    index = LEAGUE_ORDER.index(stage)
    if wins.include?(stage)
      pbMessage(_INTL("{1}: Já fui derrotado nesta tentativa.", name))
      return true
    end
    unless wins.length == index && LEAGUE_ORDER[0,index] == wins
      pbMessage(_INTL("Você precisa superar a Elite Four na ordem correta."))
      return false
    end
    version = (stage == "CHAMPION") ? LEAGUE_CHAMPION_VERSIONS.fetch(starter) : 0
    if stage == "CHAMPION" && type == :BLUE_KANTO_CHAMPION_BLUE && name == "Blue"
      BlueMusic.with_kanto_scene("rival_appears") do
        pbMessage(_INTL("Blue: Você venceu a Elite! Nossa batalha final começa agora."))
      end
    end
    setBattleRule("canLose")
    won = TrainerBattle.start(type, name, version)
    unless won
      $player.heal_party
      progress["pilot_league_active"] = false
      progress["pilot_league_wins"] = []
      pbMessage(_INTL("Você perdeu esta tentativa da Liga. Volte ao saguão para tentar novamente."))
      pbFadeOutIn { BlueRegionTravel.move_to([lobby_map, 11, 16, 2]) }
      return false
    end
    wins << stage
    pbMessage(_INTL("Vitória contra {1}! Progresso da Liga: {2}/5.", name, wins.length))
    true
  end

  def self.league_advance(stage, map_id, x, y)
    wins = progress.fetch("pilot_league_wins", [])
    if !league_active? || !wins.include?(stage)
      pbMessage(_INTL("A passagem só abre depois de vencer o adversário desta sala."))
      return false
    end
    pbFadeOutIn { BlueRegionTravel.move_to([map_id, x, y, 2]) }
    true
  end

  def self.league_finalize(pallet_map)
    if progress.fetch("leagues", []).include?("KANTO")
      pbMessage(_INTL("Sua conquista da Liga de Kanto já está registrada."))
      return false
    end
    unless league_active? && progress.fetch("pilot_league_wins", []) == LEAGUE_ORDER
      pbMessage(_INTL("Hall of Fame bloqueado: faltam vitórias na Elite Four ou no Campeão."))
      return false
    end
    return false unless BlueRegions.complete_league(progress, "KANTO")
    progress["pilot_league_active"] = false
    progress["pilot_hall_of_fame"] = true
    BlueMusic.with_kanto_scene("hall_of_fame") do
      pbMessage(_INTL("Hall of Fame: Kanto concluída! Decades e Johto foram liberadas no circuito regional."))
    end
    pbFadeOutIn { BlueRegionTravel.move_to([pallet_map, 18, 8, 2]) }
    true
  end

  # The regional transport NPC already exists in starter-town Pallet. The
  # Lobby's guide is an additional after-League point and uses the same
  # single-save travel service (only destinations with maps can be visited).
  def self.league_champion_npc
    pbMessage(_INTL("Blue: Vencer a Elite foi só o começo! Quero ver se você supera o Campeão."))
  end

  def self.league_oak
    if progress.fetch("leagues", []).include?("KANTO")
      pbMessage(_INTL("Oak: Seu nome entrou para o Hall of Fame de Kanto!"))
    else
      pbMessage(_INTL("Oak: Primeiro derrote Blue e conclua a jornada no Hall of Fame."))
    end
  end

  def self.league_guide
    if progress.fetch("leagues", []).include?("KANTO")
      pbMessage(_INTL("Guia da Liga: Parabéns, Campeão! Consulte o agente regional aqui ou em Pallet."))
      BlueRegionTravel.agent(true)
    else
      pbMessage(_INTL("Guia da Liga: Vença Lorelei, Bruno, Agatha, Lance e Blue em sequência."))
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
      pbMessage(_INTL("Escolha um Pokémon com Oak antes de usar os teletransportes de teste."))
      return
    end
    unless $scene && $scene.respond_to?(:transfer_player) && $game_temp && !$game_temp.in_battle
      pbMessage(_INTL("O transporte de teste não está disponível durante batalhas."))
      return
    end
    stops = experimental_stops
    if stops.empty?
      pbMessage(_INTL("Nenhum destino experimental foi preparado."))
      return
    end
    choice = pbMessage(_INTL("Teste experimental: viajar sem concluir a história anterior."),
                       stops.map(&:first) + [_INTL("Cancelar")], -1)
    return if !choice || choice < 0 || choice >= stops.length
    label, point = stops[choice]
    return unless pbConfirmMessage(_INTL("Ir para {1}? Esta opção existe apenas no piloto de testes.", label))
    begin
      pbFadeOutIn { BlueRegionTravel.move_to(point) }
      pbMessage(_INTL("Chegou a {1}. Continue jogando e salve no perfil Kanto Piloto.",label))
    rescue StandardError => e
      pbMessage(_INTL("Falha no destino experimental: {1}",e.message))
    end
  end

  # The source Safari Gate is mapped for navigation, but the isolated
  # pilot must NOT start a fake Safari session: native catch rules, step
  # limits, Safari Balls and exit restoration have not been audited.
  # Both the gate's counter and its guide use this non-transactional message.
  def self.safari_preview
    pbMessage(_INTL("Safari Zone: a entrada para captura está em preparação. " +
                    "Nenhum ingresso, dinheiro ou Safari Ball será consumido nesta versão."))
  end

  # Local Pallet residents; never run the foreign FRLG quest scripts.
  def self.mom
    if $player && $player.party.any? { |pkmn| !pkmn.egg? }
      $player.heal_party
      BlueMusic.kanto_me_play("healed")
      pbMessage(_INTL("Mãe: Descanse um pouco antes de continuar sua aventura por Kanto."))
    else
      pbMessage(_INTL("Mãe: Seu quarto fica no andar de cima. Depois visite Oak no laboratório."))
    end
  end

  def self.daisy
    pbMessage(_INTL("Daisy: Bem-vindo à casa do Gary! O laboratório de Oak fica ao sul de Pallet."))
  end

  def self.heal
    $player.heal_party
    pbSetPokemonCenter
    pbMessage(_INTL("Sua equipe está descansada."))
  end
end

# This menu is visible ONLY in the isolated pilot with its local stop manifest.
MenuHandlers.add(:pause_menu, :blue_kanto_experimental, {
  "name"=>_INTL("Testes Kanto (experimental)"),
  "order"=>71,
  "condition"=>proc { |_menu| BlueKantoPilot.experimental? },
  "effect"=>proc do |menu|
    menu.pbHideMenu
    BlueKantoPilot.experimental_menu
    menu.pbShowMenu
    false
  end
})
