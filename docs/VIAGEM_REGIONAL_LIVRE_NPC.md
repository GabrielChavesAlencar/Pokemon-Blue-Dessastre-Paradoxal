# Viagem regional livre por NPC — jogo principal (15/11/2026)

**Decisão vigente:** o jogador pode trocar entre quaisquer regiões **efetivamente integradas à mesma instalação** desde o começo do jogo, sem precisar vencer a Liga, obter insígnias, desbloquear vizinhos ou concluir missões de transporte. Para executar uma viagem, é obrigatório **falar com o Agente Regional na cidade inicial da região atual**.

Este documento **substitui somente as regras de desbloqueio de viagem** do plano v2, que condicionavam deslocamentos a vencer a Liga e liberavam duas regiões vizinhas. Não altera as regras de HMs, níveis, insígnias/esmeraldas, progressão dos eventos locais, restrições de Pokémon especiais, vitórias e pós-jogo global.

## Cidades iniciais e NPCs

| Origem | Mapa do NPC | Regra |
|---|---|---|
| **Kanto** | Pallet Town, mapa FRLG original 005, remapeado pelo manifesto de instalação | NPC gerado em tempo de execução, perto do ponto de chegada auditado. Não ocupa a casa do jogador e não substitui RXDATA. |
| **Decades** | Cherryhill City, Map077 nativo Decades | NPC gerado em tempo de execução, inclusive em saves Decades antigos sem metadados regionais; não substitui Map077.rxdata. |
| **Johto** | New Bark Town, ponto `npc_point` registrado no manifesto auditado | NPC disponível assim que Johto for integrada e validada, sem exigir a Liga; **piloto separado não serve**. |
| **Hoenn e demais** | Cidade inicial canônica de cada região, com ponto auditado a ser acrescentado quando integrada | **Não inventar coordenadas nem anunciar transporte jogável sem integração e QA.** |

Kanto ↔ Decades é o primeiro trecho efetivo desse circuito; Johto só aparece se um instalador tiver colocado mapas, compilação e prova confiável de NPC/chegada **no Game.exe principal**. Hoenn e Sinnoh têm pilotos independentes, portanto ainda não são destinos deste save; Hisui continua sendo o arco especial em desenvolvimento.

## Regras de deslocamento

1. O menu **Circuito de regiões** é apenas informativo. **Nenhum botão de teleporte no menu de pausa**. `BlueRegionTravel.agent(true)` é chamado exclusivamente pelo evento do NPC; `travel` e `perform` exigem esse contexto e verificam que o jogador continua na cidade inicial correta.
2. O agente mostra todas as regiões do catálogo e indica **atual**, **viajar** ou **em preparação**, conforme mapas verdadeiros e ponto de chegada validado. Não criar mapa, progresso ou save fictício.
3. O jogador confirma o destino. A equipe, dinheiro, inventário, PC, Pokédex e histórico regional permanecem no **mesmo save**, sem trocar de `Game.exe`; ao voltar, usa o ponto seguro registrado.
4. A regra de **oito conquistas locais para Pokémon especiais** continua valendo na região de destino. Quando necessário, o sistema pré-reserva vagas do PC e deposita os especiais antes de transferir; não pode deixar a party sem Pokémon apto, nem viajar com Box cheia. Falha de transferência faz rollback de região, equipe, PC e posição.
5. Cada região mantém seus próprios eventos, HMs, badges e elite; viajar cedo **não** concede automaticamente iniciais, insígnias ou vitórias em Ligas. O jogador pode voltar à região anterior para continuar seu progresso local.
6. A Liga é mantida no estado `leagues` apenas para conquistas, pós-jogo e rematches Full Power; não desbloqueia transporte. O nome `unlocked` no código passa a significar destinos do circuito disponíveis conceitualmente; **disponibilidade física** exige instalador e prova local.
7. Saves Decades antigos sem `blue_regions` podem encontrar o NPC, e o primeiro deslocamento cria o estado regional sem migrar ou apagar sua campanha original. Saves de Kanto já criados utilizam o ponto de chegada nativo de Decades registrado no início, sem depender da Liga.

## Arquivos de implementação

- `scripts/battle_polish/Regions.rb`: catálogo de viagem livre, menu somente informativo, conquistas inalteradas.
- `scripts/battle_polish/RegionTravel.rb`: validação dos destinos instalados, agentes em Pallet/Cherryhill/New Bark e gate obrigatório do evento do NPC.
- `scripts/battle_polish/RegionStart.rb`: início regional nativo e prova do pacote integrado; sem alterações de ponto inicial.
- `tests/region_travel_runtime.rb`: testes isolados de NPCs físicos, viagem antes da Liga, mapa correto, PC, rollback, não duplicação e proteção de RXDATA.
- `tests/hoenn_qa_phase10_runtime.rb`: QA da Liga mantendo concessão de vitórias separada da liberdade de transporte.

## Validar no Game.exe Windows (pendente de teste real)

- Atualizar pelo **Blue-Story.exe**, mantendo o save de teste salvo em backup; começar **Kanto** com zero badges e encontrar o agente em **Pallet Town**.
- Abrir o agente, viajar para **Decades**, confirmar a chegada nativa e encontrar o agente em **Cherryhill City**, sem vencer a Liga. Retornar para **Pallet Town**.
- Fazer o caminho inverso começando **Decades**, inclusive num **save antigo** anterior à integração regional, sem apagar progressos.
- Verificar que o menu de pausa **não transporta**; falar com NPC em rota aleatória não pode liberar uma viagem.
- Confirmar que **Johto, Hoenn e Sinnoh** não oferecem teleporte para pilotos isolados; se uma Johto integrada for certificada, testar New Bark sem concluir a Liga.
- Validar o depósito de especiais no PC, rejeição de viagem com Box cheia ou equipe inutilizável, save/reload e rollback em falha de transfer.
- Confirmar que HMs, insígnias, escalonamento, encontros, rival e campanha de Decades **não são avançados por uma viagem**.

**Status:** alterações no código e testes publicadas; **sem aprovação jogável até executar QA no Game.exe**.
