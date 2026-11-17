# Unova — G06.3: pesquisa, filtros e URLs compartilháveis do guia

**Escopo:** exclusivamente portal Web, catálogo referencial *planned*, sem instalar ou editar mapas, NPCs, encontros, PBS, Game.exe, JoiPlay ou saves.

## Rotas

A G06.3 amplia a [G06.2 de 74 áreas](UNOVA_G06_2_GUIAS_74_AREAS_HISTORIA.md). Todas as páginas usam os mesmos registros auditados. Filtros são **GET** e ficam na URL, funcionando em atualizações, links copiados, navegação por teclado e histórico.

| Rota | Tipos de registros |
| --- | --- |
| `/unova/areas` | 74 áreas simbólicas U03 |
| `/unova/capitulos` | 12 capítulos de G01 |
| `/unova/missoes` | 12 missões G01.1 com referência de capítulo e área |
| `/unova/npcs` | Catálogo de personagens SP04 |
| `/unova/treinadores` | Confrontos G03.3 |
| `/unova/ginasios` | Oito ginásios G02.2 |
| `/unova/liga` | Quatro membros da Elite Four e eventos do Castelo G02.3 |
| `/unova/pendencias` | Falta de MapIDs, eventos, equipes, níveis, direitos e QA |

As páginas individuais `/unova/area/<UNOVA_KEY>` e `/unova/capitulo/<UNOVA_CH_KEY>` continuam navegáveis e oferecem links para catálogos contextuais filtrados. O filtro `area` refere-se ao **catálogo editorial**, não a uma posição verificada no Game.exe. O filtro `fase` refere-se a fases documentais U07–U30, não às fases de desbloqueio jogável.

## Como filtrar

Combinações suportadas de parâmetros GET, todos opcionais e sanitizados:

- `busca`: pesquisa textual (nome, chave, local, ator ou insígnia); remove acentos, ignora caixa e compara todas as palavras. Também entende “rota” e “route”.
- `fase`: fase U publicada no contrato da área principal ou capítulo; seleção restrita às opções da página.
- `capitulo`: chave de capítulo G01.1 existente, permitindo filtrar missões, NPCs, treinadores, áreas e ginásios pelo agrupamento editorial.
- `tipo`: tipo de área, papel de NPC, ator de encontro, classe de Elite ou tipo de pendência. Sempre selecionado entre os valores auditados.
- `pendencia`: motivo nativo não verificado (MapID, evento, PBS, nível, sprite, direito, encontro e QA), não faz o conteúdo passar de `planned` a instalado.
- `area`: vínculo com uma área simbólica do catálogo. Para NPCs, considera área principal e áreas adicionais explicitamente citadas em SP04.

Exemplos compartilháveis:

- `/unova/areas?busca=Rota+1&tipo=route`
- `/unova/npcs?area=UNOVA_NUVEMA_TOWN`
- `/unova/treinadores?capitulo=UNOVA_CH01_NUVEMA`
- `/unova/missoes?capitulo=UNOVA_CH01_NUVEMA`
- `/unova/ginasios?pendencia=equipes`
- `/unova/pendencias?tipo=mapas`

Filtros são combinados com **E**; a contagem mostra resultados/total. Quando não há correspondência, o portal mostra mensagem explícita e não inventa registros. Filtros desconhecidos ou valores fora das listas são ignorados; texto de busca tem limite de 100 caracteres. Nenhum filtro é interpretado como comando, MapID, evento físico, nível ou alteração de estado.

## Acessibilidade

- Formulário sem dependência de JavaScript: `method="get"`; tecla **Enter** envia a busca e o botão **Pesquisar** é alcançável por Tab.
- Campos possuem `label`, `aria-label`, opções acessíveis e indicador de foco de alto contraste.
- Indicador de resultados com `role="status" aria-live="polite"`; vazio com `role="status"`.
- Botão **Limpar filtros** retorna à rota canônica do catálogo, sem parâmetros.
- No SPA, submissão de formulário é interceptada para preservar a navegação/histórico; recarregar o endereço mantém o filtro.
- Links contextuais nas fichas de áreas e capítulos levam às listas filtradas de NPCs, treinadores e missões.

## Proveniência, segurança e limites

- `site/scripts/unova-guide.mjs` continua lendo exclusivamente U03, G01, G02, G03 e SP04. A G06.3 acrescenta apenas o índice das **12 missões**, extraídas de `story.missions`, com `nativeEventId: null`, `nativeMapId: null`, `installed: false`, `status: planned`.
- `site/src/assets/unova-search.js` faz filtragem **pura e imutável**. Não tem acesso à engine, ao filesystem ou a saves. `site/src/assets/unova-guide.js` valida os mesmos invariantes fail-closed da G06.2 antes de renderizar, incluindo equipes, mapas, níveis e eventos que **devem permanecer não verificados**.
- Uma associação editorial de capítulo por fase **não comprova uma saída, roteiro real, acesso físico, NPC ou capítulo jogável**.
- Permanecem pendentes a verificação física de MapIDs, encontros, níveis, equipes, eventos, NPCs licenciados e Game.exe/JoiPlay. Unova continua `planned`; **Barra A 0/8 e Unova jogável 0/32**. Nenhuma modificação de saves ou scripts Ruby.

## Arquivos e testes

- `site/src/assets/unova-search.js` — contrato puro de filtros e URLs.
- `site/src/assets/unova-guide.js` — interface com filtros em todos os catálogos, estado vazio e seção de missões.
- `site/src/assets/app.js` — submete GET e usa `URLSearchParams` nas rotas.
- `site/scripts/unova-guide.mjs` — inclusão das missões G01, sem dados nativos novos.
- `site/src/assets/styles.css` — layout responsivo e foco visível.
- `site/tests/unova-search.test.mjs` — pesquisas, combinações, query string, contexto, teclado e testes negativos de falsa jogabilidade e injeção HTML.
- `site/tests/unova-guide.test.mjs` — regressão das 74 áreas, 12 capítulos, oito ginásios e fontes auditadas.
- `.github/workflows/unova-documentation.yml` — testes Node G06.2 e G06.3 em Linux e Windows; `Portal Blue - validar site` compila e testa o portal.

Comandos:

~~~bash
npm run build --prefix site
npm test --prefix site
node --test site/tests/unova-guide.test.mjs site/tests/unova-search.test.mjs
~~~

**Conclusão auditável:** G06.3 somente quando o CI Linux/Windows/portal for aprovado; registrar **Barra G 27/32 (84%)**, frente G06 **4/4**. Barra A e status jogável ficam inalterados.
