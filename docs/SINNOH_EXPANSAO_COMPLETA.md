# Sinnoh completa — expansão F01–F15

Referência Platinum. Progresso de preparação (não aprovação nativa):

- Rotas: **30/30**, Rota 201–230 e seis segmentos adicionais.
- Cidades: **14/14**, todas preparadas na F04.
- Piloto privado: **127 mapas preparados**.
- Fases novas: **7/15 concluídas**, F01/F02/F04/F05/F06/F07 integradas (11/11 cada), F03 integrada (9/9); F08 subconjunto seguro integrado (49 portais e 7 seams), complementação F08B em validação.

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
- [x] F07 — Importação dos interiores e edifícios (PR #285, 11/11; 127 mapas preparados)
- [ ] F08 — Conexões entre mapas e colisões (PR #286 integrado parcialmente, 97 relações pendentes)
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

### F07 — diagnóstico de identidade do mapa 148

O rerun do job 138765931080 baixou e verificou os dois ZIPs, reconfirmou os marcadores F05/F06 e encontrou componentes transitáveis nos primeiros 24 interiores. Falhou em SOURCE_EXTERIOR_IDENTITY antes de emitir o diagnóstico de terreno do próximo mapa (148). O inventário F03 usa strip() nos nomes; F07 passa a comparar somente com esse ajuste de espaços externos. Parent ID, hash do mapa, hash do ZIP, dimensões e tileset continuam obrigatórios; fases anteriores mantêm comparação literal. A hipótese de espaços externos precisa ser confirmada pelo novo job real; não há marcador F07 aprovado nesta execução.


## F07 — aceite CI

PR #285 integrado em 2770a91f790a2ae904caff83bd92f6f2595b35f2; 11/11 workflows, 26/26 checks. Marcador SINNOH_REAL_F07_36_INTERIORS_127_TELEPORTS_35_EVENTS_64_EXTERIORS_OK confirmado no job 138773135299. Mapa 148 -> 557 (10,7), 53 células. 36 interiores, 91 mapas anteriores preservados.

## F08 — conexões privadas, subconjunto seguro

Catálogo de 123 mapas físicos e 145 relações dirigidas distintas, 69 pares recíprocos, extraídos do inventário F03. Reabre o ZIP pinado local, verifica hashes e alvos estáticos, analisa páginas e coordenadas sem executar ou copiar scripts. Reconstrói somente transferências simples recíprocas sem condições, com origem/destino transitáveis, sem conflitos de eventos ou teleporte QA. Anexa eventos autorais mínimos apenas nos mapas novos, sem mudar os 35 eventos anteriores, geometria, MapIDs, atlas ou máscaras. Conexões seamless apenas exteriores com lados únicos e eixo transitável. Preserva abertura autoral, bloqueia conexões ambíguas, destinos ausentes e páginas condicionais. Reutiliza namespace apenas com hashes completos da geração F07 anterior ou F08 atual; nenhum save aberto. Saves nativos ainda não testados; mapas salvos podem precisar ser recarregados para receber novos eventos. O marcador F08 confirma um subconjunto seguro, não aprovação dos 145 vínculos nem QA nativa; vínculos rejeitados ficam pendentes para implementação específica. Sem distribuição de assets.

### F08 — primeiro resultado real e refinamento dos portais

HEAD fd964ee865f5daeef9222ad8e3ccf496bdf89957: 11/11 workflows e 26/26 checks; job 138779035163 confirmou marcador SAFE_SUBSET_OK, sete seams (79–77,84–104,91–90,110–96,151–150,157–159,214–206), zero portais; 353 eventos classificados genericamente como complexos/condicionais. Nenhum dos 145 vínculos estáticos aceito como portal. Não avançar F09 com esse resultado. O refinamento distingue motivos e registra formas sanitizadas de páginas/comandos, sem scripts ou texto. Aceita exclusivamente comandos cosméticos limitados (espera, efeito sonoro, transição e comentários) e botão de ação original, mantém bloqueios de movimento, scripts, condições, variáveis, diálogos, páginas múltiplas, coordenadas e reciprocidade. As animações descartadas não são importadas. A ampliação é conservadora e ainda precisa ser confirmada pelo ZIP real; se zero portais persistir, usar as formas do novo log para corrigir casos específicos, sem afrouxar colisões.

### F08 — transições de tonalidade identificadas

HEAD 8f82b9e48fd8d3080b9a308b0e4021b3959de897: 11/11 workflows, 26/26 checks, marcadores F07/F08 confirmados no job 138794303660. Sete seams preservados, zero portais; 242 unsupported_commands, 102 multiple_pages, 8 nested_commands e 1 page_conditions. 188 eventos apresentam exatamente [250,223,106,201,223,0] (som, alteração de tonalidade, espera, transferência, alteração de tonalidade, fim); 105 relações dirigidas internas e 45 pares recíprocos candidatos nesse grupo, antes da validação geométrica. Refinamento: aceita apenas Tone inerte de 32 bytes com quatro doubles finitos em limites RMXP e duração inteira 0–120, substitui tonalidade por fade nativo, não executa comandos originais. Registra rejeições geométricas individualmente e forma/tipos dos parâmetros cosméticos; mantém scripts, variáveis e condições bloqueados. Testes negativos de Tone e regressão das sete seams. Ainda sem evidência real de portais aceitos nesta nova HEAD; não avançar F09 até validar.

### F08 — recuperação de portas com coordenadas recíprocas

HEAD ea919135abb7cac490af1dbf0fa2b75266d16274, job 138799290004: 11/11 workflows, 26/26 checks, marcadores F07/F08, 7 seams, 0 portais. 188 sequências de tonalidade agora classificadas como aceitas, mas rejeições geométricas: 71 origens não seguras, 8 destinos não seguros, 26 sem retorno seguro, 4 loops/ambiguidade, 75 fora do grafo recíproco, 4 abertura protegida, 102 páginas múltiplas, 8 comandos aninhados, 1 condição de página, 54 comandos não suportados. Evidência concreta: Oreburgh 22 evento 13 (50,18) -> 43 (15,15); 43 evento 4 (15,16) -> 22 (50,18). A saída original está bloqueada, o ponto de chegada recíproco é transitável e adjacente. Há 34 pares de eventos no log com posições recíprocas a distância <=1, incluindo dois protegidos da abertura e casos com destino bloqueado; não são aprovações. Nova reconstrução admite somente aproximação adjacente única provada pelo retorno original, ainda exigindo componente seguro, destino original seguro, ausência de eventos/QA spawn e testemunha recíproca sobrevivente. Converte aproximações e posições compartilhadas com chegada em interação por botão (evento transparente e atravessável), sem teleporte automático circular, sem alterar colisões, geometrias ou scripts. Destinos bloqueados continuam rejeitados. Preserva sete seams e 127 mapas, 35 eventos anteriores, hashes de namespace e teleportes; teste real ainda necessário. Não declarar portais recuperados antes do CI.

### F08A — subconjunto integrado e continuação F08B

PR #286 integrado em 974706db5ccb976ac3d45da07f290b85578ff268 após 11/11 workflows, 26/26 checks, marcador real no job 138803198748. 49 eventos em 38 mapas, 22 aproximações, 45 ações, 48/145 relações dirigidas e 24/69 pares, sete seams. Nove Centros Pokémon, oito Marts e duas portarias com pelo menos uma ligação. Restam 97 relações; F08 continua aberta, F09 pendente, progresso 7/15. F08B fixa assinatura dos 49 eventos reais e sete seams. Para portas com retorno diagonal (exemplo mapa 106 (0,23) -> 107 (12,7), retorno 107 (13,7) -> 106 (1,22)), aceita apenas ponte ortogonal única já transitável e retorno recíproco único; sem inventar destino, sem alterar colisões, sem tocar os 49 eventos anteriores. Portais novos por ação, sem conflito com posições e chegadas anteriores, sem scripts/condições. Preserva namespace por hashes completos F07, F08A ou F08B; não abre saves. Nenhum portal novo declarado aprovado antes do teste real. Marcador de preservação F08B não implica aprovação de todas as conexões.

### F08B integrada e F08C — quatro exteriores ausentes

PR #287 integrado em 46f0131bec418e7b12c7c526034362c7b940b487 após 11/11 workflows, 26/26 checks. Job 138807444684: 63 portais (14 novos), 62 relações, 31 pares, 7 seams. F08C acrescenta quatro mapas originais pinados: Resort 139, Cycling Road 147, Survival 163, Fight 166. IDs privados append-only, SHA e geometria obrigatórios, 131 mapas alvo. Reabre as fontes dos pares que envolvem novos mapas e recria apenas transferências simples, recíprocas e transitáveis; preserva os 63 eventos aprovados, 35 antigos, sete seams e 127 geometrias/IDs. Sem copiar scripts, sem inventar destinos. Contabilizar os portais efetivamente recuperados no job real; não declarar todos os edifícios conectados sem evidência. Compatibilidade de namespace por hashes F07/F08A/F08B/F08C; QA nativa pendente. F09 permanece pendente até cobertura suficiente.

### F08C — primeiro teste real e correção do catálogo

Job 138811521915: F07/F08/F08B confirmados; importação real dos quatro mapas pinados, IDs 569–572, pontos seguros (26,14), (23,74), (16,20), (32,19). Relatório gerou dez portais em cinco pares: Survival–168/171 e Fight–169/172/188. Teste final falhou na comparação do catálogo, antes de emitir marcador F08C: os quatro símbolos já existiam no catálogo F01 como planejados; a F08C duplicava entradas, e a comparação excluía os quatro somente do lado novo. Correção mantém catálogo, ordem e categorias, popula exclusivamente os quatro destinos; exige ausência de duplicatas e igualdade dos demais. Diagnóstico real de Cycling Road mostrou 2442 células de tag 4 passáveis; o refinamento permite apenas solo normal/rocha no novo mapa 147, ligado ao spawn original sem alterar máscaras ou colisões. Novos diagnósticos geométricos por lado para Resort/Cycling. Testes fixam os dez portais já gerados. Marcador final ainda pendente; não alegar importação integrada ou aprovação nativa.

### F08C integrada; início F09A

PR #288 integrado em 817ca9df06008650f2fdbe3d173bffa3b83f2a3e após 11/11 workflows e 26/26 checks. Job 138814277503 confirmou 131 mapas e 63 portais anteriores, sete seams e dez novos portais (73 total). Resort e Cycling Road permanecem separados por componentes de geometria; não liberar colisões nem forçar passagens condicionais. 11/12 Centros Pokémon, 10/10 Marts, 7/8 portarias com ao menos um vínculo. F08 parcial, 7/15 integralmente concluídas; cobertura suficiente para testar encontros no piloto via teleporte QA, não para declarar travessia completa. F09A audita 131 mapas, prepara até 14 tabelas autorais Blue QA com espécies do catálogo CH13, pesos iguais e níveis explicitamente autorais, só quando existe grama ou mapa de caverna e espécies locais válidas. Conserva PBS e encontros iniciais, não inclui lendários/eventos estáticos, métodos aquáticos novos ou atribuições de hora sem evidência. Inventaria PBS de encontros do ZIP pinado, se existente, sem importar formato desconhecido. Relatório distingue ausência de referência, terreno e espécie local. Preserva 131 MapIDs, 73 portais e 35 eventos antigos, sem modificar mapas/saves. Validação nativa e cobertura integral de encontros pendentes.

### F09A integrada e F09B — PBS original pinado

PR #289 integrado em efd414ed8ec4d2f4ed225aa249de019b6a441967 após 11/11 workflows e 26/26 checks. Job 138820566539: 131 mapas auditados, 13 tabelas QA autorais, 17 mapas com encontros, 29 mapas com grama sem Land. PBS original encontrado: SHA e812fb6413b410a8c9ce4380cd02c0e1f8a5d257f5793cf87182201d6e6d7990, 81 MapIDs, 67 correspondências. F09B valida hash, mapeia apenas IDs pinados, aceita exclusivamente seções v0 e sintaxe ponderada inequívoca compatível com Essentials, pesos 100, níveis 1–100, espécies locais, terreno Land/Cave e horários conhecidos. Preserva métodos anteriores inclusive os autorais; insere métodos adicionais sem duplicar seções. Bloqueia abertura, espécies especiais, versões, métodos desconhecidos, água/varas até prova de acesso. Diagnósticos sanitizados de dialeto, rejeições e cobertura; fixture CI de espécies doadoras não substitui catálogo local. Nenhuma nova tabela declarada aprovada antes do CI. 131 mapas/73 portais/7 seams e saves preservados; F08 e F09 parciais, 7/15 fases integrais.

### F09B integrada; F09C — pesos proporcionais e evidência aquática

PR #290 integrado em 97c52e299ed0fb5305a9a15192586b76c37c3674 após 11/11 workflows e 26/26 checks. Job 138823887883: 99 métodos originais, 666 slots, 59 mapas com encontros, três mapas com grama sem Land; espécies fixture, não base local. 21 métodos rejeitados por soma de pesos !=100; 156 aquáticos pendentes, 45 Radar, 25 preservados, dois protegidos, uma seção incompatível. F09C fixa assinaturas dos 99 métodos e os 21 candidatos. Política autoral Blue: converte proporções para percentuais inteiros somente se todos forem exatos, sem arredondamento, sem modificar espécies ou níveis, sem alterar tabelas anteriores. Caso contrário mantém pendente e registra soma real. Relatório de lacunas de horários sem fallback e contagem de tags de terreno e margens adjacentes em mapas aquáticos, sem atribuir semântica de água por número. Surf/pesca continuam bloqueados: aquisição de HM/varas e acesso nativo não comprovados. Não declara novas tabelas antes de CI; 131 mapas/73 portais/7 seams e saves intactos, F08/F09 parciais.

### F09C integrada; F09D — preservar pesos relativos originais

PR #291 integrado em cc6dba50e99c4535a75f24983f677f84f60d84d2 após 11/11 workflows e 26/26 checks. Job 138831024964: 99 métodos preservados, LandMorning da Rota 221 convertido exatamente (soma 125), 20 candidatos restantes, seis lacunas de horário, 39 mapas com evidência geométrica aquática. F09D utiliza a convenção de pesos relativos existente em pbs.py (Safari North FRLG soma 95), sem arredondar nem modificar slots, espécies ou níveis. Restringe a lista dos 20 candidatos ao hash da fonte e às somas/slots do job real; rejeita espécies ausentes, especiais, métodos e terrenos incompatíveis. Verificação nativa adicional de igualdade das tuplas compiladas, sem alegar execução Game.exe; se falhar, marcador de compilação fica bloqueado. CI fixture de espécies não prova base local. Surf, pesca e Radar permanecem pendentes, tags numéricas não provam semântica nem aquisição de HM/varas. F10 somente após validar a cobertura F09D suficiente. 131 mapas/73 portais/7 seams e saves não modificados.


### F09D integrada; F10A — inventário de treinadores e NPCs

PR #292 integrado em 902ad2be9517d85ee2df787c5c14565dcab10705 após 11/11 workflows e 26/26 checks. Job 138835064619 confirmou 20/20 métodos relativos, 136 slots adicionais, 120 métodos originais recuperados no total, zero lacunas de horários e 60 mapas com encontros. Cycling Road e Lake Valor segmento 216 ainda sem Land. A fixture não comprova compilação nativa. Surf/pesca/Radar seguem pendentes.

F10A audita eventos dos 127 mapas-fonte fixados por SHA-256 correspondentes aos 131 mapas QA (quatro sem mapeamento direto de eventos). Classifica transferências, marcadores de treinador, diálogo simples e outros eventos, contabiliza formatos do PBS de treinadores caso presente e cruza posições com máscaras/componentes/ocupação da cópia QA. A fila é somente metadados: nenhum script, fala, sprite ou equipe do doador é publicado ou executado. Candidatos geométricos não são aprovação de identidade, classe, equipe, colisão, sprite ou batalha. Nenhum novo treinador/NPC instalado nesta subfase; F10B deve reconstruir primeiro os candidatos ordinários com PBS local validado, IDs append-only, auto-switch compatível e regressão de saves; chefes/história ficam nas fases próprias. Mantém política Blue Normal 70%, Master 90%, chefes protegidos. CI real pendente; não declara QA nativa.


### F10A integrada; F10B — reconstrução de treinadores

PR #293 integrado em 7302bcc3345dbb8e649b8d8a63498524f6cd9cc5 após 11/11 workflows e 26/26 checks. Job 138840621200: 2.124 eventos em 127 mapas-fonte, 12 candidatos a treinador, cinco posições elegíveis (42/29–31 e 79/34–35), quatro diálogos, dois elegíveis; nenhum PBS de treinadores no ZIP. F10B lê somente identificadores literais de chamadas de batalha, inclusive condição RMXP código 111, sem executar scripts. Equipes de primeira batalha são referências históricas de Platinum ([207](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_207), [211](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_211)), não PBS do doador. Identidade, classe local, espécies, sprite exato, geometria, desembarque e conectividade exigidos; pares duplos e bloqueios por Rock Smash não liberados. Eventos append-only acionados por interação, diálogos autorais PT-BR, vitórias persistidas no estado regional apenas após retorno true, usa o hook BlueCampaign 70%/90% sem fallback não escalado. Recompilação verifica equipes e mantém perfil de save anterior se hashes F09D coincidirem. Nenhum novo treinador declarado instalado até CI real e compilação local; testes usam catálogos fixture. Surf/pesca/Radar, R07/R08/R09 continuam pendentes.


### F10B2 — sprites e diagnóstico integral dos candidatos

F10B PR #294 integrada em 9a261b423c2982f8651edf5779dc77d492727aa9 (11 workflows, 26 checks). Job 138845255807 confirmou zero recuperados: 42/29, 42/30 e 79/35 sem correspondência histórica; 42/31 e 79/34 com identidade validada, sprite ausente/inválido. F10B2 consulta os dois ZIPs SHA-fixados e admite apenas uma folha de classe equivalente inequívoca no pacote Gen 4, distinguindo essa substituição do sprite exato. Diagnostica nomes e classes literais, nomes de arquivos e geometria dos 12 candidatos sem exportar scripts ou diálogos. Os sete anteriormente bloqueados por geometria/movimento continuam sem instalação. Preserva as posições, IDs e spawns já aceitos; não habilita Surf/pesca/Radar. Nenhum treinador adicional confirmado até relatório real; compilação local e QA nativa pendentes.


### F10B3 — ampliação conservadora

F10B2 real (job 138853026342, HEAD 95c2ea9b397d5e1e03adf398a1149ba6703d8e55): Justin (HIKER, Geodude e Nosepass nv.20, MapID 469, evento 1, posição 48/9) recuperado com sprite de classe NPC_046_Hiker.png; 12 identidades literais. F10B3 seleciona explicitamente NPC_007_Black_Belt.png para Sean apenas quando as duas folhas previamente auditadas estão presentes, marcando como escolha visual de projeto, não equivalência do sprite original. Kath conserva nome literal e recebe referência histórica Katherine (Noctowl nv.34) somente se a classe BIRDKEEPER e a posição previamente auditada coincidirem; sprite ainda obrigatório. Anthony/Lauren têm equipes históricas Chimchar/Pachirisu nv.22, porém continuam bloqueados por batalha dupla. Referências https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_207 e https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_211. Alexander e Wyatt permanecem pendentes por divergência de nome/classe; demais acessos/movimento mantidos. Mantém IDs/eventos F10B2 e aceita hashes dos mapas da revisão anterior para perfil de saves. Teste real exige Justin e Sean, não declara instalação nativa. Surf/pesca/Radar permanecem pendentes. CI da F10B3 pendente.


F10B2 integrada em b0a5868130429ed2cdcf05f5c8688bc8d42227e3 (11/11 workflows, 26/26 checks). F10B3 HEAD fd2e7908e70490b6c718aa7cc8b36655fd3ed5a6 job 138855505090 confirmou Justin e Sean (2/12), preservação de mapas e encontros, Kath sem sprite, Anthony/Lauren sem batalha dupla. Os 10 workflows/25 checks da base anterior passaram. PR #296 redirecionado para main; este commit atualiza somente evidências/estado e dispara nova validação completa incluindo Kanto. Sem aprovação nativa ou compilação local.


### F10B4 — dupla e acesso seguro

Implementa Anthony/Lauren como grupo atômico: ambos os sprites de classe precisam existir e a geometria de ambas as células deve preservar conectividade e todos os spawns; nenhum evento parcial. Cada interação exige dois Pokémon aptos, equipes PBS compiladas, escopo QA, campanha ativa; invoca TrainerBattle.start_core com dois arrays (API Essentials v21.1, https://github.com/Maruno17/pokemon-essentials/blob/v21.1/Data/Scripts/012_Overworld/002_Battle%20triggering/001_Overworld_BattleStarting.rb). Vitória somente outcome 1, salva ambos os identificadores em uma operação. Corrige party2starts apenas durante essa dupla, pois Master expande equipes após geração de offsets originais; sem alterar BlueCampaign global. Harry pode ser reconstruído como evento estacionário autoral no ponto original, não importa movimento donor. Kath tenta aliases exatos adicionais de folha feminina, sem sprite inventado. Preserva IDs Justin/Sean, 131 mapas, teleportes, 73 portais, sete seams, 120 métodos e hashes de perfil F10B3. Cinco eventos fora do componente não são deslocados arbitrariamente. Ruby fixture testa derrota, vitória/reload, duas equipes e offsets; relatório real define cobertura. Não libera Surf/pesca/Radar, QA nativa pendente.
