# A single campaign reward per habitat, based on unique owned species in its active table.
class PokemonGlobalMetadata
  attr_accessor :blue_habitat_rewards
end
module BlueHabitatRewards
  def self.claim(area,announce=true)
    return false unless BlueCampaign.active? && !BlueBattleOptions.battle_area?
    state=($PokemonGlobal.blue_habitat_rewards ||= {})
    return false if state[area[:map]]
    seen,caught,total=BlueHabitat.progress(area)
    return false unless total>0 && caught==total
    amount=total*500;return false if $player.money+amount>Settings::MAX_MONEY
    state[area[:map]]={species:total,amount:amount,version:$PokemonGlobal.encounter_version}
    $player.money+=amount
    pbMessage(_INTL('Habitat complete: {1}! {2} Pokémon × $500 = ${3}.',area[:name],total,amount.to_s_formatted)) if announce
    true
  end
  def self.current
    return unless BlueCampaign.active? && $game_map
    list=BlueHabitat.areas;index=BlueHabitatMap.current_index(list)
    claim(list[index]) if index
  end
  def self.install
    EventHandlers.add(:on_end_battle,:blue_habitat_reward,proc { |*args| BlueHabitatRewards.current })
  end
end

# Transparent memo backgrounds must cover the previously open party screen.
module BlueSummaryBackdrop
  def drawPage(*args)
    unless @sprites['blue_opaque_background']
      backdrop=BitmapSprite.new(Graphics.width,Graphics.height,@viewport);backdrop.z=-10
      b=backdrop.bitmap;b.fill_rect(0,0,Graphics.width,Graphics.height,Color.new(247,249,252))
      b.fill_rect(0,0,216,Graphics.height,Color.new(22,62,87));b.fill_rect(0,0,Graphics.width,56,Color.new(225,160,38))
      @sprites['blue_opaque_background']=backdrop
    end
    super
  end
end
