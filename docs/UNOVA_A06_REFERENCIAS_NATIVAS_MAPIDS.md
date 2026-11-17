# Unova A06 — auditoria automática de referências MapIDs (somente leitura)

**Base de entrada:** o resumo A04/A05 fornecido em 17/11/2026 indica 648 MapIDs presentes/declarados na instalação real, SHA-256 de MapInfos 8f2d23d49ee0bb97779b129ffd7d14c161f4bef27fede6b89111ce266760a420, 0 sobreposições, 0 novos conflitos com 174 candidatos históricos e bloco 518–599 não observado. Esse resultado é a saída informada pelo usuário; **o relatório JSON local não foi transferido para o GitHub**, e a A06 ainda não foi executada na máquina do usuário.

## Entrega A06

O [auditor A06](../scripts/regions/audit_unova_a06_references.py) usa as entradas de MapNNN.rxdata verificadas pelo A04, relê cada mapa de maneira **inerte** (Ruby Marshal, sem executar Ruby), confere hash do arquivo e procura comandos de evento tipo 201 de transferir jogador. Ele conta destinos estáticos, referências ausentes do conjunto ocupado, referências ao bloco candidato Unova 518–599, referências ao intervalo Sinnoh 442–517, transferências dinâmicas e comandos de script que não foram executados nem interpretados.

**O que A06 não comprova:** referências em CommonEvents.rxdata, Scripts.rxdata, plugins, eventos criados dinamicamente, portas/conexões especiais, Blue-Story/manifestos nem reservas futuras. Se um mapa não puder ser decodificado, ele é registrado como erro de leitura e a cobertura de A06 fica **parcial**. Uma lista sem conflitos **não homologa MapIDs livres**.

## Como executar sem procurar pastas

A nova versão autocontida de [RUN_UNOVA_MAPIDS.bat](../RUN_UNOVA_MAPIDS.bat) mantém a descoberta automática da instalação em LocalAppData, executa A04, A05 e A06 em sequência, abre o resumo no Bloco de Notas e salva relatórios privados com SHA no cache do pacote: a04-mapids-HASH.json, a05-candidates-HASH.json, a06-references-HASH.json e LEIA_AQUI_UNOVA_MAPIDS.txt.

O BAT pode ser baixado em ZIP, extraído e executado diretamente de Downloads. Não precisa de PowerShell, não pede seleção de pastas e não altera MapInfos, MapNNN, Game.exe, gráficos, eventos ou saves. Requer Python 3.11+ instalado.

## Decisão após A06

Com os arquivos reais disponíveis localmente, interpretar a cobertura do parser, referências estáticas e a lista de destinos ausentes. Independentemente de haver transferências para 518–599, **a reserva de MapIDs continua bloqueada** até examinar CommonEvents/scripts/manifestos e determinar quais mapas de origem de Unova e seus direitos podem ser integrados.

**Progresso:** A = 0/8 (não há mapas Unova homologados), E = 4/8, Unova jogável 0/32. Os contratos e as ferramentas A04–A06 não são mapas instalados.
