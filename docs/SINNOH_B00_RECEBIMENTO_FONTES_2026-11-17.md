# Sinnoh — Barra B / Etapa 00: receber os arquivos reais

**Atualização (17/11/2026):** ZIP e créditos **recebidos e auditados**. Veja o [inventário real de 76 mapas](SINNOH_B00_FONTE_REAL_AUDITORIA_2026_11_17.md). **B/C/D = 0/13**, pois há 22 mapas vazios, faltam interiores/warps/NPCs e direitos de uso por recurso; Game.exe/JoiPlay não foram executados.

## Fonte principal indicada para avaliação

**Pokémon World V18** — projeto compartilhado pelo próprio criador como pacote RMXP/Essentials v18 com mapas recriados de Sinnoh e de outras regiões. O autor autorizou o reaproveitamento de partes do projeto publicamente na discussão; isso **não comprova licença de todos os tilesets, músicas, gráficos e outros trabalhos de terceiros**.

- Pacote original: https://www.mediafire.com/file/tq5w0in2xt2peb1/Pokemon_World_V18.zip/file
- Créditos originais: https://www.mediafire.com/file/gdtsjg5lbnstzo1/Credits.txt/file
- Postagem e discussão de permissão: https://www.reddit.com/r/PokemonRMXP/comments/wsiyyr
- Fonte já documentada anteriormente, **não substituída**: Pokémon Ancient Platinum (Phantombass), https://eeveeexpo.com/threads/9085/ . Para este, código editável e permissão de uso não foram demonstrados.
- Recurso gráfico adicional opcional: https://www.deviantart.com/alchemybats/art/DPP-Style-Sinnoh-Overworld-Tileset-V-2-1205547742 — o artista declara uso em fangames; conferir termos e créditos antes de integrar.

**Os links MediaFire foram localizados na postagem do autor, mas não foi possível confirmar diretamente que o download funciona neste ambiente.**

## O que o usuário deve enviar aqui no ChatGPT

1. `Pokemon_World_V18.zip`, baixado diretamente da página do criador, **sem recompactar ou executar**.
2. `Credits.txt` do mesmo autor.
3. **Somente se for necessário para a etapa seguinte:** cópia privada dos arquivos-base de `game/Data` do Decades com `MapInfos.rxdata`, `Tilesets.rxdata` e `MapNNN.rxdata`, para confrontar IDs locais. Não publicar saves pessoais ou um jogo completo no GitHub.

Se o ZIP for maior que o limite de upload da conversa, solicitar um pacote reduzido que mantenha os caminhos de `Data/`, `Graphics/Tilesets/`, `Graphics/Autotiles/`, `Graphics/Characters/`, `PBS/` e o índice original `MapInfos.rxdata`. Não misturar com a instalação principal.

## Recebimento seguro por ferramenta

A [ferramenta B00](../scripts/regions/audit_sinnoh_b00_intake.py) reaproveita o [auditor de fontes](../scripts/regions/audit_sinnoh_source.py). Ela não descompacta, não instala nem executa conteúdo de terceiros: verifica estrutura do ZIP, número bruto de mapas de **todas** as regiões do doador, inventário de tilesets/autotiles/characters/PBS e hash dos créditos.

Com os arquivos em disco, a equipe técnica pode usar:

```bash
python scripts/regions/audit_sinnoh_b00_intake.py --source "/arquivo/Pokemon_World_V18.zip" --credits "/arquivo/Credits.txt"
```

Sem nenhum arquivo, o comando simplesmente mostra `AWAITING_USER_FILES` e mantém `0/13`:

```bash
python scripts/regions/audit_sinnoh_b00_intake.py
```

O número bruto de `MapNNN.rxdata` do ZIP **não equivale** à quantidade de mapas de Sinnoh; será preciso auditar `MapInfos.rxdata`, mapear hierarquia/nomes e evitar colisões em Decades/Kanto/Johto/Hoenn. Tilesets e eventos devem ser revistos separadamente.

## A seguir (sem testes manuais por enquanto)

Depois que os dois arquivos forem recebidos, executar os auditores existentes de fontes e RXDATA, identificar mapas reais de Sinnoh e suas dependências, montar proposta de remapeamento com hashes e registros de direitos, e construir a prévia de geometria fora do jogo principal. Eventos/PBS/rivais/viagem usam o Blue, não scripts antigos do doador.

**Gates permanecem fechados:** nenhuma fonte importada, nenhum MapID reservado, nenhum save alterado, nenhum teste Windows/Android realizado. Só promover a Barra B após evidência técnica compatível com os critérios da fase.
