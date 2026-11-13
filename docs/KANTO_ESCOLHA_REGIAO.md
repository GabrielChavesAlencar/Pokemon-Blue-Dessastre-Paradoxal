# Etapa 04 — Escolha da região inicial no jogo-mestre

**Status:** implementação e teste nativo integrado **aprovados no GitHub Actions**; **a aceitação do menu e da jogabilidade por um jogador continua pendente**.  
**Regras:** [Plano regional v2](PLANO_REGIOES_DESSASTRE_V2.md).  
**Contadores:** etapa de desenvolvimento **04/16 (25%)**; etapas integralmente aceitas **01/16 (6,25%)**.

## Como começar

No jogo principal, abra **Nova partida**, escolha o personagem e o nome, e selecione **Modo História**. O seletor mostra **Decades** e as regiões instaladas. Com Kanto integrado, selecione **Kanto** para começar no quarto da casa de Pallet. O Modo Batalha mantém seu fluxo próprio.

O piloto isolado começa em Kanto. A seleção de personagem e nome abre na primeira partida, antes de o jogador controlar o personagem. Na primeira descida da escada, a mãe se aproxima. Ao tentar sair de Pallet sem inicial, Oak vem buscar o jogador e o conduz ao laboratório. Gary desafia o jogador na porta do laboratório após a escolha do inicial.

## 1. Preparar a instalação principal

Feche o jogo e atualize a branch `main`. Confirme `game/Game.exe` preparado, e a fonte editável FRLG 1.1 autorizada em:

```text
.blue-work/frlg-source/Essentials FRLG/Data/MapInfos.rxdata
```

A fonte, hashes, autoria e créditos estão em [Circuito Regional](CIRCUITO_REGIONAL.md). Este repositório não inclui executáveis, mapas, tilesets ou músicas de terceiros.

Para instalar, execute:

**`KANTO_INSTALAR_NO_JOGO.bat`**

O BAT mostra uma prévia da operação, pede confirmação e executa o importador [install_kanto.py](../scripts/regions/install_kanto.py). Alternativamente:

```powershell
python scripts/regions/install_kanto.py
python scripts/regions/install_kanto.py --apply
```

O primeiro comando é um **dry-run** e não modifica a instalação. O segundo aplica os arquivos após auditoria, com cópias de segurança em `.blue-backups/kanto-...` e rollback em erro de gravação. Se o piloto estiver desatualizado, uma nova cópia é preparada sem eliminar a anterior. A segunda execução não duplica mapas.

**O que é integrado:** 142 mapas, tilesets/autotiles, personagens adaptados, PBS de encontros/treinadores/metadados/conexões, plugin de eventos de Kanto e marcador de origem. O importador **não copia** `System.rxdata`, `Scripts.rxdata`, `Game.ini`, `mkxp.json`, o executável nem diretórios de saves.

O passo seguinte é abrir **`ABRIR_JOGO.bat`**, que prepara a campanha, e aguardar a compilação nativa do Essentials. Em **Nova partida → Modo História**, escolha **Decades** ou **Kanto**.

## 2. O que testar ao iniciar

- [ ] Com Kanto instalado, selecionar **Nova partida → Modo História → Decades** e conferir a introdução e o sistema de iniciais originais.
- [ ] Começar uma nova partida Kanto e conferir o surgimento em Pallet Town.
- [ ] Escolher o inicial regional (Bulbasaur, Charmander ou Squirtle), enfrentar Gary e verificar o modo história.
- [ ] Salvar a partida Kanto, sair, carregar e conferir região, posição, Pokémon e itens.
- [ ] Abrir um save **antigo de Decades** e conferir que a região inicial, eventos, PC, Pokédex, dinheiro e missões continuam intactos.
- [ ] Conferir que o seletor lista somente as regiões instaladas.
- [ ] Verificar janela/controles, portas e batalhas reais até Pewter — isso também fecha as pendências manuais das etapas 02 e 03.

## 3. Limites nesta entrega

Kanto continua em versão experimental. A validação visual do seletor, das cenas de Pallet e da jornada permanece no roteiro manual.

A instalação no seu PC é **opt-in**. O GitHub Actions instala e testa numa **cópia Windows descartável**, não altera os arquivos `game/` no seu computador nem distribui automaticamente conteúdo de terceiros. A [execução 43132795847 do GitHub Actions](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43132795847) comprovou que o jogo integrado iniciou na Pallet Town, preservou o ponto original Decades em `System.rxdata` e salvou/recarregou o estado de Kanto. A seleção foi automatizada no teste para não exigir clique; a interface visível, eventos Decades e a jornada até Brock ainda precisam de teste manual.

**Etapa 04 não pode ser marcada como totalmente concluída antes de validar visualmente o menu e salvar/recarregar as duas origens no Windows.**
