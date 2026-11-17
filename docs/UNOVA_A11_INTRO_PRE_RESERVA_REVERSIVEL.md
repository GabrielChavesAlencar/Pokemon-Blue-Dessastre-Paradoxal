# Unova A11 — validação inerte das introduções e pré-reserva reversível

**17/11/2026 · Somente diagnóstico.** Não instala Unova, não altera MapInfos, mapas, Scripts, Game.exe ou saves e **não cria backup nativo**.

## Evidência da A10 executada no computador do usuário

Fonte: \`LEIA_AQUI_UNOVA_MAPIDS(4).txt\`. Baseline MapInfos SHA-256 \`8f2d23d49ee0bb97779b129ffd7d14c161f4bef27fede6b89111ce266760a420\`, **648 mapas** examinados. O intervalo **518–599** tem **82 candidatos observados desocupados**, **sem reserva**. O MapID 3 segue ausente apesar de duas transferências em Map001, evento 1 (\`Intro\`) e evento 2 (\`Quick start intro\`). A09 classifica **20 expressões computadas**; nenhuma foi executada. Os manifestos Kanto/Johto/Hoenn são apenas parcialmente reconhecidos; Sinnoh/Unova não foram encontrados.

A saída A10 apresenta \`DESCONHECIDO\` nas categorias ausentes do histograma, embora todos os 82 IDs estejam classificados como \`OBSERVED_VACANT_NOT_RESERVED\`; a A11 corrige o **resumo de apresentação** para exibir zero, **somente quando a matriz contabiliza integralmente os 82 IDs**. Não transforma essa observação em uma reserva homologada.

## O que faz

1. Exige relatórios A04–A10 coerentes e mesmo hash do MapInfos. Se A10 estiver bloqueada, a A11 não pode alegar sucesso.
2. Lê as páginas dos eventos de introdução descritas em A10, conserva gatilhos, condições habilitadas, existência de páginas superiores, índice do comando 201 e controles imediatamente anteriores. **A ativação real e a prioridade entre páginas dependem do runtime e permanecem desconhecidas.**
3. Reexamina *como texto inerte* Scripts.rxdata e os scripts de evento 355/655 de Map001 eventos 1/2. Para chamadas dinâmicas, registra **tipo de expressão** e uma impressão SHA-256 curta, sem copiar texto de scripts. Compara as contagens com A09, mantendo quaisquer diferenças como bloqueio.
4. Gera uma matriz explícita **82/82** de pré-reserva, com todas as categorias contadas (inclusive zero) e todos os IDs com \`reserved=false\`, \`safe_to_write=false\`. Confere a ocupação de A04 em cada ID e rejeita aprovações forjadas.
5. Registra um **protocolo de rollback em rascunho**, com requisitos futuros de backup de MapInfos, mapas, tilesets, scripts, recursos, instaladores regionais e saves, além de SHA-256 de pré-instalação e testes em cópia isolada. Nenhum backup, arquivo nativo ou instalador é produzido.
6. Salva \`a11-intro-preflight-HASH.json\` em cache privado e abre \`LEIA_AQUI_UNOVA_MAPIDS.txt\` com a seção A11 pelo BAT de 16 arquivos.

## Gatilhos de revisão obrigatória

- MapID 3 permanece sem mapa de destino e sem verificação de comportamento de Intro/Quick start intro no Game.exe.
- Referências computadas podem usar variáveis e APIs fora dos padrões encontrados. Análise textual não prova destinos em execução.
- O Blue-Story ainda pode atribuir mapas no futuro. Manifestos locais atuais não comprovam reservas futuras.
- Não há fonte de mapas Unova, documentação de direitos, remapeamento físico ou roteiro de teste nativo/Android aprovados.
- Um plano de rollback **não equivale a backup executado**; o código não escreve na instalação.

**Barras:** A = **0/8**, Unova jogável = **0/32**. A próxima decisão requer o JSON A11 completo e validação real em ambiente isolado antes de qualquer atribuição nativa.

## Como testar

Baixar/extrair o ZIP do RUN A11, executar \`RUN_UNOVA_MAPIDS.bat\` (Python >= 3.11). Enviar \`LEIA_AQUI_UNOVA_MAPIDS.txt\` e principalmente \`a11-intro-preflight-HASH.json\`. Não solicitar execução manual de PowerShell.
