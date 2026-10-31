# Reaplicar as regras de Pokémon e golpes

O procedimento usa o Pokémon Decades 3.0.8 com Essentials 21.1 e Generation 9 Pack 3.3.3. Reproduz a restauração documentada em [RESTAURACAO_GERACAO9.md](RESTAURACAO_GERACAO9.md). Mapas, eventos, equipes e recursos audiovisuais permanecem na instalação local.

## Preparar e revisar

Na pasta do projeto, com Python 3.10+ e `tar` do Windows disponíveis:

```powershell
python scripts/official_rules/restore.py
```

O comando baixa as duas referências originais, valida SHA-256, prepara os arquivos e verifica as referências entre espécies, formas, habilidades, golpes, tipos e itens. O plano fica em `.blue-work/official-rules/plan.json`. Nessa etapa o jogo não é alterado.

Para usar arquivos já baixados, sem novo download:

```powershell
python scripts/official_rules/restore.py --essentials-zip "caminho/essentials-v21.1.zip" --gen9-rar "caminho/gen9-v3.3.3.rar"
```

## Aplicar e compilar

Feche o jogo antes de aplicar:

```powershell
python scripts/official_rules/restore.py --apply
```

O aplicador confere os hashes anteriores, cria um backup completo de `Data` e dos arquivos substituídos em `.blue-backups/official-rules-*`, e aplica apenas os caminhos previstos. Em caso de falha de gravação, restaura os arquivos já substituídos. Os hashes de mapas e arquivos da campanha são verificados novamente.

Em seguida, dentro de `game/`, execute:

```powershell
.\Game.exe debug
```

O modo Debug compila os PBS e executa a verificação única da engine. Essa execução encerra antes de carregar uma partida. Confira `Data/blue-official-validation.txt`: o resultado deve terminar em `RESULT=PASS`. Depois abra o jogo normalmente. O comando de preparação/aplicação não promete que a compilação já aconteceu; a confirmação é o relatório da engine.

Se usar uma instalação externa, acrescente `--game-dir "caminho/do/jogo"`. `--work-dir` permite escolher onde guardar downloads e arquivos intermediários.

## Escopo e compatibilidade

- Restaura os registros existentes por ID, incluindo atributos, tipos, habilidades, evoluções e listas de golpes.
- Reverte as alterações de batalha identificadas no núcleo e no plugin de geração 9, usando a mesma versão dos componentes.
- Mantém as pedras universais de Mega Evolução da campanha e os registros exclusivos sem equivalente nas referências.
- Mantém a interface de EVs com atributos independentes e limites 510/252.
- Corrige a leitura de quebras de linha do compilador DBK para aceitar PBS com LF ou CRLF.
- Os arquivos do jogo, referências baixadas, arquivos intermediários e backups ficam fora do Git. O repositório distribui o procedimento e as verificações.
- Os arquivos de equipes e encontros são preservados; conteúdo atribuído explicitamente pelos eventos e tutores do fangame continua disponível.

O script se destina à versão da base indicada acima e recusa arquivos de referência cujo hash divergir. Não o execute ao mesmo tempo que o jogo ou outro editor estiver gravando os PBS.
