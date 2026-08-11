# Pilha de ferramentas

## Desenvolvimento

| Ferramenta | Uso no projeto |
| --- | --- |
| C# e .NET | Implementação do plugin de runtime. |
| [BepInEx](https://github.com/BepInEx/BepInEx) | Carregamento do mod no cliente Unity. |
| [HarmonyX](https://github.com/BepInEx/HarmonyX) | Patches controlados no pipeline de localização. |
| Git e GitHub | Versionamento, histórico e organização de releases. |

## Backend Unity

| Ferramenta | Uso no projeto |
| --- | --- |
| [Cpp2IL](https://github.com/SamboyCoding/Cpp2IL) | Metadata e tipos quando o cliente usar IL2CPP. |
| [Il2CppInterop](https://github.com/BepInEx/Il2CppInterop) | Ponte entre o plugin gerenciado e o runtime IL2CPP. |
| Assemblies gerenciados | Referências diretas quando o cliente usar Mono. |

Cpp2IL e Il2CppInterop são componentes condicionais: só entram se o backend for IL2CPP.

## Conteúdo e localização

| Ferramenta | Uso no projeto |
| --- | --- |
| Unity Addressables | Mapear catálogos, dependências e conteúdo carregado pelo cliente. |
| [AssetRipper](https://github.com/AssetRipper/AssetRipper) | Inspecionar estrutura de assets Unity necessária ao mapeamento. |
| [UABEA](https://github.com/nesrak1/UABEA) | Analisar SerializedFiles e AssetBundles. |
| [UnityPy](https://github.com/K0lb3/UnityPy) | Automatizar inventário de objetos e TextAssets. |
| TextMeshPro | Mapear componentes de texto, fontes, materiais e atlases. |

## Catálogo e automação

| Ferramenta | Uso no projeto |
| --- | --- |
| Python | Construção, consolidação e auditoria do catálogo. |
| PowerShell | Inventário, build, instalação privada e validação do ambiente. |
| JSON/JSONL | Formato principal de catálogos e camadas editoriais. |
| CSV | Intercâmbio editorial e relatórios tabulares quando necessário. |
| Regex | Placeholders, tags, resíduos de idioma e padrões proibidos. |

## Tradução e revisão

| Ferramenta | Uso no projeto |
| --- | --- |
| OpenAI Codex | Ferramenta auxiliar para gerar a base de tradução, apoiar revisão contextual, desenvolver automações e acelerar auditorias. |
| Glossário versionado | Consistência de nomes, facções, armas, sistemas e termos recorrentes. |
| Camadas editoriais | Correções contextuais rastreáveis sem destruir a base anterior. |
| QA in-game | Validação final de contexto, layout e funcionamento no cliente. |

## Validação e empacotamento

- Compilação Release com zero erro e zero aviso do projeto.
- Auditoria de marcadores, Unicode, duplicatas e integridade do catálogo.
- Logs sem exceções do plugin.
- Perfil de desempenho na inicialização e durante o jogo.
- Testes de regressão em narrativa, interface, combate e atualização.
- Pacote mínimo com backup, remoção e hash verificável.
