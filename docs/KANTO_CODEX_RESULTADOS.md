# Kanto — resultado da execução E2E

Revisão testada [`b35a084e`](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/commit/b35a084ef25f6b2a7dae0e898c50122838ae375e).

**Barra 2 em 1/16 (6,25%).** Nenhuma etapa recebeu aceite novo. Kanto continua `prototype`.

No Windows, a sondagem do piloto isolado falhou na inicialização do PhysFS. A sessão interativa abriu a janela do mkxp-z e exibiu `No script file has been specified`. A ferramenta de captura esgotou o tempo de espera. O menu e a casa de Pallet não foram observados. As tentativas geraram logs e registros de acessibilidade, sem screenshots ou saves novos.

Passaram 170 testes Python de Kanto, 61 testes do portal e o build do site. A auditoria confirmou 142 mapas, 45 prévias sem eventos, 144 perfis no portal, oito insígnias, 22 áreas de encontros e 153 registros de equipes comparados com a fonte FRLG. Os seis hashes conferidos na instalação pessoal coincidiram antes e depois.

A [CI nativa original](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43336795536) recusou o arquivo FRLG porque o SHA-256 divergiu do manifesto. O [PR #25](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/25) usa o preparador compartilhado com verificação do mesmo SHA-256. A [regressão do PR](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43339783002) passou e a [CI nativa do PR](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43339783021) reproduziu a divergência no runner. A cópia local passou na conferência do SHA-256 e na extração.

| Etapa | Caso | Estado | Observação |
| --- | --- | --- | --- |
| 01 | Auditoria estrutural | `PASS_STRUCTURAL_ONLY` | 142 mapas, 45 prévias sem eventos, 51 conexões e 13 pares de interiores auditados. Aceite histórico preservado. |
| 02 | Movimento de Pallet a Cerulean | `BLOCKED_ENV` | A janela do mkxp-z exibiu um diálogo de script ausente. A sondagem com diretório correto falhou no PhysFS. A captura expirou antes do menu. |
| 03 | Pallet a Pewter, eventos e Brock | `NOT_RUN` | Oak, iniciais, rival, pacote, cura, treinadores e Brock aguardam gameplay. |
| 04 | Seleção da região inicial | `NOT_RUN` | Menu Kanto/Decades, autosave e save legado aguardam teste na cópia integrada. |
| 05 | Viagem Decades e Kanto | `NOT_RUN` | NPC, bloqueio pré-Liga, ida e volta e persistência no mesmo save aguardam gameplay. |
| 06 | Balanceamento, HMs e especiais | `NOT_RUN` | Normal e Master, insígnias locais, PC cheio e regras regionais aguardam gameplay. |
| 07 | Cerulean, captura e Misty | `NOT_RUN` | Mt. Moon, captura, interiores, Misty, derrota e save aguardam gameplay. |
| 08 | Vermilion, S.S. Anne e Lt. Surge | `NOT_RUN` | Ticket, capitão, puzzle, combate e insígnia aguardam gameplay. |
| 09 | Celadon e Erika | `BLOCKED_IMPLEMENTATION` | Loja em prévia e Rocket/Game Corner pendente. Erika não foi enfrentada. |
| 10 | Fuchsia, Koga e Safari | `BLOCKED_IMPLEMENTATION` | Mapas de captura Safari em prévia. Ingresso, Safari Balls, passos, Gold Teeth e Warden pendentes. Koga não foi enfrentado. |
| 11 | Saffron, Sabrina e Silph | `NOT_RUN` | Dojo, teleportes, andares, chave, rival e Giovanni aguardam gameplay. |
| 12 | Cinnabar e Blaine | `BLOCKED_IMPLEMENTATION` | Rota marítima exigida e Seafoam em prévia. Mansion, quizzes e Blaine não exercitados. |
| 13 | Viridian e Giovanni | `NOT_RUN` | Portão, sete insígnias locais, Silph e oito treinadores aguardam gameplay. |
| 14 | Victory Road e Liga | `BLOCKED_IMPLEMENTATION` | O plano exige Strength físico. A revisão tem um mecanismo experimental. Guardas, Liga, variantes do Blue e Hall não foram jogados. |
| 15 | Fidelidade FireRed e LeafGreen | `PASS_STRUCTURAL_ONLY` | 22 áreas, 52 espécies e 153 equipes verificadas contra Essentials FRLG 1.1. Route 23 segue em revisão. Faltam exclusividades oficiais, itens e diálogos. |
| 16 | Integração, publicação e Android | `BLOCKED_ENV` | Gate estrutural executado. Jogo principal integrado e persistência aguardam teste gráfico. Nenhum dispositivo ou emulador JoiPlay acessível foi encontrado. |

**Total:** 0 `PASS_E2E`, 0 `FAIL` em cenários de gameplay, 2 `PASS_STRUCTURAL_ONLY`, 2 `BLOCKED_ENV`, 4 `BLOCKED_IMPLEMENTATION` e 8 `NOT_RUN`.

Evidências locais em `.blue-work/kanto-codex-e2e/20261112-b35a084e/`: `resultado.md`, `resultado.json`, `t2-probe.json`, `t3-windows-ui.json`, `interactive-stderr.log`, `verify_pilot.json`, `audit_canonical.json` e `release_gate.json`.

Retomar pelo boot na etapa 02. Após observar o menu, iniciar um novo save isolado, provar movimento/colisão/escada e percorrer Pallet–Cerulean com as teclas reais. Os casos de Android/JoiPlay permanecem bloqueados até haver dispositivo ou emulador acessível.

## Continuação na revisão 083b98a

O piloto em uma pasta curta compilou e abriu a tela de título. Um Enter físico abriu o menu, confirmado por um quadro capturado do próprio Game.exe. Enter e seta para baixo enviados pelo controle automatizado deixaram New Game selecionado. As capturas de antes e depois e o registro de teclas estão no relatório local. Movimento em Pallet, batalhas, viagens e save/reload continuam sem execução gráfica. A Barra 2 permanece em 1/16.

A Rota 23 voltou a ter encontros no PBS e no portal no [PR #26](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/26). O método LandDay aparecia duas vezes com conteúdo idêntico. A importação mantém uma cópia com os pesos relativos originais. A auditoria comparou 23 áreas, 69 métodos, 53 espécies e 153 registros de equipes com a fonte verificada. Passaram 171 testes de Kanto, 61 testes do portal e o build. Falta exercitar os encontros da Rota 23 pela interface.

O [PR #25](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/25) voltou a passar na regressão geral. A [CI nativa](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43343135584) recebeu uma página HTML de 2.040 bytes, compatível com a cota de download do Google Drive observada localmente. A solicitação local com URL nova baixou o RAR com o SHA-256 correto. O runner recusou o arquivo inválido e interrompeu a compilação.

Evidências locais em `.blue-work/kanto-codex-e2e/20261112-b35a084e/`: `resultado-seguimento.md`, `resultado-seguimento.json`, `followup-title.png`, `kanto02-009-menu-after.png`, capturas de `kanto02-010-new-game` e `kanto02-011-menu-down`, `followup-actions.jsonl` e `followup-canonical.json`.
