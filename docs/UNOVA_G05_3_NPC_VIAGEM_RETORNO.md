# Unova G05.3 — NPC de viagem e retorno regional com fallback seguro

**WHITE_BW** · **Somente auditoria GitHub (planned)** · **Nenhum NPC ou mapa instalado.**

## Fontes reais

O contrato segue os comportamentos **já existentes** em [RegionTravel.rb](../scripts/battle_polish/RegionTravel.rb), [Regions.rb](../scripts/battle_polish/Regions.rb) e [RegionStart.rb](../scripts/battle_polish/RegionStart.rb):

- `BlueRegionTravel.agent(true)` é acionado pelo **NPC físico da cidade inicial**. O menu comum, uma rota aleatória ou um script sem esse contexto não autorizam teleporte; `quiet=true` só esconde mensagens.
- `safe_context?` exige a campanha principal ativa, cena apropriada, ausência de batalha/transferência/transição e possibilidade real de transferir o jogador.
- `source_valid?` restringe as origens à lista que o Ruby atual conhece: **Decades, Kanto, Johto e Hoenn**, com verificações de instalação próprias de cada região.
- `destination` exige região disponível, **instalação comprovada** e ponto seguro de chegada. Um registro em `regions.json`, mesmo no circuito, **não** comprova instalação. Não há um ramo `UNOVA` para esse método nativo.
- `BlueRegions.unlocked` não exige Hall of Fame nem vitória da Liga para as regiões do circuito atual. A G05.3 preserva essa regra em vez de inventar uma exigência de progresso; as restrições **de Pokémon especiais** permanecem baseadas nas oito conquistas locais da **região de destino**.
- O retorno a **Decades** aceita apenas um local do mapa seguro de Cherryhill validado pelo jogo; um marcador antigo ou desconhecido não deve levar para a introdução nem para um quarto. O Ruby usa um fallback para Cherryhill após validar o mapa e a passabilidade.
- O `perform` real revê os pré-requisitos imediatamente antes de alterar o estado, reserva as posições das Boxes e tenta reverter **party, Boxes, Bolsa, PC de itens, região, mecânicas e posição** se ocorrer falha. A G05.3 **não invoca `perform` real nem modifica esse Ruby**.

## Contrato de segurança G05.3

Referências:
- [JSON de regras e lacunas](../data/regions/unova-g05-travel-contract.json)
- [Auditor Python e simulador de viagens](../scripts/regions/audit_unova_g05_travel.py)
- [127 testes positivos e negativos](../tests/test_unova_g05_travel.py)
- [G05.1 de itens regionais](../data/regions/unova-g05-regional-items-contract.json)
- [G05.2 de insígnias/especiais](../data/regions/unova-g05-badges-specials-contract.json)

### Estados de disponibilidade

| Região | Reconhecida como rota potencial no Ruby | Instalabilidade **comprovada nesta G05.3** |
|---|---|---|
| Decades | Sim, depende do runtime já integrado e retorno seguro | Não auditada com Game.exe na G05.3 |
| Kanto | Sim, depende da prova nativa `kanto_integrated?` | Não auditada com Game.exe na G05.3 |
| Johto | Sim, depende de instalação e pontos comprovados no runtime | Não auditada com Game.exe na G05.3 |
| Hoenn | Sim, depende de instalação e ponto comprovados no runtime | Não auditada com Game.exe na G05.3 |
| Unova | **Não**, apenas circuito e catálogo planejado | **Não instalada; viagem bloqueada** |
| Sinnoh, Kalos, Alola, Galar, Paldea e Hisui | Não há integração de viagem física nessa função | Não instalada ou aprovada aqui |

Todos os campos de prova nativa de Unova permanecem `null`: NPC, origem, MapID, instalação, chegada, retorno, Windows/Android e licenças. **Nenhum MapID foi reservado ou criado por esta entrega.**

## Passos de uma viagem (prévia sintética)

1. Validar que o jogador iniciou a interação no NPC da cidade inicial e está na campanha, não na arena; confirmar que a cena é segura.
2. Validar origem, destino, instalação e ponto de chegada. Nem a lista de regiões nem um progresso suficiente substituem a instalação.
3. Usar o **simulador de G05.1** para projetar Bolsa/PC de itens e impedir que HMs/itens-chave cruzem regiões; itens globais permanecem globais.
4. Usar o **simulador de G05.2** para identificar as flags `Legendary`, `Mythical`, `UltraBeast` e `Paradox`, conservar ao menos um Pokémon não-ovo e não desmaiado na party e exigir vagas de Box.
5. Se qualquer passo falhar, bloquear. Se passar, fazer uma **simulação em memória**, preservando histórico e mecânicas por região. É possível injetar falhas após alteração sintética da party, do estado, da Bolsa, do PC ou da posição e confirmar a reversão integral.

Todos os rótulos de mapas usados nas simulações começam por `FIXTURE_`; **não são IDs reais**, coordenadas, provas de instalação ou pontos novos no Game.exe. A simulação Kanto → Hoenn → Kanto demonstra retorno seguro dos itens locais e permanência dos Pokémon depositados na Box, sem retirada automática.

Para **Decades**, se houver Pokémon especiais na party, o fixture recusa a autorização: o auditor não tem o estado nativo de insígnias de Decades e não presume um desbloqueio. Sem Pokémon especiais, simula o retorno a Cherryhill, nunca à introdução.

## O que ainda não está feito

Nenhum NPC foi adicionado a Unova; nenhum destino de Unova foi habilitado. A auditoria tampouco valida mapas, transferências reais no Windows ou JoiPlay, nem conclui que o sistema real seja transacional em todas as condições possíveis. O rollback mostrado é uma **verificação sintética dos comportamentos previstos pelo código existente**. O trabalho de integração nativa exige provas reais de instalação e testes no Game.exe.

A G05.4 vai tratar de **blackout, Centro Pokémon da região atual, estado compartilhado e salvamentos**, mantendo essas limitações explícitas.

## Executar

```bash
python scripts/regions/audit_unova_g05_travel.py --check
python scripts/regions/audit_unova_g05_travel.py --simulate-demo
python -m unittest discover -s tests -p 'test_unova_g05_travel.py' -v
```

O CI testa a auditoria e a regressão de Unova no Linux e Windows, além de verificar a documentação e o site. O marcador G05.3 só poderá ser publicado como **etapa G da documentação técnica** após CI aprovado; Barra A e Unova jogável devem continuar em **0**.
