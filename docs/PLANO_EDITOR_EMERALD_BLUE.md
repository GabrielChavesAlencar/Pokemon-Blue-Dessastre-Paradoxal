# Migração visual do Emerald Studio para o Blue Studio

Fonte de referência: \`Lancelioti/emerald-studio\`, especialmente:
- \`packages/web/src/App.tsx\` (topo, navegação entre editor de ROM e MD).
- \`packages/web/src/rom/pages/BinaryRomEditorPage.tsx\` (14 abas principais e 6 avançadas).
- \`packages/web/src/rom/rom.css\` e \`packages/web/src/styles.css\` (tema escuro, painéis, botões e acentos).

Destino: \`GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal\`.

## Entrega desta fase

- Novo shell com **Visão geral**, **Editor de ROM** e **Ver MD de Movesets**.
- 14 abas principais e 6 ferramentas avançadas preservam nomes e agrupamentos do Emerald Studio.
- Identidade própria com base escura (ink-950, ink-900, ink-700), cartões, controles compactos, acento rosa e detalhes azuis.
- O editor PBS existente continua real nas abas **Pokédex**, **Itens**, **Treinadores** e **Selvagens**.
- Abas restantes abrem **painéis claramente sinalizados como planejamento**, sem aparentar gravação que não existe.
- Navegação por hash, retorno à Pokédex e proteção contra descartar mudanças de arquivo PBS sem confirmação.
- Zero redistribuição de ROM/arquivos originais do Pokémon Decades.

## Incompatibilidades técnicas importantes

O Emerald Studio modifica uma ROM GBA em formato binário. O Pokémon Decades funciona em Pokémon Essentials v21.1/RPG Maker XP com PBS, plugins Ruby e mapas RXDATA. **Não copiar offsets, patches binários GBA, 4bpp ou sistemas de ROM diretamente.** Reutilizar conceitos visuais e contratos do editor, construindo implementações próprias.

## Backlog priorizado

| Fase | Entrega | Critérios de aceite |
|---|---|---|
| 1 (atual) | Interface, 20 abas e regressão | Navegação funciona; 4 abas PBS editam de verdade; outras marcadas como planejadas; CI verde |
| 2 | Pokédex visual, fakémon e formas paradoxais | Front/back/shiny, tipos, atributos, evoluções e golpes com validação e backups |
| 3 | Importador de sprites | PNG, normal/shiny, prévias, verificação de tamanho e paths corretos |
| 4 | Treinadores e encontros | Pesquisa por mapa, equipes, drops, dia/noite, chances e verificação de referências |
| 5 | Mapas/eventos | Leitura segura RXDATA, preview, eventos visuais, salvar com backup + testes |
| 6 | Logo, efeitos e áudio | Importação de recursos, testes no jogo, restauração sem corromper projeto |
| 7 | MD Movesets | Markdown validado, reconciliação com PBS e relatório de divergências |
| 8 | Test Lab de jogo | Inicialização debug, captura, evolução, salvamento, batalhas e logs |
| 9 | Distribuição | Exportar somente conteúdo próprio e instruções compatíveis com direitos/licenças |

## Política de regressão obrigatória nas próximas fases

Executar antes de cada alteração e depois de cada alteração:

1. \`python -m unittest discover -s tests -v\` — PBS (parse, UTF-8/BOM, campos repetidos), backups, API, concorrência, segurança, contratos HTML e abas.
2. \`node --check web/app.js && node --check web/navigation.js\` — validação sintática.
3. \`node tests/browser_smoke.cjs\` com Playwright instalado — Chromium, navegação entre 20 abas, trocar arquivos PBS, salvar dados em diretório temporário, placeholders, console sem erros.
4. No GitHub, **Actions** executa os mesmos testes automaticamente em cada \`push\` na \`main\`, cada PR e execução manual.
5. Testes **NUNCA** devem abrir/escrever no Pokémon Decades real: fixtures sintéticas \`tmp\` obrigatórias.
6. Mudanças que tornem uma aba funcional devem adicionar testes unitários e pelo menos um caminho E2E para essa função antes de retirar o estado \`PLANEJADO\`.

**Nota:** o workflow só executa quando o GitHub Actions está habilitado no repositório e os jobs têm acesso ao runner; o resultado precisa ser conferido na aba Actions. Não presumir sucesso sem logs.

## Critérios permanentes de segurança

- Não apagar \`game/\` e \`.blue-backups/\`.
- Não aplicar hard reset no Git do usuário.
- Não gravar fora do PBS por endpoints sem validação de caminho e sem backups.
- Não prometer compatibilidade de patch GBA num motor RPG Maker XP.
