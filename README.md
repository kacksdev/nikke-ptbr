<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/workbench-dark.png" />
  <source media="(prefers-color-scheme: light)" srcset="./assets/workbench-light.png" />
  <img src="./assets/workbench-light.png" alt="Mesa de pesquisa em desenho monocromático, com interfaces, código e anotações técnicas" width="100%" />
</picture>

<h1 align="center">GODDESS OF VICTORY: NIKKE PT-BR / PC</h1>

<p align="center">
  <strong>PESQUISA TÉCNICA PÚBLICA / MOD NÃO INICIADO / SEM DOWNLOAD</strong>
</p>

<p align="center">
  <code>FASE 0</code>&nbsp;&nbsp;
  <code>VIABILIDADE CONDICIONAL</code>&nbsp;&nbsp;
  <code>RISCO CONTRATUAL ALTO</code>&nbsp;&nbsp;
  <code>PC</code>
</p>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/ink-rule-dark.svg" />
  <source media="(prefers-color-scheme: light)" srcset="./assets/ink-rule-light.svg" />
  <img src="./assets/ink-rule-light.svg" alt="" width="100%" />
</picture>

## 01 / ESTADO REAL DO PROJETO

<table>
  <tr>
    <td width="220" align="center">
      <picture>
        <source media="(prefers-color-scheme: dark)" srcset="./assets/nikke-icon-dark.jpg" />
        <source media="(prefers-color-scheme: light)" srcset="./assets/nikke-icon-light.jpg" />
        <img src="./assets/nikke-icon-light.jpg" alt="Ícone de NIKKE reinterpretado em desenho monocromático" width="185" />
      </picture>
    </td>
    <td>
      <strong>AINDA NÃO EXISTE UM MOD DE TRADUÇÃO</strong><br /><br />
      O trabalho atual é somente pesquisa de viabilidade para uma possível localização comunitária em português brasileiro no cliente de PC.<br /><br />
      Este repositório não contém textos extraídos, tradução do jogo, código de injeção, DLLs, ferramentas de contorno, instaladores ou releases.
    </td>
  </tr>
</table>

O botão **Code → Download ZIP** baixa apenas documentação e imagens deste estudo. Nenhuma versão jogável está escondida no repositório.

## 02 / CONCLUSÃO DE VIABILIDADE

| Dimensão | Conclusão atual |
| --- | --- |
| **Técnica** | **Condicional e não comprovada.** O cliente usa Unity e há evidência local de Addressables e catálogos com contêiner próprio `NKDB`; ainda não foi determinado onde todos os textos vivem nem qual integração seria segura. |
| **Política e conta** | **Bloqueada para desenvolvimento prático.** O contrato atual proíbe programas de terceiros não autorizados, mods que interajam com o serviço, engenharia reversa, modificação, tradução e datamining, salvo exceções legais aplicáveis. |
| **Distribuição** | **Não autorizada.** Nenhum mod, extração ou pacote será criado/publicado enquanto não houver permissão escrita ou esclarecimento oficial suficiente. |

A rota recomendada é pedir autorização por escrito ao suporte indicado no contrato, **help@nikke-en.com**, antes de modificar o cliente, analisar recursos protegidos ou testar hooks em runtime.

Leia a análise completa em [Viabilidade e limites](./docs/VIABILIDADE.md).

## 03 / EVIDÊNCIAS PRELIMINARES

Levantamento local de 11 de agosto de 2026, sem descriptografar, alterar ou distribuir conteúdo:

- cliente baseado em **Unity**;
- estrutura de cache do **Unity Addressables**;
- catálogos com arquivos `.db` e acompanhantes `.nds`;
- cabeçalho `NKDB`, indicando contêiner próprio em vez de JSON ou SQLite comuns;
- idiomas oficiais exibidos na página de PC sem português brasileiro.

Esses sinais ajudam a mapear perguntas técnicas, mas não autorizam engenharia reversa e não provam que uma estratégia de mod funcionará.

Fontes primárias: [cliente oficial de PC](https://nikke-en.com/download.html), [contrato atual em português](https://nikke-en.com/termsofservice/children/pt.html) e [documentação do Unity Addressables](https://docs.unity3d.com/Packages/com.unity.addressables@1.21/manual/build-content-catalogs.html).

## 04 / ROTAS ANALISADAS

| Rota | Potencial | Risco atual | Decisão |
| --- | --- | --- | --- |
| Suporte oficial, autorização ou localização nativa | Melhor qualidade e menor risco | Depende da empresa | **Prioridade** |
| Sobreposição externa com captura/OCR | Não altera bundles diretamente | Ainda é programa de terceiro e pode coletar informações da tela | **Não testar sem autorização** |
| Leitura de catálogos e recursos Unity | Pode localizar tabelas e fontes | Contrato cita datamining e engenharia reversa | **Bloqueada** |
| Substituição/reempacotamento de AssetBundles | Integração visual mais natural | Quebra por atualização, hash/CRC e política | **Bloqueada** |
| Hook de runtime em Mono/IL2CPP | Tradução antes da renderização | Interage com processo e detecção de programas | **Bloqueada** |
| Proxy ou interceptação de rede | Poderia observar conteúdo remoto | Interceptação e serviço são áreas expressamente sensíveis | **Rejeitada** |
| Injeção em memória ou contorno de anti-cheat | Nenhuma necessidade legítima para este projeto | Segurança de conta e serviço | **Rejeitada** |

Mais detalhes em [Rotas técnicas](./docs/ROTAS-TECNICAS.md).

## 05 / FERRAMENTAS CANDIDATAS

Nenhuma ferramenta abaixo foi aplicada ao cliente. Esta é uma lista de avaliação para uso **somente se houver autorização**.

| Área | Candidatos | Finalidade possível |
| --- | --- | --- |
| Inventário | PowerShell, hashes, Process Monitor | Mapear arquivos e mudanças sem modificar o cliente. |
| Unity e assets | AssetRipper, UABEA, UnityPy | Identificar bundles, TextAssets, fontes e tabelas. |
| Backend | Cpp2IL, Il2CppInterop | Confirmar e compreender uma eventual build IL2CPP. |
| Runtime | BepInEx, HarmonyX | Prototipar integração controlada caso seja permitida. |
| Texto | Python, JSON/CSV, regex, glossário | Normalização, placeholders, terminologia e auditoria. |
| Tradução | OpenAI Codex + revisão e QA | Rascunho assistido, análise contextual e automação. |
| Validação | OCR, capturas, testes de layout e regressão | Conferir fontes, cortes, timing e consistência visual. |

O inventário completo, com links oficiais e limitações, está em [Ferramentas candidatas](./docs/FERRAMENTAS-CANDIDATAS.md).

## 06 / TRANSPARÊNCIA

- Projeto para **PC**, comunitário, gratuito e sem monetização.
- Nenhuma promessa de versão foi feita e não existe previsão de lançamento.
- O uso futuro de IA será declarado: a ferramenta planejada é o [OpenAI Codex](https://developers.openai.com/codex/).
- Não haverá publicação de arquivos proprietários, textos integrais do jogo, credenciais ou técnicas de contorno.
- NIKKE, personagens, marcas e conteúdos pertencem aos respectivos titulares.
- Este estudo não é afiliado, patrocinado ou endossado pela SHIFT UP ou pelas demais empresas responsáveis.

Consulte também o [Roadmap condicionado](./docs/ROADMAP.md) e a [Transparência sobre IA](./docs/TRANSPARENCIA-IA.md).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/ink-rule-dark.svg" />
  <source media="(prefers-color-scheme: light)" srcset="./assets/ink-rule-light.svg" />
  <img src="./assets/ink-rule-light.svg" alt="" width="100%" />
</picture>

<p align="center"><code>KACKS / TECHNICAL RESEARCH / BRASIL</code></p>
