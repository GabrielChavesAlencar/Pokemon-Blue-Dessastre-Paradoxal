# História, mapas e equipes do Pokémon Blue

## Páginas públicas

- `/historia`: missão central, Beatha, objetivos confirmados, 18 Type Masters, Zenith Domain e dicas.
- `/chefes`: os 18 Type Masters e o chefe final Danny. Cada ficha oferece 1v1/2v2/3v3 em Basic Power ou Full Power, quando presente no PBS original.
- `/localizacoes`: imagem do mapa regional oficial de Beatha nas listagens e detalhes. Coordenadas extraídas do `town_map.txt` quando há correspondência exata. **Não são capturas dos mapas internos do RPG Maker XP**.

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
