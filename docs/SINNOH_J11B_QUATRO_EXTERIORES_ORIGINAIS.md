# Sinnoh J11-B — quatro exteriores originais e nove geometrias isoladas

Base: J11 / PR #245 integrado com 15/15 checks. Continuação da issue #241.

## O que esta fase efetivamente cria

A ferramenta \`scripts/regions/generate_sinnoh_four_exteriors_j11b.py\` pinta quatro novos ambientes em código Python, sem utilizar imagens, mapas ou arquivos ZIP dos jogos oficiais. O desenho geométrico também não replica a planta de Pokémon Diamond/Pearl: as disposições de praças, casas, rotas, jardins e curvas são escolhas originais, passíveis de revisão humana. Não há atribuição falsa de desenho humano.

| Símbolo | Dimensões | Layout proposto (não final) |
| --- | ---: | --- |
| SINNOH_TWINLEAF_TOWN | 44×34 | Bairro original em cruz, praça central, quatro edificações, acessos laterais |
| SINNOH_ROUTE_201 | 50×24 | Trilha leste-oeste curvilínea, bosque e lago secundário no norte |
| SINNOH_SANDGEM_TOWN | 46×34 | Praça alongada, avenida central, quatro edifícios e vias de ligação |
| SINNOH_ROUTE_202 | 36×46 | Trilho sinuoso sul-norte, arvoredo, pedras, água lateral e cercas |

As quatro geometrias foram escritas como três camadas explícitas de tiles, serializadas em **RPG::Map Ruby Marshal RXDATA reais**, com nenhum evento do doador. O tileset exterior **ExteriorJ11B.png** (256×256, 32 desenhos 32×32) é criado pixel a pixel em Python, com uma paleta própria diferente do **OriginalJ10A.png** dos cinco ambientes anteriores.

O script reúne **nove** RXDATA originais no mesmo bundle de design **privado e não instalável**: cinco da J10-A, byte a byte idênticos à geração anterior, mais quatro novos. Nunca importa os quatro mapas exteriores históricos do B00; as referências e licenças incertas permanecem em suas auditorias anteriores, apenas sem uso na alternativa original J11-B.

## Executar offline sem instalação

Só auditar e visualizar hashes em memória:

    python scripts/regions/generate_sinnoh_four_exteriors_j11b.py

Criar bundle de design pela primeira vez em cópia de trabalho isolada:

    python scripts/regions/generate_sinnoh_four_exteriors_j11b.py --build

O modo build só escreve uma pasta nova (não pode sobrescrever):

    .blue-work/sinnoh-j11b-nine-original-designs/
      ExteriorJ11B.png
      OriginalJ10A.png
      SINNOH_*.rxdata                # nove mapas, ainda não instaláveis
      previews/SINNOH_*.svg         # nove vistas esquemáticas
      tileset-registration-proposal.json
      nine-map-source-plan.json
      manifest.json

Todos os arquivos são conferidos contra hashes SHA-256. Em GitHub Actions, os RXDATA e PNG são gerados e testados em runner efêmero; o artifact público inclui **somente** nove SVG e três JSON, sem arquivos privados binários. O relatório contém hashes/metadata, não as imagens em si.

Um iniciador opcional \`SINNOH_J11B_GERAR_NOVE_PRIVADOS.bat\` gera o mesmo diretório em uma cópia local quando explicitamente executado; esta fase não acessou o PC, os saves pessoais ou a instalação principal.

## Preparação de Tilesets e passabilidade

\`tileset-registration-proposal.json\` registra dois grupos de tiles (J10A_INTERIORS e J11B_EXTERIORS), SHA-256 dos PNGs, lista de 32 tiles cada, máscara de passagem **apenas hipotética** e prioridade **apenas sugerida**. O motor exige dois RPG::Tileset distintos, com IDs genuínos extraídos de \`Tilesets.rxdata\` da cópia QA, cuja autorização/mapa ainda está ausente. **Ambos os tipos de RXDATA ainda possuem \`@tileset_id=1\` PROVISÓRIO**; NUNCA os instale assim, pois desenhariam com tilesets incorretos. Remapeamento de tile ID/tileset/entradas, prioridade, terreno, comportamento da água e autotiles depende de revisão do motor.

As entradas/saídas são \`edge_candidates\` desenhadas, verificadas por BFS em terreno hipoteticamente transitável. NÃO são coordenadas de transferência/evento e não substituem testes com os masks reais \`@passages\` e prioridades \`@priorities\`.

## R07 / R08 / R09 — fail-closed

- R07: o \`nine-map-source-plan.json\` deixa todos os MapIDs nulos, com 0 IDs atribuídos. Sem baseline MapInfos real, o script não sugere números como se estivessem livres. Uma análise opcional somente de leitura usa o validador \`j11.check_r07\` com \`--r07-baseline .blue-work/sinnoh-j11-baseline/Data\` e \`--r07-review .blue-work/sinnoh-j11-reviews/r07.json\`, **apenas quando esses arquivos genuínos já existirem**. Nenhum atestado local é transformado em aprovação independente.
- R08: os novos layouts e imagens são produzidos por código, mas a revisão humana de procedência e autorização do projeto ainda está pendente; nenhum atestado é inventado. Para recursos externos adicionais, exigir licença/evidência particular antes de importação.
- R09: J12/43 casos reais Windows e 1 Android JoiPlay **não foram executados**. As suítes GitHub Actions são testes de integridade e código, não gameplay nativo.

Próxima integração autorizada: revisar visualmente as nove geometrias e os PNG; reservar nove MapIDs reais; registrar dois Tilesets nativos; remapear em cópia QA isolada; conferir passagens, prioridades, água e colisões; definir posições reais de 16 portais, cinco NPCs, três Poké Bolas; compilar eventos J04 e overlay J06. Só então executar 43+1 QA nativa J12. O binder J02 e J09 foram construídos com referências históricas e precisam ser adaptados de maneira segura a uma nova proveniência alternativa, sem marcar as quatro fontes B00 como aprovadas.

**O projeto permanece \`PILOT_NOT_INSTALLED_NOT_PLAYABLE\`**, 0/9 mapas instalados, 0/44 testes nativos, R07/R08/R09 pendentes. Decades, Kanto, Johto, Hoenn, Game.exe, Android e saves não foram modificados.

### Regressões

    python -m unittest discover -s tests -p test_sinnoh_j11b_four_original_exteriors.py -v

40 testes positivos e negativos validam integridade, nove mapas distintos, 3 layers, verificação de PNG e previews, colisões potenciais, direitos não atestados, propostas de tilesets não instaláveis, entradas bloqueadas, bytes corrompidos e isolamento de arquivos privados. CI também regressa J10-A e J11 e valida site.
