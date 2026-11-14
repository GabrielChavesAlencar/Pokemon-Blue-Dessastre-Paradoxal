# Hoenn — barra de progresso jogável (12 fases)

**Atualizado:** 14/11/2026. Referência de dados: [hoenn-qa-progresso.json](../data/regions/hoenn-qa-progresso.json). Etapa técnica anterior: [10/10](HOENN_ETAPA_10_SOOTOPOLIS_RAYQUAZA_LIGA.md).

**Acompanhe as DUAS barras separadamente:**

- **Etapas de código existentes:** 10/10 — ██████████ (concluídas e publicadas, sem certificar Game.exe).
- **Fases jogáveis 1–12:** preparação das fases 1 a 5 implementada; execução/aceite pendentes — ▣▣▣▣▣□□□□□□□ (▣ = ferramenta pronta; NÃO = jogável).
- **Fases nativamente aprovadas:** 0/12 — □□□□□□□□□□□□ (sem testes reais completos).

| # | Etapa | Preparação | Aceite Game.exe |
|---:|---|---|---|
| 1 | Gerar cópia isolada com 199 mapas e PBS | **Ferramenta preparada, execução local pendente** | ⏳ |
| 2 | Corrigir conexões e colisões dos mapas | **Auditoria de RXDATA/PBS implementada; execução local pendente** | ⏳ |
| 3 | Conferir encontros, NPCs, treinadores e itens | **Perfis-base, itens simples e catálogo de pendências implementados; QA nativo pendente** | ⏳ |
| 4 | Surf, Dive, Waterfall, Strength e puzzles | **HM e gate regional + rochas simples + auditoria fonte; puzzles nativos pendentes** | ⏳ |
| 5 | Equipes Aqua/Magma, Seafloor Cavern | **Gates de história e auditoria de eventos implementados; teste real pendente** | ⏳ |
| 6 | Cave of Origin, clima, Rayquaza | Pendente | ⏳ |
| 7 | Oito ginásios e insígnias locais | Pendente | ⏳ |
| 8 | Victory Road e Wally | Pendente | ⏳ |
| 9 | Elite Four e Wallace | Pendente | ⏳ |
| 10 | Hall of Fame e pós-jogo | Pendente | ⏳ |
| 11 | Traduções, placas, áudio e Trainer Card | Pendente | ⏳ |
| 12 | QA da campanha inteira Windows/Android | Pendente | ⏳ |

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
- `scripts/regions/inspect_hoenn_qa5_public.py` consulta **oito mapas RXDATA** da revisão imutável Hoenn, valida SHA-1 Git com `data/regions/hoenn-source.json` e produz apenas metadados dos eventos. Nenhum script, fala ou binário do doador é publicado.
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
