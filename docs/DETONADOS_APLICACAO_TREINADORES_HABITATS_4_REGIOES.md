# Integração de treinadores, líderes e encontros — quatro regiões

**Data:** 13/11/2026  
**Estado atual desta entrega:** referência e auditoria disponíveis no GitHub; **nenhum treinador, mapa ou PBS nativo adicional foi ativado** nesta entrega. Documentação/site não são prova de gameplay.

## 1. Fontes e contratos

| Região | Roteiro já existente | Localizações de consulta |
|---|---|---|
| Kanto | [FRLG](KANTO_DETONADO_FIRERED_LEAFGREEN_REFERENCIA_ORGANIZADA.md) | [FRLG](https://rankedboost.com/pokemon/location/firered-leafgreen/) |
| Johto | [HGSS](JOHTO_DETONADO_HEARTGOLD_SOULSILVER_REFERENCIA_ORGANIZADA.md) | [HGSS](https://rankedboost.com/pokemon/location/heartgold-soulsilver/) |
| Hoenn | [Emerald](HOENN_DETONADO_EMERALD_REFERENCIA_ORGANIZADA.md) | [Emerald](https://rankedboost.com/pokemon/location/emerald/) |
| Sinnoh | [Platinum](SINNOH_DETONADO_PLATINUM_REFERENCIA_ORGANIZADA.md) | [Platinum](https://rankedboost.com/pokemon/location/platinum/) |

Os detonados orientam história, encontros e elencos de personagens, mas **não** se sobrepõem aos PBS, mapas, flags, política regional ou motor de batalha do Blue/Decades. Os sites de localizações são fontes auxiliares: conferir método, dia/noite, versões exclusivas e condições especiais no jogo de referência antes de alterar tabelas.

O manifesto [data/regions/detonados-content-review.json](../data/regions/detonados-content-review.json) contém uma **amostra não exaustiva de 61 habitats** e o elenco de **32 líderes** para conferência. Não contém porcentagens inventadas, MapIDs deduzidos, níveis finais ou coordenadas fictícias. Encontros estáticos/roteirizados são separados dos selvagens.

## 2. Comparação executável sem alterar o jogo

O script [audit_detonados_content.py](../scripts/regions/audit_detonados_content.py) compara os candidatos com os catálogos publicados. Ele **não lê o jogo compilado** e **não modifica mapas ou tabelas**. Assim, uma entrada ausente do site pode existir no Game.exe, e uma entrada presente no site pode não funcionar no Game.exe.

~~~bash
python scripts/regions/audit_detonados_content.py --output .blue-work/detonados-audit.json
python -m unittest discover -s tests -p "test_detonados_content_audit.py" -v
~~~

A opção --strict retorna código 2 quando houver lacunas de catálogo; não usar como gate da CI geral antes da instalação das regiões.

### Inventário constatado

| Região | Catálogo publicado | Restrições |
|---|---|---|
| Kanto | 142 localidades / 144 treinadores | Parte ainda experimental ou prévia |
| Johto | 11 locais / 10 treinadores do piloto; 148 locais simbólicos separados | Preview não é mapa jogável |
| Hoenn | 9 locais / 4 treinadores no piloto | Apenas abertura Littleroot/Oldale e rotas 101–103 |
| Sinnoh | Lista de planejamento, sem catálogo jogável aprovado | Geometria piloto e colisões de IDs ainda exigem resolução |

**Correção comprovada:** em FRLG, a Route 22 tem **Rattata, Mankey e Spearow**, não Pidgey. O detonado interno citava Pidgey erroneamente e foi corrigido; o catálogo Kanto já estava correto. Ver [Route 22 FRLG](https://rankedboost.com/pokemon/location/firered-leafgreen/route-22/).

- Johto Route 29 já contém Pidgey, Rattata, Sentret e Hoothoot à noite no catálogo do piloto. Evitar duplicações; revisar horários e exclusivos das Routes 30/31, e não ativar demais áreas somente por estarem no roteiro.
- Hoenn Route 102 já contém Poochyena, Zigzagoon, Wurmple, Lotad, Seedot, Ralts e Surskit. RankedBoost mostra uma distribuição percentual diferente; não substituir pesos do Blue sem aprovação e soma de probabilidades conferida.
- Sinnoh Route 201 prevê Starly e Bidoof, mas não há MapID novo aprovado nesta entrega. Drifloon, Rotom, Gyarados vermelho, Lapras semanal e outras interações especiais não devem ser inseridas como slots comuns de grama.

## 3. Implementação do conteúdo real — instruções para Codex

1. **Inventariar os MapIDs físicos:** registrar origem, destino, hash, geometria, tileset, status do mapa, evento e coordenadas caminháveis. Comparar Data/MapXXX.rxdata, MapInfos, Tilesets e PBS da instalação real. Ausência ou colisão de IDs = **bloqueio**, não criar mapa fictício.
2. **Conferir cada treinador comum** do detonado: classe, nome, versão do PBS, equipe, sprite, posição, linha de visão, interação, flag de batalha e persistência após vitória/derrota e reload. Incluir treinadores em rotas, cavernas, prédios e interiores, sem duplicar os já existentes.
3. **Conferir cada líder de ginásio:** localização do NPC e acesso ao ginásio, PBS real, evento de batalha, insígnia local única e prêmio. A primeira insígnia concede +1 esmeralda global; a insígnia de outra região não substitui a local. Nenhum prêmio por derrota ou repetição de autorun.
4. **Construir as tabelas selvagens por mapa e método real**, não apenas por nome de rota: dia/noite, Surf, pesca, Rock Smash, Headbutt, Safari, Honey Tree e Poké Radar quando apropriados. Preservar espécies já presentes, acrescentar somente omissões comprovadas, validar taxas em 100% por método. Manter encontros estáticos como eventos separados.
5. **Preservar o balanceamento da engine** (normal 70%, Master 90%, cálculo global por insígnias/esmeraldas, evolução conforme level cap, regras da área para selvagens). Nunca apresentar níveis fixos no portal; não copiar níveis originais diretamente como nível final. Não quebrar Eevees regionais, paradoxos ou espécies adicionadas.
6. **Instalar apenas em cópias privadas e isoladas**, usando os criadores/instaladores regionais já existentes; não copiar diretório Data de outro jogo sobre Decades. Manter backups, rollback e flags por região. Resolver especificamente a incompatibilidade de MapIDs do antigo piloto Sinnoh 800–805 na faixa protegida por Johto; verificar também colisões com o piloto Hoenn.
7. **Testar no Game.exe/Android**: movimentação, encontros aleatórios reais, batalhas comuns, líderes, insígnias, NPCs de cura, warps, save/reload, derrotas, HMs, restrição de Pokémon especiais/Box e viagem entre regiões. Registrar vídeo/log/hash e só promover status de mapa quando aprovado.
8. **Sincronizar o site por último**, com habitats e times que correspondem à versão instalada; distinguir planejado/experimental/jogável; manter em documento separado as equipes mais fortes do pós-jogo global.

### Ordem sugerida de lotes que podem receber integração nativa

- **K1 — Kanto:** auditar primeiro mapas e treinadores já instalados, retificar apenas omissões provadas pelas fontes do FRLG e PBS compilados.
- **J1 — Johto:** New Bark → Violet, incluindo treinadores, Falkner, Sprout Tower e encontros; validar pacote offline sem declarar fases jogáveis sem testes.
- **H1 — Hoenn:** Littleroot → Petalburg, reconciliar habitats e eventos já instalados, sem sobrescrever a probabilidade da Route 102.
- **S1 — Sinnoh:** Twinleaf → Oreburgh, solucionar IDs, validar Barry, Roark e espécies das rotas iniciais.
- **Lotes seguintes:** expandir rotas, ginásios, Elite Four, campeões e encontros especiais por região; fechar cada lote com regressão de Decades, Windows e Android.

## 4. Critérios de aceite

É obrigatório comprovar em jogo real os **32 líderes**, suas equipes PBS, insígnias corretas e respectivas cidades. Para treinadores e selvagens: validar cada mapa/horário/método, comportamento, níveis dinâmicos e salvamento. Uma linha no MD, site ou manifesto não autoriza aumentar a barra de região jogável.

**Esta entrega fornece preparação técnica, revisão factual e testes de regressão do auditor.** A instalação dos NPCs/encounters restantes é **pendente**, até haver evidência de mapas físicos e PBS correspondentes.
