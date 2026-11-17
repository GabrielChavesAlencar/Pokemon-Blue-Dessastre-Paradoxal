# Sinnoh — B03: reservas futuras e plano preliminar de MapIDs/tilesets

**Entregável:** auditoria estática dos instaladores de Kanto, Johto e Hoenn, modelos de reserva futura ainda não revisados e estratégia de conversão de tilesets. **Nenhum mapa de Sinnoh foi instalado ou recebeu MapID de destino aprovado.** A Barra B continua **0/13**, com R07, R08 e R09 pendentes; testes Game.exe/JoiPlay permanecem adiados conforme pedido.

## 1. O que o código prova — e o que não prova

| Região | Prova no GitHub | Evidência privada que ainda falta |
|---|---|---|
| Kanto | [`install_kanto.py`](../scripts/regions/install_kanto.py) lê `info["maps"]`, valida hashes e grava `Data/blue-kanto-install.json` após instalar | Manifesto real da instalação com os destinos atuais e plano de **futuros** MapIDs ainda não implantados; não inferir que todo 1–441 pertence a Kanto |
| Johto | [`johto_main_preview.py`](../scripts/regions/johto_main_preview.py) declara `PREVIEW_IDS=600..699`, confere `Data/blue-johto-main-preview.json` e preserva outros mapas | Comprovar reservas de mapas posteriores à prévia de 100 IDs, se houver; revisão local e origem rastreável |
| Hoenn | [`pilot_hoenn.py`](../scripts/regions/pilot_hoenn.py) escolhe dinamicamente em `700..999` após considerar `MapInfos`, arquivos `MapNNN`, referências PBS e a prévia de Johto | Manifesto real `Data/blue-hoenn-install.json` e a relação de novas reservas planejadas, se houver, sem adivinhar nomes/IDs |

O ZIP enviado na B01 continha **somente** `MapInfos.rxdata`, `Tilesets.rxdata` e o resumo de arquivos físicos. Ele comprovou **648 MapIDs ocupados** e permitiu comparar os nomes, **mas não continha os manifestos de instalação de Kanto/Johto/Hoenn**, nem os documentos de suas reservas futuras. Por isso, os nomes observados e as reivindicações do instalador não equivalem à propriedade exaustiva de cada ID.

O contrato já documentado [CH05](../data/regions/sinnoh-map-id-reservations.json) protege **600–699** para Johto e **700–999** para Hoenn, mesmo se alguns arquivos dessa faixa ainda estiverem ausentes. Nenhum ID dentro ou fora dessas faixas foi atribuído a Sinnoh.

## 2. Plano preliminar: apenas cenário hipotético

A B01 identificou **250 IDs fisicamente vazios entre 1 e 599**, sendo o maior bloco contínuo **442–599 (158 IDs)**. Para dimensionamento **apenas**, os 76 mapas da árvore Sinnoh caberiam numericamente em um segmento de 76 posições, por exemplo **442–517**.

**A faixa 442–517 não é uma proposta de alocação aprovada.** O [manifesto B03](../data/regions/sinnoh-b03-installer-evidence.json) registra `selected_as_destinations=false`, `future_claims_checked=false`, e `destination_mapping={}`. Nenhum MapID de fonte foi vinculado a algum destino, nenhuma colisão futura foi descartada e o plano não serve de entrada para instaladores.

Antes de qualquer mapeamento real, usar o [auditor de reservas R07](../scripts/regions/audit_sinnoh_r07_reservations.py), manifestos locais comprovados, [`plan_sinnoh_remap.py`](../scripts/regions/plan_sinnoh_remap.py) e o [reconciliador S07](../scripts/regions/sinnoh_s07_reconcile.py), sempre preservando os saves existentes e os destinos de outras regiões.

## 3. Tilesets e autotiles: renumerar sem sobrescrever

A fonte Sinnoh V18 possui dois IDs de tileset identificados no inventário: `1` e `31`. Na base Decades, esses números já existem com **nomes diferentes**:

| ID | Tileset no doador | Tileset na instalação |
|---|---|---|
| 1 | `OutsideWorld2.7` | `Outside stock` |
| 31 | `SinnohCompleteTileset` | `FRLG_Preview_Mart interior` |

A tabela nativa do snapshot B01 contém **70 entradas registradas**. Isso **não autoriza escolher 70 ou 71** como novos índices: a tabela pode mudar com outros instaladores, pode ter entradas vazias e as imagens precisam de direitos e caminhos verificados.

O padrão auditado é o mesmo usado no código já existente:

1. Ler os tilesets RMXP originais e a tabela nativa **atual**, em cópia privada e read-only.
2. Para cada tileset efetivamente referenciado pelos mapas Sinnoh autorizados, conferir o nome da imagem e **todos os autotiles** existentes e permitidos.
3. Na montagem de uma cópia de testes isolada, **acrescentar novas entradas** ao final da tabela nativa vigente, sem alterar seus índices e metadados anteriores; registrar correspondência origem → novo índice.
4. Reescrever `@tileset_id` dos mapas **somente nessa cópia** para seus novos índices, preservando passagem, prioridade e tags de terreno que forem suportadas.
5. Aplicar verificações de hashes e transação com rollback; não trazer eventos, scripts ou músicas do doador e não copiar imagens sem autorização.

Referências de implementação: [`johto_main_preview.py`](../scripts/regions/johto_main_preview.py), [`pilot_hoenn.py`](../scripts/regions/pilot_hoenn.py) e o [conversor seguro de geometria Sinnoh](../scripts/regions/convert_sinnoh_geometry.py). O B03 só **audita o contrato de código**; não executou essa transformação com a fonte original.

## 4. Modelo dos três manifestos R07

O arquivo [`sinnoh-b03-reservation-review-templates.json`](../data/regions/sinnoh-b03-reservation-review-templates.json) inclui modelos separados de **KANTO**, **JOHTO** e **HOENN** com hash do `MapInfos` real enviado no B01. De propósito, todos têm `future_reserved_map_ids=[]`, `ownership_evidence=""` e `reviewed_locally=false`.

**Esses modelos não são aceitos como prova R07.** É preciso localizar a relação verdadeira dos MapIDs de conteúdo ainda não instalado, registrar origem auditável e revisar a cópia local. O vazio nos modelos significa **desconhecido**, nunca **sem reservas**. Não forçar `reviewed_locally=true` apenas para ultrapassar a checagem.

Para reproduzir o diagnóstico no repositório:

```bash
python scripts/regions/audit_sinnoh_b03_installer_evidence.py
python -m unittest discover -s tests -p "test_sinnoh_b03_installer_evidence.py" -v
```

O [auditor B03](../scripts/regions/audit_sinnoh_b03_installer_evidence.py) verifica os quatro códigos-fonte, recusa adulteração das evidências e bloqueia aprovação implícita. Foram acrescentados **20 testes** negativos e de consistência à suíte offline. Ele não lê nem modifica `game/Data` e não exige novo arquivo do usuário agora.

## 5. Resultado e dependências para B04

**B03 concluída como auditoria de engenharia offline**, não como fase tecnicamente aprovada: A **32/32**, B **0/13**, C **0/13**, D **0/13**. R07 ainda exige os manifestos reais revisados; R08 exige recursos Sinnoh com permissão de uso e conversão isolada; R09 depende de Game.exe/JoiPlay. **O status da região continua `planned`.**

A próxima etapa B04 pode preparar um **coletor local de manifestos/proveniência das instalações regionais**, reduzindo a necessidade de copiar manualmente dados do Windows, com controle para não enviar saves nem conteúdo gráfico de terceiros.