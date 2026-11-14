# Pure-Ruby fake RPG Map/GameData contract checks; NO actual Essentials, ROM or save.
require "json"
require "tmpdir"
require "fileutils"

Event = Struct.new(:name, :x, :y, :pages)
Page = Struct.new(:trigger, :graphic, :list)
Graphic = Struct.new(:character_name)
Cmd = Struct.new(:code, :parameters)
Map = Struct.new(:width, :height, :events)
Trainer = Struct.new(:pokemon)

module GameData
  module Trainer
    TABLE = {}
    def self.get(type, name, version)
      TABLE[[type, name, version]]
    end
  end
end

module BlueCampaign
  def self.trainer_level(*_args)
    1
  end
end

module BlueSinnohPilot
  def self.choose_starter_from_ball(_species)
    true
  end
  def self.barry_rival
    false
  end
end

def check(condition, message)
  raise "SINNOH QA PROBE TEST: #{message}" unless condition
end

def load_data(path)
  $maps.fetch(path)
end

require File.expand_path(ARGV.fetch(0))
template = JSON.parse(File.read(File.expand_path(ARGV.fetch(1))))
contract = template.fetch("maps").each_with_index.map do |row, index|
  map_id = 500 + index
  {
    "symbol" => row.fetch("symbol"), "id" => map_id,
    "events" => row.fetch("events").each_with_index.map do |event, ev_id|
      data = {
        "key" => event.fetch("key"), "kind" => event.fetch("kind"),
        "x" => 1 + ev_id, "y" => 2 + ev_id,
        "trigger" => event.fetch("trigger")
      }
      case event.fetch("kind")
      when "warp"
        data.update("destination" => event.fetch("destination"),
                    "arrival_x" => 4, "arrival_y" => 5)
      when "handler"
        data.update("sprite" => "NPC_Test",
                    "handler" => event.fetch("handler"))
      when "starter_ball"
        data.update("sprite" => "Ball_Test",
                    "species" => event.fetch("species"))
      end
      data
    end
  }
end
mapping = contract.to_h { |item| [item.fetch("symbol"), item.fetch("id")] }
$maps = {}
contract.each do |definition|
  events = {}
  definition.fetch("events").each_with_index do |spec, index|
    script = if spec["kind"] == "handler"
               BlueSinnohQAProbe::HANDLERS.fetch(spec["handler"])
             elsif spec["kind"] == "starter_ball"
               "BlueSinnohPilot.choose_starter_from_ball(:#{spec["species"]})"
             end
    opcode = if script
               Cmd.new(355, [script])
             else
               Cmd.new(201, [0, mapping.fetch(spec.fetch("destination")),
                             spec.fetch("arrival_x"), spec.fetch("arrival_y"), 2, 0])
             end
    character = spec["sprite"] || ""
    page = Page.new(spec["trigger"] == "touch" ? 1 : 0,
                    Graphic.new(character), [opcode, Cmd.new(0, [])])
    events[index+1] = Event.new(spec["key"], spec["x"], spec["y"], [page])
  end
  $maps[format("Data/Map%03d.rxdata", definition["id"])] = Map.new(80, 70, events)
end
BlueSinnohQAProbe::CHOICES.each_with_index do |pair, index|
  GameData::Trainer::TABLE[[:BLUE_SINNOH_RIVAL, "Barry", index]] =
    Trainer.new([{:species => pair[1].to_sym, :level => 5}])
end

Dir.mktmpdir("sinnoh-qa-probe-") do |tmp|
  Dir.chdir(tmp) do
    FileUtils.mkdir_p("Data")
    contract.each do |definition|
      File.write(format("Data/Map%03d.rxdata", definition["id"]), "fixture")
    end
    proof = {
      "schema" => 1, "region" => "SINNOH",
      "kind" => "ISOLATED_SINNOH_QA", "runtime_playable" => false,
      "compile_token" => "c"*64, "event_contract" => contract,
      "start" => [500, 3, 4]
    }
    File.write("Sinnoh qa.json", JSON.generate(proof))
    report = BlueSinnohQAProbe.run!
    check(report["status"] == "NATIVE_STRUCTURAL_CHECK_NOT_GAMEPLAY",
          "wrong report status")
    check([report["maps_inspected"], report["events_inspected"],
           report["warps_inspected"]] == [9, 24, 16], "wrong map/warp count")
    check(report["physical_starter_balls_inspected"] ==
          %w[CHIMCHAR PIPLUP TURTWIG], "three starter balls missing")
    check(report["barry_versions_inspected"].map { |r| r["opponent"] } ==
          %w[CHIMCHAR PIPLUP TURTWIG], "Barry counter starters wrong")
    %w[battle_executed dynamic_level_verified physical_navigation_tested
       save_reload_tested android_verified trainer_sprite_rendered
       barry_ready_marker_created gameplay_approved].each do |key|
      check(report[key] == false, "probe falsely approved #{key}")
    end
    check(!File.exist?("Data/blue-sinnoh-rival-ready.txt"),
          "probe created forbidden Barry marker")

    def expect_failure(message)
      begin
        BlueSinnohQAProbe.run!
        raise "Probe incorrectly accepted #{message}"
      rescue RuntimeError => error
        raise if error.message.start_with?("Probe incorrectly accepted")
      end
    end

    # Changing only the staged event command, not the expected spec, is rejected.
    map = $maps["Data/Map505.rxdata"]
    event = map.events.values.find { |e| e.name == "SN_BALL_PIPLUP" }
    original = event.pages[0].list[0].parameters.dup
    event.pages[0].list[0].parameters[0] =
      "BlueSinnohPilot.choose_starter_from_ball(:CHARMANDER)"
    expect_failure("illegal starter callback")
    event.pages[0].list[0].parameters = original

    warp = $maps["Data/Map500.rxdata"].events.values.first
    original_warp = warp.pages[0].list[0].parameters.dup
    warp.pages[0].list[0].parameters[1] = 800
    expect_failure("legacy Johto map ID")
    warp.pages[0].list[0].parameters = original_warp

    bad = GameData::Trainer::TABLE[[:BLUE_SINNOH_RIVAL, "Barry", 2]]
    bad.pokemon = [{:species => :CHIMCHAR, :level => 5}]
    expect_failure("Barry wrong counter-starter")
    bad.pokemon = [{:species => :TURTWIG, :level => 5}]

    File.write("Data/blue-sinnoh-rival-ready.txt", "premature")
    expect_failure("early Barry ready marker")
    File.delete("Data/blue-sinnoh-rival-ready.txt")

    File.delete("Data/Map507.rxdata")
    expect_failure("missing route data")
  end
end
puts "SINNOH_QA_ENGINE_MAPS_EVENTS_BARRY_GUARDS_OK"
