# Circuito regional do Dessastre Paradoxal

> **Regra atual de transporte (15/11/2026):** viagem livre desde o início exclusivamente por NPC na cidade inicial de cada região integrada, sem precisar vencer a Liga. O restante da documentação histórica de desbloqueio por vizinhos foi substituído por [VIAGEM_REGIONAL_LIVRE_NPC.md](VIAGEM_REGIONAL_LIVRE_NPC.md).

Decades continua sendo a campanha jogável. O circuito de dez Ligas e a
expedição de Hisui estão cadastrados no mesmo catálogo usado pelo jogo,
Blue Studio e portal. O painel de pausa mostra a progressão; não teleporta
o jogador para mapas que ainda não foram validados.

## 0. Auditoria de Decades

- A instalação auditada tem 207 mapas, de ID 1 a 275. A engine lê
  `Map%03d.rxdata`, mas há ferramentas do projeto que enumeram nomes com
  três algarismos. Por isso o piloto limita IDs a 999, sem assumir que
  esse é o limite da engine. Não reutiliza IDs baixos de mapas antigos.
- Zenith Domain: mapa 136, evento 2. Quatro variantes da batalha de
  Danny. A derrota encerra o evento antes da Esmeralda Stellar (badge
  18); o switch 122 só liga após `pbHallOfFameEntry`. Ambos os sinais
  são necessários, e a leitura é habilitada para o mapa de hash auditado.
- Os primeiros oito marcos nativos são as esmeraldas dos mapas 80,
  196, 195, 213, 214, 198, 217 e 216. São exibidos a partir das flags
  originais. Não recriamos nem recontamos nenhum desses prêmios.

## 1. Regras regionais

A conclusão da Liga registra progresso e pós-jogo, mas não libera nem bloqueia a viagem. Hisui não conta como
Liga e tem saídas próprias quando escolhido como origem. O pós-jogo
mundial depende das dez Ligas; o núcleo só seleciona uma revanche quando
já houver um perfil verificado.

O núcleo distingue conquistas locais do total global e prevê acesso de
campo por insígnia, item e evento. Para a viagem com especiais, calcula
quais Pokémon e slots seriam usados, recusando Box cheia ou equipe sem
Pokémon utilizável. Esta versão não ativa essas regras no PC, batalha ou
mapas de Decades. O catálogo de espécies especiais, eventos de viagem,
equipes definitivas e integração de depósitos ainda exigem validação na
engine. Saves existentes são lidos sem gravação automática.

## 2. Fonte e inspeção de Kanto

Usar o [Essentials FRLG 21.1 / 1.1](https://eeveeexpo.com/resources/1797/),
de TheTinfoilTemplar, que permite a reutilização dos mapas e eventos do kit.
Créditos à equipe do Pokémon Essentials (Poccil, Maruno e colaboradores)
e a TheTinfoilTemplar pelos mapas e eventos. A fonte usa a mesma versão do
Essentials que o Blue e já oferece tabelas mescladas de FireRed/LeafGreen.
O estudo também aponta o [Fire Ash](https://eeveeexpo.com/threads/9489/)
como referência de cobertura; seu roteiro segue o anime e a engine
indicada pelo autor é v19.1, por isso não é a base do piloto.

A cópia local do pacote FRLG foi conferida pelo SHA-256 registrado em
`data/regions/kanto-source.json`. O projeto não inclui o pacote, músicas,
scripts, binários nem gráficos da fonte no Git. Não se executa o Game.exe
da fonte. A leitura do Marshal é feita como dados, sem executar código.

```powershell
python scripts/regions/audit.py --source '.blue-work/frlg-source/Essentials FRLG' --output .blue-work/kanto-audit.json
python scripts/regions/stage.py --source '.blue-work/frlg-source/Essentials FRLG' --output .blue-work/kanto-preview
```

Use um nome de saída novo se a prévia já existir. Os 13 mapas abrangem
Pallet, laboratório, Rota 1, Viridian, Rota 2, floresta e Pewter. A prévia
contém o terreno e tilesets remapeados, o plano com conflitos e conexões
propostas e rascunhos locais de cinco tabelas de encontros e dez perfis
de treinadores (incluindo três variações do rival e Brock). Os pesos
totalizam 100 por método; espécies e golpes são conferidos no PBS Blue.
Os rascunhos mantêm a fonte FRLG, ainda a comparar com as versões oficiais.
O comando escreve numa pasta temporária e só publica a pasta de prévia
depois da validação. Não altere o jogo com essa pasta: a geometria não
contém eventos ativos nem substitui a campanha.

## 3. Próximos marcos

1. Adaptar a introdução, escolha dos iniciais, rival, NPCs e Brock; remapear
   switches, variáveis, portas, transfers, pontos de cura e mapa regional.
2. Provar, em uma cópia e save de teste, a jornada Pallet → Pewter:
   encontro, duas batalhas, Boulder Badge, salvar/reabrir e retorno a
   Decades. Validar no Windows e no Android antes de abrir o destino.
3. Completar Kanto e sua Liga. Somente então usar o piloto validado como
   modelo para Johto, Hoenn, Sinnoh, Unova, Kalos, Alola, Galar e Paldea.
   Hisui recebe um arco separado. Paldea e Hisui ainda precisam de base
   editável ou de mapas 2D próprios.
4. Quando houver dados reais no jogo, exportar encontros, treinadores e
   localizações por região para Pokédex, Habitat Dex, álbum e portal.
   Publicar revanches oficiais com as fontes e sem inventar equipes.

## Piloto de Kanto em uma cópia local

Na pasta do Blue, execute:

~~~powershell
python scripts/regions/pilot.py --launch
~~~

A primeira execução monta a cópia em .blue-work/kanto-pilot com a
instalação do Blue e a fonte Essentials FRLG 1.1 extraída em
.blue-work/frlg-source/Essentials FRLG. Para outro caminho da fonte,
informe --source. O executável também pode ser aberto diretamente na
pasta do piloto. Os saves usam o perfil Kanto Piloto, dentro de
Dessastre Paradoxal Kanto Testes.

Comece uma partida e entre no laboratório de Oak em Pallet Town.
Fale com Oak para escolher o inicial e com Blue para a primeira batalha.
Explore a Rota 1 e Viridian, atravesse a floresta e desafie Brock em
Pewter. As fichas do portal usam os níveis base do PBS do piloto.
A Boulder Badge conta como conquista local nesse save.

O catálogo público é gerado com python scripts/regions/export_kanto.py
a partir dos mesmos rascunhos de encontros e equipes usados na cópia.
A verificação nativa compila a cópia, carrega Pallet e o laboratório,
confere encontros e equipes e verifica save e recarga. A verificação
automatiza a escolha do inicial e fornece os resultados das batalhas.


## 4. Integrar Kanto ao jogo principal (fluxo atual em 15/11/2026)

O seletor da **tela inicial → Novo Jogo** oferece **Decades** e **Kanto**. Diferentemente do piloto de teste, Kanto agora pode começar **no mesmo Game.exe e na mesma estrutura de saves/PC** quando o pacote atual tiver sido integrado localmente à instalação Decades. A escolha é armazenada apenas durante a criação do novo jogo; iniciar Decades mantém o spawn e história nativos e não repete o seletor no Story Mode.

**Instalação:** `KANTO_INSTALAR_NO_JOGO.bat` prepara e audita a fonte FRLG fixada, apresenta um dry-run, exige confirmação, instala os **142 mapas catalogados**, PBS, tilesets, NPCs, dependências de eventos e overlay de traduções no `game/` local. `ABRIR_JOGO.bat` atualiza plugins/idioma e solicita compilação dos arquivos Essentials. Não copia executáveis, `System.rxdata`, scripts da fonte nem saves. A verificação `python scripts/regions/install_kanto.py --verify-installed` confirma integridade de arquivos, **não** gameplay.

O código de início guarda o ponto nativo de Decades como chegada segura de quem começa em Kanto. **Sem precisar vencer a Liga**, o jogador pode viajar entre **Kanto (NPC em Pallet Town)** e **Decades (NPC em Cherryhill City)** na mesma partida. Johto terá o NPC em **New Bark Town** quando for integrada e validada no jogo principal; o piloto independente ainda não é destino compartilhado. O menu regional é apenas informativo e o transporte exige falar pessoalmente com o NPC da cidade inicial. As regras de insígnias/esmeraldas, HMs, especiais, proteção da Box e motor de batalha Blue permanecem as do [Plano v2](PLANO_REGIOES_DESSASTRE_V2.md).

**Migração:** instalações antigas com só 13/25 mapas são recusadas pelo verificador; não apagar marcadores ou copiar arquivos do piloto sobre `game/` para contornar bloqueios, pois MapIDs e saves podem divergir. Preserve a instalação e use nova cópia de teste até existir um migrador comprovado.

**Status real:** infraestrutura publicada no GitHub, mas o teste ponta a ponta em `Game.exe` principal e JoiPlay ainda precisa ser comprovado. O projeto tem mapas `preview_only`; a barra de aceitação de Kanto não deve subir por mera presença de arquivos ou sucesso em CI.

Passo a passo e testes: [KANTO_INTEGRACAO_DECADES.md](KANTO_INTEGRACAO_DECADES.md).

## 5. Expansão experimental Pallet → Mt. Moon → Cerulean (fase 07)

A primeira versão do piloto tinha **13 mapas até Brock**; a fase 07 adicionou **12 mapas** (Rota 3, Rota 4, Mt. Moon 1F/B1F/B2F, Cerulean e seus serviços), totalizando **25 mapas auditados**, com Misty e Cascade Badge. [Detalhes da implementação e das limitações](KANTO_FASE_07.md).

Para experimentar agora sem tocar na campanha principal, execute **`KANTO_JOGAR_EXPERIMENTAL.bat`**, inicie uma nova partida na cópia isolada e abra **Testes Kanto (experimental)** no menu de pausa. Esse menu permite visitar pontos da nova região sem avançar artificialmente a história. Ao fechar, o script cria um relatório local de observações. [Passo a passo completo](KANTO_TESTE_EXPERIMENTAL.md).

**Instalações do jogo principal que já têm apenas os 13 mapas anteriores não são atualizadas automaticamente** para 25: é necessário um procedimento de migração auditado para evitar que saves antigos apontem para mapas errados. O piloto novo mantém os IDs dos 13 mapas anteriores e adiciona os demais em slots distintos; o teste de compatibilidade visual e a migração incremental permanecem pendentes.
