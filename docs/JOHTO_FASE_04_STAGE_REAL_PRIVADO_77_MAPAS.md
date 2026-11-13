# Johto Fase 04 — geração offline real de uma prévia com 77 mapas (13/11/2026)

**Estado:** os dados privados `johto-pilot-inputs.zip` (Blue/Decades) e `Remastered Kanto Johto Map Packv1.zip` foram recebidos e auditados. Gerada e validada uma **prévia isolada** (compartilhada somente na conversa privada), mantendo a campanha principal intacta. **Não jogável.**

## Resultado comprovado

- **74 mapas de terreno reais** da fonte Johto Map IDs 79–152 remapeados para **600–673**.
- Três **rascunhos geométricos** de interiores MapIDs **674 (quarto 2F)**, **675 (casa 1F)** e **676 (laboratório)**. Os layouts temporários foram copiados dos mapas nativos Decades **84 (cabana), 79 (Centro Pokémon) e 80 (ginásio)**; esses ambientes **não são fiéis** aos de Johto e exigem reconstrução antes de aprovação. Os scripts e eventos originais foram removidos.
- **42 conexões PBS de borda** foram recompiladas usando os MapIDs novos; New Bark ↔ Rota 29 agora usa `600,West,13,625,East,0`. `JOHTO_ROUTE_29` é MapID **625**.
- Gerado um rascunho `johto-new-bark-bound.json` com **cinco MapIDs e cinco SHA-256 reais de mapa**, além das 12 chaves de eventos. **Coordenadas, sprites e spawn permanecem sem aprovação**.
- Gerada lista preliminar com 14 posições de fachada, porta, escada, spawn e NPCs. Os 14 pontos não têm bloqueio nos bits direcionais da tabela estática de tiles, **mas não há qualquer prova de passabilidade do Game.exe**; `actual_engine_walk_verified=false` e `verified_position=false` foram preservados.
- Serialização RMXP reaberta em Ruby sem erro; conferidos **74 MapNNN** na primeira prévia, **77** na segunda, 3 tilesets doadores remapeados e 1 de interior; os **207 MapInfos** e **28 tilesets** nativos foram preservados, sem sobrescrita. Um autotile `R49Water` ausente foi limpo somente após verificar que seu slot não é usado pelos 74 mapas, de acordo com a auditoria anterior.
- A prévia não contém `Game.exe`, scripts não auditados, saves, músicas estrangeiras nem eventos doados. Os dados gráficos de terceiros foram disponibilizados apenas no ZIP privado, **nunca no GitHub**.

## Arquivos da prévia privada

```
.blue-work/
  johto-staging/
    Data/Map600.rxdata ... Map673.rxdata
    Data/MapInfos.rxdata
    Data/Tilesets.rxdata
    Graphics/Tilesets/
    Graphics/Autotiles/
    johto-stage.json
  johto-staging-interiors/
    Data/Map600.rxdata ... Map676.rxdata
    Data/MapInfos.rxdata
    Data/Tilesets.rxdata
    Graphics/...
    johto-stage.json
  johto-connections-preview.txt
  johto-new-bark-bound.json
  johto-coordinates-PROPOSAL-unverified.json
```

A prévia foi preparada no ambiente privado e entregue como ZIP ao proprietário. **Não extrair sobre `game/`**: sempre usar somente `.blue-work/`. Para validar com o código atual de Johto: `python scripts/regions/verify_johto.py --preview .blue-work/johto-staging --game game` e repetir com a prévia de interiores. A segunda prévia contém três templates não-fieis e não deve ser promovida a instalação da campanha.

## O que falta para o primeiro 1/13

1. **Refazer os três ambientes internos para HGSS** com os tilesets disponíveis, quarto → casa → laboratório, preservando os MapIDs e coordenadas aprovadas.
2. Auditar os warps bidirecionais com passagem; os pontos do relatório são sugestões, não verificações.
3. Integrar mãe, Elm, três Poké Bolas físicas para escolha do inicial, Silver e a batalha no PBS compilado.
4. Montar o piloto `Game.exe` isolado, com plugins e perfil de save separado. O exportador do usuário não inclui executável/plugins; não foi possível executar a engine nesta sessão.
5. Testar a progressão, entrada/saída de New Bark e Rota 29, combate, save/reload, regressões Decades/Kanto. Somente então **1/13 jogável**; depois do QA, **1/13 testada**.

**Progresso auditável:** terreno e staging **construídos**; interiores **provisórios**; código de eventos **não integrado**; `JOGÁVEIS 0/13`, `TESTADAS 0/13`.

**Direitos:** não versionar, distribuir ou anexar esses RXDATA/tilesets/PNG de terceiros ao GitHub sem autorização.