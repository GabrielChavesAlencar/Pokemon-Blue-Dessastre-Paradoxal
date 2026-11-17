# Unova — A08: contexto dos eventos de Map001 e provas do instalador

**17/11/2026. Auditoria somente leitura; não reserva MapIDs e não altera Game.exe, MapInfos, scripts, saves, mapas ou Blue-Story.**

## Evidência real fornecida pelo usuário (A07)
Arquivo \`LEIA_AQUI_UNOVA_MAPIDS(1).txt\`:
- A04: 648 MapIDs observados, MapInfos SHA-256 \`8f2d23d49ee0bb97779b129ffd7d14c161f4bef27fede6b89111ce266760a420\`, nenhuma nova sobreposição.
- A06: 648/648 mapas, 1798 transferências estáticas, destino ausente MapID 3, 87247 comandos de script não executados, nenhuma referência estática observada a 518–599.
- A07: **duas** transferências para MapID 3: **Map001 evento 1 página 1** e **Map001 evento 2 página 1**; zero pistas literais do scanner restrito; CommonEvents \`READ_ONLY_INSPECTED\`, Scripts \`TEXT_SCANNED_INERT\`; zero erros de varredura.
- Esses números são observações do relatório, não prova de ausência de transferências geradas dinamicamente nem de segurança do destino 3.

## O que a A08 faz
1. Revalida cadeia **A04→A06→A07**, hashes e integridade do \`Map001.rxdata\`, sem executar comandos.
2. Examina os eventos 1 e 2: nome, posição, páginas, índices de comandos de transferência, destino, coordenadas, gatilho, flags/IDs das condições e contagem de comandos. **Não avalia se a página é realmente ativada em jogo.**
3. Confronta as transferências observadas no Map001 com os índices vindos da A07; registra evento ausente ou divergências.
4. Inspeciona, quando disponíveis, os manifestos locais \`game/Data/blue-kanto-install.json\`, \`blue-johto-main-preview.json\`, \`blue-hoenn-install.json\`, \`blue-sinnoh-install.json\` e \`blue-unova-install.json\`. Verifica possíveis destinos no bloco 518–599, mas não trata arquivos ausentes ou formatos desconhecidos como prova de ausência de conflito. Os manifestos só capturam reservas existentes, não instalações futuras.
5. Compara os dados de planejamento A05/B03/B05 existentes no pacote. Também coleta **indícios heurísticos** de possíveis transferências computadas nos scripts do Map001 e de Scripts.rxdata. Não inspeciona todos os scripts em todas as fontes e não executa Ruby.
6. Grava relatório privado imutável \`a08-readiness-HASH.json\` e atualiza \`LEIA_AQUI_UNOVA_MAPIDS.txt\` com a seção A08. O BAT portátil contém as dependências e só necessita Python 3.11+.

## Critérios de bloqueio da aprovação
- Sem decisão sobre a intenção dos dois eventos que apontam para o MapID 3, inclusive condições e efeitos em runtime;
- Sem auditoria conclusiva de todas as referências dinâmicas, plugins e futuras operações de Blue-Story;
- Sem arquivo-fonte dos mapas de Unova com direitos verificados e plano real de mapeamento/rollback;
- Sem teste de progressão de jogo no Game.exe.

**Nenhuma reserva, remapeamento, instalação, exclusão de eventos ou marcação como jogável é autorizada pela A08.** Os códigos de estado de diagnóstico não equivalem a sucesso jogável. Barra A = 0/8, jogável = 0/32.

## Resultado esperado na máquina do usuário
No resumo A08: quantidade de eventos Map001 descritos, confronto com A07, contexto de condições, indícios em scripts, possíveis conflitos de manifestos e caminho do relatório JSON. O **JSON A08** é a fonte mais detalhada; se a interpretação dos eventos exigir exame da página, o usuário deve enviá-lo.

## Próxima decisão
Avaliar manualmente o JSON A08. Resolver o destino 3 por evidência de design e testes reais, sem "corrigir" o jogo por adivinhação. Só então considerar uma etapa de preparação de reserva com rollback e verificação de ownership/installer de todas as regiões.
