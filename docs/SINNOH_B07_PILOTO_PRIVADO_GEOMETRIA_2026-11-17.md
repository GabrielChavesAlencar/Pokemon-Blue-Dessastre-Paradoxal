# Sinnoh — B07: piloto privado de geometria e rollback

**Data:** 17/11/2026. **Status:** conversor privado implementado e testado com fixtures sintéticos; ainda não executado na instalação nativa do usuário. Barras B/C/D = 0/13, R07/R08/R09 pendentes, Sinnoh planned.

## Pré-validação dos arquivos reais fornecidos pelo usuário

- Foram inspecionados os 54 mapas com terreno válido (RPG Maker Table 3D), contendo 484.722 células não vazias de terreno.
- Desses mapas, 53 usam o tileset de origem 31 e um usa o 1.
- Os 14 PNGs necessários foram encontrados no ZIP doador (total de 3.808.519 bytes, sem copiá-los para o GitHub).
- Os 397 eventos da fonte **não** serão importados para o piloto; o código cria novos mapas sem eventos e sem música.
- Os 22 mapas sem terreno não entram no estágio; seus 22 candidatos de MapID 496–517 continuam pendentes.

Os resultados derivados estão em [sinnoh-b07-private-source-preflight.json](../data/regions/sinnoh-b07-private-source-preflight.json). A presença dos arquivos gráficos não constitui prova de autorização para redistribuição.

## O que o builder B07 gera

[Builder Python](../scripts/regions/build_sinnoh_b07_private_stage.py) + [contrato de proteção](../data/regions/sinnoh-b07-private-stage.json).

O builder utiliza o ZIP doador original, o ZIP privado do inventário B01 e os contratos B00/B04 V2/B05/B06. Ele confere SHA do arquivo completo, hashes dos 76 mapas de origem, MapInfos e Tilesets, além dos 648 MapIDs ocupados.

Para a prévia, cria **54 mapas sanitizados com terreno nos destinos candidatos 442–495**, mais cópias da tabela MapInfos e da tabela Tilesets nativas. Na cópia, acrescenta dois tilesets novos ao final da tabela e arquivos PNG renomeados com hash, sem sobrescrever os índices 1 e 31 do Decades. Nenhum evento, trainer, script, encontro ou áudio do doador é copiado.

Por segurança, o dry-run não grava arquivos. Antes de gravar um estágio privado, é necessário conferir **os hashes atuais e os MapNNN de game/Data**, e apresentar o SHA de dry-run calculado no primeiro passo. O destino é exclusivamente a pasta ignorada **.blue-work/sinnoh-stage/** do repositório; nunca escreve no jogo principal ou nos saves.

O rollback usa o SHA original da transação, revalida todos os arquivos e **recusa apagar um estágio que tenha sido alterado**.

## Execução local facilitada (Windows)

O arquivo [SINNOH_B07_PILOTO_PRIVADO.bat](../SINNOH_B07_PILOTO_PRIVADO.bat) é um iniciador por duplo clique. Ele procura o ZIP doador e o inventário B01 em Downloads ou na raiz do repositório; se faltar, pede o caminho. Também procura a pasta real game/Data. Requer Python 3 instalado e o repositório local; **não abre PowerShell, Game.exe ou JoiPlay**.

O BAT executa o dry-run em memória, obtém o SHA calculado e só então executa o estágio privado, se o baseline for igual ao recebido. O resultado contém a localização e o identificador do estágio.

Para diagnosticar apenas com os metadados do GitHub, sem os ZIPs privados:

    python scripts/regions/build_sinnoh_b07_private_stage.py

Para executar o dry-run usando os arquivos da sua máquina:

    python scripts/regions/build_sinnoh_b07_private_stage.py --source-zip "Pokemon World V18.zip" --native-inventory "SINNOH_B01_INVENTARIO_DECADES.zip"

Para gravar stage, informar também o game/Data atual, a opção --stage e --expected-sha com o SHA exibido no dry-run. Para apagar um estágio privado intacto, executar o mesmo script com --rollback-sha "SHA_DO_DRY_RUN". O rollback **não** pode apagar conteúdo do game/Data.

## O que ainda falta para aprovar tecnicamente

A fase B07 **não equivale a uma instalação nativa**. Ainda faltam: comprovar as reservas futuras R07, resolver os direitos de recursos gráficos, revisar o estágio real na máquina do usuário, definir os interiores dos 22 mapas vazios, criar conexões/eventos próprios e testar o jogo no Game.exe/JoiPlay posteriormente.

**Barra B aprovada 0/13**, C/D 0/13; a engenharia do piloto é entregável separado de aprovação jogável. Nenhuma licença, posse de MapID ou compatibilidade foi presumida.

Código testado por [14 testes](../tests/test_sinnoh_b07_private_stage.py) mais as suítes CH19, S30 e Portal.
