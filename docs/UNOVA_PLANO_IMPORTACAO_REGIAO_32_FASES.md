# UNOVA — integração ao Dessastre Paradoxal: plano passo a passo (U01–U32)

> **Data:** 17/11/2026 · **Jogo-base narrativo:** Pokémon White / Black & White (Nintendo DS) · **Destino:** Pokémon Decades + Pokémon Essentials v21.1 / RPG Maker XP.
>
> **ESTADO REAL: PLANNED / NÃO INSTALADA / NÃO JOGÁVEL.** Este documento não importa mapas, não instala scripts, não mexe em saves, não prova funcionamento no Game.exe e não autoriza anunciar Android/JoiPlay como funcional. A auditoria de um ZIP de terceiros continua pendente.

## 0. Objetivo e princípio

Integrar a região completa de Unova ao MESMO Game.exe e sistema de saves do Pokémon Blue: Dessastre Paradoxal, com mapas, NPCs, eventos, treinadores, Pokémon selvagens, oito ginásios, Elite Four, N, Ghetsis, pós-jogo e músicas autorizadas. Usar a estrutura de Black/White e a variante White como campanha inicial. Black City/Drayden e Black 2/White 2 ficam como variantes e expansão futuras, separadas da cronologia original.

**Primeiro candidato de arquivos editáveis:** Pokémon World V18, que inclui apenas parte de Unova e precisa ser inventariado; a publicação do autor permite uso de partes do projeto, mas não garante direitos sobre todas as músicas e artes. Pokémon Fire Ash v3.7.1 é referência de uma Unova jogável, não fonte automaticamente autorizada de assets. O Pokémon World Project em Essentials v21.1 informa Unova 0%. Ler [pesquisa de fontes](UNOVA_PESQUISA_FONTES_RMXP.md).

**Princípio herdado de Kanto/Johto/Hoenn/Sinnoh:** AUDITAR → ISOLAR → REMAPEAR → PORTAR → TESTAR → INTEGRAR → VALIDAR NO GAME.EXE → VALIDAR NO ANDROID. Dados sintetizados para teste não substituem um mapa real; portal e documentação não aumentam a barra de jogabilidade.

## 1. Documentação e fontes de entrada

- [Pesquisa atualizada de projetos de Unova para RPG Maker XP](UNOVA_PESQUISA_FONTES_RMXP.md).
- [Detonado Pokémon Black/White](https://www.pokemythology.net/detonados/detonado-black-white/) para definir história e etapas; não copiar longos diálogos ou o artigo integral.
- Arquivo anterior fornecido nesta conversa: **UNOVA_PLANO_MESTRE_DETONADO_BLACK_WHITE_DESSASTRE_PARADOXAL.md**, com roteiro de história, áreas, líderes e pós-jogo. Ainda não pressupor publicação dele no repositório.
- [Seleção regional](NOVO_JOGO_SELECAO_REGIONAL.md) — Unova ainda indisponível no Novo Jogo.
- [Viagens por NPC e itens regionais](VIAGEM_REGIONAL_LIVRE_NPC.md) — viagem livre desde o início apenas entre regiões realmente integradas, exclusivamente pelo Agente Regional da cidade inicial.
- [Auditoria de reservas e MapInfos](SINNOH_R07_DIAGNOSTICO_RESERVAS.md) — inspecionar Kanto/Johto/Hoenn/Sinnoh e a base instalada antes de reservar IDs para Unova.
- [Integração Kanto](KANTO_INTEGRACAO_DECADES.md), [Editor de músicas](EDITOR_MUSICAS.md) e [regras de evolução/progresso](PROGRESSAO_E_ANIMACOES.md).

## 2. Regras inegociáveis de compatibilidade

1. **Nada de substituir o Decades:** importar somente recursos necessários, namespaced por UNOVA, com backups e rollback; não transplantar todos os scripts v18/v19 para Essentials v21.1.
2. **MapIDs reais:** ler MapInfos.rxdata da instalação principal e identificar IDs ocupados e reservas legítimas de todas as regiões. Nunca escolher números hipotéticos nem sobrescrever mapas existentes.
3. **Novo Jogo:** só habilitar Unova depois de provar que o conteúdo está integrado ao Game.exe principal, compilado e que o quarto em Nuvema funciona. Um piloto isolado não conta.
4. **Agente Regional:** NPC em Nuvema Town em posição passável realmente observada. Viagem para outras regiões integradas mediante conversa, sem teleportar pelo menu. Ao chegar, não executar a escolha de personagem do Decades.
5. **Itens regionais:** HMs e itens-chave de Unova ficam restritos a Unova, inclusive os guardados no PC de itens; reaparecem ao retornar. Pokémon, Boxes, dinheiro, TMs/TRs e itens comuns permanecem compartilhados, seguindo as regras atuais.
6. **Insígnias e esmeraldas:** cada uma das oito insígnias conta uma única vez, e toda verificação de HM e Pokémon especial é local; a trava de especiais até oito insígnias continua ativa.
7. **Centro Pokémon:** ao perder a batalha em Unova, reviver no último Centro válido da região atual; usar o Centro da cidade inicial local como fallback, nunca o de outra região.
8. **Progressão dinâmica:** preservar level cap, escalonamento de treinadores e evolução dinâmica de selvagens/trainer Pokémon, XP compartilhada e modos de dificuldade; manter equipes clássicas como dado de referência.
9. **Mecânicas especiais:** Mega, Z-Moves e Terastal obedecem às regras já configuradas no Blue; Dynamax respeita a opção global/regional, sem inventar canonização no roteiro B/W.
10. **PT-BR e evidência:** todos os NPCs, placas, ginásios, mapas e itens adicionados precisam de localização e testes reais; nenhuma área fica “concluída” apenas pelo nome no site.
11. **Músicas:** só copiar áudio com direitos de uso e redistribuição claramente comprovados; OST comercial e material de terceiros não são automaticamente livres. Usar BlueMusic e fallbacks autorizados.
12. **Android/JoiPlay:** exigir teste próprio com updater incremental, saves e controles, separadamente de Windows. O CI não substitui nenhuma das duas execuções reais.

## 3. Preparação técnica e rastreabilidade

### 3.1 Diretórios futuros sugeridos

- **.blue-work/unova/sources/** — ZIP e créditos baixados da fonte do autor, fora do Git e fora do game principal.
- **.blue-work/unova/audit/** — inventários, hashes, relatórios e mapas de dependência.
- **.blue-work/unova/qa-game-IDENTIFICADOR/** — instalação privada isolada para conversão e teste real.
- **scripts/regions/unova/** — auditores de RXDATA, verificadores de fontes, planos de remap, instalador com rollback e testes.
- **docs/unova/** — catálogos auditados de mapas, NPCs, história, músicas, treinadores e encontros.
- **site/** — páginas de Unova em modo planejado/pendente ou jogável conforme evidência, sem MapIDs fictícios.

Essa árvore é proposta, não é alegação de que seus arquivos já existem.

### 3.2 Manifestos obrigatórios

| Manifesto / relatório | Campos mínimos e objetivo |
|---|---|
| source-manifest | URL, autor, projeto, licença/consentimento, tamanho, SHA-256, data da aquisição, permissões por recurso |
| map-inventory | MapID original, nome, dimensão, tileset, eventos, portas, conexão, BGM, dependências, SHA-256 |
| rights-matrix | autor de cada recurso, terceiro envolvido, créditos, autorização, distribuição permitida, blocked |
| remap-plan | MapID antigo → MapID novo atribuído com baseline real, referências recalculadas, conflitos |
| event-catalog | event_key, condições, flags, gatilho, diálogos PT-BR, recompensas, reentrada, não duplicação |
| trainers-encounters | área, treinador, times originais auditados, escalonamento, métodos e horários/estações reais |
| music-catalog | chave BlueMusic, prioridade, fallback, proprietário, formato, licença, testes por plataforma |
| install-report | versão, arquivos before/after, hashes, backup, compilação PBS, teste e rollback |
| playtest-report | plataforma, versão do jogo, save isolado, roteiro, captura/log, bugs e resultado real |

### 3.3 Processo de importação de cada mapa

1. Descompactar fonte em área isolada, sem executar arquivos executáveis ou scripts desconhecidos.
2. Ler MapInfos, MapNNN.rxdata, Tilesets.rxdata, scripts de eventos e recursos gráficos somente para inventário; calcular hashes.
3. Identificar área canônica de Unova, época da campanha, original-map-id e todas as dependências.
4. Verificar que o conteúdo e cada asset têm origem/autorização apropriadas; caso contrário marcar blocked e reconstruir com recursos próprios/licenciados.
5. Ler MapInfos REAL da instalação Decades (com Kanto/Johto/Hoenn/Sinnoh já considerados).
6. Alocar IDs disponíveis por plano documentado, nunca editar/reescrever um ID ocupado; reescrever transferências e referências vinculadas.
7. Portar para cópia QA privada: tilesets, passabilidade, autotiles, prioridades, portais, metadados e eventos **compatibilizados com Essentials 21.1**.
8. Resolver NPCs/placas, sons, itens, trainers, encounters e flags Unova; aplicar localização PT-BR e balanceamento Blue.
9. Compilar os dados realmente no Game.exe QA e fazer travessia, batalha, save/reload, blackout, retorno e testes negativos.
10. Aprovar, registrar evidência e só então permitir que a área componha o overlay para futura integração principal.

Se o ZIP Pokémon World não tiver a área, classificá-la como **MISSING** e criar mapa próprio; não chamar tal área “importada”.

## 4. Fases U01–U32 — sequência de execução

| Fase | Entrega | Critério verificável |
|---|---|---|
| **U01** | Pesquisa das fontes e autorizações | Links primários, direitos e limites documentados; nenhuma permissão presumida |
| **U02** | Inventário do ZIP de Pokémon World V18 | Hashes reais, lista de mapas/NPcs/eventos/músicas, créditos e lacunas |
| **U03** | Matriz completa de cidades, rotas e áreas | Cada área B/W confrontada com um mapa fonte real ou MISSING |
| **U04** | Diagnóstico MapInfos e reservas multirregionais | Baseline da instalação real, IDs sem colisão, riscos e plano de remap |
| **U05** | Conversor de mapas v18→v21.1 em QA isolada | Um mapa real abre e navega com collision, tileset e portas testados |
| **U06** | Estado regional Unova, save e flags | Saves antigos intactos, flags idempotentes, teste de rollback |
| **U07** | Nuvema, Route 1 e Accumula | Juniper, Snivy/Tepig/Oshawott, Cheren/Bianca, N e início funcional |
| **U08** | Route 2, Striaton e Dreamyard | Running Shoes, líder variável, insígnia 1, Cut local, Munna |
| **U09** | Route 3 e Wellspring Cave | Evento com Cheren/Plasma, grama dupla, Day Care, treinador e itens |
| **U10** | Nacrene e Pinwheel Forest | Museu, Lenora, insígnia 2, roubo e recuperação do fóssil |
| **U11** | Skyarrow Bridge e Castelia | Ponte, ruas/interiores, NPCs, Team Plasma e portos |
| **U12** | Burgh, Route 4 | Terceira insígnia, deserto e progressão |
| **U13** | Desert Resort, Relic Castle I | Fósseis, areia, transições, itens e puzzles sem softlock |
| **U14** | Nimbasa, Route 16 e Lostlorn | Bianca/N, Musical, esportes, bicicleta e eventos opcionais |
| **U15** | Elesa, Route 5 e ponte | Quarta insígnia, puzzle, Alder e Driftveil Drawbridge |
| **U16** | Driftveil, Cold Storage e Clay | Eventos Plasma e quinta insígnia, portões e encontros |
| **U17** | Route 6 e Chargestone Cave | Cristais, N, Juniper, itens e saídas seguras |
| **U18** | Mistralton, Route 7 e Celestial Tower | Skyla, sino, rival, torre, aeroporto |
| **U19** | Ginásio Skyla, Surf e revisitas | Sexta insígnia, HM local e revisitas sem duplicação |
| **U20** | Mistralton Cave, Routes 17–18 | Cobalion, Larvesta, Waterfall regional e navegação marinha |
| **U21** | Twist Mountain e Icirrus | Estações/neve alteram rotas de forma testável |
| **U22** | Brycen e Dragonspiral Tower | Sétima insígnia, Plasma, dragão, condições de história |
| **U23** | Relic Castle II, pedra e Tubeline | Pedra da versão White, cenas com Cheren/Bianca/Ghetsis |
| **U24** | Opelucid e Iris | Oitava insígnia, ginásio dragão e liberação da Liga |
| **U25** | Route 10 e Victory Road | Rivais, portões de insígnias, caverna e Pokémon League |
| **U26** | Elite Four inicial | Quatro salas em ordem livre e salvamento correto |
| **U27** | N's Castle, Zekrom, N, Ghetsis | Clímax, lendário único, derrotas/reentrada, créditos |
| **U28** | Pós-jogo Looker e seis sábios | Flags independentes, recompensas únicas, revisitas |
| **U29** | Routes 11–15, White Forest, Undella, Giant Chasm | Áreas orientais, encontros, itens, ligações e variantes |
| **U30** | Lendários e atividades paralelas | Kyurem, Volcarona, trio de forças, Abyssal Ruins, Subway, Royal Unova |
| **U31** | Revanche Elite/Alder, tradução, música e site | NPCs/placas e guias completos, áudio legal, pendências explícitas |
| **U32** | Blue-Story e integração no Game.exe + JoiPlay | Instalação idempotente, Windows real, viagens, saves, Android incremental |

### Bloco A — U01–U06: fonte, conversão e state

- **U01:** a pesquisa identifica candidatos, não comprova licenciamento de todos os assets. Coletar permissão e créditos por material.
- **U02:** obter o ZIP pela publicação original do autor; auditar Data/MapInfos e MapNNN, gráficos, sons e PBS. Resolver divergência de quantidade de Unova (autor mencionou metade, mas também um quarto em comentário).
- **U03:** confrontar o inventário com o detonado B/W, incluindo cidades, pontes, interiores, cavernas, ginásios, rotas, pontes, ilhas e pós-jogo. Definir quais mapas precisam ser criados.
- **U04:** auditar IDs reais de Decades/Kanto/Johto/Hoenn/Sinnoh, inclusive reservas e espaços bloqueados; criar diagnóstico read-only e abortar ao detectar MapInfos ausente/corrompido.
- **U05:** escolher um mapa existente e permitido, converter em QA e testar em Game.exe privado. Se o mapa não compilar, não prosseguir.
- **U06:** criar flags versionadas e persistência regional. Testar reentrada, save/reload, novos e antigos saves, insígnias ganhas uma vez e rollback.

### Bloco B — U07–U13: início e três primeiras insígnias

- **U07:** quarto de Nuvema com escala de protagonista compatível, escolha entre Snivy/Tepig/Oshawott, batalhas com Cheren e Bianca, Juniper e Pokedex; introduzir Team Plasma em Accumula e N. O evento de início não deve reabrir na viagem regional.
- **U08:** Route 2, Striaton Gym com líder escolhido segundo inicial e Dreamyard com Munna/Cut; primeiro badge restrito a Unova.
- **U09:** evitar softlock na caverna do resgate Pokémon; incorporar encontros por grama escura/duplas conforme catálogo.
- **U10:** museu, N, Lenora e resgate do fóssil; preservar itens/recompensas únicas.
- **U11–U13:** reconstruir Castelia, Skyarrow, Route 4, Desert Resort e Relic Castle, incluindo portais, NPCs, itens e areia movediça, mesmo que a fonte tenha só parte dos mapas. Confirmar confrontos Plasma, travas e saída.

### Bloco C — U14–U20: Nimbasa a revisitas aquáticas

- **U14–U15:** Nimbasa/eles a, Musical e lutas na cidade, ginásio da Elesa, Alder, rota 5 e ponte; marcar opcionais distintamente de travas da história.
- **U16:** Driftveil e Cold Storage antes de Clay, com time base auditado e escalonamento Blue.
- **U17:** Chargestone Cave deve usar eventos portáveis, sem chamar APIs obsoletas do Essentials v18. Eventos de N e cristais não podem travar a saída.
- **U18–U19:** Celestial Tower, o sino, Skyla e insígnia 6; acesso a Surf somente com HM da região/insígnias aplicáveis. Fly também é regional.
- **U20:** Routes 17–18, Mistralton Cave e lendários opcionais não devem desbloquear história principal por erro de flags.

### Bloco D — U21–U27: neve, oito ginásios e clímax

- **U21:** quatro estações de Unova: persistir estado e testar mudança de caminho da Twist Mountain; Android precisa ter fallback sem congelamento de render.
- **U22:** Brycen, insígnia 7 e Dragonspiral Tower; Team Plasma/N conforme narrativa White.
- **U23–U24:** pedra e dragão corretos para White, tubeline bridge, Opelucid com Iris (não misturar com Drayden como líder Black), Master Ball e insígnia 8.
- **U25–U26:** checkpoints e rival na Route 10; Victory Road, portões por insígnia e Elite Four em qualquer ordem.
- **U27:** N's Castle, batalha de Zekrom, N e Ghetsis. Lendário não duplica; perder/voltar/salvar no castelo não quebra a narrativa; créditos concluídos definem pós-jogo.

### Bloco E — U28–U31: pós-jogo e conteúdo completo

- **U28:** Looker e os seis sábios restantes, revisitas opcionais e itens únicos.
- **U29:** rotas orientais, White Forest e vilas, inclusive Giant Chasm/Undella; não usar Black City da variante errada.
- **U30:** Kyurem, trio de mosqueteiros, forças da natureza/Landorus, Volcarona, Abyssal Ruins, Battle Subway, Royal Unova; cada missão tem pré-requisitos e save persistente.
- **U31:** revanche de Elite Four e Alder, treinador/encounter/item catalogados por local, todos os NPCs e placas em PT-BR, site de Unova com status honestos, playlist BlueMusic com origem autorizada ou fallback.

### Bloco F — U32: integração no principal

- **Preflight:** source verificada, direitos, hashes, backups, MapInfos real, remap sem colisão, todos os arquivos existentes.
- **Overlay:** aplicar mapas, gráficos autorizados, eventos e PBS sem substituir script central do Decades; compilar pela engine real.
- **Menu:** habilitar Unova somente com spawn real e testes; Agente Regional de Nuvema e destinos integrados com coordenadas auditadas.
- **Windows:** teste completo da campanha, save/reload, derrota, viagens, três iniciais, todos os ginásios, elite, N, pós-jogo e regressão Decades/Kanto/Johto/Hoenn/Sinnoh.
- **Blue-Story:** pacote incremental que baixa apenas conteúdo autorizado e verificável, instala automaticamente quando há evidência e faz rollback em falha, sem necessidade de comandos manuais pelo jogador.
- **Android:** atualização incremental apropriada ao JoiPlay, testes de Game.exe/plugin, gráficos e sons, controles, nomes de arquivo, saves, charset, eventos e visita regional; não igualar “ZIP gerado” a “Android aprovado”.

## 5. Conteúdos técnicos por área

| Tipo | Dados a registrar e validar |
|---|---|
| Mapa | area_key, source, original MapID real, destination MapID real, tamanho, tileset, colisão, conectividade e metadata |
| NPC | sprite com direitos, local, páginas de evento, fala PT-BR, flags e recarregamento |
| História | trigger, preconditions, changes, after_event, reentrada, recompensas, softlock e defeat state |
| Treinador | trainer_key, espécie, nível base documentado, modo dinâmico, rematch, itens, recompensa e flag |
| Selvagens | área, método, slot, estação, hora, versão, nível/probabilidade realmente verificados; ausências = pendente |
| Item | localização, obtenção única, HM regional, gate de insígnia e diálogo |
| Música | map/battle/ME, chave, prioridade, fallback, licença/origem, formato e plataformas |
| Portal | estado da área (planned/QA/jogável), guia, treinador, encontro, itens, links e data da auditoria |

**Importante:** referências do detonado não contêm todos os NPCs/slots e não permitem inventar probabilidades; cruzar com fontes específicas de dados por área antes de preencher os PBS.

## 6. Testes positivos mínimos

- **Estrutura:** RXDATA válido, MapInfos real, ids únicos, nenhuma transferência quebrada, recursos de tileset/characters presentes, áudio com fallback, direitos claros, PBS compilável e scripts Ruby compatíveis.
- **Jogo:** todas entradas/saídas, NPCs, sinais, itens no chão, encontros por método/estação, trainers e puzzles, além de save/load e blackout.
- **Região:** iniciar em Unova; viajar por NPC para Decades/Kanto e voltar; HMs e key items isolados inclusive no PC; Boxes/TMs compartilhados; esmeraldas únicas e trava de especiais.
- **História:** 8 ginásios em ordem, Elite sem ordem fixa, Zekrom/N/Ghetsis, créditos e pós-jogo; variante White e cenas de rivais corretas.
- **Android:** update incremental, inicialização JoiPlay, novos/antigos saves, colisão, áudio e botões, interação com scripts de eventos.
- **Regressão:** nenhuma alteração sem explicação nas regiões já integradas, nem nos instaladores de pilotos.

## 7. Testes negativos obrigatórios

- Fonte ZIP ausente, URL inválida ou SHA-256 errado → abortar sem modificar game/.
- Credits/licença de sprite/mapa/música não conferidos → não republicar o arquivo; preferir asset próprio.
- MapInfos ausente ou divergente, ID duplicado com K/J/H/S/Decades, portal para mapa inexistente → bloquear.
- Event source v18 chamando função removida no v21.1 → falhar QA, jamais copiar script sem portar.
- Menu permitindo Unova sem mapa e spawn instalados, ou agente oferecendo destino que não existe → bloquear.
- NPC e placa ainda em inglês ou recompensas duplicadas por save/reentrada → marcar incompleto.
- HP = 0 / blackout voltar à cidade de outra região → falhar.
- HM/Poké Flauta de uma região funcionar em Unova sem possuir sua variante local → falhar.
- Seleção de personagem reaparecer após viagem desde Nuvema → falhar.
- N/Ghetsis ou lendário repetidos, Softlock no Castle/Victory Road/Twist Mountain → falhar.
- Música oficial/não licenciada enviada no instalador público → bloquear essa distribuição, manter fallback.
- Atualizador Android instalar parcialmente e corromper saves ou alterar Decades → rollback e reprovação.
- CI de dados sintéticos passar e alguém declarar jogável → não elevar barra sem Game.exe/JoiPlay real.

## 8. Evidências e progresso (não confundir documentação com jogo)

Cada entrega deve registrar: commit SHA, arquivos modificados, fontes/creditos/hashes, MapIDs de origem/destino reais, dependências, testes executados com status, relatório de integração, vídeo/captura/log do Game.exe quando relevante, QA JoiPlay separado, riscos e pendências.

Estados por área: **planned → source_audited → qa_converted → automated_pass → windows_pass → integrated_main → android_pass → accepted**. Pode haver partial/blocked com motivo explícito. Uma fase só é considerada implementada quando os critérios específicos foram comprovados; barras do site avançam somente na dimensão correta.

**Estado na publicação deste MD:** U01 com pesquisa inicial documentada, mas verificação de permissões por asset pendente; U02–U32 não executadas. **0/32 fases aceitas como Unova jogável**. Nenhuma porcentagem de mapa ou história afirmada sem análise da fonte.

## 9. Próxima tarefa pronta — U02

**Executar U02:** obter o Pokémon World V18 pelos links publicados pelo autor, verificar integridade, registrar créditos e direitos, inventariar em modo read-only todos os MapInfos/MapNNN e assets, detectar quais áreas e eventos Unova existem, gerar matriz completa de lacunas e relatório de riscos. **Não mexer no game principal, não selecionar MapIDs do destino e não habilitar Unova na tela inicial.** Informar contagens de arquivos reais (não presumir metade ou quarto) e o que ainda está bloqueado por licenças.

## Referências externas

- Publicação do autor de Pokémon World V18: https://www.reddit.com/r/PokemonRMXP/comments/wsiyyr/
- Fire Ash, Essentials v19.1: https://eeveeexpo.com/threads/9489/
- The Pokémon World Project v21.1: https://eeveeexpo.com/resources/1877/
- Projeto técnico Gen 5 Essentials v20.1: https://github.com/MCChara/Pokemon-Essentials-Gen-5
- Repositório de referência Essentials v21.1: https://github.com/Maruno17/pokemon-essentials
- Detonado B/W: https://www.pokemythology.net/detonados/detonado-black-white/
