# Hoenn — Etapa 02: abertura, maleta do Birch, rival e recompensas

**Data:** 14/11/2026  
**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Base de auditoria:** [Etapa 01](HOENN_AUDITORIA_PILOTO_ETAPA_01.md) · [Detonado Emerald](HOENN_DETONADO_EMERALD_REFERENCIA_ORGANIZADA.md)  
**Estado:** **scripts e testes de implementação para CÓPIA ISOLADA**. Não existe aprovação do Game.exe, do Android, nem integração desta fase ao jogo principal.

## 1. O que a Etapa 02 fez no GitHub

- **\`scripts/regions/HoennPilot.rb\`:** ativou flags exclusivas de Hoenn para o resgate de Birch, a seleção do inicial, a batalha do rival na Route 103, o recebimento da Pokédex e dos Tênis de Corrida. O relógio e a mãe continuam sendo pré-requisitos do resgate.
- **\`scripts/regions/pilot_hoenn.py\`:** passou a criar três eventos físicos de Poké Bola na Route 101, em posições determinadas a partir de **tiles realmente passáveis** do pacote auditado, em vez de depender da lista de seleção de diálogos. O encontro do rival é colocado em uma área alcançável da Route 103, também validada por busca na geometria do mapa. Se nenhuma posição segura existir, o gerador **recusa a montagem**.
- **\`PBS/trainers_hoenn_pilot.txt\` da cópia:** além dos quatro treinadores da Route 102, agora cadastra **seis combinações de rival**: May e Brendan, cada qual com três equipes possíveis. O trainer type \`RIVAL1\` é reutilizado da instalação Blue; o gerador aborta caso o tipo esteja ausente ou os IDs PBS entrem em conflito com treinadores nativos.
- **\`BlueHoennPilot.verify_compilation\`:** passa a exigir as seis equipes do rival no PBS compilado antes de aprovar a cópia.
- **\`tests/hoenn_pilot_runtime.rb\`:** novo harness Ruby sem engine para simular início, escolha da bola, derrota/vitória, flags regionais, bag cheia, save/reload e migração de estados antigos.
- **\`tests/test_hoenn_stage2.py\`:** testes Python de criação dos eventos, três iniciais, seis variantes e falha segura de geometria.
- **\`scripts/regions/audit_hoenn_pilot_contract.py\`:** auditoria estática atualizada com o escopo da Etapa 02. Mantém \`native_assets_examined=false\`, \`game_exe_tested=false\` e \`android_tested=false\`.
- **\`.github/workflows/regression.yml\`:** executa a auditoria Python, verificação de sintaxe Ruby e o novo harness Ruby.

## 2. Fluxo esperado na cópia de teste

1. Novo jogo entra na casa do jogador em Littleroot (não há cena visual do caminhão nesta fase).
2. Falar com a mãe, ajustar o relógio no quarto e retornar à mãe.
3. Na saída norte para Route 101, Birch pede ajuda. Sem esses pré-requisitos, o evento devolve o personagem à parte sul.
4. Escolher **uma das três Poké Bolas FÍSICAS** próximas ao evento do resgate: **Treecko**, **Torchic** ou **Mudkip**. A adição à party e a confirmação são verificadas antes da gravação da escolha.
5. Batalhar contra Zigzagoon. Com \`canLose\`, uma derrota não reinicia o tutorial. Birch pede que se visite o laboratório.
6. Atravessar Route 101, Oldale e subir à Route 103; o evento físico do rival dispara uma luta com time que tem vantagem de tipo:
   - Player Treecko → May/Brendan Torchic (PBS versão 210);
   - Player Torchic → May/Brendan Mudkip (versão 211);
   - Player Mudkip → May/Brendan Treecko (versão 212).
7. Ganhar ou perder a luta do rival conclui **somente esse marco da história**. A flag \`rival_103_done\` impede repetição ao voltar ou carregar o save.
8. Voltar ao laboratório de Birch para receber **Pokédex**. Novos saves também recebem **cinco Poké Bolas** nessa etapa; saves do piloto antigo, que já as receberam ao pegar o inicial, não as recebem novamente.
9. Conversar com a mãe para obter **Running Shoes**. As flags impedem dupla entrega ao recarregar.

**Nota:** o piloto usa os níveis históricos/base (nível 5 no duelo do primeiro rival); o balanceamento próprio Blue deve ser conferido no jogo real, e não substituído por níveis fixos no catálogo.

## 3. Salvaguardas

- O plugin só modifica \`$PokemonGlobal.blue_regions["hoenn_pilot"]\` quando a região ativa é \`"HOENN"\`.
- Nenhum mapa, save, PBS, áudio, sprite ou script da instalação principal é substituído pelo commit do GitHub.
- O montador continua produzindo uma **nova pasta independente**, com remapeamento dos MapIDs existentes e checksum do conteúdo doador \`c59233bdbaac4fbfeca6aa01c7f05be628da2a92\`.
- A abertura nova coloca três bolas sobre locais físicos auditados; não sobrescreve recursos do mapa original indiscriminadamente.
- A batalha do rival exige equipes PBS, e o sprite é **selecionado da instalação local**. Se não houver sprite próprio de May/Brendan, o montador marca \`rival_sprite_placeholder=true\` e recorre a sprite nativo de Lass; **esse fallback não é aceite visual**.
- A rota de recompensa trata falha ao acrescentar cinco Poké Bolas (bolsa cheia): não libera a Pokédex sem conceder a recompensa para um novo save. Repetição e relançamento não duplicam iniciais, Pokédex nem Running Shoes.
- **Limitação de posicionamento:** uma posição caminhável não garante a encenação visual ideal; o rival precisa bloquear a passagem ou ser encontrado naturalmente. Isso exige sessão real no Game.exe.

## 4. Como verificar

### Testes independentes da engine

~~~bash
python -m unittest discover -s tests -p "test_hoenn_*.py" -v
python scripts/regions/audit_hoenn_pilot_contract.py --strict
ruby -c scripts/regions/HoennPilot.rb
ruby tests/hoenn_pilot_runtime.rb scripts/regions/HoennPilot.rb
~~~

### Preparar e testar a cópia de verdade (somente com os arquivos da sua máquina)

1. Localizar a instalação privada \`game/\`, o ZIP de Hoenn do *The Pokémon World Project* e a árvore completa da revisão fixa.
2. Seguir [preparação segura do ZIP](HOENN_PREPARACAO_ZIP_E_RECURSOS.md), preservando o pacote original e seus hashes.
3. Executar o gerador isolado com caminhos que **não** apontem para a instalação principal:
   ~~~powershell
   py -3 scripts/regions/pilot_hoenn.py --game "game" --source ".blue-work/hoenn-source/PASTA_EXTRAIDA/Data" --inventory ".blue-work/hoenn-source/ARVORE_AUDITADA.json" --output ".blue-work/hoenn-piloto-etapa02"
   ~~~
   **Os dois caminhos de fonte acima são placeholders** e devem ser substituídos por caminhos reais produzidos pelo inventário do ZIP; não presumir que o \`inventory.json\` local seja uma árvore Git completa. \`--inventory\` exige a árvore Git do commit fixo, com \`revision\`, \`truncated=false\` e blobs \`Data/*\`.
4. Abrir o **Game.exe** da pasta gerada, compilar os PBS quando solicitado pelo piloto, validar a posição das bolas, derrotas, sprites, portais, encontros, audios e persistência.
5. Não copiar a pasta de saída para \`game/\` principal ou publicar recursos do doador sem auditoria dos direitos de redistribuição.

## 5. Validações que ainda dependem de Windows/Game.exe

- [ ] Montar com o ZIP real e testar as nove passabilidades, três bolas e o ponto do rival (sem obstáculo indevido).
- [ ] Confirmar que \`RIVAL1\` existe no PBS nativo e as seis combinações são compiladas, com nome/gênero/sprite adequados.
- [ ] Testar sequência Birch → escolha → Zigzagoon, incluindo derrota, voltar à cena e salvar/carregar.
- [ ] Testar chegada à Route 103, rival (ambos os gêneros), retorno ao laboratório e cinco Poké Bolas.
- [ ] Testar Pokédex regional, Running Shoes, mochila cheia, duelo já vencido e transferência de save antigo.
- [ ] Conferir itens de chão, placas e NPCs não presentes no piloto, música regional e gráficos de Oldale/Littleroot.
- [ ] Confirmar que a Route 102 não permite pular a progressão; se a geometria permitir, adicionar bloqueio seguro.
- [ ] Conferir que a cópia de teste não altera os saves da instalação principal ou as outras regiões.
- [ ] Confirmar no Android/JoiPlay separadamente.

## 6. Limitações e etapa seguinte

**Não estão incluídos:** introdução animada do caminhão, composição exaustiva de NPCs e placas, interiores extras de Littleroot, eventos de Petalburg, Wally ou Norman, nem uma versão completa das Routes 104+. Esses dados dependem da auditoria de geometria e eventos reais da fonte. Estes itens não podem ser declarados prontos em função dos testes de unitários.

**Próxima fase após testes nativos:** Etapa 03 — **Petalburg e Route 104/Petalburg Woods**, trazendo Wally, Norman, encontro Devon/Aqua, treinadores, itens e flora de encontro. Preservar os sistemas atuais de Decades/Kanto/Johto/Sinnoh.
