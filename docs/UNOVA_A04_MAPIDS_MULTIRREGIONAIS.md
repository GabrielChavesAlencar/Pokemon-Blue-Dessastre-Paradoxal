# Unova A04 — auditoria de MapInfos e MapIDs multirregionais

**Data:** 17/11/2026. **Projeto:** Pokémon Blue: Dessastre Paradoxal.

> **Estado real:** ferramenta implementada; a instalação nativa Decades não foi fornecida nem examinada neste ambiente. O piloto Unova continua planejado. Este documento não confirma MapIDs livres.

## Objetivo

O [auditor A04](../scripts/regions/audit_unova_a04_mapids.py) lê somente os dados de mapas das fontes locais explicitamente escolhidas: a pasta real **game/Data do Decades** ou seu ZIP de backup, e fontes opcionais de Kanto, Johto, Hoenn e Sinnoh como pasta Data ou ZIP. Os rótulos das regiões são **informados pelo operador, não são provas de propriedade dos mapas**.

**O que identifica:**
- MapIDs com arquivos MapNNN.rxdata existentes, SHA-256 e tamanho em bytes;
- MapIDs declarados no MapInfos.rxdata, com leitura inerte dos nomes de mapas (sem executar Ruby);
- Entradas de MapInfos sem arquivo e arquivos MapNNN sem entrada correspondente;
- Sobreposições de IDs entre fontes, separando bytes iguais de hashes diferentes (ambos exigem revisão);
- Quantos snapshots regionais estão ausentes e se a baseline real foi fornecida.

**O que NÃO faz:** declarar MapIDs livres, reservar ID de Unova, validar eventos de mapas, atribuir a autoria de um mapa a uma região, executar scripts Ruby, instalar ou extrair arquivos, alterar Game.exe, Blue-Story ou saves.

## Como utilizar no Windows sem PowerShell

1. Atualize o repositório para obter **[UNOVA_A04_AUDITAR_MAPIDS.bat](../UNOVA_A04_AUDITAR_MAPIDS.bat)**.
2. Identifique a pasta **game/Data da instalação real do Decades**, que contém MapInfos.rxdata e MapNNN.rxdata. O repositório do editor não substitui essa instalação.
3. Dê dois cliques no BAT: ele abrirá a janela para escolher a pasta Data/game da instalação real. Também é possível arrastar essa pasta sobre o BAT; nesse caso, audita a baseline diretamente.
4. O assistente perguntará se deseja comparar overlays separados de Kanto, Johto, Hoenn e Sinnoh, caso tenha cópias verdadeiras dos pilotos; escolha as pastas Data/game ou ZIPs pelas janelas. Não rotule a mesma instalação consolidada como quatro snapshots regionais distintos.
5. Consulte os relatórios JSON privados em **.blue-work/unova/audit/a04-mapids-HASH.json**, nomeados pelo hash da evidência, sem exportar MapInfos ou sprites.

Com o terminal CMD tradicional, o equivalente é:

    python scripts/regions/audit_unova_a04_mapids.py --base-data "C:\Jogo\game\Data" --overlay "KANTO=C:\Pilotos\Kanto\Data" --overlay "JOHTO=C:\Pilotos\Johto\Data" --overlay "HOENN=C:\Pilotos\Hoenn.zip" --overlay "SINNOH=C:\Pilotos\Sinnoh\Data" --write

## Interpretação

| Campo | Significado |
|---|---|
| observed_or_declared_occupied_map_ids | União de todos os IDs observados em MapNNN e declarados no MapInfos das fontes analisadas |
| sources.DECADES | Baseline do jogo e MapInfos nativo; o rótulo não garante autoria por região |
| sources.KANTO/JOHTO/HOENN/SINNOH | Fontes opcionais informadas pelo operador |
| missing_map_file_ids | IDs declarados no MapInfos mas ausentes como arquivo — **não são livres** |
| orphan_map_file_ids | Arquivos MapNNN não listados no MapInfos da mesma fonte |
| overlaps | MapIDs presentes em mais de uma fonte; SHA idêntico ainda exige revisão |
| region_overlay_snapshots_missing | Fontes de overlay que não foram fornecidas |
| available_map_ids_certified | Sempre null: nenhum ID livre foi certificado |
| can_reserve_mapids, can_install | Sempre false; diagnóstico não é alocação nem instalação |

**Observação:** uma instalação consolidada já pode conter Kanto, Johto, Hoenn e Sinnoh no mesmo MapInfos. O auditor registra a ocupação total desse conjunto, mas não infere qual região detém cada ID. Para isso precisaremos de histórico de manifests, reservas e arquivos de origem, além de revisão manual dos eventos e transferências.

## Proteções e critérios de aprovação

- Recusa symlinks, traversal, arquivos duplicados por caixa/zeros, ZIP criptografado ou suspeito de descompressão excessiva.
- Ruby Marshal é interpretado como dados inertes; não se executam scripts do Essentials ou do fornecedor.
- MapNNN é conferido pelo hash, não decodificado. Não declarar evento jogável com base em seu nome.
- Dados de auditoria ficam privados. Nenhum arquivo binário de terceiros é enviado ao GitHub.
- Se não houver baseline Decades verdadeira com MapInfos, o estado é **BLOCKED_NATIVE_DECADES_MAPINFOS_NOT_PROVIDED** e a Barra A não avança.
- **A04 só poderá ser marcada como concluída** após comparar o MapInfos real com os manifests de instalação/regiões, investigar faltas e colisões, confirmar outros usos de MapID nos scripts, salvar evidências e checar a integridade de backup/rollback.
- A05 (reserva de MapIDs) só pode começar depois de fontes reais de mapas e disponibilidade verificada; números simplesmente não vistos ainda podem estar referenciados em scripts.

## Progresso

**Barra A = 0/8, Barra E = 4/8, B/C/D = 0/8, campanha Unova jogável = 0/32.** São ferramentas de preparação, não mapas importados.

Referências internas: [Roteiro operacional SP05–U32](UNOVA_ROTEIRO_IMPLEMENTACAO_OPERACIONAL_SP05_U32.md), [Plano U01–U32](UNOVA_PLANO_IMPORTACAO_REGIAO_32_FASES.md), [auditor de RXDATA de Sinnoh](../scripts/regions/audit_sinnoh_rxdata.py).
