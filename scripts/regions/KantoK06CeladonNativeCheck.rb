# Disposable Game.exe proof. UI inputs are stubbed; collision, native event
# interpreter, actual bag, player money and gift state are not mocked.
module KantoK06CeladonNativeCheck
  N = KantoK05CityNativeCheck
  C = KantoNativeCheck
  def self.truth(value,label)
    raise "Celadon services: #{label}" unless value
    value
  end

  def self.run
    SaveData.initialize_bootup_values
    spawn = BlueRegionStart.kanto_spawn
    truth(BlueRegionStart.kanto_compact_maps(spawn)&.length == 182 &&
          BlueRegionStart.request_initial("KANTO"), "182-map readiness gate rejected")
    Game.start_new
    truth(BlueKantoPilot.kanto_current?, "normal new-game hook did not start Kanto")
    $player.party.replace([Pokemon.new(:BULBASAUR,20)])
    $game_system.encounter_disabled = true
    picks = []
    confirmed = true
    captured_stock = []
    Object.send(:define_method,:pbMessage) { |_text,choices=nil,*_args| choices.is_a?(Array) ? picks.shift : nil }
    Object.send(:define_method,:pbConfirmMessage) { |*_args| confirmed }
    Object.send(:define_method,:pbPokemonMart) do |stock,*_args|
      captured_stock << stock.map { |item| GameData::Item.get(item).id }
    end
    ids = [114,*(117..123),*(125..128)].to_h { |sid| [sid,BlueKantoPilot.kanto_map_id(sid)] }
    truth(ids.values.all?, "missing authorized city interiors")
    truth((129..135).none? { |sid| BlueKantoPilot.kanto_map_id(sid) }, "later Rocket maps installed early")

    doors = []
    door = lambda do |from,eid,to,anchor,landing|
      line = [from,eid,to,anchor,landing]
      File.open("Data/blue-kanto-k06-celadon-trace.txt","a") { |f| f.puts(line.inspect) }
      result = N.door!(ids.fetch(from),ids.fetch(to),eid,anchor,landing)
      doors << line
      result
    end
    [
      [14,117,[11,20],[2,14],1,[11,20]],
      [15,117,[15,20],[10,14],2,[15,20]],
      [4,125,[37,35],[6,9],1,[37,35]],
      [27,126,[49,35],[4,9],1,[49,35]],
      [26,127,[41,35],[4,7],1,[41,35]],
      [24,128,[30,17],[12,18],3,[30,17]],
      [34,128,[30,10],[2,2],5,[30,10]]
    ].each do |eid,to,city,inside,exit,returned|
      door.call(114,eid,to,city,inside)
      door.call(to,exit,114,inside,returned)
    end

    stairs = [
      [117,4,118,[2,14],[3,2]],
      [118,3,119,[3,2],[9,2]],
      [119,3,120,[9,2],[3,2]],
      [120,3,121,[3,2],[9,2]],
      [121,3,122,[9,2],[22,10]],
      [122,1,121,[22,10],[3,2]],
      [121,2,120,[3,2],[9,2]],
      [120,2,119,[9,2],[3,2]],
      [119,2,118,[3,2],[9,2]],
      [118,2,117,[9,2],[4,2]]
    ]
    stairs.each { |leg| door.call(*leg) }

    (117..121).each do |floor|
      door.call(floor,floor == 117 ? 3 : 1,123,[6,2],[2,5])
      picks << -1
      N.service!(ids[123],[2,5],2)
      door.call(123,1,floor,[2,5],[6,2])
      door.call(floor,floor == 117 ? 3 : 1,123,[6,2],[2,5])
      selected = 117 + (floor-116)%5
      picks << selected-117
      N.service!(ids[123],[2,5],2)
      door.call(123,1,selected,[2,5],[6,2])
    end

    [[118,5],[118,6],[120,5],[121,5],[121,6]].each do |floor,event|
      N.service!(ids.fetch(floor),[6,2],event)
    end
    truth(captured_stock.length == 5 && captured_stock[0] == [:TM05,:TM15,:TM28,:TM31,:TM43,:TM45] &&
          captured_stock[1].include?(:MAXREPEL) && captured_stock[2].include?(:FIRESTONE) &&
          captured_stock[3].include?(:HPUP) && captured_stock[4].include?(:XATTACK), "native clerk catalogue drift")
    roof = ids.fetch(122)
    roof_service = ->(id) { N.service!(roof,[22,10],id) }
    $player.money = 199
    picks << 0
    roof_service.call(2)
    truth($player.money == 199 && !$bag.has?(:FRESHWATER),"sold a drink without funds")
    $player.money = 850
    picks << -1
    roof_service.call(2)
    truth($player.money == 850 && !$bag.has?(:FRESHWATER),"cancel charged money")
    [$player.money, 650, 350].each_with_index do |amount,i|
      truth($player.money == amount,"wrong running vending balance")
      picks << i
      roof_service.call(2)
    end
    truth($player.money == 0,"wrong vending total")
    confirmed = false
    roof_service.call(6)
    truth($bag.has?(:FRESHWATER) && !$bag.has?(:TM16),"exchange cancelled after mutating")
    confirmed = true
    [[:FRESHWATER,:TM16],[:SODAPOP,:TM20],[:LEMONADE,:TM33]].each do |drink,tm|
      roof_service.call(6)
      truth(!$bag.has?(drink) && $bag.quantity(tm) == 1,"exchange failed for #{tm}")
    end
    $bag.add(:FRESHWATER,1)
    roof_service.call(6)
    truth($bag.quantity(:TM16) == 1 && $bag.quantity(:FRESHWATER) == 1,"roof reward repeated")

    N.service!(ids[125],[6,9],5)
    N.service!(ids[125],[6,9],5)
    truth($bag.quantity(:COINCASE)==1,"Coin Case was not unique")
    N.service!(ids[128],[12,18],1)
    N.service!(ids[128],[12,18],1)
    truth($bag.quantity(:TEA)==1,"Tea was not unique")
    $map_factory.setup(ids[128])
    gift = $game_map.events.fetch(23)
    gift_anchor = [gift.x,gift.y+1]
    confirmed = false
    N.service!(ids[128],gift_anchor,23)
    truth($player.party.length == 1,"declined Eevee entered party")
    confirmed = true
    2.times { N.service!(ids[128],gift_anchor,23) }
    received = $player.party.select { |mon| mon.species == :EEVEE }
    truth(received.length == 1 && received.first.level == 25,"Eevee reward missing, duplicated or wrong level")

    [108,112].each do |sid|
      $map_factory.setup(BlueKantoPilot.kanto_map_id(sid))
      truth($game_map.events.fetch(2).list.none? { |command| command.code == 201 },"Tea activated Saffron too early")
    end
    truth(picks.empty?, "test choice was not consumed")
    File.write("Data/blue-kanto-k06-celadon-native-proof.txt",
      {"doors"=>doors,"stock"=>captured_stock,"vending_total"=>850,
       "unique_roof_tms"=>3,"unique_coin_case_tea_eevee"=>true,
       "saffron_closed"=>true,"next_sublot_active"=>false,"manual_playthrough"=>false}.inspect)
    puts "KANTO_K06_CELADON_NATIVE_SERVICES_OK"
  end
end
