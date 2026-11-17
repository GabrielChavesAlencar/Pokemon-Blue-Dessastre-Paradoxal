# Unova — A07 rastreio do MapID 3 e de referências literais a candidatos

**17/11/2026 — diagnóstico inerte, sem instalar regiões.**

## Evidência recebida no chat

No relatório LEIA_AQUI_UNOVA_MAPIDS.txt da máquina real do usuário:
- Game.exe encontrado em LocalAppData, Decades atual com 648 IDs declarados/ocupados, SHA-256 MapInfos 8f2d23d49ee0bb97779b129ffd7d14c161f4bef27fede6b89111ce266760a420;
- A05: nenhuma nova colisão observada no conjunto de candidatos históricos (174); 518–599 permanece desocupado nos snapshots analisados; 442–517 é retenção administrativa de Sinnoh;
- A06: 648/648 mapas decodificados, 0 falhas, 1798 transferências estáticas, destino **MapID 3** não encontrado, nenhum destino estático 518–599, 0 transferências dinâmicas de comando 201 e 87247 comandos de script de evento **não executados**.

Os dados acima foram **relatados em arquivo de resumo textual**: o relatório JSON A06 com a origem do MapID 3 não foi fornecido. Não presumir que MapID 3 seja erro de progressão sem verificar o evento que o referencia.

## Entrega A07

O [auditor A07](../scripts/regions/audit_unova_a07_reference_provenance.py) usa A04/A06 do mesmo scan e faz leitura *somente de dados* de MapNNN.rxdata, CommonEvents.rxdata e Scripts.rxdata (se existirem). Em mapas, identifica o MapID de origem, ID do evento, página e índice de comandos de transferência 201 que tenham como destino o ID 3 ou algum ID de 518–599. Em scripts de evento 355/655 e texto zlib de Scripts.rxdata procura apenas **padrões literais de APIs conhecidas** de transferência, com limites conservadores.

Scripts são descompactados com teto por entrada e no total, sem execução Ruby. Os hits são **pistas**, não provas de execução nem de cobertura de todas as formas de referência. O código não divulga o texto inteiro de scripts e não comita dados nativos.

O novo [RUN_UNOVA_MAPIDS.bat](../RUN_UNOVA_MAPIDS.bat), autocontido, executa A04→A05→A06→A07 em um duplo clique sem selecionar pastas, gravando no cache privado o relatório **a07-provenance-HASH.json** e exibindo no Bloco de Notas a origem das transferências para o ID 3. Em caso de A07 bloqueada por dados incompletos, mantém as auditorias anteriores e mostra contagens desconhecidas, nunca zeros inventados.

### Gatilhos para decisão

1. Descobrir em qual evento a transferência estática aponta para 3 e verificar se ela é intenção legítima, script de debug antigo, mapa removido ou referência quebrada.
2. Examinar os indícios literais a 518–599 nos Scripts.rxdata, comandos de eventos e CommonEvents; confirmar limites, cobertura e erros de decodificação.
3. Consultar ainda o histórico de reservas e manifests do Blue-Story e scripts dinâmicos não alcançados pelas heurísticas; **zero hits textuais não significa zero referências reais**.
4. Só após essas verificações e acesso aos mapas de origem de Unova com direitos adequados elaborar plano de atribuição e rollback nativo em QA. Nenhum MapID é reservado pelo A07.

**Estado:** Barra A 0/8 (ainda não houve aceite de mapa/reserva real), E 4/8, Unova jogável 0/32. Este roteiro não muda o Game.exe, MapInfos, scripts, saves ou instalador.
