# Johto — Etapa 13/16: Tohjo Falls, Victory Road, Elite Four, Lance e Hall of Fame

**Estado: PARCIAL — núcleo Ruby, contrato simbólico de mapas e testes isolados no GitHub.**  
Os arquivos **não foram instalados no Game.exe**, e nenhuma Liga de Johto pode ser jogada sem maps/RXDATA, PBS, mapas de saída e callbacks nativos do Hall of Fame auditados.  
**Dependência:** [Etapa 12 — Ice Path, Clair e RISING](JOHTO_FASE_12_ICE_PATH_BLACKTHORN_CLAIR.md) · [Acompanhamento](JOHTO_ETAPAS.md) · [Plano mestre](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md).

## Arquivos entregues

| Arquivo | O que implementa |
|---|---|
| [scripts/regions/JohtoLeague.rb](../scripts/regions/JohtoLeague.rb) | Módulo regional isolado: New Bark, Route 27/26, Tohjo Falls, Victory Road e rival, Indigo Plateau de Johto, Elite Four Will/Koga/Bruno/Karen, Lance, confirmação do Hall of Fame, registro de conclusão e NPC introdutório de viagem |
| [tests/johto_league_runtime.rb](../tests/johto_league_runtime.rb) | Teste Ruby com saves e batalhas simulados, vitórias/derrotas, perda de progresso da Elite, Hall of Fame falho, desbloqueio de Kanto/Hoenn no estado e isolamento de Kanto/Decades |
| [tests/test_johto_league_runtime.py](../tests/test_johto_league_runtime.py) | Encaminha a suíte Ruby para a CI do Blue Studio |
| [data/regions/johto-phase13.json](../data/regions/johto-phase13.json) | Grafo simbólico New Bark → Tohjo → Victory Road → Indigo Plateau e salas da Liga, sem MapIDs reais, coordenadas ou warps inventados |
| [tests/test_johto_phase13_contract.py](../tests/test_johto_phase13_contract.py) | Valida oito insígnias locais, ordem da Elite, registro regional, limitação do adaptador de viagem e não instalação do mapa |

## Caminho para a Liga

1. O jogador **vence Clair**, conclui a prova do Dragon Master, recebe a **RISING** (oitava insígnia) e aciona o handoff da Etapa 12, \`johto_league_approach_ready\`.
2. \`new_bark_return\` registra a volta narrativa para a **cidade inicial de Johto**, New Bark. **Não teleporta** o jogador nem altera um mapa.
3. \`route27(tool_ready)\` exige oito insígnias da própria Johto, handoff pronto, Surf permitido por **FOG + ferramenta** e mapa validado.
4. \`tohjo_falls_enter\` exige Route 27. \`tohjo_waterfall(tool_ready)\` exige **RISING + ferramenta Waterfall + HM realmente obtido** na Ice Path. Não coloca o jogador no alto da cachoeira sem warp físico verificado.
5. \`route26\` e \`victory_road\` exigem conclusão da travessia e marcadores de mapas reais.
6. \`victory_road_rival\` usa \`BLUE_JOHTO_VICTORY_ROAD_RIVAL\` com versão 0, 1 ou 2 em função do inicial escolhido em Elm. Perda não completa esse combate.
7. \`indigo_plateau_arrive\` registra que a **campanha selecionada é Johto**, após a vitória contra o rival.

**Indigo Plateau é geograficamente compartilhado com Kanto**, mas os eventos, trainers, switches, batalhas e conclusão de Hall of Fame **não podem compartilhar os mesmos estados da Liga de Kanto**. Antes de instalar a fase, auditar a implementação real e atribuir eventos exclusivos de Johto, sem sobrescrever a região já funcional.

## Elite Four e campeão Lance

A ordem do desafio é fixa:

| Ordem | Treinador | PBS previsto |
|---|---|---|
| 1 | Will | \`BLUE_JOHTO_ELITE_WILL\` v0 |
| 2 | Koga | \`BLUE_JOHTO_ELITE_KOGA\` v0 |
| 3 | Bruno | \`BLUE_JOHTO_ELITE_BRUNO\` v0 |
| 4 | Karen | \`BLUE_JOHTO_ELITE_KAREN\` v0 |
| 5 | Campeão Lance | \`BLUE_JOHTO_CHAMPION_LANCE\` v0 |

\`begin_challenge\` exige oito insígnias, chegada a Indigo Plateau, PBS realmente compilado e marcador de prontidão do piloto.

\`elite_four(0..3)\` aumenta \`johto_league_step\` **somente quando a batalha correspondente foi vencida**. Pular membros ou repetir a mesma batalha no mesmo desafio é recusado. **Perder** qualquer uma das quatro lutas ou contra Lance chama \`reset_challenge\`: o próximo desafio precisa recomeçar por Will. O script não executa automaticamente blackout, cura, movimentação ou persistência do motor; isso deve ser implementado por eventos oficiais seguros.

\`champion_lance\` só pode ser iniciado depois das quatro vitórias. Vencê-lo marca \`johto_league_lance_won\`, mas **não conclui Johto e não libera Kanto/Hoenn antes do Hall of Fame real**.

Os cinco times, moves, itens, níveis e variações normal/Master Mode **ainda não estão em PBS**. Não inventar dados: compilar a fonte correta e manter os hooks de balanceamento do Decades, incluindo as regras Master Mode e o balanceamento por total de insígnias/esmeraldas já previsto.

## Hall of Fame — condição real de conclusão

O Hall of Fame tem **duas etapas**:

1. \`hall_of_fame_begin\` exige quatro vitórias, Lance vencido e um marcador de evento de Hall of Fame **verificado no piloto**; registra apenas uma pendência.
2. \`hall_of_fame_result(:recorded)\` exige a confirmação de que o **motor real gravou com sucesso o Hall of Fame e a persistência pertinente**. Somente nesse caso chama \`BlueRegions.complete_league(state, "JOHTO")\`.

Se o Hall of Fame falhar ou for cancelado, não altera \`state["leagues"]\`; a tentativa de gravação pode ser repetida. A conclusão confirmada ocorre **uma única vez** e define a flag local \`johto_league_cleared\`. Não há insígnia de número 9 nem incremento manual de esmeraldas.

**Implementação nativa ainda pendente:** identificar a API e os callbacks exatos de Essentials/Decades e comprovar que a cena, o save e a atribuição de evento de Johto acontecem na ordem correta. Um símbolo \`:recorded\` em teste com mock **não é** evidência de gravação no Game.exe. O instalador só poderá criar o marcador \`Data/blue-johto-hall-of-fame-ready.txt\` depois dessa validação. Jamais chamar \`hall_of_fame_result(:recorded)\` somente porque Lance foi derrotado.

## Desbloqueio regional após a primeira Liga

O circuito de regiões existente possui a ordem:

\`Decades → Kanto → Johto → Hoenn → Sinnoh → Unova → Kalos → Alola → Galar → Paldea\`.

Após \`BlueRegions.complete_league(state, "JOHTO")\`, \`BlueRegions.unlocked\` libera os vizinhos **Kanto e Hoenn** no **estado do save** da campanha de Johto. Isso é independente da geografia e não conclui a Liga de Kanto nem altera suas insígnias. \`region_unlock_preview\` apenas exibe o resultado lógico.

**Viagem física ainda indisponível:** no código atual, \`BlueRegionTravel\` só aceita \`DECADES\` e \`KANTO\` como origem, e Hoenn não tem mapas instalados. Logo, mesmo depois da conclusão de Johto, nenhum teleporte para Hoenn ou spawn não auditado é criado. \`travel_agent_intro\` somente prepara a conversa do futuro NPC na **cidade inicial New Bark Town**. A Etapa 16 deverá instalar o NPC, validar destino/Box/party e habilitar o serviço depois de garantir passagens seguras.

A autorização para usar lendários/míticos/Ultra Beasts/paradoxos vem das oito insígnias locais (Etapa 12). Concluir a Liga **não deve modificar a regra de bloqueio** em regiões com menos de oito insígnias. Ao viajar, a seleção da party e o depósito no Box serão responsabilidade do adaptador regional existente, depois de teste com inventário e slots livres.

## PBS e marcadores não instalados

| Recurso | Marcador esperado |
|---|---|
| Route 27/26, Tohjo Falls, Victory Road e Indigo | \`Data/blue-johto-league-route-ready.txt\` → \`BLUE_JOHTO_LEAGUE_ROUTE_V1_READY\` |
| Rival de Victory Road | \`Data/blue-johto-victory-rival-ready.txt\` → \`BLUE_JOHTO_VICTORY_RIVAL_V1_READY\` |
| Elite Four e Lance, versões e equipes PBS | \`Data/blue-johto-league-trainers-ready.txt\` → \`BLUE_JOHTO_LEAGUE_TRAINERS_V1_READY\` |
| Hall of Fame gravado com sucesso e adapter verificado | \`Data/blue-johto-hall-of-fame-ready.txt\` → \`BLUE_JOHTO_HALL_OF_FAME_V1_READY\` |

Todos **ainda inexistentes**; nenhum marcador será criado para fingir que os dados estão instalados.

## Testes

\`\`\`powershell
python -m unittest discover -s tests -p "test_johto_league_runtime.py" -v
python -m unittest discover -s tests -p "test_johto_phase13_contract.py" -v
python -m unittest discover -s tests -p "test_johto*.py" -v
python -m unittest discover -s tests -p "test_regions.py" -v
\`\`\`

A suíte Ruby usa save, treinador e callbacks **simulados** para cobrir tentativa em Kanto/Decades, falta de uma insígnia, Surf/Waterfall, mapas e PBS não instalados, rival perdido, ordem Elite Four, derrota contra Will e Lance, repetição da Liga, Hall of Fame falho/cancelado, conclusão idempotente, desbloqueio de Kanto/Hoenn no circuito, persistência após Marshal reload e preservação dos badges de Kanto.

**Suíte verde prova o contrato da lógica, NÃO o registro real do Hall of Fame no Game.exe.**

## Critérios para aceitar a Etapa 13/16

- [ ] Receber e auditar o Map Pack de Johto com SHA-256, tiles, créditos/direitos e MapIDs de origem e destino não conflitantes.
- [ ] Montar New Bark → Route 27 → Tohjo Falls → Route 26 → Victory Road → Indigo com tiles, passagens ida/volta, Surf, Waterfall e encontros.
- [ ] Provar os checkpoints e o combate do rival no Victory Road, incluindo save/reload e derrota sem teleporte.
- [ ] Auditar a região compartilhada do Indigo Plateau, garantindo eventos e switches de Johto separados de Kanto.
- [ ] Compilar os cinco treinadores da Liga e o rival, incluindo variantes normal/Master Mode compatíveis com Decades.
- [ ] Rodar no Game.exe sequência inteira da Elite Four, perdas em cada etapa e retorno seguro sem avançar flags incorretas.
- [ ] Inspecionar API Hall of Fame e gravação no save real; verificar conclusão exclusiva de Johto e nenhum efeito na Liga de Kanto.
- [ ] Comprovar Kanto/Hoenn desbloqueados apenas **no circuito**, sem ativar spawn/viagem não instalada para Hoenn.
- [ ] Criar NPC de viagem na **cidade inicial de Johto**, só depois de Liga e destinations/Box verificadas.
- [ ] Validar regressão Decades/Kanto, contas de insígnias/esmeraldas, saves separados, Windows/JoiPlay e CI do commit final.

**Barras:** 0/16 etapas integralmente concluídas; 0/16 jogabilidade integralmente aprovada. Etapa 13 **PARCIAL**, sem Game.exe instalável.
