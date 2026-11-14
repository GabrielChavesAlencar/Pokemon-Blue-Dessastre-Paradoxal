# Catálogo das próximas fases — conteúdo regional ainda não adicionado

**Atualizado:** 13/11/2026  
**Regiões:** Kanto (FireRed/LeafGreen), Johto (HeartGold/SoulSilver), Hoenn (Emerald), Sinnoh (Platinum).  
**Foco:** visibilidade das pendências no portal, não instalação de RXDATA/PBS.

## O que foi publicado

O arquivo [pending-regions.json](../site/public/data/pending-regions.json) alimenta as páginas de regiões e a nova rota `/pendencias`. Os cartões aparecem em Localizações, Treinadores, Chefes e Liga, inclusive para Sinnoh, que antes não tinha uma tela de catálogo regional no portal.

| Região | Áreas para revisão | Treinadores/grupos | Líderes | Elite Four | Campeão |
|---|---:|---:|---:|---:|---:|
| Kanto | 74 | 5 | 8 | 4 | 1 |
| Johto | 177 | 25 | 8 | 4 | 1 |
| Hoenn | 88 | 36 | 8 | 4 | 1 |
| Sinnoh | 120 | 40 | 8 | 4 | 1 |
| **Total** | **459** | **106** | **32** | **16** | **4** |

**Contagem de registros de auditoria**, não total real de mapas/NPCs existentes no Game.exe. Alguns são andares/interiores simbólicos, agrupamentos de treinadores ou áreas em múltiplas condições, e não devem ser convertidos automaticamente em MapIDs ou encontros.

### Significado das etiquetas

- **Ainda não adicionado:** conteúdo exigido pela documentação, porém **sem integração jogável confirmada**. Pode existir como referência em docs/site, mas ainda requer validação da presença real no motor.
- **Em validação:** conteúdo com algum registro concreto no piloto/código experimental, mas sem comprovação suficiente para considerá-lo aprovado em Windows/Android. Não copiar de novo.
- **Não rotulado como pendência:** já está listado no catálogo do piloto; isso **não** equivale a garantia de gameplay aprovado.

**Exceção importante:** o piloto de Kanto já tem handlers para ginásios, Elite Four e campeão. O inventário os mantém como **Em validação**, não como **Ainda não adicionado**, evitando reimplementações destrutivas. O primeiro ginásio de Johto também já está catalogado no piloto e deve ser validado antes de criar outra versão.

## Para as próximas fases do Codex

1. Escolher uma região e categoria do backlog em `/pendencias?regiao=kanto`, `johto`, `hoenn` ou `sinnoh`.
2. Extrair inventário real dos mapas, NPCs, eventos, `MapInfos.rxdata`, `PBS/trainers*` e `PBS/encounters*` da instalação **privada** escolhida, com hashes e MapIDs auditados.
3. Para cada entrada, comparar com [o manifesto de referências](../data/regions/detonados-content-review.json), com o detonado correspondente e com o conteúdo existente; se já existe e funciona, apenas marcar como verificado com evidência.
4. Caso falte realmente, adicionar na **cópia isolada**, incluindo sprite, colisão, movimento, diálogo, batalhas ou encontros com método correto e taxa validada, sem inventar equipe ou nível. Treinadores por grupos precisam ser individualizados a partir dos PBS/mapas reais.
5. Incluir batalha/insígnia local e persistência para líderes; ordem das quatro batalhas, campeão e Hall of Fame para a Liga. **Não alterar** o cálculo compartilhado 70% Normal / 90% Master, evolução por cap, esmeraldas globais, HMs locais nem restrições de Pokémon especiais.
6. Validar no Game.exe e Android/JoiPlay, save/reload, vitória/derrota, NPC duplicado, captura, retorno de região e regressão de Decades.
7. Somente com evidência real atualizar o **status**, retirando da lista de pendências o registro aprovado e sincronizando a publicação do site. Não atualizar status por leitura de detonado ou aprovação de teste sintético.
8. Repetir por rota/cidade, e só então considerar a etapa jogável. Não misturar conclusão de documentação com conclusão do jogo.

### Comandos de teste do portal

```bash
cd site
npm test
npm run build
```

Testes dedicados: `site/tests/pending-regions.test.mjs` validam quatro regiões, líderes, Elite Four, estado da tag, segurança da renderização e ausência de repetição no complemento dos catálogos dos pilotos.

## Limitação importante

Este inventário é **abrangente em áreas e principais adversários documentados**, mas **não representa um dump exaustivo de cada treinador individual de Emerald/Platinum/HGSS**. Onde os detonados não identificam nome, classe e versão, constam grupos de auditoria. Somente a leitura dos PBS e eventos reais poderá transformar esses grupos em entradas individuais sem inventar treinadores. Algumas áreas também exigirão refinamento em múltiplos andares/setores e métodos de encontro.

**Nenhum arquivo nativo de jogo, save, áudio ou mapa foi alterado nesta fase.** A integração e o teste de cada entrada permanecem documentados na [issue #49](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/49).
