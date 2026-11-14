# Hoenn — Etapa 09/10: Mt. Pyre, esconderijos Magma/Aqua, Mossdeep e Mind Badge

**Data:** 14/11/2026  
**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Status:** **implementação técnica de piloto isolado**; sem aceite nativo em Game.exe/Android. A instalação principal Blue/Decades e os saves das outras regiões não são alterados.

Referências: [Etapa 08](HOENN_ETAPA_08_NORMAN_FORTREE_LILYCOVE.md) · [Detonado Emerald](HOENN_DETONADO_EMERALD_REFERENCIA_ORGANIZADA.md) · [Registro regional](../site/public/data/regions.json).

## 1. Origem, escopo e inventário

O inventário chegou a **138 mapas fonte** (110 anteriores + **28 novos**). São IDs da revisão fixa do doador `c59233bdbaac4fbfeca6aa01c7f05be628da2a92`, remapeados apenas na cópia isolada do Blue:

| IDs da fonte | Locais |
|---|---|
| 76–82 | Mossdeep City, Centro, Mart, casas, Game Corner, Centro Espacial e ginásio |
| 141, 144 | Rotas aquáticas 122 e 124 |
| 182–189 | Oito setores internos do esconderijo Magma |
| 206–213 | Mt. Pyre 1F–6F, exterior e cume |
| 215–217 | Três setores do esconderijo Aqua |

### Auditoria real do RXDATA

Diferentemente de uma lista de nomes inferida, esta etapa inclui uma auditoria **read-only** das estruturas RMXP e eventos originais da fonte pelo GitHub Actions. Ela leu os MapInfos e os MapIDs da revisão fixada, sem salvar ou publicar os arquivos de mapa de terceiros. Confira [o auditor](../scripts/regions/inspect_hoenn_stage9_donor.py) e [workflow dedicado](../.github/workflows/hoenn_stage9_source_audit.yml).

Foram confirmados, entre outros, os seguintes pontos: a entrada de Mt. Pyre na Rota 122 em `Map141 (22,29)` conecta à `Map206 (16,20)`; o esconderijo Magma possui escadas entre os andares 182–189; o esconderijo Aqua usa teletransportes no mapa 216 e tem submarino em `Map217 (19,22)`; o ginásio de Mossdeep está em `Map82`, com Tate `(25,11)` e Liza `(26,11)`; o Centro Espacial é `Map81`.

**Tratamento seguro das portas:** o gerador lê os eventos originais somente para extrair transferências diretas com destino estático, verificar limites e recriar eventos do próprio Blue em português. Ele **não executa nem copia scripts do doador**. Transições ambíguas (várias páginas/condições) ficam fora dessa extração, sem inventar warps livres. A passagem entre Rotas 121/122, Lilycove/124 e 124/Mossdeep deve depender do Surf real do Blue.

**Correção de infraestrutura:** a integração em PBS passou a publicar também todas as conexões verificadas nas Etapas 4–8, que antes eram usadas na auditoria geométrica mas não estavam todas sendo emitidas no PBS de saída. Este ponto ainda requer um teste da cópia instalada no Game.exe.

## 2. Batalhas e equipes-base

**Tate & Liza:** Claydol 41, Xatu 41, Lunatone 42 e Solrock 42, como no PBS do Emerald. A batalha está configurada como dupla no Blue e deve conceder **HOENN:MIND** somente após vitória. A TM Calm Mind é condicionada à existência de uma TM que ensine efetivamente o movimento e ao espaço na Bolsa.

Outros chefes: **Matt** (Mightyena/Golbat), **Maxie** e **Tabitha** nos esconderijos e no Centro Espacial. Além deles há **18 treinadores comuns** com posições verificadas em Mt. Pyre/ginásio, **4 recrutas Aqua em Mt. Pyre**, **7 recrutas Magma no esconderijo**, **5 recrutas Aqua no esconderijo** e **2 recrutas Magma no Centro Espacial**. São **42 novos registros**, totalizando **186 equipes catalogadas** no site.

Os times e níveis dos líderes vêm do PBS de referência; os **times dos recrutas de esconderijo continuam explicitamente provisórios**, pois ainda é necessário associar cada evento ao versionamento de sua equipe no PBS original. **Níveis não são fixos no jogo**, que conserva o escalonamento de Decades por insígnias/esmeraldas.

## 3. Progressão principal implementada (simulação de história)

1. Depois da Feather Badge, o jogador pode chegar a Mt. Pyre. Os recrutas Aqua precisam ser derrotados antes da cena de **Archie roubando o Red Orb**.
2. A anciã concede o **Magma Emblem**, respeitando espaço na Bolsa; a entrada secreta de Jagged Pass fica condicionada ao emblema.
3. No esconderijo Magma, os recrutas e **Tabitha/Maxie** são enfrentados; Groudon desperta por meio de evento de história. A animação cinematográfica nativa está pendente.
4. Após o evento Magma, o diálogo de **Capitão Stern em Slateport** registra o roubo do submarino pela Equipe Aqua.
5. O esconderijo Aqua de Lilycove passa a ficar acessível. Derrotar **Matt** libera a cena de fuga do submarino.
6. Depois da fuga, **Tate & Liza** podem ser desafiados em Mossdeep. Conquistar **HOENN:MIND** autoriza o movimento Dive **somente na região correta**, por meio do registro regional existente.
7. No Centro Espacial, o jogador enfrenta os recrutas Magma e a sequência de Tabitha/Maxie junto da história de Steven. **A luta cooperativa original com Steven não foi implementada como dupla nativa**: há uma sequência provisória de chefes, isolada e sinalizada, até validar o motor real.
8. Na casa de Steven em Mossdeep, após a Mind Badge e a defesa do Centro Espacial, o jogador recebe **HM Dive** se o item realmente ensinar DIVE e couber na Bolsa. A Super Rod também possui entrega protegida contra repetição.

Os eventos, derrotas, rematches de história, entregas tardias e save/reload usam flags em `hoenn_pilot`, não switches globais das demais regiões. Os bloqueios de Sootopolis, Seafloor Cavern, Victory Road, Elite Four e final da história **não foram declarados concluídos** — pertencem à Etapa 10.

## 4. Código, catálogo e testes

- [Definições Stage9](../scripts/regions/hoenn_stage9.py)
- [Gerador isolado, incluindo scanner dos RXDATA](../scripts/regions/pilot_hoenn.py)
- [Eventos e história em Ruby](../scripts/regions/HoennPilot.rb)
- [Contrato do catálogo](../scripts/regions/audit_hoenn_pilot_contract.py)
- [Auditoria do inventário doador](../scripts/regions/audit_hoenn_baseline.py)
- [Catálogo de Hoenn](../site/public/data/hoenn-pilot.json)
- [Testes Python de geometria/parties/eventos](../tests/test_hoenn_stage9.py)
- [Teste Ruby de fluxo de história, derrota e save](../tests/hoenn_stage9_runtime.rb)
- [Regressão geral](../.github/workflows/regression.yml)

Comandos de teste em máquina de desenvolvimento, **sem Game.exe**:

    python -m unittest discover -s tests -p "test_hoenn_*.py" -v
    python scripts/regions/audit_hoenn_pilot_contract.py --strict
    ruby -c scripts/regions/HoennPilot.rb
    ruby tests/hoenn_stage9_runtime.rb scripts/regions/HoennPilot.rb

**O teste automatizado mede consistência dos arquivos e dos fluxos simulados**. Nem teste Ruby nem teste com navegador de edição de PBS comprovam que as batalhas, animações ou transfers foram jogados com sucesso no Game.exe.

## 5. Teste real pendente no Game.exe/Android

- [ ] Criar a cópia isolada do Blue e compilar os **138 MapIDs** com os RXDATA privados de origem, tilesets, sprites, sons e PBS.
- [ ] Percorrer as rotas aquáticas com Surf até Mt. Pyre e Mossdeep, testando colisões, HM e retorno sem atalhos.
- [ ] Confirmar todas as entradas/saídas e teletransportes do esconderijo Aqua, e todas as escadas, pedras de Strength e saídas do esconderijo Magma.
- [ ] Conferir cada recruta Magma/Aqua, a equipe PBS exata por evento, derrota, rematch e progressão de flags.
- [ ] Visualizar as cenas de Red Orb, Magma Emblem, Groudon, roubo/fuga do submarino, em vez de apenas confirmar diálogos.
- [ ] **Restaurar e validar a mecânica de botões, estátuas e teleportes do ginásio de Tate & Liza**: a extração de warps diretos não substitui todas as páginas condicionais dos 90 eventos originais.
- [ ] Provar a batalha dupla de Tate & Liza com level scaling e a entrega única da Mind Badge/Calm Mind.
- [ ] Integrar a **batalha em dupla cooperativa real de Steven** no Centro Espacial; a versão atual é provisória e sequencial.
- [ ] Validar HM Dive no campo (mergulho, emergir, save/load e escopo de região) e a entrega da Super Rod.
- [ ] Revisar sprites/efeitos, músicas, traduções PT-BR, compatibilidade dos saves e regressões Decades/Kanto/Johto/Sinnoh, Windows e Android/JoiPlay.

## 6. Próximo estágio

**Etapa 10/10 — Sootopolis, Seafloor Cavern, Rayquaza, Juan, Ever Grande, Victory Road, Elite Four, Wallace e Hall of Fame**. **O progresso técnico (9/10) não significa 9 etapas jogáveis**; o aceite real no Game.exe continua independente da CI.
