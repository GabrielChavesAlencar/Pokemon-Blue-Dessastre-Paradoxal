# Estudo técnico — Fangame Pokémon com todas as regiões

**Projeto-alvo:** Pokémon Blue Dessastre Paradoxal  
**Engine:** RPG Maker XP (RMXP) com Pokémon Essentials  
**Escopo:** Kanto, Johto, Hoenn, Sinnoh, Unova, Kalos, Alola, Galar, Paldea e Hisui  
**Data:** 11/11/2026

> **Critério de evidência:** a lista de fangames abaixo consolida referências discutidas nas pesquisas anteriores. A presença exata de mapas, a versão do Essentials, a completude, a disponibilidade de arquivos-fonte e as licenças **não foram auditadas diretamente neste estudo**. Tratar cada referência como candidato a verificar, não como pacote pronto para importação.

## 1. Objetivo

Criar um único fangame com exploração de todas as regiões oficiais citadas, mantendo o estilo 2D do RPG Maker XP, com progressão coerente, Pokémon de diferentes gerações, mapas conectados, treinadores, encontros selvagens, eventos e pós-jogo. Preservar a campanha já existente do Blue Dessastre Paradoxal e acrescentar regiões sem destruir saves ou modificar IDs existentes desnecessariamente.

### Princípios

1. **Um projeto principal:** um único conjunto de scripts, banco de dados e regras de batalha.
2. **Regiões como módulos de conteúdo:** mapas, eventos, gráficos, encontros e treinadores importados ou recriados por região.
3. **Importação controlada:** nunca sobrescrever `MapInfos.rxdata`, `Tilesets.rxdata` ou scripts do projeto principal diretamente com os de outro jogo.
4. **Fontes autorizadas:** verificar licença/permissão antes de incorporar mapas, tilesets, eventos ou outros recursos de terceiros. Um download jogável não implica autorização de reutilização.
5. **Validação contínua:** testar cada lote de mapas e manter backups e migrações de save.

## 2. Panorama das dez regiões

| Região | Referência geográfica | Complexidade relativa em RMXP | Principal desafio | Prioridade sugerida |
|---|---|---|---|---|
| Kanto | Red/Blue, FireRed/LeafGreen | Baixa–média | Padronizar eventos e conexões | 1 |
| Johto | Crystal, HeartGold/SoulSilver | Baixa–média | Integrar a Kanto e ajustar pós-jogo | 2 |
| Hoenn | Emerald, ORAS | Média | Mar, mergulho, clima e rotas aquáticas | 3 |
| Sinnoh | Platinum | Média–alta | Mt. Coronet, neve, Distortion World | 4 |
| Unova | Black 2/White 2 | Alta | Pontes, cidades grandes e mudanças sazonais | 5 |
| Kalos | X/Y | Alta | Converter cidades 3D, especialmente Lumiose, para 2D | 6 |
| Alola | Ultra Sun/Ultra Moon | Alta | Quatro ilhas, provas e transporte marítimo | 7 |
| Galar | Sword/Shield + DLC | Muito alta | Wild Area, zonas abertas e Dynamax | 8 |
| Paldea | Scarlet/Violet + DLC | Muito alta | Mundo aberto, verticalidade, Area Zero | 9 |
| Hisui | Legends: Arceus | Muito alta | Exploração em áreas, captura e progressão não tradicionais | 10 |

*Prioridade é ordem de integração recomendada, não ranking de qualidade.*

## 3. Projetos candidatos a referência

As páginas abaixo devem ser verificadas quanto à **região realmente jogável**, à versão publicada e à existência de **projeto editável**. Não pressupor que mapas completos ou direitos de reutilização estejam disponíveis.

| Região | Projetos citados nas pesquisas | Observação |
|---|---|---|
| Kanto | Pokémon Añil; Infinite Fusion; Fire Ash; Astra Adventures; Blue Adventures; Kanto Reloaded | Alguns reinterpretam Kanto ou possuem partes da região |
| Johto | GS Vitro; Grueling Gold; Giovanni Origins; Fire Ash; Infinite Fusion | Infinite Fusion possui Johto parcial |
| Hoenn | Eternal Emerald; Fire Ash; Starwish; Stygian Snakewood | Distinguir remake de versão alternativa/demo |
| Sinnoh | Ancient Platinum; Platinum Dawn; Banished Platinum; Uprising; Fire Ash | Conferir alcance das demos e fidelidade dos mapas |
| Unova | Fire Ash; The Pokémon World Project | World Project não deve ser tratado como Unova pronta |
| Kalos | Virtualization; Fire Ash; Pokémon Z | Pokémon Z retrata uma Kalos histórica |
| Alola | Fire Ash; Golden Crown | Confirmar alcance e editabilidade das quatro ilhas |
| Galar | Pokémon Royal; Fire Ash | Royal foi descrito como projeto parcial |
| Paldea | Golden Crown (planejamento); Abstract Version e Shadowside (referências técnicas) | **Nenhum mapa completo de Paldea em RMXP confirmado** |
| Hisui | MewMaps (referência visual); ferramentas Essentials | **Nenhum fangame com Hisui inteira em RMXP confirmado** |

### Links iniciais para investigação

- Fire Ash: https://eeveeexpo.com/threads/9489/
- Infinite Fusion (repositório): https://github.com/infinitefusion/infinitefusion-e18
- Astra Adventures: https://eeveeexpo.com/threads/255/
- Grueling Gold: https://www.pokeharbor.com/2024/02/pokemon-grueling-gold/
- Giovanni Origins: https://eeveeexpo.com/threads/6220/
- Eternal Emerald: https://eeveeexpo.com/threads/4871/
- Pokémon Starwish: https://zamius.wixstudio.com/pokemonstarwish
- Pokémon Z: https://pokemonzfangame.com/
- Golden Crown: https://www.eeveeexpo.com/threads/4419/
- Pokémon Royal: https://whackahack.com/juegos/pokemon-royal/
- Pokémon World Project: https://eeveeexpo.com/resources/1877/
- Pokémon Essentials (referência): https://github.com/Maruno17/pokemon-essentials
- Essentials Gen 5 (referência): https://github.com/FloofyPanthar/Pokemon-Essentials-Gen-5
- Reliqui Studio (ferramenta): https://github.com/andyu19/Reliqui-Studio
- Hisui — referência de mapas: https://www.mewmaps.org/legends-arceus

**Checklist para cada projeto:** URL oficial; versão; engine; região e percentual realmente jogável; acesso aos mapas `.rxdata`; tilesets; eventos; scripts customizados; termos de uso; permissão do autor; compatibilidade com a base principal.

## 4. Arquitetura de conteúdo recomendada

### 4.1 Uma base de código única

Manter a versão de Essentials e os plugins já usados pelo Blue Dessastre Paradoxal. Não atualizar a engine apenas para importar um mapa; fazer atualização separada, com testes de regressão. Mapas de outros jogos são **dados de origem**, nunca substitutos diretos do banco do projeto principal.

### 4.2 Registro global de regiões

Criar um registro lógico com campos como:

```yaml
region_id: HOENN
name: Hoenn
entry_map_id: 310
unlock_condition: johto_league_completed
recommended_level_range: [45, 70]
encounter_profile: hoenn_main
progression_mode: regional_badges
status: planned
```

O formato é **ilustrativo**, não uma sintaxe nativa do Essentials. Implementar com PBS, Ruby ou metadados próprios de acordo com a versão instalada.

### 4.3 IDs de mapas e recursos

- Manter um **manifesto de mapeamento** `source_project/source_map_id -> destination_map_id`.
- Reservar faixas de IDs por região apenas como convenção de planejamento; verificar limites reais e colisões antes de gravar arquivos.
- Atualizar todas as referências a mapas: eventos `Transfer Player`, pontos de retorno, fly points, conexões, posições de NPCs, scripts e teletransportes.
- Remapear IDs de tilesets, autotiles, switches, variáveis, common events e eventos dependentes de scripts externos.
- Não assumir que o limite de mapas é ilimitado; inspecionar a versão real de RMXP/Essentials e avaliar divisão em projetos ou ferramentas de compilação quando necessário.

### 4.4 Estrutura de trabalho sugerida

```text
project/
  Data/                      # dados nativos do RMXP
  Graphics/
    Tilesets/
    Autotiles/
    Characters/
    Pictures/
  PBS/                       # nomes/formatos variam por versão
  tools/
    region_importer/
    validators/
  docs/
    regions/
      kanto.md
      johto.md
      hoenn.md
      sinnoh.md
      unova.md
      kalos.md
      alola.md
      galar.md
      paldea.md
      hisui.md
    map-id-manifest.csv
    asset-provenance.csv
  tests/
```

## 5. Pipeline seguro de importação de mapas

**Etapa A — Inventário:** identificar versão de RPG Maker XP/Essentials, mapas existentes, IDs, gráficos, plugins, eventos e condições de desbloqueio.

**Etapa B — Licença e proveniência:** registrar autor, URL, licença, permissão e alterações previstas. Sem permissão, usar o projeto somente como referência e criar mapas próprios.

**Etapa C — Extração isolada:** trabalhar numa cópia de teste do projeto de origem. Inspecionar `Data/MapXXX.rxdata`, `MapInfos.rxdata`, `Tilesets.rxdata` e pastas gráficas; observar que pacotes distribuídos podem não conter fontes editáveis.

**Etapa D — Remapeamento:** atribuir IDs de destino; converter referências de mapas, tilesets, switches, variáveis, eventos comuns e comandos que dependam de scripts personalizados. Não copiar o `Scripts.rxdata` da origem por cima do projeto principal.

**Etapa E — Conversão de eventos:** adaptar centros Pokémon, Poké Marts, ginásios, cutscenes, HMs, transportes, encontros e NPCs às APIs do Essentials de destino.

**Etapa F — Integração de PBS:** mesclar encontros, metadados, treinadores e outros dados por identificadores estáveis; compilar e verificar erros. A estrutura PBS difere entre versões.

**Etapa G — Testes:** executar entrada/saída, colisão, salvamento, encontros, eventos, retorno após derrota, viagem rápida, clima, música e transições.

**Etapa H — Publicação gradual:** liberar uma cidade ou conjunto de rotas por vez, preservando compatibilidade dos saves.

## 6. Estratégia por região

### Kanto
- Base recomendada: FireRed/LeafGreen; organizar Pallet, Viridian, Pewter, Cerulean, Vermilion, Lavender, Celadon, Fuchsia, Saffron e Cinnabar.
- Aproveitar o padrão de mapas e eventos tradicionais como referência para o restante do jogo.
- Testar rotas, ginásios, Safari Zone, Silph Co. e Victory Road.

### Johto
- Base: HeartGold/SoulSilver ou Crystal.
- Integrar com Kanto por transporte ou eventos de pós-jogo; não presumir conexões existentes entre projetos distintos.
- Validar Ruins of Alph, Whirl Islands, Mt. Silver, Lake of Rage e Ice Path.

### Hoenn
- Base: Emerald.
- Dar atenção às rotas marítimas, Surf, Dive, correntes, clima e transições subaquáticas.
- Validar Seafloor Cavern, Sootopolis, Sky Pillar e Battle Frontier.

### Sinnoh
- Base: Platinum.
- Separar Mt. Coronet em múltiplos mapas com conexões claras; tratar neve, escalada e Distortion World como sistemas específicos.
- Verificar Victory Road, Iron Island, Great Marsh e Battle Zone.

### Unova
- Base: Black 2/White 2, com variantes de Black/White quando fizer sentido.
- Projetar Castelia e outras cidades grandes como setores; criar transições para pontes e passagens.
- Decidir se estações alteram apenas gráficos/encontros ou também colisões e eventos.

### Kalos
- Base: X/Y.
- Planejar Lumiose em distritos 2D conectados por portas/ruas; evitar reproduzir literalmente câmeras e geometrias 3D.
- Tratar Reflection Cave, Tower of Mastery, Frost Cavern e Terminus Cave como módulos próprios.

### Alola
- Base: Ultra Sun/Ultra Moon.
- Organizar Melemele, Akala, Ula'ula e Poni como sub-regiões, com transporte e retorno rápido.
- Implementar provas, kahunas e Totem Pokémon sem forçar o modelo tradicional de oito ginásios.

### Galar
- Base: Sword/Shield e, depois, Isle of Armor/Crown Tundra.
- Transformar Wild Area em setores interconectados; prever clima, spawns visíveis e escalonamento.
- Dynamax e raids são mecânicas separadas da importação dos mapas.

### Paldea
- Base: Scarlet/Violet, com Kitakami e Terarium como expansões futuras.
- Dividir províncias e Area Zero em setores 2D com rotas de entrada e saída bem definidas.
- Planejar progressão não linear, Titãs, Team Star, ginásios e montarias como sistemas independentes.
- Como não há mapa RMXP completo confirmado, estimar esforço de produção de tilesets, eventos e level design próprios.

### Hisui
- Base: Legends: Arceus.
- Usar Jubilife Village como hub e cinco grandes áreas como zonas exploráveis.
- Diferenciar progressão por pesquisa/captura e Pokémon nobres do circuito de ginásios.
- Opcionalmente relacionar Hisui e Sinnoh por viagem temporal, mas manter mapas, NPCs e encontros separados.

## 7. Progressão entre regiões

Há três modelos possíveis:

| Modelo | Vantagens | Riscos |
|---|---|---|
| Linear (Kanto → Hisui) | Curva de dificuldade simples | Campanha excessivamente longa e níveis saturados |
| Livre após um prólogo | Sensação de mundo aberto | Balanceamento complexo e risco de eventos fora de ordem |
| **Híbrido recomendado** | Libera blocos de regiões e preserva liberdade local | Exige controle de desbloqueios |

### Modelo híbrido proposto

1. Preservar a história principal do Blue Dessastre Paradoxal.
2. Desbloquear viagens para Kanto e Johto como primeiro bloco.
3. Abrir Hoenn e Sinnoh após marcos narrativos.
4. Abrir Unova e Kalos como bloco intermediário.
5. Liberar Alola e Galar como bloco avançado.
6. Tratar Paldea como região de mundo aberto e Hisui como arco especial/temporal.

Esses blocos são sugestão de design; não pressupõem que o jogo já tenha essa progressão.

### Evitar o problema do nível 100

- Não somar simplesmente +10 ou +20 níveis por região: o teto de nível torna esse modelo inviável em dez campanhas.
- Preferir escalonamento de treinadores por progresso regional, composição de times, itens, habilidades e IA.
- Considerar limites de nível temporários, formatos de batalha especiais e desafios opcionais.
- **Não reduzir níveis dos Pokémon do jogador sem aviso**; qualquer normalização precisa ser clara e, idealmente, limitada a batalhas específicas.
- Registrar conquistas por região independentemente do nível global.

## 8. Sistemas compartilhados

### Pokédex e espécies
- Uma Pokédex global com filtros por região, formas e categorias (incluindo Pokémon originais do Dessastre Paradoxal).
- Preservar IDs estáveis e evitar duplicações de espécies entre pacotes de origem.
- Diferenciar formas regionais, Paradoxos, Megas e variantes sem sobrescrever dados oficiais.

### Encontros
- Tabelas por mapa, horário, clima e progresso, conforme suporte da engine.
- Encontros raros com taxas configuráveis; validar se os percentuais de cada método de encontro totalizam o esperado.
- Separar disponibilidade regional de decisões de balanceamento.

### Treinadores e ginásios
- IDs únicos para treinadores, equipes alternativas e rematches.
- Escalonar por progresso sem eliminar a identidade temática dos líderes.
- Criar visualização dos times no site/guia, com controle de spoilers.

### Transporte
- Hub de viagem regional; Fly dentro da região; navios, trens e portais quando fizer sentido narrativo.
- Sempre oferecer rota de retorno e pontos seguros para respawn.

### Saves
- Criar número de versão do save, rotina de migração e testes com saves antigos.
- Evitar remover ou reutilizar IDs de mapas já referenciados por saves existentes.
- Testar carregamento em mapas alterados e recuperação de posições inválidas.

## 9. Desempenho e limitações

- **Quantidade de mapas:** monitorar IDs, tamanho dos arquivos e tempo de compilação/carregamento.
- **Mapas gigantes:** dividir áreas extensas em setores com transições suaves.
- **Eventos paralelos:** evitar loops de eventos executados a cada frame sem necessidade.
- **Gráficos:** consolidar tilesets com cuidado; reduzir imagens redundantes e sprites de resolução excessiva.
- **Música e efeitos:** padronizar formatos e manter catálogo para evitar duplicações.
- **JoiPlay/Android:** testar separadamente; compatibilidade de plugins, scripts Ruby, renderização e entrada não é garantida.
- **Builds:** automatizar validação de referências quebradas, recursos ausentes e colisões de IDs.

## 10. Testes automáticos e manuais

| Teste | Critério de aprovação |
|---|---|
| Integridade de IDs | Nenhum mapa/tileset/evento referenciado indevidamente |
| Conexões | Todas as saídas levam ao destino correto e permitem retorno |
| Colisão | Sem bloqueios indevidos ou passagem por paredes |
| Encontros | Tabelas válidas e métodos compatíveis com o terreno |
| NPCs e eventos | Scripts e recursos presentes, sem travamentos |
| Salvamento | Salvar/carregar em cada região e migrar saves anteriores |
| Transporte | Fly, barcos, trens e portais respeitam desbloqueios |
| Derrota | Respawn seguro e retorno à progressão |
| Performance | Tempos de carga e FPS medidos em hardware-alvo |
| Android/JoiPlay | Testes próprios de controles, mapas e batalhas |

**Teste de fumaça por região:** começar no hub → entrar na primeira cidade → atravessar duas rotas → enfrentar um treinador → encontrar Pokémon selvagem → salvar → reiniciar → carregar → retornar ao hub.

## 11. Plano de execução em fases

### Fase 0 — Auditoria do projeto atual
- Identificar versão exata do Essentials, plugins, mapas, scripts, formato de saves e limitações.
- Criar backup e baseline de testes; registrar IDs e assets existentes.

### Fase 1 — Infraestrutura multirregional
- Registro de regiões, transporte, desbloqueios, Pokédex, tabelas de encontros e manifesto de IDs.
- Ferramenta de verificação de referências e de origem/licença dos recursos.

### Fase 2 — Prova de conceito
- Integrar **uma cidade e duas rotas de Kanto** em branch isolada.
- Validar eventos, encontros, saves e retorno ao mapa original.
- Só depois ampliar para Kanto completa.

### Fase 3 — Regiões tradicionais
- Johto → Hoenn → Sinnoh; integrar por blocos pequenos e testáveis.

### Fase 4 — Regiões com conversão 3D→2D
- Unova → Kalos → Alola; padronizar estilo visual e transições.

### Fase 5 — Mundos abertos e campanha especial
- Galar → Paldea → Hisui; criar sistemas específicos apenas quando necessários.

### Fase 6 — Balanceamento e lançamento
- Ajustar curva de dificuldade, progressão, missões, guias, mapas e estabilidade em PC/Android.

## 12. Estimativa de esforço e riscos

Não é responsável atribuir prazos numéricos sem inventariar o repositório, as permissões dos assets e a equipe disponível. Os maiores riscos são:

1. Falta de mapas editáveis e reutilizáveis com autorização.
2. Incompatibilidade de versões do Essentials e scripts de terceiros.
3. Colisões de IDs e eventos quebrados após importação.
4. Crescimento excessivo de mapas, gráficos e tempo de carregamento.
5. Balanceamento de dez regiões em uma única progressão.
6. Diferenças de execução entre Windows e JoiPlay/Android.
7. Escopo de produção de Paldea e Hisui em 2D.

## 13. Critérios de pronto por região

Uma região só deve ser marcada como **completa** quando possuir:

- [ ] Cidades, rotas, cavernas e locais principais definidos no escopo
- [ ] Todos os mapas acessíveis, com transições e colisões validadas
- [ ] Eventos principais, treinadores e encontros funcionais
- [ ] Transporte, cura, comércio e respawn seguros
- [ ] Gráficos e músicas presentes, com proveniência registrada
- [ ] Salvamento e carregamento testados
- [ ] Compatibilidade com a Pokédex e regras globais
- [ ] Teste de fumaça aprovado no Windows
- [ ] Teste específico em JoiPlay, se o lançamento Android for prometido
- [ ] Permissões de uso dos recursos verificadas

## 14. Decisão recomendada

**Construir uma infraestrutura multirregional e provar o processo em Kanto antes de importar grandes conjuntos de mapas.** Usar fangames existentes para análise técnica e geográfica, aproveitando arquivos apenas quando houver acesso legítimo e autorização de reutilização. Concentrar primeiro as regiões 2D tradicionais; tratar Galar, Paldea e Hisui como adaptações de design com orçamento próprio.

### Próxima ação concreta

Auditar o repositório do Blue Dessastre Paradoxal para identificar versão do Essentials, estrutura de `Data/`, `PBS/` e `Graphics/`, IDs ocupados, mecanismos de save e estado dos testes. A partir disso, criar um **manifesto real de importação para Kanto** e uma prova de conceito pequena, reversível e automatizável.
