# Kanto — jogar e testar fases 07 a 11 no Windows (experimental)

**Status atual:** piloto **isolado** com 109 mapas: 40 previamente integrados, 8 interiores adicionais, **3 mapas funcionais em Celadon**, **5 em Fuchsia**, 8 prévias restantes de Celadon, 15 prévias de Fuchsia/Safari e 30 prévias de Saffron/Silph. **53 mapas seguem sem eventos**. A engine foi testada com vitórias/derrotas simuladas; controles, caminho e batalhas reais ainda precisam ser testados por você.

**Progresso:** [9/16 núcleos com CI — faltam 7; 1/16 aceito integralmente — faltam 15](KANTO_AVANCO_FUNCIONAL_09.md). [CI nativa de Koga 43231117254](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43231117254) e [regressão 43232052342](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43232052342) aprovadas.

## Atualização de 12/11/2026 — núcleo 16

O piloto agora tem **142 mapas**, **45 prévias apenas de cenário**, **144 perfis de treinadores no portal**, **22 áreas com encontros auditados** e **64 destinos de teletransporte experimental**. Os números de 109 mapas/53 prévias e 17 ou 41 atalhos encontrados nas seções históricas abaixo são registros das fases anteriores, não da versão atual.

**Depois de jogar pelo terceiro botão “Testar Kanto”**, o BAT de teste solicita a **seção que você realmente testou**: início, ginásios, Liga, integração/viagem/PC ou JoiPlay. Marque somente S = passou de verdade, F = falhou, N = não testado. O relatório local fica em `.blue-work/kanto-gui-reports/` em Markdown **e JSON**, sem enviar saves ao GitHub. **Nenhum status do relatório aprova automaticamente a etapa 02 nem a etapa 16.** Consulte [fase 16 — preparação do aceite](KANTO_FASE_16.md) e [roteiro atualizado](KANTO_ETAPAS.md).

## Opção diretamente no Game.exe principal

Se você baixou **`Blue-Story.exe`** pelo [site oficial do projeto](https://pokemondessastreparadosal.vercel.app/downloads), **basta abrir o mesmo EXE novamente**: ele busca a revisão atual da `main`, atualiza os plugins, prepara o jogo e abre `game/Game.exe` na pasta de instalação (normalmente `%LOCALAPPDATA%/PokemonBlueDessastreParadoxal`). Você não precisa instalar Python, Git ou mexer no repositório manualmente. Na tela dos saves do jogo aberto aparecerá:

1. **Continuar** (ou o nome do slot de save, se o plugin Auto Multi Save estiver ativo);
2. **Novo Jogo**;
3. **Testar Kanto**;
4. As opções anteriores, como Mystery Gift, Opções e Sair (sem perder funcionalidades).

Ao escolher **Testar Kanto**, o jogo pede confirmação, abre automaticamente o piloto experimental pelo lançador do próprio repositório e **fecha o menu do EXE principal**. O piloto abre em outra janela/processo com um perfil de saves separado: nenhuma rotina de instalação escreve no save original de Decades. O botão reaproveita `KANTO_JOGAR_EXPERIMENTAL.bat`, mas **você não precisa executar esse arquivo manualmente**.

**Pré-requisitos:** a instalação deve estar completa e conectada à internet na primeira execução do teste. O menu usa o `KANTO_JOGAR_EXPERIMENTAL.bat` e `scripts/regions/pilot.py` que o próprio `Blue-Story.exe` atualiza; o BAT encontra **primeiro o Python portátil já instalado pelo Blue**, mesmo que o nome da pasta do Windows contenha espaços. O [preparador da fonte](../scripts/regions/ensure_source.py) baixa o arquivo original FRLG fixado no manifesto, confere o SHA-256 e extrai **somente mapas, PBS e gráficos necessários** para `.blue-work/frlg-source/`. Se a fonte já existir, ela não é sobrescrita. O download depende de o servidor original estar acessível; falhas geram mensagem no console do teste, sem modificar saves. O botão não aparece dentro do próprio piloto, para impedir abertura em cadeia.

Se estiver usando uma instalação **manual** sem `Blue-Story.exe`, instale/prepare o Blue e mantenha os arquivos do projeto na pasta acima de `game/`; Python 3.10+ e o `tar` do Windows precisam estar acessíveis caso a instalação não tenha as ferramentas portáteis.

**Importante:** o botão fica **dentro do EXE principal**, mas por segurança a jogabilidade experimental ocorre na cópia isolada de Kanto. Não foram incorporados arquivos de mapas/terceiros ao binário `Game.exe`, e isso **não é uma fusão de saves**. A terceira posição é exibida quando há um save e, portanto, a opção Continuar; sem save, Novo Jogo vem em primeiro e Testar Kanto em segundo.

## 1. Abrir com um clique

1. Feche a instalação principal, atualize a `main` e confira que `game/Game.exe` foi preparado com `INSTALAR_JOGO.bat` ou o fluxo de instalação existente.
2. Na primeira abertura, se a fonte Essentials FRLG 1.1 ainda não existir, o BAT tenta prepará-la automaticamente com verificação de SHA-256. Se o site de origem estiver indisponível, consulte [Circuito Regional](CIRCUITO_REGIONAL.md) para obtenção manual. O repositório não redistribui os mapas.
3. **Pelo EXE baixado no site, prefira clicar em Testar Kanto dentro do próprio menu do jogo.** Alternativamente, na raiz do projeto, execute `KANTO_JOGAR_EXPERIMENTAL.bat`. Ambos preparam uma cópia isolada do piloto e abrem o `Game.exe` dessa cópia. **Não alteram saves normais de Decades.**
4. No jogo, escolha **Nova partida** e fale com Oak para pegar um inicial. Salve em um **slot de testes**; não sobrescreva outras partidas do piloto.
5. Feche o jogo normalmente quando quiser encerrar. O BAT pede que você avalie o checklist (S passou / F falhou / N não testado) e salva um MD no seu computador.

**Para forçar uma nova cópia e preservar a anterior**, execute pelo terminal do Windows:

```bat
KANTO_JOGAR_EXPERIMENTAL.bat --rebuild
```

O perfil de saves **Kanto Piloto** pode ser compartilhado pelas cópias do piloto; prefira um slot diferente e crie uma nova partida de teste quando a versão dos mapas mudar.

## 2. Menu de teletransporte exclusivo do piloto

Após escolher o inicial com Oak, abra o **menu de pausa → Testes Kanto (experimental)**. Confirme o destino para visitar os trechos das fases 07 e 08 sem precisar repetir toda a campanha anterior.

Os **17 atalhos antigos** são: Pallet, Pewter, Rota 4, Centro e três andares de Mt. Moon, Cerulean, Misty, Rota 5, Rota 6, Vermilion, Lt. Surge, porto, S.S. Anne 1F, cabine do capitão e convés. O acesso à **Rota 3** é caminhando para leste a partir de Pewter; assim você também poderá testar os treinadores e as conexões originais.

**Importante:** o menu usa somente mapas da cópia experimental e **não libera Liga, não concede insígnias, não altera a campanha principal e não existe no jogo Decades instalado**. Os pontos de chegada foram derivados de entradas/saídas da fonte FRLG, mas ainda precisam de validação visual de colisão no Windows.

## Passo funcional 07/16 — pacote de Oak e portas (etapa 03)

Após [CI Windows aprovada](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43222828441), teste no `Game.exe → Testar Kanto` usando save próprio:

- [ ] Inicie uma nova jornada, escolha um dos três iniciais e entre no Poké Mart de Viridian; o atendente deve entregar o **pacote virtual** de Oak e continuar vendendo.
- [ ] Volte ao laboratório em Pallet e fale com Oak no mesmo evento do inicial para registrar a entrega; confira a Pokédex.
- [ ] Converse com Oak novamente: não deve receber novo inicial, pacote ou outra recompensa.
- [ ] Retorne ao Mart: loja normal sem nova missão; salve, feche e recarregue para conferir as flags.
- [ ] Verifique os **dois acessos do Museu de Pewter** e os **três acessos verificados da portaria da Rota 2**, além das casas. Todos precisam permitir retorno.
- [ ] Teste um treinador por visão, uma derrota e uma vitória, sem repetir prêmio ou perder progresso.

**Atenção:** o pacote é um registro do save Kanto, não um item físico da Bolsa. As cinco Poké Bolas dadas na seleção do inicial foram preservadas por compatibilidade. A conclusão deste checklist manual ainda é necessária para a Barra 2.

## Correção funcional MAN-01/MAN-02 — teste prioritário

[Checklist exato dos 8 interiores e 50 treinadores Sight(n)](KANTO_CORRECOES_FUNCIONAIS_MAN01_MAN02.md). A CI inspeciona o estado de eventos na engine, mas o teste de controles e colisões precisa ocorrer no Windows com **Testar Kanto**.

- [ ] Pallet: casa do rival e retorno.
- [ ] Viridian: duas casas, entrada e saída.
- [ ] Rota 2: portaria secreta e casa escondida, retorno ao caminho.
- [ ] Pewter: Museu e duas casas, retorno pela porta real.
- [ ] Viridian Forest: Rick avista o jogador a 5 casas (quando direção e obstáculos permitem), sem pressionar ação; combate iniciado.
- [ ] Após derrota: lutar novamente é permitido. Após vitória: Rick não repete batalha ao passar na visão.
- [ ] Salvar, recarregar e testar novamente; flag de vitória e estado da página 2 preservados.

**Não testar ainda como completas:** Viridian Gym/Giovanni, Diglett's Cave profunda, NPCs/diálogos dos novos interiores e as 61 prévias de cenário. Não marcar etapas 02/03/07 como totalmente aprovadas sem validar o percurso.

## Teste manual relatado em 12/11/2026

[Registro e análise do TXT enviado](KANTO_FEEDBACK_TESTES_MANUAIS_2026-11-12.md): o jogador visitou **Pallet Town, Rota 1, Rota 2, Viridian City, Viridian Forest, Pewter City, lado esquerdo da Rota 4 e Mt. Moon**.

**Observações pendentes detectadas pelo jogador:**

- [ ] Verificar cada porta de residência, laboratório, Centro Pokémon, Poké Mart e demais estabelecimentos: entrada real no interior e retorno, sem falha de warp.
- [ ] Aproximar-se dos treinadores e verificar se o evento de batalha inicia automaticamente quando previsto na fonte; não permitir ultrapassar encontros obrigatórios antes da batalha.
- [ ] Exibir painel das oito insígnias de Kanto e painel de insígnias/conquistas de todas as regiões.
- [ ] Repetir os testes nos mapas visitados depois das correções e registrar resultado *por mapa e evento*.

A lista de visitação **não comprova** aprovação manual dos testes de combate, colisão, portas, save/reload ou todos os andares de Mt. Moon; o progresso de aceite permanece **1/16**.

## Fase 09 — núcleo funcional Erika/Celadon (8º avanço)

[Documentação e checklist da nova integração](KANTO_AVANCO_FUNCIONAL_08.md). Os **109 mapas** incluem três cenários de Celadon com eventos autorais limitados: **City (114)** com portas do ginásio e Centro Pokémon; **Center (115)** com cura e retorno; **Gym (124)** com Erika, sete treinadoras `Sight(n)`, Rainbow Badge e saída. Permanecem **58 mapas somente cenário**, incluindo Rota 7, loja Celadon, Fuchsia e Saffron. O menu de pausa mantém **41 atalhos experimentais**, inclusive os cinco de Celadon.

- [ ] Entrar na cidade, atravessar **a porta do ginásio e a do Centro** caminhando e voltar por cada saída.
- [ ] Curar a equipe em Celadon, confirmar gráficos e ponto de retorno.
- [ ] Testar batalhas com as **sete treinadoras** por linha de visão e suas equipes.
- [ ] Perder para Erika: **não** receber Rainbow nem guardar vitória.
- [ ] Vencer Erika: receber Rainbow **uma vez**; testar conversa pós-vitória e save/reload.
- [ ] Confirmar que loja Celadon, Game Corner, Rocket Hideout e outros eventos ainda estão indisponíveis.
- [ ] Verificar colisão, caminho até a líder, Cut trees, save antigo e posteriormente JoiPlay.

**Nota:** o [relatório original da prévia de cenário](KANTO_FASE_09.md) é histórico. O novo núcleo de gameplay possui [CI Windows aprovada](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43227499299), mas **não** tem QA manual concluído.


## Fase 11 — Saffron City, Sabrina e Silph Co. (prévia sem eventos)

Os [30 novos cenários](KANTO_FASE_11.md) incluem Saffron e portarias, Rota 8, Dojo, Fan Club, ginásio de Sabrina e os 11 andares da Silph Co. (**101 mapas no total; 61 somente cenário**). Foram acrescentados dez atalhos de acesso pelo menu de pausa de Testar Kanto: Rota 8, portaria oeste, Saffron City, ginásio Sabrina, Fighting Dojo, Centro Pokémon, Silph Co. 1F/5F/11F e elevador (41 atalhos no total).

**Nesta prévia os novos cenários não contêm NPCs, Rocket, batalhas, teletransportadores, elevador funcional, Card Key, Marsh Badge, lojas ou eventos de porta.** Os atalhos servem apenas para inspecionar terrenos e coordenadas sem tocar no save Decades. Não relatar como aprovado o que não foi testado no Windows interativo.

- [ ] Conferir visual/tileset de Saffron City, Rota 8, ginásio Sabrina, Dojo e Silph Co.
- [ ] Conferir pontas dos corredores, colisões e posições dos dez destinos; nenhum deles concede itens ou insígnias.
- [ ] Confirmar que a instalação e os saves de Decades permanecem sem alterações.
- [ ] Registrar visualmente a passabilidade dos andares da Silph e os limites de seus teletransportadores (ainda inativos).
- [ ] Adiar os eventos até revisão específica e testar cada um por ida/volta, batalha, reload e derrota.

## Fase 10 — Fuchsia/Koga jogáveis; Safari ainda não habilitada

[Documentação e checklist da implementação](KANTO_AVANCO_FUNCIONAL_09.md). O núcleo tem **cinco mapas** ativos em Fuchsia: City (144), Centro (145), Mart (146), Ginásio (147) e portão Safari (153). Os outros **15 mapas da fase 10** são cenários sem eventos. O piloto oferece **42 atalhos** de teste, incluindo um novo para o Poké Mart de Fuchsia.

- [ ] No `Game.exe → Testar Kanto`, iniciar no save isolado e viajar para **Fuchsia City** pelo menu experimental.
- [ ] Caminhar pelas quatro entradas da cidade (ginásio, Centro, Mart, Safari Gate) e testar o retorno por cada saída.
- [ ] Conversar com enfermeira, curar equipe e verificar compras no Mart; confirmar sprites/colisões.
- [ ] Enfrentar seis treinadores por aproximação (`Sight(n)`), testar derrota, vitória, self-switch e repetição sem novo combate.
- [ ] **Koga:** perder uma vez sem Soul Badge; vencer com equipe FRLG (Koffing 37, Muk 39, Koffing 37, Weezing 43), obter Soul **somente uma vez**, salvar/recarregar.
- [ ] **Portão Safari:** falar com o atendente e o guia; confirmar que não há cobrança, Safari Balls, captura ou acesso à área antes da implementação da sessão nativa completa.
- [ ] Usar atalhos para inspecionar Safari Sul/Norte/Oeste, Warden e Rota 15 somente como cenários; não contar como progresso de história.
- [ ] Não alterar saves nem arquivos da instalação principal Decades; depois testar Android/JoiPlay.

**Pendências explícitas:** sistemas de Safari Balls, encontros, passos/tempo, ingresso e restauração; Gold Teeth/Strength, Secret House/Surf, conexão canônica de rotas e diálogos EN/PT-BR. **Barra 1 9/16; Barra 2 1/16.**

## 3. O que testar nas fases 07 e 08

- [ ] Partida nova em Pallet, Oak e escolha de inicial; saída e retorno de Pewter
- [ ] Rota 3: oito treinadores, batalhas reais, encontros e ligação para Rota 4
- [ ] Rota 4: Centro Pokémon, entrada/saída de Mt. Moon, caminho para Cerulean
- [ ] Mt. Moon: 1F, B1F e B2F, escadas nos dois sentidos, Pokémon selvagens e Rockets
- [ ] Recompensa Moon Stone: retirada apenas uma vez no evento de teste
- [ ] Cerulean: mapa, Centro Pokémon, Poké Mart e ginásio
- [ ] Misty: batalhas reais com Luis e Diana, equipe Staryu/Starmie e vitória/derrota
- [ ] Cascade Badge: concedida uma única vez, registrada separadamente da Boulder e contada corretamente no balanceamento
- [ ] Save/reload: equipe, Box, mapa, dinheiro, inventário, vitórias e duas insígnias persistem
- [ ] Rota 5 → passagem subterrânea → Rota 6 → Vermilion, com retorno sem teleportes
- [ ] Vermilion: Centro Pokémon, Poké Mart, bloqueio do porto e acesso após obter a Cascade
- [ ] S.S. Anne: embarque, desembarque, cabines, 1F, 2F, B1F, convés e capitão
- [ ] Capitão: receber HM Cut apenas uma vez, ou registrar a ausência do item na versão Decades
- [ ] Ginásio de Lt. Surge: 15 lixeiras, duas chaves adjacentes, travas e reset ao errar
- [ ] Surge: time FRLG com Voltorb 21, Pikachu 18 e Raichu 24
- [ ] Thunder Badge: obtenção única; permissões de Fly e evolução do balanceamento
- [ ] S.S. Ticket experimental persistido por save; não depender de item ausente no Decades
- [ ] Instalação original Decades e saves preexistentes continuam intactos

**Limitação:** ainda não foram adaptados todos os scripts complexos da história original (fósseis, cutscenes e NPCs secundários). A passagem de navio é experimental; a visita canônica a Bill e a saída cinematográfica do S.S. Anne continuam pendentes. Os eventos novos importam apenas batalhas, saídas, centros, marts e um item auditado. Não confunda a presença dos mapas com a conclusão integral da campanha de Kanto.

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
