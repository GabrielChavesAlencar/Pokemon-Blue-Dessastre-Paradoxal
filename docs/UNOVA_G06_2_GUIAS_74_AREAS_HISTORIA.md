# Unova G06.2 — guias de 74 áreas e história no portal

**Status:** guia informativo planejado · **Unova não jogável** · **sem alterações em Game.exe, RXDATA, PBS ou saves**.

## Rotas do portal

- [/unova](/unova): visão geral, contagem de áreas/capítulos, grupos de capítulos e lacunas.
- [/unova/areas](/unova/areas): 74 áreas de referência de Unova White, sem mapas nativos instalados.
- `/unova/area/UNOVA_NUVEMA_TOWN` (exemplo): página de área, capítulo editorial, NPCs citados, confrontos de referência, links de outras áreas.
- [/unova/capitulos](/unova/capitulos): 12 capítulos G01.1/2 da jornada White, incluindo Elite Four, Castelo de N e pós-jogo.
- `/unova/capitulo/UNOVA_CH01_NUVEMA` (exemplo): missão e gates simbólicos, áreas, ginásios, confrontos e links anterior/próximo.
- [/unova/ginasios](/unova/ginasios): oito ginásios G02.2, cidade, líder de referência, insígnia e capítulo.
- [/unova/liga](/unova/liga): quatro membros da Elite Four, N/Ghetsis e eventos de Castelo G02.3.
- [/unova/npcs](/unova/npcs): personagens SP04, relacionando lugares documentados; nenhum sprite/evento instalado.
- [/unova/treinadores](/unova/treinadores): encontros simbólicos G03.3 de rivais e Plasma, sem equipes, níveis ou PBS verificados.
- [/unova/pendencias](/unova/pendencias): MapIDs, direitos, eventos, equipes, encontros e testes nativos pendentes.
- [/unova-progresso](/unova-progresso): Barra G de desenvolvimento **separada** da Barra A e Unova jogável.

Todos os caminhos são páginas do SPA construído por `site/scripts/build.mjs` com o dataset `dist/data/unova-guide.json`. A página `/regioes` e a Barra G passam a ter link para o guia. Não há adição de NPC físico, mudança em passagens do mapa ou alteração do jogo.

## Fontes auditadas e fronteiras

O gerador `site/scripts/unova-guide.mjs` lê **somente** os catálogos já versionados, diretamente do repositório:

| Fonte | Informação aproveitada | O que permanece pendente |
|---|---|---|
| `data/regions/unova-u03-areas.json` | Identidade, nome, tipo e fase das 74 áreas | Origem/destino MapID, passagens, gráficos, direitos |
| `data/regions/unova-g01-state-contract.json` | 12 capítulos mais pré-jogo, áreas de referência e missões | Eventos executáveis, flags e saves reais |
| `data/regions/unova-g01-chapter-transitions.json` | Gates e progressão sintéticos G01.2 | Eventos reais no Game.exe |
| `data/regions/unova-g02-gym-story-contracts.json` | 8 insígnias, locais, líderes White e capítulos | Níveis, times, recompensas e ginásios jogáveis |
| `data/regions/unova-g02-elite-finale-contracts.json` | Elite Four e eventos narrativos do Castelo de N | Combates, captura, créditos e MapIDs |
| `data/regions/unova-g02-postgame-contracts.json` | Progresso opcional, pós-jogo e suas lacunas | Eventos, itens, encontros e conteúdo instalado |
| `data/regions/unova-g03-rivals-plasma-story-contracts.json` | Confrontos e referências de Bianca, Cheren, N e Plasma | Dados Trainer PBS, equipe, nível e execução |
| `data/regions/unova-sp04-npcs.json` | Personagens citados e ligações com locais | Sprites licenciados, posição, evento NPC no mapa |

A geração falha se uma área aparecer como instalada, algum MapID deixar de ser `null`, ocorrer duplicação de chaves ou faltar fonte obrigatória. Ela não lê nem edita arquivos do jogo.

### Por que as 74 áreas estão agrupadas editorialmente?

A lista U03 distingue campanha, pós-jogo, locais opcionais e eventos condicionados e fornece a **fase planejada U07–U30**, mas não garante para cada área uma transição de mapa ou um capítulo único. Para a navegação não criar ligações falsas:

1. As **áreas principais** usam a fase do capítulo auditado mais próximo. Áreas pós-jogo ou de evento pós-jogo usam o capítulo de pós-jogo.
2. Cada área é mostrada **uma única vez** no catálogo e possui um capítulo para fins de navegação editorial.
3. A interface exibe claramente o texto: **“agrupamento editorial por fase, não ligação física ou rota jogável”**.
4. Links entre áreas do mesmo grupo são links de consulta, **não saídas de mapa, passagens nem teleporte**.

As páginas de área usam os códigos simbólicos `UNOVA_*`, nunca MapIDs do Essentials. Não são incluídos níveis fixos, taxas de encontro, espécies encontradas, equipamentos de Pokémon, ou Trainer PBS não comprovados.

## Proteções e testes

`site/tests/unova-guide.test.mjs` verifica:

- 74 áreas com links próprios; 12 capítulos navegáveis e suas ligações;
- 8 ginásios, 4 Elite, NPCs SP04 e confrontos G03.3;
- source-closed: recusa MapIDs, níveis, times, eventos, NPCs e progresso jogável falsos;
- rejeita chaves duplicadas, associações quebradas e perda de cobertura;
- HTML escapado para nomes de referências e navegação contextual acessível;
- Barra A em **0/8** e Unova jogável em **0/32**, mantendo a classificação `planned`.

Executar no repositório:

~~~bash
cd site
npm run build
npm test
cd ..
node --test site/tests/unova-guide.test.mjs
~~~

O fluxo `.github/workflows/unova-documentation.yml` executa os testes G06.2 no Linux e Windows; o fluxo de portal executa `npm run build` e `npm test`. A Barra G só pode subir para **26/32 (81%)** após aprovação do CI relevante e merge na `main`.

## Próximo marco — G06.3

Busca, filtros de NPCs, treinadores e missões, refinamentos de links contextuais e acessibilidade sobre o mesmo dataset verificado. Até lá, os guias G06.2 já permitem navegar pelas 74 páginas e pela história, mas ainda não possuem os filtros avançados da G06.3.
