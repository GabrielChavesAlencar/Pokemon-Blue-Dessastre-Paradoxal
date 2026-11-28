# Blue-authored elevator. State is stored in one namespaced save field and only
# accessible while on a configured store floor or within the cabin.
class PokemonGlobalMetadata
  attr_accessor :blue_kanto_celadon_floor
end

module BlueKantoCeladonServices
  FLOORS = (117..121).freeze
  CABIN = 123

  def self.at?(source)
    $game_map && $PokemonGlobal && BlueKantoPilot.kanto_current? &&
      $game_map.map_id == BlueKantoPilot.kanto_map_id(source)
  end

  def self.enter_cabin(source)
    return false unless FLOORS.cover?(source) && at?(source)
    $PokemonGlobal.blue_kanto_celadon_floor = source
    true
  end

  def self.select_floor
    return false unless at?(CABIN)
    options = FLOORS.map { |floor| BlueKantoPilot.t("{1}F","{1}º andar",floor-116) }
    options << BlueKantoPilot.t("Cancel","Cancelar")
    selection = pbMessage(BlueKantoPilot.t("Which floor?","Qual andar?"), options, -1)
    return false unless selection.is_a?(Integer) && selection.between?(0,FLOORS.size-1)
    $PokemonGlobal.blue_kanto_celadon_floor = FLOORS.begin+selection
    true
  end

  def self.take_exit?(source)
    return false unless FLOORS.cover?(source) && at?(CABIN)
    floor = $PokemonGlobal.blue_kanto_celadon_floor
    return false unless source == (floor.is_a?(Integer) && FLOORS.cover?(floor) ? floor : FLOORS.begin)
    $PokemonGlobal.blue_kanto_celadon_floor = nil
    true
  end

  DRINKS = { FRESHWATER: 200, SODAPOP: 300, LEMONADE: 350 }.freeze
  EXCHANGES = { FRESHWATER: :TM16, SODAPOP: :TM20, LEMONADE: :TM33 }.freeze

  def self.say(en,pt,*args)
    pbMessage(BlueKantoPilot.t(en,pt,*args))
  end

  def self.item_name(item)
    GameData::Item.get(item).name
  end

  def self.gift_ledger
    BlueKantoPilot.progress["celadon_services_gifts"] ||= {}
  end

  def self.vend
    return false unless at?(122) && $player && $bag
    options = DRINKS.map { |item,price| "#{item_name(item)} - $#{price}" }
    options << BlueKantoPilot.t("Cancel","Cancelar")
    choice = pbMessage(BlueKantoPilot.t("Which drink?","Qual bebida?"),options,-1)
    return false unless choice.is_a?(Integer) && choice.between?(0,DRINKS.size-1)
    item,price = DRINKS.to_a.fetch(choice)
    if $player.money < price
      say("You don't have enough money.","Você não tem dinheiro suficiente.")
      return false
    end
    unless $bag.add(item,1)
      say("There is no room in your Bag.","Não há espaço na Bolsa.")
      return false
    end
    $player.money -= price
    say("You bought {1}.","Você comprou {1}.",item_name(item))
    true
  end

  def self.exchange
    return false unless at?(122) && $bag
    pair = EXCHANGES.find { |_drink,tm| !gift_ledger["roof_#{tm}"] }
    return false unless pair
    drink,tm = pair
    return false unless $bag.has?(drink)
    return false unless pbConfirmMessage(BlueKantoPilot.t("Trade one {1} for {2}?",
      "Trocar uma unidade de {1} por {2}?",item_name(drink),item_name(tm)))
    already_owned = $bag.has?(tm)
    return false unless already_owned || $bag.add(tm,1)
    unless $bag.remove(drink,1)
      $bag.remove(tm,1) unless already_owned
      return false
    end
    gift_ledger["roof_#{tm}"] = true
    say("You traded for {1}.","Você recebeu {1} na troca.",item_name(tm))
    true
  end

  def self.item_gift(source,item,key)
    return false unless at?(source) && $bag && !gift_ledger[key]
    return false unless $bag.has?(item) || $bag.add(item,1)
    gift_ledger[key] = true
    say("You received {1}.","Você recebeu {1}.",item_name(item))
    true
  end

  def self.coin_case
    item_gift(125,:COINCASE,"coin_case")
  end

  def self.tea
    # The item does not change the still-closed Saffron gates in this lot.
    item_gift(128,:TEA,"tea")
  end

  def self.eevee
    return false unless at?(128) && !gift_ledger["eevee"]
    return false unless pbConfirmMessage(BlueKantoPilot.t("Take this Eevee with you?",
      "Quer levar este Eevee com você?"))
    return false unless pbAddPokemonSilent(:EEVEE,25)
    gift_ledger["eevee"] = true
    say("Eevee joined you!","Eevee se juntou a você!")
    true
  end
end
