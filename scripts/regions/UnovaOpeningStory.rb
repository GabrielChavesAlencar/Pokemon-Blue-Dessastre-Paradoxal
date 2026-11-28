# The canal field assignment is loaded only in the isolated Unova QA game.
class PokemonGlobalMetadata
  attr_accessor :blue_unova_opening_qa
end

module BlueUnovaOpeningStory
  PARTNERS = [:SNIVY, :TEPIG, :OSHAWOTT].freeze
  BALL_REWARD = 5

  def self.progress
    $PokemonGlobal.blue_unova_opening_qa
  end

  def self.checked_in?
    !progress.nil?
  end

  def self.block_route
    pbMessage("Antes de seguir pelo canal, faça o credenciamento no laboratório de Nuvema.")
  end

  def self.check_in
    if checked_in?
      pbMessage("Credencial ativa. Leia o medidor depois da ponte e leve o registro ao centro em Accumula.")
      return
    end
    if $player.party_full?
      pbMessage("Deixe um espaço na equipe para o parceiro de campo.")
      return
    end
    names = PARTNERS.map { |species| GameData::Species.get(species).name }
    choice = pbMessage("Posto do Canal. Escolha um parceiro para inspecionar a ponte.",
                       names + ["Voltar"], 4)
    return unless choice.is_a?(Integer) && choice.between?(0, PARTNERS.length - 1)
    species = PARTNERS.fetch(choice)
    return unless pbAddPokemonSilent(species, 5)
    $PokemonGlobal.blue_unova_opening_qa = {
      "partner" => species.to_s, "reading" => false, "reported" => false
    }
    pbMessage("#{names[choice]} entrou para a equipe. Cruze a ponte e procure o medidor da Rota 1.")
  end

  def self.read_gauge
    return block_route unless checked_in?
    if progress["reading"]
      pbMessage("A leitura está registrada. Leve o relatório ao centro em Accumula.")
      return
    end
    progress["reading"] = true
    pbMessage("O medidor registrou o nível do canal. A ponte pode continuar aberta. Entregue a leitura no centro.")
  end

  def self.deliver_report
    if !checked_in? || !progress["reading"]
      pbMessage("O centro está aguardando a leitura do medidor da Rota 1.")
      return
    end
    if progress["reported"]
      pbMessage("Relatório arquivado. A ponte segue aberta.")
      return
    end
    unless $bag.can_add?(:POKEBALL, BALL_REWARD) && $bag.add(:POKEBALL, BALL_REWARD)
      pbMessage("Abra espaço na bolsa para retirar o kit do posto.")
      return
    end
    progress["reported"] = true
    pbMessage("Leitura recebida. O posto separou cinco Poké Bolas para suas próximas viagens.")
  end
end
