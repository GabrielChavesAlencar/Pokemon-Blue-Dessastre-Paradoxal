# Local pools only. Rod access is anchored to FRLG/Emerald fishing tables;
# later/custom species use an explicit catch-rate/BST fallback, not official odds.
module BlueFishing
  RODS=[:OldRod,:GoodRod,:SuperRod].freeze
  MASSES=[{1=>100},{1=>30,2=>70},{1=>10,2=>75,3=>15}].freeze
  OFFICIAL={MAGIKARP:1,HORSEA:2,KRABBY:2,SHELLDER:3,GYARADOS:3,PSYDUCK:3,GOLDEEN:1,POLIWAG:2,SEAKING:3,DRATINI:3,DRAGONAIR:3,POLIWHIRL:3,SEADRA:3,QWILFISH:3,GRIMER:3,STARYU:3,SLOWPOKE:3,KINGLER:3,REMORAID:2,SLOWBRO:3,CORPHISH:2,TENTACOOL:1,WAILMER:2,SHARPEDO:3,BARBOACH:2,CARVANHA:2,TENTACRUEL:3,WHISCASH:3,LUVDISC:2,CORSOLA:3,OCTILLERY:3,FEEBAS:3}.freeze
  def self.rank(species)
    data=GameData::Species.get(species)
    return OFFICIAL[data.species] if OFFICIAL.key?(data.species)
    # Starters, fossils, low-catch-rate and unusually strong local species stay rare.
    return 3 if data.catch_rate<90 || data.base_stats.values.sum>450
    return 1 if data.catch_rate>=190 && data.base_stats.values.sum<=350 && data.get_baby_species==data.species
    2
  end
  def self.tables(types)
    copy=types.transform_values { |slots| slots.map(&:dup) }
    pool=RODS.flat_map { |rod| types[rod] || [] }
    return copy if pool.empty?
    # A slot repeated across native rod tables must not multiply its local weight.
    pool=pool.uniq
    RODS.each_with_index do |rod,index|
      totals=Hash.new(0);pool.each { |slot| totals[rank(slot[1])]+=slot[0] }
      copy[rod]=pool.filter_map do |slot|
        rarity=rank(slot[1]);mass=MASSES[index][rarity];next unless mass
        weight=[(slot[0]*mass*100.0/totals.fetch(rarity)).round,1].max
        [weight,*slot.drop(1)]
      end.sort_by { |slot| -slot[0] }
    end
    copy
  end
end
