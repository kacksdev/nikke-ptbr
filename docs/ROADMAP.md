# Roadmap do NIKKE PT-BR

O roadmap separa cobertura textual, revisão manual e validação técnica. Uma
etapa concluída não antecipa automaticamente a próxima.

## Fase 0: Mapeamento do cliente

**Estado: concluída**

- versão, Unity, backend e anticheat identificados;
- 75 contêineres e 724.181 linhas lógicas inventariados;
- formatos `.lsc`, `.lss`, `.cat`, `NKDB` e SQLite classificados.

## Fase 1: Ferramentas e catálogo

**Estado: concluída**

- decodificador e remontador independentes;
- igualdade binária comprovada em remontagem sem alteração;
- catálogo privado com deduplicação e contexto;
- lotes editoriais determinísticos e importação transacional;
- construtor isolado e testes automatizados.

## Fase 2: Tradução e integridade lateral

**Estado: atual**

- traduzir os domínios do catálogo em lotes privados;
- preservar nomes próprios, títulos musicais e marcadores funcionais;
- registrar separadamente tradução, revisão e aprovação;
- determinar o papel dos sidecars `.nds` e hashes dos catálogos;
- manter toda construção fora do cliente instalado.

## Fase 3: Instalação reversível

**Estado: pendente**

- construir um executável gráfico único para Windows;
- localizar o cliente automaticamente e permitir seleção manual;
- reconhecer versão, estrutura e hashes antes de escrever;
- validar o conteúdo incorporado e preparar mudanças fora do cliente ativo;
- produzir backup com manifesto, aplicação transacional e rollback automático;
- reunir instalação, atualização, reparo, verificação e remoção na mesma
  interface;
- recusar versões desconhecidas sem afetar o jogo;
- preservar arquivos alheios e impedir resíduos após atualização ou remoção;
- aprovar matriz automatizada e ciclo do arquivo final em cliente limpo.

## Fase 4: QA privado

**Estado: pendente**

- validar carregamento e restauração no cliente;
- medir inicialização, memória, travamentos e fluidez;
- testar interface, narrativa, combate, eventos e resoluções;
- registrar limites, textos pendentes e compatibilidade exata.

## Fase 5: Primeira versão pública

**Estado: pendente**

- publicar arquivo somente em Releases;
- fornecer SHA-256 e manifesto;
- distribuir o instalador gráfico único já validado;
- documentar instalação, atualização, reparo, verificação, remoção e rollback;
- manter a numeração pré-1.0 enquanto houver revisão integral pendente.

## Fase 6: Versão 1.0.0

**Estado: sem prazo**

A versão 1.0.0 exige cobertura total, revisão manual integral, terminologia
uniforme, contexto aprovado, layout verificado e ausência de falhas técnicas
conhecidas nos critérios definidos pelo projeto. Traduzir todas as entradas,
sozinho, não satisfaz esse marco.
