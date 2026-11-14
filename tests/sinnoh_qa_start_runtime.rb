# Isolated QA start proof test. Pure Ruby, fully synthetic, no Game.exe.
require "tmpdir"
require "json"
require "digest"
require "fileutils"

class FakeGlobal
  attr_accessor :blue_regions, :blue_traditional_starters, :blue_campaign_departure
end

class FakeSystem
  attr_accessor :start_map_id, :start_x, :start_y
end

module BlueRegions
  def self.new_state(region)
    {"version" => 1, "current" => region, "initial" => region}
  end
end

module BlueStory
  @history = []
  class << self
    attr_reader :history
    def choose_mode(v)
      @history << v
    end
  end
end

module BlueCampaign
  @history = []
  class << self
    attr_reader :history
    def begin_journey(v)
      @history << v
    end
  end
end

module BlueRegionStart
  class << self
    attr_accessor :new_game
    def select_and_prepare(*_args)
      $original_called += 1
    end
  end
end

$original_called = 0
$PokemonGlobal = FakeGlobal.new
$data_system = FakeSystem.new

def check(value, label)
  raise "SinnohQAStart test failed: #{label}" unless value
end

require File.expand_path(ARGV.fetch(0))
Dir.mktmpdir("sinnoh-qa-start-") do |tmp|
  Dir.chdir(tmp) do
    FileUtils.mkdir_p("Data")
    FileUtils.mkdir_p("PBS")
    required = {
      "Data/MapInfos.rxdata" => "original map infos synthetic",
      "Data/System.rxdata" => "original system synthetic",
      "Data/Map500.rxdata" => "original geometry synthetic",
      "PBS/trainer_types_sinnoh_barry.txt" => "synthetic type",
      "PBS/trainers_sinnoh_barry.txt" => "synthetic teams",
    }
    required.each { |path, data| File.write(path, data) }
    token = "a" * 64
    proof = {
      "schema" => 1,
      "region" => "SINNOH",
      "kind" => "ISOLATED_SINNOH_QA",
      "runtime_playable" => false,
      "compile_token" => token,
      "start" => [500, 10, 11],
      "file_sha256" => required.transform_values { |raw| Digest::SHA256.hexdigest(raw) }
    }
    File.write("Sinnoh qa.json", JSON.generate(proof))

    BlueRegionStart.instance_variable_set(:@new_game, true)
    check(BlueSinnohQAStart.proof.nil?, "uncompiled QA must remain blocked")
    begin
      BlueRegionStart.select_and_prepare
      raise "failed to block missing compilation"
    rescue RuntimeError => e
      raise if e.message == "failed to block missing compilation"
      check(e.message.include?("compile"), "unexpected guard error")
    end
    check($original_called == 0, "unverified QA fell through to Decades")
    check($PokemonGlobal.blue_regions.nil?, "changed state without proof")

    File.write("Data/blue-sinnoh-qa-compiled.txt", "0" * 64)
    check(BlueSinnohQAStart.proof.nil?, "wrong compile proof was accepted")
    File.write("Data/blue-sinnoh-qa-compiled.txt", token + "\n")
    check(BlueSinnohQAStart.proof.nil?,
          "compiled marker alone bypassed engine check")
    engine_report = {
      "schema" => 1,
      "region" => "SINNOH",
      "mode" => "ENGINE_STATIC_INDEX_AND_EVENTS_PROBE_ONLY",
      "status" => "NATIVE_STRUCTURAL_CHECK_NOT_GAMEPLAY",
      "compile_token" => token,
      "maps_inspected" => 9,
      "events_inspected" => 24,
      "warps_inspected" => 16,
      "physical_starter_balls_inspected" => %w[CHIMCHAR PIPLUP TURTWIG],
      "barry_versions_inspected" => [
        {"version" => 0}, {"version" => 1}, {"version" => 2}
      ],
      "gameplay_approved" => false,
      "barry_ready_marker_created" => false
    }
    File.write("Data/blue-sinnoh-qa-engine-check.json", JSON.generate(engine_report))
    check(BlueSinnohQAStart.proof == [500, 10, 11],
          "valid proof was rejected")
    BlueRegionStart.select_and_prepare
    check($PokemonGlobal.blue_regions["current"] == "SINNOH",
          "Sinnoh region state not initialized")
    check(BlueSinnohQAStart.barry_test_authorized?,
          "Validated QA pilot cannot try its own Barry fight")
    check([$data_system.start_map_id, $data_system.start_x, $data_system.start_y] ==
          [500, 10, 11], "wrong safe Twinleaf bedroom spawn")
    check($PokemonGlobal.blue_traditional_starters == true,
          "traditional starter state changed")
    check(BlueStory.history == [:story], "story mode not prepared")
    check(BlueCampaign.history == [false], "campaign not initialized")
    check($original_called == 0, "new game invoked old-region selector")

    $PokemonGlobal.blue_regions["current"] = "JOHTO"
    check(!BlueSinnohQAStart.barry_test_authorized?,
          "QA Barry leaked into Johto")
    $PokemonGlobal.blue_regions["current"] = "SINNOH"
    engine_report["warps_inspected"] = 15
    File.write("Data/blue-sinnoh-qa-engine-check.json", JSON.generate(engine_report))
    check(BlueSinnohQAStart.proof.nil?, "invalid native report was accepted")
    check(!BlueSinnohQAStart.barry_test_authorized?,
          "QA Barry ignored a changed warp report")
    engine_report["warps_inspected"] = 16
    File.write("Data/blue-sinnoh-qa-engine-check.json", JSON.generate(engine_report))
    check(BlueSinnohQAStart.proof == [500, 10, 11], "fixed report not accepted")

    # Existing save loads never invoke a QA new-game reset.
    BlueRegionStart.instance_variable_set(:@new_game, false)
    before = Marshal.dump($PokemonGlobal.blue_regions)
    BlueRegionStart.select_and_prepare
    check($original_called == 1, "existing save did not use native behavior")
    check(Marshal.dump($PokemonGlobal.blue_regions) == before,
          "existing regional state changed on load")

    File.write("Data/Map500.rxdata", "tampered terrain")
    check(BlueSinnohQAStart.proof.nil?, "changed map hash was accepted")
    File.write("Data/Map500.rxdata", required["Data/Map500.rxdata"])
    File.delete("PBS/trainers_sinnoh_barry.txt")
    check(BlueSinnohQAStart.proof.nil?, "absent Barry PBS was accepted")
  end
end

puts "SINNOH_QA_START_SAVE_AND_PBS_GUARDS_OK"
