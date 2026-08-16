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

- reconhecer versão e hashes antes de escrever;
- produzir backup verificável e restauração automática;
- recusar versões desconhecidas sem afetar o jogo;
- definir atualização e substituição de pacote sem resíduos.

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
- documentar instalação, atualização e remoção;
- manter a numeração pré-1.0 enquanto houver revisão integral pendente.

## Fase 6: Versão 1.0.0

**Estado: sem prazo**

A versão 1.0.0 exige cobertura total, revisão manual integral, terminologia
uniforme, contexto aprovado, layout verificado e ausência de falhas técnicas
conhecidas nos critérios definidos pelo projeto. Traduzir todas as entradas,
sozinho, não satisfaz esse marco.
