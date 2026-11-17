# Sinnoh B04 — coletor privado de proveniência de Kanto, Johto e Hoenn

**Status atualizado (17/11/2026):** ZIP gerado no Windows **recebido e confrontado com B01**; os três manifestos foram localizados, mas o coletor V1 omitiu 31 IDs menores que 100. Veja o [catálogo consolidado e a correção](MAPIDS_DECADES_SINNOH_UNOVA_2026-11-17.md). **A versão corrigida do coletor foi entregue nesta conversa**. Ainda não foram homologadas reservas futuras. A etapa é preparação de evidências, não integração de mapas, liberação de R07, ou aprovação de Game.exe/JoiPlay. **Barra B = 0/13, C = 0/13, D = 0/13.**

## Reexecução após a primeira correção (17/11/2026)

O usuário entregou `SINNOH_B04_PROVENIENCIA_REGIONAL(1).zip` (SHA `32b865890c7a85698afbc9e498483a4e2b2fff7a3ac092fc37ecfdbb0f571bc0`). **O JSON é idêntico ao do B04 anterior:** 617 mapas físicos, ainda faltando os 31 IDs menores que 100 na comparação com a B01. Os três manifestos regionais e hashes MapInfos/Tilesets não mudaram; nenhum dos 31 IDs foi liberado para Unova. Isso **não permite confirmar qual script foi executado**.

Foi disponibilizado no chat um novo `SINNOH_B04_COLETOR_V2_VALIDADO.zip`, com `COLETAR_B04_SINNOH_V2.cmd` e nome distinto de saída `SINNOH_B04_PROVENIENCIA_REGIONAL_V2.zip`. Essa V2 usa a mesma regra de reconhecimento de `MapNNN.rxdata` da B01, compara os 648 IDs com o snapshot B01 quando os hashes coincidem e recusa produzir arquivo incompleto. **Verificação estática feita; execução real no Windows ainda pendente.** [Recibo da reexecução](../data/regions/sinnoh-b04-rerun-receipt.json). A instrução abaixo descreve o primeiro pacote B04, mantida como histórico.

## Obter o ZIP B04 com apenas dois cliques

O pacote **`SINNOH_B04_COLETOR_MANIFESTOS.zip`**, entregue ao usuário nesta conversa, tem estes arquivos: `COLETAR_B04_SINNOH.cmd`, `coletar_b04_sinnoh.ps1`, `LEIA_ME.txt`.

1. Extrair os três arquivos para uma pasta de trabalho.
2. Executar `COLETAR_B04_SINNOH.cmd` por duplo clique. Ele chama o coletor PowerShell automaticamente, **sem abrir PowerShell manualmente e sem Python instalado**.
3. O coletor tenta `%LOCALAPPDATA%\PokemonBlueDessastreParadoxal\game\Data`; se necessário pede para selecionar `game\Data`.
4. O resultado aparece **ao lado do coletor**: `SINNOH_B04_PROVENIENCIA_REGIONAL.zip`.
5. Enviar **somente esse ZIP** na conversa.

A ferramenta não executa nenhum código do jogo nem faz upload automático. A leitura é local; grava o relatório somente no diretório extraído e arquivos temporários no TEMP, removidos após a geração.

**Observação de teste:** o coletor Windows foi conferido quanto à composição e estrutura do ZIP entregue, mas não foi executado no Windows neste ambiente. A execução real será confirmada pelo relatório devolvido pelo usuário.

## Conteúdo privado deliberadamente reduzido

O ZIP gerado contém somente `native_provenance.json` e `LEIA_ME.txt`. O JSON registra **apenas MapIDs numéricos, mapeamentos numéricos origem→destino, contagens, hashes SHA-256 e estados selecionados** dos manifestos:

| Região | Manifesto local examinado (se existir) | Informações extraídas |
|---|---|---|
| Kanto | `Data/blue-kanto-install.json` | `maps`, SHA, schema, contagem e IDs de destino |
| Johto | `Data/blue-johto-main-preview.json` | `map_ids`, status, SHA, contagem e IDs |
| Hoenn | `Data/blue-hoenn-install.json` | `maps`, status, SHA, contagem e IDs de destino |

Também registra os hashes de `MapInfos.rxdata` e `Tilesets.rxdata` (sem copiar esses arquivos) e os nomes numéricos de `MapNNN.rxdata` presentes em disco, para detectar se a instalação mudou desde o inventário B01.

**Nunca inclui:** saves, executáveis, sprites, música, conteúdo de mapas ou tilesets, caminhos absolutos, logs pessoais, chaves ou o conteúdo integral dos manifestos. Nenhum dado é enviado automaticamente.

**Limite importante:** o ZIP é um relatório **autodeclarado localmente**, não uma prova criptográfica independente da autenticidade dos manifestos. Os SHA informados não substituem a verificação local dos arquivos originais se houver discrepância ou necessidade de homologação.

## Auditor B04 no repositório

[Contrato](../data/regions/sinnoh-b04-collector-contract.json), [auditor](../scripts/regions/audit_sinnoh_b04_provenance.py) e [22 testes](../tests/test_sinnoh_b04_provenance.py).

Sem ZIP: o comando informa `AWAITING_LOCAL_B04_ZIP` sem executar o jogo e com saída válida para o CI:

```bash
python scripts/regions/audit_sinnoh_b04_provenance.py
```

Com o ZIP enviado pelo usuário:

```bash
python scripts/regions/audit_sinnoh_b04_provenance.py --input SINNOH_B04_PROVENIENCIA_REGIONAL.zip
```

O auditor rejeita arquivos extras, subpastas, duplicações, links, erros de hash/formato, IDs inválidos, afirmações de revisão futura ou aprovação automática. Também sinaliza:

- **`BASELINE_CHANGED_REQUIRES_NEW_B01`** — os arquivos MapInfos/Tilesets mudaram desde o ZIP B01: atualizar o inventário e não reutilizar reservas antigas.
- **`PARTIAL_OR_INVALID_REGIONAL_PROVENANCE`** — faltam manifestos ou algum não segue o contrato esperado.
- **`INSTALLED_REGIONAL_ID_COLLISIONS_NEED_REVIEW`** — os MapIDs declarados como instalados se sobrepõem.
- **`THREE_INSTALLED_MANIFESTS_REPORTED_FUTURE_RESERVATIONS_STILL_UNKNOWN`** — os três manifestos parecem consistentes com seus esquemas, **mas as reservas futuras seguem desconhecidas**.

## O que B04 não pode afirmar

A B04 não verifica direitos de tilesets, não executa Game.exe/JoiPlay, não atribui IDs 442–517, não executa as importações e não aprova R07/R08/R09. Os manifestos de instalação de regiões existentes não substituem a [revisão de reservas futuras R07](SINNOH_R07_DIAGNOSTICO_RESERVAS.md), que exige evidências dos mapas ainda planejados e os respectivos IDs efetivamente reservados.

Quando o usuário enviar o ZIP, a próxima etapa será a **B05 — comparação dos três manifestos reais e planejamento de conflitos em cópia isolada**, sempre sem instalação ou atualização de saves antes da aprovação de evidências e recursos.
