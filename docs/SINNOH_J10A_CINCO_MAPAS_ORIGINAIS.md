# Sinnoh J10-A — cinco layouts originais e mapas RMXP privados

Base: PR #243 (J10) integrado, 16/16 checks; próxima etapa J11: issue #241.

## Arquivos originais reproduzíveis

O gerador scripts/regions/generate_sinnoh_original_j10a.py desenha, por algoritmos próprios (não cópia de mapas oficiais), estas cinco geometrias distintas:

| Cena | Tamanho | Composição |
| --- | --- | --- |
| SINNOH_PLAYER_BEDROOM | 20×15 | Quarto com cama, tapete, escrivaninha, computador, prateleira, luminárias, plantas e escada |
| SINNOH_PLAYER_HOUSE_1F | 25×19 | Sala com sofá, mesa, tapete, cozinha com pia e bancada, escada e entrada |
| SINNOH_BARRY_HOUSE | 23×18 | Sala, escada, mesa, computador, estante, sofá e planta |
| SINNOH_LAKE_VERITY | 38×27 | Lago original, margens, floresta, flores, pedras, caminhos e ponte |
| SINNOH_PROFESSOR_ROWAN_LABORATORY | 29×21 | Laboratório com bancadas laterais, máquinas, computadores, corredor e área de trabalho |

O tileset é criado diretamente por Python, sem arquivos de terceiros: PNG de 256×256 pixels com 32 tiles originais de 32×32. Os dados dos cinco mapas possuem três camadas RMXP completas e eventos vazios. **O RXDATA é uma geometria original real, mas ainda não foi integrado nem aprovado no jogo nativo.** Não há NPC, script externo, transferência ou coordenada de evento atribuída automaticamente.

A autoria desses layouts é **programática**, não humana. O gerador não usa o fluxo de J10 que exige declaração de autoria/revisão humana; ele aproveita somente a função de serialização de RPG::Map e confere o resultado pelo auditor J09.

## Gerar sem instalar

Para validar sem escrever, na raiz de uma cópia do repositório:

    python scripts/regions/generate_sinnoh_original_j10a.py

Para produzir os cinco arquivos privados pela primeira vez:

    python scripts/regions/generate_sinnoh_original_j10a.py --build

A única saída em disco será esta pasta nova, ignorada pelo Git:

    .blue-work/sinnoh-j10a-original/
      OriginalJ10A.png
      SINNOH_PLAYER_BEDROOM.rxdata
      SINNOH_PLAYER_HOUSE_1F.rxdata
      SINNOH_BARRY_HOUSE.rxdata
      SINNOH_LAKE_VERITY.rxdata
      SINNOH_PROFESSOR_ROWAN_LABORATORY.rxdata
      previews/*.svg
      manifest.json

Não sobrepõe dados existentes. Não escreve em game/, saves/, .blue-work/sinnoh-j09-authored/ ou na instalação Android. Não executa Game.exe nem JoiPlay. O tileset_id=1 dos arquivos é uma **identificação interna provisória** e não prova que o tileset 1 do jogo corresponde ao novo PNG.

Os cinco SVG representam **prévias esquemáticas auditáveis**, não screenshots de gameplay. As marcações brancas e amarelas são pontos de acesso e de interesse *propostos*, não eventos nativos, portais, coordenadas aprovadas ou uma garantia de passabilidade. O teste de caminhabilidade potencial é feito por BFS com classes de obstáculos sem tabelas reais de passagem/priority.

O GitHub Actions produz e revalida os cinco RXDATA no runner descartável, mas só publica como artifact os cinco SVG e o manifesto sanitizado; **não publica PNG, RXDATA ou fonte do doador**.

## Validações J11 ainda necessárias

1. Rever visualmente os cinco layouts e aprovar os ajustes necessários, sem forjar revisão humana.
2. R08: revisar os direitos de todos os nove mapas, incluindo os quatro exteriores pré-existentes cuja licença não foi comprovada. Se não houver permissão, reconstruir os quatro exteriores autoralmente.
3. R07: conferir MapInfos real e reservas Decades/Kanto/Johto/Hoenn/Unova antes de atribuir os MapIDs de destino.
4. Criar/validar entradas do Tilesets.rxdata, passability, priority, PNG, posições/warps e comportamento de água e obstáculos no motor real.
5. Só após aprovação explícita, transferir os cinco RXDATA para o receptor privado J09 em cópia QA e compilar via J03/J04/J06 16 portais, 5 NPCs e 3 Poké Bolas do Blue.
6. R09/J12: 43 casos nativos Windows e 1 Android JoiPlay com revisão independente, sem ler os saves pessoais.

**Barra preservada:** engenharia J01–J08 8/8; jogabilidade 0/8; mapas instalados 0/9; QA nativa 0/44; R07/R08/R09 pendentes; Sinnoh planned/não jogável.

Testar:

    python -m unittest discover -s tests -p test_sinnoh_j10a_original_geometry.py -v

São 25 testes de geração, hashing, tabela de três camadas, integração estrutural J09, conectividade potencial e proteção contra sobrescrita, com dados de fixture e sem Game.exe.
