# Plano de desenvolvimento — Pokémon Blue: Dessastre Paradoxal

## Estado inicial (outubro de 2026)

- [x] Projeto local e editor próprio inicial (Python e navegador).
- [x] Estrutura para importar Pokémon Decades v3.0.8 (via clone local, sem redistribuição).
- [x] Interface para editar arquivos PBS por seções, com pesquisa e backups.
- [x] Inclusão de espécies, formas, golpes, habilidades e registros PBS (templates genéricos).
- [x] Execução do Game.exe via interface local.
- [x] Personalização local do título do jogo via Game.ini e mkxp.json (sem substituir logotipo).
- [ ] Criar repositório na conta GitHub por `PUBLICAR_GITHUB.bat`.
- [ ] Solicitar ao HazyCrazy autorização de uso/redistribuição do conteúdo original, se desejar publicar um fork integral.
- [ ] Confirmar o funcionamento real do Decades no computador do usuário e a recompilação dos PBS.

## Fase 1 — Fundamentos

1. Definir o enredo de Blue: Dessastre Paradoxal, mapa/região e progressão.
2. Definir o catálogo final de Fakémon, Paradoxos do passado/futuro, evoluções alternativas e Megas.
3. Criar biblioteca de IDs simbólicos estáveis para espécies/formas e convenções de nomes.
4. Validar compatibilidade de plugins do Decades com espécies novas e mecânicas de batalha; corrigir problemas específicos.
5. Montar primeira build de teste com 1 espécie nova, uma forma, 2 encontros e 1 treinador.
6. Automatizar compilação de PBS pelo modo debug e verificar que alterações efetivamente aparecem no jogo.

## Fase 2 — Blue Studio 1.0

1. Importação de arte normal/shiny, frente/trás/ícone; pixel-art e ajuste do pivô.
2. Editor avançado de Pokémon: base stats, abilities, learnsets, egg moves, TMs/tutor.
3. Formulário de encontros com pesos percentuais e separação dia/noite; validação do total de pesos.
4. Editor de equipes de treinadores com controle de levels, IV, EV, nature e itens.
5. Gerador de cópias de mod (somente arquivos originais/autorizados) e manifesto de mudanças.
6. Testes de integridade referencial: cada golpe, tipo, habilidade, espécie e item cadastrado.
7. Separação entre alterações locais e branch de desenvolvimento; revisão antes da publicação.

## Fase 3 — Criar a campanha

1. Novas rotas, cidades, tilesets e eventos pelo RPG Maker XP.
2. Novas telas: logotipo Blue, menu de início, Pokédex e identidade visual.
3. Eventos e missões de Pokémon Paradoxo; controle de spawns e encontros.
4. Testes de save/load, evolução, troca de forma, megaevolução e batalha em dupla.
5. Alpha local, beta fechado e decisões sobre distribuição pública após autorizações.

## Riscos conhecidos

- **Licença:** o upstream é público, mas não foi identificada uma licença geral. Não presumir direito de republicar.
- **Tamanho:** a base original é grande e pode exigir espaço/tempo significativos.
- **Dados PBS:** `PBS/pokemon.txt` e `PBS/trainers_battle_mode.txt` são grandes. O editor usa carregamento de lista por arquivo e salva apenas a seção modificada.
- **Engine:** salvamento de PBS em disco não implica recompilação automática do conteúdo que o Game.exe usa.
- **Conflitos:** scripts de plugins podem introduzir formatos particulares, exigindo ajustes no editor.
