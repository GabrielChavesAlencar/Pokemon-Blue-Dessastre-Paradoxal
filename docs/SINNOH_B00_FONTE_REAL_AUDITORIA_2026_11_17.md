# Sinnoh B00 — análise verificada dos arquivos realmente recebidos (17/11/2026)

**Estado:** ZIP e créditos recebidos nesta conversa, hashes conferidos e MapInfos + 76 mapas Sinnoh lidos de maneira inerte, sem executar Ruby, extrair, converter ou instalar conteúdo. Os binários originais não foram enviados ao GitHub. **B/C/D seguem 0/13.**

## Fonte e identidade

- Nome do arquivo enviado: `Pokemon World V18.zip`; diretório interno **`Pokemon Journeys V18`** — é o mesmo pacote recebido, não uma nova fonte.
- ZIP SHA-256: `ca6226a070026a8f269c927bfe9a30821b659e2629df26513be780fc34ceda35` (208057674 bytes).
- Créditos SHA-256: `42433e84a3bb8d462ce86d7a7245a23fefe7602ba707f3ea6139aefe4aff5240`.
- `Data/MapInfos.rxdata` SHA-256: `a5de4d870ae08aa3730942496734c7a0917505a6d435ff178ce5a10f73fc6495`.
- Índice `MapInfos` com **911 entradas**, **912 arquivos MapNNN** no ZIP multirregional (um órfão: **Map999**, sem atribuir a Sinnoh).
- Árvore `Sinnoh Region` = **Map408**, formada por **76 arquivos reais indexados**. A árvore não implica 76 mapas jogáveis.

## Aproveitamento técnico real

| Evidência | Quantidade |
|---|---:|
| Mapas na árvore Sinnoh | **76** |
| Mapas com ao menos um tile no terreno | **54** |
| Mapas sem tiles (organização/interiores NC) | **22** |
| Mapas sem eventos | **64** |
| Eventos RMXP cadastrados nos outros 12 mapas | **397** |
| Chamadas de script (`pbBridgeOn`/`pbBridgeOff`) | **383** (169/214) |
| Comandos de movimentação e scroll | **14 + 7** |
| Comandos nativos de transferência de mapa | **0** |
| Tilesets usados | **1** OutsideWorld2.7 e **31** SinnohCompleteTileset |
| Total de células de tile não zeradas | **484.722** |

**Exemplos positivos:** Twinleaf (**Map209**, 86×36, 0 eventos), Sandgem (Map210), Jubilife (Map211), Oreburgh (Map212), Eterna (Map214), Sunyshore (Map222), Rotas 201–230, Mt Coronet Wilds (Map892). Os tileset gráficos citados existem no ZIP, mas seus direitos de redistribuição ainda precisam de análise.

**Gargalos:** `4 Lakes NC` (**Map263**) é vazio; `Sinnoh Labs` (272), `Sinnoh Gyms` (273), Poké Centers (274), Poké Marts (275) e cavernas como Mt Coronet Caves (267) são vazios; Twinleaf não contém NPCs ou evento de maleta de Rowan/Barry. Portanto a sequência da introdução não pode ser simplesmente copiada do ZIP.

Os **397 eventos** encontrados são efeitos de pontes/movimentação; **não** demonstram treinadores, battle encounters, ginásios, narrativa, warps, itens-chave ou estado jogável. O arquivo `Credits.txt` nomeia múltiplos colaboradores, incluindo SageDeoxys com anotação de permissão para sprites, mas não fornece licença individual verificável para todos os recursos e sua redistribuição.

## IDs de origem na árvore de Sinnoh

`5, 165, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 250, 251, 252, 253, 254, 255, 256, 257, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 302, 408, 888, 892, 897, 898, 899, 900, 906`

**IDs com terreno vazio:** `5, 165, 208, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 302, 897, 898`.

**IDs com eventos:** `222` (31), `231` (27), `232` (61), `234` (9), `237` (80), `238` (14), `239` (19), `242` (29), `243` (30), `253` (18), `255` (16), `892` (63).

## Regras e próximas ações

1. Reutilizar somente os **mapas com terreno** em estágio local e isolado, após avaliação de uso. **Não copiar scripts de terceiros, músicas ou os mapas para a main**.
2. Fazer reconhecimento dos tilesets 1/31, dependencies e objetos sem licença clara. Não atribuir automaticamente o MapID 209 como destino 209 do Decades.
3. Obter inventário privado de `game/Data/MapInfos.rxdata` e reservas Kanto/Johto/Hoenn para projetar MapIDs sem colisão; não subir saves e base privada ao GitHub.
4. Recriar interiores, Lago Verity, NPCs, badges, eventos de Rowan/Barry e warps usando contratos já existentes do Blue.
5. Executar testes nativos Windows/JoiPlay apenas quando o usuário decidir — nenhuma dessas provas foi obtida.

[Comprovante JSON de hashes/IDs](../data/regions/sinnoh-b00-actual-source.json). A ferramenta [`audit_sinnoh_rxdata.py`](../scripts/regions/audit_sinnoh_rxdata.py) já permite repetição de auditoria profunda read-only contra ZIP local com `--source`; [`audit_sinnoh_b00_intake.py`](../scripts/regions/audit_sinnoh_b00_intake.py) confere metadados e créditos. **Fase B00: fonte recebida e catalogada; aprovação técnica B permanece 0/13**, C/D permanecem 0/13, `Sinnoh planned`.
