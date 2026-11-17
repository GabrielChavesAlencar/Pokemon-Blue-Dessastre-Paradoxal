# Sinnoh — B08: auditoria do estágio privado e overlay de QA

**17/11/2026.** Implementação disponível, mas ainda não foi apresentado o stage B07 gerado na máquina do usuário. **B/C/D = 0/13; R07, R08, R09 pendentes**. Nenhum mapa foi instalado no jogo principal.

## Resultado da auditoria real de PNGs

Foram reabertos, sem executar scripts, os recursos necessários aos tilesets de origem 1 e 31 no ZIP Pokémon World V18 do usuário. **14 PNGs (12 autotiles e 2 tilesets)** foram validados quanto à assinatura, chunks IHDR/IDAT/IEND e CRC-32. Somam **3.808.519 bytes**. Os dois tilesets grandes têm dimensões **256×50.000** (OutsideWorld2.7) e **256×70.000** (SinnohCompleteTileset). Isso não comprova que o Game.exe/JoiPlay renderize imagens tão altas, nem autorização de redistribuição.

Relatório com dimensões e hashes SHA-256 individuais: [catálogo PNG B08](../data/regions/sinnoh-b08-real-png-audit.json). Os gráficos binários não foram publicados no GitHub.

## Inspeção da pasta B07 (somente leitura)

O [auditor B08](../scripts/regions/audit_sinnoh_b08_private_qa.py) exige um stage B07 previamente gerado sob a pasta ignorada .blue-work/sinnoh-stage. Ele valida a identidade por SHA-256, o manifesto, todos os arquivos e a ausência de extras e symlinks. Depois abre os RXDATA usando o parser Ruby Marshal inerte, sem carregar código externo.

Verificações: **54 mapas 442–495**, 22 placeholders 496–517 ausentes, **484.722 células de terreno não vazias**, eventos/encounters e música apagados; MapInfos original preservado; tabela Tilesets original preservada; **exatamente dois tilesets adicionados** à cópia privada; contagens de uso 53+1; referências gráficas resolvidas para os 14 PNGs, com prefixo SHA e CRC correto, sem arquivos órfãos.

Qualquer diferença de MapID, PNG, tileset, áudio, conteúdo ou hash bloqueia a preparação do QA e deixa o stage para diagnóstico.

## Preparação nativa isolada: overlay privado, ainda não executável

Se a verificação passar **e o game/Data atual for idêntico à B01**, a opção --prepare-qa gera uma nova pasta em .blue-work/sinnoh-b08-qa/qa-<SHA>, com cópias dos 54 mapas, MapInfos, Tilesets e 14 PNGs e um qa-overlay-manifest.json. A operação é atômica, não sobrescreve um QA anterior e não contém Game.exe, saves, scripts ou runtime. **Esse overlay não é um jogo pronto, não deve ser copiado para o jogo original e não atesta permissões de uso**.

## Como usar com um clique no Windows

1. Na cópia local atualizada do repositório, execute SINNOH_B07_PILOTO_PRIVADO.bat se ainda não gerou o estágio B07.
2. Dê dois cliques em **[SINNOH_B08_VERIFICAR_QA_PRIVADO.bat](../SINNOH_B08_VERIFICAR_QA_PRIVADO.bat)**. Precisa de Python 3, mas não de PowerShell ou Game.exe.
3. O BAT identifica a única pasta B07, localiza ou pede o ZIP B01 e game/Data, inspeciona os arquivos e, quando seguro, cria o QA overlay e um relatório SINNOH_B08_RELATORIO_QA_*.json.
4. Envie **somente o relatório JSON** na conversa para validar os resultados reais. Não envie arte ou saves.

Para inspeção sem stage, apenas metadados: python scripts/regions/audit_sinnoh_b08_private_qa.py. Para execução isolada pela CLI: python scripts/regions/audit_sinnoh_b08_private_qa.py --latest --native-inventory B01.zip --game-data CAMINHO_DE_GAME_DATA --prepare-qa.

Se houver mais de um estágio B07, --latest se recusa a escolher automaticamente; escolha explicitamente --stage-sha. Se o jogo foi atualizado desde a B01, a B08 aborta sem copiar para o jogo.

## Portões de segurança e próxima etapa

O auditor B08 só valida geometria e referências de assets no estágio. **R07** requer comprovação das reservas futuras de Kanto/Johto/Hoenn. **R08** ainda requer autorização dos recursos e integração privada de verdade. **R09** depende de Game.exe/JoiPlay, rotas, portais, NPCs e saves. B/C/D permanecem **0/13**; Sinnoh e Unova planned. O próximo trabalho, B09, é receber o relatório B08 real e planejar uma cópia nativa de QA sem alterar a instalação principal.

[Contrato B08](../data/regions/sinnoh-b08-private-qa.json) · [Auditor B08](../scripts/regions/audit_sinnoh_b08_private_qa.py) · [22 testes](../tests/test_sinnoh_b08_private_qa.py).
