# This override is loaded only by the standalone Johto copy.
module BlueJohtoPilotStart
  MARKER = "Data/blue-johto-qa-start.txt".freeze

  def self.spawn
    return nil unless defined?(BlueRegionStart) && File.file?("Johto pilot.json")
    return nil unless File.file?(MARKER) && !File.symlink?(MARKER)
    values = File.read(MARKER).strip.split(",")
    return nil unless values.length == 4 && values.shift == "BLUE_JOHTO_QA_START_V1"
    return nil unless values.all? { |value| value.match?(/\A\d+\z/) }
    point = values.map(&:to_i)
    return nil unless (600..681).cover?(point[0]) && pbRgssExists?(sprintf("Data/Map%03d.rxdata", point[0]))
    point
  rescue IOError, SystemCallError
    nil
  end

  module IsolatedOverride
    def johto_spawn
      BlueJohtoPilotStart.spawn || super
    end
  end

  BlueRegionStart.singleton_class.prepend(IsolatedOverride) if defined?(BlueRegionStart)
end
