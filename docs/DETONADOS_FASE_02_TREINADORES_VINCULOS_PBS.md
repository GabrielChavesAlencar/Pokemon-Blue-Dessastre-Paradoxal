# Fase 02 — auditoria de treinadores individuais e vínculos PBS

Data: 14/11/2026 · Estado: **fontes e instrumentação publicadas**, nenhum NPC novo autorizado em game/ ou Game.exe.

## Resultado

- [x] [Inventário de 13 treinadores](../data/regions/trainer-event-bindings-phase1.json): classe, nome, área, localização da fonte, MapID de staging ou origem, coordenadas do estágio/gerador, chamadas de batalha, versões PBS e evidência que falta.
- [x] [Auditor de vínculos](../scripts/regions/verify_trainer_event_bindings.py): compara o inventário com os próprios geradores/manifestos, sem executar scripts do jogo; com a opção --copy inspeciona mapas RXDATA e PBS em uma **cópia isolada** (somente leitura).
- [x] Proteção nova no gerador Hoenn: antes de montar o piloto, rejeitar colisão entre qualquer identidade PBS existente e os quatro treinadores da Rota 102. O relatório Hoenn pilot.json registra destinos MapID realmente alocados.
- [x] Portal: fichas individuais com tag **Em validação**, e registro específico do rival Brendan/May na Route 103 como **Ainda não adicionado** (ausente do gerador atual; não prova ausência no jogo já instalado).
- [x] Testes novos para drift do manifesto, duplicidade PBS, RXDATA sintético e interface do portal.

## Inventário 13/13 — referência em código, NÃO prova no Game.exe

| Região | Área | Pessoas | MapID | Situação |
|---|---|---|---|---|
| Hoenn | Route 102 | Calvin, Rick, Allen, Tiana | 102 **origem doadora**; remapeamento no piloto | Evento + PBS gerados, não testados aqui |
| Johto | Route 29 | Johto Mikey | 625 **staging privado** | Evento + PBS em estágio offline |
| Johto | Route 30 | Johto Joey, Johto Don | 626 **staging privado** | Offline |
| Johto | Route 31 | Johto Wade, Johto Ian | 627 **staging privado** | Offline |
| Johto | Violet Gym | Falkner | 677 **staging privado** | Offline |
| Johto | Sprout Tower 1F–3F | Nico, Troy, Li | 678–680 **staging privado** | Offline |

As cinco equipes da rota inicial de Johto são conteúdo de estágio do Blue, não uma transcrição integral de HGSS. Suas versões Normal/Master usam versões 0/1 e dependem do escalonamento compartilhado. Para Hoenn o gerador usa a versão 102 de PBS; o MapID de destino é resolvido pela cópia privada e não é 102 necessariamente.

**Progresso desta fase:** 13/13 vínculos identificados na fonte; **0/13 batalhas certificadas em execução nativa nesta entrega**. Não aumentar a barra de jogabilidade.

## Como executar auditoria e testes

A partir da raiz do repositório:

    python scripts/regions/verify_trainer_event_bindings.py --output .blue-work/trainer-bindings-source.json
    python -m unittest discover -s tests -p "test_regional_trainer_event_bindings.py" -v
    cd site
    npm test
    npm run build

Para testar uma cópia privada offline, informar --copy apontando para a pasta de estágio ou piloto, incluindo Data e PBS. A verificação de Hoenn requer também o arquivo Hoenn pilot.json, que contém a tabela de remapeamento da fonte para MapIDs de destino.

    python scripts/regions/verify_trainer_event_bindings.py --copy .blue-work/johto-staging-violet-v1 --scope JOHTO --output .blue-work/trainer-bindings-private.json
    python scripts/regions/verify_trainer_event_bindings.py --copy .blue-work/johto-staging-routes-v1 --scope JOHTO_ROUTES --output .blue-work/trainer-routes.json
    python scripts/regions/verify_trainer_event_bindings.py --copy .blue-work/hoenn-pilot --scope HOENN --output .blue-work/trainer-hoenn.json

A pasta .blue-work/hoenn-pilot é apenas um exemplo: use o caminho efetivo da cópia privada gerada no ambiente local. Os escopos adicionais são JOHTO_VIOLET e ALL. Escopos menores evitam exigir eventos de outras regiões em um estágio parcial.

Com --strict o auditor retorna código 2 se houver vínculos ausentes em uma cópia informada. O relatório continua a marcar Game.exe e compilação real como **não verificados**, mesmo quando os bytes do mapa e PBS coincidem.

## Trabalho pendente — próximo lote jogável

1. **H103 — Brendan/May:** identificar posição caminhável, sprite e equipe por inicial na fonte real; criar evento no piloto, versões PBS, flag única, vitória/derrota, save/reload. Não inventar tile nem equipe.
2. **H102 — quatro treinadores:** executar build de Hoenn em ambiente privado, compilar e medir mapas, NPCs e PBS; validar posicionamento e flags no Game.exe e Android.
3. **J29–31 — cinco treinadores:** verificar 625–627, scripts, equipes Normal/Master, encounters e save/reload em staging/piloto aprovado antes de instalar em game/.
4. **J-Violet — quatro treinadores:** verificar 677–680, sprites, Zephyr apenas após vitória e transições reais.
5. **Demais rotas, ginásios e Liga:** individualizar grupos pelo PBS/eventos reais, evitar duplicatas e só então atualizar a marcação do catálogo.

Não alterar Data de outras regiões, saves, o escalonamento 70% Normal/90% Master, HMs locais nem pós-jogo. Ver [issue #49](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/49).
