# Sinnoh isolated-QA only. Installed only in a distinct .blue-work copy.
# Never load from the main Decades/Kanto/Johto/Hoenn installation.
# This gate DOES NOT unlock Barry. Native gameplay still requires manual QA.
module BlueSinnohQAStart
  CONFIG = "Sinnoh qa.json".freeze
  COMPILED = "Data/blue-sinnoh-qa-compiled.txt".freeze
  EXPECTED_FILES = %w[Data/MapInfos.rxdata Data/System.rxdata
                       PBS/trainer_types_sinnoh_barry.txt
                       PBS/trainers_sinnoh_barry.txt].freeze

  def self.proof
    return nil unless File.file?(CONFIG) && !File.symlink?(CONFIG)
    return nil unless File.file?(COMPILED) && !File.symlink?(COMPILED)
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
    files = data["file_sha256"]
    required = EXPECTED_FILES + [format("Data/Map%03d.rxdata", start[0])]
    return nil unless files.is_a?(Hash) && required.all? do |file|
      hash = files[file]
      hash.is_a?(String) && hash.match?(/\A[a-f0-9]{64}\z/) &&
        File.file?(file) && !File.symlink?(file) &&
        Digest::SHA256.file(file).hexdigest == hash
    end
    start
  rescue JSON::ParserError, IOError, SystemCallError, ArgumentError
    nil
  end

  module Override
    def select_and_prepare(*args)
      return super unless @new_game && defined?($PokemonGlobal) &&
                          $PokemonGlobal
      start = BlueSinnohQAStart.proof
      raise "Sinnoh QA: compile os tres PBS de Barry antes de Novo Jogo" unless start
      raise "Sinnoh QA: motor regional nao carregado" unless
        defined?(BlueRegions) && defined?(BlueStory) && defined?(BlueCampaign)
      raise "Sinnoh QA: perfil regional invalido" unless
        BlueRegions.respond_to?(:new_state)
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
