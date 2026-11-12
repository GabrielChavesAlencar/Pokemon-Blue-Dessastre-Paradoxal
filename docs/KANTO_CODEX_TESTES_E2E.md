# Kanto — plano de execução do Codex para testar e elevar a Barra 2

**Projeto:** `GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal`  
**Objetivo:** fazer o **Codex executar os testes**, localizar e corrigir os defeitos, gerar evidências verificáveis e só então propor aceite integral de cada uma das 16 etapas. O usuário **não precisa jogar** para realizar a bateria automatizável.  
**Estado inicial:** Barra 1 = **16/16 núcleos técnicos**; Barra 2 = **1/16 etapas integralmente aceitas**; Kanto = `prototype`. **Não redefina esses números no início da execução.**

> **Contrato essencial:** os testes nativos existentes usam simulação de resultados de batalha e verificações de eventos/mapas. Não constituem um playthrough de verdade. Para aprovar uma etapa da Barra 2, execute seus cenários reais pela interface do jogo (GUI/teclado ou controle automatizado), com evidências de entrada, ação, resultado e persistência. Se o ambiente não suportar GUI Windows ou JoiPlay, registre **BLOCKED_ENV**, não **PASS**. A primeira barra já está 100%; a segunda só sobe com evidências reais.

## 0. Como iniciar o Codex

1. Abra o repositório no **Codex com acesso de escrita e execução de comandos**, idealmente no computador **Windows com sessão gráfica ativa e desbloqueada**. Abra um ambiente com ferramentas para capturar a janela e enviar teclas ao `Game.exe`. A execução em Linux/headless fica limitada a testes estáticos, Playwright do site e CI.
2. Peça ao Codex para ler este arquivo e `AGENTS.md` da raiz, além de `docs/KANTO_ETAPAS.md`, `docs/KANTO_FASE_02_MOVIMENTO.md`, `docs/KANTO_FASE_14.md`, `docs/KANTO_FASE_15.md`, `docs/KANTO_FASE_16.md` e `docs/PLANO_REGIOES_DESSASTRE_V2.md`.
3. Use o [prompt de execução pronto](KANTO_CODEX_PROMPT.md). Não delegue um comando vago como "faça todos os testes": o Codex deve seguir **todas** as fases e entregar uma matriz de evidências.
4. O Codex pode implementar os scripts auxiliares que estiverem faltando, repetir os testes, corrigir defeitos e criar PRs. **Não** executar testes apenas por inspeção de código e chamá-los de gameplay.

## 1. Segurança obrigatória, antes de qualquer execução

- `game/`, executáveis, fontes FRLG, ROMs, `Data/*.rxdata`, saves, backups e `.blue-work/` são **locais e ignorados pelo Git**. Não commitá-los, não removê-los, não enviar anexos de saves a PRs ou logs públicos.
- Criar branch de trabalho a partir da `main` mais recente, sem `force push`. Antes de qualquer script com `--apply`, conferir se age numa cópia descartável e não no jogo pessoal.
- Não reinstalar nem sobrescrever os saves do usuário. O piloto é uma cópia sob `.blue-work/kanto-pilot`; o modo de teste integrado que injeta `Main` em `game/` está restrito a runners descartáveis com `GITHUB_ACTIONS=true`. **Nunca contornar essa restrição.**
- Registrar commit, plataforma, versão de Python/Node, localização da instalação piloto e hashes de `game/Data/MapInfos.rxdata`, `game/Data/Tilesets.rxdata` e demais arquivos originais relevantes **antes e depois**. Diferença inesperada = **FAIL_SAFETY** e interromper.
- A fonte `Essentials FRLG 1.1` deve ser preparada por `scripts/regions/ensure_source.py`, que verifica SHA-256. Não usar fontes de mapas de terceiros de checksum desconhecido.
- Não conceder badges por console, não alterar flags do jogo, não injetar vitórias, não usar o menu de teleporte experimental para **comprovar** um caminho que deveria ser percorrido a pé. Atalhos podem ser usados apenas para **posicionar um teste isolado**, e o relatório deve explicitar isso.
- Não declarar `playable` e não alterar `accepted_integrally` em lote. Um relato automático de estrutura ou um formulário preenchido pelo próprio teste não equivale à evidência visual do evento.
- Se a instalação local de `game/` não estiver disponível, usar uma cópia efêmera em CI mediante o instalador documentado; registrar o bloqueio dos testes gráficos, sem presumir que o Codex enxergou uma janela real.

### Comandos de inspeção (PowerShell na raiz)

```powershell
git status --short
git rev-parse HEAD
git branch --show-current
py -3 --version
node --version
Test-Path .\game\Game.exe
Test-Path .\game\Data\MapInfos.rxdata
Test-Path ".\game\Plugins\ZZZZ Blue Story and Presentation\Regions.rb"
```

**Se houver modificações locais não relacionadas, preservar e isolar**; não executar reset/clean destrutivo. Criar uma pasta de evidências com identificador único dentro de `.blue-work/kanto-codex-e2e/`, fora do controle de versão.

## 2. Camadas de testes (não confundir resultados)

| Camada | Quem/onde executa | O que pode comprovar | O que NÃO comprova |
|---|---|---|---|
| T0 — Estático/Unitário | Python e Node em qualquer SO | Manifesto, PBS, regras, cálculos, estrutura do site | Movimento, menus, batalhas reais |
| T1 — Engine nativa | `Game.exe` no runner Windows da CI | Compilação, eventos, badges, save/reload simulados, passos `Game_Player` | Jogabilidade pela GUI; os combates são simulados |
| T2 — Janela/boot | `gui_diagnostics.py` no Windows | Processo inicia e janela é detectada | Que o jogador se moveu ou venceu uma luta |
| T3 — E2E visual automatizado | Codex num desktop Windows desbloqueado | Teclas reais, telas, menus, mapa, batalhas, curas, captura, retorno e save/reload | JoiPlay físico sem aparelho/sessão Android |
| T4 — Android/JoiPlay | Codex com acesso a dispositivo/emulador adequado | Input, mapas, batalha, save e renderização Android | Certificação em aparelho real se só usou emulador |

**A Barra 2 depende sobretudo de T3 e, para a etapa 16/Android, de T4.** T0–T2 são pré-requisitos, não provas substitutas. Codex não deve marcar como PASS uma condição que somente verificou via simulação nativa.

## 3. Preparar e executar a base automatizada (T0/T1/T2)

**Rodar nesta ordem; salvar saída e status de cada comando**. Se um falhar, parar, identificar causa e corrigir antes de continuar.

### 3.1. Testes de código e portal

```powershell
py -3 -m unittest discover -s tests -p "test_kanto_*.py"
Push-Location site
npm test
npm run build
Pop-Location
```

O diretório `site` oferece os scripts `test` (`node --test tests/*.test.mjs`) e `build`. Se os pacotes não estiverem preparados, seguir o `site/README.md` e instalar dependências **no ambiente local**, registrando a mudança; não gerar alterações em `package-lock.json` por acidente.

### 3.2. Preparar o piloto *isolado*

**Antes:** confirmar `game/Game.exe` e o runtime Blue preparado. Se ausentes, seguir `docs/INSTALACAO.md` num ambiente descartável. Não usar `install_kanto.py --apply` no jogo pessoal para testar.

```powershell
py -3 scripts/regions/ensure_source.py
py -3 scripts/regions/gui_diagnostics.py --output .blue-work/kanto-pilot --probe --seconds 25
py -3 scripts/regions/verify_pilot.py .blue-work/kanto-pilot
py -3 scripts/regions/audit_canonical.py --pilot .blue-work/kanto-pilot
py -3 scripts/regions/release_gate.py --pilot .blue-work/kanto-pilot
```

`gui_diagnostics.py` cria a cópia do piloto quando necessário e verifica só o arranque. Se a cópia existente estiver desatualizada, ele cria nova pasta e conserva a antiga; **capturar o caminho efetivo** impresso no log, não assumir que a pasta padrão foi reutilizada.

`release_gate.py` conserva `declared_playable=false` e `accepted_integrally=false` por definição. Isso é correto enquanto faltar aceite real. Executar ainda as pipelines reais em `.github/workflows/kanto-pilot-check.yml` e `.github/workflows/regression.yml` no GitHub Actions, aguardando cada job encerrar com **success**.

**Não executar `scripts/regions/native_check.py --integrated` na instalação pessoal.** Essa rotina injeta uma prova temporária no `Main` do jogo em CI e é explicitamente restrita a ambiente efêmero.

### 3.3. Evidência mínima T0/T1/T2

Salvar: hashes antes/depois, relatório de 142 mapas/45 previews, 144 perfis, 8 badges, 22 localidades de encontros, rota 23 em revisão, ações CI e errolog. O número da barra continua **1/16** até passar T3/T4.

## 4. Construir a automação visual do Codex (T3)

O repositório **ainda não contém um robô que termine o jogo pela interface**. O Codex deve criá-lo, testá-lo e documentá-lo. Sugestão de estrutura (criar somente se necessário):

```text
scripts/regions/e2e/
  README.md
  driver_windows.py            # abrir/focar Game.exe e SendInput real
  capture.py                   # screenshot e vídeo com timestamps
  detect_state.py              # detectar menu/mapa/diálogo/batalha
  scenarios/
    02_walk.json
    03_pallet_pewter.json
    ...
    16_integrated.json
  run_suite.py
tests/test_kanto_e2e_driver.py
```

**Regras do driver:**

1. Rodar numa sessão Windows **interativa, desbloqueada**, com resolução/DPI anotados. Um GitHub runner headless não é substituto. Se não houver desktop gráfico, registrar `BLOCKED_ENV`.
2. Lançar `Game.exe` original da **cópia isolada** (`.blue-work/...`) com `cwd` correto. Não usar o `KantoNativeCheck.rb` como script de gameplay e não executar a prova de batalha simulada como se fosse jogada.
3. Obter HWND/PID da janela, conferir título e que o foco está no jogo. Para teclas reais, usar uma implementação de `SendInput`/Win32, ou biblioteca equivalente (`pydirectinput`/`pyautogui`) **somente se o motor responder**. Calibrar Enter/Escape/setas e teclas de ação. Playwright é para o portal, **não controla automaticamente a janela do `Game.exe`**.
4. Capturar tela **antes e depois de cada ação**, com timestamp, PID, posição observável, jogo/estado, tecla enviada e resposta. Usar detecção visual verificável (sprites, HUD, textos, transições); um mero `sleep` não confirma que a ação ocorreu.
5. Criar uma API de espera por condição: `wait_for_menu`, `wait_for_dialogue`, `wait_for_battle`, `wait_for_map_change`, `wait_for_badge`, `wait_for_save_load`. Configurar timeout, screenshots de falha e saída. Evitar laços infinitos ou spam de teclas.
6. Quando permitido, cruzar o resultado visível com **estado de teste somente leitura** (ID de mapa, equipe, badges, itens, save). A leitura auxilia a prova; **não gravar flags para fabricar a condição**.
7. Cada cenário deve iniciar de **checkpoint de teste legítimo**, criado por progresso jogado ou fixture isolada claramente rotulada. **Fixtures ou teleporte experimental não provam desbloqueio por gameplay.** Para teste de portões, chegar a eles pelo caminho legal e testar tanto bloqueio quanto liberação.
8. Ao salvar, fechar o processo, abri-lo de novo e verificar visualmente posição, badges, equipe, PC, itens e ausência de softlock. Não usar o próprio save do usuário para testes destrutivos.
9. Se uma funcionalidade estiver ausente (Safari completo, Strength físico, Johto não instalada), retornar `BLOCKED_IMPLEMENTATION`, não inventar um resultado. Em caso de crash ou comportamento incorreto com evidência, `FAIL`.
10. Salvar capturas/filmagens **somente em `.blue-work/kanto-codex-e2e/<execucao>/`**; registrar caminhos relativos na versão pública do relatório, sem publicar dados pessoais, saves, assets de terceiros ou ROMs.

**Dependências externas opcionais:** avaliar `pywinauto`, `pydirectinput`, `mss` e `opencv-python` dentro de venv local isolado. Não assumir que já estão instaladas; verificar licenças/versões, não incluir pacotes grandes ou binários no Git. Se os menus não responderem ao driver, capturar evidência e reportar `BLOCKED_ENV`, nunca usar injeção de vitória no lugar do teste gráfico.

## 5. Matriz obrigatória das 16 etapas — seguir esta ordem

Para **cada uma**: testar caminho feliz, bloqueio/condição negativa, derrota/repetição quando houver, persistência após save/reload e regressão do caminho anterior. O Codex deve criar casos rastreáveis `KANTO-01` a `KANTO-16`, com subcasos e evidências.

| Etapa | Testes E2E e condições de aceite |
|---|---|
| **01 — Auditoria estrutural** | `audit.py`, `verify_pilot.py`, `release_gate.py`; mapeamento sem colisão de IDs, 142 mapas, 45 prévias sem eventos, conexões consistentes; manter etapa 01 previamente aceita, revalidando regressão. |
| **02 — Movimento real** | Iniciar **dentro da casa do jogador em Pallet**. Caminhar 4 direções, testar colisão contra árvores/paredes, subir/descer escada, sair/entrar em casa/rival/laboratório; movimento sem teleporte para Route 1 → Viridian → Route 2 → Forest → Pewter → Route 3 → Mt. Moon → Route 4 → Cerulean; retornar, salvar e carregar. |
| **03 — Pallet/Pewter e eventos** | Oak, escolha do inicial, rival, pacote Poké Mart Viridian → Oak, cura, museu, casas, Brock. Os treinadores por visão iniciam batalha sem atravessar obstáculos; derrota deixa o jogo recuperável; não conceder Boulder em derrota nem duplicar vitória. |
| **04 — Região inicial** | Menu de nova partida permite começar em Kanto quando instalada, preserva a opção original Decades, não troca Kanto para fora de casa, escolhas e autosave não afetam saves legados. Testar ao menos uma vez cada inicial e regressão de novo jogo Decades. |
| **05 — Viagem Decades ⇄ Kanto** | NPC da cidade inicial e condições pós-Liga; ida e volta mantendo **o mesmo save**; retornar à posição anterior, equipe/PC/itens consistentes. Testar bloqueio de viagem antes dos requisitos e pós-jogo válido; não criar Johto artificialmente. |
| **06 — Balanceamento regional / HMs / especiais** | Esmeraldas/badges globais influenciam nível conforme regras de Decades, **badges locais** controlam HMs e história. Lendários/míticos/UB/paradoxos restringidos até 8 insígnias daquela região; troca deposita na box; impedir reintrodução prematura, preservar PC cheio e save. Modo Master: times/níveis conforme a regra existente, sem hardcode adicional. |
| **07 — Cerulean/Misty** | Route 3/4, Mt. Moon com escadas sem softlock, encontro e captura reais, Cerulean, ginásio Misty, Cascade Badge única; derrotas e saves; entrar/sair de todos os interiores ativos. |
| **08 — Vermilion/Lt. Surge** | Rotas 5/6, passagem subterrânea, porto, S.S. Anne, Ticket e capitão, puzzle dos interruptores do ginásio, batalha com Lt. Surge, Thunder Badge apenas uma vez; HM correspondente e retorno. |
| **09 — Celadon/Erika** | Entrar/sair de cidade, Center e ginásio, sete treinadores e Erika, Rainbow Badge; verificar árvores Cut, Rocket/Game Corner e loja. **Se são só prévia, deixar bloqueado e não aceitar a etapa completa.** |
| **10 — Fuchsia/Koga/Safari** | Center/Mart, seis treinadores e Koga, Soul Badge única; **Safari real** requer ingresso, Safari Balls, encontros, contagem de passos, Gold Teeth, Warden/Surf/Strength, retorno e save. A versão informativa do portão Safari **não aprova** este item. |
| **11 — Saffron/Sabrina/Silph** | Dojo, teleportes do ginásio, ordenação dos 11 andares Silph Co., Card Key, rival, Giovanni separado da versão do ginásio, resgate e Marsh Badge só após vitória; todas as portas/andares com volta. |
| **12 — Cinnabar/Blaine** | Surf real até ilha (sem teleporte de aceitação), Mansion 1F–B1F, estátuas, Secret Key, ginásio fechado sem chave, 6 quizzes, Blaine, Volcano única; fósseis/laboratório e Seafoam/Articuno quando aplicáveis. **Se apenas mapa/preview, registrar bloqueio.** |
| **13 — Viridian/Giovanni** | Ginásio fechado sem **7 insígnias locais + Silph libertada**; não usar total global para contornar. Oito treinadores, batalha Giovanni com equipe própria, Earth única, retorno à cidade e save; testar bloqueio antes e liberação depois. |
| **14 — Victory Road/Liga** | Route 22/23 com **8 guardas locais**, passagem real por Victory Road 1F–3F e mecanismos **Strength físicos**, não só abertura experimental. Lorelei→Bruno→Agatha→Lance→Blue; três variantes de Blue conforme inicial; derrota reseta tentativa, sem completar Hall. Hall of Fame só após cinco vitórias, uma vez, libera **elegibilidade** a Decades/Johto, não Johto instalada. |
| **15 — Fidelidade FRLG** | 22 áreas selvagens/52 espécies e níveis/probabilidades preservados no PBS, 153 registros de equipes, itens e diálogos das áreas ativas; cruzar com fontes oficiais separadas para diferenças FireRed x LeafGreen. **Route 23/Map209 tem LandDay duplicado e está sob revisão**, não aceitar como equivalente oficial sem resolução verificável. |
| **16 — Integração/publicação** | Menu no `Game.exe` principal, save Decades íntegro, NPC de viagem na cidade inicial, mesmo save/PC/box/money/bag/Pokédex, volta após Hall e save/reload. Portal com 8 badges e status das 45 prévias. Teste Android/JoiPlay real ou ambiente equivalente explicitamente identificado. O gate fica `prototype` até conclusão de TODOS os bloqueadores. |

**Obrigatórios transversalmente:** modo normal + Master; tipo/nível/party corretos; time diferente conforme inicial; treinador não repete recompensa; controle de HMs por região; caminhos ida/volta; nenhum evento de história é liberado por insígnias de região errada.

### Ordem de execução eficiente

- **Lote A:** etapas 01–04, começando pela etapa **02**, com múltiplos saves de teste (três iniciais).
- **Lote B:** etapas 05–08; concluir primeiro a jornada sem atalhos, depois testar viagem.
- **Lote C:** etapas 09–13; abrir bugs para Rocket, Safari e demais previews sem declarar sucesso.
- **Lote D:** etapas 14–16; Liga, fidelidade de dados, site, integração e Android.

Não há obrigação de concluir os quatro lotes num único processo. Após cada correção, rodar **a suíte da etapa afetada, a anterior, a próxima e toda a CI**, com screenshot/log antes/depois. Não deixar um item falho "para depois" e contabilizá-lo.

## 6. Controle de progresso e evidências — padrão obrigatório

Criar relatório **local** `.blue-work/kanto-codex-e2e/<execucao>/resultado.json` e `resultado.md`, com este formato (exemplo de estrutura; valores de resultado sempre precisam vir de testes de fato executados):

```json
{
  "schema": 1,
  "source_commit": "SHA_REAL_DA_EXECUCAO",
  "environment": {
    "os": "WINDOWS_OU_OUTRO",
    "mode": "native_headless|real_gui|android_device|browser_only",
    "game_exe": "caminho_local_da_copia_isolada",
    "graphics_session": false
  },
  "stage": "02",
  "scenario_id": "KANTO-02-PALLET-ESCADA",
  "status": "NOT_RUN",
  "steps": [],
  "expected": "Descer e subir a escada sem softlock",
  "observed": "Sem execução",
  "evidence": [],
  "logs": [],
  "save_reload_verified": false,
  "used_test_shortcut": false,
  "gameplay_e2e_verified": false,
  "limitations": ["Aguardando sessão gráfica"]
}
```

Estados permitidos: `PASS_E2E`, `PASS_STRUCTURAL_ONLY`, `FAIL`, `BLOCKED_ENV`, `BLOCKED_IMPLEMENTATION`, `NOT_RUN`. **Não** converter `PASS_STRUCTURAL_ONLY` em `PASS_E2E` sem execução real de menus/ações. Não preencher automaticamente o `kanto_feedback.py` como se ele fosse um usuário; ele é um **formulário local de observação**, com `accepted_integrally=false`.

Cada cenário deve ter: passos exatos, pré-requisitos, input enviado, resultado observado, screenshot/vídeo/log, commit, tempo, estado de save. Se faltar evidência crítica, o estado não pode ser `PASS_E2E`.

### Defeitos encontrados: fluxo de correção pelo Codex

1. Criar `BUG-KANTO-<etapa>-<numero>` com **passo mínimo de reprodução**, mapa/evento, estado de save, screenshots e logs.
2. Classificar `BUG_GAMEPLAY` (motor/cena/interação), `BUG_DATA` (PBS/equipe/encounters), `BUG_UI`, `BUG_SAVE`, `MISSING_FEATURE`, `BLOCKED_ENV` ou `INCONSISTENT_SOURCE`.
3. Corrigir na fonte/scripts próprios do repositório, **nunca diretamente apenas na instalação local**. Não copiar o projeto FRLG inteiro nem importar scripts não auditados.
4. Criar teste automatizado de regressão reproduzível, recompilar piloto em cópia nova, repetir cenário visual, executar T0/T1 e conferir integridade da base Decades.
5. Publicar commits via PR, sem `force push`, e sincronizar com `main`. Não fechar bug só porque o código compilou — exigir o resultado visual ou declarar que ficou bloqueado.

## 7. Quando atualizar a Barra 2

Uma etapa só pode virar `[x]` em `docs/KANTO_ETAPAS.md` quando:

- Todas as **condições obrigatórias** dessa etapa tiverem `PASS_E2E` com evidência verificável, **incluindo casos negativos, save/reload e execução sem atalhos quando aplicável**.
- As regressões T0/T1/portal estiverem verdes na **mesma revisão** de código da prova E2E.
- Nenhum `FAIL`, `BLOCKED_ENV`, `BLOCKED_IMPLEMENTATION` ou `NOT_RUN` obrigatório estiver pendente.
- A prova puder ser **repetida do zero**, em novo save isolado, por uma segunda execução independente do cenário.
- O Codex produzir um resumo de evidências para revisão, sem fingir aprovação humana. A aceitação por automação visual pode substituir a necessidade de o usuário jogar, **mas somente com observação real de interface**, testes reproduzíveis e revisão da evidência; quando a política de aceite atual exigir revisão humana explícita, registrar essa pendência em vez de burlá-la.

**Atualização permitida após aceite comprovado:** incrementar só os itens aprovados, recalcular `N/16` e `100*N/16%`, registrar links de CI, evidências da GUI e PR. **Não alterar a Barra 1** (já 16/16). Se nenhuma etapa passar integralmente, **manter Barra 2 em 1/16** mesmo que centenas de testes estruturais passem.

Nunca usar estes atalhos para justificar aprovação: `KantoNativeCheck.rb` (combates simulados), `KantoWalkCheck.rb` (passos headless), `gui_diagnostics.py --probe` (apenas janela) e `release_gate.py` (`accepted_integrally=false` por design).

## 8. Entregáveis que o Codex deve produzir

- Harness de GUI automatizado quando o ambiente suportar, **com testes reproduzíveis** por mapa/evento/treinador.
- `resultado.md` e `resultado.json` locais contendo os 16 blocos com PASS/FAIL/BLOCKED/NOT_RUN, caminhos de screenshots, logs, timestamps e SHA.
- Bugs encontrados e correções em PRs pequenos, testes de regressão e notas sobre impacto no save.
- `docs/KANTO_CODEX_RESULTADOS.md` com **resumo sanitizado**: SHA, CI, contagem por etapa, pendências e links de PR; sem saves, mídia do jogo ou dados pessoais.
- Atualização **somente quando justificada** de `docs/KANTO_ETAPAS.md` e da Barra 2. Informar explicitamente quais etapas **não** foram aceitas e por quê.
- Relatório específico dos cenários Android/JoiPlay que foram feitos ou ficaram bloqueados pela falta de dispositivo.

## 9. Critério de parada e comunicação

Ao fim de cada lote, o Codex deve responder de maneira objetiva:

1. O que rodou **de verdade** (Windows GUI, engine headless, site, Android) e em quais commits.
2. Número de PASS_E2E, FAIL, BLOCKED e NOT_RUN.
3. Quais bugs corrigiu, quais PRs/commits publicou e quais cenários repetiu.
4. A nova Barra 2 **somente se houver aceite integral comprovado**; caso contrário explicar o bloqueio.
5. A próxima sequência precisa de testes/correções, sem solicitar que o usuário jogue se o Codex dispõe de ambiente de automação adequado.

**Prioridade imediata:** etapa 02/16 e o caminho **Pallet → Cerulean**, porque as verificações do motor já existem mas faltam os testes reais da interface e das portas. Depois avançar nas 15 etapas em aberto, corrigindo funcionalidades que estão explicitamente incompletas antes de exigir aceite.
