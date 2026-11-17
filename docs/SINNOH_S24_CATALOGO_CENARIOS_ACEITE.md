# Sinnoh S24 — catálogo musical por cenário (escopo offline)

**25ª entrega da Barra A, sujeita ao CI e merge na main.** Esta entrega organiza metadados e testes; **não instala músicas nem torna Sinnoh jogável**.

## Implementação

- [Matriz S24](../data/regions/sinnoh-music-s24.json) cobre todos os 46 cues CH16, com **14 cidades, 6 rotas, 7 ambientes/cavernas, 4 cenas, 10 batalhas, 1 transporte Surf, 1 pós-jogo e 3 ME**. Há 43 BGM, 3 ME e 45 chaves históricas únicas (Hall of Fame compartilha fonte, mas separa BGM/ME).
- Cada cenário tem contexto, prioridade, janela temporal, guarda de autorização, fallback e campos para futuramente auditar autor, licença, procedência e redistribuição. **Não existem fontes licenciadas verificadas**; por isso todos os créditos e caminhos são `null`.
- [Auditor S24](../scripts/music/audit_sinnoh_music_s24.py) valida a matriz contra a auditoria [CH16](../scripts/music/audit_sinnoh_music_ch16.py); [19 testes positivos/negativos](../tests/test_sinnoh_s24_music.py) bloqueiam cues removidos/trocados, MapIDs fictícios, permissões falsas, caminhos e hashes inventados e flags nativas.
- [CH19](../scripts/regions/sinnoh_ci_ch19.py) e [S30](../scripts/regions/audit_sinnoh_s30_suite.py) incorporam as verificações offline.

## Separação de escopos

**S24 `done` refere-se exclusivamente à catalogação por cenário. S25 permanece `pending`** até que existam arquivos de áudio com licença e consentimento de redistribuição, atribuição, hashes e vínculo nativo aprovados, além de testes de reprodução/loop/fade no Game.exe/JoiPlay. A ausência de licença não será ocultada nem convertida em suposta gravação utilizável.

O `BlueMusic.rb` compartilhado e o motor de outras regiões não foram modificados. Nenhum autoplay, hook, MapID, MP3, ME, PBS ou som foi instalado. **Barra A 25/32 (78%) em código, 4 parciais, 3 pendentes; E 20/20; B/C/D 0/13; 44 verificações nativas pendentes.**

## Aceite

Concluir apenas depois dos workflows CH19 (Python/Ruby), S30 (5 jobs), Portal e CH20 estático aprovados e da integração do PR à `main`. Teste offline não prova audição no jogo.
