# J10 — Editor de mapas originais de Sinnoh (sem jogo instalado)

Base: J09 integrada na main, PR #239; cinco ambientes reais seguem ausentes. A J10 implementa **autoria manual** e compilação de geometria somente em workspace local privado. **Não contém os cinco mapas prontos**. Próxima validação: [J11 #242](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/242).

## Os cinco ambientes que precisam ser desenhados

1. `SINNOH_PLAYER_BEDROOM` — quarto do protagonista.
2. `SINNOH_PLAYER_HOUSE_1F` — térreo da casa.
3. `SINNOH_BARRY_HOUSE` — casa de Barry.
4. `SINNOH_LAKE_VERITY` — Lago Verity.
5. `SINNOH_PROFESSOR_ROWAN_LABORATORY` — laboratório de Rowan.

Não reutilizar placeholders vazios Map005/263/272, arquivos de outro projeto sem autorização ou coordenadas presumidas. As quatro áreas exteriores Map209/210/227/228 continuam em ZIP original privado, SHA-256 da auditoria J09. Nenhum arquivo binário/asset externo entra no GitHub.

## 1. Abrir o editor

No portal, abrir `/sinnoh-j10-editor.html`. O editor HTML é **client-side e sem chamadas de rede**: selecione no seu dispositivo um PNG de tileset RMXP (256 px de largura, altura múltipla de 32), de autoria própria ou cujo uso você realmente tem permissão. O navegador calcula SHA-256 do PNG, mostra a paleta 32×32 e permite desenhar com clique/arraste em três camadas independentes. A versão inicial não suporta autotiles RMXP 48–383; use tiles explícitos do PNG para rascunhos, sem assumir passabilidade, animação de água ou integração com o jogo.

Escolha o símbolo da cena, tamanho (12–120 de largura, 10–120 de altura, no máximo 14.400 células) e `tileset_id` local, que deverá ser reconciliado com `Tilesets.rxdata` na J11. Preencha e revise a geometria manualmente. O editor mantém o desenho de cada uma das cinco cenas **apenas na memória da aba**: exporte os JSON antes de recarregar ou fechar. Cada JSON contém três camadas completas, símbolos, metadados de autoria/revisão, SHA do PNG, eventos vazios, MapID nulo e `native_gameplay_verified=false`.

**IMPORTANTE:** referência de autoria e de permissão são declarações locais para futura revisão, não licença e não certificação automática. O editor não cria desenhos prontos nem recursos protegidos. O JSON não é aprovado para publicação.

## 2. Colocar arquivos na pasta privada da cópia do repositório

Dentro da pasta em que está o código do projeto (não a instalação `game/`):

```text
.blue-work/
  sinnoh-j10-tilesets/
    SEU_TILESET_AUTORIZADO.png
  sinnoh-j10-drafts/
    SINNOH_PLAYER_BEDROOM.json
    SINNOH_PLAYER_HOUSE_1F.json
    SINNOH_BARRY_HOUSE.json
    SINNOH_LAKE_VERITY.json
    SINNOH_PROFESSOR_ROWAN_LABORATORY.json
```

O nome do PNG em cada JSON deve coincidir **exatamente** com o nome do PNG colocado em `sinnoh-j10-tilesets/`. O hash SHA-256 também deve coincidir. O arquivo `.blue-work/` já é ignorado pelo Git. Não copie esses dados para `site/public/`, `data/` ou `game/`; não envie prints com recursos privados nem dados pessoais.

## 3. Pré-voo (somente leitura) e exportação RXDATA privada

Na **cópia de código** (Python 3.11+), execute:

```cmd
python scripts/regions/author_sinnoh_playable_j10.py
```

O comando padrão verifica todos os cinco JSONs e PNGs, dimensões, IDs, SHA, camadas, autoria, terreno e duplicatas, mas **não escreve um único mapa**. Ele rejeita cenas vazias, IDs fora da imagem e qualquer referência falsa à liberação nativa. Regras mínimas de sanidade: 60% da base, 70% das posições com terreno, quatro tiles distintos e quatro tiles em camadas altas. Esses limiares **não aprovam** qualidade visual nem licenciamento.

Apenas após a revisão de todos os cinco, execute:

```cmd
python scripts/regions/author_sinnoh_playable_j10.py --build
```

Se tudo estiver válido, o comando gera **exatamente cinco RXDATA de geometria sem eventos**, como objetos `RPG::Map` com tabela de três camadas, em:

```text
.blue-work/sinnoh-j09-authored/
```

Cada saída é verificada pelo auditor inerte J09, criada de forma transacional e **nunca sobrescrita**. Nenhum MapID, guerra de eventos, passabilidade, scripts Ruby, gráficos, NPCs, sprites ou coordenadas é inserido automaticamente; nenhum jogo, save ou Game.exe/JoiPlay é aberto. Para revisar esses mapas com a J09, use o comando da documentação `SINNOH_J09_FONTE_REAL_MAPAS_R07_R08.md` com os materiais de origem e recibos privados.

## 4. O que continua pendente para J11 e J12

- Os cinco desenhos humanos reais ainda não estão disponíveis. A publicação desta ferramenta **não é** a publicação dos mapas.
- R07: verificar IDs e `MapInfos.rxdata` reais contra todas as reservas (Decades/Kanto/Johto/Hoenn/Unova), sem confiar só em faixa planejada 442–517.
- R08: comprovar individualmente permissões de **nove mapas**, PNGs, sprites, autotiles, áudio e demais recursos; verificar o `tileset_id` e tabelas reais de passabilidade.
- J11: auditar geometria, colisões, portas e coordenadas reais, montar somente QA Windows isolada (J03/J04/J06).
- J12: executar e revisar independentemente 43 casos Windows e 1 Android JoiPlay (R09) com dados autorizados. Não tocar em `game/` nem nos saves pessoais.

**Estado público fixo até provas novas:** J01–J08 código 8/8; J10 ferramenta de autoria disponível, **cinco mapas ainda não desenhados/recebidos**, 0/9 mapas instalados, 0/44 QA nativa, R07/R08/R09 pendentes, Sinnoh planned/não jogável.

Continuar na issue [J11 #242](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/242) somente com mapas privados genuínos, sem publicar conteúdos de terceiros.
