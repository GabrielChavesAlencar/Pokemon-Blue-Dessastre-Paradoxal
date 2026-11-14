# Read-only, private Sinnoh Essentials QA probe.
# Runs ONLY after Compiler.main in the isolated QA Game.exe. It never battles,
# changes saves, modifies maps, creates Barry's ready marker or approves play.
module BlueSinnohQAProbe
  CONFIG = "Sinnoh qa.json".freeze
  RIVAL_READY = "Data/blue-sinnoh-rival-ready.txt".freeze
  HANDLERS = {
    "mother" => "BlueSinnohPilot.mother",
    "barry_intro" => "BlueSinnohPilot.barry_intro",
    "rowan_briefcase" => "BlueSinnohPilot.rowan_briefcase",
    "barry_rival" => "BlueSinnohPilot.barry_rival",
    "rowan_pokedex" => "BlueSinnohPilot.rowan_pokedex"
  }.freeze
  CHOICES = [
    ["TURTWIG", "CHIMCHAR"],
    ["CHIMCHAR", "PIPLUP"],
    ["PIPLUP", "TURTWIG"]
  ].freeze

  def self.check!(test, message)
    raise "[SINNOH QA ENGINE] #{message}" unless test
  end

  def self.mon_species(mon)
    if mon.is_a?(Hash)
      mon[:species] || mon["species"]
    elsif mon.respond_to?(:species)
      mon.species
    end
  end

  def self.mon_level(mon)
    if mon.is_a?(Hash)
      mon[:level] || mon["level"]
    elsif mon.respond_to?(:level)
      mon.level
    end
  end

  def self.string_value(value)
    value.respond_to?(:to_str) ? value.to_str : value.to_s
  end

  def self.validate_trainer!
    check!(defined?(GameData::Trainer), "GameData::Trainer indisponivel")
    check!(defined?(BlueCampaign) && BlueCampaign.respond_to?(:trainer_level),
           "Level cap BlueCampaign ausente")
    CHOICES.each_with_index.map do |(player, opponent), version|
      trainer = GameData::Trainer.get(:BLUE_SINNOH_RIVAL, "Barry", version)
      check!(!trainer.nil?, "Barry #{version} nao existe no GameData compilado")
      party = trainer.respond_to?(:pokemon) ? trainer.pokemon : nil
      check!(party.is_a?(Array) && party.length == 1,
             "Barry #{version}: a primeira batalha exige um inicial")
      species = mon_species(party[0])
      species = species.to_s if species.is_a?(Symbol)
      check!(species == opponent && mon_level(party[0]) == 5,
             "Barry #{version}: especie contra-inicial ou seed PBS incorreto")
      {"version" => version, "player" => player,
       "opponent" => opponent, "pbs_seed_level_only" => 5}
    end
  end

  def self.event_script(event)
    list = event.pages[0].list
    check!(list.is_a?(Array) && list.length == 2,
           "Evento #{event.name}: lista de comandos nao autorizada")
    check!(list[1].code == 0, "Evento #{event.name}: terminador invalido")
    list[0]
  end

  def self.inspect_map!(definition, mapping)
    id = definition.fetch("id")
    check!(id.is_a?(Integer) && (1..599).cover?(id),
           "MapID fora da reserva Sinnoh")
    file = format("Data/Map%03d.rxdata", id)
    check!(File.file?(file) && !File.symlink?(file), "Mapa QA ausente: #{file}")
    check!(respond_to?(:load_data, true) || Kernel.respond_to?(:load_data),
           "Essentials load_data nao disponivel")
    native = load_data(file)
    check!(native.respond_to?(:events) && native.respond_to?(:width) &&
           native.respond_to?(:height), "RPG::Map invalido: #{file}")
    expected = definition.fetch("events")
    check!(expected.is_a?(Array) && expected.length > 0, "Mapa sem eventos planejados")
    values = native.events.values
    check!(values.length == expected.length, "Mapa #{id}: numero de eventos mudou")
    by_name = {}
    values.each do |event|
      check!(event.respond_to?(:name) && !by_name.key?(event.name),
             "Mapa #{id}: evento sem nome/duplicado")
      by_name[event.name] = event
    end
    check!(by_name.keys.sort == expected.map { |row| row.fetch("key") }.sort,
           "Mapa #{id}: nomes dos eventos diferentes")
    count_warp = 0
    starters = []
    count_handlers = []
    expected.each do |row|
      key = row.fetch("key")
      event = by_name.fetch(key)
      check!(event.x == row.fetch("x") && event.y == row.fetch("y"),
             "#{key}: coordenadas alteradas")
      check!(event.pages.is_a?(Array) && event.pages.length == 1,
             "#{key}: paginas extras nao autorizadas")
      page = event.pages[0]
      trigger = row.fetch("trigger") == "touch" ? 1 : 0
      check!(page.trigger == trigger, "#{key}: trigger incorreto")
      opcode = event_script(event)
      case row.fetch("kind")
      when "warp"
        target = mapping.fetch(row.fetch("destination"))
        params = [0, target, row.fetch("arrival_x"), row.fetch("arrival_y"), 2, 0]
        check!(opcode.code == 201 && opcode.parameters == params,
               "#{key}: destino/chegada de warp divergente")
        count_warp += 1
      when "handler", "starter_ball"
        check!(page.graphic.character_name == row.fetch("sprite"),
               "#{key}: sprite fisico divergente")
        script = if row["kind"] == "starter_ball"
                   species = row.fetch("species")
                   check!(%w[TURTWIG CHIMCHAR PIPLUP].include?(species),
                          "#{key}: inicial fora da lista")
                   starters << species
                   "BlueSinnohPilot.choose_starter_from_ball(:#{species})"
                 else
                   handler = row.fetch("handler")
                   check!(HANDLERS.key?(handler), "#{key}: handler nao aprovado")
                   count_handlers << handler
                   HANDLERS.fetch(handler)
                 end
        check!(opcode.code == 355 && opcode.parameters == [script],
               "#{key}: script nao corresponde ao handler original Blue")
      else
        check!(false, "#{key}: evento desconhecido")
      end
    end
    [count_warp, starters, count_handlers]
  end

  # Not an in-game battle test. Never claim 70/90 dynamic level was observed.
  def self.run!
    check!(File.file?(CONFIG) && !File.symlink?(CONFIG),
           "Nao executar fora da copia QA")
    check!(!File.exist?(RIVAL_READY), "Barry ja foi liberado antecipadamente")
    begin
      require "json" unless defined?(JSON)
    rescue LoadError
      check!(false, "Modulo JSON indisponivel no motor Essentials")
    end
    config = JSON.parse(File.read(CONFIG))
    check!(config.is_a?(Hash) && config["schema"] == 1 &&
           config["region"] == "SINNOH" &&
           config["kind"] == "ISOLATED_SINNOH_QA" &&
           config["runtime_playable"] == false,
           "Prova de QA incorreta")
    contract = config.fetch("event_contract")
    check!(contract.is_a?(Array) && contract.length == 9,
           "Contrato dos nove mapas de Sinnoh incompleto")
    mapping = {}
    contract.each do |row|
      symbol, id = row.fetch("symbol"), row.fetch("id")
      check!(!mapping.key?(symbol) && !mapping.value?(id),
             "MapIDs duplicados no contrato de eventos")
      mapping[symbol] = id
    end
    trainers = validate_trainer!
    warps, starters, handlers = 0, [], []
    contract.each do |definition|
      count, found, actions = inspect_map!(definition, mapping)
      warps += count
      starters.concat(found)
      handlers.concat(actions)
    end
    check!(warps == 16 && starters.sort == %w[CHIMCHAR PIPLUP TURTWIG] &&
           handlers.sort == HANDLERS.keys.sort,
           "Sinnoh necessita de 16 portais, 3 Pokebolas e 5 NPCs")
    start = config.fetch("start")
    bedroom = mapping.fetch("SINNOH_PLAYER_BEDROOM")
    check!(start.is_a?(Array) && start.length == 3 && start[0] == bedroom,
           "Novo Jogo nao inicia no quarto verificado")
    check!(defined?(BlueSinnohPilot) &&
           BlueSinnohPilot.respond_to?(:choose_starter_from_ball) &&
           BlueSinnohPilot.respond_to?(:barry_rival),
           "Handlers autorais de Sinnoh nao carregados na engine")
    {
      "schema" => 1, "region" => "SINNOH",
      "mode" => "ENGINE_STATIC_INDEX_AND_EVENTS_PROBE_ONLY",
      "status" => "NATIVE_STRUCTURAL_CHECK_NOT_GAMEPLAY",
      "compile_token" => config.fetch("compile_token"),
      "maps_inspected" => 9, "events_inspected" => 24,
      "warps_inspected" => 16, "physical_starter_balls_inspected" => starters.sort,
      "barry_versions_inspected" => trainers,
      "map_ids" => mapping.values.sort,
      "battle_executed" => false, "dynamic_level_verified" => false,
      "physical_navigation_tested" => false, "save_reload_tested" => false,
      "android_verified" => false, "trainer_sprite_rendered" => false,
      "barry_ready_marker_created" => false, "gameplay_approved" => false
    }
  end
end
