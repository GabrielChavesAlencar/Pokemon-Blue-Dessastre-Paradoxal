# FireRed → Kanto no Dessastre Paradoxal: diálogos EN/PT-BR, passo a passo

**Criado em:** 12/11/2026  
**Alvo:** [Pokémon Blue: Dessastre Paradoxal](../README.md), campanha **Kanto** em Pokémon Essentials 21.1 (RPG Maker XP / Decades).  
**Tipo:** procedimento de preparação, auditoria e tradução. **Não instala** falas nem eventos no jogo por si só.

> **Limite de conteúdo:** o repositório contém documentação e ferramentas próprias; não inclui o roteiro completo em inglês nem sua tradução integral. Para gerar o inventário fala a fala, o usuário precisa executar o extrator sobre arquivos-fonte locais aos quais tenha acesso autorizado. Não publique saídas integrais do texto de FireRed num repositório público sem os direitos necessários.

## 1. O que foi colocado neste projeto

| Arquivo | Finalidade |
|---|---|
| [Guia_Dialogos_Pokemon_FireRed_EN_PT.md](Guia_Dialogos_Pokemon_FireRed_EN_PT.md) | Guia original, lugares, personagens, estrutura das fontes e critérios de tradução |
| [extrair_traduzir_dialogos_firered.py](../scripts/localization/extrair_traduzir_dialogos_firered.py) | Extrai entradas de texto de uma cópia local da decompilação e gera Markdown EN/PT; tradução Argos opcional |
| [extrair_eventos_firered.py](../scripts/regions/extrair_eventos_firered.py) | Ferramenta já existente para catalogar eventos, warps, flags e referências de scripts |
| [PORTUGUES_E_UI.md](PORTUGUES_E_UI.md) | Sistema já existente de idioma do Decades/Blue, baseado nas mensagens originais do jogo instalado |
| [KANTO_ROADMAP_EVENTOS_FIRERED.md](KANTO_ROADMAP_EVENTOS_FIRERED.md) | Ordem e autorização da adaptação dos eventos em Kanto |

**Diferença essencial:** texto do *FireRed GBA* não é automaticamente uma chave de tradução de *Decades RPG Maker XP*. Os dois catálogos têm fontes, IDs e engines diferentes. Associar eventos e revisar o texto é um trabalho adicional.

## 2. Cuidados antes de começar

1. Feche Game.exe e RPG Maker XP. Faça backup dos saves existentes.
2. Atualize sua cópia de trabalho da branch main sem apagar arquivos locais. Execute os passos abaixo na raiz do repositório Blue.
3. Nunca inclua arquivos de jogo de terceiros, ROM, save, base Decades ou a fonte FireRed no commit. As pastas game/ e .blue-work/ já são ignoradas pelo Git.
4. O piloto Kanto é isolado do jogo principal. Mantenha separados os dados experimentais e os saves normais.
5. A documentação de eventos controla o que pode ser ativado. Mapas marcados preview_only continuam **sem diálogos ou eventos**, até autorização explícita para implementá-los.
6. Registre a revisão exata da fonte e do Blue para conseguir reproduzir resultados.

## 3. Passo A — preparar a referência FireRed local

Pré-requisitos: **Windows 10/11, Python 3.10+, Git** e acesso permitido à fonte de referência. No PowerShell, na raiz do Blue:

~~~powershell
git clone https://github.com/pret/pokefirered.git .blue-work/pokefirered-reference
git -C .blue-work/pokefirered-reference rev-parse HEAD
git rev-parse HEAD
~~~

Se .blue-work/pokefirered-reference já existir, não a sobrescreva: reutilize a cópia e registre o SHA retornado. Para congelar a referência em um commit específico, faça checkout naquela cópia local, **nunca na main do Blue**. É aceitável guardar o SHA em um relatório privado.

Estrutura esperada da referência:

~~~text
.blue-work/
  pokefirered-reference/
    data/
      maps/
        PalletTown/
          text.inc
          scripts.inc
      text/
    src/
~~~

Não copie arquivos desta referência para game/Data nem para a pasta versionada docs/.

## 4. Passo B — inventário das falas em inglês, sem tradução

Execute a partir da raiz do Blue:

~~~powershell
py -3 scripts/localization/extrair_traduzir_dialogos_firered.py .blue-work/pokefirered-reference --saida .blue-work/kanto-dialogos/FireRed_Dialogos_EN_PT.md
~~~

Resultado privado: **.blue-work/kanto-dialogos/FireRed_Dialogos_EN_PT.md**.

O arquivo terá uma seção por entrada detectada, agrupada por local, com identificação, caminho, linha de origem, campo inglês, campo português pendente e estado de revisão. O identificador da fala é **rótulo da fonte GBA**, não é ID de Event do RPG Maker.

Para testar sem criar um catálogo enorme:

~~~powershell
py -3 scripts/localization/extrair_traduzir_dialogos_firered.py .blue-work/pokefirered-reference --limite 50 --sem-c --saida .blue-work/kanto-dialogos/TESTE_50_FALAS.md
~~~

**Cobertura:** o script procura padrões .string em data/ e macro _() em src/*.c. Ele não garante atingir toda mensagem dinâmica, todas as variantes condicionais ou todas as cenas jogáveis. Revise as ausências antes de considerar um mapa completo.

## 5. Passo C — tradução automática para português, opcional

O tradutor é ferramenta de autoria. Não entra no pacote do jogo.

~~~powershell
py -3 -m pip install argostranslate
py -3 scripts/localization/extrair_traduzir_dialogos_firered.py .blue-work/pokefirered-reference --traduzir --limite 50 --saida .blue-work/kanto-dialogos/TESTE_50_TRADUZIDAS.md
~~~

Depois de inspecionar o teste e instalar o modelo inglês→português:

~~~powershell
py -3 scripts/localization/extrair_traduzir_dialogos_firered.py .blue-work/pokefirered-reference --traduzir --saida .blue-work/kanto-dialogos/FireRed_Dialogos_EN_PT.md
~~~

**Atenção:** Argos gera português genérico; somente uma revisão humana pode validar **pt-BR**. Uma nova execução sobrescreve o Markdown de saída: para preservar comentários ou revisões, mantenha um arquivo separado com suas decisões. Não altere macros ou variáveis como {PLAYER}, {RIVAL}, {STR_VAR_1}, marcas de controle ou o significado das opções de escolha.

## 6. Passo D — cruzar falas com os eventos FireRed

Rode também o extrator de eventos já existente:

~~~powershell
py -3 scripts/regions/extrair_eventos_firered.py .blue-work/pokefirered-reference --out .blue-work/kanto-event-audit
~~~

Confira esses artefatos privados:

- **eventos_detalhados.csv** e **eventos_detalhados.json**: NPCs, objetos, gatilhos, warps e metadados explícitos.
- **mapas_resumo.json**: relação de mapas, flags citadas e arquivos de script.
- **INVENTARIO_COMPLETO_FIRERED.md**: checklist de registros e scripts por mapa.

Para cada fala escolhida, abra **data/maps/NOME/text.inc** na fonte e depois o **scripts.inc** correspondente. Busque o rótulo da fala, identifique quem a apresenta e qual condição a dispara. Siga também chamadas a scripts globais. Considere as variações *antes e depois* de receber item, vencer batalha, obter insígnia, retornar ao NPC e recarregar o save.

**Não associe por semelhança de nome apenas:** confirme o contexto por mapa, evento e estados.

## 7. Passo E — criar a matriz de implementação Kanto

Mantenha uma planilha ou relatório privado, com um registro por **uso de fala**, não somente por texto distinto:

| Campo | Como preencher |
|---|---|
| source_commit | SHA completo da decompilação FireRed |
| gba_map | Nome do mapa e script de origem |
| gba_text_id | Rótulo da fala em text.inc |
| gba_script | Rótulo da rotina que usa a fala |
| source_flag / condition | Flag, variável e condição da fonte |
| speaker / context | NPC, placa, batalha, escolha ou sistema |
| source_rmxp_map_id | MapID da fonte Essentials FRLG, se houver |
| blue_map_id / event_id | IDs reais do piloto Blue, **depois** de comprovados |
| event_state | Estado em que o texto deve aparecer |
| en_reference / pt_br_review | Referência local e texto adaptado/revisado |
| token_check | Preservou controles e variáveis? |
| status / evidence | Pendente, mapeado, revisado, implementado, testado |

O mapeamento deve respeitar **data/regions/kanto-source.json** e os manifestos do piloto. O GBA MAP_* e o RPG Maker MapXXX.rxdata não possuem IDs intercambiáveis. Nunca converta um warp de GBA diretamente em ID de mapa.

### Exemplo demonstrativo AUTORAL (não é transcrição de FireRed)

~~~text
gba_map: PalletTown
gba_text_id: EXEMPLO_OAK_INICIO
speaker/context: Professor no laboratório; jogador entra pela primeira vez
en_reference: "Welcome, {PLAYER}. Choose your partner."
pt_br_review: "Bem-vindo, {PLAYER}. Escolha seu parceiro."
event_state: antes de escolher o primeiro Pokémon
status: exemplo de documentação, NÃO IMPLEMENTADO
~~~

## 8. Passo F — adaptar para o sistema de localização do Blue

O projeto já usa:

- **scripts/localization/catalog.py**: lê mensagens compiladas, mapas e eventos da cópia **local** de Decades; extrai chaves de texto que a engine realmente exibe.
- **data/pt-br.json**: tabela pt-BR distribuída, onde as chaves são mensagens **inglesas da engine**, não rótulos GBA.
- **scripts/localization/review.py**: valida um cache de pares origem→tradução, controles e resíduos de placeholders.
- **scripts/localization/install.py**: prepara a tabela de idioma para o instalador escrever **game/Data/blue-pt-br.dat** com backup/rollback.
- **docs/PORTUGUES_E_UI.md**: comportamento da opção Language/Idioma e limite das traduções.

### Caso 1 — a fala inglesa equivalente já existe no Blue

1. Identifique a **mensagem exata** no catálogo Blue, não apenas a fala FireRed parecida.
2. Revise a adaptação para pt-BR preservando os controles dessa mensagem Blue.
3. Adicione ou atualize somente o par correspondente em **data/pt-br.json**, sem perder as demais traduções. Mantenha o esquema version=1, language=pt-BR, translations como objeto.
4. Confira que não há duplicatas/confusões com nomes de Pokémon, golpes, itens ou variáveis de batalha.
5. Execute a validação de controles com a função catalog.validate(origem, traducao), usada também na instalação.
6. Instale/recompile pelo procedimento existente do Blue e confirme o resultado **dentro do jogo**.

### Caso 2 — a fala/evento ainda não existe no Blue

1. Não adicione uma chave GBA fictícia ao JSON esperando que ela apareça.
2. Registre o texto aprovado no planejamento do evento e escolha o MapID e EventID corretos da cópia piloto.
3. **Somente após autorização para implementar o evento:** crie/adapte a fala no RPG Maker XP/Essentials ou por um script próprio versionável em scripts/regions/.
4. Proteja estado, flags, escolhas e premiações para não contaminar a campanha Decades e não duplicar recompensas.
5. Reextraia o catálogo da cópia piloto e localize a nova **chave inglesa realmente exibida**. Só então vincule a tradução pt-BR no JSON, valide e instale.
6. Teste a primeira conversa, repetição, condições alternativas, troca de idioma e save/reload.

**Nunca importe diretamente os .inc de FireRed para Ruby/RXDATA.** O texto pode ser uma referência de adaptação, mas scripts de GBA e eventos do Essentials precisam de tradução de comportamento, não de cópia binária.

## 9. Passo G — regras para revisão e interface

- Preservar {PLAYER}, {RIVAL}, {STR_VAR_1}, valores dinâmicos, tags e escolhas em suas posições sem alterar a ordem das opções.
- Proteger controles específicos da engine: códigos de nome, formatação, pausas, janelas, quebras e referências a eventos.
- Usar **Equipe Rocket**, **Líder de Ginásio**, **Elite dos Quatro**, **Poké Ball**, **Pokédex** com consistência; manter os nomes oficiais de espécies e golpes conforme as regras vigentes no Blue.
- Conferir concordância, gênero, pontuação, caixa de diálogo e contexto: uma fala pós-batalha difere da fala inicial do mesmo NPC.
- Usar o texto original apenas na referência privada; em eventos públicos do fangame, publicar conteúdo somente quando houver permissão.
- A revisão é por fala **e por uso**: falas reutilizadas podem exigir contexto diferente.

## 10. Passo H — teste sem comprometer a campanha

O roteiro de testes é o mesmo do piloto [KANTO_TESTE_EXPERIMENTAL.md](KANTO_TESTE_EXPERIMENTAL.md). Abra o jogo experimental pelo menu **Testar Kanto**, quando disponível, ou por **KANTO_JOGAR_EXPERIMENTAL.bat**, e faça o seguinte em **cada evento já autorizado e instalado**:

1. Teste com idioma **English**; anote texto, NPC, mapa e condição.
2. Mude em **Configurações → Language / Idioma → Português**; confira a tradução correspondente.
3. Verifique os controles {PLAYER}/{RIVAL} e caracteres com acento; nenhum placeholder deve aparecer truncado.
4. Teste as escolhas (Sim/Não, aceitar/recusar, opções de batalha) e suas consequências; o índice da opção não pode mudar.
5. Antes/depois de receber item, vencer/perder/fugir de batalha, entrar e sair do mapa: confirme o diálogo esperado.
6. Salve e carregue novamente para observar persistência e ausência de recompensas duplicadas.
7. Teste menus e mensagens globais em português e inglês para evitar regressão.
8. Confira o mesmo roteiro em Windows; depois valide JoiPlay se o conteúdo estiver pronto.
9. Registre resultado, commit, MapID/EventID e evidências. Teste de sintaxe/extração **não** vale como aceite de jogabilidade.

## 11. Ordem recomendada de implementação e limites de Kanto

| Lote | Locais | Conteúdo de diálogo a mapear | Pré-condição |
|---|---|---|---|
| A | Pallet / Oak / Rota 1 | Introdução, escolha de inicial, rival, entrega e tutoriais | Corrigir/validar interiores e gatilhos existentes |
| B | Viridian / Forest / Pewter | Parcel, NPCs, treinadores, Brock, insígnia e retorno | MAN-01 e MAN-02; flags de vitória |
| C | Rotas 3–4 / Mt. Moon | Treinadores, Rocket, fósseis, placas, itens únicos | Escadas, warps e escolhas |
| D | Cerulean / Bill / Vermilion | Misty, rival, Nugget Bridge, S.S. Anne, Capitão e Surge | Eventos correspondentes já autorizados |
| E | Celadon / Lavender / Saffron | Rocket, Torre, Fuji, ginásios e Silph Co. | **Não ativar** em mapas preview_only |
| F | Fuchsia / Cinnabar / Viridian | Safari, Koga, Blaine, Giovanni, bloqueios e HMs | Avanço de fases e autorização |
| G | Liga / pós-jogo / Sevii | Elite Four, campeão, conquistas e viagens | Progressão regional e escopo aprovados |

O estado de desenvolvimento e aceite é registrado **somente** em [KANTO_ETAPAS.md](KANTO_ETAPAS.md). Criar este guia **não aumenta** nenhuma barra de progresso e não autoriza alterar mapas preview_only.

## 12. Checklist de conclusão por área

- [ ] Origem da fala confirmada (SHA + arquivo + label)
- [ ] NPC e evento/ramo identificados
- [ ] Mapeamento GBA → Essentials → Blue comprovado
- [ ] Tradução revisada manualmente (pt-BR)
- [ ] Tokens e controles validados
- [ ] Uso autorizado, implementado no piloto isolado
- [ ] Nenhuma recompensa/flag/switch alterada indevidamente
- [ ] Diálogos English e Português validados no Game.exe
- [ ] Repetição, save/reload e condições alternativas aprovados
- [ ] Commit, MapID, EventID e evidência registrados

## 13. Problemas comuns

| Sintoma | Verificação |
|---|---|
| Nenhuma fala encontrada | Confirme a pasta de origem; o extrator exige data/ e arquivos .inc/.s |
| Falha ao instalar Argos | Teste primeiro sem --traduzir; verifique Python/pip/rede/modelo |
| Parte das falas não aparece | O extrator detecta padrões literais, não executa lógica dinâmica; inspecione scripts globais |
| A fala foi traduzida, mas não aparece no jogo | A chave GBA não equivale à string da engine Blue; verifique o catálogo real |
| Texto em português corrompe comandos | Revalide placeholders com catalog.validate e revise o texto manualmente |
| Texto certo, NPC errado | Volte ao script, estado e event_id; não associe apenas por nome |
| Kanto muda a campanha Decades | Não publique a adaptação; retorne à cópia piloto isolada e revise flags/rollback |

**Resultado desta entrega:** documentação + extrator de referência versionados. **Não concluído nesta etapa:** geração do catálogo integral a partir da cópia local, tradução revisada de todas as falas, integração automática ao jogo ou aceite funcional dos eventos.
