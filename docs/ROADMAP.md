# Roadmap do NIKKE PT-BR

O roadmap separa cobertura técnica, revisão editorial, integração, instalação e publicação. Concluir uma área não transforma automaticamente as demais em revisão integral.

## Fase 0: mapeamento do cliente

**Estado: concluída**

- formatos e bancos relevantes identificados;
- inventário do cliente e hashes reproduzíveis;
- limites de segurança definidos.

## Fase 1: ferramentas e catálogo

**Estado: concluída**

- decodificação e remontagem independentes;
- catálogo privado deduplicado;
- lotes determinísticos e importação transacional;
- auditorias de placeholders, tags, Unicode e termos protegidos.

## Fase 2: cobertura da tradução

**Estado: concluída para a primeira versão funcional**

- 429.498 unidades conhecidas com base PT-BR;
- 536.489 ocorrências em 34 tabelas;
- zero bloqueio estrutural pendente;
- apontamentos editoriais mantidos separadamente.

## Fase 3: integração reversível

**Estado: concluída no cliente 151.8.5**

- runtime próprio depois do NKDB;
- correspondência por chave, texto exato e formato;
- rota legada da interface;
- validação de identidade e comportamento fail-open;
- cliente restaurado sem arquivo oficial modificado.

## Fase 4: instalador e QA privado

**Estado: concluída**

- instalador gráfico único para Windows x64;
- detecção automática e escolha manual;
- instalar, verificar, reparar e remover;
- journal, recuperação, quarentena e rollback;
- 18/18 provas do pacote;
- 11/11 provas do executável final;
- 116/116 testes do workspace;
- duas construções finais idênticas.

## Fase 5: primeira publicação

**Estado: concluída em 11 de setembro de 2026**

- documentação pública revisada;
- Release `v0.1.0` publicada no GitHub com instalador, manifesto e checksum;
- distribuição alternativa publicada no GameBanana;
- hashes dos downloads públicos conferidos contra os artefatos aprovados;
- código autoral do instalador e do núcleo transacional disponibilizado para auditoria.

## Fase 6: manutenção e maturidade editorial

**Estado: contínuo, sem prazo**

- adaptar o mod a versões futuras do cliente;
- importar textos adicionados por atualizações;
- corrigir relatos reproduzíveis;
- revisar contexto, tom, gênero e terminologia quando priorizado;
- ampliar evidência visual e testes de uso prolongado.

A versão `1.0.0` exige maturidade editorial superior, consistência contextual e validação suficiente no jogo. A cobertura técnica da beta `0.1.0`, por si só, não satisfaz esse marco.
