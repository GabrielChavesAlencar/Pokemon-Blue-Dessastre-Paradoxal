# Hoenn — barra de progresso jogável (12 fases)

**Atualizado:** 14/11/2026. Referência de dados: [hoenn-qa-progresso.json](../data/regions/hoenn-qa-progresso.json). Etapa técnica anterior: [10/10](HOENN_ETAPA_10_SOOTOPOLIS_RAYQUAZA_LIGA.md).

**Acompanhe as DUAS barras separadamente:**

- **Etapas de código existentes:** 10/10 — ██████████ (concluídas e publicadas, sem certificar Game.exe).
- **Fases jogáveis 1–12:** preparação das fases 1 e 2 implementada; execução/aceite pendentes — ▣▣□□□□□□□□□□ (▣ = ferramenta pronta; NÃO = jogável).
- **Fases nativamente aprovadas:** 0/12 — □□□□□□□□□□□□ (sem testes reais completos).

| # | Etapa | Preparação | Aceite Game.exe |
|---:|---|---|---|
| 1 | Gerar cópia isolada com 199 mapas e PBS | **Ferramenta preparada, execução local pendente** | ⏳ |
| 2 | Corrigir conexões e colisões dos mapas | **Auditoria de RXDATA/PBS implementada; execução local pendente** | ⏳ |
| 3 | Conferir encontros, NPCs, treinadores e itens | Pendente | ⏳ |
| 4 | Surf, Dive, Waterfall, Strength e puzzles | Pendente | ⏳ |
| 5 | Equipes Aqua/Magma, Seafloor Cavern | Pendente | ⏳ |
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
