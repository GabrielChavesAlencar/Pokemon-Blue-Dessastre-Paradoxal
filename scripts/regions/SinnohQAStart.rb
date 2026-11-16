# Sinnoh isolated-QA only. Installed only in a distinct .blue-work copy.
# Never load from the main Decades/Kanto/Johto/Hoenn installation.
# This gate DOES NOT unlock Barry. Native gameplay still requires manual QA.
module BlueSinnohQAStart
  CONFIG = "Sinnoh qa.json".freeze
  COMPILED = "Data/blue-sinnoh-qa-compiled.txt".freeze
  ENGINE_REPORT = "Data/blue-sinnoh-qa-engine-check.json".freeze
  EXPECTED_FILES = %w[Data/MapInfos.rxdata Data/System.rxdata
                       PBS/trainer_types_sinnoh_barry.txt
                       PBS/trainers_sinnoh_barry.txt].freeze

  def self.proof
    return nil unless File.file?(CONFIG) && !File.symlink?(CONFIG)
    return nil unless File.file?(COMPILED) && !File.symlink?(COMPILED)
    return nil unless File.file?(ENGINE_REPORT) && !File.symlink?(ENGINE_REPORT)
    begin
      require "json" unless defined?(JSON)
      require "digest" unless defined?(Digest::SHA256)
    rescue LoadError
      return nil
    end
    data = JSON.parse(File.read(CONFIG))
    return nil unless data.is_a?(Hash) && data["schema"] == 1 &&
                      data["region"] == "SINNOH" &&
                      data["kind"] == "ISOLATED_SINNOH_QA" &&
                      data["runtime_playable"] == false
    token = data["compile_token"]
    return nil unless token.is_a?(String) &&
                      token.match?(/\A[a-f0-9]{64}\z/) &&
                      File.read(COMPILED).strip == token
    start = data["start"]
    return nil unless start.is_a?(Array) && start.length == 3 &&
                      start.all? { |x| x.is_a?(Integer) } &&
                      (1..599).cover?(start[0]) &&
                      start[1] >= 0 && start[2] >= 0
    native = JSON.parse(File.read(ENGINE_REPORT))
    return nil unless native.is_a?(Hash) &&
                      native["region"] == "SINNOH" &&
                      native["mode"] == "ENGINE_STATIC_INDEX_AND_EVENTS_PROBE_ONLY" &&
                      native["status"] == "NATIVE_STRUCTURAL_CHECK_NOT_GAMEPLAY" &&
                      native["compile_token"] == token &&
                      native["maps_inspected"] == 9 &&
                      native["events_inspected"] == 24 &&
                      native["warps_inspected"] == 16 &&
                      native["physical_starter_balls_inspected"] == %w[CHIMCHAR PIPLUP TURTWIG] &&
                      native["barry_versions_inspected"].is_a?(Array) &&
                      native["barry_versions_inspected"].length == 3 &&
                      native["gameplay_approved"] == false &&
                      native["barry_ready_marker_created"] == false
    files = data["file_sha256"]
    required = EXPECTED_FILES + [format("Data/Map%03d.rxdata", start[0])]
    return nil unless files.is_a?(Hash) && required.all? { |file| files.key?(file) }
    return nil unless files.all? do |file, hash|
      hash.is_a?(String) && hash.match?(/\A[a-f0-9]{64}\z/) &&
        File.file?(file) && !File.symlink?(file) &&
        Digest::SHA256.file(file).hexdigest == hash
    end
    start
  rescue JSON::ParserError, IOError, SystemCallError, ArgumentError
    nil
  end

  # Permission to TRY Barry only inside the verified, isolated QA copy.
  # Not native battle acceptance and never a release-marker substitute.
  def self.barry_test_authorized?
    return false unless defined?($PokemonGlobal) && $PokemonGlobal &&
                        $PokemonGlobal.respond_to?(:blue_regions)
    current = $PokemonGlobal.blue_regions
    return false unless current.is_a?(Hash) &&
                        current["version"] == 1 &&
                        current["current"] == "SINNOH"
    return false if current.key?("initial") && current["initial"] != "SINNOH"
    !proof.nil?
  rescue IOError, SystemCallError, ArgumentError, TypeError
    false
  end

  module Override
    def select_and_prepare(*args)
      # Existing saves still use the native reload path, but new QA games
      # must not silently enter another region when globals are absent.
      unless @new_game
        # Do not rewrite a loaded foreign-region save through QA's start path.
        if defined?($PokemonGlobal) && $PokemonGlobal &&
           $PokemonGlobal.respond_to?(:blue_regions)
          saved = $PokemonGlobal.blue_regions
          if saved && (!saved.is_a?(Hash) || saved["version"] != 1 ||
             saved["current"] != "SINNOH" ||
             (saved.key?("initial") && saved["initial"] != "SINNOH"))
            raise "Sinnoh QA: save de outra região incompatível; carregamento bloqueado"
          end
        end
        return super
      end
      raise "Sinnoh QA: estado global ausente; Novo Jogo bloqueado" unless
        defined?($PokemonGlobal) && $PokemonGlobal &&
        $PokemonGlobal.respond_to?(:blue_regions=)
      old_state = $PokemonGlobal.blue_regions if
        $PokemonGlobal.respond_to?(:blue_regions)
      if old_state && (!old_state.is_a?(Hash) ||
         old_state["version"] != 1 ||
         old_state["current"] != "SINNOH" ||
         (old_state.key?("initial") && old_state["initial"] != "SINNOH"))
        raise "Sinnoh QA: save regional incompatível; não substituir por Sinnoh"
      end
      start = BlueSinnohQAStart.proof
      raise "Sinnoh QA: compile os tres PBS de Barry antes de Novo Jogo" unless start
      raise "Sinnoh QA: motor regional nao carregado" unless
        defined?(BlueRegions) && defined?(BlueStory) && defined?(BlueCampaign)
      raise "Sinnoh QA: perfil regional invalido" unless
        BlueRegions.respond_to?(:new_state)
      raise "Sinnoh QA: mapa de inicialização ausente" unless
        defined?($data_system) && $data_system &&
        $data_system.respond_to?(:start_map_id=) &&
        $data_system.respond_to?(:start_x=) &&
        $data_system.respond_to?(:start_y=)
      $PokemonGlobal.blue_regions = BlueRegions.new_state("SINNOH")
      BlueStory.choose_mode(:story)
      BlueCampaign.begin_journey(false)
      $PokemonGlobal.blue_traditional_starters = true
      $PokemonGlobal.blue_campaign_departure = false
      $data_system.start_map_id, $data_system.start_x, $data_system.start_y = start
      nil
    end
  end

  BlueRegionStart.singleton_class.prepend(Override) if defined?(BlueRegionStart)
end
