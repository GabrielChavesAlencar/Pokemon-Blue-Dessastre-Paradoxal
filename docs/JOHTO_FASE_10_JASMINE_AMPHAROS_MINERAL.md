# Johto — Etapa 10/16: recuperação de Ampharos, Jasmine, Mineral Badge e Whirl Islands

**Estado:** PARCIAL — código da história, testes e contrato de mapas simbólicos publicados. **Os eventos não estão instalados em mapas RMXP nem disponíveis no Game.exe.**  
**Data:** 12/11/2026  
**Plano mestre:** [JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md)  
**Acompanhamento:** [JOHTO_ETAPAS.md](JOHTO_ETAPAS.md)  
**Dependência:** [Etapa 09 — Olivine, Lighthouse e Chuck](JOHTO_FASE_09_OLIVINE_CIANWOOD_CHUCK.md)

## Entregas concretas no GitHub

| Arquivo | Função |
|---|---|
| [scripts/regions/JohtoJasmine.rb](../scripts/regions/JohtoJasmine.rb) | Núcleo Ruby isolado para entrega única da medicina, cura de Ampharos, entrada no ginásio, batalha de Jasmine, badge MINERAL e bloqueio seguro das Whirl Islands |
| [tests/johto_jasmine_runtime.rb](../tests/johto_jasmine_runtime.rb) | Exercita um inventário simulado, bloqueios de história, derrota/vitória, badge única, save/reload e isolamento de regiões |
| [tests/test_johto_jasmine_runtime.py](../tests/test_johto_jasmine_runtime.py) | Integra o teste Ruby às verificações automatizadas Python |
| [data/regions/johto-phase10.json](../data/regions/johto-phase10.json) | Contrato simbólico de retorno Cianwood–Olivine, ginásio, mapa não auditado das ilhas, itens provisórios e provas de aceite pendentes |
| [tests/test_johto_phase10_contract.py](../tests/test_johto_phase10_contract.py) | Confere 6ª badge, regras dos itens, vínculo à Etapa 09, bloqueio das quatro entradas das ilhas e ausência de MapIDs inventados |

## Etapa 10 — sequência de história

### 1. Voltar a Olivine com a SecretPotion

O módulo anterior `BlueJohtoOlivineCianwood` já prepara o pedido de Jasmine, a retirada da medicina na farmácia de Cianwood e o retorno à cidade com Surf. O novo `BlueJohtoJasmine.deliver_medicine` exige **todas** estas condições:

- `olivine_medicine_requested == true`: Jasmine pediu o medicamento.
- `cianwood_medicine_received == true`: a farmácia entregou o item legítimo.
- `olivine_returned_with_medicine == true`: a travessia de volta foi realizada.
- `olivine_lighthouse_floor == 6`: o evento está no topo do Lighthouse.
- `GameData::Item.exists?(`**`:SECRETPOTION`**`) e o inventário real possui pelo menos uma unidade.
- O instalador do **piloto isolado** conferiu a interface de `PokemonBag` e criou o marcador `Data/blue-johto-ampharos-cure-ready.txt` com `BLUE_JOHTO_AMPHAROS_CURE_V1_READY`.

A função reutiliza a **mesma chave de item da Etapa 09**, evitando constantes divergentes. Exige `$bag.quantity(item) >= 1`, chama `$bag.remove(item, 1)` e verifica que a remoção retornou **`true`** e que a quantidade caiu **exatamente 1**. **Só então** marca:

```text
blue_regions["johto_pilot"]["olivine_medicine_delivered"] = true
blue_regions["johto_pilot"]["olivine_ampharos_healed"] = true
```

Entregar outra vez, tentar sem remédio, usar um marcador errado, um inventário inexistente ou uma remoção falsa **não avança o estado**. A apresentação física da cura, animações e retorno de Jasmine ao ginásio ainda exigem evento RMXP.

**Alerta para integração:** o resultado `true` de `PokemonBag#remove` e seu efeito na contagem ainda são **suposições a auditar na instalação real**. Se a API usar outro contrato, criar um adaptador validado e corrigir o script antes de gerar o marcador. Nunca escrever o marcador apenas para fazer a sequência prosseguir; caso o método remova mas retorne outro tipo, deve-se testar e solucionar isso antes de permitir consumo do item em um save real.

### 2. Ginásio de Olivine e Jasmine

`gym_entrance` exige a recuperação de Ampharos **e STORM Badge da própria Johto**, mantendo a sequência de insígnias do sistema existente. A batalha `jasmine` requer ainda:

1. Entrada registrada no Ginásio de Olivine.
2. Equipe PBS `BLUE_JOHTO_JASMINE`, versão 0, realmente compilada.
3. Marcador local `Data/blue-johto-jasmine-ready.txt` com conteúdo `BLUE_JOHTO_JASMINE_V1_READY`, criado somente após revisar os times.

Em **derrota**, não há recompensa. Após **vitória confirmada**, o código chama `BlueRegions.award(state, "JOHTO", "MINERAL")` e marca `olivine_jasmine_defeated`. A MINERAL é a **6ª insígnia local** no registro oficial de Johto e é contada como **uma** esmeralda no cartão global pelo cálculo já existente. Repetir a batalha ou reabrir o save não concede segunda insígnia. Não reimplementar balanceamento em eventos: continuar usando os hooks normal/master de Decades, incluindo as regras configuradas de nível e cobertura.

A MINERAL **não concede Whirlpool nem outro HM**. Surf continua exigindo FOG e Fly continua exigindo STORM; nenhuma conquista de Kanto deve ser usada para ignorar esses requisitos.

### 3. Whirl Islands — auditoria, sem liberação fictícia

`BlueJohtoJasmine.whirlpool_allowed?(tool_ready)` consulta a política existente: **GLACIER de Johto + ferramenta**, que pertence à fase posterior de Pryce. Ter STORM ou MINERAL não substitui essa autorização.

O método `whirl_islands_entry` está programado para **retornar sempre `false`**, mesmo que GLACIER e a ferramenta estejam presentes. Isso é proposital: sem dados reais, nenhum warp deve levar a uma caverna incompleta e prender o jogador.

O [contrato de mapas](../data/regions/johto-phase10.json) registra quatro entradas **candidatas** (NW, NE, SW, SE), andares planejados e a câmara de Lugia, **sem afirmar MapIDs, coordenadas, interiores jogáveis ou topologia real**. As listas de warps de entrada e saída estão vazias, e o encontro/captura de Lugia segue desabilitado. Auditar os caminhos ida/volta, a correnteza, o uso de Whirlpool e o bloqueio dos eventos de lendários na etapa apropriada.

## Testes automatizados

```powershell
python -m unittest discover -s tests -p "test_johto_jasmine_runtime.py" -v
python -m unittest discover -s tests -p "test_johto_phase10_contract.py" -v
python -m unittest discover -s tests -p "test_johto*.py" -v
python -m unittest discover -s tests -p "test_regions.py" -v
```

O teste Ruby valida a ausência de efeitos em Decades/Kanto, cada requisito da medicina, item removido exatamente uma vez, resposta falsa de `remove`, inconsistência entre sucesso e contagem, cura não duplicada, STORM antes da batalha, PBS não instalado, derrota, vitória, MINERAL única, esmeraldas, persistência em save/reload e bloqueio de Whirl Islands mesmo com GLACIER. O teste Python valida o grafo simbólico e os contratos.

**Esses testes não constituem prova de jogabilidade em Game.exe.** Eles usam inventário, API de batalha, item e save sintéticos; precisam ser repetidos com o motor real e o arquivo original de mapas depois da integração.

## Critérios de aceite integral ainda pendentes

- [ ] Obter um Map Pack real com direitos/gráficos auditados, hashes fixados e MapIDs remapeados sem colisão com Kanto ou Decades.
- [ ] Integrar física e visualmente a recuperação de Ampharos no 6º andar, com evento da SecretPotion e retorno ao ginásio.
- [ ] Confirmar a implementação concreta de `PokemonBag#quantity` e `#remove`, incluindo falhas/transações, reinício, cancelamento e save/reload.
- [ ] Compilar os times de Jasmine e validar balanceamento normal/Master Mode, sem criar times falsos no código de evento.
- [ ] Vincular batalha e MINERAL real, comprovando derrota sem badge e vitória única, com cartões regionais/global.
- [ ] Auditar Whirl Islands com entradas, pisos, gráficos, correntezas, espaços de retorno e bloqueio de Lugia até fase apropriada.
- [ ] Testar trajeto Cianwood → Olivine, retorno ao Lighthouse, cura, Ginásio, oceano e ilhas em piloto separado no Windows, com save/reload.
- [ ] Confirmar regressões Blue Studio e Kanto, manter saves de Decades intactos, testar JoiPlay quando possível.

**Barras de progresso:** integral técnico **0/16**, aceite de jogabilidade **0/16**. A Etapa 10 foi iniciada e permanece **PARCIAL**.
