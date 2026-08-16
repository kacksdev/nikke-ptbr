# Arquitetura técnica

## Objetivo

Entregar português brasileiro pelo sistema de dados do próprio cliente, sem
OCR, sobreposição visual ou hooks de runtime. A prioridade é que uma versão
desconhecida do jogo permaneça intacta e inicializável.

## Cliente confirmado

| Item | Valor |
| --- | --- |
| Plataforma | Windows / PC |
| Versão analisada | `150.6.9` |
| Unity | `2021.3.56f2` |
| Backend | IL2CPP |
| Anticheat | AntiCheat Expert |
| Pacotes de texto | 49 `.lsc` e 24 `.lss` |
| Catálogos | 2 `.cat` |

## Contêiner e catálogo

Os pacotes textuais principais usam o contêiner `NKDB` versão 1. A ferramenta
independente do projeto reconstrói seus segmentos, obtém o banco SQLite e é
capaz de remontar os arquivos byte a byte quando não há alterações.

O catálogo privado registra:

- hash do contêiner e do banco lógico;
- arquivo, tabela, chave e tipo da chave;
- texto-fonte e identidade SHA-256;
- classificação, estado editorial e tradução PT-BR;
- ocorrências duplicadas e contexto de uso.

Textos proprietários e bancos extraídos permanecem fora do Git.

## Pipeline editorial

Os lotes privados usam JSONL e uma identidade estável da base. Antes de uma
importação, o processo confirma texto-fonte e hash, valida placeholders,
marcações e quebras de linha e impede conflitos ou rebaixamento editorial. A
gravação é transacional: qualquer erro desfaz o lote inteiro.

Estados atuais:

- `pending`: ainda sem tradução;
- `translated`: base PT-BR produzida e estruturalmente válida;
- `reviewed`: revisada com contexto;
- `approved`: aprovada para uma versão testada.

## Construção isolada

O construtor:

1. recusa destinos dentro do cliente instalado;
2. exige os hashes exatos da versão catalogada;
3. aplica somente estados editoriais aceitos;
4. valida cada chave e o texto atual antes da alteração;
5. executa `integrity_check` no SQLite resultante;
6. remonta o `NKDB`, reabre o resultado e verifica o round-trip;
7. emite um manifesto sem texto proprietário.

A construção atual é marcada como `not_installable` e serve apenas como prova
de engenharia.

## Integridade lateral

Os arquivos `.nds` possuem 96 bytes e aparentam participar da cadeia de
integridade ou atualização. Seu papel exato ainda não foi comprovado. Eles não
são copiados, modificados nem sintetizados por suposição.

Nenhum instalador será liberado antes de confirmar:

- relação entre contêiner, sidecar e catálogos de assets;
- comportamento do launcher e do cliente com arquivos modificados;
- backup e restauração automáticos;
- detecção de atualização desconhecida;
- ausência de regressão mensurável de desempenho.

## Política de atualização segura

Uma futura instalação deverá reconhecer a versão e todos os hashes esperados.
Se qualquer verificação divergir, ela encerra sem alterar o jogo. A atualização
do launcher sempre ocorre com o cliente original restaurado; só depois uma
versão compatível do mod pode ser reaplicada.

Esse modelo não promete compatibilidade cega com toda versão futura. Ele
garante comportamento seguro: atualização desconhecida nunca deve receber um
pacote antigo à força.
