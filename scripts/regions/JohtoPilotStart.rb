# Loaded only by the COPIED, experimental .blue-work/johto-pilot installation.
# Never include this plugin in the main game/. It cannot make Johto releasable.
require "json"
require "digest"

module BlueJohtoPilotStart
  PROOF = "Data/blue-johto-pilot-proof.json".freeze
  PILOT_MARKER = "Johto pilot.json".freeze

  def self.spawn
    return nil unless defined?(BlueRegionStart)
    return nil unless File.file?(PILOT_MARKER) && !File.symlink?(PILOT_MARKER)
    return nil unless File.file?(PROOF) && !File.symlink?(PROOF)
    marker = JSON.parse(File.read(PILOT_MARKER))
    proof = JSON.parse(File.read(PROOF))
    return nil unless marker.is_a?(Hash) && proof.is_a?(Hash)
    return nil unless marker["kind"] == "ISOLATED_JOHTO_TEST" &&
                      proof["schema"] == 1 && proof["region"] == "JOHTO" &&
                      proof["status"] == "EXPERIMENTAL_UNTESTED" &&
                      proof["can_install"] == false &&
                      marker["archive_sha256"] == proof["archive_sha256"] &&
                      proof["archive_sha256"].is_a?(String) &&
                      proof["archive_sha256"].match?(/\A[a-f0-9]{64}\z/)
    start = proof["start"]
    return nil unless start.is_a?(Array) && start.length == 3 &&
                      start.all? { |v| v.is_a?(Integer) } &&
                      (600..999).include?(start[0]) && start[1] >= 0 && start[2] >= 0
    hashes = proof["file_hashes"]
    map_name = sprintf("Data/Map%03d.rxdata", start[0])
    required = ["Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
                "Data/System.rxdata", map_name,
                "PBS/trainer_types_johto.txt", "PBS/trainers_johto.txt"]
    return nil unless hashes.is_a?(Hash) && required.all? do |path|
      expected = hashes[path]
      expected.is_a?(String) && expected.match?(/\A[a-f0-9]{64}\z/) &&
        File.file?(path) && !File.symlink?(path) &&
        Digest::SHA256.file(path).hexdigest == expected
    end
    return nil unless defined?(pbRgssExists?) && pbRgssExists?(map_name)
    # EXPERIMENTAL, NOT VERIFIED_PLAYABLE. Production proof remains untouched.
    start
  rescue JSON::ParserError, IOError, SystemCallError, ArgumentError
    nil
  end

  module IsolatedOverride
    def johto_spawn
      BlueJohtoPilotStart.spawn || super
    end
  end

  # Only the test-copy plugin prepends this scope. RegionStart's normal
  # 13-check VERIFIED_PLAYABLE gate is NOT changed in Kanto/Decades/main game.
  BlueRegionStart.singleton_class.prepend(IsolatedOverride) if defined?(BlueRegionStart)
end
