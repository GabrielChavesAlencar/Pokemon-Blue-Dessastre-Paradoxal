# Hoenn — barra de progresso jogável (12 fases)

**Atualizado:** 14/11/2026. Referência de dados: [hoenn-qa-progresso.json](../data/regions/hoenn-qa-progresso.json). Etapa técnica anterior: [10/10](HOENN_ETAPA_10_SOOTOPOLIS_RAYQUAZA_LIGA.md).

**Acompanhe as DUAS barras separadamente:**

- **Etapas de código existentes:** 10/10 — ██████████ (concluídas e publicadas, sem certificar Game.exe).
- **Fases jogáveis 1–12:** preparação das fases 1 a 12 implementada; execução local/aceite pendentes — ▣▣▣▣▣▣▣▣▣▣▣▣ (▣ = ferramenta pronta; NÃO = jogável).
- **Fases nativamente aprovadas:** 0/12 — □□□□□□□□□□□□ (sem testes reais completos).

| # | Etapa | Preparação | Aceite Game.exe |
|---:|---|---|---|
| 1 | Gerar cópia isolada com 199 mapas e PBS | **Ferramenta preparada, execução local pendente** | ⏳ |
| 2 | Corrigir conexões e colisões dos mapas | **Auditoria de RXDATA/PBS implementada; execução local pendente** | ⏳ |
| 3 | Conferir encontros, NPCs, treinadores e itens | **Perfis-base, itens simples e catálogo de pendências implementados; QA nativo pendente** | ⏳ |
| 4 | Surf, Dive, Waterfall, Strength e puzzles | **HM e gate regional + rochas simples + auditoria fonte; puzzles nativos pendentes** | ⏳ |
| 5 | Equipes Aqua/Magma, Seafloor Cavern | **Gates de história e auditoria de eventos implementados; teste real pendente** | ⏳ |
| 6 | Cave of Origin, clima, Rayquaza | **Gates regionais, auditoria RXDATA e perfil QA06 preparados; cenas nativas pendentes** | ⏳ |
| 7 | Oito ginásios e insígnias locais | **Nove eventos autorais, oito times PBS e auditoria QA07 preparados; Game.exe pendente** | ⏳ |
| 8 | Victory Road e Wally | **Três mapas, Wally, gates de Waterfall e Liga e auditoria QA08 preparados; Game.exe pendente** | ⏳ |
| 9 | Elite Four e Wallace | **Cinco salas, equipes PBS, ordem de vitórias e auditoria QA09 preparados; Game.exe pendente** | ⏳ |
| 10 | Hall of Fame e pós-jogo | **Registro da Liga via BlueRegions, Johto/Sinnoh liberados no circuito e QA10 preparados; Game.exe pendente** | ⏳ |
| 11 | Traduções, placas, áudio e Trainer Card | **199 nomes de mapa, oito insígnias PT-BR, BGM provisória e Trainer Card de Hoenn preparados; Game.exe pendente** | ⏳ |
| 12 | QA da campanha inteira Windows/Android | **Portão integrado QA01–QA12 e 30 casos Windows/JoiPlay preparados; execução nativa pendente** | ⏳ |

**Regra:** nenhuma fase muda para "aprovada" só porque a CI ou um simulador Ruby passaram; exige observação real no Game.exe.

## Fase 01/12 — código implementado

- [scripts/regions/hoenn_qa_phase1.py](../scripts/regions/hoenn_qa_phase1.py) confere a pasta Blue, MapIDs livres, inventário da fonte fixada, arquivos e SHA dos 199 RXDATA originais, tilesets, PNGs usados, sete áudios-base, PBS, oito chefes e perfil de save separado.
- [TESTAR_HOENN.bat](../TESTAR_HOENN.bat) prepara uma **nova pasta** e inicia o Game.exe isolado. A primeira abertura pode compilar e fechar; execute novamente caso ocorra.
- [tests/test_hoenn_qa_phase1.py](../tests/test_hoenn_qa_phase1.py) cobre ausência de arquivos, fonte divergente, MapIDs duplicados, perfil, integridade e bloqueio de substituição.
- O relatório local em `.blue-work/hoenn-qa-fase01-report.json` registra o resultado. Ele não é enviado ao GitHub.
- A árvore pública do doador é fixada em `c59233bdbaac4fbfeca6aa01c7f05be628da2a92`, usando subárvore Git `c3876ecea7545eb3a91b9c8748d7e2b13f07805d`. Não inventar arquivos se houver divergência de versão ou ZIP.

### Executar no Windows

1. Atualize a `main` (por `RUN.bat` ou `git pull origin main`).
2. Tenha a base principal Blue instalada em `game/`, com `game/Game.exe`, `Data/`, `PBS/` e `Plugins/`.
3. Coloque o ZIP privado `The Pokémon World Project - Hoenn.zip` na raiz do clone, sem extrair mapas para o `game/`. Instale Python 3.11+ e tenha internet na primeira execução para obter a árvore de hashes do GitHub.
4. Execute **`TESTAR_HOENN.bat`**. Ele usa `.blue-work/hoenn-source/<prefixo-hash>/` e cria `.blue-work/hoenn-qa-fase01/` sem tocar na instalação principal. Se a fonte não coincidir com a revisão fixada, a montagem abortará com relatório.
5. Confirme no relatório: `copy.maps_present=199`, `copy.trainer_boss_pbs_entries=8`, `copy.distinct_save_profile="Hoenn Piloto"`. Isso ainda é verificação de **arquivos**, não de jogabilidade.
6. No Game.exe da cópia, aguarde a compilação. Se fechar depois dela, abra o BAT outra vez. Verifique os marcadores `Data/blue-hoenn-compiled.txt` e mensagens de erro.
7. Faça novo jogo; confirme início em casa em Littleroot, sprite e movimentação, pelo menos uma porta, inicial, uma batalha e Centro Pokémon. Teste **salvar, fechar e carregar**.
8. Abra Decades principal e seu save anterior. Confirme que a cópia não alterou os dados nem o perfil de save principal.

**Comandos equivalentes:**

~~~powershell
py -3 scripts/regions/hoenn_qa_phase1.py
py -3 scripts/regions/hoenn_qa_phase1.py --prepare
py -3 scripts/regions/hoenn_qa_phase1.py --prepare --offline
~~~

O primeiro é auditoria de pasta, não instala; `--prepare` usa o ZIP; `--offline` só funciona após gerar o inventário local fixo.

### Checklist de aprovação real 1/12 — pendente

- [ ] 199 RXDATA e dependências fonte verificadas na máquina; base Blue preservada.
- [ ] Game.exe recompilou PBS e abriu sem erro (não confundir presença de marcador com teste visual).
- [ ] Novo jogo em Littleroot, início, porta, NPC, inicial e batalha testados.
- [ ] Save/reload funciona no perfil separado; save Decades intacto.
- [ ] Logs/relatório e capturas revisados; não há erro bloqueante de compilação.
- [ ] Direitos/créditos dos assets a distribuir avaliados antes de fazer pacote público.

A auditoria de arquivos e testes sintéticos NÃO executam o Game.exe. A fase 1 só fica **1/12 aprovada** quando houver evidência da execução no computador. O preparador de dados da **2/12 — mapas/conexões** está descrito abaixo; os dois aceites nativos seguem pendentes.

**Preservação:** ZIP e arquivos `.rxdata`, áudios, PNG e Game.exe do doador não devem ser enviados à branch pública. Os bugs conhecidos do ginásio de Mossdeep, Steven, Dive, Sky Pillar e Hall of Fame permanecem tarefas das fases seguintes.


## Fase 02/12 — mapas e conexões (preparação técnica)

**A barra continua em 0/12 aprovada no Game.exe**. A Fase 2 passou a ter verificação de dados planejada, mas não foi certificada como jogável.

### Código preparado

- [scripts/regions/hoenn_qa_phase2.py](../scripts/regions/hoenn_qa_phase2.py): lê a **cópia gerada na Fase 1**, confere exatamente 199 RXDATA e o MapInfos correspondente; rejeita IDs, eventos e warps nativos inválidos, landing cells fora de limites, scripts de transferência sem origem correta e sobreposição de eventos.
- Confere as **conexões de borda realmente adicionadas** em PBS, seus dois lados, offsets e a faixa de dimensões. Rejeita uma conexão de Hoenn que inesperadamente aponte para um MapID nativo de Decades/Kanto/Johto.
- Confere se os destinos das portas da abertura (WARP_PAIRS) coincidem **com as coordenadas** dos destinos originais, não só com o número do mapa.
- Gera relatório `.blue-work/hoenn-qa-fase02-report.json` com número de eventos e transferências e mapas sem saída *observada* nos scripts de transferência. Ausência de saída observada não prova isolamento: travessias por HM, scripts específicos ou puzzles podem existir.
- [tests/test_hoenn_qa_phase2.py](../tests/test_hoenn_qa_phase2.py) acrescenta testes sintéticos de integridade, duplicação, remapeamento, posição e proteção de arquivo.
- [TESTAR_HOENN.bat](../TESTAR_HOENN.bat) agora roda Fase 1, depois a **auditoria read-only da Fase 2** e só abre o Game.exe isolado se ambas as verificações estáticas passarem. O jogo principal não é modificado.

### Como executar

1. Atualize a `main` do repositório.
2. Com a instalação privada `game/` e seu `The Pokémon World Project - Hoenn.zip` na raiz, execute **`TESTAR_HOENN.bat`**.
3. Confirme no relatório local da Fase 1 a existência da cópia isolada `.blue-work/hoenn-qa-fase01/`.
4. Confira o relatório de mapas: `.blue-work/hoenn-qa-fase02-report.json`, cujo campo `status` deve ser `STATIC_MAP_CONNECTIONS_AUDITED`, com `maps_read=199` e `errors=[]`.
5. Se o relatório apontar MapID, porta ou PBS incorreto, **não substitua os arquivos originais**. Corrija o mapeamento e reconstrua a cópia em nova pasta (nunca sobrescreva uma cópia com save).
6. Quando abrir o Game.exe, percorra Littleroot, Oldale, Petalburg, Rustboro, Slateport, Mossdeep, rotas Surf, Dive, Sootopolis, Sky Pillar, Victory Road e Liga. Teste ida e volta de portas e passagens, eventos condicionais, batalha, save e retorno.
7. Registre coordenada, mapa, direção, flag e estado do save de cada falha; valide Decades e outros pilotos separadamente.

O auditor de dados pode ser rodado também de modo independente:

~~~powershell
py -3 scripts/regions/hoenn_qa_phase2.py --copy ".blue-work/hoenn-qa-fase01"
~~~

### Aprovação nativa — ainda pendente

- [ ] Cópia privada real gerada e 199 RXDATA carregados.
- [ ] Relatório `hoenn-qa-fase02-report.json` sem erros de coordenadas, mapa, portais ou PBS.
- [ ] Game.exe compilou, iniciou e percorreu fisicamente os segmentos da campanha.
- [ ] Portas de ida/volta, bloqueios por Surf/Dive/Waterfall, escadas e puzzles funcionaram.
- [ ] Save/reload e instalação original confirmados intactos.
- [ ] Eventuais falhas anotadas e corrigidas, com nova regressão.

**Aviso:** este auditor lê tabelas e código de eventos sem executá-los. Não demonstra que os gráficos, colisões, HMs, páginas condicionais ou movimentação funcionam na engine. Nenhuma fase foi promovida para "aprovada" somente por CI.


## Fase 03/12 — encontros, itens, NPCs, placas e treinadores

**Estado:** implementação técnica em cópia isolada; sem aprovação de jogabilidade. A preparação avança para 3/12 e o aceite real permanece 0/12.

### Implementado na fase

- `scripts/regions/hoenn_qa_phase3.py` lê o `PBS/encounters.txt` **real** da fonte Hoenn de revisão fixa (`c59233bdbaac4fbfeca6aa01c7f05be628da2a92`), usando `Source.read` com SHA Git verificado.
- Importa somente o **perfil padrão de cada MapID** dentro do piloto de 199 mapas: grama (`Land`), cavernas (`Cave`), água (`Water`), pesca (`OldRod/GoodRod/SuperRod`) e pedras (`RockSmash`), conforme existam na fonte. **Não inventa encontros para mapas sem tabela.**
- Preserva os perfis de `Land/Cave` que o projeto Blue já personalizou e adiciona somente os métodos **ausentes**. O novo `PBS/encounters_hoenn_pilot.txt` possui **uma única seção por MapID remapeado**, evitando definições duplicadas.
- O doador contém tabelas especiais `[MapID,versão]` para enxames de Pokémon. Essas versões **não entram automaticamente** no jogo, pois exigem lógica de clima/evento. O relatório separa essas versões de `[MapID]` padrão.
- Algumas porcentagens do `PBS` original somam valores diferentes de 100% (por exemplo 200%, 95% ou 30%); o montador usa normalização determinística e documenta o total original por mapa/método. **As porcentagens normalizadas não devem ser apresentadas como chances canônicas de Emerald.**
- Inspeciona a fonte `Data/MapNNN.rxdata` de todos os 199 mapas na preparação local, **sem executar scripts de terceiros**. Recria apenas `Item/HiddenItem` com um `pbItemBall(:ITEM)` inequívoco, sem condição inicial e sem colisão física com evento já criado. Verifica se o item existe no `game/PBS/items*.txt` do Blue. Utiliza `BlueHoennPilot.pickup` e Self Switch A para não duplicar o item depois de salvar/carregar.
- Mantém **um relatório de pendências por mapa** para eventos candidatos de treinadores, NPCs, diálogos e placas que não são seguros de copiar automaticamente. Posições já ocupadas e itens condicionais também são sinalizados. Não publica diálogos, sprites ou scripts do doador.
- Integra o verificador `hoenn_qa_phase3.py` ao `TESTAR_HOENN.bat` **depois das auditorias 1/12 e 2/12**; a auditoria verifica integridade do PBS e lê o manifesto de source events gerado localmente.

### Proteção de saves anteriores

**A partir desta fase**, `TESTAR_HOENN.bat` usa a nova pasta:

`.blue-work/hoenn-qa-fase03/`

Isso evita sobrescrever a cópia original `.blue-work/hoenn-qa-fase01/` e seus saves. Reexecutar o BAT **não recria/atualiza em silêncio** uma cópia que já existe. Caso o projeto avance para a próxima fase, escolher outra pasta de saída ou arquivar a antiga após backup e reconstruir; nunca sobrescrever a cópia com saves.

### Executar no Windows

1. Atualize a branch `main` e confirme a instalação principal em `game/`.
2. Coloque seu ZIP **The Pokémon World Project - Hoenn.zip** na raiz, sem enviar RXDATA nem áudios de terceiros ao GitHub.
3. Execute **`TESTAR_HOENN.bat`**. A Fase 1 prepara a cópia privada nova, a Fase 2 verifica mapas/warps/PBS e a Fase 3 valida encontros e inventário de eventos. O Game.exe só abre se as três verificações de arquivo passarem.
4. Leia estes relatórios na pasta local ignorada:
   - `.blue-work/hoenn-qa-fase03-prep-report.json` — preparação e SHA da fonte;
   - `.blue-work/hoenn-qa-fase03-mapas-report.json` — auditora de portas, PBS e MapIDs;
   - `.blue-work/hoenn-qa-fase03-report.json` — métodos novos, pesos normalizados, itens seguros adicionados e contagem de NPCs/treinadores/placas pendentes.
5. No jogo, teste a pesca com três varas, encontros Surf, grama/caverna, itens visíveis e ocultos, batalha com treinador, derrotas, save/reload e troca de região. Não considere a existência do arquivo PBS como prova de que o motor selecionou esse tipo de encontro corretamente.
6. Para investigar NPCs e treinadores que ainda faltam, leia o relatório **`Hoenn pilot.json`** na cópia, seção `qa3.source_events.unimplemented_source_event_candidates`. Cada entrada identifica MapID original, x/y, tipo de evento e motivo de revisão, sem executar o script do doador.

### Evidência adicional da fonte pública

O workflow [Hoenn QA 03 - auditar fonte original de encontros](../.github/workflows/hoenn_qa3_source_audit.yml) busca **temporariamente** apenas dois PBS de texto (encontros e treinadores) da revisão pinada, confere SHA de cada arquivo, descarta os bytes após processamento e executa os testes sintéticos. Ele não importa novos sprites, mapas, sons ou executáveis para a `main`.

### Critérios de aprovação nativa — AINDA ABERTOS

- [ ] Nova cópia da Fase 3 montada com o ZIP real e scripts atuais.
- [ ] As três auditorias locais sem bloqueios; documentação dos perfis originais normalizados revisada.
- [ ] Surf/água, pesca e Rock Smash realmente selecionam seus Pokémon no Game.exe.
- [ ] Os itens incondicionais não duplicam após salvar/recarregar; nenhum item desconhecido causa erro.
- [ ] Revisar **todos** os NPCs, placas, diálogos, itens condicionais e treinadores da lista de pendências. Não marcar como completos apenas pelo inventário.
- [ ] Validar líderes e encontros com o balanceamento Blue e regras das insígnias (sem níveis fixos na UI).
- [ ] Saves Decades/Kanto/Johto/Sinnoh intactos; Android/JoiPlay continua pendente.

**Limitações:** esta fase não converte automaticamente treinadores de mapas do doador em eventos de batalha, não importa sprites/NPCs condicionalmente animados, não traduz todas as placas e não implementa os encontros de enxame. São lacunas explicitamente abertas; a barra mede **preparação de código**, não integralidade de conteúdo.


## Fase 04/12 — movimentos de campo, pedras e quebra-cabeças

**Implementação técnica preparada (4/12), aceite em Game.exe pendente (0/12).** Esta fase não instala hooks globais nas HMs do Blue e não muda a política de insígnias de Decades/Kanto/Johto/Sinnoh.

### Implementado

- `HoennPilot.rb` recebeu `field_move_ready?(move)` com exigência simultânea de **insígnia de Hoenn**, **HM/TM correspondente registrado e presente na Bolsa** e **Pokémon da equipe conhecendo a técnica**. Tabela: Cut/Stone; Flash/Knuckle; Rock Smash/Dynamo; Strength/Heat; Surf/Balance; Dive/Mind; Waterfall/Rain. Retorna falso quando o save não está na região Hoenn.
- A entrada **submersa** via transferência autoral da fase 10 exige Dive completo (não apenas uma flag); os scripts não bloqueiam deliberadamente a saída de jogadores que já estão em mapas submersos. A passagem **Ever Grande Sul (91) → Norte (322)** exige Waterfall completo, evitando desbloqueio somente por Rain Badge. As conexões aquáticas em PBS sem evento continuam dependendo da engine nativa.
- `tunnelers`, após a missão de Rusturf e Dynamo Badge, oferece Strength (`HM04` ou variante equivalente cadastrada) uma vez por save de Hoenn. Não dá o item sem espaço nem tenta adicionar IDs ausentes. O recebedor é provisório; comparar a cena canônica com o detonado.
- `juan`, depois da Rain Badge, oferece Waterfall (`HM07` ou variante equivalente cadastrada) com checagem de espaço, registro único e possibilidade de falar novamente caso não haja espaço. Não altera a recompensa TM anterior.
- `rock_smash_obstacle(event_id)` só remove uma pedra após validar habilidade local, confirmar a ação e ativar **Self Switch A**, persistindo flag de Hoenn. `strength_boulder(event_id)` tenta empurrar a pedra pelo método de movimento da engine e retorna falha se a colisão impedir. Sem teleporte e sem alterar posição do jogador artificialmente.
- `hoenn_qa_phase4.py` inspeciona as posições dos obstáculos no RXDATA real do doador, reautora **apenas nomes exatos, incondicionais e de uma página** de pedras de Rock Smash/Strength, onde não há evento sobreposto e existe um sprite equivalente já instalado no Blue. Ambiguidades, falta de sprite, páginas condicionais, pistas de Surf/Dive/Waterfall e gelo entram no **backlog do relatório** — não são falsamente implementadas.
- `TESTAR_HOENN.bat` agora prepara cópia isolada **`.blue-work/hoenn-qa-fase04/`**, preservando a da Fase 3, e executa as auditorias 1→2→3→4 antes de abrir o Game.exe. O relatório é `.blue-work/hoenn-qa-fase04-report.json`. O `mkxp.json` desta cópia usa **`dataPathOrg = Dessastre Paradoxal Hoenn QA04`** e **`dataPathApp = Hoenn QA Fase04`**, impedindo compartilhamento acidental do diretório de saves com as fases anteriores.
- A CI inclui teste Ruby com badges, HMs, golpe no time, rocha, boulder, bloqueio Ever Grande/Dive, save/reload e troca para Kanto. O workflow específico audita eventos da revisão original fixa do doador, em leitura, sem importar mapas ou scripts ao GitHub.

### Como executar

1. Atualize a `main`, confirme `game/Game.exe` e `The Pokémon World Project - Hoenn.zip` original na raiz do clone, depois abra `TESTAR_HOENN.bat`.
2. Confira os relatórios `hoenn-qa-fase04-prep-report.json`, `hoenn-qa-fase04-mapas-report.json`, `hoenn-qa-fase04-encontros-report.json` e `hoenn-qa-fase04-report.json` sob `.blue-work/`.
3. No Game.exe isolado: obtenha cada insígnia correspondente, HM e Pokémon com o movimento, e verifique o **antes/depois**; tente Rock Smash (repetir e salvar/recarregar), empurrar Strength e bloqueio quando não puder mover.
4. Teste **Surf em praias e bordas**, **Dive em rotas marinhas**, emergir após Dive e **Waterfall** em Ever Grande. Movimentos de campo da engine ainda não foram interceptados universalmente; o teste nativo deve identificar se o motor os permite indevidamente fora do contexto regional.
5. Teste **gelo de Sootopolis**, pedras e correntes de Seafloor Cavern e **Victory Road**. Um gráfico ou script inventariado não significa puzzle funcional. Registre MapID, coordenadas, insígnia, golpe no time e se é possível continuar/voltar.
6. Teste troca de região e saves Decades/Kanto/Johto/Sinnoh. Não renomeie nem recopie os assets do doador ao jogo principal.

### Resultado auditado da origem fixa (GitHub Actions)

A leitura de **32 mapas reais do doador** na revisão fixada identificou **39 eventos StrengthBoulder** (Seafloor Cavern e Victory Road), **64 eventos Ice Floor Puzzle** (ginásio de Sootopolis), **3 eventos Dive** e **1 bloqueador relacionado a Waterfall**. Esses 64 eventos de gelo usam **três páginas** na fonte e, por segurança, não foram copiados como se o puzzle estivesse concluído. Os eventos exatos Strength usam o sprite `OBJ_RSE_Strength Boulder`, disponível no ZIP original. Se não houver sprite nativo do Blue, somente a **cópia local isolada** recebe o PNG desse nome, após confirmação de hash da revisão; nenhum asset é enviado ao GitHub público.

A quantidade **efetivamente instalada** de boulders depende de não haver sobreposição de eventos e da integridade de sua cópia privada. Consulte `qa4.new_safe_obstacles` e `qa4.source_obstacles_needing_review` em `Hoenn pilot.json`. A fonte não demonstrou rochas Rock Smash nesses 32 mapas selecionados; o construtor verifica os 199 mapas na montagem local, sem presumir que elas não existam em outras áreas.

### Critérios de aceite nativo — pendentes

- [ ] Cópia fase 4 gerada com ZIP pinado, 199 mapas reais e relatórios sem bloqueio.
- [ ] Rocha Rock Smash visível, bloqueia, desaparece, não reaparece após save/reload.
- [ ] Strength empurra pedra pelo layout real, não empurra através de paredes e permite resolver puzzles.
- [ ] Surf e Dive usam colisões corretas, não atravessam fronteiras sem HM e permitem voltar.
- [ ] Waterfall sobe/desce sob controle da Rain Badge e da engine sem perder posições.
- [ ] Puzzle de gelo de Juan/Sootopolis, Seafloor e Victory Road foram efetivamente resolvidos.
- [ ] Batalhas, saves e trocas de região anteriores permanecem intactos.
- [ ] Windows e Android/JoiPlay testados separadamente.

**Limites explícitos:** sem hooks nas rotas aquáticas nativas, sem solução completa do gelo, sem confirmação visual de movimentos/efeitos e sem correção de todos os obstáculos condicionais do doador. A CI mede apenas scripts, entradas estáticas e simulações; a barra aprovada continua em 0/12.


## Fase 05/12 — Aqua, Magma, Seafloor Cavern, Archie e Kyogre

**Preparação técnica: 5/12. Aprovação jogável nativa: 0/12.** O código novo **não** importa scripts do doador e **não** altera a instalação principal de Decades nem os saves de Kanto, Johto ou Sinnoh.

### Correções efetivas

- A **cena invisível de Groudon** no esconderijo Magma (Map189, x21/y19) agora usa evento **Player Touch** (`trigger=1`, `through=true`): o jogador não precisa apertar ação em um evento invisível. Ainda exige derrotar Maxie, e o despertar continua único por save.
- A fuga do submarino Aqua agora exige **o roubo em Slateport e a vitória contra Matt**, e não apenas uma flag de batalha solta.
- **Entrada externa de Seafloor Cavern** (Map227–236): exige a sequência regional `groudon_awakened`, `slateport_submarine_stolen`, `submarine_escaped`, `space_center_saved`, `hm_dive_received` e **Mind Badge de Hoenn**. O acesso físico submerso ainda depende dos guards de Dive da Fase 4.
- **Saídas da caverna e escadas entre os dez mapas internos não dependem dessas flags de entrada**, evitando aprisionar o jogador em um save parcialmente migrado.
- A batalha de **Archie** e o despertar de **Kyogre** exigem a sequência completa e ocorrer no santuário Map236. Uma derrota não marca vitória, a batalha não se repete após vitória, e Kyogre não desperta antes de Archie.
- Os scripts de batalha continuam usando o **motor do Blue**, incluindo balanceamento dinâmico por insígnias; os números PBS são referências, não níveis fixos para o site.

### Auditoria estática e código

- `scripts/regions/hoenn_qa_phase5.py` confere **9 eventos autorais centrais**, suas coordenadas, handlers e trigger correto, além de **18 eventos de recrutas** (4 Pyre, 7 Magma, 5 Aqua, 2 Centro Espacial). Também confere os PBS de Maxie, Tabitha, Matt e Archie.
- `scripts/regions/inspect_hoenn_qa5_public.py` consulta **oito mapas RXDATA** da revisão imutável Hoenn, valida os SHA-1 Git previamente conferidos na subárvore imutável `c3876ecea7545eb3a91b9c8748d7e2b13f07805d` e usa `data/regions/hoenn-source.json` para confirmar a revisão; produz somente metadados de eventos. Nenhum script, fala ou binário do doador é publicado.
- Os NPCs e treinadores da fonte sem correspondência validada continuam no backlog. **Não** se pode afirmar que todas as equipes e cenas da campanha já estejam completas.
- `TESTAR_HOENN.bat` usa a nova pasta privada `.blue-work/hoenn-qa-fase05/` e novo perfil mkxp **Hoenn QA Fase05** / **Dessastre Paradoxal Hoenn QA05**; cópias e saves das fases anteriores permanecem separados.

### Executar e conferir

1. Atualize a `main`, mantenha o `The Pokémon World Project - Hoenn.zip` verdadeiro na raiz e o `game/Game.exe` intacto.
2. Rode `TESTAR_HOENN.bat`: as auditorias das fases 1→2→3→4→5 precisam passar antes da abertura do piloto.
3. Leia os relatórios locais `.blue-work/hoenn-qa-fase05-prep-report.json`, `hoenn-qa-fase05-mapas-report.json`, `hoenn-qa-fase05-encontros-report.json`, `hoenn-qa-fase05-campo-report.json` e `hoenn-qa-fase05-report.json`.
4. Teste em ordem: Mt. Pyre/Red Orb → Magma Emblem/Jagged Pass → Tabitha/Maxie/Groudon → Slateport/Submarino → Lilycove/Matt/fuga → Tate e Liza/Centro Espacial/Steven/Dive → Rota 128/Seafloor → Archie/Kyogre.
5. Registre MapID/x/y, flags e resultado da batalha para cada bloqueio. Tente entrar antes e depois dos requisitos, sair da caverna, salvar/carregar e retornar a outra região.

### Aprovação do Game.exe — ainda pendente

- [ ] Gerar a cópia QA05 com os 199 mapas reais e compilar/iniciar Game.exe.
- [ ] Groudon dispara por contato após Maxie, mas não antes.
- [ ] Portas de Aqua/Magma e Seafloor respeitam a ordem sem softlock.
- [ ] Submarino foge somente depois de Slateport/Matt, sem duplicação.
- [ ] Strength e correntes dos **dez interiores** de Seafloor são transponíveis fisicamente.
- [ ] Archie, Kyogre e os efeitos de clima ocorrem corretamente, com reentrada e save/reload.
- [ ] Trainer teams e áudio, tradução de NPCs/placas e sprites aprovados visualmente.
- [ ] Saves Blue/Decades e Kanto/Johto/Sinnoh preservados; Android/JoiPlay testado separadamente.

**Limites:** não foram reproduzidos todos os puzzles, animações lendárias ou o movimento físico do submarino. Fase 6/12 cuidará da crise do clima, Cave of Origin e Rayquaza. A CI não comprova jogabilidade nativa.

## Fase 06/12 — crise climática, Wallace, Cave of Origin e Rayquaza

**Preparação técnica: 6/12. Aprovação nativa Game.exe: 0/12.** Esta fase aprimora os eventos da Etapa 10/10, sem distribuir RXDATA/scripts do doador e sem alterar o motor de batalha Blue/Decades.

### Mudanças no piloto isolado

- A sequência só começa quando **Groudon despertou, Archie foi derrotado e Kyogre despertou**. O evento de Steven em **Sootopolis City (Map83, x32/y33)** só modifica flags no mapa correto.
- **Cave of Origin** usa os MapIDs de origem 238–240. Wallace na sala B1F (**Map240, x11/y16**) só ativa a busca por Rayquaza após o início da crise, no próprio mapa.
- **Sky Pillar** usa os MapIDs 241–248. Wallace no exterior (**Map241, x13/y8**) libera o interior; a transferência externa aos andares superiores (243–248) é bloqueada até essa conversa. As saídas e transferências internas **não** prendem o jogador em um save antigo.
- Rayquaza no topo (**Map248, x15/y15**) só encerra a crise depois da ordem correta, **uma única vez por save regional**. Os flags `rayquaza_summoned` e `crisis_resolved` ficam no estado de Hoenn. Juan continua bloqueado até a resolução, sem introduzir níveis fixos ou insígnias duplicadas.
- O arquivo `scripts/regions/hoenn_qa_phase6.py` verifica **cinco âncoras de história**, suas coordenadas, scripts e triggers nos RXDATA da **cópia privada**, além de conferir os mapas Cave 238–240, Sky Pillar 241–248, manifesto e guardas Ruby efetivamente instalados.
- `TESTAR_HOENN.bat` agora prepara `.blue-work/hoenn-qa-fase06/`, com perfil de save **Hoenn QA Fase06** (organização **Dessastre Paradoxal Hoenn QA06**). Roda sequencialmente auditorias QA01–QA06; relatórios ficam exclusivamente em `.blue-work/`. O perfil QA05 e anteriores permanecem inalterados.

### Teste local no Windows

1. Atualize `main`, mantenha sua instalação `game/` e o ZIP original **The Pokémon World Project - Hoenn.zip** sem modificar. Execute `TESTAR_HOENN.bat`.
2. Confira o relatório `.blue-work/hoenn-qa-fase06-report.json`, com `status=CLIMATE_STORY_STATICALLY_VERIFIED`, cinco cenas verificadas e `native_game_exe_approved=false`. Falha de SHA, mapa, evento ou perfil deve **bloquear a abertura**.
3. No Game.exe, teste Sootopolis **antes** de derrotar Archie e despertar Kyogre: a crise não pode iniciar. Após ambas as lendas despertarem, converse com Steven e procure Wallace na Cave of Origin.
4. Antes de falar com Wallace em Cave of Origin, verifique a entrada de Sky Pillar bloqueada. Após a conversa, vá ao exterior da torre; **antes de falar com Wallace no exterior**, teste a transferência para os andares superiores, que deve continuar fechada. Depois da autorização, suba ao topo.
5. Confirme que Rayquaza só resolve o clima após o passo anterior, que a cena não se repete no mesmo save e que o ginásio de Juan abre somente depois disso. Salve, feche, carregue e tente entrar/sair de Cave of Origin e Sky Pillar novamente.
6. Verifique visualmente **chuva/sol/clima real, transição, música, sprite/animação de Rayquaza e puzzles**; registre como **pendente** quando houver apenas diálogo/flag. Faça regressão com saves de Decades/Kanto/Johto/Sinnoh e, separadamente, Android/JoiPlay.

### Critérios de aceite nativo — não cumpridos automaticamente

- [ ] Gerar a cópia real QA06, iniciar o Game.exe, compilar e salvar/recarregar.
- [ ] Clima visível e áudio da crise reproduzidos corretamente, sem afetar outras regiões.
- [ ] Cave of Origin, Wallace, todas as escadas da torre e topo navegáveis, sem softlock.
- [ ] Sprite, cinemática, transição de clima e persistência do evento de Rayquaza aprovados.
- [ ] Juan não abre antes de Rayquaza e continua usando os níveis dinâmicos de Decades.
- [ ] Teste de replay, derrota/reinício, troca de região e preservação integral dos saves.
- [ ] QA Windows e Android/JoiPlay documentados em evidências separadas.

**Limites:** as transições climáticas visuais e a cinemática de Rayquaza permanecem **não implementadas/aprovadas nativamente**; os puzzles originais da torre e a resolução dos caminhos por HMs exigem teste dentro do Game.exe. Os cinco contratos RXDATA e os testes Ruby/Python não provam essas funcionalidades. A barra de aceite permanece **0/12**.

## Fase 07/12 — oito ginásios e insígnias regionais

**Preparação técnica: 7/12. Aprovação jogável nativa: 0/12.** As oito batalhas já existiam no Ruby/PBS de Hoenn; esta fase adiciona **despacho com guarda de mapa** aos eventos reais do piloto e um verificador de todos os ginásios. Não altera o motor de batalha nem congela níveis de treinadores.

### Inventário de líderes e insígnias de Hoenn

| Líder | Mapa original | Insígnia de Hoenn | Movimento de campo relacionado |
|---|---|---|---|
| Roxanne / Rustboro | 27 | STONE | Cut |
| Brawly / Dewford | 31 | KNUCKLE | Flash |
| Wattson / Mauville | 47 | DYNAMO | Rock Smash |
| Flannery / Lavaridge | 63 | HEAT | Strength |
| Norman / Petalburg | 20 | BALANCE | Surf |
| Winona / Fortree | 68 | FEATHER | Fly |
| Tate e Liza / Mossdeep | 82 (dois NPCs) | MIND | Dive |
| Juan / Sootopolis | 87 | RAIN | Waterfall |

**Regras:** são *oito insígnias locais*, não globais. O registro é feito pelo `BlueRegions.award(..., "HOENN", badge)` após vitória real; o nível da batalha fica sob **Blue/Decades**. A tabela de movimentos é um contrato de referência, **não** prova de que os comandos nativos Cut/Flash/Fly/etc. foram liberados corretamente.

### O que foi efetivamente programado

- O novo `BlueHoennPilot.qa7_gym_battle(:INSIGNIA)` usa uma lista fechada dos **oito ginásios** e a conversão real do MapID da cópia isolada. Não aceita ginásio errado, nome arbitrário de função, nem outro save regional. Os scripts originais de cada líder continuam sendo responsáveis pela vitória, flag, TM e acesso às HMs.
- O gerador `scripts/regions/pilot_hoenn.py` conectou os **nove eventos de NPCs** ao dispatcher: Roxanne, Brawly, Wattson, Flannery, Norman, Winona, **Tate e Liza (dois NPCs, uma batalha dupla)** e Juan. Posições de mapa não são inventadas; são as âncoras autorais já usadas pelo piloto.
- `scripts/regions/hoenn_qa_phase7.py` confere as nove posições de RXDATA, scripts e triggers de interação, a presença de **oito equipes PBS distintas**, a correspondência das oito insígnias, e se o Ruby protegido foi efetivamente instalado. Falha de evento ausente, fora do mapa, duplicado ou equipe faltante bloqueia a abertura.
- `TESTAR_HOENN.bat` agora prepara `.blue-work/hoenn-qa-fase07/` com novo perfil de saves **Hoenn QA Fase07** / **Dessastre Paradoxal Hoenn QA07**, sem sobrescrever QA04–QA06 nem a base `game/`. Executa QA01–QA07 antes da abertura do Game.exe.
- Há testes Python para ausência, sobreposição, posição, trigger e scripts de líderes; um teste Ruby verifica **mapa correto, rota para cada líder, tentativa fora do mapa e troca de região**. A CI mantém os testes históricos de derrota/vitória/TM/recompensa em cada etapa.

### Como verificar localmente

1. Atualize a `main` com o `game/` instalado e o ZIP privado e fixado de Hoenn na raiz; rode **`TESTAR_HOENN.bat`**. Se a cópia da Fase 7 foi criada antes de esta atualização chegar, não a sobrescreva: remova **somente uma cópia QA07 sem save importante**, ou use uma pasta nova via preparador.
2. Verifique `.blue-work/hoenn-qa-fase07-report.json`: status `EIGHT_GYM_BINDINGS_STATICALLY_VERIFIED`; nove eventos de líder, oito mapas, oito PBS, `native_game_exe_approved=false`.
3. No Game.exe, enfrente Roxanne → Brawly → Wattson → Flannery → Norman → Winona → Tate e Liza → Juan, respeitando os eventos de história e itens de campo. Uma derrota jamais pode liberar a insígnia.
4. Teste as peculiaridades dos ginásios, incluindo **portas de Norman, interruptores elétricos de Wattson, saídas de vapor de Flannery, dupla Tate/Liza e gelo em Sootopolis**. Registre MapID, coordenadas, captura e log de qualquer bloqueio.
5. Confirme a insígnia no estado e no Trainer Card regional, equipe e nível escalonados pelo Blue, TM correta sem duplicação (inclusive Bolsa cheia), save/reload e rematch. No oitavo ginásio, a crise de Rayquaza deve estar resolvida.
6. Confirme que nenhuma insígnia de Hoenn libera ações indevidas em Decades, Kanto, Johto ou Sinnoh; teste novamente as cópias antigas e Android separadamente.

### Critérios de aceite ainda pendentes no Game.exe

- [ ] Oito ginásios e salas realmente alcançáveis por movimento e colisões de mapa.
- [ ] Treinadores secundários, puzzles, portas e obstáculos totalmente funcionais (não só inventariados).
- [ ] Equipes e batalhas corretas com *escalonamento dinâmico de Blue*, incluindo modo de batalha dupla.
- [ ] Oito vitórias geram oito insígnias locais sem repetição ou recompensa duplicada após salvar/carregar.
- [ ] Trainer Card exibe corretamente as oito insígnias, e golpes de campo obedecem cada requisito regional.
- [ ] Sem vazamento de flags, sprites ou saves para Decades, Kanto, Johto e Sinnoh.
- [ ] Game.exe e Android/JoiPlay verificados com evidências reais, em separado.

**Importante:** a auditoria PY/Ruby prova apenas a estrutura **autoral** e seus contratos, não que uma campanha completa, a interface, os puzzles ou os visuais sejam jogáveis. Por isso o marco de aceite permanece em **0/12**.

## Fase 08/12 — Victory Road, Wally e acesso à Liga

**Preparação técnica: 8/12 (66,7%). Aprovação jogável nativa: 0/12.** Foi publicada na `main` a auditoria da **Victory Road 1F (Map250), B1F (Map251), B2F (Map252)**, ligando a parte sul e norte de Ever Grande à Liga, sem substituir os mapas originais da cópia isolada ou alterar o motor de batalha Decades.

### Implementação realizada

- `BlueHoennPilot.qa8_league_badges?` exige **STONE, KNUCKLE, DYNAMO, HEAT, BALANCE, FEATHER, MIND e RAIN** dentro do estado regional `HOENN`; possuir apenas a Rain Badge ou insígnias de outras regiões não autoriza pular o percurso.
- `BlueHoennPilot.wally_victory_road` só executa no **Map250 remapeado** e exige oito insígnias. Em derrota, o encontro pode ser tentado novamente; em vitória grava `wally_road_defeated` sem promover o Wally a líder ou mudar balanceamento.
- As transferências autorais da `stage10_transfer` exigem **Waterfall pronto** (insígnia + HM correto na Bolsa + Pokémon com o movimento) quando se chega do **sul de Ever Grande (91)** para Victory Road (250) ou Ever Grande Norte (322). Os saltos dentro da caverna não exigem novamente HM.
- A saída **Victory Road 1F (250) → Ever Grande Norte (322)** exige vencer Wally; o acesso à **Liga (Map93 e salas)** exige oito insígnias regionais + Wally. O retorno das camadas da caverna não é bloqueado artificialmente.
- O inventário inclui o caminho lógico do autor: `91 → 250 → 251 → 252`, `250 → 322 → 93`. São **ligações de referência, não confirmação de jogabilidade**, pois colisões, escadas, ondas, encontros selvagens e os puzzles nativos não foram testados.
- `scripts/regions/hoenn_qa_phase8.py` relê os mapas reais no perfil privado e confere o evento automático de Wally **(Map250, 8,26)**, a placa da Liga **(Map322, 23,16)**, os cinco Pokémon do PBS `[BLUE_HOENN_WALLY,Wally,1025]` e os obstáculos recriados pela QA04 versus os ainda pendentes. Se faltarem eventos, scripts, mapas ou houver divergência de manifesto, a checagem bloqueia.
- A geração usa `.blue-work/hoenn-qa-fase08/` e save `Hoenn QA Fase08` / `Dessastre Paradoxal Hoenn QA08`; a base `game/`, QA04–QA07 e os saves das demais regiões permanecem separados.
- `TESTAR_HOENN.bat` executa auditorias **QA01–QA08**, cada uma com relatório independente, antes da abertura da nova cópia.
- Os testes Python sintéticos verificam contrato dos mapas, evento do rival, placa, equipe PBS, inventário de obstáculos e falhas artificiais. Os testes Ruby simulam perda/vitória, bloqueios de Waterfall, progressão, retorno e isolamento regional. A CI é apenas regressão de contratos; não executa `Game.exe`.

### Equipe de Wally (referência Emerald; níveis não são fixados por este plano)

| Pokémon | Nível de referência |
|---|---:|
| Altaria | 44 |
| Delcatty | 43 |
| Roselia | 44 |
| Magneton | 41 |
| Gardevoir | 45 |

**O escalonamento de Pokémon no jogo continua pertencendo ao Blue/Decades.** Os níveis acima identificam a origem da equipe e são usados apenas para validar os dados PBS.

### Como executar a fase 8 no PC

1. Atualize a `main`, instale a base em `game/` e mantenha o ZIP original do projeto Hoenn na raiz, sem renomear os arquivos RXDATA.
2. Execute `TESTAR_HOENN.bat`; será criada a cópia **Hoenn QA Fase08**. Veja `.blue-work/hoenn-qa-fase08-report.json`, que deve registrar `VICTORY_ROAD_WALLY_STATICALLY_VERIFIED`, sem declaração de aceite nativo.
3. No `Game.exe` isolado, avance até obter as oito insígnias. Ensine Waterfall a um Pokémon e confirme que a Bolsa contém o HM com o movimento correto.
4. Entre por Ever Grande Sul; percorra **Victory Road 1F → B1F → B2F**, usando iluminação, Strength e Rock Smash onde aplicável. Teste retorno, pisos, escadas e se as pedras de Strength voltam ao lugar correto após salvar e recarregar.
5. Enfrente Wally em seu ponto original. Teste **derrota e repetição**, depois vitória e tentativa de confronto duplicado. Entre em Ever Grande Norte e confirme o bloqueio/liberação da Liga.
6. Salve e recarregue, volte à caverna e troque de região para confirmar que os eventos não alteram Kanto, Johto, Sinnoh ou Decades. Repita no Android/JoiPlay **separadamente**, sem supor compatibilidade a partir do PC.

### Critérios de aceite ainda pendentes

- [ ] Percurso real de Ever Grande, Victory Road 1F/B1F/B2F e Liga atravessado **no Game.exe**, sem atravessar paredes ou ficar preso.
- [ ] Todos os treinadores secundários, itens, escadas, placas, pedras, iluminação e puzzles específicos revisados; pendências de QA04 resolvidas.
- [ ] HM Waterfall, Strength e Rock Smash usados na prática, respeitando as insígnias e os Pokémon da equipe.
- [ ] Wally aparece no lugar correto, com gráfico e batalha funcionais e escalonados; derrota permite tentar novamente.
- [ ] Wally derrotado libera a saída, e a Liga exige oito insígnias; impossível pular a batalha por outro warp/entrada.
- [ ] Save/load, retorno e eventos após vitória sem softlock nem duplicação; demais regiões intactas.
- [ ] Windows **e** Android/JoiPlay aprovados com evidência real.

**Aprovação jogável ainda é 0/12.** O auditor prova que arquivos e scripts foram preparados e conferidos estaticamente, não que o jogo completo já foi jogado.

## Fase 09/12 — Elite Four e Campeão Wallace

**Preparação técnica: 9/12 (75%). Aceite jogável nativo: 0/12.** Esta fase reforça a Liga Pokémon de Hoenn já presente no piloto, utilizando **mapas originais da fonte fixada** e eventos autorais; não incorpora código, falas nem scripts originais do doador ao GitHub. A equipe real e o escalonamento de níveis continuam responsabilidade do Blue/Decades.

### Ordem obrigatória da Liga

| Ordem | Líder | MapID original | PBS autoral | Pokémon na referência |
|---|---|---:|---|---:|
| 1 | Sidney | 94 | `BLUE_HOENN_ELITE,Sidney,1094` | 5 |
| 2 | Phoebe | 95 | `BLUE_HOENN_ELITE,Phoebe,1095` | 5 |
| 3 | Glacia | 96 | `BLUE_HOENN_ELITE,Glacia,1096` | 5 |
| 4 | Drake | 97 | `BLUE_HOENN_ELITE,Drake,1097` | 5 |
| 5 | Campeão Wallace | 98 | `BLUE_HOENN_CHAMPION,Wallace,1098` | 6 |

A entrada oficial na Liga envolve Map93 e o corredor Map100; Map99 é o **Hall of Fame** (integração jogável deixada para a fase 10). **Os MapIDs são da fonte** e são remapeados para o intervalo privado da cópia Blue. O mapa de destino é conferido em cada chamada de batalha.

### Alterações realizadas

- O Ruby `BlueHoennPilot.qa9_at_league_map?` impede chamar líderes por outro mapa/fora da região.
- `qa9_elite_unlocked?(index)` exige **as oito insígnias locais de Hoenn**, a vitória contra Wally e **todas as vitórias anteriores**. Não basta existir um flag do líder imediatamente anterior: saves com flags posteriores faltando anteriores não passam.
- `qa9_champion_unlocked?` exige os **quatro** flags da Elite Four, além do progresso regional correto. O acesso aos mapas internos e ao Campeão aplica os mesmos critérios.
- As cinco batalhas continuam em `TrainerBattle.start`, com `setBattleRule("canLose")`: **perder não grava vitória**, e refalar após vencer não repete a luta. Não introduzemos níveis fixos.
- `scripts/regions/hoenn_qa_phase9.py` inspeciona **oito mapas (93–100)**, cinco eventos de chefes, a saída do Campeão e a entrada no Hall of Fame; compara os **cinco PBS completos** com a referência técnica. Confere ainda se os guardas Ruby novos foram instalados fisicamente no piloto.
- A saída do Campeão para o Hall exige vitória. **Não** marca créditos, telas nativas do Hall, pós-jogo ou liberação de regiões: essas ações pertencem à **Fase 10/12**.
- `TESTAR_HOENN.bat` executa auditorias das **fases 1–9**, cada uma com seu relatório; prepara exclusivamente `.blue-work/hoenn-qa-fase09` com save **Hoenn QA Fase09** / **Dessastre Paradoxal Hoenn QA09**, sem sobrescrever os perfis anteriores.
- `tests/test_hoenn_qa_phase9.py` cobre mapas faltantes, script/trigger incorreto, evento duplicado, times e identidade PBS ausentes/distorcidos. `tests/hoenn_qa_phase9_runtime.rb` testa isolamento, derrota e repetição, progressão de cada sala, flags adulterados, bloqueio do campeão e save/load. A CI também executa os cenários Ruby existentes de Hoenn.

### Teste de jogabilidade real pendente

1. Atualize a `main`. Mantenha o ZIP Hoenn original fixado na raiz e a base Blue instalada em `game/`. Execute `TESTAR_HOENN.bat`. Se a pasta QA09 já existir de uma execução anterior, **não a sobrescreva**: faça backup dos saves e recrie apenas uma cópia QA09 sem dados importantes.
2. Inspecione `.blue-work/hoenn-qa-fase09-report.json`: deve indicar `LEAGUE_ELITE_CHAMPION_STATICALLY_VERIFIED` e `native_game_exe_approved=false`. Os relatórios das fases anteriores também são executados em sequência.
3. No `Game.exe`, obtenha as oito insígnias, vença Wally, vá à Liga e percorra Sidney → Phoebe → Glacia → Drake → Wallace. Em cada sala, confira colisões, portas, texto, sprite correto, itens da equipe, movimentos, batalha e **escalonamento nativo de Decades**.
4. Provoque **derrota** e repita o desafio de um membro. Verifique que o próximo mapa continua fechado até a vitória real. Reentre em uma sala completada e confirme que a batalha não é reiniciada indevidamente. Teste tentativa de salto de salas e acesso prematuro a Wallace.
5. Salve e recarregue depois de cada vitória, inclusive após Drake. Confira que os flags pertencem **somente a Hoenn**, sem sobrescrever ou liberar progresso em Decades, Kanto, Johto ou Sinnoh.
6. Após vencer Wallace, confira somente **a passagem** para o Hall of Fame. A animação e os créditos do Hall, o pós-jogo, a liberação de regiões e o Android/JoiPlay **não** recebem aceite nesta fase.

### Critérios de aceite — ainda NÃO aprovados

- [ ] Cinco líderes com batalhas realmente executadas no `Game.exe` e times completos, sem níveis fixos impostos.
- [ ] Quatro salas e o campeão na ordem certa, sem saltos por portas ou eventos, com animação e itens corretos.
- [ ] Derrotas não gravam vitória; refalar após vitória não repete batalha de forma indevida.
- [ ] Sprites individuais dos quatro membros da Elite conferidos visualmente (o tipo compartilhado `BLUE_HOENN_ELITE` exige atenção específica para evitar arte repetida).
- [ ] Corredores, portas, música, colisões e entradas/saídas jogáveis; save/reload sem travamento.
- [ ] Desafios fora de Hoenn bloqueados e saves das outras regiões preservados.
- [ ] Android/JoiPlay testado independentemente do PC.

**Limite:** Python/Ruby e CI apenas confirmam contratos autorais e fluxos simulados; não executam o `Game.exe`, não verificam a renderização da Liga e não certificam a campanha jogável. Portanto o marcador **0/12 nativo** permanece.

## Fase 10/12 — Hall of Fame e pós-jogo multirregional

**Preparação técnica: 10/12 (83,3%). Aprovação jogável nativa: 0/12.** A conclusão de Hoenn agora utiliza o mesmo núcleo regional autoral que organiza Kanto, Johto e as demais regiões, **sem** modificar insígnias, switches, equipes ou a progressão do Decades.

### Registro do fim da campanha de Hoenn

1. Os eventos anteriores já garantem **oito insígnias regionais**, a vitória sobre Wally em Victory Road, e a ordem **Sidney → Phoebe → Glacia → Drake → Wallace**. A confirmação definitiva é feita **somente no evento original reautorado do Hall of Fame, Map99, (9,18)**.
2. `BlueHoennPilot.qa10_hall_ready?` exige o **mapa atual correspondente ao original 99**, todas as conquistas, o campeão derrotado, o namespace `HOENN` e o serviço `BlueRegions.complete_league` instalado.
3. `BlueHoennPilot.hall_of_fame_stage10` chama `BlueRegions.complete_league(region,"HOENN")` apenas quando o circuito ainda não contém Hoenn. O serviço central persiste uma única entrada em `$PokemonGlobal.blue_regions["leagues"]`. Só após o registro confiável a flag local `hoenn_pilot["hoenn_hall_of_fame"]` é definida. Reinterações e saves anteriores corretos não adicionam duplicatas.
4. No circuito original `Decades – Kanto – Johto – Hoenn – Sinnoh – Unova – Kalos – Alola – Galar – Paldea`, concluir **Hoenn** libera como **regiões vizinhas Johto e Sinnoh**, preservando quaisquer Ligas já conquistadas. Um jogador iniciado em Johto, após concluir Hoenn, também mantém Kanto liberada pelo triunfo anterior.
5. A ação **não** executa `BlueRegionTravel.travel`, não inventa spawn/portos/PC, não concederá uma nova insígnia nem altera as esmeraldas nativas do Decades. A disponibilidade de viagem depende de **mapas reais e chegada segura** e permanece pendente para regiões ainda não instaladas.
6. `BlueHoennPilot.qa10_postgame_status` informa o desbloqueio no Hall e no **aviso de Ever Grande Norte (Map322, 23,16)**, somente após conclusão validada e estando no mapa adequado. O resto do mapa usa seu diálogo normal antes do Hall.
7. Não são ativadas revanches Full Power, Battle Frontier ou desafio de Steven sem confirmar conclusão de todo o circuito ou eventos adicionais e referências oficiais. A lógica de Decades permanece a autoridade para o escalonamento dos times.

### Implementação técnica e isolamento

- `scripts/regions/hoenn_qa_phase10.py`: auditoria estática das âncoras RXDATA de saída do campeão **Map98 (8,4)**, evento do Hall **Map99 (9,18)** e aviso de Ever Grande **Map322 (23,16)**; confere o manifesto, os scripts Ruby autorais e a instalação **`BlueRegions`**. Bloqueia qualquer relatório que marque jogo, créditos ou viagem como verificados sem teste.
- `tests/test_hoenn_qa_phase10.py`: testes sintéticos de eventos ausentes, alterados, duplicados, gatilhos trocados e inventário do circuito.
- `tests/hoenn_qa_phase10_runtime.rb`: testes Ruby usando os **métodos reais** do núcleo `scripts/battle_polish/Regions.rb`; cobrem salvamento, oito insígnias, derrota/flags antecipados, map guard, Hoenn inicial, jornada legal Johto→Hoenn, duplicatas e isolamento do Decades.
- `tests/hoenn_stage10_runtime.rb`: regressão da antiga conclusão, agora exigindo deslocamento para **Map99** após Wallace e conferindo que `leagues` recebe Hoenn uma única vez.
- `TESTAR_HOENN.bat` passou a preparar **`.blue-work/hoenn-qa-fase10/`**, novo perfil de save **Hoenn QA Fase10 / Dessastre Paradoxal Hoenn QA10** e as dez auditorias QA01–QA10, cada qual com relatório separado. A cópia anterior QA09 e os saves de outras regiões não são sobrescritos.

### Como testar na instalação Windows

1. Atualize a `main`, mantenha a pasta original `game/` instalada e o ZIP de origem fixado. Inicie **`TESTAR_HOENN.bat`**. Nunca substitua a cópia QA10 de um teste anterior sem fazer backup de saves; o preparador requer um destino novo.
2. Confira `.blue-work/hoenn-qa-fase10-report.json`: status esperado **`HALL_OF_FAME_CIRCUIT_STATICALLY_VERIFIED`**, `native_game_exe_approved=false` e ausência de scripts do doador. O preparador também executa QA01–QA09.
3. No `Game.exe`, conclua a campanha e vença o campeão Wallace. Antes de acessar o Hall, confirme que ainda **não** foi concedida a conclusão da Liga.
4. Entre no Hall of Fame, acione o evento real e confira no menu/circuito o registro da Liga, o desbloqueio de Johto e Sinnoh e a manutenção das insígnias e missões de Hoenn. A exibição visual/cinemática e créditos **não** foram implementados nem certificados pelo script simples e exigem avaliação.
5. Reinteraja com o Hall, salve, feche e carregue novamente. Confira que existe exatamente **uma** entrada `HOENN` em `leagues`; não há nova insígnia, esmeralda, recompensa ou batalha duplicada.
6. Retorne a Ever Grande, confira a mensagem pós-jogo e navegue por qualquer saída original. **Se houver travamento de saída ou mapa inacessível, registre o MapID e não marque a fase aprovada.**
7. Teste um save iniciado em Johto que tenha liberado Hoenn legitimamente. Ao concluir Hoenn, Johto, Kanto e Sinnoh permanecem disponíveis no circuito, sem mutações nas quests de Johto. Teste Kanto, Sinnoh, Decades e Android/JoiPlay por separado.

### Limites e aceites pendentes

- [ ] Hall of Fame nativo, animação, créditos, músicas, Trainer Card e retorno pós-Liga exibidos corretamente no **Game.exe**.
- [ ] Todas as salas/portas desde Wallace até o Hall e a saída de retorno funcionam sem softlocks.
- [ ] Conclusão de Hoenn concede Johto + Sinnoh **apenas no circuito**, habilitando viagem física **somente** para destinos instalados com chegada validada.
- [ ] Nenhuma duplicação após save/load, conclusão de outra Liga ou acesso repetido ao Hall.
- [ ] Regiões externas, Decades, PC, esmeraldas, insígnias e modos de batalha intactos.
- [ ] Revanches e conteúdo pós-jogo identificados e testados no jogo; não presumir Full Power.
- [ ] Compatibilidade Windows/Android confirmada com testes nativos reais.

**A fase 10 prepara e protege a conclusão regional, mas não equivale à campanha jogável aprovada. Faltam as fases 11–12 e o aceite real no Game.exe permanece em 0/12.**

## Fase 11/12 — Português, placas, músicas e Trainer Card de Hoenn

**Preparação técnica: 11/12 (91,7%). Aprovação jogável nativa: 0/12.** A interface de Hoenn usa os sistemas já existentes no Blue/Decades, sem importar scripts de outros jogos nem reescrever os recursos de Decades.

### Textos em português

- `scripts/regions/hoenn_qa_phase11.py` possui uma tabela fechada de nomes de locais para a apresentação ao jogador. O gerador atualiza os **199 nomes de mapas** em `Data/MapInfos.rxdata` e `PBS/map_metadata_hoenn_pilot.txt` sem mudar MapIDs, scripts de eventos ou identificadores de espécies, itens e golpes.
- Termos como **Victory Road → Estrada da Vitória**, **Cave of Origin → Caverna da Origem**, **Seafloor Cavern → Caverna Submarina**, **Sky Pillar → Pilar Celeste**, **Hall of Fame → Hall da Fama**, **Elite Four → Elite Quatro**, além de `Town`/`City`, exibem rótulos em PT-BR sem modificar nomes próprios de cidades.
- As referências aos oito ginásios nos diálogos autorais `HoennPilot.rb` passaram a chamar as insígnias pelos nomes em português: **Pedra, Punho, Dínamo, Calor, Equilíbrio, Pena, Mente e Chuva**. **Os IDs regionais STONE, KNUCKLE, DYNAMO, HEAT, BALANCE, FEATHER, MIND e RAIN não mudam.**
- A auditoria confirma o handler autoral das placas. **Ela não prova que todos os NPCs e placas de todos os 199 mapas tiveram todas as falas traduzidas.** A revisão de falas não recriadas ou não cadastradas e o comportamento sob as opções de idioma ainda são tarefas manuais importantes da Fase 12.

### Músicas e áudio

- O gerador já possuía sete faixas OGG referenciadas: **Littleroot**, **Birch**, **Route101**, **Oldale**, **Center**, **Wild** e **WildVictory**. Elas são verificadas com `OggS` na cópia de teste, em vez de inventar novas músicas ou enviar assets não confirmados.
- Agora cada um dos **199 mapas** recebe explicitamente um BGM autoral da lista. Os mapas da etapa 10 — Sootopolis, Victory Road, salas da Elite e Wallace, Ever Grande e Hall of Fame — usam uma **seleção provisória** dessas faixas já presentes. O auditor marca os 61 MapIDs finais como **pendentes de trilha autêntica e audição nativa**; a música provisória não representa a trilha definitiva de Emerald/ORAS.
- O BGM de encontros selvagens e vitória usa os handlers existentes de `BlueHoennPilot::Music`, exclusivamente dentro de Hoenn. A engine original ainda controla batalha contra treinadores, eventos especiais, fades, prioridades, looping e restauração após trocas de mapa; tudo isso exige teste no Game.exe e não está certificado.

### Cartão do treinador

- `scripts/battle_polish/RegionalCards.rb` agora reconhece **Hoenn e Kanto** no ponto de abertura nativo do Trainer Card. Em Hoenn, a página 1 exibe o nome **Hoenn**, a contagem local e as oito insígnias; a página 2 mostra as esmeraldas totais do circuito sem duplicar a contagem. Os badges exibem abreviações diferentes (**PE, PU, DI, CA, EQ, PN, ME, CH**) em vez de depender de imagens não verificadas.
- Kanto mantém seu mesmo cartão regional; **Decades mantém o Trainer Card original**, sem interceptação. O conteúdo e as insígnias são leitura pura do estado regional, sem conceder marcos, atualizar a Pokédex ou alterar saves.
- A cópia de Hoenn leva o arquivo atualizado `RegionalCards.rb` no plugin de apresentação do Blue. A auditoria verifica sua presença, a lista de oito insígnias e os controles de escopo. **O layout real, tamanho da fonte e cores precisam ser conferidos visualmente no jogo** e no Android.

### Auditoria e testes

- `scripts/regions/hoenn_qa_phase11.py`: relê **199 mapas RXDATA**, `MapInfos`, PBS de nomes, sete arquivos OGG, o `RegionalCards.rb` instalado e as assinaturas dos handlers de Hoenn, comparando com o manifesto autoral `qa11` e bloqueando divergências.
- `tests/test_hoenn_qa_phase11.py`: testes sintéticos de 199 mapas, tradução de nomes, áudio ausente/inválido, volume, manifesto e proibição de aceite nativo automático.
- `tests/region_cards_runtime.rb`: regressão Ruby ampliada com 8 insígnias de Hoenn, Kanto, abertura do Trainer Card nativo e isolamento visual/funcional do cartão de Decades. A CI também faz `ruby -c` em `RegionalCards.rb`.
- `TESTAR_HOENN.bat` prepara **`.blue-work/hoenn-qa-fase11`**, usa o perfil isolado **Hoenn QA Fase11 / Dessastre Paradoxal Hoenn QA11** e executa auditorias 1–11. Os relatórios QA01–QA10 são conservados com nomes próprios e QA11 escreve **`.blue-work/hoenn-qa-fase11-report.json`**.
- Espera-se o status estático `PTBR_SIGNS_MUSIC_TRAINER_CARD_STATICALLY_VERIFIED` se os insumos originais, a compilação e os arquivos realmente conferirem. Esse status **não é aprovação do Game.exe**.

### Teste nativo obrigatório — pendente

1. Atualize a `main` e mantenha o ZIP Hoenn original fixado e a pasta `game/` da base Decades. Execute **`TESTAR_HOENN.bat`** para gerar a cópia QA11 (não sobrescrever um save anterior sem backup).
2. No `Game.exe`, selecione português, percorra **Littleroot, Oldale, Rustboro, Dewford, Mauville, Fortree, Mossdeep, Sootopolis, Victory Road e Liga**. Leia NPCs, diálogos condicionais, placas, cidades, rotas, anúncios, ginásios e as insígnias. Anote qualquer texto inglês residual ou controle de cor ilegível, sem marcar tradução completa automaticamente.
3. Abra o **Trainer Card original** em Hoenn com 0, 1, 4 e 8 insígnias. Verifique todas as abreviações e duas páginas; compare com Kanto e com o Trainer Card original do Decades. Teste retorno ao menu e save/load.
4. Ouça música de início, cidades, rotas, Centros Pokémon, cavernas, Victory Road, Elite, Wallace e Hall, verificando ausência de silêncio/cortes, prioridade em batalha, vitória, volume, loops e retorno da música após portas e viagem regional.
5. Repita em Android/JoiPlay. A resolução e renderização de textos/insígnias, BGM e controles de áudio podem diferir do Windows.
6. Marque como pendente na Fase 12 tudo que exigir assets musicais originais, falas adicionais, sprites autênticos de insígnias, revisões de UI e testes de toda a campanha.

**QA11 pronta para execução técnica, não para aceitação nativa. A Fase 12 é a verificação integral de campanha Windows/Android.**

## Fase 12/12 — Auditoria integrada da campanha Hoenn (Windows + Android/JoiPlay)

**Preparação técnica de ferramentas: 12/12 (100%). Fases jogáveis nativamente aceitas: 0/12 (0%).** Essas métricas **não** devem ser confundidas. Publicar ferramentas e executar testes unitários não comprova que a campanha inteira abre, compila e termina sem bugs no `Game.exe`.

### 1. Portão técnico integrado QA01–QA12

- `scripts/regions/hoenn_qa_phase12.py` é a última validação. Ela exige **11 relatórios QA01–11 no mesmo perfil QA12**, sem nenhum status `BLOCKED`, erro ou alegação de aprovação nativa. O script não aceita um relatório ausente ou de outra região.
- O verificador confirma cópia privada com **199 MapIDs da fonte fixada**, `Game.exe` idêntico à base Blue instalada, perfil de save único **Hoenn QA Fase12** e arquivos de RXDATA/PBS/Trainer Card/HoennPilot. Gera impressões digitais SHA-256 de `MapInfos`, PBS, plugin, cartão e manifesto.
- Os contratos de QA07 conferem **8 ginásios**, QA09 confere 4 equipes da Elite + Wallace (5,5,5,5,6 Pokémon de referência), QA10 confere desbloqueio **Johto + Sinnoh**, e QA11 exige 199 rótulos de mapas em português e 199 atribuições de músicas provisórias. Os níveis de batalha reais continuam responsabilidade de Decades.
- A auditoria mantém visíveis as contagens de **NPCs/treinadores/placas originais ainda não implementados**, **obstáculos com necessidade de revisão** e **sprites provisórios em mapas finais**; esses itens constam no registro `known_blockers` e não são aprovados nem preenchidos artificialmente.
- `tests/test_hoenn_qa_phase12.py` rejeita relatórios ausentes, resultados anteriores bloqueados, perfil errado, mapa duplicado/desconhecido, perda do inventário de pendências e falsos indicadores de aceite. A CI roda testes unitários e sintaxe Python separadamente.
- O status de sucesso **`STATIC_QA_01_12_PASSED__NATIVE_ACCEPTANCE_PENDING`** certifica somente a verificação estática dos dados presentes na instalação privada **após execução local**. **Não** certifica jogabilidade.

### 2. Preparação segura de teste

1. Atualize a `main` no computador. Confirme `game/Game.exe` com o Blue instalado e o ZIP exato **`The Pokémon World Project - Hoenn.zip`**. A auditoria não substitui esses insumos por mapas de outro pack.
2. Com o jogo original fechado, execute **`TESTAR_HOENN.bat`**. A cópia será criada em `.blue-work/hoenn-qa-fase12/`, separada de `game/` e dos perfis QA04–QA11. O script deve falhar de forma explícita se faltar uma fonte ou houver conflito. **Nunca substitua a pasta de um teste anterior sem copiar os saves importantes.**
3. Verifique os relatórios `.blue-work/hoenn-qa-fase12-prep-report.json` até `.blue-work/hoenn-qa-fase12-interface-report.json`, e por fim **`.blue-work/hoenn-qa-fase12-report.json`**.
4. Depois do portão estático, o BAT abre a cópia do `Game.exe`. Se a primeira inicialização provocar compilação e fechamento, execute o launcher novamente e confira os logs antes de prosseguir. Não use o save principal do Decades para esses testes.
5. O script cria, **sem sobrescrever ao executar novamente**, `.blue-work/hoenn-qa-fase12-playtest.json`, com **30 casos reais pendentes:** 15 para Windows Game.exe e 15 para Android/JoiPlay. O preenchimento manual não altera `native_approved` nem cria aceite automático.

### 3. Caminho de teste completo do início até a Liga

| Bloco de jogo | Referências de teste no jogo | Critério jogável |
|---|---|---|
| Início | Littleroot → Birch → Rotas 101–103 → Oldale | 3 Poké Bolas, escolha, rival, Pokédex, diálogos em PT-BR e saves |
| Primeiros ginásios | Petalburg → Rustboro/Roxanne → Dewford/Brawly | Cut/Flash, itens, treinadores, insígnias locais e batalhas |
| Meio da região | Slateport → Mauville/Wattson → Lavaridge/Flannery → Norman | Aqua/Magma, bicicletas, Rock Smash, Strength, Surf e gates |
| Reta leste | Fortree/Winona → Lilycove → Mt. Pyre → Mossdeep/Tate & Liza | Surf/Fly, sprites, clima, encontros e avanço da história |
| Clímax | Esconderijos Aqua/Magma → Seafloor → Sootopolis → Sky Pillar | Dive, Rayquaza, animações, Waterfall, Juan e oito insígnias |
| Liga | Ever Grande → Victory Road/Wally → Sidney → Phoebe → Glacia → Drake → Wallace | Portas sem softlock, derrota sem flag, escala real e cinco chefes |
| Pós-jogo | Hall da Fama → circuito Hoenn/Johto/Sinnoh | Registro único, créditos, cartão, save/reload e sem viagem para mapa sem instalação |

A caminhada deve incluir **NPCs novos/antigos, placas, itens no chão, encontros selvagens, rochas e puzzles**, não apenas acessar os destinos via teleportes administrativos. Qualquer mapa sem passagem real ou evento impedindo progresso mantém o bloco sem aceite.

### 4. Testes de regressão obrigatórios

**No Windows:** realize uma nova partida na cópia QA12 e capture evidências de todos os principais bloqueios, lutas, artes dos treinadores, texto, música/loop, controles, batalha selvagem, cartões, jogo salvo e carregado. Valide o retorno ao Hall e a mensagem pós-jogo; os créditos e o Hall animado ainda não possuem prova nativa. Não libere viagem física para outra região sem pontos de chegada reais.

**No Android/JoiPlay:** execute teste independente do início ao Hall, com eventos de mato/batalha, tela de toque, teclas, som, performance, menu, Trainer Card, tilesets e saves. A aprovação do Windows não transfere automaticamente para o Android. Arquivos de instalação e configurações de JoiPlay precisam ser conferidos no dispositivo.

**Regressão multirregional:** reabra e teste Decades, Kanto, Johto e Sinnoh sem migrar nem sobrescrever seus saves. Confirme que a progressão de Hoenn, insígnias, TMs, PC e `complete_league` não destravam conquistas indevidas, não reiniciam história anterior e não alteram os sprites, áudio e cartões das outras regiões.

### 5. Pendências para aprovação real

- [ ] **Compilação e jogo real:** executar `Game.exe` e concluir a aventura do início ao Hall, com saves de vários pontos.
- [ ] **Cobertura de mundo:** revisar **todos os candidatos NPC/treinador/placa não implementados** e obstáculos pendentes apontados pelo relatório. O inventário é verificável, mas não equivale à implementação.
- [ ] **Gates e puzzles:** confirmar passabilidade, HM, puzzles de ginásio, Seafloor e Victory Road em todos os cenários legítimos.
- [ ] **Diálogos e textos:** corrigir qualquer fala em inglês restante, texto ilegível, placa sem tradução, cores/contornos ruins e nomes de mapa incorretos.
- [ ] **Áudio:** substituir/faixar adequadamente trilhas de chefes/Liga/cenas onde ainda há OGG provisório; conferir música real, fade e loop.
- [ ] **Gráficos e UI:** validar sprites de líderes/Elite, telas, oito ícones de insígnias, cartões e Hall da Fama em tela real.
- [ ] **Saves e compatibilidade:** derrotas, vitórias e recompensas sem duplicação; PC, itens, esmeraldas, box de Pokémon e saves de outras regiões intactos.
- [ ] **Windows e Android separados:** checklist `playtest.json` com evidências reproduzíveis por plataforma, **sem conclusão automática**.

**Conclusão da etapa:** todas as **12/12 ferramentas de preparação/auditoria estão no repositório**, mas não foi executado aqui um jogo completo com os insumos privados de Hoenn. Portanto **aceite nativo: 0/12**, até que testes reais em Windows e Android comprovem o contrário. É normal e correto permanecer com pendências abertas após a etapa técnica final.


## Ferramenta extra — Testar Hoenn · Teleporte para qualquer mapa

Esta ferramenta é **exclusiva do piloto Hoenn** preparado pelo `TESTAR_HOENN.bat`. Não é instalada no Blue/Decades principal, em Kanto, Johto ou Sinnoh.

### Acesso no jogo

1. Atualize a `main`, feche qualquer `Game.exe` da cópia QA12 que esteja aberto e execute **`TESTAR_HOENN.bat`**.
2. O BAT prepara `.blue-work/hoenn-qa-fase12/` e roda as auditorias de RXDATA/PBS. Se a cópia QA12 já existir, o preparador atualiza **somente o plugin do piloto, o catálogo de destinos e o manifesto QA12**, após conferir os 199 mapas e o `Game.exe` contra a instalação Blue. O original `game/`, outros pilotos e os saves não são alterados. Arquivos anteriores modificados são copiados para `.blue-work/hoenn-qa12-debug-backups/`.
3. No piloto, **escolha seu Pokémon inicial** e abra o menu de pausa. Entre em **Testar Hoenn · Teleporte**.
4. Use **Lista completa (199 mapas)**, **Escolher faixa de MapIDs**, **Pesquisar nome do mapa** (quando disponível no dispositivo) ou **Digitar MapID (original/Blue)**. A lista é paginada; cada destino mostra seu número **original** e nome em português. Digitar o ID real remapeado também localiza o destino, sem aceitar mapas externos.
5. Confirme o destino. Uma coordenada calculada da **geometria RXDATA original** é escolhida para não pousar em NPCs, portas, itens ou obstáculos; o catálogo verifica o ID remapeado e o arquivo físico. A opção **Voltar ao mapa anterior** restaura o último local da sessão, sem editar o save.
6. Examine NPCs, placas, itens, ginásios, transições, encontros e eventos e anote o **MapID original** no relatório. **O teleporte ultrapassa gates narrativos para permitir inspeção, mas não concede insígnias, não conclui batalhas, não modifica missões e não habilita viagens regionais oficiais.** Batalhas e gatilhos podem permanecer bloqueados até a progressão legítima.

**Segurança e limitações:** menus de teleporte ficam ocultos fora da região Hoenn e em batalha. O uso é limitado aos 199 mapas remapeados do piloto, não aos mapas de Decades nem a IDs arbitrários. Uma coordenada de terreno caminhável validada estaticamente **não** comprova movimento nativo, colisão de NPC ou retorno após eventos; salve apenas no **perfil de testes**. O último ponto de retorno existe somente enquanto a sessão estiver aberta.

### Código, regressão e aceite

- `scripts/regions/pilot_hoenn.py`: gera `Data/blue-hoenn-test-stops.txt` com **199 destinos reais**, após inserir NPCs, eventos, itens e obstáculos, com coordenadas derivadas dos tilesets. Inclui hash e inventário no manifesto.
- `scripts/regions/HoennPilot.rb`: menu in-game, busca, entrada de MapID original/remapeado, páginas e retorno. Utiliza a transferência existente `BlueRegionTravel.move_to` e nunca altera o estado regional.
- `scripts/regions/hoenn_qa_teleport_upgrade.py`: atualiza ferramentas de teste em cópias QA12 já preparadas, com backups e rollback, sem criar mapas fictícios ou exigir repetição da extração do ZIP.
- `scripts/regions/hoenn_qa_phase12.py`: valida o hash do catálogo, os **199 MapIDs**, posições dentro de cada mapa, terreno passável, ausência de eventos na célula de chegada e presença do menu Ruby na cópia.
- `tests/hoenn_qa_teleport_runtime.rb` e `tests/test_hoenn_qa_teleport.py`: testes simulados do menu, proteção regional, retorno, buscas e geometria. São simuladores, **não Game.exe**.

**Não altera:** a barra técnica continua 12/12 e a barra de aprovação nativa permanece 0/12 até o teste real em Windows e Android/JoiPlay.
