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
