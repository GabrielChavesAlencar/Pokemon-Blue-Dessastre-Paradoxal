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
    profile_token = "abcdef123456"
    profile = {
      "title" => "Sinnoh QA " + profile_token,
      "dataPathApp" => "Sinnoh-QA-" + profile_token,
      "dataPathOrg" => "Dessastre-Sinnoh-QA-" + profile_token
    }
    config = {
      "windowTitle" => profile["title"],
      "dataPathApp" => profile["dataPathApp"],
      "dataPathOrg" => profile["dataPathOrg"]
    }
    File.write("mkxp.json", JSON.generate(config))
    File.write("Game.ini", ["[Game]", "Title=#{profile['title']}", ""].join(10.chr))
    proof = {
      "schema" => 1,
      "profile" => profile,
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

    # S11: a tampered save namespace must block even a valid engine report.
    config["dataPathApp"] = "Decades Main"
    File.write("mkxp.json", JSON.generate(config))
    check(BlueSinnohQAStart.proof.nil?, "foreign save namespace accepted")
    config["dataPathApp"] = profile["dataPathApp"]
    File.write("mkxp.json", JSON.generate(config))
    check(BlueSinnohQAStart.proof == [500, 10, 11], "restored private namespace denied")

    # S11: legacy saves with no BlueRegions origin must NEVER delegate to
    # the main Decades loader. This is distinct from a new Sinnoh save.
    BlueRegionStart.instance_variable_set(:@new_game, false)
    existing_state = Marshal.dump($PokemonGlobal.blue_regions)
    $PokemonGlobal.blue_regions = nil
    before_legacy = $original_called
    begin
      BlueRegionStart.select_and_prepare
      raise "Legacy save with missing region was loaded"
    rescue RuntimeError => error
      raise if error.message == "Legacy save with missing region was loaded"
      check(error.message.include?("incompatível"), "missing region guard error")
    end
    check($original_called == before_legacy, "legacy save reached original loader")
    check($PokemonGlobal.blue_regions.nil?, "legacy save unexpectedly initialized")
    $PokemonGlobal.blue_regions = Marshal.load(existing_state)

    # Existing save loads never invoke a QA new-game reset.
    BlueRegionStart.instance_variable_set(:@new_game, false)
    before = Marshal.dump($PokemonGlobal.blue_regions)
    BlueRegionStart.select_and_prepare
    check($original_called == 1, "existing save did not use native behavior")
    check(Marshal.dump($PokemonGlobal.blue_regions) == before,
          "existing regional state changed on load")

    # CH07: an unavailable global on *new game* must not silently open
    # Decades/Johto. An existing-save load still delegates to super.
    previous_global = $PokemonGlobal
    $PokemonGlobal = nil
    BlueRegionStart.instance_variable_set(:@new_game, true)
    original_count = $original_called
    begin
      BlueRegionStart.select_and_prepare
      raise "QA new-game incorrectly delegated to native flow"
    rescue RuntimeError => error
      raise if error.message == "QA new-game incorrectly delegated to native flow"
      check(error.message.include?("estado global ausente"),
            "new-game failure message not explanatory")
    end
    check($original_called == original_count,
          "new QA game delegated to another region")
    $PokemonGlobal = previous_global
    check(BlueSinnohQAStart.proof == [500, 10, 11],
          "QA proof not preserved after failing new game")
    $PokemonGlobal.blue_regions["initial"] = "JOHTO"
    check(!BlueSinnohQAStart.barry_test_authorized?,
          "a foreign initial-region record authorized Barry")
    $PokemonGlobal.blue_regions["initial"] = "SINNOH"
    check(BlueSinnohQAStart.barry_test_authorized?,
          "verified Sinnoh save was incorrectly blocked")

    # CH10: a foreign Johto/Decades save must never be passed to the
    # original selector or overwritten when entering QA New Game.
    BlueRegionStart.instance_variable_set(:@new_game, false)
    $PokemonGlobal.blue_regions["current"] = "JOHTO"
    prior_count = $original_called
    foreign_state = Marshal.dump($PokemonGlobal.blue_regions)
    begin
      BlueRegionStart.select_and_prepare
      raise "Foreign saved region unexpectedly loaded"
    rescue RuntimeError => error
      raise if error.message == "Foreign saved region unexpectedly loaded"
      check(error.message.include?("incompatível"), "foreign save error not clear")
    end
    check($original_called == prior_count, "foreign save delegated to native loader")
    check(Marshal.dump($PokemonGlobal.blue_regions) == foreign_state,
          "foreign save was changed during blocked load")
    BlueRegionStart.instance_variable_set(:@new_game, true)
    begin
      BlueRegionStart.select_and_prepare
      raise "Foreign save replaced with Sinnoh during new game"
    rescue RuntimeError => error
      raise if error.message == "Foreign save replaced with Sinnoh during new game"
      check(error.message.include?("incompatível"), "foreign new game not blocked")
    end
    check($original_called == prior_count, "foreign new game fell back")
    check(Marshal.dump($PokemonGlobal.blue_regions) == foreign_state,
          "foreign new game erased save")
    $PokemonGlobal.blue_regions["current"] = "SINNOH"
    $PokemonGlobal.blue_regions["initial"] = "SINNOH"
    # Missing initial origin must remain blocked even if current is SINNOH.
    initial_value = $PokemonGlobal.blue_regions.delete("initial")
    BlueRegionStart.instance_variable_set(:@new_game, false)
    before_missing_initial = $original_called
    begin
      BlueRegionStart.select_and_prepare
      raise "Save without initial region was loaded"
    rescue RuntimeError => error
      raise if error.message == "Save without initial region was loaded"
      check(error.message.include?("incompatível"), "missing initial guard error")
    end
    check($original_called == before_missing_initial, "missing initial delegated to native")
    $PokemonGlobal.blue_regions["initial"] = initial_value
    check(BlueSinnohQAStart.proof == [500, 10, 11],
          "Sinnoh restored after foreign save test")

    File.write("Data/Map500.rxdata", "tampered terrain")
    check(BlueSinnohQAStart.proof.nil?, "changed map hash was accepted")
    File.write("Data/Map500.rxdata", required["Data/Map500.rxdata"])
    File.delete("PBS/trainers_sinnoh_barry.txt")
    check(BlueSinnohQAStart.proof.nil?, "absent Barry PBS was accepted")
  end
end

puts "SINNOH_QA_START_SAVE_AND_PBS_GUARDS_OK"
