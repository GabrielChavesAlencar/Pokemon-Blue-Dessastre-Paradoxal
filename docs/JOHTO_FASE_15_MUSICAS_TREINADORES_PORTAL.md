# Johto — Etapa 15/16: música, treinadores e portal Blue

**Situação: PARCIAL — catálogo M0/M1, regras musicais desativadas, auditor de segurança, prévia navegável e testes publicados. Nenhum áudio de Johto foi instalado, nenhum MapID foi resolvido e nenhuma equipe PBS de Johto foi compilada.**  
**Data:** 13/11/2026  
**Referências:** [Plano de 16 etapas](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md), [Acompanhamento](JOHTO_ETAPAS.md), [Etapa 14 — lendários](JOHTO_FASE_14_LENDARIOS_POS_JOGO.md).

## Arquivos criados ou atualizados

| Recurso | Finalidade |
|---|---|
| [data/johto-music.json](../data/johto-music.json) | **53 cues de planejamento:** 42 BGM e 11 ME. Nenhum arquivo, hash, licença, duração, loop ou autoria presumidos. |
| [data/johto-music-rules.json](../data/johto-music-rules.json) | 35 regras de áreas simbólicas, 10 categorias de batalha, 11 fanfarras e 7 eventos especiais. **Todas desativadas.** |
| [scripts/music/audit_johto_phase15.py](../scripts/music/audit_johto_phase15.py) | Auditor **somente leitura**: detecta direitos falsamente aprovados, regras ativadas, Map Pack não auditado, áudio inventado e status enganoso do portal. |
| [site/public/data/johto-preview.json](../site/public/data/johto-preview.json) | Índice de **148 locais simbólicos** e **36 tipos de treinadores** das etapas 05–14, com referência aos manifests de origem e nenhum time fictício. |
| [site/src/assets/johto.js](../site/src/assets/johto.js) | Renderiza a prévia em seções, separando mapas, treinadores e líderes/Elite. |
| [site/src/assets/app.js](../site/src/assets/app.js) | Roteia \`/localizacoes?regiao=johto\`, \`/treinadores?regiao=johto\` e \`/chefes?regiao=johto\` sem afetar as páginas já existentes. |
| [site/src/assets/regions.js](../site/src/assets/regions.js) | Adiciona seletor de Johto com indicação **prévia** e link no circuito. |
| [site/src/assets/styles.css](../site/src/assets/styles.css) | Estilo de cartões informativos com layout adaptável. |
| [tests/test_johto_phase15_contract.py](../tests/test_johto_phase15_contract.py) | Contratos de M0–M6 fail-closed, datas de origem, oito líderes, ausências de times e preservação das rotas Kanto/Decades. |

## Música — M0 a M6

**M0 — Fonte e direitos.** Não há ZIP/MP3/OGG de Johto com direitos auditados no repositório. Nenhuma faixa de Kanto foi reutilizada. Os nomes dos 53 cues são **rótulos de uso pretendido**, não nomes de arquivos oficiais nem prova de licença. O manifesto permanece \`PLANNED_CUES_NOT_INSTALLED\`, com \`recordings: []\`, \`license_verified: false\` e \`distribution_approved: false\`.

**M1 — Catálogo e rules.** \`johto-music.json\` e \`johto-music-rules.json\` estão criados. Os MapIDs compilados de Johto **não existem**, portanto as 35 áreas são aliases de planejamento e nenhum mapeamento \`MapXXX.rxdata\` foi inventado. As regras iniciam com \`enabled: false\`.

**M2 — BGM por locais.** Cues separados para New Bark, Cherrygrove, Violet, Azalea, Goldenrod, Ecruteak, Olivine, Cianwood, Mahogany, Blackthorn, rotas, centros, ginásios, cavernas, torres, Surf e bicicleta. **Não tocar** onde não houver mapa aprovado, arquivo de áudio licenciado, hash e ligação de evento real.

**M3 — Combates.** Cues por batalha selvagem, treinador, rival, líder, Rocket, bestas errantes, Lugia, Ho-Oh, Elite e Lance. O hook futuro deve usar a classificação real da batalha, preservar escolhas pessoais de áudio do Blue e restringir a região a \`JOHTO\`. Vitória restaura BGM. **Nenhum hook foi instalado**.

**M4 — ME.** Cues para vitória (selvagem, treinador, ginásio), captura, cura, obtenção de insígnia, item, Pokémon, HM, evolução e Hall of Fame. Só executar quando eventos reais comprovarem o disparo e a ausência de repetição. Música ambiente deve ser restaurada ao terminar.

**M5 — Cenas.** Professor Elm, Radio Tower, Kimono Girls, Hall of Fame e créditos; nenhuma cutscene ganha áudio automaticamente. Eventos HGSS/Crystal devem ter seleção de versão auditada antes de ligar uma faixa.

**M6 — Validação e instalação futura.** Usar exclusivamente \`Audio/BGM/Johto\` e \`Audio/ME/Johto\`, sem sobrescrever áudios existentes. Verificar: hash SHA-256 e direitos de cada arquivo; metadados/loops; MapIDs reais de um piloto isolado; saída de caverna; batalha, fade e restauração; funcionamento com áudio ausente; saves e regresso a Kanto/Decades. O script auditável implementado aqui **não instala músicas**: ele só assegura que tudo permaneça desligado até essas condições existirem.

### Auditor de música e portal

\`\`\`powershell
python scripts/music/audit_johto_phase15.py
python -m unittest discover -s tests -p "test_johto_phase15_contract.py" -v
python -m unittest discover -s tests -p "test_johto*.py" -v
\`\`\`

A primeira chamada emite um resumo \`PASS_SAFE_PREVIEW\` **somente** se a fonte continuar não instalada, todos os 53 cues não tiverem arquivo, as regras permanecerem inativas e o portal mostrar zero mapas/treinadores/áudio aprovados. A suíte testa que marcas falsamente habilitadas ou a tentativa de permitir áudio de Kanto sejam rejeitadas.

## Portal de Johto — prévia existente, não jogável

As seguintes rotas do site agora usam o filtro **Johto · prévia**:

- \`/localizacoes?regiao=johto\`: lista **148 locais simbólicos**, por etapa, sem alegar MapID, screenshot de mapa ou taxa de encontro.
- \`/treinadores?regiao=johto\`: lista **36 tipos PBS planejados**, incluindo versões do rival, Rockets, treinadores comuns, Kimono Girls, Elite e outros; **nenhuma equipe ou variante foi gerada**.
- \`/chefes?regiao=johto\`: reúne os **oito líderes** e Elite/campeão previstos. Cada líder possui sua insígnia local, mas nenhum treinador possui PBS compilado ou níveis confirmados.

No circuito de regiões, Johto continua com \`status: planned\`. **O site não deve chamar Johto de jogável nem calcular capturas inexistentes.** O recurso de música e os registros de mapa são apenas um índice com links para a documentação.

A estrutura regional já prevê **dois cartões de treinador**: insígnias da região atual e esmeraldas de todas as regiões. O portal mostra esse requisito, não um save fictício de jogador. O futuro piloto deve integrar os dois cartões ao estado real do jogo.

## Como completar a integração do catálogo de treinadores

1. Receber o pacote de mapas Johto legítimo com direitos, hash e MapIDs, sem sobrescrever os de Kanto/Decades; inventariar todos os trainers nos eventos.
2. Confrontar os 36 tipos do manifesto com a fonte real e expandir para **todos os NPCs** faltantes. Tipos/números são candidatos de contrato, não times compilados.
3. Criar PBS válido para treinadores comuns, oito líderes, Rocket, Kimono, Elite e campeão, com versões 0/1/2 para rivais quando necessário. Conferir stats, moves, itens, habilidades, rematches e regras do próprio Decades.
4. Usar o cálculo global de esmeraldas já implementado por \`BlueRegions.crystal_total\`. No Master Mode, aplicar as regras existentes de **90% do nível e quatro Pokémon para treinadores que hoje começariam com três**, incluindo cobertura de fraqueza, sem inventar times para o site antes do PBS estar aprovado.
5. Gerar automaticamente as equipes do portal **a partir do PBS instalado** e diferenciar normal/Master e rematches; os líderes pós-todas-regiões devem herdar o perfil \`world_champion_rematch\` **somente após o mundo inteiro ser concluído**.
6. Integrar mapa de captura, localizações e Dex a partir dos encounters reais. Onde não há MapID/encounter auditado, continuar mostrando \`PENDENTE\` e **não declarar porcentagens de encontro**.

## Aceite da fase 15/16 ainda pendente

- [ ] Receber áudio com origem, licença, permissão de distribuição e hash verificados por arquivo.
- [ ] Compilar as regras musicais para MapIDs reais de Johto e testá-las em um piloto separado, inclusive fallback, loop, fade e Kanto/Decades.
- [ ] Compilar o PBS de todos os treinadores de Johto, suas equipes normais/Master, condições e variantes; validar níveis/estatísticas no motor.
- [ ] Sincronizar o portal com equipes compiladas, imagens de mapas verificadas e encontros verdadeiros; remover placeholders só após aceite.
- [ ] Auditar a fase final HGSS/Crystal, a entrega do Hall of Fame e as flags de rematches.
- [ ] Testar as duas páginas de cartão local/global, a navegação, o Box e as permissões por oito insígnias.
- [ ] Aprovar regressões Blue Studio/Kanto e Game.exe Windows/JoiPlay.

**Progresso oficial:** 0/16 etapas completamente aprovadas; 0/16 jogabilidade integralmente aprovada. Etapa 15 **PARCIAL**. A próxima etapa, 16/16, deve priorizar Map Pack verdadeiro, instalação reversível, viagem, teste jogável e aceite, sem assumir que os estudos anteriores equivalem a mapas compilados.
