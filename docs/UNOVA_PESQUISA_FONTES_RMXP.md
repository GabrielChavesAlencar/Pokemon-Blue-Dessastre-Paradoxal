# Unova — pesquisa de fangames RPG Maker XP para reaproveitamento auditado

> **Projeto:** Pokémon Blue: Dessastre Paradoxal | **Pesquisa:** 17/11/2026 | **Estado:** PESQUISA / SEM IMPORTAÇÃO / SEM AUTORIZAÇÃO GERAL DE ASSETS
>
> **Propósito:** escolher a fonte de mapas, NPCs, eventos e músicas para uma adaptação de Pokémon White (Black/White) ao jogo principal Decades + Essentials 21.1. Este documento NÃO instala nada. Nenhum ZIP de terceiros foi baixado e inspecionado nesta pesquisa; conteúdo/versão de cada arquivo ainda requer auditoria local.

## 1. Decisão executiva

**Melhor candidato verificável para obter arquivos editáveis de região:** **Pokémon World V18**, disponibilizado pelo próprio criador na comunidade r/PokemonRMXP em 19/08/2022. O autor afirma ter produzido mapas de várias regiões, incluindo parte de Unova, e fornece um ZIP do projeto, um arquivo de créditos e documentação. Em resposta pública de 2024, concordou que outro criador usasse parte do projeto. Isso é sinal favorável para **solicitar/confirmar uso do trabalho autoral**, NÃO é licença de músicas, artes oficiais ou materiais de outros colaboradores.

**Limite decisivo:** Unova NÃO está completa nesse pacote, segundo o próprio autor. O post inicial diz aproximadamente metade e uma resposta dele fala em aproximadamente um quarto; essa divergência deve ser resolvida exclusivamente pelo inventário do ZIP, nunca por estimativas. Foi mencionado um percurso até **Castelia City**, mas isso não prova que Nuvema, Nacrene ou cada evento esteja completo.

**Fonte de comparação funcional de Unova:** **Pokémon Fire Ash**, versão 3.7.1, feito com RPG Maker XP + Pokémon Essentials v19.1. Seu tópico oficial afirma que é possível viajar por Unova entre várias regiões. Porém segue a jornada do anime de Ash, **não** a campanha Black/White de N, Ghetsis, Cheren e Bianca. Não foi identificada permissão explícita para transplantar mapas, NPCs, música ou eventos; usar apenas para estudar progressão, navegação e características visuais até conseguir autorização específica.

**Referência estrutural v21.1 a acompanhar:** **The Pokémon World Project**, de SocomSeal. É um recurso feito para recriar campanhas principais em Essentials 21.1; porém seu quadro público v2.0 declara **UNOVA 0%**. Não escolher como fonte existente de Unova. Pode ajudar com padrões técnicos e outras regiões em momento posterior, após leitura das condições de uso.

**Recurso técnico complementar:** **MCChara/Pokemon-Essentials-Gen-5**, fork voltado ao estilo B/W e B2/W, porém baseado em Essentials v20.1 e descrito como **não sendo um projeto completo**. Útil para estudar mecanismos e estética, não para supor existência de cidades/eventos completos nem substituir o motor do Decades 21.1.

**Conclusão operacional:** fonte primária **Pokémon World V18 (sob condição de auditoria)** + reconstrução própria das áreas ausentes usando detonado/documentação + referência visual ao Fire Ash. Preservar integralmente o motor e as regras já implementadas no Dessastre. Caso o ZIP não contenha mapas editáveis de Unova, esteja inacessível, ou a autorização de um recurso específico não seja suficiente, registrar bloqueio e produzir essa área com recursos próprios/licenciados em vez de tentar extrair de arquivos protegidos.

## 2. Fontes verificáveis e links

| Identificador | Fonte | Evidência pública observada | Link |
|---|---|---|---|
| F01 | Pokémon World V18 — publicação original e consentimento em comentários | Autor publicou links do projeto, créditos e docs; declara Unova parcial; aceita uso de parte do projeto numa resposta | https://www.reddit.com/r/PokemonRMXP/comments/wsiyyr/ |
| F02 | Pokémon World V18 — ZIP anunciado pelo autor | Arquivo anunciado publicamente; conteúdo não inspecionado nesta pesquisa | https://www.mediafire.com/file/tq5w0in2xt2peb1/Pokemon_World_V18.zip/file |
| F03 | Pokémon World V18 — créditos | Créditos originais fornecidos pelo autor; examinar antes de qualquer reaproveitamento | https://www.mediafire.com/file/gdtsjg5lbnstzo1/Credits.txt/file |
| F04 | Pokémon World V18 — documentos | Pasta de referência anunciada pelo autor | https://drive.google.com/drive/folders/1xBVQkXb47gTl7xgEMfDBz4oSukaNmKH4?usp=sharing |
| F05 | Pokémon Fire Ash — página da equipe | RPG Maker XP/Essentials v19.1, regiões incluindo Unova, v3.7.1; roteiro inspirado no anime | https://eeveeexpo.com/threads/9489/ |
| F06 | The Pokémon World Project — página do autor | Essentials 21.1 e UNOVA 0% no quadro de progresso | https://eeveeexpo.com/resources/1877/ |
| F07 | The Pokémon World Project — fórum | Objetivo de recriar regiões e link de projeto público | https://www.pokecommunity.com/threads/the-pok%C3%A9mon-world-project.541079/ |
| F08 | MCChara Gen-5 — código | Fork Essentials 20.1, não é campanha completa | https://github.com/MCChara/Pokemon-Essentials-Gen-5 |
| F09 | Maruno17 Essentials — referência compatível | Repositório de scripts baseado em v21.1; não contém campanha pronta | https://github.com/Maruno17/pokemon-essentials |
| F10 | Detonado Black/White | Referência da campanha a recriar; não é fonte binária de mapas | https://www.pokemythology.net/detonados/detonado-black-white/ |
| F11 | Plano narrativo gerado nesta conversa | Análise da sequência original de Unova disponibilizada como arquivo nesta conversa; ainda não está publicada no GitHub | UNOVA_PLANO_MESTRE_DETONADO_BLACK_WHITE_DESSASTRE_PARADOXAL.md (arquivo local do chat) |
| F12 | Regras regionais do projeto | Contrato real de saves, viagens, NPC de viagem e itens regionais | docs/VIAGEM_REGIONAL_LIVRE_NPC.md |

**Observação de proveniência:** o conteúdo de F01 é uma manifestação do autor do fangame; não resolve direitos da franquia Pokémon ou de autores de sprites, tilesets, arranjos musicais e plugins incluídos. Um fangame gratuito não é automaticamente um pacote de recursos reutilizáveis.

## 3. Matriz de escolha por finalidade

Legenda: **sim** = declarado por fonte primária; **parcial** = declarado como incompleto; **desconhecido** = sem auditoria binária ou autorização; **não** = fonte não oferece o escopo.

| Fonte | RMXP / Essentials | Mapas Unova | NPCs Unova | Eventos do enredo B/W | Músicas reaproveitáveis | Arquivos abertos / direito de reaproveitar |
|---|---|---|---|---|---|---|
| Pokémon World V18 | Sim / v18 | **Parcial** | Desconhecido | Desconhecido | Desconhecido; direitos não verificados | Projeto ZIP anunciado; autorização do criador para partes; direitos por item pendentes |
| Pokémon Fire Ash 3.7.1 | Sim / v19.1 | Região jogável declarada | Personagens do anime; inventário pendente | **Não corresponde** à narrativa Black/White | Pacote de áudio anunciado; direito de reutilizar não demonstrado | Jogo distribuído; fonte editável e autorização não confirmadas |
| The Pokémon World Project v2.0 | Sim / v21.1 | **Não: Unova 0%** | Não | Não | Não verificado | Recurso público para criação; Unova ausente no status consultado |
| MCChara Essentials Gen-5 | Sim / v20.1 | Não demonstrado | Não demonstrado | Não demonstrado | Não demonstrado | Repositório técnico, não jogo completo |
| Remake 3D de Castelia (Unity) | **Não** | Cena 3D de Castelia | Não aplicável | Não aplicável | Não aplicável | Engine incompatível, desconsiderado |
| ROMs oficiais DS / PokeMMO | **Não** | Referência geográfica | Referência narrativa | Jogo oficial | Trilhas oficiais protegidas | Não converter/redistribuir ROMs ou áudio oficial como pacote |

### Pontuação prática (estimativa técnica, não medição)

1. **Pokémon World V18:** melhor custo-benefício potencial para o **primeiro lote editável**, por compartilhar formato RMXP e divulgar o projeto com docs; alto custo de adaptação v18 → v21.1, grande lacuna de Unova e direitos específicos ainda pendentes.
2. **Fire Ash:** melhor prova pública de Unova extensa já jogável em RMXP; **não recomendado como doador automático** de scripts/músicas/personagens devido a outra história, versões e falta de autorização comprovada.
3. **Pokémon World Project:** melhor direção de arquitetura multi-regional compatível com v21.1; utilidade futura, **nenhum mapa Unova comprovado**.
4. **MCChara Gen-5:** ferramenta de estudo; extrair apenas ideias técnicas/implementações licenciadas quando compatíveis, nunca sobrescrever integralmente scripts do jogo.

Esta classificação pode mudar se uma inspeção futura revelar mapas completos ou direitos claros em outra fonte. Não se deve chamar Pokémon World V18 de “base completa”.

## 4. O que realmente podemos importar e sob quais condições

| Camada | Arquivos típicos de RMXP/Essentials | Inspeção obrigatória | Condição de uso |
|---|---|---|---|
| Mapa e geometria | Data/MapNNN.rxdata, Data/MapInfos.rxdata | Dimensões, tileset, autotiles, passabilidade, eventos, IDs | Proveniência/permite reutilização + remapeamento sem colisão |
| NPCs e placas | Eventos dentro de MapNNN.rxdata; Graphics/Characters | Sprite, páginas, switches, textos, interações, duplicações | Créditos/autorização por sprite e revisão PT-BR |
| Eventos da história | Eventos de mapa, CommonEvents, scripts Ruby | Dependência de switches, variáveis, itens, transferências | Reescrita conforme Black/White; nunca copiar script v18 cegamente |
| Dados de treinadores | PBS/trainers*.txt, trainer_types, sprites | Times, IDs, espécie, golpes, level cap, rivais | Conciliar com PBS e balanceamento local |
| Encontros | PBS/encounters*.txt e metadata | Método, slots, versionamento, estação e flags | Tabelas rastreáveis, sem chance/nível inventados |
| Mapas regionais | Graphics/Pictures ou UI equivalente | Coordenadas da região, pontos Fly, nomes | Converter a formato do Blue sem inventar destinos |
| BGM / ME / SE | Audio/BGM, Audio/ME, Audio/SE | Nome, duração, origem, autor, licença, permissões | **Nunca redistribuir trilhas comerciais sem autorização** |
| Tilesets | Graphics/Tilesets, Autotiles, Data/Tilesets.rxdata | Dependência e direitos, escala, prioridades | Pode exigir redesenho original |
| Plugins | Plugins e Scripts | Versão v18/19/20 vs v21.1; riscos de monkey patch | Portar trechos compatíveis se licença e autoria permitirem |

**Regra:** “o arquivo existe no ZIP” não implica “pode subir à main”, “é seguro no JoiPlay”, “está integrado” nem “está completo”.

## 5. Especificação de auditoria do Pokémon World V18

### 5.1 Aquisição segregada

- Baixar **somente da publicação do autor** quando o link estiver funcional. Não usar mirrors desconhecidos.
- Guardar fonte bruta **fora do Git**: .blue-work/unova/sources/pokemon-world-v18/.
- Registrar URL, data, nome, tamanho real, SHA-256 e identificador de revisão no manifesto de fontes.
- Salvar cópia de Credits.txt e registrar eventuais autores separados; não publicar automaticamente mídias do ZIP.
- Inventariar sem execução: atenção a arquivos .exe, .dll, .bat, scripts e arquivos compactados aninhados.
- Se ZIP estiver indisponível, registrar SOURCE_MISSING; não usar arquivos vazios fictícios para simular aprovação.

### 5.2 Extração somente em área de trabalho

- Listar os caminhos Data/, Graphics/, Audio/, PBS/, Plugins/, Game.rxproj e a versão Essentials detectada.
- Identificar MapInfos real e referências de mapas de Unova **por nome, conteúdo e conexões**; IDs numéricos só podem sair de bytes reais.
- Para cada mapa Unova: dimensões, nome, mapa pai, tileset, eventos, portal/saída, posição inicial, encounters, metadata, BGM, assets externos, estado de edição.
- Para cada evento: ID local, coordenadas, páginas, gatilhos, conditions, comandos e chamadas Ruby. Catalogar referências cruzadas.
- Calcular hashes dos arquivos e listar dependências não encontradas.
- Inventariar áudio sem copiá-lo: BGM/ME/SE, fonte declarada, formato, licença, necessidade de substituto.
- Separar “potencialmente transferível” de “incompatível”, “origem desconhecida” e “material de terceiro”.

### 5.3 Esquema sugerido (campos; não é um manifesto real)

| Campo do relatório | Significado |
|---|---|
| source_id | pokemon-world-v18 |
| original_map_id | MapID REAL observado na fonte, nunca adivinhado |
| original_map_name | Nome na fonte, sujeito a validação |
| unova_area | Cidade/rota canônica associada ou unresolved |
| unova_campaign | BW, B2W2 ou unknown |
| has_map_geometry | Evidência de mapa íntegro |
| event_count | Eventos realmente presentes no RXDATA |
| trainer_count | Treinadores cruzados com dados PBS |
| rights_status | permitted_author_only / third_party_pending / blocked |
| compatibility | compatible / port_needed / blocked |
| import_status | source_audited / qa_candidate / accepted / rejected |
| mapped_map_id | Novo MapID no Decades, alocado após auditoria do MapInfos local |
| evidence | Caminho, SHA-256, relatório, ticket e teste |

**Gate obrigatório:** não criar remap para produção sem baseline real do Decades instalado e inventário conjunto de Kanto/Johto/Hoenn/Sinnoh. Não usar intervalos arbitrários de IDs. Não sobrescrever MapInfos, System, Tilesets, CommonEvents, scripts e saves.

## 6. Correspondência com a história Black/White

**Base narrativa canônica escolhida:** White. A origem de conteúdo não altera o roteiro definido no detonado: Nuvema → Accumula → Striaton → Nacrene → Castelia → Nimbasa → Driftveil → Mistralton → Icirrus → Opelucid → Pokémon League → N's Castle; depois pós-jogo oriental, lendários e rematches.

Mesmo quando uma cidade existir fisicamente na fonte, marcar separadamente:
- Mapa e colisão: presente/ausente/pendente de QA;
- NPC e placa: presente/ausente/tradução pendente;
- Eventos story B/W: implementados/reconstruídos/testados;
- Treinadores, encounters, itens: inventariados/rebalanceados/testados;
- Música: licenciamento verificado / substituto / mudo deliberadamente;
- Estado real: planned / QA / installed / playtested.

**Não aproveitar automaticamente eventos de Ash** para substituir N/Ghetsis nem importar times, recompensas, flags, HMs ou outro controle de história de uma região sobre a outra.

## 7. Música: plano de trabalho, não autorização de redistribuição

**Categorias do BlueMusic:** introdução, Nuvema, Accumula, Striaton, Nacrene, Castelia, Nimbasa, Driftveil, Mistralton, Icirrus, Opelucid, rotas, cavernas, pontes, ginásios, Centro Pokémon, encontro selvagem, treinador comum, rival, líderes, Team Plasma, N, Ghetsis, Elite, campeão, lendários, créditos e pós-jogo.

Para cada chave registrar: area_key, context (map/battle/ME), season (opcional), variant (WHITE/BLACK), source_file, rights_owner, written_permission_or_license, attribution, fallback_blue_music, tested_in_windows, tested_in_android. Fallback tem prioridade quando o arquivo não existir ou não houver direito de uso; nunca baixar e embutir automaticamente OST comercial ou áudio vindo do Fire Ash/World V18.

Critério: nenhum evento pode chamar uma BGM inexistente; uma faixa não liberada não pode entrar no instalador público. É permitido preparar **catálogo textual de nomes/chaves e referências** sem redistribuir o áudio original.

## 8. Segurança do instalador Blue-Story

A fonte escolhida **não** vira dependência silenciosa do instalador geral. Implantação futura apenas mediante manifestos auditados, hashes, direitos, endereço de origem consentido, opt-in quando aplicável, backup atômico e rollback. Se falhar, o instalador mantém Kanto/Johto/Hoenn/Sinnoh/Decades e saves intactos, informa “Unova em preparação”, e jamais declara êxito.

O modo privado QA trabalha em cópia isolada de game/ (ou overlay auditado), sem executar código da fonte antiga no host e sem alterar seu executable principal. Criação de novos mapas ocorre somente depois de aprovação do catálogo real e do remap.

## 9. Fases sugeridas para aproveitar fontes

1. U01 — obter autorização/credits e catalogar fontes.
2. U02 — inspeção física dos ZIPs e classificação item a item.
3. U03 — auditoria das cidades/rotas presentes vs detonado.
4. U04 — auditoria dos IDs de mapas e reservas das outras regiões.
5. U05 — converter **um** mapa piloto e validar colisões/portais.
6. U06–U31 — reconstruir o restante, reescrever eventos, encontros, treinadores, áudio, traduções e pós-jogo.
7. U32 — integrar com Blue-Story na instalação principal, testar Windows/JoiPlay e regressão. Ver [plano de implementação detalhado](UNOVA_PLANO_IMPORTACAO_REGIAO_32_FASES.md).

## 10. Checklist de aceitação desta pesquisa

- [x] Comparar candidatos reais RMXP.
- [x] Identificar autor que publicou arquivos editáveis e permitiu uso de parte de sua obra (sem ampliar a autorização a terceiros).
- [x] Distinguir versão de Essentials e tipo de campanha de cada candidato.
- [x] Documentar fonte que **não** tem Unova pronta e rejeitá-la como doadora atual.
- [x] Documentar música/terceiros como itens **não autorizados por presunção**.
- [ ] Baixar, verificar SHA-256, abrir e catalogar o ZIP de Pokémon World V18.
- [ ] Conferir o arquivo Credits.txt e licenças originais de cada asset.
- [ ] Confirmar exatamente quais mapas, eventos, NPCs e músicas de Unova existem.
- [ ] Auditar uma cópia real do Decades instalada.
- [ ] Testar um mapa convertido em Game.exe isolado.
- [ ] Obter qualquer consentimento adicional necessário para publicar assets.

**Resultado atual:** CANDIDATE_IDENTIFIED_ONLY. **Unova continua não instalada, não jogável e sem qualquer aumento nas barras de progresso jogáveis.**
