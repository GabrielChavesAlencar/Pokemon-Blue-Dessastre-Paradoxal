# Sinnoh L05 — Matriz documental: 44 casos CH20/G12 × 20 critérios humanos L04

**17–18/11/2026 — issue #179.** Esta L05 é uma **fase de documentação e auditoria somente no GitHub**. Não deve ser confundida com o *gate local L05* de QA real Android/JoiPlay definido em G12, que continua pendente. Não acessa PC, Game.exe, Windows Sandbox, JoiPlay, saves, PNGs do doador, snapshots privados ou arquivos do jogo.

## Entregas versionadas

- [Matriz L05](../data/regions/sinnoh-l05-native-case-dependencies.json): 44 linhas em correspondência 1:1 com os **IDs verdadeiros do handoff G12**, plataforma, tipo, lista exata de critérios L04, bloqueios e nenhum resultado nativo.
- [Auditor L05](../scripts/regions/audit_sinnoh_l05_native_dependencies.py): valida a matriz **contra L04 e G12/CH20 em tempo de execução**, com política de dependências fixada no código e rejeição de qualquer status não pendente, critério removido, ordem adulterada, aprovação física inventada ou mudança de plataforma.
- [40 testes sintéticos e negativos](../tests/test_sinnoh_l05_native_dependencies.py) de cobertura, direitos, segurança, identidade, privacidade, hashes/recibos, regressões regionais e fraude de aprovação.
- [Workflow CI](../.github/workflows/sinnoh-l05-native-documentary.yml): dois jobs, 40 testes L05 e **189 testes de regressão** L04 (35), L03 (40), L02 (40), L01 (30), L00 (24), G12 (20). Não publica relatórios privados nem executa nativo.

## Como os 44 casos se relacionam com os 20 critérios

| Grupo G12 | Casos | Critérios humanos associados | Estado |
| --- | ---: | --- | --- |
| Escolha do inicial | 3 | Origem B09, isolamento B10, cobertura B11, MapIDs R07, licenças/eventos/PBS R08 | Pendentes |
| Barry (Normal/Master, vitória/derrota) | 12 | B09/B10/B11, R07, R08 (incluindo PBS) | Pendentes |
| Save/reload | 3 | B09/B10/B11, R07, R08 (eventos); **não equivale a isolamento global** | Pendentes |
| Portais | 16 | B09/B10/B11, R07 (topologia), R08 (direitos e eventos) | Pendentes |
| Eventos NPC | 5 | B09/B10/B11, R07 (topologia), R08 (eventos e PBS) | Pendentes |
| Regressões Decades/Kanto/Johto/Hoenn | 4 | B09/B10/B11, R07 (reservas regionais), R08 | Pendentes |
| Android/JoiPlay | 1 | **B09/R07/R08** mais futuro perfil e QA Android independentes; não herda prova de Windows Sandbox B10/B11 | Pendente |
| **Total** | **44 (43 Windows + 1 Android)** | **20 critérios L04 versionados, sem nenhum aceito** | **0/44** |

Todos os casos Windows exigem revisão de origem B09, configuração B10, abrangência B11, inventário/reservas R07 e direitos R08. O caso Android continua separado: não é permitido inferir QA Android por uma eventual prova da VM Windows.

O vínculo de cada caso aos critérios específicos está registrado no JSON, não apenas nesta tabela. Os critérios **não são certificações**: possuem `review_state=NOT_REVIEWED`, `independent_evidence_present=false` e `local_human_signoff=false` na L04.

## Comportamento fail-closed

O auditor:

1. Compara os **44 IDs reais** e seus tipos/plataformas com G12 e com a fonte de CH20 que o próprio auditor G12 valida, recusando ID inventado, duplicado, ausente ou reordenado.
2. Carrega os **20 IDs reais L04**, exige cobertura total, ordem e dependências previstas e recusa alteração de lista de critérios e permissões.
3. Usa os relatórios **L04 → L03 → L02 → L00** para preservar ausência/pendência, integridade documental e ausência de aprovação nativa; qualquer `approved`, `passed`, `evidence` real inserido artificialmente causa bloqueio.
4. Mantém o cuidado com **B09→B10** (SHA autodeclarado não prova origem), **B11** (pasta observada sem alterações não prova isolamento global nem vínculo da sessão), **R07** (MapID candidato não está reservado) e **R08** (contagem de análises não comprova direitos).
5. Emite somente IDs e critérios públicos, códigos fixos de bloqueio e contagens. Não reproduz hashes de recibo, caminhos, identificadores de save, logs HMAC, capturas, PNGs ou dados privados, nem gera tokens/autorizações.
6. Mantém `may_run_game_exe=false`, `may_run_joiplay=false`, `may_start_windows_sandbox=false`, `may_install_live_game=false` e `native_cases_approved=0` **independentemente de um JSON ter formato válido**.

## Execução exclusivamente documental (opcional)

O modo normal lê **somente contratos públicos** e gera JSON no terminal:

```sh
python scripts/regions/audit_sinnoh_l05_native_dependencies.py
```

Opcionalmente, alguém que já tenha produzido **voluntariamente** um relatório sanitizado pela L01 pode usar:

```sh
python scripts/regions/audit_sinnoh_l05_native_dependencies.py --workspace-reports
```

Esse parâmetro lê **somente** o arquivo fixo `.blue-work/sinnoh-l00-input/public-reports.json`, por meio dos validadores L04/L03/L02/L00. Não é um caminho arbitrário, não executa o jogo, não varre a máquina e não faz upload. **Estes comandos não foram executados no computador do usuário.**

## Protocolo de revisão humana antes de qualquer QA futura

Uma pessoa autorizada deverá, fora do GitHub e em ambiente adequado, revisar fonte/direitos do clone B09, vínculo B09/B10 e configuração segura WSB, relação privada da sessão B11 e cobertura real de diretórios de save, reservas regionais R07 e licenças R08. Depois, ainda será necessária **uma autorização separada para qualquer QA física**, um pacote de teste aprovado e a execução humana dos 43 casos Windows e 1 Android/JoiPlay. A L05 não emite essa autorização e não resolve os impedimentos de evento/PBS/mapas do jogo.

## Estado preservado

**Sinnoh planned e não jogável, R07/R08/R09 pendentes, B/C/D 0/13, 0/44 casos executados, 0/20 critérios aceitos, 0/5 relatórios locais recebidos.** A conclusão de L05 apenas significa que a **matriz de dependências está completa como código**, não que os testes estão aprovados.

**Próxima etapa segura sugerida — L06:** revisão estática da cobertura dos bloqueios e do handoff entre Windows/Android, rastreando as pendências com evidência documental (sem executar runtime, conferir arquivos privados ou liberar QA).
