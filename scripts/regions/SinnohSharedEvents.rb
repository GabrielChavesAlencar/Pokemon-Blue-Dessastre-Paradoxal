# Runtime for the Sinnoh layer of the shared Blue-Story world.
module BlueSinnohSharedEvents
  POINTS = "Data/blue-sinnoh-shared.txt".freeze
  RECEIPT = "Data/blue-sinnoh-shared.json".freeze

  def self.map_ids
    return nil unless File.file?(POINTS) && !File.symlink?(POINTS) && File.size(POINTS) < 2048
    return nil unless File.file?(RECEIPT) && !File.exist?("sinnoh-experimental-qa.json")
    raw = File.binread(POINTS)
    # Keep the parsed map set while reading the small marker so removal or
    # replacement takes effect without restarting an existing process.
    return @map_ids if @points == raw
    header, *rows = raw.lines.map(&:strip)
    return nil unless header == "BLUE_SINNOH_SHARED_V1" && rows.length == 4
    return nil unless rows.last.match?(/\A[0-9]+(?:,[0-9]+)*\z/)
    ids = rows.last.split(",").map(&:to_i)
    return nil unless ids.length == 144 && ids == ids.sort.uniq && ids.all? { |id| (442..599).cover?(id) }
    @points, @map_ids = raw, ids.freeze
    @map_ids
  rescue StandardError
    nil
  end

  def self.ready?
    !!map_ids && !File.exist?("Data/blue-compile-request.txt") &&
      defined?(BlueSinnohPilot) && BlueSinnohPilot.all_rival_versions_valid?
  end

  def self.active?
    return false unless $game_map && $PokemonGlobal && $PokemonGlobal.respond_to?(:blue_regions)
    state = $PokemonGlobal.blue_regions
    return false unless state.is_a?(Hash) && state["version"] == 1 && state["current"] == "SINNOH"
    # GameData is loaded once per process. Leave the disk/catalogue checks to
    # availability and map entry, rather than performing them on every step.
    @active_maps ||= map_ids if !@active_maps && ready?
    @active_maps && @active_maps.include?($game_map.map_id)
  end

  def self.enter_map
    @active_maps = ready? ? map_ids : nil
    return unless active?
    BlueSinnohPilot.hide_starter_balls
    BlueSinnohPilot.sync_route_trainers
  end

  module PreserveAuthoredMaps
    def main(*args, &block)
      return super unless BlueSinnohSharedEvents.map_ids
      paths = Dir.glob("Data/Map[0-9][0-9][0-9].rxdata")
      paths.concat(%w[Data/MapInfos.rxdata Data/Tilesets.rxdata Data/map_connections.dat])
      originals = paths.select { |path| File.file?(path) }.to_h { |path| [path, File.binread(path)] }
      begin
        super
      ensure
        originals.each do |path, contents|
          next if File.file?(path) && File.binread(path) == contents
          temp = path + ".blue-sinnoh-compile"
          begin
            File.binwrite(temp, contents)
            File.rename(temp, path)
          ensure
            File.delete(temp) if File.file?(temp)
          end
        end
      end
    end
  end

  def self.bind!
    return false unless defined?(EventHandlers)
    EventHandlers.add(:on_enter_map, :blue_sinnoh_shared_events, proc { |*args| BlueSinnohSharedEvents.enter_map })
    BlueSinnohSafeMovement.install! if defined?(BlueSinnohSafeMovement)
    BlueSinnohForestEdge.install! if defined?(BlueSinnohForestEdge)
    if defined?(Compiler) && !Compiler.singleton_class.ancestors.include?(PreserveAuthoredMaps)
      Compiler.singleton_class.prepend(PreserveAuthoredMaps)
    end
    if defined?(BlueSinnohF12DIntegrated)
      raise "Sinnoh: hooks de campo indisponíveis" unless BlueSinnohF12DIntegrated.bind_pages!
    end
    true
  end
end
