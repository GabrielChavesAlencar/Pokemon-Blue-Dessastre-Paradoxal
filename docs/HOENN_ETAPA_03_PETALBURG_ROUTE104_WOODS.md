# Hoenn — Etapa 03: Petalburg, Rota 104 e Petalburg Woods

**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Data:** 14/11/2026  
**Referências:** [Etapa 01](HOENN_AUDITORIA_PILOTO_ETAPA_01.md), [Etapa 02](HOENN_ETAPA_02_ABERTURA_RIVAL_RECOMPENSAS.md), [Detonado Emerald](HOENN_DETONADO_EMERALD_REFERENCIA_ORGANIZADA.md).  
**Status:** IMPLEMENTAÇÃO TÉCNICA DE PILOTO ISOLADO — NÃO APROVADO COMO JOGÁVEL NO GAME.EXE.

## 1. Nove mapas novos no piloto

| ID fonte | Local | Cobertura |
|---:|---|---|
| 16 | Petalburg City | Entradas das duas rotas, ginásio, casas, placas |
| 17 | Centro Pokémon de Petalburg | Enfermeira, cura/retorno |
| 18 | Poké Mart de Petalburg | Balcão e loja |
| 19 | Casas de Petalburg | Casa de Wally e outras residências |
| 20 | Ginásio de Petalburg | Norman e roteiro inicial de Wally, sem luta de ginásio |
| 104 | Rota 104 | Treinadores, itens, portas e floresta |
| 105 | Casa de Mr. Briney | NPC antes de Peecko ser resgatada |
| 106 | Pretty Petal Flower Shop | Presente único Wailmer Pail |
| 156 | Petalburg Woods | Equipe Aqua, funcionário Devon, itens, treinadores |

**Total da cópia:** 18 mapas (9 já existentes + 9 novos). São IDs da fonte, remapeados para IDs livres dentro da cópia isolada. Não representam mapas aprovados na instalação principal. Não foram distribuídos RXDATA, artes, ROMs ou músicas do doador.

### Bordas e entradas físicas

Map connections confirmadas no PBS da fonte: 102,West,0,16,East,10 (Rota 102 → Petalburg) e 104,East,50,16,West,0 (Rota 104 → Petalburg), além de onze pares de portas/warps dos nove novos mapas.

O atlas da Rota 104 no projeto doador retorna de alguns interiores para células bloqueadas (coordenadas entre x=5 e x=32). A implementação autoral do **piloto isolado** retifica os retornos para as células caminháveis ao sul das portas reais: (127,51), (115,19), (120,39), (142,43) e (120,31). Não é uma modificação dos mapas do doador nem do jogo principal.

Uma verificação local **somente de geometria**, feita sobre os RXDATA da fonte privada com leitura Ruby Marshal e cálculo conservador de passabilidade, partiu da casa (Map 8, x25, y6) e alcançou 4.506 células em 18 mapas. **Todos os 50 pontos obrigatórios** do grafo configurado eram alcançáveis; as seis bordas tinham interseções transitáveis. Isso NÃO garante interação, cutscene, som, sprites, recompensas ou jogabilidade no Game.exe.

## 2. Encontros selvagens baseados em Emerald

- **Rota 104, grama:** Poochyena 40%, Marill 20%, Wurmple 20%, Taillow 10%, Wingull 10%.
- **Petalburg Woods, grama:** Wurmple 25%, Poochyena 30%, Shroomish 15%, Cascoon 10%, Silcoon 10%, Slakoth 5%, Taillow 5%.

Cada tabela soma 100%. Os níveis nos PBS e no catálogo são **base histórica**, não níveis fixos para confrontos escalonados do Blue/Decades. Pesca, Surf e capturas roteirizadas ainda precisam de integração específica.

## 3. Dez novos encontros de treinadores

| Área | Treinador | Equipe histórica |
|---|---|---|
| Rota 104 | Youngster Billy | Zigzagoon 5, Seedot 7 |
| Rota 104 | Fisherman Darian | Magikarp 9 |
| Rota 104 | Lady Cindy | Zigzagoon 7 |
| Rota 104 | Rich Boy Winston | Zigzagoon 7 |
| Rota 104 | Lass Haley | Lotad 6, Shroomish 6 |
| Rota 104 | Twins Gina & Mia | Seedot 6, Lotad 6 (Double Battle) |
| Rota 104 | Fisherman Ivan | Magikarp 5/6/7 |
| Petalburg Woods | Bug Catcher James | Nincada 6 × 2 |
| Petalburg Woods | Bug Catcher Lyle | Wurmple 3 × 4 |
| Petalburg Woods | Recruta Aqua | Poochyena 9 |

O gerador cria versões PBS 104 e 156 para treinadores comuns e versão 304 para o recruta, cria um tipo autoral BLUE_HOENN_AQUA e verifica duplicatas, tipos nativos e disponibilidade dos sprites. As gêmeas possuem dois eventos físicos vinculados à mesma vitória; só iniciam a dupla quando o jogador pode usar dois Pokémon. Fallback de sprite não é aceito como aprovação visual.

## 4. Eventos roteirizados

1. **Petalburg:** ao entrar no ginásio, Norman conhece o jogador e apresenta Wally; a captura de Ralts está **narrada em português e registrada em flag**, mas a batalha/cena animada de captura por Wally NÃO foi implementada.
2. **Norman:** desafio de ginásio após quatro insígnias pertence a etapa posterior. Ainda NÃO há Balance Badge nem batalha de Norman nessa entrega.
3. **Rota 104:** eventos de treinadores, placas em português, itens e acesso ao mesmo mapa de Petalburg Woods por três portas originais.
4. **Floricultura:** Wailmer Pail dado uma única vez, com proteção de bolsa cheia, save e recarga.
5. **Casa de Briney:** diálogo sobre Peecko antes da missão de Rusturf; viagem marítima não liberada prematuramente.
6. **Petalburg Woods:** devon e Recruta Aqua. Uma vitória registra o marco do combate; Great Ball só é marcada como entregue quando cabe na bolsa. Uma derrota não conta como vitória e o treinador deve poder ser desafiado novamente.
7. **Itens do chão:** 20 pontos de coleta, visíveis/ocultos, baseados em coordenadas do doador, com self-switch A e flag exclusiva de Hoenn para bloquear duplicação.
8. **Placas:** 9 mensagens próprias em português, sem reproduzir diálogos originais do doador.

**Pendente:** a captura de Wally animada, demais NPCs/diálogos, Cut trees, plantio/rega de Berries, pescas, músicas exclusivas, interiores adicionais e a saída ao norte para Rustboro. Não interpretar preparação de dados como gameplay.

## 5. Arquivos publicados (sem binários de terceiros)

- [hoenn_stage3.py](../scripts/regions/hoenn_stage3.py): mapas, posições, conexões, equipes, itens e encontros.
- [pilot_hoenn.py](../scripts/regions/pilot_hoenn.py): expansão de nove mapas, remapeamento, travessias, PBS, sprites locais e geração isolada.
- [HoennPilot.rb](../scripts/regions/HoennPilot.rb): eventos, recompensas e flags.
- [audit_hoenn_baseline.py](../scripts/regions/audit_hoenn_baseline.py): agora confere 18 mapas.
- [audit_hoenn_pilot_contract.py](../scripts/regions/audit_hoenn_pilot_contract.py): valida catálogos e contratos de código.
- [hoenn-pilot.json](../site/public/data/hoenn-pilot.json): 18 localidades, 14 treinadores-base, status ainda experimental.
- [test_hoenn_stage3.py](../tests/test_hoenn_stage3.py): testes Python de mapas, templates, recompensas, offsets e seguranças.
- [hoenn_stage3_runtime.rb](../tests/hoenn_stage3_runtime.rb): testes Ruby de Norman, Wally, Aqua, itens, gêmeas e recarga.
- [regression.yml](../.github/workflows/regression.yml): inclui o novo teste Ruby.

## 6. Testes reproduzíveis sem Game.exe

~~~bash
python -m unittest discover -s tests -p "test_hoenn_*.py" -v
python scripts/regions/audit_hoenn_pilot_contract.py --strict
ruby -c scripts/regions/HoennPilot.rb
ruby tests/hoenn_pilot_runtime.rb scripts/regions/HoennPilot.rb
ruby tests/hoenn_stage3_runtime.rb scripts/regions/HoennPilot.rb
~~~

### Aceite real ainda pendente

- [ ] Montar cópia isolada com a instalação Blue local e revisão fixa da fonte de Hoenn; compilar o PBS e todos os 18 mapas.
- [ ] Caminhar Rota 102 → Petalburg → Rota 104 → Woods (três entradas e retornos), depois voltar sem travar.
- [ ] Entrar/sair do Centro, Mart, três casas, ginásio, casa de Briney e floricultura; testar cura/blackout e save/reload.
- [ ] Testar equipes, sprites, linhas de visão, duplas, vitória/derrota e persistência de todos os dez treinadores novos.
- [ ] Testar presente Wailmer Pail, vinte itens, bolsa cheia, Great Ball de Devon e não duplicação.
- [ ] Validar início com Norman e a narrativa provisória de Wally; construir a cutscene real de captura depois.
- [ ] Conferir NPCs não implementados, árvores Cut, berries, faixas musicais e saída norte da Rota 104.
- [ ] Executar regressões do jogo base, Kanto, Johto, Sinnoh e Android/JoiPlay.

**Barra de engenharia:** alterações e testes sintéticos documentados.  
**Barra de jogabilidade:** nenhuma aprovação nova sem sessão Game.exe/Android documentada.

## 7. Próxima etapa

Etapa 04 — Rustboro, Roxanne, Devon e Rusturf Tunnel: primeira insígnia de Hoenn, Cut, resgate de Peecko e continuidade real ao norte de Petalburg Woods. A Etapa 03 não deve ser considerada jogável enquanto faltar teste nativo.
