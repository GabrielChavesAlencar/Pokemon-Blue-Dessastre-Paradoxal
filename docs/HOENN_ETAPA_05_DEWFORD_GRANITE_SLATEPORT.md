# Hoenn — Etapa 05: Dewford, Granite Cave e Slateport

**Data:** 14/11/2026  
**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Status:** scripts para PILOTO ISOLADO; **não aprovada como jogável no Game.exe ou Android**. Não foi alterada a instalação principal do Blue/Decades.

Referências: [Etapa 04](HOENN_ETAPA_04_RUSTBORO_ROXANNE_RUSTURF.md) · [Detonado Emerald](HOENN_DETONADO_EMERALD_REFERENCIA_ORGANIZADA.md).

## 1. Inventário e geometria

Foram acrescentados **20 MapIDs da fonte** (total acumulado: **48**) conferidos na revisão fixa do projeto doador: c59233bdbaac4fbfeca6aa01c7f05be628da2a92. Esses números são remapeados para MapIDs livres em uma cópia privada isolada.

| MapID original | Local |
|---:|---|
| 28, 29, 30, 31 | Dewford Town, Centro, casas e Ginásio |
| 32, 33, 34, 35, 36 | Slateport City, Porto, Centro, Mart e casas |
| 37, 38, 39, 40 | Pokémon Fan Club, estaleiro Stern, Museu Oceânico, Battle Tent |
| 108, 111, 112 | Rota 106, Rota 109 e Casa da Praia |
| 159, 160, 161, 162 | Granite Cave 1F, B1F, B2F e sala de Steven |

**Portas e escadas:** 27 pares auditados, incluindo as duas portas distintas do Museu Oceânico.  
**Bordas naturais:** Rota 106 ↔ Dewford e Rota 109 ↔ Slateport, preservando os offsets reais do PBS do doador.  
**Inspeção geométrica do ZIP privado:** 56 células de chegada foram verificadas como passáveis; as duas bordas apresentaram 8 e 28 pares passáveis, respectivamente. Não houve teste de movimento no Game.exe.

**Barco de Mr. Briney:** viagem por evento e transferência da engine entre casa da Rota 104, Dewford e praia de Slateport, vinculada às flags de história. Não é implementação de Surf nem das rotas oceânicas 105/107/108 ou ilhas.

## 2. Brawly e a segunda insígnia de Hoenn

Seis treinadores do ginásio foram incluídos como dados-base: Laura, Takao, Brenden, Lilith, Cristian e Jocelyn. Equipe inicial de Brawly em Emerald:

- Machop (base 16): Karate Chop, Low Kick, Seismic Toss, Bulk Up
- Meditite (base 16): Focus Punch, Light Screen, Reflect, Bulk Up
- Makuhita (base 19): Arm Thrust, Vital Throw, Reversal, Bulk Up e Sitrus Berry

**Os níveis da fonte não substituem o escalonamento dinâmico de Blue/Decades.** Somente vitória concede o marco regional HOENN:KNUCKLE via BlueRegions.award; derrota não concede. Insígnias nativas de Decades/Kanto/Johto não são alteradas. A TM Bulk Up fica pendente se a Bolsa estiver cheia ou o item não ensinar realmente o movimento.

## 3. Granite Cave, Flash e Steven

- Encounter Cave por andar: 1F Makuhita/Zubat/Abra/Geodude; B1F Aron/Zubat/Abra/Makuhita/Mawile/Sableye; B2F Aron/Zubat/Abra/Mawile/Sableye; sala de Steven Makuhita/Zubat/Abra/Aron. Cada tabela soma 100%.
- Montanhista entrega HM Flash uma vez. A permissão de campo pertence à Knuckle Badge LOCAL, conforme registro das regiões; o uso real dentro da caverna requer teste do motor.
- Steven recebe a Letter de Mr. Stone, com proteção de item ausente/entrega única. TM Steel Wing só é concedida se a TM realmente corresponder ao movimento; caso contrário fica pendente.
- Pisos rachados, escuridão da caverna, Rock Smash e cutscenes especiais **ainda não estão implementados integralmente**.

## 4. Slateport, Museu e Equipe Aqua

1. Depois de entregar a carta a Steven e conquistar Knuckle, Mr. Briney transporta o jogador para a praia da Rota 109. O retorno também usa pontos de chegada auditados.
2. No estaleiro, um funcionário orienta o jogador a procurar Capitão Stern no museu. A recuperação prévia dos produtos Devon é verificada por flag regional, evitando recriação indevida dos itens devolvidos em Rustboro.
3. A primeira entrada do Museu Oceânico custa ₽50. Não há cobrança se faltam fundos ou a entrada foi recusada, nem cobrança repetida depois do pagamento.
4. Dois recrutas Aqua, com versões PBS diferentes, usam respectivamente Carvanha 15 e Zubat 14 + Carvanha 14. Vitória e derrota são registradas separadamente; Stern só aceita a encomenda depois de ambos derrotados.
5. Itens Soothe Bell e Soft Sand, mais pickups de Protein e Escape Rope, são únicos e persistem após carregar o save.
6. **Rota 110 ao norte de Slateport não foi instalada** e permanece bloqueada até a Etapa 06.

## 5. Arquivos publicados no GitHub

- [Dados da Etapa 5](../scripts/regions/hoenn_stage5.py)
- [Montador isolado do piloto](../scripts/regions/pilot_hoenn.py)
- [Eventos e persistência Ruby](../scripts/regions/HoennPilot.rb)
- [Auditoria do inventário](../scripts/regions/audit_hoenn_baseline.py)
- [Auditoria de contrato](../scripts/regions/audit_hoenn_pilot_contract.py)
- [Catálogo Hoenn do site](../site/public/data/hoenn-pilot.json) — 48 locais, 41 treinadores-base, sem aprovação nativa
- [Testes Python de mapas e eventos](../tests/test_hoenn_stage5.py)
- [Testes Ruby de história](../tests/hoenn_stage5_runtime.rb)
- [Regressão no GitHub Actions](../.github/workflows/regression.yml)

Testes reproduzíveis em um checkout de desenvolvimento, sem Game.exe:

    python -m unittest discover -s tests -p "test_hoenn_*.py" -v
    python scripts/regions/audit_hoenn_pilot_contract.py --strict
    ruby -c scripts/regions/HoennPilot.rb
    ruby tests/hoenn_stage5_runtime.rb scripts/regions/HoennPilot.rb

## 6. Aceite pendente do Game.exe

- [ ] Montar a cópia com os RXDATA do ZIP privado e recursos Blue originais e compilar os 48 mapas.
- [ ] Confirmar embarque, desembarque e retornos entre Rota 104, Dewford e Slateport sem travamento.
- [ ] Confirmar todos os pares de escadas, duas portas do Museu, entradas de Granite Cave e interiores.
- [ ] Batalhar contra Brawly e os dois recrutas Aqua, conferindo resultados, sprites e balanceamento nativo.
- [ ] Conferir segunda insígnia, autorização de Flash, TM Bulk Up, Steel Wing, Letter e save/reload.
- [ ] Validar cobrança do museu, procura de Stern, pacote Devon, produtos e presentes sem duplicação.
- [ ] Conferir música, gráficos finais, pisos rachados, NPCs secundários e obstáculos.
- [ ] Repetir regressão Decades, Kanto, Johto, Sinnoh e Android/JoiPlay.

**Uma CI aprovada comprova contratos testados, não que o piloto tenha sido executado no Game.exe.**

## 7. Próxima etapa

**Etapa 06 — Rota 110, Mauville, Wattson, bicicletas e rival.** Não desbloquear a próxima saída até o pacote de Stern e a construção segura dos mapas correspondentes.
