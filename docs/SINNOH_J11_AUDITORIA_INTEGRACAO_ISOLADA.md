# Sinnoh J11 — auditoria independente e integração física isolada (fail-closed)

**Base:** J10-A / PR #244, integrado com 14/14 workflows aprovados. Issue atual: J11 #241. Cinco RXDATA geométricos foram gerados em ambiente isolado, mas **não estão instalados e não foram aprovados no motor real**.

## Auditoria entregue

A ferramenta scripts/regions/audit_sinnoh_playable_j11.py reconstrói em memória os cinco mapas originais da J10-A e verifica:
- Cinco símbolos e dimensões exatas: quarto 20×15, térreo 25×19, Barry 23×18, Lago Verity 38×27 e laboratório Rowan 29×21.
- Round-trip Ruby Marshal de cinco RPG::Map, três camadas por mapa, todas as células iguais às fontes, nenhum evento/áudio do doador, SHA-256 de cada RXDATA e referência de tileset interno provisória (id=1, NÃO registrado no jogo).
- PNG procedural 256×256 com 32 tiles de 32×32; CRCs de todos os chunks, zlib com limite, pixels RGBA, filtros e número de tiles distintos. Integridade técnica **não** equivale a licença ou passabilidade.
- Cinco SVGs XML, grade geométrica completa, ausência de scripts/imagens externos, SHA-256 e comparação exata com as cenas originais. São prévias esquemáticas, não capturas de gameplay.
- BFS de caminhabilidade **apenas potencial**, com classes provisórias de obstáculos, água e caminho, verificando acesso proposto aos pontos de interesse. A tabela de passagens, prioridade e direção de RPG::Tileset **ainda não foi validada**.
- Nove slots simbólicos da J02: cinco geometrias originais, quatro fontes exteriores históricas sem prova de direito de uso. Nenhum dos quatro mapas privados é distribuído/copiado.
- Contratos CH06/J04: 16 portais direcionais, oito pares reversíveis, cinco NPCs, três Poké Bolas e spawn inicial. Coordenadas, sprites, IDs e colisões reais continuam SEM aprovação.

## Comandos sem Game.exe, saves ou instalação

Auditoria em memória, sem escrita:

    python scripts/regions/audit_sinnoh_playable_j11.py

Gerar plano de leitura privado, sem MapXXX.rxdata:

    python scripts/regions/audit_sinnoh_playable_j11.py --write-plan

O segundo comando cria uma única vez o JSON inerte .blue-work/sinnoh-j11-readonly-plan.json; nunca sobrescreve. O BAT opcional SINNOH_J11_AUDITAR_PRIVADO.bat executa apenas esta segunda operação. Não há escrita em game/, Data/, saves, arquivos de outras regiões, pasta J09, staging J03, nem instalação Android.

## Evidências privadas opcionais — não inventar aprovação

É possível indicar, apenas em workspace privado de uma cópia de trabalho e somente quando disponíveis:

- --donor-zip .blue-work/arquivo-autorizado.zip: o auditor J09 verifica os quatro terrenos históricos contra hashes B00, MapInfos e dimensões. Lê sem extrair e sem publicar, mas não concede licença.
- --baseline-dir .blue-work/sinnoh-j11-baseline/Data: uma CÓPIA isolada de MapInfos.rxdata e Tilesets.rxdata, não a instalação real do usuário. O validador lê o inventário, sem criar MapIDs.
- --review-dir .blue-work/sinnoh-j11-reviews: recibos r07.json e r08.json em schemas J09, mais j10a-art-rights.json para a imagem procedural; devem ser fornecidos somente depois de revisão real. Recibos locais jamais constituem aprovação independente.

A revisão da arte, apenas quando efetivamente realizada, aceita um objeto JSON com exatamente os campos schema=1, region=SINNOH, stage=J11, kind=J10A_PROCEDURAL_ORIGINAL_ART_RIGHTS, tileset_sha256 com o hash medido, license_reference e review_reference reais (12–240 caracteres), locally_reviewed=true, private_qa_permission=true, independent_approval=false. **Não crie esse recibo preventivamente.**

R07 exige nove MapIDs sem conflitos com MapInfos e reservas de Decades, Kanto, Johto, Hoenn e Unova, amarrados ao baseline real. R08 exige direitos individualizados dos quatro exteriores, cinco interiores/lago e do PNG/tilesets usados; sempre sujeito a revisão humana/independente. Nenhum desses documentos privados é exigido pelo CI ou considerado aprovado por ausência.

## Gates para integração nativa isolada (J11 → J12)

| Gate | Exigência | Estado |
| --- | --- | --- |
| Cinco geometrias novas | SHA, três camadas, PNG, SVG, conectividade provisória | Verificadas offline |
| Quatro terrenos históricos | Fonte B00 privada e direitos efetivos | Pendente |
| R07 | Baseline MapInfos e reservas de cinco regiões | Pendente |
| Tilesets | Registro de RPG::Tileset, passagens, priorities e colisão do motor | Pendente |
| R08 | Permissões para todos os nove mapas e todos os recursos gráficos | Pendente |
| J04 | 16 portais, cinco handlers, três bolas, coordenadas e sprites revisados | Pendente |
| J03/J06 | Overlay/instalação somente em cópia QA isolada | Pendente |
| R09/J12 | 43 testes reais Windows e 1 Android JoiPlay | 0/44 |

Quando as autorizações forem comprovadas, reutilizar J09 para intake por SHA, J03 para stage/conversão privados, J04 para eventos, J06 para cópia QA segura, J07/J08 para testes. O auditor J11 **não escreve nove mapas** nem altera seus IDs ou obriga integração dos quatro exteriores protegidos.

O projeto continua Sinnoh PILOT_NOT_INSTALLED_NOT_PLAYABLE, engenharia J01–J08 8/8, nativa 0/8, 0/9 mapas instalados, 0/44 QA nativa. Decades, Kanto, Johto, Hoenn, o Game.exe e saves pessoais não foram acessados nem alterados.

## Testes e publicação

    python -m unittest discover -s tests -p test_sinnoh_j11_physical_intake_gates.py -v

Há 50 casos, positivos e negativos: XML ativo em SVG, PNG falso/CRC, RXDATA corrompido, manifesto SHA falso, layers alteradas, entrada/landmark bloqueados, recepção R07 conflitante, fontes e revisão ausentes, falsa autoria, falsos direitos, sobrescrita e symlinks, além da preservação das regiões/estado nativo. O CI da J11 roda também regressões J09/J10-A e o portal. Seu único artifact é o plano JSON sanitizado; nenhuma imagem PNG, RXDATA, ZIP privado ou save.
