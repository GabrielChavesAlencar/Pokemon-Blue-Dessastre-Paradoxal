# Verify two trainer pages and one-crystal-per-badge without game/graphics.
class PokemonGlobalMetadata;end
def check(v,msg);raise msg unless v;end
require ARGV.fetch(0)
require ARGV.fetch(1)
require ARGV.fetch(2)

kanto=BlueRegions.new_state("KANTO")
check(BlueRegionalCards.data(kanto,0)[:local]==0,"Kanto begins with zero local badges")
check(BlueRegionalCards.data(kanto,0)[:stage]==0,"zero emeralds means beginner")
check(BlueRegions.award(kanto,"KANTO","BOULDER"),"first Boulder award")
check(!BlueRegions.award(kanto,"KANTO","BOULDER"),"duplicate Boulder")
check(BlueRegions.award(kanto,"KANTO","CASCADE"),"Cascade award")
record=BlueRegionalCards.data(kanto,1)
check(record[:current]=="KANTO" && record[:local]==2,"local page must contain only Kanto")
check(record[:global]==3 && record[:stage]==1,"native + Kanto count in Intermediate")
check(record[:milestones].length==8,"Kanto has eight named badges")
check(record[:acquired]==%w[BOULDER CASCADE],"local badges retain registry order")
check(record[:rows].find{|row|row[0]=="KANTO"}[2]==2,"world page includes Kanto progress")
check(record[:rows].find{|row|row[0]=="DECADES"}[2]==1,"world page includes native Decades")

decades=BlueRegions.new_state("DECADES")
record=BlueRegionalCards.data(decades,9)
check(record[:current]=="DECADES" && record[:local]==9,"Decades local crystals are native")
check(record[:global]==9 && record[:stage]==2,"nine emeralds is advanced")
check(BlueRegionalCards.data(kanto,9)[:global]==11,"cross-region world total")
check(BlueRegionalCards.data(kanto,9)[:stage]==3,"11 global emeralds is Master")
check(BlueRegionalCards.data(kanto,9)[:rows].length==10,"all circuit regions visible")

# Exercise the native Trainer Card entry point, not just the detached page data.
# Kanto must open its card immediately; Decades must keep its original UI.
class PokemonTrainerCardScreen
  def pbStartScreen
    :native_card
  end
end
class PokemonGlobalMetadata
  attr_accessor :blue_regions
end
module BlueBattleOptions
  def self.battle_area?
    false
  end
end
module MenuHandlers
  def self.add(*_args)
  end
end
def _INTL(value)
  value
end
$PokemonGlobal = PokemonGlobalMetadata.new
$PokemonGlobal.blue_regions = kanto
$card_pages = []
BlueRegionalCards.define_singleton_method(:open) { |page = 0| $card_pages << page }
BlueRegionalCards.install
check(PokemonTrainerCardScreen.new.pbStartScreen == [0],
      "Native Trainer Card opens Kanto badge page")
check($card_pages == [0], "Native card routed to Kanto page zero")
$PokemonGlobal.blue_regions = decades
check(PokemonTrainerCardScreen.new.pbStartScreen == :native_card,
      "Native Decades Trainer Card remains unchanged")
puts "Trainer regional/global cards: badge totals, entry point, Decades isolation OK"
