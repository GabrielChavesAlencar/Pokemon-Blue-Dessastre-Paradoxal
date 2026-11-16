# Sinnoh — CH17: guias do portal com estado real de planejamento

**Data:** 16/11/2026 · **Resultado:** CH17 concluída no site e em testes automatizados; **região Sinnoh não jogável**. A publicação do código em GitHub e o sucesso do build não comprovam deploy externo na Vercel.

## Acesso pelo portal

A página de referência está na rota **`/sinnoh`** do portal após seu build/deploy. Os links de **Guias** e **Regiões** foram integrados; `/localizacoes?regiao=sinnoh`, `/treinadores?regiao=sinnoh`, `/chefes?regiao=sinnoh` e `/liga?regiao=sinnoh` agora abrem a seção correta, sem usar as equipes fortes de Kanto como se fossem Sinnoh.

| Seção | Caminho | Comportamento |
|---|---|---|
| Visão geral | `/sinnoh` | Indicadores **de referência**, não progresso jogável |
| Áreas por fase | `/sinnoh?aba=areas&fase=3` | Acesso a 91 áreas distribuídas pelas fases 3–10 |
| Áreas sem fase auditada | `/sinnoh?aba=areas&fase=sem-fase` | **29 referências** sem fase; não distribuir artificialmente |
| Treinadores | `/sinnoh?aba=treinadores` | **40 referências**, sem versões PBS ou local nativo certificado |
| Oito ginásios | `/sinnoh?aba=ginasios` | Ordem histórica de Platinum, nomes, insígnias e espécies de referência, **sem níveis fixos** |
| Elite Four e Cynthia | `/sinnoh?aba=liga` | Composição inicial e revanches históricas de Platinum, sem afirmar Full Power do Blue |
| Itens e HMs | `/sinnoh?aba=itens` | **8 HMs/insígnias regionais**, sem marcar entregas ou permissões ativadas |
| História | `/sinnoh?aba=progresso` | **8 fases de cobertura e 22 checkpoints** Galactic/Cyrus/Liga; Hall of Fame independente |

Todas as seções mostram **“Sinnoh · Planejada · Não jogável”** e cada ficha relevante mostra **“Ainda não adicionado”**.

## Fontes e preservação

O gerador [`site/scripts/sinnoh-guide.mjs`](../site/scripts/sinnoh-guide.mjs) transforma fontes versionadas CH11–CH16 em um JSON publicável no portal **sem acrescentar suposições sobre a engine**:

- [CH11 — insignias/HMs](../data/regions/sinnoh-badges-hms-contract.json): exigências locais de campo e `pickupVerified=false`.
- [CH13 — encontros de referência](../data/regions/sinnoh-symbolic-encounters.json): espécies candidatas em **21 áreas**, sem taxas de encontro, slots, níveis nem MapIDs.
- [CH14 — história](../data/regions/sinnoh-story-ch14-contract.json): 22 checkpoints estritos e Hall of Fame separadamente confirmado, sem teleporte liberado.
- [CH15 — equipes](../data/regions/sinnoh-trainer-teams-ch15.json): oito líderes, Elite Four e Cynthia com espécies de Platinum; níveis históricos **não são exportados** para o portal, e PBS/Full Power permanecem não verificados.
- [CH16 — música](../data/regions/sinnoh-music-ch16.json): **46 chaves simbólicas** e zero arquivos licenciados instalados.
- [Cobertura oficial](../data/regions/sinnoh-coverage.json), [catálogo público de pendências](../site/public/data/pending-regions.json) e [registro regional](../site/public/data/regions.json): fornecem as 120 áreas, 40 treinadores e fase/planned. **29 entradas não têm fase definida** no catálogo e por isso o guia apresenta o filtro **Fase a auditar**, sem inventar a ordem da campanha.

O build [`site/scripts/build.mjs`](../site/scripts/build.mjs) exporta `site/dist/data/sinnoh-guide.json` a partir dessas fontes, não adiciona arquivo nativo ao game. A [interface](../site/src/assets/sinnoh-guide.js) e os [estilos](../site/src/assets/styles.css) exibem abas e cartões responsivos com escapamento HTML. Não foram alterados mapas físicos, PBS, saves, música ou equipes dos outros jogos.

## Bloqueios e regressões

Os [19 testes](../site/tests/sinnoh-guide.test.mjs) incluem cenários negativos para: regiões falsamente jogáveis, flags de instalação/compilação, MapIDs ou coordenadas inventadas, níveis e taxas de Pokémon, aquisição fictícia de HM, equipes e eventos verificados sem prova, áudio protegido, dados ausentes/duplicados, nomes HTML maliciosos, filtros de fase e navegação para regiões legadas.

- **Portal:** [CI 43979589575](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43979589575) — **build aprovado, 108/108 testes do site aprovados**. O workflow `site-checks.yml` foi ajustado para gerar o JSON antes dos testes.
- **Sinnoh isolado:** [CI 43979589757](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43979589757) — **19/19 testes CH17**, **347/347 testes Python de Sinnoh**, execução Windows `RUN.bat` aprovada. A regressão de outros subsistemas é independente e pode prosseguir no pipeline.
- **Não houve Game.exe/JoiPlay**, inspeção de PBS nativo ou testes manuais de encontros/eventos; site não foi promovido a fonte de prova jogável.

**Indicadores após CH17:** Barra E **17/20 (85%)**, Barra A **8/32 (25%)**, Barras B/C/D **0/13**.
