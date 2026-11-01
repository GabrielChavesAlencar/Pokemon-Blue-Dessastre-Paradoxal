# Pokémon Blue: Dessastre Paradoxal — Pokédex, descrições, altura e peso

> **DOCUMENTAÇÃO DE REFERÊNCIA PUBLICADA — 47/59 ESPÉCIES APROVADAS; 12 AINDA PENDENTES DE REVISÃO.**  
> **Progresso:** 47 de 59 entradas aprovadas. Swadloadne (#1084) aprovado junto com Stundrift (#1083), Ammnoid (#1081) e Cephalonid (#1082). Permanecem em revisão Rampage Horn (#1055), Ravenous Crest (#1056), Razor Carapace (#1057), Savege Jowl (#1058), Thorn Bastion (#1061) e Iron Matriarch (#1070). As seis espécies convergentes (#1071–#1076) foram adiadas pelo criador. A origem de Primatizer ainda não foi confirmada.
> O jogo será escrito em **inglês**. As traduções em português são apenas para revisão com o criador.  
> Atualizado em 31/10/2026 (Swadloadne aprovado; publicação autorizada para a documentação e descrições do site). As propostas pendentes permanecem no MD apenas para revisão futura.

## Objetivo

Elaborar, **uma espécie por vez**, uma nova entrada de Pokédex em inglês, com **altura (m)** e **peso (kg)** propostos. O criador lê a tradução portuguesa, pede ajustes e aprova. A publicação parcial das **47 entradas aprovadas** no GitHub e na Pokédex foi autorizada. Entradas em revisão continuam documentadas, mas não devem substituir as descrições exibidas no site.

## Estado atual e escopo

**Ordem de revisão ajustada em 31/10/2026:** pular temporariamente as seis espécies convergentes (46–51/59) e iniciar as novas evoluções em Archgutor (52/59). Os IDs e a contagem total de 59 espécies não são alterados. Iron Matriarch (#1070) continua em revisão porque a aprovação explícita da descrição e das medidas ainda não foi registrada.

| Grupo | Novas espécies | Ainda pendentes no catálogo |
|---|---:|---:|
| Past Paradox | 38 | 1 |
| Future Paradox | 7 | 0 |
| Convergent species | 6 | 6 |
| New evolutions | 8 | 0 |
| **Total** | **59** | **7** |

Além das 59 espécies, há **12 Mega Evoluções autorais** (`customForms`), listadas separadamente no final deste MD: são formas de outras espécies, e altura/peso podem seguir uma regra diferente.

**Situação do catálogo:** as 59 espécies estão com descrição `????` e valores `height`/`weight` nulos. As 7 espécies marcadas como pendentes no jogo não devem ser tratadas como prontas para implementação só por possuírem texto novo.

## Critérios de criação

1. **Texto in-game somente em inglês**, com 1 ou 2 frases curtas de tom Pokédex, de preferência entre 90 e 170 caracteres. Sem exagerar em superlativos nem prometer poderes não presentes no design.
2. **Coerência visual e biológica:** considerar silhueta/sprite, tipo(s), comportamento, habitat, parentesco ou convergência, e papel da evolução. Se a origem visual não estiver clara, marcar o texto como *provisório* até revisão.
3. **Paradoxos do passado:** linguagem de predador ancestral, adaptação natural ou ambiente pré-histórico; evite simplesmente dizer que tudo tem rochas e espinhos.
4. **Paradoxos do futuro:** enfatizar mecanismos, materiais, energia ou funções reinterpretadas, sem trocar a identidade do Pokémon original por uma máquina genérica.
5. **Convergentes:** explicar como a espécie tem aparência familiar, mas biologia e nicho ecológico próprios; preservar a progressão entre as três etapas.
6. **Novas evoluções:** fazer o estágio parecer uma continuação convincente da espécie anterior, e não um Pokémon sem ligação com a família.
7. **Altura:** valor decimal em **metros (m)**. **Peso:** valor decimal em **quilogramas (kg)**. São propostas autorais, não medições oficiais. Manter proporção plausível entre os membros da linha.
8. **Revisão individual:** apresentar o inglês e a tradução PT-BR, com altura/peso e uma justificativa curta; usar o status `Aguardando aprovação` até resposta do criador.
9. **Não alterar** IDs, tipos, stats, habilidades, golpes nem nomes no jogo como efeito deste MD. Nomes com grafia ou capitalização incomuns serão apenas sinalizados para revisão.
10. **Publicação parcial autorizada:** registrar no site somente as entradas aprovadas; preservar as pendentes para revisão futura, sem alterar os PBS locais.
11. **Nomes a partir do #1054:** por solicitação do criador, **não criar novos nomes**; preservar os nomes já cadastrados, exceto se ele pedir expressamente uma alteração.

### Campos que serão aplicados ao Pokémon Essentials (somente no fim)

Para uma seção existente `[CAVEFANG]` no arquivo PBS correspondente, inserir/substituir **apenas**:

```ini
Height = 1.6
Weight = 36.0
Pokedex = An ancient relative of Zubat, it hunts in pitch-black caves using ultrasonic cries. Its oversized fangs inject a powerful venom, paralyzing prey before it can escape.
```

**46 espécies com texto, medidas e nomes (quando aplicável) aprovados pelo criador; consultar a fila de revisão abaixo. Ainda não aplicados ao jogo nem enviados ao GitHub.** `Pokedex` é o campo do jogo, não `description`. A exportação do portal lê `Height`, `Weight` e `Pokedex` do PBS quando estiverem presentes.

---

## 01/59 — Cave Fang — #1026

- **ID PBS:** `CAVEFANG`
- **Category:** Past Paradox
- **Type:** Poison / Dark
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Zubat**.
- **Pokédex EN (aprovada):** An ancient relative of Zubat, it hunts in pitch-black caves using ultrasonic cries. Its oversized fangs inject a powerful venom, paralyzing prey before it can escape.
- **Tradução PT-BR (aprovada para revisão):** Um antigo parente de Zubat, ele caça em cavernas completamente escuras utilizando gritos ultrassônicos. Suas presas enormes injetam um veneno poderoso, paralisando suas presas antes que consigam escapar.
- **Height / Altura (aprovada):** **1.6 m**
- **Weight / Peso (aprovado):** **36.0 kg**
- **Justificativa:** Zubat ancestral muito maior e mais musculoso, mas com anatomia relativamente leve para o voo. As presas pronunciadas e o veneno combinam com o visual e o tipo Poison / Dark; os gritos ultrassônicos preservam um traço reconhecível da linhagem de Zubat. O comportamento predatório é parte da descrição autoral aprovada.
- **Review status:** **APROVADO pelo criador — aguardando conclusão de todo o MD antes de qualquer publicação.**
- **Notas do criador:** Aprovou descrição, altura de 1,6 m e peso de 36,0 kg. **Não publicar na `main` até o documento completo.**

---

## 02/59 — Abyss Lure — #1027

- **ID PBS:** `ABYSSLURE`
- **Category:** Past Paradox
- **Type:** Water / Fairy
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Lanturn**.
- **Pokédex EN (aprovada):** An ancient relative of Lanturn, it roamed the deepest oceans using its enormous fins. Its golden lure emits an enchanting glow that draws unsuspecting prey straight into its powerful jaws.
- **Tradução PT-BR (aprovada para revisão):** Um antigo parente de Lanturn, ele percorria as regiões mais profundas dos oceanos utilizando suas enormes nadadeiras. Sua isca dourada emite um brilho encantador que atrai presas desavisadas diretamente para suas poderosas mandíbulas.
- **Height / Altura (aprovada):** **1.9 m**
- **Weight / Peso (aprovado):** **64.0 kg**
- **Justificativa:** A forma ancestral mantém a antena luminosa de Lanturn, mas apresenta nadadeiras maiores e boca ameaçadora. A luz encantadora reforça o tipo Fairy, enquanto seu tamanho e mandíbulas sugerem um predador de águas profundas. Altura e peso são escolhas autorais aprovadas, não medidas oficiais.
- **Review status:** **APROVADO pelo criador — aguardando conclusão de todo o MD antes de qualquer publicação.**
- **Notas do criador:** Identificou Abyss Lure como Paradoxo do passado de Lanturn e aprovou a descrição proposta, altura de 1,9 m e peso de 64,0 kg. **Não publicar na `main` até o documento completo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [ABYSSLURE]
Height = 1.9
Weight = 64.0
Pokedex = An ancient relative of Lanturn, it roamed the deepest oceans using its enormous fins. Its golden lure emits an enchanting glow that draws unsuspecting prey straight into its powerful jaws.
```

---

## 03/59 — Ancestrash — #1028

- **ID PBS:** `ANCESTRASH`
- **Category:** Past Paradox
- **Type:** Poison / Ground
- **Origem definida pelo criador:** Forma Paradoxo ancestral de **Garbodor**.
- **Pokédex EN (aprovada):** An ancient relative of Garbodor, it piles bones and decaying vegetation onto its muddy body. Toxic fumes seep from the rotting mass, turning the ground around it into a deadly bog.
- **Tradução PT-BR (aprovada para revisão):** Um antigo parente de Garbodor, ele acumula ossos e vegetação em decomposição sobre seu corpo lamacento. Vapores tóxicos escapam dessa massa apodrecida, transformando o solo ao seu redor em um pântano mortal.
- **Height / Altura (aprovada):** **2.4 m**
- **Weight / Peso (aprovado):** **260.0 kg**
- **Justificativa:** Antes do lixo produzido pelos humanos, a criatura aproveitava resíduos naturais como ossos, carcaças e plantas apodrecidas. Seu corpo formado por lama e restos orgânicos justifica o tipo Ground e o peso elevado, enquanto os gases da decomposição reforçam o tipo Poison. Conceito e medidas autorais aprovados pelo criador.
- **Review status:** **APROVADO pelo criador — aguardando conclusão de todo o MD antes de qualquer publicação.**
- **Notas do criador:** Identificou Ancestrash como o Paradoxo ancestral de Garbodor e aprovou o texto proposto, altura de 2,4 m e peso de 260,0 kg. **Não publicar na `main` até o documento completo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [ANCESTRASH]
Height = 2.4
Weight = 260.0
Pokedex = An ancient relative of Garbodor, it piles bones and decaying vegetation onto its muddy body. Toxic fumes seep from the rotting mass, turning the ground around it into a deadly bog.
```

---

## 04/59 — Burial Gaze — #1029

- **ID PBS:** `BURIALGAZE`
- **Category:** Past Paradox
- **Type:** Ghost / Ground
- **Origem definida pelo criador:** Forma Paradoxo ancestral de **Duskull**.
- **Pokédex EN (aprovada):** An ancient relative of Duskull, it wanders forgotten burial grounds with its body covered in grave dust. Those who meet its unblinking gaze are said to hear the voices of spirits buried deep underground.
- **Tradução PT-BR (aprovada para revisão):** Um antigo parente de Duskull, ele vaga por cemitérios esquecidos com seu corpo coberto pela poeira das sepulturas. Dizem que aqueles que encaram seu olhar imóvel conseguem ouvir as vozes de espíritos enterrados nas profundezas da terra.
- **Height / Altura (aprovada):** **1.4 m**
- **Weight / Peso (aprovado):** **42.0 kg**
- **Justificativa:** Guardião ancestral de antigos locais de sepultamento; a terra e a poeira funerária reforçam o tipo Ground, enquanto o olhar sobrenatural e a relação com espíritos refletem o tipo Ghost. A descrição e as medidas foram aprovadas pelo criador. Características visuais específicas permanecem sujeitas a conferência com a arte final.
- **Review status:** **APROVADO pelo criador — aguardando conclusão de todo o MD antes de qualquer publicação.**
- **Notas do criador:** Identificou Burial Gaze como Paradoxo ancestral de Duskull e aprovou a descrição proposta, altura de 1,4 m e peso de 42,0 kg. **Não publicar na `main` até o documento completo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [BURIALGAZE]
Height = 1.4
Weight = 42.0
Pokedex = An ancient relative of Duskull, it wanders forgotten burial grounds with its body covered in grave dust. Those who meet its unblinking gaze are said to hear the voices of spirits buried deep underground.
```

---

## 05/59 — Craggy Siphon — #1030

- **ID PBS:** `CRAGGYSIPHON`
- **Category:** Past Paradox
- **Type:** Water / Fighting
- **Origem definida pelo criador:** Forma Paradoxo ancestral de **Octillery**.
- **Pokédex EN (aprovada):** An ancient relative of Octillery, it ruled rocky coastal waters with its immense strength. It strikes foes with stone-hard tentacles and fires powerful jets of water from its muscular siphon.
- **Tradução PT-BR (aprovada para revisão):** Um antigo parente de Octillery, ele dominava as águas costeiras rochosas graças à sua força imensa. Ataca seus inimigos com tentáculos duros como pedra e dispara poderosos jatos de água através de seu sifão musculoso.
- **Height / Altura (aprovada):** **1.7 m**
- **Weight / Peso (aprovado):** **108.0 kg**
- **Justificativa:** A arte mostra corpo vermelho-alaranjado, revestimento que lembra rocha, tentáculos musculosos e um sifão pronunciado. O tipo Water aparece nos jatos de água, enquanto o tipo Fighting está ligado aos golpes físicos dos tentáculos. As medidas destacam seu porte robusto em relação a Octillery.
- **Review status:** **APROVADO pelo criador — aguardando conclusão de todo o MD antes de qualquer publicação.**
- **Notas do criador:** Identificou Craggy Siphon como Paradoxo ancestral de Octillery e aprovou a descrição proposta, altura de 1,7 m e peso de 108,0 kg. **Não publicar na `main` até o documento completo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [CRAGGYSIPHON]
Height = 1.7
Weight = 108.0
Pokedex = An ancient relative of Octillery, it ruled rocky coastal waters with its immense strength. It strikes foes with stone-hard tentacles and fires powerful jets of water from its muscular siphon.
```

---

## 06/59 — Dire Ruff — #1031

- **ID PBS:** `DIRERUFF`
- **Category:** Past Paradox
- **Type:** Dark / Ground
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Mightyena**.
- **Pokédex EN (aprovada):** An ancient relative of Mightyena, it hunted in ruthless packs across barren plains. Its jagged mane bristles as it kicks up blinding clouds of dust, allowing its pack to ambush unsuspecting prey.
- **Tradução PT-BR (aprovada para revisão):** Um antigo parente de Mightyena, ele caçava em matilhas implacáveis pelas planícies áridas. Sua crina pontiaguda se arrepia enquanto levanta nuvens de poeira que cegam suas vítimas, permitindo que sua matilha embosque presas desprevenidas.
- **Height / Altura (aprovada):** **1.6 m**
- **Weight / Peso (aprovado):** **82.0 kg**
- **Justificativa:** A pelagem escura, a crina pontiaguda, as patas musculosas, as garras e os olhos avermelhados da arte inspiram uma forma ancestral mais robusta de Mightyena. O tipo Dark é expresso pela caça em matilha e emboscadas; o tipo Ground, pelas planícies áridas e pelas nuvens de poeira. As medidas ressaltam seu porte maior em comparação com Mightyena.
- **Review status:** **APROVADO pelo criador — aguardando conclusão de todo o MD antes de qualquer publicação.**
- **Notas do criador:** Identificou Dire Ruff como forma Paradoxo do passado de Mightyena e aprovou integralmente a descrição, a altura de 1,6 m e o peso de 82,0 kg. **Não publicar na `main` até o documento completo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [DIRERUFF]
Height = 1.6
Weight = 82.0
Pokedex = An ancient relative of Mightyena, it hunted in ruthless packs across barren plains. Its jagged mane bristles as it kicks up blinding clouds of dust, allowing its pack to ambush unsuspecting prey.
```

---

## 07/59 — Dread Crest — #1032

- **ID PBS:** `DREADCREST`
- **Category:** Past Paradox
- **Type:** Flying / Ground
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Noctowl**.
- **Pokédex EN (aprovada):** An ancient relative of Noctowl, it ruled the skies above barren canyons. Its enormous crest intimidated rivals, while its powerful wings stirred up blinding dust clouds to conceal its attacks.
- **Tradução PT-BR (aprovada para revisão):** Um antigo parente de Noctowl, ele dominava os céus acima de cânions áridos. Sua enorme crista intimidava os rivais, enquanto suas asas poderosas levantavam nuvens de poeira que cegavam suas vítimas e ocultavam seus ataques.
- **Height / Altura (aprovada):** **2.1 m**
- **Weight / Peso (aprovado):** **58.0 kg**
- **Justificativa:** A imagem mostra plumagem marrom volumosa, grandes asas, garras e uma enorme crista dourada semelhante a chifres. O tipo Flying é refletido pelo voo e pelo domínio dos céus; Ground, pelo habitat árido e pela poeira levantada com as asas. O porte é maior que o do Noctowl atual, com peso relativamente moderado para um Pokémon voador.
- **Review status:** **APROVADO pelo criador — aguardando conclusão de todo o MD antes de qualquer publicação.**
- **Notas do criador:** Identificou Dread Crest como a forma Paradoxo ancestral de Noctowl e aprovou integralmente descrição em inglês, altura de 2,1 m e peso de 58,0 kg. **Não publicar na `main` até o documento completo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [DREADCREST]
Height = 2.1
Weight = 58.0
Pokedex = An ancient relative of Noctowl, it ruled the skies above barren canyons. Its enormous crest intimidated rivals, while its powerful wings stirred up blinding dust clouds to conceal its attacks.
```

---

## 08/59 — Fetid Gullet — #1033

- **ID PBS:** `FETIDGULLET`
- **Category:** Past Paradox
- **Type:** Poison / Ghost
- **Origem definida pelo criador:** Forma Paradoxo ancestral de **Swalot**.
- **Pokédex EN (aprovada):** An ancient relative of Swalot, it swallowed decaying matter from primeval marshes without pause. The foul gases in its cavernous body are said to trap the lingering spirits of anything it consumes.
- **Tradução PT-BR (aprovada para revisão):** Um antigo parente de Swalot, ele engolia sem parar matéria em decomposição dos pântanos primordiais. Dizem que os gases fétidos em seu corpo cavernoso aprisionam os espíritos remanescentes de tudo o que ele consome.
- **Height / Altura (aprovada):** **1.9 m**
- **Weight / Peso (aprovado):** **94.0 kg**
- **Justificativa:** A arte apresenta corpo roxo viscoso e inchado, uma boca enorme e marcas sombrias. A decomposição e os gases tóxicos reforçam Poison; a ideia de espíritos aprisionados liga a espécie ao tipo Ghost. As medidas representam uma criatura um pouco maior e mais pesada que Swalot.
- **Review status:** **APROVADO pelo criador — aguardando conclusão de todo o MD antes de qualquer publicação.**
- **Notas do criador:** Identificou Fetid Gullet como a forma Paradoxo do passado de Swalot e aprovou a descrição proposta, altura de 1,9 m e peso de 94,0 kg. **Não publicar na `main` até o documento completo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [FETIDGULLET]
Height = 1.9
Weight = 94.0
Pokedex = An ancient relative of Swalot, it swallowed decaying matter from primeval marshes without pause. The foul gases in its cavernous body are said to trap the lingering spirits of anything it consumes.
```

---

## 09/59 — Fossil Husk — #1034

- **ID PBS:** `FOSSILHUSK`
- **Category:** Past Paradox
- **Type:** Bug / Rock
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Pineco**.
- **Pokédex EN (aprovada):** An ancient relative of Pineco, it developed a shell of mineralized plates as hard as solid rock. It clung to trees along prehistoric cliffs, dropping onto predators with enough force to shatter stone.
- **Tradução PT-BR (aprovada para revisão):** Um antigo parente de Pineco, ele desenvolveu uma carapaça de placas mineralizadas tão duras quanto rocha sólida. Agarrava-se às árvores de penhascos pré-históricos, lançando-se sobre predadores com força suficiente para despedaçar pedras.
- **Height / Altura (aprovada):** **1.1 m**
- **Weight / Peso (aprovado):** **79.0 kg**
- **Justificativa:** A arte mostra carapaça azul-esverdeada formada por placas minerais pontiagudas e olhos avermelhados. O tipo Bug preserva o parentesco com o Pokémon casulo Pineco; Rock corresponde à carapaça mineral muito densa. A proposta também combina com Defense 180 do catálogo. A altura e o peso, maiores que os de Pineco, foram aprovados pelo criador.
- **Review status:** **APROVADO pelo criador — aguardando conclusão de todo o MD antes de qualquer publicação.**
- **Notas do criador:** Identificou Fossil Husk como a forma Paradoxo do passado de Pineco e aprovou a descrição proposta, altura de 1,1 m e peso de 79,0 kg. **Não publicar na `main` até o documento completo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [FOSSILHUSK]
Height = 1.1
Weight = 79.0
Pokedex = An ancient relative of Pineco, it developed a shell of mineralized plates as hard as solid rock. It clung to trees along prehistoric cliffs, dropping onto predators with enough force to shatter stone.
```

---

## 10/59 — Fossl Tide — #1035

- **ID PBS:** `FOSSLTIDE`
- **Category:** Past Paradox
- **Type:** Water / Steel
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Gastrodon**.
- **Pokédex EN (aprovada):** An ancient relative of Gastrodon, it absorbed iron from the prehistoric seafloor to form a thick metallic shell. Its armored body could withstand crushing ocean currents and attacks from enormous predators.
- **Tradução PT-BR (aprovada para revisão):** Um antigo parente de Gastrodon, ele absorvia ferro do fundo dos oceanos pré-históricos para formar uma espessa carapaça metálica. Seu corpo blindado era capaz de resistir a correntes oceânicas esmagadoras e aos ataques de predadores gigantescos.
- **Height / Altura (aprovada):** **1.6 m**
- **Weight / Peso (aprovado):** **118.0 kg**
- **Justificativa:** A arte mostra o corpo rosado de uma lesma marinha semelhante a Gastrodon, protegido por placas marrons endurecidas, espinhos e protuberâncias que lembram chifres. A absorção de ferro e outros minerais do leito oceânico explica o tipo Steel e o peso elevado; a origem aquática preserva o tipo Water. A descrição e as medidas foram aprovadas pelo criador.
- **Review status:** **APROVADO pelo criador — aguardando conclusão de todo o MD antes de qualquer publicação.**
- **Notas do criador:** Confirmou ser o Paradoxo do passado de Gastrodon e aprovou a descrição proposta, altura de 1,6 m e peso de 118,0 kg. **Não publicar na `main` até o documento completo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [FOSSLTIDE]
Height = 1.6
Weight = 118.0
Pokedex = An ancient relative of Gastrodon, it absorbed iron from the prehistoric seafloor to form a thick metallic shell. Its armored body could withstand crushing ocean currents and attacks from enormous predators.
```

---

## 11/59 — Jagged Maw — #1036

- **ID PBS:** `JAGGEDMAW`
- **Category:** Past Paradox
- **Type:** Water / Rock
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Cloyster**.
- **Pokédex EN (aprovada):** An ancient relative of Cloyster, it lurked among submerged cliffs, disguising its jagged shell as stone. When prey approached, its enormous jaws snapped shut with enough force to crush solid rock.
- **Tradução PT-BR (aprovada para revisão):** Um antigo parente de Cloyster, ele se escondia entre penhascos submersos, disfarçando sua carapaça serrilhada como uma rocha. Quando uma presa se aproximava, suas enormes mandíbulas se fechavam com força suficiente para esmagar rocha sólida.
- **Height / Altura (aprovada):** **2.2 m**
- **Weight / Peso (aprovado):** **285.0 kg**
- **Justificativa:** A arte apresenta uma concha roxa mineralizada com longos espinhos irregulares e grande abertura central. O tipo Water preserva a origem marinha de Cloyster; o tipo Rock representa a carapaça mineral endurecida e sua camuflagem em penhascos submersos. Defesa 200 e peso elevado são coerentes com uma proteção extremamente densa.
- **Review status:** **APROVADO pelo criador — aguardando conclusão de todo o MD antes de qualquer publicação.**
- **Notas do criador:** Confirmou Jagged Maw como a forma Paradoxo do passado de Cloyster e aprovou a descrição proposta, altura de 2,2 m e peso de 285,0 kg. **Não publicar na `main` até o documento completo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [JAGGEDMAW]
Height = 2.2
Weight = 285.0
Pokedex = An ancient relative of Cloyster, it lurked among submerged cliffs, disguising its jagged shell as stone. When prey approached, its enormous jaws snapped shut with enough force to crush solid rock.
```

---

## 12/59 — Miasmic — #1037

- **ID PBS:** `MIASMIC`
- **Category:** Past Paradox
- **Type:** Poison / Dark
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Weezing**.
- **Pokédex EN (aprovada):** An ancient relative of Weezing, it drifted through toxic marshes while spewing a noxious yellow haze. Prey that inhaled its miasma grew weak and disoriented, making them easy targets for its vicious assault.
- **Tradução PT-BR (aprovada para revisão):** Um antigo parente de Weezing, ele vagava por pântanos tóxicos enquanto expelia uma névoa amarelada e nociva. As presas que inalavam seu miasma ficavam fracas e desorientadas, tornando-se alvos fáceis para seu ataque cruel.
- **Height / Altura (aprovada):** **1.8 m**
- **Weight / Peso (aprovado):** **72.0 kg**
- **Justificativa:** O sprite mostra dois corpos roxos unidos, expressão mais ameaçadora, espinhos e gases amarelos. O tipo Poison representa as emissões nocivas; o Dark, o ataque oportunista contra presas enfraquecidas. A massa maior em relação a Weezing é uma decisão autoral aprovada.
- **Review status:** **APROVADO pelo criador — aguardando conclusão de todo o MD antes de qualquer publicação.**
- **Notas do criador:** Confirmou a forma Paradoxo do passado de Weezing e aprovou a descrição proposta, altura de 1,8 m e peso de 72,0 kg. **Não publicar na `main` até o documento completo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [MIASMIC]
Height = 1.8
Weight = 72.0
Pokedex = An ancient relative of Weezing, it drifted through toxic marshes while spewing a noxious yellow haze. Prey that inhaled its miasma grew weak and disoriented, making them easy targets for its vicious assault.
```

---

## 13/59 — Mire Crest — #1038

- **ID PBS:** `MIRECREST`
- **Category:** Past Paradox
- **Type:** Dark / Fighting
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Skuntank**.
- **Pokédex EN (aprovada):** An ancient relative of Skuntank, it flares its towering mane to frighten rivals. It fights with deceptive lunges and crushing claw strikes, refusing to retreat even when outnumbered.
- **Tradução PT-BR (aprovada para revisão):** Um antigo parente de Skuntank, ele eriçava sua enorme crina para intimidar os rivais. Lutava com investidas traiçoeiras e golpes esmagadores de suas garras, recusando-se a recuar mesmo quando estava em desvantagem numérica.
- **Height / Altura (aprovada):** **1.5 m**
- **Weight / Peso (aprovado):** **74.0 kg**
- **Justificativa:** A arte mostra pelagem roxa escura, crina amarelada e eriçada, patas robustas e garras afiadas. O tipo Dark é refletido nas táticas de intimidação e emboscada; o Fighting, na força física empregada nos combates. O tamanho maior que Skuntank e o peso de 74,0 kg refletem a constituição mais robusta.
- **Review status:** **APROVADO pelo criador — aguardando conclusão de todo o MD antes de qualquer publicação.**
- **Notas do criador:** Confirmou a origem como Paradoxo do passado de Skuntank e aprovou descrição em inglês, altura de 1,5 m e peso de 74,0 kg. **Não publicar na `main` até o documento completo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [MIRECREST]
Height = 1.5
Weight = 74.0
Pokedex = An ancient relative of Skuntank, it flares its towering mane to frighten rivals. It fights with deceptive lunges and crushing claw strikes, refusing to retreat even when outnumbered.
```

---

## 14/59 — Phantomire — #1039

- **ID PBS:** `PHANTOMIRE`
- **Category:** Past Paradox
- **Type:** Ghost / Dark
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Haunter**.
- **Pokédex EN (aprovada):** An ancient relative of Haunter, it prowled mist-covered marshes long before humans existed. Its spectral hands spread unnatural darkness, trapping unsuspecting prey in terrifying illusions.
- **Tradução PT-BR (aprovada para revisão):** Um antigo parente de Haunter, ele rondava pântanos cobertos de névoa muito antes da existência dos humanos. Suas mãos espectrais espalhavam uma escuridão sobrenatural, aprisionando presas desprevenidas em ilusões aterrorizantes.
- **Height / Altura (aprovada):** **1.9 m**
- **Weight / Peso (aprovado):** **0.4 kg**
- **Justificativa:** Espírito predador de pântanos antigos, que manipula sombras e ilusões para emboscar presas. O tipo Ghost representa seu corpo quase imaterial, e o tipo Dark, a utilização de escuridão sobrenatural. Medidas aprovadas como escolha autoral, sem arte definitiva examinada para esta ficha.
- **Review status:** **APROVADO pelo criador — aguardando conclusão de todo o MD antes de qualquer publicação.**
- **Notas do criador:** Identificou Phantomire como Paradoxo do passado de Haunter e aprovou a descrição, a altura de 1,9 m e o peso de 0,4 kg. **Não publicar na `main` até o documento completo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [PHANTOMIRE]
Height = 1.9
Weight = 0.4
Pokedex = An ancient relative of Haunter, it prowled mist-covered marshes long before humans existed. Its spectral hands spread unnatural darkness, trapping unsuspecting prey in terrifying illusions.
```

---

## 15/59 — Frost Plume (antigo Priamalgong) — #1040

- **ID PBS atual:** `PRIAMALGONG` (**preservado até a implementação final**).
- **Nome definitivo aprovado pelo criador:** **Frost Plume** (antigo nome provisório: Priamalgong).
- **Category:** Past Paradox
- **Type:** Ice / Dragon
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Dewgong**.
- **Referência visual:** forma branca e azul-clara, nadadeiras e cauda alongadas e franjas geladas semelhantes a plumas.
- **Pokédex EN (aprovada):** An ancient relative of Dewgong, it glided beneath polar ice on featherlike fins. Its icy breath froze seawater into sharp crystals, driving away even the fiercest predators.
- **Tradução PT-BR (aprovada):** Um antigo parente de Dewgong, ele deslizava sob o gelo polar com nadadeiras semelhantes a penas. Seu sopro gelado congelava a água do mar em cristais afiados, afastando até os predadores mais ferozes.
- **Height / Altura (aprovada):** **2.3 m**
- **Weight / Peso (aprovado):** **148.0 kg**
- **Justificativa:** Frost remete ao tipo Ice, e Plume à aparência das nadadeiras. A silhueta alongada reforça o tipo Dragon, e a descrição explora seu sopro congelante. Maior que Dewgong (1,7 m; 120,0 kg), mas relativamente esguio.
- **Review status:** **APROVADO pelo criador — nome, descrição e medidas. Aguardando documento inteiro para publicação.**
- **Nota de implementação futura:** usar `Name = Frost Plume` na espécie de ID `PRIAMALGONG`. Não renomear o ID interno sem análise de referências, scripts e saves. Não alterar arquivos do jogo agora.

### Campos PBS previstos (não aplicar ainda)

```ini
# [PRIAMALGONG]
Name = Frost Plume
Height = 2.3
Weight = 148.0
Pokedex = An ancient relative of Dewgong, it glided beneath polar ice on featherlike fins. Its icy breath froze seawater into sharp crystals, driving away even the fiercest predators.
```

---

## 16/59 — Spined Wyrm (antigo Primal Caterpie) — #1041

- **ID PBS atual:** `PRIMALCATERPIE` (**preservar até a implementação final**).
- **Nome definitivo aprovado pelo criador:** **Spined Wyrm** (antigo nome provisório: Primal Caterpie).
- **Category:** Past Paradox
- **Type:** Bug / Dragon
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Caterpie**.
- **Referência visual:** larva verde com segmentos robustos, espinhos/estruturas vermelhas pelo corpo e pela cabeça, olhos grandes e aparência dracônica.
- **Pokédex EN (aprovada):** An ancient relative of Caterpie, it charged larger predators with its dragonlike horns. Its armored segments and sharp spines made it a fearsome forest dweller.
- **Tradução PT-BR (aprovada):** Um antigo parente de Caterpie, ele investia contra predadores maiores usando seus chifres semelhantes aos de um dragão. Seus segmentos blindados e espinhos afiados faziam dele uma criatura temível das florestas.
- **Height / Altura (aprovada):** **1.2 m**
- **Weight / Peso (aprovado):** **24.0 kg**
- **Justificativa:** Spined refere-se aos espinhos dorsais; Wyrm, a um dragão serpentiforme, coerente com uma larva Bug / Dragon. O corpo robusto e segmentado é plausível como ancestral maior de Caterpie.
- **Review status:** **APROVADO pelo criador — nome, descrição e medidas. Aguardando conclusão do MD para publicação.**
- **Nota de implementação:** adicionar `Name = Spined Wyrm` e preservar o ID `PRIMALCATERPIE` até revisar todas as referências. Não alterar arquivos do jogo agora.

### Campos PBS previstos (não aplicar ainda)

```ini
# [PRIMALCATERPIE]
Name = Spined Wyrm
Height = 1.2
Weight = 24.0
Pokedex = An ancient relative of Caterpie, it charged larger predators with its dragonlike horns. Its armored segments and sharp spines made it a fearsome forest dweller.
```

---

## 17/59 — Tidal Tyrant (antigo Primal Drenaw) — #1042

- **ID PBS atual:** `PRIMALDRENAW` (**preservar até a implementação final**).
- **Nome definitivo aprovado pelo criador:** **Tidal Tyrant** (antigo nome provisório: Primal Drenaw).
- **Category:** Past Paradox
- **Type:** Water / Dragon
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Drednaw**.
- **Referência visual:** réptil marinho azul com mandíbula repleta de dentes, corpo alongado, garras e carapaça dourado-acastanhada de placas pontiagudas, lembrando um predador pré-histórico.
- **Pokédex EN (aprovada):** An ancient relative of Drednaw, it stalked prehistoric seas beneath a jagged, armored shell. Its crushing jaws could drag even massive prey into the depths.
- **Tradução PT-BR (aprovada):** Um antigo parente de Drednaw, ele rondava mares pré-históricos protegido por uma carapaça serrilhada e blindada. Suas mandíbulas esmagadoras podiam arrastar até presas enormes para as profundezas.
- **Height / Altura (aprovada):** **2.8 m**
- **Weight / Peso (aprovado):** **310.0 kg**
- **Justificativa:** Tidal significa relativo às marés e Tyrant significa tirano; o nome retrata um predador dominante de mares antigos. O tipo Water corresponde ao habitat aquático e Dragon à forma reptiliana primitiva. A carapaça espessa e o corpo maior que Drednaw (1,0 m; 115,5 kg) justificam as dimensões aprovadas.
- **Review status:** **APROVADO pelo criador — nome, descrição e medidas. Aguardando conclusão do MD para publicação.**
- **Nota de implementação:** usar `Name = Tidal Tyrant` na espécie de ID `PRIMALDRENAW` sem alterar o identificador interno. Não alterar arquivos do jogo agora.

### Campos PBS previstos (não aplicar ainda)

```ini
# [PRIMALDRENAW]
Name = Tidal Tyrant
Height = 2.8
Weight = 310.0
Pokedex = An ancient relative of Drednaw, it stalked prehistoric seas beneath a jagged, armored shell. Its crushing jaws could drag even massive prey into the depths.
```

---

## 18/59 — Witchcap Haze (antigo Primal Notic) — #1043

- **ID PBS atual:** `PRIMALNOTIC` (**não alterar nesta fase**).
- **Nome definitivo aprovado pelo criador:** **Witchcap Haze** (antigo Primal Notic).
- **Significado do nome:** *Witchcap* = chapéu de bruxa / chapéu encantado (o cogumelo de aspecto mágico); *Haze* = névoa (a nuvem de esporos venenosos).
- **Category:** Past Paradox
- **Type:** Fairy / Poison
- **Origem definida pelo criador:** Forma Paradoxo ancestral de **Shiinotic**.
- **Referência visual:** cogumelo de chapéu grande, violeta e luminoso, com pontos brilhantes rosados; haste pálida, raízes espalhadas e apêndices pendentes sob o chapéu. A arte shiny troca os tons roxos por amarelo e laranja. A ilustração foi enviada pelo criador como sprite sheet (frente normal/shiny e costas).
- **Pokédex EN (APROVADA):** An ancient relative of Shiinotic, it lures wanderers beneath its glowing cap. The spores it sheds cause vivid hallucinations before slowly numbing the body.
- **Tradução PT-BR (APROVADA):** Um antigo parente de Shiinotic, ele atrai viajantes para debaixo de seu chapéu luminoso. Os esporos que libera provocam alucinações vívidas antes de entorpecer lentamente o corpo.
- **Height / Altura (APROVADA):** **1.7 m** (Shiinotic: 1,0 m).
- **Weight / Peso (APROVADO):** **28.0 kg** (Shiinotic: 11,5 kg).
- **Justificativa aprovada:** O chapéu brilhante e o efeito hipnótico dos esporos combinam com Fairy; o entorpecimento causado pelos esporos explica Poison sem inventar novas habilidades de batalha. A aparência robusta e as raízes justificam maior estatura e massa que Shiinotic.
- **Condição no catálogo público:** **PENDENTE** (espécie ainda marcada como não concluída; sem stats e sem altura/peso publicados). A eventual aprovação do texto não altera esse estado automaticamente.
- **Review status:** **APROVADO pelo criador — nome, descrição e medidas. Aguardando conclusão do MD para publicação.**
- **Nota de implementação futura:** usar `Name = Witchcap Haze` na espécie de ID `PRIMALNOTIC`, preservando o ID interno e a situação de pendência até eventual implementação no jogo. Não publicar no GitHub até a revisão de toda a Pokédex.

### Campos PBS previstos (não aplicar ainda)

```ini
# [PRIMALNOTIC]
Name = Witchcap Haze
Height = 1.7
Weight = 28.0
Pokedex = An ancient relative of Shiinotic, it lures wanderers beneath its glowing cap. The spores it sheds cause vivid hallucinations before slowly numbing the body.
```

---

## 19/59 — Burrow Brawler (antigo Primal Punny) — #1044

- **ID PBS atual:** `PRIMALPUNNY` (**preservar até implementação final**).
- **Nome definitivo aprovado pelo criador:** **Burrow Brawler** (antigo Primal Punny).
- **Significado do nome:** *Burrow* = toca/túnel subterrâneo; *Brawler* = brigador/lutador corporal. Mantém o estilo de nomes Paradoxo com duas palavras.
- **Category:** Past Paradox
- **Type:** Ground / Fighting
- **Origem definida pelo criador:** Forma Paradoxo ancestral de **Lopunny**.
- **Referência visual:** o sprite específico não foi fornecido nesta rodada. A descrição autoral foi aprovada mesmo sem essa referência; conferir proporções na etapa de revisão final.
- **Pokédex EN (APROVADA):** An ancient relative of Lopunny, it carved deep burrows with its powerful hind legs. Its devastating kicks could crack the ground beneath charging predators.
- **Tradução PT-BR (APROVADA):** Um antigo parente de Lopunny, ele escavava tocas profundas com suas poderosas patas traseiras. Seus chutes devastadores podiam rachar o chão sob predadores que avançavam contra ele.
- **Height / Altura (APROVADA):** **1.6 m** (Lopunny original: 1,2 m).
- **Weight / Peso (APROVADO):** **62.0 kg** (Lopunny original: 33,3 kg).
- **Justificativa:** Ground representa o hábito de cavar tocas; Fighting, a força das patas e os chutes. As medidas refletem uma criatura maior e mais robusta, conforme proposta aprovada.
- **Review status:** **APROVADO pelo criador — nome, descrição e medidas. Aguardando conclusão do MD para publicação.**
- **Nota de implementação futura:** prever `Name = Burrow Brawler`, `Height = 1.6`, `Weight = 62.0` e `Pokedex` no ID `PRIMALPUNNY` sem renomear o ID interno nem editar o jogo agora.

### Campos PBS previstos (não aplicar ainda)

```ini
# [PRIMALPUNNY]
Name = Burrow Brawler
Height = 1.6
Weight = 62.0
Pokedex = An ancient relative of Lopunny, it carved deep burrows with its powerful hind legs. Its devastating kicks could crack the ground beneath charging predators.
```

---

## 20/59 — Canopy Titan (antigo Primal Tropical) — #1045

- **ID PBS atual:** `PRIMALTROPICAL` (**preservar até implementação final**).
- **Nome definitivo aprovado pelo criador:** **Canopy Titan**.
- **Significado do nome:** *Canopy* = copa de árvores / dossel florestal; *Titan* = gigante de grande porte, remetendo ao corpo de dinossauro do Tropius ancestral.
- **Category:** Past Paradox
- **Type:** Grass / Dragon
- **Origem definida pelo criador:** Forma Paradoxo ancestral de **Tropius** (referido informalmente como «Tropicus»).
- **Referência visual:** sprite enviado pelo criador: dinossauro de corpo robusto, pescoço alongado e folhas verdes muito grandes nas laterais e no topo, lembrando uma copa tropical. Há estruturas semelhantes a cachos de frutas sob a folhagem. Nenhuma função mecânica nova é pressuposta.
- **Pokédex EN (APROVADA):** An ancient relative of Tropius, it carried enormous leaflike wings above its back. Its long neck reached fruit growing far beyond the reach of other Pokémon.
- **Tradução PT-BR (APROVADA):** Um antigo parente de Tropius, ele carregava enormes asas semelhantes a folhas sobre as costas. Seu longo pescoço alcançava frutos que cresciam muito acima do alcance de outros Pokémon.
- **Height / Altura (APROVADA):** **3.2 m** (Tropius original: 2,0 m).
- **Weight / Peso (APROVADO):** **240.0 kg** (Tropius original: 100,0 kg).
- **Justificativa:** Grass aparece na folhagem exuberante e na dieta de frutas; Dragon reflete a silhueta de réptil saurópode ancestral. A altura considera o pescoço alongado e as folhas amplas; o peso representa um corpo consideravelmente maior que o de Tropius, sem impedir mobilidade. A descrição evita supor capacidades não mostradas na arte.
- **Review status:** **APROVADO pelo criador — nome, descrição e medidas. Aguardando conclusão do MD para publicação.**
- **Nota de implementação futura:** prever `Name = Canopy Titan`, `Height = 3.2`, `Weight = 240.0` e `Pokedex` no ID `PRIMALTROPICAL`; não alterar IDs, PBS, jogo ou arquivos do GitHub agora.


### Campos PBS previstos (não aplicar ainda)

```ini
# [PRIMALTROPICAL]
Name = Canopy Titan
Height = 3.2
Weight = 240.0
Pokedex = An ancient relative of Tropius, it carried enormous leaflike wings above its back. Its long neck reached fruit growing far beyond the reach of other Pokémon.
```

---

## 21/59 — Timber Maul (antigo Primalduurr) — #1046

- **ID PBS atual:** `PRIMALDUURR` (**não alterar nesta fase**).
- **Nome definitivo aprovado pelo criador:** **Timber Maul** (antigo Primalduurr).
- **Significado do nome:** *Timber* = madeira/tronco de árvore; *Maul* = marreta pesada ou ato de golpear brutalmente. Alude ao ancestral de Conkeldurr que usa um grande tronco como arma, antes do emprego de pilares de concreto.
- **Category:** Past Paradox
- **Type:** Fighting / Ground
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Conkeldurr**.
- **Referência visual:** sprite enviado pelo criador: humanoide volumoso de pelagem avermelhada e bege, juba/barba desgrenhadas, braços fortes e um tronco de árvore enorme apoiado à mão como um porrete. A arte sugere uma interpretação pré-histórica, em que o cimento de Conkeldurr é substituído por madeira bruta.
- **Pokédex EN (APROVADA):** An ancient relative of Conkeldurr, it uprooted whole trees to wield as clubs. Its mighty blows left deep fractures across the earth.
- **Tradução PT-BR (APROVADA):** Um antigo parente de Conkeldurr, ele arrancava árvores inteiras para usá-las como porretes. Seus golpes poderosos deixavam profundas rachaduras no solo.
- **Height / Altura (APROVADA):** **2.1 m** (Conkeldurr original: 1,4 m).
- **Weight / Peso (APROVADO):** **185.0 kg** (Conkeldurr original: 87,0 kg).
- **Justificativa:** o tronco é uma ferramenta de combate ancestral, coerente com Fighting. As pancadas que partem a terra remetem a Ground sem precisar inventar poderes especiais. Seu corpo musculoso e a estrutura robusta sugerem um aumento considerável de altura e massa em relação a Conkeldurr. As medidas propostas se referem ao Pokémon, não ao tronco que ele segura.
- **Review status:** **APROVADO pelo criador — nome, descrição, 2.1 m e 185.0 kg. Aguardando conclusão do documento para publicação.**
- **Nota de implementação futura:** prever `Name = Timber Maul`, `Height = 2.1`, `Weight = 185.0` e o texto `Pokedex` no ID `PRIMALDUURR`. O nome foi aprovado apenas no MD; preservar o ID interno `PRIMALDUURR` e não alterar o jogo nem a `main` por enquanto.

### Campos PBS previstos (não aplicar ainda)

```ini
# [PRIMALDUURR]
Name = Timber Maul
Height = 2.1
Weight = 185.0
Pokedex = An ancient relative of Conkeldurr, it uprooted whole trees to wield as clubs. Its mighty blows left deep fractures across the earth.
```


---

## 22/59 — Tempest Talon (antigo Primalgeot) — #1047

- **ID PBS atual:** `PRIMALGEOT` (**preservar; não renomear o ID nesta fase**).
- **Nome definitivo (APROVADO):** **Tempest Talon**.
- **Significado:** *Tempest* = tempestade, associada a ventos violentos; *Talon* = garra de ave de rapina, remetendo aos golpes físicos e ao tipo Fighting.
- **Category:** Past Paradox
- **Type:** Flying / Fighting
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Pidgeot**.
- **Arte:** o sprite definitivo ainda não foi fornecido nesta etapa. Não presumir detalhes específicos além da linhagem de Pidgeot, suas asas e garras.
- **Pokédex EN (APROVADA):** An ancient relative of Pidgeot, it challenged rivals with ferocious aerial dives. Its powerful talons could knock even large Pokémon out of the sky.
- **Tradução PT-BR (APROVADA):** Um antigo parente de Pidgeot, ele desafiava rivais com mergulhos aéreos ferozes. Suas garras poderosas eram capazes de derrubar até Pokémon grandes do céu.
- **Height / Altura (APROVADA):** **2.1 m** (Pidgeot original: 1,5 m).
- **Weight / Peso (APROVADO):** **61.0 kg** (Pidgeot original: 39,5 kg).
- **Justificativa aprovada:** Flying representa a capacidade de voo e os mergulhos aéreos; Fighting representa combates corporais com garras e investidas. O nome lembra um predador de tempestades sem pressupor poderes elétricos ou novas habilidades. As medidas sugerem uma ave ancestral maior, mas ainda apta a voar. O sprite não foi enviado nesta etapa.
- **Review status:** **APROVADO pelo criador — nome, descrição, 2.1 m e 61.0 kg. Aguardando conclusão do documento para publicação.**
- **Nota de implementação futura:** aprovado o uso de `Name = Tempest Talon`, `Height = 2.1`, `Weight = 61.0` e `Pokedex` na espécie de ID `PRIMALGEOT`. Não renomear o ID interno. Nada foi enviado ao GitHub.

### Campos PBS previstos (não aplicar ainda)

```ini
# [PRIMALGEOT]
Name = Tempest Talon
Height = 2.1
Weight = 61.0
Pokedex = An ancient relative of Pidgeot, it challenged rivals with ferocious aerial dives. Its powerful talons could knock even large Pokémon out of the sky.
```

---

## 23/59 — Cinder Coil (antigo Primalkorch) — #1048

- **ID PBS atual:** `PRIMALKORCH` (**preservar; não renomear o ID nesta fase**).
- **Nome aprovado pelo criador:** **Cinder Coil**.
- **Significado:** *Cinder* = brasa ou cinza incandescente; *Coil* = espiral/corpo enrolado. O nome se refere à silhueta de centopeia enrolada e aos segmentos laranja-avermelhados luminosos, sem alterar os tipos Bug / Dragon para Fire.
- **Category:** Past Paradox
- **Type:** Bug / Dragon
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Centiskorch**.
- **Referência visual:** sprite enviado pelo criador, com corpo comprido de múltiplos segmentos em espiral, carapaça escura e pontiaguda, placas em tons laranja incandescente, chifres/garras dianteiras e silhueta dracônica. A interpretação de calor vulcânico é uma **proposta criativa** a ser aprovada; a imagem não prova seu habitat.
- **Pokédex EN (APROVADA):** An ancient relative of Centiskorch, it guarded volcanic tunnels with its armored coils. Its glowing plates radiated enough heat to drive away predators.
- **Tradução PT-BR (APROVADA):** Um antigo parente de Centiskorch, ele protegia túneis vulcânicos com seu corpo blindado e enrolado. Suas placas brilhantes irradiavam calor suficiente para afastar predadores.
- **Height / Altura (APROVADA):** **4.2 m** (Centiskorch original: 3,0 m; comprimento total do corpo desenrolado).
- **Weight / Peso (APROVADO):** **180.0 kg** (Centiskorch original: 120,0 kg).
- **Justificativa provisória:** Bug conserva a anatomia de centopeia segmentada; Dragon corresponde aos chifres ameaçadores, ao porte ancestral e à aparência de um dragão-serpente. As placas incandescentes e o corpo blindado sugerem adaptação a calor intenso, sem requerer o tipo Fire. As medidas foram estimadas considerando a criatura desenrolada, não apenas a pose curvada do sprite.
- **Review status:** **APROVADO pelo criador — nome, descrição, altura e peso aprovados. Aguardar conclusão de todo o MD antes de qualquer publicação.**
- **Nota de implementação futura:** usar `Name = Cinder Coil`, `Height = 4.2`, `Weight = 180.0` e `Pokedex` na espécie de ID `PRIMALKORCH`, somente após finalizar e aprovar todo o MD. Nada foi enviado ao GitHub.

### Campos PBS previstos (não aplicar ainda)

```ini
# [PRIMALKORCH]
Name = Cinder Coil
Height = 4.2
Weight = 180.0
Pokedex = An ancient relative of Centiskorch, it guarded volcanic tunnels with its armored coils. Its glowing plates radiated enough heat to drive away predators.
```

---

## 24/59 — Rime Shroud (antigo Primalmoth) — #1049

- **ID PBS atual:** `PRIMALMOTH` (**preservar; não renomear o ID nesta fase**).
- **Nome definitivo aprovado pelo criador:** **Rime Shroud** (antigo Primalmoth).
- **Significado:** *Rime* = camada de geada que se forma sobre superfícies; *Shroud* = manto ou véu, referindo-se à névoa de escamas geladas que recobre a mariposa e sua região de voo.
- **Category:** Past Paradox
- **Type:** Bug / Ice
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Venomoth**.
- **Referência visual:** ainda não foi enviado um sprite específico de `PRIMALMOTH` nesta etapa. A ideia de escamas geladas sobre as asas é uma proposta criativa inspirada no Pokémon de origem e nos tipos Bug / Ice; ajustar o texto e as medidas caso a arte apresente outra anatomia.
- **Pokédex EN (APROVADA):** An ancient relative of Venomoth, it drifted through frozen forests, scattering icy scales that numbed anything they touched. Its powder lingered in the frigid air for hours.
- **Tradução PT-BR (APROVADA):** Um antigo parente de Venomoth, ele flutuava por florestas congeladas, espalhando escamas geladas que entorpeciam tudo o que tocavam. Seu pó permanecia no ar gélido por horas.
- **Height / Altura (APROVADA):** **1.8 m** (Venomoth original: 1,5 m).
- **Weight / Peso (APROVADO):** **21.0 kg** (Venomoth original: 12,5 kg).
- **Justificativa provisória:** Bug mantém o corpo de mariposa; Ice se manifesta por escamas congelantes e habitat frio, reinterpretando o pó liberado por Venomoth sem necessariamente conservá-lo como veneno. Uma forma ancestral de voo leve não precisa ser excessivamente pesada. Nome, descrição, altura e peso foram aprovados pelo criador; o sprite não foi fornecido nesta rodada.
- **Review status:** **APROVADO pelo criador — nome, descrição, altura e peso aprovados; não aplicar até o fim do MD.**
- **Nota de implementação futura:** aprovado usar `Name = Rime Shroud`, `Height = 1.8`, `Weight = 21.0` e `Pokedex` na espécie com ID `PRIMALMOTH`. Não aplicar ainda ao jogo nem publicar no GitHub.

### Campos PBS previstos (não aplicar ainda)

```ini
# [PRIMALMOTH]
Name = Rime Shroud
Height = 1.8
Weight = 21.0
Pokedex = An ancient relative of Venomoth, it drifted through frozen forests, scattering icy scales that numbed anything they touched. Its powder lingered in the frigid air for hours.
```

---

## 25/59 — Tar Chasm (antigo Primalmuk) — #1050

- **ID PBS atual:** `PRIMALMUK` (**preservar; não renomear o ID nesta fase**).
- **Nome aprovado:** **Tar Chasm** (antigo Primalmuk).
- **Significado:** *Tar* = piche/betume natural, remetendo a poços viscosos primordiais; *Chasm* = abismo/fenda profunda, referindo-se à boca enorme e escura da criatura.
- **Category:** Past Paradox
- **Type:** Poison / Ground
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Muk**.
- **Referência visual:** sprite enviado pelo criador, mostrando um corpo largo e amontoado de lodo roxo, abertura bucal enorme e escura, dentes aparentes e estruturas duras semelhantes a ossos ou detritos mineralizados emergindo da massa. Associar o habitat a poços naturais de piche é uma interpretação autoral proposta, não uma informação confirmada no jogo.
- **Pokédex EN (APROVADA):** An ancient relative of Muk, it lurked in primeval tar pits, its sludge thick with bones and sediment. Prey pulled into its gaping maw rarely escaped.
- **Tradução PT-BR (APROVADA):** Um antigo parente de Muk, ele se escondia em poços de piche primordiais, com sua lama impregnada de ossos e sedimentos. Presas arrastadas para sua boca escancarada raramente escapavam.
- **Height / Altura (APROVADA):** **2.0 m** (Muk original: 1,2 m).
- **Weight / Peso (APROVADO):** **180.0 kg** (Muk original: 30,0 kg).
- **Justificativa:** Poison corresponde ao lodo tóxico e Ground aos sedimentos e ao piche natural onde se esconde. A boca escancarada e as estruturas ósseas do sprite sugerem um predador de emboscada capaz de engolir presas inteiras. O peso elevado resulta de um corpo ancestral mais denso, carregado de lama, detritos e minerais. Aprovadas pelo criador.
- **Review status:** **APROVADO — nome, descrição, altura e peso aprovados pelo criador.**
- **Nota de implementação futura:** aprovado usar `Name = Tar Chasm`, `Height = 2.0`, `Weight = 180.0` e `Pokedex` no ID `PRIMALMUK`, sem alterar o ID interno. Não aplicar ainda ao jogo nem publicar no GitHub.

### Campos PBS previstos (não aplicar ainda)

```ini
# [PRIMALMUK]
Name = Tar Chasm
Height = 2.0
Weight = 180.0
Pokedex = An ancient relative of Muk, it lurked in primeval tar pits, its sludge thick with bones and sediment. Prey pulled into its gaping maw rarely escaped.
```

---

## 26/59 — Venom Crown (antigo Primalseaking) — #1051

- **ID PBS atual:** `PRIMALSEAKING` (**preservar; não renomear o ID nesta fase**).
- **Nome aprovado pelo criador:** **Venom Crown**.
- **Significado:** *Venom* = veneno inoculado por ferrões ou espinhos; *Crown* = coroa, alusão tanto à aparência de um leque de espinhos como ao nome do Pokémon original, **Seaking**.
- **Category:** Past Paradox
- **Type:** Water / Poison
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Seaking**.
- **Referência visual:** sprite enviado pelo criador, com corpo vermelho-alaranjado, grande olho, chifre proeminente, espinhos claros e nadadeiras brancas amplas com marcas pretas, semelhantes a um leque de peixe-leão. A propriedade venenosa dos espinhos é um conceito de Pokédex proposto para justificar Poison, ainda não validado no jogo.
- **Pokédex EN (APROVADA):** An ancient relative of Seaking, it spread its venomous fins like a crown to warn predators. A single prick from its spines could paralyze even larger foes.
- **Tradução PT-BR (APROVADA):** Um antigo parente de Seaking, ele abria suas nadadeiras venenosas como uma coroa para alertar predadores. Uma única picada de seus espinhos podia paralisar até adversários maiores.
- **Height / Altura (APROVADA):** **1.8 m** (Seaking original: 1,3 m).
- **Weight / Peso (APROVADO):** **67.0 kg** (Seaking original: 39,0 kg).
- **Justificativa aprovada:** Water preserva o habitat aquático de Seaking; Poison é representado pelos espinhos defensivos de aparência venenosa. O nome alude à coroa de nadadeiras e à linhagem do Seaking. O corpo maior e musculoso justifica as medidas, apesar da estrutura leve das barbatanas. Nome, descrição e medidas aprovados pelo criador.
- **Review status:** **APROVADO pelo criador — nome, descrição, altura e peso aprovados.**
- **Nota de implementação futura:** aprovado usar `Name = Venom Crown`, `Height = 1.8`, `Weight = 67.0` e `Pokedex` no ID `PRIMALSEAKING`, sem alterar o ID interno. Não aplicar ainda ao jogo nem publicar no GitHub.

### Campos PBS previstos (não aplicar ainda)

```ini
# [PRIMALSEAKING]
Name = Venom Crown
Height = 1.8
Weight = 67.0
Pokedex = An ancient relative of Seaking, it spread its venomous fins like a crown to warn predators. A single prick from its spines could paralyze even larger foes.
```

---

## 27/59 — Spore Rampart (antigo Primalsect) — #1052

- **ID PBS atual:** `PRIMALSECT` (**preservar; não renomear o ID nesta fase**).
- **Nome aprovado pelo criador:** **Spore Rampart**.
- **Significado:** *Spore* = esporo, em referência ao fungo que domina Parasect; *Rampart* = muralha/fortificação, em referência à estrutura rochosa e espinhosa que protege o corpo.
- **Category:** Past Paradox
- **Type:** Grass / Rock
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Parasect**.
- **Referência visual:** sprite enviado pelo criador com corpo avermelhado, grandes pinças, cogumelo vermelho volumoso e espinhos claros e pontiagudos ao longo do dorso. A ideia de placas fúngicas endurecidas por minerais é uma **interpretação criativa aprovada para a Pokédex**, não um dado já confirmado do jogo.
- **Pokédex EN (APROVADA):** An ancient relative of Parasect, it grew jagged, stone-hard fungal plates across its back. It used its massive claws to defend the spore colonies beneath its shell.
- **Tradução PT-BR (APROVADA):** Um antigo parente de Parasect, ele desenvolveu placas fúngicas serrilhadas e duras como pedra sobre as costas. Usava suas enormes pinças para proteger as colônias de esporos sob sua carapaça.
- **Height / Altura (APROVADA):** **1.7 m** (Parasect original: 1,0 m).
- **Weight / Peso (APROVADO):** **132.0 kg** (Parasect original: 29,5 kg).
- **Justificativa aprovada:** Grass se associa ao fungo e seus esporos; Rock representa a carapaça endurecida e mineralizada. A Defesa 140 e o Ataque 135 combinam com a proteção rochosa e as pinças robustas. As dimensões foram escolhidas para uma forma ancestral maior e muito mais pesada que Parasect, sem exagerar seu porte; aprovado pelo criador.
- **Review status:** **APROVADO — nome, descrição, altura e peso aprovados pelo criador.**
- **Nota de implementação futura:** aprovado usar `Name = Spore Rampart`, `Height = 1.7`, `Weight = 132.0` e `Pokedex` no ID `PRIMALSECT`, sem mudar o ID interno. Não aplicar ainda ao jogo nem publicar no GitHub.

### Campos PBS previstos (não aplicar ainda)

```ini
# [PRIMALSECT]
Name = Spore Rampart
Height = 1.7
Weight = 132.0
Pokedex = An ancient relative of Parasect, it grew jagged, stone-hard fungal plates across its back. It used its massive claws to defend the spore colonies beneath its shell.
```

---

## 28/59 — Venom Scythe (antigo Primalviper) — #1053

- **ID PBS atual:** `PRIMALVIPER` (**preservar; não renomear o ID nesta fase**).
- **Nome aprovado pelo criador:** **Venom Scythe** (antigo Primalviper).
- **Significado:** *Venom* = veneno, em referência à linhagem de Seviper e seu tipo Poison; *Scythe* = foice, em referência à extremidade da cauda que parece uma lâmina curva.
- **Category:** Past Paradox
- **Type:** Poison / Dragon
- **Origem definida pelo criador:** Forma Paradoxo do passado de **Seviper**.
- **Referência visual:** sprite enviado pelo criador com corpo serpentiforme escuro e musculoso, marcas douradas e avermelhadas, crista angular na cabeça e uma grande lâmina rubra na ponta da cauda. A ideia de uma cauda revestida de veneno é uma **proposta criativa**, ainda não validada no jogo.
- **Pokédex EN (APROVADA):** An ancient relative of Seviper, it hunted through primeval jungles using its scythe-shaped tail. Venom seeping from the blade could weaken even towering predators.
- **Tradução PT-BR (APROVADA):** Um antigo parente de Seviper, ele caçava nas selvas primitivas usando sua cauda em forma de foice. O veneno que escorria da lâmina podia enfraquecer até predadores gigantescos.
- **Height / Altura (APROVADA):** **4.2 m** — considerando o comprimento do corpo estendido, por ser uma serpente (Seviper original: 2,7 m).
- **Weight / Peso (APROVADO):** **92.0 kg** (Seviper original: 52,5 kg).
- **Justificativa:** Poison corresponde à toxina presente na cauda; Dragon corresponde ao corpo maior, à cabeça angulosa e às escamas de aparência dracônica. A lâmina vermelha e a postura enrolada do sprite sugerem um predador ancestral de emboscada. O aumento de comprimento e massa reflete um corpo mais musculoso, sem afirmar uma anatomia que não aparece na arte.
- **Review status:** **APROVADO pelo criador — nome, texto, altura e peso. Aguardar conclusão do MD.**
- **Nota de implementação futura:** usar `Name = Venom Scythe`, `Height = 4.2`, `Weight = 92.0` e `Pokedex` no ID `PRIMALVIPER`, sem mudar o ID interno. Não aplicar ainda ao jogo nem publicar no GitHub.

### Campos PBS previstos (não aplicar ainda)

```ini
# [PRIMALVIPER]
Name = Venom Scythe
Height = 4.2
Weight = 92.0
Pokedex = An ancient relative of Seviper, it hunted through primeval jungles using its scythe-shaped tail. Venom seeping from the blade could weaken even towering predators.
```

---

## 29/59 — Primatizer — #1054

- **ID PBS:** `PRIMATIZER` (**preservar**).
- **Nome:** **Primatizer** (**manter nome existente por instrução do criador**).
- **Category:** Past Paradox
- **Type:** Water / Rock
- **Origem:** **aguardando confirmação do criador**. O sprite lembra um crustáceo ancestral com uma grande garra/canhão semelhante ao de Clawitzer; isso é uma hipótese visual, **não** uma confirmação de parentesco.
- **Referência visual:** sprite enviado pelo criador em 31/10/2026: corpo azul, antenas longas amarelo-douradas, segmentos blindados com pontas bege, uma grande estrutura frontal em forma de garra/canhão e patas articuladas.
- **Pokédex EN (APROVADA):** Its massive, stone-plated claw fires bursts of pressurized water strong enough to shatter coral. It ambushes prey among ancient reefs.
- **Tradução PT-BR (APROVADA):** Sua enorme garra revestida de placas rochosas dispara rajadas de água pressurizada fortes o bastante para despedaçar corais. Ele embosca suas presas entre recifes ancestrais.
- **Height / Altura (APROVADA):** **2.2 m** — comprimento do corpo incluindo a grande estrutura frontal.
- **Weight / Peso (APROVADO):** **135.0 kg** — massa sugerida para carapaça mineral e garra robusta.
- **Justificativa aprovada:** tipo Water pelo disparo de água; tipo Rock pela carapaça com placas minerais. Os detalhes da anatomia e o ataque de água pressurizada são elementos ficcionais aprovados da descrição. **O parentesco de Primatizer com Clawitzer continua não confirmado pelo criador**; não o registrar como fato na Pokédex.
- **Review status:** **APROVADO pelo criador — descrição, 2.2 m e 135.0 kg; nome Primatizer mantido. Aguardar a conclusão de todo o MD antes de publicar.**
- **Nota de implementação futura:** apenas `Height`, `Weight` e `Pokedex`, sem mudança do campo `Name` ou do ID interno. Não aplicar ainda ao jogo nem publicar no GitHub.

### Campos PBS previstos (não aplicar ainda)

```ini
# [PRIMATIZER]
Height = 2.2
Weight = 135.0
Pokedex = Its massive, stone-plated claw fires bursts of pressurized water strong enough to shatter coral. It ambushes prey among ancient reefs.
```

---

## 30/59 — Rampage Horn — #1055

- **ID PBS:** `RAMPAGEHORN` (**preservar**).
- **Nome:** **Rampage Horn**, mantido conforme instrução do criador de não inventar novos nomes.
- **Category:** Past Paradox
- **Type:** Rock / Dragon
- **Origem provável (aguardando confirmação):** a arte parece retratar um ancestral de **Rhydon**. Não considerar confirmada até o criador dizer.
- **Referência visual:** sprite enviado pelo criador em 31/10/2026: criatura cinzenta robusta, com um enorme chifre frontal marfim, olhos vermelhos, braços fortes, garras, espinhos e placas de pedra pelo corpo e pela cauda.
- **Pokédex EN (PROPOSTA; ainda não aprovada):** An ancient relative of Rhydon, it charged across rugged mountains, smashing boulders with its massive horn. Thick stone plates shielded it from rival predators.
- **Tradução PT-BR (PROPOSTA):** Um antigo parente de Rhydon, ele avançava por montanhas acidentadas, despedaçando rochas com seu enorme chifre. Grossas placas de pedra o protegiam de predadores rivais.
- **Height / Altura (PROPOSTA):** **2.5 m** (Rhydon original: 1,9 m).
- **Weight / Peso (PROPOSTO):** **340.0 kg** (Rhydon original: 120,0 kg).
- **Justificativa provisória:** Rock corresponde à armadura mineral, chifre e corpo coberto de placas; Dragon reforça a silhueta reptiliana e a aparência de monstro ancestral. A criatura é maior e mais pesada que Rhydon devido às placas e à estrutura corporal robusta. O parentesco precisa ser confirmado.
- **Review status:** **EM REVISÃO — nome mantido; origem, descrição, altura e peso aguardam aprovação.**
- **Nota de implementação futura:** manter o ID interno e `Name = Rampage Horn`; propor apenas `Height`, `Weight` e `Pokedex`. Não aplicar ao jogo nem publicar no GitHub.

### Campos PBS previstos (não aplicar ainda)

```ini
# [RAMPAGEHORN]
Height = 2.5
Weight = 340.0
Pokedex = An ancient relative of Rhydon, it charged across rugged mountains, smashing boulders with its massive horn. Thick stone plates shielded it from rival predators.
```

---

## 31/59 — Ravenous Crest — #1056

- **ID PBS:** `RAVENOUSCREST` (**preservar**).
- **Nome:** **Ravenous Crest** (não propor nome novo).
- **Category:** Past Paradox
- **Type:** Fighting
- **Origem provável (aguardando confirmação):** a arte indica uma forma Paradoxo do passado de **Vigoroth**, pelo corpo peludo branco, crista vermelha, braços longos e garras negras. O criador ainda não confirmou essa relação.
- **Referência visual:** sprite enviado pelo criador em 31/10/2026: criatura de quatro apoios com pelagem branca, crista dorsal avermelhada, boca aberta, grandes braços e enormes garras escuras.
- **Pokédex EN (PROPOSTA; não aprovada):** An ancient relative of Vigoroth, it roamed primeval forests on all fours. Its crimson crest rose as it charged, tearing through tree trunks with its massive claws.
- **Tradução PT-BR (PROPOSTA):** Um antigo parente de Vigoroth, ele percorria as florestas primitivas sobre quatro patas. Sua crista carmesim se eriçava quando investia, despedaçando troncos de árvores com suas enormes garras.
- **Height / Altura (PROPOSTA):** **1.9 m** (Vigoroth original: 1,4 m).
- **Weight / Peso (PROPOSTO):** **96.0 kg** (Vigoroth original: 46,5 kg).
- **Justificativa provisória:** Fighting relaciona-se às investidas e à força dos braços longos; a crista vermelha preserva a identidade de Vigoroth e o corpo volumoso e musculoso justifica o aumento de massa. A aparência e as medidas são propostas autorais, aguardando aprovação.
- **Review status:** **EM REVISÃO — confirmar origem, descrição, altura e peso.**
- **Nota de implementação futura:** manter o ID interno `RAVENOUSCREST` e o nome exibido `Ravenous Crest`; não aplicar ao jogo nem publicar no GitHub.

### Campos PBS previstos (não aplicar ainda)

```ini
# [RAVENOUSCREST]
Height = 1.9
Weight = 96.0
Pokedex = An ancient relative of Vigoroth, it roamed primeval forests on all fours. Its crimson crest rose as it charged, tearing through tree trunks with its massive claws.
```

---

## 32/59 — Razor Carapace — #1057

- **ID PBS:** `RAZORCARAPACE` (**preservar**).
- **Nome:** **Razor Carapace**, mantido conforme instrução do criador de não inventar novos nomes.
- **Category:** Past Paradox
- **Type:** Steel / Dragon
- **Origem provável (aguardando confirmação):** pela silhueta de quadrúpede blindado, cabeça e focinho, a arte lembra uma forma Paradoxo ancestral de **Lairon**. Isso ainda é **hipótese**, não parentesco confirmado.
- **Referência visual:** sprite enviado pelo criador em 31/10/2026: quadrúpede cinzento de corpo alongado, placas metálicas angulares e serrilhadas, espinhos claros nas costas, patas robustas e olhos vermelhos.
- **Pokédex EN (PROPOSTA; ainda não aprovada):** An ancient relative of Lairon, its razor-edged armor hardened as it consumed iron-rich stone. It charged headfirst at threats, leaving deep gouges in cliffsides.
- **Tradução PT-BR (PROPOSTA):** Um antigo parente de Lairon, sua armadura de lâminas afiadas endurecia à medida que consumia rochas ricas em ferro. Ele investia de cabeça contra ameaças, deixando sulcos profundos nas encostas rochosas.
- **Height / Altura (PROPOSTA):** **1.7 m** (Lairon original: 0,9 m).
- **Weight / Peso (PROPOSTO):** **285.0 kg** (Lairon original: 120,0 kg).
- **Justificativa provisória:** tipo Steel pela blindagem metálica e alimentação com minério; Dragon pela anatomia reptiliana e predatória. A defesa muito alta (200 no catálogo) combina com placas blindadas. Altura e peso propostos para um animal maior e muito mais robusto que Lairon, sujeito à revisão do criador. O hábito de comer rochas e provocar sulcos é criação de lore, não mecânica confirmada.
- **Review status:** **EM REVISÃO — confirmar origem de Lairon, descrição, altura e peso.**
- **Nota de implementação futura:** preservar o nome e ID `RAZORCARAPACE`; preencher apenas `Height`, `Weight` e `Pokedex` depois da aprovação e somente quando o MD inteiro estiver concluído. Nada aplicar ao jogo ou enviar ao GitHub agora.

### Campos PBS previstos (não aplicar ainda)
```ini
# [RAZORCARAPACE]
Height = 1.7
Weight = 285.0
Pokedex = An ancient relative of Lairon, its razor-edged armor hardened as it consumed iron-rich stone. It charged headfirst at threats, leaving deep gouges in cliffsides.
```

---

## 33/59 — Savege Jowl — #1058

- **ID PBS:** `SAVEGEJOWL`
- **Category:** Past Paradox
- **Type:** Fairy / Dark
- **Nome:** Savege Jowl (mantido conforme o catálogo; não corrigir grafia sem pedido do criador).
- **Origem provável, aguardando confirmação:** forma Paradoxo do passado de **Granbull**.
- **Arte enviada pelo criador:** corpo roxo-rosado, grandes patas dianteiras, mandíbula larga, grandes presas claras e pelagem clara no peito/pescoço.
- **Pokédex EN (PROPOSTA):** An ancient relative of Granbull, it guarded its pack with terrifying ferocity. Its massive jaws and tusklike fangs drove away even larger predators.
- **Tradução PT-BR (PROPOSTA):** Um antigo parente de Granbull, ele protegia sua matilha com uma ferocidade assustadora. Suas mandíbulas enormes e presas semelhantes a dentes de sabre afastavam até predadores maiores.
- **Height / Altura (PROPOSTA):** **1.8 m** (Granbull original: 1.4 m).
- **Weight / Peso (PROPOSTA):** **104.0 kg** (Granbull original: 48.7 kg).
- **Justificativa:** Fairy preserva a identidade da linhagem Granbull e a lealdade protetora à matilha; Dark reforça sua intimidação feroz. A postura baixa, os braços robustos, as presas e a mandíbula larga inspiram uma versão ancestral mais pesada e agressiva. Parentesco e medidas aguardam aprovação do criador.
- **Review status:** **EM REVISÃO — confirmar Granbull, descrição, altura e peso. NÃO aplicar ao jogo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [SAVEGEJOWL]
Height = 1.8
Weight = 104.0
Pokedex = An ancient relative of Granbull, it guarded its pack with terrifying ferocity. Its massive jaws and tusklike fangs drove away even larger predators.
```

---

## 34/59 — Scorch Mane — #1059

- **ID PBS:** `SCORCHMANE`
- **Category:** Past Paradox
- **Type (catálogo):** Fire / Electric
- **Nome:** Scorch Mane (mantido).
- **Origem confirmada pelo criador:** forma Paradoxo do passado de **Rapidash** (a proposta foi aprovada).
- **Arte enviada pelo criador:** cavalo ancestral amarelo-claro, enorme crina de chamas amarelas, laranjas e vermelhas.
- **Pokédex EN (APROVADA):** An ancient relative of Rapidash, it galloped across volcanic plains with a mane crackling with electricity. Its blazing hooves left trails of fire wherever it ran.
- **Tradução PT-BR (APROVADA):** Um antigo parente de Rapidash, ele galopava pelas planícies vulcânicas com uma crina que crepitava de eletricidade. Seus cascos incandescentes deixavam rastros de fogo por onde passava.
- **Height / Altura (APROVADA):** **2.1 m** (Rapidash original: 1.7 m).
- **Weight / Peso (APROVADO):** **140.0 kg** (Rapidash original: 95.0 kg).
- **Justificativa:** Fire representa as chamas da crina e dos cascos; Electric é justificado pelas descargas enquanto galopa; porte e musculatura maiores que Rapidash.
- **Review status:** **APROVADO pelo criador — nenhuma publicação até concluir todo o MD.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [SCORCHMANE]
Height = 2.1
Weight = 140.0
Pokedex = An ancient relative of Rapidash, it galloped across volcanic plains with a mane crackling with electricity. Its blazing hooves left trails of fire wherever it ran.
```

---

## 35/59 — Scoria Shell — #1060

- **ID PBS:** `SCORIASHELL`
- **Category:** Past Paradox
- **Type no catálogo consultado:** **Fire / Steel**.
- **Atenção à divergência:** a apresentação aprovada anteriormente dizia **Fire / Rock**, coerente com a arte vulcânica, mas o catálogo do Blue consultado registra **Fire / Steel**. **Não corrigir nem trocar tipos sem decisão explícita do criador**. A descrição abaixo permanece aprovada tal como apresentada; o tipo deve ser conferido na revisão final.
- **Nome:** Scoria Shell (mantido).
- **Origem aceita pelo criador ao aprovar a proposta:** forma Paradoxo ancestral de **Magcargo**.
- **Arte enviada pelo criador:** lesma de magma exposto e uma grande carapaça escura, com fendas incandescentes e chamas no topo.
- **Pokédex EN (APROVADA):** An ancient relative of Magcargo, it crawled through volcanic craters with a shell of hardened scoria. Molten rock constantly seeped from the cracks in its body, scorching everything in its path.
- **Tradução PT-BR (APROVADA):** Um antigo parente de Magcargo, ele rastejava por crateras vulcânicas com uma concha de escória endurecida. Rocha derretida escorria constantemente das fendas de seu corpo, queimando tudo em seu caminho.
- **Height / Altura (APROVADA):** **1.4 m** (Magcargo original: 0.8 m).
- **Weight / Peso (APROVADO):** **190.0 kg** (Magcargo original: 55.0 kg).
- **Justificativa:** seu corpo de magma e concha vulcânica densa sustentam a descrição e a massa elevada. Verificar a tipagem antes de aplicar ao jogo: Fire / Steel no catálogo, Fire / Rock na proposta aprovada.
- **Review status:** **APROVADO pelo criador — descrição, altura e peso. Tipagem a conferir, mas não bloqueia o registro do texto.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [SCORIASHELL]
Height = 1.4
Weight = 190.0
Pokedex = An ancient relative of Magcargo, it crawled through volcanic craters with a shell of hardened scoria. Molten rock constantly seeped from the cracks in its body, scorching everything in its path.
```

---

## 36/59 — Thorn Bastion — #1061

- **ID PBS:** `THORNBASTION`
- **Category:** Past Paradox (Paradoxo do passado)
- **Type:** Ground / Rock
- **Nome:** Thorn Bastion (mantido, conforme instrução do criador).
- **Origem visual provável, aguardando confirmação:** forma Paradoxo ancestral de **Sandslash**.
- **Arte enviada pelo criador:** criatura quadrúpede de carapaça dourada com enormes espinhos rochosos, garras longas e afiadas, olhos avermelhados e cauda terminando em uma estrutura espinhosa.
- **Conceito:** fortaleza viva das regiões áridas pré-históricas, especializada em escavar terrenos extremamente duros e resistir às investidas de grandes predadores.
- **Pokédex EN (PROPOSTA):** An ancient relative of Sandslash, it dug deep trenches with its massive claws. When threatened, it braced its spiked armor against charging predators.
- **Tradução PT-BR (PROPOSTA):** Um antigo parente de Sandslash, ele escavava trincheiras profundas com suas garras enormes. Quando ameaçado, firmava sua armadura espinhosa para resistir às investidas de predadores.
- **Height / Altura (PROPOSTA):** **1.6 m** (Sandslash original: 1.0 m).
- **Weight / Peso (PROPOSTO):** **145.0 kg** (Sandslash original: 29.5 kg).

### Justificativa da proposta

- **Ground:** suas garras gigantescas são especializadas em escavação, permitindo abrir caminhos em solos compactados.
- **Rock:** a carapaça tem grandes placas mineralizadas, formando uma proteção extremamente resistente.
- **Defense 175:** a alta Defesa é coerente com uma criatura capaz de suportar investidas violentas.
- **Cauda espinhosa:** constitui proteção adicional contra inimigos que tentam atacá-lo por trás.
- **Peso de 145.0 kg:** a carapaça mineral e o corpo robusto justificam uma massa muito superior à de Sandslash.
- **Review status:** **EM REVISÃO — aguarda aprovação explícita da origem proposta, descrição e medidas pelo criador. NÃO aplicar ao jogo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [THORNBASTION]
Height = 1.6
Weight = 145.0
Pokedex = An ancient relative of Sandslash, it dug deep trenches with its massive claws. When threatened, it braced its spiked armor against charging predators.
```

---

## 37/59 — Titan Baleen — #1062

- **ID PBS:** `TITANBALEEN`
- **Category:** Past Paradox (Paradoxo do passado)
- **Type:** Water / Steel
- **Nome:** Titan Baleen (mantido, conforme instrução do criador).
- **Origem confirmada pelo criador:** forma Paradoxo ancestral de **Wailord**.
- **Arte enviada pelo criador:** corpo de baleia azul com ventre claro e sulcado, carapaça com placas protetoras, espinhos dorsais e nadadeiras robustas com projeções pontiagudas.
- **Conceito:** leviatã blindado dos oceanos pré-históricos; uma criatura colossal que filtrava grandes cardumes com barbatanas bucais resistentes e se protegia com uma armadura natural rica em metais.
- **Pokédex EN (APROVADA):** An ancient relative of Wailord, it crossed prehistoric seas in metallic armor. Its tough baleen strained whole shoals of fish, while its dorsal spines repelled predators.
- **Tradução PT-BR (APROVADA):** Um antigo parente de Wailord, ele atravessava os mares pré-históricos protegido por uma armadura metálica. Suas barbatanas bucais resistentes filtravam cardumes inteiros de peixes, enquanto seus espinhos dorsais afastavam predadores.
- **Height / Altura (APROVADA):** **17.0 m** (Wailord original: 14.5 m).
- **Weight / Peso (APROVADO):** **1250.0 kg** (Wailord original: 398.0 kg).

### Justificativa da descrição e das medidas

- **Water:** preserva a natureza oceânica e a alimentação por filtração da linhagem Wailord.
- **Steel:** placas protetoras e espinhos possuem mineralização metálica, formando uma blindagem natural.
- **Espinhos dorsais:** oferecem proteção contra predadores capazes de atacar a parte superior de seu corpo.
- **Nadadeiras robustas:** ajudam a movimentar o grande corpo e a enfrentar correntes oceânicas.
- **Altura de 17.0 m:** representa o porte colossal de uma forma ancestral maior do que Wailord.
- **Peso de 1250.0 kg:** é uma proposta proporcional ao universo Pokémon, considerando a blindagem metálica e maior robustez corporal. Não corresponde à massa de uma baleia real deste comprimento.
- **Review status:** **APROVADO pelo criador — descrição, altura de 17.0 m e peso de 1250.0 kg. Aguardar conclusão de todo o MD antes de aplicar ao jogo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [TITANBALEEN]
Height = 17.0
Weight = 1250.0
Pokedex = An ancient relative of Wailord, it crossed prehistoric seas in metallic armor. Its tough baleen strained whole shoals of fish, while its dorsal spines repelled predators.
```

---

## 38/59 — Wooly Sting — #1063

- **ID PBS:** `WOOLYSTING`
- **Category:** Past Paradox (Paradoxo do passado)
- **Type:** Flying / Fighting
- **Nome:** Wooly Sting (mantido como cadastrado, sem criar novo nome).
- **Origem confirmada pelo criador:** forma Paradoxo ancestral de **Gliscor**.
- **Arte enviada pelo criador:** criatura semelhante a um escorpião-morcego, com pelagem volumosa arroxeada, gola de pelos claros ao redor do rosto e do peito, olhos vermelhos, grandes pinças com pontas curvas, asas membranosas escuras e cauda arqueada com ponta afiada.
- **Conceito:** predador territorial de penhascos frios da pré-história. Sua pelagem espessa isolava o corpo durante os voos planados, enquanto as pinças fortes e a cauda em gancho permitiam combates a curta distância contra rivais.
- **Pokédex EN (APROVADA):** An ancient relative of Gliscor, it glided between icy cliffs with thick fur shielding it from the cold. It used its powerful pincers and hooked tail to repel rivals.
- **Tradução PT-BR (APROVADA):** Um antigo parente de Gliscor, ele planava entre penhascos gelados, protegido do frio por uma pelagem espessa. Usava suas poderosas pinças e a cauda em gancho para afastar rivais.
- **Height / Altura (APROVADA):** **2.3 m** (Gliscor original: 2.0 m).
- **Weight / Peso (APROVADO):** **76.0 kg** (Gliscor original: 42.5 kg).

### Justificativa da descrição e das medidas

- **Flying:** as asas membranosas permitem planar entre paredões e explorar correntes de ar; conserva a locomoção aérea de Gliscor.
- **Fighting:** as pinças grandes e o corpo mais musculoso favorecem disputas territoriais e golpes físicos, sem depender de veneno.
- **Pelagem espessa:** a gola clara e a pelagem roxa volumosa sugerem adaptação a ventos frios de altitudes elevadas, reinterpretando a silhueta ancestral da linhagem.
- **Pinças e cauda:** as pinças servem para agarrar oponentes, enquanto a cauda curva dificulta aproximações durante o combate.
- **Altura de 2.3 m:** propõe uma versão ligeiramente maior que Gliscor, coerente com o porte das asas e da pelagem.
- **Peso de 76.0 kg:** considera musculatura e isolamento corporal mais desenvolvidos, apesar de ainda ser adaptado ao voo planado.
- **Review status:** **APROVADO pelo criador em 31/10/2026 — descrição, altura e peso. Nenhuma publicação até concluir o MD.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [WOOLYSTING]
Height = 2.3
Weight = 76.0
Pokedex = An ancient relative of Gliscor, it glided between icy cliffs with thick fur shielding it from the cold. It used its powerful pincers and hooked tail to repel rivals.
```

---

## 39/59 — Iron Crawler — #1064

- **ID PBS:** `IRONCRAWLER`
- **Category:** Future Paradox (Paradoxo do futuro)
- **Type (catálogo):** Bug / Poison
- **Nome:** Iron Crawler (nome mantido, sem renomear o Pokémon no jogo).
- **Origem confirmada pelo criador:** forma Paradoxo do futuro de **Wimpod**.
- **Arte enviada pelo criador:** artrópode biomecânico de corpo alongado e baixo, carapaça prateada segmentada, grandes olhos roxos brilhantes com desenho em cruz, antenas longas e curvas e espinhos roxos posteriores. Possui várias patas articuladas.
- **Conceito:** criatura adaptada a costas poluídas do futuro; seus sensores detectam substâncias nocivas e seus sistemas internos concentram toxinas para liberar uma névoa defensiva. Apesar da aparência metálica, a tipagem proposta no catálogo é Bug / Poison (não Steel).
- **Pokédex EN (APROVADA):** A futuristic relative of Wimpod, it scuttles across polluted shores. Its glowing sensors detect toxins, which it absorbs and releases as a defensive mist.
- **Tradução PT-BR (APROVADA):** Um parente futurista de Wimpod, ele percorre rapidamente costas poluídas. Seus sensores luminosos detectam toxinas, que ele absorve e libera na forma de uma névoa defensiva.
- **Height / Altura (APROVADA):** **0.8 m** (Wimpod original: 0.5 m).
- **Weight / Peso (APROVADO):** **22.0 kg** (Wimpod original: 12.0 kg).

### Justificativa da proposta

- **Bug:** preserva o corpo de artrópode e a locomoção com múltiplas patas características de Wimpod.
- **Poison:** o processamento e armazenamento de agentes químicos sustenta a névoa tóxica defensiva.
- **Olhos roxos:** lentes luminosas em cruz sugerem sensores capazes de perceber contaminantes e movimentos.
- **Antenas curvas:** sensores de longo alcance que identificam obstáculos e resíduos tóxicos.
- **Carapaça segmentada:** protege os mecanismos internos de substâncias corrosivas, sem exigir tipagem Steel.
- **Altura de 0.8 m:** mantém uma silhueta compacta e rápida, um pouco maior que Wimpod.
- **Peso de 22.0 kg:** sugere placas reforçadas, sensores e mecanismos, com massa ainda compatível com um inseto ágil.
- **Review status:** **APROVADO pelo criador — descrição, altura e peso. Aguardar conclusão de todo o MD para publicar.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [IRONCRAWLER]
Height = 0.8
Weight = 22.0
Pokedex = A futuristic relative of Wimpod, it scuttles across polluted shores. Its glowing sensors detect toxins, which it absorbs and releases as a defensive mist.
```

---

## 40/59 — Iron Crusher — #1065

- **ID PBS:** `IRONCRUSHER`
- **Category:** Future Paradox (Paradoxo do futuro)
- **Type (catálogo):** Water / Steel
- **Nome:** Iron Crusher (mantido, sem renomear o Pokémon no jogo).
- **Origem confirmada pelo criador:** forma Paradoxo do futuro de **Kingler**.
- **Arte enviada pelo criador:** caranguejo biomecânico com couraça laranja e placas prateadas, olhos ou sensores cianos brilhantes, múltiplas pernas metálicas pontiagudas, uma pinça enorme e outra menor, ambas com peças articuladas e faixas luminosas azul-ciano.
- **Conceito:** máquina anfíbia semelhante a Kingler, adaptada para patrulhar áreas submersas. A pinça desproporcional usa um mecanismo hidráulico de esmagamento; as articulações seladas e o exoesqueleto metálico suportam ambientes de grande pressão.
- **Pokédex EN (APROVADA):** A futuristic relative of Kingler, it patrols the seafloor with hydraulic claws. Its oversized pincer can crush the metal hulls of sunken vessels.
- **Tradução PT-BR (APROVADA):** Um parente futurista de Kingler, ele patrulha o fundo do mar com pinças hidráulicas. Sua pinça gigantesca consegue esmagar os cascos metálicos de embarcações naufragadas.
- **Height / Altura (APROVADA):** **1.9 m** (Kingler original: 1.3 m).
- **Weight / Peso (APROVADO):** **210.0 kg** (Kingler original: 60.0 kg).

### Justificativa da proposta

- **Water:** conserva a origem aquática de Kingler, com mecanismos resistentes à imersão e atividade no fundo do mar.
- **Steel:** carapaça, pernas e pinças são feitas de placas metálicas reforçadas e articulações mecânicas.
- **Pinça assimétrica:** o membro maior funciona como uma prensa hidráulica, reinterpretando a pinça dominante de Kingler sem perder sua identidade visual.
- **Luzes cianas:** sugerem sensores e circuitos de controle nas pinças e no corpo, reforçando a estética futurista.
- **Pernas pontiagudas:** oferecem estabilidade e tração sobre rochas e destroços submersos.
- **Altura de 1.9 m:** amplia o porte de Kingler de forma compatível com a pinça superior gigantesca.
- **Peso de 210.0 kg:** massa adicional justificada pelas placas de metal e pelos mecanismos hidráulicos, muito acima dos 60.0 kg de Kingler.
- **Review status:** **APROVADO pelo criador em 31/10/2026 — descrição, altura e peso. Não aplicar ao jogo até concluir a revisão geral do MD.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [IRONCRUSHER]
Height = 1.9
Weight = 210.0
Pokedex = A futuristic relative of Kingler, it patrols the seafloor with hydraulic claws. Its oversized pincer can crush the metal hulls of sunken vessels.
```

---

## 41/59 — Iron Feaster — #1066

- **ID PBS:** `IRONFEASTER`
- **Category:** Future Paradox (Paradoxo do futuro)
- **Type (catálogo):** Normal / Steel
- **Nome:** Iron Feaster (mantido, sem renomear o Pokémon no jogo).
- **Origem confirmada pelo criador:** forma Paradoxo do futuro de **Snorlax**.
- **Arte enviada pelo criador:** criatura biomecânica volumosa e arredondada, com corpo azul-escuro, placas metálicas claras protegendo o ventre, grandes braços articulados, patas robustas, orelhas com luzes cianas, sensores circulares brilhantes e um núcleo luminoso central na região abdominal. A postura sentada e os olhos semicerrados preservam a identidade visual de Snorlax.
- **Conceito:** um consumidor e reciclador de metais do futuro. Sua alimentação exagerada é reinterpretada como a capacidade de engolir sucata e transformá-la em energia para um reator abdominal; após armazenar energia suficiente, entra em modo de economia de energia e permanece imóvel por longos períodos.
- **Pokédex EN (PROPOSTA):** A futuristic relative of Snorlax, it devours scrap metal to charge the reactor in its belly. Once fully powered, it enters a deep, motionless sleep.
- **Tradução PT-BR (PROPOSTA):** Um parente futurista de Snorlax, ele devora sucata metálica para carregar o reator em seu ventre. Quando está totalmente carregado, entra em um sono profundo e imóvel.
- **Height / Altura (PROPOSTA):** **2.4 m** (Snorlax original: 2.1 m).
- **Weight / Peso (PROPOSTO):** **850.0 kg** (Snorlax original: 460.0 kg).

### Justificativa da proposta

- **Normal:** preserva os hábitos marcantes de Snorlax, como o apetite voraz e os longos períodos de sono.
- **Steel:** braços, carapaça ventral e articulações são revestidos por placas metálicas; o sistema digestivo foi reinterpretado como um reator de reciclagem.
- **Núcleo abdominal ciano:** concentra a energia produzida pela conversão de sucata e destaca a enorme barriga, elemento visual central do Snorlax original.
- **Sensores nas orelhas e juntas:** os elementos brilhantes sugerem monitoramento de carga, movimentação e gasto energético.
- **Braços e patas pesados:** sustentam o corpo de grandes dimensões, sem exigir que o Pokémon seja rápido; mantêm sua aparência acomodada e tranquila.
- **Altura de 2.4 m:** forma ligeiramente maior que Snorlax, com espessura extra de blindagem e componentes externos.
- **Peso de 850.0 kg:** a massa quase duplicada é coerente com o corpo metálico, a estrutura reforçada e o reator instalado no abdômen.
- **Review status:** **APROVADO pelo criador — descrição, altura e peso validados. Nenhuma publicação até concluir todo o MD.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [IRONFEASTER]
Height = 2.4
Weight = 850.0
Pokedex = A futuristic relative of Snorlax, it devours scrap metal to charge the reactor in its belly. Once fully powered, it enters a deep, motionless sleep.
```

---

## 42/59 — Iron Invernose — #1067

- **ID PBS:** `IRONINVERNOSE`
- **Category:** Future Paradox (Paradoxo do futuro)
- **Type (catálogo):** Fire / Steel
- **Nome:** Iron Invernose (mantido, sem renomear o Pokémon no jogo).
- **Origem confirmada pelo criador:** forma Paradoxo do futuro de **Centiskorch**.
- **Arte/conceito base para proposta:** centopeia biomecânica longa e segmentada, com couraça metálica, múltiplas pernas articuladas, mandíbulas aquecidas e aberturas de calor ao longo do corpo. A identidade de Centiskorch é preservada por meio do corpo alongado, da presença de muitos membros e da ideia de calor intenso concentrado no tronco.
- **Conceito:** uma unidade térmica de rastreamento criada para atravessar túneis industriais e zonas superaquecidas. Suas placas metálicas armazenam calor extremo, enquanto seus dutos internos expelem chamas para abrir caminho ou intimidar intrusos.
- **Pokédex EN (PROPOSTA):** A futuristic relative of Centiskorch, it slithers through industrial tunnels with a body heated like a furnace. The vents along its armor release bursts of flame to melt obstacles in its path.
- **Tradução PT-BR (PROPOSTA):** Um parente futurista de Centiskorch, ele desliza por túneis industriais com o corpo aquecido como uma fornalha. As saídas de calor em sua armadura liberam rajadas de chamas para derreter obstáculos em seu caminho.
- **Height / Altura (PROPOSTA):** **3.8 m** (Centiskorch original: 3.0 m).
- **Weight / Peso (PROPOSTO):** **145.0 kg** (Centiskorch original: 120.0 kg).

### Justificativa da proposta

- **Fire:** preserva a principal identidade de Centiskorch, reinterpretando seu calor corporal como um sistema térmico interno semelhante a uma fornalha.
- **Steel:** a carapaça e os segmentos externos funcionam como placas metálicas resistentes ao calor e ao impacto.
- **Corpo alongado e articulado:** mantém o padrão centopeia da linha original e sustenta a ideia de deslocamento rápido por áreas estreitas.
- **Mandíbulas e dutos térmicos:** reforçam a função agressiva e industrial da forma Paradoxo, permitindo cortar, derreter ou afastar ameaças.
- **Pernas múltiplas:** garantem tração em superfícies metálicas e estabilidade mesmo em ambientes inclinados ou instáveis.
- **Altura/comprimento de 3.8 m:** amplia a imponência da forma futurista sem perder a silhueta reconhecível de Centiskorch.
- **Peso de 145.0 kg:** o aumento moderado representa blindagem e sistemas internos, sem tornar o Pokémon desproporcional ao papel de predador ágil.
- **Review status:** **APROVADO pelo criador — descrição, altura e peso validados. Nenhuma publicação até concluir todo o MD.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [IRONINVERNOSE]
Height = 3.8
Weight = 145.0
Pokedex = A futuristic relative of Centiskorch, it slithers through industrial tunnels with a body heated like a furnace. The vents along its armor release bursts of flame to melt obstacles in its path.
```

---

## 43/59 — Iron Leporis — #1068

- **ID PBS:** `IRONLEPORIS`
- **Category:** Future Paradox (Paradoxo do futuro)
- **Type (catálogo):** Normal / Electric
- **Nome:** Iron Leporis (mantido, sem renomear o Pokémon no jogo).
- **Origem confirmada pelo criador:** forma Paradoxo do futuro de **Lopunny**.
- **Arte enviada pelo criador:** coelha biomecânica de silhueta esguia, com orelhas longas em formato de lâminas/fios energéticos, corpo marrom-dourado com placas metálicas, olhos vermelhos brilhantes, juntas circulares expostas e grandes módulos cilíndricos nos braços e nas pernas, preservando a postura atlética e elegante de Lopunny.
- **Conceito:** uma unidade de mobilidade e combate corpo a corpo criada para executar saltos de alta precisão e descargas rápidas. Seus membros atuam como propulsores e acumuladores de energia, permitindo arrancadas instantâneas e golpes eletrificados.
- **Pokédex EN (PROPOSTA):** A futuristic relative of Lopunny, it stores electricity in its powerful limbs to unleash explosive jumps. Its blade-like ears and charged kicks can disable foes in an instant.
- **Tradução PT-BR (PROPOSTA):** Um parente futurista de Lopunny, ele armazena eletricidade em seus membros poderosos para realizar saltos explosivos. Suas orelhas em forma de lâmina e seus chutes carregados podem incapacitar inimigos em um instante.
- **Height / Altura (PROPOSTA):** **1.7 m** (Lopunny original: 1.2 m).
- **Weight / Peso (PROPOSTO):** **48.0 kg** (Lopunny original: 33.3 kg).

### Justificativa da proposta

- **Normal:** preserva a base corporal, a agilidade e a identidade geral de Lopunny como um Pokémon veloz e focado em mobilidade.
- **Electric:** a energia acumulada nas pernas, braços e orelhas justifica a nova tipagem e reforça o conceito futurista.
- **Membros com módulos cilíndricos:** sugerem motores, baterias ou estabilizadores que amplificam saltos e chutes.
- **Orelhas longas e cortantes:** mantêm o elemento visual mais reconhecível de Lopunny, agora reinterpretado como apêndices energizados.
- **Postura atlética:** favorece ataques rápidos, esquivas e movimentos acrobáticos, coerentes com uma forma Paradoxo tecnológica.
- **Altura de 1.7 m:** amplia o porte de Lopunny para uma versão mais imponente e mecânica, sem perder a silhueta elegante.
- **Peso de 48.0 kg:** o aumento moderado reflete blindagem leve e componentes internos, mantendo a ideia de velocidade.
- **Review status:** **APROVADO pelo criador — descrição, altura e peso validados. Nenhuma publicação até concluir todo o MD.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [IRONLEPORIS]
Height = 1.7
Weight = 48.0
Pokedex = A futuristic relative of Lopunny, it stores electricity in its powerful limbs to unleash explosive jumps. Its blade-like ears and charged kicks can disable foes in an instant.
```

---

## 44/59 — Iron Maeltrom — #1069

- **ID PBS:** `IRONMAELTROM`
- **Category:** Future Paradox (Paradoxo do futuro)
- **Type (catálogo):** Flying / Steel
- **Nome:** Iron Maeltrom (mantido, sem renomear o Pokémon no jogo).
- **Origem confirmada pelo criador:** forma Paradoxo do futuro de **Gyarados**.
- **Arte enviada pelo criador:** criatura biomecânica de corpo serpentino, enrolado em uma espiral, com couraça segmentada prateada e azul, espinhos dorsais em forma de lâmina, mecanismos circulares azul-ciano semelhantes a turbinas nas laterais e mandíbula escancarada com brilho interno. A cabeça feroz e o corpo longo preservam a identidade de Gyarados.
- **Conceito:** um leviatã mecânico que sobrevoa oceanos tempestuosos usando turbinas embutidas no corpo. Seu sistema de propulsão gera redemoinhos violentos, reinterpretando a fúria de Gyarados como uma força meteorológica artificial, sem alterar o tipo Flying / Steel registrado no catálogo.
- **Pokédex EN (PROPOSTA):** A futuristic relative of Gyarados, it uses turbines along its armored body to fly over raging seas. The violent air currents it creates can capsize ships.
- **Tradução PT-BR (PROPOSTA):** Um parente futurista de Gyarados, ele utiliza turbinas ao longo de seu corpo blindado para voar sobre mares revoltos. As violentas correntes de ar que produz podem virar embarcações.
- **Height / Altura (PROPOSTA):** **7.5 m** (Gyarados original: 6.5 m).
- **Weight / Peso (PROPOSTO):** **620.0 kg** (Gyarados original: 235.0 kg).

### Justificativa da proposta

- **Flying:** turbinas permitem voo e deslocamento sobre o mar, além de gerar redemoinhos, sem necessidade de asas convencionais.
- **Steel:** couraça segmentada, espinhos, mandíbula e componentes internos são reinterpretados como peças metálicas resistentes.
- **Turbinas laterais azul-ciano:** sugerem propulsão e estabilização aérea; a energia brilhante reforça o caráter futurista.
- **Espinhos semelhantes a lâminas:** reforçam a silhueta agressiva e podem funcionar como superfícies de estabilização e proteção.
- **Mandíbula mecânica aberta:** mantém o comportamento intimidador de Gyarados e dá personalidade ao design.
- **Altura de 7.5 m:** um leviatã um pouco maior que Gyarados, com uma silhueta alongada ainda reconhecível.
- **Peso de 620.0 kg:** o aumento de massa representa blindagem, turbinas e mecanismos internos, com a sustentação aérea explicada por propulsão ativa.
- **Review status:** **APROVADO pelo criador — descrição, altura de 7.5 m e peso de 620.0 kg. Aguardar conclusão do MD antes de publicar.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [IRONMAELTROM]
Height = 7.5
Weight = 620.0
Pokedex = A futuristic relative of Gyarados, it uses turbines along its armored body to fly over raging seas. The violent air currents it creates can capsize ships.
```

---

## 45/59 — Iron Matriarch — #1070

- **ID PBS:** `IRONMATRIARCH`
- **Category:** Future Paradox (Paradoxo do futuro)
- **Type (catálogo):** Normal / Steel
- **Nome:** Iron Matriarch (mantido, sem renomear o Pokémon no jogo).
- **Origem confirmada pelo criador:** forma Paradoxo do futuro de **Kangaskhan**.
- **Arte enviada pelo criador:** mãe biomecânica de carapaça marrom, creme e laranja, orelhas angulares, olhos e luzes azul-ciano, grandes punhos metálicos articulados, placas circulares nas pernas e uma pequena unidade robótica alojada na bolsa abdominal. A dupla mãe e filhote preserva a característica visual mais reconhecível de Kangaskhan.
- **Conceito:** um sistema mecânico de proteção cooperativa. A unidade principal utiliza punhos blindados como escudos, enquanto o pequeno robô em sua bolsa monitora ameaças e sincroniza os movimentos defensivos. As duas unidades agem juntas, reinterpretando o instinto maternal de Kangaskhan sem perder a identidade familiar.
- **Pokédex EN (PROPOSTA):** A futuristic relative of Kangaskhan, it protects a smaller unit inside its armored pouch. The two synchronize their movements to drive away threats.
- **Tradução PT-BR (PROPOSTA):** Um parente futurista de Kangaskhan, ele protege uma unidade menor dentro de sua bolsa blindada. Os dois sincronizam seus movimentos para afastar ameaças.
- **Height / Altura (PROPOSTA):** **2.6 m** (Kangaskhan original: 2.2 m).
- **Weight / Peso (PROPOSTO):** **310.0 kg** (Kangaskhan original: 80.0 kg).

### Justificativa da proposta

- **Normal:** conserva a silhueta, a relação protetora entre adulto e filhote e o comportamento de Kangaskhan.
- **Steel:** punhos, pernas, articulações, cabeça e bolsa possuem blindagem mecânica resistente.
- **Filhote robótico na bolsa:** elemento central do conceito; a pequena unidade complementa os sensores e movimentos da unidade adulta, sem eliminar a identidade maternal do original.
- **Punhos circulares blindados:** atuam como escudos e permitem conter adversários fisicamente sem expor a unidade menor.
- **Luzes e olhos cianos:** sugerem sensores, comunicação e sincronização entre as duas unidades.
- **Altura de 2.6 m:** crescimento moderado em relação a Kangaskhan, com ombros e articulações mais volumosos.
- **Peso de 310.0 kg:** a massa elevada reflete a estrutura reforçada e os componentes de dois organismos biomecânicos, sem depender de um tamanho exagerado.
- **Review status:** **EM REVISÃO — aguardando aprovação explícita da descrição, altura e peso pelo criador. NÃO aplicar ao jogo.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [IRONMATRIARCH]
Height = 2.6
Weight = 310.0
Pokedex = A futuristic relative of Kangaskhan, it protects a smaller unit inside its armored pouch. The two synchronize their movements to drive away threats.
```

---

## 52/59 — Archgutor — #1077

- **ID PBS:** `ARCHGUTOR`
- **Category:** New evolution (Nova evolução)
- **Type (catálogo):** Grass / Psychic
- **Nome:** Archgutor (mantido, sem renomear no jogo).
- **Linha evolutiva confirmada pelo criador:** Exeggcute → Exeggutor → **Archgutor**.
- **Habilidade informada pelo criador:** **Mega Sol**, a mesma habilidade de Mega Meganium. Trata-se de uma escolha já declarada pelo criador; **não modificar a habilidade no jogo nesta etapa de redação**.
- **Arte enviada pelo criador:** coqueiro robusto de tronco marrom-arenoso, com raízes/pés largos, copa de folhas verdes grandes e numerosas e três rostos arredondados semelhantes a cocos amarelados. Mantém o caráter vegetal de Exeggutor, mas apresenta uma copa mais exuberante e estrutura mais sólida.
- **Conceito:** ao passar décadas em praias ensolaradas, um Exeggutor desenvolveu uma copa de altíssima eficiência fotossintética. As folhas captam luz de forma excepcional e suas três cabeças armazenam a energia acumulada em tecidos vegetais especializados; a energia psíquica distribui essa reserva pelo corpo, permitindo que seus golpes respondam como se o sol estivesse forte, mesmo à noite ou sob nuvens.
- **Pokédex EN (PROPOSTA):** After decades on tropical beaches, this evolution of Exeggutor stores solar energy in its coconuts. It uses sun-powered moves even beneath storm clouds.
- **Tradução PT-BR (PROPOSTA):** Após décadas nas praias tropicais, esta evolução de Exeggutor armazena energia solar em seus cocos. Ele utiliza golpes alimentados pelo sol mesmo sob nuvens de tempestade.
- **Height / Altura (PROPOSTA):** **3.2 m** (Exeggutor original: 2.0 m).
- **Weight / Peso (PROPOSTO):** **185.0 kg** (Exeggutor original: 120.0 kg).

### Justificativa da proposta

- **Grass:** copa mais ampla e produção intensificada de energia por fotossíntese, característica natural de um coqueiro de ambientes tropicais.
- **Psychic:** as três cabeças coordenam o uso da energia armazenada; a parte psíquica reinterpreta o componente Psychic que Exeggutor já possuía.
- **Mega Sol:** a longa exposição ao sol mudou a fisiologia do Pokémon, permitindo armazenar energia luminosa e simular internamente as condições de sol forte para seus próprios golpes.
- **Folhas largas e numerosos folíolos:** ampliam a área de captura da radiação solar; o visual lembra uma copa madura e resistente ao clima costeiro.
- **Três cocos expressivos:** preservam a silhueta icônica de Exeggutor e funcionam, no conceito autoral, como reservatórios biológicos de energia solar.
- **Tronco grosso, raízes e pés robustos:** sustentam a copa maior e permitem locomoção em terrenos arenosos.
- **Altura de 3.2 m:** maior que Exeggutor comum, mas bem menor que a forma regional de Alola; corresponde a uma evolução mais robusta e frondosa.
- **Peso de 185.0 kg:** aumento coerente com tronco espesso, raízes musculosas e copa ampliada.
- **Review status:** **APROVADO pelo criador — descrição, altura e peso (3.2 m, 185.0 kg). Nenhuma publicação até concluir todo o MD.**

### Nota de habilidade — Mega Sol (já escolhida pelo criador)

**Mega Sol não invoca Sunny Day e não altera o clima global.** Faz os golpes usados pelo portador terem os efeitos de sol forte para ele próprio, independentemente do clima real. Por exemplo, Solar Beam dispensa o turno de carregamento, e Synthesis se beneficia do efeito de sol para a cura, conforme as regras aplicáveis na implementação. Não conferir esses benefícios aos aliados nem assumir a alteração de clima em campo. A aplicação concreta dessa mecânica no jogo requer verificação separada de compatibilidade com o motor usado no projeto.

Referência externa do funcionamento original: https://bulbapedia.bulbagarden.net/wiki/Mega_Sol_(Ability)

### Campos PBS previstos (não aplicar ainda)

```ini
# [ARCHGUTOR]
Height = 3.2
Weight = 185.0
Pokedex = After decades on tropical beaches, this evolution of Exeggutor stores solar energy in its coconuts. It uses sun-powered moves even beneath storm clouds.
```

---

## 53/59 — Dynamotrode — #1078

- **ID PBS:** `DYNAMOTRODE`
- **Category:** New evolution (Nova evolução)
- **Type (catálogo):** Electric / Steel
- **Nome:** Dynamotrode (mantido, sem renomear no jogo).
- **Linha evolutiva confirmada pelo criador:** Voltorb → Electrode → **Dynamotrode**.
- **Inspiração confirmada pelo criador:** **Fast Ball**, Poké Bola associada à captura de Pokémon velozes. A inspiração é visual e temática; não implica que Dynamotrode seja literalmente uma Poké Bola.
- **Arte enviada pelo criador:** corpo esférico com metade superior branca, placas e vincos em formato de armadura, metade inferior amarela/dourada, marcações vermelhas e azuis nas laterais, olhos estreitos e um sorriso largo com dentes brancos. O design retém o formato redondo e a expressão maliciosa de Electrode.
- **Conceito:** evolução de Electrode focada em velocidade. Em vez de dissipar toda a eletricidade em explosões, concentra carga em mecanismos eletromagnéticos e a descarrega em pulsos sequenciais que aceleram sua rolagem. Uma casca metálica reforçada resiste ao atrito e aos impactos; freadas bruscas podem liberar a energia restante como ondas de choque. Essa é uma proposta narrativa, sem atribuir novas habilidades ou golpes ao jogo.
- **Pokédex EN (APROVADA):** An evolution of Electrode resembling a Fast Ball, it propels itself with electromagnetic bursts. It rolls so quickly that sparks trail behind it.
- **Tradução PT-BR (APROVADA):** Uma evolução de Electrode que lembra uma Fast Ball, ela se impulsiona por descargas eletromagnéticas. Rola tão depressa que deixa um rastro de faíscas.
- **Height / Altura (APROVADA):** **1.4 m** (Electrode original: 1.2 m).
- **Weight / Peso (APROVADO):** **118.0 kg** (Electrode original: 66.6 kg).

### Justificativa da proposta

- **Electric:** preserva a capacidade de acumular grandes cargas elétricas, agora aproveitadas para propulsão em vez de explosões indiscriminadas.
- **Steel:** a metade superior funciona como blindagem metálica que tolera choques, fricção e calor durante as acelerações.
- **Fast Ball:** a combinação de corpo esférico, porção amarela, placas claras e detalhes vermelhos/azuis cria uma referência reconhecível, enquanto a velocidade é reinterpretada como característica do Pokémon.
- **Propulsão eletromagnética:** pulsos de energia sucessivos fornecem arrancadas rápidas; faíscas revelam a descarga em movimento.
- **Expressão travessa:** os olhos agressivos e os dentes reforçam a personalidade imprevisível de Electrode, mesmo após evoluir.
- **Altura de 1.4 m:** aumento discreto de diâmetro para abrigar o revestimento e o sistema de impulsão, mantendo a silhueta compacta.
- **Peso de 118.0 kg:** a carapaça de liga metálica justifica a massa maior; a propulsão elétrica compensa o aumento durante a movimentação.
- **Review status:** **APROVADO pelo criador — descrição, altura de 1.4 m e peso de 118.0 kg. Nenhuma publicação até concluir todo o MD.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [DYNAMOTRODE]
Height = 1.4
Weight = 118.0
Pokedex = An evolution of Electrode resembling a Fast Ball, it propels itself with electromagnetic bursts. It rolls so quickly that sparks trail behind it.
```

---

## 54/59 — Magnetrix — #1079

- **ID PBS:** `MAGNETRIX`
- **Category:** New evolution (Nova evolução)
- **Type (catálogo):** Steel / Electric
- **Nome:** Magnetrix (mantido, sem renomear no jogo).
- **Linha evolutiva confirmada pelo criador:** Magnemite → Magneton → **Magnetrix**, evolução alternativa a Magnezone.
- **Diretriz confirmada pelo criador:** mais rápido e ofensivamente poderoso que Magneton, mas menos defensivo; oferecer as habilidades **Electric Surge** (gera Electric Terrain) e **Levitate** como possibilidades distintas.
- **Arte enviada pelo criador:** estrutura metálica esverdeada formada por vários módulos esféricos com olhos circulares, organizados ao redor de um núcleo central com polos vermelho e azul. Um grande anel elíptico metálico circunda o conjunto; quatro ímãs escuros em formato de U, com extremidades vermelhas e azuis, ficam distribuídos na parte externa. Pequenas hastes e conexões aparentes reforçam a silhueta de um aparelho eletromagnético aberto, ágil e sem blindagem pesada.
- **Conceito revisado após receber a arte:** **acelerador eletromagnético vivo**. Seus quatro ímãs externos trabalham em sincronia com um núcleo polarizado e com o anel estabilizador, que canaliza a eletricidade e corrige a direção do corpo durante mudanças bruscas de movimento. Magnetrix segue a rota oposta à de Magnezone: em vez de construir uma estrutura compacta e blindada, mantém os módulos separados e expostos para aumentar a potência de descarga e a velocidade. Em ambientes com alta atividade magnética, a rotação do anel cria um zumbido agudo e arcos elétricos.
- **Electric Surge — interpretação temática:** ao realinhar os quatro ímãs, o núcleo descarrega pulsos que percorrem o solo e ativam Electric Terrain quando ele entra no campo de batalha. O design aberto facilita a dissipação da energia acumulada.
- **Levitate — interpretação temática:** em exemplares com esta habilidade, a repulsão magnética gerada pelo núcleo e pelo anel permite flutuar e alterar a própria posição quase instantaneamente. As duas habilidades são alternativas individuais, não ficam ativas em simultâneo.
- **Pokédex EN (PROPOSTA REVISADA COM A ARTE):** An alternate evolution of Magneton, it spins four powerful magnets around its core to build immense electrical pressure. It can electrify the ground or propel itself through the air at incredible speed.
- **Tradução PT-BR (PROPOSTA REVISADA COM A ARTE):** Uma evolução alternativa de Magneton, ele faz quatro poderosos ímãs girarem ao redor de seu núcleo para acumular enorme pressão elétrica. Pode eletrificar o solo ou se impulsionar pelo ar em velocidade incrível.
- **Height / Altura (PROPOSTA):** **1.3 m** (Magneton original: 1.0 m).
- **Weight / Peso (PROPOSTO):** **82.0 kg** (Magneton original: 60.0 kg).

### Justificativa da proposta revisada

- **Steel:** os ímãs, o anel orbital e as conexões são metálicos; a carcaça é fina e deixa os módulos expostos, justificando a menor Defense.
- **Electric:** o núcleo central polarizado e os quatro ímãs externos produzem descargas concentradas, explicando o alto Special Attack.
- **Núcleo com polos vermelho e azul:** concentra e redistribui energia, preservando os polos magnéticos característicos da família de Magnemite.
- **Quatro ímãs em U:** geram campos em direções alternadas; ao se sincronizarem, produzem tanto rajadas elétricas quanto acelerações e curvas muito rápidas.
- **Anel elíptico:** atua como estabilizador e indutor, mantendo a formação alinhada durante a rotação dos módulos e o voo.
- **Módulos esféricos com olhos:** preservam a identidade visual de Magneton, mas ficam mais distribuídos, com menos proteção entre eles.
- **Velocidade em vez de blindagem:** seu estilo de combate prioriza disparar primeiro e esquivar, em vez de suportar ataques de frente.
- **Altura de 1.3 m:** crescimento moderado em relação a Magneton, especialmente pela expansão vertical do conjunto de ímãs e hastes.
- **Peso de 82.0 kg:** ímãs e anel acrescentam massa, mas o corpo aberto continua muito mais leve que a estrutura de Magnezone.
- **Review status:** **APROVADO pelo criador — descrição, altura de 1.3 m e peso de 82.0 kg validados com base na arte. Habilidades Electric Surge e Levitate confirmadas como alternativas; stats são apenas sugestões não aprovadas. NÃO aplicar ao jogo até terminar o MD.**

### Habilidades e interação com Electric Terrain

| Escolha de habilidade | Efeito em batalha | Compensação |
|---|---|---|
| **Electric Surge** | Cria Electric Terrain ao entrar em campo; Magnetrix, por não possuir Levitate nesta configuração, pode receber o bônus do terreno se estiver aterrado pelas regras do jogo. | Sem a proteção de Levitate, continua vulnerável a Ground. |
| **Levitate** | Protege contra ataques Ground habituais e permite flutuar de acordo com as regras da habilidade. | Por estar fora do solo, não recebe o bônus direto de Electric Terrain. |

**Nota técnica:** o sprite flutuando não implica automaticamente Levitate ativo. Com **Electric Surge**, Magnetrix do tipo Steel / Electric é considerado aterrado nas condições normais de batalha, mesmo que sua animação pareça suspensa. Habilidades não se acumulam: cada exemplar usa Electric Surge **ou** Levitate, exceto se o jogo implementar expressamente uma regra customizada. A proposta não modifica o cadastro do jogo.

### Sugestão opcional de atributos base (não aplicar nesta revisão)

| Atributo | Magneton (referência) | Magnetrix (sugestão) |
|---|---:|---:|
| HP | 50 | 60 |
| Attack | 60 | 60 |
| Defense | 95 | 70 |
| Sp. Attack | 120 | 145 |
| Sp. Defense | 70 | 70 |
| Speed | 70 | 120 |
| **Total** | **465** | **525** |

**Papel em batalha:** atacante especial rápido (Speed 120, Sp. Attack 145), com Defense 70 como fraqueza intencional. Esses valores são sugestões opcionais de balanceamento, não mudanças aprovadas nem aplicadas à ROM.

### Campos PBS previstos (não aplicar ainda)

```ini
# [MAGNETRIX]
Height = 1.3
Weight = 82.0
Pokedex = An alternate evolution of Magneton, it spins four powerful magnets around its core to build immense electrical pressure. It can electrify the ground or propel itself through the air at incredible speed.
```

---

## 55/59 — Magiscale — #1080

- **ID PBS:** `MAGISCALE`
- **Category:** New evolution (Nova evolução alternativa)
- **Type (catálogo):** Water / Psychic
- **Nome:** Magiscale (mantido, sem renomear no jogo).
- **Origem confirmada pelo criador:** evolução alternativa de **Magikarp**, em outro ramo da linha evolutiva, em vez de Gyarados; não é uma evolução posterior a Gyarados.
- **Habilidade indicada pelo criador:** capaz de gerar **Psychic Terrain**, sugerindo **Psychic Surge** como habilidade que o ativa automaticamente ao entrar em batalha. A descrição narrativa e a aplicação mecânica devem ser verificadas em momento separado; não alterar habilidades nem cadastro nesta revisão.
- **Arte enviada pelo criador:** criatura semelhante a um dragão-carpa comprido e sinuoso, com escamas escuras, contornos e marcas douradas, grandes nadadeiras e cristas esbranquiçadas com bordas amarelo-ouro, longos bigodes dourados e cabeça de expressão serena e imponente. A silhueta é esguia e fluida, contrastando com o corpo agressivo e musculoso de Gyarados.
- **Conceito:** **O sábio das marés invisíveis.** Enquanto Gyarados representa a evolução de Magikarp por força e fúria, Magiscale surge de uma adaptação baseada em percepção, paciência e domínio mental. Durante anos, Magikarp percebe sutis correntes e vibrações no oceano; sua mente aprende a acompanhar esses padrões até liberar ondas psíquicas que influenciam o espaço ao redor. As barbatanas funcionam como receptores de vibrações, os bigodes dourados detectam perturbações, e as escamas marcadas de ouro conduzem e distribuem a energia psíquica.
- **Psychic Surge — interpretação temática:** ao entrar em combate, Magiscale concentra a energia psíquica e a espalha pelo campo como uma maré invisível, criando **Psychic Terrain**. Essa energia fortalece ataques Psychic usados por Pokémon considerados no solo e impede que golpes com prioridade atinjam alvos considerados no solo, conforme as regras usuais. O terreno não é um clima e não implica que Magiscale controle a mente de outros Pokémon. Pokémon fora do solo não recebem o reforço do terreno. A arte sinuosa ou postura elevada não equivale a Levitate; Magiscale Water / Psychic normalmente é considerado no solo para esses efeitos.
- **Pokédex EN (APROVADA):** An alternate evolution of Magikarp, it reads ocean currents through its golden whiskers. With a pulse of its mind, it blankets the battlefield in psychic energy.
- **Tradução PT-BR (APROVADA):** Uma evolução alternativa de Magikarp, ele percebe as correntes oceânicas por meio de seus bigodes dourados. Com um pulso de sua mente, envolve o campo de batalha em energia psíquica.
- **Height / Altura (APROVADA):** **5.4 m** (comprimento corporal; Magikarp original: 0.9 m; Gyarados: 6.5 m).
- **Weight / Peso (APROVADO):** **128.0 kg** (Magikarp original: 10.0 kg; Gyarados: 235.0 kg).

### Justificativa da proposta aprovada

- **Water:** mantém a natureza aquática da carpa e sua habilidade de ler correntes e vibrações do oceano.
- **Psychic:** substitui o caminho da fúria de Gyarados por concentração mental, controle de energia e percepção extraordinária.
- **Bigodes compridos dourados:** funcionam como órgãos sensíveis capazes de perceber alterações minúsculas na água e nos campos de energia.
- **Escamas escuras com detalhes dourados:** visualmente canalizam energia psíquica, com o dourado reforçando o aspecto raro e majestoso.
- **Barbatanas amplas e claras:** contribuem para uma movimentação silenciosa e precisa, sem exigir força bruta; a aparência etérea é visual, não uma tipagem Flying.
- **Psychic Surge:** os impulsos mentais se espalham pelo campo em ondas sincronizadas, explicando por que Psychic Terrain aparece automaticamente ao entrar em batalha.
- **Relação com Gyarados:** são evoluções alternativas de Magikarp: uma voltada à agressividade e força física, outra ao autocontrole e poder especial.
- **Altura/comprimento de 5.4 m:** tamanho impressionante, porém um pouco menor que Gyarados e coerente com o corpo longo e esguio mostrado na arte.
- **Peso de 128.0 kg:** representa um corpo grande e ágil, sem a massa mais volumosa do Gyarados original.
- **Review status:** **APROVADO pelo criador — descrição, altura e peso. Nenhuma publicação até concluir todo o MD.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [MAGISCALE]
Height = 5.4
Weight = 128.0
Pokedex = An alternate evolution of Magikarp, it reads ocean currents through its golden whiskers. With a pulse of its mind, it blankets the battlefield in psychic energy.
```

---

## 56/59 — Ammnoid — #1081

- **ID PBS:** `AMMNOID`
- **Category:** New evolution (Nova evolução alternativa)
- **Type (catálogo):** Rock / Psychic
- **Nome:** Ammnoid (mantido, sem renomear no jogo).
- **Evolução definida pelo criador:** **Omanyte → Ammnoid** ao utilizar uma **Dusk Stone**; ramo alternativo ao Omastar. Não é uma evolução posterior a Omastar.
- **Arte recebida:** corpo azul-turquesa, olhos grandes com anéis dourados, numerosos tentáculos flexíveis com faixas amarelas e uma concha volumosa grafite/preta, segmentada por faixas amarelo-douradas, com espinhos pontiagudos e uma espiral lateral marcada.
- **Conceito revisado após análise da arte — O Oráculo das Profundezas:** a Dusk Stone desperta uma propriedade psíquica latente nos minerais da concha fóssil. As faixas douradas passam a conduzir impulsos mentais, e os tentáculos turquesa captam as vibrações do assoalho marinho. A concha espiral amplifica esses sinais, permitindo detectar criaturas na escuridão absoluta. A aparência curiosa dos olhos contrasta com os espinhos que protegem o corpo macio contra predadores abissais. O poder principal deste estágio é a **percepção psíquica**, não o controle total das correntes oceânicas.
- **Pokédex EN (REVISÃO VISUAL APROVADA):** After exposure to a Dusk Stone, Omanyte evolves into Ammnoid. Its gold-banded shell amplifies psychic pulses that reveal movement across the dark seafloor.
- **Tradução PT-BR (REVISÃO VISUAL APROVADA):** Após ser exposto a uma Dusk Stone, Omanyte evolui para Ammnoid. Sua concha com faixas douradas amplifica pulsos psíquicos que revelam movimentos pelo fundo escuro do oceano.
- **Height / Altura (APROVADA, MANTIDA):** **0.9 m** (Omanyte: 0.4 m; Omastar: 1.0 m).
- **Weight / Peso (APROVADO, MANTIDO):** **31.0 kg** (Omanyte: 7.5 kg; Omastar: 35.0 kg).

### Justificativa baseada na arte

- **Rock:** a concha espiral escura e os espinhos dourados formam uma proteção mineral, preservando a origem fóssil de Omanyte.
- **Psychic:** a concha e os tentáculos canalizam e interpretam pulsos psíquicos para detectar vibrações em águas profundas sem depender de luz.
- **Dusk Stone:** ativa as propriedades psíquicas da concha mineralizada; o simbolismo das profundezas sem luz não exige tipagem Dark nem Ghost.
- **Faixas douradas e espiral:** fazem parte do desenho visível; na narrativa, funcionam como condutores e ressonadores mentais.
- **Olhos grandes e tentáculos turquesa:** mantêm a identidade de Omanyte; combinam curiosidade e sensibilidade, em contraste com a concha armada.
- **Espinhos:** defesa física natural para evitar que predadores mordam a parte macia do cefalópode.
- **Altura de 0.9 m:** condiz com o estágio intermediário, maior que Omanyte mas ligeiramente menor que Omastar.
- **Peso de 31.0 kg:** condiz com a concha grossa, sem tornar o corpo desproporcional.
- **Relação com Cephalonid:** Ammnoid percebe e antecipa; sua evolução final transforma a ressonância da concha em controle direto das correntes e da pressão oceânica.
- **Habilidades, atributos, golpes e método evolutivo:** manter os dados já cadastrados; o método Omanyte + Dusk Stone foi definido pelo criador. A condição da próxima evolução ainda não foi definida.
- **Review status:** **APROVADO pelo criador — a nova descrição baseada na arte foi reconfirmada, com altura de 0.9 m e peso de 31.0 kg mantidos. NÃO aplicar ao jogo até concluir o MD.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [AMMNOID]
Height = 0.9
Weight = 31.0
Pokedex = After exposure to a Dusk Stone, Omanyte evolves into Ammnoid. Its gold-banded shell amplifies psychic pulses that reveal movement across the dark seafloor.
```

---

## 57/59 — Cephalonid — #1082

- **ID PBS:** `CEPHALONID`
- **Category:** New evolution (Nova evolução)
- **Type (catálogo):** Rock / Psychic
- **Nome:** Cephalonid (mantido, sem renomear no jogo).
- **Evolução confirmada pelo criador:** **Omanyte → Ammnoid (com Dusk Stone) → Cephalonid**. A condição para evoluir de Ammnoid para Cephalonid ainda não foi definida.
- **Arte recebida:** concha grande, escura e espiralada, com placas sobrepostas, faixas de brilho azul-ciano, vários espinhos e chifres dourados compridos; uma estrutura frontal semelhante a coroa com um detalhe azul brilhante; olhos azul-turquesa e muitos tentáculos longos azul-esverdeados com bordas douradas. A concha e a coroa são mais elaboradas que as de Ammnoid.
- **Conceito revisado após análise da arte — O Soberano das Correntes Abissais:** a sensibilidade psíquica de Ammnoid alcança uma nova etapa. Sua concha se torna uma câmara de ressonância que acumula ondas mentais e as concentra na estrutura azul da coroa. Os grandes chifres dourados auxiliam a direcionar essa energia, enquanto os tentáculos modulam os movimentos finos. Cephalonid manipula correntes e pressão da água ao redor, cria barreiras psíquicas e repele predadores sem contato físico. Não necessita de pedras permanentemente flutuando ao redor: a própria blindagem, os chifres e a coroa já transmitem seu poder.
- **Pokédex EN (REVISÃO VISUAL APROVADA):** Its horned shell stores immense psychic energy. When the blue gem on its crown flashes, Cephalonid can bend deep-sea currents and repel predators without touching them.
- **Tradução PT-BR (REVISÃO VISUAL APROVADA):** Sua concha com chifres armazena uma enorme quantidade de energia psíquica. Quando a gema azul de sua coroa brilha, Cephalonid consegue alterar correntes das profundezas e repelir predadores sem tocá-los.
- **Height / Altura (APROVADA):** **1.7 m** (Ammnoid: 0.9 m; Omastar: 1.0 m).
- **Weight / Peso (APROVADO):** **110.0 kg** (Ammnoid: 31.0 kg; Omastar: 35.0 kg).

### Justificativa baseada na arte

- **Rock:** a concha fóssil se desenvolve em camadas compactas com espinhos e chifres minerais, ampliando sua resistência física.
- **Psychic:** os sinais de percepção de Ammnoid evoluem para telecinese, barreiras mentais e alterações nas correntes submarinas.
- **Detalhe azul brilhante na coroa:** interpretado narrativamente como ponto de foco dos impulsos psíquicos, sem implicar alteração do sprite.
- **Chifres dourados da concha:** concentram a energia mental e, fisicamente, dificultam investidas de predadores.
- **Faixas azul-ciano:** reforçam visualmente a ideia de energia psíquica circulando pelos segmentos do exoesqueleto.
- **Tentáculos longos com bordas douradas:** dirigem os campos psíquicos e proporcionam precisão no controle da água.
- **Diferença em relação a Ammnoid:** Ammnoid percebe e localiza; Cephalonid controla e repele, assumindo o papel de guardião das profundezas.
- **Altura de 1.7 m:** compatível com o estágio final, com concha e coroa muito mais desenvolvidas.
- **Peso de 110.0 kg:** representa uma concha densamente mineralizada e uma blindagem maior do que a de Ammnoid.
- **Habilidades, atributos, golpes e evolução:** não inventar nem alterar dados do jogo; o método Ammnoid → Cephalonid permanece em aberto até decisão do criador.
- **Review status:** **APROVADO pelo criador — nova descrição com base na arte, altura de 1.7 m e peso de 110.0 kg aprovados. Condição Ammnoid → Cephalonid ainda não definida; NÃO aplicar ao jogo até concluir o MD.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [CEPHALONID]
Height = 1.7
Weight = 110.0
Pokedex = Its horned shell stores immense psychic energy. When the blue gem on its crown flashes, Cephalonid can bend deep-sea currents and repel predators without touching them.
```

---

## 58/59 — Stundrift — #1083

- **ID PBS:** `STUNDRIFT`
- **Category:** New evolution (Nova evolução)
- **Type (catálogo):** Ground / Electric
- **Nome:** Stundrift (mantido, sem renomear o Pokémon no jogo).
- **Origem confirmada pelo criador:** evolução de **Stunfisk**.
- **Habilidades escolhidas pelo criador:** **Water Absorb** e **Earth Eater**, como opções de habilidade individual, não simultâneas. Não definir por conta própria qual é comum ou oculta; manter conforme cadastro do jogo.
- **Arte recebida:** corpo marrom-arenoso, bem achatado e largo como uma arraia, com grandes padrões elétricos amarelo-dourados nas costas; olhos salientes e boca rosada; nadadeiras laterais compostas de pontas rígidas e amareladas, bordas espinhosas e cauda alta com pontas em forma de leque. A silhueta preserva Stunfisk, mas evidencia mais ancoragem nos sedimentos.
- **Conceito proposto — O Capacitor das Marés Subterrâneas:** vive enterrado sob os sedimentos do leito marinho e suporta tanto a passagem de água pelas camadas de areia quanto as compressões e vibrações do solo. Estruturas em seu corpo captam a energia dessas forças e a transformam em bioeletricidade. As marcas amarelas atuam como reservatórios elétricos; as nadadeiras espinhosas e a cauda alta o estabilizam durante o deslocamento dos sedimentos. Pode liberar choques através da areia úmida enquanto permanece camuflado.
- **Pokédex EN (PROPOSTA):** Buried deep beneath the seabed, it absorbs energy from rushing water and shifting earth. Its golden markings glow before it releases a powerful electric shock.
- **Tradução PT-BR (PROPOSTA):** Enterrado nas profundezas do leito marinho, ele absorve energia das correntes de água e dos movimentos da terra. Suas marcas douradas brilham antes de liberar uma poderosa descarga elétrica.
- **Height / Altura (PROPOSTA):** **1.2 m** (Stunfisk original: 0.7 m).
- **Weight / Peso (PROPOSTO):** **36.0 kg** (Stunfisk original: 11.0 kg).

### Justificativa baseada na arte e nas habilidades

- **Ground:** corpo achatado, nadadeiras e espinhos favorecem o movimento e a fixação entre areia e sedimentos submersos.
- **Electric:** marcas douradas funcionam, na narrativa, como superfícies de armazenamento e condução da bioeletricidade.
- **Water Absorb:** sua fisiologia especializada absorve a água que atravessa a areia; em combate, essa opção de habilidade anula golpes Water dirigidos ao Pokémon e recupera até 25% do HP máximo, nas condições usuais.
- **Earth Eater:** estruturas sensíveis à compressão convertem os impactos do solo em energia; em combate, essa opção anula golpes Ground dirigidos ao Pokémon e recupera até 25% do HP máximo, nas condições usuais.
- **Habilidades alternativas, não cumulativas:** com Water Absorb, Stundrift continua sujeito aos golpes Ground; com Earth Eater, continua sujeito aos golpes Water. Isso preserva escolhas estratégicas, sem conceder ambas as imunidades ao mesmo tempo.
- **Nadadeiras e espinhos laterais:** fixam o corpo no solo e ajudam a conter a força das correntes.
- **Cauda alta:** estabiliza e detecta vibrações do entorno, mesmo quando grande parte do corpo está enterrada.
- **Olhos salientes:** permitem acompanhar movimento acima dos sedimentos sem revelar a posição completa.
- **Altura de 1.2 m:** representa o crescimento de uma forma mais extensa e larga que Stunfisk.
- **Peso de 36.0 kg:** acompanha o maior porte, a musculatura das nadadeiras e os órgãos de armazenamento elétrico.
- **Habilidades, stats, golpes e condição evolutiva:** não alterar dados existentes nem inventar requisito de evolução. Apenas texto da Pokédex e medidas propostas aguardam aprovação do criador.
- **Review status:** **APROVADO pelo criador — descrição, altura de 1.2 m e peso de 36.0 kg confirmados. NÃO aplicar ao jogo até concluir o MD nem publicar no GitHub.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [STUNDRIFT]
Height = 1.2
Weight = 36.0
Pokedex = Buried deep beneath the seabed, it absorbs energy from rushing water and shifting earth. Its golden markings glow before it releases a powerful electric shock.
```

---

## 59/59 — Swadloadne — #1084

![Sprite de Swadloadne (#1084)](https://pokemondessastreparadosal.vercel.app/assets/fan-pokemon/SWADLOADNE/front.png)

> **Referência visual:** sprite original fornecido pelo criador, em PNG de 128 × 128 pixels com transparência. A arte autoral é servida pelo portal do projeto; este MD usa o endereço do sprite já publicado no site.

- **ID PBS:** `SWADLOADNE`
- **Category:** New evolution (Nova evolução alternativa)
- **Type (catálogo):** Grass / Bug
- **Nome:** Swadloadne (mantido, sem renomear no jogo).
- **Evolução definida pelo criador:** **Swadloon + Leaf Stone → Swadloadne**; evolução alternativa a **Leavanny**, nunca uma evolução posterior de Leavanny.
- **Referência da espécie base enviada pelo criador:** `https://pokemondessastreparadosal.vercel.app/pokedex/SWADLOON`
- **Habilidades definidas pelo criador:** **Shell Armor** e **Thick Fat**, como opções alternativas, não simultâneas; não alterar a distribuição cadastrada no jogo durante esta revisão de Pokédex.
- **Arte fornecida pelo criador (confirmada):** corpo compacto e robusto, com tronco marrom-oliva; membros inferiores curtos; capuz de folha apontado para a frente, parcialmente sombreando os olhos; expressão firme; uma coroa de folhas verdes se projeta para cima; grandes folhas laterais formam um manto semelhante a escudos, com marcas claras em forma de cruz e pontas alongadas. A silhueta é de um guardião terrestre móvel, não de um casulo fechado e imóvel.
- **Conceito proposto — O Guardião da Floresta / O Escudo Vivo:** a Leaf Stone desperta crescimento acelerado das fibras vegetais, transformando o manto flexível de Swadloon em folhas espessas, sobrepostas e articuladas. Em vez de abandonar a cobertura foliar como Leavanny, Swadloadne a utiliza como uma armadura móvel, podendo avançar contra ameaças e proteger Pokémon menores atrás de seu corpo. Sob as folhas existe, como explicação biológica proposta, uma camada de tecido isolante que estabiliza a temperatura corporal em climas rigorosos.
- **Pokédex EN (REVISADA COM ARTE; PROPOSTA):** After evolving with a Leaf Stone, it guards its forest beneath overlapping leaf shields. Thick inner padding protects it from heat and cold, while its armor covers vulnerable spots.
- **Tradução PT-BR (REVISADA COM ARTE; PROPOSTA):** Após evoluir com uma Leaf Stone, ele protege sua floresta sob escudos de folhas sobrepostas. Uma espessa camada interna o protege do calor e do frio, enquanto sua armadura cobre os pontos vulneráveis.
- **Height / Altura (PROPOSTA MANTIDA):** **1.1 m** (Swadloon original: 0.5 m; Leavanny original: 1.2 m).
- **Weight / Peso (PROPOSTO MANTIDO):** **42.0 kg** (Swadloon original: 7.3 kg; Leavanny original: 20.5 kg).

### Justificativa revisada com base na arte

- **Grass:** as folhas amplas e vigorosas recobrem o corpo; a Leaf Stone torna esse revestimento mais espesso e resistente, preservando a estética vegetal da família evolutiva.
- **Bug:** o inseto continua com postura compacta e coberto pelo antigo manto foliar, mantendo a ligação com Swadloon.
- **Shell Armor:** as folhas laterais sobrepostas funcionam narrativamente como escudos que se fecham sobre pontos vitais. **Efeito de batalha:** impede golpes críticos, sem reduzir todo dano recebido.
- **Thick Fat:** propõe-se uma camada interna de tecidos isolantes sob a capa de folhas, **não visível diretamente na arte**. **Efeito de batalha:** reduz pela metade o dano recebido de golpes Fire e Ice.
- **Coroa de folhas:** crescimento em camadas acima da cabeça que reforça o aspecto de camuflagem na mata e proteção superior.
- **Capuz de folha e olhar sério:** o capuz cobre parte do rosto, e os olhos firmes sugerem um protetor vigilante, não apenas uma criatura adormecida dentro de um casulo.
- **Marcas claras em cruz nas folhas:** característica **visível** do sprite; podem ser interpretadas, na narrativa, como nervuras resistentes que distribuem impactos. A função biológica é proposta, não confirmada pela imagem.
- **Silhueta baixa, tronco forte e folhas largas:** sustentam um estilo de combate defensivo, de posicionamento e resistência, mantendo a possibilidade de deslocamento ativo.
- **Habilidades alternativas, não cumulativas:** com **Thick Fat**, a fraqueza Fire ×4 do tipo Grass/Bug passa a ×2 e Ice ×2 passa a ×1; Flying permanece ×4. Com **Shell Armor**, essas fraquezas permanecem, mas críticos são impedidos. Sem criar uma imunidade completa a Fire ou Ice.
- **Personalidade:** guardião territorial pouco agressivo, que intercepta ataques e cria abrigo para pequenos Pokémon sob as folhas, em oposição à agilidade de Leavanny.
- **Altura de 1.1 m:** crescimento concentra-se no corpo e no volume foliar, sem precisar atingir o porte esguio de Leavanny.
- **Peso de 42.0 kg:** massa superior à de Leavanny é coerente com folhas densas, fibras rígidas e corpo compacto; valor narrativo ainda sujeito à aprovação.
- **Review status:** **APROVADO pelo criador — descrição revisada com arte, altura de 1.1 m e peso de 42.0 kg aprovados. Não alterar o jogo/PBS automaticamente.**

### Campos PBS previstos (não aplicar ainda)

```ini
# [SWADLOADNE]
Height = 1.1
Weight = 42.0
Pokedex = After evolving with a Leaf Stone, it guards its forest beneath overlapping leaf shields. Thick inner padding protects it from heat and cold, while its armor covers vulnerable spots.
```

---

## Fila de revisão — espécies e pendências

### Past Paradox

| # | Pokémon (nome atual) | ID PBS | Tipo(s) | No jogo | Texto/medidas |
|---:|---|---|---|---|---|
| 1026 | Cave Fang | `CAVEFANG` | Poison / Dark | Cadastrado | **01 — APROVADO** |
| 1027 | Abyss Lure | `ABYSSLURE` | Water / Fairy | Cadastrado | **02 — APROVADO** |
| 1028 | Ancestrash | `ANCESTRASH` | Poison / Ground | Cadastrado | **03 — APROVADO** |
| 1029 | Burial Gaze | `BURIALGAZE` | Ghost / Ground | Cadastrado | **04 — APROVADO** |
| 1030 | Craggy Siphon | `CRAGGYSIPHON` | Water / Fighting | Cadastrado | **05 — APROVADO** |
| 1031 | Dire Ruff | `DIRERUFF` | Dark / Ground | Cadastrado | **06 — APROVADO** |
| 1032 | Dread Crest | `DREADCREST` | Flying / Ground | Cadastrado | **07 — APROVADO** |
| 1033 | Fetid Gullet | `FETIDGULLET` | Poison / Ghost | Cadastrado | **08 — APROVADO** |
| 1034 | Fossil Husk | `FOSSILHUSK` | Bug / Rock | Cadastrado | **09 — APROVADO** |
| 1035 | Fossl Tide | `FOSSLTIDE` | Water / Steel | Cadastrado | **10 — APROVADO** |
| 1036 | Jagged Maw | `JAGGEDMAW` | Water / Rock | Cadastrado | **11 — APROVADO** |
| 1037 | Miasmic | `MIASMIC` | Poison / Dark | Cadastrado | **12 — APROVADO** |
| 1038 | Mire crest | `MIRECREST` | Dark / Fighting | Cadastrado | **13 — APROVADO** |
| 1039 | Phantomire | `PHANTOMIRE` | Ghost / Dark | Cadastrado | **14 — APROVADO** |
| 1040 | **Frost Plume** (antigo Priamalgong) | `PRIAMALGONG` | Ice / Dragon | Cadastrado | **15 — APROVADO (nome/texto/medidas)** |
| 1041 | **Spined Wyrm** (antigo Primal Caterpie) | `PRIMALCATERPIE` | Bug / Dragon | Cadastrado | **16 — APROVADO (nome/texto/medidas)** |
| 1042 | **Tidal Tyrant** (antigo Primal Drenaw) | `PRIMALDRENAW` | Water / Dragon | Cadastrado | **17 — APROVADO (nome/texto/medidas)** |
| 1043 | **Witchcap Haze** (antigo Primal Notic) | `PRIMALNOTIC` | Fairy / Poison | Pendente | **18 — APROVADO (nome/texto/medidas)** |
| 1044 | **Burrow Brawler** (antigo Primal Punny) | `PRIMALPUNNY` | Ground / Fighting | Cadastrado | **19 — APROVADO (nome/texto/medidas)** |
| 1045 | **Canopy Titan** (antigo Primal Tropical) | `PRIMALTROPICAL` | Grass / Dragon | Cadastrado | **20 — APROVADO (nome/texto/medidas)** |
| 1046 | **Timber Maul** (antigo Primalduurr) | `PRIMALDUURR` | Fighting / Ground | Cadastrado | **21 — APROVADO (nome/texto/medidas)** |
| 1047 | **Tempest Talon** (antigo Primalgeot) | `PRIMALGEOT` | Flying / Fighting | Cadastrado | **22 — APROVADO (nome/texto/medidas)** |
| 1048 | **Cinder Coil** (antigo Primalkorch) | `PRIMALKORCH` | Bug / Dragon | Cadastrado | **23 — APROVADO (nome/texto/medidas)** |
| 1049 | **Rime Shroud** (antigo Primalmoth) | `PRIMALMOTH` | Bug / Ice | Cadastrado | **24 — APROVADO (nome/texto/medidas)** |
| 1050 | Tar Chasm (antigo Primalmuk) | `PRIMALMUK` | Poison / Ground | Cadastrado | **25 — APROVADO (nome/texto/medidas)** |
| 1051 | **Venom Crown** (antigo Primalseaking) | `PRIMALSEAKING` | Water / Poison | Cadastrado | **26 — APROVADO (nome/texto/medidas)** |
| 1052 | **Spore Rampart** (antigo Primalsect) | `PRIMALSECT` | Grass / Rock | Cadastrado | **27 — APROVADO (nome/texto/medidas)** |
| 1053 | **Venom Scythe** (antigo Primalviper) | `PRIMALVIPER` | Poison / Dragon | Cadastrado | **28 — APROVADO (nome/texto/medidas)** |
| 1054 | Primatizer (nome mantido) | `PRIMATIZER` | Water / Rock | Cadastrado | **29 — APROVADO (texto/medidas; origem ainda não confirmada)** |
| 1055 | Rampage Horn | `RAMPAGEHORN` | Rock / Dragon | Cadastrado | **30 — EM REVISÃO** |
| 1056 | Ravenous Crest | `RAVENOUSCREST` | Fighting | Cadastrado | **31 — EM REVISÃO** |
| 1057 | Razor Carapace | `RAZORCARAPACE` | Steel / Dragon | Cadastrado | **32 — EM REVISÃO** |
| 1058 | Savege Jowl | `SAVEGEJOWL` | Fairy / Dark | Cadastrado | **33 — EM REVISÃO** |
| 1059 | Scorch Mane | `SCORCHMANE` | Fire / Electric | Cadastrado | **34 — APROVADO (texto/medidas)** |
| 1060 | Scoria Shell | `SCORIASHELL` | Fire / Steel | Cadastrado | **35 — APROVADO (texto/medidas; verificar tipo)** |
| 1061 | Thorn Bastion | `THORNBASTION` | Ground / Rock | Cadastrado | **36 — EM REVISÃO** |
| 1062 | Titan Baleen | `TITANBALEEN` | Water / Steel | Cadastrado | **37 — APROVADO (texto/medidas)** |
| 1063 | Wooly Sting | `WOOLYSTING` | Flying / Fighting | Cadastrado | **38 — APROVADO (texto/medidas)** |

### Future Paradox

| # | Pokémon (nome atual) | ID PBS | Tipo(s) | No jogo | Texto/medidas |
|---:|---|---|---|---|---|
| 1064 | Iron Crawler | `IRONCRAWLER` | Bug / Poison | Cadastrado | **39 — APROVADO (texto/medidas)** |
| 1065 | Iron Crusher | `IRONCRUSHER` | Water / Steel | Cadastrado | **40 — APROVADO (texto/medidas)** |
| 1066 | Iron Feaster | `IRONFEASTER` | Normal / Steel | Cadastrado | **41 — APROVADO (texto/medidas)** |
| 1067 | iron invernose | `IRONINVERNOSE` | Fire / Steel | Cadastrado | **42 — APROVADO (texto/medidas)** |
| 1068 | Iron Leporis | `IRONLEPORIS` | Normal / Electric | Cadastrado | **43 — APROVADO (texto/medidas)** |
| 1069 | Iron Maeltrom | `IRONMAELTROM` | Flying / Steel | Cadastrado | **44 — APROVADO (texto/medidas)** |
| 1070 | Iron Matriarch | `IRONMATRIARCH` | Normal / Steel | Cadastrado | **45 — EM REVISÃO** |

### Convergent species

**Revisão destas seis espécies adiada a pedido do criador.** Elas seguem na lista e serão retomadas após as novas evoluções; não foram removidas da Pokédex nem consideradas concluídas.

| # | Pokémon (nome atual) | ID PBS | Tipo(s) | No jogo | Texto/medidas |
|---:|---|---|---|---|---|
| 1071 | Horsand | `HORSAND` | Ground / Poison | Pendente | **Adiado — revisão futura** |
| 1072 | Spinedra | `SPINEDRA` | Ground / Poison | Pendente | **Adiado — revisão futura** |
| 1073 | Stingdra | `STINGDRA` | Ground / Poison | Pendente | **Adiado — revisão futura** |
| 1074 | Gillble | `GILLBLE` | Water / Electric | Pendente | **Adiado — revisão futura** |
| 1075 | Galbite | `GALBITE` | Water / Electric | Pendente | **Adiado — revisão futura** |
| 1076 | Garcholt | `GARCHOLT` | Water / Electric | Pendente | **Adiado — revisão futura** |

### New evolutions

| # | Pokémon (nome atual) | ID PBS | Tipo(s) | No jogo | Texto/medidas |
|---:|---|---|---|---|---|
| 1077 | Archgutor | `ARCHGUTOR` | Grass / Psychic | Cadastrado | **52 — APROVADO (Mega Sol; texto/medidas)** |
| 1078 | Dynamotrode | `DYNAMOTRODE` | Electric / Steel | Cadastrado | **53 — APROVADO (texto/medidas)** |
| 1079 | Magnetrix | `MAGNETRIX` | Steel / Electric | Cadastrado | **54 — APROVADO (texto/medidas; stats sugeridos separadamente)** |
| 1080 | Magiscale | `MAGISCALE` | Water / Psychic | Cadastrado | **55 — APROVADO (texto/medidas)** |
| 1081 | Ammnoid | `AMMNOID` | Rock / Psychic | Cadastrado | **56 — APROVADO (descrição revisada com arte; medidas mantidas)** |
| 1082 | Cephalonid | `CEPHALONID` | Rock / Psychic | Cadastrado | **57 — APROVADO (descrição com arte; medidas)** |
| 1083 | Stundrift | `STUNDRIFT` | Ground / Electric | Cadastrado | **58 — APROVADO (texto/medidas)** |
| 1084 | Swadloadne | `SWADLOADNE` | Grass / Bug | Cadastrado | **59 — APROVADO (descrição revisada com arte; medidas)** |

### 12 Mega Evoluções autorais (revisão separada)

As formas Mega não entram no total de 59 novas espécies. Quando terminarmos as 59, decidir se cada Mega precisa de descrição e medidas próprias ou se deve herdar a ficha da espécie base.

Mega Tentacruel, Mega Sunflora, Mega Arbok, Mega Fearow, Mega Hypno, Mega Kabutops, Mega Ledian, Mega Ludicolo, Mega Miltank, Mega Purugly, Mega Vileplume, Mega Walrein.

## Controle editorial

- [x] Revisar e aprovar Cave Fang (#1026): descrição em inglês, altura 1.6 m, peso 36.0 kg.
- [x] Revisar e aprovar Abyss Lure (#1027): descrição em inglês, altura 1.9 m, peso 64.0 kg.
- [x] Revisar e aprovar Ancestrash (#1028): descrição em inglês, altura 2.4 m, peso 260.0 kg.
- [x] Revisar e aprovar Burial Gaze (#1029): descrição em inglês, altura 1.4 m, peso 42.0 kg.
- [x] Revisar e aprovar Craggy Siphon (#1030): descrição em inglês, altura 1.7 m, peso 108.0 kg.
- [x] Revisar e aprovar Dire Ruff (#1031): descrição em inglês, altura 1.6 m, peso 82.0 kg.
- [x] Revisar e aprovar Dread Crest (#1032): descrição em inglês, altura 2.1 m, peso 58.0 kg.
- [x] Revisar e aprovar Fetid Gullet (#1033): descrição em inglês, altura 1.9 m, peso 94.0 kg.
- [x] Revisar e aprovar Fossil Husk (#1034): descrição em inglês, altura 1.1 m, peso 79.0 kg.
- [x] Revisar e aprovar Fossl Tide (#1035): descrição em inglês, altura 1.6 m, peso 118.0 kg.
- [x] Revisar e aprovar Jagged Maw (#1036): descrição em inglês, altura 2.2 m, peso 285.0 kg.
- [x] Revisar e aprovar Miasmic (#1037): descrição em inglês, altura 1.8 m, peso 72.0 kg.
- [x] Revisar e aprovar Mire Crest (#1038): descrição em inglês, altura 1.5 m, peso 74.0 kg.
- [x] Revisar e aprovar Phantomire (#1039): descrição em inglês, altura 1.9 m, peso 0.4 kg.
- [x] Aprovar Frost Plume (#1040, antigo Priamalgong): nome, descrição em inglês, altura 2.3 m e peso 148.0 kg.
- [x] Aprovar Spined Wyrm (#1041, antigo Primal Caterpie): nome, descrição em inglês, altura 1.2 m e peso 24.0 kg.
- [x] Aprovar Tidal Tyrant (#1042, antigo Primal Drenaw): nome, descrição em inglês, altura 2.8 m e peso 310.0 kg.
- [x] Aprovar Witchcap Haze (#1043, antigo Primal Notic): nome, descrição em inglês, altura 1.7 m e peso 28.0 kg. Continua marcado como pendente no jogo.
- [x] Aprovar Burrow Brawler (#1044, antigo Primal Punny): nome, descrição em inglês, altura 1.6 m e peso 62.0 kg.
- [x] Aprovar Canopy Titan (#1045, antigo Primal Tropical): nome, descrição em inglês, altura 3.2 m e peso 240.0 kg.
- [x] Aprovar Timber Maul (#1046, antigo Primalduurr): nome, descrição em inglês, altura 2.1 m e peso 185.0 kg.
- [x] Aprovar Tempest Talon (#1047, antigo Primalgeot): nome, descrição em inglês, altura 2.1 m e peso 61.0 kg.
- [x] Aprovar Cinder Coil (#1048, antigo Primalkorch): nome, descrição em inglês, altura 4.2 m e peso 180.0 kg.
- [x] Aprovar Rime Shroud (#1049, antigo Primalmoth): nome, descrição em inglês, altura 1.8 m e peso 21.0 kg.
- [x] Aprovar Tar Chasm (#1050, antigo Primalmuk): nome, descrição em inglês, altura 2.0 m e peso 180.0 kg.
- [x] Aprovar Venom Crown (#1051, antigo Primalseaking): nome, descrição em inglês, altura 1.8 m e peso 67.0 kg.
- [x] Aprovar Spore Rampart (#1052, antigo Primalsect): nome, descrição em inglês, altura 1.7 m e peso 132.0 kg.
- [x] Aprovar Venom Scythe (#1053, antigo Primalviper): nome, descrição em inglês, altura 4.2 m e peso 92.0 kg.
- [x] Aprovar Primatizer (#1054): descrição em inglês, altura 2.2 m e peso 135.0 kg; nome mantido. Origem ainda não confirmada.
- [ ] Revisar Rampage Horn (#1055): confirmar origem de Rhydon, descrição em inglês, altura 2.5 m e peso 340.0 kg; depois continuar as demais espécies.
- [ ] Revisar Ravenous Crest (#1056): confirmar origem de Vigoroth, descrição em inglês, altura 1.9 m e peso 96.0 kg.
- [ ] Revisar Razor Carapace (#1057): confirmar possível origem de Lairon, descrição em inglês, altura 1.7 m e peso 285.0 kg.
- [ ] Revisar Savege Jowl (#1058): confirmar possível origem de Granbull, descrição em inglês, altura 1.8 m e peso 104.0 kg.
- [x] Aprovar Scorch Mane (#1059): descrição em inglês, altura 2.1 m e peso 140.0 kg.
- [x] Aprovar Scoria Shell (#1060): descrição em inglês, altura 1.4 m e peso 190.0 kg. Tipo do catálogo Fire / Steel diverge do Fire / Rock citado na proposta, conferir no final.
- [ ] Revisar Thorn Bastion (#1061): confirmar origem de Sandslash, descrição em inglês, altura 1.6 m e peso 145.0 kg.
- [x] Aprovar Titan Baleen (#1062): origem de Wailord confirmada, descrição em inglês, altura 17.0 m e peso 1250.0 kg.
- [x] Aprovar Wooly Sting (#1063): origem de Gliscor confirmada, descrição em inglês, altura 2.3 m e peso 76.0 kg.
- [x] Aprovar Iron Crawler (#1064): origem de Wimpod confirmada, descrição em inglês, altura 0.8 m e peso 22.0 kg.
- [x] Aprovar Iron Crusher (#1065): origem de Kingler confirmada, descrição em inglês, altura 1.9 m e peso 210.0 kg.
- [x] Aprovar Iron Feaster (#1066): origem de Snorlax confirmada, descrição em inglês, altura 2.4 m e peso 850.0 kg.
- [x] Aprovar Iron Invernose (#1067): origem de Centiskorch, descrição em inglês, altura 3.8 m e peso 145.0 kg.
- [x] Aprovar Iron Leporis (#1068): origem de Lopunny, descrição em inglês, altura 1.7 m e peso 48.0 kg.
- [x] Aprovar Iron Maeltrom (#1069): origem de Gyarados, descrição em inglês, altura 7.5 m e peso 620.0 kg.
- [ ] Revisar Iron Matriarch (#1070): origem de Kangaskhan, descrição em inglês, altura 2.6 m e peso 310.0 kg.
- [ ] Retomar posteriormente as seis espécies convergentes (#1071–#1076), adiadas a pedido do criador.
- [x] Aprovar Archgutor (#1077): evolução de Exeggutor com habilidade Mega Sol, descrição em inglês, altura 3.2 m e peso 185.0 kg. Habilidade já escolhida pelo criador; sem mudança no jogo.
- [x] Aprovar Dynamotrode (#1078): evolução de Electrode inspirada na Fast Ball; descrição em inglês, altura 1.4 m e peso 118.0 kg.
- [x] Aprovar Magnetrix (#1079): arte recebida e conceito revisado (quatro ímãs, anel estabilizador e núcleo polarizado); Electric Surge ou Levitate, descrição em inglês, altura 1.3 m e peso 82.0 kg. Stats sugeridos apenas para discussão futura.
- [x] Aprovar Magiscale (#1080): evolução alternativa de Magikarp com Psychic Surge; descrição em inglês, comprimento 5.4 m e peso 128.0 kg. Ainda não aplicar ao jogo.
- [x] Aprovar a redação revisada de Ammnoid (#1081) com arte recebida: evolução de Omanyte com Dusk Stone, Rock / Psychic; altura 0.9 m e peso 31.0 kg mantidos e aprovados. Não aplicar ao jogo.
- [x] Aprovar Cephalonid (#1082): evolução de Ammnoid, tipo Rock / Psychic; descrição refeita com base na arte, altura 1.7 m e peso 110.0 kg aprovados. Condição específica da evolução ainda pendente. Não aplicar ao jogo.
- [x] Aprovar Stundrift (#1083): evolução de Stunfisk, tipo Ground / Electric, Water Absorb ou Earth Eater, descrição em inglês, altura 1.2 m e peso 36.0 kg. Não aplicar ao jogo.
- [ ] Revisar Swadloadne (#1084): evolução alternativa de Swadloon via Leaf Stone, tipo Grass / Bug, Shell Armor ou Thick Fat; conferir descrição em inglês, altura 1.1 m e peso 42.0 kg. Arte recebida e analisada; validar a descrição revisada e manter 1.1 m e 42.0 kg, se aprovados. Não aplicar ao jogo.
- [ ] Conferir proporções de altura e peso com as artes definitivas.
- [ ] Conferir nomes com grafia incomum antes de eventual correção separada (ex.: Fossl Tide, Savege Jowl; o nome Priamalgong já recebeu substituição aprovada por Frost Plume).
- [ ] Revisar se as 12 Mega Evoluções precisam de entradas específicas.
- [ ] Revisão final do inglês e do formato PBS.
- [ ] Somente depois, solicitar publicação do MD na `main`.
