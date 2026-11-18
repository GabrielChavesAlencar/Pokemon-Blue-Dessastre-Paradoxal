# Sinnoh J10 — criação original dos cinco mapas faltantes

**Base:** J09 integrada no PR #239. Issue [J10 #240](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/240), próxima etapa [J11 #241](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/241).

## Estado real

O ZIP privado Pokémon World V18 contém apenas quatro mapas exteriores com terreno de abertura: Twinleaf Map209, Route 201 Map227, Sandgem Map210 e Route 202 Map228. Cinco locais reais ainda faltam. Os placeholders de lago, interiores e laboratório não são mapas jogáveis, e a licença do conteúdo do doador não foi comprovada.

A J10 implementa a ferramenta de autoria, não gera desenhos falsos. Ferramenta pronta NÃO significa cinco mapas concluídos, nove mapas instalados ou Sinnoh jogável.

## Editor local

Execute SINNOH_J10_EDITOR_MAPAS.bat na raiz do projeto no Windows com Python 3. Ele abre http://127.0.0.1:8772/sinnoh-j10-map-editor.html e só serve o HTML da interface por loopback. Não publica dados, não aceita uploads POST, não acessa Game.exe nem saves. Feche o CMD para encerrar.

Arquivos:
- web/sinnoh-j10-map-editor.html — editor manual de cinco ambientes, três camadas RMXP, pincel, paleta de tiles 32×32 de PNG próprio/licenciado, desfazer, seleção de camadas, importação e exportação local em JSON.
- scripts/regions/serve_sinnoh_j10_editor.py — servidor local somente HTTP 127.0.0.1, sem acesso à rede externa e sem escrita de dados.
- scripts/regions/author_sinnoh_playable_j10.py — importação dos cinco desenhos privados, verificação da geometria/PNG, geração RMXP atômica e auditoria estrutural J09.

**Não se atribuem dimensões, coordenadas, eventos, MapIDs ou layouts canônicos automaticamente**: cada pessoa autora desenha a planta a partir de referências próprias/autorizadas. Não use PNG com licença desconhecida.

## Desenhar e exportar cinco originais

1. Carregue um tileset PNG com largura 256 px e altura múltipla de 32 px, original ou licenciado. O editor calcula seu SHA. Guarde cópia com o mesmo nome em .blue-work/sinnoh-j10-tilesets/.
2. Desenhe o chão e mais duas camadas; mínimo 60% de cobertura da camada chão, 70% da área coberta, quatro tiles não nulos na camada 2 ou 3, quatro IDs distintos. Esses limites evitam placeholders óbvios, mas não provam fidelidade visual, passabilidade ou boa jogabilidade.
3. Preencha referência de autoria e direitos e marque confirmação de revisão apenas se verdadeira. Exporte o JSON, mova-o para .blue-work/sinnoh-j10-drafts/.
4. Faça isso para todos os cinco JSON, com nome exato:
   - SINNOH_PLAYER_BEDROOM.json
   - SINNOH_PLAYER_HOUSE_1F.json
   - SINNOH_BARRY_HOUSE.json
   - SINNOH_LAKE_VERITY.json
   - SINNOH_PROFESSOR_ROWAN_LABORATORY.json
5. Pré-voo somente leitura: py -3 scripts\regions\author_sinnoh_playable_j10.py
6. Só após os cinco desenhos físicos realmente concluídos: py -3 scripts\regions\author_sinnoh_playable_j10.py --build

O compilador exige SHA do tileset PNG existente e referências de autoria/revisão humana. Rejeita: tile IDs fora do PNG, menos de três camadas, mapas em branco ou uniformes, duplicados, conteúdo com eventos/scripts de terceiros, destinos MapID presumidos, symlinks, direitos ausentes e falsa aprovação de jogabilidade. Usa estrutura RPG Maker XP RPG::Map e uma tabela Table 3D; o auditor J09 relê os RXDATA para verificar integridade.

Somente quando todos os cinco forem válidos, cria de forma atômica, uma única vez e **sem sobrescrita**, exatamente:
- .blue-work/sinnoh-j09-authored/SINNOH_PLAYER_BEDROOM.rxdata
- .blue-work/sinnoh-j09-authored/SINNOH_PLAYER_HOUSE_1F.rxdata
- .blue-work/sinnoh-j09-authored/SINNOH_BARRY_HOUSE.rxdata
- .blue-work/sinnoh-j09-authored/SINNOH_LAKE_VERITY.rxdata
- .blue-work/sinnoh-j09-authored/SINNOH_PROFESSOR_ROWAN_LABORATORY.rxdata

Nenhum RXDATA privado é enviado ao GitHub, nenhum mapa é inserido em game/Data, nenhuma ID é reservada e nenhum save é acessado. Os arquivos são **fontes originais privadas ainda não validadas** para a próxima etapa, não mapa jogável.

## J11 — requisitos para futura integração física

Antes de usar qualquer um: verificar direitos dos nove mapas, PNGs e tilesets e autorização de uso (R08), existência e passagem do tileset em Tilesets.rxdata, coordenadas/portais só depois de desenhados, MapInfos real e R07 contra Decades/Kanto/Johto/Hoenn/Unova. J03/J04 devem compilar 16 portais, cinco NPCs e três bolas somente em QA isolada. J07 exige 43 casos Windows nativos e J08 o caso JoiPlay real, com revisão humana R09.

O CI J10 roda 35 testes **sintéticos**, nenhum é execução de Game.exe/JoiPlay. A barra original de engenharia J01–J08 permanece 8/8; jogabilidade Sinnoh 0/8, 0/9 mapas instalados, 0/44 QA real. **Não declarar cinco mapas prontos antes de receber cinco desenhos reais.**
