# Arquitetura do mod

## Objetivo técnico

Integrar português brasileiro diretamente ao cliente de PC por um plugin Unity que substitua textos no pipeline de localização antes da renderização. O mod deverá carregar somente código próprio, catálogos PT-BR e recursos de fonte permitidos, sem redistribuir arquivos proprietários do jogo.

## Componentes planejados

### 1. Carregador do plugin

- BepInEx como ponto de entrada do mod.
- Plugin em C# e .NET compatível com a versão Unity do cliente.
- Inicialização única, logs objetivos e desligamento seguro.

### 2. Integração com o backend

O cliente será classificado como Mono ou IL2CPP:

- **Mono:** referências gerenciadas e patches HarmonyX sobre os métodos de localização.
- **IL2CPP:** Cpp2IL para reconstrução de metadata utilizável e Il2CppInterop para a ponte gerenciada do plugin.

Somente os componentes correspondentes ao backend confirmado entrarão no pacote.

### 3. Ponto central de localização

O plugin procurará o método que resolve uma chave ou texto-fonte para a string exibida. A substituição deverá ocorrer antes de:

- animação progressiva de diálogos;
- medição e quebra de linhas;
- paginação;
- criação final do componente TextMeshPro;
- cache visual da interface.

Isso evita o atraso em inglês e as substituições tardias que podem causar cortes, flicker ou inconsistência interna.

### 4. Catálogo PT-BR externo

Estrutura-alvo:

- identificador estável ou texto-fonte normalizado;
- tradução PT-BR;
- estado editorial;
- origem e versão do registro;
- placeholders e marcadores esperados;
- observações terminológicas quando necessárias.

O catálogo será organizado em camadas, permitindo que correções contextuais substituam a base sem apagar o histórico.

### 5. Fontes e TextMeshPro

- Identificar fontes e atlases usados pelo cliente.
- Confirmar suporte a `á`, `à`, `â`, `ã`, `é`, `ê`, `í`, `ó`, `ô`, `õ`, `ú`, `ü` e `ç`.
- Criar cobertura compatível em runtime caso a fonte original não tenha os glifos.
- Verificar largura, kerning, fallback, materiais e resoluções.

### 6. Auditoria

Antes de carregar o catálogo:

- JSON/JSONL válido;
- tradução não vazia;
- placeholders preservados;
- tags e quebras funcionais preservadas;
- normalização Unicode NFC;
- duplicatas e conflitos classificados;
- nomes e termos protegidos verificados.

### 7. Desempenho

- Índices em memória para consulta constante.
- Nenhuma varredura global por frame.
- Cache somente onde não impedir atualização correta do texto.
- Diagnóstico detalhado desativado no uso normal.
- Medição de inicialização, troca de cena e chamadas de tradução.

### 8. Distribuição

O pacote final deverá conter apenas:

- plugin compilado;
- catálogo PT-BR;
- configuração mínima;
- documentação de instalação, atualização e remoção;
- hash de integridade.

Nenhum AssetBundle, executável ou arquivo proprietário completo do cliente será redistribuído.
