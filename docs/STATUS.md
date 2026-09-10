# Status técnico

Atualizado em 10 de setembro de 2026.

## Versão preparada

| Item | Estado |
| --- | --- |
| Mod | `0.1.0 beta` |
| Cliente validado | `NIKKE.PC_Official_GL_151.8.5` |
| Plataforma | Windows x64 |
| Catálogo conhecido | 429.498 unidades únicas |
| Ocorrências | 536.489 |
| Tabelas | 34 |
| Modelos formatados | 2.743 |
| Bloqueios estruturais | 0 |
| Apontamentos editoriais | 1.689 |
| Revisão editorial integral | Não concluída |

Cobertura técnica não significa revisão manual integral. A base está pronta para a primeira versão funcional, mas ainda pode receber refinamentos de tom, contexto, gênero e terminologia em versões futuras.

## Integração

O runtime apresenta as traduções depois do carregamento dos dados pelo cliente. Ele reconhece correspondências por tabela, chave e texto original, com uma rota adicional para superfícies legadas e textos formatados.

A distribuição adiciona somente:

- `winhttp.dll`;
- `NIKKEPTBR-Runtime.dll`;
- `NIKKEPTBR-Runtime.idx`.

Nenhum arquivo oficial é substituído. O runtime valida o cliente e falha de forma segura quando a identidade esperada não coincide.

## Validação confirmada

| Prova | Resultado |
| --- | --- |
| Pacote transacional | 18/18 |
| Executável final em réplica | 11/11 |
| Suíte atual | 116/116 |
| Construções finais consecutivas | Idênticas byte a byte |
| Instalação real | Aprovada |
| Inicialização pelo launcher | Aprovada |
| Catálogo PT-BR carregado | Aprovado |
| Chave, texto exato e formato | Observados |
| Reparação e repetição idempotente | Aprovadas |
| Remoção e rollback | Aprovados |
| Arquivos oficiais modificados | 0 |
| Resíduo depois da remoção | 0 |

A carga útil exata da versão final foi aceita no cliente real. Depois dessa prova, o invólucro foi recompilado para tornar a construção determinística e completar os avisos de terceiros. Pacote, bootstrap e núcleo do instalador permaneceram idênticos; o executável final passou novamente pela matriz isolada de 11 verificações.

## Limites conhecidos

- a versão `1.0.0` permanece reservada para maturidade editorial superior;
- 1.689 apontamentos editoriais não bloqueantes estão preservados;
- 8.588 unidades traduzíveis possuem resultado idêntico ao texto-fonte por identidade, nome protegido, homógrafo ou decisão do pipeline;
- textos incorporados em imagens não são alterados;
- conteúdo introduzido por atualização pode aparecer em inglês;
- não existe promessa de compatibilidade com clientes futuros desconhecidos;
- o executável não possui certificado comercial de assinatura de código.

## Publicação

Os artefatos preparados para a versão incluem instalador, SHA-256, manifesto e documentação. A página pública deve sempre indicar o cliente validado e separar cobertura técnica de revisão editorial.
