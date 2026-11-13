# Synthetic Ruby harness for Johto routes 29–31, no Game.exe/real PBS.
require "tmpdir"
module BlueJohtoPilot
  class << self
    attr_accessor :mock_flags
    def progress
      return nil unless $active_region == "JOHTO"
      @mock_flags ||= {}
    end
  end
end
module BlueStory
  class << self
    attr_accessor :stage
  end
end
module BlueCampaign
  def self.common_level(_party = nil); 5; end
  def self.wild_level(_party = nil); 3; end
end
module TrainerBattle
  @history = []
  class << self
    attr_accessor :result
    attr_reader :history
    def start(*args)
      @history << args
      @result
    end
  end
end
$messages, $battle_rules, $active_region = [], [], "JOHTO"
def _INTL(message, *_args); message; end
def pbMessage(message); $messages << message; nil; end
def setBattleRule(rule); $battle_rules << rule; end
def assert(test, description)
  raise description unless test
end

require ARGV.fetch(0)
Dir.mktmpdir("johto-routes10-") do |tmp|
  Dir.chdir(tmp) do
    Dir.mkdir("Data")
    BlueStory.stage = 0
    assert(!BlueJohtoRouteTrainers.battle(:JH_ROUTE29_MIKE),
           "No PBS marker should block battle")
    assert(TrainerBattle.history.empty?, "Battle started without a marker")
    File.write(BlueJohtoRouteTrainers::READY, "FAKE")
    assert(!BlueJohtoRouteTrainers.battle(:JH_ROUTE29_MIKE), "Fake ready marker allowed")
    assert(TrainerBattle.history.empty?, "Fake marker started battle")
    # Harness-only marker; never written to the installed game.
    File.write(BlueJohtoRouteTrainers::READY,BlueJohtoRouteTrainers::MARKER+"\n")
    TrainerBattle.result = true
    BlueJohtoRouteTrainers::TEAMS.each do |key,(kind,name)|
      BlueJohtoPilot.mock_flags = {}
      $active_region = "KANTO"
      assert(!BlueJohtoRouteTrainers.battle(key),"Kanto executed Johto trainer")
      $active_region = "JOHTO"
      BlueStory.stage = 1
      assert(BlueJohtoRouteTrainers.battle(key),"Normal trainer battle missing")
      assert(TrainerBattle.history.last == [kind,name,0],"Normal variant incorrect")
      assert(!BlueJohtoRouteTrainers.battle(key),"Trainer rewarded twice")
      assert(BlueJohtoPilot.progress["route_trainers"][key.to_s]==true,
             "Normal victory not persisted")
      assert(!BlueJohtoRouteTrainers.battle(key),"Save repeat allowed")
      # Replay on another clean save in Master difficulty.
      BlueJohtoPilot.mock_flags = {}
      BlueStory.stage = 3
      assert(BlueJohtoRouteTrainers.battle(key),"Master trainer battle missing")
      assert(TrainerBattle.history.last==[kind,name,1],"Master team PBS index incorrect")
      assert(BlueJohtoPilot.progress["route_trainers"][key.to_s],
             "Master victory not persisted")
    end
    BlueJohtoPilot.mock_flags = {}
    BlueStory.stage = 0
    TrainerBattle.result = false
    assert(!BlueJohtoRouteTrainers.battle(:JH_ROUTE30_JOEY),
           "Lost battle must not mark trainer defeated")
    assert(!BlueJohtoPilot.progress["route_trainers"]["JH_ROUTE30_JOEY"],
           "Defeat rewarded prematurely")
    TrainerBattle.result = true
    assert(BlueJohtoRouteTrainers.battle(:JH_ROUTE30_JOEY),
           "Replay after loss should work")
    saved = Marshal.load(Marshal.dump(BlueJohtoPilot.progress))
    BlueJohtoPilot.mock_flags = saved
    assert(!BlueJohtoRouteTrainers.battle(:JH_ROUTE30_JOEY),
           "Save/reload gave a duplicate battle")
    assert(!BlueJohtoRouteTrainers.battle(:UNKNOWN_TRAINER),
           "Unrecognized trainer ID enabled a battle")
    $active_region = "DECADES"
    assert(!BlueJohtoRouteTrainers.battle(:JH_ROUTE30_JOEY),
           "Decades got Johto route events")
  end
end
puts "JOHTO_ROUTES10_OFFLINE_RUBY_GUARDS_OK"
