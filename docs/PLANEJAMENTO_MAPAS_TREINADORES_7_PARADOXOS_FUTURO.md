# Distribuição planejada — 7 Paradoxos futuros no mapa e nos treinadores

**Escopo desta etapa:** apenas Pokédex e simuladores do portal `site/`. O pacote do jogo (`game/`), o instalador `INSTALAR_JOGO.bat`, os arquivos PBS e saves permanecem intocados.

## Encontros selvagens planejados

Cada espécie tem exatamente **5% dos encontros do método indicado** nas **10 variações** da área. Essa porcentagem não é chance de captura nem taxa de encontros ao caminhar. Os níveis do site são herdados da tabela original da área: algumas áreas de Beatha usam níveis de referência 1, escalonados pela engine. Isso **não valida** níveis para a futura implementação.

| Paradoxo | Área | ID do mapa | Método PBS | Chance | Justificativa |
|---|---|---:|---|---:|---|
| Iron Oracle (Claydol) | Desert Zone | 175 | Land | 5% | Areia, ruínas e fenômenos psíquicos; mantém a afinidade Terra/Psíquico |
| Iron Coil (Furret) | Iron City | 129 | Land | 5% | Infraestrutura industrial adequada ao corpo metálico segmentado |
| Iron Echo (Exploud) | Circuit City | 119 | Land | 5% | Circuitos elétricos e equipamentos acústicos combinam com seus amplificadores |
| Iron Glimmer (Lumineon) | Seafloor Zone | 184 | Land | 5% | Habitat submarino e nadadeiras holográficas; a engine chama a tabela desta zona submersa de Land |
| Iron Wraith (Spiritomb) | Stygian Cave | 159 | Land | 5% | Caverna sombria e reator espiritual digital |
| Iron Raptor (Swellow) | Stratos Horizon | 171 | Land | 5% | Penhascos, correntes de ar e caça aérea |
| Iron Stinger (Yanmega) | Cloakfall Forest | 82 | Land | 5% | Floresta fechada apropriada para emboscadas de libélula |

As porcentagens são redistribuídas apenas entre as espécies comuns do mesmo método. O sistema mantém os 5% dos Paradoxos anteriores e os 5% ou 20% das formas regionais do Eevee já exibidos. Outros métodos e outras áreas não são alterados. Cada método permanece com soma de 100%, inclusive após recarregar a Pokédex.

## Treinadores — prévia de equipe Master

As sete adições são feitas somente na **prévia Master** do portal para não introduzir Pokémon com 570 BST nas faixas Inicial, Intermediário ou Avançado, que têm limites de 350, 450 e 540 BST. O nível de exibição permanece em **90% do maior nível do jogador**, conforme a prévia existente; os quatro movimentos são derivados do learnset proposto disponível até aquele nível. Não se trata de alteração dos times reais no jogo.

| Paradoxo futuro | Treinador existente | Área do treinador | Justificativa |
|---|---|---|---|
| Iron Oracle | Sachiko (Medium) | Mantic City | Médium que estuda forças psíquicas e relíquias |
| Iron Coil | Layton (Chaser Man) | Iron City | Ambiente industrial e equipe com Magnezone |
| Iron Echo | Ball Guy | Circuit City | Afinidade tecnológica e elétrica |
| Iron Glimmer | Lester (Bellhop) | Shimmer Coast City | Próximo à região costeira do Pokémon aquático |
| Iron Wraith | Ume (Hex Maniac) | Route 15 | Treinadora associada a aparições perto de Revenant |
| Iron Raptor | Julia (Veteran Woman) | Stratos City | Veterana de uma região de altitude |
| Iron Stinger | Dean (Bug Maniac) | Apterygota City | Especialista em insetos que já usa Yanmega |

O site preserva integralmente os times do PBS original. Nenhum treinador recebe mais de seis Pokémon na prévia. A presença de cada Paradoxo é marcada como **planejada**, não como membro confirmado do time real.

## Arquivos de implementação do portal

- `site/public/data/future-iron-placements.json`: fonte autoral de distribuição e justificativas; acrescenta registros *somente* na camada de apresentação do site.
- `site/src/assets/future-iron.js`: mesclagem idempotente e validação de 5%/100%, preservação dos encontros existentes e identificação de treinadores.
- `site/src/assets/data.js`: aplica os planejamentos quando carrega o portal; preserva os arquivos de exportação originais.
- `site/src/assets/views.js`, `site/src/assets/regular-trainers.js`, `site/src/assets/story.js`, `site/src/assets/detail.js`: mapas, equipes e Pokédex com avisos explícitos.
- `site/tests/future-iron-placements.test.mjs`: regressão para encontros e times, inclusive todas as versões dos mapas.

## Pendências para a implementação futura no jogo

Confirmar as quatro tipagens ainda propostas (Iron Coil, Echo, Glimmer e Wraith), compatibilidade de golpes e da habilidade Quark Drive no PBS, método de encontros submersos do Seafloor Zone, requisitos de história e level caps. A instalação deve ser feita com backup e testes no Game.exe/JoiPlay, sem sobrepor o Pokémon original nem alterar saves.
