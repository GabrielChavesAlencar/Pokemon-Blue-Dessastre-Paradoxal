# Hoenn — pendências de implementação após as 12 fases técnicas

**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Região:** Hoenn (piloto isolado, fonte fixada de 199 mapas)  
**Revisão inicial:** 14/11/2026  
**Tipo de acompanhamento:** implementação de conteúdo; **não** substitui a auditoria e o aceite jogável de `HOENN_QA_PROGRESSO_12_FASES.md`.

> **Estado de referência:** as ferramentas técnicas de QA estão preparadas em **12/12**, mas isso **não significa Hoenn 100% implementada**. A aprovação nativa continua **0/12** até existir evidência de execução real. O objetivo deste documento é **desenvolver o conteúdo ainda ausente**, mesmo antes dos testes manuais.

## 1. Fontes de verdade e regras de trabalho

1. **Repositório (fonte do código):** `scripts/regions/pilot_hoenn.py`, `scripts/regions/HoennPilot.rb`, módulos `scripts/regions/hoenn_stage*.py`, `scripts/regions/hoenn_qa_phase*.py` e `data/regions/hoenn-qa-progresso.json`.
2. **Auditorias locais (fonte das pendências específicas):** `.blue-work/hoenn-qa-fase12/Hoenn pilot.json` e relatórios `.blue-work/hoenn-qa-fase12-*-report.json`. Em particular:
   - `qa3.source_events.unimplemented_source_event_candidates`: eventos originais ainda **sem equivalente autoral confirmado**. Classificar por mapa e tipo antes de implementar; não presumir que toda entrada da lista é falta real.
   - `qa4.source_obstacles_needing_review`, `qa4.source_obstacle_candidates`, `qa4.new_safe_obstacles`: obstáculos ambíguos, condicionais e efetivamente recriados.
   - `qa11`, `qa12.unresolved_backlog` e `stage10.boss_battle_art_placeholder`: localização, mídia provisória e lacunas registradas.
   - O relatório QA12 aponta **contagens**, mas a lista detalhada de candidatos vem sobretudo de QA03/QA04. Não inventar totais sem o relatório privado real.
3. **Referência de progressão:** detonados/MDs de Hoenn já existentes no projeto, Emerald/RSE e as regras regionais próprias do Blue. O detonado é referência de conteúdo, **não autorização para copiar scripts/diálogos de outro jogo**.
4. **Dados de origem:** somente o ZIP doador **original e com revisão/hash fixados**, disponível localmente. Não substituir por mapas artificiais, outro map pack, coordenadas supostas ou código doador não auditado.
5. **Escopo e preservação:** instalar mudanças apenas no **piloto isolado de Hoenn**, nunca sobrescrever `game/`, os 199 MapIDs remapeados, os perfis de save anteriores nem Decades/Kanto/Johto/Sinnoh. O sistema de batalha, scaling, esmeraldas, HMs e progressão regional continua sob as regras autorais do Blue.
6. **Distribuição:** não fazer commit de ZIP privado, ROM, RXDATA originais, gráficos/áudios protegidos do doador ou dumps de saves. Publicar código autoral, inventários de pendências e verificações; instalar recursos permitidos somente na cópia local.

**Importante:** uma frase antiga como "será integrado na próxima etapa" pode estar obsoleta se uma etapa posterior já implementou o conteúdo. Primeiro confirmar **eventos, guards e dependências atuais**. Não duplicar evento ou NPC só por existir mensagem antiga de `future_gate`.

## 2. O que já existe e deve ser preservado

- Preparador de **199 mapas remapeados**, conexões selecionadas, inventário de eventos e PBS de encontros/treinadores, em cópia privada.
- Fluxo autoral da campanha, do início até oito ginásios, Wally, Elite Four, Wallace e flag regional de Hall da Fama, **com limitações** listadas abaixo.
- Regras regionais de insígnias e HMs, dinâmicas de batalhas/level cap, Trainer Card local e integração de `BlueRegions`.
- Nome exibido de 199 mapas em PT-BR, **oito insígnias locais traduzidas**, sete OGG de referência usados também como fallback provisório e diálogos autorais específicos.
- `TESTAR_HOENN.bat` e menu **Testar Hoenn · Teleporte**: lista de 199 destinos por nome/MapID com parada em terreno validado e perfil de save isolado. **Teleporte é ferramenta de inspeção; não conclui progresso de história.**
- Auditores QA01–QA12 e regressões Ruby/Python existentes. Não recomeçar toda a implementação nem marcar mecânicas como completas apenas porque os contratos sintéticos passam.

## 3. Inventário das lacunas de implementação

| ID | Prioridade | Área | Evidência e lacuna | Critério para marcar como implementada |
|---|---|---|---|---|
| H-01 | P0 | NPCs, treinadores, placas e itens | `qa3.source_events.unimplemented_source_event_candidates`; o relatório do gerador ainda declara `all_trainers_npcs_signs_added: false`. Algumas pickups simples foram implementadas; eventos complexos foram só catalogados. | Cada candidato classificado em implementado, intencionalmente omitido (com motivo), ou bloqueado (com evidência); todos os itens de história obrigatórios têm evento autoral, gatilho e persistência corretos. |
| H-02 | P0 | Obstáculos e puzzles de campo | `qa4.source_obstacles_needing_review`; não há solução completa garantida para pedras condicionais, Surf/Dive/Waterfall, gelo e correntes. Auditoria antiga identificou 39 candidatos StrengthBoulder, 64 Ice Floor de múltiplas páginas, 3 Dive e 1 Waterfall em 32 mapas analisados; esses números **não significam itens já instalados**. | Obstáculos obrigatórios recriados de forma autoral nos mapas certos, com interação, passagem, reversibilidade/persistência e pré-requisitos corretos. |
| H-03 | P0 | Ginásios e acessos | As oito batalhas e badges têm contratos, mas puzzles de Wattson (interruptores), Flannery (vapor), Norman (salas) e Juan/Sootopolis (gelo) não têm cobertura nativa completa. | Ginásios acessíveis e concluíveis por rota legítima, sem atravessar bloqueios ou depender do teleporte QA; flags/badges/TMs sem duplicação. |
| H-04 | P0 | Seafloor, clima e Rayquaza | Implementadas flags, diálogos e gates autorais, mas animações de clima, transições de cena, Sky Pillar, puzzle e conclusão cinematográfica podem estar ausentes. | Progressão narrativa completa do submarino/Seafloor até Cave of Origin, Sootopolis, Sky Pillar e resolução do conflito; eventos visuais/sonoros implementados e consistentes. |
| H-05 | P0 | Liga, Hall da Fama e pós-jogo | `hall_of_fame_stage10` registra o campeonato/flag e mensagem; o código aponta animação nativa, tela de Hall e créditos como não completados/validados. | Encerramento completo, sem dupla recompensa/registro; apresentação final, créditos, retorno pós-jogo e consequências regionais funcionais. |
| H-06 | P1 | Falas e placas PT-BR | Os **199 nomes de mapas** e diálogos autorais específicos estão em PT-BR, mas não equivalem ao conteúdo integral dos NPCs do doador. | Todas as falas/placas efetivamente exibidas pelo piloto possuem versão PT-BR consistente, com variáveis, controles, e textos sem corte; idioma alternativo preservado onde existente. |
| H-07 | P1 | Trilha e efeitos sonoros | Os **sete OGG preparados** são usados como fallback em 199 mapas; trilha específica de cidades/rotas/ginasios/cenas/Liga/Hall, fades e loops ainda precisam de seleção e integração definitivas. | Tabela de áudio por contexto sem fallback indevido, BGM/BGS/ME coerentes, sem ausência e sem afetar áudio de outras regiões. Não inventar arquivos nem publicar ativos sem licença. |
| H-08 | P1 | Sprites, visual de chefes e batalhas especiais | O gerador registra placeholders para certos líderes/chefes (inclusive no Stage10) e `original_partner_battle_pending: true` na etapa 9. | Placeholders substituídos por recursos legais disponíveis na instalação; eventos especiais, incluindo combate em dupla quando requerido, usam corretamente o motor de batalha Blue. |
| H-09 | P1 | Viagem regional e pós-jogo | O Hall registra `complete_league` e libera Johto/Sinnoh no estado, mas a viagem física só pode ocorrer com as regiões de destino efetivamente instaladas e validadas. | Viagem real sem destinos fictícios nem bypass dos pré-requisitos; equipe/PC/progresso preservados, e acesso bloqueado com mensagem quando o destino não estiver pronto. |
| H-10 | P2 | Conteúdo opcional Emerald | Há mensagens/guards para **Safari Zone, concursos, Mirage Tower, Fossil Maniac/túnel, Scorched Slab, cinzas vulcânicas/Glass Workshop**, alguns acessos de Meteor Falls/Route 115 e áreas opcionais. Vários textos podem ser legados: conferir se etapas 9–10 já resolveram a área. | Cada área escolhida contém mecânica e recompensas reais ou fica marcada explicitamente como opcional não implementada, sem se apresentar como completa. |
| H-11 | P1 | Consistência de encontros/recompensas | Encontros importados/normalizados, variantes condicionais, TMs/HMs ausentes do catálogo Blue e recompensas reservadas aparecem no código; nem todas as chances e recompensas equivalem automaticamente às de Emerald. | Cada área tem métodos de encontro coerentes, pesos/níveis conforme regra Blue, itens/HMs compatíveis com engine, recompensas entregues uma só vez, sem concessão automática indevida. |

### 3.1. Distinção entre ausência confirmada, pendência e código legado

- **Ausência reconhecida no código:** `all_trainers_npcs_signs_added: false`, inventários `unimplemented_source_event_candidates`, `source_obstacles_needing_review`; sete faixas provisórias; `original_partner_battle_pending`; mensagens declarando Safari Zone/Concursos/Glass Workshop como futuras; encerramento do Hall via mensagem sem animação/créditos implementados pelo piloto.
- **Implementado apenas parcialmente:** puzzles e transições condicionais; catálogo de encontros/recompensas; clima e sequência de Rayquaza; pós-jogo e ligação com regiões de destino.
- **Não afirmar falta sem inspeção:** qualquer evento mencionado numa mensagem `future_gate` de etapa antiga (como esconderijos Aqua/Magma, Mt. Pyre ou ferry) pode já ter evento próprio numa etapa posterior. Auditar o mapa final **depois da composição das 10 etapas**, não um trecho isolado do Ruby.
- **Não é pendência de implementação por si só:** ausência de aprovação em `Game.exe`, ausência de CI verde, necessidade de audição manual e checklist Android. Essas são **tarefas de verificação**, acompanhadas no documento QA, e não devem ser contadas como conteúdo faltante.

## 4. Plano de execução — cinco fases de implementação

Acompanhe a barra **separada do QA 12/12**, sem converter número de arquivos ou testes em porcentagem de funcionalidade. A base contém implementações parciais; todas as fases abaixo começam em **não concluídas** até revisão e aceite de código por critérios explícitos.

| Fase | Entregáveis e ordem sugerida | Dependências | Status |
|---|---|---|---|
| **IMP-1 — Mundo e encontros** | Resolver H-01 e H-11: extrair candidatos QA03, cruzar por MapID com RXDATA final, repor NPCs/itens/placas/treinadores faltantes, encontros e recompensas, deduplicar eventos, produzir inventário por mapa. | Inventário de ZIP privado + `pilot_hoenn.py` + PBS Blue | **Parcial** |
| **IMP-2 — Obstáculos, puzzles e história** | Resolver H-02 a H-04: gelo de Sootopolis, rochas/Strength, Dive/Surf/Waterfall, correntes, ginásios, Seafloor/Sky Pillar, cenas climáticas e Rayquaza. Corrigir gates e estado sem teleporte de QA. | IMP-1 e regras de `HoennPilot.rb` | **Parcial** |
| **IMP-3 — Liga, apresentações e multimídia** | Resolver H-05, H-07 e H-08: Hall/créditos, artes definitivas disponíveis, áudio contextual, batalha em dupla e apresentação dos chefes. | Progressão IMP-2 | **Parcial** |
| **IMP-4 — Conteúdo opcional** | Resolver H-10 e conteúdo Emerald secundário por prioridade, sem interferir no percurso principal (Safari Zone, Contests, Mirage Tower, fósseis, Workshop, Scorched Slab). | IMP-1 a IMP-3 estáveis | **Parcial** |
| **IMP-5 — Tradução e integração regional** | Resolver H-06 e H-09 e fechar as pendências transversais: PT-BR integral do conteúdo **realmente instalado**, interfaces, viagem regional condicionada à instalação, estado/save/PC e revisão final do inventário. | IMP-1 a IMP-4 | **Parcial** |

**Barra de implementação (não confundir com QA):**

`IMP-1 [~]  IMP-2 [~]  IMP-3 [~]  IMP-4 [~]  IMP-5 [~]` — **0/5 encerradas**, `~` indica avanço de implementação com pendências.

**Barra de jogabilidade (QA):** **0/12 aprovada**. Verificação de hash, montagem, compilação ou simulação Ruby não aprovam uma etapa jogável.

Conclusão significa **código + dados instaláveis + cobertura específica das alterações**, não execução nativa. O aceite real do jogo continua sendo registrado apenas no documento de QA.

## 5. Método de implementação por mapa/evento

1. **Auditar antes de alterar:** identificar mapa original, ID remapeado, evento original, nome, `x/y`, páginas, condições, sprite e finalidade. Checar se já existe equivalente autoral no mapa final.
2. **Classificar:** `IMPLEMENTADO` / `FALTANDO` / `BLOQUEADO_DEPENDENCIA` / `OPCIONAL_OMITIDO` / `DUPLICADO` / `PENDENTE_FONTES`. Manter motivo e, quando possível, arquivo/ID do handler. Evitar usar `TESTADO` como sinônimo de `IMPLEMENTADO`.
3. **Adicionar de maneira autoral:** criar evento/handler no `HoennPilot.rb`, integrar no gerador `pilot_hoenn.py`, preservar coordenada e precondições coerentes com o mapa, colisão, visual, gatilho `Action/Touch`, flags regionais, recompensa e estado de save.
4. **Validar conflitos:** não sobrepor NPC, obstáculo, item, porta, passagem ou ponto de teleporte; testar idempotência de pickups/batalhas/badges; manter MapIDs e remapeamento do piloto invariantes.
5. **Regerar apenas na cópia privada:** compor os 199 mapas e os PBS. Não substituir `game/` ou saves existentes. A atualização do teleportador QA12 deve continuar refletindo a geometria final de todos os mapas.
6. **Documentar resultado:** atualizar este MD ou relatório de implementação com código, MapIDs atendidos, antes/depois, quantos candidatos foram resolvidos e quantos seguem abertos, **sem zerar backlog artificialmente**.

### Testes técnicos mínimos durante implementação

- Rodar os testes focados Python e Ruby dos módulos alterados e a CI relevante; corrigir regressões **causadas pela alteração**. Não tentar mascarar falhas alheias à Hoenn.
- Executar QA01–QA12 na cópia original local quando os insumos estiverem disponíveis; uma auditoria estática não aprova jogabilidade.
- Se `Game.exe` ou o ZIP original não estiverem acessíveis, sinalizar `SEM_EXECUCAO_NATIVA` e continuar com as tarefas implementáveis sem inventar mapas, resultados ou imagens.

## 6. Regras de preservação obrigatórias para o Codex

- **Não usar** o teleporte administrativo como substituto de evento, transição ou pré-requisito. Ele apenas permite inspeção rápida dos 199 mapas.
- **Não alterar** os saves de Decades, Kanto, Johto, Sinnoh nem o motor de batalha/scaling; não conceder HMs, badges ou recompensas fora dos critérios regionais.
- **Não fazer importação indiscriminada** de scripts e diálogos do doador. Recriar apenas comportamentos autorais sustentados por referência e implementáveis no motor Blue.
- **Não publicar** ativos privados protegidos ou substituí-los por placeholders que sejam apresentados como definitivos. Quando faltar um arquivo necessário, registrar dependência exata e o que já foi feito.
- **Não sobrescrever** perfis `Hoenn QA Fase04` até `Hoenn QA Fase12` nem a instalação original; usar fluxo de atualização seguro e perfis novos quando necessário.
- **Não declarar** `100% IMPLEMENTADO`, `JOGÁVEL`, `TESTADO NO GAME.EXE` ou `ANDROID APROVADO` sem evidência correspondente.

## 7. Critério de encerramento deste MD

A implementação pode ser marcada **100% concluída** somente quando:

- Todas as linhas H-01 a H-11 estiverem resolvidas ou explicitamente excluídas do escopo, com justificativa e aceite de produto para itens realmente opcionais.
- Nenhum evento obrigatório da campanha permanecer como placa informativa substituindo um sistema ainda ausente.
- O inventário de eventos/obstáculos tiver classificação completa, IDs e evidências, inclusive os casos condicionais/multipágina não resolvidos pela automação.
- O gerador puder montar a cópia isolada **sem perder um dos 199 mapas**, eventos autorais, times, conexões, encontros, trainer cards e ferramenta de teleporte.
- Os progressos de Kanto, Johto, Sinnoh, Decades e as regras de battle/level cap permanecerem preservados.
- A documentação `HOENN_QA_PROGRESSO_12_FASES.md` continuar registrando o **aceite nativo de forma independente**.

## 8. Implementação iniciada em 14/11/2026

Fonte de trabalho: arquivos extraídos do ZIP do upstream na revisão `c59233bdbaac4fbfeca6aa01c7f05be628da2a92`. Os hashes dos 199 mapas foram conferidos com a árvore fixada. O relatório local guarda os IDs originais, os IDs remapeados e as dependências. A montagem usa o perfil separado **Hoenn Implementacao**.

**Verificação da cópia:** 199 RXDATA remapeados presentes e perfil de save isolado. O `Game.exe` compilou PBS e plugins, saiu com código 0 e gravou o marcador da revisão fixada. Depois da compilação, os 199 pontos de inspeção foram conferidos nos RXDATA finais. O auditor agora confirma que uma entrada em cache ainda pertence ao mapa carregado, pois um endereço reutilizado pelo Python podia validar o terreno errado. A auditoria estática confirmou 241 pontos de caminhada. Outros 76 pontos e sete bordas ainda precisam de validação com as mecânicas reais de campo. O manifesto corrigiu o aninhamento dos capítulos para que QA12 encontre as evidências na raiz.

- **IMP-1:** inventário com 2.059 candidatos em 184 mapas; 7 placas e 5 itens gerados, 12 duplicatas de itens com equivalente confirmado. Restam 2.035 candidatos em revisão (1.518 sem equivalente identificado e 517 com implementação ou origem ainda ambígua). A cópia preserva 25 tabelas de encontros autorais e gera 194 tabelas padrão por método. A classe `RICHBOY` usa os dados equivalentes já presentes no Blue sem modificar o PBS original, preservando IDs e times.
- **IMP-2:** 62 dos 64 pisos de gelo auditados foram gerados no mapa original 87. Os eventos originais 19 e 20 continuam fora porque o ponto de pouso está bloqueado no RXDATA. O relatório consolidado ainda tem 26 obstáculos aguardando revisão. No mapa original 255, 246 referências a 16 IDs sem dados completos foram isoladas como bloqueadas. É preciso verificar o tileset correto antes de liberar essas casas.
- **IMP-3:** arte de batalha de Juan, Archie e Wallace instalada na cópia privada com hashes conferidos; a classe de arte compartilhada da Elite continua pendente. Não houve audição manual das faixas.
- **Testes automatizados:** 186 testes focados de Hoenn e 17 verificações Ruby. A suíte Python geral, anterior ao acréscimo da regressão do cache, executou 1.055 casos, com 46 ignorados e sem falhas. Os auditores QA03 e QA04 passaram na cópia compilada. Os verificadores QA05–QA11 exigem os próprios perfis; a composição gerou os contratos dessas fases, mas não regravou os perfis antigos. Nenhuma etapa de jogabilidade foi promovida; Windows e Android seguem sem aceite de campanha.
- **QA02 em aberto:** o auditor encontrou cinco conexões marítimas originais cujos deslocamentos excedem as dimensões de uma das bordas: 147→76, 148→144, 149→144, 150→91 e 152→147. A montagem preserva o PBS de origem relativo a essas bordas. Antes de alterá-las, é preciso conferir o comportamento de Surf e as alternativas reais no mapa.

| Fase | Implementação e arquivos | Pendências e próximo passo |
|---|---|---|
| IMP-1 | `hoenn_qa_phase3.py`, `pilot_hoenn.py`, `HoennPilot.rb`: inventário QA03 com IDs e classificação; pickups limitados a interações e recompensas reconhecidas; placas direcionais reescritas em posições comprovadas. Coincidência de posição só é marcada como duplicata quando há equivalente reconhecido. As tabelas de encontros prioritárias do Blue foram preservadas. | Conferir equivalência dos NPCs e treinadores em posições ocupadas; revisar recompensas com páginas condicionais ou efeitos colaterais e variantes de encontros. |
| IMP-2 | `hoenn_imp2_ice.py`, `pilot_hoenn.py`, `HoennPilot.rb`: piso de Sootopolis com rachadura e queda na segunda passagem, apenas onde o retorno e a chegada são verificáveis. A tempestade da crise é visual e some após Rayquaza. A verificação estática aceita uma travessia válida por borda e registra pontos que ainda não comprova a pé. | Tratar pisos com pouso bloqueado; confirmar solução integral do ginásio, obstáculos condicionais, Surf/Dive/Waterfall, correntes e cenas no jogo. |
| IMP-3 | `HoennPilot.rb`, `pilot_hoenn.py`: apresentação nativa adaptada para Hoenn, créditos próprios e retorno ao mapa; não grava o Hall global de Decades. Arte correta de Juan, Archie e Wallace e faixa de créditos copiadas apenas para a instalação privada, após verificação de hash. | Testar apresentação, áudio e save no jogo; concluir artes individuais da Elite Four, trilhas contextuais e a batalha em dupla com Steven. |
| IMP-4 | `HoennPilot.rb`: o NPC existente na casa do Fossil Maniac (origem 126, evento 3) entrega uma TM que ensina Dig. O item é conferido pelo golpe e registrado somente quando entra na Bolsa. | Túnel, Mirage Tower, Safari, concursos e oficina de cinzas seguem abertos; não liberar destinos que estão fora da instalação atual. |
| IMP-5 | `HoennPilot.rb`: placas direcionais, apresentação e disponibilidade pós-Liga usam o idioma selecionado; o painel diferencia região liberada de chegada verificada na instalação. Nenhuma viagem foi adicionada por teleporte de QA. | Auditar e traduzir as falas restantes; implementar transporte de ida e volta após validar as duas regiões no mesmo pacote e conferir preservação de equipe, PC e progresso. |

**Próxima ação:** fechar a classificação dos eventos da IMP-1 no inventário gerado e percorrer no jogo os acessos registrados sem caminho de caminhada demonstrado (começando por Lavaridge e Rota 118 → Rota 119), seguidos das cinco bordas marítimas sinalizadas pelo QA02.
