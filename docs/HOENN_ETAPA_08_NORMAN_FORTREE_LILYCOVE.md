# Hoenn — Etapa 08: Norman, Surf, Fortree, Weather Institute e Lilycove

**Data:** 14/11/2026  
**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Status real:** implementação técnica de dados/scripts no **piloto isolado de Hoenn**. Não instalada nem aprovada como jogável no Game.exe/Android. Não altera a instalação principal Blue/Decades, os saves existentes, nem os projetos de Kanto, Johto ou Sinnoh.

Referências: [Etapa 07](HOENN_ETAPA_07_FALLARBOR_MT_CHIMNEY_LAVARIDGE.md), [Detonado de Emerald](HOENN_DETONADO_EMERALD_REFERENCIA_ORGANIZADA.md), [Registro regional](../site/public/data/regions.json).

## 1. Inventário de mapas

Acrescentados **25 MapIDs de origem** ao piloto, total acumulado **110 mapas**. São os IDs de arquivo RXDATA do projeto The Pokémon World Project - Hoenn, revisão fixa `c59233bdbaac4fbfeca6aa01c7f05be628da2a92`. O gerador remapeia os IDs em uma cópia privada do Blue; **nenhum RXDATA de terceiros foi enviado ao repositório público**.

| ID fonte | Local |
|---|---|
| 48–52 | Verdanturf Town, Centro, Mart, casas e Battle Tent |
| 64–68 | Fortree City, Centro, Mart, casas nas árvores e Ginásio de Winona |
| 69–75 | Lilycove City, porto, Centro, Department Store, casas/motel, museu e Contest Hall |
| 132–133 | Rota 117 e Day Care |
| 134–137 | Rotas 118 e 119, casa da Rota 119 e Weather Institute |
| 138–139 | Rotas 120 e 121 |

**Petalburg City e seu ginásio (Map20) já existiam desde a Etapa 3.** A Etapa 8 reutiliza o mapa, agora com **24 pares de portas internas** do ginásio de Norman e sete treinadores.

A auditoria preserva **39 pares de transições internas** entre mapas e **oito conexões de borda passáveis**, especialmente Mauville→Verdanturf, Mauville→Rota 118, Rota 118→119, Rota 119→Fortree, Fortree→Rota 120, Rota 120→121 e Rota 121→Lilycove. Verificação independente dos tiles do ZIP real identificou 4, 6, 6, 18, 5, 4, 10 e 4 passagens caminháveis por conexão, respectivamente.

**Correções de segurança de mapa:** as bordas originais com destino físico obstruído (incluindo Rota 118→Fortree direto e conexões paralelas inconsistentes na Rota 119) não foram copiadas como atalhos falsos; os dois Kecleon exigem Devon Scope. A portaria de Cycling Road continua preservada. O Day Care usa somente a entrada correta a partir da Rota 117, evitando duplicidade de acesso indevido.

## 2. Batalhas-base e balanceamento

Os dados-base do Emerald são referências, não níveis fixos. O nível real e as evoluções dos treinadores e selvagens são governados pelo motor Blue/Decades e o cálculo de esmeraldas/insígnias.

| Personagem | Equipe base de Emerald | Marco |
|---|---|---|
| **Norman** | Spinda 27, Vigoroth 27, Linoone 29, Slaking 31 | **HOENN:BALANCE** |
| **Winona** | Swablu 29, Tropius 29, Pelipper 30, Skarmory 31, Altaria 33 | **HOENN:FEATHER** |
| **Shelly** | Carvanha 28, Mightyena 28 | Batalha de história no Weather Institute |

O capítulo também contém **29 treinadores comuns**, **quatro recrutas Aqua**, duas batalhas de rival com **três times por inicial** tanto para May quanto Brendan: seis versões do rival na Rota 119 e seis em Lilycove. Total **48 novos registros de equipes**; catálogo de Hoenn chega a **144 registros**.

**Encontros de grama:** Rotas 117, 118, 119, 120 e 121. Tabelas de 100% cada; espécies raras da fonte (incluindo Kecleon, Grovyle, Absol, Surskit e Seedot) são preservadas e visíveis no catálogo. Não foram inventados NPCs, batalhas ou encontros aquáticos para substituir áreas não verificadas.

## 3. Fluxo de história e recompensas

1. O jogador retorna ao **ginásio de Norman** após as quatro primeiras insígnias de Hoenn. A vitória concede `HOENN:BALANCE` via `BlueRegions.award` e uma TM Facade verificada; a derrota não concede nada e permite tentar novamente.
2. A família de Wally, já incluída no piloto da Etapa 3, passa a entregar **HM Surf**, uma única vez e apenas após a Balance Badge. O item só é entregue se existir na instalação Blue e ensinar realmente `SURF`. **Conceder HM não comprova que a travessia aquática funciona nativamente.**
3. O pescador na Rota 118 entrega **Good Rod**, protegida contra repetição; o Day Care possui informação de atendimento, **não um sistema completo de ovos**.
4. No **Weather Institute**, quatro recrutas Aqua precisam ser derrotados. Depois há confronto com **Shelly**. Só após a vitória, o pesquisador pode presentear um **Castform**, usando a API nativa de entrega, sem duplicação mesmo com falha/sem espaço.
5. O rival pode ser enfrentado na **Rota 119** depois da missão Weather Institute. A vitória libera HM **Fly** se houver item nativo que ensina FLY; a habilidade de campo só será autorizada depois da Feather Badge.
6. **Steven** oferece o **Devon Scope** depois da batalha da Rota 119. Os bloqueios de Kecleon em Fortree e na Rota 120 dependem do item, têm self-switch de remoção e salvam progresso regional. **A animação e a batalha real de Kecleon ainda não foram incorporadas.**
7. **Winona** só aceita o desafio após Balance, Weather Institute, rival da Rota 119 e Devon Scope/Kecleon. A vitória concede `HOENN:FEATHER` e a TM Aerial Ace, sem alterar as insígnias de Decades ou Kanto.
8. Em **Lilycove** existe outra batalha de rival, dependente da Feather Badge. O porto, museu, loja de departamentos, Contest Hall, Safari Zone e Aqua Hideout permanecem com **conteúdo parcial ou acesso bloqueado**, sem serem classificados como plenamente jogáveis.

Os seguintes marcos são exclusivamente **regionais**: `STONE`, `KNUCKLE`, `DYNAMO`, `HEAT`, `BALANCE`, `FEATHER`. A autorização de campo já prevista no registro de regiões determina **Surf = HOENN:BALANCE; Fly = HOENN:FEATHER**. Todo o progresso persiste sob a chave `hoenn_pilot` e não mexe no save das outras regiões.

## 4. Itens e auditoria de dados

Foram preparados **39 pickups de itens visíveis/ocultos**, com posições lidas de eventos do RXDATA original. Cada pickup usa verificação de Bolsa e self-switch, impedindo duplicações ao salvar/carregar.

A verificação dos blobs das **25 novas fontes RXDATA** deve sempre comparar seus SHA-1 de Git blob com a revisão auditada antes de montar a cópia. O site [hoenn-pilot.json](../site/public/data/hoenn-pilot.json) agora documenta **110 locais / 144 equipes**, com status explícito `SCRIPTED_ISOLATED_PILOT_NOT_GAMEPLAY_APPROVED`.

## 5. Arquivos publicados e testes reproduzíveis

- [Definições de mapa/evento Stage8](../scripts/regions/hoenn_stage8.py)
- [Gerador isolado de Hoenn](../scripts/regions/pilot_hoenn.py)
- [Handlers Ruby](../scripts/regions/HoennPilot.rb)
- [Auditoria da fonte](../scripts/regions/audit_hoenn_baseline.py)
- [Auditoria de contratos do catálogo](../scripts/regions/audit_hoenn_pilot_contract.py)
- [Dados do site](../site/public/data/hoenn-pilot.json)
- [Testes Python](../tests/test_hoenn_stage8.py)
- [Simulação Ruby (Norman → Lilycove)](../tests/hoenn_stage8_runtime.rb)
- [GitHub Actions](../.github/workflows/regression.yml)

Comandos de desenvolvimento **sem Game.exe**:

    python -m unittest discover -s tests -p "test_hoenn_*.py" -v
    python scripts/regions/audit_hoenn_pilot_contract.py --strict
    ruby -c scripts/regions/HoennPilot.rb
    ruby tests/hoenn_stage8_runtime.rb scripts/regions/HoennPilot.rb

A CI Python/Ruby cobre integridade de IDs, ausência de sobreposições, times/itens, derrotas, Bolsa cheia, entrega tardia e save/reload. **CI aprovada não equivale a teste nativo Game.exe**.

## 6. Checklist de aceite ainda pendente no Game.exe

- [ ] Montar e compilar os **110 mapas fonte** reais numa cópia separada do Blue com MapInfos/Tilesets/gráficos do ZIP auditado.
- [ ] Testar as 24 portas do ginásio de Norman, incluindo posição do jogador, retorno e colisão das salas.
- [ ] Testar Norman, Balance Badge e o recebimento real de Facade/Surf após salvar e recarregar. Conferir permissões regionais e cálculo de esmeraldas.
- [ ] Testar a travessia aquática Surf na Rota 118/119, inclusive múltiplas regiões/saves e retorno correto.
- [ ] Testar Weather Institute com quatro recrutas, Shelly e Castform, incluindo party/box cheia e derrotas.
- [ ] Testar o rival na Rota 119, entrega de Fly, Steven/Devon Scope, Kecleon bloqueado e liberação de Fortree.
- [ ] Testar o ginásio de Winona, obstáculos giratórios/mecanismos originais, Feather Badge e Fly na interface de mapa.
- [ ] Testar rival de Lilycove, interiores da loja, Contest Hall e porto, sem fingir que os sistemas opcionais estão finalizados.
- [ ] Auditar sprites e músicas, cenas PT-BR, água/colisão, itens e regressões de Decades, Kanto, Johto e Sinnoh.
- [ ] Repetir todo o fluxo em Android/JoiPlay — separado da prova Windows.

## 7. Próxima etapa

**Etapa 09/10 — Equipes Magma/Aqua e Mossdeep:** eventos do Hideout, submarino e centro espacial, Tate & Liza e cenas da história até a próxima região. Mapas e finais dos eventos devem ser auditados antes de desbloquear os portões que ainda estão fechados.
