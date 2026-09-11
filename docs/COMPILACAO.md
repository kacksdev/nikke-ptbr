# Compilação e limites do código público

O repositório disponibiliza o código autoral da interface WPF, do núcleo transacional e das ferramentas que validam o pacote do NIKKE PT-BR. Esse material permite auditar as regras de instalação, verificação, reparo, remoção, recuperação e integridade.

## Conteúdo intencionalmente ausente

O catálogo de tradução, o índice compilado, os binários do runtime, o bootstrap incorporado e qualquer dado obtido do cliente não fazem parte do repositório. Por esse motivo, compilar apenas o código público produz a interface verificável do instalador, mas não uma distribuição funcional do mod.

O instalador pronto e aprovado deve ser obtido exclusivamente na [Release oficial](https://github.com/kacksdev/nikke-ptbr/releases/latest). Não aceite compilações de terceiros como equivalentes à versão publicada.

## Requisitos para validação

- Windows x64;
- Python 3.10 ou posterior;
- .NET SDK 8 ou posterior;
- acesso à internet apenas para restaurar o pacote de referências do .NET na primeira compilação.

## Validação local

Na raiz do repositório, execute:

```powershell
.\tools\Test-PublicSource.ps1
```

O script executa a auditoria do conteúdo público, os testes do núcleo transacional e a compilação determinística da interface WPF sem carga útil. A mesma sequência é executada pelo GitHub Actions.

## Construção oficial

A construção de uma distribuição funcional exige uma carga útil privada previamente aprovada, composta somente pelos três componentes pertencentes ao projeto. O bootstrap é criado com ordem e timestamps fixos, tem cada arquivo registrado por SHA-256 e é incorporado ao instalador somente depois da verificação do contrato.

Esse processo deliberadamente não é transformado em um download alternativo pelo repositório. A separação protege os direitos dos titulares, impede a publicação acidental de dados do jogo e mantém uma única origem oficial para o binário testado.
