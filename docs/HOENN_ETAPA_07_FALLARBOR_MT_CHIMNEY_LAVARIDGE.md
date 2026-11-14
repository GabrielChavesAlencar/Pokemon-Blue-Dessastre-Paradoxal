# Hoenn — Etapa 07: Fallarbor, Meteor Falls, Mt. Chimney e Lavaridge

**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Data:** 14/11/2026  
**Estado:** **IMPLEMENTAÇÃO TÉCNICA NO PILOTO ISOLADO** — NÃO aprovada como jogável no Game.exe/Android. Preserva o jogo principal Blue/Decades e os trabalhos de Kanto, Johto e Sinnoh.

Referências: [Etapa 06](HOENN_ETAPA_06_MAUVILLE_ROUTE110_WATTSON.md) · [Detonado Emerald](HOENN_DETONADO_EMERALD_REFERENCIA_ORGANIZADA.md) · [Registro regional](../site/public/data/regions.json).

## 1. Mapas da etapa: 27 novos, 85 acumulados

Os **MapIDs abaixo são os IDs de origem do pacote The Pokémon World Project - Hoenn**, na revisão fixa `c59233bdbaac4fbfeca6aa01c7f05be628da2a92`. O gerador atribui outros IDs livres na **cópia isolada**, lendo os arquivos RXDATA reais do ZIP privado e verificando a identidade SHA-1 dos blobs. Os RXDATA, tilesets, gráficos e áudios do doador não foram publicados no GitHub.

| MapIDs de origem | Conteúdo |
|---|---|
| 53–57 | Fallarbor Town, Centro, Mart, casas, Battle Tent |
| 58–63 | Lavaridge, Centro, Mart, casas, Herbal Shop, Ginásio Flannery |
| 117, 118, 120 | Rota 111, Casa dos Winstrate e casa de descanso |
| 121, 122 | Rota 112 e estação inferior do teleférico |
| 123, 124 | Rota 113 e oficina de cinzas vulcânicas |
| 125, 126, 128 | Rota 114, casa do Fossil Maniac e casa de Lanette |
| 177, 178, 179, 180 | Fiery Path, Mt. Chimney, estação superior e Jagged Pass |
| 191, 192 | Meteor Falls 1F e setor interno |

**Conectividade:** 23 pares de portas/escadas da fonte auditada, mais 7 bordas reais do PBS. As bordas com passabilidade comprovada no pacote privado tinham 20, 21, 10, 11, 11, 7 e 1 pares caminháveis, respectivamente. Estação inferior ↔ superior é **transferência por evento controlado**, não warp sem condição.

**Correção importante:** a casa do Fossil Maniac (Map126) retorna à **Rota 114 (Map125)**. O evento original do doador apontava indevidamente para a Rota 111 (Map117). Não foi editado o arquivo original.

## 2. Encontros selvagens e treinadores

A distribuição base do Emerald foi convertida para o Blue, sempre somando 100% em cada tabela, preservando as espécies:

| Área | Encontros-base |
|---|---|
| Rota 111 | Sandshrew, Trapinch, Baltoy, Cacnea |
| Rota 112 | Numel, Marill |
| Rota 113 | Spinda, Slugma, Skarmory |
| Rota 114 | Swablu, Lotad, Seedot, Lombre, Nuzleaf, Seviper, Zangoose, Surskit |
| Fiery Path | Numel, Grimer, Koffing, Machop, Slugma, Torkoal |
| Jagged Pass | Numel, Machop, Spoink, Combusken |
| Meteor Falls 1F | Zubat, Lunatone, Solrock |
| Meteor Falls interior | Golbat, Lunatone, Solrock |

Quando o PBS da fonte soma 200 pesos relativos, a tabela do piloto normaliza para 100, com arredondamentos explicitados em [hoenn_stage7.py](../scripts/regions/hoenn_stage7.py). Os **níveis apresentados são apenas referência da equipe Emerald**; a progressão, o level cap e as evoluções permanecem governados pelo motor Blue/Decades.

A fase cadastra **23 treinadores comuns**, **2 recrutas Magma**, Tabitha, Maxie e **Flannery**: **28 novas equipes**, total de **96 registros no catálogo público de Hoenn**. Sprites de substituição nativa são marcados como provisórios, nunca como aprovação visual.

## 3. História implementada em Ruby

1. Após o pacote de Stern e a Dynamo Badge, o evento de **Meteor Falls** registra o roubo do meteorito do Professor Cozmo.
2. O bloqueio de recrutas na Rota 112 permite liberar a estação do teleférico após a investigação. A viagem ao topo tem fallback seguro em erro de transferência e não altera progresso de outras regiões.
3. Em **Mt. Chimney**, os dois recrutas Magma devem ser vencidos antes de **Tabitha**; somente após Tabitha pode ocorrer a batalha contra **Maxie**. Perder uma batalha não marca vitória e permite tentar novamente.
4. Depois de vencer Maxie, a máquina libera o meteorito. Se o item `METEORITE_RSE` não existir na instalação Blue, um estado virtual de missão substitui **somente** a identidade do item. Bolsa cheia não conclui a retirada do item real.
5. Em **Lavaridge**, Flannery só aceita o desafio após Dynamo + Maxie + recuperação do meteorito. Vitória concede a **Heat Badge (HOENN:HEAT)** via BlueRegions.award, sem modificar a lista de insígnias nativas de Decades ou de outras regiões.
6. A TM Overheat é entregue uma vez se a TM candidata cadastrada **realmente ensinar Overheat**. Se faltar o item ou não houver espaço na Bolsa, a recompensa continua pendente.
7. O registro regional já determina que **Strength depende da Heat Badge**. A animação e as rochas/obstáculos nativos ainda exigem QA.

Equipe-base original de Flannery em Emerald: **Numel 24, Slugma 24, Camerupt 26, Torkoal 29**, com as características base e White Herb do Torkoal. Equipe de Tabitha: Numel, Poochyena, Numel, Zubat. Equipe de Maxie: Mightyena, Zubat, Camerupt.

## 4. Mecânicas e limites de escopo

- Ginásio Lavaridge: **11 pares verificados de pisos de queda/lançamento a vapor**, com transferências simuladas por eventos. Cinco vents sem parceiro equivalente e efeitos visuais de vapor originais ainda precisam de integração visual e teste real.
- **Fallarbor Battle Tent**, Winstrate House, oficina de cinzas e casa do Fossil Maniac têm área/interiores ou diálogos-base; seus sistemas completos de batalha, coleta de cinzas, fósseis e prêmios **não foram declarados implementados**.
- **Magma Hideout (Jagged Pass), Mirage Tower, Fossil Tunnel, Meteor Falls profundo, saída para Rota 115 e rotas além de Lavaridge** permanecem bloqueados. O piloto não publica áreas falsas para preencher esses caminhos.
- Os diálogos implementados são autorais e estão em **português brasileiro**. Ainda não substituem todas as interações e NPCs do Emerald.
- As músicas regionais continuam utilizando aliases disponíveis no piloto; as trilhas exclusivas de Mt. Chimney/Fallarbor/Lavaridge ainda não têm aprovação de audição manual.

## 5. Arquivos e testes

- [Definições da Etapa 7](../scripts/regions/hoenn_stage7.py)
- [Montador isolado do piloto](../scripts/regions/pilot_hoenn.py)
- [Handlers de história e batalhas](../scripts/regions/HoennPilot.rb)
- [Auditoria da origem](../scripts/regions/audit_hoenn_baseline.py)
- [Auditoria de contratos/site](../scripts/regions/audit_hoenn_pilot_contract.py)
- [Catálogo publicado do site](../site/public/data/hoenn-pilot.json)
- [Testes Python](../tests/test_hoenn_stage7.py)
- [Testes Ruby](../tests/hoenn_stage7_runtime.rb)
- [CI GitHub Actions](../.github/workflows/regression.yml)

Os testes rodam sem Game.exe:

    python -m unittest discover -s tests -p "test_hoenn_*.py" -v
    python scripts/regions/audit_hoenn_pilot_contract.py --strict
    ruby -c scripts/regions/HoennPilot.rb
    ruby tests/hoenn_stage7_runtime.rb scripts/regions/HoennPilot.rb

## 6. Aceite obrigatório no Game.exe / Android

- [ ] Compilar os **85 MapIDs** na cópia Blue com os arquivos RXDATA reais do ZIP privado, além de metadados, tilesets e gráficos originais;
- [ ] Andar Mauville → Rota 111 → Rota 112 / Fiery Path → Rota 113 → Fallarbor → Rota 114 → Meteor Falls;
- [ ] Verificar que o roubo do meteorito não acontece antes da história de Stern e Dynamo; retornar à Rota 112 e subir o teleférico, com retorno possível;
- [ ] Enfrentar e perder/vencer os dois recrutas Magma, Tabitha e Maxie; retirar o meteorito com Bolsa cheia e após salvar/recarregar;
- [ ] Descer Jagged Pass, chegar a Lavaridge e vencer/perder para Flannery, checando a Heat Badge e esmeraldas acumuladas;
- [ ] Testar **todos os pisos a vapor**, colisor e animações reais do ginásio, inclusive vent sem par;
- [ ] Testar TM Overheat, autorização de Strength, itens de chão, musicas, sprites, portas e textos PT-BR;
- [ ] Regressão de Decades, Kanto, Johto, Sinnoh e Android/JoiPlay. Nenhum teste Ruby simulado substitui esta etapa.

## 7. Próximo trabalho

**Etapa 8/10 — Petalburg, Fortree e Lilycove:** Norman, Weather Institute, Winona, Surf/Fly e novos eventos conforme o plano geral. Falhas observadas no teste nativo de Etapa 7 devem ser corrigidas antes de declarar a região jogável.
