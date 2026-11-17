# Sinnoh G03 — Matriz estática de MapIDs (GitHub-only)

**17/11/2026.** Fonte: manifestos versionados de B01/B03/B05/B07 e catálogo de Unova. **Nenhum `game/Data` real foi relido pelo GitHub**, e nenhum arquivo do usuário, save, ZIP de origem ou executável foi baixado.

## Resultado do inventário versionado

| Escopo | MapIDs | Quantidade | Grau de prova |
|---|---:|---:|---|
| Base / outros não atribuídos | 1; 22; 32–33; 42–43; 48; 76–275 | **207** | Físicos registrados na B01; sem atribuição regional definitiva |
| Kanto | 300–441 | **142** | B01 físico + atribuição por manifesto regional B04 (autodeclarada) |
| Johto | 600–699 | **100** | B01 físico + atribuição por manifesto regional B04 |
| Hoenn | 700–898 | **199** | B01 físico + atribuição por manifesto regional B04 |
| **Total físico B01** | Sem sobreposição entre os grupos | **648** | Baseline com SHA-256, não atualização ao vivo |
| **Sinnoh (retenção administrativa)** | **442–517** | **76** | Não é instalação jogável |
| └ Geometrias privadas B07 | 442–495 | **54** | Apenas terreno, sem eventos do doador |
| └ Placeholders excluídos | 496–517 | **22** | Sem mapa físico inventado |
| **Unova (candidatos vazios em 1–599)** | Inclui 518–599 e outras lacunas menores | **174** | **Candidatos**, não reserva/alocação |
| └ Janela contígua preferida Unova | 518–599 | **82** | Não foi homologada |
| Hoenn protegido conservadoramente sem mapas físicos B01 | 899–999 | **101** | Não liberar só por ausência física |
| Sinnoh legado, sem permissão multirregional | 800–805 | **6** | Aparece no bloco B01 atribuído a Hoenn, **não instalar Sinnoh sobre ele** |

Os números são a fotografia de B01 reconciliada com B04/B05. A B04 inicialmente coletava apenas IDs com 3–5 dígitos e omitira 31 IDs físicos de 1–2 dígitos; a B05 impede que essa diferença de 617 × 648 seja esquecida.

## Definições que não devem ser confundidas

- **`NATIVE_PHYSICAL_B01_WITH_MANIFEST_ATTRIBUTION`**: ID consta no inventário físico B01, enquanto a etiqueta de Kanto/Johto/Hoenn decorre de manifestos. Não garante completude de mapas ou direitos sobre recursos.
- **`ADMINISTRATIVE_HOLD_NOT_INSTALLED`**: Sinnoh 442–517 foi separado por planejamento; 54 mapas têm terreno no stage privado e 22 ficam excluídos. Não significa que a região esteja disponível no jogo.
- **`VACANT_CANDIDATES_NOT_RESERVED_OR_INSTALLED`**: 174 IDs de Unova não conflitam com a fotografia B01 e a retenção Sinnoh; **não** comprova permissão futura para usar qualquer um deles.
- **`legacy Sinnoh 800–805`**: o piloto isolado anterior não autoriza que esses MapIDs sejam introduzidos no Decades multirregional, pois estão no bloco 700–898 ocupado e atribuído a Hoenn.
- **`MapIDs >=1000`**: permanecem bloqueados por falta de validação nativa.

**Reservas futuras de Kanto, Johto, Hoenn, Sinnoh e Unova: não comprovadas.** Um manifesto público ou mapa fisicamente ausente não equivale à verificação R07 de todas as reservas ainda não instaladas.

## Entrega executável

- [Auditor G03](../scripts/regions/audit_sinnoh_g03_regional_mapids.py) — lê **somente** JSONs públicos do repositório; passa antes pelo auditor B05 e recusa divergências, colisões, mudança de flags e variação dos IDs 442–517.
- [16 testes de regressão](../tests/test_sinnoh_g03_regional_mapids.py) — cenários positivos e negativos de sobreposição, contadores, mudanças de baseline, falso R07, Unova instalada sem evidência, formato e proteção do legado.
- [GitHub Actions G03](../.github/workflows/sinnoh-g03-mapids.yml) — roda os testes e publica `.blue-work/sinnoh-g03/matrix.json` como artifact **de metadados**, sem game, saves, PNGs ou dados pessoais.

Para gerar o relatório na sua cópia do repositório, quando necessário:

~~~bash
python scripts/regions/audit_sinnoh_g03_regional_mapids.py
python -m unittest discover -s tests -p "test_sinnoh_g03_regional_mapids.py" -v
~~~

**Status esperado:** `STATIC_MATRIX_RECONCILED_FUTURE_RESERVATIONS_UNVERIFIED`.

## Limites e próximos passos

1. **R07 ainda não foi aprovado**: falta confronto com todas as reservas futuras das regiões, inclusive conteúdo não instalado, com hash do jogo e revisão de autoria.
2. A existência dos 54 arquivos de terreno em stage B07/B09 não valida eventos, transferências dinâmicas, entradas na região, caminho de save, nem a propriedade dos tilesets.
3. **B10/B11** dependem do Windows Sandbox e verificação de saves do host; **Game.exe/JoiPlay** só têm homologação por teste real.
4. As barras **B/C/D de Sinnoh continuam 0/13**; G03 completa apenas a engenharia offline do GitHub, sem alocar MapIDs nem instalar conteúdo.

**Próxima etapa:** **G04** — endurecimento das proteções B10 Windows Sandbox e seus testes negativos; não habilitar VM, iniciar jogo ou migrar saves pela CI.
