# Sinnoh completa — expansão F01–F15

Referência Platinum. Progresso de preparação (não aprovação nativa):

- Rotas: **30/30**, Rota 201–230 e seis segmentos adicionais.
- Cidades: **14/14**, todas preparadas na F04.
- Piloto privado: **91 mapas preparados**.
- Fases novas: **6/15 concluídas**, F01/F02/F04/F05/F06 integradas (11/11 cada), F03 integrada (9/9); F07 implementada, aguarda CI.

## Progresso das cidades

| Cidade | Preparação |
|---|---|
| Twinleaf Town | Preparada |
| Sandgem Town | Preparada |
| Jubilife City | Preparada |
| Oreburgh City | Preparada |
| Floaroma Town | Preparada |
| Eterna City | Preparada |
| Hearthome City | Preparada |
| Solaceon Town | Preparada |
| Veilstone City | Preparada |
| Pastoria City | Preparada |
| Celestic Town | Preparada |
| Canalave City | Preparada |
| Snowpoint City | Preparada |
| Sunyshore City | Preparada |

## Progresso das rotas

201–230 preparadas; seis segmentos adicionais validados. Fight, Survival e Resort Area são contadas separadamente das 14 cidades.

## Fases

- [x] F01 — Menu de teleporte QA no menu de pausa (PR #279, 11/11)
- [x] F02 — Correção das bordas pretas com árvores (PR #280, 11/11)
- [x] F03 — Inventário completo dos mapas, sprites e MapIDs (PR #281, 9/9)
- [x] F04 — Importação de todas as cidades e vilarejos (PR #282, 11/11; 22 mapas preparados)
- [x] F05 — Importação de todas as rotas 201–230 (PR #283, 11/11; 56 mapas preparados)
- [x] F06 — Importação de florestas, lagos e cavernas (PR #284, 11/11; 91 mapas preparados)
- [ ] F07 — Importação dos interiores e edifícios (36 mapas candidatos, aguardando CI)
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

## F03 — inventário completo e preparação da F04

O auditor lê os dois ZIPs SHA-256 fixados pela F01/F02, sem extrair nem executar scripts do doador. Enumera todos os MapIDs físicos e indexados (inclusive submapas ainda não catalogados), nomes, dimensões, hierarquia, geometria não vazia, tilesets e tabelas, referências gráficas, eventos/transferências estáticas, PNGs do pacote de overworlds. A comparação com o catálogo de 133 destinos usa nomes normalizados e aliases explícitos; ausência de correspondência exata não prova ausência do mapa. Candidatos ambíguos, vazios, com referências inválidas ou faltantes precisam de revisão. O CI publica apenas recibo JSON de metadados e contagens, nunca os ZIPs, imagens, RXDATA ou scripts do doador. PNGs são checados por cabeçalho e dimensões, não por fidelidade visual.

F04: 14 cidades, duas já preparadas e 12 pendentes. O recibo identifica os candidatos por cidade. O auditor opcional de capacidade consulta MapInfos e arquivos Map*.rxdata da base local, preserva os dez IDs anteriores e verifica capacidade na faixa privada 442–517, sem reservar nem instalar. A faixa comporta no máximo 76 IDs, por isso toda Sinnoh pode exigir revisão de reservas futura; não reutilizar IDs de outras regiões. O snapshot histórico B01 de 648 IDs não prova disponibilidade atual. A F04 precisa de confirmação da geometria de cada cidade, gráficos/colisões, remapeamento, spawns seguros e política de compatibilidade dos saves ao ampliar a lista de IDs. Não importar eventos ou scripts externos. R07/R08/R09 e Game.exe continuam pendentes.

Execução local somente leitura (com os ZIPs já baixados):

```powershell
python scripts/regions/audit_sinnoh_expansion_f03.py --maps "Sinnoh Maps.zip" --overworlds "Ultimate Gen 4 Overworlds Pack.zip"
```

Opcionalmente informar --base game e --prior-manifest com o manifesto privado anterior. O relatório vai para stdout; nenhum save é lido ou alterado. Contagens físicas serão registradas somente após o recibo original do CI.

## F04 — 12 cidades adicionais

F03 confirmou 238 mapas de origem (224 não vazios e sem problemas geométricos detectados), 25 tilesets e 495 PNGs de overworlds. As 12 cidades adicionais são identificadas por MapInfo raiz, tileset 24, dimensões e SHA-256 fixados em data/regions/sinnoh-f04-city-sources.json. O instalador prepara 22 mapas somente na cópia privada, sem copiar eventos ou scripts externos. As cidades novas recebem atlases independentes para manter intactos os índices dos dez mapas anteriores; pontos seguros de chegada, máscaras de movimento e bordas F02 são derivados dos mapas reais. Os novos exteriores são acessíveis pelo menu de teleporte QA, sem conexões ou interiores novos nesta fase. BGM temporário de Sandgem até a fase de músicas/progressão. Os 35 eventos anteriores permanecem; NPCs e história das novas cidades não são implementados nesta fase.

A compatibilidade com saves antigos exige exatamente a mesma base MapInfos e os dez MapIDs anteriores intactos, além dos SHA-256 dos dez mapas gerados iguais ao manifesto anterior. O namespace é então reutilizado, sem abrir/copiar saves. Base ou mapas incompatíveis mantêm o perfil isolado anterior intacto; nenhuma migração forçada. A QA nativa, R07/R08/R09 e a validação visual continuam pendentes. O CI real deve demonstrar 14 cidades, 22 destinos, 18 exteriores e 35 eventos preservados antes de qualquer merge.

## F05 — rotas 201–230 e segmentos

F04 integrada no PR #282 (11/11). Marcador real: SINNOH_REAL_F04_14_CITIES_22_TELEPORTS_35_EVENTS_18_EXTERIORS_OK. A F05 acrescenta 34 mapas exteriores do tileset 24: 28 rotas restantes e seis mapas adicionais associados às rotas 205, 210, 212, 224, 225 e 228. Os IDs de origem, nomes, hierarquia, dimensões e hashes SHA-256 estão fixados no catálogo data/regions/sinnoh-f05-route-sources.json. A classificação dos mapas subordinados como segmentos QA não implica que sejam conexões naturais, nem que a variante 224 seja uma passagem adicional na história. Portarias e interiores permanecem em F07.

Meta: 56 mapas privados, 30 rotas principais, 36 destinos na categoria Rotas (incluindo seis entradas extras), 139 destinos de catálogo, 52 exteriores com proteção de bordas e 35 eventos antigos. Os 22 mapas e respectivos tilesets anteriores permanecem byte a byte; somente IDs livres de 442–517 podem ser usados. Não são adicionadas conexões, encontros, scripts ou eventos do doador. Música temporária de Sandgem para novas rotas. O filtro de chegada conserva terreno comum, passagem em todas as direções e dois vizinhos; se uma rota marítima ou qualquer outra não tiver ponto terrestre seguro, o CI bloqueia a importação até uma solução específica, nunca teleporta para água ou colisão. Saves reutilizam namespace somente se base, IDs e hashes anteriores coincidirem. Nenhum save pessoal aberto. Game.exe, R07/R08/R09 e aprovação visual nativa pendentes.


## F05 — aceite CI

PR #283 integrado em 09409e01dd89d57b74b334cb2826077791d5c3c0; 11/11 workflows e 26/26 checks. Marcador real SINNOH_REAL_F05_30_ROUTES_56_TELEPORTS_35_EVENTS_52_EXTERIORS_OK no job 138742746702. Fonte 165 (0,27), 142 (18,14), IDs da fixture não são reservas locais.

## F06 — áreas naturais privadas

35 mapas com dimensões, hierarquia e SHA-256 do inventário real F03 (job 138719583390). Meta 91 mapas, 64 exteriores, 35 eventos antigos, 56 mapas e teleportes anteriores imutáveis. Sem scripts ou eventos externos, sem conexões novas, sem afirmação de piso ou progressão para variantes. Classificação exterior/interior provisória, cavernas não recebem cobertura de árvores F02. MapIDs adicionais selecionados somente após leitura da ocupação local MapInfos, Data/Map*.rxdata e PBS; faixa 442–599 apenas na cópia QA isolada. 518–599 são candidatos históricos de Unova e NÃO são reservados para Sinnoh compartilhada. Se insuficiente, abortar; não usar 600+ nem mudar 56 IDs. Reutilizar namespace somente com hash de base, IDs e bytes anteriores iguais; não acessar saves. R07/R08/R09 e aprovação nativa continuam pendentes. Victory Road, ruínas lendárias e outras áreas de pós-jogo ficam para F13/F14.

### F06 — correção de chegada rochosa

O job 138748423718 confirmou novamente F05 e encontrou 21 interiores naturais sem componente de chegada de terreno 0. Todos os 21 contêm células transitáveis de terreno 4 (Rock). A exceção usa allowlist explícita desses símbolos, mantém todas as camadas desobstruídas, interior dos limites, componente conectado de pelo menos 12 células elegíveis e dois vizinhos elegíveis. Não inclui água, gelo (inclusive Snowpoint Temple), grama, terrenos especiais ou tiles bloqueados. Os outros 14 mapas e os 56 anteriores mantêm sua política de chegada. Nenhuma geometria, tabela de passagens ou tile do doador é alterado. A aprovação continua condicionada ao novo teste real.


## F06 — aceite CI

PR #284 integrado em b33d57d2ee199b404ad7e53424ee573b83d1bf56; 11/11 workflows e 26/26 checks. Marcador SINNOH_REAL_F06_35_NATURAL_MAPS_91_TELEPORTS_35_EVENTS_64_EXTERIORS_OK confirmado no job 138751381224. 35 novas chegadas, 56 mapas anteriores e 35 eventos preservados; 64 exteriores. Sem aprovação nativa.

## F07 — interiores originais privados

36 mapas reais do tileset 25 (indoors.png, 256x29984, 7880 entradas, sem autotiles), hashes SHA-256, nomes, dimensões e hierarquia pinados no catálogo data/regions/sinnoh-f07-interior-sources.json a partir do inventário F03 (job 138719583390). 12 Centros Pokémon, dez marts, oito portarias, seis outros interiores; identificadores por MapID de origem evitam inventar funções para nomes ambíguos. Alvo 127 mapas e teleportes QA, 35 eventos antigos e 64 exteriores. Não copiar os 134 eventos externos, scripts, warps ou funcionalidades dos edifícios. Nenhum novo interior recebe árvores F02. Preservar os 91 MapIDs, bytes, atlas, conexões, máscaras e teleportes anteriores. IDs adicionais livres 442–599 após leitura de MapInfos, Data e PBS; abortar se insuficiente, sem reservar IDs compartilhados. Namespace anterior somente se hashes de base e mapas e todos os IDs coincidirem. Nenhum acesso a saves pessoais ou Game.exe. Fonte privada, sem distribuição pública. Salas, ginásios e edifícios não presentes neste conjunto de 36 não são declarados preparados; conexões, cura, compras e história ficam para fases posteriores.
