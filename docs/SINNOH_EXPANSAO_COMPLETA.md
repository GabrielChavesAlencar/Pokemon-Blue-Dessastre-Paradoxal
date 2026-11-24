# Sinnoh completa — expansão F01–F15

Referência Platinum. Progresso de preparação (não aprovação nativa):

- Rotas: **2/30**, Rota 201 e 202.
- Cidades: **2/14**, Twinleaf e Sandgem.
- Piloto privado: **10 mapas preparados**.
- Fases novas: **1/15 concluída**, F01 integrada no PR #279 (11/11); F02 implementada, aguarda CI.

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

- [x] F01 — Menu de teleporte QA no menu de pausa (PR #279, 11/11)
- [ ] F02 — Correção das bordas pretas com árvores (implementada, aguardando CI)
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

No menu de pausa da cópia privada com mapas originais, a opção Teleportar - Sinnoh QA permite escolher uma categoria ou buscar nome/número. O catálogo de 133 áreas/destinos simbólicos inclui as 30 rotas e as 14 cidades, além de áreas de história e pós-jogo. O inventário físico de submapas e andares será feito em F03; não se afirma que todos estejam catalogados individualmente ou instalados. Somente mapas efetivamente preparados e com ponto de chegada calculado a partir do RXDATA podem receber transferência. Não há ID fictício para destinos pendentes. O menu exibe contagens reais por categoria, incluindo rotas e cidades. A transferência não concede insígnias, itens nem progresso; os cinco autoruns conhecidos são suprimidos transitoriamente na chegada QA, e interações explícitas permanecem disponíveis. Ao sair normalmente do mapa, o comportamento normal retorna. O save não é lido nem alterado pelo instalador. A validação nativa continua pendente; a barra preta é tratada na F02.

Catálogo: [destinos](../data/regions/sinnoh-expansion-destinations.json). Progresso: [JSON](../data/regions/sinnoh-expansion-progress.json).


## F02 — continuidade visual das bordas

Escopo: seis exteriores reais do piloto privado (Twinleaf, Route 201, Sandgem, Route 202, Verity Lakefront e Lake Verity). O renderizador nativo resolve a geometria de todos os mapas carregados, incluindo vizinhos conectados. Após a renderização, o complemento preenche somente células com as três camadas vazias (tile_id < 48), atrás de qualquer tile ou sprite de jogo. Não muda o tamanho dos mapas, coordenadas, eventos, colisões, PBS, MapInfos, conexões ou namespace de save. Usa a posição subpixel e a tonalidade do renderizador; oculta os sprites em interiores e outras regiões, e descarta recursos ao destruir o renderizador.

A textura opaca de 64x64 é gerada exclusivamente na instalação privada: prioriza amostra repetida de tiles bloqueados, verdes e opacos da borda da fonte original já verificada; caso não exista amostra adequada, usa árvores autorais do piloto. A escolha heurística de arte não equivale à avaliação visual nativa. Não publica os gráficos importados no GitHub. O relatório indica a origem escolhida e os seis MapIDs.

CI: teste Ruby simulado de célula vazia, vizinho carregado, tile transparente mas válido, posição subpixel, tom, escopo e descarte; teste com os ZIPs originais compara mapas, máscaras de colisão, 35 eventos e dez pontos QA sem alterações, e valida a opacidade da textura. Ainda não há aprovação visual em Game.exe nem garantia de aparência idêntica às árvores originais em cada borda. Testar andando até as bordas em todos os seis exteriores, inclusive nas conexões e após teleporte, de dia e de noite. F03 continua pendente.
