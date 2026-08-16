# Status técnico

Atualizado em 16 de agosto de 2026.

## Métricas confirmadas

| Métrica | Valor |
| --- | ---: |
| Contêineres inventariados | 75 |
| Linhas lógicas | 724.181 |
| Entradas catalogadas | 564.723 |
| Unidades textuais únicas | 427.944 |
| Unidades traduzíveis únicas | 427.345 |
| Unidades traduzidas | 941 |
| Lotes privados importados | 11 |
| Títulos musicais protegidos | 178 |
| Testes automatizados | 10 aprovados / 0 falha |

## Cobertura por domínio

| Domínio | Traduzido | Estado |
| --- | ---: | --- |
| Pré-instalação e erros de protocolo | 641/641 unidades | **100%** |
| Interface de sistema | 300 unidades | Em andamento |
| Catálogo integral | 941/427.345 unidades | **0,22%** |

As unidades traduzidas ainda não equivalem a revisão manual completa. A base
passa pelas auditorias estruturais no momento da importação; revisão contextual
e testes dentro do jogo são fases separadas.

## Engenharia

Concluído:

- inventário do cliente;
- decodificação independente do `NKDB`;
- remontagem sem alteração byte a byte;
- catálogo privado e deduplicação;
- exportação e importação de lotes;
- histórico editorial transacional;
- construção isolada com hashes e integridade SQLite;
- proteção contra escrita acidental dentro do cliente.

Em andamento:

- tradução da interface;
- investigação dos sidecars `.nds` e hashes de catálogo;
- definição do pacote reversível e do comportamento após atualizações.

Pendente:

- instalação controlada;
- validação no cliente;
- medições de desempenho;
- pacote público, instruções e release.

## Disponibilidade

Não há build pública. Nenhum arquivo exibido neste repositório instala ou
altera o jogo.
