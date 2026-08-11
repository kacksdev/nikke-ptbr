# Viabilidade e limites

Data do levantamento: **11 de agosto de 2026**.

## Resumo executivo

A localização de NIKKE para português brasileiro no PC parece **tecnicamente investigável**, mas sua implementação não está autorizada por este estudo. A política atual produz um bloqueio anterior ao desafio técnico.

O [contrato em português publicado no site oficial](https://nikke-en.com/termsofservice/children/pt.html) restringe, entre outras condutas, programas de terceiros não autorizados, mods que interajam com o serviço, engenharia reversa, derivação de código, modificação, adaptação, tradução, datamining e contorno de proteção. O texto ressalva situações permitidas pela lei aplicável, mas este projeto não presume que uma exceção exista.

O contrato também informa que o jogo pode empregar software de detecção de fraude ou programas não autorizados e que o acesso pode ser encerrado. Por isso, um protótipo aparentemente funcional ainda poderia representar risco à conta.

Esta análise não é aconselhamento jurídico. A decisão prudente é solicitar autorização escrita antes de qualquer teste invasivo.

## Viabilidade técnica preliminar

### O que foi observado

- Estrutura de dados associada a um cliente Unity.
- Cache de conteúdo em diretório do Unity Addressables.
- Catálogos `.db` acompanhados de arquivos `.nds`.
- Assinatura binária `NKDB`, incompatível com a expectativa de um catálogo JSON ou banco SQLite comum.

### O que ainda não foi comprovado

- Backend Mono ou IL2CPP do executável atual.
- Localização exata das tabelas de texto.
- Uso de TextMeshPro e conjunto de fontes em todas as telas.
- Assinaturas, hashes, CRCs e validações adicionais do conteúdo.
- Possibilidade de integrar PT-BR sem alterar processo, rede ou arquivos protegidos.
- Impacto em atualizações e segurança da conta.

## Viabilidade editorial

Uma tradução completa exigiria, no mínimo:

- inventário de história, eventos, interface, combate, itens, personagens e tutoriais;
- mapeamento de placeholders, tags, variáveis e limites de linha;
- glossário de facções, armas, classes, habilidades e nomes próprios;
- suporte de fonte aos caracteres do português;
- revisão de voz por personagem;
- controle de versões para conteúdo remoto e eventos frequentes;
- testes de cortes, animação, timing e legibilidade.

O volume e a cadência de um jogo de serviço contínuo tornam a manutenção parte central do projeto, não uma etapa posterior.

## Viabilidade contratual e operacional

| Pergunta | Estado |
| --- | --- |
| Há PT-BR listado no site oficial de PC? | Não no levantamento atual. |
| Há autorização pública localizada para mods de tradução? | Não encontrada nas fontes oficiais consultadas. |
| O contrato restringe mods e programas de terceiros? | Sim. |
| O contrato restringe tradução, modificação e datamining? | Sim, com ressalva geral à lei aplicável. |
| Um protótipo pode ser testado com segurança de conta? | Não demonstrado. |
| O desenvolvimento deve começar agora? | Não; requer esclarecimento ou permissão escrita. |

## Próxima ação recomendada

Enviar ao suporte oficial uma descrição curta, não técnica e transparente:

1. projeto comunitário, gratuito e sem monetização;
2. foco exclusivo em localização PT-BR para PC;
3. nenhum interesse em automação, vantagem competitiva ou contorno de proteção;
4. pedido de autorização para investigar arquivos locais ou usar uma integração aprovada;
5. compromisso de não redistribuir recursos proprietários;
6. solicitação de canal oficial ou diretrizes de modding/localização.

Contato indicado no contrato: **help@nikke-en.com**.

Até resposta suficiente, este repositório permanece em pesquisa documental.
