# S25 — Interface BlueMusic para Sinnoh (26ª entrega, offline)

**Escopo exclusivamente de código e testes.** Nenhum áudio instalado, tocado ou licenciado; não é certificação de Game.exe/JoiPlay.

## Realizado

- [Bridge Ruby](../scripts/music/SinnohBlueMusicBridge.rb) consulta a API verdadeira `BlueMusic.entry` e respeita música explícita da engine, `mute`, `custom`, `random`, mapas e tipos de batalha, sem substituir hooks globais.
- [Manifesto S25](../data/regions/sinnoh-music-s25.json) mantém registries de músicas autorizadas, MapIDs, eventos e bindings **vazios**, playback e instalação desabilitados.
- [Auditoria](../scripts/music/audit_sinnoh_music_s25.py) reutiliza as validações CH16/S24. [21 testes Python](../tests/test_sinnoh_s25_music.py) e [runtime Ruby com BlueMusic real e fixtures sintéticas](../tests/sinnoh_s25_music_runtime.rb) protegem contra licença/arquivo/callback inventados, músicas entre regiões e desrespeito às preferências manuais.
- CH19/S30 ampliados para executar e exigir a bridge, sem modificar `scripts/music/BlueMusic.rb`.

## Bloqueios restantes

Nenhum plugin/hook nativo foi registrado. A ativação de músicas reais exige arquivo com direitos de uso e redistribuição, créditos, hash SHA-256 auditado, vínculo de MapIDs/eventos compilados, teste sonoro de fade/loop e regressão Windows/JoiPlay. A bridge publicada é uma interface preparatória, **não integração sonora instalada**.

**Após CI e merge:** Barra A **26/32 (81%)**, quatro parciais e duas pendentes; Barra E **20/20**, barras técnicas/jogáveis B/C/D **0/13**; **44 casos nativos pendentes**.
