# Arquitetura técnica

## Princípios

A primeira versão funcional segue cinco regras:

1. não substituir arquivos oficiais do cliente;
2. recusar versão ou identidade desconhecida antes de gravar;
3. aplicar somente correspondências exatas ou determinísticas;
4. falhar de forma segura, preservando o texto original;
5. tornar instalação, reparo e remoção auditáveis e reversíveis.

O projeto não contorna autenticação, monetização, rede, anticheat ou mecanismos de atualização.

## Catálogo privado

Os textos conhecidos são extraídos dos contêineres de texto do cliente para um catálogo SQLite privado. Cada unidade recebe identidade estável, contexto, estado editorial, proveniência e histórico de importação.

A base de distribuição não é um banco oficial modificado. Ela é compilada para um índice próprio, imutável e validado, que contém somente os dados necessários à apresentação local das traduções. Bancos, chaves, dumps e textos integrais extraídos não são publicados no repositório.

## Runtime

A distribuição instala três arquivos ao lado de `nikke.exe`:

| Arquivo | Função |
| --- | --- |
| `winhttp.dll` | Encaminha a superfície WinHTTP para a biblioteca do Windows e carrega somente o plugin fixo. |
| `NIKKEPTBR-Runtime.dll` | Valida o processo, ativa as rotas de texto e aplica correspondências seguras. |
| `NIKKEPTBR-Runtime.idx` | Índice imutável das correspondências PT-BR. |

O encaminhador preserva as exportações esperadas do WinHTTP do sistema. O runtime verifica a identidade do executável, do módulo e de dois pontos independentes antes de ativar qualquer interceptação temporária.

As rotas cobertas são:

- consulta principal por tabela e chave;
- comparação exata com o texto-fonte;
- correspondência determinística de modelos formatados, preservando placeholders;
- atribuição legada de `UnityEngine.UI.Text` para superfícies que não passam pela primeira rota.

Uma chave desconhecida, texto divergente, formato inválido, índice ausente ou cliente incompatível conserva o valor original. O runtime não modifica `GameAssembly.dll` em disco.

## Instalador

O instalador WPF contém um núcleo transacional e o pacote incorporado. Antes de escrever, ele valida:

- pasta e estrutura do cliente;
- versão e hashes críticos;
- dois fingerprints internos independentes;
- identidade e SHA-256 do bootstrap;
- manifesto e todos os arquivos da carga útil;
- estado anterior e colisões com componentes desconhecidos.

A operação segue este ciclo:

1. inspeção sem gravação;
2. criação ou recuperação do journal;
3. materialização verificada fora do cliente;
4. cópia atômica de cada componente próprio;
5. verificação integral do resultado;
6. registro do estado e do recibo;
7. rollback automático diante de falha.

Reparo usa quarentena para um componente conhecido alterado. Remoção exige um estado correspondente e apaga somente arquivos com identidade reconhecida. Um arquivo desconhecido bloqueia a ação em vez de ser sobrescrito ou removido.

## Estado local

Journal, recibos e quarentena ficam em `%LOCALAPPDATA%\Kacksdev\NIKKEPTBR\state`, separados por identidade da instalação. O bootstrap verificado usa `%LOCALAPPDATA%\Kacksdev\NIKKEPTBR\cache`.

O runtime pode criar apenas `NIKKEPTBR-Runtime\runtime.log` como saída no diretório do jogo. Saída inesperada bloqueia a remoção automática até inspeção.

## Validação

O pacote passou por 18 verificações de contrato e ciclo transacional. O executável final passou por 11 cenários em réplica descartável, incluindo instalação limpa, repetição idempotente, reparo, quarentena, recusa de versão desconhecida, remoção, colisão com proxy de terceiro, materialização do bootstrap e preservação dos hashes do cliente real.

A aceitação real comprovou carregamento do catálogo, texto visível, reparo, remoção e rollback no cliente `151.8.5`. A carga útil da versão final é a mesma aceita nessa prova. O invólucro final recebeu apenas congelamento determinístico e avisos completos de terceiros, seguido de nova aprovação dos 11 cenários isolados.

## Limites

A arquitetura não promete compatibilidade cega com atualizações futuras. Cada versão pública declara o cliente testado. Uma atualização desconhecida precisa de nova análise de catálogo, fingerprints, testes isolados e, quando necessário, aceitação real antes de receber suporte.
