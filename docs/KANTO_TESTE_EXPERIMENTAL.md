# Kanto — jogar e testar a fase 07 no Windows (experimental)

**Status:** disponível como **cópia isolada**, com 25 mapas de Pallet a Cerulean. A CI valida mapas, NPCs, equipes, Misty e salvamento com resultados de batalha simulados. **A jogabilidade interativa ainda depende do seu teste.**

## Opção diretamente no Game.exe principal

Depois de atualizar a `main` e executar a preparação/instalação do Blue para recompilar os plugins, abra **`game/Game.exe`** pela forma habitual. A tela onde ficam os saves terá:

1. **Continuar** (ou o nome do slot de save, se o plugin Auto Multi Save estiver ativo);
2. **Novo Jogo**;
3. **Testar Kanto**;
4. As opções anteriores, como Mystery Gift, Opções e Sair (sem perder funcionalidades).

Ao escolher **Testar Kanto**, o jogo pede confirmação, abre automaticamente o piloto experimental pelo lançador do próprio repositório e **fecha o menu do EXE principal**. O piloto abre em outra janela/processo com um perfil de saves separado: nenhuma rotina de instalação escreve no save original de Decades. O botão reaproveita `KANTO_JOGAR_EXPERIMENTAL.bat`, mas **você não precisa executar esse arquivo manualmente**.

**Pré-requisitos:** execute o Game.exe da pasta `game/` dentro de uma cópia completa do repositório. `KANTO_JOGAR_EXPERIMENTAL.bat` e `scripts/regions/pilot.py` devem estar na pasta anterior; para preparar uma nova cópia do piloto são necessários Python 3.10+, a instalação Blue e a fonte FRLG local descritos abaixo. Se faltar algum item, o EXE mostra uma mensagem e mantém o menu da campanha disponível. A opção não aparece dentro do próprio piloto, para impedir abertura em cadeia.

**Importante:** o botão fica **dentro do EXE principal**, mas por segurança a jogabilidade experimental ocorre na cópia isolada de Kanto. Não foram incorporados arquivos de mapas/terceiros ao binário `Game.exe`, e isso **não é uma fusão de saves**. A terceira posição é exibida quando há um save e, portanto, a opção Continuar; sem save, Novo Jogo vem em primeiro e Testar Kanto em segundo.

## 1. Abrir com um clique

1. Feche a instalação principal, atualize a `main` e confira que `game/Game.exe` foi preparado com `INSTALAR_JOGO.bat` ou o fluxo de instalação existente.
2. A fonte editável Essentials FRLG 1.1 precisa existir em `.blue-work/frlg-source/Essentials FRLG`, conforme [Circuito Regional](CIRCUITO_REGIONAL.md). Ela não é incluída neste repositório.
3. Na raiz do projeto, abra **`KANTO_JOGAR_EXPERIMENTAL.bat`**. O script prepara uma cópia nova do piloto se necessário e abre o `Game.exe` dessa cópia. **Não usa nem modifica o executável nem os saves normais de Decades.**
4. No jogo, escolha **Nova partida** e fale com Oak para pegar um inicial. Salve em um **slot de testes**; não sobrescreva outras partidas do piloto.
5. Feche o jogo normalmente quando quiser encerrar. O BAT pede que você avalie o checklist (S passou / F falhou / N não testado) e salva um MD no seu computador.

**Para forçar uma nova cópia e preservar a anterior**, execute pelo terminal do Windows:

```bat
KANTO_JOGAR_EXPERIMENTAL.bat --rebuild
```

O perfil de saves **Kanto Piloto** pode ser compartilhado pelas cópias do piloto; prefira um slot diferente e crie uma nova partida de teste quando a versão dos mapas mudar.

## 2. Menu de teletransporte exclusivo do piloto

Após escolher o inicial com Oak, abra o **menu de pausa → Testes Kanto (experimental)**. Confirme o destino para visitar o trecho da fase 07 sem precisar repetir toda a campanha anterior.

Os atalhos disponíveis são Pallet, Pewter, saída de Mt. Moon na Rota 4, Centro Pokémon de Mt. Moon, Mt. Moon 1F, B1F e B2F, Cerulean City e ginásio de Misty. O acesso à **Rota 3** é caminhando para leste a partir de Pewter; assim você também poderá testar os treinadores e as conexões originais.

**Importante:** o menu usa somente mapas da cópia experimental e **não libera Liga, não concede insígnias, não altera a campanha principal e não existe no jogo Decades instalado**. Os pontos de chegada foram derivados de entradas/saídas da fonte FRLG, mas ainda precisam de validação visual de colisão no Windows.

## 3. O que testar na fase 07

- [ ] Partida nova em Pallet, Oak e escolha de inicial; saída e retorno de Pewter
- [ ] Rota 3: oito treinadores, batalhas reais, encontros e ligação para Rota 4
- [ ] Rota 4: Centro Pokémon, entrada/saída de Mt. Moon, caminho para Cerulean
- [ ] Mt. Moon: 1F, B1F e B2F, escadas nos dois sentidos, Pokémon selvagens e Rockets
- [ ] Recompensa Moon Stone: retirada apenas uma vez no evento de teste
- [ ] Cerulean: mapa, Centro Pokémon, Poké Mart e ginásio
- [ ] Misty: batalhas reais com Luis e Diana, equipe Staryu/Starmie e vitória/derrota
- [ ] Cascade Badge: concedida uma única vez, registrada separadamente da Boulder e contada corretamente no balanceamento
- [ ] Save/reload: equipe, Box, mapa, dinheiro, inventário, vitórias e duas insígnias persistem
- [ ] Instalação original Decades e saves preexistentes continuam intactos

**Limitação:** ainda não foram adaptados todos os scripts complexos da história original (fósseis, cutscenes e NPCs secundários). Os eventos novos importam apenas batalhas, saídas, centros, marts e um item auditado. Não confunda a presença dos mapas com a conclusão integral da campanha de Kanto.

## 4. Se a janela ou os controles falharem

O novo BAT chama o lançador em `--launch-only`, **sem depender da enumeração de janelas Win32**, contornando o `WinError 0` encontrado no diagnóstico do Codex. Isso não injeta comandos de teclado/mouse; você joga normalmente. O resultado ao fechar o processo **não é interpretado como prova de jogabilidade**.

Os logs do motor e o relatório ficam em:

```text
.blue-work/kanto-gui-reports/
  kanto-gui-<data>.json
  kanto-gui-<data>-stdout.txt
  kanto-gui-<data>-stderr.txt
  kanto-experimental-<data>.md
```

Se a abertura falhar, confira `Game.exe`, `Game.ini`, `mkxp.json`, `Data`, `Graphics` e as dependências do jogo **dentro da mesma cópia**. Não remova nem substitua pastas de save para corrigir um erro.

O relatório **não é enviado ao GitHub automaticamente**. Revise caminhos locais ou dados pessoais antes de compartilhá-lo aqui. A fase 07 e as etapas manuais anteriores só serão marcadas como concluídas depois de evidências da jogabilidade real.

[Contador das 16 etapas](KANTO_ETAPAS.md) · [Referência técnica e fonte FRLG](CIRCUITO_REGIONAL.md)
