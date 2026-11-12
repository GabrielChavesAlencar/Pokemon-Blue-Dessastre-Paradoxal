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
puts "Trainer regional/global cards: badge totals and difficulty OK"
