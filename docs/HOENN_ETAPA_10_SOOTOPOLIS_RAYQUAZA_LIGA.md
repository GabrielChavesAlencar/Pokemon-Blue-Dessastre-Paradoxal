# Hoenn — Etapa 10/10: Sootopolis, Seafloor Cavern, Sky Pillar e Liga Pokémon

**Data:** 14/11/2026  
**Status:** **implementação técnica em piloto isolado** — **não aprovada como jogável**.  
**Origem fixa:** `SocomSeal/The-PMon-World-Project@c59233bdbaac4fbfeca6aa01c7f05be628da2a92`.  
**Etapa anterior:** [Etapa 09](HOENN_ETAPA_09_MT_PYRE_MAGMA_AQUA_MOSSDEEP.md).

## 1. Inventário auditado

O inventário do piloto passa de **138 para 199 MapIDs** (+61). A auditoria **read-only** dos MapInfos e dos eventos originais do doador ocorreu em [GitHub Actions: Hoenn Stage 10](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43622125989). A auditoria não importa, executa ou republica scripts RXDATA.

Os MapIDs originais integrados à cópia isolada incluem Sootopolis (83–87), Pacifidlog (88–90), Ever Grande/Liga (91–100 e 322), rotas costeiras 125–134 (146–155), Seafloor Cavern (227–236), Cave of Origin (238–240), Sky Pillar (241–248), Victory Road (250–252) e subconjunto de áreas subaquáticas (255, 258–263, 266). IDs remapeados para o namespace seguro 700–999 na cópia do jogador, sem substituir mapas, PBS ou saves de Decades/Kanto/Johto/Sinnoh.

**Conexões:** 15 bordas externas que realmente aparecem no PBS da fonte foram adicionadas, mas dependem das mecânicas de Surf. O scanner dos eventos RXDATA reutiliza somente teleportes diretos com alvo estático válido e itens inequívocos; descarta destinos ambíguos, condicionais ou fora do mapa. Não inventa coordenadas.

## 2. História e líderes adicionados

1. Após o submarino Aqua, a Mind Badge e HM Dive, Archie pode ser enfrentado em Seafloor Cavern. Apenas vitória marca derrota do líder.
2. A história registra o despertar de Kyogre e a crise do clima; a sequência anterior de Groudon é pré-requisito para a cena em Sootopolis.
3. Wallace na Cave of Origin orienta sobre Rayquaza; Wallace em Sky Pillar autoriza a abertura do topo. Rayquaza encerra a crise em **diálogo e flags**, não em cinemática real.
4. Juan desafia o jogador depois da crise. Vitória concede apenas **HOENN:RAIN** via registro regional de insígnias. TM Water Pulse é opcional, só se o item existir, ensinar o movimento correto e a Bolsa tiver espaço.
5. Após Rain Badge, Wally tem batalha em Victory Road.
6. Sidney, Phoebe, Glacia e Drake são vencidos na ordem. Wallace é o Campeão (como no Emerald), com equipe de seis Pokémon. Derrotas não marcam vitória, e saves preservam flags isoladas.
7. A entrada no Hall of Fame registra **hoenn_hall_of_fame** neste save regional somente após Wallace. **Não** executa a apresentação/credits nativa, desbloqueio geral de regiões ou registro oficial no motor sem teste integrado.

As oito equipes de chefes usam os Pokémon/números do PBS do Emerald como **referência**. Blue/Decades é responsável pelo escalonamento com insígnias/esmeraldas, portanto não há nível fixo de batalha.

## 3. Código e testes

- `scripts/regions/hoenn_stage10.py`: mapas, liga, equipes e âncoras.
- `scripts/regions/pilot_hoenn.py`: montagem isolada RXDATA/PBS e novos eventos autorais, com falha fechada em colisões.
- `scripts/regions/HoennPilot.rb`: história e bloqueios em flags regionais.
- `scripts/regions/audit_hoenn_baseline.py` e `scripts/regions/audit_hoenn_pilot_contract.py`: inventário e consistência.
- `site/public/data/hoenn-pilot.json`: **199 áreas e 194 equipes** com destaque de Juan e Campeão.
- `tests/test_hoenn_stage10.py`: testagem de contratos, scanner e colisões com dados sintéticos.
- `tests/hoenn_stage10_runtime.rb`: derrota/vitória, badge RAIN, sequência da Liga, save/reload e escopo regional.
- `.github/workflows/regression.yml`: execução dos testes Ruby Stage10.

Comandos locais de desenvolvimento, **sem prova de Game.exe**:

```sh
python -m unittest discover -s tests -p "test_hoenn_*.py" -v
python scripts/regions/audit_hoenn_pilot_contract.py --strict
ruby -c scripts/regions/HoennPilot.rb
ruby tests/hoenn_stage10_runtime.rb scripts/regions/HoennPilot.rb
```

## 4. Limitações e QA obrigatório — Game.exe e Android/JoiPlay

- [ ] Montar o piloto em **nova pasta**, com pacote RXDATA privado original íntegro, sprites, tilesets e músicas; compilar PBS, 199 mapas e conexões e verificar carga de save.
- [ ] Percorrer rotas marítimas com **Surf**, mergulhar/emergir com **Dive** e testar cascatas de **Waterfall**, sem teletransporte artificial; confirmar se a máquina/flag real da engine respeita a região e as insígnias.
- [ ] Restaurar e validar todas as mecânicas de **Strength, Rock Smash, correntezas e gelo quebrável** nos mapas originais; eventos condicionais não foram executados nem copiados.
- [ ] Verificar as portas internas, teletransportes, travessias e bloqueios; a topologia de auditoria não é prova de mapas alcançáveis com colisão real.
- [ ] Implementar/validar as cenas animadas de Kyogre, Groudon e Rayquaza, música/efeitos, tempo, transição do clima e gravação de save.
- [ ] Validar cada Pokémon, item, gráfico, ataque, nível dinâmico, batalha, derrotas e rematches dos líderes, Wally, Elite Four e Wallace na engine.
- [ ] Implementar e testar Hall of Fame **nativo**, créditos e eventual desbloqueio de regiões sem tocar indevidamente nos saves de Decades/Kanto/Johto/Sinnoh.
- [ ] Repassar todos os NPCs, itens de chão, falas em PT-BR, placas, sprites e mapas, inclusive os que ainda não possuem eventos autorais traduzidos.
- [ ] Rodar regressões nativas Decades e pilotos Kanto/Johto/Sinnoh, Windows e Android/JoiPlay.
- [ ] Revisar direitos e créditos dos recursos da fonte antes de qualquer redistribuição.

**Marcos separados:** **10/10 etapas técnicas de código** somente após CI validada; **0/10 de aprovação jogável nativa** até percorrer os testes reais. Nenhuma certificação de Game.exe/Android está implícita.

As pendências da Etapa 9 (botões de Mossdeep, coop real de Steven e PBS de recrutas Magma/Aqua) continuam abertas e não devem ser apagadas pelo fim do roteiro da Etapa 10.
