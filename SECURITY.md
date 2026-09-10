# Política de segurança

## Versões cobertas

| Versão | Suporte |
| --- | --- |
| 0.1.x beta | Sim |
| Builds privadas anteriores | Não |

## Relato privado

Não abra uma Issue pública para vulnerabilidade, credencial, dado pessoal ou comportamento que possa comprometer o computador de outro usuário. Use o [relato privado de vulnerabilidade](https://github.com/kacksdev/nikke-ptbr/security/advisories/new).

Inclua, quando possível:

- versão do mod e do cliente;
- arquivo ou etapa afetada;
- comportamento observado e esperado;
- reprodução mínima sem dados pessoais.

## Medidas da versão

- instalador, manifesto e hash SHA-256 publicados juntos;
- pacote incorporado validado antes da escrita;
- versão, arquivos críticos e dois fingerprints conferidos;
- journal persistente e recuperação após interrupção;
- rollback automático;
- reparo restrito a componentes reconhecidos;
- colisões com arquivos desconhecidos recusadas;
- remoção limitada aos três arquivos próprios;
- runtime fail-open, preservando o texto original;
- zero telemetria e zero download durante a instalação.

## Fora do escopo

- vulnerabilidades do próprio NIKKE ou de seus serviços;
- contorno de autenticação, proteção, anticheat ou monetização;
- arquivos do cliente obtidos de fontes não autorizadas;
- modificações feitas por pacotes de terceiros;
- suporte geral de conta ou launcher.
