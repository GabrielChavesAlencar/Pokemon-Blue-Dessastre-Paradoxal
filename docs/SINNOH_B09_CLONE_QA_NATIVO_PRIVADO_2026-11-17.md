# Sinnoh — Barra B / B09: cópia nativa privada de QA

**17/11/2026 — implementação técnica preparada, execução real no Windows ainda pendente.** O usuário ainda não enviou o relatório B08 gerado localmente. Esta fase não homologa R07/R08/R09 nem altera o status `planned` de Sinnoh/Unova ou os contadores B/C/D **0/13**.

## Objetivo e limites

A B09 prepara uma **cópia local, isolada e não autorizada a iniciar** do jogo Decades instalado, mesclando nela os 54 mapas sanitizados de Sinnoh do B08, depois de verificar novamente os hashes da B01 e a identidade exata B07→B08. **Nunca** escreve no Game.exe, Data, Graphics ou saves da instalação principal e não faz upload de arquivos do jogo ou da fonte.

Embora a cópia contenha o Game.exe original do usuário, **NÃO ABRA esse executável ainda**. Alguns runtimes compartilham dados/saves em APPDATA mesmo quando o diretório é duplicado. O isolamento de salvamento e testes do Game.exe/JoiPlay serão investigados e aprovados em uma próxima fase. O instalador original não é executado nem alterado por este script.

## Proteções aplicadas

1. Necessita do stage B07 real e do overlay QA B08 na pasta ignorada `.blue-work`; valida seus manifestos, os arquivos individualmente e a igualdade de conteúdo entre ambos, sem executar Ruby externo.
2. Reaudita com o inventário B01 os **648 MapIDs físicos**, hashes MapInfos/Tilesets, as **54 geometrias 442–495**, 14 PNGs e 484.722 células. Nenhum placeholder 496–517 é fabricado; nenhuma vaga Unova 518–599 é utilizada.
3. Lê o jogo local e prepara uma lista de arquivos permitidos com SHA-256. Exclui saves, diretórios de usuário, logs, caches e backups; detecta symlinks/junctions, nomes duplicados, Game.exe ausente e limites de tamanho. **Não copia saves nem perfis**.
4. Exibe apenas um plano/dry-run determinístico com SHA-256. O modo de clonagem exige `--clone --expected-plan-sha` que deve ser idêntico ao calculado; se o jogo mudar, recusa a operação.
5. Grava a cópia apenas em `.blue-work/sinnoh-b09-native-qa/native-<SHA>`, inicialmente em diretório temporário, valida novamente cada arquivo e faz rename atômico. Overlay substitui **somente as cópias de MapInfos/Tilesets**, acrescentando os 54 novos mapas e 14 PNGs.
6. Após a clonagem esperam-se **702 MapIDs na cópia privada (648 + 54)**. Mantêm-se intocados os 22 placeholders e todos os arquivos originais. A cópia não executa o Game.exe automaticamente e tem aviso `NAO_EXECUTAR_ANTES_DE_ISOLAR_SAVES.txt`.
7. O rollback `--rollback-sha` remove somente o clone privado intacto; se novos arquivos ou saves tiverem sido criados, recusa apagá-lo. Nunca remove a instalação original.

## Executar no Windows com duplo clique

Na cópia local atualizada do repositório, execute as ferramentas B07 e B08 antes da B09. Depois abra [SINNOH_B09_COPIA_NATIVA_QA_PRIVADA.bat](../SINNOH_B09_COPIA_NATIVA_QA_PRIVADA.bat). O iniciador procura o ZIP B01 e o Game.exe local, produz um dry-run e pergunta se você quer criar a **cópia privada**. Ele não exige PowerShell, mas requer Python 3.

Se a clonagem passar, o BAT gera `SINNOH_B09_RELATORIO_*.json` ao lado dos scripts. **Envie apenas esse JSON**, nunca o Game.exe, mapas RXDATA ou arquivos gráficos. Se B07/B08 ainda não foram executados, a B09 interromperá com uma mensagem clara e sem alterar seu jogo.

CLI avançada (na raiz do projeto):

```bat
py -3 scripts\regions\build_sinnoh_b09_native_qa.py
py -3 scripts\regions\build_sinnoh_b09_native_qa.py --latest --game-dir "%LOCALAPPDATA%\PokemonBlueDessastreParadoxal\game" --native-inventory "SINNOH_B01_INVENTARIO_DECADES.zip"
py -3 scripts\regions\build_sinnoh_b09_native_qa.py --latest --game-dir "%LOCALAPPDATA%\PokemonBlueDessastreParadoxal\game" --native-inventory "SINNOH_B01_INVENTARIO_DECADES.zip" --clone --expected-plan-sha "SHA_DO_DRY_RUN"
py -3 scripts\regions\build_sinnoh_b09_native_qa.py --rollback-sha "SHA_DO_DRY_RUN"
```

## Critérios de homologação pendentes

**R07:** manifestos de reservas FUTURAS de Kanto/Johto/Hoenn ainda não foram revisados/homologados. **R08:** direitos individuais dos tilesets e importação de conteúdo jogável ainda não resolvidos. **R09:** Game.exe/JoiPlay ainda não iniciados nem validados. Nenhuma aprovação de gameplay é inferida de arquivos existentes ou tests sintéticos. **A Barra B/C/D permanece 0/13.**

**Próxima etapa B10:** após o usuário enviar os relatórios B08 e B09, avaliar os caminhos de salvamento e elaborar uma maneira verificável de executar o jogo de QA sem compartilhar saves com a instalação principal; testar apenas com autorização e dados verificados.

[Contrato B09](../data/regions/sinnoh-b09-native-qa.json) · [Builder](../scripts/regions/build_sinnoh_b09_native_qa.py) · [18 testes de regressão](../tests/test_sinnoh_b09_native_qa.py).
