# Johto — acompanhamento técnico das 16 etapas

**Início:** 12/11/2026  
**Plano mestre:** [JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md)  
**Fontes:** [JOHTO_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md](JOHTO_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md)  
**Estado:** preparação técnica iniciada. Nenhum mapa de Johto foi incorporado ou habilitado para jogar.

## Duas barras separadas

- **Barra 1 — Núcleos implementados e comprovados por testes automatizados:** **0/16 (0%)** — faltam 16.
- **Barra 2 — Etapas integralmente aceitas com gameplay real:** **0/16 (0%)** — faltam 16.

Progresso parcial não é etapa concluída. Nenhum teste sintético ou documento concluído autoriza subir a Barra 2.

## Trabalho inicial de Johto entregue ao GitHub

- [x] Fonte de mundo/tiles selecionada: [Map Pack de Johto de AenaonDogsky](https://www.eeveeexpo.com/resources/828/) — overworld e cavernas de Johto; Mt. Silver não incluído.
- [x] Política de não-regressão para Decades, Kanto, Game.exe, slots, saves, músicas, portal e Blue Studio.
- [x] **data/regions/johto-source.json** criado com fonte e créditos, direitos pendentes, import_enabled=false, mapping_verified=false, maps vazio e hash da fonte ainda desconhecido.
- [x] **scripts/regions/audit_johto.py** criado para ler RMXP em modo somente leitura (sem executar Ruby), inventariar mapas, dimensões, tilesets, eventos, transferências, hashes e colisões com IDs atuais.
- [x] **tests/test_johto_source_audit.py** criado com mapas sintéticos, proteção de hashes, referências faltantes, scripts não executados e teste de fonte ausente.
- [x] **Testar Johto** já está no menu principal junto de **Testar Kanto**. Enquanto o piloto estiver ausente, informa que Johto está em preparação sem usar os arquivos de Kanto.
- [ ] Confirmar arquivo original ZIP/RAR e SHA-256 do Map Pack.
- [ ] Auditar mapa real de origem, permissões separadas de cada arte e inventário da instalação game/ local.
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
| 14 | Lendários e pós-jogo | PENDENTE |
| 15 | Música, treinadores e portal | PENDENTE |
| 16 | Instalação, viagem e aceite final | PENDENTE |

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
