# Unova A05 — proposta auditável de MapIDs baseada em B01, B04 e B05

**17/11/2026 · Pokémon Blue: Dessastre Paradoxal · Estado:** planejamento baseado em snapshot histórico, **não é alocação de MapIDs**.

## Fonte usada

O usuário forneceu o MD MAPIDS_DECADES_SINNOH_UNOVA_2026-11-17(1).md. Seu SHA-256 é:

e50ae9a9bbb3a93db54523e0e74c0bd2ad0e0272b87643fad8ee07bd17705c95

O conteúdo confirma os números do [inventário B05 de Sinnoh](../data/regions/sinnoh-b05-mapid-planning.json), já publicado e protegido pelo [auditor B05](../scripts/regions/audit_sinnoh_b05_mapid_planning.py). Também existe o [relatório de MapIDs do projeto](MAPIDS_DECADES_SINNOH_UNOVA_2026-11-17.md) com o mesmo desenho de retenções e ocupação. O MD fornecido é uma **síntese de B01/B04**, não uma nova leitura da instalação do Game.exe ou um manifesto de reserva homologado.

A A05 reutiliza esses dados e falha se os contratos existentes de B01/B03/B05 e U03 forem alterados.

## Resultado conservador

| Bloco | IDs | Quantidade | Decisão de planejamento |
|---|---|---:|---|
| Decades/base não atribuído | 1, 22, 32–33, 42–43, 48, 76–275 | 207 | Ocupados; não reutilizar |
| Kanto | 300–441 | 142 | Ocupados |
| Johto | 600–699 | 100 | Ocupados e protegidos |
| Hoenn | 700–898 | 199 | Ocupados, alocador protege 700–999 |
| **Total histórico ocupado** | | **648** | B01; não confundir com 617 reportados pelo B04 antigo |
| **Sinnoh** | **442–517** | **76** | Retenção administrativa, não instalação |
| **Unova primeiro candidato** | **518–599** | **82** | Maior bloco contínuo histórico; sem reservas oficiais |
| Unova expansão histórica | 276–299, 49–75, 2–21, 23–31, 34–41, 44–47 | **92** | Alternativas sem autorização de uso |
| **Total candidato de Unova** | | **174** | Apenas vagas vistas no snapshot |
| Hoenn expansão protegida | 899–999 | 101 | Não usar apesar de não haver MapNNN físico |
| IDs 1000+ | | — | Compatibilidade não homologada |

O coletor B04 antigo deixou de enumerar 31 mapas com MapIDs de um ou dois dígitos: 1, 22, 32–33, 42–43, 48 e 76–99. Esses IDs **estão ocupados** segundo o B01 e são excluídos pelo A05.

**Detalhe fundamental:** o catálogo [U03](../data/regions/unova-u03-areas.json) contém 74 *áreas simbólicas*, não 74 mapas RXDATA. Nuvema, casa e laboratório, por exemplo, podem exigir vários MapIDs físicos. Os 82 candidatos do bloco prioritário **não são atribuídos a nenhuma área ou MapID de origem**.

## Entrega de software

- [Manifesto A05](../data/regions/unova-a05-mapid-candidates.json): registra origem, hashes, faixa Sinnoh retida, bloco prioritário, faixas alternativas, proteções e MapIDs atribuídos **vazios**.
- [Auditor A05](../scripts/regions/audit_unova_a05_candidates.py): executa primeiro o auditor B05 (B01+B03+B05+U03), calcula as 174 vagas do snapshot, verifica faixas protegidas e bloqueia quaisquer campos falsamente aprovados.
- [32 testes de A05](../tests/test_unova_a05_candidates.py): falsos MapIDs, licenças/instalações, contagens e colisões B04, MapInfos histórico adulterado, Sinnoh/Hoenn protegidos, A04 falso e divergências de MapIDs.
- [UNOVA_A05_PLANEJAR_MAPIDS.bat](../UNOVA_A05_PLANEJAR_MAPIDS.bat): uso por duplo clique no Windows, sem PowerShell. Compara opcionalmente um relatório privado verdadeiro do [auditor A04](../scripts/regions/audit_unova_a04_mapids.py).

### Como usar sem PowerShell

1. Atualize o repositório do Pokémon Blue.
2. Dê dois cliques em UNOVA_A05_PLANEJAR_MAPIDS.bat.
3. Se já gerou um relatório A04 no seu PC, escolha **Sim** e selecione a04-mapids-HASH.json dentro de .blue-work/unova/audit/. O relatório deve ter sido obtido apontando a instalação real do Decades em [UNOVA_A04_AUDITAR_MAPIDS.bat](../UNOVA_A04_AUDITAR_MAPIDS.bat).
4. Se ainda não tem esse relatório, escolha **Não**. O programa gera a proposta histórica **sem inventar que o Game.exe atual foi auditado**.
5. O resultado fica em .blue-work/unova/audit/a05-candidates-HASH.json. Pode enviá-lo nesta conversa para a próxima análise.

A análise de A04 verifica formato, hash do relatório, coerência dos arquivos declarados e contagens. Quando há conflito novo com IDs que eram candidatos em B01, registra explicitamente os números. Mesmo que o MapInfos atual tenha o mesmo SHA do B01, **a compatibilidade com reservas futuras, scripts e uso regional ainda precisa ser examinada**. Isso não é homologação automática.

Terminal CMD opcional:

python scripts/regions/audit_unova_a05_candidates.py --write

python scripts/regions/audit_unova_a05_candidates.py --a04-report ".blue-work\unova\audit\a04-mapids-HASH.json" --write

## Próxima etapa real depois da A05

1. Reconferir arquivo MapInfos atual e o histórico de reservas de Kanto/Johto/Hoenn/Sinnoh, por manifests reais, incluindo espaço de expansão.
2. Corrigir/descrever qualquer colisão identificada; não usar IDs com conflitos, mesmo que visualmente vazios.
3. Receber arquivo real de mapas Unova (original ou mapa próprio licenciado), com árvore de MapInfos de origem; mapear cada arquivo MapNNN e suas dependências.
4. Criar somente numa cópia privada uma proposta determinística source_map_id → destination_map_id, incluindo interiores, links, teletransportes e IDs em scripts; nunca sobrescrever a base.
5. Revisar passabilidade, gráficos, tilesets, rights, rollback e testes Game.exe antes de aprovar os primeiros MapIDs nativos.

### Progresso honesto

A ferramenta A05 pode ser criada agora com os dados históricos. **A04 ainda precisa de relatório real e conciliação de reservas; A05 não atribuiu IDs à região**. As barras de implementação continuam: **A = 0/8, B/C/D = 0/8, E = 4/8; Unova jogável 0/32.** A existência de 174 candidatos não representa 174 mapas instalados.
