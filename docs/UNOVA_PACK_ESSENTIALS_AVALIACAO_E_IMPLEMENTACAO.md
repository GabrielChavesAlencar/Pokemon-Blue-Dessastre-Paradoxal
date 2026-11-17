# Unova Pack para Pokémon Essentials — avaliação e plano de implementação

> **Projeto:** Pokémon Blue: Dessastre Paradoxal · **Data da pesquisa:** 17/11/2026
>
> **Status real:** PESQUISA CONCLUÍDA / RECURSOS NÃO INSTALADOS / FONTES BINÁRIAS NÃO AUDITADAS / UNOVA NÃO JOGÁVEL. Este MD não é autorização para importar trilhas, gráficos ou mapas de terceiros e não altera a distribuição do jogo.

## 1. Resposta: já usamos o Unova Pack?

**Não.** Os documentos e catálogos da main ainda não registram incorporação verificada do Unova Pack. No arquivo data/regions/unova-e06-e07-preparation.json, source_assets_imported = false; em data/regions/unova-u03-areas.json, o projeto-base é apenas um *candidato* Pokémon World V18, os source_map_id são null e o estado permanece planned. No registro site/public/data/regions.json, a região continua planejada. A pesquisa de fontes atual priorizava Pokémon World V18 para mapas parciais e não havia selecionado um pack de NPCs de Unova para incorporação.

**Importante:** o repositório é um editor/instalador; parte do Game.exe original/recursos Decades fica fora dele. A ausência de um pack do GitHub não prova a ausência desse pack numa instalação privada não anexada. Para validar a máquina do usuário, comparar os hashes e o inventário da instalação de origem quando houver acesso.

## 2. A palavra “Unova Pack” designa recursos distintos

### 2.1 Unova Pack antigo / Ultimate BW Pack 7 (2011–2012)

**Fonte:** https://www.pokecommunity.com/threads/ultimate-bw-pack-for-pok%C3%A9mon-essentials.270197/

O tópico do Ultimate BW Pack 7 (Pharetra/P-Sign e colaboradores) descreve um pacote para **Pokémon Essentials 7+**, com sprites animados Black/White, overworld sprites, ícones, cries, músicas, pokemon.txt com 649 espécies e moves.txt / abilities.txt com dados Gen 5. O próprio autor diz que os efeitos das novas habilidades e golpes **não funcionam** apenas com o PBS; a instalação histórica ordena **apagar Graphics/Battlers** e sobrescrever os diretórios **Audio, Graphics e PBS**. Comentários da época registram falta de tilesets/autotiles BW e sprites de treinadores.

**Avaliação atual:** NÃO importar o pacote inteiro. O Dessastre já parte de Essentials 21.1, regras recentes e conteúdo além de 649 espécies, com formas, Megas, Pokémon autorais, moves, IA e balanceamento. Sobrescrever PBS/Battlers/Scripts perderia conteúdo e poderia quebrar saves. Tratar o pack como **fonte histórica de referência** para comparar imagens e nomes, caso um arquivo específico ainda falte e direitos sejam suficientes. Áudio oficial de Black/White não ganha licença de redistribuição por existir no ZIP.

### 2.2 Gen 5 Overworld Pack 1.0 — Radical Raptr (2017)

**Fonte:** https://eeveeexpo.com/resources/25/

Pacote feito para trazer muitos sprites de treinadores/NPCs de Unova em folhas com alinhamento pronto para RMXP; o autor menciona objetos extras como árvore de Cut, pedras e buracos de Strength. Solicita crédito, incluindo Radical Raptr (compilação e alinhamento) e Spriter's Resource (rips).

**Nossa prioridade gráfica inicial:** ALTA. Bom para Cheren, Bianca, N, Ghetsis, Team Plasma e líderes, desde que o inventário de imagens realmente confirme quais existem, a escala corresponda ao Decades e as condições de uso/redistribuição sejam verificadas. É pack gráfico, **não mapa pronto**, **não evento de NPC**, **não diálogo**, **não música**.

### 2.3 ULTIMATE Gen 5 Overworlds Pack — PurpleZaffre (2021)

**Fonte:** https://eeveeexpo.com/resources/619/

O autor afirma ter compilado/alinhado quase 200 personagens de BW/B2W2, Pokémon não seguidores e objetos para RMXP. Pede crédito a PurpleZaffre e diz expressamente **“Please do not redistribute this anywhere else.”** Isso impede presumir que possamos espelhar ou empacotar o arquivo como recurso no Blue-Story; qualquer redistribuição específica que exceda o uso permitido na obra exige confirmação escrita. Os sprites oficiais ripados mantêm questões próprias de titularidade.

**Nossa avaliação:** COBERTURA GRÁFICA potencialmente alta, mas licença/rehost precisam de revisão especial. Usar apenas recursos apropriados com proveniência documentada; não hospedar pack original no GitHub, no site ou no pacote público.

### 2.4 Gen 5 Characters in Gen 4 OW style v2.0 — DiegoWT (2023)

**Fonte:** https://eeveeexpo.com/resources/370/

O autor descreve grande coleção de personagens Gen 5 recriados no estilo Gen 4 (listagem do Eevee Expo menciona 305 sprites), com variantes em quatro direções e animações especiais, incluindo personagens de Team Plasma e protagonistas. A atualização v2.0 completou personagens e revisou os sprites. Autor pede crédito e **não redistribuir o recurso em outros lugares**.

**Nossa avaliação:** BOM PLANO ALTERNATIVO se escolhermos estética Gen 4 para Unova ou precisarmos de animações específicas. Evitar misturar sprites de pixel density, perspectiva e altura divergentes no mesmo mapa. Não usar versões B2W2 para substituir, sem critério, as versões BW da campanha de Nuvema.

### 2.5 Pokémon World V18 (2022) — fonte de mapas parciais

**Fonte:** https://www.reddit.com/r/PokemonRMXP/comments/wsiyyr/

Projeto editável com mapas de múltiplas regiões, incluindo **parte** de Unova. Ainda é o primeiro candidato a ser auditado para geometrias de mapas, portais e eventos. Essentials v18 é antigo para nosso motor 21.1; mapas podem servir após remapeamento e reconstrução dos eventos, porém não basta copiar Data/.

**Nossa avaliação:** A fonte de **mapas** deve continuar independente da fonte de **sprites**. Cruzar mapa doador + sprites permitidos + eventos originais da história White. Nada disso substitui QA.

### 2.6 Pokémon World Project v21.1 e BW Kit de código

- https://eeveeexpo.com/resources/1877/ — Pokémon World Project 2.0 tem subsistemas multi-regionais em Essentials 21.1, mas informa **Unova = 0%**; não é fonte existente de mapas de Unova.
- https://github.com/Eronan/Essentials-BW/releases — Essentials BW Kit V3.2 é um kit/código legado, cuja própria release alerta para possíveis bugs. Não instalar por cima do motor Decades e não supor que contenha mapas completos.
- https://www.eeveeexpo.com/resources/569/ — Gen V Summary Pack DX tem scripts de interface direcionados ao Essentials v20.1, incompatibilidade potencial com v21.1; estética opcional somente em fase posterior, após port isolado.

## 3. Escolha por função

| Função | Primeiro candidato | Alternativa | Restrições |
|---|---|---|---|
| Mapas físicos de cidades/rotas | Pokémon World V18 (parcial) | Mapa original criado no editor com tiles permitidos | Verificar MapInfos, MapNNN, tilesets, portas, licença |
| NPCs e treinadores overworld | Radical Raptr Gen 5 OW Pack | PurpleZaffre ULTIMATE Gen 5 OW; DiegoWT se estética Gen 4 | Revisar autores/licença, altura, frames, direção, BW vs B2W2 |
| Sprites de Pokémon e dados PBS | **Manter Decades/Essentials v21.1 e geração atual** | Seleção pontual de recurso validado | Não importar pokemon.txt com 649 nem moves/abilities antigos |
| Gatilhos, diálogos e eventos B/W | **Construção própria por fases U07–U31** | Inspiração estrutural de eventos auditados, sob direitos | Flags locais, PT-BR, NPCs, N/Ghetsis, ginásios, save |
| Músicas | BlueMusic atual + fallbacks autorizados | Faixas originais/licenciadas específicas | Pack com OST oficial não autoriza redistribuição |
| Tilesets BW | Tiles autorais/licenciados auditados | Reconstituir mapas em tileset compatível | Ultimate BW Pack 7 NÃO entrega cidade inteira com tilesets/maps |
| UI Gen V | Nada na fase inicial | BW Summary Pack via port isolado | Não sobrescrever UX, plugins nem menus atuais |

**Decisão:** Não trocar o motor nem o inventário Pokémon por um pacote genérico antigo. Aproveitar a parte realmente vantajosa para Unova: **sprite sheets de NPCs RMXP**, na estética correta, e combinar separadamente com mapas auditados.

## 4. Plano técnico de implementação no projeto — SP01 a SP12

**Nenhum passo abaixo foi executado como importação nesta pesquisa.** O estado exige fontes reais e autorização antes de fazer staging público. Todo trabalho inicial fica em cópia local e scripts read-only.

### SP01 — Congelar baseline e registrar conflitos existentes

- Registrar commit da main, arquivos/shas do Blue-Story, status real das regiões já instaladas, PBS atuais, personagens existentes e lista de thumbnails.
- Criar cópia QA isolada do Game.exe, sem compartilhar saves; gravar hashes dos arquivos da base.
- Fazer lista de nomes já existentes: spritesheets, battlers, icons, cries, TMs, species, moves, abilities, trainers; registrar conflitos.

### SP02 — Obter packs com proveniência, separadamente

- Fonte de mapa: Pokémon World V18; fonte visual primária: Radical Raptr Gen 5 Overworld Pack.
- Outras fontes opcionais: PurpleZaffre (atenção a proibição de redistribuição), DiegoWT (estilo Gen 4), Ultimate BW Pack 7 (apenas referência histórica).
- Guardar arquivos privados em **.blue-work/unova/sources/<source-id>/** com URL, autor, versão, SHA-256, data e termos de uso.
- Não comitar ZIP, áudio comercial ou arte de terceiros. Não baixar/instalar automaticamente sem autorização e fonte confiável.

### SP03 — Auditorar PACOTE DE ASSETS (novo tipo)

- **Diferença crítica:** os auditores atuais E04/E05 assumem ZIP com **Data/MapInfos.rxdata** e **Data/Tilesets.rxdata**. Packs **só de sprites** podem não ter Data e serão bloqueados — corretamente — pelo auditor de mapas.
- Construir modo **asset_pack_only** dedicado: inventariar PNG/GIF (ou RAR validado se necessário), metadados de folha, direção/frame/offset, tamanho, transparência, animações, paths e hashes.
- Classificar arquivos como NPC/player/trainer/objects/battler/audio/PBS; não tentar convertê-los para MapNNN.
- Exigir lista de direitos por arquivo e os termos dos autores antes de habilitar distribuição.

### SP04 — Resolver padrão visual e selecionar personagens

- Selecionar **um padrão visual base** (OW BW original ou OW Gen 4), sem misturar aleatoriamente.
- Auditar 4 direções, linha de pé, pivô, sombra, passos, animações de bicicleta/corrida, sprite do jogador e proporção com NPCs do Decades.
- Priorizar: Juniper, Cheren, Bianca, N, Ghetsis, membros Plasma, oito ginásios (em White: Iris), Elite Four, Alder e NPCs genéricos.
- Criar planilha/manifesto de **NPC requerido → sprite → autor/licença → dimensões/quadros → estado**.
- Corrigir escalonamento visual sem alterar de forma global a escala do protagonista em Kanto/Decades.

### SP05 — Importar um único sprite piloto em QA

- Escolher sprite de um NPC BW **com uso permitido**, instalar com nome namespaced, como **UNOVA_NPC_CHEREN** (exemplo de namespace, não nome físico verificado).
- Não sobrescrever Graphics/Characters de outro jogo. Usar alias de assets separado para Unova e fallback permitido.
- Validar carga e todos os frames, movimento, direção, pivô, alpha, escala, Linux/Windows path case e JoiPlay.
- Comparar hash de antes/depois; nenhum outro mapa/asset deve mudar.

### SP06 — Crosswalk dos MAPAS reais (separado dos sprites)

- Usar o pipeline de auditoria já criado E04 → RXDATA → E05 → E06 para obter MapInfos/MapNNN e a matriz simbólica das **74 áreas**.
- Só aceitar IDs e dimensões vistos nos arquivos de origem.
- Cruzar nome, geometria, tileset, portas, eventos, conexões, licenças e roteiro BW (não B2W2).
- Mapas faltantes: criar ou reconstruir, nunca declarar “importado”. Não inventar IDs de origem/destino.

### SP07 — Preparar remap sem colisão

- Ler MapInfos real do Decades instalado e reservas de Kanto, Johto, Hoenn e Sinnoh; considerar scripts e overlays existentes.
- Reservar IDs de destino exclusivamente após o diagnóstico, com tabela original → destino.
- Validar todas as transferências/eventos/teleporte, nomes de áreas, tilesets e colisões; não substituir MapInfos inteiro nem CommonEvents.
- Manter mapa de origem, mapa de destino e SHA da base, com backup/rollback atômico.

### SP08 — Eventos e NPCs próprios da campanha White

- Criar sequência inicial Nuvema → Route 1 → Accumula com Juniper, Cheren, Bianca, Team Plasma e N, seguindo detonado.
- Converter a associação **sprite NPC → evento com condições → diálogo PT-BR → flag local → item/recompensa → destino real**.
- Seguir até oito ginásios (Striaton, Nacrene, Castelia, Nimbasa, Driftveil, Mistralton, Icirrus, Opelucid/Iris), Elite Four, Castelo de N, Zekrom, N/Ghetsis e pós-jogo.
- Não usar eventos do anime Fire Ash como substitutos dos arcos B/W e não misturar B2W2.
- Corrigir eventos RMXP antigos para APIs de Essentials v21.1; nunca executar scripts Ruby do doador sem revisão.

### SP09 — PBS, selvagens e balanceamento

- Manter espécies, golpes, habilidades, forms, itens, Megas, XP compartilhada e cap do Blue/Decades.
- Popular encontros e treinadores somente a partir de dados de slots e times **verificados**; aplicar evolução dinâmica e modos de dificuldade existentes.
- Não importar PBS genérico com só 649 espécies; nunca sobrescrever TM/HM global, dados de seguidores e itens regionais.

### SP10 — Áudio e interface

- Mapear chaves existentes do catálogo de **69 cues** para áreas/cenários/chefes White, com fallback BlueMusic.
- Só distribuir novas faixas com direitos comprovados (composição/licença própria ou permissões específicas). OST comercial contida em pack histórico não vira asset liberado.
- UI Black/White é opcional e não pode substituir menus de outras regiões; fazer testes isolados de tela e performance antes de considerar um port v20.1→v21.1.

### SP11 — Integrar com progressão e Blue-Story, condicionado a gates

- **Região Unova permanece “Em preparação”** até Nuvema, spawn, sprites, portais e roteiro mínimo estarem instalados/testados no Game.exe principal.
- Adicionar Agente Regional em Nuvema, usando assinatura Essentials v21.1 e coordenadas reais; viagem por conversa desde início para regiões efetivamente instaladas.
- HMs/itens-chave e insígnias locais; esmeraldas únicas, travas de Pokémon especiais, Centro Pokémon local em blackout; não reabrir seleção de personagem do Decades ao viajar.
- Blue-Story deve instalar overlay **apenas de conteúdo que pode ser distribuído**, com manifesto, hashes, atualização incremental, backup e rollback; nunca baixar/resdistribuir sprites não autorizados em silêncio.

### SP12 — Testes e aceite honesto

- **Sintéticos/CI:** integridade dos manifests, hashes, license gates, MapID únicos, namespacing, fallback, deformação de sprites, versões v21.1, regressões das outras regiões.
- **Nativo Windows Game.exe:** movimento/escala de NPC piloto, quatro direções, cena Nuvema, eventos/placas PT-BR, save/reload, batalha, transferência, blackout e agente.
- **Android JoiPlay:** spritesheets e formatos, case sensitivity, escala, atualização incremental, batalhas, transferência e save.
- **Regressão:** Decades/Kanto/Johto/Hoenn/Sinnoh não mudam indevidamente; arquivos/IDs que não constam no manifesto de overlay mantêm hash idêntico.
- Não aprovar conteúdo jogável apenas porque o CI de Python/Ruby passou.

## 5. Dependências e risco específico do nosso projeto

| Risco | Consequência | Regra de proteção |
|---|---|---|
| Seguir o “apague Graphics/Battlers” do pack de 2012 | Perda dos sprites atuais e formas autorais | **Proibido**; importar somente arquivo individual autorizado |
| Copiar pokemon.txt com 649 Pokémon | Sobrescrever 1–9ª gerações e Dex autoral | **Proibido**; manter PBS atual |
| Copiar Scripts.rxdata de versão antiga | Quebrar Essentials v21.1, batalha, save e viagem | **Proibido**; portar partes auditadas para plugin isolado se necessário |
| Usar MapID de pacote como destino | Colisão com outras regiões | Remap após MapInfos real |
| Misturar BW com B2W2 | Ginásios, NPCs e eventos cronologicamente incorretos | Política White primeiro; B2W2 futuro |
| Copiar sprites sem verificar dimensões | Player maior que NPC / frames saltando | Testes específicos de pivô, escala, walking/cycling |
| Achar que crédito equivale a licença | Redistribuição sem direitos | Aprovação individual; não hospedar packs sem autorização |
| Presumir que pack inclui cidades e eventos | Conteúdo falso no portal e instalador | Marcar status por recurso; mapas e história auditados separadamente |

## 6. Integração com o plano anterior e barras

Este documento é adendo aos planos [UNOVA_PLANO_IMPORTACAO_REGIAO_32_FASES.md](UNOVA_PLANO_IMPORTACAO_REGIAO_32_FASES.md) e [UNOVA_PESQUISA_FONTES_RMXP.md](UNOVA_PESQUISA_FONTES_RMXP.md).

- SP01–SP05 complementam **U01–U06** (fontes, assets e ambiente piloto).
- SP06–SP07 correspondem a **U02–U05**, com MapInfos/remap reais.
- SP08–SP10 alimentam **U07–U31**, reconstruindo história, mecânica e pós-jogo.
- SP11–SP12 correspondem a **U32** de integração, QA e Windows/JoiPlay.

**Barras permanecem inalteradas nesta pesquisa:** A 0/8, B 0/8, C 0/8, D 0/8, E 4/8. Fases jogáveis de Unova aceitas: 0/32. Adicionar o nome de um pacote a este documento não significa asset instalado, mapa utilizável ou autorização legal.

## 7. Ordem prática recomendada

1. **Não instalar Ultimate BW Pack 7 inteiro.** Ele é redundante para PBS e perigoso para o motor atual.
2. Auditar primeiro **Radical Raptr / Gen 5 Overworld Pack** como possível fonte de NPCs; conferir licença/atribuição e a adequação da estética.
3. Comparar cobertura e termos com **PurpleZaffre** e **DiegoWT**, sem redistribuir seus packs; escolher uma estética base.
4. Fazer auditor **asset_pack_only** para sprites (PNG/GIF), pois o auditor atual de Pokémon World requer MapInfos e não serve para ZIPs gráficos.
5. Adicionar **um NPC piloto em QA**; testar frames, tamanho, posicionamento e transições.
6. Continuar o programa de mapas/E04–E06 com Pokémon World V18 e só planejar remap/integração depois de fonte real e direitos.

### Referências primárias

- Ultimate BW Pack 7 — https://www.pokecommunity.com/threads/ultimate-bw-pack-for-pok%C3%A9mon-essentials.270197/
- Gen 5 Overworld Pack — https://eeveeexpo.com/resources/25/
- ULTIMATE Gen 5 Overworlds Pack — https://eeveeexpo.com/resources/619/
- DiegoWT Gen 5 Characters OW v2.0 — https://eeveeexpo.com/resources/370/
- Pokémon World V18 — https://www.reddit.com/r/PokemonRMXP/comments/wsiyyr/
- Pokémon World Project — https://eeveeexpo.com/resources/1877/
- BW Essentials Kit — https://github.com/Eronan/Essentials-BW/releases
- Gen V Summary Pack v20.1 — https://www.eeveeexpo.com/resources/569/

**Nenhum pacote foi baixado, instalado ou confirmado como licenciado por esta entrega.**
