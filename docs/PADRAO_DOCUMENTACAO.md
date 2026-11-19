# Padrão para documentação do projeto

[← Central de documentação](INDEX.md)

## Princípios

- A página inicial apresenta o projeto; [INDEX.md](INDEX.md) é o ponto único de entrada na documentação.
- Cada documento deve dizer **o que é**, **para quem serve**, **qual região/componente cobre**, **estado e data de referência**, **pré-requisitos** e **onde encontrar evidências** quando relevante.
- **Não reescrever retrospectivamente relatórios históricos** para transformá-los em status atual. Adicionar cabeçalho de contexto ou referência para a versão mais recente quando comprovada.
- Não confundir PR aprovado, workflow verde, documentação concluída, pacote de instalação pronto e teste nativo Game.exe/JoiPlay.
- Nunca declarar R07/R08/R09, direitos, reservas de MapIDs, mapas instalados ou testes humanos aprovados sem evidências rastreáveis.
- Não publicar ROM, recursos de terceiros ou dados privados/saves.

## Convenções de nomes

- Guias permanentes: `ASSUNTO.md` em letras maiúsculas (preservar nomes existentes).
- Regiões: `KANTO_*`, `JOHTO_*`, `HOENN_*`, `SINNOH_*`, `UNOVA_*`.
- Etapas e evidências: manter seus identificadores originais (`J12`, `L19`, `A16`, etc.) para compatibilidade com issues, scripts e CI.
- Documento novo deve ser linkado em [INDEX.md](INDEX.md) na seção adequada; evite criar uma segunda página inicial.

## Cabeçalho recomendado para novas páginas

```markdown
# Título claro

> Tipo: Guia | Especificação | Relatório histórico | Checklist | Auditoria
> Região/componente: ...
> Estado verificado: planejado | implementado no código | CI testada | QA nativa pendente | QA nativa aprovada
> Referência: AAAA-MM-DD, commit/PR/issue
> Limitações: ...

[← Central de documentação](INDEX.md)

## Objetivo
## Pré-requisitos
## Passos / Especificação
## Validação e evidências
## Pendências
## Documentos relacionados
```

## Mudanças seguras

1. Levante os arquivos e as referências em `README.md`, `site/`, scripts, testes e `.github/workflows/`.
2. Prefira **índices e links** à movimentação massiva de documentos. Links absolutos/relativos podem existir fora do Git.
3. Se houver consolidação de duplicatas, mantenha redirecionamento Markdown no caminho antigo antes de remover conteúdo, e confirme que nenhuma automação depende dele.
4. Valide links locais, build do site e testes de documentação antes do merge.
5. Mantenha modificações editoriais isoladas de alterações em `game/`, `Data/`, saves e instaladores.

## Guia de descoberta

Use o [índice](INDEX.md), a busca por arquivos Markdown do [GitHub](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/search?q=extension%3Amd&type=code) ou as buscas regionais. Relatórios numerados permanecem na estrutura original até auditoria de dependências.
