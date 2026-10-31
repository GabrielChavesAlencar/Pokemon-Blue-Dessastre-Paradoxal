# Portal Pokémon Blue

Site público estático do projeto: Pokédex com formas, atributos, habilidades, evoluções e golpes; áreas de encontro; guias; histórico real de commits. Os dados vêm dos PBS locais exportados, sem executáveis, mapas binários, saves ou assets do fangame.

## Executar

Com Node.js 24 e Git, na pasta `site`:

```sh
npm run dev
```

Abra `http://127.0.0.1:4173`. O servidor serve `dist`; após editar arquivos, execute novamente `npm run build` e recarregue a página. `npm test` valida histórico, dados e regras de herança das formas. Não há dependências npm de produção.

## Vercel

Importe este mesmo repositório na Vercel. Escolha **Root Directory: `site`**, **Framework Preset: Other**, **Node.js: 24.x**, **Production Branch: main**. O `vercel.json` fornece `npm run build`, saída `dist` e rotas para os links da Pokédex. Nenhuma variável secreta é necessária.

Em Settings → Build and Deployment → Root Directory, mantenha **Skip deployment desativado**, se a opção aparecer, para atualizar também quando mudar apenas o jogo/editor. O `ignoreCommand` força o build a continuar. Depois da primeira implantação, pushes na main geram novas versões pelo Git Integration da Vercel.

Veja [o procedimento completo e a rotina de atualizações](../docs/SITE_E_VERCEL.md).

A geração autoral **Dessastre Paradoxal** acrescenta 59 espécies e 12 Megas. O build extrai os sprites de `assets/fan-pokemon.tar.gz`, verificando seu SHA-256. O pacote contém somente os sprites autorais normalizados. [Cadastro, pendências e importação no jogo](../docs/GERACAO_DESSASTRE_PARADOXAL.md).
