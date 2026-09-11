# Ferramentas do projeto

Somente componentes confirmados no fluxo da versão `0.1.0` são listados.

## Dados e qualidade

| Ferramenta | Uso |
| --- | --- |
| Python 3 | Inventário, catálogo, lotes, auditoria, contratos e empacotamento. |
| SQLite | Base privada de unidades, ocorrências, estados e histórico editorial. |
| JSON e JSONL | Relatórios, manifestos e lotes determinísticos. |
| SHA-256 | Identidade de entradas, arquivos, pacotes e evidências. |
| Testes automatizados | Placeholders, transações, recuperação, runtime e distribuição. |

## Runtime

| Componente | Uso |
| --- | --- |
| C nativo | Runtime de consulta e apresentação local da tradução. |
| MinHook 1.3.4 | Interceptação temporária dos dois pontos validados do cliente. |
| Zig 0.16.0 | Toolchain fixada para construção reproduzível do runtime Windows x64. |
| WinHTTP proxy próprio | Encaminhamento para a biblioteca do Windows e carga do plugin fixo. |

O runtime não modifica `GameAssembly.dll` em disco e não implementa contorno de anticheat.

## Instalador

| Componente | Uso |
| --- | --- |
| .NET Framework 4.7.2 / WPF | Interface gráfica Windows x64. |
| Python 3.10 | Núcleo transacional incorporado. |
| PyInstaller 6.22.2 | Congelamento do núcleo em executável local. |
| PowerShell | Orquestração e verificações reproduzíveis da construção. |
| ZIP determinístico | Pacote GameBanana com ordem, timestamps e conteúdo fixos. |

O instalador não baixa componentes nem envia telemetria durante a operação.

## Colaboração e publicação

| Ferramenta | Uso |
| --- | --- |
| OpenAI Codex | Tradução em escala, engenharia, auditoria, testes e documentação sob direção do mantenedor. |
| Git e GitHub | Versionamento, Issues, segurança, manifesto e Releases. |
| GameBanana | Distribuição alternativa e feedback da comunidade. |

## Código público

O repositório público contém a interface WPF do instalador, o núcleo transacional em Python, o empacotador determinístico, testes automatizados e a validação contínua. O catálogo PT-BR, a carga útil compilada, binários e dados obtidos do cliente não são publicados.

Consulte [Compilação e limites do código público](./COMPILACAO.md) para reproduzir a validação disponível sem material privado.
