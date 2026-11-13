# Johto — Etapa 16/16: integração final, viagem e aceite

**Estado: PARCIAL — infraestrutura de segurança e testes publicada; instalação e gameplay bloqueados pela ausência da fonte verificada e da integração real.**  
**Data:** 13/11/2026 · [Acompanhamento](JOHTO_ETAPAS.md) · [Plano de 16 fases](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) · [Testes ponta a ponta](JOHTO_TESTES_E2E.md)

## Implementado nesta etapa

| Arquivo | Entrega |
|---|---|
| [scripts/regions/install_johto.py](../scripts/regions/install_johto.py) | Auditor completo da Etapa 16, com matriz das 16 fases, blockers por fonte/MapIDs/PBS/áudio/game/piloto, `--dry-run` padrão, `--strict`, relatório opcional sob `.blue-work`, **`--apply` bloqueado** |
| [scripts/battle_polish/RegionStart.rb](../scripts/battle_polish/RegionStart.rb) | Prova legível de instalação Johto, 13 checks, hash SHA-256 dos arquivos essenciais e coordenadas independentes de casa de New Bark, chegada de viagem e NPC |
| [scripts/battle_polish/RegionTravel.rb](../scripts/battle_polish/RegionTravel.rb) | Viagem Kanto↔Johto condicionada a fonte real e estado regional, NPC em memória na cidade inicial **depois** da Liga, reaproveitando reserva de Box, rollback e save único |
| [data/regions/johto-release-proof.schema.json](../data/regions/johto-release-proof.schema.json) | Contrato explícito do que o futuro instalador **deve** comprovar antes de marcar `VERIFIED_PLAYABLE`, sem escrever marcadores falsos |
| [tests/region_start_runtime.rb](../tests/region_start_runtime.rb) | Impede que `{ }` ou arquivo de start isolado ative Johto; recusa manifesto com PBS não verificado ou hashes adulterados |
| [tests/region_travel_runtime.rb](../tests/region_travel_runtime.rb) | Simula Kanto↔Johto, destino auditado, origem bloqueada antes da Liga, perda de prova, rollback pós-falha, PC e saves |
| [tests/test_johto_phase13_contract.py](../tests/test_johto_phase13_contract.py) | Atualiza contrato da Liga ao suporte opcional de transporte da fase 16, condicionado à instalação |
| [tests/test_johto_phase16_release.py](../tests/test_johto_phase16_release.py) | Testa auditor, código de retorno, impossibilidade de `--apply`, relatório isolado, proofs e preservação de dados das fases anteriores |
| [docs/JOHTO_TESTES_E2E.md](JOHTO_TESTES_E2E.md) | Matriz real de E2E, planos de backup/rollback e comandos seguros |

## Como o novo início de Johto está protegido

`BlueRegionStart.johto_spawn` requer simultaneamente:

1. `Data/blue-johto-start.txt` no formato `BLUE_JOHTO_START_V1,JOHTO,map,x,y`.
2. `Data/blue-johto-install.json` com `schema:1`, `region:"JOHTO"`, `status:"VERIFIED_PLAYABLE"` e hash SHA-256 de origem válida.
3. **13 critérios de aceite** todos verdadeiros: origem/licenças, mapa/warps, artes, eventos, PBS, batalhas/encontros, saves reais, HMs, transporte/Box, áudio, regressão Kanto/Decades, Windows e JoiPlay.
4. Dois MapIDs de Johto dentro do espaço reservado **600–999**, além da posição validada do NPC no mesmo mapa da chegada (mas não na mesma coordenada do jogador).
5. Hash correto dos arquivos `Data/MapInfos.rxdata`, `Data/Tilesets.rxdata`, mapa de início e mapa do agente. Mudanças posteriores nesses arquivos invalidam a liberação até nova auditoria.

**O manifesto não foi criado** no jogo; este documento não é um certificado de QA. Os 13 booleans só podem ser preenchidos a partir de evidências de execução real, não dos testes sintéticos. A prova é uma barreira preventiva para não habilitar por acidente: não substitui revisão independente, nem é uma assinatura criptográfica.

## Como a viagem entre regiões fica preparada

- **Kanto → Johto:** disponível apenas se Johto estiver logicamente desbloqueada pela Liga de Kanto e se a instalação Johto passar a verificação de arquivos e spawn. O destino é a **rua de New Bark** indicada por `travel_point`, nunca o quarto do jogador.
- **Johto → Kanto:** disponível apenas depois do **Hall of Fame real de Johto** registrado em `state["leagues"]` e com prova de Johto e instalação Kanto válidas. O jogador utiliza o agente de New Bark e a cidade de Pallet como destino Kanto.
- **Johto → Hoenn:** segue **sem destino**, embora a Liga Johto possa desbloquear Hoenn no save. Não teleportar para mapa inexistente.
- **New Bark NPC:** criação em memória **somente** se o mapa, a coordenada, os eventos do motor, a origem JOHTO e o Hall of Fame estiverem válidos. Nenhum evento é adicionado ao `MapXXX.rxdata` original.
- **Equipe e Box:** a rotina de viagem já reserva slots reais antes de remover especiais da party, impede viagem que deixe o jogador sem Pokémon utilizável e restaura equipe, PC, estado e posição quando o warp falha. Tests Ruby validam essa lógica de maneira sintética. A instalação nativa deve reconfirmá-la em Windows/JoiPlay, em particular a persistência após save/reload.

**Não confundir:** `BlueRegions.unlocked` controla desbloqueio do circuito, enquanto `BlueRegionTravel.destination` só retorna pontos existentes em mapas realmente instalados.

## Resultado do dry-run nesta etapa

O projeto ainda registra:

- `data/regions/johto-source.json`: **hash original ausente**, `mapping_verified:false`, `import_enabled:false`, `maps:{}`, licença/distribuição não confirmadas.
- Fases 05–14: manifestos e eventos de lógica **parciais**, sem mapas físicos, PBS nem aceite de gameplay.
- Fase 15: catálogo de **53 cues sem áudio licenciado** e prévia do site com **148 locais simbólicos/36 tipos de treinadores**, com zero mapas ou equipes realmente instalados.
- Piloto: **sem manifesto verificável de uma campanha jogável**. `stage_johto.py` só prepara prévia de terreno e `verify_johto.py` não autoriza uso como Game.exe.
- Mapas/teses do jogo nativo: não incluídos no Git em `game/`; o auditor reporta a ausência da instalação local em vez de inventar verificação.

Consequentemente: **`--apply` nunca escreve em `game/`**, o aceite técnico final continua **0/16** e o gameplay final continua **0/16**. As 16 fases foram iniciadas, mas nenhum núcleo pode ser classificado como integralmente aprovado apenas por testes de contratos.

## Próximas ações reais para concluir Johto

1. Obter **o ZIP/RMXP verdadeiro** do Map Pack e verificar direitos e SHA-256. A extração segura existente funciona com `prepare_johto_source.py`.
2. Executar auditoria/planejamento/staging isolado com `audit_johto.py`, `plan_johto.py`, `stage_johto.py` e `verify_johto.py`.
3. Criar os interiores faltantes — sobretudo **casa de New Bark**, laboratório de Elm e **Mt. Silver** — e integrar todos os eventos, puzzles, treinadores PBS, encontros selvagens, líderes, Liga, Hall of Fame, lendários e sons autorizados.
4. Construir **instalador transacional real** (não presente nesta etapa) que execute os planos aprovados em cópia de `game/`, crie backups e valide rollback antes de permitir escrita na instalação principal. Jamais copiar Scripts.rxdata estrangeiro ou sobrescrever um MapID Kanto/Decades.
5. Executar os testes **E2E no motor** conforme [JOHTO_TESTES_E2E.md](JOHTO_TESTES_E2E.md), verificando Windows/JoiPlay, save/reload, duas páginas de treinador, níveis Master Mode, Box e ausência de regressões.
6. Só depois de comprovar o estado verdadeiro, emitir `Data/blue-johto-install.json` conforme o schema e `Data/blue-johto-start.txt`. Atualizar catálogo, deploy e barras de progresso com os testes registrados.

**Observação sobre Kanto:** a verificação nativa de Kanto já apresentou falhas de infraestrutura/prova em execuções recentes; Johto não deve neutralizar os controles ou desligar essa CI para ser aceita.
