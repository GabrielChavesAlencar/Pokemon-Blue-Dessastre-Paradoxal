# Unova SP05 — piloto Cheren: QA privado, nunca instalador

Projeto: Pokémon Blue: Dessastre Paradoxal. Data: 17/11/2026. Região: Unova — narrativa Pokémon White.

**Estado real:** o manifesto SP05, o programa de QA e seus testes foram criados. Ainda NÃO recebemos o sprite real licenciado de Cheren, um documento verificável de autorização ou a instalação do Game.exe para testar. Não há NPC instalado.

## Entrega

- [Manifesto do piloto](../data/regions/unova-sp05-cheren-pilot.json): NPC UNOVA_NPC_CHEREN, área simbólica Nuvema Town, sem MapID/posição de evento inventados, nome reservado Graphics/Characters/UNOVA_NPC_CHEREN.png.
- [Validador e preparador](../scripts/regions/unova_sp05_cheren_pilot.py): usa exatamente o ZIP, o relatório SP03 e o relatório SP04 correspondentes, conferidos por SHA-256.
- O sprite precisa ser PNG estático RGBA8, 4 colunas x 4 linhas (16 quadros), cada quadro com pixels visíveis. Os bytes são decodificados para medir silhueta, tamanho visível e posição de pés por direção.
- A referência de tamanho é um PNG real de Graphics/Characters do Decades. A faixa preliminar é altura visível 80%–120% e largura 80%–125% da referência. São guardas de QA, não garantias de que o jogo irá mostrar no tamanho correto.
- Comprovante local de permissão, autor e URL HTTPS são obrigatórios para staging. O script registra hash e declaração, **não comprova autenticidade nem direitos de redistribuição**.
- O resultado fica exclusivamente em .blue-work/unova/qa/sp05-cheren/HASH/Graphics/Characters/UNOVA_NPC_CHEREN.png, acompanhado de manifesto privado. Não há alteração no Decades principal, Game.exe, Blue-Story, saves ou PBS.

**Observação técnica:** no Essentials e RPG Maker XP, folhas de personagens de campo normalmente usam divisão 4x4. Isso não valida, sozinho, que os quadros estão na ordem down/left/right/up. O script mede pixels, mas ainda requer revisão visual de direções, pivô, alinhamento, animação e escala no renderizador real.

## Passos no Windows sem PowerShell

1. Atualize o repositório e abra [UNOVA_CHEREN_SP05_QA.bat](../UNOVA_CHEREN_SP05_QA.bat).
2. Escolha a opção 1 para consultar o plano e os bloqueios sem precisar do ZIP.
3. Quando tiver os arquivos reais, escolha a opção 2 e selecione pelas janelas: ZIP de sprites, relatórios SP03/SP04 privados, imagem PNG de referência Decades, documento de permissão, autor e URL de origem.
4. O programa oferece os arquivos candidatos a Cheren identificados no SP04 para você escolher. Nenhum asset é selecionado automaticamente.
5. Se a validação técnica passar, somente a área privada de QA recebe a imagem com nome exclusivo. Não há comando para instalar no jogo principal.
6. A saída JSON registra os resultados dos 16 quadros, hashes de fonte/referência, proporção de silhueta e o bloqueio de aprovação definitiva.

Operação alternativa via Python:
- Planejamento: python scripts/regions/unova_sp05_cheren_pilot.py
- Janelas: python scripts/regions/unova_sp05_cheren_pilot.py --gui
- Staging técnico: python scripts/regions/unova_sp05_cheren_pilot.py --stage --zip FONTE.zip --member Graphics/Characters/Cheren.png --sp03 RELATORIO_SP03.json --sp04 RELATORIO_SP04.json --reference-sprite SPRITE_DECADES.png --rights-evidence COMPROVANTE.txt --rights-holder "Autor" --source-url https://eeveeexpo.com/resources/25/

## Critérios ainda pendentes para liberar Cheren

- [ ] ZIP verdadeiro auditado (SP03) e Cheren visualmente identificado (SP04).
- [ ] Direitos e autoria **verificados**, incluindo os titulares das artes ripadas. Um arquivo de crédito não autoriza automaticamente redistribuição.
- [ ] Layout, quadro parado, direção, pivô, pés e escala com protagonista comparados visualmente.
- [ ] Nuvema com MapID real, tile passável e evento de Cheren revisado, PT-BR e flags regionais próprias.
- [ ] NPC testado numa **cópia isolada do Game.exe**, com movimentação e save/reload.
- [ ] NPC testado no JoiPlay/Android e regressões das demais regiões.
- [ ] Autorização para incluir sprite em pacote de distribuição e instalador Blue-Story.

**O script NÃO faz instalação ou QA jogável**: gera somente o arquivo de sprite numa área privada para revisão posterior. Não presume licenças, não declara Game.exe ou Android aprovados.

## Barras

E — Documentação e ferramentas: **4/8 (50%)**. A/B/C/D: **0/8** nesta entrega; Unova jogável: **0/32**. SP05 prepara o primeiro piloto, mas E04/E05/E06/E08 ainda exigem arquivos reais, direitos e QA.

Próximo passo real: fornecer o ZIP de sprite da fonte original, o comprovante de uso e a referência Decades para executar SP03→SP04→SP05 e preparar testes nativos quando Nuvema estiver disponível.
