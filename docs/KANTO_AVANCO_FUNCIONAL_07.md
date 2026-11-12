# Kanto — Avanço funcional 07/16: núcleo da etapa 03 (Pallet → Pewter)

**Data:** 12/11/2026. **Situação:** núcleo funcional **aprovado na CI Windows** ([execução 43222828441](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43222828441)); evolução da primeira barra de **6/16 para 7/16**. Refere-se à etapa **03** do roadmap original, não a uma nova implementação de Cerulean/Misty (etapa 07), cujo núcleo já estava contado. Não confundir o marcador global `07/16` com a etapa **07 — Cerulean e Misty**, cujo núcleo já estava contado.

## O que foi implementado no jogo

1. **Missão do pacote de Oak:** o lojista real do Poké Mart de Viridian inicia o retorno a Pallet somente após o jogador escolher um inicial e antes de conquistar Boulder. O pacote é uma **flag local**; não inventar um item global que possa não existir em Decades.
2. **Retorno ao laboratório de Oak:** interagir com o evento já existente da escolha do inicial registra a entrega uma única vez e ativa `$player.has_pokedex` quando o método está disponível. O evento de escolha continua protegendo contra receber outro inicial.
3. **Loja sempre acessível:** o mesmo NPC continua oferecendo o estoque do Poké Mart depois de entregar ou concluir a missão. O jogador pode voltar sem ganhar prêmios extras.
4. **Salvamento/regressão:** `pilot_oak_parcel_received` e `pilot_oak_parcel_delivered` vivem somente em `BlueRegions` do save Kanto. Saves antigos com Boulder não são forçados a refazer o pacote. O conjunto de 5 Poké Balls que o piloto já entrega com o inicial foi preservado por compatibilidade, sem outro presente duplicado.
5. **Portas reais:** ampliadas as verificações estruturais de 8 para **11 pares** de transferências com retorno: casa do rival, duas casas de Viridian, portaria/casa escondida da Rota 2, duas entradas alternativas da portaria, duas entradas do Museu de Pewter e duas casas de Pewter. Não importa NPCs ou scripts originais de terceiros nos interiores.
6. **Treinadores:** mantidas as 50 linhas de visão `Sight(n)`, evento por aproximação, estado persistido `KANTO_<mapa>_<evento>`, página de conversa após vitória e ausência de prêmios na derrota.
7. **Isolamento:** os 61 cenários `preview_only` de Celadon, Fuchsia e Saffron não receberam novos eventos. O catálogo permanece em **109 MapIDs**, preservando os IDs anteriores.

## Provas automatizadas concluídas

- [x] **[CI Windows 43222828441](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43222828441):** verificação estrutural aprovou **11 transferências de ida e volta**, um único lojista de Viridian com `BlueKantoPilot.viridian_mart`, 50 treinadores `Sight(n)` e 61 mapas protegidos sem eventos.
- [x] **Teste nativo Ruby da mesma execução:** completou o ciclo **escolher inicial → receber pacote no Poké Mart → entregar em Pallet → voltar à loja**, verificando flags, Pokédex quando disponível, loja aberta e persistência após save/reload; batalhas simuladas na CI.
- [x] **[Regressão 43222828560](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43222828560) aprovada**, incluindo testes de código e geração do piloto. A mesma CI nativa também verificou abertura de janela e importação em cópia descartável de Decades.
- [x] Roadmap e status das duas barras atualizados, com referências às execuções.

## Teste de aceitação manual (mantido para a Barra 2)

No `Game.exe → Testar Kanto`, use **um save de teste novo ou separado**:

- [ ] Escolher um dos três iniciais; tentar escolher novamente não concede segundo Pokémon.
- [ ] Chegar ao Poké Mart de Viridian; o atendente informa o pacote e continua vendendo.
- [ ] Voltar ao laboratório de Oak, entregar e conferir a Pokédex; falar outra vez não entrega recompensas adicionais.
- [ ] Retornar ao Mart, confirmar compras normais, salvar, sair e recarregar.
- [ ] Testar as duas entradas do Museu de Pewter e ambas as saídas; testar as entradas da portaria secreta da Rota 2, inclusive portas secundárias.
- [ ] Confirmar direção, colisão, sprites e retorno de **todas as portas**, e o gatilho de Rick na Viridian Forest sem botão de ação.
- [ ] Vencer, perder e repetir um treinador; o jogo não deve conceder insígnia ou flag por derrota, nem reiniciar batalha vencida.
- [ ] Repetir testes em instalação existente, com verificação de saves antigos, e depois JoiPlay.

**Limites honestos:** não foram implementados todos os eventos do FireRed, NPCs opcionais, falas originais EN/PT-BR, Ginásio Viridian (mapa fonte 13) ou a Diglett's Cave completa (23). A entrega do pacote é uma adaptação **experimental** integrada ao piloto, não a reprodução integral do roteiro. A etapa 03 pode ter um **núcleo funcional testado** sem estar aceita integralmente na Barra 2.

**Contagem atual após CI:** **Barra 1 = 7/16 (43,75%, faltam 9 núcleos)**, pelas etapas 01, 03, 04, 05, 06, 07 e 08; **Barra 2 = 1/16 (6,25%, faltam 15 aceites)**. A missão e as correções não são consideradas totalmente aceitas sem gameplay manual. Os valores anteriores de 6/16 e 1/16 permanecem preservados no [registro histórico de reavaliação](KANTO_REAVALIACAO_BARRAS_2026-11-12.md).
