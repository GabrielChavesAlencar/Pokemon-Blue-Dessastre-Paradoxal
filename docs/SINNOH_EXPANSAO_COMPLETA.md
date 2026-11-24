# Sinnoh completa — expansão F01–F15

Referência Platinum. Progresso de preparação (não aprovação nativa):

- Rotas: **2/30**, Rota 201 e 202.
- Cidades: **2/14**, Twinleaf e Sandgem.
- Piloto privado: **10 mapas preparados**.
- Fases novas: **0/15 concluídas**, F01 implementada em PR, aguarda CI.

## Progresso das cidades

| Cidade | Preparação |
|---|---|
| Twinleaf Town | Preparada |
| Sandgem Town | Preparada |
| Jubilife City | Pendente |
| Oreburgh City | Pendente |
| Floaroma Town | Pendente |
| Eterna City | Pendente |
| Hearthome City | Pendente |
| Solaceon Town | Pendente |
| Veilstone City | Pendente |
| Pastoria City | Pendente |
| Celestic Town | Pendente |
| Canalave City | Pendente |
| Snowpoint City | Pendente |
| Sunyshore City | Pendente |

## Progresso das rotas

201 e 202 preparadas; 203–230 pendentes. Fight, Survival e Resort Area são contadas separadamente das 14 cidades.

## Fases

- [ ] F01 — Menu de teleporte QA no menu de pausa (implementada, aguardando CI)
- [ ] F02 — Correção das bordas pretas com árvores
- [ ] F03 — Inventário completo dos mapas, sprites e MapIDs
- [ ] F04 — Importação de todas as cidades e vilarejos
- [ ] F05 — Importação de todas as rotas 201–230
- [ ] F06 — Importação de florestas, lagos e cavernas
- [ ] F07 — Importação dos interiores e edifícios
- [ ] F08 — Conexões entre mapas e colisões
- [ ] F09 — Pokémon selvagens de todas as áreas
- [ ] F10 — Todos os treinadores e NPCs
- [ ] F11 — Oito ginásios e insígnias
- [ ] F12 — História, Equipe Galactic e itens-chave
- [ ] F13 — Victory Road, Elite Four e Cynthia
- [ ] F14 — Battle Frontier, lendários e pós-jogo
- [ ] F15 — Testes de regressão, saves, Windows e Android

## F01 — teleporte

No menu de pausa da cópia privada com mapas originais, a opção Teleportar - Sinnoh QA permite escolher uma categoria ou buscar nome/número. O catálogo de 133 áreas/destinos simbólicos inclui as 30 rotas e as 14 cidades, além de áreas de história e pós-jogo. O inventário físico de submapas e andares será feito em F03; não se afirma que todos estejam catalogados individualmente ou instalados. Somente mapas efetivamente preparados e com ponto de chegada calculado a partir do RXDATA podem receber transferência. Não há ID fictício para destinos pendentes. O menu exibe contagens reais por categoria, incluindo rotas e cidades. A transferência não concede insígnias, itens nem progresso; os cinco autoruns conhecidos são suprimidos transitoriamente na chegada QA, e interações explícitas permanecem disponíveis. Ao sair normalmente do mapa, o comportamento normal retorna. O save não é lido nem alterado pelo instalador. A validação nativa continua pendente; a barra preta será tratada em F02.

Catálogo: [destinos](../data/regions/sinnoh-expansion-destinations.json). Progresso: [JSON](../data/regions/sinnoh-expansion-progress.json).
