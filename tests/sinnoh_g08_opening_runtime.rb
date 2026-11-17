# G08 — run the real authored SinnohPilot.rb and inert CH13/14 bridges.
# Nine synthetic encounters (three starters x true/false/nil), not Game.exe QA.
require "tmpdir"

class G08Global
  attr_accessor :blue_regions
end
class G08Player
  attr_accessor :party, :has_pokedex
  attr_reader :heals
  def initialize
    @party=[]
    @has_pokedex=false
    @heals=0
  end
  def heal_party
    @heals += 1
  end
end
module GameData
  module Trainer
    @entries = {
      0 => [{species: :CHIMCHAR, level: 5}],
      1 => [{species: :PIPLUP, level: 5}],
      2 => [{species: :TURTWIG, level: 5}]
    }
    class << self
      attr_accessor :entries
      def get(type, name, version)
        return nil unless type == :BLUE_SINNOH_RIVAL && name == "Barry"
        team=@entries[version]
        team && Struct.new(:pokemon).new(team)
      end
    end
  end
end
module TrainerBattle
  @calls=[]
  class << self
    attr_reader :calls
    def start(*args)
      @calls << args
      $battle_result
    end
  end
end
def _INTL(s,*_args);s;end
def pbMessage(s);$messages << s;end
def setBattleRule(s);$rules << s;end
def pbAddPokemonSilent(species,level)
  return false unless $grant_allowed
  $player.party << [species,level]
  true
end
def check(condition,label)
  raise "SINNOH_G08_OFFLINE_RUNTIME: #{label}" unless condition
end
def fresh
  $PokemonGlobal=G08Global.new
  $PokemonGlobal.blue_regions={
    "version"=>1, "current"=>"SINNOH", "initial"=>"SINNOH"
  }
  $player=G08Player.new
  $messages=[]
  $rules=[]
  $grant_allowed=true
  $battle_result=nil
  TrainerBattle.calls.clear
end

load File.expand_path(ARGV.fetch(0))
load File.expand_path(ARGV.fetch(1))
load File.expand_path(ARGV.fetch(2))
check(BlueSinnohIntroContracts::VERIFIED_NATIVE_HANDLERS.empty?,
      "unverified native intro bridge acquired a handler")
check(BlueSinnohStarterContracts::VERIFIED_NATIVE_SOURCES.empty?,
      "unverified native ball bridge acquired a handler")
matchups={
  :TURTWIG=>[:CHIMCHAR,0,:SN_BALL_TURTWIG],
  :CHIMCHAR=>[:PIPLUP,1,:SN_BALL_CHIMCHAR],
  :PIPLUP=>[:TURTWIG,2,:SN_BALL_PIPLUP]
}
check(BlueSinnohPilot::RIVAL_CHOICES == matchups.transform_values { |v| v.take(2) },
      "source rival counter choices changed")
check(BlueSinnohPilot::RIVAL_READY == "Data/blue-sinnoh-rival-ready.txt",
      "real game ready marker location changed")

Dir.mktmpdir("sinnoh-g08-offline-") do |tmp|
  Dir.chdir(tmp) do
    Dir.mkdir("Data")
    matchups.each do |selected,(counter,version,ball_key)|
      [nil,false,true].each do |outcome|
        fresh
        state=$PokemonGlobal.blue_regions
        check(BlueSinnohIntroContracts.preview(state)==:native_events_unverified,
              "intro bridge falsely approved event")
        check(!BlueSinnohPilot.rowan_briefcase,"Rowan skipped mother and Barry")
        check(!BlueSinnohPilot.choose_starter_from_ball(selected),
              "received starter before Rowan")
        check(!BlueSinnohPilot.rowan_pokedex,"Dex before rival")
        check(BlueSinnohPilot.mother,"mother did not progress")
        check(BlueSinnohPilot.barry_intro,"Barry introduction did not progress")
        check(BlueSinnohPilot.rowan_briefcase,"Rowan intro did not progress")
        check(BlueSinnohStarterContracts::BALLS.fetch(selected.to_s).first==ball_key.to_s,
              "physical ball key mismatch")
        check(BlueSinnohStarterContracts.preview(state,selected.to_s)==:native_event_missing,
              "unverified physical event was accepted")

        # The failed grant must not mutate the regional story or the party.
        $grant_allowed=false
        untouched=Marshal.dump(state)
        check(!BlueSinnohPilot.choose_starter_from_ball(selected),
              "failed Pokemon engine grant accepted")
        check(Marshal.dump(state)==untouched && $player.party.empty?,
              "failed grant mutated state")
        $grant_allowed=true
        check(BlueSinnohPilot.choose_starter_from_ball(selected),
              "physical starter grant failed")
        check($player.party==[[selected,5]],
              "physical ball gave incorrect Pokemon or seed")
        check(BlueSinnohPilot.starter==selected,"selected starter was not persisted")
        check(BlueSinnohPilot.rival_species==counter &&
              BlueSinnohPilot.rival_version==version,"rival matchup mismatch")
        check(!BlueSinnohPilot.choose_starter,"Rowan dialog gave another choice")
        check(!BlueSinnohPilot.choose_starter_from_ball(selected),
              "duplicate physical starter accepted")
        (matchups.keys - [selected]).each do |other|
          check(!BlueSinnohPilot.choose_starter_from_ball(other),
                "second ball granted alternate starter")
        end
        check($player.party.length==1,"second ball changed player party")

        # A compiled-looking fixture is NOT sufficient: no release marker,
        # no authorized native QA probe. Only a temporary isolated marker can
        # exercise the runtime's later branch; it never enters the repo/game.
        check(!File.exist?(BlueSinnohPilot::RIVAL_READY),
              "synthetic marker leaked across cases")
        check(!BlueSinnohPilot.barry_rival,"rival ran without marker/probe")
        check(TrainerBattle.calls.empty?,"battle started before authorization")
        marker=BlueSinnohPilot::RIVAL_READY
        File.write(marker,BlueSinnohPilot::RIVAL_PROOF)
        begin
          saved_team=GameData::Trainer.entries[version]
          GameData::Trainer.entries[version]=[{species: :RATTATA, level: 5}]
          check(!BlueSinnohPilot.barry_rival,"wrong rival species was allowed")
          GameData::Trainer.entries[version]=[{species: counter, level: 7}]
          check(!BlueSinnohPilot.barry_rival,"wrong PBS seed level was allowed")
          GameData::Trainer.entries[version]=[
            {species: counter, level: 5}, {species: counter, level: 5}
          ]
          check(!BlueSinnohPilot.barry_rival,"two-Pokemon seed was allowed")
          check(TrainerBattle.calls.empty?,"invalid PBS invoked battle")
          GameData::Trainer.entries[version]=saved_team

          $battle_result=outcome
          check(BlueSinnohPilot.barry_rival == !outcome.nil?,
                "wrong handling of true/false/nil battle")
          check(TrainerBattle.calls==[[:BLUE_SINNOH_RIVAL,"Barry",version]],
                "battle used wrong version")
          check($rules==["canLose"],"canLose missing or duplicated")
          if outcome.nil?
            check(!BlueSinnohPilot.rival_fought?,"nil result advanced story")
            check($player.heals==0,"nil result healed party")
            check(!$player.has_pokedex &&
                  !BlueSinnohPilot.rowan_pokedex,"nil result awarded Dex")
            $battle_result=true
            check(BlueSinnohPilot.barry_rival,"retry after nil was blocked")
            check(TrainerBattle.calls.length==2,"retry did not start new battle")
          end
          check(BlueSinnohPilot.rival_fought?,"completed battle not committed")
          check($player.heals==1,"completed battle did not heal once")
          check(!BlueSinnohPilot.barry_rival,"rival repeated after completion")
          check(BlueSinnohPilot.rowan_pokedex,"Dex not granted after battle")
          check($player.has_pokedex,"real player Dex field not updated")
          check(!BlueSinnohPilot.rowan_pokedex,"duplicate Pokedex grant accepted")

          # Simulate save/load and travel: never grant a second starter or
          # write the Sinnoh story while another region is active.
          snapshot=Marshal.dump(state)
          $PokemonGlobal.blue_regions=Marshal.load(snapshot)
          current=$PokemonGlobal.blue_regions
          check(BlueSinnohPilot.starter==selected,"reload lost starter")
          check(current["sinnoh_pilot"]["pokedex_received"]==true,
                "reload lost Dex checkpoint")
          %w[KANTO JOHTO HOENN DECADES].each do |region|
            current["current"]=region
            before=Marshal.dump(current)
            check(!BlueSinnohPilot.choose_starter_from_ball(selected),
                  "foreign region duplicated starter")
            check(!BlueSinnohPilot.barry_rival,
                  "foreign region started Barry battle")
            check(!BlueSinnohPilot.rowan_pokedex,"foreign region granted Dex")
            check(Marshal.dump(current)==before,
                  "foreign region Save state modified by Sinnoh handlers")
          end
          current["current"]="SINNOH"
          check(!BlueSinnohPilot.choose_starter_from_ball(selected),
                "return travel reopened chosen ball")
          check(BlueSinnohIntroContracts.preview(current)==:complete_offline_only,
                "finished story was marked playable")
        ensure
          File.delete(marker) if File.file?(marker)
        end
      end
    end
    check(!File.exist?(BlueSinnohPilot::RIVAL_READY),
          "marker from offline test was left behind")
  end
end
puts "SINNOH_G08_NINE_OPENING_SCENARIOS_NO_NATIVE_APPROVAL_OK"
