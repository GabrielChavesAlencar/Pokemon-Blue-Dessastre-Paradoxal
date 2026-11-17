# Unova SP04 — Catálogo auditável de NPCs e ligação com sprites

**Projeto:** Pokémon Blue: Dessastre Paradoxal · **Data:** 17/11/2026 · **Estado:** planejamento / não jogável.

## Entrega

- [Catálogo JSON](../data/regions/unova-sp04-npcs.json): **73 registros** de personagens nomeados, NPCs de serviço, classes de treinadores e objetos de campo, com papel, prioridade, área simbólica, fase planejada, variação da história, aliases de sprites e status de direitos/QA.
- [Auditor SP04](../scripts/regions/audit_unova_sp04_npcs.py): valida o catálogo e cruza os NPCs com imagens candidatas provenientes do relatório privado do auditor [SP03](../scripts/regions/audit_unova_sprite_pack.py).
- [UNOVA_CATALOGAR_NPCS.bat](../UNOVA_CATALOGAR_NPCS.bat): gera relatório sem PowerShell, usando o último SP03 ou um arquivo JSON de auditoria arrastado.
- [UNOVA_AUDITAR_SPRITES.bat](../UNOVA_AUDITAR_SPRITES.bat): passa a executar SP04 automaticamente após auditar um ZIP com sucesso.
- [Testes SP04](../tests/test_unova_sp04_npcs.py): casos negativos para licenças falsas, colisões, IDs, versões Black/White e proteção de relatórios privados.

**Escopo da palavra completo:** os 73 registros abrangem elenco nomeado e arquétipos relevantes para planejar Black/White; não representam todos os NPCs anônimos, eventos e treinadores individuais de todos os 74 mapas. Esses só serão conhecidos por inspeção dos RXDATA e testes reais.

## Organização e fidelidade à campanha White

| Categoria | Personagens / classes | Cuidados |
|---|---|---|
| Início | Hilbert, Hilda, Juniper, Cheren, Bianca, mãe, pai de Bianca | Avatares separados de eventos reais; locais simbólicos |
| Cientistas | Cedric Juniper, Fennel, Amanita | Sem eventos, posições ou diálogos instalados |
| Team Plasma | N, Ghetsis, Shadow Triad, grunts M/F, Anthea, Concordia e sete sábios | Pós-jogo separado; sprite/credits pendentes |
| Ginásios | Cilan/Chili/Cress, Lenora, Burgh, Elesa, Clay, Skyla, Brycen, Iris | São dez personagens para oito ginásios, incluindo o trio de Striaton |
| Variante Black | Drayden | Na campanha White, Iris é a líder de Opelucid; não transformar Drayden em líder obrigatório |
| Liga | Shauntal, Grimsley, Caitlin, Marshal, Alder | Alder deve respeitar sua batalha pós-jogo |
| Pós-jogo e extras | Looker, Cynthia, Morimoto, Ingo e Emmet | Registros para planejamento, não eventos validados |
| Genéricos | Rangers, Youngster/Lass, Ace Trainer, trabalhadores, atendentes, objetos Cut/Strength/item | Cada linha é arquétipo, não instância de NPC no mapa |
| Blue | Agente Regional em Nuvema | Personagem planejado, sem MapID ou coordenadas inventadas |

As **19 referências de treinadores** já documentadas em data/regions/unova-e06-e07-preparation.json foram mantidas por chave, sem inventar equipes, níveis ou IDs PBS. As **74 áreas simbólicas** continuam como referências da história.

Fontes de roteiro: [manual oficial White da Nintendo](https://csassets.nintendo.com/noaext/image/private/t_KA_PDF/DS_Pokemon_White), [ginásios Black/White](https://www.serebii.net/blackwhite/gyms.shtml), [Team Plasma](https://www.serebii.net/blackwhite/plasma.shtml), [Sete Sábios](https://bulbapedia.bulbagarden.net/wiki/Seven_Sages). Áreas e aliases são planejamento, não proveniência verificada de sprites.

## Como executar no Windows

1. Atualize os arquivos do repositório.
2. Sem ZIP de sprites, dê dois cliques em **UNOVA_CATALOGAR_NPCS.bat**. Ele gera o catálogo com estado **NO_PACK_AUDIT** para todos, preservando as pendências.
3. Quando tiver um ZIP autorizado do autor, use **UNOVA_AUDITAR_SPRITES.bat** para selecionar o ZIP. A comparação com Graphics/Characters do Decades é opcional, somente leitura.
4. Após o sucesso de SP03, o mesmo BAT invoca SP04 para cruzar possíveis correspondências pelo nome.
5. Para usar um relatório específico, arraste o JSON da pasta privada sprite-packs sobre **UNOVA_CATALOGAR_NPCS.bat**.
6. Leia o relatório gerado em **.blue-work/unova/audit/npc-catalog/**. Se nenhum pack foi fornecido, o nome é **npc-sp04-planned-only.json**; caso contrário, **npc-sp04-[hash].json**.

No Python de desenvolvimento, execute: python scripts/regions/audit_unova_sp04_npcs.py --latest --write.

## Interpretação das correspondências

| Estado | Interpretação |
|---|---|
| NO_PACK_AUDIT | Não há relatório SP03; nenhum personagem foi localizado |
| NO_FILENAME_MATCH_UNVERIFIED | Nenhum nome correspondeu; o personagem pode existir com outro nome |
| SINGLE_CANDIDATE_MANUAL_REVIEW | Um arquivo corresponde por nome; não comprova identidade visual ou licença |
| MULTIPLE_CANDIDATES_MANUAL_REVIEW | Há várias versões candidatas, pendentes de seleção manual |

Cada candidato mantém seu caminho interno de ZIP, SHA-256, dimensões, formato, animações/grades declaradas e alertas de escala. **Não há extração, atribuição de sprite definitiva ou aprovação automática.**

## Segurança e próximas fases

- Reprovar falsos estados de licenciamento, instalação, revisão visual ou teste Game.exe/JoiPlay.
- Reprovar alterações indevidas nas referências anteriores dos 19 treinadores, nas 74 áreas, nas fases e no elenco White (Iris líder, Drayden opcional de Black).
- Aceitar apenas relatório SP03 privado de nome/hash consistente, sem sprites inválidos, sem symlink e sem reivindicação de direitos.
- Não modificar Graphics/Characters, sprites de outras regiões, PBS, MapInfos, arquivos Game.exe, Blue-Story ou saves.
- **SP05:** após receber arquivos e permissões, selecionar um NPC piloto (por exemplo Cheren) e testar uma cópia isolada com quatro direções, escala e pivô antes de tocar no jogo principal.

**Progresso real permanece E = 4/8 (50%)**, A/B/C/D = 0/8 nesta entrega e **Unova jogável = 0/32**. O catálogo não substitui auditorias de fonte/direitos nem QA nativo.
