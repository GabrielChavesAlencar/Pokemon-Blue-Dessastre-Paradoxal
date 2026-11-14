# Hoenn — Etapa 06: Rota 110, Mauville, Wattson e Cycling Road

**Data:** 14/11/2026  
**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Estado:** PILOTO ISOLADO — scripts e dados de implementação, **sem aceite de Game.exe/Android**. Referências: [Etapa 05](HOENN_ETAPA_05_DEWFORD_GRANITE_SLATEPORT.md), [Detonado Emerald](HOENN_DETONADO_EMERALD_REFERENCIA_ORGANIZADA.md).

## 1. Mapas e conexões auditadas

A Etapa 6 acrescenta **10 mapas fonte**, totalizando **58** no piloto:

| MapID Emerald | Área |
|---:|---|
| 41 | Mauville City |
| 42 | Centro Pokémon de Mauville |
| 43 | Poké Mart de Mauville |
| 44 | Casas de Mauville |
| 45 | Rydel's Cycles |
| 46 | Mauville Game Corner |
| 47 | Ginásio de Mauville |
| 113 | Rota 110 |
| 114 | Cycling Road / Route110-C |
| 115 | Portaria da Cycling Road |

O PBS doador da revisão fixa c59233bdbaac4fbfeca6aa01c7f05be628da2a92 usa as bordas **113,South,0,32,North,0** (Slateport) e **113,North,0,41,South,0** (Mauville). A verificação de passabilidade do ZIP privado encontrou **6 pares caminháveis** na primeira ligação e **10** na segunda.

A Cycling Road tem mapa próprio (114) e portaria (115). Seus quatro trajetos são **condicionais à bicicleta**, não warps livres. O doador possui tiles bloqueados nas linhas 8, 9 e 22 da portaria; os destinos foram corrigidos no piloto isolado para (3,7), (14,7), (3,21) e (14,21), após conferência com as células da origem. A saída da pista continua possível mesmo se a bicicleta não estiver mais na Bolsa, evitando prender saves antigos.

## 2. Equipes, encontros e nível dinâmico

Rota 110, grama: Electrike 30%, Poochyena 20%, Gulpin 15%, Oddish 10%, Wingull 10%, Plusle 8%, Minun 7%. Os pesos relativos da fonte (soma 200) foram normalizados para a tabela da engine (soma 100) sem retirar espécies.

**Wattson:** Voltorb 20, Electrike 20, Magneton 22, Manectric 24. PBS da cópia: BLUE_HOENN_WATTSON, versão 647.

**Wally:** Ralts 16, PBS BLUE_HOENN_WALLY, versão 641.

**Rival da Rota 110:** seis combinações de May/Brendan (versões 610, 611 e 612):
- Player Treecko: Wingull, Lombre, Combusken.
- Player Torchic: Lombre, Slugma, Marshtomp.
- Player Mudkip: Slugma, Wingull, Grovyle.

Além desses personagens, o piloto inclui **19 treinadores comuns** na Rota 110, Cycling Road e ginásio. São **27 registros adicionais** e **68 equipes acumuladas** no catálogo do site.

**Os níveis listados são de Emerald, usados somente como referência.** A escala de nível, evolução e batalha do Blue/Decades deve ser respeitada em todas as regiões.

## 3. Progressão e recompensas

1. A Rota 110 libera passagem de Slateport somente após o pacote entregue ao Capitão Stern.
2. O rival desafia o jogador na Rota 110. Derrota permite nova tentativa; vitória desbloqueia o Itemfinder, sem recompensas duplicadas se houver bolsa cheia/save-reload.
3. Em Mauville, Wally desafia com Ralts; a vitória libera o desafio de Wattson.
4. **Wattson** exige a sequência concluída, concede **HOENN:DYNAMO** via sistema BlueRegions.award **somente após a vitória**, sem escrever insígnias nativas de Decades/Kanto/Johto. A TM Shock Wave só é entregue se o item realmente ensinar o movimento, mantendo entrega pendente se necessário.
5. O morador de Mauville oferece Rock Smash (HM06/TM94), validando o movimento registrado. Seu uso de campo depende de **DYNAMO**, conforme o registro regional existente.
6. **Rydel:** o jogador escolhe Mach Bike ou Acro Bike, pode trocar e não deve duplicar nem perder a bicicleta anterior se o acréscimo da nova falhar.
7. **Cycling Road:** entrada apenas com item de bicicleta existente no Blue, retorno com rota segura, inclusive em save antigo.
8. **Ginásio de Wattson:** quatro interruptores e sete barreiras elétricas com self-switches; faltando sprite correto, o fallback fica rotulado como **não aprovado visualmente**. As barreiras com footprint de múltiplos tiles e o acionamento real do mapa exigem teste Game.exe.
9. Rotas 111 e 118, Trick House, New Mauville, Game Corner e batalhas secundárias não foram declaradas completas.

## 4. Arquivos atualizados no GitHub

- [Catálogo técnico da Etapa 6](../scripts/regions/hoenn_stage6.py)
- [Gerador isolado de Hoenn](../scripts/regions/pilot_hoenn.py)
- [Eventos Ruby e progressão](../scripts/regions/HoennPilot.rb)
- [Auditoria da fonte](../scripts/regions/audit_hoenn_baseline.py)
- [Auditoria dos contratos](../scripts/regions/audit_hoenn_pilot_contract.py)
- [Dados do site](../site/public/data/hoenn-pilot.json)
- [Testes Python](../tests/test_hoenn_stage6.py)
- [Teste Ruby de história](../tests/hoenn_stage6_runtime.rb)
- [CI do GitHub Actions](../.github/workflows/regression.yml)

Executar os testes independentes da engine:

    python -m unittest discover -s tests -p "test_hoenn_*.py" -v
    python scripts/regions/audit_hoenn_pilot_contract.py --strict
    ruby -c scripts/regions/HoennPilot.rb
    ruby tests/hoenn_stage6_runtime.rb scripts/regions/HoennPilot.rb

## 5. Aceite no Game.exe ainda pendente

- [ ] Montar os 58 mapas na cópia isolada usando o pacote RXDATA privado e os gráficos da instalação Blue, incluindo os PBS de treinadores/encounters.
- [ ] Caminhar Slateport → Route 110 → Mauville, enfrentando rival, Wally e Wattson; conferir batalha/rematch e persistência.
- [ ] Verificar dinamicamente a Dynamo Badge, TM Shock Wave, Itemfinder e HM/TM Rock Smash com bolsa cheia/save/reload, sem conceder insígnias às outras regiões.
- [ ] Validar os gráficos finais, interrupções, colisões e footprint dos sete portões, quatro interruptores e acesso ao líder.
- [ ] Testar Mach Bike, Acro Bike, controles e animação de pedalar e acrobacias, portaria superior/inferior e retorno após derrota ou save antigo.
- [ ] Confirmar os sete itens da rota/cidade, todos os interiores e os sprites de Wally/Wattson.
- [ ] Regressão no Windows, Android/JoiPlay, Decades, Kanto, Johto e Sinnoh.

**A CI prova os contratos testados, não gameplay no Game.exe.** O jogo principal permaneceu intocado.

## 6. Próximo estágio

**Etapa 07/10 — Fallarbor, Mt. Chimney, Lavaridge e Flannery**, incluindo eventos Magma e meteorito e novas rotas.
