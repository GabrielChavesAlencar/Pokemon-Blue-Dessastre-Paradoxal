# Roadmap de eventos FireRed para o Pokémon Blue: Dessastre Paradoxal

**Base consultada em:** 12/11/2026. **Status:** análise consolidada, implementação e testes dos novos eventos **pendentes**. **Escopo:** Kanto, com trilha opcional separada para Ilhas Sevii e pós-jogo.
**Estado atual (12/11/2026):** [9º núcleo funcional](KANTO_AVANCO_FUNCIONAL_09.md) aprovado: **Koga/Soul**, seis treinadores, quatro portas e portão Safari informativo implementados no piloto isolado. **Capturas Safari, Safari Balls, limite de passos, Warden/Strength, Secret House/Surf e demais eventos continuam pendentes**. [CI 43231117254](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43231117254), [regressão 43232052342](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43232052342).

## 0. Fontes, limites e precedência

1. [Estudo técnico de eventos de FireRed](ESTUDO_EVENTOS_MAPA_POKEMON_FIRERED_RPG_MAKER_XP.md): taxonomia EVT-01 a EVT-50, mapas, HMs, progressão, 12 etapas de auditoria e matriz de testes.
2. [Guia para aplicar eventos no Blue](FIRERED_EVENTOS_COMO_APLICAR_NO_BLUE.md): conversão para Essentials v21.1 e lotes A–I, sem instalação automática.
3. [Extrator somente leitura](../scripts/regions/extrair_eventos_firered.py): enumera registros `object_events`, `warp_events`, `coord_events`, `bg_events` e `connections`, além de referências a scripts/flags.
4. [Plano de regiões v2](PLANO_REGIOES_DESSASTRE_V2.md): **prevalece** para as regras do Blue (balanceamento, circuito, HMs por região, bloqueio de especiais, pós-jogo, save único).
5. [Feedback dos testes manuais](KANTO_FEEDBACK_TESTES_MANUAIS_2026-11-12.md): MAN-01, MAN-02 e MAN-03, todos ainda pendentes.

**Não misturar três contagens:** o estudo GBA refere 425 mapas em 43 grupos; o piloto atual contém **109 mapas** da fonte Essentials FRLG (48 mapas antes de Celadon, **3 Celadon funcionais** e **58 em `preview_only`**); o roadmap de Kanto possui **16 etapas**. **Os 425 mapas não foram todos auditados semanticamente**, convertidos ou instalados.

**Fonte de comportamento:** `pret/pokefirered` (map.json, scripts.inc, text.inc, scripts globais); é preciso fixar SHA antes de nova auditoria. **Fonte de geometria e IDs RMXP:** Essentials FRLG 21.1/1.1, hash já fixado em [kanto-source.json](../data/regions/kanto-source.json). Flags KANTO_* da análise são **propostas**, não switches já implementados. Não presumir que `dest_warp_id` da origem GBA seja MapID no RPG Maker; resolver o warp e as coordenadas no destino.

## 1. Duas barras gerais e uma trilha de auditoria independente

- **Barra 1 — Desenvolvimento funcional atual:** **9/16 = 56,25%, faltam 7 etapas**. Núcleos: 01/03/04/05/06/07/08/09/**10**. A [CI Koga/Soul](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43231117254) e [regressão](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43232052342) aprovam apenas o **núcleo parcial** de Fuchsia, não toda a Safari.
- **Barra de aceitação integral:** **1/16 = 6,25%; faltam 15 etapas**. Só 01 está aceita (escopo estrutural); CI simulada não substitui caminhada, colisões e batalhas reais no Windows.
- **Trilha de eventos FireRed:** **12 marcos de auditoria e adaptação**, definidos no estudo e listados abaixo; **progresso numérico ainda não aferido**. O total de eventos em escopo precisa vir da execução real do extrator e da triagem das salas opcionais, não de um percentual estimado.

**Proteção vigente:** permanecem `preview_only` **8 mapas de Celadon** (111,117–123), **15 de Fuchsia/Safari** (incluindo Safari South/East/North/West, Warden e Secret House) e **30 de Saffron/Silph**, totalizando **53 mapas sem eventos**. Cinco mapas de Fuchsia (144/145/146/147/153) possuem whitelist auditada; o Safari Gate não leva à área de captura.

## 2. Preparação / auditoria sem alterar gameplay

- [ ] **AUD-01 — Versão congelada:** guardar commit exato de `pret/pokefirered`, hash do pacote FRLG, revisão do Blue, versão Essentials e dependências; backup dos saves e da cópia instalada.
- [ ] **AUD-02 — Inventário literal:** executar o extrator na referência fixada, registrar quantos mapas e eventos foram efetivamente lidos e exportar `eventos_detalhados.csv`, `eventos_detalhados.json`, `mapas_resumo.json` e `INVENTARIO_COMPLETO_FIRERED.md`. Marcar registros ausentes, protótipos e especiais, sem considerar o script uma análise semântica.
- [ ] **AUD-03 — Matriz de correspondências:** GBA `MAP_*`/`scripts.inc`/warp de origem → ID da fonte Essentials FRLG → ID real da cópia Blue → EventID e coordenada (com direção, tileset, colisão, prioridade, trigger). Distinguir porta, conexão contínua, escada, autorun e treinador. Marcar `RESOLVER` onde a referência ainda não foi comprovada.
- [ ] **AUD-04 — Dependências e flags:** ler branches e scripts globais citados; documentar pré-condições, efeitos, pós-condições, alternativas, permissões de HM, vitória/derrota/fuga, inventário/PC cheios, recarga, switches de história e estados locais. Não copiar ``FLAG_*` diretamente para números de switches do Decades.
- [ ] **AUD-05 — Congelar o escopo de implementação:** separar obrigatório, secundário, pós-Liga, Sevii e eventos distribuídos/protótipos. Excluir salas especiais inacessíveis quando justificado; registrar a exclusão.

**Contrato mínimo de uma linha da futura matriz:**
`gba_map,source_script,event_kind,gba_warp_id,frlg_source_id,blue_map_id,blue_event_id,trigger,priority,sight,source_flag,kanto_state,precondition,success,defeat_or_escape,repeat,save_reload,source_commit,status,evidence`

O extrator não gera RXDATA, não interpreta todo script global, não define equipes e não importa encontros selvagens em PBS. Seu êxito **não** libera eventos automaticamente.

## Estado de implementação de eventos no trecho inicial — MAN-01 e MAN-02

A [correção funcional de Pallet a Pewter](KANTO_CORRECOES_FUNCIONAIS_MAN01_MAN02.md) está implementada em código e aprovada na [CI nativa 43218959042](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43218959042): **8 interiores com ida/volta**, **50 treinadores com `Sight(n)`/Event Touch** e página 2 persistente pós-vitória; os outros 6 treinadores mantêm interação manual conforme a fonte. A **regressão de projeto** também foi aprovada. O mapa fonte 13 (Ginásio Viridian) e o 23 (Diglett's Cave) continuam fora do lote de portas por dependerem de progressão e de outros mapas.

**Estado:** MAN-01 e MAN-02 estão **parcialmente implementados**, **não concluídos**. Os interiores de outros trechos, guardas/quest, bloqueios obrigatórios, diálogos finais, validação manual e MAN-03 ainda faltam. Este lote MAN-01/02 não alterou, na época, os 61 mapas de prévia; o avanço posterior de Erika reduziu esse total para 58, não contou como conclusão de uma nova etapa; barras reavaliadas em [6/16 e 1/16](KANTO_REAVALIACAO_BARRAS_2026-11-12.md) e não distribuiu textos originais de FireRed.

**Atualização após estudo (12/11/2026):** o [sétimo núcleo de desenvolvimento](KANTO_AVANCO_FUNCIONAL_07.md) entrega o pacote regional de Oak no Mart de Viridian, valida 11 pares de portas e mantém 50 eventos `Sight(n)`. **MAN-01 e MAN-02 ainda não têm aceite integral**: interiores secundários, barreiras de história, textos e gameplay manual permanecem pendentes.

**Novidade após o roteiro (12/11/2026):** [8º núcleo de Kanto](KANTO_AVANCO_FUNCIONAL_08.md) ativa apenas City/Center/Gym Celadon com Erika/Rainbow e sete treinadoras, sob whitelist; CI 43227499299 e regressão 43227499314 aprovadas. **Manter pendentes** Rocket/Game Corner, Silph Scope, Cut trees, loja, portas restantes, falas EN/PT-BR, QA de movimento e os eventos de Lavender/Saffron.

## 3. Sequência prioritária de correções — conforme teste do jogador

| ID | Ação, na ordem | Famílias do estudo | Critério de aceite | Dependência |
| --- | --- | --- | --- | --- |
| **MAN-01** | Portas de casas, laboratório, Center, Mart, portarias, ginásios, escadas e retorno | EVT-22/23/24, EVT-44 | Todas as entradas catalogadas e coordenadas de destino válidas; ida/volta real; salvar dentro e reabrir; não saltar para Decades | AUD-03 e mapas internos realmente instalados |
| **MAN-02** | Treinadores por visão/contato, aproximação e bloqueio apenas quando canônico | EVT-11/12/13/14/18/19 | Visão não atravessa parede, derrota não vira vitória, NPC derrotado não reinicia batalha, save preservado; treinador opcional não vira barreira artificial | AUD-04 e contrato estável de TrainerID/EventID |
| **MAN-03** | Painel das oito insígnias de Kanto e painel geral de conquistas regionais | EVT-47 + UI Blue | Ler conquistas existentes, sem conceder flags pelo painel; Alola/Hisui/Decades com marcos próprios; progressão e HMs corretas após reload | BlueRegions/RegionalPolicy já existentes |
| **SAVE-01** | Estado persistente e migração das flags e dos mapas | EVT-02/05/07/17/40/41/42 | Repetição/respawn sem duplicar prêmios, saves antigos/Decades intactos, isolamento entre regiões e recuperação após falha | AUD-03/04; esquema versionado |
| **QA-01** | Caminhada humana com checklist por evento | Todas no escopo | Windows: primeiro uso, repetição, colisão, ida/volta, vitória, derrota/fuga, bag/PC cheios, save/reload; depois JoiPlay, rollback | Cada lote funcional |

**Regra do projeto:** antes de adaptar grandes arcos de história, tratar MAN-01 e MAN-02 nos mapas que o usuário já visitou (Pallet, Rotas 1/2, Viridian, floresta, Pewter, lado esquerdo da Rota 4 e Mt. Moon); o relato de visita **não equivale a aceite**.

## 4. Lotes da história e encaixe nas 16 etapas

| Lote | Áreas e eventos previstos na análise | Etapas Kanto relacionadas | Estado |
| --- | --- | --- | --- |
| **A** | Pallet/Oak/Rota 1: dois triggers de Oak, três iniciais, rival, laboratório, casas, item único da Rota 1 | 02, 03, 04, 16 | Revisão dos eventos pendente |
| **B** | Viridian/Rotas 2/3/Forest/Pewter/Mt. Moon: Parcel, Mart/Center, treinadores por visão, Brock/Boulder, escadas, Rockets, escolha Helix/Dome | 03, 06, 07, 15 | Revisão pendente; parte da geometria e batalha simulada existe |
| **C** | Cerulean/Rotas 24/25/Bill: rival, Nugget Bridge, Rocket, Misty, Bill, S.S. Ticket e guarda da Cave | 07, 08, 15 | Não substituir a quest de Bill por concessão automática baseada apenas na Cascade |
| **D** | Rotas 5/6/11/Vermilion/S.S. Anne: guardas, ticket, embarque, rival, capitão/Cut, lata dupla, Surge/Thunder | 06, 08, 15 | Implementação experimental parcial; falta sequência canônica e testes reais |
| **E** | Celadon/Lavender/Saffron: Rocket/Game Corner, Lift Key/Silph Scope, Pokémon Tower/Marowak/Mr. Fuji/Poké Flute, chá/guardas, Silph Co./Card Key/portais, Erika e Sabrina | 09, 11, 15 | **Celadon parcialmente funcional (Erika/Rainbow); Rocket/Game Corner e Saffron seguem pendentes de gameplay/QA** |
| **F** | Fuchsia/Snorlax/Rotas 12–18/Safari: Poké Flute, dois Snorlax independentes, Cycling Road, Gold Teeth, Surf/Strength, Koga | 06, 10, 15 | **5 mapas Fuchsia com núcleo Koga/Soul e portão seguro; 15 mapas Safari/rotas ainda sem eventos, gameplay completo pendente** |
| **G** | Seafoam/Cinnabar/Viridian final: pedras e correnteza, Mansion/Secret Key, Blaine/Volcano, Giovanni/Earth, arcos Sevii 1–3 quando aprovados | 12, 13, 15 | Pendente |
| **H** | Rotas 22/23, oito portões, Victory Road, Elite Four, campeão, Hall of Fame e liberação Decades/Johto somente após Liga | 14, 15, 16 | Pendente |
| **I** | Pós-jogo/Sevii 4–7: National Dex, Ruby/Sapphire, Celio, Icefall, Warehouse, Network Machine, Cerulean Cave, lendários e eventos especiais | Escopo opcional separado / 15, 16 se incluído | Pendente de decisão de escopo |

O roteiro técnico estende-se além da jornada até a Liga. **Sevii não altera automaticamente o denominador 16**; definir seu escopo separado antes de implementar.

**Flexibilidade preservada:** não impor Misty antes de Bill quando o original permitir; não impor sequência fictícia Erika → Koga → Sabrina; não transformar treinadores comuns em bloqueios; Mewtwo/Deoxys/Lugia/Ho-Oh não são exigências para concluir a Liga.

## 5. HMs, puzzles e relações que exigem testes de integração

Conforme o estudo de FireRed, **posse do HM** e **permissão local de uso** são verificações distintas no sistema Blue:

| HM | Origem em FireRed | Insígnia de Kanto para usar |
| --- | --- | --- |
| Cut | Capitão no S.S. Anne | Cascade |
| Fly | Rota 16 | Thunder |
| Surf | Secret House da Safari Zone | Soul |
| Strength | Warden após Gold Teeth | Rainbow |
| Flash | Oak's Aide na Rota 2 (10 espécies capturadas) | Boulder |
| Rock Smash | Ember Spa, One Island | Marsh |
| Waterfall | Icefall Cave, Four Island | Volcano |

- [ ] Comparar a tabela do estudo às regras reais do `RegionalPolicy.rb` e à equivalência de montarias, sem alterar a autorização global do Decades.
- [ ] Quebra-cabeças: duas lixeiras de Surge; tiles de seta Rocket; Silph teletransportes; Safari temporizado; Seafoam com pedras e correnteza; Mansion com estátuas; Victory Road com botões; Dotted Hole. Validar controle, colisão, persistência e saída para evitar softlock.
- [ ] Estados de encontros únicos: Snorlax R12/R16 independentes; Marowak 6F; Electrode e Zapdos; Articuno; Pokémon de evento e Sevii — capturar, derrotar, fugir e reentrar conforme cada script original. Nunca remover NPC só por tentar a batalha.
- [ ] Após oito insígnias locais, checar travas de party/Box de lendários, míticos, Ultra Beasts e Paradoxos conforme o Plano v2. Não usar insígnias de Decades/Johto em Kanto.

## 6. Doze marcos da trilha de eventos (não confundir com 16 etapas Kanto)

| Marco | Entrega mensurável | Estado |
| --- | --- | --- |
| 01/12 | Exportar inventário completo e registrar SHA pret | Pendente de execução documentada |
| 02/12 | Resolver correspondências de mapas e warps GBA/FRLG/Blue | Pendente |
| 03/12 | Testar bidirecionalmente portas, conexões e escadas do piloto | Pendente |
| 04/12 | Conferir eventos de treinadores, diálogos, itens, flags | Pendente |
| 05/12 | Namespace Kanto, salvamento versionado e migração de saves | Pendente |
| 06/12 | Marcos/cutscenes Pallet–Vermilion por lotes A–D | Pendente |
| 07/12 | Celadon/Lavender/Saffron por lote E | **Aguardar autorização** |
| 08/12 | Fuchsia/Surf/Rotas 12–18 por lote F | Pendente |
| 09/12 | Cinnabar/Viridian/Liga por lotes G–H | Pendente |
| 10/12 | Sevii e pós-jogo por lote I, se incluído | Escopo opcional |
| 11/12 | Integração BlueRegions, RegionalPolicy, portal e Blue Studio | Pendente |
| 12/12 | Teste humano Windows → Android + rollback + evidências por evento | Pendente |

**Sem numerador inventado:** contar eventos *implementados* e *validados* por registro após AUD-02/AUD-05 e manter duas barras próprias. A existência de um MD, do extrator, de um MapID ou de uma CI verde não aprova um evento.

## 7. Portões de qualidade / checklist por lote

- [ ] Matriz de mapeamento com MapID, EventID, referência do script, status e origem verificáveis.
- [ ] Tradução explícita de `object`/`warp`/`coord`/`bg`/`connection`, prioridade das páginas, trigger e condições; sem scripts de terceiros executados em bloco.
- [ ] Máquina de estados antes/durante/depois; vitória vs. derrota/fuga; repetição; inventário/party/PC cheios.
- [ ] Warps de ida/volta, direção e coordenadas, colisões, visão de treinadores e limites do mapa.
- [ ] Flag de vitória somente após resultado positivo; itens, badges e prêmios não duplicáveis.
- [ ] Compilação de PBS e teste nativo na cópia isolada, sem sobrescrever saves/MapIDs do Decades.
- [ ] Testes manuais em Game.exe para caminhada/combate, save/reload, retorno e modos de dificuldade; depois JoiPlay.
- [ ] Política regional de HMs, insignias e especiais verificada; rollback funcional registrado.
- [ ] Registros públicos (guia, treinadores, locais) atualizados somente com dados efetivamente implementados.
- [ ] **Demais mapas da fase 09 e fases 10/11:** remover `preview_only` somente ao implementar o evento específico e sua validação e testes; até lá exigir zero eventos.

## 8. Próxima ação permitida

**Agora:** somente consolidar especificação, crosswalk, fonte SHA, checklist e tarefas MAN-01/02/03. **Depois da autorização do usuário:** implementar MAN-01 primeiro, MAN-02 em seguida, salvar/flags e UI; avançar os lotes de história em cópia isolada. Nenhuma dessas pendências está declarada concluída neste roadmap.

## Referência complementar — diálogos e tradução EN/PT-BR

**Rastreamento operacional:** [KANTO_ROADMAP_DIALOGOS_EN_PT.md](KANTO_ROADMAP_DIALOGOS_EN_PT.md) (DIA-01–DIA-10, correspondência por fala, lotes KAN/SEV, validação bilíngue). Fontes: [guia EN/PT-BR](Guia_Dialogos_Pokemon_FireRed_EN_PT.md), [passo a passo do Blue](FIRERED_DIALOGOS_PASSO_A_PASSO.md), [extrator local](../scripts/localization/extrair_traduzir_dialogos_firered.py).

- **67 cenas KAN-001–KAN-067** e **14 referências SEV-001–SEV-014** são **resumos temáticos**, não falas EN/PT já extraídas, traduzidas ou instaladas. O corpus integral e o total real de falas ainda não foram comprovados por relatório de extração.
- Auditar referência `text.inc` → `scripts.inc`/flag → MapID/EventID **por uso**, incluindo diálogos pré/pós-batalha, escolha, repetição, itens e save/reload. Não confundir rótulos GBA com chaves de mensagens inglesas compiladas da engine.
- Integrar pt-BR com `scripts/localization/catalog.py`, `scripts/localization/review.py`, `data/pt-br.json`, preservando `{PLAYER}`, `{RIVAL}`, outros controles e a opção English.
- **Portões de aceite por evento:** fala EN e PT-BR revisada, renderização sem corte, branches e escolhas corretos, tokens intactos, nenhuma recompensa duplicada, teste Windows e depois JoiPlay.
- **Mapas ainda pendentes em 09–11:** manter os 53 `preview_only` sem eventos/diálogos até implementação autorizada, com fontes originais restritas a pasta local e direitos respeitados.

As **10 tarefas DIA** são uma trilha documental adicional às **12 de eventos** e **16 de Kanto**. Nenhuma nova fala foi instalada com esta atualização; não alterar os contadores atuais 9/16 ou 1/16.
