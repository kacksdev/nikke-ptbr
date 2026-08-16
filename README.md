<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/nikke-hero-dark.png" />
  <source media="(prefers-color-scheme: light)" srcset="./assets/nikke-hero-light.png" />
  <img src="./assets/nikke-hero-light.png" alt="NIKKE em composição monocromática desenhada para a identidade visual do projeto" width="100%" />
</picture>

<h1 align="center">GODDESS OF VICTORY: NIKKE PT-BR / PC</h1>

<p align="center">
  <strong>TRADUÇÃO COMUNITÁRIA / DESENVOLVIMENTO ATIVO / SEM BUILD PÚBLICA</strong>
</p>

<p align="center">
  <code>v0.1.0-dev</code>&nbsp;&nbsp;
  <code>FASE 2/6</code>&nbsp;&nbsp;
  <code>CLIENTE 150.6.9</code>&nbsp;&nbsp;
  <code>PC / WINDOWS</code>
</p>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/ink-rule-dark.svg" />
  <source media="(prefers-color-scheme: light)" srcset="./assets/ink-rule-light.svg" />
  <img src="./assets/ink-rule-light.svg" alt="" width="100%" />
</picture>

## 01 / O PROJETO

Este é o painel público de desenvolvimento do **NIKKE PT-BR para PC**, uma
tradução comunitária, gratuita e sem monetização. O objetivo é cobrir os textos
do jogo por modding interno dos próprios pacotes de idioma, preservando
marcadores, nomes próprios, títulos musicais e funcionamento do cliente.

O projeto já saiu da fase de planejamento: o cliente foi mapeado, o formato de
dados foi reconstruído, o catálogo privado foi criado e a tradução começou.
Ainda **não existe pacote seguro para instalar**. O botão **Code → Download
ZIP** baixa somente esta documentação e os recursos visuais do repositório.

> **Tradução, não localização profissional.** A meta imediata é traduzir 100%
> do conteúdo textual e realizar verificações técnicas e editoriais seletivas.
> Partes da base podem permanecer literais ou exigir correção contextual até
> receberem revisão manual. A versão 1.0.0 fica reservada para um estado
> integralmente revisado e validado, sem prazo prometido.

## 02 / ESTADO ATUAL

| Área | Estado verificável |
| --- | --- |
| Cliente analisado | **150.6.9**, Unity **2021.3.56f2**, IL2CPP, Windows |
| Inventário | **75 contêineres**, **724.181** linhas lógicas, zero estrutura desconhecida |
| Catálogo privado | **564.723** entradas e **427.345** unidades traduzíveis únicas |
| Tradução importada | **1.141** unidades únicas em **13 lotes** privados |
| Primeiro domínio | Pré-instalação e protocolo: **641/641 unidades (100%)** |
| Interface de sistema | **500** unidades importadas; domínio ainda em andamento |
| Ocorrências cobertas | **3.751** no catálogo; **3.730** substituições na cópia isolada |
| Construção isolada | **28** contêineres reabertos e validados; cliente intocado |
| Cobertura integral | **0,27%** das unidades únicas traduzíveis |
| Validação automática | **10 testes aprovados**, zero falha |
| Build pública | **Não disponível** |

Os arquivos traduzidos são reconstruídos e auditados apenas em cópias
isoladas. Nenhum deles foi aplicado ao cliente instalado. As 21 ocorrências de
diferença entre catálogo e construção pertencem a entradas deliberadamente
preservadas, principalmente títulos musicais, e não são substituídas. A
barreira atual é comprovar o papel dos sidecars de integridade e produzir
instalação, atualização e restauração realmente reversíveis. Consulte o
[status técnico](./docs/STATUS.md).

## 03 / COMO O MOD ESTÁ SENDO CONSTRUÍDO

<p align="center">
  <code>INVENTARIAR</code> →
  <code>DECODIFICAR</code> →
  <code>CATALOGAR</code> →
  <code>TRADUZIR</code> →
  <code>AUDITAR</code> →
  <code>REMONTAR</code> →
  <code>VALIDAR</code> →
  <code>EMPACOTAR</code>
</p>

A arquitetura confirmada não usa OCR, sobreposição de tela nem injeção em
runtime. O fluxo trabalha diretamente com os bancos de idioma do cliente:

1. reconhece versão e hashes antes de qualquer operação;
2. extrai os contêineres `NKDB` para bancos SQLite em área privada;
3. organiza textos repetidos em unidades únicas com contexto e estado editorial;
4. importa lotes PT-BR de forma transacional;
5. bloqueia regressões em placeholders, marcações e quebras de linha;
6. remonta os arquivos em diretório isolado e verifica o round-trip;
7. somente permitirá instalação quando backup, integridade lateral e rollback
   estiverem comprovados.

Uma atualização desconhecida do jogo deverá fazer o instalador **falhar de
forma segura**, mantendo o cliente original intacto, em vez de aplicar arquivos
incompatíveis. Veja a [arquitetura técnica](./docs/ARQUITETURA.md).

## 04 / ESCOPO DA TRADUÇÃO

| Conteúdo | Tratamento previsto |
| --- | --- |
| História e eventos | Texto integral em PT-BR; contexto refinado gradualmente por revisão manual. |
| Interface e sistemas | Menus, avisos, recompensas, loja, configurações e fluxos de conta. |
| Personagens | Episódios, aconselhamento, perfis, mensagens e terminologia recorrente. |
| Combate | Habilidades, efeitos, equipamentos, atributos, buffs, debuffs e tutoriais. |
| Itens e coleções | Nomes, descrições, categorias, missões e progressão. |
| Identidade da obra | Nomes próprios, marcas e títulos musicais preservados quando a tradução prejudicar a identificação. |
| Integridade | IDs, tags, variáveis, Unicode, layout e atualizações não podem ser quebrados pela tradução. |

## 05 / AUTORIA E TRANSPARÊNCIA

**NIKKE PT-BR é um projeto criado, dirigido, mantido e validado por mim.** A
definição do escopo, o padrão de qualidade, as decisões editoriais, os testes no
cliente, a compatibilidade e a publicação permanecem sob minha responsabilidade.

O **OpenAI Codex** integra o fluxo como ferramenta auxiliar. Ele foi utilizado
para mapear os dados do cliente, desenvolver as automações, produzir as
traduções PT-BR dos lotes do catálogo, aplicar correções orientadas pelo projeto,
automatizar auditorias e acelerar a documentação. Eu defino os requisitos,
identifico problemas durante o uso real, conduzo os testes, aprovo os resultados
e participo da execução técnica; o Codex amplia a capacidade de trabalho em
grande escala.

As métricas diferenciam tradução produzida, revisão manual e validação no jogo.
Nenhum número publicado implica que todas as frases já foram revisadas por uma
pessoa. Consulte [Autoria e processo](./docs/AUTORIA-E-PROCESSO.md).

## 06 / PUBLICAÇÃO

- Projeto comunitário para **PC / Windows**, gratuito e sem paywall.
- O repositório público contém progresso e documentação; não contém textos
  extraídos, bancos proprietários nem uma build disfarçada.
- Quando existir uma versão segura, o download ficará em **Releases**, com
  arquivo, hash, compatibilidade, instalação, atualização e remoção documentados.
- O botão **Code → Download ZIP** não é o download do mod.
- GODDESS OF VICTORY: NIKKE e seus elementos pertencem aos respectivos titulares.
- O projeto é independente e não possui afiliação ou endosso oficial.

O avanço pode ser acompanhado no [Roadmap](./docs/ROADMAP.md).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/ink-rule-dark.svg" />
  <source media="(prefers-color-scheme: light)" srcset="./assets/ink-rule-light.svg" />
  <img src="./assets/ink-rule-light.svg" alt="" width="100%" />
</picture>

<p align="center"><code>KACKS / TRADUÇÃO COMUNITÁRIA / BRASIL</code></p>
