# Johto — acompanhamento técnico das 16 etapas

**Início:** 12/11/2026  
**Plano mestre:** [JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md)  
**Fontes:** [JOHTO_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md](JOHTO_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md)  
**Estado (13/11/2026):** fonte real ZIP v1 auditada (74 mapas Johto, 42 conexões externas); nenhum mapa foi incorporado ao jogo nativo ou habilitado para jogar.

## Progresso auditável — fonte vs. 16 etapas (13/11/2026)

O [registro estruturado de progresso](../data/regions/johto-progress.json) separa o trabalho sobre os arquivos reais do ZIP da aprovação das fases do jogo. Os totais são verificados em `tests/test_johto_progress.py`.

| Indicador | Resultado | Significado |
|---|---:|---|
| Mapas reais identificados no ZIP | **74/74 (100%)** | IDs e nomes da fonte v1 catalogados, não instalados |
| Linhas de conexão do ZIP registradas | **42/42 (100%)** | Total **existente na fonte**, não todas as transições necessárias |
| Núcleos técnicos totalmente aprovados | **0/16 (0%)** | Critérios técnicos ainda incompletos, inclusive baseline `game/` |
| Testes automatizados de código/contratos disponíveis | **16/16 (100%)** | Há testes de código por fase, **não são testes de gameplay** |

### As duas barras de gameplay — separadas para não confundir

**1. Fases JOGÁVEIS (fases 04–16)** — **0/13 (0%)**

```text
[░░░░░░░░░░░░░]  0 / 13
```

Conta a fase quando existe uma **versão real no Game.exe isolado** em que seja possível começar, percorrer mapas e executar seu fluxo principal, com eventos/portas funcionais. O marco pode ser jogável **antes** de completar todos os testes de regressão; não basta ter mapas no ZIP, scripts Ruby ou testes sintéticos.

**2. Fases TESTADAS no jogo (fases 04–16)** — **0/13 (0%)**

```text
[░░░░░░░░░░░░░]  0 / 13
```

Conta somente fases já jogáveis que tenham **QA nativo concluído**, com testes observáveis das portas, NPCs, batalhas, estados de vitória/derrota, salvamento/carregamento e regressões Windows/JoiPlay quando aplicável. **Passar na CI de Python/Ruby não aumenta essa barra.**

As fases **01–03** são auditoria e infraestrutura, portanto não são consideradas fases de campanha jogável; as duas barras usam **13 etapas (04–16)**. O indicador de infraestrutura continua 0/16 separadamente. Cada fase possui campos distintos `gameplay_playable` e `gameplay_tested` em [johto-progress.json](../data/regions/johto-progress.json), e um vínculo ao teste de código automatizado. Uma fase pode estar **jogável** sem ter **QA aprovado**, mas não pode ter QA de gameplay aprovado sem estar jogável.

**Por que as barras de gameplay ainda não avançaram com o ZIP?** A fonte não contém eventos, NPCs, Pokémon, interiores do começo ou os testes no motor de jogo. A primeira etapa ainda requer verificação de direitos e arquivos nativos; a segunda ainda requer revisão de passabilidade e conexões físicas. Etapas 03–16 exigem integração e verificações específicas. Publicar os 74 MapIDs ou passar testes sintéticos **não equivale a fase 100% aprovada**.

**Próximo desbloqueio:** fornecer `game/Data`, `game/Graphics/Tilesets`, `game/Graphics/Autotiles` e `game/PBS` (sem saves nem Game.exe) para planejar remapeamento sem colisão e gerar prévia real em cópia isolada.

Nenhum teste sintético, checklist ou documento autoriza subir a barra de fases jogáveis sem jogo executável comprovado ou a barra de fases testadas sem QA nativo comprovado.

## Trabalho inicial de Johto entregue ao GitHub

- [x] Fonte de mundo/tiles [Map Pack de AenaonDogsky](https://www.eeveeexpo.com/resources/828/): o ZIP **v1 efetivamente recebido** possui 74 mapas Johto IDs 79–152, **incluindo Mt. Silver (102/103)**. A v3 do catálogo não foi assumida como equivalente à v1.
- [x] Política de não-regressão para Decades, Kanto, Game.exe, slots, saves, músicas, portal e Blue Studio.
- [x] **data/regions/johto-source.json** agora contém SHA-256 real do ZIP v1 e as **74 associações verificadas ID de origem → símbolo Johto**, com direitos pendentes e `import_enabled=false`.
- [x] **scripts/regions/audit_johto.py** criado para ler RMXP em modo somente leitura (sem executar Ruby), inventariar mapas, dimensões, tilesets, eventos, transferências, hashes e colisões com IDs atuais.
- [x] **tests/test_johto_source_audit.py** criado com mapas sintéticos, proteção de hashes, referências faltantes, scripts não executados e teste de fonte ausente.
- [x] **Testar Johto** já está no menu principal junto de **Testar Kanto**. Enquanto o piloto estiver ausente, informa que Johto está em preparação sem usar os arquivos de Kanto.
- [x] Confirmado o ZIP real v1 enviado em 13/11/2026: SHA-256 `5d5697e9c3bf5db6ca7039d4af65697dd8b231f4b1305f14731e35ac324b6715`.
- [x] Auditados **74 mapas Johto reais**, dimensões, tilesets e ausência de eventos, mais 42 conexões da origem. [Relatório da fonte real v1](JOHTO_AUDITORIA_FONTE_REAL_V1.md).
- [ ] Verificar licenças/créditos específicos e auditar o `game/` instalado para evitar colisões com MapIDs, salvar provas e confirmar o motor nativo.
- [x] Planejamento seguro de IDs implementado em `scripts/regions/plan_johto.py` (IDs livres ≥600, compatibilidade com mapeamentos anteriores).
- [x] Staging de terreno em `scripts/regions/stage_johto.py`, somente em `.blue-work`, sem eventos nem músicas, com proteção dos arquivos originais.
- [x] Verificador `scripts/regions/verify_johto.py` e testes sintéticos `tests/test_johto_map_plan.py` e `tests/test_johto_stage.py`.
- [x] [Documento detalhado da Etapa 03](JOHTO_FASE_03_PREVIA_SEGURA.md) com comandos, critérios e limites.
- [ ] Gerar cópia isolada a partir dos **mapas reais de Johto**; sem a fonte externa validada o staging real permanece bloqueado.
- [x] Base de seleção de início Johto em `scripts/battle_polish/RegionStart.rb`, com guardas por marcador regional, instalação e mapa existente, sem liberar a região antes da instalação real.
- [x] Regressões Ruby ampliadas em `tests/region_start_runtime.rb` para início sintético Johto, segurança de Kanto/Decades e saves.
- [x] [Documento da Etapa 04 parcial](JOHTO_FASE_04_BASE_DO_INICIO.md).
- [x] **scripts/regions/JohtoPilot.rb** criado com diálogos da mãe e de Elm, escolha segura de Chikorita/Cyndaquil/Totodile e combate com rival guardado até treinador PBS efetivo.
- [x] O progresso de história fica em `blue_regions["johto_pilot"]` e não altera os marcadores de Kanto ou o save Decades.
- [x] Teste Ruby puro `tests/johto_pilot_runtime.rb`, incorporado à regressão Python em `tests/test_johto_story_runtime.py`.
- [x] Extrator **ZIP local** `scripts/regions/prepare_johto_source.py` e testes `tests/test_johto_source_prepare.py` com lista segura de RMXP/PNG, hashes e proteção contra diretórios externos e symlinks.
- [x] [Estudo do núcleo New Bark + entrada segura do ZIP](JOHTO_FASE_04_EVENTOS_NEW_BARK.md).
- [ ] Fazer o vínculo real dos eventos em New Bark e do rival aos mapas e treinadores PBS da cópia isolada, somente após auditoria do mapa original.
- [ ] Criar New Bark, casa, laboratório de Elm, rival e inicial **realmente jogáveis** após auditar a fonte; não escrever em Decades/Kanto.
- [x] **Etapa 05 iniciada:** `scripts/regions/JohtoViolet.rb` implementa introdução a Violet, batalha do ancião Li e Falkner com Zephyr registrada pela API regional; não carrega no jogo mestre.
- [x] Testes `tests/johto_violet_runtime.rb` e `tests/test_johto_violet_runtime.py` criados para derrota/vitória, insígnia única, esmeraldas, Rock Smash e save/reload.
- [x] `data/regions/johto-phase05.json` define caminho New Bark → Route 29 → Cherrygrove → Routes 30–31 → Violet e interiores sem alegar MapIDs reais, com `tests/test_johto_phase05_contract.py` validando o contrato.
- [x] [MD de Violet City/Falkner e critérios de aceite](JOHTO_FASE_05_VIOLET_FALKNER.md).
- [ ] Montar mapas reais, PBS dos treinadores, transições e jogar o trecho completo no Game.exe isolado; somente então finalizar Etapa 05.
- [x] **Etapa 06 iniciada:** `scripts/regions/JohtoAzalea.rb` implementa chegada a Azalea, missão do Kurt, dois Rockets, Proton, Bugsy, HIVE e rival com marcadores de PBS isolados.
- [x] `tests/johto_azalea_runtime.rb` e `tests/test_johto_azalea_runtime.py` verificam pré-requisitos, perdas, vitórias, não duplicação de HIVE/esmeraldas, Cut, save/reload e nenhuma alteração em Kanto/Decades.
- [x] `data/regions/johto-phase06.json` descreve Route 32 → Union Cave → Route 33 → Azalea, seus interiores e a ligação futura com Ilex Forest, sem fingir MapIDs reais.
- [x] `tests/test_johto_phase06_contract.py` garante o contrato HIVE/CUT, origem Violet, treinadores previstos e marcadores de integração desativados.
- [x] [MD de Azalea/Slowpoke Well/Bugsy e critérios de aceite](JOHTO_FASE_06_AZALEA_BUGSY.md).
- [ ] Conectar mapas e eventos reais de Azalea, Union Cave, Slowpoke Well, Rocket e Ginásio de Bugsy em piloto separado; compilar equipes PBS e testar a jornada dentro do Game.exe.
- [x] **Etapa 07 iniciada:** `scripts/regions/JohtoGoldenrod.rb` adiciona lenhador e Farfetch'd em duas etapas, premiação Cut condicionada ao item real, Route 34/Day Care, quiz da Rádio, Whitney/PLAIN, Floricultura e Sudowoodo futuro em código isolado.
- [x] `tests/johto_goldenrod_runtime.rb` e `tests/test_johto_goldenrod_runtime.py` simulam puzzle, itens, perdas e vitórias, PLAIN única, Cut/Strength, save/reload e isolamento Kanto/Decades.
- [x] `data/regions/johto-phase07.json` define trajeto simbólico Azalea → Ilex → Route 34 → Goldenrod, incluindo interiores, sem MapIDs fictícios ou integração prematura; contrato testado em `tests/test_johto_phase07_contract.py`.
- [x] [MD da Etapa 07 e critérios de aceitação](JOHTO_FASE_07_ILEX_GOLDENROD_WHITNEY.md).
- [ ] Importar mapas reais de Ilex/Goldenrod, modelar movimentação dos Farfetch'd, compilar PBS, conectar NPCs e testar Whitney e save no Game.exe isolado.
- [x] **Etapa 08 iniciada:** `scripts/regions/JohtoEcruteak.rb` prepara Rotas 35–37, National Park introdutório, bloqueio de Sudowoodo, Burned Tower, rival, despertar simbólico, Rocket do Dance Theater, Morty/FOG e Surf local.
- [x] `tests/johto_ecruteak_runtime.rb` e `tests/test_johto_ecruteak_runtime.py` validam derrotas, vitórias, itens, FOG única, Surf, save/reload e ausência de efeitos em Kanto/Decades.
- [x] `data/regions/johto-phase08.json` descreve a topologia planejada Goldenrod → Rota 35 → Rota 36 → Rota 37 → Ecruteak, National Park, torres e interiores sem alegar MapIDs reais.
- [x] `tests/test_johto_phase08_contract.py` protege o contrato de FOG/SURF e o estado não integrado, mantendo competições/lendários como pendências explícitas.
- [x] [MD da Etapa 08 e critérios de aceitação](JOHTO_FASE_08_ECRUTEAK_MORTY.md).
- [ ] Implantar mapas originais validados, rotas físicas, National Park, Burned Tower, treinadores PBS, prêmio Surf real e testar Morty no piloto executável isolado.
- [x] **Etapa 09 iniciada:** `scripts/regions/JohtoOlivineCianwood.rb` prepara Ecruteak → Rotas 38/39 → Olivine, farol (6 andares), pedido de medicina por Jasmine, Surf nas Rotas 40/41, farmácia de Cianwood, Chuck/STORM, Fly e retorno com medicina.
- [x] `tests/johto_olivine_cianwood_runtime.rb` e `tests/test_johto_olivine_cianwood_runtime.py` validam travas, vitória/derrota, itens únicos, FOG/STORM, Fly, save/reload, cura não antecipada e isolamento Kanto/Decades.
- [x] `data/regions/johto-phase09.json` define percurso e interiores simbólicos, sem fingir MapIDs reais; `tests/test_johto_phase09_contract.py` valida o contrato e bloqueia declaração prematura de etapa jogável.
- [x] [MD da Etapa 09 com requisitos de entrada, equipe PBS, Lighthouse, medicina e transição para Jasmine](JOHTO_FASE_09_OLIVINE_CIANWOOD_CHUCK.md).
- [ ] Conectar mapas e eventos reais Olivine/Lighthouse/Cianwood, compilar PBS, auditar SecretPotion e HM Fly e testar Chuck/STORM/Surf no Game.exe, sem curar Ampharos na fase 09.
- [x] **Etapa 10 iniciada:** `scripts/regions/JohtoJasmine.rb` prepara consumo único da SecretPotion por Jasmine, cura lógica de Ampharos, ginásio, MINERAL como 6ª insígnia e bloqueio das Whirl Islands sem mapas.
- [x] `tests/johto_jasmine_runtime.rb` e `tests/test_johto_jasmine_runtime.py` verificam requisitos do pedido/retorno, inventário com remoção confirmada, cura única, PBS/derrota/vitória de Jasmine, badge/esmeraldas, save/reload e isolamento Decades/Kanto.
- [x] `data/regions/johto-phase10.json` delimita mapas simbólicos, estados das quatro entradas das Whirl Islands, tokens de prontidão e aceite pendente; `tests/test_johto_phase10_contract.py` protege o contrato.
- [x] [MD da Etapa 10 — Jasmine, Ampharos, MINERAL e Whirl Islands](JOHTO_FASE_10_JASMINE_AMPHAROS_MINERAL.md).
- [ ] Verificar item/bag de Essentials real, integrar física e NPCs de Olivine, PBS de Jasmine, mapas das ilhas e testar no Game.exe antes de concluir a Etapa 10.
- [x] **Etapa 11 iniciada:** `scripts/regions/JohtoMahogany.rb` prepara Mahogany/Lake of Rage, Red Gyarados com resultado auditável, Lance, Rocket HQ, Electrode, Pryce/GLACIER, Whirlpool e Radio Tower após a sétima insígnia.
- [x] `tests/johto_mahogany_runtime.rb` e `tests/test_johto_mahogany_runtime.py` cobrem fuga, derrota/vitória, Rocket, recompensas únicas, GLACIER, Whirlpool, save/reload e isolamento Kanto/Decades.
- [x] `data/regions/johto-phase11.json` descreve Ecruteak → Route 42 → Mahogany → Route 43 → Lake of Rage, HQ, ginásio e Radio Tower com nós simbólicos sem MapIDs reais.
- [x] `tests/test_johto_phase11_contract.py` verifica treinadores PBS, itens, encontros e bloqueios de liberação.
- [x] [MD da Etapa 11 — Mahogany, Equipe Rocket, Pryce e GLACIER](JOHTO_FASE_11_MAHOGANY_ROCKET_PRYCE.md).
- [ ] Integrar mapas e eventos reais, compilar PBS, validar Gyarados/Electrode, HQ, Pryce, Whirlpool e Radio Tower no Game.exe antes de concluir 11/16.
- [x] **Etapa 12 iniciada:** `scripts/regions/JohtoBlackthorn.rb` prepara Rota 44, Ice Path com slide e quatro rochas, Waterfall condicionado ao item real, Blackthorn, puzzle de Clair, Dragon's Den/Master e RISING como oitava insígnia.
- [x] `tests/johto_blackthorn_runtime.rb` e `tests/test_johto_blackthorn_runtime.py` cobrem ferramentas Strength/Whirlpool/Waterfall, derrotas, vitórias, teste do Dragon Master, RISING única, 8 insígnias e saves isolados de Decades/Kanto.
- [x] `data/regions/johto-phase12.json` define mapa simbólico de Ice Path/Blackthorn/Dragon's Den, Rota 45/46 e Dark Cave bloqueada, sem MapIDs; `tests/test_johto_phase12_contract.py` verifica a integridade.
- [x] [MD da Etapa 12 — Ice Path, Clair, Dragon Master e Rising](JOHTO_FASE_12_ICE_PATH_BLACKTHORN_CLAIR.md).
- [ ] Integrar mapas e puzzles físicos, compilar PBS de Clair, validar Waterfall real, entrega pós-Master de RISING e acesso à Liga em Game.exe antes de concluir a etapa.
- [x] **Etapa 13 iniciada:** `scripts/regions/JohtoLeague.rb` prepara New Bark → Route 27 → Tohjo Falls → Route 26 → Victory Road e rival → Indigo Plateau, Elite Will/Koga/Bruno/Karen/Lance e Hall of Fame condicionado à confirmação real.
- [x] `tests/johto_league_runtime.rb` e `tests/test_johto_league_runtime.py` verificam insígnias, Surf/Waterfall, ordem e reinício da Elite após derrota, Lance, Hall of Fame falho/cancelado, conclusão única, save/reload e preservação da Liga Kanto.
- [x] `data/regions/johto-phase13.json` relaciona mapas/salas simbólicos e a separação do Indigo Plateau geográfico das campanhas de Johto/Kanto; `tests/test_johto_phase13_contract.py` valida o contrato.
- [x] [MD da Etapa 13 — Liga de Johto, Elite Four, Lance e Hall of Fame](JOHTO_FASE_13_LIGA_ELITE_FOUR_LANCE.md), com desbloqueio de Kanto/Hoenn apenas no estado e não como viagem.
- [ ] Integrar mapas e corredores reais, compilar PBS da Elite/Rival, confirmar gravação verdadeira de Hall of Fame, criar NPC pós-Liga em New Bark e validar Box/viagem antes do aceite 13/16.
- [x] **Etapa 14 iniciada:** `scripts/regions/JohtoLegendaries.rb` prepara escolha HG/SS/Crystal, Raikou/Entei com confirmação de roamer, Kimono Girls, Bell Tower/Ho-Oh, Whirl Islands/Lugia e Ruins of Alph sem encontros fictícios.
- [x] `tests/johto_legendaries_runtime.rb` e `tests/test_johto_legendaries_runtime.py` simulam capturas, fugas, derrotas, retorno de lendários por Hall of Fame comprovado, Wings/Bells únicos, versões independentes, save/reload e isolamento Decades/Kanto.
- [x] `data/regions/johto-phase14.json` mapeia topologia simbólica de torres, quatro entradas de Whirl Islands com saídas seguras, Ruins of Alph, Mt. Silver indisponível e diferenças de história HGSS/Crystal.
- [x] `tests/test_johto_phase14_contract.py` verifica os estados bloqueados, versões, itens e a divergência canônica HGSS (mascote antes da Liga) a corrigir antes da integração final.
- [x] [MD da Etapa 14 — lendários e pós-jogo](JOHTO_FASE_14_LENDARIOS_POS_JOGO.md).
- [ ] Integrar mapas licenciados/MapIDs verificados, callbacks de captura, roamers reais, Suicune/Eusine por versão, cinco PBS Kimono, Unown e recurso legal de Mt. Silver/Red; testar tudo no Game.exe.
- [x] **Etapa 15 iniciada (M0–M6):** `data/johto-music.json` cataloga 42 BGM + 11 ME planejados e `data/johto-music-rules.json` descreve 35 áreas, 10 batalhas, 11 ME e 7 cenas; **todas desativadas**, sem arquivo ou licença presumidos.
- [x] `scripts/music/audit_johto_phase15.py` impede habilitação de áudio sem origem, direitos, MapIDs, região e fallback; `tests/test_johto_phase15_contract.py` verifica integridade e isolamento Kanto/Decades.
- [x] Portal: `site/public/data/johto-preview.json` reúne 148 locais simbólicos e 36 tipos de treinadores, incluindo oito líderes, sem teams PBS inventados; `site/src/assets/johto.js`, `app.js`, `regions.js` e `styles.css` expõem os filtros `?regiao=johto` como prévia explícita.
- [x] [MD da Etapa 15 — Músicas, treinadores e portal](JOHTO_FASE_15_MUSICAS_TREINADORES_PORTAL.md), com checklist M0–M6, entregas e provas de aceite.
- [ ] Receber áudio com licença e SHA-256, compilar mapas e PBS reais e completar o sistema de BGM/ME, equipes normal/Master e habitats no Game.exe antes de declarar a etapa concluída.
- [x] **Etapa 16 iniciada:** `scripts/regions/install_johto.py` audita as 16 fases em **dry-run**, identifica impedimentos materiais e recusa `--apply` sem instalador transacional revisado.
- [x] `RegionStart.rb` exige 13 evidências, SHA-256 dos arquivos de mapa e posições separadas de casa, chegada e NPC antes de habilitar Johto; manifesto vazio `{}` não funciona.
- [x] `RegionTravel.rb` suporta viagem Kanto↔Johto **somente com release comprovado** e após Liga da região de origem, NPC em New Bark e rollback/PC; Hoenn continua sem destino instalado.
- [x] `tests/region_start_runtime.rb`, `tests/region_travel_runtime.rb` e `tests/test_johto_phase16_release.py` validam gates, variações de save, Box, rollback e relatório dos bloqueios.
- [x] [Schema da prova de release](../data/regions/johto-release-proof.schema.json), [MD da Etapa 16](JOHTO_FASE_16_INTEGRACAO_E_ACEITE.md) e [matriz E2E](JOHTO_TESTES_E2E.md) publicados.
- [ ] Criar instalador **transacional de verdade** com backups/rollback em cópia isolada, **após** obter Map Pack com direitos/hashes, eventos, PBS, músicas e prova Windows/JoiPlay; não emitir marcadores de aprovação antes disso.

**Limitação atual:** o GitHub não inclui os arquivos reais da instalação game/, da fonte RMXP nem dos saves. O pacote é hospedado externamente via Mega e o arquivo não foi obtido nesta etapa. Não foram inventados MapIDs, hashes ou evidências de jogabilidade.

## Estado das 16 etapas

| Etapa | Núcleo | Estado |
|---|---|---|
| 01 | Fonte, direitos e baseline | **PARCIAL**: manifesto criado; fonte real, hash e direitos pendentes |
| 02 | Auditoria RXDATA e dependências | **PARCIAL**: scanner/testes criados; fonte real e validação pendentes |
| 03 | Importador isolado e prévia | **PARCIAL**: código e testes sintéticos; pacote, IDs e prévia reais pendentes |
| 04 | New Bark, casa, Elm e inicial | **PARCIAL**: início condicionado, roteiro de Elm/mãe/iniciais/rival e testes Ruby; eventos ainda sem mapas reais e sem piloto jogável |
| 05 | Violet e Falkner | **PARCIAL**: lógica de ginásio/Torre Sprout, insígnia e rota simbólica prontas; faltam mapas reais, PBS e gameplay |
| 06 | Azalea e Bugsy | **PARCIAL**: arco Kurt/Rocket, Bugsy/HIVE, Cut e rota simbólica com testes; faltam fonte, mapas reais, PBS e gameplay |
| 07 | Goldenrod e Whitney | **PARCIAL**: Ilex/Farfetch'd, Cut, Rádio, Whitney/PLAIN e mapa simbólico programados; faltam mapas reais, PBS e gameplay |
| 08 | Ecruteak e Morty | **PARCIAL**: eventos das rotas, Burned Tower, rival, Rocket, FOG/Surf e topologia simbólica; faltam fonte, mapas, PBS e gameplay |
| 09 | Cianwood e Chuck | **PARCIAL**: rotas Olivine/Cianwood, farol, medicina, Chuck/STORM, Surf/Fly e contrato simbólico; faltam mapas, PBS e gameplay |
| 10 | Olivine e Jasmine | **PARCIAL**: cura segura de Ampharos, Jasmine/MINERAL, inventário e Whirl Islands bloqueadas com testes; faltam Map Pack, PBS e jogo real |
| 11 | Mahogany, Rocket e Pryce | **PARCIAL**: Lake of Rage, Rocket HQ, Pryce/GLACIER, Whirlpool e Radio Tower preparados; faltam mapas, PBS e gameplay |
| 12 | Blackthorn e Clair | **PARCIAL**: Ice Path/Strength/Waterfall, Clair, Dragon Master/RISING e preparação da Liga em testes isolados; faltam mapas, PBS e gameplay |
| 13 | Liga Johto e Lance | **PARCIAL**: Tohjo, Victory Road, Elite Four/Lance, Hall of Fame protegido e unlock Kanto/Hoenn no save em código/testes; mapas e gameplay pendentes |
| 14 | Lendários e pós-jogo | **PARCIAL**: versões HG/SS/Crystal, Raikou/Entei, Kimono, Ho-Oh/Lugia e Ruins com lógica/testes; Suicune, mapas, Mt. Silver e gameplay pendentes |
| 15 | Música, treinadores e portal | **PARCIAL**: 53 cues sem áudio, regras M0–M6 desativadas, auditor, prévia de 148 mapas simbólicos/36 treinadores e UI Johto; faltam MapIDs, arquivos licenciados, PBS e gameplay |
| 16 | Instalação, viagem e aceite final | **PARCIAL**: preflight dry-run e 13 provas, hashes, viagem Kanto↔Johto guardada, NPC New Bark e testes; falta instalação transacional real e gameplay |

## Regras obrigatórias antes de importar qualquer mapa

1. Não alterar nenhum MapID de Kanto/Decades; atribuir IDs de destino livres e fixos para Johto.
2. Não copiar MapInfos.rxdata, Tilesets.rxdata, Scripts.rxdata ou System.rxdata sobre game/. Reconstruir IDs/conexões com logs e rollback.
3. Piloto em .blue-work/johto-pilot, com saves separados. O botão **Testar Johto** nunca pode abrir Kanto como fallback.
4. Só liberar Johto como região inicial quando New Bark, a casa e a introdução estiverem prontas, com testes observáveis.
5. Comparar testes e hashes antes/depois de mudanças em plugins e mapas compartilhados. CI verde de um teste não valida toda a jogabilidade.
6. Não publicar músicas oficiais ou componentes de terceiros sem direitos e créditos verificados.

## Comandos quando a fonte local estiver disponível

Colocar o Map Pack extraído em .blue-work/johto-source (ou em subdiretório com Data/) e executar:

~~~powershell
# Somente leitura: não modifica game/ nem a fonte
python scripts/regions/audit_johto.py --source ".blue-work/johto-source" --game "game" --output ".blue-work/johto-audit.json"

# Testes sintéticos offline
python -m unittest discover -s tests -p "test_johto_source_audit.py" -v

# Regressão da tela e do circuito existente
python -m unittest discover -s tests -p "test_title_kanto.py" -v
python -m unittest discover -s tests -p "test_regions.py" -v
~~~

O auditor nunca instala conteúdo e grava apenas um JSON em .blue-work/. Se a saída já existir com dados diferentes, não a sobrescreve: use outro nome. Se a fonte real estiver ausente, falha explicitamente em vez de produzir mapa fictício.

## Critérios para aceitar a Etapa 01

- [ ] Fonte RMXP original preservada com SHA-256 e proveniência validada.
- [ ] Créditos e direitos revisados por recurso; sem republicação não autorizada.
- [ ] MapIDs/tile IDs de Johto e do jogo instalado inventariados.
- [ ] Risco de sobrescrita removido, rollback e cópia isolada definidos.
- [ ] Testes automatizados concluídos sem regressão e evidências documentadas.

**Próxima ação:** preparar o ZIP legítimo com `prepare_johto_source.py`, conferir SHA-256, credenciais de uso de artes e os IDs originais; então executar `audit_johto.py`, `plan_johto.py`, `stage_johto.py` e `verify_johto.py` sobre o pacote real e a instalação local, de acordo com [a Etapa 03](JOHTO_FASE_03_PREVIA_SEGURA.md). Depois, ligar os eventos já preparados aos interiores de New Bark dentro de um piloto isolado. O botão de nova partida em Johto e o teste executável continuam bloqueados enquanto esses mapas reais não forem validados.

## Implementação iniciada — inventário físico de conteúdo RMXP (13/11/2026)

**Entrega em código, ainda sem Map Pack externo:** [inventory_johto.py](../scripts/regions/inventory_johto.py) é um scanner complementar a [audit_johto.py](../scripts/regions/audit_johto.py). Ele analisa **cada mapa e suas páginas de eventos**, incluindo coordenadas, triggers, contagens de diálogo, comandos de batalha, mudanças de itens, transferência, scripts de origem não confiáveis e avisos de MapIDs ausentes/XY inválidos. Nunca executa scripts externos e não copia diálogos, sprites ou eventos para o jogo.

- [x] [johto-area-scope.json](../data/regions/johto-area-scope.json): 80 áreas/interiores obrigatórios de referência inicial (HGSS e variantes), incluindo ginásios, casas cruciais e Mt. Silver. **São aliases candidatos, não mapas confirmados.**
- [x] [test_johto_content_inventory.py](../tests/test_johto_content_inventory.py): fixtures RMXP artificiais, teste de integridade SHA-256, comando Ruby não executado, itens/treinadores/warps e prova de que nenhum conteúdo é declarado jogável.
- [ ] Executar o inventário com pacote **real** obtido e auditado localmente, e preencher manualmente o mapeamento Johto vs. mapas Kanto misturados na fonte.
- [ ] Reconstruir integralmente os NPCs/itens/eventos HGSS por local e conectá-los ao motor Blue via Game.exe; o scanner não faz isso sozinho.

No Windows, o novo atalho [JOHTO_PREPARAR_MAPAS.bat](../JOHTO_PREPARAR_MAPAS.bat) executa a extração ZIP, auditoria e inventário **somente em .blue-work/**, exigindo fonte e instalação local presentes. Ele não instala mapas. Alternativamente, após preparar o ZIP verdadeiro e rodar `audit_johto.py`, executar:

~~~powershell
python scripts/regions/inventory_johto.py --source ".blue-work/johto-source" --audit ".blue-work/johto-audit.json" --output ".blue-work/johto-content-inventory.json"
python -m unittest discover -s tests -p "test_johto_content_inventory.py" -v
~~~

Os eventos de origem são **metadados de auditoria**, não prova de uma campanha completa. A fonte, a instalação local `game/`, as músicas e os PBS reais continuam ausentes neste repositório. Portanto, as barras de aceitação **permanecem 0/16 em ambas** e `install_johto.py --apply` continua bloqueado.

## Etapa física 04 — compilador seguro dos primeiros eventos (13/11/2026)

**Novo código publicado na branch de implementação:**

- [scripts/regions/build_johto_events.py](../scripts/regions/build_johto_events.py): cria `RPG::Event` e `RPG::Event::Page` **autorais** (mother, Elm, escolha de inicial, rival e teletransportes); grava somente mapas derivados em nova pasta de `.blue-work/`, sem alterar a instalação. Scripts de evento limitados a `BlueJohtoPilot.mother`, `elm`, `choose_starter` e `rival`. Não importa código, flags ou áudio de terceiros.
- [data/regions/johto-new-bark-events.json](../data/regions/johto-new-bark-events.json): **cinco mapas simbólicos** (quarto 2F, casa 1F, cidade, laboratório e Route 29) e **12 eventos planejados**. Todos os `map_id`, SHA, `x/y`, posições de chegada e sprites ainda necessitam auditoria real. **Nenhuma posição fictícia foi gravada**.
- [tests/test_johto_event_build.py](../tests/test_johto_event_build.py): testes de serialização de eventos e warps, handler allowlist, proteção anti-overwrite, bytes idênticos de cenário, integridade de hash e recusa de publicação em `game/`.

**Fluxo futuro quando `johto-staging-v1` for obtido com mapas verdadeiros e aprovados:**

1. Conferir em janela de mapa o quarto, 1F, laboratório, rua e Route 29; identificar IDs correspondentes. **Interiores eventualmente ausentes do Map Pack terão de ser criados e auditados antes**.
2. Preencher `map_id`, `map_sha256` e as posições verificadas no JSON, com sprites realmente disponíveis na instalação. Para cada warp, verificar que o ponto de chegada não colide com parede/NPC.
3. Rodar `python scripts/regions/build_johto_events.py --preview ".blue-work/johto-staging-v1" --spec "data/regions/johto-new-bark-events.json" --output ".blue-work/johto-new-bark-events"`; o destino deve ser **novo**.
4. O resultado `AUTHORED_EVENT_MAPS_NOT_PLAYABLE` ainda depende dos PBS reais do rival, sprites, integração no piloto, eventos de saída/entrada, compilação Essentials, saves, QA Windows/JoiPlay e direitos de redistribuição. **Não executar `install_johto.py --apply`**.

**Status oficial:** fases 01–04 continuam **PARCIAIS**, barras **0/16 aprovadas**. O compilador valida somente serialização/contratos em sintéticos; a batalha continua sendo a de Decades/Blue e os scripts `JohtoPilot.rb` ainda não foram montados em um Game.exe de Johto.

## Batalha inicial — três versões do rival (implementação preparatória)

- [scripts/regions/draft_johto_rival_pbs.py](../scripts/regions/draft_johto_rival_pbs.py) gera `trainer_types_johto.txt` e `trainers_johto.txt` em `.blue-work/johto-rival-pbs/PBS/` **somente após ler a Pokédex e o tipo RIVAL1 verdadeiros do jogo local**.
- Mapeamento seguro no nível 5: jogador Chikorita → rival Cyndaquil (v0); jogador Cyndaquil → rival Totodile (v1); jogador Totodile → rival Chikorita (v2). O script respeita `TrainerBattle.start(:BLUE_JOHTO_RIVAL, "Rival", version)` que já está em `JohtoPilot.rb`.
- Testes: [test_johto_rival_pbs_draft.py](../tests/test_johto_rival_pbs_draft.py). São rascunhos compatíveis com o PBS do Blue, não batalhas efetivamente compiladas.

~~~powershell
python scripts/regions/draft_johto_rival_pbs.py --game "game" --output ".blue-work/johto-rival-pbs"
python -m unittest discover -s tests -p "test_johto_rival_pbs_draft.py" -v
~~~

**Critério de aceite ainda aberto:** conferir trainer graphic e áudio, compilar as três versões na **cópia isolada**, executar uma luta por versão, salvar e recarregar e só depois ativar o marcador `blue-johto-rival-ready.txt` **no piloto**. Nenhum desses testes reais ocorreu nesta fase.

## Continuação da Etapa 04 — montagem de piloto isolado em New Bark (13/11/2026)

Nova base de **cópia experimental compilável**, sem aprovar Johto nem alterar Kanto/Decades:

- [scripts/regions/pilot_johto.py](../scripts/regions/pilot_johto.py) cria **somente** `.blue-work/johto-pilot/` a partir de `game/` + prévia geométrica auditada + eventos próprios; mescla MapInfos/Tilesets, instala 3 versões PBS do rival, duplica retrato nativo de rival e copia os handlers `BlueJohtoPilot` em plugin experimental. Se qualquer validação falhar, não publica a pasta final.
- [scripts/regions/JohtoPilotStart.rb](../scripts/regions/JohtoPilotStart.rb) é inserido **somente na cópia do piloto**, junto aos handlers. Permite teste de início no quarto com manifesto `EXPERIMENTAL_UNTESTED`, hash dos mapas, System e PBS e save isolado. Não cria nem afrouxa `VERIFIED_PLAYABLE` ou os 13 gates de release do jogo principal.
- [data/regions/johto-new-bark-events.json](../data/regions/johto-new-bark-events.json) exige campo `start` dentro do quarto com `verified_position` e `passability_verified`. **Continuam explicitamente pendentes** até inspeção da fonte verdadeira.
- [tests/test_johto_pilot_assembly.py](../tests/test_johto_pilot_assembly.py) verifica integralidade dos dados, hashes, retorno de cada warp, separação de save, rollback em falha e início Ruby com prova local; os mapas dos testes são **artificiais**.

**Comando após concluir a importação real de New Bark, casa e laboratório:**

~~~powershell
python scripts/regions/pilot_johto.py --game "game" --preview ".blue-work/johto-staging-v1" --spec "data/regions/johto-new-bark-events.json" --output ".blue-work/johto-pilot"
~~~

O comando cria uma **cópia nova** e não substitui saída anterior. Somente se a auditoria real, os direitos locais, as posições e o estado do motor confirmarem as pré-condições poderá gerar uma pasta executável para testar manualmente `.blue-work/johto-pilot/Game.exe`.

**Bloqueios honestos:** não existe pacote de mapas HGSS confirmado no repositório, interiores ausentes (quarto/casa/lab), sprites e coordenadas não foram auditados, `TrainerBattle` de rival ainda não recebeu teste nativo, nem saves Johto verificados. Não criar `blue-johto-rival-ready.txt` nem publicar `JOHTO_JOGAR_EXPERIMENTAL.bat` enquanto o piloto real não iniciar corretamente — o atalho do menu principal não deve fechar a partida do usuário se o build falhar. **Barras oficiais ainda 0/16 e 0/16.**

## Continuação da Fase 03–04 — interiores físicos de New Bark com templates nativos (13/11/2026)

Entregue um gerador **de geometria real RMXP, ainda em prévia**, para as salas que o Map Pack HGSS provavelmente não contém. O gerador não inventa posição de porta nem declara fidelidade visual HGSS:

- [build_johto_interiors.py](../scripts/regions/build_johto_interiors.py): a partir de uma `johto-stage.json` válida e do jogo original, clona três mapas **nativos e previamente revisados** para quarto 2F, casa 1F e laboratório de Elm. Preserva camadas `RPG::Map/@data` (RMXP Table tridimensional), tilesets, autotiles e formatos de colisão da própria base; remapeia IDs/tileset de forma isolada e limpa todos os eventos, encontros e BGM/BGS antigos. Gera apenas **nova prévia**, não `Game.exe`.
- [johto-interior-templates.json](../data/regions/johto-interior-templates.json): três fontes nativas, MapIDs/destinos e SHA-256 **nulos** até localizar os layouts verdadeiros e confirmar sua geometria. Impede sobrescrever mapas já presentes no pack ou base. Quarto tem como parent a casa 1F, demais interiores têm como parent New Bark.
- [test_johto_interior_authoring.py](../tests/test_johto_interior_authoring.py): testes de clone e roundtrip RMXP Table, ausência de eventos/músicas, integridade do game/base Kanto e da prévia de origem, SHA, autotiles, colisões de IDs e rollback.
  
### Execução local condicionada à origem real

1. Concluir `JOHTO_PREPARAR_MAPAS.bat` e `stage_johto.py` com pack/pasta originais autorizados e SHA-256 fixado em `data/regions/johto-source.json`. A etapa de interiores **não substitui** auditoria de mapas externos.
2. Procurar no `game/Data` três **mapas nativos de interiores realmente existentes**, documentar `native_map_id`, SHA-256 do `MapNNN.rxdata`, `destination_id` único (600–999), `native_template_reviewed=true` e `room_geometry_reviewed=true` **apenas após verificação visual de cada sala**.
3. Executar `python scripts/regions/build_johto_interiors.py --preview ".blue-work/johto-staging" --game "game" --layouts "data/regions/johto-interior-templates.json" --output ".blue-work/johto-staging-interiors"`; a pasta de saída deve ser nova. A ferramenta reexecuta a verificação estrutural `verify_johto.py` no resultado.
4. **Redesenhar a geometria das salas segundo HGSS/Johto quando necessário**. Examinar porta, escada, caminhos andáveis, spawn e ponto de chegada; conferir sprites. Somente então preencher `johto-new-bark-events.json` com ID/hash `MapXXX`, NPCs, eventos, XY e `verified_position=true`. O piloto só pode ser montado depois disso.

**Limitação:** clonagem de interiores Decades **não é fidelidade a HeartGold/SoulSilver**; apenas desbloqueia a preparação técnica de um mapa editável. Não declara músicas, itens, eventos, nem um início jogável confirmado. **Barras oficiais permanecem 0/16 + 0/16**, sem alterar o balanceamento ou o motor de batalha.

## Continuação da Fase 03–04 — auditoria de interiores e vínculo automático de New Bark (13/11/2026)

Implementados dois passos adicionais para reduzir trabalho manual **sem inventar coordenadas**:

1. [audit_johto_native_rooms.py](../scripts/regions/audit_johto_native_rooms.py) lê **somente** o `game/Data/Map*.rxdata` real e uma prévia validada. Enumera os interiores compatíveis com a estrutura de tiles RMXP (três camadas), nomes, tamanhos, hashes SHA-256, tipos de tileset e transferências diretas (comando 201). Propõe ordenações por nome para quarto, casa e laboratório, mas todos os candidatos têm `template_reviewed=false` e dependem de inspeção visual; não executa scripts presentes nos eventos da origem. Salva `.blue-work/johto-native-room-candidates.json`.
2. [bind_johto_new_bark.py](../scripts/regions/bind_johto_new_bark.py) só funciona **depois** de `build_johto_interiors.py`. Revalida o staging contra o `game/` original e preenche automaticamente `map_id` + `map_sha256` dos cinco mapas esperados (quarto 2F, casa 1F, cidade, laboratório e Route 29), em **cópia nova** `.blue-work/johto-new-bark-bound.json`. Mantém `x`, `y`, `arrival_x`, `arrival_y`, `sprite`, `verified_position`, `passability_verified` pendentes. Não gera `Game.exe`, saves, prova de release ou marca `VERIFIED_PLAYABLE`.
3. [JOHTO_PREPARAR_NEW_BARK.bat](../JOHTO_PREPARAR_NEW_BARK.bat) divide o processo no Windows em **auditar** (gera relatório e uma cópia editável do manifesto de templates em `.blue-work/`) e **montar** (gera nova prévia dos interiores e vincula MapIDs/hashes; só se a revisão do template estiver marcada corretamente). Falhas interrompem o processo, sem substituir saídas existentes ou alterar `game/`.
4. [test_johto_new_bark_binding.py](../tests/test_johto_new_bark_binding.py) valida a sequência sobre RMXP **sintético**, integridade dos 5 MapIDs, hashes, coords e scripts não certificados, template ausente, regressão de snapshots e o fluxo BAT.

### Próxima execução local quando houver fonte real

```bat
JOHTO_PREPARAR_MAPAS.bat
REM Após selecionar IDs/hash do Map Pack e executar plan_johto.py + stage_johto.py:
JOHTO_PREPARAR_NEW_BARK.bat auditar
REM Revisar .blue-work/johto-native-room-candidates.json e 3 salas-base.
REM Preencher .blue-work/johto-interior-templates-review.json com IDs/hashes reais.
JOHTO_PREPARAR_NEW_BARK.bat montar
REM Inspecionar e preencher coordenadas e sprites no johto-new-bark-bound.json.
```

**As coordenadas não são descobertas automaticamente**: a saída vinculada permanece com o status `MAP_IDS_BOUND_EVENT_POSITIONS_PENDING`. A cópia experimental do `pilot_johto.py` continua bloqueada até que a geometria, as portas e os gatilhos sejam realmente validados. Os binários de `game/` e do Map Pack não estão versionados no GitHub; os testes sintéticos não substituem executar `Game.exe`. **Barras de aceite: 0/16 técnicas e 0/16 gameplay real.**

## Atualização verificada do arquivo real de Johto v1 — 13/11/2026

O usuário forneceu `Remastered Kanto Johto Map Packv1.zip`, que foi efetivamente lido sem executar eventos. Identificados **74 mapas Johto**, **42 conexões de borda** e SHA-256 fixado. [Detalhes completos aqui](JOHTO_AUDITORIA_FONTE_REAL_V1.md). A seleção está congelada em `data/regions/johto-source.json` e a topologia de referência em `data/regions/johto-v1-map-connections.json`. Nenhum `.rxdata` estrangeiro, `.png` ou `.ogg` foi colocado na `main`.

- **Map079 = New Bark Town**, **Map104 = Route 29** (origem), **Map102/103 = Mt. Silver/Mt. Silver Peak**, não presentes no jogo instalado ainda.
- O ZIP contém **0 eventos nos 74 mapas de Johto**. `Map001` ausente é índice Intro não selecionado; `R49Water` ausente e comprovadamente **sem tiles de referência** nesta seleção. O stage permite limpar somente autotile realmente sem uso e rejeita os usados.
- Falta ainda a **instalação local `game/`** para plano de IDs de destino, prévia RMXP com assets, interiores, conversão segura de 42 conexões e testes reais de Game.exe, batalha, save e troca de região.
- **Subtarefas da fonte auditadas:** 74/74 MapIDs identificados e 42/42 linhas de conexões capturadas; esses não são 74 mapas jogáveis. **Barras de gameplay separadas:** 0/13 fases jogáveis (04–16), 0/13 com QA real aprovado. Indicador técnico histórico: 0/16 plenamente aceitas. Testes de código/contratos presentes: 16/16 (não comprovam gameplay).

## Primeira fase jogável — New Bark Town: pipeline de preparação (13/11/2026)

**Objetivo concreto:** fase 04 começar dentro do quarto de New Bark, sair de casa, falar com mãe e Elm, escolher inicial e percorrer Rota 29. Até existir essa sequência no Game.exe, **fase jogável 0/13 e testada 0/13**.

Adicionados recursos técnicos que aproximam do primeiro piloto real, sem alterar Kanto, Decades ou os saves:

- [compile_johto_connections.py](../scripts/regions/compile_johto_connections.py) remapeia para IDs **livres da instalação local** as 42 conexões de borda vindas do ZIP v1 (`79,West,13,104,East,0` é New Bark ↔ Rota 29). O resultado é somente texto de PBS em prévia, não um `Game.exe`. O compilador exige hash do ZIP igual ao manifesto, regiões corretas e todos os destinos existentes, e rejeita referências ao Kanto, arestas duplicadas ou lados inválidos.
- [pilot_johto.py](../scripts/regions/pilot_johto.py) agora aceita `--with-connections` **apenas na montagem experimental**. Mescla as conexões Johto com o `PBS/map_connections.txt` existente **somente na cópia piloto**, preservando as linhas de Kanto/Decades e adicionando hash ao relatório experimental. Isso **não prova** passabilidade, percurso nem spawn no motor.
- [prepare_johto_first_playable.py](../scripts/regions/prepare_johto_first_playable.py) organiza extração segura do ZIP real, auditoria com `game/`, reserva 600–999 sem colisões, staging geométrico e verificação, e geração das 42 conexões. Relatório `.blue-work/johto-first-playable-readiness.json` termina em `GEOMETRY_READY_NEW_BARK_PLAYABILITY_PENDING`, com a lista explícita do que falta.
- [JOHTO_PREPARAR_PRIMEIRA_FASE.bat](../JOHTO_PREPARAR_PRIMEIRA_FASE.bat) executa esse pipeline local no Windows; **nunca inicia Game.exe nem muda a instalação principal**.
- [test_johto_connection_compilation.py](../tests/test_johto_connection_compilation.py) e [test_johto_first_playable_preflight.py](../tests/test_johto_first_playable_preflight.py) verificam importação sintética de 74 mapas, remapeamento de 42 conexões, seleção Johto e não modificação dos dados nativos.

### Para executar com o ZIP real e a instalação Blue/Decades

Colocar os **mesmos bytes** do ZIP v1 em `.blue-work/johto-source/original.zip` e manter a instalação local em `game/` sem modificar seus arquivos originais. Executar `JOHTO_PREPARAR_PRIMEIRA_FASE.bat`. O hash do ZIP é conferido com `johto-source.json`; não enviar binários/tiles sem direitos para o GitHub. A saída e os logs ficam apenas em `.blue-work/`. A extração não instala scripts de terceiros.

**Ainda faltam antes de aumentar a barra JOGÁVEL:** auditar e desenhar os interiores da casa do jogador 2F/1F e laboratório de Elm, resolver sprites e coordenadas reais das portas/NPCs, compilar os handlers/PBS, corrigir a passagem Rota 29 ↔ Cherrygrove ausente da fonte e iniciar/testar Game.exe em **cópia isolada**, incluindo save/reload. Os arquivos `game/Data`, sprites e PBS nativos ainda não foram fornecidos nesta conversa. **Não marcar fase jogável por testes sintéticos.**

## Fase 04 — trabalho concreto sobre as portas do Map079 real (13/11/2026)

**Referência:** [JOHTO_FASE_04_ENTRADAS_REAIS_V1.md](JOHTO_FASE_04_ENTRADAS_REAIS_V1.md).

O ZIP enviado pelo usuário já permitiu **renderizar o New Bark exterior real e identificar quatro candidatos de entrada**, com tiles nas três camadas e hash do Map079: laboratório grande noroeste (5,21), casa nordeste (14,23), casa sudoeste (4,31), casa sudeste (13,33). A ferramenta [audit_johto_new_bark_exterior.py](../scripts/regions/audit_johto_new_bark_exterior.py) agora verifica diretamente os bytes de `Map079.rxdata` e `Tilesets.rxdata` dentro do ZIP e rejeita candidatos alterados/indevidamente aprovados. Comando Windows: [JOHTO_AUDITAR_ENTRADAS_NEW_BARK.bat](../JOHTO_AUDITAR_ENTRADAS_NEW_BARK.bat). O relatório fica em `.blue-work/johto-new-bark-exterior-audit.json`.

O piloto isolado com `--with-connections` foi corrigido para **não duplicar teletransportes** na conexão de borda New Bark–Route29 já fornecida no `map_connections.txt`. Os dois eventos redundantes são removidos **apenas da cópia dos eventos em memória**, preservando origem, Kanto, Decades e o rival. Há testes sintéticos de montagem do piloto com verificações de eventos de borda ausentes e NPCs preservados.

**Não transformar essa auditoria em aprovação de gameplay:** os papéis exatos das casas, o quarto 2F/1F, Elm Lab interior, passabilidade em Game.exe, sprites e saves ainda não foram testados. A fonte fornecida não traz os interiores e o `game/` original ainda não foi entregue. **Barra Jogáveis: 0/13. Barra Testadas: 0/13.** Próximo: obter os dados nativos do motor, validar a casa do jogador, preparar 3 interiores e montar/testar o piloto real.

## Fase 04 — exportador privado de insumos para primeiro piloto (13/11/2026)

Criados [JOHTO_EXPORTAR_BASE_PILOTO.bat](../JOHTO_EXPORTAR_BASE_PILOTO.bat),
[export_johto_pilot_inputs.py](../scripts/regions/export_johto_pilot_inputs.py) e
[guia de envio](JOHTO_FASE_04_ENVIAR_BASE_NATIVA.md). Quando o Blue/Decades estiver instalado
em game/, o usuário poderá gerar somente localmente um ZIP com MapInfos,
Tilesets, System, MapNNN, PBS e gráficos de tiles; modo sprites acrescenta
Characters/Trainers. O ZIP fica ignorado pelo Git e só deve ser compartilhado
em conversa privada. Saves, Game.exe, plugins, scripts e segredos
não são exportados. tests/test_johto_export_pilot_inputs.py verifica esses
limites com fixtures sintéticas, sem assets externos.

**Isso não monta os interiores nem prova a jogabilidade.** Ainda faltam
três interiores auditados, identificar a casa do jogador, confirmar tiles de
porta/spawn, compilar eventos/PBS e testar Game.exe isolado. Barras
**Jogáveis 0/13, Testadas 0/13** até validação nativa.

### Novo gate de aceitação isolada para o primeiro piloto

Adicionados `scripts/regions/inspect_johto_pilot_readiness.py`, `scripts/regions/assemble_johto_first_playable.py` e dois atalhos Windows. A verificação audita os **12 eventos** do início, sua topologia/handlers, spawn, sprites, posições e conexões PBS. O relatório inclui todos os bloqueios, sem aprovar posição por heurística. A montagem só permite uma **cópia experimental em `.blue-work`** quando o próprio estado do mapa e dos eventos confirma pré-requisitos. Nenhum marcador `VERIFIED_PLAYABLE` é produzido.

Próximo bloqueio factual: dados nativos `game/` disponíveis **no Windows do usuário**, seleção auditada de 3 interiores, posições de entrada/chegada e execução real do Game.exe. **Fases JOGÁVEIS 0/13; Fases TESTADAS 0/13.**

### Auditoria dos insumos reais entregues em 13/11/2026

Recebido e verificado em contexto privado o arquivo `johto-pilot-inputs.zip` (SHA-256 `f34b13b56fd42f089c6df525c54e11ad0f5b64acef9027911867efc4be89fee4`), com **2.460 arquivos sem erro de hash**, **207 mapas nativos**, **95 PBS**, gráficos/sprites de `NPC_GSC_Mom`, `NPC_HGSS_Professor_Elm`, `NPC_HGSS_Silver`, `Object_Ball`; `CHIKORITA`/`CYNDAQUIL`/`TOTODILE` e `RIVAL1` presentes. Consulte [auditoria detalhada](JOHTO_FASE_04_AUDITORIA_BASE_NATIVA_20261113.md). A dependência de insumos para **auditoria offline** está satisfeita; o arquivo não contém executável nem plugins e **não** resolve a criação de interiores fiéis, posições/colisões e QA Windows. Fases JOGÁVEIS **0/13**, TESTADAS **0/13**.

### Geração privada de mapa real e geometria interior provisória

Com os ZIPs auditados da fonte e instalação Blue/Decades, gerado **staging privado efetivo** de 74 MapNNN Johto remapeados para IDs 600–673, com 42 conexões PBS e 3 interiores provisórios IDs 674–676. Verificadas reabertura dos 77 RXDATA, integridade de 207 MapInfos e 28 tilesets nativos, zero eventos não-confiáveis importados, e cinco MapIDs/SHA reais vinculados ao template de 12 eventos. Os interiores (cabana, Centro Pokémon e ginásio) são **apenas geometria temporária, não fiéis a HGSS** e não foram testados no Game.exe. Ver [relatório](JOHTO_FASE_04_STAGE_REAL_PRIVADO_77_MAPAS.md). **JOGÁVEIS 0/13 · TESTADAS 0/13**.

### Etapa 05 — duas ligações derivadas offline do próprio terreno de Johto

Com os RXDATA reais do staging privado, o verificador localizou dois corredores **unívocos**, cada um com a assinatura de estrada `[116,96,124]` e flags de direção livres por três linhas × quatro colunas em ambos os mapas: **Route29 (625) ↔ Cherrygrove (601)**, PBS candidato `601,East,12,625,West,0`, e **Route31 (627) ↔ Violet (602)**, PBS candidato `602,East,6,627,West,0`. Agora existe uma sequência topológica *proposta* New Bark → Rota 29 → Cherrygrove → Rota 30 → Rota 31 → Violet, pois as outras três conexões já constam no donor v1. Duas ferramentas Python e nove testes sintéticos validados, além de execução das rotinas de extração de tile dos quatro mapas reais. **Não instalar candidatos na campanha, nem marcar Game.exe jogável/testado.** Ver [documentação](JOHTO_FASE05_CONEXOES_OFFLINE_ATE_VIOLET.md).


## Barra 3 — Desenvolvimento OFFLINE (sem Game.exe)

**5/12 marcos técnicos concluídos (41,7%) — `[###---------]`**

A terceira barra é **independente** das barras **1) Jogáveis 0/13** e **2) Testadas 0/13**. Ela usa `data/regions/johto-progress.json → offline_development`. Foram contabilizados apenas: **1) auditoria dos dados nativos e fonte; 2) staging de 74 mapas mais três salas provisórias; 3) auditoria de duas bordas faltantes**. Essas entregas não significam mapas com eventos jogáveis.

Próximo: **04/12, desenhar o quarto do jogador 2F**. Depois, casa 1F (05), laboratório de Elm (06), portas e spawn (07), eventos (08), PBS de iniciais/rival (09), encontros e treinadores (10), Violet/Sprout/Falkner (11) e auditoria de integração offline (12). Ver [barra e critérios detalhados](JOHTO_BARRA_DESENVOLVIMENTO_OFFLINE.md). **Não executar Game.exe** para completar nenhum dos 12 marcos; isso será avaliado apenas nas barras originais, mais tarde.

### Barra OFFLINE 4/12 — quarto 2F de New Bark concluído

Gerador `scripts/regions/build_johto_bedroom_v1.py`: layout próprio 14×11 no Map674, com cama, escrivaninha, guarda-roupa, janela e escada visual, sem importar eventos; serialização Ruby Marshal testada, 5 cenários automatizados e prévia privada comparada preservando os outros 76 mapas. O quarto ainda não contém warp para 1F, e o spawn é apenas candidato estático. Consulte [fase 04 offline](JOHTO_OFFLINE_FASE_04_QUARTO_2F.md). **OFFLINE: 4/12. JOGÁVEIS: 0/13. TESTADOS: 0/13.**

### Etapa 05/12 OFFLINE — Casa 1F de New Bark construída e auditada

`Map675.rxdata` recriado com 16×13 tiles próprios sobre a base `Inside.png`: cozinha, jantar, área de estar, escada visual, porta e posições candidatas de mãe/chegadas. Os testes offline confirmaram acesso entre cinco posições por 106 tiles estaticamente conectados; 6 testes sintéticos passaram. A prévia Ruby Marshal alterou **somente** Map675 de 77; MapInfos/Tilesets e os outros 76 mapas foram preservados. **Os warps e o NPC ainda não existem** — sem prova jogável ou instalação automática do site. [Ver relatório](JOHTO_OFFLINE_FASE_05_CASA_1F.md). **OFFLINE 5/12 (41,7%). JOGÁVEIS 0/13. TESTADOS NO EXE 0/13.**

### Etapa 06/12 OFFLINE — Laboratório de Elm preparado

O mapa `Map676.rxdata` foi substituído por geometria autoral 20×16 no staging privado: três Poké Bolas realmente visíveis nos tiles (7,6), (10,6), (13,6), bancada para cada inicial, pesquisa, estante, porta visual e proposta de Elm (10,4). Um tileset **privado** (ID 32) reaproveita gráficos nativos sem publicá-los no GitHub. **198 tiles** conectados em auditoria estática; 7 testes Python e roundtrip Ruby Marshal aprovados; apenas Map676 e o acréscimo do novo tileset na cópia privada. **Nenhum evento de escolha, conexão nem QA do Game.exe** ainda. Próximo: **07/12** para warps/portas/spawn; **08/12** para os três eventos das Poké Bolas. [Documentação](JOHTO_OFFLINE_FASE_06_LABORATORIO_ELM.md). **OFFLINE 6/12, JOGÁVEIS 0/13, TESTADAS 0/13.**

### Etapa 07/12 OFFLINE — seis warps de New Bark (escadas e portas)

Gerados em prévia isolada quatro RXDATA com seis eventos `code 201`, todos pareados entre quarto 2F, casa 1F, cidade e laboratório de Elm; posição inicial proposta no quarto `Map674 (6,7)`. A conexão com Route29 foi preservada como borda PBS, sem warp duplicado. Os dados estáticos apontam 81 tiles alcançáveis no quarto, 106 na casa, 228 na cidade e 198 no laboratório, cobrindo todos os gatilhos e chegadas. O teste de roundtrip Ruby Marshal preservou 73 mapas e os metadados nativos. `build_johto_warps_v1.py`, `johto-stage07-warps.json`, 12 casos de teste e [relatório](JOHTO_OFFLINE_FASE_07_PORTAS_ESCADAS_SPAWN.md) publicados. **Instalação do site e gameplay continuam pendentes. OFFLINE 7/12, JOGÁVEIS 0/13, TESTADAS 0/13.**

### Etapa 08/12 OFFLINE — eventos de história criados, warps preservados

O estágio privado de 77 mapas contém mãe na casa 1F (675), Elm e as três bolas interativas no laboratório (676), e Silver na Route 29 (625). **Seis eventos** de ação (`code 355`) foram adicionados aos **seis warps** existentes (`code 201`) da etapa 07, sem apagá-los. As bolas agora são sprites `Object_Ball` em eventos individuais com handler explícito de espécie e sem menu; o `JohtoPilot.rb` impede prêmio duplicado, desautoriza outras regiões e exige a conversa inicial com Elm. Os três tiles visuais antigos foram removidos. Comparação de RXDATA: **74 de 77 mapas preservados**, MapInfos/Tilesets inalterados. A batalha de Silver requer PBS de três versões na etapa 09. [Relatório](JOHTO_OFFLINE_FASE_08_EVENTOS_NEW_BARK.md). Instalação Blue-Story.exe ainda pendente, Game.exe não executado. **OFFLINE 8/12 (66,7%) · JOGÁVEIS 0/13 · TESTADAS 0/13.**

### Etapa OFFLINE 09/12 — PBS do rival Silver preparado

Três versões PBS (0/1/2) de `BLUE_JOHTO_RIVAL,Rival`: Cyndaquil, Totodile e Chikorita respectivamente, todos nível 5 e com golpes realmente aprendidos até esse nível no PBS nativo. A checagem inclui RIVAL1, `pokemon.txt`, `moves*.txt`, colisões e hashes SHA-256; vinculada aos eventos e a três RXDATA privados da etapa 08. A bateria adicionou 10 testes Python e 1 Ruby com três opções de inicial, flags por save e isolamento Kanto/Decades. **Não compilou PBS na engine, nem criou marcador de prontidão; a integração com o `Blue-Story.exe` e o balanceamento dinâmico ainda precisam ser implementados/testados.** [Documentação](JOHTO_OFFLINE_FASE_09_PBS_RIVAL_SILVER.md). **OFFLINE 9/12 (75%) · JOGÁVEIS 0/13 · TESTADAS 0/13.**

### Etapa OFFLINE 10/12 — Rotas 29, 30 e 31 com dados próprios

Gerados seis encontros de dia/noite e cinco treinadores com dez variantes PBS, usando espécie/moves reais do Blue e probabilidades propostas (não canônicas do pacote de mapa). A cópia privada do stage 08 recebeu eventos nos RXDATA Map625, Map626 e Map627; 74 mapas e MapInfos/Tilesets originais sem alterações, Silver preservado. Rota31 Wade foi realocado para uma componente caminhável conectada à de Ian. Foram adicionados testes automatizados Python/Ruby e guardas para que as batalhas não iniciem antes da compilação e QA real. [Relatório 10/12](JOHTO_OFFLINE_FASE_10_ROTAS_29_31.md). O estágio **não é instalado automaticamente** por Blue-Story.exe, e as regras 70/90 + 45 ainda não foram exercitadas no motor. **OFFLINE 10/12 (83,3%), JOGÁVEIS 0/13, TESTADAS EXE 0/13.**
