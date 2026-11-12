# Kanto — Avanço funcional 07/16: núcleo da etapa 03 (Pallet → Pewter)

**Data:** 12/11/2026. **Objetivo:** transformar parte da correção de Pallet → Pewter (etapa **03** do roadmap original) em um **sétimo núcleo funcional** da Barra 1, **somente após CI aprovada**. Não confundir o marcador global `07/16` com a etapa **07 — Cerulean e Misty**, cujo núcleo já estava contado.

## O que foi implementado no jogo

1. **Missão do pacote de Oak:** o lojista real do Poké Mart de Viridian inicia o retorno a Pallet somente após o jogador escolher um inicial e antes de conquistar Boulder. O pacote é uma **flag local**; não inventar um item global que possa não existir em Decades.
2. **Retorno ao laboratório de Oak:** interagir com o evento já existente da escolha do inicial registra a entrega uma única vez e ativa `$player.has_pokedex` quando o método está disponível. O evento de escolha continua protegendo contra receber outro inicial.
3. **Loja sempre acessível:** o mesmo NPC continua oferecendo o estoque do Poké Mart depois de entregar ou concluir a missão. O jogador pode voltar sem ganhar prêmios extras.
4. **Salvamento/regressão:** `pilot_oak_parcel_received` e `pilot_oak_parcel_delivered` vivem somente em `BlueRegions` do save Kanto. Saves antigos com Boulder não são forçados a refazer o pacote. O conjunto de 5 Poké Balls que o piloto já entrega com o inicial foi preservado por compatibilidade, sem outro presente duplicado.
5. **Portas reais:** ampliadas as verificações estruturais de 8 para **11 pares** de transferências com retorno: casa do rival, duas casas de Viridian, portaria/casa escondida da Rota 2, duas entradas alternativas da portaria, duas entradas do Museu de Pewter e duas casas de Pewter. Não importa NPCs ou scripts originais de terceiros nos interiores.
6. **Treinadores:** mantidas as 50 linhas de visão `Sight(n)`, evento por aproximação, estado persistido `KANTO_<mapa>_<evento>`, página de conversa após vitória e ausência de prêmios na derrota.
7. **Isolamento:** os 61 cenários `preview_only` de Celadon, Fuchsia e Saffron não receberam novos eventos. O catálogo permanece em **109 MapIDs**, preservando os IDs anteriores.

## Provas exigidas antes de contar este marco como o sétimo

- [ ] A verificação estrutural confirma **11 transferências de ida e volta**, o único lojista de Viridian com `BlueKantoPilot.viridian_mart`, 50 treinadores `Sight(n)` e 61 mapas protegidos sem eventos.
- [ ] O teste nativo Ruby percorre o ciclo **iniciar com Oak → receber pacote no Poké Mart → entregar em Pallet → retornar ao comércio**, comprovando flags, Pokédex quando disponível, loja aberta e persistência após reload.
- [ ] A regressão geral de Python/PBS, abertura da engine e portal passa na CI.
- [ ] O guia e os status das duas barras são atualizados com o ID da execução bem-sucedida, sem usar a mera presença de código para marcar sucesso.

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

**Regras de contagem:** após CI totalmente aprovada, Barra 1 muda **6/16 → 7/16 (43,75%, faltam 9)**; Barra 2 permanece **1/16 (6,25%, faltam 15)** até aceitação real de uma etapa adicional. Antes disso, manter 6/16 e 1/16.
