# Sinnoh — Barra B / B02: reservas regionais reais e declaradas

**Data:** 17/11/2026  
**Resultado:** auditoria do inventário B01 e dos contratos de instalação de Kanto, Johto e Hoenn. **Os MapIDs de Sinnoh NÃO foram alocados**. B/C/D continuam **0/13**, R07 continua pendente (6/9 na trilha de remapeamento).

## Evidência realmente auditada

1. O ZIP enviado pelo usuário em B01 revelou **648 MapIDs presentes** em arquivos e em `MapInfos.rxdata`, com os hashes registrados em [B01](SINNOH_B01_RESULTADO_REAL_MAPIDS_2026-11-17.md).
2. O manifesto de [reservas CH05](../data/regions/sinnoh-map-id-reservations.json) e os instaladores existentes declaram **600–699 para a prévia Johto**, **700–999 como faixa de alocação do instalador Hoenn**. Esses intervalos são **restrições de código**, não prova independente de propriedade física de cada ID.
3. O `MapInfos` real contém **100 registros na faixa Johto** e **199 na faixa Hoenn**. Os nomes observados corroboram a classificação de trabalho: ID 600 `[Johto preview] New Bark Town`, ID 699 `Casa em Ecruteak`, ID 700 `Vila Littleroot`, ID 800 `Museu de Lilycove`, ID 805 `Rota 119`, ID 898 `Cidade de Ever Grande Norte`. Os nomes não substituem os registros e provas de posse dos instaladores.
4. O índice real também contém ID 439 `Elite Four — sala de Lance` e ID 441 `Hall of Fame — Kanto`. Porém, o instalador de **Kanto remapeia dinamicamente**; a presença desses nomes **não prova que todos os IDs 1–441 pertençam a Kanto ou que seus IDs futuros estejam reservados**.

## Disponibilidade física ≠ reserva aprovada

| Segmento | Ocupação observada | Reserva de código | Decisão para Sinnoh |
|---|---:|---|---|
| 1–599 | 349 ocupados; **250 fisicamente vazios** | Reservas futuras de Kanto/Johto/Hoenn **não comprovadas** | **Não alocar** |
| 600–699 | 100 ocupados | Prévia Johto protegida | **Bloquear** |
| 700–999 | 199 ocupados, 101 vazios | Faixa do instalador Hoenn | **Bloquear inclusive vazios** |
| 1000+ | não homologado | Sem teste de compatibilidade | **Bloquear** |

Na faixa 1–599, o maior intervalo contíguo fisicamente vazio é **442–599**, com **158 IDs**. Isso basta em quantidade para os **76 mapas Sinnoh**, mas não é garantia de que os IDs possam ser utilizados, especialmente com novas fases das outras regiões. O piloto antigo de Sinnoh **800–805** está isolado e esses números já aparecem em locais de Hoenn no snapshot.

[Manifesto B02 derivado](../data/regions/sinnoh-b02-reservations.json) registra apenas hashes, intervalos, nomes observados e flags **false**. O auditor [`audit_sinnoh_b02_reservations.py`](../scripts/regions/audit_sinnoh_b02_reservations.py) reconcilia B00, B01, CH05 e o código-fonte das reservas, com bloqueios contra aprovação falsa e MapIDs pré-atribuídos. **16 testes Python** em [`test_sinnoh_b02_reservations.py`](../tests/test_sinnoh_b02_reservations.py) cobrem integridade, exclusões, documentação e fraudes. Pode opcionalmente revalidar o ZIP B01 real na máquina de análise, sem executá-lo:

```bash
python scripts/regions/audit_sinnoh_b02_reservations.py
python scripts/regions/audit_sinnoh_b02_reservations.py --inventory SINNOH_B01_INVENTARIO_DECADES.zip
```

**Nenhum arquivo `rxdata` do usuário foi copiado para a main. Nenhum tile, map ID, save, região, jogo ou pacote Android foi alterado.**

## Bloqueio concreto R07 — o que falta

Os scripts `audit_sinnoh_r07_reservations.py` e `sinnoh_s07_reconcile.py` já existem. Ainda são necessários os **três manifestos de reservas FUTURAS** efetivamente revisados para **Kanto, Johto e Hoenn**, vinculados ao mesmo SHA do MapInfos da instalação. Eles devem distinguir IDs já ocupados de IDs reservados para conteúdo **ainda não instalado**; não criar números apenas para passar nos testes. O [guia R07](SINNOH_R07_DIAGNOSTICO_RESERVAS.md) define o contrato exigido.

A **próxima etapa B03** pode pesquisar os arquivos de manifesto e instaladores reais no projeto Blue-Story para produzir propostas de reservas com evidência rastreável, mas **sem preencher `reviewed_locally=true` ou liberar Sinnoh por inferência**. Também falta resolver o conflito do **tileset 31** e direitos de uso de imagens.

**Status:** B02 (auditoria estática + snapshot) preparada e documentada; **R07, R08 e R09 não aprovados**, 44 testes Windows/JoiPlay não realizados.
