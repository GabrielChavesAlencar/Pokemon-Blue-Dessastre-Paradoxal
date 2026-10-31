# Site e publicação na Vercel

O portal está em `site/`, no mesmo repositório do Blue Studio. Publicar o site não publica a pasta ignorada `game/`. Os JSON de `site/public/data` são o retrato factual da base local exportada: espécies, formas, golpes, habilidades, itens e tabelas de encontro. As imagens usam URLs públicas do projeto PokeAPI/sprites; exigem conexão. As formas autorais de Dessastre Paradoxal usam os sprites do autor; outras formas exibem a ilustração da espécie base com identificação explícita.

## Primeiro deploy

1. Na Vercel, use **Add New → Project** e importe `GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal`. Se necessário, autorize a integração GitHub a ler este repositório privado.
2. Configure **Root Directory = site**, **Framework Preset = Other**, **Node.js Version = 24.x** e **Production Branch = main**.
3. O arquivo `site/vercel.json` configura **Build Command = npm run build** e **Output Directory = dist**. Não configure um servidor Python ou um comando de desenvolvimento como build.
4. Mantenha **Skip deployment** desativado em **Settings → Build and Deployment → Root Directory**, se disponível. Isso permite que mudanças em qualquer pasta apareçam no diário. O `ignoreCommand` versionado também manda continuar o build.
5. Clique **Deploy**. A Vercel fornecerá a URL. Nenhuma chave de API, banco de dados ou token GitHub precisa ser colocado no site.

Este repositório prepara a implantação; não cria uma conta, projeto ou domínio na Vercel. A integração GitHub deve permanecer conectada para as próximas publicações automáticas.

Referências: [configuração estática](https://vercel.com/docs/project-configuration/vercel-json), [Git Integration](https://vercel.com/docs/git), [opção de pular projetos sem alterações](https://vercel.com/docs/monorepos#disable-the-skipping-unaffected-projects-feature).

## Atualizações automáticas

Cada push na **main** aciona `.github/workflows/site-history.yml`. A rotina lê o histórico Git completo e grava `site/public/data/updates.json`, preservando SHA, título, data e link de cada commit. O commit de manutenção do próprio robô é omitido do diário e não inicia um ciclo de sincronizações. Pushes concorrentes são serializados e o envio usa avanço normal, com novas tentativas, sem force push.

O build também lê os commits do checkout e os metadados Git fornecidos pela Vercel. Assim, a versão recém-enviada aparece já no seu próprio deploy, e o JSON versionado preserva o histórico mesmo em checkouts rasos. O navegador lê apenas arquivos estáticos; não precisa acessar a API de um repositório privado.

Os logs mostram **títulos de commits**, não uma descrição inventada de cada linha alterada. Use títulos claros, por exemplo `feat: adicionar nova área`, `fix: corrigir encontro noturno` e `docs: atualizar guia de evolução`. Categorias são derivadas desses títulos. Alterações locais só aparecem após commit e push. Branches de trabalho aparecem no diário de produção depois de integrarem a main.

O workflow usa somente `GITHUB_TOKEN` com `contents: write`. Se regras da main ou políticas da conta bloquearem commits do GitHub Actions, a execução falhará visivelmente em Actions. Nesse caso, execute a sincronização local e envie o JSON junto com suas mudanças, ou ajuste a política do repositório conforme sua preferência. Não é necessário fornecer um token ao cliente do site.

Para reprocessar o histórico: GitHub → **Actions → Portal Blue - sincronizar atualizações → Run workflow**, ou execute na raiz:

```sh
node site/scripts/changelog.mjs --write-seed
```

## Atualizar Pokédex e localizações

Como o jogo está fora do Git, o CI não tem os PBS locais. Depois de alterar espécies, golpes ou encontros no Blue Studio, execute na raiz:

```sh
python scripts/export_site_data.py
npm test --prefix site
npm run build --prefix site
```

Envie os três arquivos regenerados (`catalog.json`, `details.json`, `locations.json`) junto com as alterações. O exportador não envia arquivos, não altera o jogo e não recompila os PBS. Guias editoriais ficam em `site/public/data/guides.json`. A campanha pode escolher versões diferentes de encontros; o portal mostra todas as versões cadastradas, com esse limite visível na interface.

## Validação

`.github/workflows/site-checks.yml` testa o site e gera `dist` em push/PR. Localmente, `npm run dev --prefix site` abre um servidor estático na porta 4173. O build valida sintaxe dos módulos e os JSON obrigatórios. `dist/`, `node_modules/` e `.vercel/` são ignorados pelo Git. Nenhum backend do Blue Studio é necessário no servidor da Vercel.

## Horários no diário

O diário mostra a data e a hora real dos commits (`%cI` do Git, preservada em ISO 8601) em **America/Sao_Paulo**. No frontend, a hora é convertida com `Intl.DateTimeFormat`, sem usar o fuso do navegador. A página `/atualizacoes` também tem um atalho para `/guias`. Os links `*.vercel.app` com sufixos aleatórios são snapshots de uma implantação específica; para abrir a versão atual, use `https://pokemondessastreparadosal.vercel.app/guias` e `https://pokemondessastreparadosal.vercel.app/atualizacoes`.
