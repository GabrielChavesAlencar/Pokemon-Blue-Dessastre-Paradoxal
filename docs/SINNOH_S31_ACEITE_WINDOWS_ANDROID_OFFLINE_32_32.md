# S31 — Aceite Windows/JoiPlay: protocolo final de engenharia (32/32)

**Status: apenas a infraestrutura de coleta/reconciliação de testes está pronta.** Não foi executado Game.exe, JoiPlay, mapa real ou batalha real nesta entrega. O contrato da Barra A marca S31 como `done` **somente para a camada de engenharia de QA**, não para a certificação nativa.

## Arquivos implementados

- [Manifesto S31](../data/regions/sinnoh-s31-acceptance.json): 44 casos categorizados, 43 de Windows e 1 de Android, direitos e MapIDs ainda não comprovados, nenhuma autorização de `playable`.
- [Reconciliador S31](../scripts/regions/audit_sinnoh_s31_acceptance.py): valida o checklist estático de [CH20](../scripts/regions/audit_sinnoh_android_ch20.py), liga os IDs dos 44 casos aos eventos compilados do QA privado, usa o [auditor de evidências](../scripts/regions/audit_sinnoh_playtest.py) para conferir SHA, compile token, perfil de save e observações. É **somente leitura** e exige revisão humana independente mesmo com 44 relatos completos.
- [19 testes S31](../tests/test_sinnoh_s31_acceptance.py): falsificação de conclusão, Android, aprovações, checklist alterado, fase nativa, cópia QA sintética, caso parcialmente relatado e caminho sem QA.
- A [suíte S30](../scripts/regions/audit_sinnoh_s30_suite.py) agora rejeita qualquer tentativa de elevar B/C/D ou `native_qa_approved` **mesmo com S31 `done` em código**; a [CH19](../scripts/regions/sinnoh_ci_ch19.py) e a [CH20](../.github/workflows/sinnoh-ch20.yml) verificam o reconciliador.

## Uso

Sem cópia nativa, mostrar 44 casos pendentes, sem gravar nada:

```bash
python scripts/regions/audit_sinnoh_s31_acceptance.py
```

Com cópia QA privada já compilada e verificada em `.blue-work`:

```bash
python scripts/regions/audit_sinnoh_s31_acceptance.py --qa .blue-work/game-sinnoh-qa-XXXXXXXXXXXX
```

Para exigir evidências de todos os casos e receber exit code 2 se ainda houver pendências:

```bash
python scripts/regions/audit_sinnoh_s31_acceptance.py --qa .blue-work/game-sinnoh-qa-XXXXXXXXXXXX --require-native
```

Mesmo quando um operador registra capturas para todos os casos, o resultado é **`ALL_44_RECORDED_MANUAL_REVIEW_AND_RIGHTS_STILL_REQUIRED`**, jamais certificação automática de Game.exe/JoiPlay. A autenticidade de sessões e permissões é revisão independente, externa ao CI; o comando não libera barra nativa, região jogável nem marcador Barry.

## Pendências de campo

| Etapa | Estado efetivo | Para concluir |
|---|---|---|
| I01–I08 | **5/8** | I06–I08: mapas/sprites/spawn, PBS Barry, Game.exe/JoiPlay |
| R01–R09 | **6/9** | R07–R09: reservas MapIDs reais, fonte autorizada e QA |
| T01–T07 | **4/7** | T05–T07: 12 batalhas Barry, warps, saves, regiões, Android e revisão das provas |
| 44 casos nativos | **0/44 verificados** | 43 Windows + 1 Android, capturas/logs de sessões reais |
| Barras B/C/D | **0/13 cada** | 13 fases com aceite técnico, jogável e nativo realmente comprovado |

**Após CI e merge:** Barra A **32/32 (100% engenharia/documentação e testes offline)**, Barra E **20/20**, B/C/D 0/13. Não instalar Sinnoh nem alterar `planned` antes das provas.
