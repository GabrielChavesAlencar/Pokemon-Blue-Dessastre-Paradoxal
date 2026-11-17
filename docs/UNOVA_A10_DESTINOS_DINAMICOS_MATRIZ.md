# Unova A10 — destinos dinâmicos e matriz de segurança para MapIDs 518–599

**17/11/2026 · apenas diagnóstico · não executa Game.exe nem Ruby nem altera os dados do jogo.**

## Fonte real A09 fornecida pelo usuário
O relatório \`LEIA_AQUI_UNOVA_MAPIDS(3).txt\` da instalação
\`%LOCALAPPDATA%\PokemonBlueDessastreParadoxal\game\` informa:
- A04: **648/648** MapIDs observados, MapInfos SHA-256 \`8f2d23d49ee0bb97779b129ffd7d14c161f4bef27fede6b89111ce266760a420\`;
- A06: **1.798** transferências estáticas, destino ausente **3**, nenhuma referência estática relatada ao intervalo \`518–599\`;
- A07/A08: duas transferências de \`Map001\` para **MapID 3**, originadas em **evento 1 — Intro, página 1** e **evento 2 — Quick start intro, página 1**;
- A09: páginas das introduções possuem **154** e **24** comandos respectivamente, gatilho \`ACTION_BUTTON\` nas quatro páginas; **22** ocorrências textuais classificadas (1 definição, 20 simbólicas/computadas, 0 literais para 3 e 0 para 518–599). O relatório **não descreve execução de condições em runtime**;
- Manifestos locais Kanto/Johto/Hoenn disponíveis, Sinnoh/Unova ausentes, cobertura incompleta. Bloco 518–599 ainda somente **candidato**.

O usuário não forneceu o JSON detalhado A09; os detalhes dos comandos não podem ser inferidos do resumo textual. A10 os examina **no próprio PC** e produz a evidência JSON.

## Entrega A10
1. **Confronto A04/A06/A07/A08/A09** no mesmo snapshot/hash. Falhas bloqueiam o diagnóstico; nunca convertem falta de evidência em confirmação de liberdade.
2. **Map001 eventos 1 e 2**: registra página, flags de condições, somente entradas de condições habilitadas, gatilho, transferências do comando RMXP 201, posição dos comandos e controles de fluxo anteriores (sem executar códigos Ruby, com dados reduzidos).
3. **Scripts computados**: usa as classificações A09, preserva proveniência de chamadas simbólicas e indica explicitamente que os destinos não foram resolvidos por execução.
4. **Manifestos locais**: lê JSONs conhecidos de Kanto, Johto, Hoenn, Sinnoh e Unova dentro de \`game/Data\`, observando esquemas comuns de mapeamento, mas sem considerar inexistência, chaves desconhecidas ou prova parcial como ausência de reservas futuras.
5. **Matriz com 82 linhas** para \`518–599\`:
    - \`OCCUPIED_IN_CURRENT_SNAPSHOT\`;
    - \`INSTALLER_MANIFEST_CLAIM_REVIEW\`;
    - \`STATIC_REFERENCE_REVIEW\`;
    - \`OBSERVED_VACANT_NOT_RESERVED\`.
   **Nenhum** status autoriza instalação ou garante ID livre no futuro. \`approved_for_reservation=false\` em todas as linhas.
6. Salva \`a10-dynamic-matrix-<hash>.json\` no cache privado e acrescenta o resumo A10 ao \`LEIA_AQUI_UNOVA_MAPIDS.txt\` do BAT autocontido.

## Limitações e próximos bloqueios
- Condições de página, branches e variáveis não são executadas: não se comprovou que os dois caminhos de introdução realmente executam um warp para MapID 3.
- Não foi identificado destino substituto correto; **não alterar, renumerar nem excluir eventos 1/2** sem validação de design e progressão.
- A varredura é heurística; APIs não reconhecidas, valores calculados, plugins, scripts de outras fontes e claims futuros do Blue-Story ficam pendentes.
- Não existem reservas Unova homologadas, fonte nativa/tilesets comprovados, remap, rollback, teste Game.exe nem Android nesta fase.
- **Barra A 0/8** e **Unova jogável 0/32** permanecem inalteradas.

## Como entregar evidência
Rodar \`RUN_UNOVA_MAPIDS.bat\` (Python >=3.11) em Windows. Enviar o novo
\`LEIA_AQUI_UNOVA_MAPIDS.txt\` e **principalmente** o caminho \`a10-dynamic-matrix-*.json\`
mostrado na seção A10. Nenhum ZIP de mapas nem alteração nativa é exigido.
