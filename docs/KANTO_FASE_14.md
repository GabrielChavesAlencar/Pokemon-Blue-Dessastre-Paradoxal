# Kanto — Etapa 14/16: Victory Road, Elite Four, Campeão e Hall of Fame

**Data:** 12/11/2026. **Estado:** núcleo funcional aprovado pela [CI nativa Windows 43260317898](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43260317898), com [regressão Blue Studio 43260317908](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43260317908) e [portal 43260318030](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43260318030). **Aceite manual integral não realizado.**

## Origem, mapa e segurança

Fonte FRLG 1.1 fixa em `data/regions/kanto-source.json` pelo SHA-256; inventário somente leitura `scripts/regions/audit_league.py` publica `.blue-work/kanto-phase-14-audit.json`. Os quinze mapas originais incluídos são:

| Fonte | Destino | Escopo |
|---|---|---|
| 16 | Route 22 | acesso ao portão, rival/script estrangeiro adiado |
| 17 | Indigo Plateau Gate | primeiro guarda de Boulder Badge, porta e barreira locais |
| 209 | Route 23 | sete guardas e barreiras (Cascade até Earth), ida/volta à Victory Road |
| 210 | Victory Road hub | geometria **sem eventos** (`preview_only`) |
| 211/212/213 | Victory Road 1F/2F/3F | escadas/saídas auditadas, treinadores e abertura experimental dos mecanismos |
| 214 | Indigo Plateau | entrada ao saguão condicionada a oito insígnias |
| 215 | Indigo Lobby | nurse/Mart/guia e início oficial da sequência da Liga |
| 216/217/218/219 | Lorelei/Bruno/Agatha/Lance | cinco Pokémon PBS por membro e portas condicionadas à vitória |
| 220 | Champion's Hall | Blue com três times PBS diferentes pelo inicial |
| 221 | Hall of Fame | registro único do fim de Kanto, retorno para Pallet |

A ordem de `stable_source_order` congela os **127 mapas anteriores** e acrescenta os **15 novos** no final. **142 mapas totais, 45 prévias sem eventos**. Não importar variáveis, flags de save, cenas de créditos ou scripts de batalha da fonte FRLG; todas as rotas/guardas e prêmios são callbacks locais `BlueKantoPilot`.

## Regras da fase 14

1. **Oito insígnias locais:** Boulder/Cascade/Thunder/Rainbow/Soul/Marsh/Volcano/Earth precisam constar no progresso de Kanto. Insígnias de Johto, esmeraldas de Decades e outras regiões **afetam apenas os níveis via sistema global**, não os guardas da Liga.
2. **Postos de Route 23:** a portaria inicial confere Boulder; os outros sete postos conferem cada um o prefixo das insígnias até Earth, abrindo barreira e guarda no save via self-switch A. Entradas de Victory Road não aceitam bypass.
3. **Três andares de Victory Road:** treinadores de visão e escadas originais remapeados; Ray & Tyra compartilham **uma batalha dupla e uma vitória**, não duas equipes artificiais.
4. **Mecanismos das pedras:** fase experimental oferece uma interação local sob condição de Rainbow que abre barreiras, **não recria ainda o empurrar canônico de pedras/HM Strength**. É um bloqueador conhecido de aceite integral; deve ser substituído por posicionamento de boulders com push físico comprovado.
5. **Saguão:** o `league_begin` só inicia uma tentativa com 8 badges. Teletransportar diretamente ao quarto de Lorelei ou ao Hall não libera batalhas/resultado sem início válido.
6. **Elite Four na ordem:** Lorelei → Bruno → Agatha → Lance; sem inventar rosters e sem permitir que a porta da sala avance antes da vitória registrada na tentativa atual.
7. **Blue como Campeão:** equipe do PBS conforme inicial: Bulbasaur → time que contém Charizard; Charmander → Blastoise; Squirtle → Venusaur. A seleção em runtime é 1/2/3 na mesma ordem da fonte.
8. **Derrota:** a tentativa é invalidada; equipe curada e retorno ao Lobby, nenhuma conclusão ou insígnia duplicada.
9. **Hall of Fame:** `BlueRegions.complete_league(progress, "KANTO")` **só após as cinco vitórias sequenciais**, e apenas uma vez. A primeira conclusão torna **Decades e Johto elegíveis** no circuito regional, pois são vizinhas de Kanto. **Elegibilidade não instala automaticamente Johto**, nem muda os badges nativos de Decades. Registra `pilot_hall_of_fame` e retorna a Pallet.
10. **NPCs de viagem:** o agente já existente em Pallet permanece; o Guia da Liga no Lobby também encaminha ao mesmo `BlueRegionTravel.agent(true)` após a primeira vitória. Destinos sem mapas instalados continuam identificados como em preparação.

## Treinadores e portal

- **12 confrontos originais** de Victory Road: Naomi, Rolando, Daisuke, Vincent, Nelson, Gregory, Dawson, George, Alexa, Caroline, Colby e a dupla Ray & Tyra (eventos 15/16 compartilhados).
- **Quatro membros da Elite:** Lorelei, Bruno, Agatha e Lance (5 Pokémon cada).
- **Campeão Blue:** 3 variantes de 6 Pokémon no PBS, preservadas sem transformação para times de pós-jogo.
- O portal mantém 142 localidades e **144 perfis de treinadores**, incluindo a Elite e o Campeão em páginas localizáveis.
- **64 atalhos** de teste experimental no piloto, dez novos locais de Route 22 até Hall.

## Verificação e critérios de aceite

O pipeline Windows deve garantir: ausência de eventos estrangeiros; catálogo e MapIDs imutáveis; guardas individuais e segurança dos oito badges; conexão de todas as rotas e escadas; arquivo PBS do Campeão; sequência de membros e portas; derrota/reinício; cinco vitórias, final Hall único, salvamento/reload; elegibilidade apenas Decades/Johto. Os resultados de combate na CI são **simulados**, embora a engine `Game.exe` seja compilada e executada.

**Pendências para etapa integral [ ]:**
- Reprodução real de Strength em cada andar, piso/colisões/escadas e testes de caminhar/retornar nos mapas Windows e JoiPlay.
- Encontros selvagens de Route 22, Victory Road, Route 23 e Indigo excluídos por enquanto: alguns slots originais contêm faixas de níveis não contíguas; precisam de migração fiel no **núcleo 15**.
- Rival da Route 22 e diálogos/cenas de créditos/Professor Oak canônicos, incluindo música e Hall of Fame visual; materiais externos requerem revisão de licença.
- Revanches das equipes mais fortes de cada líder/Elite/Campeão **somente após concluir todas as regiões**, conforme plano v2. Não confundir esta primeira conquista da Liga com uma nova vitória por revanche.
- UI de conquistas da região e do circuito (MAN-03), viagem de fato para JOHTO após instalar sua região, save único no jogo principal e QA Android.

**Barras atuais após aprovação nativa:** **Barra 1 13/16 (81,25%) — faltam 3 núcleos (02, 15, 16)**; **Barra 2 1/16 (6,25%) — faltam 15 etapas de aceite integral**. O teste nativo roda a engine `Game.exe` e simula resultados de batalha. Também simula apenas no teste headless as transferências, porque o spriteset de um plugin gráfico não está inicializado antes de entrar no mapa. **O serviço de viagem real do jogo não foi alterado por essa simulação**. Ainda é obrigatório validar transferências e colisões manualmente no Windows/JoiPlay.
