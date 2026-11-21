# Central de documentação — Pokémon Blue: Dessastre Paradoxal

> **Comece aqui.** Este índice organiza as entradas de uso, regiões, desenvolvimento e auditoria. Ele é um mapa de navegação, **não** uma declaração de que todos os recursos estão instalados ou aprovados.

[← Voltar à página inicial](../README.md) · [Portal](../site/README.md) · [Histórico de mudanças no GitHub](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/commits/main/)

## Quero...

| Objetivo | Abra primeiro |
| --- | --- |
| Instalar ou atualizar no Windows | [Instalação](INSTALACAO.md) |
| Começar a jogar ou escolher região | [Novo jogo por região](NOVO_JOGO_SELECAO_REGIONAL.md) e [viagem regional](VIAGEM_REGIONAL_LIVRE_NPC.md) |
| Entender Kanto integrado e seus limites | [Integração de Kanto](KANTO_INTEGRACAO_DECADES.md) |
| Ver pendências e próximos trabalhos | [Próximos passos](PROXIMOS_PASSOS.md) *(verifique a data do relatório)* |
| Testar batalhas sem mexer na campanha | [Hub de Batalha](HUB_BATALHA.md) |
| Editar Pokémon ou golpes | [Auditoria do editor Pokémon](AUDITORIA_EDITOR_POKEMON.md) e [editor de golpes](EDITOR_GOLPES_POKEMON.md) |
| Editar músicas | [Editor de músicas](EDITOR_MUSICAS.md) |
| Executar o site | [Portal e Vercel](SITE_E_VERCEL.md) |
| Encontrar uma documentação pelo nome | [Busca de arquivos Markdown no GitHub](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/search?q=extension%3Amd&type=code) |

## Regiões e andamento

**Importante:** código, roteiro, auditoria, pacote piloto e **jogo testado em Windows/Android** são estados diferentes. A existência de arquivos Markdown ou aprovação de CI não comprova execução no Game.exe/JoiPlay.

| Região | Porta de entrada | Como interpretar |
| --- | --- | --- |
| **Kanto** | [Instalação no Decades](KANTO_INTEGRACAO_DECADES.md) · [Etapas](KANTO_ETAPAS.md) · [QA E2E](KANTO_CODEX_TESTES_E2E.md) | Distinguir integração prevista, execução local e aceite da campanha |
| **Johto** | [Pesquisar documentação Johto](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/search?q=JOHTO+extension%3Amd&type=code) | Pilotos e auditorias não equivalem à campanha instalada |
| **Hoenn** | [Pesquisar documentação Hoenn](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/search?q=HOENN+extension%3Amd&type=code) | Conferir testes nativos antes de classificar como jogável |
| **Sinnoh** | [R07: reservas](SINNOH_R07_DIAGNOSTICO_RESERVAS.md) · [QA isolado](SINNOH_S12_INSTALADOR_QA_ISOLADO_ACEITE.md) · [Pesquisar Sinnoh](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/search?q=SINNOH+extension%3Amd&type=code) | Documentação, requisitos R07/R08/R09 e QA nativa são verificações separadas |
| **Unova** | [Pesquisar documentação Unova](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/search?q=UNOVA+extension%3Amd&type=code) | Planejamento e contratos não significam mapas instalados |
| **Decades** | [Restaurar geração 9](RESTAURACAO_GERACAO9.md) · [Reaplicar regras](REAPLICAR_REGRAS_OFICIAIS.md) | Base de referência; preservar instalação e saves |

As pesquisas do GitHub abrangem documentos além deste índice e ajudam a localizar etapas numeradas sem alterar seus caminhos históricos.

## Jogo, regras e experiência

- [Seleção da região inicial](NOVO_JOGO_SELECAO_REGIONAL.md)
- [Viagem regional por NPC e itens regionais](VIAGEM_REGIONAL_LIVRE_NPC.md)
- [Progressão, níveis e animações](PROGRESSAO_E_ANIMACOES.md)
- [Battle Mode e desempenho](BATTLE_MODE_E_DESEMPENHO.md)
- [Geração autoral Dessastre Paradoxal](GERACAO_DESSASTRE_PARADOXAL.md)

## Ferramentas e criação de conteúdo

- [Blue Studio: plano do editor](PLANO_EDITOR_EMERALD_BLUE.md)
- [Auditoria do editor Pokémon](AUDITORIA_EDITOR_POKEMON.md) · [Golpes dos Pokémon](EDITOR_GOLPES_POKEMON.md)
- [Músicas: edição](EDITOR_MUSICAS.md) · [Mapeamento Kanto](KANTO_MUSICAS_MAPEAMENTO.md) · [Inventário](KANTO_MUSICAS_PACOTE.md) · [Plano histórico de aplicação](KANTO_PLANO_APLICAR_MUSICAS.md)
- [Diálogos FireRed EN/PT-BR](Guia_Dialogos_Pokemon_FireRed_EN_PT.md) · [Passo a passo](FIRERED_DIALOGOS_PASSO_A_PASSO.md)
- [Regras oficiais: reaplicação](REAPLICAR_REGRAS_OFICIAIS.md)

## Batalhas e testes

- [Hub de Batalha](HUB_BATALHA.md) · [Multiplayer](MULTIPLAYER.md)
- [Laboratório de batalha](LABORATORIO_BATALHA.md) · [IA Blue Radical](IA_BLUE_RADICAL.md)
- [Plano de testes Kanto](KANTO_CODEX_TESTES_E2E.md) · [Prompt histórico para Codex](KANTO_CODEX_PROMPT.md)
- [Workflows / Actions](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions) · [Pull requests](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pulls) · [Issues](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues)

## Site e distribuição

- [Instalação do jogo](INSTALACAO.md)
- [Site, publicação e Vercel](SITE_E_VERCEL.md) · [README do site](../site/README.md)
- [Página inicial do projeto](../README.md)

## Como saber se uma informação ainda vale?

1. Confira a **data**, o commit/PR e o escopo do documento. Relatórios numerados descrevem um estágio específico, não necessariamente o estado atual da `main`.
2. Diferencie **planejado**, **implementado no código**, **testado em CI**, **instalado em cópia QA** e **testado nativamente**.
3. Para pendências ou bloqueios, consulte a issue/PR associada e os [workflows](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions).
4. Em caso de contradição, não altere números ou status sem evidência: registre o conflito e atualize o documento responsável.

## Para manter a documentação organizada

Leia as [regras de organização e manutenção](PADRAO_DOCUMENTACAO.md). **Não mova nem apague** arquivos numerados de auditoria sem verificar referências em scripts, testes, portal, workflows e links externos.
