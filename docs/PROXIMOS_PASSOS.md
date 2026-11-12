# Próximos passos — Pokémon Blue: Dessastre Paradoxal

**Acompanhe as [16 etapas de conclusão de Kanto](KANTO_ETAPAS.md).**

**Referência nova — eventos FireRed:** [estudo técnico dos 425 mapas](ESTUDO_EVENTOS_MAPA_POKEMON_FIRERED_RPG_MAKER_XP.md) · [passo a passo detalhado de aplicação em RPG Maker XP/Essentials](FIRERED_EVENTOS_COMO_APLICAR_NO_BLUE.md) · [extrator de eventos da decompilação](../scripts/regions/extrair_eventos_firered.py). Documentação e ferramenta **não instalam eventos**: manter os 11 mapas de prévia da Fase 09 sem NPCs, portas ou gatilhos enquanto não houver liberação explícita. Priorizar MAN-01/02/03 e preservar as duas barras de progresso. O contador é atualizado somente com testes concluídos.

**Desenvolvimento atual: etapa 08/16 (50%). Conclusão validada: 01/16 (6,25%).** O piloto experimental já integra 40 mapas até Vermilion/S.S. Anne, com teste nativo automatizado; a caminhada, as portas internas, os eventos de treinadores e as batalhas reais ainda precisam ser validados. [Instalação opcional no jogo principal e seletor de região](KANTO_ESCOLHA_REGIAO.md) · [feedback manual de 12/11](KANTO_FEEDBACK_TESTES_MANUAIS_2026-11-12.md).

## Especificações de referência — regras já definidas

As decisões funcionais do circuito regional, balanceamento, pós-jogo, regras locais, viagens e preservação de saves **já estão especificadas** nos documentos abaixo. Este roteiro acompanha a implementação e a validação; **não substitui nem redefine** essas decisões.

- [Plano de regiões Dessastre v2 — especificação funcional principal](PLANO_REGIOES_DESSASTRE_V2.md): escolha da região inicial, duas regiões vizinhas por Liga, integração com esmeraldas e balanceamento atuais, pós-jogo após dez Ligas, classificação/bloqueio de especiais, NPC de transporte, HMs/montarias regionais, saves e testes.
- [Estudo de fangames e todas as regiões — referência técnica](ESTUDO_FANGAME_TODAS_AS_REGIOES_POKEMON.md): levantamento de fontes, licenças, importação modular de mapas e eventos, remapeamento de IDs, compatibilidade do Essentials e critérios de validação.

Se houver diferença entre uma sugestão exploratória do estudo e uma decisão explícita do Plano v2, usar a decisão do Plano v2. O estado do código deve ser verificado separadamente: documentação de regra não equivale a funcionalidade implementada.

## Ponto de partida

- [x] Decades é a campanha principal. O menu **Circuito de Regiões** reconhece o encerramento de Decades em saves existentes. As regras de progresso regional, viagem e pós-jogo já têm uma base em [`Regions.rb`](../scripts/battle_polish/Regions.rb).
- [x] O piloto começou em **Pallet → Pewter (13 locais)**, foi ampliado para **25 mapas até Cerulean/Misty** e depois para **40 mapas até Vermilion, S.S. Anne e Lt. Surge**. As [fases 07](KANTO_FASE_07.md) e [08](KANTO_FASE_08.md) documentam os blocos; a [jogabilidade no Windows](KANTO_TESTE_EXPERIMENTAL.md) ainda precisa de validação manual por evento. A fonte e os créditos estão no [guia do circuito](CIRCUITO_REGIONAL.md).
- [x] O portal publica as fichas do piloto. [Localizações](https://pokemondessastreparadosal.vercel.app/localizacoes?regiao=kanto) · [Treinadores](https://pokemondessastreparadosal.vercel.app/treinadores?regiao=kanto) · [Brock](https://pokemondessastreparadosal.vercel.app/chefes/kanto-brock).
- [x] O teste nativo compilou o conteúdo, carregou Pallet e o laboratório, consultou encontros e equipes, registrou a Boulder Badge e recarregou o save. As vitórias de batalha foram simuladas pelo teste. [Execução no GitHub Actions](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43123226204).
- [ ] Jogar o percurso manualmente. Na última tentativa de abrir a cópia local por automação, o motor falhou ao inicializar o sistema de arquivos (PhysFS). A abertura em uma sessão normal do Windows ainda precisa ser confirmada.

## Fase 09 — autorização limitada a cenários

Foi iniciada uma [prévia de Celadon e Erika](KANTO_FASE_09.md): cenário/tileset das áreas selecionadas, sem eventos de qualquer tipo no lote novo. **Manter MAN-01 (interiores), MAN-02 (treinadores) e eventos de Erika/Team Rocket em espera pela análise do usuário.** Não apagar as pendências nem criar atalhos que concedam insígnias.

**Estado de Kanto:** etapa 09 iniciada (cenário), mas desenvolvimento funcional **8/16 (50%)**, aceitação **1/16 (6,25%)**, porque a fase 09 ainda não tem progressão nem batalha.

## 0. Correções prioritárias identificadas pelo usuário (12/11/2026)

**Fonte:** [feedback de teste dos mapas — leitura e critérios de aceite](KANTO_FEEDBACK_TESTES_MANUAIS_2026-11-12.md).

**Cobertura informada:** Pallet Town, Rota 1, Rota 2, Viridian City, Viridian Forest, Pewter City, **somente o lado esquerdo da Rota 4** e Mt. Moon. O registro demonstra que o jogador **visitou** essas áreas, não que tenha aprovado portas, combates, todos os andares e save/reload.

- [ ] **Prioridade 1 — Entradas dos interiores (MAN-01).** Auditar e conectar casas, Centro Pokémon, Poké Mart, laboratório, portarias e ginásios aos seus mapas reais de interior. Validar saída e retorno, coordenadas, colisões, eventos de porta e ausência de colisões de IDs Decades/Kanto.
- [ ] **Prioridade 2 — Detecção e bloqueio dos treinadores (MAN-02).** Os treinadores devem reagir ao jogador, e encontros obrigatórios não devem permitir passagem sem cumprir a batalha. Respeitar as regras individuais e os treinadores opcionais da fonte; preservar vitórias/derrotas e saves.
- [ ] **Prioridade 3 — Duas telas de insígnias (MAN-03).** Tela local de Kanto com oito posições, líder e estado; tela geral por região/geração com o progresso de todas as regiões, sem inventar insígnias em Alola, Hisui ou Decades. Atualizar a UI a partir do mesmo estado regional persistido.
- [ ] Executar regressão de caminhada real e registrar evidências por mapa/evento **antes de aceitar** as etapas 02, 03 e 07. O TXT não afirma ter testado Vermilion/Surge (fase 08).

**Não alterar as barras por receber feedback:** desenvolvimento **8/16**; aceitação total **1/16**. Corrigir esses itens em paralelo à próxima expansão, sem considerá-los concluídos antecipadamente.

## 1. Validar o piloto de Kanto

**Teste gráfico da etapa 02:** execute [`KANTO_TESTAR_WINDOWS.bat`](../KANTO_TESTAR_WINDOWS.bat) em um Windows com sessão de desktop ou siga o [checklist completo](KANTO_TESTE_WINDOWS.md). O runner Windows já [detectou a janela real do Game.exe](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43127669413), mas os controles, batalhas e caminhada continuam pendentes de teste interativo. **Contador: 1/16 concluída, 15 restantes.**

Prepare a [instalação do Blue](INSTALACAO.md) e extraia o Essentials FRLG 1.1 conforme o [guia do circuito](CIRCUITO_REGIONAL.md). Na raiz do repositório, execute:

```powershell
python scripts/regions/pilot.py --launch
```

O comando usa `.blue-work/kanto-pilot` e o perfil de save **Kanto Piloto**. Se precisar reconstruir a cópia após mudar mapas ou scripts, passe um caminho novo, por exemplo `--output .blue-work/kanto-pilot-revisao`.

- [ ] Abrir o piloto no Windows. Se houver erro do motor, registrar a mensagem e o log, corrigir a causa e repetir a abertura.
- [ ] Em partida nova, entrar no laboratório de Oak, escolher um inicial e jogar a batalha contra Blue. Conferir as três escolhas e o comportamento após vitória e derrota.
- [ ] Sair de Pallet, encontrar e capturar um Pokémon na Rota 1, curar em Viridian e atravessar as conexões, portarias e saídas da floresta até Pewter.
- [ ] Jogar as lutas de Liam e Brock. Conferir o time de Brock, a Boulder Badge concedida uma vez e a recuperação após derrota.
- [ ] Salvar e reabrir pelo menu do jogo. Conferir posição, equipe, Pokémon capturado, itens e progresso. Reabrir também um save de Decades para conferir a compatibilidade.
- [ ] Testar o piloto no Android depois de validar no Windows, seguindo o [guia de JoiPlay](ANDROID_JOIPLAY.md).

## 2. Integrar uma viagem de ida e volta

**Implementação do serviço de ida/volta:** [guia da fase 05](KANTO_VIAGEM_DEC_KANTO.md). O transporte aparece no menu de pausa após a Liga comprovada e os mapas instalados. A inserção física do NPC no pós-Liga e a validação gráfica continuam pendentes.

- [ ] Colocar o agente de transporte depois do encerramento real de Decades. A confirmação deve usar os marcos auditados da Esmeralda Stellar e do Hall da Fama, descritos no [guia do circuito](CIRCUITO_REGIONAL.md).
- [ ] Ligar o agente a um ponto de chegada confirmado em Kanto e a um ponto de retorno acessível. Mostrar destinos jogáveis, condições de bloqueio e opção de cancelar. Validar em uma cópia antes de abrir a viagem na campanha.
- [ ] Usar um único save para a campanha integrada. Acrescentar estado regional versionado e preservar equipe, PC, Pokédex, itens, dinheiro, conquistas e missões. Exercitar save antigo, viagem, retorno, salvamento e recarga.
- [ ] Validar visualmente a seleção de região inicial no Windows: o [seletor e a instalação opt-in de Kanto](KANTO_ESCOLHA_REGIAO.md) já foram implementados, com proteção para regiões não instaladas, Decades e saves antigos. Só marcar após confirmar a interface e o carregamento em ambas as origens.
- [ ] **Validar visualmente** o cálculo de insígnias no balanceamento Blue. A [fase 06](KANTO_FASE_06.md) já soma conquistas locais únicas ao estágio global nativo e aplica permissões regionais de especiais e HMs, com testes Ruby/nativos aprovados. Faltam cobertura completa de caminhos alternativos e aceitação manual.
- [ ] Classificar lendários, míticos, Ultra Beasts e Paradoxos, incluindo os autorais. Aplicar a regra das oito conquistas locais à equipe e ao PC. Na viagem, reservar slots antes de depositar os especiais e validar que sobra equipe utilizável. Se faltar espaço ou equipe, manter o estado anterior e permitir reorganizar a equipe.
- [ ] Validar as HMs locais em mapas reais e expandir montarias/outras ações; [RegionalPolicy.rb](../scripts/battle_polish/RegionalPolicy.rb) já intercepta os comandos padrão de campo, mantendo as regras de Decades. Aplicar também as provas de Alola e o arco de Hisui conforme o [catálogo regional](../site/public/data/regions.json).

## 3. Completar Kanto

- [ ] Expandir o trecho de Pewter aos oito ginásios e à Liga. Recriar eventos, rival, treinadores e marcos de história. Avaliar Sevii Islands conforme a disponibilidade de mapas e o escopo da campanha.
- [ ] Mesclar encontros de FireRed e LeafGreen preservando habitats, horários, métodos, níveis e pesos. Conferir espécies, golpes, itens e equipes-base contra as referências.
- [ ] Auditar IDs de mapas, switches, variáveis, tilesets, portas, pontos de cura e conexões. Resolver dependências em cada lote e registrar origem, créditos, remapeamento e como desfazer a importação.
- [ ] Validar a jornada até a Liga. Kanto deve liberar **Decades e Johto** somente após o encerramento da Liga. Repetir a finalização não duplica a conquista nem desbloqueios.

## 4. Expandir o circuito

O circuito de desbloqueio é **Decades ↔ Kanto ↔ Johto ↔ Hoenn ↔ Sinnoh ↔ Unova ↔ Kalos ↔ Alola ↔ Galar ↔ Paldea ↔ Decades**. A ordem abaixo é de desenvolvimento. Ao jogar, cada Liga libera as duas vizinhas, conforme o progresso do save.

| Ordem | Região | Trabalho a entregar |
| --- | --- | --- |
| 1 | Johto | Unificar HeartGold e SoulSilver, validar ginásios, Liga e viagens com Kanto e Hoenn. |
| 2 | Hoenn e Sinnoh | Fundir Ruby/Sapphire com Emerald e Diamond/Pearl com Platinum. Auditar conexões, encontros e eventos das Ligas. |
| 3 | Unova, Kalos e Alola | Tratar Black/White e Black 2/White 2 por era, unificar X/Y e adaptar as ilhas e provas de Ultra Sun/Ultra Moon. |
| 4 | Galar e Paldea | Tratar versões e conteúdo adicional por escopo. Implementar o Champion Cup de Galar e a progressão de Paldea. Encontrar uma fonte editável adequada para Paldea ou construir mapas próprios. |
| 5 | Hisui | Encontrar fonte editável ou construir mapas 2D. Criar expedição, permissões de campo e viagem temporal. Hisui tem encerramento próprio e fica fora da contagem das dez Ligas. |

- [ ] Para cada região, verificar a permissão da fonte, registrar créditos, importar primeiro um trecho em cópia isolada e validar mapas, eventos, batalhas, save e rollback antes de integrar.
- [ ] Depois das dez Ligas, ativar o pós-jogo mundial. Catalogar por região as equipes oficiais mais fortes de líderes, Elite Four onde houver e campeões. Registrar jogo, versão e referência de cada equipe antes de habilitar a revanche correspondente.

## 5. Atualizar o portal e o Blue Studio junto com cada lote

- [ ] Gerar localizações, encontros, treinadores e líderes dos mesmos dados usados pelo jogo. Para o piloto atual, use [`export_kanto.py`](../scripts/regions/export_kanto.py) a partir do diretório de prévia.
- [ ] Atualizar os estados no [catálogo de regiões](../site/public/data/regions.json) e vincular fichas da Pokédex, Habitat Dex, Pokégear e Álbum de Treinadores aos IDs efetivamente importados.
- [ ] Conferir seletores de região, fichas, equipes e links em desktop e celular. Informar no portal o que já pode ser jogado e o que ainda está em preparação.
- [ ] Rodar `npm test --prefix site` e `npm run build --prefix site`. Depois do push, conferir os testes do GitHub Actions e o [portal publicado](https://pokemondessastreparadosal.vercel.app/regioes).

## 6. Retomar as outras frentes do projeto

- **Pokédex autoral:** fechar os dados das espécies pendentes, revisar sprites, golpes e evoluções, e testar em batalha antes de liberar. [Geração Dessastre Paradoxal](GERACAO_DESSASTRE_PARADOXAL.md) · [Estudo dos sete Paradoxos futuros](PARADOXOS_FUTURO_7_POKEMON_ESTUDO.md).
- **Blue Studio:** revisar o plano de edição de mapas, flags, encontros e equipes. Priorizar validação de referências, pesos de encontros, backups e integração com a compilação. [Plano do editor](PLANO_EDITOR_EMERALD_BLUE.md).
- **Hub de Batalha:** usar o multiplayer sincronizado existente como referência. Retomar o experimento de servidor autoritativo se o projeto avançar para partidas com ranking. [Roadmap do Hub](ROADMAP_HUB.md) · [Manual do multiplayer](MULTIPLAYER.md).
- **Instalação e distribuição:** verificar instalação limpa, atualização, recuperação de falha e compatibilidade com saves. Versionar scripts e dados próprios. Manter a instalação do jogo, as fontes de terceiros, binários e saves nas cópias locais. [Instalação](INSTALACAO.md) · [Android](ANDROID_JOIPLAY.md).

Antes de retomar uma etapa, confira a `main` e marque neste arquivo o que tiver sido reproduzido. Quando concluir um lote, registre o teste, o commit e a próxima tarefa que ficou aberta.
