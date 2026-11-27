# Unova — execução Codex até 100% jogável no Windows e Android

**Pokémon Blue: Dessastre Paradoxal · 27/11/2026 · Plano operacional de execução, não recibo de implementação.**

Alvo: campanha Pokémon White (BW1), adaptada ao mesmo jogo principal Decades + Essentials 21.1/RMXP, com saves compartilhados, oito insígnias, final, pós-jogo e atualização incremental. Black City/Drayden como variante e BW2 como expansão futura; não misturar mapas, personagens ou cronologias. A referência White é a decisão já registrada no projeto. Conteúdo dependente de servidores descontinuados deverá ter equivalente offline definido e documentado, ou exclusão explícita aprovada pelo mantenedor.

## 0. Instrução prioritária para Codex (ler antes de executar)

**Você é o agente executor, não apenas autor de planos.** Leia AGENTS.md (se existir), este arquivo e o estado real da main. Faça a implementação vertical, em PRs pequenos, use ferramentas e workflows existentes, corrija falhas reproduzidas e só avance com evidências. Não gaste novos lotes construindo simulações de contratos que já existem. Não espere interação humana para tarefas independentes que podem ser feitas com fontes próprias/autorizadas; quando um gate material exigir autorização ou hardware, registre BLOCKED com o insumo exato, mantenha a parte bloqueada isolada e não marque aceite. Não contorne gates.

- Preserve saves, MapIDs já publicados, Gary e times autorais, dados de Decades, Kanto, Johto, Hoenn e Sinnoh. Não redefina MapInfos, Tilesets, Scripts, CommonEvents ou PBS globais a partir de outro jogo.
- Um lote perceptível ao jogador = um par Windows + Android multirregional, mesma revisão funcional, antes do próximo lote. Siga [a regra de publicação vigente](KANTO_ROADMAP_PUBLICACAO_WINDOWS_ANDROID.md). Lotes offline internos e QA privada não são releases públicas.
- Não publique jogo incompleto como 100%, não altere marcadores de versão manualmente, não desative testes, não gere mapas vazios ou portais fictícios para preencher indicadores.
- Consulte o estado de PRs, checks e releases na retomada. Use SHA completo. Não force-push main nem sobrescreva PR alheio, não reexecute jobs verdes sem motivo; confira HEAD e base atual antes do merge.
- Faça mudanças de gameplay na infraestrutura compartilhada, não crie um segundo Game.exe permanente para Unova. Cópia descartável QA é permitida e necessária antes de promover.
- Minimize relato no chat: informe lote, PR, SHA, CI, evidência, versões e próximo passo. Escreva relatório persistente no repositório e issue de acompanhamento.
- Este documento não autoriza re-hospedar fontes, extrair ROMs comerciais, usar credenciais alheias ou executar arquivos desconhecidos. Use origem autorizada, ambiente efêmero, secrets existentes com menor privilégio e hashes; nunca imprimir tokens ou enviar saves pessoais para Actions.
- Sempre que uma instrução abaixo conflitar com o estado real do código, inspecione os arquivos e adapte os comandos. Nomes marcados como **propostos** são tarefas, não interfaces existentes. Não confunda testes Ruby em stubs com gameplay nativo.

## 1. Baseline auditada

| Indicador | Evidência disponível |
|---|---|
| Registro regional | UNOVA = planned; White como base do roteiro |
| Barra G (contratos/GitHub) | 32/32, não nativa |
| Barra A (aceite técnico nativo) | 0/8, 17 campos de evidência pendentes na matriz A15 |
| Barra U (aceite jogável) | 0/32 |
| Catálogo U03 | 74 áreas simbólicas: 15 localidades/settlements (inclui Liga e White Forest), 18 rotas, 8 ginásios; não são 74 MapIDs físicos |
| Fonte World V18, PR #92 | 64 mapas do ramo Unova lidos, ZERO eventos RMXP; 20 nomes correspondentes ao ramo, 19 coincidências fora dele e 35 sem nome idêntico. Não inferir cobertura de 64/74 |
| NPCs SP04 / U07 | 73 personagens/arquétipos de referência; 13 eventos iniciais simbólicos |
| E06/E07 | 14 grupos de direitos a revisar, 69 cues musicais desativadas, 19 referências de treinadores sem equipes instaladas |
| Encontros G04 | 74 áreas, 20 métodos candidatos de parser; dados de origem/PBS nativos ainda não certificados |
| MapIDs históricos 17/11 | 648 ocupados, 82 candidatos 518–599 e 92 alternativas (174 no total); 442–517 retenção administrativa de Sinnoh, não reserva definitiva. Reauditar main e instalação atuais |
| Anomalias históricas | 2 transferências de Map001 para MapID 3 ausente; 20 expressões computadas. Verificar se ainda existem e se afetam o fluxo atual; corrigir somente comportamento comprovado |
| PR #195 | A16 aberto na consulta de 27/11; recepção de 11 recibos sanitizados, não implantação. Revisar base atual e dependências; não assumir merge |
| PR #208 | Auxiliar FRLG source-only, não fornece mapas de Unova. Não tratar FRLG como dependência geográfica do piloto Unova |

Fontes internas:
- [Tracker G](../site/public/data/unova-github-progress.json) · [registro de regiões](../site/public/data/regions.json) · [matriz A15](../data/regions/unova-a15-native-readiness-matrix.json).
- [Catálogo U03](../data/regions/unova-u03-areas.json) · [NPCs SP04](../data/regions/unova-sp04-npcs.json) · [contratos U07](../data/regions/unova-u07-nuvema-events.json) · [E06/E07](../data/regions/unova-e06-e07-preparation.json).
- [Auditoria da fonte #92](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/92) · [PR A16 #195](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/195) · [PR FRLG #208](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/208).
- [Roteiro U01–U32](UNOVA_PLANO_IMPORTACAO_REGIAO_32_FASES.md) · [Plano operacional SP05](UNOVA_ROTEIRO_IMPLEMENTACAO_OPERACIONAL_SP05_U32.md) · [Fontes RMXP](UNOVA_PESQUISA_FONTES_RMXP.md) · [A15](UNOVA_A15_PRONTIDAO_NATIVA_A04_A14.md).

Limites desta revisão: fonte bruta não baixada novamente, instalação do usuário e Game.exe/JoiPlay não acessados. Os números de MapIDs e resultados históricos não são evidência da instalação atual. Nenhum direito foi homologado aqui.

## 2. Fontes, downloads e ferramenta de teste

Use a página do autor para adquirir o arquivo, e não mirrors desconhecidos. Em qualquer fonte, registre URL final, versão, nome, tamanho, SHA-256 calculado, licença por arquivo, autor, créditos e se o uso e a redistribuição pretendidos são permitidos. Se a fonte não estiver acessível, não invente um URL de download nem desative validação.

| Fonte | Link de aquisição/consulta | Como usar |
|---|---|---|
| Pokémon World V18 (origem candidata de geometria) | [Post do autor](https://www.reddit.com/r/PokemonRMXP/comments/wsiyyr/) · [ZIP MediaFire](https://www.mediafire.com/file/tq5w0in2xt2peb1/Pokemon_World_V18.zip/file) · [Credits.txt](https://www.mediafire.com/file/gdtsjg5lbnstzo1/Credits.txt/file) · [Documentos](https://drive.google.com/drive/folders/1xBVQkXb47gTl7xgEMfDBz4oSukaNmKH4?usp=sharing) | Fonte parcial v18; auditar geometria, tiles e dependências, nunca instalar o jogo doador por inteiro. Links históricos do repositório; acesso/bytes não reconfirmados nesta revisão |
| Gen 5 Overworld Pack, Radical Raptr | [Página e botão Go to download](https://eeveeexpo.com/resources/25/) | Candidatos de sprites alinhados RMXP; página acessível e pede créditos, inclui sprites derivados de rips. Direitos do compilador não equivalem a autorização sobre todos os recursos; revisar antes de redistribuir |
| Pokémon Fire Ash 3.7.1 | [Página oficial da equipe com MEGA/Drive](https://eeveeexpo.com/threads/9489/) | Referência visual e funcional, história do anime, Essentials 19.1, não doador automático; sem importar mídia/eventos não licenciados |
| The Pokémon World Project | [Página do autor](https://eeveeexpo.com/resources/1877/) | Referência estrutural Essentials 21.1; pesquisa anterior registrou Unova 0%; verificar estado antes de considerar fonte |
| MCChara Gen 5 | [Código e documentação](https://github.com/MCChara/Pokemon-Essentials-Gen-5) | Referência técnica v20.1, não campanha pronta; portar apenas trechos permitidos e compatíveis |
| Pokémon Essentials | [Repositório upstream](https://github.com/Maruno17/pokemon-essentials) · [Wiki](https://essentialsdocs.fandom.com/wiki/Essentials_Docs_Wiki) | Inspecionar APIs compatíveis com v21.1 e pin da engine real Blue; não atualizar a engine junto com Unova |
| Decades | [Repositório da base](https://github.com/HazyCrazy/Pokemon-Decades) | Usar o processo de aquisição já implementado no Blue e sua revisão pinada, não copiar saves ou substituir jogo vivo |
| História BW | [Detonado Pokémothology](https://www.pokemythology.net/detonados/detonado-black-white/) · [Bulbapedia Unova](https://bulbapedia.bulbagarden.net/wiki/Unova) · [Serebii Pokéarth](https://www.serebii.net/pokearth/unova/) | Referências de topologia, sequência, equipes, itens e encontros; reescrever falas PT-BR, verificar versão White, não copiar artigos inteiros |
| Windows | [Releases Blue](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases) · [RPG Maker XP](https://www.rpgmakerweb.com/products/rpg-maker-xp) | Blue-Story.exe do par funcional verificado; editor comercial opcional para autoria, usar licença legítima |
| Android | [JoiPlay + plugins](https://joiplay.net/) · [Termux](https://termux.dev/en/) · [Releases Blue](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases) | RPG Maker Plugin adequado, versão pinada e registrada, jogo compartilhado multirregional e atualizador incremental; não usar APK de terceiros desconhecidos |

SHA-256 histórico World V18: `ca6226a070026a8f269c927bfe9a30821b659e2629df26513be780fc34ceda35`. Validar bytes antes de extração. Hash divergente = quarentena e nova revisão de origem, nunca editar pin só para passar. Fonte v18 contém geometria mas não eventos; construir os eventos no formato nativo. Se direitos de um recurso permanecerem bloqueados, preferir geometria, tiles, sprites e música originais ou licenciados, sem extrair conteúdo protegido. Não prometer identidade gráfica perfeita com o original se a substituição autoral for necessária.

### 2.1 Aquisição e ambiente (privado e descartável)

- Preparar `.blue-work/unova/sources/` e `.blue-work/unova/qa/`, fora do Git; conferir gitignore. Nunca gravar URLs temporárias com tokens, arquivos privados, Game.exe, saves ou arquivos doador em commits/artifacts públicos.
- Usar o downloader auditado U02/E04 existente, ou baixar manualmente da fonte oficial mediante permissão. Não executar EXE/BAT/Ruby do doador, não carregar Marshal arbitrário no processo principal. Primeiro parser inerte, limite de tamanho, rejeição de path traversal, links, duplicatas e arquivos suspeitos.
- Em runner Windows autorizado, criar cópia baseline do jogo via instalador atual, perfil de save exclusivamente QA e manifesto before/after. Não tocar a instalação pessoal.
- No PowerShell, em fonte já adquirida: `Get-FileHash -Algorithm SHA256 -LiteralPath '.blue-work/unova/sources/Pokemon_World_V18.zip'`. Em Linux: `sha256sum .blue-work/unova/sources/Pokemon_World_V18.zip`.
- As URLs externas podem mudar; páginas e hashes acima são ponto de partida, não garantia de download atual. Não faça scraping de páginas com restrição de acesso. Use fontes alternativas próprias se indisponíveis.

## 3. Mapa de código real a reaproveitar

| Componente existente | Responsabilidade / ação Codex |
|---|---|
| [scripts/install_game.py](../scripts/install_game.py) | Orquestrador Windows; inspecionar integração compartilhada Sinnoh, recover, compile, marcadores; adicionar Unova com staging transacional e rollback |
| [scripts/windows/Bootstrap.cs](../scripts/windows/Bootstrap.cs) | Blue-Story, estado de regiões e launcher; exibir estado Unova, progresso e erros sem travar |
| [scripts/android/update_client.py](../scripts/android/update_client.py) | Seleção paginada de releases, canal, manifests, compatibilidade de patches, hashes e preservação Sinnoh; estender preservação para Unova sem quebrar clientes |
| [scripts/regions/install_kanto.py](../scripts/regions/install_kanto.py) · [auto_integrate_kanto.py](../scripts/regions/auto_integrate_kanto.py) · [stage.py](../scripts/regions/stage.py) | Instalação, remap, ownership, recuperação de drift e migração; portar padrões em vez de copiar dados Kanto |
| [scripts/regions/qa_k00_migration.py](../scripts/regions/qa_k00_migration.py) · [release_gate.py](../scripts/regions/release_gate.py) | Padrões de fixture real, gates de release e proteção de arquivos |
| [RegionStart.rb](../scripts/battle_polish/RegionStart.rb) · [TitleKanto.rb](../scripts/battle_polish/TitleKanto.rb) | Novo Jogo, Continue, seleção de região, spawn e fluxo inicial. Não quebrar índices nativos |
| [Regions.rb](../scripts/battle_polish/Regions.rb) · [RegionTravel.rb](../scripts/battle_polish/RegionTravel.rb) · [RegionalPolicy.rb](../scripts/battle_polish/RegionalPolicy.rb) · [RegionalRespawn.rb](../scripts/battle_polish/RegionalRespawn.rb) | Registro, NPC de viagem, política HMs/insígnias, blackout e estado compartilhado |
| [unova-documentation.yml](../.github/workflows/unova-documentation.yml) | CI offline atual, regressão de contratos; manter evidência histórica e acrescentar estados nativos sem relaxar guardas |
| [blue-story-windows.yml](../.github/workflows/blue-story-windows.yml) · [android-multiregion.yml](../.github/workflows/android-multiregion.yml) · [android-updater-regression.yml](../.github/workflows/android-updater-regression.yml) | Publicação compartilhada e teste do cliente incremental |
| [kanto-pilot-check.yml](../.github/workflows/kanto-pilot-check.yml) · [regression.yml](../.github/workflows/regression.yml) | Padrões de smoke nativo, regressão PBS, Ruby, Windows/Linux e portal |
| [PR #334](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/334) · [PR #340](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/340) · [PR #366](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/366) | Exemplos reais de topologia Sinnoh, migração e gates Kanto. Inspecionar diffs e reaproveitar métodos, sem assumir igualdade de fontes |

Descobrir implementação Sinnoh compartilhada pelo import `sinnoh_shared` em install_game.py e busca local; não presumir caminho ou CLI. Examinar geradores, tilesets, probes nativos, atlas, catálogo QA, compiladores de música/encounters/trainers e instalador incremental por `git ls-files` e `rg`. Não copiar inteira a árvore de um piloto.

## 4. Execução otimizada: preflight e ciclo de trabalho

### 4.1 Comandos de entrada (shell do Codex)

```bash
git status --short
git fetch origin --prune
git rev-parse origin/main
git ls-files 'docs/UNOVA*' 'data/regions/unova*' 'scripts/*/*unova*' '.github/workflows/*'
gh pr view 195 --json state,mergeable,headRefOid,baseRefName,statusCheckRollup,url
gh pr view 208 --json state,headRefOid,url
gh run list --branch main --limit 20
gh release list --limit 30
rg -n 'UNOVA|sinnoh_shared|blue-sinnoh-shared|RegionalRespawn|RegionTravel' scripts data site
python -m unittest discover -s tests -p 'test_unova_*.py' -v
```

Se gh não estiver autenticado, usar conector GitHub ou Actions UI autorizado. Não pedir token no chat. Se a branch local tiver mudanças alheias, criar worktree/branch limpa sem apagar nada. Revalidar source contracts e CLI com `--help` quando suportado. Não disparar manualmente workflow que exija fonte privada sem autorização.

### 4.2 Lotes, dependências e caminho crítico

F01/F07 (aquisição e sprites) podem avançar independentemente em staging; F02/F03/F04/F05 dependem da identidade/reserva F01. **Primeiro entregar um corte vertical Nuvema → Accumula**, incluindo F02/F03/F05/F06/F07/F08/F09/F13/F14 somente para o recorte; não esperar todos os mapas para ter uma primeira experiência real. Depois ampliar por corredor de ginásio, sempre com portas, NPCs, encounters e testes no mesmo lote. Não publicar mapa desconectado como campanha pronta. Outros trabalhos podem preparar código interno em paralelo, mas só um lote perceptível ativo para merge/release de Unova e sem conflitar com outras regiões.

| Frente proposta | Entrega concreta / evidência mínima | Dependência |
|---|---|---|
| F01 | Inventário atual, direitos e remap revisados; relatório por fonte/mapa/asset, sem colisões | baseline |
| F02 | Cidades/localidades físicas, tiles e metadados | F01 |
| F03 | Routes 1–18, terrenos e acessos | F01 |
| F04 | Cavernas/torres/florestas/pontes/áreas aquáticas | F01 |
| F05 | Interiores, casas, laboratórios, centros, lojas, ginásios e andares | F01/F02 |
| F06 | Grafo físico, portas reversíveis, colisões, atlas e teleporte QA para todos os mapas instalados | F02–F05 por lote |
| F07 | Sprites, protagonista e NPCs com escala e áudio autorizado | fontes |
| F08 | Encontros, PBS, treinadores, itens e compilação nativa | F01/F06 |
| F09 | História, rivais, Plasma, flags e recompensas | F06–F08 |
| F10 | Oito ginásios, puzzles, líderes e insígnias | F09 por corredor |
| F11 | Victory Road, Elite Four, N, Zekrom, Ghetsis e créditos | F10 |
| F12 | Pós-jogo, lendários, atividades, Alder e revisitas | F11 |
| F13 | Novo Jogo, viagens, save, blackout e regras Blue (progressivamente desde piloto) | F06, F09 |
| F14 | Integração no instalador principal, QA, versões pareadas (por lote e final) | todos os critérios do lote |

### 4.3 Gate por PR e retomada

1. Ler issue/PR ativo, identificar exatamente HEAD/base/checks. Antes de código, declarar um objetivo observável e testes. Criar issue mestre de Unova se nenhuma existente cobrir execução nativa; referenciar os PRs antigos.
2. Implementar menor recorte que funcione, preservar interfaces, escrever testes negativos e manifesto, rodar testes dirigidos. Se novo bug, reproduzir antes de corrigir.
3. Executar suíte relevante e CI integral da HEAD; `gh pr checks NUMERO --watch` e `gh run view RUN_ID --log-failed`. Não marcar testes skip/cancelled como aprovados. Se ambiente não suportar watch, registrar IDs pendentes e retomar depois, sem alegar conclusão.
4. Conferir diff, ausência de assets restritos, revisão contra main atual, aprovar todos os checks obrigatórios. Só então merge pelo procedimento do repo. Se main mudou funcionalmente, revalidar.
5. Fixar SHA funcional S e executar Windows/Android a partir de S, sem misturar versões. Conferir artifacts, tags, manifests, digests e QA. Não iniciar novo lote perceptível enquanto releases ou gate crítico do lote atual falharem.
6. Atualizar registro de progresso e relatório, incluindo bloqueios ambientais e próximos comandos. Teste físico não disponível = BLOCKED_ENV, não PASS. Qualquer exceção de avanço por QA humana adiada precisa de autorização expressa e não promove 100%.

## 5. F01 — fontes, MapIDs e migração

- Reconciliar A04–A16: inspeção da PR #195, compatibilidade com main, recibos e checks; integrar somente se revisão e testes aprovados. A16 não reserva nada. A17 (proposta): aceitar evidências externas sanitizadas, conferir origem e revisão independente, sem autoaprovar direitos.
- Rodar auditores U02/E05/E06/SP03/SP04/A04–A14 já existentes sobre fonte e baseline reais. CLI: consultar os respectivos manuais e `--help`. Usar `RUN_UNOVA_MAPIDS.bat` apenas no ambiente apropriado, não no PC pessoal sem autorização. Se alterar dependências embutidas no BAT, regenerar bundle por ferramenta existente e rodar teste de integridade.
- Ler MapInfos atual, mapas físicos, manifests regionais, System, MapMetadata, MapConnections, portas, common events, mapas por script e spots Fly/respawn. Construir inventário de ownership e detectar duplicação, órfãos, referências estáticas/dinâmicas, diferenças em instalações Windows/Android.
- Reavaliar 518–599 e alternativas: Sinnoh cresceu depois do snapshot 648, Kanto também. Não usar faixa fixa por conveniência. Reservar quantidade suficiente para interiores/andares descobertos + expansão futura, com IDs estáveis e relatório de owner. Verificar Map001/MapID3, não criar mapa 3 vazio para passar.
- Mapear área simbólica → origem/autoria → MapID destino real → hash → tileset → portas → flags → estado. Permitir múltiplos MapIDs por área. Não renumerar os publicados ao inserir novos mapas. Manter registro versionado de ownership e tombstones para IDs removidos.
- Antes de migrar save antigo, testar baseline com save sintético em mapas de todas as regiões, inclusive Unova já instalada em releases futuras; manter mapa, posição, equipe, Box, itens, progresso, configuração e fallback válido. Proteger arquivos locais divergentes que não pertençam ao instalador.
- Direitos: per-asset allowlist; fonte ausente ou proibida -> criar arte/geometria original com design revisado. Não liberar payload até validar SHA, autoria e permissão de distribuição. Registrar faltas reais em vez de travar trabalho independente.
- Aceite F01: zero sobreposição entre owners, todas as referências a mapas afetados resolvidas ou bloqueadas com motivo, recibos revisados, rollback e plano de migração verificáveis.

## 6. F02–F07 — mundo físico, conexões e visual

### 6.1 Inventário obrigatório

Usar U03 (74 áreas), mas expandir em inventário físico por mapa. Incluir:
- Localidades: Nuvema, Accumula, Striaton, Nacrene, Castelia, Nimbasa, Driftveil, Mistralton, Icirrus, Opelucid, Pokémon League, Anville, Lacunosa, Undella e White Forest.
- Rotas 1–18; as orientais 11–15 pertencem ao pós-jogo, 17–18 ao corredor opcional aquático.
- Dreamyard, Wellspring Cave, Pinwheel Forest, Nacrene Museum, Skyarrow Bridge, Desert Resort, Relic Castle, Lostlorn Forest, Battle Subway, Driftveil Drawbridge, Cold Storage, Chargestone Cave, Celestial Tower, Mistralton Cave, Twist Mountain, Moor of Icirrus, Dragonspiral Tower, Tubeline Bridge, Victory Road, Elite Four Chambers, N's Castle, Giant Chasm, Village Bridge, Marvelous Bridge, Abyssal Ruins, Abundant Shrine, Challenger's Cave, P2 Laboratory, Liberty Garden, Royal Unova, Undella Bay, Unity Tower.
- Oito ginásios, todos os centros/lojas combinados, casas e prédios acessíveis, lab, quarto/térreo, casas Bianca/Cheren se acessíveis na referência, portões entre rotas, Day Care, estações, barcos, andares, escadas, elevadores, entradas de cavernas. Revisar catálogo para locais auxiliares e atividades omitidos (por exemplo Musical, estádio, shopping e pontes especiais) e registrar se são necessários para campanha ou 100% opcional.
- Cada mapa deve ter dimensões, 3 layers quando aplicável, tile/autotile, passabilidade, prioridade, terrain tags, borda, spawn, mapa pai, visuais, BGM, nome PT-BR, clima e portas reais. Preencher bordas sem vazios/recortes visuais. Validar ponte sobreposta, sombras, água e altura; transpor elementos 3D DS para 2D navegável sem alegar reprodução exata.

### 6.2 Conversão

1. Inspecionar referência e origem real por bytes; identificar mapa BW1 versus BW2/anime por geografia, nome, conexões, layout; ausência = MISSING.
2. Extrair apenas arquivos permitidos para staging; registrar tilesets e autotiles por identidade/hash. Não importar Scripts.rxdata v18, globais, PBS ou executáveis do doador.
3. Gerar mapa nativo compatível com RPG::Map, MapInfos e Tilesets atuais; para ausentes usar ferramentas de autoria já usadas em Sinnoh. Reusar tiles autorizados ou produzir originais. Definir portas/saídas por inspeção de geometria e caminhada real, não coordenadas arbitrárias.
4. Resolver metadata, graph directed/reciprocal e portais por map/event id. Testar BFS com terreno, prioridades, paredes, água, ledges, portas e NPCs; simular locks por flags, HM, insígnia. BFS offline é necessário mas não suficiente: prova de movimento pela engine também.
5. Testar ida/volta de cada entrada de interior, escadas, saída de caverna, portões, pontes, barco e puzzles; câmera sem faixas pretas, sem player preso. Criar atlas local e lista QA de todos os MapIDs efetivamente instalados, agrupados por cidade/rota/interior; não usar teleporte QA como caminho normal da história.
6. Sprite pack: selecionar Cheren, Bianca, Juniper, Hilbert/Hilda, N, Ghetsis, líderes, Plasma, treinadores e NPCs genéricos. Conferir 4×4, 16 quadros, pivô, pés, alpha, directions, proporção visível ao protagonista e NPCs Blue (referência SP05 altura 0,80–1,20, largura 0,80–1,25; complementar com screenshot nativo). Não alterar zoom global; não reaproveitar sprite de Gary como Cheren.
7. Música BlueMusic: ligar cues autorizadas a mapas/contexts, batalha, vitória, rival, Plasma, elite, créditos. Conferir formato e loop em Windows e JoiPlay; usar fallback existente autorizado ou faixa original quando fonte não liberada. Não incluir OST comercial sem autorização.

Aceite por mapa: mapa real abre no runtime, todas as entradas/saídas testadas, recursos presentes, colisões e spawn corretos, save/reload seguro, estado catalogado e hashes reproduzíveis. Incluir screenshot/log sanitizado de cada padrão de mapa e mapa crítico.

## 7. F08–F12 — implementação por corredor (U01–U32)

Cada linha abaixo significa um objetivo de gameplay, subdividível em PRs verticais menores. Registrar os IDs U existentes, não iniciar um segundo tracker que contradiga os anteriores. Todo lote inclui NPCs, portas, trainers, encounters, itens, diálogos PT-BR, música, metadata, flags, QA e publicação conforme escopo.

| Fase | Tarefas exatas | Aceite de gameplay |
|---|---|---|
| U01–U04 | F01: fonte, catálogo, direitos, MapIDs e dependências | Manifesto revisado, zero colisão |
| U05 | Converter primeiro mapa QA + tileset, spawn e interior | Game.exe abre e caminha, porta de ida/volta |
| U06 | Estado Unova versionado, flags, save, checkpoint e migração | Novo/antigo save, rollback e reentrada sem duplicação |
| U07 | Nuvema quarto/casa/lab, presente, Snivy/Tepig/Oshawott, Bianca/Cheren, mãe, Juniper/Pokédex, Route 1 captura, Accumula centro/praça, Plasma/Ghetsis, N e Route 2 | 13 eventos U07 instalados, 3 iniciais × variantes de rival; derrota inicial dos rivais permite avanço conforme contrato; N exige vitória; recompensas únicas; não sair para grama sem Pokémon |
| U08 | Route 2, Running Shoes conforme roteiro Blue, Striaton, Cilan/Chili/Cress por inicial, puzzle, Dreamyard/Munna/Fennel/Amanita, Cut | Trio 1x, primeira esmeralda, Cut regional, reentrada segura |
| U09 | Route 3, Day Care, Wellspring Cave, Cheren/Plasma, grama escura/duplas, itens | Depósito/retirada persistentes, resgate e retorno físico |
| U10 | Nacrene, museu, Lenora, roubo e recuperação do crânio no Pinwheel | Basic 1x, puzzle, acesso à ponte |
| U11 | Skyarrow Bridge, Castelia ruas/portos/interiores, Bianca/Iris/Plasma | Cidade navegável e história libera ginásio |
| U12 | Burgh, puzzle mel, Route 4, gates e rival | Insect 1x, deserto acessível |
| U13 | Desert Resort, Relic Castle, fósseis/areia, itens e revisitas | Escolha de fóssil não duplica; caminho reversível |
| U14 | Nimbasa, Bianca/N, Musical, atrações, bicicleta, Route16/Lostlorn | NPCs e atividades, bicicleta persistente |
| U15 | Elesa, montanha-russa, Route5/Alder, Driftveil Drawbridge | Bolt 1x; ponte abre sem prender |
| U16 | Driftveil, Cold Storage, Plasma, Clay, puzzle elevador | Quake 1x e saída correta |
| U17 | Route6, Chargestone Cave, cristais, N/Juniper | Cristais não bloqueiam retorno; cenas e encontros reais |
| U18 | Mistralton, aeroporto, Route7, Celestial Tower, sino e Skyla | Ida/volta e pré-requisitos do ginásio |
| U19 | Skyla, puzzle canhões, rival, Fly/Surf conforme referência e regra regional | Jet 1x, HMs obtidos no contexto correto e funcionamento local |
| U20 | Mistralton Cave, Cobalion, Routes17–18, P2 Laboratory, Larvesta, correnteza, Waterfall conforme fonte | Exploração aquática, ovo/recompensa única, sem bypass da história |
| U21 | Twist Mountain, neve/estações, Icirrus, Route8 e Moor | Todas as variantes sazonais com caminho e retorno válidos |
| U22 | Brycen, puzzle gelo, Dragonspiral Tower, Plasma/N | Freeze 1x, cenas e flags persistentes |
| U23 | Relic Castle II, pedra da versão White, Ghetsis, Tubeline Bridge/Route9 | Dark Stone e eventos corretos de White, não misturar Black |
| U24 | Opelucid, Iris, puzzle dragão, Master Ball | Legend 1x, oito insígnias locais e acesso Liga |
| U25 | Route10, Cheren/Bianca, portões por insígnia, Victory Road | Gate 8/8 local, caverna sem softlock, centro Liga |
| U26 | Shauntal, Grimsley, Caitlin, Marshal e salas | 24 ordens válidas (teste de estado), quatro vitórias únicas, retry/blackout e save reais |
| U27 | Castelo de N, libertação do dragão, captura Zekrom, N, Ghetsis, créditos | Captura/derrota/PC cheio/reentrada seguros, final único e pós-jogo desbloqueado |
| U28 | Looker, seis sábios restantes, TMs/recompensas | Cada missão única; revisita e persistência |
| U29 | Routes11–15, Lacunosa, Undella, Cynthia, Giant Chasm, Village/Marvelous Bridge, White Forest/Undella Bay | Leste explorável a pé/água, encontros pós-jogo e gates |
| U30 | Kyurem, mosqueteiros, Thundurus White e outros condicionados a versão, Landorus, Volcarona, Abundant Shrine, Abyssal Ruins, Subway, Anville, Royal Unova, Challenger's Cave, Liberty Garden/Unity Tower | Lendários únicos, atividades jogáveis, equivalente offline aprovado quando rede antiga inviável; não contar conteúdo inacessível como completo |
| U31 | Elite/Alder, revanches, Trainer Card, Pokédex/atlas, placas/PT-BR, áudio, guias e tarefas opcionais pendentes | Nenhum conteúdo obrigatório ausente; distinção entre White e extras |
| U32 | Integração final compartilhada, migração, instalação limpa, patches, releases e QA | Gates da seção 11 integralmente aprovados |

### 7.1 PBS, encontros e batalhas

- Catalogar treinadores por MapID/evento estável, trainer type, nome, versão, time de referência, níveis, golpes, habilidade, itens e recompensas. Usar fonte White rastreável; validar espécie/forma/ID, evitar colisões com Full Power ou Journey de Decades. Não reutilizar IDs de Kanto (Gary etc.). Criar namespace UNOVA para identidade do evento/trainer quando compatível.
- Rivais: Snivy → Cheren Tepig/Bianca Oshawott; Tepig → Cheren Oshawott/Bianca Snivy; Oshawott → Cheren Snivy/Bianca Tepig. Usar contratos U07/G03 e equipe conforme capítulo, não randomizar chefes. Três líderes Striaton selecionados pelo inicial; só uma Trio Badge.
- Encontros: mapear cada área física para método nativo suportado (Land, Cave, Water, rods, RockSmash e variantes verificadas). Preservar slots/probabilidades, diferenças White, horário e estação; implementar grama escura, shaking grass, dust cloud, rippling water quando aplicáveis ao recorte e suportados pelo motor; se precisar adaptar, documentar equivalência. Validar taxas totais, ausência de duplicatas, espécies existentes, nível min/max, compatibilidade com evolução e level cap. Campos desconhecidos ficam pendentes até fonte confirmada ou decisão autoral explicitamente aprovada, não silenciosamente inventados.
- Compilar PBS de trainers, encounters, itens, metadata e tipos pela engine atual em cópia isolada; conferir dados compilados, GameData e carregamento real. Não sobrescrever base global a partir do pack. Testar batalha simples/dupla, perder, fugir quando permitido, vitória, recompensa, rematch e save/reload.
- Dificuldade: respeitar regra Blue atual Normal 70% / Master 90% do maior nível elegível; preservar regras especiais de líderes, Elite, Campeões e chefes autorais. Evolução dinâmica existente: nível +5, pedra >=30, troca >=40, felicidade >=45, consultar implementação atual para chances, caps e exclusões. Não criar novo balanceamento incompatível. XP party ligado, Dynamax off, outras mecânicas conforme configuração Blue.
- Itens: obter/consumir uma vez, inventário cheio e falha de compra tratados; fósseis, presentes, TMs, HMs, pesca, mochila, dinheiro, bicicleta, creche e NPCs comerciais. Testar compras/vendas, cura, PC e respawn.

### 7.2 História, flags e eventos

Usar contratos G01/G02 como especificação, implementar em Ruby/ev commands e estado persistido pela API nativa em vez de copiar simulador Python para gameplay. Mapear symbolic event key → MapID/event ID/página → pré-condição → efeito → resultado. Namespaces por região; recompensa e batalha devem ser transacionais/idempotentes; failure ou perda não marca vitória. Aceitar reentrada em capítulos concluídos sem repetir itens/cenas. Testar save antes/depois de cada evento crítico, derrota/retry, voltar a mapa anterior e viajar para outra região. Nenhum softlock causado por evento autorun, NPC em porta ou escolha cancelada.

## 8. F13 — região compartilhada, saves e regras globais

- Atualizar registro regional apenas quando instalação validada e spawn real. Novo Jogo deve permitir Unova no mesmo Game.exe, escolha Hilbert/Hilda e nome, quarto, inicial. Continue deve preservar save existente, sem alterar seleção original de Decades ou reabrir a seleção após viagem.
- Agente Regional físico em Nuvema, conectado aos agentes das cidades iniciais de Decades, Kanto, Johto, Hoenn e Sinnoh instaladas. Não exigir Liga para viajar se regra vigente permite desde o início; preservar pré-condições seguras e não viajar durante evento/batalha. Menu de pausa normal informa destinos; teleporte somente em QA.
- Ao trocar, seguir implementação atual de depósito do time no Box, sem perder Pokémon quando Box cheio, preservando regra de sobrevivência e rollback. Compartilhar dinheiro, TMs, itens comuns e Boxes conforme política. HMs e key items locais inclusive no PC, restaurar ao retornar; Fly só para pontos autorizados da região. Badge local e espécie compatível + HM local obrigatórios para ações de campo.
- Oito badges TRIO/BASIC/INSECT/BOLT/QUAKE/JET/FREEZE/LEGEND; uma esmeralda por conquista; especiais seguem trava regional de oito, não contar badges de outra região. Manter Trainer Card e guia consistentes.
- Blackout retorna ao Centro Pokémon mais recente de Unova, fallback seguro para Nuvema (ponto de cura inicial real, não inventar Centro inexistente na referência). Nenhum retorno a outra região por checkpoint antigo.
- Testar todos os pares ida/volta disponíveis, fresh/legacy save, time cheio/Box cheio, HM local/estrangeiro, badge local/estrangeira, estado de história, fail/rollback e retomada. Proteger também saves que estejam dentro de Unova durante atualização.
- Menu **Testar Unova** e teleporte QA para cada MapID instalado, catálogo agrupado e busca. Não permitir debug/teleporte burlar campanha normal. Mostrar revisão funcional e horário de build dentro do jogo; não confundir SHA do launcher com SHA efetivamente instalado/compilado.

## 9. Windows — integrar ao Blue-Story.exe principal

1. Descobrir a chamada de integração Sinnoh/Kanto em install_game.py e o contrato de manifestos/recovery. Adicionar módulo Unova (nome proposto), com preflight de fonte, direitos, hashes, ownership, espaço e versões. O launcher não deve depender de um piloto externo permanente.
2. Gerar overlay somente de arquivos novos/alterados, map entries adicionadas sem substituir globais, plugins e PBS namespaced, recursos licenciados. Usar staging em diretório separado; proteger origem, Game.exe, saves, outras regiões e configurações. Verificar antes/depois e commit transacional; em falha, recuperar somente arquivos afetados. Não apagar mapa/saves para contornar drift.
3. Integrar estado de instalação em Bootstrap.cs, com etapa visível (fonte/auditoria/mapas/compilação/validação), mensagem de erro e log; prevenir travamento, segunda execução idempotente, release antiga e migrações por cadeia. Usar compilação já existente; testar cache e GameData.
4. Validar em runner Windows autorizado: instalação limpa, atualização de versão anterior, migração antiga de múltiplas regiões, interrupção, disco insuficiente, arquivo corrompido/estrangeiro, falta de fonte, rollback, retry, launch real, Novo Jogo/Continue, viagem e save. Não tocar PC pessoal.
5. Usar workflow existente [blue-story-windows.yml](../.github/workflows/blue-story-windows.yml), depois conferir tag battle-hub-*, asset Blue-Story.exe, manifestos e hash. O EXE é launcher, não presumir que contém o jogo. Verificar SHA efetivamente sincronizado e compilado.
6. Entregar link exato do asset da release aprovada. Não usar releases/latest indiscriminadamente se apontar para revisão de outro canal. Caso distribuição exija fonte local autorizada, explicar pré-requisito sem incluir pacote proibido.

## 10. Android — integração multirregional e atualização incremental

1. Inspecionar workflow [android-multiregion.yml](../.github/workflows/android-multiregion.yml) e cliente [update_client.py](../scripts/android/update_client.py). Integrar o mesmo conjunto de mapas, plugins/PBS e metadata de Windows a partir da mesma revisão funcional. Compilar dados conforme pipeline Android atual; não depender de JSON/plugin ausente no JoiPlay sem fallback seguro.
2. Manter canal **multiregion** e nomes atuais (historicamente Blue-Android-Decades-Kanto-Hoenn.zip, conferir os nomes reais no workflow). Não misturar Hub ou piloto kanto-android-*; não alterar canal só para fazer patch aceitar.
3. Gerar manifesto com versão, revisão, arquivo, tamanho, hash, caminho, lista de adições/alterações/remoções permitidas. Manter preservação das regiões anteriores e adicionar guardas para Unova em saves compartilhados; impedir remoção de mapa ocupado. Conferir compatibilidade de patch para baselines publicadas, paginação, cadeia de atualização e idempotência.
4. **Sem backup completo automático e sem download integral automático para atualizar.** Delta somente arquivos efetivamente alterados, staging temporário e reversão limitada aos arquivos tocados conforme mecanismo atual; nunca incluir saves. Se não existir delta compatível, publicar delta/cadeia verificada; instalação integral somente com consentimento explícito. Instalação limpa pode usar pacote integral autorizado.
5. Testar workflow [android-updater-regression.yml](../.github/workflows/android-updater-regression.yml): falta de espaço, rede interrompida, patch inválido, hash errado, versão errada, arquivo local estrangeiro, falha parcial, retry, preservação de saves, nome/case UTF-8 e sem backup total. Verificar hash final de todos os arquivos, não apenas do ZIP.
6. Teste real Android autorizado: instalar JoiPlay e RPG Maker plugin da [fonte oficial](https://joiplay.net/), registrar versões, Android/dispositivo, abrir o Game.exe da pasta atual pelo JoiPlay. Testar fresh/continue, controle virtual, áudio, movimento, encontros, eventos, transições, blackout, save/reload, viagens e mapa que estava ocupado durante update. Emulador compatível pode fornecer evidência separada, não substituir aparelho real sem aprovação.
7. No Termux, após fechar JoiPlay, entrar **na pasta real** do jogo; não inventar caminho de armazenamento:

```sh
pkg install python
# Se necessário, conceder acesso ao armazenamento pelo fluxo normal do Termux.
# cd para a pasta real que contém Game.exe e ATUALIZAR-ANDROID.py
pwd
ls Game.exe ATUALIZAR-ANDROID.py Data/blue-update.json
python ATUALIZAR-ANDROID.py
python ATUALIZAR-ANDROID.py --update
```

Conferir Data/blue-update.json, revisão in-game, canal, quantidade de MapIDs, hashes do manifesto e abertura JoiPlay. Não editar marcador de versão. Se falhar, registrar saída sanitizada e corrigir o delta. Testar a segunda execução e confirmar que não baixou pacote completo.

### 10.1 Pareamento das duas releases

Consultar `gh workflow view blue-story-windows.yml --yaml` e `gh workflow view android-multiregion.yml --yaml` para conferir triggers/inputs reais. Se os workflows aceitarem dispatch, usar os argumentos documentados e SHA/ref permitido. Exemplo de inspeção, não inventar inputs:

```bash
gh run list --workflow blue-story-windows.yml --limit 10
gh run list --workflow android-multiregion.yml --limit 10
gh run view RUN_ID --json headSha,status,conclusion,url,jobs
gh release view TAG --json tagName,targetCommitish,assets,url
# Substituir TAG e nome de asset por valores reais verificados:
gh release download TAG --pattern 'Blue-Story.exe' --dir .blue-work/unova/release-check
```

Checar `headSha`, `targetCommitish` e revisão dentro do manifesto; ambos precisam apontar ao mesmo S. Se workflow só construir main e esta já avançou funcionalmente, revalidar novo S e reconstruir par conforme roadmap. Baixar assets autorizados para staging, SHA-256 comparado ao manifesto e digest de release quando disponível; conferir ZIP, manifest e patches associados. Se só um canal publicado, estado BLOCKED_RELEASE. Não publicar save, fonte doadora ou arquivo restrito.

## 11. Testes, CI e critérios finais

### 11.1 Teste rápido local (existente)

```bash
python -m unittest discover -s tests -p 'test_unova_*.py' -v
python -m unittest discover -s tests -v
ruby -c scripts/battle_polish/RegionStart.rb
ruby -c scripts/battle_polish/RegionTravel.rb
ruby tests/region_start_runtime.rb scripts/battle_polish/RegionStart.rb
ruby tests/region_travel_runtime.rb tests/regions_data_fixture.rb scripts/battle_polish/Regions.rb scripts/battle_polish/RegionTravel.rb
# Portal: entrar em site/, instalar dependências pelo lockfile, rodar scripts definidos no package.json.
```

Os comandos Ruby usam stubs/test harness e não provam Game.exe. Conferir sintaxe de todos os scripts novos, e executar testes específicos de regressão do updater, instaladores, música, mapa, PBS, portal e Chromium conforme workflow. Não ignorar falha preexistente; registrar baseline e tratar de modo isolado.

### 11.2 CI nativa proposta (reutilizar o existente antes de criar)

Adicionar workflow Unova nativo (nome proposto `unova-native-check.yml`) quando houver pipeline real: job Linux rápido para contratos/remap e testes negativos; Windows com baseline autorizado, staging e Game.exe real; job Android build/patch e validação de pacote; regressão global. JoiPlay físico é gate separado. Não ativar segredo de fonte em PR não confiável. Runner sem fonte/licença marca BLOCKED, não verde falso. Reutilizar harness/probes de Kanto/Sinnoh e coletar logs de engine, MapID, coordenadas, GameData, estado before/after e resultados reais. Marcadores **propostos**, só emitir após asserts no runtime:
- UNOVA_NATIVE_MAP_INSTALL_OK / UNOVA_NATIVE_PHYSICAL_NETWORK_OK
- UNOVA_NATIVE_U07_STARTERS_RIVALS_SAVE_RELOAD_OK
- UNOVA_NATIVE_ENCOUNTERS_TRAINERS_PBS_OK
- UNOVA_NATIVE_GYM_BADGES_HM_OK / UNOVA_NATIVE_LEAGUE_FINALE_OK
- UNOVA_NATIVE_POSTGAME_OK / UNOVA_NATIVE_REGIONAL_TRAVEL_BLACKOUT_OK
- UNOVA_NATIVE_MIGRATION_ROLLBACK_OK / UNOVA_WINDOWS_RELEASE_VERIFIED / UNOVA_ANDROID_PATCH_VERIFIED
- UNOVA_ANDROID_JOIPLAY_DEVICE_QA_OK (somente após recibo do dispositivo)
Não contar string impressa isoladamente como teste; relatório estruturado deve provar preconditions, ações, asserts, revisão e versão.

### 11.3 Matriz de aceite (cada linha, ambas plataformas quando aplicável)

| ID | Evidência obrigatória |
|---|---|
| Q01 | Inventário 100% dos MapIDs físicos aprovados do escopo, fontes/direitos, hashes, sem colisões/órfãos |
| Q02 | Todos os portais, portas, rotas, retornos e checkpoints físicos; sem teleporte QA para completar história |
| Q03 | Sprites/escala/colisões/áudio, nomes e diálogos PT-BR; nenhuma referência ausente |
| Q04 | Novo Jogo três iniciais, Hilbert/Hilda, nome, rivais, N; todas variantes e derrota/retry conforme contratos |
| Q05 | Todos os encontros, treinadores, itens, probabilidades e PBS compilados/validados |
| Q06 | Oito ginásios, puzzles, 8 insígnias e 8 esmeraldas únicas, Trainer Card e gates |
| Q07 | Elite Four qualquer ordem, Castelo de N, Zekrom, Ghetsis, créditos, loss/retry/save |
| Q08 | Pós-jogo, seis sábios, White Forest, lendários, atividades, Alder e demais áreas aceitas |
| Q09 | HMs e key items locais, Bag/PC/Box/dinheiro/TMs, viagem entre todas as regiões instaladas e blackout local |
| Q10 | Fresh/legacy save, posições em cada região, migração, rollback, reentrada, flags, versão in-game |
| Q11 | Windows Game.exe real: instalação limpa, update, abertura, campanha e regressão |
| Q12 | Android/JoiPlay real: versão/plugin, controles, áudio, campanha, update somente delta, save/reload |
| Q13 | Dois canais publicados mesmo SHA, manifests/assets/hashes/patches verificados, nenhum material proibido |
| Q14 | Regressão integral de Decades, Kanto, Johto, Hoenn e Sinnoh, portal e Blue Studio |
| Q15 | Revisão humana visual/gameplay e aceite final, nenhuma pendência bloqueante; escopo offline de eventos antigos aprovado |

Testes negativos: tentar entrar sem inicial, obter item duas vezes, vencer sem batalha, abrir HM estrangeiro, entrar em Liga com 7 badges locais e badges de outra região, viajar durante evento, Box cheio, perda contra N/Ghetsis, PC cheio ao capturar lendário, retornar para mapa não instalado, update interrompido, hash errado, colisão de ID, origem/rights inválidos, ausência de recurso, save antigo em mapa afetado. Cada teste deve observar comportamento esperado e ausência de alteração não autorizada.

## 12. Progresso e artefatos de retomada

- Manter G 32/32 como histórico. Barra A 0/8 e U 0/32 só aumentam por evidência nativa prevista; não promover por documentação.
- Criar manifest/progresso nativo (proposto `data/regions/unova-native-progress.json`) com area_key, map_ids, sources, owner, status, evidence, U/F e dependências. Campos desconhecidos = null/blocked, nunca true por falta de dados.
- Medir separadamente: mapas físicos instalados / total físico aprovado (denominador fechado após F01); áreas completas / escopo 74+ revisado; conexões testadas / total; eventos/treinadores/encounters/músicas aceitos; fases U; QA Windows; QA Android. Não somar mapas preview aos instalados nem atribuir peso de tempo sem estimativa.
- Estados: PLANNED, SOURCE_AUDITED, QA_CONVERTED, NATIVE_TESTED, INTEGRATED_MAIN, PUBLISHED_BOTH, ACCEPTED, BLOCKED_SOURCE, BLOCKED_RIGHTS, BLOCKED_ENV, BLOCKED_RELEASE. Evidência de plataforma separada, não promoção automática. Status regional público planned até piloto efetivamente instalado e verificado; depois prototype/early access se permitido e escopo explícito; playable/complete só após aceite.
- Um recibo sanitizado por lote: schema, timestamp, PR, head/base SHA, workflow run/job IDs, arquivos alterados, MapIDs instalados, referências de origem/autorização, hashes, resultados de testes nativos e sintéticos separados, QA físico, versão Windows/Android/asset/patch e links, regressões, pendências e próxima tarefa. Não enviar saves pessoais, logs com secrets ou binários restritos.
- Atualizar site e README quando houver mudança de status real; preservar documentação histórica como histórica.

## 13. Primeira tarefa executável (copiar para Codex)

```text
Leia docs/UNOVA_ROADMAP_CODEX_100_JOGAVEL_WINDOWS_ANDROID.md e AGENTS.md se existir.
Trabalhe no repositório GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal.
Comece rechecando main, PR #195/A16 e PR #208; preserve trabalho de Kanto/Sinnoh.
Não crie mais simuladores de sistemas já concluídos em G01–G08.
Execute F01: baseline real atual de MapInfos/ownership de todas as regiões, fontes
autorizadas, inventário físico de Nuvema/Route1/Accumula, remap estável e direitos.
Use World V18 apenas como candidato de geometria auditada (64 mapas, zero eventos);
se faltar fonte ou licença, crie mapas/recursos originais em QA e registre bloqueios.
Reaproveite os conversores, staging, tilesets e probes nativos existentes de Sinnoh/Kanto.
Implemente o menor piloto vertical: quarto/casa/lab/cidade de Nuvema, Route1,
Accumula e interiores necessários; conecte portas e caminhos físicos, NPCs,
três iniciais, Bianca/Cheren, Juniper, N, encontros e bloqueios, save/reload,
blackout local e opção Testar Unova em QA. Não simule mapa instalado.
Execute testes de contrato, regressões e Game.exe em ambiente Windows autorizado.
Se aprovado, integre ao mesmo jogo principal com saves/MapIDs estáveis,
NPC regional, versão in-game, instalador Blue-Story e Android multirregional.
Crie/atualize a issue mestre e manifestos com evidências e gates.
Faça merge somente após todos checks obrigatórios verdes na HEAD/base corretas;
cada lote perceptível exige Windows + Android do mesmo SHA, assets/hashes/patches
verificados, sem backup integral automático e sem apagar saves.
Se JoiPlay físico ou direitos faltarem, registre bloqueio específico sem falsificar
aceite. Prossiga somente conforme gates e autorização do mantenedor.
Depois amplie U08–U32 em lotes verticais, seguindo a ordem deste documento.
Priorize implementação e workflows; relato mínimo, com links e próxima tarefa.
```

**Fim do plano:** Unova só estará 100% jogável após U01–U32 e Q01–Q15 aprovados com evidência verificável. Publicar um instalador, contar áreas simbólicas ou executar testes de fixtures não é suficiente.
