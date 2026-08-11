# Rotas técnicas avaliadas

Esta matriz descreve possibilidades, não instruções de execução. Nenhuma rota invasiva será testada enquanto o bloqueio contratual permanecer.

## 1. Localização oficial ou integração autorizada

**Prioridade máxima.** Uma tabela oficial, API, pacote de idioma aceito pelo cliente ou autorização formal permitiria trabalhar com menor risco técnico e de conta.

Vantagens:

- compatibilidade com atualizações;
- ausência de injeção no processo;
- melhor tratamento de fontes e layout;
- canal claro para distribuição e suporte.

Limitação: depende de resposta e decisão da empresa.

## 2. Sobreposição externa com OCR

Fluxo conceitual: capturar somente a região textual visível, reconhecer caracteres, traduzir e apresentar uma camada externa.

Vantagens possíveis:

- não reempacota arquivos do jogo;
- protótipo independente de formatos internos.

Problemas:

- latência, erros de OCR, nomes próprios e texto animado;
- oclusão da interface e dificuldade com escolhas interativas;
- captura de tela ainda coleta informações do jogo;
- programa de terceiro pode entrar nas restrições contratuais.

**Decisão:** não prototipar sem autorização escrita.

## 3. Catálogos e AssetBundles

O Unity Addressables usa catálogos para localizar recursos e dependências e normalmente empacota conteúdo em AssetBundles. No levantamento local, o contêiner `NKDB` indica uma camada própria que ferramentas genéricas podem não compreender.

Potencial:

- localizar TextAssets, tabelas, fontes e identificadores;
- permitir tradução anterior à renderização.

Riscos:

- datamining e engenharia reversa citados pelo contrato;
- hashes, CRCs e catálogos remotos podem invalidar mudanças;
- redistribuir bundles alterados pode incluir conteúdo proprietário;
- cada atualização pode substituir ou incompatibilizar o pacote.

**Decisão:** bloqueada.

## 4. Hook de runtime

Um framework Unity poderia, em tese, interceptar o ponto que entrega texto à interface e substituir somente a string, sem redistribuir assets.

Potencial:

- tradução dinâmica;
- preservação de conteúdo remoto;
- pacote pequeno.

Riscos:

- interação direta com o processo;
- diferença importante entre Mono e IL2CPP;
- possível detecção como programa não autorizado;
- regressões, crashes e custo de manutenção.

**Decisão:** bloqueada.

## 5. Interceptação de rede

Mesmo que parte do conteúdo venha de servidores, interceptar ou alterar tráfego ultrapassa o escopo necessário de uma localização e aumenta drasticamente risco de segurança, privacidade e contrato.

**Decisão:** rejeitada permanentemente para este projeto.

## 6. Injeção em memória ou contorno de proteção

Não existe justificativa para desabilitar anti-cheat, autenticação, integridade ou proteção tecnológica para traduzir texto.

**Decisão:** rejeitada permanentemente.

## Rota de trabalho se houver permissão

1. Registrar por escrito o escopo autorizado.
2. Identificar backend e formato sem acessar dados de conta.
3. Inventariar somente tabelas necessárias à localização.
4. Construir esquema com placeholders e glossário.
5. Produzir rascunho assistido por IA com rastreabilidade.
6. Revisar contexto, vozes e termos protegidos.
7. Validar fontes, cortes, timing e atualização.
8. Empacotar sem recursos proprietários e com rollback.
9. Publicar compatibilidade, riscos, autoria e limitações.

## Fontes técnicas primárias

- [Unity Addressables — catálogos de conteúdo](https://docs.unity3d.com/Packages/com.unity.addressables@1.21/manual/build-content-catalogs.html)
- [Unity Addressables — carregamento de AssetBundles](https://docs.unity3d.com/Packages/com.unity.addressables@1.20/manual/LoadingAssetBundles.html)
- [Contrato oficial de NIKKE em português](https://nikke-en.com/termsofservice/children/pt.html)
