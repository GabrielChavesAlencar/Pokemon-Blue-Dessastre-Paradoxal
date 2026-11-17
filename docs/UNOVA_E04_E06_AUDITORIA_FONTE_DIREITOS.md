# Unova E04–E06 — auditoria privada de fontes e direitos

**Data:** 17/11/2026 · **Projeto:** Pokémon Blue: Dessastre Paradoxal · **Base narrativa:** Pokémon White / Black & White.

> **ESTADO:** Ferramentas criadas para auditoria, mas não foi importado nenhum mapa/NPC/música do Pokémon World V18. Os marcos E04, E05 e E06 continuam pendentes de evidência real. O ZIP de origem não estava acessível neste ambiente. Unova permanece planejada e não jogável.

## Ferramentas e relatórios

| Etapa | Script | Entrada real necessária | Relatório privado produzido | Limite de confiança |
|---|---|---|---|---|
| U02 / E04 inventário | [audit_unova_u02.py](../scripts/regions/audit_unova_u02.py) | ZIP do autor | .blue-work/unova/audit/u02-source.json | Metadados, não identifica mapas Unova |
| E05 inspeção inerte | [audit_unova_source_detail.py](../scripts/regions/audit_unova_source_detail.py) | RXDATA do mesmo ZIP | .blue-work/unova/audit/u02-rxdata-detail.json | Nomes, dimensões, eventos, páginas, hashes e transferências |
| E05 comparação | [audit_unova_e05_crosswalk.py](../scripts/regions/audit_unova_e05_crosswalk.py) | Relatório RXDATA + 74 áreas | .blue-work/unova/audit/e05-crosswalk.json | Candidatos por nome, não mapas confirmados |
| E06 matriz privada | [audit_unova_e06_rights_inventory.py](../scripts/regions/audit_unova_e06_rights_inventory.py) | ZIP e opcional Credits.txt | .blue-work/unova/audit/e06-rights-inventory.json | Todos os arquivos exigem análise individual de direitos |

Não executar nem extrair scripts do fangame. Nada no resultado prova licença de distribuição, compatibilidade v21.1, MapID livre, ou mapa jogável no Game.exe.

## Como executar por duplo clique, sem PowerShell

1. Baixe o ZIP e Credits.txt da publicação do criador, indicados na [pesquisa de fontes](UNOVA_PESQUISA_FONTES_RMXP.md), conforme as condições de uso aplicáveis.
2. Coloque o ZIP sem descompactar em **.blue-work/unova/sources/Pokemon_World_V18.zip** e o arquivo de créditos, se disponível, em **.blue-work/unova/sources/Credits.txt**.
3. Na pasta do projeto, dê duplo clique em **[UNOVA_VALIDAR_DOCUMENTACAO.bat](../UNOVA_VALIDAR_DOCUMENTACAO.bat)**. Ele executará as auditorias sem abrir o jogo.
4. Examine os quatro relatórios na pasta privada **.blue-work/unova/audit**. Os relatórios não entram no GitHub por padrão.
5. Revise associações por nome contra o detonado e cada mapa; não habilite Unova nem remapeie IDs até concluir a auditoria da instalação principal e dos direitos.
6. Se um relatório indicar bloqueio, resolva a origem ou permissão e preserve a evidência anterior em vez de substituí-la silenciosamente.

## E05 — estados de correspondência

O relatório contém exatamente uma linha para cada uma das 74 áreas documentadas:

- **SINGLE_NAME_CANDIDATE_UNCONFIRMED:** há um nome igual ao da área, mas nenhum mapa foi aprovado para Unova.
- **MULTIPLE_NAME_MATCHES_UNRESOLVED:** vários mapas do doador têm o mesmo nome, exigindo revisão manual.
- **GENERIC_NAME_UNRESOLVED:** nomes como Route 1, Victory Road e Pokémon League não identificam região sozinhos.
- **NO_NAME_MATCH_NOT_PROOF_OF_ABSENCE:** nenhum nome igual foi encontrado. Isso não comprova que a área esteja ausente — o mapa pode ter sido renomeado.

Mesmo no melhor caso, todos os resultados permanecem com identidade regional não confirmada, direitos não verificados, MapID de destino nulo, jogo não instalado e Game.exe não testado.

## E06 — categorias e autorizações

O relatório lista arquivos do ZIP por categorias, como mapas/eventos, tilesets, personagens, áudio, PBS e plugins. Cada arquivo recebe **REVIEW_REQUIRED_NOT_LICENSED**, autorização de redistribuição falsa e aprovação de instalação falsa. Ele registra somente o hash e quantidade de linhas de Credits.txt, sem publicar seu texto.

Creditar o autor de um fangame não confere automaticamente direito de redistribuir todos os trabalhos incluídos. Verificar individualmente autoria/licença/permissão de gráficos, músicas comerciais, sprites, scripts e demais recursos de terceiros. Para um arquivo sem direito claro, criar ou escolher um recurso original/licenciado em vez de redistribuí-lo.

## Proteções obrigatórias

- Só lê ZIP e relatórios privados; não executa Game.exe nem scripts Ruby doador.
- Não modifica o registro regional, sprites, PBS, scripts, mapas, instalador, saves ou outras regiões.
- Rejeita links simbólicos, caminhos fora da pasta permitida e arquivos ZIP inseguros.
- Nunca interpreta nome de rota como confirmação regional.
- Nunca cria MapIDs numéricos de destino sem auditoria real da instalação local.
- Não permite que um relatório afirme aprovação de licenças, campanha ou QA nativo.

## Critérios da Barra E (sem inflação de progresso)

| Marco | Estado real |
|---|---|
| E01 — pesquisa de fontes | CONCLUÍDO |
| E02 — plano U01–U32 | CONCLUÍDO |
| E03 — catálogo de 74 áreas | CONCLUÍDO |
| E04 — ZIP real auditado e créditos conferidos | PENDENTE (ferramenta pronta) |
| E05 — mapas/eventos reais confrontados com Unova | PENDENTE (crosswalk pronto) |
| E06 — direitos por arquivo comprovados | PENDENTE (matriz pronta) |
| E07 — cues e treinadores simbólicos | CONCLUÍDO (nada instalado) |
| E08 — QA Windows Game.exe e Android JoiPlay | PENDENTE |

**Barra E = 4/8 (50%). Unova jogável = 0/32 fases aprovadas.** As barras A–D permanecem 0/8. Os testes automatizados validam a segurança de preparação, mas não comprovam jogo rodando.

## Próxima evidência indispensável

ZIP original e Credits.txt, para inventário real e revisão humana. E08 depende de execução de Game.exe e JoiPlay reais, com saves isolados e regressões de Decades/Kanto/Johto/Hoenn/Sinnoh.
