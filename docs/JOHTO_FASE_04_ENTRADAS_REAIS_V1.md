# Johto — Fase 04: entradas reais de New Bark e conexão correta com Rota 29

**Data:** 13/11/2026 · **Escopo:** começar a construir a primeira fase jogável (04/16; 1/13 no contador de conteúdo).  
**Estado:** auditoria do terreno real e correção da fronteira concluídas no código; **nenhum Game.exe com Johto iniciado e validado**. Barras continuam **0/13 jogáveis** e **0/13 testadas no jogo**.

## Evidência extraída do ZIP v1 recebido

- Arquivo `Remastered Kanto Johto Map Packv1.zip`, SHA-256 `5d5697e9c3bf5db6ca7039d4af65697dd8b231f4b1305f14731e35ac324b6715`.
- New Bark: `Map079.rxdata`, SHA-256 `e5ffa3a8831101eca319b2567ebc3f6cff22ac673072776a31bf69fceaefc9c9`.
- Dimensões verificadas: **22 × 48 tiles**, três camadas, tileset de origem **23**. `Tilesets.rxdata` SHA-256 `45a7b0b7af849fdc07a7984d702a0eebeb52c4faf7a759166b6afb7b23ff4afd`.
- `Map079` não contém eventos RMXP. O ZIP não fornece os interiores da casa ou laboratório.
- Registro estruturado: [johto-new-bark-exterior-v1.json](../data/regions/johto-new-bark-exterior-v1.json). **São candidatos visuais de fachada, não posições aprovadas de warp.**

### Fachadas localizadas na imagem real do Map079

| Área candidata | Tile (x,y) | Calçada dois tiles abaixo | Papel no piloto |
|---|---:|---:|---|
| Edifício grande noroeste | **(5,21)** | (5,23) | Laboratório de Elm — provável, revisar |
| Casa nordeste | **(14,23)** | (14,25) | Casa de NPC/jogador — indefinido |
| Casa sudoeste | **(4,31)** | (4,33) | Casa de NPC/jogador — indefinido |
| Casa sudeste | **(13,33)** | (13,35) | Candidata à casa do jogador, revisar |

As coordenadas foram obtidas da **Table RMXP real**, conferidas contra tiles nas camadas 0/1/2 e flags de passagem; `@passages` não substitui a lógica de colisão do Pokémon Essentials, então cada entrada segue com `verified_position=false`. Não identificar automaticamente a casa do jogador com base apenas na cor do telhado.

**Auditar com o ZIP real, mesmo sem game/:**

```bat
REM Colocar o ZIP original (mesmo hash) em .blue-work\johto-source\original.zip
JOHTO_AUDITAR_ENTRADAS_NEW_BARK.bat
REM Saida: .blue-work\johto-new-bark-exterior-audit.json
```

A ferramenta [audit_johto_new_bark_exterior.py](../scripts/regions/audit_johto_new_bark_exterior.py) verifica o SHA-256 do ZIP e dos arquivos Map079 e Tilesets, as dimensões, as Table 3D/1D, os IDs de cada fachada e os bits de passagem. Falha se os bytes mudarem ou se tentarem marcar a posição como previamente aprovada; nunca escreve em `game/`.

## Corrigida a viagem por fronteira entre New Bark e Route 29

No Map Pack v1, `PBS/map_connections.txt` define `79,West,13,104,East,0`. Essa é uma **conexão de borda de mapa**: não se deve também pôr dois eventos de teletransporte RMXP nas bordas.

Com `pilot_johto.py --with-connections`, o piloto experimental:

1. Remapeia `79` e `104` para os IDs reais livres da cópia Blue/Decades (600–999), usando o compilador seguro já existente.
2. Valida que a conexão original aparece no PBS compilado.
3. **Remove da cópia em memória** os dois eventos redundantes `JH_TOWN_TO_ROUTE29` e `JH_ROUTE29_TO_NEW_BARK` antes de compilar eventos. Mantém o JSON original intacto e preserva os NPCs da região.
4. Mescla o PBS com as conexões existentes somente na cópia experimental; guarda hash, não altera `game/`.
5. Continua com `gameplay_verified=false` até teste real em Game.exe.

**Atenção:** o pacote não inclui conexão Route 29 ↔ Cherrygrove no PBS, e ela ainda exige implementação e teste; ausência não é escondida.

## Critério para elevar a barra Fases Jogáveis de 0/13 a 1/13

- [x] Map079 real do exterior auditado, com quatro entradas candidatas e fonte protegida por SHA.
- [x] Conexão real de borda New Bark ↔ Route 29 convertida para PBS sem teletransporte duplicado em piloto isolado.
- [x] Scripts dos quatro NPCs/handlers do início já existem em [JohtoPilot.rb](../scripts/regions/JohtoPilot.rb), com testes sintéticos; não são eventos de jogo validados.
- [ ] Ter a instalação `game/` de Blue/Decades com `Data`, `Graphics` e `PBS` acessível para montar a cópia; **atualmente não fornecida**.
- [ ] Construir e conferir quarto 2F, casa 1F e laboratório com gráficos, colisões e portas utilizáveis.
- [ ] Confirmar visualmente qual casa pertence ao jogador e os pontos de entrada/retorno; revisar sprites reais.
- [ ] Compilar os eventos nas coordenadas auditadas, selecionar inicial, verificar rival/PBS e acessar a Rota 29.
- [ ] Executar a cópia experimental no `Game.exe` real, carregar/salvar sem afetar Kanto/Decades, confirmar início no quarto.

Somente após esse último conjunto o marco poderá ser **1/13 jogável**, ainda que o QA completo não tenha passado (barra testada poderia continuar 0/13). O GitHub não contém nem deve publicar automaticamente os mapas/tiles de terceiros ou saves.
