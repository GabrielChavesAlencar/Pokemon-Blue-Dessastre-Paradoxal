# Hoenn — ZIP recebido e preparação segura da fonte de mapas

**Data:** 13/11/2026  
**Referências:** [plano de 16 fases](HOENN_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) · [fontes de mapas e músicas](HOENN_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md).  
**Estado:** fonte pública e instalação local auditadas para a Fase 01; ZIP privado e direitos por recurso ainda pendentes. Nenhum arquivo de mapa Hoenn foi instalado no jogo.

## 1. O que pode e não pode ir ao GitHub público

O usuário enviou o ZIP **The Pokémon World Project - Hoenn.zip**, referente ao projeto de SocomSeal para Pokémon Essentials v21.1. Ele disponibiliza a fonte para uso como base de fangames; porém **não foi identificada uma licença explícita de redistribuição dos mapas, gráficos e áudios de todos os colaboradores** no repositório público. Os créditos indicam recursos adicionais de terceiros.

Por isso foram publicados apenas **código original do preparador, testes e metadados de auditoria**, sem copiar arquivos de terceiros para a main. Os arquivos RXDATA, gráficos, músicas e PBS originais ficam apenas na pasta ignorada **.blue-work/** e **não são instalados no game/** neste estágio.

O projeto já contém regras em [.gitignore](../.gitignore) para não versionar **game/**, **.blue-work/** e arquivos **.rxdata**. Não removê-las para publicar material do doador. Antes de redistribuição pública, conferir autorização e créditos por asset.

Fontes: https://github.com/SocomSeal/The-PMon-World-Project e https://www.pokecommunity.com/threads/the-pok%C3%A9mon-world-project.541079/.

## 2. Seleção dos arquivos úteis dentro do ZIP

| Parte do projeto doador | Seleção | Finalidade |
|---|---|---|
| Data/MapNNN.rxdata | Sim | Mapas físicos, eventos e geometria |
| Data/MapInfos.rxdata | Sim | Catálogo/organização dos mapas, apenas referência |
| Data/Tilesets.rxdata | Sim | Passabilidade/autotiles/tilesets, apenas referência |
| Data/CommonEvents.rxdata e Data/Animations.rxdata | Sim | Dependências para adaptação e auditoria |
| Graphics/ (imagens) | Sim | Tilesets, autotiles, personagens, panoramas, etc. |
| PBS/ (texto/JSON/CSV) | Sim | Treinadores, encontros e dados para análise |
| Audio/ | Opcional | Referência local de músicas/efeitos, direitos pendentes |
| Game.exe, Plugins/, Data/Scripts.rxdata, Data/System.rxdata | Não | Proibido trocar a engine e os scripts do Blue |

**Nada é copiado automaticamente para o jogo ou GitHub.** O preparador extrai apenas os recursos de referência para a área ignorada, com manifestos de hash. Importar de verdade exige remapear MapIDs/tilesets, entradas, NPCs e eventos.

## 3. Passo a passo no Windows

Coloque **The Pokémon World Project - Hoenn.zip** na raiz do projeto Dessastre Paradoxal, ao lado de RUN.bat. Execute:

**Auditoria somente leitura — sem criar arquivos:**

~~~powershell
py -3 scripts/regions/prepare_hoenn_source.py --archive "The Pokémon World Project - Hoenn.zip"
~~~

**Separar os mapas e dependências em pasta de trabalho privada:**

~~~powershell
py -3 scripts/regions/prepare_hoenn_source.py --archive "The Pokémon World Project - Hoenn.zip" --extract
~~~

**Opcional: separar também o áudio para consulta local, sem distribuição:**

~~~powershell
py -3 scripts/regions/prepare_hoenn_source.py --archive "The Pokémon World Project - Hoenn.zip" --extract --with-audio
~~~

**Verificar a ferramenta de seleção sem arquivos reais de Pokémon:**

~~~powershell
py -3 -m unittest discover -s tests -p "test_hoenn_source_prepare.py" -v
~~~

O script registra SHA-256 do ZIP, lista MapNNN, dependências e volumes, bloqueia travessia de diretórios/symlinks, nomes duplicados, dados muito grandes e conflitos entre arquivos existentes. A extração produz um **inventory.json** dentro de **.blue-work/hoenn-source/<prefixo_sha256>/**. O comando sem --extract é read-only.

## 4. Próxima etapa: mapas realmente jogáveis

1. Auditar o ZIP **real**, identificar hashes, número de mapas, os IDs fonte e suas dependências de gráficos.
2. Inventariar MapIDs do **game/** atual, os reservados por Kanto/Johto e o suporte a IDs acima de 999, antes de atribuir destinos.
3. Recriar conexões de mapas, warps, switch/variables, MapInfos, tilesets e Pokémon Essentials no motor Blue, sem importar scripts do doador.
4. Montar um **piloto separado** de Littleroot (casa do jogador, cidade, Birch/Lab) → Route 101 → Oldale.
5. Testar movimento, portas, NPCs, iniciais, batalhas nativas, captura, PC, save/reload e regressões.
6. Criar instalador transacional com backups/rollback e permitir Testar Hoenn no menu somente quando existir um piloto real.
7. Integrar os outros mapas por etapas conforme [o roteiro](HOENN_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md).

### Arquivos que foram publicados

- [scripts/regions/prepare_hoenn_source.py](../scripts/regions/prepare_hoenn_source.py)
- [tests/test_hoenn_source_prepare.py](../tests/test_hoenn_source_prepare.py)
- [data/regions/hoenn-source.json](../data/regions/hoenn-source.json)
- Este documento.

**Limite desta entrega:** a tentativa de abrir o ZIP montado no ambiente do assistente falhou por indisponibilidade técnica da ferramenta de leitura de arquivos. Os bytes reais não foram examinados nem foi calculado um hash do ZIP fornecido; o preparador e seus testes foram publicados mas ainda exigem execução/CI para validação. **Não existe importação jogável de Hoenn nesta etapa.**

## Auditoria da fonte pública e da instalação local (13/11/2026)

A revisão pública [c59233b](https://github.com/SocomSeal/The-PMon-World-Project/tree/c59233bdbaac4fbfeca6aa01c7f05be628da2a92) tem **373 mapas** com registro em MapInfos e **100 tilesets**. A árvore do subdiretório Hoenn estava completa. O script conferiu os IDs e os hashes dos arquivos de referência contra a árvore Git; não executou eventos nem programas do doador.

| Mapa de origem | ID | Tileset | Eventos de origem |
|---|---:|---:|---:|
| Littleroot | 7 | 23 | 28 |
| Casa do jogador | 8 | 34 | 42 |
| Laboratório do Birch | 11 | 35 | 19 |
| Rota 101 | 101 | 23 | 12 |
| Oldale | 12 | 23 | 16 |

Os arquivos dos tilesets/autotiles citados por esses cinco mapas aparecem no inventário público. Isso não valida conteúdo, passabilidade ou direitos desses PNGs. O Blue local tem **349 mapas físicos e 349 registros**, com maior ID **441**; **281 IDs colidem** com a numeração do doador e nenhum mapa ocupa a faixa Johto 600–681. Nenhum destino Hoenn foi reservado nesta verificação.

Use [audit_hoenn_baseline.py](../scripts/regions/audit_hoenn_baseline.py) com a resposta completa de `git/trees/<SHA da subárvore Hoenn>?recursive=1`, adicionando o campo `revision` com o SHA do commit público. Em `--source-data`, forneça as cópias locais de MapInfos, Tilesets e Map007/008/011/012/101 da revisão; em `--game-data`, indique o Data do Blue. Passe `--archive` somente se tiver o ZIP privado. O resultado da fonte pública está em [hoenn-source.json](../data/regions/hoenn-source.json).

**Fase 01: parcial.** O ZIP privado original continua sem SHA-256 confirmado e a autorização de redistribuição continua pendente. Nenhum mapa foi instalado; nenhuma fase foi aprovada por gameplay.
