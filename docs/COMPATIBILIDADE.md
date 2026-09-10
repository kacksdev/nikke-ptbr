# Compatibilidade

## Versões registradas

| Mod | Cliente | Resultado |
| --- | --- | --- |
| 0.1.0 beta | `NIKKE.PC_Official_GL_151.8.5` | Instalação, launcher, runtime, catálogo, reparo, remoção e rollback aprovados |
| Builds privadas anteriores | `NIKKE.PC_Official_GL_150.6.9` | Engenharia validada; não distribuir |

A Release `0.1.0` reconhece somente o cliente testado. Isso é uma proteção intencional.

## O que é validado

Antes da instalação, o aplicativo confere:

1. estrutura da pasta e presença de `nikke.exe`;
2. tamanho e SHA-256 de três arquivos críticos;
3. dois fingerprints independentes em `GameAssembly.dll`;
4. identidade do pacote e de cada um dos três componentes;
5. ausência de colisão com outro `winhttp.dll` ou runtime desconhecido.

Uma divergência interrompe a operação antes da primeira gravação.

## Política após atualizações

O mod não modifica o sistema de atualização do NIKKE. Quando o jogo muda:

- executáveis ou pontos internos podem receber nova identidade;
- textos podem ser adicionados ou alterados;
- o índice precisa ser recomposto;
- a integração deve ser validada novamente.

Antes de atualizar o jogo:

1. feche jogo e launcher;
2. remova a tradução pelo instalador;
3. conclua a atualização oficial;
4. consulte esta página ou a Release mais recente;
5. reinstale apenas depois da confirmação de compatibilidade.

## Comportamento seguro

O runtime valida a identidade necessária antes de instalar seus pontos de observação. Se a validação falhar, ele não permanece ativo e o cliente preserva o texto original. Correspondências ausentes ou ambíguas também mantêm o valor original.

Esse comportamento reduz a possibilidade de estado parcial, mas não constitui promessa absoluta para versões futuras desconhecidas. Conteúdo novo pode aparecer em inglês até uma atualização do mod.
