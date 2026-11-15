# Etapa 04 — Escolha da região inicial no jogo-mestre

**Status atualizado:** a seleção `Novo Jogo → Kanto` e as verificações de integração foram implementadas na `main`. O resultado dos novos testes automatizados e a aceitação do fluxo completo no **Game.exe principal** ainda precisam ser confirmados. As evidências de CI descritas abaixo são históricas e não substituem a nova campanha de 142 mapas.  
**Regras:** [Plano regional v2](PLANO_REGIOES_DESSASTRE_V2.md).  
**Contadores:** etapa de desenvolvimento **04/16 (25%)**; etapas integralmente aceitas **01/16 (6,25%)**.

## Como começar

No **Game.exe principal**, escolha **Novo Jogo → Kanto** antes de iniciar a campanha. Quando os 142 mapas e recursos atuais estiverem integrados, o jogo começa no quarto da casa de Pallet **com o mesmo sistema de saves do Decades**. Caso não estejam, aparece **Kanto (instalação necessária)** e a seleção não abre o piloto separado automaticamente. O Modo Batalha original continua disponível pelo fluxo de Decades. O arquivo [KANTO_INTEGRACAO_DECADES.md](KANTO_INTEGRACAO_DECADES.md) documenta o procedimento atual e seus bloqueios.

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

O passo seguinte é abrir **`ABRIR_JOGO.bat`**, que prepara a campanha, integra o catálogo de traduções Kanto sem sobrescrever traduções Decades e solicita compilação do Essentials. Na **tela principal → Novo Jogo**, escolha **Decades** ou **Kanto**. O importador antigo de 13/25 mapas é bloqueado; a versão atual exige os **142 mapas e dados auxiliares** e não substitui saves ou MapIDs antigos automaticamente.

## 2. O que testar ao iniciar

- [ ] Com Kanto instalado, selecionar **Novo Jogo → Decades** e conferir a introdução, o sistema de iniciais original e a ausência de um segundo seletor.
- [ ] Começar uma nova partida Kanto e conferir o surgimento em Pallet Town.
- [ ] Escolher o inicial regional (Bulbasaur, Charmander ou Squirtle), enfrentar Gary e verificar o modo história.
- [ ] Salvar a partida Kanto, sair, carregar e conferir região, posição, Pokémon e itens.
- [ ] Abrir um save **antigo de Decades** e conferir que a região inicial, eventos, PC, Pokédex, dinheiro e missões continuam intactos.
- [ ] Conferir que o seletor sinaliza **Kanto (instalação necessária)** quando seus 142 mapas ou arquivos essenciais não estiverem no jogo principal; não criar save ou fallback falso.
- [ ] Verificar janela/controles, portas e batalhas reais até Pewter — isso também fecha as pendências manuais das etapas 02 e 03.

## 3. Limites nesta entrega

Kanto continua em versão experimental. A validação visual do seletor, das cenas de Pallet e da jornada permanece no roteiro manual.

A instalação no seu PC é **opt-in**. O GitHub Actions instala e testa numa **cópia Windows descartável**, não altera os arquivos `game/` no seu computador nem distribui automaticamente conteúdo de terceiros. A [execução 43132795847 do GitHub Actions](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43132795847) comprovou que o jogo integrado iniciou na Pallet Town, preservou o ponto original Decades em `System.rxdata` e salvou/recarregou o estado de Kanto. A seleção foi automatizada no teste para não exigir clique; a interface visível, eventos Decades e a jornada até Brock ainda precisam de teste manual.

**Etapa 04 não pode ser marcada como totalmente concluída antes de validar visualmente o menu e salvar/recarregar as duas origens no Windows.**
