# Prompt para iniciar o Codex — Aceite integral de Kanto

**Copie o texto a seguir para o Codex com este repositório aberto.** O roteiro operacional completo está em [KANTO_CODEX_TESTES_E2E.md](KANTO_CODEX_TESTES_E2E.md). O Codex deve executar os comandos e analisar os resultados, não apenas gerar novos documentos.

---

Você está trabalhando no repositório:

`https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal`

**Sua missão é realizar o QA end-to-end de Kanto no lugar de eu jogar**, identificar defeitos, corrigi-los, repetir os testes e apresentar evidências reais para aumentar a **Barra 2 — Aceite integral**. A Barra 1 de núcleos técnicos já é 16/16; a Barra 2 começa em 1/16, e a região está como `prototype`.

## Instruções obrigatórias

1. Leia primeiro `AGENTS.md`, **`docs/KANTO_CODEX_TESTES_E2E.md`**, `docs/KANTO_ETAPAS.md`, `docs/KANTO_FASE_02_MOVIMENTO.md`, `docs/KANTO_FASE_16.md` e o plano regional v2. Siga a matriz de **16 etapas**, respeitando os critérios de aceite e dependências.
2. Confirme o sistema operacional e a existência do `game/Game.exe`. Crie branch a partir da main atual, preserve minhas alterações locais e **não modifique nem publique saves, binários, ROMs ou arquivos originais de Decades**. Use somente o piloto isolado em `.blue-work`.
3. Execute testes unitários e estruturais, a pipeline nativa Windows, os testes do portal e o gate de publicação. Guarde logs e o SHA real.
4. **Priorize a etapa 02 e o percurso Pallet → Cerulean.** Não basta verificar mapas por script: automatize uma **sessão real de interface Windows**, iniciando o `Game.exe`, detectando a janela, enviando teclas, observando personagem e mudanças de mapa, acionando portas, NPCs, menus, batalhas, cura, captura, save e load. Use screenshots/vídeos e resultados observados como prova.
5. O projeto ainda **não possui um robô que termine o jogo inteiro**. Se necessário, crie um harness de testes E2E Windows em `scripts/regions/e2e` com driver de janela/teclado, detecção de telas e cenários reproduzíveis. Teste o próprio driver antes de confiar nele. Playwright serve para o site, não controla automaticamente `Game.exe`.
6. Depois teste, sem atalhos indevidos, as **16 etapas**: seleção de região inicial, oito ginásios/badges, esmeraldas globais e HMs locais, treinadores/níveis inclusive Master, viagens com o mesmo save, restrição de especiais e depósito na box, Safari, Silph Co., Mansion, Victory Road, Elite Four, três variantes do Campeão e Hall of Fame. Para cada etapa faça também testes negativos, derrota, repetições e save/reload.
7. Teste Android/JoiPlay se houver um ambiente **realmente acessível** ao Codex. Se não houver, registre `BLOCKED_ENV`; jamais declare que testou Android sem sessão Android.
8. Para cada falha, documente **passo mínimo de reprodução, log, screenshot, mapa/evento, resultado esperado e observado**. Corrija no código-fonte, crie teste de regressão, gere novo piloto e execute novamente o cenário real. Não usar injeção de vitórias, badges, flags ou teleporte experimental como evidência de playthrough.
9. Produza `.blue-work/kanto-codex-e2e/<execucao>/resultado.json` e `resultado.md` com estados `PASS_E2E`, `PASS_STRUCTURAL_ONLY`, `FAIL`, `BLOCKED_ENV`, `BLOCKED_IMPLEMENTATION`, `NOT_RUN`. Faça um resumo sanitizado em `docs/KANTO_CODEX_RESULTADOS.md`. **Não publicar screenshots/ROMs/arquivos de saves em GitHub.**
10. **Só aumente a Barra 2 se a etapa inteira tiver PASS_E2E reproduzível na GUI, sem defeitos obrigatórios pendentes e com regressão verde.** Um runner headless, a prova de movimento `KantoWalkCheck`, batalha simulada, mera abertura de janela e um relatório autogerado não são aceite real. Se faltar ambiente gráfico, implemente o que puder mas mantenha a Barra 2 em 1/16.
11. Publique commits e PRs testados na `main`, seguindo `AGENTS.md`, sem `force push`. Mantenha Kanto `prototype` enquanto os critérios finais ainda não forem atendidos.
12. Ao concluir cada lote, devolva: plataforma/versão, cenários que realmente rodaram, PASS/FAIL/BLOCKED por etapa, bugs e correções, links de PR/CI, evidências locais e Barra 2 correta. **Não peça que eu jogue para suprir um teste que você consegue automatizar.** Só peça ambiente/permissões se forem indispensáveis.

**Comece agora:** verifique o ambiente, rode T0/T1/T2, crie/execute o driver T3 para **etapa 02**, investigue os bloqueios e faça correções com reexecução; depois avance para as demais etapas até onde a infraestrutura permitir. Não diga que todos os testes passaram sem tê-los executado de fato. Não aumente as barras por documentação apenas.

---

## O que esperar da primeira execução

Uma primeira rodada aceitável pode concluir **os testes estruturais, algumas interações reais na GUI e uma lista de bugs**, sem concluir a campanha inteira. Isso é avanço legítimo. Quando faltarem Windows interativo, instalação do jogo ou dispositivo Android, o Codex deverá informar exatamente quais evidências não pôde produzir — o usuário não precisa repetir manualmente a bateria por causa disso.

**Arquivo de referência:** `docs/KANTO_CODEX_TESTES_E2E.md`.
