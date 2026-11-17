# Sinnoh — Esteira de trabalho direto no GitHub após B09

**Estado registrado em 17/11/2026.** Esta esteira orienta entregas executáveis via GitHub, sem acesso ao PC, sem material proprietário no repositório e sem afirmar que Sinnoh é jogável.

## 1. Evidência recebida: recuperação B09

Relatório privado fornecido pelo usuário: `SINNOH_B09_RECUPERACAO_20261117_170828.json`. **Não publicar o JSON completo, saves, Game.exe, assets, caminhos pessoais ou relatórios de baseline privados.**

| Campo do relatório enviado | Valor |
| --- | --- |
| `status` | `PRIVATE_NATIVE_QA_CLONE_CREATED_NOT_RUNNABLE_YET` |
| Caminho relativo do clone privado | `.blue-work/sinnoh-b09-native-qa/native-635f645f2e7aa562` |
| Arquivos reaproveitados | 25.918 |
| Arquivos novos copiados | 2.755 |
| Arquivos reparados | 1 |
| Originais listados / entradas do overlay | 28.606 / 70 |
| MapIDs no clone reportados | 702 (648 originais + 54 terrenos Sinnoh) |
| Geometrias B08 verificadas, PNGs | 54 / 14 |
| Células de terreno não vazias | 484.722 |
| Saves copiados / Game.exe executado | não / não (conforme ferramenta) |
| `safe_to_launch`, `can_install_live_game` | `false`, `false` |
| `r07_complete`, `future_reservations_verified` | `false`, `false` |
| Barra B / C / D (fases aprovadas) | **0/13** (sem novas aprovações) |

**Interpretação do total de arquivos:** 25.918 + 2.755 + 1 = 28.674 itens físicos processados no recuperador, ao passo que 28.606 + 70 = 28.676 entradas lógicas no plano. Os dois registros adicionais podem representar a substituição de `Data/MapInfos.rxdata` e `Data/Tilesets.rxdata` pelo overlay; **não declarar verificada essa hipótese sem um teste de reconciliação do plano real**. A mensagem `created` é evidência registrada pelo programa, **não uma inspeção independente** da pasta do usuário.

Não executar `Game.exe` da cópia B09 no Windows principal: B10/B11 devem isolar e auditar saves antes de qualquer execução.

## 2. Barras que não mudam automaticamente

- Desenvolvimento S01–S32 (**Barra A 32/32**) e entregas CH01–CH20 (**Barra E 20/20**) foram concluídos no escopo de **código/documentação**, conforme `data/regions/sinnoh-progress.json`.
- **Barra B 0/13** (aprovação técnica), **Barra C 0/13** (jogo executado), **Barra D 0/13** (aceite Windows/JoiPlay) continuam assim até evidências nativas verificadas.
- Subetapas R07–R09, I06–I08, testes Windows/Android e licença de cada recurso gráfico continuam pendentes.
- A conclusão do script ou do CI de uma etapa desta esteira **não equivale** à aprovação de qualquer uma dessas fases.

## 3. Esteira GitHub (G01–G12): entregas independentes do PC

Cada item deve produzir **código ou documento versionado + testes negativos + execução CI + commit/PR**, quando aplicável. Toda nova saída deve ser declarada `offline`/`planned` até prova real. Evitar reimplementar ferramentas existentes.

| ID | Prioridade | Entrega realizável só pelo GitHub | Critério de aceite e limite |
| --- | --- | --- | --- |
| **G01** | P0 | **Auditor de recibos B09**: conferir status, contagens de recuperação, 702 IDs declarados, 54/14, gates falsos e consistência de caminhos privados, usando apenas fixtures JSON sintéticas/sanitizadas | Testes para recibo falso, faltante, adulterado ou com `safe_to_launch=true`; nunca acessar o PC ou publicar arquivos originais |
| **G02** | P0 | **Progresso e integridade B09**: revisar [PR #139](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/139), validar hashes na cópia, `stderr` de progresso e abortos seguros; confrontar CI da branch com a base | CI Sinnoh S30 e CH19; não mesclar com regressão não explicada; esclarecer falhas das outras suítes |
| **G03** | P0 | **R07 — matriz de reservas futuras:** comparar manifests de Kanto/Johto/Hoenn/Unova/Sinnoh e lacunas, protegendo 442–517, 518–599 e faixas Johto existentes | Exportar diagnóstico determinístico e testes de sobreposição; **não** assinalar `r07_complete` sem aprovação física e reservas ainda não instaladas |
| **G04** | P0 | **B10 — endurecer preparação da Windows Sandbox**: revisar mapeamentos somente leitura, falta de rede/clipboard/autostart, Windows Home e falhas de instalação | Testes sintéticos de WSB inválido, caminhos inesperados e recusa de acesso a saves; não executar VM pela CI |
| **G05** | P0 | **B11 — auditor de preservação de saves**: revisar diretórios observados, manifestações de cobertura incompleta, hashes locais e mensagens de privacidade | Testes para saves criados, removidos, alterados e diretórios não monitorados; resultado nunca afirma isolamento global com poucos diretórios |
| **G06** | P1 | **QA de rendering estático**: validar dimensões e estrutura dos 14 PNGs, CRC, índices de tilesets 71/72 e riscos de tilesets de 256×50.000 / 256×70.000 | Relatório apenas de compatibilidade estrutural; renderização e memória real dependem de Game.exe |
| **G07** | P1 | **Twinleaf — mapa de vínculos físicos planejados**: checklist de 9 mapas, 16 transfers, 5 eventos, 3 Poké Bolas, spawn e recursos; resolver simbolicamente só o que já tem evidência | Sem coordenadas, IDs ou warps inventados; recusar instalação de evento sem vínculo real |
| **G08** | P1 | **Rowan, Barry e iniciais**: reforçar contratos de ordem, duplicidade, escolha e save por região; conferir 3 versões PBS e 70%/90% com fixtures | Fixtures de vitória, derrota, save/reload, eventos repetidos e modo Master; sem alegar PBS compilado no jogo |
| **G09** | P1 | **Regras regionais de progressão**: suite offline para 8 insígnias, HMs e itens-chave locais, Elite/Cynthia, Hall of Fame e desbloqueios | Testes negativos para progressão quebrada entre regiões; não alterar a main do jogo sem regressões |
| **G10** | P1 | **Portal Sinnoh**: conferir busca, filtros, áreas e links, marcando terreno de QA separadamente de conteúdo planejado | Testes impedem mostrar qualquer área como `playable` ou `installed` apenas pela B09 |
| **G11** | P1 | **Matriz CI B07→B11**: testes sintéticos integrados de SHA, overlay, colisões, rollback, permissões e marcadores falsos | Artefatos da CI só com metadados e fixtures próprias; nenhum Game.exe, save ou PNG de terceiro no GitHub |
| **G12** | P2 | **Handoff Windows/Android versionado**: checklist e BATs de pré-voo, inventário de evidências B10/B11 e dos 44 casos de teste nativo | Todo teste real permanece `pending` até recebimento de relatórios, observações de gameplay e revisão independente |

**Sequência:** `G01 → G02 → G03 → G04 → G05 → G06 → G07 → G08 → G09 → G10 → G11 → G12`. Após G03, G04–G10 podem ser desenvolvidos em paralelo por PRs pequenos. A conclusão da esteira GitHub não altera a necessidade de QA nativa.

## 4. Portões locais (não podem ser substituídos por GitHub)

| Gate | Dependência real | Condição para avançar |
| --- | --- | --- |
| **L01 / B10** | Clone físico B09 + Windows Sandbox compatível e habilitado | WSB gerado na máquina do usuário, VM isolada, clone copiado dentro do convidado, sem iniciar o jogo principal |
| **L02 / B11** | B10 real + watch de saves do host antes/depois | Relatório sanitizado `watch_unchanged` e confirmação de que cobertura do monitoramento é limitada |
| **L03 / R07–R08** | Reservas futuras reais, direitos de cada asset, mapas/eventos autorais | Aprovação documental e confronto dos IDs reais; sem instalar automaticamente |
| **L04 / R09** | Game.exe isolado + 44 casos + revisão visual de Twinleaf, colisões, transfers, batalhas, save/load | Prova Windows no clone isolado, jamais suposta pelo resultado de `pytest` |
| **L05 / Android** | Build Android/JoiPlay, instalador, saves de teste isolados | QA em dispositivo, falhas de runtime e relatórios reais |

Se Sandbox não estiver disponível, **não** sugerir Game.exe no host como fallback.

## 5. CI e integração — estado na abertura da esteira

[PR #139](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/139) introduz progresso B09 e cópia com hash em stream. Na inspeção de 17/11/2026: os workflows **Sinnoh S30** e **Sinnoh CH19** terminaram com sucesso, mas **Kanto** e **Blue Studio** falharam. O log de Kanto mostra `Boulder did not unlock Flash`; o log de Blue Studio contém `CutTree regression: previous protagonist scale fix was lost`. Essas falhas devem ser separadas entre baseline preexistente e regressão real antes da fusão do PR; não atribuí-las automaticamente à B09.

Regra para qualquer PR da esteira: executar testes específicos e negativos; comparar checks com a `main`; documentar as falhas conhecidas; preservar proteção multi-regional; solicitar merge apenas com aceitação suficiente. Não enviar dados privados aos artifacts do GitHub Actions.

## 6. Progresso da esteira

- **G01–G12:** **0/12 implementados nesta nova trilha**; ferramentas pré-existentes não contam como entregas novas.
- **Marco anterior local:** B07 e B08 reportados, **B09 recuperada e concluída apenas como clone privado não executável**.
- **B10/B11 locais:** pendentes até os relatórios do usuário.
- **Barra A:** 32/32 (100% código); **E:** 20/20 (100% CH); **B/C/D:** 0/13.

Cada alteração desta página deve atualizar somente o estado real da esteira G, **sem forçar o percentual das fases jogáveis**.
