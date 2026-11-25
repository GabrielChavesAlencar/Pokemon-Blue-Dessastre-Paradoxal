# Private Sinnoh QA only: dialogue with no progression or save mutation.
module BlueSinnohF10C
  SPECS = (__F10C_ROWS__).to_h.freeze
  def self.talk(key)
    return false unless defined?(BlueSinnohExperimental) && BlueSinnohExperimental.private_copy?
    return false unless defined?(BlueSinnohPilot) && BlueSinnohPilot.regional_state
    spec=SPECS[key]
    return false unless spec && $game_map && $game_map.map_id==spec[0]
    return false if @busy
    @busy=true
    begin
      spec[2].each { |message| pbMessage(_INTL(message)) }
      true
    ensure
      @busy=false
    end
  rescue StandardError => error
    BlueSinnohPilot.profile_error("f10c_dialogue",error)
    false
  end
end
