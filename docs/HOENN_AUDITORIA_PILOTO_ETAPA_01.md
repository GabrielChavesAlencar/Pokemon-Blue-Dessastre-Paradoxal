# Hoenn — Etapa 01: auditoria do piloto existente (sem Codex)

**Data:** 14/11/2026  
**Projeto:** [Pokémon Blue: Dessastre Paradoxal](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal)  
**Escopo:** arquivos da branch `main` do GitHub, scripts originais e catálogos publicados.  
**Estado de aceite:** **auditoria estática / preparação técnica**. **Nenhum mapa novo foi instalado ou declarado jogável no Game.exe.**

> Este documento atualiza as informações *históricas* nos planos de Hoenn que ainda diziam não existir nenhum piloto. Já existe um **gerador experimental de cópia independente**. Sua existência não prova que os mapas funcionem no executável.

## 1. Componentes efetivamente presentes no repositório

| Recurso | Evidência | Resultado |
|---|---|---|
| Piloto isolado | `scripts/regions/pilot_hoenn.py` | Gerador de cópia do jogo, sem alterar a instalação principal |
| Rotinas do jogo | `scripts/regions/HoennPilot.rb` | Métodos de início, resgate, NPCs, cura, compra, treinadores e música |
| Auditoria de origem | `scripts/regions/audit_hoenn_baseline.py` | Conferência RXDATA/MapInfos/Tilesets e colisões de IDs (requer arquivos locais) |
| Preparação do ZIP | `scripts/regions/prepare_hoenn_source.py` | Seleção segura e isolada de materiais do projeto doador |
| Catálogo publicado | `site/public/data/hoenn-pilot.json` | Nove locais, encontros de 3 rotas e quatro treinadores |
| Registro de região | `site/public/data/regions.json` | HOENN segue com `status: planned`, sem promoção indevida |
| Auditoria nova | `scripts/regions/audit_hoenn_pilot_contract.py` | Contrato somente leitura entre script, catálogos, nós de mapa e handlers |
| Regressão nova | `tests/test_hoenn_pilot_contract.py` | Testes positivos e de falha intencional por inconsistência |
| CI ampliada | `.github/workflows/regression.yml` | Inclui contrato Hoenn `--strict` e `ruby -c` |

### Fonte de geometria e limite de licenciamento

O gerador exige **revisão fixa** do projeto doador: `c59233bdbaac4fbfeca6aa01c7f05be628da2a92`. Não é permitido instalar mapas ou sons genéricos para substituir a revisão auditada, nem publicar recursos do doador sem os direitos necessários. Este trabalho **não enviou nenhum recurso externo, ROM, áudio, RXDATA ou Game.exe ao GitHub**.

O piloto é construído em cópia isolada, com remapeamento de MapIDs para números livres entre **700 e 999** encontrados na instalação local. Esses números não são MapIDs definitivos da campanha multirregional. A reserva de Johto e futuras regiões exige nova auditoria antes da integração ao jogo principal.

## 2. Inventário real de mapas do código

| ID da fonte | Área do piloto | Cobertura identificada |
|---:|---|---|
| 7 | Littleroot Town | Exterior da cidade; entrada na casa e no laboratório |
| 8 | Casa do jogador | Spawn do novo jogo, mãe, relógio, escada, perfil |
| 11 | Laboratório de Birch | Birch e três objetos de seleção de iniciais (atualmente inativos antes do resgate) |
| 101 | Route 101 / Rota 101 | Grama, ligação Littleroot–Oldale, resgate com Birch |
| 12 | Oldale Town | Exterior; ligações com rotas e portas do Center/Mart |
| 13 | Centro Pokémon de Oldale | Enfermeira, cura e interação de balcão |
| 14 | Poké Mart de Oldale | Vendedor e interação de balcão |
| 102 | Rota 102 | Quatro treinadores e encontros; sem acesso final a Petalburg |
| 103 | Rota 103 | Encontros; batalha de rival ainda não implementada |

**Conectividade codificada:** cinco pares de entradas/escadas e quatro conexões de borda. **Spawn:** mapa fonte 8, coordenadas (25, 6), **dentro da casa**, não no caminhão de Emerald. A conectividade topológica nos scripts não substitui a verificação da passabilidade real dos tiles da fonte; `validate_geometry()` faz essa verificação durante o staging privado.

**Correção da Etapa 01:** `audit_hoenn_baseline.py` verificava apenas cinco mapas (7, 8, 11, 12, 101) na origem auditada; agora inclui os **nove** mapas efetivamente usados, especialmente Centro, Mart, rotas 102 e 103. O teste sintético preexistente segue usando `PILOT` como referência, portanto acompanha o conjunto completo.

## 3. Inventário dos encontros e treinadores

### Encontros de grama definidos pelo gerador

| Mapa | Pokémon | Soma das chances |
|---|---|---|
| Rota 101 | Zigzagoon 45%, Poochyena 35%, Wurmple 20% | 100% |
| Rota 102 | Poochyena 30%, Zigzagoon 15%, Wurmple 30%, Lotad 10%, Seedot 10%, Ralts 4%, Surskit 1% | 100% |
| Rota 103 | Poochyena 60%, Zigzagoon 20%, Wingull 20% | 100% |

As porcentagens são as **definições do piloto** e não a distribuição final de Emerald ou de toda Hoenn. O site apresenta os valores-base das rotas. A auditoria compara **espécies, pesos e intervalos de níveis** entre JSON e script, rejeitando divergências ou tabelas cuja soma não seja 100%.

### Quatro treinadores codificados na Rota 102

| Classe | Nome | Equipe-base | Coordenada na fonte |
|---|---|---|---|
| Youngster | Calvin | Poochyena 5 | (33, 14) |
| Bug Catcher | Rick | Wurmple 4, Wurmple 4 | (25, 15) |
| Youngster | Allen | Zigzagoon 4, Taillow 4 | (19, 4) |
| Lass | Tiana | Zigzagoon 4, Shroomish 4 | (8, 7) |

**Importante:** os níveis são exclusivamente para dados-base e não devem prevalecer sobre a escala dinâmica do Blue. O gerador cria definições PBS com **versão 102** para não colidir com os treinadores originais; exige auditoria de conflitos no PBS da instalação. O teste estático não comprova linha de visão, movimento de NPC, batalha nativa ou persistência de vitória/derrota.

## 4. Diferenças observáveis em relação ao detonado Emerald

| Necessidade da campanha | Estado encontrado | Próxima ação |
|---|---|---|
| Começar na mudança/caminhão e explorar casa | Parcial: spawn já dentro da casa | Implementar abertura própria, preservando save/viagem |
| Relógio e conversa com mãe | Handlers Ruby presentes | Testar ordem, flags, texto, retorno e save/reload |
| Birch perseguido por Zigzagoon na Route 101 | Handler de resgate presente | Testar combate real, derrota, cancelamento e estados |
| Seleção pela maleta com três Poké Balls | **Diferente:** menu de diálogo durante o resgate | Trocar por evento da maleta/objetos quando houver mapa auditado |
| Primeira batalha Brendan/May na Route 103 | Não implementada no piloto | Criar NPC/evento, equipe por inicial, derrota e vitória |
| Pokédex e Poké Balls após retorno ao laboratório | Parcial: cinco Balls são dadas com o inicial; Pokédex não implementada pelo plugin | Ajustar distribuição sem duplicar itens |
| Running Shoes da mãe | Não implementado no plugin | Integrar ao marco correto |
| Route 102 com treinadores/selvagens | Presets e eventos preparados | Validar batalhas, contato, derrotas, evolução e recompensas |
| Petalburg, Norman e Wally | Fora do recorte de 9 mapas | Etapa seguinte, com mapas reais |
| Todos os NPCs, placas, itens no chão e falas PT-BR | Não inventariados por este piloto reduzido | Auditar os RXDATA doadores e implementar com dados reais |

**Não corrigido nesta fase:** a história incompleta. Modificar o comportamento do jogador sem os RXDATA reais e os testes nativos seria promover um evento não aprovado. Essa parte pertence à etapa seguinte.

## 5. Correções e verificações adicionadas

1. **Ampliação da auditoria de origem para nove mapas**, bloqueando arquivos fonte ausentes/alterados nos mapas novos.
2. **Novo auditor de contrato, somente leitura:** verifica inventário de mapas, grafo das ligações, integridade dos handlers, colisões estáticas de eventos, tabelas de encontros (incluindo pesos e níveis), quatro equipes e estado `planned/prototype`.
3. **Testes de regressão com mutações propositais:** taxa selvagem alterada, equipe publicada incorreta, handler ausente e promoção indevida de Hoenn para jogável devem falhar.
4. **CI da branch main:** `unittest discover` passa a incluir os testes Hoenn, além de `audit_hoenn_pilot_contract.py --strict` e `ruby -c scripts/regions/HoennPilot.rb`.

### Comandos para reprodução

```powershell
py -3 -m unittest discover -s tests -p "test_hoenn_*.py" -v
py -3 scripts/regions/audit_hoenn_pilot_contract.py --strict
ruby -c scripts/regions/HoennPilot.rb
```

**Estes testes não requerem o Game.exe nem o ZIP doador.** A auditoria `audit_hoenn_baseline.py` dos bytes reais exige os arquivos de origem auditados, MapInfos e Tilesets do `game/Data` privado. Ela não foi executada com esses arquivos nesta etapa.

## 6. Resultado de aceite e próxima etapa

| Barra | Situação |
|---|---|
| Definições/scripts de piloto existentes | **SIM** — nove mapas como escopo, 3 tabelas selvagens, 4 treinadores, 1 plugin Ruby |
| Contrato automatizado de arquivos públicos | **Executado via GitHub Actions; conferir a última CI do commit publicado** |
| Arquivos RXDATA reais auditados nesta sessão | **NÃO**, ausentes do GitHub |
| Cópia Hoenn efetivamente instalada e compilada aqui | **NÃO** |
| Caminhada completa no Game.exe e Windows | **NÃO** |
| Android/JoiPlay | **NÃO** |
| Abertura Emerald canônica concluída | **NÃO** |
| Acesso até Petalburg | **NÃO** |
| Fases de Hoenn aprovadas como jogáveis | **0 novas aprovações nesta auditoria** |

**Próxima etapa proposta:** concluir a abertura de Littleroot → Route 101 → Oldale → Route 103, com batalha do rival, Pokédex e Running Shoes, mantendo uma cópia isolada do jogo. Depois inventariar a continuação física da Route 102 até Petalburg usando mapas originais auditados. Não importar outras rotas ou declarar progressão jogável antes dessa verificação.

**Links relacionados:** [detonado Emerald](HOENN_DETONADO_EMERALD_REFERENCIA_ORGANIZADA.md) · [plano passo a passo](HOENN_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) · [preparação do ZIP](HOENN_PREPARACAO_ZIP_E_RECURSOS.md).
