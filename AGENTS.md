# Instruções do projeto

- Ao concluir e verificar alterações solicitadas pelo usuário, publique os commits na branch `main` de `GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal`. Esta é uma preferência explícita do usuário; não deixe trabalho concluído apenas na pasta local.
- Antes de publicar, confira a versão atual da main e preserve alterações remotas. Use avanço normal; não faça force push.
- Mantenha `game/`, saves, binários do jogo e backups locais fora do Git, conforme `.gitignore`. Publique os scripts próprios que reproduzem as alterações locais do jogo.
- Informe o commit publicado e o resultado das verificações. Se a publicação falhar, explique o bloqueio em vez de afirmar que o GitHub foi atualizado.

- Os sprites autorais de Dessastre Paradoxal podem ser publicados em `site/assets/`; o pacote contém apenas arte do autor normalizada, sem arquivos originais do fangame.

- Para tarefas de teste, aceitação ou correção de jogabilidade de Kanto, seguir `docs/KANTO_CODEX_TESTES_E2E.md` e `docs/KANTO_ETAPAS.md`. Testes estruturais/headless não comprovam gameplay E2E; sem sessão Windows gráfica ou Android disponível, registrar o bloqueio e não elevar a Barra 2 sem evidências reais.

- Para implementar trilhas de Kanto solicitadas por chat, seguir `docs/KANTO_PLANO_APLICAR_MUSICAS.md` por fases; conferir `data/kanto-music.json`, preservar IDs do piloto e preferências de Decades. Não confundir plano/publicação de MP3 com áudio aplicado/testado no `Game.exe`.
