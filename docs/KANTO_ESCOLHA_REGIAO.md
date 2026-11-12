# Etapa 04 — Escolha da região inicial no jogo-mestre

**Status:** implementação e teste nativo integrado **aprovados no GitHub Actions**; **a aceitação do menu e da jogabilidade por um jogador continua pendente**.  
**Regras:** [Plano regional v2](PLANO_REGIOES_DESSASTRE_V2.md).  
**Contadores:** etapa de desenvolvimento **04/16 (25%)**; etapas integralmente aceitas **01/16 (6,25%)**.

## O que foi implementado

- O plugin [RegionStart.rb](../scripts/battle_polish/RegionStart.rb) integra-se ao início de **Nova partida**, depois de o Essentials inicializar os valores de um save novo e antes de criar o mapa inicial. **Continue/Carregar save não é interceptado.**
- O menu lista as dez regiões do circuito e Hisui. Decades conserva seu ponto inicial/introdução original; regiões sem mapas integrados aparecem como **em preparação** e não podem ser selecionadas.
- **Kanto só é selecionável se existir um marcador instalado após validação**, apontando para um mapa real. Nesse caso, o save começa em Pallet Town, com estado de progresso local Kanto e Story Mode/Traditional Starters. Oak, Blue e as primeiras rotas usam os eventos próprios do piloto.
- No piloto isolado `.blue-work/kanto-pilot`, Kanto continua iniciando automaticamente, em saves próprios; no jogo principal, a escolha entre Decades e Kanto é apresentada apenas depois de uma instalação autorizada dos mapas.
- Se Kanto não estiver instalado, a Nova partida segue automaticamente o fluxo Decades; não aparece um menu com destinos impossíveis.
- Nenhum ID dos mapas Decades é sobrescrito; não são alterados `Data/System.rxdata`, `Game.ini`, `mkxp.json` nem os saves existentes.

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

**O que é integrado:** 13 mapas, tilesets/autotiles, personagens adaptados, PBS de encontros/treinadores/metadados/conexões, plugin de eventos de Kanto e marcador de origem. O importador **não copia** `System.rxdata`, `Scripts.rxdata`, `Game.ini`, `mkxp.json`, o executável nem diretórios de saves.

O passo seguinte é abrir **`ABRIR_JOGO.bat`**, que prepara a campanha, e aguardar a compilação nativa do Essentials. A tela **Nova partida** exibirá Decades e Kanto como destinos disponíveis, além das regiões ainda não jogáveis.

## 2. O que testar ao iniciar

- [ ] Com Kanto instalado, selecionar **Nova partida → Decades** e conferir a introdução e o sistema de iniciais originais.
- [ ] Começar uma nova partida Kanto e conferir o surgimento em Pallet Town.
- [ ] Escolher o inicial regional (Bulbasaur, Charmander ou Squirtle), enfrentar Blue e verificar o modo história.
- [ ] Salvar a partida Kanto, sair, carregar e conferir região, posição, Pokémon e itens.
- [ ] Abrir um save **antigo de Decades** e conferir que a região inicial, eventos, PC, Pokédex, dinheiro e missões continuam intactos.
- [ ] Verificar que uma região sem mapas instalados **não pode** ser selecionada.
- [ ] Verificar janela/controles, portas e batalhas reais até Pewter — isso também fecha as pendências manuais das etapas 02 e 03.

## 3. Limites nesta entrega

Kanto ainda é um **piloto Pallet → Pewter**, não uma região completa. A viagem Decades ↔ Kanto, desbloqueio pelas Ligas, regras de HMs locais e depósitos de especiais pertencem às próximas etapas. A tela está preparada para crescer, mas **não inventa** spawns das regiões restantes. O piloto Kanto usa os iniciais tradicionais nesta primeira integração; modos de iniciais alternativos exigem adaptação adicional ao roteiro original.

A instalação no seu PC é **opt-in**. O GitHub Actions instala e testa numa **cópia Windows descartável**, não altera os arquivos `game/` no seu computador nem distribui automaticamente conteúdo de terceiros. A [execução 43132795847 do GitHub Actions](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43132795847) comprovou que o jogo integrado iniciou na Pallet Town, preservou o ponto original Decades em `System.rxdata` e salvou/recarregou o estado de Kanto. A seleção foi automatizada no teste para não exigir clique; a interface visível, eventos Decades e a jornada até Brock ainda precisam de teste manual.

**Etapa 04 não pode ser marcada como totalmente concluída antes de validar visualmente o menu e salvar/recarregar as duas origens no Windows.**
