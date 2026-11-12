# Kanto — Fase 11/16: Saffron City, Sabrina e Silph Co.

**Data da preparação:** 12/11/2026. **Estado:** prévia de terreno na cópia isolada de Kanto, **sem eventos**, conforme o pedido de deixar a adaptação dos eventos para uma etapa posterior. Não é uma fase funcionalmente concluída.

**Referências:** [roadmap dos eventos FireRed](KANTO_ROADMAP_EVENTOS_FIRERED.md), [estudo de eventos](ESTUDO_EVENTOS_MAPA_POKEMON_FIRERED_RPG_MAKER_XP.md), [Plano de Regiões v2](PLANO_REGIOES_DESSASTRE_V2.md) e [análise de fase 10](KANTO_FASE_10.md).

## 1. Origem e escopo dos mapas

A auditoria [audit_saffron.py](../scripts/regions/audit_saffron.py) usa **apenas leitura** da fonte Essentials FRLG verificada pelo SHA-256 de [kanto-source.json](../data/regions/kanto-source.json). A lista de origem contém **34 mapas relacionados**; quatro deles já estavam no piloto (IDs 59, 60, 63 e 111). Foram escolhidos os **30 mapas ainda ausentes**:

| ID da fonte FRLG | Mapa | Observação |
| ---: | --- | --- |
| 57 | Portaria norte de Saffron | Cenário sem guardas |
| 62 | Portaria sul de Saffron | Cenário sem guardas |
| 107 | Rota 8 | Sem treinadores/encontros |
| 108 | Portaria leste de Saffron | Sem guardas |
| 109 | Entrada leste da passagem subterrânea | Porta ainda sem eventos |
| 110 | Túnel subterrâneo leste/oeste | Sem eventos |
| 112 | Portaria oeste de Saffron | Sem guardas |
| 113 | Entrada oeste da passagem subterrânea | Sem eventos |
| 168 | Saffron City | Terreno da cidade |
| 169 | Centro Pokémon de Saffron | Sem cura/NPC |
| 170 | Poké Mart de Saffron | Sem compras/NPC |
| 171 | Ginásio de Sabrina | **Sem Sabrina ou teletransportadores** |
| 172 | Fighting Dojo | Sem combates ou prêmio |
| 173 | Pokémon Trainer Fan Club | Interior descoberto pela auditoria de warp |
| 174 | Casa de Saffron A | Sem eventos |
| 175 | Casa de Saffron B | Sem eventos |
| 176 | Casa de Saffron C | Sem eventos |
| 177 | Silph Co. — recepção | Sem eventos |
| 178–188 | Silph Co. — andares 1F a 11F | Sem Rocket, teletransportes, Card Key ou Giovanni |
| 189 | Silph Co. — elevador | Sem controles/elevador ativo |

**Totais:** 101 mapas no catálogo (40 com a integração anterior + 11 Celadon + 20 Fuchsia + **30 Saffron**); **61 em `preview_only` com zero eventos**; 54 perfis de treinadores anteriormente publicados, sem perfis novos da fase 11.

Os MapIDs **da fonte** não são MapIDs do Blue. Uma proteção em `audit.py` agora fixa a ordem dos **71 mapas anteriores** e também dos primeiros 29 mapas de Saffron; o Fan Club foi **adicionado ao final**, sem deslocar slots já atribuídos a outros mapas. Isso reduz riscos de regressão nos saves de teste.

## 2. Teste no piloto isolado

No **Game.exe principal → Testar Kanto** (terceira opção quando há save), abra a cópia experimental. No menu de pausa, entre em **Testes Kanto (experimental)**. Foram acrescentados **10 atalhos**, chegando a 41:

| Atalho | Source MapID | Chegada (x,y) |
| --- | ---: | ---: |
| Rota 8 | 107 | 3,25 |
| Portaria oeste | 112 | 11,5 |
| Saffron City | 168 | 28,4 |
| Ginásio Sabrina | 171 | 15,23 |
| Fighting Dojo | 172 | 5,13 |
| Centro Pokémon | 169 | 7,8 |
| Silph Co. 1F | 178 | 8,20 |
| Silph Co. 5F | 182 | 28,2 |
| Silph Co. 11F | 188 | 7,2 |
| Silph Co. — elevador | 189 | 2,5 |

Os pontos vêm das coordenadas das **transferências de entrada auditadas**. Isto não significa que passabilidade, colisão e visualização já tenham sido aceitas manualmente. Atalhos não substituem portas, guardas nem roteiro canônico de Saffron e não concedem Marsh Badge.

## 3. Eventos mantidos fora desta entrega

O estudo de FireRed indica dependências para uma futura implementação:

- Guardas das portarias com o desbloqueio de acesso previsto no roteiro, sem forçar entrada prematura.
- Invasão da Silph Co., Card Key, teletransportadores, batalhas contra Rocket, rival, Giovanni e recompensa final.
- Fighting Dojo, escolha de prêmio único com espaço na equipe/PC, sem duplicação.
- Ginásio de Sabrina: rede de teletransportes, visão de treinadores e **Marsh Badge só após vitória real**.
- Interiores e transições de portas, itens, NPCs, cura, lojas e cenas da cidade.
- Estados persistentes, derrota/fuga, flags regionais, colisão e save/reload.
- HMs/insígnias e especiais restritos a Kanto conforme o Plano de Regiões v2.
- Correções anteriores **MAN-01, MAN-02 e MAN-03** continuam pendentes; a importação de terreno não as resolve.

**Não executar scripts Ruby originais da fonte, nem permitir eventos de guerra ou Story da Silph nesta fase.**

## 4. Testes e critérios para a próxima integração

- [x] Auditoria fonte FRLG para Saffron/Dojo/Silph, incluindo interior 173.
- [x] Mapeamento no manifesto e preparação de geometria dos 30 mapas com `preview_only`.
- [x] Proteção da ordem dos IDs já usados no piloto.
- [x] Atalhos experimentais definidos sem recompensas nem história.
- [x] **[CI Windows 43213494522](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43213494522) aprovada:** 101 mapas, 61 sem eventos, 41 atalhos, abertura nativa da Silph Co. e ginásio, Marsh não concedida e save/reload da campanha anterior.
- [x] **[Site checks 43213985203](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43213985203) aprovados:** 101 localidades publicadas, 54 perfis de treinadores anteriores preservados; 30 novas localidades de Saffron/Silph sem métodos de encontro ou treinadores.
- [x] **[Regressão 43213984922](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43213984922) aprovada:** execução Windows do RUN.bat, suíte Python/PBS/contratos e navegação/salvamento do site em Chromium.
- [ ] Testar manualmente tiles, prioridade, movimento, colisões, coordenadas e saves no Windows.
- [ ] Implementar portas, guardas, Silph Co., Dojo, Sabrina, Marsh Badge e progressão após autorização dos eventos; testar também JoiPlay.
- [ ] Não marcar Saffron como `playable` até a jornada e os eventos estarem integrados.

## Progresso

**Status geral atualizado:** [Barra de núcleos 7/16 (43,75%, faltam 9 passos) e Barra de aceite 1/16 (6,25%, faltam 15 passos)](KANTO_AVANCO_FUNCIONAL_07.md). Os 8/16 e 6/16 dos registros anteriores são históricos; a fase 11 continua apenas cenário, sem Sabrina ou Silph jogáveis.

**Barra 1 — Desenvolvimento funcional:** 8/16 (50%). **Barra 2 — Aceitação completa:** 1/16 (6,25%). As fases 09, 10 e 11 são novas áreas de cenário, ainda não completas funcionalmente. **Trilha de eventos FireRed:** 12 marcos próprios ainda sem medição quantitativa confiável.

**Próximo trabalho de mapa, sem eventos:** preparar Fase 12 — Cinnabar/Blaine em cópia isolada. Antes de liberar as fases 09–11 como histórias jogáveis, integrar as dependências de roteiro na ordem adequada e aceitar o checklist manual.
