# Pure Ruby fake GameData tests for READ-ONLY probe; does not run Game.exe.
require "tmpdir"

module GameData
  module Trainer
    @table = {}
    class << self
      attr_accessor :table
      def get(type, name, version)
        @table[[type, name, version]]
      end
    end
  end
end

module BlueCampaign
  def self.trainer_level(_trainer = nil, _party = nil)
    5
  end
end

FakeTrainer = Struct.new(:pokemon)
def check(cond, message)
  raise message unless cond
end

require File.expand_path(ARGV.fetch(0))
Dir.mktmpdir("sinnoh-native-probe-") do |dir|
  Dir.chdir(dir) do
    GameData::Trainer.table = {
      [:BLUE_SINNOH_RIVAL, "Barry", 0] =>
        FakeTrainer.new([{:species => :CHIMCHAR, :level => 5}]),
      [:BLUE_SINNOH_RIVAL, "Barry", 1] =>
        FakeTrainer.new([{:species => :PIPLUP, :level => 5}]),
      [:BLUE_SINNOH_RIVAL, "Barry", 2] =>
        FakeTrainer.new([{:species => :TURTWIG, :level => 5}]),
    }
    begin
      BlueSinnohBarryNativeProbe.run!
      raise "Accepted missing pilot.json"
    rescue RuntimeError => error
      check(error.message.include?("copia isolada"), "Wrong no-pilot rejection")
    end

    File.write("Sinnoh pilot.json", "{}")
    success = BlueSinnohBarryNativeProbe.run!
    check(success[:compiled_teams_indexed] == 3, "Wrong count")
    check(success[:teams].map { |v| v[:rival_species] } ==
          [:CHIMCHAR, :PIPLUP, :TURTWIG], "Wrong species")
    [:battle_executed, :effective_level_checked_in_battle,
     :trainer_sprite_checked, :save_load_checked, :joi_play_checked,
     :ready_marker_created, :safe_to_enable_barry, :gameplay_approved].each do |key|
      check(success[key] == false, "Probe claimed unearned native proof for #{key}")
    end
    check(!File.exist?("Data/blue-sinnoh-rival-ready.txt"),
          "Probe incorrectly wrote a ready marker")

    bad = GameData::Trainer.table[[:BLUE_SINNOH_RIVAL, "Barry", 1]]
    original = bad.pokemon
    bad.pokemon = [{:species => :CHIMCHAR, :level => 5}]
    begin
      BlueSinnohBarryNativeProbe.run!
      raise "Accepted wrong Barry species"
    rescue RuntimeError => error
      check(error.message.include?("contra-inicial"), "Wrong species rejection")
    end
    bad.pokemon = original

    bad = GameData::Trainer.table[[:BLUE_SINNOH_RIVAL, "Barry", 2]]
    bad.pokemon = [{:species => :TURTWIG, :level => 7}]
    begin
      BlueSinnohBarryNativeProbe.run!
      raise "Accepted wrong seed"
    rescue RuntimeError => error
      check(error.message.include?("seed PBS"), "Wrong seed rejection")
    end
    bad.pokemon = [{:species => :TURTWIG, :level => 5}]

    FileUtils.mkdir_p("Data") if defined?(FileUtils)
    Dir.mkdir("Data") unless File.directory?("Data")
    File.write("Data/blue-sinnoh-rival-ready.txt", "BLUE_SINNOH_BARRY_V1_READY")
    begin
      BlueSinnohBarryNativeProbe.run!
      raise "Accepted pre-existing ready marker"
    rescue RuntimeError => error
      check(error.message.include?("ja existe"), "Wrong marker rejection")
    end
  end
end
puts "SINNOH_NATIVE_BARRY_PROBE_GUARDS_OK"
