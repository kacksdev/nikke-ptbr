# Instalação do NIKKE PT-BR

## Método recomendado

1. Abra a seção **Releases** do repositório.
2. Baixe `NIKKEPTBRv0.1.0.exe` e, opcionalmente, o arquivo `.sha256`.
3. Atualize o NIKKE pelo launcher oficial.
4. Feche completamente o jogo e o launcher.
5. Abra o instalador.
6. Confirme a pasta detectada ou selecione **ESCOLHER PASTA**.
7. Selecione **INSTALAR TRADUÇÃO**.
8. Aguarde a confirmação e abra o jogo pelo launcher oficial.

Também existe um ZIP na página do GameBanana. Extraia-o antes de executar o instalador.

## Pasta correta

A pasta escolhida precisa conter:

```text
nikke.exe
nikke_Data\
UnityPlayer.dll
GameAssembly.dll
```

Selecione a pasta `game` que contém esses arquivos, não a raiz do launcher e não a pasta `nikke_Data`.

## Ações disponíveis

- **Instalar tradução**: valida o cliente e adiciona os três componentes do projeto.
- **Verificar**: compara os arquivos instalados com o manifesto interno.
- **Reparar tradução**: repõe somente um componente conhecido ausente ou alterado, preservando o estado anterior em quarentena.
- **Remover tradução**: remove somente arquivos reconhecidos como pertencentes ao pacote.
- **Abrir pasta do jogo** e **abrir log**: ajudam na conferência e no suporte.

Jogo e launcher devem permanecer fechados durante instalação, reparo e remoção.

## Segurança da operação

Antes de gravar, o instalador confere:

- `nikke.exe`, `UnityPlayer.dll` e `GameAssembly.dll`;
- dois fingerprints independentes necessários ao runtime;
- SHA-256 de todo o conteúdo incorporado;
- ausência de colisão com arquivos desconhecidos;
- inexistência de uma transação incompatível.

O journal e o estado da instalação ficam sob:

```text
%LOCALAPPDATA%\Kacksdev\NIKKEPTBR\state
```

O conteúdo incorporado é materializado em cache verificado sob:

```text
%LOCALAPPDATA%\Kacksdev\NIKKEPTBR\cache
```

Se uma operação falhar ou for interrompida, a próxima abertura recupera o journal antes de aceitar outra ação. Uma mensagem de sucesso só aparece depois da verificação final.

## Como confirmar o carregamento

Depois de abrir o jogo uma vez, o runtime pode criar:

```text
NIKKEPTBR-Runtime\runtime.log
```

Uma execução correta registra o carregamento do índice, a validação do cliente e as primeiras substituições. Não publique o log inteiro sem conferir se ele contém caminhos locais; para suporte, envie apenas o trecho necessário.

## Atualizar o jogo

1. Feche jogo e launcher.
2. Use **Remover tradução** no instalador do mod.
3. Atualize o cliente pelo launcher oficial.
4. Consulte [Compatibilidade](./COMPATIBILIDADE.md).
5. Reinstale apenas quando a nova versão estiver listada como compatível.

O pacote `0.1.0` foi validado somente no cliente `NIKKE.PC_Official_GL_151.8.5`. Um cliente desconhecido é recusado sem alteração.

## Remoção

Feche jogo e launcher, abra o mesmo executável e selecione **REMOVER TRADUÇÃO**.

A remoção apaga somente os três componentes com identidade reconhecida pelo estado da instalação. Arquivos desconhecidos não são removidos. O log pode ser preservado como evidência no diretório de recibos.

## Segurança e origem

A versão `0.1.0` não possui certificado comercial de assinatura de código. O Windows pode mostrar **Fornecedor desconhecido** ou uma tela do SmartScreen.

Use somente estas origens:

- Release oficial em `github.com/kacksdev/nikke-ptbr`;
- página oficial em `gamebanana.com/mods/715729`.

SHA-256 aprovado de `NIKKEPTBRv0.1.0.exe`:

```text
F1EB0CEB91A88F6EC23CC6B48A0376FA04B8BCC42FB8F9A0BD2962FCD7EEB444
```

O instalador não envia telemetria e não baixa componentes durante a operação.

## Problemas comuns

### O jogo não foi encontrado

Escolha manualmente a pasta que contém `nikke.exe`. Se a estrutura ou os hashes não coincidirem, a seleção será recusada sem alteração.

### A versão é incompatível

Não force a instalação. Remova qualquer versão anterior, atualize pelo launcher e aguarde uma confirmação de compatibilidade.

### A operação foi interrompida

Abra o instalador novamente. A recuperação da transação pendente ocorre antes de qualquer nova ação.

### O jogo continua em inglês

Use **Verificar**. Se a instalação estiver íntegra, abra o log e informe a versão do mod, a versão exibida pelo launcher, a tela afetada e o texto observado em uma Issue.
