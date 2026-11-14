# Kanto — HMs de campo com três requisitos (Piloto Windows)

**Motivação (14/11/2026):** no início do piloto de Kanto, o personagem conseguiu surfar e usar Cut sem Soul/Cascade Badge, sem HM e sem Pokémon compatível. O validador `BlueRegionalPolicy.state` exigia o marcador de instalação do jogo principal `Data/blue-kanto-install.json`, inexistente na cópia experimental, e devolvia `:native`. Além disso, `field_result` passava `tool_ready=true` sem verificar HM, Bolsa ou equipe.

## Contrato em Kanto

O comando de campo é permitido somente se, nesta ordem:

1. **Insígnia local de Kanto** correspondente ao HM, verificada com `BlueRegions.field_access` e `BlueRegions.local_achievements`; conquistas de outras regiões não contam.
2. **HM físico** obtido e presente na Bolsa (ID `HMxx` ou alias equivalente quando registrado). Não basta encontrar o evento ou possuir uma insígnia.
3. **Pokémon utilizável na equipe** que possa aprender o golpe segundo `Pokemon#compatible_with_move?`. Ovo, desmaiado, Pokémon na Box ou espécie incompatível não satisfazem a regra. Não é necessário substituir nenhum dos quatro movimentos equipados.

| HM de Kanto | Insígnia exigida | Item |
| --- | --- | --- |
| Cut | Cascade (Misty) | HM01 |
| Fly | Thunder (Lt. Surge) | HM02 |
| Surf | Soul (Koga) | HM03 |
| Strength | Rainbow (Erika) | HM04 |
| Flash | Boulder (Brock) | HM05 |
| Rock Smash | Marsh (Sabrina) | HM06 |
| Waterfall | Volcano (Blaine) | HM07 |

O quadro reflete o registro regional já existente em `site/public/data/regions.json`, sem conceder itens ou insígnias automaticamente. Para movimentos sem regra local de Kanto, o validador não cria permissões adicionais.

## Implementação

- `scripts/battle_polish/RegionalPolicy.rb` reconhece a cópia isolada pelo `Kanto pilot.json`. A proteção fica ativa sem exigir instalação de Kanto no Decades principal, mas somente se o save for de Kanto.
- A checagem do HM na Bolsa e da compatibilidade real é feita depois da insígnia. O hook `Trainer#get_pokemon_with_move`, apenas durante um HM de campo autorizado de Kanto, retorna um membro compatível mesmo que ele não saiba o golpe. É assim que Pidgey pode usar Fly com quatro golpes diferentes, mas Bulbasaur não.
- O bloqueio cobre menus de habilidades, `pbCut`, `pbSurf`, `pbFly`, demais interações nativas, bem como entrada direta em Surf (`pbStartSurfing`) e empurrão de pedra (`pbPushThisBoulder`).
- `scripts/regions/pilot.py` copia a versão atual de `RegionalPolicy.rb` para o plugin preparado e adiciona o arquivo ao hash da construção, garantindo que a cópia do piloto seja reconstruída após esta correção.
- `tests/kanto_hm_gate_runtime.rb` verifica cada HM e a combinação de pré-requisitos; `tests/region_policy_runtime.rb` preserva as regras de PC, conquistas e Decades.

**Segurança:** as funções de campo de Decades continuam caindo na política nativa em saves antigos; Johto, Hoenn e Sinnoh não recebem novas regras de obtenção de HM por este patch. Os saves são mantidos, e nenhum item, conquista ou Pokémon é criado pelo gate.

## Aceite de gameplay pendente

Atualize a `main` e reconstrua o piloto com `KANTO_JOGAR_EXPERIMENTAL.bat --rebuild`. Em Pallet, sem HM/Soul Badge, tente usar Surf na água: o personagem deve permanecer em terra. Teste Cut sem Cascade Badge e HM01; a árvore deve continuar. Com a insígnia, ainda sem HM, o uso continua bloqueado. Depois de obter HM e incluir na equipe um Pokémon compatível que **não tenha** o movimento entre seus quatro golpes, a habilidade deve funcionar. Testar também o uso em menus e após save/reload.

A CI Ruby verifica contratos e fluxos simulados, mas não comprova física do mapa, animações, colisões ou navegação real no `Game.exe`. Não aumentar a barra de aceite integral até obter evidência jogável.
