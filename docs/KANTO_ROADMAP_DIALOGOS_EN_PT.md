# Kanto — Roadmap de diálogos em inglês e português (EN/PT-BR)

**Revisão documental:** 12/11/2026. **Status:** análise concluída e planejamento registrado; **catálogo integral ainda não extraído, traduções não revisadas por completo e nenhuma fala nova aplicada ao piloto nesta entrega**.

## 1. Documentos realmente disponíveis e o que comprovam

- [Guia_Dialogos_Pokemon_FireRed_EN_PT.md](Guia_Dialogos_Pokemon_FireRed_EN_PT.md): guia de organização e revisão, 67 referências de cenas `KAN-001` a `KAN-067` e 14 referências opcionais de Sevii `SEV-001` a `SEV-014`; descreve o conteúdo em PT-BR, **não transcreve as falas originais de FireRed**.
- [FIRERED_DIALOGOS_PASSO_A_PASSO.md](FIRERED_DIALOGOS_PASSO_A_PASSO.md): processo de extração, localização e implantação no Blue; explicita que a documentação não instala falas ou eventos.
- [extrair_traduzir_dialogos_firered.py](../scripts/localization/extrair_traduzir_dialogos_firered.py): gerador **somente leitura** para uma cópia local autorizada de `pret/pokefirered`, cobrindo literais `.string` nos arquivos `data/**/*.inc`, `data/**/*.s` e padrões `_()` em `src/**/*.c`. Tradução en→pt por Argos é **opcional e não revisada**.
- [KANTO_ROADMAP_EVENTOS_FIRERED.md](KANTO_ROADMAP_EVENTOS_FIRERED.md): precondições, triggers, eventos `EVT-01`–`EVT-50` e trilha própria de 12 marcos; cada uso de fala precisa vincular-se ao evento real.
- [PORTUGUES_E_UI.md](PORTUGUES_E_UI.md): sistema **existente** de idioma do Blue. A base `data/pt-br.json` usa **chaves das mensagens inglesas compiladas na engine**, não os rótulos GBA; o guia não demonstra uma importação das falas de FireRed.

**Contagem correta:** 67 + 14 = **81 referências temáticas de cenas**, **não** 81 falas literalmente extraídas/traduzidas, nem 81 eventos instalados. Não há neste repositório, segundo os documentos analisados, evidência de um `FireRed_Dialogos_EN_PT.md` integral gerado e revisado. O número real de entradas em inglês, sua cobertura e as traduções aprovadas precisam ser aferidos ao executar os extratores.

**Limites de publicação:** não versionar no repositório público transcrições/traduções integrais do roteiro de terceiros sem os direitos aplicáveis. Manter os arquivos integrais locais em `.blue-work/kanto-dialogos/` e usar no jogo adaptações autorais/permitidas, sempre respeitando as regras de crédito e uso do projeto.

## 2. Etapas concretas de trabalho (DIA-01 a DIA-10)

| ID | Entrega exigida | Status | Dependência e evidência |
| --- | --- | --- | --- |
| **DIA-01** | Congelar os commits da referência `pret/pokefirered`, fonte FRLG e Blue; registrar cobertura e esquema de idiomas | Pendente | AUD-01 do roadmap de eventos; SHAs e versão no relatório local |
| **DIA-02** | Executar extrator em modo sem tradução e produzir catálogo privado com `source:line`, rótulo, texto inglês e contagem por área | Pendente | Fonte local autorizada; relatório com nº real de entradas, arquivos lidos, avisos e lacunas |
| **DIA-03** | Reconciliar rótulo GBA → script/branch `scripts.inc` → ID de mapa/evento RMXP FRLG → ID do Blue, por **uso de fala** | Pendente | AUD-03/04 e MAN-01/02; sem mapear só pela semelhança de nomes |
| **DIA-04** | Traduzir inicialmente cada entrada elegível para pt-BR e classificar *automática*, *revisão necessária*, *aprovada* ou *não aplicável* | Pendente | Tradução opcional Argos; manter revisão humana e origem privada |
| **DIA-05** | Unificar glossário e tokens: `{PLAYER}`, `{RIVAL}`, `{STR_VAR_1}`, macros, nomes Pokémon/itens/golpes e termos da UI | Pendente | `catalog.validate`/`review.py`; **não** mudar IDs de comando/escolha |
| **DIA-06** | Especificar localização `locale/en` + `locale/pt-BR` por ID autoral estável de diálogo Blue, sem confundir GBA label com chave de engine | Pendente | Correlacionar com `scripts/localization/catalog.py` e o formato real `data/pt-br.json` |
| **DIA-07** | Criar/adaptar apenas falas **autorizadas e com eventos implementados**. Para texto já exibido pela engine, traduzir a chave inglesa real; para evento inexistente, deixar em plano | Pendente | Permissão de implementação do evento, QA, controle de versões/saves |
| **DIA-08** | Testar English ↔ Português nos estados **antes/depois** de encontro, vitória/derrota/fuga, quests, insígnias, itens, escolha, revisita e reload | Pendente | `Game.exe`, snapshots, resultados por MapID/EventID/estado |
| **DIA-09** | Verificar legibilidade de caixas: linhas, acentos, nomes dinâmicos, opções Sim/Não, fontes e compatibilidade Windows/JoiPlay | Pendente | Capturas de tela, testes com nomes longos e limites de diálogo |
| **DIA-10** | Congelar relatórios de cobertura e fechar lacunas por área; atualizar portal só com conteúdo autorizado, nunca com corpus integral de terceiros | Pendente | Tabela `aprovado/extraído`, regressão e rollback; aceite humano |

**Métricas separadas:** número de falas *extraídas*, *mapeadas para uso*, *traduzidas automaticamente*, *revisadas*, *aplicadas*, *validadas em dois idiomas*. **Nenhum desses numeradores está medido neste momento.** Não calcular percentual fictício com base nas 81 referências de cenas.

## 3. Lotes de diálogos ligados às 16 fases de Kanto

As referências abaixo são **IDs de resumos temáticos** do guia, não IDs instalados no jogo. As relações com fases são critérios de planejamento, não evidência de implementação.

| Lote de diálogos | Referências do guia | Conteúdo | Etapas/fases relacionadas | Prioridade/estado |
| --- | --- | --- | --- | --- |
| **DLG-A** | `KAN-001`–`KAN-010` | Pallet/Oak, iniciais, rival, entrega, Viridian e Forest | 02, 03, 04 e início do roteiro | Alta; revisar evento/portas MAN-01 e rival |
| **DLG-B** | `KAN-011`–`KAN-022` | Pewter/Brock, Mt. Moon/fósseis, Cerulean/Misty, Nugget Bridge e Bill | 03, 07, 08 | Alta; escolhas, treinadores, fóssil, ticket e flags |
| **DLG-C** | `KAN-023`–`KAN-033` | Vermilion/S.S. Anne/Surge, Diglett's Cave, Rock Tunnel, Lavender/Pokémon Tower/Fuji | 08, 09, 11 e lacunas de acesso | Alta no trecho já implementado; Lavender pendente |
| **DLG-D** | `KAN-034`–`KAN-046` | Celadon/loja/Rocket/Game Corner/Erika, Saffron/Dojo/Silph/Sabrina | 09 e 11 | **Erika/Celadon já possui núcleo experimental (3 mapas); 8 mapas Celadon + 30 Saffron continuam `preview_only`, sem eventos/diálogos integrados** |
| **DLG-E** | `KAN-047`–`KAN-052` | Fuchsia/Safari/Secret House/Warden/Koga e Snorlax das rotas 12/16 | 10 e pré-requisitos de Lavender | **Núcleo Fuchsia/Koga ativado em 5 mapas; 15 mapas de Fuchsia/Safari continuam `preview_only` sem eventos ou diálogos** |
| **DLG-F** | `KAN-053`–`KAN-057` | Cinnabar/Mansion/Blaine, Viridian final/Giovanni e pesquisa de Oak | 12–13 | Planejado; fase ainda não implementada |
| **DLG-G** | `KAN-058`–`KAN-067` | Verificação de badges, Victory Road, Elite Four, rival campeão, Hall of Fame, Oak e Cerulean Cave | 14–16 | Planejado; separar Liga do pós-jogo |
| **DLG-SEV** | `SEV-001`–`SEV-014` | One–Seven Island, Celio, Rocket Warehouse, Lorelei e afins | Pós-jogo/escopo opcional; fases 15–16 só se decidido | Não altera automaticamente 16 etapas; precisa decisão de escopo |

**Tratamento das cenas transversais (seção 5.8 do guia):** NPCs de comércio/Center, placas, tutores, PC, batalhas, itens, escolhas, NPC derrotado, alternativas e placeholders devem ser auditados **em cada lote**. Um rótulo de texto pode ser reutilizado por mais de um NPC ou estado; o aceite se dá por *uso de fala* e contexto, não por quantidade de rótulos únicos.

## 4. Contrato de matriz por uso de fala

Colunas a registrar (não preencher IDs por inferência):

`source_commit`, `gba_map`, `gba_text_id`, `gba_script`, `source_flag`, `condition`, `speaker`, `context`, `source_rmxp_map_id`, `blue_map_id`, `event_id`, `event_state`, `locale_en_reference`, `locale_pt_br_review`, `blue_dialogue_id`, `engine_english_key`, `tokens_ok`, `box_ok`, `en_test`, `pt_br_test`, `status`, `evidence`.

A **referência GBA** não pode virar `engine_english_key` por substituição de string. São sistemas distintos. Por exemplo, o ID autoral ilustrativo `kanto.pallet.oak.inicial.apresentacao` do guia é um **exemplo**, não um diálogo existente. Itens, batalhas, switches, flags e consequências de opções pertencem à implementação de eventos, **não** à tabela de tradução.

## 5. Fluxo recomendado sem instalar falas

1. Criar uma cópia local autorizada de `pret/pokefirered` em `.blue-work/pokefirered-reference`; registrar o SHA. Não copiar seus textos para `docs/` nem distribuí-los.
2. Executar `py -3 scripts/localization/extrair_traduzir_dialogos_firered.py .blue-work/pokefirered-reference --saida .blue-work/kanto-dialogos/FireRed_Dialogos_EN_PT.md` para inventário **sem tradução**; contabilizar e identificar limitações.
3. Opcionalmente usar `--traduzir --limite 50` para pequeno lote de revisão, sem concluir que o tradutor gerou pt-BR aprovado.
4. Confrontar com a saída privada de `scripts/regions/extrair_eventos_firered.py`; registrar o roteiro de `text.inc` / `scripts.inc` e condições de fala, sem executar código de terceiros.
5. Aplicar QA de preservação de tokens e revisão de localização segundo `scripts/localization/catalog.py`, `scripts/localization/review.py`, `docs/PORTUGUES_E_UI.md`.
6. **Não modificar os 53 mapas ainda em `preview_only` nem liberar seus diálogos antes da autorização dos eventos**. O teste `Testar Kanto` é uma cópia com save isolado.

## 6. Critérios de aceite do diálogo em cada evento

- [ ] Origem/commit/arquivo/linha/rótulo identificáveis, e correspondência GBA → FRLG → Blue **comprovada**.
- [ ] Falante, mapa, condição e estados anterior/posterior documentados; opcionalidade correta (não bloquear eventos opcionais).
- [ ] Tradução pt-BR revisada para contexto, gênero, terminologia e gramática, ou texto autoral/permitido.
- [ ] Preservados placeholders, controles de pausa, mudança de janela, escolhas e códigos da engine.
- [ ] Em jogo, opções EN e PT-BR mostram o texto certo, sem corte ou caracteres inválidos.
- [ ] Repetição e estados alternativos mantêm scripts e recompensas únicos; derrota/fuga não registra vitória.
- [ ] Save/reload e troca de idioma não alteram quest, Pokémon, flags nem Decades.
- [ ] Screenshot/evidência Windows; Android/JoiPlay quando aplicável; rollback documentado.

## 7. Progresso e bloqueios

- **Campanha Kanto, núcleos funcionais comprovados:** **9/16 (56,25%); faltam 7 etapas**. O [9º núcleo](KANTO_AVANCO_FUNCIONAL_09.md) ativou Fuchsia/Koga com textos locais provisórios; adaptação sistemática de diálogos FireRed EN/PT-BR ainda pendente. **53 mapas protegidos** sem eventos ou diálogos.
- **Campanha Kanto, aceitação completa:** **1/16 (6,25%); faltam 15 etapas**. QA humano pendente.
- **Auditoria de eventos FireRed:** 12 marcos; sem porcentagem aferida.
- **Auditoria/localização de diálogos:** 10 tarefas DIA-01–DIA-10; **0 finalizadas nesta revisão documental**, execução ainda não registrada.
- **Tradução Kanto EN/PT-BR:** percentual **não aferido**; 67 cenas são referência, não denominador de falas.
- **MAN-01, MAN-02 e MAN-03:** pendentes. Resolver os problemas reais do jogador antes de liberar eventos posteriores.

**Próximo passo permitido:** inventário e revisão de contexto em lote, mantendo textos originais em pasta privada. Implementar falas no Game.exe apenas junto com os eventos autorizados, preservando os saves e o mapa de estados.
