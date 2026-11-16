# Sinnoh — CH18: busca, filtros, pendências e navegação do portal

**Data:** 16/11/2026 · **Status:** CH18 concluída com build e testes automáticos do site. **Nenhum dado foi promovido a jogável**, nem ocorreu verificação de Game.exe/JoiPlay ou deploy externo em Vercel.

## Pesquisa e filtros seguros

A página `/sinnoh` foi ampliada sobre os catálogos da CH17, que continuam derivados dos arquivos auditados das CH11–CH16. Cada busca e seleção usa GET, um URL compartilhável e navegação client-side, sem solicitar ou modificar o motor do jogo.

| Função | Exemplo de URL | O que é mostrado |
|---|---|---|
| Área e espécie candidata | `/sinnoh?aba=areas&busca=Starly` | Áreas que mencionam Starly como referência, **não localização nativa confirmada** |
| Fase documentada | `/sinnoh?aba=areas&fase=3` | Nove áreas previstas da abertura |
| Fase sem definição | `/sinnoh?aba=areas&fase=sem-fase` | 29 referências sem fase, sem inventar ordem |
| Área com espécies candidatas | `/sinnoh?aba=areas&pendencia=com-especies` | Espécies citadas em auditoria, **sem taxas/slots** |
| Rival e grupos | `/sinnoh?aba=treinadores&busca=Barry` | Treinadores documentados sem prova de vínculo NPC/PBS |
| Ginásio/insígnia | `/sinnoh?aba=ginasios&busca=RELIC` | Fantina e espécies de Platinum, sem nível fixo |
| HMs | `/sinnoh?aba=itens&busca=HM05` | HM de Defog sujeito à insígnia local; coleta **não confirmada** |
| Revanche histórica | `/sinnoh?aba=liga&pendencia=com-revanche` | Platinum de referência, **não Full Power instalado** |
| História | `/sinnoh?aba=progresso&busca=GALACTIC` | Checkpoints simbólicos sem vitórias certificadas |
| Pendências por assunto | `/sinnoh?aba=pendencias&tipo=musica` | Cues sem arquivos/licenças/hook instalados |

**Pesquisa normalizada:** ignora acentos e caixa, reconhece a equivalência *Rota/Route*, limita a entrada a 100 caracteres, preserva combinações fase+texto+tipo de pendência e indica resultados vazios com aviso inequívoco. Opções de fase/aba/categoria desconhecidas não criam mapas, atalhos ou conteúdo jogável.

**Sete grupos de pendência documentados:** mapas 120; treinadores 40; equipes históricas 13; HMs 8; checkpoints 22; áreas de encontros de referência 21; chaves musicais simbólicas 46. Esses números não medem instalação na build.

## Navegação contextual

Os cartões conectam páginas já existentes do guia:

- Área → lista de treinadores de referência e pendências de MapID; o link **não afirma** que o treinador esteja naquela área.
- Treinador → áreas a conferir e comprovação futura de evento/PBS.
- Líder → HM da insígnia histórica → líder correspondente, sem desbloqueio real.
- Elite Four/Cynthia → sequência de história e pendências das equipes.
- Etapa histórica → áreas planejadas daquela fase; a página de backlog `/pendencias?regiao=sinnoh` retorna ao novo catálogo.

O módulo [`sinnoh-search.js`](../site/src/assets/sinnoh-search.js) é puro e faz tanto filtros quanto a validação read-only do JSON derivado no build. A [interface](../site/src/assets/sinnoh-guide.js) utiliza GET com formulário real; [`app.js`](../site/src/assets/app.js) melhora a navegação sem exigir reload, e [`styles.css`](../site/src/assets/styles.css) define layout responsivo para busca/resultado vazio. Não foi alterado `site/public/data/regions.json`, PBS, scripts da engine, MapIDs, saves ou áudios das outras regiões.

## Proteções negativas

A [suíte CH18](../site/tests/sinnoh-search.test.mjs) valida pesquisas, filtros combinados, resultados vazios, acessibilidade básica (labels/form/submit), encoding/escape de URLs/HTML e links entre guias. Os testes bloqueiam:

- **Game state falso:** `playable`, `canPlay`, `gameplayVerified`, mapas/treinadores/itens/etapas nativas alegadamente verificados.
- **Dados inventados:** MapIDs, coordenadas, níveis históricos apresentados como níveis Blue, taxas e slots selvagens e versões PBS.
- **Evidência incorreta:** times Full Power confirmados sem fonte, HM marcado como coletado, evento concluído, música licenciada/instalada, progressão Normal/Master modificada e registro incompleto ou duplicado.

É uma verificação **sintética** e de interface; ela não substitui validação no motor original.

## CI e estado de Sinnoh

- [**Portal Blue — run 43981753762**](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43981753762): build `npm run build --prefix site` e suíte `npm test --prefix site`: **137/137 testes aprovados**.
- [**Sinnoh isolado — run 43981753812**](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43981753812): **29/29 testes CH18**, **137 testes do site** e **347 testes Python de Sinnoh** aprovados, além de testes CH01–CH17 e runner Windows. O pipeline geral de outras disciplinas tem ciclo próprio.
- **Barras:** E **18/20 (90%)**; A **8/32 (25%)**; B/C/D **0/13**, sem novas certificações técnicas/jogáveis/nativas.

**Próxima etapa:** CH19 — auditoria das regressões de Sinnoh e separação objetiva dos resultados Python/Ruby e CI, sem confundir fixtures com uma build Game.exe.
