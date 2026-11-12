# Kanto — Fase 08/16: Vermilion, S.S. Anne e Lt. Surge

**Data:** 12/11/2026. **Estado:** expansão experimental publicada e testada na engine pelo GitHub Actions, porém ainda **não aceita manualmente**.

**Desenvolvimento:** 8/16 (50%). **Etapas completamente concluídas:** 1/16 (6,25%), 15 aguardando testes e aceite.

## Implementado

- O catálogo regional foi ampliado de 25 para **40 mapas**: Rota 5, passagem subterrânea, Rota 6, Vermilion City, Centro Pokémon, Poké Mart, ginásio, porto e áreas do S.S. Anne (1F, 2F, cabine do capitão, B1F e convés).
- IDs de todos os mapas anteriores preservados; a fonte FRLG é usada somente após validação de SHA-256 e não é redistribuída pelo GitHub.
- **54 treinadores** agora publicados no guia do portal, incluindo 26 perfis novos das rotas, navio e ginásio.
- Lt. Surge usa a equipe auditada **Voltorb nível 21, Pikachu nível 18, Raichu nível 24**. A vitória concede a insígnia Thunder uma única vez, junto às outras duas conquistas locais.
- Enigma elétrico: 15 lixeiras e 10 travas, resposta consecutiva entre lixeiras vizinhas, reinício após erro; Surge só pode ser desafiado após resolver o enigma.
- Ticket para o S.S. Anne: desbloqueio regional temporário condicionado à Cascade Badge; registra-se no save experimental mesmo se o item original FRLG não existir na base Decades. Sem esse desbloqueio, o porto bloqueia a passagem.
- Capitão do navio: evento adaptado para entregar HM Cut uma única vez se existir um item compatível no catálogo instalado. Sem esse item, o evento indica a pendência.
- **17 destinos de teletransporte exclusivos da cópia experimental**, acessível pelo terceiro comando Testar Kanto no Game.exe principal; os saves de Decades não são substituídos.

## Evidências verificadas

- [CI Windows fase 08: execução 43198430978](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43198430978): geração e importação de mapas em cópia descartável, checagem de topologia bidirecional, compilação na engine, eventos e treinamento, quebra-cabeça, Thunder Badge e persistência no save.
- [Site: guia de Kanto](../site/public/data/kanto.json) com 40 localidades e 54 treinadores auditados.
- [Guia manual de teste](KANTO_TESTE_EXPERIMENTAL.md) para testar a expansão no Windows.
- As batalhas do teste automático tiveram resultados simulados; uma aprovação de CI **não comprova** caminhada, colisões ou combate real com um jogador.

## Pendências

- [ ] Jogar manualmente do trecho Cerulean até Vermilion, testando todas as portas, passagens e transições.
- [ ] Testar batalha real dos treinadores, Lt. Surge, trancas, captura, derrota e save/reload no Windows.
- [ ] Implementar a cena canônica de Bill, o rival a bordo e a partida do S.S. Anne; a permissão de embarque atual é uma ponte experimental e não equivale à história original completa.
- [ ] Validar entrega e uso do HM Cut, Fly após Thunder e compatibilidade do catálogo de itens da instalação.
- [ ] Confirmar migração segura de instalações principais com 25 mapas (não foi executada atualização destrutiva automática).
- [ ] Validar por gameplay o comportamento no JoiPlay e preservar os saves legados.
- [ ] Ajustar retrato específico de Surge; no protótipo utiliza retrato provisório da classe Engineer.

**Próximo desenvolvimento:** 09/16 — Celadon e Erika, mantendo a etapa 08 aberta para aceite manual.
