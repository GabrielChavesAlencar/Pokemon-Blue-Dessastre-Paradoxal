# Hoenn — Etapa 04: Rustboro, Roxanne, Devon e Rusturf Tunnel

**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Data:** 14/11/2026  
**Referências:** [Etapa 03](HOENN_ETAPA_03_PETALBURG_ROUTE104_WOODS.md) · [Detonado Emerald](HOENN_DETONADO_EMERALD_REFERENCIA_ORGANIZADA.md)  
**Resultado:** implementação de código para um **piloto isolado**, com testes automatizados de contratos. **A jogabilidade no Game.exe/Android ainda NÃO está aprovada.**

## 1. Mapas reais auditados e acrescentados ao gerador

| MapID da fonte | Local |
|---:|---|
| 21 | Rustboro City |
| 22 | Centro Pokémon de Rustboro |
| 23 | Poké Mart de Rustboro |
| 24 | Casas de Rustboro |
| 25 | Escola de Treinadores |
| 26 | Devon Corporation, com atlas de andares |
| 27 | Ginásio de Rustboro |
| 130 | Rota 116, necessária para chegar ao túnel |
| 131 | Casa dos Escavadores |
| 157 | Rusturf Tunnel |

**Total do piloto: 28 mapas fonte (18 anteriores + 10 novos).** Os arquivos reais do ZIP privado foram conferidos contra o Git blob SHA-1 de cada MapID na revisão fixa do doador (c59233bdbaac4fbfeca6aa01c7f05be628da2a92). Não publicamos arquivos RXDATA, imagens, músicas ou recursos de terceiro no repositório.

### Conectividade

Bordas documentadas no PBS do doador:

- Rota 104 para Rustboro: 104,North,110,21,South,0 — **9 pares de tiles transitáveis** pela auditoria de geometria.
- Rustboro para Rota 116: 130,West,0,21,East,0 — **6 pares transitáveis**.
- Dezesseis pares de portas e escadas: Centro Pokémon, Mart, ginásio, escola, Devon, seis residências, casa dos escavadores, dois acessos ocidentais de Rusturf e escadas entre andares da Devon.

**Correção do projeto doador:** a saída original de Map27 Rustboro Gym aponta equivocadamente para Map16 (Petalburg). O gerador Hoenn remapeia essa porta para Map21 Rustboro, retornando ao exterior do mesmo ginásio, sem alterar o arquivo fonte original.

**Limitação:** a terceira saída do Rusturf Tunnel, rumo a Verdanturf (Map48), fica bloqueada por mensagem no piloto; Verdanturf não está no escopo. O limite norte de Rustboro rumo à Rota 115 também ainda não oferece uma nova rota verificadamente jogável.

## 2. Encontros selvagens e treinadores

Rota 116, grama (100%): Nincada 20%, Taillow 20%, Whismur 20%, Poochyena 28%, Abra 10%, Skitty 2%.

Rusturf Tunnel, caverna (100%): **Whismur 100%**, níveis históricos de referência 5–8.

Os níveis dos Pokémon e de treinadores no PBS são somente **dados-base do Emerald**. O escalonamento dinâmico e as evoluções em níveis maiores devem continuar sob responsabilidade do motor Blue/Decades. Não divulgar um nível fixo como se fosse o nível real do jogador.

Treinadores da etapa:

| Área | Nome | Equipe-base |
|---|---|---|
| Ginásio Rustboro | Josh | Geodude |
| Ginásio Rustboro | Tommy | 2 Geodude |
| Ginásio Rustboro | Marc | 2 Geodude |
| Ginásio Rustboro | **Roxanne** | Geodude, Geodude, Nosepass |
| Rota 116 | Joey | Machop |
| Rota 116 | Jose | Wurmple, Nincada |
| Rota 116 | Karen | Shroomish |
| Rota 116 | Janice | Marill |
| Rota 116 | Jerry | Ralts |
| Rota 116 | Dawson | Zigzagoon, Poochyena |
| Rota 116 | Sarah | Lotad, Zigzagoon |
| Rota 116 | Johnson | Shroomish, Lotad |
| Rota 116 | Clark | Geodude |
| Rota 116 | Devan | 2 Geodude |
| Rusturf Tunnel | Mike | Geodude, Geodude, Machop |
| Rusturf Tunnel | **Recruta Aqua** | Poochyena |

**Total: 16 encontros de treinadores**, dos quais 14 comuns + Roxanne + Recruta Aqua. O gerador usa PBS com versões específicas de mapa para treinadores comuns, versão 427 para Roxanne e 405 para o Recruta, com verificação de colisão de IDs e tipos na instalação Blue.

## 3. Eventos implementados como scripts Ruby

1. **Roxanne**: batalha da equipe original Emerald; derrota não concede insígnia, vitória única chama *BlueRegions.award* com **HOENN:STONE** e mantém o cálculo global de esmeraldas existente. Uma vitória não altera as insígnias nativas de Decades nem os marcos locais de Kanto/Johto. A TM Rock Tomb é entregue uma vez, somente se houver TM compatível registrada (move ROCKTOMB) e espaço na Bolsa; se faltar, a recompensa fica pendente.
2. **HM Cut**: o especialista na casa de Rustboro entrega HM01/HMCUT disponível na instalação. Os cinco obstáculos Cut da Rota 116 exigem a **Stone Badge de Hoenn**, HM na Bolsa, Pokémon com o movimento Cut e confirmação do usuário. Flags regionais e self-switch A impedem remoção indevida e reabertura após save/reload. Sprite da árvore usa recurso local; fallback é registrado como **visual não aprovado**.
3. **Escola de Treinadores**: professora entrega Quick Claw uma só vez se o item estiver cadastrado e houver espaço.
4. **Roubo Devon**: após a Stone Badge, acionadores automáticos próximos aos eventos originais de Rustboro informam que a Equipe Aqua roubou os produtos.
5. **Rota 116 e Briney**: Briney descreve o desaparecimento de Peecko; NPC da Devon informa a perseguição ao túnel.
6. **Rusturf Tunnel**: batalha de Recruta Aqua. Derrota permite tentar de novo; vitória registra libertação de Peecko. Os Devon Goods são concedidos uma vez, com recompensa pendente se a Bolsa estiver cheia. Quando o item DEVONGOODS não existe no Blue, um marcador regional substitui **somente o estado de missão** — sem criar item inválido.
7. **Devon Corporation**: devolução do pacote/estado de missão ao funcionário; presidente Stone entrega carta para Steven em Dewford. Sem o item LETTER, registra o compromisso em flag, deixando a etapa de Dewford implementar a entrega definitiva.
8. **Itens de chão**: dez pickups de fonte real — X Defense em Rustboro; Repel, Ether, Super Potion, Potion, X Sp. Atk, Black Glasses e HP Up na Rota 116; Poké Ball e Max Ether em Rusturf. São escondidos após a coleta, com proteção contra duplicação.
9. **Placas**: dez textos informativos em português, criados para o piloto; o código não executa diálogos do projeto doador indiscriminadamente.

**O que NÃO está completo:** a cutscene animada do roubo Devon, animação de Peecko/Briney, a entrega presencial da carta a Steven, a batalha final nativa verificada de Roxanne, seus sprites finais se houver fallback, Cut pelo sistema completo de HMs da engine, NPCs secundários de Rustboro, Rota 115, Verdanturf, Cut trees gráficos definitivos e as músicas exclusivas da região.

## 4. Segurança e testes

Arquivos principais:

- [Catálogo da etapa 4](../scripts/regions/hoenn_stage4.py)
- [Gerador isolado do piloto](../scripts/regions/pilot_hoenn.py)
- [Handlers Ruby](../scripts/regions/HoennPilot.rb)
- [Audit de origem RXDATA](../scripts/regions/audit_hoenn_baseline.py)
- [Audit de consistência](../scripts/regions/audit_hoenn_pilot_contract.py)
- [Catálogo público experimental](../site/public/data/hoenn-pilot.json)
- [Testes Python](../tests/test_hoenn_stage4.py)
- [Testes Ruby](../tests/hoenn_stage4_runtime.rb)
- [GitHub Actions](../.github/workflows/regression.yml)

Reprodução dos contratos de código, **sem Game.exe**:

~~~bash
python -m unittest discover -s tests -p "test_hoenn_*.py" -v
python scripts/regions/audit_hoenn_pilot_contract.py --strict
ruby -c scripts/regions/HoennPilot.rb
ruby tests/hoenn_stage4_runtime.rb scripts/regions/HoennPilot.rb
~~~

O instalador continua exigindo uma instalação Blue/Decades válida, árvore completa da revisão fixa, arquivos RXDATA originais e execução em **nova pasta isolada**, sem modificar os arquivos ou saves da versão principal. A CI valida contratos Python/Ruby e outros testes existentes, não o Game.exe. Um teste Ruby simulado não substitui a checagem real de eventos.

## 5. Checklist de aceite no Game.exe

- [ ] Montar cópia isolada com todos os 28 mapas, gráficos e seus IDs remapeados. Confirmar que compilação PBS real passa.
- [ ] Caminhar Petalburg Woods → norte da Rota 104 → Rustboro → Rota 116 → Rusturf; retornar pelo mesmo caminho sem travar.
- [ ] Testar retorno de todas as portas/escadas de Rustboro e, principalmente, saída do ginásio de Roxanne para Rustboro (nunca Petalburg).
- [ ] Testar três treinadores, Roxanne e vitória/derrota, concessão única de Stone Badge e cálculo acumulado de esmeraldas; confirmar que Kanto/Johto não mudaram.
- [ ] Confirmar TM Rock Tomb correta, bolsa cheia, HM Cut e cinco Cut trees, antes/depois de Stone Badge e sem Pokémon que saiba Cut.
- [ ] Confirmar evento automático do roubo Devon e perseguir Aqua, com derrota e volta ao túnel.
- [ ] Confirmar libertação de Peecko, entrega única do pacote, retorno à Devon e carta de Mr. Stone; salvar/recarregar em todas as etapas.
- [ ] Verificar 16 treinadores, dez itens (visíveis e ocultos), NPCs, placas, sprites, músicas e obstáculos reais.
- [ ] Confirmar que a terceira saída para Verdanturf está bloqueada até existir mapa/evento aprovado.
- [ ] Testar regressões em Kanto, Johto, Decades e Sinnoh; repetir no Android/JoiPlay.

**Aprovação técnica de scripts não significa aprovação jogável.**

## 6. Próxima etapa

**Etapa 05: Dewford/Slateport, Brawly, Granite Cave, Steven, embarcação de Mr. Briney e entregas Devon.** Só integrar essas áreas depois da verificação isolada de Rustboro/Rusturf e do controle de transições sem sobrescrever regiões existentes.
