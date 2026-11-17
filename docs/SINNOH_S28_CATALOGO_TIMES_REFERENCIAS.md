# Sinnoh S28 — catálogo de equipes históricas no portal

**Escopo da Barra A:** S28 — catálogo web de equipes de treinadores e Liga de Sinnoh. **Não instala, edita nem verifica PBS no Game.exe**. O jogo real e o Android/JoiPlay continuam bloqueados até a integração auditada dos mapas e testes nativos.

## Fontes e distinção essencial

A fonte versionada é [`sinnoh-trainer-teams-ch15.json`](../data/regions/sinnoh-trainer-teams-ch15.json), auditada na CH15 e exibida pelo [gerador do guia](../site/scripts/sinnoh-guide.mjs) e pela [página `/sinnoh`](../site/src/assets/sinnoh-guide.js).

- **8 líderes de ginásio:** Roark, Gardenia, Fantina, Maylene, Crasher Wake, Byron, Candice e Volkner. A ordem é de *Pokémon Platinum*, Fantina em terceiro e Maylene em quarto.
- **4 integrantes da Elite Four:** Aaron, Bertha, Flint e Lucian.
- **1 campeã:** Cynthia.
- **5 referências de revanche Platinum:** Elite Four e Cynthia. As revanches históricas **não** são o Full Power personalizado do Blue.
- **40 treinadores gerais:** existem como referências de NPC/localização no guia, mas **não têm equipes Blue/PBS verificadas**. Não são inventados Pokémon ou níveis para eles.
- **Todas as 13 primeiras equipes:** espécies e quantidade de integrantes vêm exclusivamente do contrato CH15; níveis históricos existentes na fonte **não** são publicados como níveis efetivos do jogo.

O [schema do portal](../site/src/assets/sinnoh-search.js) exige `teamAudit` em cada uma das 13 equipes, distinguindo `firstBattle`, `historicalRematch`, `blueFullPower` e `nativePBS`. Rejeita proveniência adulterada, integrantes inventados, níveis fixos incorporados, PBS falsamente compilado, campo de batalha nativo verdadeiro e qualquer contagem de equipes jogáveis diferente de zero.

## Testes reproduzíveis

[10 novos testes S28](../site/tests/sinnoh-s28-trainer-teams.test.mjs) verificam a composição exata das 13 equipes, a contagem de ginásios/Elite/campeã, as 5 revanches históricas, a situação dos 40 treinadores sem times verificados, escapes HTML, integridade do JSON construído, e testes negativos de instalação nativa e Full Power fabricados.

```bash
cd site
npm run build
npm test
```

O workflow **Portal Blue** deve passar build + suíte completa; a regressão CH19 Python/Ruby, o pré-voo CH20 e a suíte S30 são verificações adicionais de isolamento. **Não confundir testes web aprovados com uma batalha executada.**

## Aceite da S28

A S28 é considerada **concluída em código/documentação web** após aprovação do CI e merge na `main`, registrando no [ledger](../data/regions/sinnoh-progress.json) **Barra A 12/32 (37%)**, 6 tarefas parciais e 14 pendentes. O progresso de trabalho pelo chat (Barra E) permanece 20/20 (100%); os 13 gates técnicos/jogáveis/nativos B/C/D continuam **0/13**, com **44 casos nativos não executados**.

**Limitações que persistem:** ausência de assets de mapas autorizados e fonte nativa Sinnoh compilada, equipes de NPCs gerais sem PBS, nenhuma conferência física de posições, gráficos, música, saves ou execução Windows/Android.
