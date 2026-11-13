# Johto — plano passo a passo para implementar a região no Blue Dessastre Paradoxal

**Projeto:** [Pokémon Blue: Dessastre Paradoxal](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal)  
**Atualizado em:** 12/11/2026  
**Tipo:** especificação operacional por fases, pronta para implementação incremental no GitHub  
**Situação inicial:** Johto consta no catálogo regional, mas está marcada como **planned** e não possui mapas integrados versionados no repositório. **Este documento não implementa Johto nem comprova execução dos testes.**  
**Objetivo final:** campanha HG/SS de Johto jogável no mesmo projeto/sistema de saves do Decades, com mapas, eventos, treinadores, músicas, ginásios, Liga, encontros, Pokédex, viagens e QA de verdade.

> **Princípio absoluto:** preservar Decades e a Kanto já instalada. Importar Johto como conteúdo regional, **não** como outro jogo, outra Pokédex, outra engine de batalha ou substituição do diretório game/Data.

## 0. Documentos de referência e estado real

Consultar **antes de cada fase**:

1. [Plano multirregional v2](PLANO_REGIOES_DESSASTRE_V2.md) — regras definitivas de progressão, versões fundidas, viagens, equipes, especiais e pós-jogo.
2. [Estudo de fangames por região](ESTUDO_FANGAME_TODAS_AS_REGIOES_POKEMON.md) — lista de referências e auditoria de proveniência.
3. [Circuito regional](CIRCUITO_REGIONAL.md) — arquitetura atual e procedimento seguro da fonte FRLG.
4. [Kanto: fases e duas barras](KANTO_ETAPAS.md) — distinção entre funcionalidade e aceite real.
5. [Kanto: instalação](KANTO_ESCOLHA_REGIAO.md), [viagem regional](KANTO_VIAGEM_DEC_KANTO.md) e [balanceamento/cartões](KANTO_BALANCEAMENTO_PALLET_CARTOES_REGIONAIS.md).
6. [Plano musical de Kanto](KANTO_PLANO_APLICAR_MUSICAS.md) — aplicar somente os conceitos, nunca reaproveitar músicas/mapas de Kanto como se fossem Johto.
7. [Testes E2E de Kanto](KANTO_CODEX_TESTES_E2E.md) — padrão de evidências de execução no Game.exe real.

**Inspeção confirmada na main em 12/11/2026:**

- A região **JOHTO** já existe em [site/public/data/regions.json](../site/public/data/regions.json), com base HeartGold/SoulSilver, complemento Crystal e oito insígnias: ZEPHYR, HIVE, PLAIN, FOG, STORM, MINERAL, GLACIER, RISING. Seu status é planned.
- [scripts/battle_polish/Regions.rb](../scripts/battle_polish/Regions.rb) já conhece as regiões, desbloqueios, conquistas locais e total mundial.
- [RegionStart.rb](../scripts/battle_polish/RegionStart.rb) **só libera início em Decades e Kanto** e procura marcador de Kanto.
- [RegionTravel.rb](../scripts/battle_polish/RegionTravel.rb) **só tem destinos implementados para Decades/Kanto**, com detecção de instalação presa aos marcadores de Kanto.
- [audit.py](../scripts/regions/audit.py), [stage.py](../scripts/regions/stage.py), [pilot.py](../scripts/regions/pilot.py) e [install_kanto.py](../scripts/regions/install_kanto.py) são **Kanto-específicos** e não devem ser apenas renomeados ou usados diretamente contra a fonte de Johto.
- [BlueMusic.rb](../scripts/music/BlueMusic.rb) e [compile_kanto_music.py](../scripts/music/compile_kanto_music.py) têm adaptação regional de Kanto; exigir novo catálogo e isolamento para Johto.
- **Início da implementação (12/11/2026):** [docs/JOHTO_ETAPAS.md](JOHTO_ETAPAS.md) acompanha o progresso. Já existem **data/regions/johto-source.json** (importação bloqueada), **scripts/regions/audit_johto.py** (auditoria somente leitura) e **tests/test_johto_source_audit.py** (testes sintéticos). **Não existem** ainda instalador/piloto jogável, mapa de New Bark integrado ou fonte original local auditada; não confundir auditoria preparatória com região instalada.

### 0.1. Regra prioritária de compatibilidade — NUNCA quebrar o projeto existente

**Referência obrigatória:** [análise das fontes, proteção contra regressões e botão Testar Johto](JOHTO_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md), seções 2.1 e 2.2.

**Contrato para todas as 16 etapas:**

1. Toda mudança deve ser **aditiva, regionalizada, reversível e testada**; Decades, Kanto, Blue Studio, portal, batalhas, áudio, saves e jogos já publicados não podem sofrer regressões por causa de Johto.
2. **Antes de mexer:** guardar hashes/baseline de mapas, IDs, plugins, áudio e saves de teste; executar as suítes de regressão existentes. **Depois:** repetir exatamente as mesmas verificações, registrar diferenças justificadas e bloquear publicação em caso de falha.
3. **Não substituir** `MapInfos.rxdata`, `Tilesets.rxdata`, `Scripts.rxdata`, `System.rxdata`, todo `game/Data`, o executável ou o perfil de saves com arquivos de outro jogo. Usar MapIDs livres, remap explícito de origem→destino, hashes, backups e rollback.
4. Generalizar componentes de Kanto com interfaces **retrocompatíveis**; jamais remover uma opção, hook, classe, regra, preferência de música ou evento de Kanto/Decades para favorecer Johto. Criar novos testes de contrato antes de mudar comportamentos compartilhados.
5. Compilar Johto em **cópia isolada** e save próprio. Só disponibilizar Nova Partida em Johto quando New Bark e introdução estiverem comprovadas; só disponibilizar viagem se a Liga e o destino instalado satisfizerem as condições.
6. Nenhum teste estrutural/headless ou presença de botão permite elevar a Barra 2 de aceitação integral; documentar evidência real e os bloqueios.

### 0.2. Menu inicial do mesmo Game.exe: Testar Kanto + Testar Johto

A opção **`Testar Johto` foi adicionada ao mesmo menu onde já existe `Testar Kanto`**, por `scripts/battle_polish/TitleKanto.rb`, sem mexer nos índices retornados ao carregador de saves Essentials/Auto Multi Save. A ordem na instalação principal é **Continuar (quando existir) → Novo Jogo → Testar Kanto → Testar Johto → demais comandos originais**.

- `Testar Kanto` mantém seu lançador `KANTO_JOGAR_EXPERIMENTAL.bat`, mapas e saves separados.
- `Testar Johto` procura **seu próprio** `JOHTO_JOGAR_EXPERIMENTAL.bat` e `scripts/regions/pilot_johto.py` (ambos **a implementar**); na ausência, apresenta **Johto ainda está em preparação** e retorna ao menu sem alterar nada.
- Ao disponibilizar o piloto, construir uma **cópia isolada Johto** e perfil de save diferente dos de Kanto e Decades. Nunca abrir o piloto de Kanto como fallback.
- Nenhum dos dois botões deve aparecer dentro de pilotos isolados (evitar lançamentos recursivos). O Game.exe principal, seus saves e seus comandos `New Game`, `Continue`, `Mystery Gift`, `Options` e `Quit Game` permanecem nativos.
- A suíte `tests/title_kanto_runtime.rb` deve validar a **terceira** e a **quarta** opções, a tradução para índices originais, setas de slots, isolamento e caminhos autorizados dos dois lançadores. `tests/test_title_kanto.py` mantém a integração com os testes Python.

**Estado atual:** botão e proteção de fallback são código implementado; **piloto de Johto, mapas e lançador ainda não estão implementados**. Não interpretar este ajuste de interface como conclusão das Etapas 01–16.

### 0.3. Início da implementação e leitura do progresso

**Registro de execução:** [JOHTO_ETAPAS.md](JOHTO_ETAPAS.md). As Etapas 01 e 02 estão parcialmente implementadas; duas barras permanecem **0/16** até satisfazerem seus respectivos critérios.

**Ferramenta já existente:** scripts/regions/audit_johto.py. Essa auditoria aceita --source, --game, --archive e --output, valida IDs e hashes e produz JSON somente em .blue-work/. Não faz download, não instala nem executa scripts de terceiros. O arquivo de origem distribuído externamente ainda é requisito para uma auditoria real. O comando sem a fonte deve falhar de modo explícito, não marcar a etapa como aprovada.

## 1. Decisão das fontes e direitos

| Tipo | Fonte prioritária | Utilização permitida no plano |
|---|---|---|
| Geometria RMXP editável | [Remastered Kanto and Johto Overworld and Caves Map Pack](https://eeveeexpo.com/resources/828/), AenaonDogsky/AenaonDusky | Avaliar mapa, passabilidade, conexões e tilesets; importar localmente somente sob condições da fonte e dos autores dos recursos. |
| Jogo da lista estudada | [Pokémon Grueling Gold](https://www.eeveeexpo.com/threads/7771/) | Referência secundária da jornada de Johto, **não** pressupor que o jogo forneça arquivos editáveis nem autorização de cópia. |
| Geografia, eventos e treinadores canônicos | Pokémon HeartGold + SoulSilver | Base da campanha; fundir conteúdo exclusivo sem duplicar treinadores/insígnias. |
| Conteúdo complementar | Pokémon Crystal | Eventos adicionais auditados, por exemplo Suicune, quando compatíveis com a cronologia escolhida. |
| Música de referência | Repertório de Pokémon HeartGold / SoulSilver | Identificar tema de cada mapa, chefe e cena; só instalar **áudio com direitos de uso/distribuição verificados**. |

**Observações verificáveis sobre o Map Pack:** o criador descreve overworld de Johto conectado e cavernas, mas **excetua Mt. Silver**; oferece tiles de estilo HGSS; mapas opcionais beta e ausências de portas/eventos não equivalem a conteúdo narrativo pronto. Para projeto já existente, o autor alerta expressamente para **não copiar MapInfos.rxdata** e **recriar conexões locais**, porque seus tilesets e MapIDs podem conflitar. O pacote traz remixes FRLG para **Kanto**, não uma trilha de Johto pronta. Ver [página da fonte](https://eeveeexpo.com/resources/828/) e [atualizações da fonte](https://eeveeexpo.com/resources/828/updates).

**Obrigatório antes de distribuir:** inventariar licenças, créditos exigidos (incluindo JohtoBlaziken, Earthescape/Orbitender, AenaonDusky e autores de tiles), direitos de cada asset, uso público/local e prova da autorização. A permissão para editar mapas de um recurso não transfere automaticamente os direitos das artes, composições ou gravações de terceiros. **Não subir ROMs, OST comercial ou ZIP de outros autores ao GitHub sem autorização apropriada.**

## 2. Regras de gameplay imutáveis

1. **Nova partida:** Johto deve iniciar no **quarto da casa do jogador em New Bark Town**, não no meio da rua; casa, escada, porta e retorno precisam funcionar. Introdução e escolha de inicial (Chikorita, Cyndaquil, Totodile), Elm, mãe, ovo/eventos e rival devem ser contextualizados conforme a campanha adotada.
2. **Regiões:** ao concluir a Liga Johto pela primeira vez, liberar **Kanto + Hoenn**, com guarda para mapas ainda não instalados; de Kanto, acesso a Johto somente se desbloqueado. NPC de transporte em **New Bark Town**, visível quando a viagem estiver autorizada; ao voltar à região, chegar à cidade, não no quarto inicial.
3. **Mesmo save:** conservar a party, PC, itens, dinheiro, Pokédex, quests, modos e conquistas. Nunca criar um segundo banco de espécies nem copiar Scripts.rxdata da fonte.
4. **Insígnia = uma esmeralda global:** cada insígnia **única de Johto** contribui exatamente uma vez para o total de esmeraldas usado pelo Blue, sem segunda fórmula nem recompensa duplicada. Oito insígnias locais controlam as regras próprias daquela região; não usar total mundial no lugar das oito locais.
5. **Balanceamento:** preservar os treinadores e encontros canônicos como **dados-base** e chamar o escalonamento nativo do Blue no momento da luta. Faixas documentadas: 0–1 esmeralda, BST até 350; 2–4, BST até 450; 5–10, até 540; 11+, Master sem teto de BST, adversário em torno de 90% do maior nível da party; fases anteriores usam 70% e encontros selvagens 45%, conforme [documento do balanceamento](KANTO_BALANCEAMENTO_PALLET_CARTOES_REGIONAIS.md). Não hardcodar níveis HGSS como dificuldade final, nem duplicar essa lógica.
6. **Master:** preservar a diretriz de treinadores com time reforçado e cobertura de fraquezas, verificando o adaptador real da campanha. Não alterar o time-base canônico do banco de origem.
7. **Dois cartões de treinador:** uma página com insígnias de Johto (região atual), outra com todas as regiões e total mundial, seguindo [RegionalCards.rb](../scripts/battle_polish/RegionalCards.rb).
8. **HMs locais:** usar o catálogo existente em site/public/data/regions.json e confirmar os eventos HGSS correspondentes, inclusive ROCK_SMASH/ZEPHYR, CUT/HIVE, STRENGTH/PLAIN, SURF/FOG, FLY/STORM, WHIRLPOOL/GLACIER, WATERFALL/RISING. A regra existente de ROCK_CLIMB referencia KANTO:EARTH e deve ser tratada como dependência a auditar, **não modificada silenciosamente**.
9. **Pokémon especiais:** Legendary, Mythical, UltraBeast e Paradox ficam bloqueados para a party até oito conquistas **locais** da região atual. Ao viajar, reservar Boxes, depositar sem perda, impedir retirada indevida, cancelar operação se PC cheio ou equipe inválida; completar as integrações de captura/troca/presente/carregamento descritas no Plano v2.
10. **Pós-jogo mundial:** somente depois das dez campanhas principais concluídas, alternar para as equipes oficiais mais fortes documentadas, sem inventar times ou liberar especiais prematuramente.
11. **Tradução:** preparar diálogos em inglês original + adaptação PT-BR revisada, com origem, NPC, evento e condições; não copiar tradução desconhecida como se fosse oficial.
12. **Kanto e Decades não regridem:** nenhum MapID, tileset, save, áudio personalizado, personagem, batalha, encontro, portal ou menu anterior pode ser substituído sem migração segura.

## 3. Arquitetura planejada

**Arquivos existentes a preservar/estender com cuidado:**

- [site/public/data/regions.json](../site/public/data/regions.json): JOHTO já cadastrada; só atualizar status após atingir os critérios.
- [scripts/battle_polish/Regions.rb](../scripts/battle_polish/Regions.rb), [RegionStart.rb](../scripts/battle_polish/RegionStart.rb), [RegionTravel.rb](../scripts/battle_polish/RegionTravel.rb), [RegionalPolicy.rb](../scripts/battle_polish/RegionalPolicy.rb), [RegionalCards.rb](../scripts/battle_polish/RegionalCards.rb).
- [scripts/music/BlueMusic.rb](../scripts/music/BlueMusic.rb), que já preserva preferências e playlists globais.
- Os testes existentes em [tests/](../tests/), o Kanto piloto e o instalador da versão principal.

**Arquivos propostos — NÃO existem ainda; os nomes abaixo são entregáveis das fases:**

~~~text
data/regions/johto-source.json           # versão, origem, SHA-256, licenças, chaves de mapa
data/johto-music.json                     # catálogo de áudio auditado e hashes
data/johto-music-rules.json               # vínculo simbólico entre mapas/eventos e faixas
scripts/regions/audit_johto.py            # inventário só-leitura
scripts/regions/stage_johto.py            # cópia isolada, mapeamento estável
scripts/regions/pilot_johto.py            # montar piloto sem tocar game/
scripts/regions/install_johto.py          # dry-run, backup, apply, rollback
scripts/regions/verify_johto.py           # verificação de mapa/PBS/eventos/integração
scripts/regions/export_johto.py           # dados do portal e Pokédex
scripts/regions/JohtoPilot.rb             # somente adaptador de eventos Johto
scripts/music/compile_johto_music.py      # compilação regional isolada
scripts/music/install_johto_music.py      # instalação não destrutiva (se licenciada)
tests/test_johto_*.py                     # testes estruturais/regressões
tests/johto_*_runtime.rb                  # testes Ruby/nativos
docs/JOHTO_ETAPAS.md                      # duas barras e evidências por fase
docs/JOHTO_MUSICAS_MAPEAMENTO.md          # músicas e os eventos reais
docs/JOHTO_TESTES_E2E.md                  # testes na janela do Game.exe
.blue-work/johto-source/                  # dados baixados localmente, sem upload
.blue-work/johto-pilot/                   # cópia executável isolada
.blue-backups/johto-*/                    # cópias antes de aplicar
~~~

**Manifesto de exemplo (conceitual, não pronto para importar):**

~~~json
{
  "schema": 1,
  "region": "JOHTO",
  "source_name": "Remastered Kanto and Johto Overworld and Caves Map Pack",
  "source_url": "https://eeveeexpo.com/resources/828/",
  "source_sha256": "PREENCHER_APOS_AUDITORIA_LOCAL",
  "permission_status": "PENDENTE_VERIFICACAO_DOS_COMPONENTES",
  "maps": {
    "ID_DE_ORIGEM_AUDITADO": "NEW_BARK_TOWN"
  },
  "missing_required": [
    "PLAYER_HOME_INTERIOR",
    "MT_SILVER_COMPLETO"
  ]
}
~~~

**Nunca considerar a lista de mapas acima um mapeamento definitivo.** Os IDs e interiores reais precisam vir da fonte inspecionada. Cada mapa recebe **chave simbólica estável** (JOHTO_NEW_BARK_TOWN, JOHTO_ROUTE_29...) e um ID compilado livre dentro da instalação, com tabela congelada para compatibilidade de saves. Não calcular destinos somando um offset fixo não auditado.

## 4. As duas barras obrigatórias de progresso

Adotar **16 etapas (01–16)** e acompanhar separadamente:

- **Barra 1 — Núcleos técnicos implementados e aprovados automaticamente:** **0/16 (0%)**, 16 faltando.
- **Barra 2 — Etapas aceitas integralmente com evidência de gameplay real:** **0/16 (0%)**, 16 faltando.

Estado 0/16 é a linha inicial de **Johto**, não uma reinterpretação da barra de Kanto. Um item só aumenta a Barra 1 com código, testes estruturais/CI e relatório de resultado; a Barra 2 exige execução observável do jogo, portas, colisão, batalhas e saves, sem bugs bloqueantes, inclusive Windows e JoiPlay onde aplicável. Nunca inferir sucesso a partir de documentos escritos.

Cada etapa deve produzir: arquivos modificados, commit/PR, mapa-chave + ID de destino efetivo, lista de eventos funcionais, evidências dos testes, pendências explícitas, nova contagem **N/16** de cada barra e próxima ação. Uma etapa parcialmente entregue não aumenta a contagem integral.

## 5. Sequência de implementação — 16 etapas

### Etapa 01/16 — Congelar fontes, direitos, decisões e estado da instalação

**Implementar:** inspecionar localmente o Map Pack e o jogo base instalado, conferir créditos e licenças de mapas/tiles, calcular SHA-256 do arquivo recebido, confirmar versão exata do Essentials/Decades, inventariar o estado e os mapas do Kanto, registrar ausências (interiores, eventos, Mt. Silver) e criar **data/regions/johto-source.json** sem IDs presumidos.

**Entregar:** manifesto de fonte auditada, matriz de permissões por recurso, hashes, descrição dos limites e docs/JOHTO_ETAPAS.md com as duas barras zeradas.

**Teste/aceite:** só-leitura; nenhum byte de game/, Decades, Kanto ou saves alterado. Se licença/arquivo insuficiente, registrar BLOQUEADO_FONTE e seguir apenas com planejamento ou recriação própria.

### Etapa 02/16 — Auditoria e mapa de dependências sem executar código da fonte

**Implementar:** leitor só de dados para **MapXXX.rxdata**, **MapInfos.rxdata**, **Tilesets.rxdata**, gráficos, autotiles, eventos, passabilidade, entradas/saídas, conexões e PBS quando existirem. Reutilizar o parser seguro de [server/ruby_marshal.py](../server/ruby_marshal.py), mas **generalizar as partes necessárias** de audit.py em vez de trocar a constante KANTO. Detectar scripts/eventos indisponíveis e dependências de Essentials diferente.

**Entregar:** scripts/regions/audit_johto.py e relatório JSON com IDs originais, símbolos, tamanho, origem, tileset, passabilidade, fronteiras, objetos ausentes, rotas e eventos a adaptar.

**Teste/aceite:** determinístico, idempotente, sem executar Ruby não confiável e sem escrever no jogo; fontes incompletas ficam marcadas PENDENTE, sem inventar conteúdo.

### Etapa 03/16 — Importador e prévia isolada de Johto

**Implementação parcial entregue:** [JOHTO_FASE_03_PREVIA_SEGURA.md](JOHTO_FASE_03_PREVIA_SEGURA.md). `plan_johto.py` já planeja IDs e verifica colisões, `stage_johto.py` cria prévia apenas de geometria e `verify_johto.py` valida que o jogo-base não foi alterado. `tests/test_johto_map_plan.py` e `tests/test_johto_stage.py` usam mapas sintéticos. **A fonte real não está auditada, a prévia real não foi gerada e os mapas ainda não são jogáveis.** Não elevar esta etapa a concluída com base nos testes sintéticos.


**Implementar:** preparar geometry-only em .blue-work/johto-pilot (e staging novo por execução), importar gráficos autorizados, **remapear MapIDs e IDs de tileset**, recuperar conexões sem sobrescrever arquivos antigos, manter o mapeamento de Kanto e Decades, distinguir preview/experimental/funcional. Criar dry-run de alteração de mapas, MapInfos, Tilesets, PBS e recursos. Preservar snapshots para rollback.

**Entregar:** stage_johto.py, pilot_johto.py, verify_johto.py e testes de round trip; nenhum evento de terceiros ativado automaticamente.

**Teste/aceite:** abrir cenário teste sem sprites quebrados, buracos, passabilidade incorreta, mapas órfãos ou alteração de hashes da instalação principal. Não habilitar Johto na seleção inicial apenas porque cenário está presente.

### Etapa 04/16 — Nova partida completa em New Bark Town

**Continuação parcial já implementada:** [JOHTO_FASE_04_EVENTOS_NEW_BARK.md](JOHTO_FASE_04_EVENTOS_NEW_BARK.md). `JohtoPilot.rb` contém eventos próprios para a mãe, Elm, escolha dos três iniciais e rival condicionado aos treinadores PBS; `tests/test_johto_story_runtime.py` valida a lógica Ruby. O ZIP original do Map Pack pode ser preparado localmente com `prepare_johto_source.py`, sem importar executáveis ou scripts de terceiros. Essas mudanças **não** substituem os mapas reais, nem criam um piloto jogável, nem devem habilitar o início em Johto antecipadamente.


**Implementar:** criar e auditar interior da casa, escada, saída/retorno, ruas e laboratório de Elm; intro, mãe, encontro do rival e seleção Chikorita/Cyndaquil/Totodile. Adaptar RegionStart.rb para descobrir **marcador genérico por região**, não só blue-kanto-start.txt. O novo jogo deve nascer **no quarto**, enquanto a chegada por transporte ocorre em ponto seguro externo da cidade. Preservar novo jogo/continue Decades e testes de Kanto.

**Entregar:** mapas funcionais e scripts de eventos Johto, spawn auditado, teste isolado e instruções de entrada pelo menu com Johto apenas se instalado.

**Teste/aceite:** nascer no lugar correto, descer escada, sair e entrar novamente, escolher um inicial apenas uma vez, rival/coleta/eventos sem duplicações, salvar/carregar e retornar à casa; save Decades anterior permanece válido.

### Etapa 05/16 — Rotas 29–31, Cherrygrove, Violet City e Falkner

**Parcial implementada no GitHub:** [JOHTO_FASE_05_VIOLET_FALKNER.md](JOHTO_FASE_05_VIOLET_FALKNER.md). `JohtoViolet.rb` prepara diálogos, Torre Sprout, batalha de Falkner, prêmio ZEPHYR idempotente via `BlueRegions.award` e consulta da permissão local de Rock Smash. `data/regions/johto-phase05.json` descreve o corredor simbólico, sem IDs não verificados. Os testes Ruby/Python verificam conquistas, saves e isolamento. **Não há mapas reais instalados, equipes PBS compiladas, piloto jogável nem aceitação manual**; os botões de teste e novo jogo continuam bloqueados até existir fonte validada.


**Implementar:** ligar New Bark → Route 29 → Cherrygrove → Route 30 → Route 31 → Violet, com cavernas/portarias relevantes, casas, Centro Pokémon, Mart, Sprout Tower e ginásio de Falkner. Encontros de habitat HG/SS e exclusividades unificadas, diálogos/eventos de avanço e treinadores com visão de batalha. Implementar a insígnia ZEPHYR sem prêmio duplo.

**Teste/aceite:** atravessar o trecho inteiro ida/volta, entrar/sair dos interiores, vencer Falkner, obter exatamente uma insígnia/esmeralda, salvar e repetir tentativa sem recompensa dupla.

### Etapa 06/16 — Route 32, Union Cave, Azalea, Slowpoke Well e Bugsy

**Implementação parcial publicada:** [JOHTO_FASE_06_AZALEA_BUGSY.md](JOHTO_FASE_06_AZALEA_BUGSY.md). `JohtoAzalea.rb` possui eventos regionais isolados para Kurt, Slowpoke Well, dois Rocket Grunts, Proton, Bugsy e rival, com HIVE dada somente pela API `BlueRegions.award` após vitória e autorização de Cut ligada à insígnia + ferramenta. O mapa simbólico está em `data/regions/johto-phase06.json`; testes Ruby/Python cobrem vitórias, derrotas, transições de estado, persistência e proteção Kanto/Decades. **Não há mapas reais nem treinadores PBS instalados, e esta etapa não está jogável; proibir passagem para status concluída por testes sintéticos.**


**Implementar:** percurso desde Violet, Union Cave com andares e encontros, Azalea Town, Kurt, Slowpoke Well e Team Rocket, Ginásio Bugsy, evento da Hive Badge, rival e fluxo de Cut quando autorizado.

**Teste/aceite:** caverna com transições reais, poço/Equipe Rocket funcionais, Bugsy completo, eventos únicos e HIVE contabilizada uma única vez.

### Etapa 07/16 — Ilex Forest, Route 34, Goldenrod e Whitney

**Implementação parcial publicada:** [JOHTO_FASE_07_ILEX_GOLDENROD_WHITNEY.md](JOHTO_FASE_07_ILEX_GOLDENROD_WHITNEY.md). `JohtoGoldenrod.rb` prepara lenhador/Farfetch'd, recompensa Cut dependente de item real, Day Care introdutório, quiz da Rádio, batalha de Whitney com PLAIN só após conversa posterior, Floricultura e Sudowoodo futuro bloqueado. `data/regions/johto-phase07.json` define o caminho simbólico sem IDs inventados. Testes Ruby/Python validam a sequência, derrotas, recompensas únicas, insígnias/esmeraldas, campo e save/reload. **Faltam mapas verdadeiros, interiores, NPCs vinculados, equipes PBS e gameplay em Game.exe. Essa fase permanece PARCIAL e não pode habilitar um Testar Johto fictício.**


**Implementar:** Ilex Forest com puzzle do Farfetch'd e HM/evento de Cut, Day Care, Route 34, Goldenrod, rádio, lojas, Underground, National Park quando conectado e ginásio de Whitney; Sudowoodo como evento real e não decoração inacessível.

**Teste/aceite:** puzzle e uso de Cut com credenciais locais, portas/andares/lojas corretos, Whitney + PLAIN Badge, reentrada e saves persistentes.

### Etapa 08/16 — Routes 35–37, National Park, Ecruteak, Morty

**Implementação parcial publicada no GitHub:** [JOHTO_FASE_08_ECRUTEAK_MORTY.md](JOHTO_FASE_08_ECRUTEAK_MORTY.md). O núcleo `JohtoEcruteak.rb` prepara a progressão por Rotas 35–37, visita ao National Park, porta do Sudowoodo, entrada em Ecruteak, Burned Tower e rival, despertar simbólico dos três lendários, Rocket do Dance Theater, prêmio Surf sujeito à chave de item real e Morty com concessão única de FOG. `data/regions/johto-phase08.json` só contém nós simbólicos e gates desativados; testes Ruby/Python verificam perdas, vitórias, recompensas, salva/carrega e isolamento. **Os mapas reais, o roaming dos lendários, os treinadores PBS, a competição de captura e a execução no Game.exe ainda não foram implementados. A etapa 08 permanece PARCIAL, sem habilitar Johto ficticiamente.**


**Implementar:** Route 35/36/37, National Park e competição de captura quando os sistemas estiverem prontos, Ecruteak, Burned Tower, dança/Kimono Girls quando fizer parte da versão principal, ginásio Morty e FOG Badge. Ruins of Alph e Mt. Mortar podem ser preparados como módulos opcionais com status separado, não falsamente completos.

**Teste/aceite:** caminho aberto por evento correto, torres com passabilidade e encontros, batalha de Morty, Surf desbloqueado apenas conforme regra local já registrada.

### Etapa 09/16 — Olivine, Lighthouse, Cianwood e Chuck

**Implementação parcial publicada:** [JOHTO_FASE_09_OLIVINE_CIANWOOD_CHUCK.md](JOHTO_FASE_09_OLIVINE_CIANWOOD_CHUCK.md). O módulo `JohtoOlivineCianwood.rb` prepara Route 38–41, Olivine, checkpoints dos 6 andares do Lighthouse, pedido de SecretPotion por Jasmine, travessia via FOG/Surf, farmácia de Cianwood, cascata e batalha de Chuck com STORM única, Fly com ferramenta e retorno com medicina, **sem curar Ampharos nem liberar Jasmine antes da Etapa 10**. A topologia não instalada está em `data/regions/johto-phase09.json`; testes Ruby/Python verificam recompensas idempotentes, derrotas, save/reload e separação entre regiões. **Faltam Map Pack, escadas/elevador, PBS compilado, eventos RMXP, verificação de itens, encounters e teste no Game.exe. Não declarar a fase concluída por simulação.**


**Implementar:** Routes 38–41, Olivine e Lighthouse, travessia oceânica, Cianwood, farmácia, ginásio Chuck, STORM Badge, Fly sujeito à regra regional. Garantir encontros Land/Water/Fishing e interior do farol, escadas e elevadores funcionais.

**Teste/aceite:** alcançar Cianwood, resolver o arco da medicina sem gastar recompensas duplicadas, vencer Chuck, voar somente quando permitido e voltar a Olivine.

### Etapa 10/16 — Jasmine, Olivine e áreas oceânicas

**Implementar:** concluir a recuperação de Ampharos, liberar a batalha de Jasmine e MINERAL Badge. Auditar Whirl Islands como áreas de caverna, mas manter a captura lendária bloqueada até seu evento canônico. Consertar entrada de cada andar, conexão marítima, marés/correntes se aplicável e rota de retorno.

**Teste/aceite:** Jasmine só batalha após pré-requisitos corretos; sexto marco local só é concedido uma vez; nenhuma ilha deixa jogador preso.

### Etapa 11/16 — Mahogany, Lake of Rage, Rocket Hideout e Pryce

**Implementar:** Routes 42/43/44, Mahogany, Lake of Rage, encontro com Red Gyarados e Lance, Rocket Hideout com puzzles/portas, Radio Tower takeover/Goldenrod conforme encadeamento de HGSS e ginásio de Pryce/GLACIER. Auditar nível de acesso ao WhirlPool por insígnia local.

**Teste/aceite:** eventos Rocket na ordem correta, estados persistentes, batalha contra Pryce, insígnia sem duplicação e mapas sem bloqueio permanente por switches de outra região.

### Etapa 12/16 — Ice Path, Blackthorn, Clair e Dragon's Den

**Implementar:** Ice Path com gelo/Strength, Blackthorn, ginásio Clair, Dragon's Den, prova do Dragon Master e RISING Badge na condição correta. Rotas 45/46 e Dark Cave recebem conexões auditadas quando integradas.

**Teste/aceite:** puzzles concluíveis, Clair não concede insígnia precocemente, oitava insígnia concede +1 apenas uma vez, liberar HMs e uso de especiais somente pelo estado local correto.

### Etapa 13/16 — Tohjo Falls, Victory Road, Elite Four e Lance

**Implementar:** acesso da região de Johto ao corredor da Liga por New Bark → Route 27/26 → Tohjo Falls → Victory Road → Indigo Plateau. Considerar que **Indigo Plateau é geograficamente compartilhado com Kanto**, mas a campanha, estados, treinadores e conclusão de Johto não podem sobrescrever nem premiar a Liga Kanto. Adaptar Elite Four **Will, Koga, Bruno, Karen** e campeão **Lance**, Hall of Fame, retorno ao jogo, save e flag de conclusão verificada.

**Teste/aceite:** oito badges locais exigidas, quatro membros + Lance vencidos em ordem, derrota não libera destinos, vitória repetida não concede prêmio duplicado; desbloquear Kanto + Hoenn na estrutura de save, mas **não** permitir transporte para Hoenn enquanto seus mapas não existirem.

### Etapa 14/16 — Lendários, pós-jogo e opcionais de Johto

**Implementar:** Bell Tower/Tin Tower, Whirl Islands/Lugia, Ho-Oh, Entei/Raikou/Suicune, Ruins of Alph, áreas alternativas HG/SS/Crystal, Pokéathlon ou Bug-Catching Contest quando viável. Mt. Silver é **mapa ausente no Map Pack**: só criar com fonte autorizada ou desenho próprio e registrar origem. Não sobrepor evento canônico do Crystal ao HGSS sem especificar versão/timing. Red e pós-Liga são capítulos próprios, não pré-requisitos inventados para a Liga Johto.

**Teste/aceite:** cada lendário/evento só dispara onde previsto, sem duplicatas após save/reload; conteúdo pendente permanece fora de seleção jogável, e restrições da party não são burladas.

### Etapa 15/16 — Música, sons, catálogo de treinadores e portal

**Implementar música em subfases M0–M6**, com catálogo auditado, usando o sistema de Kanto apenas como padrão técnico:

- **M0:** inventário de fontes legais, direitos e hashes; nenhum MP3 inventado/automaticamente baixado.
- **M1:** criar data/johto-music.json e data/johto-music-rules.json; resolver MapIDs compilados da **região JOHTO**.
- **M2:** BGM de New Bark, Cherrygrove, Violet, Azalea, Goldenrod, Ecruteak, Olivine, Cianwood, Mahogany, Blackthorn, rotas, cavernas, torres, surf e bicicleta; tocar somente onde houver mapa/evento real.
- **M3:** batalhas selvagens, treinador, rival, ginásio, Rocket, lendários, Elite Four, Lance, vitória; respeitar classes reais e os sorteios pessoais do Blue.
- **M4:** fanfarras ME de captura, cura, insígnia, item, evolução e prêmios, apenas quando houver hook de evento comprovado; restaurar trilha ambiente.
- **M5:** Elm, introdução, Radio Tower, Kimono Girls, Hall of Fame, créditos e cenas especiais somente quando existentes.
- **M6:** regressão com Kanto/Decades e fallback sem áudio; instalar arquivos licenciados de forma não destrutiva em Audio/BGM/Johto ou Audio/ME/Johto.

**Portal/Blue Studio:** exportar a partir de MapIDs efetivos; listar treinadores de Johto e variantes de equipe, status dos mapas (preview/experimental/funcional/aceito), habitat/onde capturar, insígnias e segunda página do cartão. Ajustar importação, edição de música e interface sem apagar as seções Decades/Kanto.

**Teste/aceite:** nenhuma faixa de Johto fora de Johto; BGM não toca por cima da cutscene; ME não repete; retorno de batalha/viagem restaura música; mapas sem arquivo têm fallback; portal só anuncia mapas realmente implementados; licenças do áudio verificadas.

### Etapa 16/16 — Instalação no jogo principal, regressões e aceite completo

**Implementar:** instalador transacional de Johto com **dry-run por padrão**, proteção dos hashes Decades/Kanto, plano de sobrescritas, backups e rollback; marcadores regionais genéricos e agente físico em New Bark Town; ampliar RegionTravel para Johto, incluindo Kanto↔Johto e Johto→Hoenn apenas se Johto concluída + destinos instalados. O plugin não pode depender de blue-kanto-install.json como prova genérica de todas as regiões.

**Entregar:** importação reproduzível em game/ local, estado de instalação por região, scripts/regions/verify_johto.py, testes Python/Ruby/Windows/JoiPlay, docs/JOHTO_TESTES_E2E.md, relatório final por mapa/evento e estado atualizado no catálogo somente após evidência.

**Critério de aceitação:** 16 etapas efetivamente jogáveis e verificadas; oito ginásios, liga, cenas essenciais, transições, encontros, save/reload, party/PC, HMs, NPC regional, áudio, Blue Studio e portal integrados, sem regressão de Decades/Kanto.

## 6. Matriz mínima de mapas e marcos (não é prova de existência na fonte)

| Núcleo | Local/trecho | Evento obrigatório | Marco |
|---|---|---|---|
| Início | New Bark + casa + lab | Elm, três iniciais, rival, portas/escadas | Spawn auditado |
| Primeiro ginásio | Rotas 29–31, Cherrygrove, Violet, Sprout Tower | Falkner | ZEPHYR |
| Segundo | Route 32, Union Cave, Azalea, Slowpoke Well | Rocket, Bugsy | HIVE |
| Terceiro | Ilex Forest, Route 34, Goldenrod | Farfetch'd, Whitney | PLAIN |
| Quarto | National Park, Routes 35–37, Ecruteak | Burned Tower, Morty | FOG |
| Quinto | Olivine, Lighthouse, Routes 40–41, Cianwood | Medicina, Chuck | STORM |
| Sexto | Olivine | Jasmine e Ampharos | MINERAL |
| Sétimo | Mahogany, Lake of Rage, Rocket Base | Red Gyarados, Rocket, Pryce | GLACIER |
| Oitavo | Ice Path, Blackthorn, Dragon's Den | Clair, Dragon Master | RISING |
| Liga | Route 27/26, Tohjo Falls, Victory Road, Indigo Plateau | Will, Koga, Bruno, Karen, Lance | JOHTO_LEAGUE |
| Complementos | Ruins of Alph, Whirl Islands, Bell Tower, Mt. Mortar, Mt. Silver | Lendários, puzzles e pós-jogo | Somente se construídos/auditados |

**Notas de cobertura:** entradas/saídas das casas, Pokémon Center, Poké Mart, ginásios e cada andar de cavernas/torres são mapas/eventos próprios e precisam de testes reais. O Map Pack não garante interiores, NPCs, cutscenes nem todos os puzzles. Não transformar todos os mapas de terreno em status funcional.

## 7. Estratégia de testes e rollback (Codex + Windows + JoiPlay)

### 7.1 Comandos já existentes — linha de base

Na raiz do repositório, **antes de alterar código**, usar as suítes atuais disponíveis e registrar resultado:

~~~powershell
python -m unittest discover -s tests -p "test_regions.py"
python -m unittest discover -s tests -p "test_kanto_*.py"
python -m unittest discover -s tests -p "test_johto_*.py"
~~~

O último comando é **planejado**, e deve encontrar testes apenas depois que forem criados. O comando de Kanto pode exigir a fonte/instalação local; relatar SKIP/BLOQUEADO quando ausente, nunca fingir que passou. Rodar também testes Ruby aplicáveis e os testes de CI existentes. Não executar scripts Johto inexistentes antes da respectiva etapa.

### 7.2 Comandos propostos — criar seus argumentos na Etapa 02/03/16

~~~powershell
# EXEMPLOS DE INTERFACE ESPERADA; NÃO EXISTEM AINDA
python scripts/regions/audit_johto.py --source ".blue-work/johto-source" --output ".blue-work/johto-audit.json"
python scripts/regions/pilot_johto.py --source ".blue-work/johto-source" --output ".blue-work/johto-pilot"
python scripts/regions/install_johto.py --dry-run
python scripts/regions/install_johto.py --apply
python scripts/regions/verify_johto.py --game ".blue-work/johto-pilot"
~~~

Cada script precisa oferecer --help e validações de caminho, hash, versão, dependências e pré-condições. Nunca criar script que substitua game/Data inteiro. Se a instalação original mudar desde o piloto, recusar o apply até nova auditoria.

### 7.3 Testes E2E que realmente validam gameplay

1. Iniciar pelo **Game.exe/Blue-Story.exe real**, em Windows com interface gráfica, na cópia isolada; verificar janela, movimento, colisões e sprites visíveis.
2. New Game em Johto → quarto de New Bark → escada → rua → laboratório → escolha de inicial → primeiro confronto.
3. Para **cada rota e interior**: caminhar de A a B e voltar, atravessar portas/escadas e verificar a coordenada de retorno. Não aceitar teleporte de debug como substituição.
4. Para **cada treinador**: entrar no alcance visual, disparar combate, verificar equipe/moves, ganhar, reabrir save e confirmar que não reinicia nem dá prêmio duplicado.
5. Para **cada ginásio**: conferir puzzle, líder, badge, soma global única, HMs locais e as duas páginas de cartões; fazer reteste com derrotas e recarga.
6. Concluir a Liga de Johto sem saltos: Elite Four + Lance, Hall of Fame, checkpoint, desbloqueios, persistência pós-save, finais repetidos.
7. Viajar Johto↔Kanto (e outros destinos autorizados) no **mesmo save**: PC/party/itens/dinheiro/Pokédex/insígnias intactos; testar especiais, Box cheia, equipe inválida, cancelamento e rollback.
8. Áudio: passar entre mapas, batalhas, cutscenes, bicicleta, Surf, cura, insígnia e retorno de região; zero música de Johto em Decades e zero ME duplicado.
9. Visual e save do **Android/JoiPlay**: controles/toque/teclado, mapas grandes, encontros, batalhas, travamentos, tela inicial, save/reload e música.
10. Regressão de **Decades + Kanto** antes/depois: mesmas IDs de mapas, hashes esperados, portas, batalha, sons, cartão, portal, menus e saves legados.

**Codex:** sempre que houver ambiente com desktop real, automatizar caminhada e interações por entrada real, coletar logs, screenshots e passos reproduzíveis. Se só for possível teste headless, registrar **NÃO ACEITO_VISUALMENTE**; nunca declarar Barra 2 aprovada por simulação de batalha, arquivo RXDATA válido ou CI verde.

### 7.4 Gates objetivos

- **G0 Fonte:** licença, autoria, hashes, mapa de dependências.
- **G1 Segurança:** auditoria/dry-run não toca game/, saves nem Kanto.
- **G2 Geometria:** MapIDs estáveis, conectividade, colisor/passabilidade, portas.
- **G3 Campanha:** eventos, 8 badges, treinadores/selvagens, Liga, flags.
- **G4 Sistemas:** balanceamento Blue, dois cartões, HMs, PC e NPC de viagem.
- **G5 Áudio e portal:** regras regionais, direitos, rastreabilidade, sem músicas fantasmas.
- **G6 Aceite real:** Windows + Android conforme escopo, regressões, rollback e evidências.

## 8. Padrão de relatórios por fase

Criar **docs/JOHTO_ETAPAS.md** na primeira fase e, após cada etapa, acrescentar:

~~~text
Johto Etapa NN/16
Status: IMPLEMENTADA | PARCIAL | BLOQUEADA
Fonte: URL, versão, SHA-256, licença
Mapas auditados: N  | funcionais: N | preview: N
IDs origem → destino: anexar manifest sem renumerar anteriores
Eventos: funcionando / pendente (com MapID, EventID, gatilho)
Testes: comando, resultado, links de CI, evidência de gameplay
Regressões: Decades / Kanto / Saves / Android / Áudio
Barra 1: XX/16; faltam 16-XX
Barra 2: YY/16; faltam 16-YY
Bloqueadores: lista verificável
Próximo passo: NN+1
~~~

Não subir arquivos de saves pessoais, screenshots privados ou dados proprietários aos commits sem revisão. Guardar evidências locais quando necessário.

## 9. Mensagens prontas para executar via ChatGPT/Codex

Use a frase do estágio desejado; o assistente **deve conferir a main atual antes de alterar qualquer coisa**:

| Pedido | Resultado esperado |
|---|---|
| **Aplique a Etapa 01/16 de docs/JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md no GitHub.** | Auditar fonte, direitos, projeto e criar manifesto/duas barras. |
| **Aplique a Etapa 02/16 do plano de Johto no GitHub.** | Scanner seguro e relatório de dependências. |
| **Aplique a Etapa 03/16 do plano de Johto no GitHub.** | Prévia dos mapas e importador isolado. |
| **Aplique a Etapa 04/16 do plano de Johto no GitHub.** | New Bark Town, casa, Elm, inicial e nova partida. |
| **Aplique a Etapa 05/16 do plano de Johto no GitHub.** | Violet/Falkner e rotas iniciais. |
| **Aplique a Etapa 06/16 do plano de Johto no GitHub.** | Azalea/Bugsy/Rocket. |
| **Aplique a Etapa 07/16 do plano de Johto no GitHub.** | Goldenrod/Whitney. |
| **Aplique a Etapa 08/16 do plano de Johto no GitHub.** | Ecruteak/Morty. |
| **Aplique a Etapa 09/16 do plano de Johto no GitHub.** | Cianwood/Chuck. |
| **Aplique a Etapa 10/16 do plano de Johto no GitHub.** | Olivine/Jasmine. |
| **Aplique a Etapa 11/16 do plano de Johto no GitHub.** | Lake of Rage/Rocket/Pryce. |
| **Aplique a Etapa 12/16 do plano de Johto no GitHub.** | Blackthorn/Clair. |
| **Aplique a Etapa 13/16 do plano de Johto no GitHub.** | Liga Johto/Lance/desbloqueios. |
| **Aplique a Etapa 14/16 do plano de Johto no GitHub.** | Lendários, cavernas e pós-jogo. |
| **Aplique a Etapa 15/16 do plano de Johto no GitHub.** | Música M0–M6, portal e catálogo. |
| **Aplique a Etapa 16/16 do plano de Johto no GitHub.** | Instalador final, viagem, testes e relatório de aceite. |

**Contrato de cada execução:** implementar as alterações reais permitidas, criar/adaptar testes, corrigi-los, publicar **apenas o que foi efetivamente validado** na branch apropriada, registrar commit/PR, atualizar os dois indicadores e informar quantas etapas faltam. **Uma etapa incompleta permanece pendente; não avançar automaticamente apenas para aumentar as barras.**

## 10. Primeira ação recomendada

**Iniciar pela Etapa 01/16:** confirmar a fonte exata e as permissões, calcular hashes, criar o manifesto de Johto e congelar os MapIDs existentes antes de importar qualquer mapa. Em seguida, Etapa 02 (auditoria) e 03 (prévia isolada). **Não** adicionar Johto à opção de nova partida enquanto a casa de New Bark, o spawn e o piloto não tiverem sido realmente testados.

**Estado após criar este documento: planejamento/documentação apenas. Barras de Johto permanecem em 0/16 e 0/16.**
