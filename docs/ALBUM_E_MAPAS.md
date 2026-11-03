# Álbum de Treinadores e mapas da Habitat Dex

Na campanha, abra **Pausa → Álbum de Treinadores**, entre o cartão do jogador e as missões. O álbum apresenta até 12 NPCs por página. Antes do primeiro confronto, aparecem a silhueta preta e `???`. Carregar a batalha revela o retrato; perder não registra vitória. Cancelar antes de carregar não revela o NPC.

O catálogo é extraído dos eventos atuais `Trainer NPC`, sem executar scripts nem alterar mapas. Inclui as variantes estáticas do mesmo evento e exclui os mestres de tipo e o treinador de teste. A primeira versão contém 61 NPCs em 38 áreas. Áreas visitadas ou com confrontos registrados ficam disponíveis na lista.

Ao vencer todos os NPCs cadastrados de uma área, o jogador recebe **33% da soma do dinheiro efetivamente recebido nas primeiras vitórias**, arredondado para baixo. Multiplicadores nativos, como Happy Hour, entram pelo valor recebido; revanches continuam pagando o prêmio normal, mas não aumentam o álbum nem repetem o bônus. Em confrontos com dois treinadores, o valor recebido é repartido proporcionalmente ao prêmio nativo de cada um. Se a carteira estiver cheia, o bônus fica pendente para **Coletar prêmio**.

Vitórias antigas só são reconhecidas quando há um registro inequívoco no histórico Blue ou uma chave de vitória explícita do evento. A base não registrava todos os confrontos antigos; esses não podem ser reconstruídos. Valores antigos não são estimados: o cálculo usa exclusivamente o dinheiro registrado a partir desta atualização, conforme a preferência do usuário. Progresso e prêmio recebido ficam no save da campanha. O Hub e o laboratório permanecem isolados desse save.

## Mapas e Pokédex

- A Habitat Dex mostra **12 Pokémon por página**, em quatro colunas e três linhas, mantendo nomes desconhecidos ocultos, estado visto/capturado, varas e navegação por mouse/teclado.
- O mapa do Pokégear inclui a região atual mesmo quando um save antigo não tem marcações de mapas visitados. Interiores podem usar a posição do mapa pai. A correção não concede destinos de Fly nem marca rotas como visitadas.
- Ammnoid recebe um quadro de costas normalizado em memória antes de a animação aplicar seus movimentos. Isso corrige a inversão durante golpes e efeitos, inclusive no segundo espaço aliado em duplas. Os arquivos de arte permanecem preservados.

## Capturas para o site

As páginas de localização usam capturas do **mesmo renderizador da Habitat Dex**, com zoom de 3×, marcador dourado do habitat e sem marcador do jogador. São recortes do mapa regional; não são fotografias do cenário interno de cada rota. Mapas diferentes podem ocupar a mesma posição regional quando a própria engine os associa ao mesmo ponto.

Há 137 mapas atuais com captura. As 18 áreas antigas cujos arquivos de mapa não existem na instalação atual ficam ocultas na lista e nos guias gerados, sem apagar os registros brutos. A associação das imagens usa o ID real de mapa, evitando confundir versões antigas e atuais das Rotas 1–8.

Para regenerar depois de mudar os mapas da instalação:

```powershell
python scripts/export_route_photos.py --prepare
python scripts/battle_lab/launch.py --prepare-only --smoke-test
# Abrir game/Game.exe imediatamente. A prova nativa exporta as capturas.
python scripts/export_route_photos.py
python scripts/launch_game.py --prepare-only
cd site
npm test
npm run build
```

`game/Data/blue-world-validation.txt` registra as provas nativas de abertura do Pokégear, grade 4×3, animações, recebimento real de dinheiro, persistência do álbum e capturas. A execução usa jogador temporário e bloqueia leitura/escrita de saves da campanha. Publicam-se apenas as capturas renderizadas e os scripts próprios; os mapas e binários originais do jogo ficam locais.
