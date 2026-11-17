# Sinnoh S26 — regressões de fallback, prioridade, fade e loop

**Conclusão de desenvolvimento em código/testes, não certificação de áudio instalado.**

## Entregas

- [`tests/sinnoh_s26_music_regression.rb`](../tests/sinnoh_s26_music_regression.rb) carrega o **BlueMusic real**, o adaptador inerte [`SinnohMusicContracts.rb`](../scripts/music/SinnohMusicContracts.rb) e os **46 cues históricos** de [CH16](../data/regions/sinnoh-music-ch16.json).
- Exercita os 46 cues contra dez regiões externas, preservando a música de Decades, Kanto, Johto, Hoenn, Unova etc.; proíbe qualquer faixa/MapID/ME/PBS fictício.
- Confere precedência: evento explícito da engine supera BlueMusic personalizado; as opções manuais (inclusive **mute** de ginásio) prevalecem sobre as sugestões de Sinnoh. Nomes e IDs de mapas ainda não verificados nunca ativam áudio.
- Confere **11 cenários de transição**: fim de batalha, retorno de ME, troca de mapa, troca de região, evento novo, repetição da mesma faixa e restauração somente quando o mesmo dono ainda controla o som.
- Testa **sem áudio real**: fade e loop não recebem duração/pontos fabricados, arquivos sem licença ou hashes falsos não passam no catálogo, e nenhum hook é instalado.
- A suíte isolada [CH19](../scripts/regions/sinnoh_ci_ch19.py) executa o teste `sinnoh-music-s26` em Ruby. A matriz [S30](../scripts/regions/audit_sinnoh_s30_suite.py) impede a ausência do arquivo/runner.

## Aceite e limites

A S26 pode ser marcada **`done` em código** depois de validar o Ruby, o portal e a matriz S30 no CI e integrar o PR à `main`. O progresso esperado é **Barra A 17/32 (53%)**, cinco tarefas parciais e dez pendentes. E **20/20**; B/C/D **0/13**.

**Não foi testado**: arquivo licenciado real, loop em milissegundos reproduzido na engine, prioridade de eventos compilados em Game.exe ou volume/fade audível no Windows/Android. A S24 (licença/áudio) permanece parcial e a S25 (instalação efetiva em BlueMusic) permanece pendente. Nenhum asset musical novo é incluído.
