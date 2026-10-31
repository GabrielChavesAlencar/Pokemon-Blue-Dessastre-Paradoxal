# Guias Pokémon Decades integrados ao Blue

## Objetivo e fontes

A seção `/guias` usa os anúncios originais de Pokémon Decades para orientar jogadores do Blue, com artigos próprios sobre Beatha, 18 Type Masters/Type Emeralds, escolha de iniciais, Battle Paradise, ferramentas de treinador e mecânicas de batalha.

Fontes:
- https://www.pokecommunity.com/threads/pokemon-decades.540970/
- https://eeveeexpo.com/threads/9341/

A campanha do Blue deriva de Decades, mas as informações originais são rotuladas **Referência do Pokémon Decades**. Elas não garantem que uma funcionalidade continue disponível no Blue, já que scripts e progressão podem mudar. Os textos são resumos com atribuição e links, não cópias integrais dos fóruns.

## Como os guias se atualizam

1. `site/public/data/guides.json` mantém os seis guias editoriais originais.
2. `site/scripts/guides.mjs` integra guias do Decades, recalcula os totais das espécies, Megas, Paradoxos, pendências e encontros, e acrescenta seções atualizadas aos artigos antigos.
3. `site/scripts/build.mjs` lê `site/public/data/catalog.json`, `details.json`, `locations.json` e `guides.json`, gerando `site/dist/data/guides.json` em cada build.
4. `site/src/assets/views.js` identifica visualmente os artigos sincronizados e mostra links internos e fontes.
5. Alterações publicadas na `main` disparam o build da Vercel, desde que a integração GitHub/Vercel esteja habilitada.

O arquivo original `site/public/data/guides.json` não é sobrescrito. Os dados calculados são reconstruídos no diretório `dist/`, em cada publicação.

### Depois de modificar Pokémon, golpes ou encontros no Blue Studio

O editor salva os PBS em `game/`, uma pasta local ignorada pelo Git. **O servidor público não consegue ler alterações locais sem exportação.** Na raiz do projeto, execute:

```bat
python scripts/export_site_data.py
npm test --prefix site
npm run build --prefix site
git add site/public/data/catalog.json site/public/data/details.json site/public/data/locations.json
git commit -m "docs: sincronizar dados do Blue com os guias"
git push origin main
```

Se os JSON já estiverem atualizados e o texto editorial tiver mudado, basta publicar os arquivos editados. Não coloque a ROM, saves, pastas `game/`, tokens ou backups no GitHub.

## O que muda automaticamente

- Total de espécies e formas;
- Total de Paradoxos, formas Mega e espécies autorais pendentes;
- Quantidade de áreas e tabelas de encontros;
- Métodos de encontros efetivamente cadastrados;
- Links para as áreas atualmente presentes na exportação.

## O que NÃO muda automaticamente

- A ordem da campanha e as condições para derrotar cada Type Master;
- Scripts de eventos, NPCs, recompensas e missões;
- Regras de combate que existam apenas nos scripts Ruby;
- Informações da versão original do Decades nos fóruns externos.

Essas partes exigem atualização editorial ou, futuramente, um exportador de eventos validado. Evite inventar eventos da história com base apenas nas tabelas PBS. Para editar guias originais, use `site/public/data/guides.json`; para editar os artigos gerados ou referências do Decades, use `site/scripts/guides.mjs`.

## Verificação

Execute `npm test --prefix site` e `npm run build --prefix site`. A CI em `.github/workflows/site-checks.yml` executa as verificações. O teste em `site/tests/guides.test.mjs` confirma a presença de fontes e que uma alteração simulada nos dados muda os textos gerados.
