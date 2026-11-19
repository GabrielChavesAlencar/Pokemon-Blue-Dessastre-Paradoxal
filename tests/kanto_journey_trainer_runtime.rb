# Regression for an actual Android crash in Cerulean Gym:
# BlueJourney used to rewrite the Kanto Swimmer Luis into
# "Luis (2v2 Full Power)", which does not exist in Kanto's compiled PBS.
# Mocked native call only; no game binary, source atlas or saves involved.
source = File.expand_path(ARGV.fetch(0))
load source

module BlueCampaign
  def self.active?; $campaign_active; end
end

$game_temp = Struct.new(:battle_rules).new({})
$rules = []
def setBattleRule(value)
  $rules << value
  $game_temp.battle_rules["size"] = value
end

class NativeTrainerBattle
  def self.start_core(*args); args; end
end

class CapturedTrainerBattle < NativeTrainerBattle
  singleton_class.prepend(BlueJourney::TrainerStart)
end

def check(value, message)
  raise "KANTO_JOIPLAY_TRAINER_ID: #{message}" unless value
end

$campaign_active = true

# BlueCampaign is active, but Kanto names are SOURCE PBS identities.
$rules.clear
result = CapturedTrainerBattle.start_core(:BLUE_KANTO_SWIMMER, "Luis", 0)
check(result == [:BLUE_KANTO_SWIMMER, "Luis", 0],
      "the Cerulean Luis identity was rewritten")
check($rules.empty?, "Kanto Swimmer was changed to a legacy double battle")

$rules.clear
check(CapturedTrainerBattle.start_core(:BLUE_KANTO_PICNICKER, "Diana", 0) ==
      [:BLUE_KANTO_PICNICKER, "Diana", 0],
      "Diana was rewritten")
check($rules.empty?, "Diana battle size was changed")

$rules.clear
check(CapturedTrainerBattle.start_core(:BLUE_KANTO_LEADER_MISTY, "Misty", 0) ==
      [:BLUE_KANTO_LEADER_MISTY, "Misty", 0],
      "Misty's native PBS identity changed")
check($rules.empty?, "Misty was forcibly converted into a legacy gym")

$rules.clear
original = [[:BLUE_KANTO_SWIMMER, "Luis", 0]]
check(CapturedTrainerBattle.start_core(original) == [original],
      "nested Kanto team was modified")
check($rules.empty?, "nested Kanto team was forced to doubles")

# String-based regional types must also stay untouched.
$rules.clear
check(CapturedTrainerBattle.start_core("BLUE_KANTO_SWIMMER", "Luis", 0) ==
      ["BLUE_KANTO_SWIMMER", "Luis", 0],
      "string Kanto type lost its native identity")
check($rules.empty?, "string Kanto trainer was forced to doubles")

# The original legacy feature must remain intact outside Kanto.
$rules.clear
result = CapturedTrainerBattle.start_core(:HOENNIAN_ORAS_AROMALADY,
                                          "Luis (1v1 Basic Power)", 0)
check(result == [:HOENNIAN_ORAS_AROMALADY, "Luis (2v2 Full Power)", 0],
      "legacy Full Power roster no longer resolves")
check($rules == ["double"] && $game_temp.battle_rules["expGain"] == true,
      "legacy doubles and EXP were disabled")

# The legacy gym adapter is still completely inactive outside BlueCampaign.
$campaign_active = false
$rules.clear
check(CapturedTrainerBattle.start_core(:HOENNIAN_ORAS_AROMALADY, "Luis", 0) ==
      [:HOENNIAN_ORAS_AROMALADY, "Luis", 0],
      "campaign-disabled battle was rewritten")
check($rules.empty?, "campaign-disabled battle was forced to doubles")

puts "PASS: Kanto Luis/Diana/Misty PBS IDs, nesting, legacy 2v2, campaign off"
