# Johto — avanço offline da Etapa 05: percurso New Bark até Violet

**Auditoria 13/11/2026. Não exige nem executa Game.exe.**

## O que foi implementado

A análise da geometria real, proveniente dos ZIPs privados auditados no chat, identificou **duas ligações de mapas ausentes das 42 conexões PBS presentes na fonte**. Os dois pares possuem a mesma assinatura de estrada RMXP **[116, 96, 124]**, em três tiles contíguos da borda, e todos os bits direcionais de passabilidade dos **4 tiles para dentro x 3 linhas** (em ambos os lados) estão livres nos dados do tileset. Isso é uma prova **estática**, não de travessia no jogo.

| Mapa externo 1 | Mapa externo 2 | Y externo 1 | Y externo 2 | Conexão PBS proposta (MapIDs da prévia 600–673) |
|---|---|---|---|---|
| Johto Route 29 — fonte Map104 → destino 625, borda oeste | Cherrygrove — fonte Map080 → destino 601, borda leste | 11 | 23 | `601,East,12,625,West,0` |
| Johto Route 31 — fonte Map106 → destino 627, borda oeste | Violet — fonte Map081 → destino 602, borda leste | 31 | 37 | `602,East,6,627,West,0` |

**Conexões que já existiam no pacote original (não modificadas):**

- `New Bark (79) West → Route29 (104) East`
- `Cherrygrove (80) North → Route30 (105) South`
- `Route30 (105) North → Route31 (106) South`

Com as duas linhas candidatas, o grafo passa a ter um caminho completo **New Bark → Route29 → Cherrygrove → Route30 → Route31 → Violet**, usando **44 linhas no total** (42 originais + 2 novas, **sem inserir automaticamente**).

### Verificação de integridade por mapa

Os quatro arquivos são do **staging privado de Johto** materializado com MapIDs finais de prévia; nenhum foi enviado ao repositório.

| Mapa | SHA-256 do RXDATA da prévia |
|---|---|
| Map625 Route29 | `e4ebe5576c1074e2b382d95705186275aafc67e2a6feafc3b2cfc843636c12cc` |
| Map601 Cherrygrove | `b9ec2d2729db8c74db8ead81162e147aba98b27a46d68100f3f8ebc71e0acb30` |
| Map627 Route31 | `e85dfa5ed49e8efb3adaa31873d7fc20fb36fc2e66051e1bce39139a124c1c56` |
| Map602 Violet | `4bc5c0be150b3378f5ed0e847420b81fabe29aa7c69584f0bf40a21dcc23670b` |

**Fonte Johto v1:** SHA-256 `5d5697e9c3bf5db6ca7039d4af65697dd8b231f4b1305f14731e35ac324b6715`.

## Código e testes no GitHub

- `scripts/regions/johto_route29_cherrygrove.py` → deduz `601,East,12,625,West,0` a partir dos tiles, verifica unicidade da passagem, passabilidade de 3 × 4 em ambos os lados, IDs Johto e duplicações.
- `scripts/regions/johto_route31_violet.py` → repete prova estática para `602,East,6,627,West,0`.
- `tests/test_johto_route29_cherrygrove.py` e `tests/test_johto_route31_violet.py` → **9 testes unitários sintéticos passaram localmente**; os dois algoritmos também foram exercitados com as tabelas de tiles extraídas dos quatro MapNNN verdadeiros e geraram exatamente as conexões acima.
- Em uma instalação contendo `.blue-work/johto-staging`, executar **apenas se desejar auditoria offline**:

```powershell
python scripts/regions/johto_route29_cherrygrove.py
python scripts/regions/johto_route31_violet.py
python -m unittest discover -s tests -p "test_johto_route*.py" -v
```

Saídas JSON ficam em `.blue-work/` e não sobrescrevem relatórios antigos. Nenhum script executa o motor, cria eventos ou modifica a instalação `game/`.

## O que ainda não foi realizado (não confundir com 1/13)

- A **passagem visual/estática** não prova que o motor Essentials atravessará os mapas com câmera, colisões, eventos, save ou posicionamento corretos.
- Os dois novos registros PBS estão **em relatório de proposta**, não integrados ao PBS da campanha ou ao `game/` original; não falsificar `tested_in_game`.
- Casas, laboratórios, ginásio Falkner, encontros selvagens, NPCs, equipes PBS e progressão para a Insígnia ZEPHYR continuam pendentes de integração e QA real. As regras Ruby dos eventos de Violet já existiam no projeto e não foram adulteradas.
- Arte de origem do terceiro não é publicada no GitHub; apenas provas em texto e código de verificação.

**Resultado:** avanço técnico da **Etapa 05**, porém permanece **PARCIAL**. **Barra de fases JOGÁVEIS: 0/13; fases TESTADAS: 0/13.**