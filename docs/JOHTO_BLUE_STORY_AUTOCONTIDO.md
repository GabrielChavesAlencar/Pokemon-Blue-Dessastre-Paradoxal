# Johto OFFLINE 12 no Blue-Story.exe — distribuição privada autocontida

## Situação

A Biblioteca do ChatGPT continha o arquivo original do usuário
`Johto_Offline_Fase12_Auditoria_Integracao_Privado(4).zip`, que foi
materializado e validado por checksum:

```
74e727875803f70b3c0598b6b88fe5d79717df849ba1b888fae0583c09202a49
```

O ZIP é uma fonte privada da região (82 mapas `600–681` e os insumos
que o Blue-Story usa para montar a prévia integrada de 100 mapas). Ele NÃO
é um arquivo público hospedado pelo GitHub, e a Biblioteca ChatGPT não
oferece uma URL de download público para executáveis externos.

Para remover a dependência de baixar manualmente dois arquivos, implementamos
um **Blue-Story.exe pessoal autocontido**, enviado diretamente ao usuário.
Ao ser iniciado, o próprio EXE prepara os bytes do ZIP privado original na
pasta gerenciada `.blue-work`, valida SHA-256 e executa o instalador geral.

## Implementação

- `scripts/windows/Bootstrap.cs`: `StageEmbeddedJohto()` reconhece o
  payload privado anexado ao final do PE, verifica seu tamanho e SHA-256,
  cria um arquivo temporário, preserva versão anterior quando necessário,
  e deixa `auto_integrate_johto.py` instalar a região ANTES do Game.exe.
- `scripts/windows/embed_johto_private.py`: empacota uma cópia do EXE Windows
  compilado e o ZIP privado exato, com a estrutura
  `<PE bytes> + <ZIP bytes> + BLUEJH12 + <int64 little-endian ZIP size>`.
  Recusa ZIP sem mapas originais e qualquer SHA diferente do auditado.
- `tests/test_embed_johto_private.py`: verifica empacotamento com dados
  sintéticos, erros de integridade e preservação das origens.
- `.github/workflows/blue-story-windows.yml`: continua compilando e testando
  **somente** o launcher sem o pacote privado. Não injeta mapas no release
  público.

## Gerar um instalador único privado

No Windows, depois de compilar `dist/Blue-Story.exe`, executar:

```powershell
python scripts/windows/embed_johto_private.py `
  --launcher dist/Blue-Story.exe `
  --johto-zip "Johto_Offline_Fase12_Auditoria_Integracao_Privado.zip" `
  --output "dist/Blue-Story-Johto-Privado.exe"
```

Distribuir **somente ao titular dos arquivos** por canal privado, depois de
verificar os termos de distribuição dos recursos. Não fazer commit do ZIP,
não publicar o EXE autocontido em Releases públicas sem direitos de distribuição.

Para uma primeira instalação, o Blue-Story ainda precisa de Internet para
baixar a `main` e as dependências oficiais do projeto. O ZIP privado de
Johto, entretanto, já está dentro do EXE e não precisa de Internet nem de
uma seleção manual de arquivo.

## Aceitação e limitações

CI compilou o Blue-Story e executou o self-test em Windows;
o empacotador Python foi testado com dados sintéticos.
A compatibilidade Windows do **EXE com bytes privados anexados** ainda exige
teste manual no computador do usuário (iniciar, entrar em New Bark,
descer/subir escadas, salvar/recarregar).

O pacote embutido corresponde à Fase OFFLINE 12 original, não substitui
os arquivos externos Akizakura16/DonLawride para deixar os interiores
idênticos aos de HeartGold/SoulSilver.
