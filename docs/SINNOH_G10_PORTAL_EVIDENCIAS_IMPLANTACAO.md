# Sinnoh — G10: evidências de implantação no portal

**17/11/2026 — entrega somente pelo GitHub.** A G10 amplia o guia `/sinnoh` com uma aba de **Estado da implementação**, cartões de evidências e vínculos entre áreas, treinadores, ginásios, HMs, Liga, Hall of Fame e pós-jogo.

A geração lê exclusivamente os **manifestos públicos versionados** B07/B08/B09, S15/S16/S21/S23 e o catálogo `regions.json`, além do guia CH17 derivado dos contratos CH11–CH16. O site **não lê** o computador, saves, pastas particulares, `Game.exe` ou JoiPlay.

## Estados evidenciados

| Estado no portal | Total | Interpretação segura |
| --- | ---: | --- |
| Planejado | 120 | Áreas documentadas na CH17, sem MapID nativo comprovado |
| Cópia privada prevista | 54 | **Terrenos candidatos** nos manifestos B07–B09. Isso não é prova de que o stage foi executado ou os arquivos existem no computador |
| Instalado | **0** | Nenhum evento, mapa, ginásio, item ou PBS de Sinnoh certificado como parte da build jogável |
| Jogável e testado | **0** | Nenhuma sessão nativa Game.exe ou JoiPlay certificada pela G10 |

**Atenção:** o número 54 não significa 54 mapas jogáveis, nem reclassifica a região como `staged` ou `installed`. Mesmo a informação de cópia B09 anteriormente relatada pelo usuário não é verificação remota de bytes, executável ou salvamentos.

## Matriz navegável

A nova aba mostra seis agrupamentos com links para os guias existentes:

- **Áreas (120):** MapIDs, warps e ligações físicas ainda pendentes.
- **Treinadores (40):** versões PBS e vínculo de evento não confirmados.
- **Ginásios (8):** líderes, cidades, insígnias e HMs locais *planejados*. Fantina → RELIC → DEFOG e Maylene → COBBLE → FLY permanecem corretamente vinculados por insígnia, não por posição no CH11.
- **HMs (8):** insígnia mais coleta efetiva e comprovante local; itens de outra região não liberam uso de campo.
- **Liga (8 checkpoints):** Volkner, Barry, Aaron, Bertha, Flint, Lucian, Cynthia e Hall of Fame, com **Hall separado da vitória de Cynthia**.
- **Pós-jogo (6):** Battle Zone, Heatran, Cresselia, Darkrai, Shaymin, revanches Full Power, com Hall local, itens especiais e dez ligas condicionais quando aplicável.

Todos os itens têm status documental `pending`; não representam dados do save do jogador.

## Proteções técnicas

1. **Gerador fail-closed:** [sinnoh-g10-status.mjs](../site/scripts/sinnoh-g10-status.mjs) não aceita alteração dos manifestos que declare `Game.exe` testado, aprovação R07–R09, badges/HMs instalados, assets liberados, times compilados, Hall confirmado ou pós-jogo nativo.
2. **Build do site:** [build.mjs](../site/scripts/build.mjs) produz `site/dist/data/sinnoh-implementation.json` a partir dos manifestos de fonte. Não há credenciais, caminhos do usuário, mapa privado ou conteúdo doador no resultado.
3. **Validação na interface:** [sinnoh-implementation.js](../site/src/assets/sinnoh-implementation.js) valida formato, contagens e flags de evidência **antes** de renderizar. Dados inseguros bloqueiam a página em vez de simular progresso.
4. **Navegação:** [sinnoh-guide.js](../site/src/assets/sinnoh-guide.js) oferece a aba `/sinnoh?aba=implantacao`; [app.js](../site/src/assets/app.js) carrega evidências também em guias por localização, treinadores e Liga. Não acrescenta downloads de Sinnoh.
5. **Testes negativos:** [sinnoh-g10-status.test.mjs](../site/tests/sinnoh-g10-status.test.mjs) cobre 20 cenários de dados planejados, B07–B09, 8 líderes/HMs, Hall, pós-jogo, injeção de estado falso, HTML escapado, filtros e arquivo do build.
6. **CI:** [sinnoh-g10-portal.yml](../.github/workflows/sinnoh-g10-portal.yml) exige build, testes G10, regressões CH17/CH18 e suíte completa do site; publica somente JSON de metadados.

## Limites

- Este guia não comprova os 14 PNGs privados, os índices de tilesets reais, o stage B07/B08 no computador, a cópia B09 local, ou qualquer instalação do `Game.exe`.
- Nenhum save real ou execução de Windows Sandbox/JoiPlay foi analisado.
- As barras de jogo **B/C/D permanecem 0/13**, mesmo após a conclusão da G10.
- A conclusão da esteira G01–G12 é **progresso de desenvolvimento no GitHub**, não porcentagem de Sinnoh jogável.

**Próxima entrega — G11:** automatizar gates de integração e smoke tests entre scripts, portal e artefatos offline, sem execução nativa.
