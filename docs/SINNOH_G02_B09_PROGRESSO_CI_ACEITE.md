# Sinnoh G02 — progresso visível, SHA em fluxo e revisão de CI

**17/11/2026 — etapa GitHub-only integrada à `main` pelo [PR #139](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/139).** Esta entrega não modifica o clone B09 já criado pelo usuário, não executa Game.exe e não eleva R07/R08/R09 ou as barras B/C/D.

## Resultado implementado

| Arquivo | Mudança |
| --- | --- |
| `scripts/regions/build_sinnoh_b09_native_qa.py` | Emite inventário a cada 1.000 arquivos e cópia a cada 500 em `stderr` com `flush=True`; mantém `stdout` reservado ao JSON. |
| `scripts/regions/build_sinnoh_b09_native_qa.py` | Gera SHA-256 da origem durante a transferência, reduzindo uma leitura da origem; confere depois o SHA-256 **do destino**, preservando a detecção de corrupção e a recusa de mudança de origem. |
| `tests/test_sinnoh_b09_native_qa.py` | Dois testes adicionais: progresso exclusivamente no `stderr` e recusa de arquivo alterado sem variação no tamanho. |
| `SINNOH_B09_COPIA_NATIVA_QA_PRIVADA.bat` | Informa que o progresso será exibido e que o relatório JSON é separado. |
| `docs/SINNOH_B09_CLONE_QA_NATIVO_PRIVADO_2026-11-17.md` | Registra o comportamento e as limitações da otimização. |

**Importante:** o monitor V2 e a Central Sinnoh ZIP já extraída **não são atualizados automaticamente pelo merge**. O progresso novo aparecerá somente nas execuções que utilizarem a versão atualizada do script no GitHub. Um launcher que capture `stderr` e só o imprima ao final ainda precisará de uma atualização própria. A recuperação B09 anteriormente concluída não é modificada.

## GitHub Actions do PR #139

- [Sinnoh S30](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44166296253): **success**, incluindo regressões Python/Ruby, manifesto, portal e Android estático.
- [Sinnoh CH19](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44166296419): **success**, somente fixtures Python/Ruby.
- [Kanto Windows](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44166296463): **failure**, `Boulder did not unlock Flash`.
- [Blue Studio](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44166296374): **failure**, `CutTree regression: previous protagonist scale fix was lost`.

Para separar sintomas da B09, cruzou-se o PR #139 com o [PR #142 (G01)](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/142), que não altera os arquivos Kanto nem a engine:

- [Kanto #142](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44168573734): **failure**, mesma mensagem `Boulder did not unlock Flash`;
- [Blue Studio #142](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44168573731): **failure**, mesma mensagem de escala `CutTree`;
- [S30 #142](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44168573718) e [CH19 #142](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44168573715): **success**.

**Conclusão limitada:** falhas gerais persistentes, não explicadas diretamente pelos arquivos modificados na G02. Isso não prova que existiam antes em uma `main` histórica sem quaisquer alterações; não declarar CI geral aprovado. A investigação foi aberta em [issue #144](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/144). Não expandir a G02 para reescrever mecânicas de Kanto ou escala de personagem sem testes específicos.

## Critérios de aceite G02

- [x] Alterações de progresso e SHA disponíveis no GitHub.
- [x] Testes negativos de preservação de JSON e mudança de conteúdo sem alteração de tamanho.
- [x] S30 e CH19 aprovados no PR #139.
- [x] PR #139 integrado na `main` (merge SHA `5411ab83dba48c372ee339c79d896b7460ce7c0e`).
- [x] Falhas externas de CI classificadas e abertas em issue específica.
- [ ] CI geral Kanto/Blue Studio aprovado — **fora do escopo; pendente issue #144**.
- [ ] Teste Game.exe/JoiPlay, direitos de PNG e R07–R09 — **requerem provas locais**.

**Esteira G01–G12:** G01 e G02 concluídas no GitHub (**2/12**); a próxima é **G03 — auditoria de reservas regionais e conflitos de MapIDs**, sem avançar B/C/D (**0/13**).
