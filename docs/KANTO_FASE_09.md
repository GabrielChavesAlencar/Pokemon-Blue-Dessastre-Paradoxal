# Kanto — Etapa 09/16: Celadon e Erika

> **Atualização de gameplay (12/11/2026):** a [entrega do 8º núcleo funcional](KANTO_AVANCO_FUNCIONAL_08.md) ativa **somente Celadon City, o Centro Pokémon e o ginásio de Erika**, com portas, enfermeira e oito treinadores. **A CI nativa da revisão atual ainda é requisito de aprovação.** Os outros oito mapas de Celadon continuam sem eventos. **Os dados e condições abaixo descrevem a antiga prévia de terreno** e são mantidos como histórico, não como proibição atual de implementar o núcleo autorizado.

## Histórico da primeira entrega de cenário



**Data:** 12/11/2026  
**Estado:** prévia de terreno implementada e aprovada na CI nativa Windows (51 mapas, 11 sem eventos). **Eventos ainda adiados por pedido do usuário:** o estudo de eventos foi recebido e incorporado ao [roadmap específico](KANTO_ROADMAP_EVENTOS_FIRERED.md), mas esta tarefa não autoriza instalar eventos.  
**Contadores preservados até conclusão da fase:** desenvolvimento integral 8/16 (50%); etapas integralmente aceitas 1/16 (6,25%).

## Escopo desta entrega — somente mapas e navegação de teste

A fonte auditada é o pacote Essentials FRLG 1.1, validado pelo hash do arquivo já definido em `data/regions/kanto-source.json`. O projeto não publica o arquivo original. IDs da origem confirmados pela auditoria executada na CI:

| ID original | Mapa | Integração desta fase |
| --- | --- | --- |
| 111 | Route 7 | Geometria e conexão regional |
| 114 | Celadon City | Geometria e conexão regional |
| 115 | Celadon Pokémon Center | Geometria, sem NPC nem cura |
| 117 | Celadon Dept. Store 1F | Geometria, sem loja nem porta |
| 118 | Celadon Dept. Store 2F | Geometria, sem loja nem escada |
| 119 | Celadon Dept. Store 3F | Geometria, sem loja nem escada |
| 120 | Celadon Dept. Store 4F | Geometria, sem loja nem escada |
| 121 | Celadon Dept. Store 5F | Geometria, sem loja nem escada |
| 122 | Celadon Dept. Store Rooftop | Geometria, sem NPC nem escada |
| 123 | Celadon Dept. Store Elevator | Geometria, sem botões ou scripts |
| 124 | Celadon Gym | Geometria, **sem Erika, treinadores ou Rainbow Badge** |

Estes **11 mapas** aumentam a geometria catalogada de **40 para 51**, sem modificar as IDs de nenhum dos mapas anteriores. A geometria é carregada com **tabelas de eventos vazias**; não são copiados warps de portas, trechos de história, treinador, sprite de evento, scripts Ruby, flag, item ou encontros selvagens das novas áreas.

O arquivo `data/regions/kanto-source.json` inclui `preview_only` com todos esses IDs; `pilot.py` recusa importar eventos nessas áreas. `pbs.py` omite encontros dessa lista e `verify_pilot.py` exige que o número de eventos compilados dessas áreas seja **zero**.

## Como acessar na cópia experimental

No menu do **Game.exe principal → Testar Kanto**, escolha o inicial no piloto e entre no **menu de pausa → Testes Kanto (experimental)**. As paradas extras estão baseadas em coordenadas de **destino de warps existentes na fonte**, não em coordenadas arbitrárias:

- Rota 7 (entrada pela portaria);
- Celadon City (em frente ao Centro Pokémon);
- Ginásio de Celadon (entrada de Erika, **cenário vazio**);
- Centro Pokémon de Celadon (**cenário vazio**);
- Loja de Celadon 1F (**cenário vazio**).

As cinco novas paradas são exclusivas do **piloto isolado**, totalizando **22**. A transferência de teste não concede insígnias, dinheiro, itens ou flags de história. Lembre-se de salvar em um slot exclusivo de testes: a aceitação de caminhada/colisões ainda depende de jogar no Windows.

## Decisões mantidas após recebimento da análise de eventos

- **Não criar nem adaptar eventos de treinadores.** Isso inclui linhas de visão e bloqueios obrigatórios (pendência MAN-02).
- **Não conectar casas nem estabelecimentos por eventos de porta.** As entradas corretas dependem da auditoria manual (pendência MAN-01).
- **Não ativar Erika, Rainbow Badge, Team Rocket/Game Corner, NPCs de loja nem cenas narrativas.**
- **Não misturar scripts originais do FRLG com o namespace nativo de Decades.**
- Os layouts de insígnias local/geral (MAN-03) seguem planejados, sem modificar a concessão existente.

## Critérios de verificação

- [x] O inventário da fonte confirma IDs, nomes, dimensões e conexões; relatório `kanto-fase-09-auditoria` em [GitHub Actions](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/kanto-pilot-check.yml).
- [x] O teste estrutural compila os 51 mapas, garante **40 mapas com progresso anterior intacto** e **11 mapas sem eventos**, rejeita coordenadas de teleporte inválidas e valida 22 paradas.
- [x] O teste nativo abre o cenário vazio e confirma que **Rainbow Badge permanece bloqueada**.
- [x] A [CI Windows 43202005222](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43202005222) validou a compilação, abertura de janela, save e importação em cópia descartável; regressão adicional de código está no workflow padrão.
- [ ] Jogabilidade manual confirma arte, passabilidade, transição e coordenadas.
- [x] O estudo técnico dos eventos FireRed foi recebido, analisado e vinculado ao [roadmap](KANTO_ROADMAP_EVENTOS_FIRERED.md).
- [ ] **Autorização explícita** para implementar eventos da fase 09 e retirar os 11 IDs de `preview_only`; até lá zero eventos novos.
- [ ] Validar gameplay interativo e os eventos **quando** forem autorizados e implementados.

**Próximo trabalho permitido:** auditar referências, mapas, scripts e flags segundo o roadmap, **sem mexer nos eventos**. A implementação de Erika, interiores, Rocket, NPCs e Rainbow Badge depende de autorização posterior.
