# mkxp provides Zlib; the CLI Ruby test needs the standard library loaded.
require "zlib" unless defined?(Zlib)
# This override is loaded only by the standalone Johto copy.
module BlueJohtoPilotStart
  MARKER = "Data/blue-johto-qa-start.txt".freeze

  def self.spawn
    return nil unless defined?(BlueRegionStart) && File.file?("Johto pilot.json")
    return nil unless File.file?(MARKER) && !File.symlink?(MARKER)
    values = File.read(MARKER).strip.split(",")
    return nil unless values.length == 5 && values.shift == "BLUE_JOHTO_QA_START_V2"
    return nil unless values.all? { |value| value.match?(/\A\d+\z/) }
    point = values.map(&:to_i)
    checksum = point.pop
    return nil unless (600..681).cover?(point[0])
    path = sprintf("Data/Map%03d.rxdata", point[0])
    return nil unless pbRgssExists?(path) && Zlib.crc32(File.binread(path)) == checksum
    point
  rescue IOError, SystemCallError
    nil
  end

  module IsolatedOverride
    def select_and_prepare
      super
      return unless @new_game && BlueJohtoPilot.progress && File.file?("Johto pilot.json")
      pbChangePlayer(3)
      $game_player.refresh_charset
      $game_player.transparent = false
      BlueJohtoPilot.progress["profile_pending"] = true
    end

    def johto_spawn
      BlueJohtoPilotStart.spawn || super
    end
  end

  BlueRegionStart.singleton_class.prepend(IsolatedOverride) if defined?(BlueRegionStart)
end
