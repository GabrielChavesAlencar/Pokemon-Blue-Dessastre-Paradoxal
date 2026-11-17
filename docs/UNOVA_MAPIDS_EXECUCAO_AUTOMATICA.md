# Unova — RUN automático de MapIDs (A04 + A05)

**Data:** 17/11/2026 · Projeto: Pokémon Blue: Dessastre Paradoxal

## Executar sem escolher pastas

**Dê dois cliques em [RUN_UNOVA_MAPIDS.bat](../RUN_UNOVA_MAPIDS.bat)** na raiz atualizada do projeto.

O BAT verifica Python 3.11+ existente e executa [unova_auto_mapids.py](../scripts/regions/unova_auto_mapids.py). O Python procura automaticamente a instalação, executa A04 e A05 e abre o resultado final no Bloco de Notas do Windows. **Não precisa abrir CMD, PowerShell nem selecionar arquivos em caixas de diálogo.**

### Caminhos procurados, em ordem de preferência

1. %LOCALAPPDATA%\PokemonBlueDessastreParadoxal\game — caminho conhecido do instalador geral Blue-Story; espera encontrar Game.exe e Data\MapInfos.rxdata.
2. Variações da mesma instalação sob %LOCALAPPDATA% e %USERPROFILE%\AppData\Local, incluindo %LOCALAPPDATA%\Blue-Story\game.
3. Game ao lado/abaixo da pasta do projeto, caso seja cópia completa contendo Game.exe e MapInfos.
4. Alternativa explícita, apenas quando necessário: variável de ambiente BLUE_DECADES_GAME_DIR apontando para a pasta game ou Data. Ela impede seleção de outra instalação, mas não é necessária na instalação padrão.

O localizador não faz varredura recursiva de todo o disco, Downloads ou saves. Exige Game.exe, MapInfos e pelo menos 20 arquivos MapNNN.rxdata para diferenciar uma instalação de uma pasta de código vazia. Ele bloqueia diretórios com links simbólicos e entradas suspeitas. Se a instalação padrão for encontrada, ela tem preferência sobre cópias antigas de desenvolvimento. Quando existirem múltiplas instalações alternativas indistinguíveis, ele bloqueia em vez de selecionar arbitrariamente.

### O que o RUN faz automaticamente

1. **A04:** lê MapInfos.rxdata (dados Ruby Marshal sem executar Ruby), inventaria MapNNN.rxdata, calcula SHA-256 de arquivos, classifica IDs observados/declarados e detecta arquivos órfãos. Não altera Data.
2. **A05:** recebe diretamente o relatório A04 exato e o compara com B01/B04/B05 e o catálogo Sinnoh/Unova. Calcula o status do bloco histórico candidato 518–599, marca ocupações novas, mantém Sinnoh 442–517 e Hoenn 700–999 protegidos e não associa IDs a áreas simbólicas.
3. **Resultado:** salva os JSONs de auditoria originais com nomes baseados em hash, imutáveis, mais um resumo simples no caminho estável: .blue-work\unova\audit\LEIA_AQUI_UNOVA_MAPIDS.txt. O Bloco de Notas abre automaticamente esse arquivo para facilitar a leitura.

A04 é executada contra a **instalação consolidada** detectada; Kanto/Johto/Hoenn/Sinnoh que já estiverem nela são contabilizados na ocupação total. O RUN **não inventa snapshots regionais separados** nem infere propriedade por região. Para provar atribuição regional é necessário o histórico de manifestos.

## Resultados possíveis

| Status | Significado |
|---|---|
| AUTO_A04_A05_DONE_NOT_NATIVE_APPROVED | A04 e A05 executaram. O relatório A05 pode indicar colisões ou divergências; **não aprova reservas**. |
| BLOCKED_NO_AUTOMATIC_GAME_FOUND | Nenhuma instalação válida encontrada nos locais conhecidos, ou várias alternativas impedem escolha segura. |
| AUTO_A04_OR_A05_BLOCKED | Instalação selecionada, mas MapInfos/RXDATA ou comparação falhou. Não substitui dados. |

### Segurança e limites

- Não baixa/instala Python nem outros programas.
- Não abre Game.exe, não altera MapInfos/MapNNN, Scripts, Blue-Story, PBS, tilesets ou saves; apenas grava relatórios privados sob .blue-work/unova/audit.
- Não instala Unova, não reserva MapIDs e não declara a região jogável. Bloco candidato "ainda desocupado" significa **somente no snapshot observado**, nunca homologação.
- Se o MapInfos atual divergir do B01 de 17/11/2026, isso aparece no diagnóstico sem sobrescrever nem reverter a instalação.
- Barra A = **0/8** até revisão de reservas e mapas de origem; E = **4/8** e Unova jogável **0/32**.

## O que enviar depois

Abra a pasta .blue-work\unova\audit e envie o arquivo a05-candidates-HASH.json indicado no bloco de notas. Não precisa localizar MapInfos manualmente.

Se aparecer "não encontrado", o resumo lista os caminhos pesquisados. Para uma instalação personalizada, basta informar onde está o Game.exe para acrescentar esse local ao RUN em uma atualização futura; não envie executável nem saves.
