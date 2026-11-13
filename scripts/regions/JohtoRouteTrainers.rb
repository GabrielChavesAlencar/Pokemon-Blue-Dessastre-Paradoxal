# Johto OFFLINE 10/12 trainer handlers for private, isolated pilot only.
# Must never be registered in production unless the real engine/pilot has
# compiled and validated all 10 proposed trainer PBS versions.
module BlueJohtoRouteTrainers
  READY = "Data/blue-johto-routes-ready.txt".freeze
  MARKER = "BLUE_JOHTO_ROUTES10_TESTED_READY".freeze
  TEAMS = {
    :JH_ROUTE29_MIKE => [:YOUNGSTER, "Johto Mikey"],
    :JH_ROUTE30_JOEY => [:YOUNGSTER, "Johto Joey"],
    :JH_ROUTE30_DON  => [:BUGCATCHER, "Johto Don"],
    :JH_ROUTE31_WADE => [:BUGCATCHER, "Johto Wade"],
    :JH_ROUTE31_IAN  => [:YOUNGSTER, "Johto Ian"]
  }.freeze

  def self.progress
    return nil unless defined?(BlueJohtoPilot) && BlueJohtoPilot.respond_to?(:progress)
    BlueJohtoPilot.progress
  end

  def self.ready?
    File.file?(READY) && !File.symlink?(READY) &&
      File.read(READY).strip == MARKER &&
      defined?(TrainerBattle) && TrainerBattle.respond_to?(:start) &&
      defined?(BlueStory) && BlueStory.respond_to?(:stage) &&
      defined?(BlueCampaign) && BlueCampaign.respond_to?(:common_level) &&
      BlueCampaign.respond_to?(:wild_level)
  rescue IOError, SystemCallError
    false
  end

  def self.version
    stage = BlueStory.stage
    return nil unless stage.is_a?(Integer) && (0..3).include?(stage)
    stage == 3 ? 1 : 0
  end

  def self.battle(key)
    flags = progress
    return false unless flags && flags.is_a?(Hash)
    key = key.to_sym if key.is_a?(String)
    team = TEAMS[key]
    return false unless team
    fought = flags["route_trainers"]
    return false unless fought.nil? || fought.is_a?(Hash)
    flags["route_trainers"] ||= {}
    return false if flags["route_trainers"][key.to_s]
    unless ready?
      pbMessage(_INTL("Treinador de Johto: batalha aguardando PBS compilado e validado."))
      return false
    end
    chosen = version
    return false unless chosen
    pbMessage(_INTL("Treinador de Johto: Vamos batalhar!"))
    # BlueCampaign/BlueTrainerMoves remain the shared authority for 70/90%,
    # global badges and wild 45%. No custom per-region scaling is applied.
    setBattleRule("canLose")
    won = TrainerBattle.start(team[0], team[1], chosen)
    return false unless won
    flags["route_trainers"][key.to_s] = true
    true
  rescue IOError, SystemCallError
    false
  end
end
