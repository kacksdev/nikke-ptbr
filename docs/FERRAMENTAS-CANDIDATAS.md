# Ferramentas candidatas

> Inventário de pesquisa. Inclusão nesta página não significa que a ferramenta foi executada contra o cliente ou que seu uso foi autorizado.

## Inventário e diagnóstico

| Ferramenta | Papel possível | Limite |
| --- | --- | --- |
| PowerShell | Inventário de arquivos, hashes e automação reproduzível. | Somente dados locais necessários; nunca credenciais ou dados de conta. |
| [Process Monitor](https://learn.microsoft.com/sysinternals/downloads/procmon) | Observar quais arquivos um processo acessa. | Usar apenas com permissão e filtros estritos. |
| Git e GitHub | Versionar scripts próprios, decisões e documentação. | Não versionar recursos proprietários. |

## Unity e conteúdo

| Ferramenta | Papel possível | Limite |
| --- | --- | --- |
| [AssetRipper](https://github.com/AssetRipper/AssetRipper) | Analisar arquivos serializados e bundles Unity. | O próprio projeto alerta para direitos sobre saídas extraídas. |
| [UABEA](https://github.com/nesrak1/UABEA) | Ler e escrever SerializedFiles e AssetBundles. | Edição de Addressables pode envolver CRC e catálogo; risco alto de quebra. |
| [UnityPy](https://github.com/K0lb3/UnityPy) | Automatizar inspeção de assets e TextAssets em Python. | Formatos próprios como `NKDB` podem exigir análise não autorizada. |
| [Unity Addressables](https://docs.unity3d.com/Packages/com.unity.addressables@1.21/manual/build-content-catalogs.html) | Referência oficial para catálogos, localizadores e bundles. | Documentação explica o sistema genérico, não o contêiner específico do jogo. |

## Backend e runtime

| Ferramenta | Papel possível | Limite |
| --- | --- | --- |
| [Cpp2IL](https://github.com/SamboyCoding/Cpp2IL) | Análise de metadata de builds Unity IL2CPP. | Só seria relevante depois de confirmar backend e autorização. |
| [Il2CppInterop](https://github.com/BepInEx/Il2CppInterop) | Ponte gerenciada para tipos IL2CPP. | Interage com runtime; risco contratual e de conta. |
| [BepInEx](https://github.com/BepInEx/BepInEx) | Framework de plugins para Unity Mono/IL2CPP. | Suporte IL2CPP pode usar versões preliminares; não testar agora. |
| [HarmonyX](https://github.com/BepInEx/HarmonyX) | Patches controlados de métodos .NET/Unity. | Não aplicável sem ponto autorizado e backend compatível. |

## Texto, tradução e qualidade

| Ferramenta | Papel possível | Limite |
| --- | --- | --- |
| Python, JSON/CSV e regex | Pipeline de tabelas, normalização, placeholders e auditoria. | O formato real ainda não foi identificado. |
| [OpenAI Codex](https://developers.openai.com/codex/) | Tradução assistida, análise contextual, código e validação. | IA não substitui revisão contextual e testes humanos. |
| [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) | Avaliar legibilidade ou uma sobreposição externa autorizada. | OCR de UI animada pode errar e ainda envolver captura de conteúdo. |
| Capturas comparativas | Detectar corte, fonte, timing e regressão. | Remover identificadores e dados pessoais antes de registrar evidência. |

## Critérios para aprovar uma ferramenta

1. Permissão compatível com o contrato e a resposta oficial.
2. Nenhuma necessidade de contornar autenticação, anti-cheat ou integridade.
3. Nenhuma coleta de credenciais, tokens, IDs pessoais ou conversas.
4. Saída reproduzível e removível.
5. Licença da ferramenta compatível com o projeto.
6. Ausência de recursos proprietários no pacote final.
7. Impacto de desempenho e estabilidade medido no cliente autorizado.
