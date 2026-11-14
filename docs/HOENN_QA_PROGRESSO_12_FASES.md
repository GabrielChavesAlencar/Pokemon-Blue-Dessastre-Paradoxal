# Hoenn — barra de progresso jogável (12 fases)

**Atualizado:** 14/11/2026. Referência de dados: [hoenn-qa-progresso.json](../data/regions/hoenn-qa-progresso.json). Etapa técnica anterior: [10/10](HOENN_ETAPA_10_SOOTOPOLIS_RAYQUAZA_LIGA.md).

**Acompanhe as DUAS barras separadamente:**

- **Etapas de código existentes:** 10/10 — ██████████ (concluídas e publicadas, sem certificar Game.exe).
- **Fases jogáveis 1–12:** preparação da fase 1 implementada; execução/aceite pendente — ▣□□□□□□□□□□□ (▣ = ferramenta pronta; NÃO = jogável).
- **Fases nativamente aprovadas:** 0/12 — □□□□□□□□□□□□ (sem testes reais completos).

| # | Etapa | Preparação | Aceite Game.exe |
|---:|---|---|---|
| 1 | Gerar cópia isolada com 199 mapas e PBS | **Ferramenta preparada, execução local pendente** | ⏳ |
| 2 | Corrigir conexões e colisões dos mapas | Pendente | ⏳ |
| 3 | Conferir encontros, NPCs, treinadores e itens | Pendente | ⏳ |
| 4 | Surf, Dive, Waterfall, Strength e puzzles | Pendente | ⏳ |
| 5 | Equipes Aqua/Magma, Seafloor Cavern | Pendente | ⏳ |
| 6 | Cave of Origin, clima, Rayquaza | Pendente | ⏳ |
| 7 | Oito ginásios e insígnias locais | Pendente | ⏳ |
| 8 | Victory Road e Wally | Pendente | ⏳ |
| 9 | Elite Four e Wallace | Pendente | ⏳ |
| 10 | Hall of Fame e pós-jogo | Pendente | ⏳ |
| 11 | Traduções, placas, áudio e Trainer Card | Pendente | ⏳ |
| 12 | QA da campanha inteira Windows/Android | Pendente | ⏳ |

**Regra:** nenhuma fase muda para "aprovada" só porque a CI ou um simulador Ruby passaram; exige observação real no Game.exe.

## Fase 01/12 — código implementado

- [scripts/regions/hoenn_qa_phase1.py](../scripts/regions/hoenn_qa_phase1.py) confere a pasta Blue, MapIDs livres, inventário da fonte fixada, arquivos e SHA dos 199 RXDATA originais, tilesets, PNGs usados, sete áudios-base, PBS, oito chefes e perfil de save separado.
- [TESTAR_HOENN.bat](../TESTAR_HOENN.bat) prepara uma **nova pasta** e inicia o Game.exe isolado. A primeira abertura pode compilar e fechar; execute novamente caso ocorra.
- [tests/test_hoenn_qa_phase1.py](../tests/test_hoenn_qa_phase1.py) cobre ausência de arquivos, fonte divergente, MapIDs duplicados, perfil, integridade e bloqueio de substituição.
- O relatório local em `.blue-work/hoenn-qa-fase01-report.json` registra o resultado. Ele não é enviado ao GitHub.
- A árvore pública do doador é fixada em `c59233bdbaac4fbfeca6aa01c7f05be628da2a92`, usando subárvore Git `c3876ecea7545eb3a91b9c8748d7e2b13f07805d`. Não inventar arquivos se houver divergência de versão ou ZIP.

### Executar no Windows

1. Atualize a `main` (por `RUN.bat` ou `git pull origin main`).
2. Tenha a base principal Blue instalada em `game/`, com `game/Game.exe`, `Data/`, `PBS/` e `Plugins/`.
3. Coloque o ZIP privado `The Pokémon World Project - Hoenn.zip` na raiz do clone, sem extrair mapas para o `game/`. Instale Python 3.11+ e tenha internet na primeira execução para obter a árvore de hashes do GitHub.
4. Execute **`TESTAR_HOENN.bat`**. Ele usa `.blue-work/hoenn-source/<prefixo-hash>/` e cria `.blue-work/hoenn-qa-fase01/` sem tocar na instalação principal. Se a fonte não coincidir com a revisão fixada, a montagem abortará com relatório.
5. Confirme no relatório: `copy.maps_present=199`, `copy.trainer_boss_pbs_entries=8`, `copy.distinct_save_profile="Hoenn Piloto"`. Isso ainda é verificação de **arquivos**, não de jogabilidade.
6. No Game.exe da cópia, aguarde a compilação. Se fechar depois dela, abra o BAT outra vez. Verifique os marcadores `Data/blue-hoenn-compiled.txt` e mensagens de erro.
7. Faça novo jogo; confirme início em casa em Littleroot, sprite e movimentação, pelo menos uma porta, inicial, uma batalha e Centro Pokémon. Teste **salvar, fechar e carregar**.
8. Abra Decades principal e seu save anterior. Confirme que a cópia não alterou os dados nem o perfil de save principal.

**Comandos equivalentes:**

~~~powershell
py -3 scripts/regions/hoenn_qa_phase1.py
py -3 scripts/regions/hoenn_qa_phase1.py --prepare
py -3 scripts/regions/hoenn_qa_phase1.py --prepare --offline
~~~

O primeiro é auditoria de pasta, não instala; `--prepare` usa o ZIP; `--offline` só funciona após gerar o inventário local fixo.

### Checklist de aprovação real 1/12 — pendente

- [ ] 199 RXDATA e dependências fonte verificadas na máquina; base Blue preservada.
- [ ] Game.exe recompilou PBS e abriu sem erro (não confundir presença de marcador com teste visual).
- [ ] Novo jogo em Littleroot, início, porta, NPC, inicial e batalha testados.
- [ ] Save/reload funciona no perfil separado; save Decades intacto.
- [ ] Logs/relatório e capturas revisados; não há erro bloqueante de compilação.
- [ ] Direitos/créditos dos assets a distribuir avaliados antes de fazer pacote público.

A auditoria de arquivos e testes sintéticos NÃO executam o Game.exe. A fase 1 só fica **1/12 aprovada** quando houver evidência da execução no computador. A fase seguinte será **2/12 — mapas/conexões**.

**Preservação:** ZIP e arquivos `.rxdata`, áudios, PNG e Game.exe do doador não devem ser enviados à branch pública. Os bugs conhecidos do ginásio de Mossdeep, Steven, Dive, Sky Pillar e Hall of Fame permanecem tarefas das fases seguintes.
