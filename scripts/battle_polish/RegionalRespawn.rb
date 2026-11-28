# Region-aware native blackout checkpoint for the Blue Story campaign.
# All battles still use Essentials' pbStartOver (healing, transfer, gameover).
# Only a stale Pokemon Center from ANOTHER region is replaced.
module BlueRegionalRespawn
  REGIONS = %w[DECADES KANTO JOHTO HOENN SINNOH].freeze
  KANTO_CENTER_SOURCE = 11  # FRLG Viridian City, first real Pokemon Center
  KANTO_ROCK_TUNNEL_CENTER_SOURCE = 88
  KANTO_LAVENDER_CENTER_SOURCE = 94
  HOENN_CENTER_SOURCE = 13  # Oldale Town, first real Pokemon Center

  def self.state
    return nil unless defined?($PokemonGlobal) && $PokemonGlobal &&
                      $PokemonGlobal.respond_to?(:blue_regions)
    stored = $PokemonGlobal.blue_regions
    return nil unless stored.is_a?(Hash) && stored["version"] == 1 &&
                      REGIONS.include?(stored["current"])
    return nil if defined?(BlueBattleLab) && BlueBattleLab::ACTIVE
    stored
  end

  def self.checkpoint
    return nil unless defined?($PokemonGlobal) && $PokemonGlobal
    return nil unless $PokemonGlobal.respond_to?(:pokecenterMapId)
    [ $PokemonGlobal.pokecenterMapId, $PokemonGlobal.pokecenterX,
      $PokemonGlobal.pokecenterY, $PokemonGlobal.pokecenterDirection ]
  end

  def self.map_exists?(id)
    return false unless id.is_a?(Integer) && id > 0
    path = sprintf("Data/Map%03d.rxdata", id)
    if defined?(pbRgssExists?)
      pbRgssExists?(path)
    else
      File.file?(path)
    end
  end

  def self.valid?(point)
    point.is_a?(Array) && point.length == 4 &&
      point.all? { |value| value.is_a?(Integer) } &&
      point[1] >= 0 && point[2] >= 0 &&
      [2, 4, 6, 8].include?(point[3]) && map_exists?(point[0])
  end

  # The installed FRLG map index is real, remapped at build time; never
  # hard-code Blue's Kanto MapID or infer a Center from a city outdoor tile.
  def self.kanto_maps
    file = File.file?("Kanto pilot.json") ? "Kanto pilot.json" :
           "Data/blue-kanto-install.json"
    return {} unless File.file?(file)
    text = File.read(file)
    # Keys in the "maps" table are original numeric FRLG MapIDs.
    table = text.match(/"maps"\s*:\s*\{([^}]*)\}/m)
    return {} unless table
    Hash[table[1].scan(/"(\d+)"\s*:\s*(\d+)/).map { |a, b| [a.to_i, b.to_i] }]
  rescue IOError, SystemCallError
    {}
  end

  def self.hoenn_maps
    return {} unless defined?(BlueHoennPilot) && BlueHoennPilot.respond_to?(:metadata)
    BlueHoennPilot.metadata[1] || {}
  rescue StandardError
    {}
  end

  def self.johto_map_ids
    return [] unless defined?(BlueRegionStart) && BlueRegionStart.respond_to?(:johto_install_proof)
    proof = BlueRegionStart.johto_install_proof
    return [] unless proof
    # Only fully verified Johto installations are accepted. No fabricated
    # range of map IDs can mark a foreign Pokemon Center as Johto.
    files = proof["file_hashes"]
    return [] unless files.is_a?(Hash)
    files.keys.filter_map { |file| file[/\AData\/Map(\d+)\.rxdata\z/, 1]&.to_i }
  rescue StandardError
    []
  end

  def self.region_map?(region, map_id)
    return false unless map_exists?(map_id)
    case region
    when "KANTO" then kanto_maps.value?(map_id)
    when "HOENN" then hoenn_maps.value?(map_id)
    when "JOHTO" then johto_map_ids.include?(map_id)
    when "SINNOH" then sinnoh_map_ids.include?(map_id)
    when "DECADES"
      # A legacy Decades checkpoint is native only when it is not in
      # any registered imported region.
      return false if kanto_maps.value?(map_id) || hoenn_maps.value?(map_id) ||
                      johto_map_ids.include?(map_id) || sinnoh_map_ids.include?(map_id)
      # A verified installed Decades game has native MapInfos entries.
      info = defined?($data_mapinfos) && $data_mapinfos && $data_mapinfos[map_id]
      !!info
    else false
    end
  end

  def self.sinnoh_map_ids
    return [] unless defined?(BlueSinnohSharedEvents)
    BlueSinnohSharedEvents.map_ids || []
  end

  def self.healing_spot(map_id)
    return nil unless map_exists?(map_id) && defined?(GameData::MapMetadata) &&
                      GameData::MapMetadata.respond_to?(:try_get)
    info = GameData::MapMetadata.try_get(map_id)
    raw = info && info.respond_to?(:healing_spot) && info.healing_spot
    point = raw.is_a?(Array) && raw.length == 3 ? raw + [2] : raw
    valid?(point) ? point : nil
  rescue StandardError
    nil
  end

  def self.map_id_named(pattern)
    return nil unless defined?($data_mapinfos) && $data_mapinfos
    $data_mapinfos.each_with_index do |info, id|
      return id if info && info.respond_to?(:name) &&
                   info.name.to_s.match?(pattern) && map_exists?(id)
    end
    nil
  end

  def self.center_point_from_name(pattern)
    id = map_id_named(pattern)
    return nil unless id
    # A town's metadata can specify the actual nurse recovery location.
    healing_spot(id)
  end

  def self.fallback(region)
    case region
    when "KANTO"
      id = kanto_maps[KANTO_CENTER_SOURCE]
      point = [id, 7, 8, 2] if id
      valid?(point) ? point : nil
    when "HOENN"
      id = hoenn_maps[HOENN_CENTER_SOURCE]
      point = [id, 8, 8, 2] if id
      valid?(point) ? point : nil
    when "DECADES"
      if defined?(BlueRegionTravel) && BlueRegionTravel.respond_to?(:decades_city_map_id)
        city = BlueRegionTravel.decades_city_map_id
        return healing_spot(city) if healing_spot(city)
      end
      # Native MapInfos may name the inside of Cherryhill's first Center.
      center_point_from_name(/Cherryhill.*(?:Pokemon|Pok[eé]mon|Centro|Center)/i) ||
        (defined?(BlueRegionTravel) && BlueRegionTravel.respond_to?(:decades_town_point) ?
         BlueRegionTravel.decades_town_point : nil)
    when "JOHTO"
      # New Bark has no Pokemon Center. Prefer a verified healing spot for
      # Cherrygrove; never invent an interior map from a Johto preview.
      id = map_id_named(/\ACherrygrove(?: City)?\z/i)
      point = id && healing_spot(id)
      return point if valid?(point)
      point = center_point_from_name(/Cherrygrove.*(?:Pokemon|Pok[eé]mon|Centro|Center)/i)
      return point if valid?(point)
      defined?(BlueRegionStart) && BlueRegionStart.respond_to?(:johto_town_point) ?
        BlueRegionStart.johto_town_point : nil
    when "SINNOH"
      sandgem = map_id_named(/\ASandgem Town\z/i)
      point = healing_spot(sandgem) if sinnoh_map_ids.include?(sandgem)
      return point if valid?(point) && region_map?(region, point[0])
      points = BlueRegionStart.sinnoh_shared_points if defined?(BlueRegionStart)
      points && points[1]
    end
  end

  def self.real_center?(region, id)
    return false unless region_map?(region, id)
    if region == "KANTO"
      # Remapped Centers must work even when map-info names are
      # not loaded by the runtime. Resolve the original identity, not Map606
      # or a localized display name. The native nurse still sets the point.
      maps = kanto_maps
      return true if [KANTO_CENTER_SOURCE,KANTO_ROCK_TUNNEL_CENTER_SOURCE,KANTO_LAVENDER_CENTER_SOURCE].any? { |sid| maps[sid] == id }
    end
    return true if region == "HOENN" && hoenn_maps[HOENN_CENTER_SOURCE] == id
    info = defined?($data_mapinfos) && $data_mapinfos && $data_mapinfos[id]
    info && info.respond_to?(:name) &&
      info.name.to_s.match?(/(?:Pokemon|Pok[eé]mon|Pok[eé])\s*(?:Center|Centre|Centro)|Centro\s*(?:Pokemon|Pok[eé]mon)|PokeCenter/i)
  end

  def self.remember!
    stored = state
    return unless stored && defined?($game_map) && $game_map
    point = checkpoint
    region = stored["current"]
    return unless valid?(point) && point[0] == $game_map.map_id &&
                  real_center?(region, point[0])
    (stored["regional_pokecenters"] ||= {})[region] = point.dup
    stored["regional_pokecenter_owner"] = region
  end

  def self.before_blackout!
    stored = state
    return unless stored
    current = stored["current"]
    native = checkpoint
    owner = stored["regional_pokecenter_owner"]
    # A native center in the current region still wins, including legacy
    # saves that do not yet have the new per-region dictionary. An old
    # Pallet/Oak checkpoint also remains valid while playing Kanto.
    return if valid?(native) && (owner == current ||
      (owner.nil? && region_map?(current, native[0])))
    remembered = stored["regional_pokecenters"]
    saved = remembered.is_a?(Hash) ? remembered[current] : nil
    candidate = if valid?(saved) && region_map?(current, saved[0])
                  saved
                else
                  fallback(current)
                end
    return unless valid?(candidate)
    # Only update the four native checkpoint coordinates; pbStartOver is
    # responsible for the actual healing/transfer. No extra scene calls,
    # Hall of Fame flags, badge changes or second heal.
    $PokemonGlobal.pokecenterMapId = candidate[0]
    $PokemonGlobal.pokecenterX = candidate[1]
    $PokemonGlobal.pokecenterY = candidate[2]
    $PokemonGlobal.pokecenterDirection = candidate[3]
    stored["regional_pokecenter_owner"] = current
  end

  module NativeCheckpoints
    def pbSetPokemonCenter(*args, &block)
      result = super
      BlueRegionalRespawn.remember!
      result
    end
    def pbStartOver(*args, &block)
      BlueRegionalRespawn.before_blackout!
      super
    end
  end

  def self.install
    return if @installed
    Object.prepend(NativeCheckpoints) unless Object.ancestors.include?(NativeCheckpoints)
    @installed = true
  end
end
