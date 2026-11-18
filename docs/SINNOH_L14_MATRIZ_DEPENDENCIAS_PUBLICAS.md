# Sinnoh L14 — Matriz pública de dependências e prontidão, toda bloqueada

**Issue #203 · modo somente documental GitHub-only.** Esta fase transforma os pedidos L13 em uma matriz de **88 linhas**, preservando os vínculos de metadados sem inferir evidência física, execução autorizada ou prontidão regional.

## Estado congelado

| Indicador | Resultado |
| --- | --- |
| Pedidos L13 classificados | **88/88** |
| Prontos para execução | **0/88** |
| Estado de todos os pedidos | **PENDING / BLOCKED** |
| Vínculos documentais | **1.084 = 846 caso→critério + 218 caso→bloqueio + 20 critério→bloqueio** |
| Relatórios locais | **0/5** |
| Revisões humanas aprovadas | **0/20** |
| Testes nativos | **0/44**, sendo Windows **0/43** e Android **0/1** |
| B/C/D aprovados | **0/13** |
| R07, R08, R09 | **PENDING** |
| Sinnoh | **planned / não jogável** |

Os vínculos L14 entre **IDs de pedidos L13** são projeções documentais dos 1.084 vínculos L11. Eles não são provas de dependências físicas executadas nem atestados de direitos.

## Regras de dependência

- Pedido de bloqueio B09/B10/B11/R07/R08: **sem pré-requisito documental adicionado**. Continua bloqueado até evidência humana/QA real, fora do escopo desta fase.
- Pedido R09: **gate regional global**, sem nova relação por caso e sem autorização nativa.
- Pedido de critério humano L04: aponta documentalmente para seu pedido de bloqueio correspondente. **20 relações.**
- Pedido de caso nativo G12: aponta para os pedidos de **seus bloqueios públicos** e **seus critérios L04**. **218 + 846 relações**. Nenhum vínculo inventado com R09.
- Cinco posições anônimas para relatórios e treze posições contábeis B/C/D: **sem vínculo ou atribuição física inferida**; nenhuma representa um arquivo recebido. **18 linhas anônimas**, todas com zero dependências.
- Prioridades **P0–P4** herdadas da L13 preservadas exclusivamente para acompanhamento documental. **Não** são sequência de execução de QA, nem direito de instalar ou testar.

As 43 entradas nativas Windows são vinculadas a B10/B11; o único caso Android/JoiPlay não recebe esses bloqueios de Windows. `watch_unchanged` não prova isolamento global de saves. R07 não prova MapIDs reservados; R08 não prova direitos sobre assets.

## Proveniência verificável — somente GitHub público

| Etapa | Commit fixo |
| --- | --- |
| L07 | `d98033b362dac82347e0d97cb5606870eaa70b22` |
| L08 | `8617ef47ea6745920cb6fe4be251982380d7628d` |
| L09 | `39e51de92aafdab3f5aea3f929f57f5c0bb72b2d` |
| L10 | `7fd821007e63fe9cf0d0c4bf14d153a23cda2b6a` |
| L11 | `9d901a0cf21aa2742f731ee387a51f945bac8a5d` |
| L12 | `58b7f2fec9f66dee06d95676eec66fb2ded6a1de` |
| L13 | `1f12bcc86c10dcc934b024a0562cdadb65d5e2c2` |
| Blob Git do JSON L13 | `357215cdfd96b37eaac291e1c0ab3873069a12fe` |

O SHA-1 é o **identificador do objeto Git público L13**, não hash de arquivo privado. Confirma somente bytes no repositório, não a proveniência física, legalidade de ativos ou execuções nativas. O hash do merge L14 será documentado na issue após checks e integração.

## Artefatos

- [Matriz versionada L14](../data/regions/sinnoh-l14-public-readiness-matrix.json) e [espelho público do portal](../site/public/data/sinnoh-l14-public-readiness-matrix.json).
- [Painel read-only L14](../site/public/sinnoh-l14-prontidao.html), rota `/sinnoh-l14-prontidao.html`, com busca, prioridades, tipos, plataformas, estado e filtro de relações.
- [Auditor fail-closed](../scripts/regions/audit_sinnoh_l14_readiness.py) de arquivos JSON públicos fixos. Calcula a matriz esperada a partir da L13, verifica ambos os blobs Git L13, executa a cadeia L13→L12→L11→L10→L09→L08→L07→L06→L05→L04→G12 e recusa divergência de conteúdo, plataforma, IDs, autorização, espelho ou relações.
- [Testes de integridade Python](../tests/test_sinnoh_l14_readiness.py), incluindo mais de 25 casos negativos sintéticos, sem execução do jogo.
- [Testes Node do painel](../site/tests/sinnoh-l14-public-readiness.test.mjs) e [workflow CI dedicado](../.github/workflows/sinnoh-l14-public-readiness.yml) com regressões L13–L00/G12 e build completo do portal.

### Todos os 88 pedidos na matriz

| # | Pedido L13 | Plataforma | Prioridade documental | Vínculos públicos | Prontidão |
| ---: | --- | --- | --- | ---: | --- |
| 1 | `L13-BLOCKER-B09` | cross-platform | P0 | 0 | `BLOCKED` |
| 2 | `L13-BLOCKER-B10` | windows | P0 | 0 | `BLOCKED` |
| 3 | `L13-BLOCKER-B11` | windows | P0 | 0 | `BLOCKED` |
| 4 | `L13-BLOCKER-R07` | cross-platform | P0 | 0 | `BLOCKED` |
| 5 | `L13-BLOCKER-R08` | cross-platform | P0 | 0 | `BLOCKED` |
| 6 | `L13-GLOBAL-R09` | global | P0 | 0 | `BLOCKED` |
| 7 | `L13-REPORT-01` | unassigned | P1 | 0 | `BLOCKED` |
| 8 | `L13-REPORT-02` | unassigned | P1 | 0 | `BLOCKED` |
| 9 | `L13-REPORT-03` | unassigned | P1 | 0 | `BLOCKED` |
| 10 | `L13-REPORT-04` | unassigned | P1 | 0 | `BLOCKED` |
| 11 | `L13-REPORT-05` | unassigned | P1 | 0 | `BLOCKED` |
| 12 | `L13-HUMAN-B09_ORIGIN` | cross-platform | P2 | 1 | `BLOCKED` |
| 13 | `L13-HUMAN-B09_CLONE` | cross-platform | P2 | 1 | `BLOCKED` |
| 14 | `L13-HUMAN-B09_ASSETS` | cross-platform | P2 | 1 | `BLOCKED` |
| 15 | `L13-HUMAN-B09_RECEIPT` | cross-platform | P2 | 1 | `BLOCKED` |
| 16 | `L13-HUMAN-B10_LINK` | windows | P2 | 1 | `BLOCKED` |
| 17 | `L13-HUMAN-B10_READONLY` | windows | P2 | 1 | `BLOCKED` |
| 18 | `L13-HUMAN-B10_OFFLINE` | windows | P2 | 1 | `BLOCKED` |
| 19 | `L13-HUMAN-B10_PLATFORM` | windows | P2 | 1 | `BLOCKED` |
| 20 | `L13-HUMAN-B11_SESSION` | windows | P2 | 1 | `BLOCKED` |
| 21 | `L13-HUMAN-B11_SCOPE` | windows | P2 | 1 | `BLOCKED` |
| 22 | `L13-HUMAN-B11_DIFFERENCE` | windows | P2 | 1 | `BLOCKED` |
| 23 | `L13-HUMAN-B11_LIMIT` | windows | P2 | 1 | `BLOCKED` |
| 24 | `L13-HUMAN-R07_NATIVE` | cross-platform | P2 | 1 | `BLOCKED` |
| 25 | `L13-HUMAN-R07_REGIONS` | cross-platform | P2 | 1 | `BLOCKED` |
| 26 | `L13-HUMAN-R07_CONFLICT` | cross-platform | P2 | 1 | `BLOCKED` |
| 27 | `L13-HUMAN-R07_TOPOLOGY` | cross-platform | P2 | 1 | `BLOCKED` |
| 28 | `L13-HUMAN-R08_LICENSE` | cross-platform | P2 | 1 | `BLOCKED` |
| 29 | `L13-HUMAN-R08_GRAPHICS` | cross-platform | P2 | 1 | `BLOCKED` |
| 30 | `L13-HUMAN-R08_EVENTS` | cross-platform | P2 | 1 | `BLOCKED` |
| 31 | `L13-HUMAN-R08_PBS` | cross-platform | P2 | 1 | `BLOCKED` |
| 32 | `L13-BCD-01` | global | P3 | 0 | `BLOCKED` |
| 33 | `L13-BCD-02` | global | P3 | 0 | `BLOCKED` |
| 34 | `L13-BCD-03` | global | P3 | 0 | `BLOCKED` |
| 35 | `L13-BCD-04` | global | P3 | 0 | `BLOCKED` |
| 36 | `L13-BCD-05` | global | P3 | 0 | `BLOCKED` |
| 37 | `L13-BCD-06` | global | P3 | 0 | `BLOCKED` |
| 38 | `L13-BCD-07` | global | P3 | 0 | `BLOCKED` |
| 39 | `L13-BCD-08` | global | P3 | 0 | `BLOCKED` |
| 40 | `L13-BCD-09` | global | P3 | 0 | `BLOCKED` |
| 41 | `L13-BCD-10` | global | P3 | 0 | `BLOCKED` |
| 42 | `L13-BCD-11` | global | P3 | 0 | `BLOCKED` |
| 43 | `L13-BCD-12` | global | P3 | 0 | `BLOCKED` |
| 44 | `L13-BCD-13` | global | P3 | 0 | `BLOCKED` |
| 45 | `L13-NATIVE-ball-TURTWIG` | windows | P4 | 25 | `BLOCKED` |
| 46 | `L13-NATIVE-barry-TURTWIG-normal-win` | windows | P4 | 25 | `BLOCKED` |
| 47 | `L13-NATIVE-barry-TURTWIG-normal-loss` | windows | P4 | 25 | `BLOCKED` |
| 48 | `L13-NATIVE-barry-TURTWIG-master-win` | windows | P4 | 25 | `BLOCKED` |
| 49 | `L13-NATIVE-barry-TURTWIG-master-loss` | windows | P4 | 25 | `BLOCKED` |
| 50 | `L13-NATIVE-save-reload-TURTWIG` | windows | P4 | 23 | `BLOCKED` |
| 51 | `L13-NATIVE-ball-CHIMCHAR` | windows | P4 | 25 | `BLOCKED` |
| 52 | `L13-NATIVE-barry-CHIMCHAR-normal-win` | windows | P4 | 25 | `BLOCKED` |
| 53 | `L13-NATIVE-barry-CHIMCHAR-normal-loss` | windows | P4 | 25 | `BLOCKED` |
| 54 | `L13-NATIVE-barry-CHIMCHAR-master-win` | windows | P4 | 25 | `BLOCKED` |
| 55 | `L13-NATIVE-barry-CHIMCHAR-master-loss` | windows | P4 | 25 | `BLOCKED` |
| 56 | `L13-NATIVE-save-reload-CHIMCHAR` | windows | P4 | 23 | `BLOCKED` |
| 57 | `L13-NATIVE-ball-PIPLUP` | windows | P4 | 25 | `BLOCKED` |
| 58 | `L13-NATIVE-barry-PIPLUP-normal-win` | windows | P4 | 25 | `BLOCKED` |
| 59 | `L13-NATIVE-barry-PIPLUP-normal-loss` | windows | P4 | 25 | `BLOCKED` |
| 60 | `L13-NATIVE-barry-PIPLUP-master-win` | windows | P4 | 25 | `BLOCKED` |
| 61 | `L13-NATIVE-barry-PIPLUP-master-loss` | windows | P4 | 25 | `BLOCKED` |
| 62 | `L13-NATIVE-save-reload-PIPLUP` | windows | P4 | 23 | `BLOCKED` |
| 63 | `L13-NATIVE-warp-SN_BEDROOM_TO_1F` | windows | P4 | 24 | `BLOCKED` |
| 64 | `L13-NATIVE-npc-SN_NPC_MOTHER` | windows | P4 | 25 | `BLOCKED` |
| 65 | `L13-NATIVE-warp-SN_1F_TO_BEDROOM` | windows | P4 | 24 | `BLOCKED` |
| 66 | `L13-NATIVE-warp-SN_1F_TO_TWINLEAF` | windows | P4 | 24 | `BLOCKED` |
| 67 | `L13-NATIVE-warp-SN_TOWN_TO_HOME` | windows | P4 | 24 | `BLOCKED` |
| 68 | `L13-NATIVE-warp-SN_TOWN_TO_BARRY_HOME` | windows | P4 | 24 | `BLOCKED` |
| 69 | `L13-NATIVE-warp-SN_TOWN_TO_ROUTE201` | windows | P4 | 24 | `BLOCKED` |
| 70 | `L13-NATIVE-npc-SN_NPC_BARRY_INTRO` | windows | P4 | 25 | `BLOCKED` |
| 71 | `L13-NATIVE-warp-SN_BARRY_HOME_TO_TOWN` | windows | P4 | 24 | `BLOCKED` |
| 72 | `L13-NATIVE-warp-SN_ROUTE201_TO_TOWN` | windows | P4 | 24 | `BLOCKED` |
| 73 | `L13-NATIVE-warp-SN_ROUTE201_TO_LAKE` | windows | P4 | 24 | `BLOCKED` |
| 74 | `L13-NATIVE-warp-SN_ROUTE201_TO_SANDGEM` | windows | P4 | 24 | `BLOCKED` |
| 75 | `L13-NATIVE-npc-SN_NPC_ROWAN_BRIEFCASE` | windows | P4 | 25 | `BLOCKED` |
| 76 | `L13-NATIVE-npc-SN_NPC_BARRY_BATTLE` | windows | P4 | 25 | `BLOCKED` |
| 77 | `L13-NATIVE-warp-SN_LAKE_TO_ROUTE201` | windows | P4 | 24 | `BLOCKED` |
| 78 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROUTE201` | windows | P4 | 24 | `BLOCKED` |
| 79 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROWAN_LAB` | windows | P4 | 24 | `BLOCKED` |
| 80 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROUTE202` | windows | P4 | 24 | `BLOCKED` |
| 81 | `L13-NATIVE-npc-SN_NPC_ROWAN_POKEDEX` | windows | P4 | 25 | `BLOCKED` |
| 82 | `L13-NATIVE-warp-SN_ROWAN_LAB_TO_TOWN` | windows | P4 | 24 | `BLOCKED` |
| 83 | `L13-NATIVE-warp-SN_ROUTE202_TO_SANDGEM` | windows | P4 | 24 | `BLOCKED` |
| 84 | `L13-NATIVE-regression-DECADES` | windows | P4 | 24 | `BLOCKED` |
| 85 | `L13-NATIVE-regression-KANTO` | windows | P4 | 24 | `BLOCKED` |
| 86 | `L13-NATIVE-regression-JOHTO` | windows | P4 | 24 | `BLOCKED` |
| 87 | `L13-NATIVE-regression-HOENN` | windows | P4 | 24 | `BLOCKED` |
| 88 | `L13-NATIVE-android-joi-play` | android | P4 | 15 | `BLOCKED` |

## Uso documental permitido

```sh
python scripts/regions/audit_sinnoh_l14_readiness.py
python -m unittest discover -s tests -p 'test_sinnoh_l14_readiness.py' -v
```

**Não acessar:** PC, Game.exe, Windows Sandbox, JoiPlay, saves, ROM, ZIP/PNG privados, arquivos pessoais, licenças privadas ou endpoints de upload. Esses comandos validam apenas arquivos fixos do repositório público. A L14 não coleta recibos, não substitui revisão humana e não concede uma única aprovação nativa.
