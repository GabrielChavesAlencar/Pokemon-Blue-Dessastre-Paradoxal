# Sinnoh B01 — Coleta segura de MapIDs do Decades

**Recebido em 17/11/2026:** ZIP de inventário real entregue pelo usuário; veja os [resultados: 648 MapIDs ocupados e 72 conflitos com Sinnoh](SINNOH_B01_RESULTADO_REAL_MAPIDS_2026-11-17.md). As instruções abaixo ficam disponíveis para gerar novos snapshots quando a instalação for atualizada. Os direitos e as reservas futuras seguem pendentes, B/C/D 0/13.

Esta fase gera o inventário da instalação local sem executar Game.exe, JoiPlay nem alterar saves. Os 76 IDs de origem de Sinnoh já estão documentados em B00, mas seus IDs de destino continuam desconhecidos sem o índice real do Decades.

## Para o usuário no Windows

1. Baixar o arquivo **SINNOH_B01_COLETOR_MAPIDS.zip** entregue nesta conversa.
2. Extrair os três arquivos em uma pasta qualquer.
3. Dar duplo clique em **COLETAR_MAPIDS_SINNOH.cmd**. Não é preciso abrir PowerShell nem instalar Python: o CMD invoca o coletor integrado ao Windows.
4. Se o diretório do Pokémon Blue não for detectado, selecionar a pasta **game/Data** na janela.
5. Enviar ao ChatGPT o ZIP gerado **SINNOH_B01_INVENTARIO_DECADES.zip**.

O ZIP contém somente `MapInfos.rxdata`, `Tilesets.rxdata` e `native_inventory.json`. Nenhum save, arquivo `MapNNN.rxdata`, Game.exe, script, sprite ou música é transferido. O usuário decide se envia o resultado.

## Análise no repositório

O [auditor B01](../scripts/regions/audit_sinnoh_b01_inventory.py) valida os hashes e a lista física de MapIDs, analisa `MapInfos.rxdata` com o leitor inerte Ruby Marshal do Blue e confronta o resultado com os **76 IDs reais** do [recibo de origem](../data/regions/sinnoh-b00-actual-source.json).

```bash
python scripts/regions/audit_sinnoh_b01_inventory.py --inventory SINNOH_B01_INVENTARIO_DECADES.zip
```

O relatório mostra IDs ocupados, sobreposições de origem, intervalos conservadores fisicamente vazios entre 1 e 599 e inconsistências entre `MapInfos` e arquivos físicos. **Uma vaga física não equivale a uma reserva aprovada**: Kanto/Johto/Hoenn planejados ainda podem usar IDs livres. A faixa 600–999 continua excluída e 1000+ não está homologada.

O auditor sempre retorna `can_select_destinations=false`, `can_install=false` e `phase_b_approved=0`. Também foram adicionados **12 testes sintéticos** de ZIP, hash, índice RMXP e alegações nativas falsas.

**B/C/D continuam 0/13.** Esta etapa é preparação do remapeamento; os testes manuais permanecem adiados a pedido do usuário.
