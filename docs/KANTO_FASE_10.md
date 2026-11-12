# Kanto — Fase 10/16: Fuchsia City, Safari Zone e Koga

**Data:** 12/11/2026. **Escopo desta entrega:** prévia de mapas/tilesets apenas; nada de eventos, treinadores, encontros, itens, HMs, recompensas, história ou batalha de Koga.

A análise de eventos do FireRed está documentada em [KANTO_ROADMAP_EVENTOS_FIRERED.md](KANTO_ROADMAP_EVENTOS_FIRERED.md) e no [estudo de eventos](ESTUDO_EVENTOS_MAPA_POKEMON_FIRERED_RPG_MAKER_XP.md). Essa referência **não equivale a eventos instalados**. A expansão dos terrenos preserva os mapas anteriores e a jogabilidade da base Decades em uma cópia de testes.

## 1. Mapas de origem confirmados e incluídos (20)

IDs referem-se à **fonte Essentials FRLG pinada** e são convertidos para IDs exclusivos no piloto. Não são IDs GBA da decompilação pret nem IDs finais do Decades.

| ID origem | Mapa físico importado | Eventos no piloto |
|---:|---|---|
| 141 | Rota 18 — trecho próximo de Fuchsia | 0 |
| 142 | Portaria da Rota 18 / Cycling Road | 0 |
| 143 | Rota 18 — trecho Cycling Road | 0 |
| 144 | Fuchsia City | 0 |
| 145 | Centro Pokémon de Fuchsia | 0 |
| 146 | Poké Mart de Fuchsia | 0 |
| 147 | Ginásio de Koga | **0 — sem Koga** |
| 152 | Casa do Warden | **0 — sem Gold Teeth ou Strength** |
| 153 | Portão da Safari Zone | **0 — sem ingresso** |
| 155 | Safari Zone, setor sul | 0 |
| 156 | Safari Rest House, setor sul | 0 |
| 157 | Safari Zone, setor leste | 0 |
| 158 | Safari Rest House, setor leste | 0 |
| 159 | Safari Zone, setor norte | 0 |
| 160 | Safari Rest House, setor norte | 0 |
| 161 | Safari Zone, setor oeste | 0 |
| 162 | Safari Rest House, setor oeste | 0 |
| 163 | Secret House | **0 — sem HM Surf** |
| 164 | Rota 15 | 0 |
| 165 | Portaria da Rota 15 | 0 |

**Total planejado após importar:** **71 mapas** (40 com os eventos adaptados anteriormente + 11 mapas de prévia Celadon + 20 mapas de prévia Fuchsia/Safari), **31** IDs em `preview_only` e **0 eventos** nesses IDs. As conexões geográficas não substituem portões e escadas que dependem de eventos; transições com script continuam indisponíveis até a adaptação.

Fonte auditada no workflow Windows pela ferramenta [audit_fuchsia.py](../scripts/regions/audit_fuchsia.py), usando o hash SHA-256 de [kanto-source.json](../data/regions/kanto-source.json) e o artefato `kanto-fase-10-auditoria` na [CI](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/kanto-pilot-check.yml).

## 2. Como testar sem afetar a campanha principal

Entre no jogo principal com **Testar Kanto** (terceira opção), inicie a cópia isolada e abra **menu de pausa → Testes Kanto (experimental)**. Há nove atalhos novos, todos com destino verificado nas transferências da fonte:

| Atalho | Source MapID | Destino (x,y) |
|---|---:|---|
| Fuchsia City | 144 | 25,36 |
| Ginásio de Koga | 147 | 7,21 |
| Centro Pokémon de Fuchsia | 145 | 7,8 |
| Casa do Warden | 152 | 6,9 |
| Portão da Safari Zone | 153 | 4,7 |
| Safari Zone — sul | 155 | 26,31 |
| Safari Zone — norte | 159 | 25,6 |
| Safari Zone — oeste | 161 | 14,9 |
| Rota 15 | 164 | 16,25 |

O menu passa de **22 para 31 atalhos**. Não conceder Soul Badge, HM Surf, HM Strength, dinheiro, item de Safari, prêmio de ginásio nem flags de história apenas por teletransportar.

**Limitação:** a Safari Zone não possui sistema de passos, Safari Balls, capturas especiais ou ingresso ativo nesta versão de prévia. A Secret House também não entrega Surf. Os interiores não têm warp de ida e volta; o atalho permite inspeção isolada, não uma campanha completa.

## 3. Conexão com o roteiro FireRed e próximo trabalho

O estudo identifica como dependências da fase Fuchsia:

- Rota 12 e Rota 16 — Snorlax e Poké Flute; desbloqueios dependem do roteiro de Lavender/Celadon.
- Rotas 13–18 — treinadores, bloqueios de bicicleta e caminhos para Fuchsia.
- Koga — batalha, paredes do ginásio, Soul Badge e uso regional de Surf.
- Safari Zone — ingresso, Safari Balls, quantidade de passos, capturas, término de sessão, Gold Teeth e Secret House/Surf.
- Casa do Warden — Gold Teeth e Strength, sem duplicação.

Esses eventos permanecem **pendentes**, junto de MAN-01 (portas), MAN-02 (treinadores) e MAN-03 (telas de insígnias). O [roadmap detalhado](KANTO_ROADMAP_EVENTOS_FIRERED.md) mapeia as pré-condições e os testes. Não transformar o prêmio da Secret House em concessão ao entrar por atalho experimental.

## 4. Evidência e aceite

- [x] IDs, nomes e pontos de entrada consultados a partir da fonte FRLG com hash verificado.
- [x] Geometria e nomes colocados no manifesto e no exportador, com `preview_only` e sem novos eventos.
- [x] Atalhos de teste registrados, sem alterar o Decades principal nem saves existentes.
- [x] [CI Windows 43208948705](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43208948705) **aprovada**: 71 mapas, 31 em `preview_only`, zero eventos nessas áreas, 31 atalhos, abertura nativa dos cenários e Soul Badge ausente; importação em Decades descartável verificada.
- [x] [Site checks 43209021242](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43209021242) **aprovados**: 71 localidades e 54 perfis de treinadores anteriores; as 20 localidades novas não têm treinadores ou habitats.
- [x] [Regressão 43209244103](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43209244103) **aprovada**: testes de PBS/contratos, RUN.bat no Windows e navegação de site no Chromium.
- [ ] QA manual Windows: tilesets, passabilidade e coordenadas de chegada da Fuchsia City, gym e Safari.
- [ ] Eventos da Safari Zone, Warden e Koga traduzidos para Essentials e testados em gamepad/teclado.
- [ ] Soul Badge obtida **apenas após vitória real**, save/reload, HM Surf com requisito regional, derrota sem prêmio, ida/volta de interiores.

**Contadores permanecem inalterados nesta prévia:** Barra 1 **8/16 (50%)** e Barra 2 **1/16 (6,25%)**. Fase 09 (Erika) e 10 (Koga) ainda não estão funcionalmente completas. A auditoria de eventos também é uma trilha independente, sem percentual estimado.
