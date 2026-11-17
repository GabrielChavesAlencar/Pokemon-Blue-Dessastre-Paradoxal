# Sinnoh S27 — aceite dos guias do portal (Barra A)

**Escopo:** guia WEB planejado e navegável de Sinnoh. **Não é instalação no Game.exe nem QA Android.** A entrega S27 exige página e guias com estados honestos e mapas simbólicos, não que os mapas do jogo já estejam disponíveis. Os demais requisitos de instalação continuam no backlog S07–S23 e S31.

## Implementação auditada

- [Gerador de dados CH17](../site/scripts/sinnoh-guide.mjs): usa contratos das fases CH11–CH16, fontes locais de cobertura, pendências e regiões; valida e rejeita qualquer sinalização de jogabilidade fictícia.
- [Página de Sinnoh](../site/src/assets/sinnoh-guide.js): oito abas (visão, áreas, treinadores, ginásios, Liga, HMs, história, pendências), navegação contextual, filtros, pesquisa e texto explícito de que **o guia existe no site mas a região não está instalada**.
- [Filtros e schema CH18](../site/src/assets/sinnoh-search.js): pesquisa e filtros que rejeitam `map_id`, níveis, taxas de encontro ou estados jogáveis fictícios.
- [Testes de aceite S27](../site/tests/sinnoh-s27-development.test.mjs): cobrem catálogo, abas, links, áreas sem fase, proibição de MapID, times PBS ou coletáveis falsamente instalados, e integridade do JSON publicado no build.
- [Testes de regressão CH17](../site/tests/sinnoh-guide.test.mjs) e [CH18](../site/tests/sinnoh-search.test.mjs) continuam na suíte completa do site.

## Aceite documental e limitações

- **120 áreas** de referência, **40 treinadores**, **8 ginásios**, **4 membros da Elite Four**, **Cynthia**, **8 HMs**, **22 passos históricos**. **29 áreas** continuam com fase a auditar.
- Os dados são `planned`: **0 mapas nativos verificados**, **0 treinadores compilados verificados**, **0 itens/HMs coletados verificados**.
- Nenhum nível de batalha fixo, MapID inventado, chance de captura nativa, warp físico, música instalada ou licença de asset é inferido do portal.
- A versão de `site/dist/data/sinnoh-guide.json` é regenerada a partir dos catálogos versionados durante o build; não cria arquivos de jogo.
- **Não há evidência de deploy externo em Vercel**, nem de teste Windows/Android. São etapas independentes.

## Evidências do CI

- [Portal Blue — execução 43987976829](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43987976829): build e **143/143 testes do site aprovados**, incluindo os **6 testes S27** e regressões CH17–CH18.
- [Sinnoh CH19 — execução 43987976802](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43987976802): matriz Python/Ruby isolada `success`; validador de contagem da Barra A `passed` e todos os seis auditores Python `passed`.
- [Sinnoh CH20 — execução 43987976741](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43987976741): pré-voo Android estático aprovado, sem Game.exe/JoiPlay.
- As falhas iniciais de oito testes Python eram causadas por asserções antigas `8/32`; [test_sinnoh_progress.py](../tests/test_sinnoh_progress.py) agora verifica os contadores reais do ledger em vez de impedir avanço futuro. **A proteção B/C/D 0/13 permanece.**

## Comandos de validação

```bash
cd site
npm run build
npm test
```

A prova de aceite da S27 é **build + suíte completa do portal em GitHub Actions** e integração do código na `main`. Os CI anteriores confirmaram os requisitos; a S27 passa a `done` no registro `data/regions/sinnoh-progress.json`, resultando em **9/32 (28%)** na Barra A (7 parciais, 16 pendentes). A Barra E permanece **20/20**, e B/C/D **0/13**.

**Esta certificação é exclusivamente web/código.** Para classificar Sinnoh como região jogável, continuam necessários mapas reais licenciados, integração à engine, QA nativo e 44 evidências de Game.exe/JoiPlay.
