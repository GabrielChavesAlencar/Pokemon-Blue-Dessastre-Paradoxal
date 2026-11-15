# Kanto integrado — erro EventScriptError na primeira batalha contra Gary

**Atualizado:** 15/11/2026. **Situação:** correção preventiva de runtime, sincronização do instalador e testes Ruby enviados à `main`; **ainda depende de reprodução no Game.exe real**.

## Sintoma recebido

No laboratório de Oak, após a fala «Gary: Ei, P! Antes de ir, vamos testar nossos Pokémon!», o jogo apresentou `Script 'Interpreter' line 177: EventScriptError occurred`. Esse texto é o **invólucro** do erro do intérprete, e **não identifica** a exceção interna. Não é possível provar a causa exata só pela imagem.

A chamada de roteiro está em `scripts/regions/KantoPilot.rb`, `BlueKantoPilot.rival`:

- Versão 11 quando o jogador escolheu Bulbasaur.
- Versão 12 quando escolheu Charmander.
- Versão 13 quando escolheu Squirtle.
- Identidade de treinador usada em todas: `BLUE_KANTO_RIVAL,Blue`, com time original do arquivo `PBS/trainers_kanto.txt` (gerado da fonte FRLG auditada); o apelido do NPC é Gary, mas a chave interna do PBS é Blue.

## Alterações implementadas

1. **Compilação pelo Blue-Story.exe**: para uma instalação Kanto já integrada, o atualizador verifica um selo SHA-256 das tabelas `trainers_kanto.txt` e `trainer_types_kanto.txt`. Em instalação nova, dados desatualizados ou tabela modificada, cria o pedido de recompilação nativa `Data/blue-compile-request.txt` **uma vez por versão**. Não apaga o save, não migra MapIDs, não sobrescreve times de Decades e não repete compilação em toda abertura quando os dados estão atualizados.
2. **Recuperação segura durante o evento**: se `GameData::Trainer` não contém a variante 11/12/13, `BlueKantoPilot.ensure_lab_rival_trainer` lê e valida **somente a seção exata** do PBS original instalado. Verifica tipo, espécies, níveis, golpes e itens existentes e registra o time em memória para a batalha. Não cria uma equipe inventada. Também solicita recompilação nativa para a próxima inicialização.
3. **Tratamento de erro preciso**: se o motor de batalha falhar, registra o nome da exceção e até 18 linhas da stack em `game/Data/blue-kanto-rival-error.log`, limpa regras de batalha pendentes quando a API existe e mostra um aviso legível. A batalha permanece pendente e pode ser tentada novamente. A falha não concede vitória, não adiciona insígnias e não modifica o save da campanha.
4. **Música opcional**: um erro ao restaurar a música de aparição de Gary não deve interromper a primeira batalha. O problema é registrado sem substituir a música do jogo principal.
5. **Blackout nativo**: derrota na primeira batalha continua usando a regra `cannotLose` e o último Centro Pokémon, sem recuperação silenciosa nem concessão de progresso.

## Como validar no seu PC

1. **Feche o Game.exe** e mantenha o save de teste. Não exclua `game/` nem seus saves.
2. Execute **Blue-Story.exe** normalmente com internet. Ele atualizará o código da `main`, validará Kanto integrado, sincronizará o plugin (se o checksum instalado corresponder ao original) e requisitará a compilação das equipes de Gary.
3. Na primeira inicialização após a atualização, deixe terminar a recompilação nativa. Se o jogo encerrar ao compilar, abra novamente.
4. **Continue o save anterior ao combate**. Atravesse a linha de saída do laboratório, deixe Gary falar e confira que a batalha inicia sem popup de `EventScriptError`.
5. Teste os três iniciais em **saves novos separados**; após vencer, Gary não deve desafiar novamente. Ao perder, deve retornar ao último Centro Pokémon e manter o rival como pendente.

### Se o erro persistir

Anexe o conteúdo do arquivo **`game/Data/blue-kanto-rival-error.log`** após tentar novamente. Se ele não existir, procure **`errorlog.txt`**, geralmente na pasta do jogo ou na pasta de dados/saves do Essentials, e inclua o trecho mais recente com `Exception`, `Message`, `Full script` e `Backtrace`. Não é necessário enviar saves pessoais.

As verificações Ruby de fixture foram adicionadas à CI:

```powershell
ruby -c scripts/regions/KantoPilot.rb
ruby tests/kanto_gary_battle_runtime.rb scripts/regions/KantoPilot.rb
ruby tests/kanto_blackout_runtime.rb scripts/regions/KantoPilot.rb
python tests/test_kanto_auto_integrate.py
```

Esses testes verificam o contrato de código, as variantes do PBS, vitória/derrota, falha de BGM e recuperabilidade. **Não substituem a abertura real da tela de batalha em Game.exe**.
