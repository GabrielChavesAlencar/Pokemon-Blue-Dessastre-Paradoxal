# Kanto — etapa 12/16: Cinnabar Island, Pokémon Mansion e Blaine

**Preparação:** 12/11/2026. **Estado:** implementação experimental na branch isolada, condicionada à CI nativa e ao QA manual Windows/JoiPlay.

## Objetivo e isolamento

Continuação após **Saffron City / Sabrina / Silph Co.**. Preservar a execução do Decades, saves existentes, conquistas locais e todos os IDs de mapas já atribuídos pelo piloto de Kanto. A fonte é Essentials FRLG 1.1, fixada pelo SHA-256 em `data/regions/kanto-source.json`. Scripts da fonte não são executados no Blue: portas, quizzes, treinadores e recompensas usam callbacks próprios no `BlueKantoPilot`.

## Mapa de escopo

O catálogo passa de **109 para 126 mapas** sem mudar as atribuições dos primeiros 109. Os **17 mapas acrescentados** vêm dos MapIDs originais 190,191,193–203 e 205–208 (192 e 204 são agrupadores vazios, não mapas jogáveis).

| Fonte FRLG | Local | Estado no piloto |
|---|---|---|
| 190, 191, 198 | Rotas marítimas 19, 20 e 21 | Geometria apenas, sem treinadores ou scripts importados |
| 193–197 | Seafoam Islands, cinco níveis | Geometria apenas, sem Articuno, quebra-cabeça das correntes ou quedas habilitadas |
| 199 | Cinnabar Island | Entradas adaptadas para Center, Mart, Mansion, Gym e Lab |
| 200, 201 | Center e Mart | Cura e loja via callbacks controlados |
| 202 | Ginásio de Blaine | Sete treinadores, Blaine, seis quizzes e seis grupos de portas por self-switch local |
| 203 | Laboratório de Cinnabar | Portas internas auditadas; restauração de fósseis não habilitada |
| 205–208 | Pokémon Mansion 1F/2F/3F/B1F | Escadas/quedas auditadas, sete treinadores, estátuas locais, portas e Secret Key única |

Resultado pretendido: **82 mapas com algum núcleo funcional, 44 `preview_only` sem eventos** (36 anteriores + oito novas prévias marítimas), e **52 atalhos** de teste (43 anteriores + nove novos). A etapa 12 NÃO equivale a Seafoam jogável.

## Contratos de história

1. A entrada do ginásio só permite a passagem após obter a **Secret Key** da Pokémon Mansion B1F; não é inserido item não cadastrado no catálogo nativo.
2. A Secret Key persiste apenas em `blue_regions["pilot_cinnabar_secret_key"]`, com self-switch A, sem prêmio duplicado.
3. O ginásio tem seis perguntas adaptadas. Resposta correta ou vitória no treinador correspondente abre o grupo de portas da sala e registra `pilot_cinnabar_doors`; derrota não abre portas por batalha.
4. Blaine usa a equipe original do arquivo PBS auditado; o balanceamento global **continua sendo o mesmo Decades** (insígnias de todas as regiões somadas às esmeraldas, modo Master e limites existentes).
5. A **Volcano Badge** é concedida apenas após vitória efetiva sobre Blaine via `BlueRegions.award(progress, "KANTO", "VOLCANO")`; no reload, é contada uma única vez e não é escrita sobre os flags nativos do Decades.
6. Treinadores são identificados por `KANTO_<MapID>_<EventID>`, e a página de evento pós-vitória usa self-switch A. Não substituir as equipes-base por versões inventadas nem importar comandos Ruby da fonte.

## Arquivos principais

- `scripts/regions/audit_cinnabar.py`: inventário somente leitura e artefato na CI.
- `data/regions/kanto-source.json`: inclusão da etapa 12 e áreas em prévia.
- `scripts/regions/audit.py`: congelamento explícito dos 109 MapIDs anteriores.
- `scripts/regions/pilot.py` e `KantoPilot.rb`: eventos seguros, mapas, Secret Key, quizzes, batalhas e atalhos.
- `scripts/regions/pbs.py` e `export_kanto.py`: equipes autênticas e dados do portal.
- `scripts/regions/verify_pilot.py`, `KantoNativeCheck.rb`: integração, anti-softlock estrutural, derrota, vitória, self-switch e save/reload.
- `.github/workflows/kanto-pilot-check.yml`: auditoria e testes nativos Windows.

## Teste experimental

No jogo principal, escolha **Testar Kanto** e use **Testes Kanto (experimental)** no menu do piloto isolado. Os nove destinos adicionados são Rota 19, Rota 20, Seafoam 1F, Cinnabar Island, Centro de Cinnabar, ginásio de Blaine, laboratório, Pokémon Mansion 1F e B1F. O teste de referência é **entrar na Mansion, alcançar a Secret Key, entrar no ginásio, resolver quiz ou vencer treinador, derrotar Blaine, salvar, recarregar e confirmar Volcano uma única vez**.

As provas CI simulam resultados de batalha e não comprovam caminhada real, surf, colisões de tiles, menus gráficos nem compatibilidade Android/JoiPlay.

## Pendências para aceite integral

- Verificar entrada e retorno de todas as portas, escadas, quedas da Mansion e passagem a pé, incluindo labirintos e autocolisão.
- Conferir todos os quizzes e autoacionamento de treinadores por visão, ganhar/perder/salvar/recarregar.
- Validar Surf da Rota 21 até Cinnabar com a Soul Badge local sem eventos externos; Seafoam/Articuno permanecem bloqueados.
- Integrar reviver fósseis no laboratório, encontros selvagens e eventos específicos quando auditados, sem itens ou histórias inventadas.
- Registrar QA real Windows/JoiPlay e só então avaliar conclusão integral da etapa.

**Progresso:** manter as duas barras independentes. A Barra de núcleos somente avança após CI nativa aprovada e a Barra de aceite somente após jogo manual real; nenhuma barra é incrementada pela simples existência deste documento.
