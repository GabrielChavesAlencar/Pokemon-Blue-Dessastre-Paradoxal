# História, mapas e equipes do Pokémon Blue

## Páginas públicas

- `/historia`: missão central, Beatha, objetivos confirmados, 18 Type Masters, Zenith Domain e dicas.
- `/chefes`: os 18 Type Masters e o chefe final Danny. Cada ficha oferece 1v1/2v2/3v3 em Basic Power ou Full Power, quando presente no PBS original.
- `/localizacoes`: prioriza imagem específica quando verificada; caso haja coordenada do local, mostra **recorte regional ampliado específico daquela área**, em vez de repetir Beatha inteira; se não houver imagem nem coordenada, avisa que a imagem ainda não está disponível. **Recortes regionais não são capturas dos mapas internos do RPG Maker XP**.

## Fonte e integridade

Os times vêm do arquivo público de referência `PBS/trainers_story_mode.txt` do jogo original, não foram inventados:
https://github.com/HazyCrazy/Pokemon-Decades/blob/main/PBS/trainers_story_mode.txt

O mapa oficial e as esmeraldas vêm de `Graphics/UI/Town Map/Regions/mapRegion0.png` e `Graphics/Pictures/*Emerald.png`, hospedados no GitHub original:
https://github.com/HazyCrazy/Pokemon-Decades

Referências textuais: https://www.pokecommunity.com/threads/pokemon-decades.540970/ e https://eeveeexpo.com/threads/9341/

**Não é garantida uma Elite Four clássica como parte da campanha Decades.** O jogo original destaca 18 Type Masters e um Final Boss, além de mencionar um Super Boss. Os times do Super Boss dependem de importar `trainers_battle_mode.txt` e ainda não foram confirmados nessa primeira extração. Não apresentamos rotas de quests inventadas ou condições de desbloqueio que exijam ler eventos `.rxdata`.

## Atualização dos times quando o Blue Studio mudar

Os dados públicos ficam em `site/public/data/story-trainers.json` e `site/public/data/region-points.json`.
O comando `python scripts/export_site_data.py` também executa `scripts/export_story_teams.py` quando `game/PBS/trainers_story_mode.txt` existir. Ele atualiza as equipes correspondentes e marca cada variante atualizada com `origin: blue-pbs`. As variantes não encontradas permanecem como referência original.

Comandos na raiz do projeto:

```bat
python scripts/export_site_data.py
npm test --prefix site
npm run build --prefix site
git add site/public/data
git commit -m "docs: sincronizar Historia e equipes do Blue"
git push origin main
```

A pasta `game/` é local e ignorada pelo Git. O servidor não pode ver alterações em PBS não exportadas. O build do Vercel lê apenas os arquivos publicados.

## Próxima etapa para imagens individuais

Para mostrar o mapa interno real de cada cidade ou caverna, exporte renderizações PNG dos arquivos `Data/MapNNN.rxdata` a partir do projeto local com seus respectivos tilesets e autotiles. A imagem regional oficial usada agora **não é** uma renderização do mapa de cada área.

## Testes

`site/tests/story.test.mjs` valida os 18 Type Masters, as seis variantes de cada mestre, o boss final, as imagens regionais e a apresentação dos times. O workflow `site-checks.yml` executa os testes e o build.


## Pesquisa de imagens reais de cada mapa — 31/10/2026

Pesquisados o repositório público do Decades, seus arquivos de UI/Town Map, os dois fóruns oficiais e resultados de busca específicos por nome de localização. **Não foi localizada uma coleção de capturas reais para cada mapa interno.** A pasta de minimapas do Decades contém apenas `mapLappetTown.png` (repetida em temas diferentes), e os outros recursos públicos encontrados não são identificados como capturas das 155 localizações.

A prioridade visual atual é:

1. **Imagem comprovada de uma área:** `site/public/data/region-points.json > areaImages[ID]`. Neste momento, Lappet Town (área 2) usa a miniatura específica encontrada no repositório público do Decades.
2. **Recorte do mapa regional:** nas outras áreas com correspondência entre nome e coordenadas de `PBS/town_map.txt`, a interface aproxima somente o trecho da região associado ao local. Há correspondência para 141 de 155 registros de localizações (alguns registros possuem nomes repetidos).
3. **Ausência de imagem confiável:** as demais áreas recebem um placeholder descritivo. Por exemplo, Rock Cave 1F (área 49) **não exibe mais o mesmo mapa inteiro de Beatha**, pois não há miniatura ou coordenada individual verificada.

Essas imagens não devem ser apresentadas como capturas do cenário interno de jogo, e o site faz essa distinção em sua legenda.

### Substituir um recorte por uma imagem verdadeira

Adicione a imagem autorizada, por exemplo, em `site/public/assets/maps/49.png` e registre no `site/public/data/region-points.json`:

```json
{
  "areaImages": {
    "49": {
      "src": "/assets/maps/49.png",
      "kind": "screenshot",
      "source": "Descrição ou URL da fonte original",
      "credit": "Imagem real do mapa Rock Cave 1F, exportada do Blue Studio"
    }
  }
}
```

**Atenção:** o trecho é apenas ilustrativo: não substitua todos os demais campos de `region-points.json` por este objeto. Acrescente a propriedade em `areaImages` já existente. O identificador da imagem precisa corresponder a `locations.json > locations[].id`. Para uma renderização fiel do RPG Maker XP, a exportação tem que ler o mapa de `Data/MapNNN.rxdata` e os tilesets/autotiles correspondentes, ou partir de uma captura real do jogo. Não use imagens de outros jogos por similaridade do nome.

Fontes da pesquisa:
- https://github.com/HazyCrazy/Pokemon-Decades/tree/main/Graphics/UI/Town%20Map/UI/Default/LocationPreview/MiniMaps
- https://github.com/HazyCrazy/Pokemon-Decades/blob/main/PBS/town_map.txt
- https://www.pokecommunity.com/threads/pokemon-decades.540970/
- https://eeveeexpo.com/threads/9341/

### Validação

`site/tests/story.test.mjs` verifica o recorte único por área com coordenadas, o minimapa de Lappet, a ausência de mapa inventado em Rock Cave e a cobertura dos registros. Ao final de `npm test --prefix site` e `npm run build --prefix site`, faça `git push origin main` para atualizar o deploy da Vercel.
